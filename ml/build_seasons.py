"""When is each species seen? Month and hour histograms from iNaturalist.

For each species, asks iNaturalist how many research-grade California
observations fall in each month of the year and each hour of the day, and
writes species/seasons.json:

    {"source": "...", "species": {"<slug>": {"months": [12 counts, Jan first],
                                              "hours": [24 counts, midnight first]}}}

These count when people *report* sightings, so daytime and spring/summer are
over-represented for everything; the app compares each species with the
average to say "more at night than most" rather than reading raw counts.
Only observations with a recorded time count toward "hours".

Usage:
    python ml/build_seasons.py            # 2 API calls per species at 1 req/sec (~4 min)
    python ml/build_seasons.py --only barn_owl coyote
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from fetch_inat import CALIFORNIA_PLACE_ID, api_get, resolve_taxon  # noqa: E402


def histogram(taxon_id: int, interval: str, size: int, first: int) -> list[int]:
    data = api_get("/observations/histogram", taxon_id=taxon_id, place_id=CALIFORNIA_PLACE_ID,
                   quality_grade="research", date_field="observed", interval=interval)
    counts = data["results"][interval]
    return [int(counts.get(str(i), 0)) for i in range(first, first + size)]


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--species", default="species/california_100.csv")
    ap.add_argument("--taxa", default="data/images/taxa.json",
                    help="taxon ids cached by fetch_inat.py (resolved from the API if missing)")
    ap.add_argument("--out", default="species/seasons.json")
    ap.add_argument("--only", nargs="*", help="just these slugs (merged into an existing file)")
    args = ap.parse_args()

    species = list(csv.DictReader(open(args.species, encoding="utf-8")))
    if args.only:
        species = [s for s in species if s["slug"] in args.only]
    taxa_path = Path(args.taxa)
    taxa = json.loads(taxa_path.read_text(encoding="utf-8")) if taxa_path.exists() else {}
    out_path = Path(args.out)
    out = (json.loads(out_path.read_text(encoding="utf-8")) if args.only and out_path.exists()
           else {"species": {}})
    out["source"] = "iNaturalist research-grade California observations (histogram by month and hour)"

    for s in species:
        tid = taxa[s["slug"]]["taxon_id"] if s["slug"] in taxa else resolve_taxon(s["scientific_name"])["id"]
        months = histogram(tid, "month_of_year", 12, 1)
        hours = histogram(tid, "hour", 24, 0)
        out["species"][s["slug"]] = {"months": months, "hours": hours}
        print(f"{s['slug']}: {sum(months)} sightings, {sum(hours)} with a time")
    out_path.write_text(json.dumps(out), encoding="utf-8")
    print(f"wrote {out_path}")


if __name__ == "__main__":
    main()
