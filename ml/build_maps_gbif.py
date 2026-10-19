"""Sighting maps and seasons for many states at once, from GBIF instead of the
iNaturalist API.

build_ranges.py and build_seasons.py ask iNaturalist directly, which is right
for one state but far too slow for 48: the API throttles a single computer to a
few thousand requests a day. GBIF republishes iNaturalist's research-grade
observations (dataset 50c9509d-22c7-4a22-a47d-8c48425ef4a7) and serves them
much faster, so this writes the same files from there:

  <state>_ranges.json   sightings on the state's grid, as build_ranges.py
  <state>_seasons.json  months (all sightings) and local hours (from a sample of
                        timed sightings), as build_seasons.py

    python ml/build_maps_gbif.py               # every state missing either file
    python ml/build_maps_gbif.py --only VA NY  # just these
"""

from __future__ import annotations

import argparse
import csv
import json
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import requests

SPECIES = Path(__file__).resolve().parents[1] / "species"
GBIF = "https://api.gbif.org/v1"
# Pages of 100: some 300-record pages came back cut off mid-way.
PAGE = 100
INAT_DATASET = "50c9509d-22c7-4a22-a47d-8c48425ef4a7"
session = requests.Session()
session.headers["User-Agent"] = "CollectAnimals-dataset-builder/0.1"
session.mount("https://", requests.adapters.HTTPAdapter(pool_maxsize=8, max_retries=requests.adapters.Retry(
    total=6, backoff_factor=2, status_forcelist=[429, 500, 502, 503, 504])))


def get(path, **params):
    for attempt in range(5):
        try:
            r = session.get(f"{GBIF}/{path}", params=params, timeout=60)
            r.raise_for_status()
            time.sleep(0.2)
            return r.json()
        except (requests.RequestException, ValueError):  # dropped or cut-off responses
            if attempt == 4:
                raise
            time.sleep(5 * (attempt + 1))


def taxon_key(sci):
    m = get("species/match", name=sci, kingdom="Animalia")
    return m.get("usageKey") if m.get("matchType") != "NONE" else None


def species_maps(sci, state_name, grid, per_species):
    key = taxon_key(sci)
    if key is None:
        return None, None
    common = dict(taxonKey=key, country="US", stateProvince=state_name, datasetKey=INAT_DATASET,
                  occurrenceStatus="PRESENT")
    fac = get("occurrence/search", limit=0, facet="month", facetLimit=12, **common)
    months = [0] * 12
    for f in fac.get("facets", []):
        for c in f["counts"]:
            months[int(c["name"]) - 1] = c["count"]
    cells, hours = {}, [0] * 24
    offset = 0
    while offset < per_species:
        page = get("occurrence/search", limit=PAGE, offset=offset, hasCoordinate="true", **common)
        for o in page["results"]:
            lat, lon = o.get("decimalLatitude"), o.get("decimalLongitude")
            if lat is not None and lon is not None:
                c = int((lon - grid["lon0"]) // grid["step"]); r = int((lat - grid["lat0"]) // grid["step"])
                if 0 <= c < grid["cols"] and 0 <= r < grid["rows"]:
                    cells[(c, r)] = cells.get((c, r), 0) + 1
            ed = o.get("eventDate") or ""
            if "T" in ed and len(ed) >= 13 and ed[11:13].isdigit():
                hours[int(ed[11:13])] += 1
        if page.get("endOfRecords") or not page["results"]:
            break
        offset += PAGE
    return [[c, r, n] for (c, r), n in sorted(cells.items())], {"months": months, "hours": hours}


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--only", nargs="*", help="state codes")
    ap.add_argument("--per-species", type=int, default=600, help="sightings to place on the map")
    ap.add_argument("--workers", type=int, default=4)
    args = ap.parse_args()
    sj = json.loads((SPECIES / "states.json").read_text(encoding="utf-8"))
    for st in sj["states"]:
        if args.only and st["code"] not in args.only:
            continue
        rpath, spath = SPECIES / st["ranges"], SPECIES / st["seasons"]
        if not args.only and rpath.exists() and spath.exists():
            continue
        rows = list(csv.DictReader(open(SPECIES / st["species"], encoding="utf-8")))
        with ThreadPoolExecutor(args.workers) as pool:
            results = list(pool.map(lambda r: species_maps(r["scientific_name"], st["name"], st["grid"],
                                                           args.per_species), rows))
        ranges = {r["slug"]: cells for r, (cells, _) in zip(rows, results) if cells}
        seasons = {r["slug"]: s for r, (_, s) in zip(rows, results) if s}
        lines = [f'  {json.dumps(k)}: {json.dumps(v, separators=(",", ":"))}' for k, v in ranges.items()]
        rpath.write_text('{"grid": ' + json.dumps(st["grid"]) + ',\n "species": {\n' + ",\n".join(lines) + "\n }}\n",
                         encoding="utf-8")
        spath.write_text(json.dumps({"source": "iNaturalist research-grade observations via GBIF",
                                     "species": seasons}) + "\n", encoding="utf-8")
        missing = [r["slug"] for r in rows if r["slug"] not in ranges]
        print(f"{st['code']}: {len(ranges)} maps, {len(seasons)} seasons" +
              (f"; no sightings for {', '.join(missing)}" if missing else ""), flush=True)


if __name__ == "__main__":
    main()
