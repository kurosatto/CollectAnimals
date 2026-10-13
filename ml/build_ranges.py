"""Build where-to-find-it maps for the species list from iNaturalist sightings.

For each species on a state's list, counts its most recent research-grade
observations in that state (up to --per-species) on the state's lon/lat grid
(from species/states.json) and writes the state's ranges file, e.g. for
California species/ranges.json:

    {"grid": {"lon0": -124.5, "lat0": 32.5, "step": 0.25, "cols": 42, "rows": 38},
     "species": {"<slug>": [[col, row, count], ...]}}

with col = floor((lon - lon0) / step), row = floor((lat - lat0) / step); only
non-empty cells are listed. Locations of sensitive species are obscured by
iNaturalist (randomized within roughly 0.2 degrees), about one grid cell, so
the maps stay coarse on purpose.

It also writes the state's outline (e.g. species/california_outline.json:
polygons as [[lon, lat], ...] rings, from Natural Earth, public domain) so the
apps can draw the map without a GIS library.

Usage:
    python ml/build_ranges.py                    # California; ~5 API calls per species at 1 req/sec (~10 min)
    python ml/build_ranges.py --state NC
    python ml/build_ranges.py --only coyote bobcat
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from fetch_inat import api_get, load_states, resolve_taxon, session  # noqa: E402

NATURAL_EARTH = ("https://raw.githubusercontent.com/nvkelso/natural-earth-vector/master/"
                 "geojson/ne_50m_admin_1_states_provinces.geojson")


def observation_points(taxon_id: int, place_id: int, limit: int):
    """Yield (lon, lat) of up to `limit` recent research-grade observations in a place."""
    id_below, seen = None, 0
    while seen < limit:
        params = dict(taxon_id=taxon_id, place_id=place_id, quality_grade="research",
                      geo="true", per_page=200, order_by="id", order="desc")
        if id_below:
            params["id_below"] = id_below
        results = api_get("/observations", **params)["results"]
        if not results:
            return
        for obs in results:
            id_below = obs["id"]
            if obs.get("location"):
                lat, lon = map(float, obs["location"].split(","))
                yield lon, lat
                seen += 1
                if seen >= limit:
                    return


def to_cells(points, grid: dict) -> list[list[int]]:
    counts: dict[tuple[int, int], int] = {}
    for lon, lat in points:
        col = math.floor((lon - grid["lon0"]) / grid["step"])
        row = math.floor((lat - grid["lat0"]) / grid["step"])
        if 0 <= col < grid["cols"] and 0 <= row < grid["rows"]:
            counts[(col, row)] = counts.get((col, row), 0) + 1
    return [[c, r, n] for (c, r), n in sorted(counts.items())]


def state_outline(name: str) -> list[list[list[float]]]:
    states = session.get(NATURAL_EARTH, timeout=60).json()
    feature = next(f for f in states["features"]
                   if f["properties"].get("name") == name and f["properties"].get("iso_a2") == "US")
    geom = feature["geometry"]
    polygons = geom["coordinates"] if geom["type"] == "MultiPolygon" else [geom["coordinates"]]
    # Outer rings only (states have no holes at this scale); 4 decimals is ~10 m.
    return [[[round(x, 4), round(y, 4)] for x, y in poly[0]] for poly in polygons]


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--state", default="CA", help="state code from species/states.json")
    ap.add_argument("--taxa", default="data/images/taxa.json",
                    help="taxon ids cached by fetch_inat.py (resolved from the API if missing)")
    ap.add_argument("--per-species", type=int, default=1000)
    ap.add_argument("--only", nargs="*", help="limit to these slugs (merged into an existing file)")
    args = ap.parse_args()

    state = load_states(only=[args.state])[0]
    grid, species_csv = state["grid"], state["species"]
    species = list(csv.DictReader(open(species_csv, encoding="utf-8")))
    if args.only:
        species = [s for s in species if s["slug"] in set(args.only)]
    taxa_path = Path(args.taxa)
    taxa = json.loads(taxa_path.read_text(encoding="utf-8")) if taxa_path.exists() else {}

    out = state["ranges"]
    ranges = json.loads(out.read_text(encoding="utf-8"))["species"] if out.exists() and args.only else {}
    for s in species:
        if s["slug"] in taxa:
            taxon_id = taxa[s["slug"]]["taxon_id"]
        else:
            taxon_id = resolve_taxon(s["scientific_name"])["id"]
        cells = to_cells(observation_points(taxon_id, state["inat_place_id"], args.per_species), grid)
        ranges[s["slug"]] = cells
        print(f"{s['slug']}: {sum(n for *_, n in cells)} sightings in {len(cells)} cells", flush=True)

    order = [r["slug"] for r in csv.DictReader(open(species_csv, encoding="utf-8"))]
    data = {"grid": grid, "species": {k: ranges[k] for k in order if k in ranges}}
    # One species per line: compact, but still diff-friendly.
    lines = [f'  {json.dumps(k)}: {json.dumps(v, separators=(",", ":"))}' for k, v in data["species"].items()]
    out.write_text('{"grid": ' + json.dumps(grid) + ',\n "species": {\n' + ",\n".join(lines) + "\n }}\n",
                   encoding="utf-8")
    print(f"wrote {out}")

    outline = state["outline"]
    if not outline.exists():
        rings = state_outline(state["name"])
        outline.write_text(json.dumps({"source": "Natural Earth 1:50m admin-1 (public domain)",
                                       "rings": rings}, separators=(",", ":")), encoding="utf-8")
        print(f"wrote {outline} ({sum(len(r) for r in rings)} points)")


if __name__ == "__main__":
    main()
