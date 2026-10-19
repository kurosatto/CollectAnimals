"""Download training photos for the species lists from iNaturalist.

The lists are the states in species/states.json (or a single --species CSV).
A species on several lists (coyote, mallard...) is one class. For each species
this script:
  1. resolves the scientific name to an iNaturalist taxon id,
  2. pages through research-grade observations in the states that list it
     and carry an open license (CC0 / CC-BY / CC-BY-NC), topping up from the
     whole US if those states don't have enough,
  3. downloads one photo per observation (so train/val splits never share an
     observation) into  <out>/<slug>/<photo_id>.jpg
Species that already have --per-species photos on disk are skipped, so adding
a state only downloads its new species.

It also builds an "other" class from random animal observations in each state
that are NOT on any list. Without it, a closed-set classifier would force every
upload (a dog, a pigeon, a houseplant...) into one of the species. Photos
already in "other" whose taxon is now on a list (e.g. a wild turkey after
adding North Carolina) are moved out to <out>/../other_pruned/.

Every downloaded photo is recorded in <out>/attribution.csv. The licenses
require attribution, so keep that file alongside the images.

Pets and pests (species/household.csv: dogs, cats, pigeons, rats...) are classes
too, so the app can say "that's a cat" instead of forcing it into "other" or a wild
species. They're always kept out of "other"; --household downloads their photos.
Pets are never research grade on iNaturalist (they're captive), so their photos
come from any quality grade across the US.

The script is resumable: re-running it skips photos already on disk.

Usage:
    python ml/fetch_inat.py --per-species 1000 --negatives 5000 --out data/images   # all states
    python ml/fetch_inat.py --states NC --size small --out data/images              # just add NC
    python ml/fetch_inat.py --household --only-household --out data/images         # just pets and pests

Please be polite to iNaturalist: the API asks for <= 1 request/sec. For much
larger pulls, use the iNaturalist Open Data bucket on AWS instead
(https://github.com/inaturalist/inaturalist-open-data).
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import requests

API = "https://api.inaturalist.org/v1"
CALIFORNIA_PLACE_ID = 14
US_PLACE_ID = 1
STATES_JSON = Path(__file__).resolve().parents[1] / "species" / "states.json"
HOUSEHOLD_CSV = STATES_JSON.parent / "household.csv"
ANIMALIA_TAXON_ID = 1
# The "other" class is spread evenly over these groups and over the 12 months,
# so it isn't dominated by whatever is most observed right now (e.g. this
# season's insects).
NEGATIVE_GROUPS = ["Aves", "Mammalia", "Reptilia", "Amphibia", "Insecta",
                   "Arachnida", "Mollusca", "Actinopterygii"]
LICENSES = "cc0,cc-by,cc-by-nc"
OTHER_CLASS = "other"
USER_AGENT = "CollectAnimals-dataset-builder/0.1"

session = requests.Session()
session.headers["User-Agent"] = USER_AGENT
_last_call = 0.0


def api_get(path: str, **params) -> dict:
    """GET an iNat API endpoint, throttled to ~1 req/sec with simple retries."""
    global _last_call
    resp = None
    for attempt in range(6):
        # INAT_MIN_INTERVAL slows long batch jobs down when iNaturalist is throttling.
        wait = float(os.getenv("INAT_MIN_INTERVAL", "1.05")) - (time.monotonic() - _last_call)
        if wait > 0:
            time.sleep(wait)
        _last_call = time.monotonic()
        try:
            resp = session.get(f"{API}{path}", params=params, timeout=30)
        except (requests.ConnectionError, requests.Timeout) as exc:
            # Dropped connections happen on long pulls; back off and retry.
            print(f"  retrying {path} after {type(exc).__name__}")
            time.sleep(2**attempt * 5)
            continue
        if resp.status_code == 429 or resp.status_code >= 500:
            time.sleep(2**attempt * 5)
            continue
        resp.raise_for_status()
        return resp.json()
    if resp is not None:
        resp.raise_for_status()
    raise RuntimeError(f"giving up on {path}")


def load_states(path: Path = STATES_JSON, only: list[str] | None = None) -> list[dict]:
    """states.json entries with file names made into paths; `only` filters by code."""
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    out = []
    for s in data["states"]:
        if only and s["code"] not in {c.upper() for c in only}:
            continue
        for k in ("species", "dex", "outline", "ranges", "hotspots", "seasons"):
            if s.get(k):
                s[k] = Path(path).parent / s[k]
        out.append(s)
    return out


def check_place(place_id: int, name: str) -> None:
    """Fail fast if states.json has the wrong iNaturalist place id for a state."""
    got = api_get(f"/places/{place_id}")["results"][0]["name"]
    if got.lower() != name.lower():
        raise SystemExit(f"states.json: iNaturalist place {place_id} is {got!r}, not {name!r}")


def resolve_taxon(scientific_name: str) -> dict:
    """Map a scientific name to an iNat taxon (handles synonyms/renames)."""
    # A one-word name ("Ariolimax") is a genus: all its species count as one class.
    rank = "genus" if len(scientific_name.split()) == 1 else "species"
    data = api_get("/taxa", q=scientific_name, rank=rank, is_active="true", per_page=10)
    results = data["results"]
    if not results:
        raise LookupError(f"no iNaturalist taxon for {scientific_name!r}")
    for taxon in results:
        if taxon["name"].lower() == scientific_name.lower():
            return taxon
    # The name may have been reclassified (e.g. Accipiter -> Astur); iNat's
    # search matches synonyms, so the top hit is the current name.
    print(f"  note: {scientific_name!r} resolved to {results[0]['name']!r}")
    return results[0]


def photo_url(photo: dict, size: str) -> str:
    # iNat returns the "square" (75px) URL; other sizes share the same path.
    return photo["url"].replace("/square.", f"/{size}.")


def iter_observations(limit: int, place_id=CALIFORNIA_PLACE_ID, **filters):
    """Yield up to `limit` observations, paging with id_below (deep-paging safe).
    place_id may be a comma-separated list of places."""
    id_below = None
    seen = 0
    while seen < limit:
        params = dict(
            place_id=place_id,
            photo_license=LICENSES,
            photos="true",
            per_page=200,
            order_by="id",
            order="desc",
            **filters,
        )
        if id_below:
            params["id_below"] = id_below
        results = api_get("/observations", **params)["results"]
        if not results:
            return
        for obs in results:
            id_below = obs["id"]
            if obs.get("photos"):
                yield obs
                seen += 1
                if seen >= limit:
                    return


def download(url: str, dest: Path) -> bool:
    if dest.exists():
        return True
    try:
        resp = session.get(url, timeout=30)
        resp.raise_for_status()
    except requests.RequestException as exc:
        print(f"  failed {url}: {exc}")
        return False
    tmp = dest.with_suffix(".part")
    tmp.write_bytes(resp.content)
    tmp.replace(dest)  # rename() fails on Windows if dest already exists
    return True


def fetch_class(name: str, out_dir: Path, limit: int, size: str, pool, attribution,
                target: int | None = None, **filters):
    """Download the photos of up to `limit` observations, stopping early once the
    class folder holds `target` photos."""
    class_dir = out_dir / name
    class_dir.mkdir(parents=True, exist_ok=True)
    have = {p.stem for p in class_dir.glob("*.jpg")}
    jobs = []
    for obs in iter_observations(limit, **filters):
        if target and len(have) >= target:
            break
        photo = obs["photos"][0]
        pid = str(photo["id"])
        if pid not in have:
            # Photos already on disk were recorded by an earlier run; the same
            # photo can also show up twice in the paging, so queue it once.
            have.add(pid)
            attribution.writerow(
                [name, pid, obs["id"], obs.get("taxon", {}).get("name", ""),
                 photo.get("license_code", ""), photo.get("attribution", ""),
                 f"https://www.inaturalist.org/observations/{obs['id']}"]
            )
            jobs.append(pool.submit(download, photo_url(photo, size), class_dir / f"{pid}.jpg"))
    ok = sum(j.result() for j in jobs)
    total = len(list(class_dir.glob("*.jpg")))
    print(f"  {name}: +{ok} new, {total} on disk")
    return total


def prune_other(out_dir: Path, listed_names: set[str]) -> None:
    """Move "other" photos of species that are now on a list out of "other"."""
    attr_path, other = out_dir / "attribution.csv", out_dir / OTHER_CLASS
    if not attr_path.exists() or not other.is_dir():
        return
    pruned = out_dir.parent / "other_pruned"
    moved = 0
    with open(attr_path, newline="", encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            # Subspecies ("Meleagris gallopavo silvestris") count as the species, and
            # a listed genus ("Ariolimax") covers all its species.
            words = row["taxon"].lower().split()
            listed = " ".join(words[:2]) in listed_names or words[:1] and words[0] in listed_names
            src = other / f"{row['photo_id']}.jpg"
            if row["class"] == OTHER_CLASS and listed and src.exists():
                pruned.mkdir(parents=True, exist_ok=True)
                src.replace(pruned / src.name)
                moved += 1
    print(f"moved {moved} 'other' photos of listed species to {pruned}")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--states", nargs="*", help="state codes from species/states.json (default: all)")
    ap.add_argument("--species", help="a single species CSV instead of the states (photos from California)")
    ap.add_argument("--out", default="data/images")
    ap.add_argument("--per-species", type=int, default=1000)
    ap.add_argument("--negatives", type=int, default=5000,
                    help="photos per state for the 'other' class (0 to skip)")
    ap.add_argument("--size", default="medium", choices=["small", "medium", "large"],
                    help="medium is ~500px, plenty for 224-384px training")
    ap.add_argument("--only", nargs="*", help="limit to these slugs")
    ap.add_argument("--household", action="store_true", help="also download the pets and pests")
    ap.add_argument("--only-household", action="store_true", help="download only the pets and pests")
    ap.add_argument("--workers", type=int, default=16,
                    help="parallel photo downloads (from the AWS open-data bucket; "
                         "API calls stay at ~1/sec regardless)")
    args = ap.parse_args()
    # One pooled connection per download thread (requests defaults to 10).
    session.mount("https://", requests.adapters.HTTPAdapter(pool_maxsize=args.workers))

    if args.species:
        lists = all_lists = [{"code": "CA", "name": "California", "species": Path(args.species),
                              "inat_place_id": CALIFORNIA_PLACE_ID}]
    else:
        lists, all_lists = load_states(only=args.states), load_states()
        if not lists:
            raise SystemExit(f"no states match {args.states}")
        # Pets and pests come from the whole US, so the states' places aren't used.
        for st in lists if not args.only_household else []:
            check_place(st["inat_place_id"], st["name"])

    # Every listed species in every state (so "other" never includes one), with
    # the places that list it.
    species: dict[str, dict] = {}
    for st in all_lists:
        for row in csv.DictReader(open(st["species"], encoding="utf-8")):
            species.setdefault(row["slug"], {**row, "places": []})["places"].append(st["inat_place_id"])
    # Pets and pests: one class each, from anywhere in the US, never in "other".
    household = []
    if HOUSEHOLD_CSV.exists():
        for row in csv.DictReader(open(HOUSEHOLD_CSV, encoding="utf-8")):
            if row["slug"] not in species:
                species[row["slug"]] = {**row, "places": [US_PLACE_ID]}
                household.append(row["slug"])
    wanted = [] if args.only_household else [
        r["slug"] for st in lists for r in csv.DictReader(open(st["species"], encoding="utf-8"))]
    if args.household or args.only_household:
        wanted += household
    wanted = list(dict.fromkeys(s for s in wanted if not args.only or s in set(args.only)))

    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)
    # Taxon ids are cached so re-runs (and the backend) don't need to re-resolve.
    taxa_path = out_dir / "taxa.json"
    taxa = json.loads(taxa_path.read_text(encoding="utf-8")) if taxa_path.exists() else {}
    for slug, s in species.items():
        if slug not in taxa:
            t = resolve_taxon(s["scientific_name"])
            taxa[slug] = {"taxon_id": t["id"], "name": t["name"],
                          "observations_count": t.get("observations_count")}
            taxa_path.write_text(json.dumps(taxa, indent=2), encoding="utf-8")

    listed_names = {s["scientific_name"].lower() for s in species.values()}
    listed_names |= {taxa[slug]["name"].lower() for slug in species}
    prune_other(out_dir, listed_names)

    attr_path = out_dir / "attribution.csv"
    new_file = not attr_path.exists()
    with open(attr_path, "a", newline="", encoding="utf-8") as fh, ThreadPoolExecutor(args.workers) as pool:
        attribution = csv.writer(fh)
        if new_file:
            attribution.writerow(["class", "photo_id", "observation_id", "taxon",
                                  "license", "attribution", "url"])
        for slug in wanted:
            on_disk = len(list((out_dir / slug).glob("*.jpg")))
            if on_disk >= args.per_species:
                print(f"{slug}: {on_disk} on disk, skipping")
                continue
            print(f"{slug} ({taxa[slug]['name']})")
            places = ",".join(str(p) for p in species[slug]["places"])
            # Pets are captive, so never research grade: take any grade for them.
            grade = "research" if slug not in household else "research,needs_id,casual"
            total = fetch_class(slug, out_dir, args.per_species, args.size, pool, attribution,
                                target=args.per_species, place_id=places,
                                taxon_id=taxa[slug]["taxon_id"], quality_grade=grade)
            if total < args.per_species:
                # Rare species (red wolf, hellbender...) need photos from their whole US range.
                print("  topping up from the whole US")
                fetch_class(slug, out_dir, 2 * args.per_species, args.size, pool, attribution,
                            target=args.per_species, place_id=US_PLACE_ID,
                            taxon_id=taxa[slug]["taxon_id"], quality_grade=grade)
            fh.flush()

        if args.negatives and not args.only and not args.only_household:
            all_ids = ",".join(str(taxa[slug]["taxon_id"]) for slug in species)
            # Include casual/needs_id too: "other" just needs to be "an animal
            # photo that isn't one of ours", not a confirmed ID. But it must be
            # identified to species: a coarse ID like "Taricha" or "Sciuridae"
            # passes without_taxon_id yet may well be one of our species, and
            # ~22% of an unfiltered pull was such coarse IDs.
            per_slice = max(1, args.negatives // (len(NEGATIVE_GROUPS) * 12))
            for st in lists:
                print(f"{OTHER_CLASS} (animals in {st['name']} not on any list)")
                for group in NEGATIVE_GROUPS:
                    for month in range(1, 13):
                        print(f"  {group}, month {month}")
                        fetch_class(OTHER_CLASS, out_dir, per_slice, args.size, pool, attribution,
                                    place_id=st["inat_place_id"],
                                    taxon_id=ANIMALIA_TAXON_ID, without_taxon_id=all_ids,
                                    iconic_taxa=group, month=month, hrank="species")
                        fh.flush()


if __name__ == "__main__":
    main()
