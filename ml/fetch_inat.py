"""Download training photos for the species list from iNaturalist.

For each species in the CSV this script:
  1. resolves the scientific name to an iNaturalist taxon id,
  2. pages through research-grade observations in California that carry an
     open license (CC0 / CC-BY / CC-BY-NC),
  3. downloads one photo per observation (so train/val splits never share an
     observation) into  <out>/<slug>/<photo_id>.jpg

It also builds an "other" class from random California animal observations
that are NOT in the species list. Without it, a closed-set classifier would
force every upload (a dog, a pigeon, a houseplant...) into one of the 100.

Every downloaded photo is recorded in <out>/attribution.csv. The licenses
require attribution, so keep that file alongside the images.

The script is resumable: re-running it skips photos already on disk.

Usage:
    python ml/fetch_inat.py --per-species 1000 --negatives 5000 --out data/images

Please be polite to iNaturalist: the API asks for <= 1 request/sec. For much
larger pulls, use the iNaturalist Open Data bucket on AWS instead
(https://github.com/inaturalist/inaturalist-open-data).
"""

from __future__ import annotations

import argparse
import csv
import json
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import requests

API = "https://api.inaturalist.org/v1"
CALIFORNIA_PLACE_ID = 14
ANIMALIA_TAXON_ID = 1
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
        wait = 1.05 - (time.monotonic() - _last_call)
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


def resolve_taxon(scientific_name: str) -> dict:
    """Map a scientific name to an iNat taxon (handles synonyms/renames)."""
    data = api_get("/taxa", q=scientific_name, rank="species", is_active="true", per_page=10)
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


def iter_observations(limit: int, **filters):
    """Yield up to `limit` observations, paging with id_below (deep-paging safe)."""
    id_below = None
    seen = 0
    while seen < limit:
        params = dict(
            place_id=CALIFORNIA_PLACE_ID,
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
    tmp.rename(dest)
    return True


def fetch_class(name: str, out_dir: Path, limit: int, size: str, pool, attribution, **filters):
    class_dir = out_dir / name
    class_dir.mkdir(parents=True, exist_ok=True)
    have = {p.stem for p in class_dir.glob("*.jpg")}
    jobs = []
    for obs in iter_observations(limit, **filters):
        photo = obs["photos"][0]
        pid = str(photo["id"])
        if pid not in have:
            # Photos already on disk were recorded by an earlier run.
            attribution.writerow(
                [name, pid, obs["id"], obs.get("taxon", {}).get("name", ""),
                 photo.get("license_code", ""), photo.get("attribution", ""),
                 f"https://www.inaturalist.org/observations/{obs['id']}"]
            )
            jobs.append(pool.submit(download, photo_url(photo, size), class_dir / f"{pid}.jpg"))
    ok = sum(j.result() for j in jobs)
    total = len(list(class_dir.glob("*.jpg")))
    print(f"  {name}: +{ok} new, {total} on disk")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--species", default="species/california_100.csv")
    ap.add_argument("--out", default="data/images")
    ap.add_argument("--per-species", type=int, default=1000)
    ap.add_argument("--negatives", type=int, default=5000,
                    help="photos for the 'other' class (0 to skip)")
    ap.add_argument("--size", default="medium", choices=["small", "medium", "large"],
                    help="medium is ~500px, plenty for 224-384px training")
    ap.add_argument("--only", nargs="*", help="limit to these slugs")
    ap.add_argument("--workers", type=int, default=4)
    args = ap.parse_args()

    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)
    species = list(csv.DictReader(open(args.species, encoding="utf-8")))
    if args.only:
        species = [s for s in species if s["slug"] in set(args.only)]

    # Taxon ids are cached so re-runs (and the backend) don't need to re-resolve.
    taxa_path = out_dir / "taxa.json"
    taxa = json.loads(taxa_path.read_text(encoding="utf-8")) if taxa_path.exists() else {}
    for s in species:
        if s["slug"] not in taxa:
            t = resolve_taxon(s["scientific_name"])
            taxa[s["slug"]] = {"taxon_id": t["id"], "name": t["name"],
                               "observations_count": t.get("observations_count")}
            taxa_path.write_text(json.dumps(taxa, indent=2), encoding="utf-8")

    attr_path = out_dir / "attribution.csv"
    new_file = not attr_path.exists()
    with open(attr_path, "a", newline="", encoding="utf-8") as fh, ThreadPoolExecutor(args.workers) as pool:
        attribution = csv.writer(fh)
        if new_file:
            attribution.writerow(["class", "photo_id", "observation_id", "taxon",
                                  "license", "attribution", "url"])
        for s in species:
            print(f"{s['slug']} ({taxa[s['slug']]['name']})")
            fetch_class(s["slug"], out_dir, args.per_species, args.size, pool, attribution,
                        taxon_id=taxa[s["slug"]]["taxon_id"], quality_grade="research")
            fh.flush()

        if args.negatives and not args.only:
            print(f"{OTHER_CLASS} (animals not in the list)")
            all_ids = ",".join(str(t["taxon_id"]) for t in taxa.values())
            # Include casual/needs_id too: "other" just needs to be "an animal
            # photo that isn't one of ours", not a confirmed ID.
            fetch_class(OTHER_CLASS, out_dir, args.negatives, args.size, pool, attribution,
                        taxon_id=ANIMALIA_TAXON_ID, without_taxon_id=all_ids)


if __name__ == "__main__":
    main()
