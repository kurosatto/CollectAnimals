"""When is each species seen? Month and hour histograms from iNaturalist.

For each species on a state's list, asks iNaturalist how many research-grade
observations in that state fall in each month of the year and each local hour
of the day, and writes the state's seasons file from species/states.json
(species/seasons.json for California):

    {"source": "...", "species": {"<slug>": {"months": [12 counts, Jan first],
                                              "hours": [24 counts, midnight first]}}}

These count when people *report* sightings, so daytime and spring/summer are
over-represented for everything; the app compares each species with the
average to say "more at night than most" rather than reading raw counts.
Only observations with a recorded time count toward "hours".

Usage:
    python ml/build_seasons.py            # 2 API calls per species at 1 req/sec (~4 min)
    python ml/build_seasons.py --state NC
    python ml/build_seasons.py --only barn_owl coyote
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from fetch_inat import api_get, load_states, resolve_taxon  # noqa: E402


def histogram(taxon_id: int, place_id: int, interval: str, size: int, first: int) -> list[int]:
    data = api_get("/observations/histogram", taxon_id=taxon_id, place_id=place_id,
                   quality_grade="research", date_field="observed", interval=interval)
    counts = data["results"][interval]
    return [int(counts.get(str(i), 0)) for i in range(first, first + size)]


def local_hour(utc: datetime, offset: int) -> int:
    """Local hour for a UTC time in a US time zone `offset` hours from UTC in
    winter, with daylight time from 2 a.m. on the 2nd Sunday of March to 2 a.m.
    on the 1st Sunday of November. No tz database needed (Windows lacks one)."""
    y = utc.year
    march = datetime(y, 3, 8 + (6 - datetime(y, 3, 8).weekday()) % 7, 2 - offset, tzinfo=timezone.utc)
    nov = datetime(y, 11, 1 + (6 - datetime(y, 11, 1).weekday()) % 7, 1 - offset, tzinfo=timezone.utc)
    return (utc + timedelta(hours=offset + 1 if march <= utc < nov else offset)).hour


def hours_of_day(taxon_id: int, place_id: int, offset: int, today: date, min_total: int = 30) -> list[int]:
    """Sightings per local hour of day. iNaturalist's "hour" histogram is a time
    series keyed by UTC timestamp, so fetch a recent window and fold it into 24
    bins; widen the window for rarely seen species."""
    for years in (1, 3):
        data = api_get("/observations/histogram", taxon_id=taxon_id, place_id=place_id,
                       quality_grade="research", date_field="observed", interval="hour",
                       d1=(today - timedelta(days=365 * years)).isoformat())
        bins = [0] * 24
        for stamp, n in data["results"]["hour"].items():
            if n:
                bins[local_hour(datetime.fromisoformat(stamp.replace("Z", "+00:00")), offset)] += int(n)
        if sum(bins) >= min_total:
            break
    return bins


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--state", default="CA", help="state code from species/states.json")
    ap.add_argument("--taxa", default="data/images/taxa.json",
                    help="taxon ids cached by fetch_inat.py (resolved from the API if missing)")
    ap.add_argument("--only", nargs="*", help="just these slugs (merged into an existing file)")
    ap.add_argument("--hours-only", action="store_true",
                    help="keep the month counts already in --out and only refetch the hours")
    args = ap.parse_args()

    state = load_states(only=[args.state])[0]
    if not state.get("seasons"):
        raise SystemExit(f"states.json: no \"seasons\" file for {state['code']}")
    place, offset = state["inat_place_id"], state["utc_offset"]
    species = list(csv.DictReader(open(state["species"], encoding="utf-8")))
    if args.only:
        species = [s for s in species if s["slug"] in args.only]
    taxa_path = Path(args.taxa)
    taxa = json.loads(taxa_path.read_text(encoding="utf-8")) if taxa_path.exists() else {}
    out_path = state["seasons"]
    out = (json.loads(out_path.read_text(encoding="utf-8")) if (args.only or args.hours_only) and out_path.exists()
           else {"species": {}})
    out["source"] = f"iNaturalist research-grade {state['name']} observations (histogram by month and hour)"

    for s in species:
        tid = taxa[s["slug"]]["taxon_id"] if s["slug"] in taxa else resolve_taxon(s["scientific_name"])["id"]
        old = out["species"].get(s["slug"], {})
        months = old["months"] if args.hours_only and old.get("months") else histogram(tid, place, "month_of_year", 12, 1)
        hours = hours_of_day(tid, place, offset, date.today())
        out["species"][s["slug"]] = {"months": months, "hours": hours}
        print(f"{s['slug']}: {sum(months)} sightings, {sum(hours)} with a time")
    out_path.write_text(json.dumps(out), encoding="utf-8")
    print(f"wrote {out_path}")


if __name__ == "__main__":
    main()
