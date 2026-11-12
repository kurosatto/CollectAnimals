"""Draft species lists and entries for the European countries (plus Turkey).

In Europe a country plays the part a US state plays: its own 100-species list,
outline, map grid, towns, ranges, parks and seasons. This script does for each
country what ml/build_states.py does for a state (same group quotas, rarities
and slug reuse, so a red fox is one model class from Portugal to Finland) and
writes the entries to species/europe.json, a staging file. Nothing in it is
playable until the entries are moved into species/states.json, which happens
once the model knows the new species and their sprites exist.

Codes are ISO 3166 alpha-3 (GBR, DEU, FRA): two-letter codes would clash with
US states (DE Delaware/Germany, AL, MD, ME, MT, VA).

Outlines come from Natural Earth 1:10m admin-0 (public domain; Ukraine and
Russia from its Ukraine point-of-view file, so Crimea is Ukrainian), clipped to
Europe (overseas parts such as French Guiana, the Canaries, Madeira, the Azores
and Svalbard are dropped; Russia is cut at the Urals, 60 E). European Russia's
species list uses that box instead of the whole-country place.

    python ml/build_countries.py                 # every missing country
    python ml/build_countries.py --only DEU FRA  # just these
    python ml/build_countries.py --list          # print the country table

Then, per country (or with --state for each code):
    python ml/build_ranges.py --state DEU
    python ml/build_hotspots.py --state DEU      # parks per country are in species/parks.json
    python ml/build_seasons.py --state DEU
"""

from __future__ import annotations

import argparse
import csv
import json

from build_states import SPECIES, api, draft_list, grid_for, known_slugs, session

NE = "https://raw.githubusercontent.com/nvkelso/natural-earth-vector/master/geojson/"
COUNTRIES_GEO = NE + "ne_10m_admin_0_countries.geojson"
# Natural Earth's default file draws Crimea as Russian (de facto lines). Ukraine
# and Russia come from its Ukraine point-of-view file, which follows the
# internationally recognized border.
UKR_VIEW_GEO = NE + "ne_10m_admin_0_countries_ukr.geojson"
UKR_VIEW = {"UKR", "RUS"}
TOWNS_GEO = NE + "ne_10m_populated_places_simple.geojson"
STAGING = SPECIES / "europe.json"
# Europe box: west of Iceland's tip, south of Cyprus and Crete, north of
# mainland Norway, east to the Urals.
BOX = (-24.6, 34.0, 60.0, 71.5)
RUSSIA_BOX = {"swlat": 41.0, "swlng": 19.0, "nelat": 70.0, "nelng": 60.0}
MIN_SPECIES = 60  # fewer research-grade species than this: report, don't stage

# Countries under 100,000 people (Andorra, Liechtenstein, Monaco, San Marino,
# Vatican City) are left out on purpose.
# code, name, other names iNaturalist may use, Natural Earth ADM0_A3, UTC offset (winter), daylight time
COUNTRIES = [
    ("ALB", "Albania", [], "ALB", 1, "eu"),
    ("AUT", "Austria", [], "AUT", 1, "eu"),
    ("BLR", "Belarus", [], "BLR", 3, "none"),
    ("BEL", "Belgium", [], "BEL", 1, "eu"),
    ("BIH", "Bosnia and Herzegovina", ["Bosnia & Herzegovina"], "BIH", 1, "eu"),
    ("BGR", "Bulgaria", [], "BGR", 2, "eu"),
    ("HRV", "Croatia", [], "HRV", 1, "eu"),
    ("CYP", "Cyprus", [], "CYP", 2, "eu"),
    ("CZE", "Czechia", ["Czech Republic"], "CZE", 1, "eu"),
    ("DNK", "Denmark", [], "DNK", 1, "eu"),
    ("EST", "Estonia", [], "EST", 2, "eu"),
    ("FIN", "Finland", [], "FIN", 2, "eu"),
    ("FRA", "France", [], "FRA", 1, "eu"),
    ("DEU", "Germany", [], "DEU", 1, "eu"),
    ("GRC", "Greece", [], "GRC", 2, "eu"),
    ("HUN", "Hungary", [], "HUN", 1, "eu"),
    ("ISL", "Iceland", [], "ISL", 0, "none"),
    ("IRL", "Ireland", [], "IRL", 0, "eu"),
    ("ITA", "Italy", [], "ITA", 1, "eu"),
    ("XKX", "Kosovo", [], "KOS", 1, "eu"),
    ("LVA", "Latvia", [], "LVA", 2, "eu"),
    ("LTU", "Lithuania", [], "LTU", 2, "eu"),
    ("LUX", "Luxembourg", [], "LUX", 1, "eu"),
    ("MLT", "Malta", [], "MLT", 1, "eu"),
    ("MDA", "Moldova", ["Republic of Moldova"], "MDA", 2, "eu"),
    ("MNE", "Montenegro", [], "MNE", 1, "eu"),
    ("NLD", "Netherlands", ["The Netherlands"], "NLD", 1, "eu"),
    ("MKD", "North Macedonia", ["Macedonia"], "MKD", 1, "eu"),
    ("NOR", "Norway", [], "NOR", 1, "eu"),
    ("POL", "Poland", [], "POL", 1, "eu"),
    ("PRT", "Portugal", [], "PRT", 0, "eu"),
    ("ROU", "Romania", [], "ROU", 2, "eu"),
    ("RUS", "Russia", ["Russian Federation"], "RUS", 3, "none"),
    ("SRB", "Serbia", [], "SRB", 1, "eu"),
    ("SVK", "Slovakia", [], "SVK", 1, "eu"),
    ("SVN", "Slovenia", [], "SVN", 1, "eu"),
    ("ESP", "Spain", [], "ESP", 1, "eu"),
    ("SWE", "Sweden", [], "SWE", 1, "eu"),
    ("CHE", "Switzerland", [], "CHE", 1, "eu"),
    ("TUR", "Turkey", ["Türkiye", "Turkiye"], "TUR", 3, "none"),
    ("UKR", "Ukraine", [], "UKR", 2, "eu"),
    ("GBR", "United Kingdom", ["UK", "Great Britain"], "GBR", 0, "eu"),
]


def country_place_id(name, alts):
    names = {n.lower() for n in [name, *alts]}
    for q in [name, *alts]:
        for p in api("places/autocomplete", q=q, per_page=20)["results"]:
            if p.get("admin_level") == 0 and p["name"].lower() in names:
                return p["id"]
    return None


def clip_ring(ring, box=BOX):
    """Sutherland-Hodgman: a polygon ring cut to the box (no shapely needed)."""
    west, south, east, north = box
    edges = [(lambda p: p[0] >= west, lambda a, b: _cross_x(a, b, west)),
             (lambda p: p[0] <= east, lambda a, b: _cross_x(a, b, east)),
             (lambda p: p[1] >= south, lambda a, b: _cross_y(a, b, south)),
             (lambda p: p[1] <= north, lambda a, b: _cross_y(a, b, north))]
    pts = ring[:-1] if ring and ring[0] == ring[-1] else list(ring)
    for inside, cross in edges:
        if not pts:
            break
        out = []
        for i, cur in enumerate(pts):
            prev = pts[i - 1]
            if inside(cur):
                if not inside(prev):
                    out.append(cross(prev, cur))
                out.append(cur)
            elif inside(prev):
                out.append(cross(prev, cur))
        pts = out
    if len(pts) < 3:
        return None
    return [[round(x, 4), round(y, 4)] for x, y in pts + [pts[0]]]


def _cross_x(a, b, x):
    t = (x - a[0]) / (b[0] - a[0])
    return [x, a[1] + t * (b[1] - a[1])]


def _cross_y(a, b, y):
    t = (y - a[1]) / (b[1] - a[1])
    return [a[0] + t * (b[0] - a[0]), y]


def ring_area(r):
    return abs(sum(x0 * y1 - x1 * y0 for (x0, y0), (x1, y1) in zip(r, r[1:]))) / 2


def outline_rings(geo, a3):
    f = next(f for f in geo["features"] if f["properties"].get("ADM0_A3") == a3)
    g = f["geometry"]
    polys = g["coordinates"] if g["type"] == "MultiPolygon" else [g["coordinates"]]
    rings = [r for p in polys if (r := clip_ring(p[0]))]
    if a3 == "NOR":  # Jan Mayen, far out in the Atlantic
        rings = [r for r in rings if min(x for x, _ in r) > 0]
    # Drop specks (rocks and tiny islets) that would only clutter the map,
    # but never a microstate's only ring.
    big = max(ring_area(r) for r in rings)
    return [r for r in rings if ring_area(r) >= big * 0.0005]


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--only", nargs="*", help="country codes (ISO alpha-3)")
    ap.add_argument("--redo", action="store_true", help="rebuild countries already staged")
    ap.add_argument("--list", action="store_true", help="print the countries and stop")
    ap.add_argument("--place", nargs="*", default=[], metavar="CODE=ID",
                    help="iNaturalist place id for a country the name lookup misses")
    args = ap.parse_args()
    if args.list:
        for c in COUNTRIES:
            print(c[0], c[1], f"UTC{c[4]:+d}", c[5])
        return
    only = {c.upper() for c in args.only or []}
    forced = {k.upper(): int(v) for k, v in (p.split("=") for p in args.place)}
    staged = json.loads(STAGING.read_text(encoding="utf-8")) if STAGING.exists() else {
        "note": "Countries drafted by ml/build_countries.py. Not playable until moved into states.json.",
        "states": []}
    if args.redo:
        staged["states"] = [s for s in staged["states"] if only and s["code"] not in only]
    have = {s["code"] for s in staged["states"]}
    todo = [c for c in COUNTRIES if c[0] not in have and (not only or c[0] in only)]
    geo = session.get(COUNTRIES_GEO, timeout=300).json()
    ukr_geo = session.get(UKR_VIEW_GEO, timeout=300).json() if any(c[0] in UKR_VIEW for c in todo) else None
    towns_geo = session.get(TOWNS_GEO, timeout=300).json()
    slugs = known_slugs()
    used = {v: k for k, v in slugs.items()}
    skipped = []
    for code, name, alts, a3, utc, dst in todo:
        stem = name.lower().replace(" ", "_")
        pid = forced.get(code) or country_place_id(name, alts)
        if not pid:
            skipped.append(f"{code} {name}: no iNaturalist place (pass --place {code}=<id>)")
            continue
        rows = draft_list(pid, slugs, used, where=RUSSIA_BOX if code == "RUS" else None)
        if len(rows) < MIN_SPECIES:
            skipped.append(f"{code} {name}: only {len(rows)} species with enough sightings")
            continue
        with open(SPECIES / f"{stem}_100.csv", "w", newline="", encoding="utf-8") as fh:
            w = csv.writer(fh)
            w.writerow(["slug", "common_name", "scientific_name", "category", "rarity"])
            for r in rows:
                w.writerow([r["slug"], r["common_name"], r["scientific_name"], r["category"], r["rarity"]])
        rings = outline_rings(ukr_geo if code in UKR_VIEW else geo, a3)
        (SPECIES / f"{stem}_outline.json").write_text(json.dumps(
            {"source": "Natural Earth 1:10m admin-0 (public domain), clipped to Europe", "rings": rings}),
            encoding="utf-8")
        xs = [x for r in rings for x, _ in r]; ys = [y for r in rings for _, y in r]
        bounds = {"west": round(min(xs) - 0.1, 1), "east": round(max(xs) + 0.1, 1),
                  "south": round(min(ys) - 0.1, 1), "north": round(max(ys) + 0.1, 1)}
        towns = sorted(([p["properties"]["name"], round(p["geometry"]["coordinates"][1], 2),
                         round(p["geometry"]["coordinates"][0], 2), p["properties"].get("pop_max") or 0]
                        for p in towns_geo["features"]
                        if p["properties"].get("adm0_a3") == a3
                        and bounds["west"] <= p["geometry"]["coordinates"][0] <= bounds["east"]
                        and bounds["south"] <= p["geometry"]["coordinates"][1] <= bounds["north"]),
                       key=lambda t: -t[3])
        (SPECIES / f"{stem}_places.json").write_text(json.dumps(
            {"note": f"Towns used to describe roughly where a capture happened in {name} (\"near ...\"). "
                     "From Natural Earth populated places (public domain).",
             "towns": [t[:3] for t in towns]}), encoding="utf-8")
        staged["states"] = [s for s in staged["states"] if s["code"] != code]
        staged["states"].append({
            "code": code, "name": name, "region": "europe", "species": f"{stem}_100.csv", "dex": None,
            "outline": f"{stem}_outline.json", "ranges": f"{stem}_ranges.json",
            "hotspots": f"{stem}_hotspots.json", "places": f"{stem}_places.json",
            "seasons": f"{stem}_seasons.json", "utc_offset": utc, "dst": dst, "inat_place_id": pid,
            "bounds": bounds, "grid": grid_for(bounds)})
        staged["states"].sort(key=lambda s: s["name"])
        STAGING.write_text(json.dumps(staged, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
        cats = {}
        for r in rows:
            cats[r["category"]] = cats.get(r["category"], 0) + 1
        print(f"{code} {name}: {len(rows)} species {cats}, {len(rings)} outline parts, {len(towns)} towns",
              flush=True)
    for s in skipped:
        print("SKIPPED", s)


if __name__ == "__main__":
    main()
