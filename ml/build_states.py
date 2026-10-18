"""Draft species lists and states.json entries for every US state.

For each state not yet in species/states.json this script:
  1. takes the state's most-observed wild animal species on iNaturalist
     (research grade, not captive, with an English name), up to a quota per
     group (20 mammals, 38 birds, 12 reptiles, 8 amphibians, 12 bugs, 10 water
     animals) like the hand-made California and North Carolina lists, then
     tops up to 100 by observation count;
  2. gives each a rarity from its rank (50 common, 27 uncommon, 18 rare,
     5 legendary: the least-observed of the 100) and a category;
  3. reuses the slug of a species already on another state's list, so a coyote
     is one class for the model wherever it lives;
  4. writes species/<state>_100.csv, the state's outline (Natural Earth, public
     domain), a map grid sized to the state, its standard-time UTC offset, and
     a towns file from Natural Earth's populated places, and adds the state to
     species/states.json (California stays the default).

The lists are drafts: review them before relying on them. Ranges, hotspots
and seasons come from build_ranges.py / build_hotspots.py / build_seasons.py.

    python ml/build_states.py                 # every missing state
    python ml/build_states.py --only VA NY    # just these
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import re
import time
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parents[1]
SPECIES = ROOT / "species"
API = "https://api.inaturalist.org/v1"
NE = "https://raw.githubusercontent.com/nvkelso/natural-earth-vector/master/geojson/"
STATES_GEO = NE + "ne_50m_admin_1_states_provinces.geojson"
TOWNS_GEO = NE + "ne_10m_populated_places_simple.geojson"
session = requests.Session()
session.headers["User-Agent"] = "CollectAnimals-dataset-builder/0.1"

# code, name, standard-time UTC offset
STATES = [
    ("AL", "Alabama", -6), ("AK", "Alaska", -9), ("AZ", "Arizona", -7), ("AR", "Arkansas", -6),
    ("CA", "California", -8), ("CO", "Colorado", -7), ("CT", "Connecticut", -5), ("DE", "Delaware", -5),
    ("FL", "Florida", -5), ("GA", "Georgia", -5), ("HI", "Hawaii", -10), ("ID", "Idaho", -7),
    ("IL", "Illinois", -6), ("IN", "Indiana", -5), ("IA", "Iowa", -6), ("KS", "Kansas", -6),
    ("KY", "Kentucky", -5), ("LA", "Louisiana", -6), ("ME", "Maine", -5), ("MD", "Maryland", -5),
    ("MA", "Massachusetts", -5), ("MI", "Michigan", -5), ("MN", "Minnesota", -6), ("MS", "Mississippi", -6),
    ("MO", "Missouri", -6), ("MT", "Montana", -7), ("NE", "Nebraska", -6), ("NV", "Nevada", -8),
    ("NH", "New Hampshire", -5), ("NJ", "New Jersey", -5), ("NM", "New Mexico", -7), ("NY", "New York", -5),
    ("NC", "North Carolina", -5), ("ND", "North Dakota", -6), ("OH", "Ohio", -5), ("OK", "Oklahoma", -6),
    ("OR", "Oregon", -8), ("PA", "Pennsylvania", -5), ("RI", "Rhode Island", -5), ("SC", "South Carolina", -5),
    ("SD", "South Dakota", -6), ("TN", "Tennessee", -6), ("TX", "Texas", -6), ("UT", "Utah", -7),
    ("VT", "Vermont", -5), ("VA", "Virginia", -5), ("WA", "Washington", -8), ("WV", "West Virginia", -5),
    ("WI", "Wisconsin", -6), ("WY", "Wyoming", -7),
]
CATEGORY = {"Mammalia": "mammal", "Aves": "bird", "Reptilia": "reptile", "Amphibia": "amphibian",
            "Insecta": "invertebrate", "Arachnida": "invertebrate", "Mollusca": "invertebrate",
            "Actinopterygii": "marine", "Animalia": "marine"}
GROUPS = [("Mammalia", "mammal"), ("Aves", "bird"), ("Reptilia", "reptile"), ("Amphibia", "amphibian"),
          ("Insecta", "invertebrate"), ("Arachnida", "invertebrate"), ("Mollusca", "invertebrate"),
          ("Actinopterygii", "marine"), ("Animalia", "marine")]
# Per state, like the hand-made lists: lots of birds and mammals, a few bugs.
QUOTA = {"mammal": 20, "bird": 38, "reptile": 12, "amphibian": 8, "invertebrate": 12, "marine": 10}
RARITY = ["common"] * 50 + ["uncommon"] * 27 + ["rare"] * 18 + ["legendary"] * 5


def api(path, **params):
    for attempt in range(5):
        r = session.get(f"{API}/{path}", params=params, timeout=60)
        if r.status_code == 200:
            time.sleep(1.0)  # iNaturalist asks for <= 1 request/sec
            return r.json()
        time.sleep(5 * (attempt + 1))
    r.raise_for_status()


def place_id(name):
    for q in (name, f"{name}, US"):
        for p in api("places/autocomplete", q=q, per_page=20)["results"]:
            # Not "Florida, PR" or "Maryland, LR": the US state.
            if p.get("admin_level") == 10 and p["name"] == name and (p.get("display_name") or "").endswith(", US"):
                return p["id"]
    raise SystemExit(f"no iNaturalist place for {name}")


def slugify(s):
    return re.sub(r"[^a-z0-9]+", "_", s.lower().replace("'", "")).strip("_")


def known_slugs():
    """scientific name (lower) -> slug, from every existing list."""
    out = {}
    for f in SPECIES.glob("*_100.csv"):
        for r in csv.DictReader(open(f, encoding="utf-8")):
            out[r["scientific_name"].lower()] = r["slug"]
    return out


def draft_list(pid, slugs, used):
    """Most-observed species per group, filled to QUOTA, then topped up by count."""
    pools = {}
    for group, cat in GROUPS:
        res = api("observations/species_counts", place_id=pid, iconic_taxa=group, quality_grade="research",
                  rank="species", captive="false", per_page=60)["results"]
        pools.setdefault(cat, []).extend(r for r in res if r["taxon"].get("preferred_common_name"))
    for cat in pools:
        pools[cat].sort(key=lambda r: -r["count"])
    picked, seen = [], set()

    def take(r, cat):
        if r["taxon"]["id"] not in seen:
            seen.add(r["taxon"]["id"]); picked.append((r, cat))

    for cat, n in QUOTA.items():
        for r in pools.get(cat, [])[:n]:
            take(r, cat)
    rest = sorted(((r, c) for c, rs in pools.items() for r in rs[QUOTA.get(c, 0):]), key=lambda x: -x[0]["count"])
    for r, cat in rest:
        if len(picked) >= 100:
            break
        take(r, cat)
    picked.sort(key=lambda x: -x[0]["count"])
    rows = []
    for r, cat in picked[:100]:
        t = r["taxon"]; sci = t["name"]; common = t["preferred_common_name"]
        slug = slugs.get(sci.lower())
        if not slug:
            slug = slugify(common)
            if used.get(slug, sci) != sci:  # same English name, different species
                slug = slugify(f"{common} {sci.split()[0]}")
        used[slug] = sci
        slugs[sci.lower()] = slug
        rows.append({"slug": slug, "common_name": common[0].upper() + common[1:], "scientific_name": sci,
                     "category": cat, "taxon_id": t["id"], "count": r["count"]})
    for row, rarity in zip(rows, RARITY):
        row["rarity"] = rarity
    return rows


def outline_rings(geo, name, code):
    f = next(f for f in geo["features"] if f["properties"].get("name") == name
             and f["properties"].get("iso_a2") == "US")
    g = f["geometry"]
    polys = g["coordinates"] if g["type"] == "MultiPolygon" else [g["coordinates"]]
    rings = [[[round(x, 4), round(y, 4)] for x, y in p[0]] for p in polys]
    if code == "AK":  # drop the far-western Aleutians across the date line
        rings = [r for r in rings if all(x < 0 for x, _ in r)]
    if code == "HI":  # the main islands, not the uninhabited chain out to Midway
        rings = [r for r in rings if all(x > -161 for x, _ in r)]
    return rings


def grid_for(bounds):
    w = bounds["east"] - bounds["west"]
    step = next(s for s in (0.0625, 0.125, 0.25, 0.5, 1.0) if w / s <= 80)
    lon0 = math.floor(bounds["west"] / step) * step
    lat0 = math.floor(bounds["south"] / step) * step
    cols = math.ceil((bounds["east"] - lon0) / step)
    rows = math.ceil((bounds["north"] - lat0) / step)
    return {"lon0": round(lon0, 4), "lat0": round(lat0, 4), "step": step, "cols": cols, "rows": rows}


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--only", nargs="*", help="state codes")
    args = ap.parse_args()
    sj_path = SPECIES / "states.json"
    sj = json.loads(sj_path.read_text(encoding="utf-8"))
    have = {s["code"] for s in sj["states"]}
    todo = [s for s in STATES if s[0] not in have and (not args.only or s[0] in args.only)]
    geo = session.get(STATES_GEO, timeout=120).json()
    towns_geo = session.get(TOWNS_GEO, timeout=120).json()
    slugs = known_slugs()
    used = {v: k for k, v in slugs.items()}
    for code, name, utc in todo:
        stem = name.lower().replace(" ", "_")
        pid = place_id(name)
        rows = draft_list(pid, slugs, used)
        with open(SPECIES / f"{stem}_100.csv", "w", newline="", encoding="utf-8") as fh:
            w = csv.writer(fh)
            w.writerow(["slug", "common_name", "scientific_name", "category", "rarity"])
            for r in rows:
                w.writerow([r["slug"], r["common_name"], r["scientific_name"], r["category"], r["rarity"]])
        rings = outline_rings(geo, name, code)
        (SPECIES / f"{stem}_outline.json").write_text(json.dumps(
            {"source": "Natural Earth 1:50m admin-1 (public domain)", "rings": rings}), encoding="utf-8")
        xs = [x for r in rings for x, _ in r]; ys = [y for r in rings for _, y in r]
        bounds = {"west": round(min(xs) - 0.1, 1), "east": round(max(xs) + 0.1, 1),
                  "south": round(min(ys) - 0.1, 1), "north": round(max(ys) + 0.1, 1)}
        towns = sorted(([p["properties"]["name"], round(p["geometry"]["coordinates"][1], 2),
                         round(p["geometry"]["coordinates"][0], 2), p["properties"].get("pop_max") or 0]
                        for p in towns_geo["features"]
                        if p["properties"].get("adm0_a3") == "USA" and p["properties"].get("adm1name") == name),
                       key=lambda t: -t[3])
        (SPECIES / f"{stem}_places.json").write_text(json.dumps(
            {"note": f"Towns used to describe roughly where a capture happened in {name} (\"near ...\"). "
                     "From Natural Earth populated places (public domain).",
             "towns": [t[:3] for t in towns]}), encoding="utf-8")
        sj["states"].append({
            "code": code, "name": name, "species": f"{stem}_100.csv", "dex": None,
            "outline": f"{stem}_outline.json", "ranges": f"{stem}_ranges.json",
            "hotspots": f"{stem}_hotspots.json", "places": f"{stem}_places.json",
            "seasons": f"{stem}_seasons.json", "utc_offset": utc, "inat_place_id": pid,
            "bounds": bounds, "grid": grid_for(bounds)})
        sj_path.write_text(json.dumps(sj, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
        cats = {}
        for r in rows:
            cats[r["category"]] = cats.get(r["category"], 0) + 1
        print(f"{code} {name}: {len(rows)} species {cats}, {len(towns)} towns", flush=True)


if __name__ == "__main__":
    main()
