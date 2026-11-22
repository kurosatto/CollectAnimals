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
    python ml/build_maps_gbif.py --only DEU FRA  # staged European countries too

A country (Europe, Singapore; staged ones in species/europe.json) is searched by
its country code instead of a US state name. draft_list_gbif() drafts a country's
100-species list the same way (ml/build_countries.py --gbif).
"""

from __future__ import annotations

import argparse
import csv
import json
import time
import unicodedata
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


# GBIF country codes for the countries (ISO alpha-2; Kosovo is XK).
ISO2 = {"ALB": "AL", "AUT": "AT", "BLR": "BY", "BEL": "BE", "BIH": "BA", "BGR": "BG", "HRV": "HR", "CYP": "CY",
        "CZE": "CZ", "DNK": "DK", "EST": "EE", "FIN": "FI", "FRA": "FR", "DEU": "DE", "GRC": "GR", "HUN": "HU",
        "ISL": "IS", "IRL": "IE", "ITA": "IT", "XKX": "XK", "LVA": "LV", "LTU": "LT", "LUX": "LU", "MLT": "MT",
        "MDA": "MD", "MNE": "ME", "NLD": "NL", "MKD": "MK", "NOR": "NO", "POL": "PL", "PRT": "PT", "ROU": "RO",
        "RUS": "RU", "SRB": "RS", "SVK": "SK", "SVN": "SI", "ESP": "ES", "SWE": "SE", "CHE": "CH", "TUR": "TR",
        "UKR": "UA", "GBR": "GB", "AND": "AD", "LIE": "LI", "MCO": "MC", "SMR": "SM", "VAT": "VA",
        # Asia
        "SGP": "SG"}


# iNaturalist names GBIF's backbone spells differently (an exact match either way).
GBIF_NAMES = {"Colias crocea": "Colias croceus"}
# The GBIF backbone has no Neogale vison: iNat's mink sightings sit on the genus
# Neogale, and in Europe and the US the only wild Neogale is the American mink.
GBIF_KEYS = {"Neogale vison": 4833733}


def taxon_key(sci):
    if sci in GBIF_KEYS:
        return GBIF_KEYS[sci]
    m = get("species/match", name=GBIF_NAMES.get(sci, sci), kingdom="Animalia", strict="true")
    # Only an exact name: a fuzzy or higher-rank match would map a different animal.
    return (m.get("acceptedUsageKey") or m.get("usageKey")) if m.get("matchType") == "EXACT" else None


def where(st):
    """GBIF filters for a state, or for a staged country by its code."""
    if st.get("region", "usa") != "usa":
        return dict(country=ISO2[st["code"]])
    return dict(country="US", stateProvince=st["name"])


def species_maps(sci, place, grid, per_species):
    key = taxon_key(sci)
    if key is None:
        return None, None
    common = dict(taxonKey=key, **place, datasetKey=INAT_DATASET,
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


# GBIF class/phylum -> the game's category, as iNaturalist's iconic taxa do it
# (build_states.CATEGORY). The GBIF backbone splits reptiles into Squamata,
# Testudines and Crocodylia and has no fish class: other chordates are fish.
GBIF_CATEGORY = {"Mammalia": "mammal", "Aves": "bird", "Squamata": "reptile", "Testudines": "reptile",
                 "Crocodylia": "reptile", "Amphibia": "amphibian", "Insecta": "invertebrate",
                 "Arachnida": "invertebrate", "Diplopoda": "invertebrate", "Chilopoda": "invertebrate"}
# Per-class searches so the small groups fill their quotas (the overall top
# 1,500 is mostly insects and birds).
GBIF_GROUPS = [dict(kingdomKey=1), dict(classKey=359), dict(classKey=11592253), dict(classKey=11418114),
               dict(classKey=11493978), dict(classKey=131), dict(phylumKey=44), dict(phylumKey=52)]


def gbif_category(t):
    if t.get("phylum") == "Mollusca":
        # land snails count as bugs; sea shells, slugs and octopuses as water animals
        return "invertebrate" if t.get("order") in ("Stylommatophora", "Systellommatophora") else "marine"
    if t.get("class") in GBIF_CATEGORY:
        return GBIF_CATEGORY[t["class"]]
    if t.get("phylum") == "Platyhelminthes" and t.get("family") == "Geoplanidae":
        return "invertebrate"  # land flatworms
    return "marine"


def english_name(key):
    """The English name most sources agree on (GBIF has no single preferred one)."""
    names, seen = {}, {}
    for v in get(f"species/{key}/vernacularNames", limit=300).get("results", []):
        if v.get("language") == "eng":
            n = v["vernacularName"].strip()
            names[n.lower()] = names.get(n.lower(), 0) + 1
            seen.setdefault(n.lower(), n)
    return seen[max(names, key=names.get)] if names else None


def draft_list_gbif(iso2, slugs, used, exclude, names=None, quota=None, rarity=None):
    """A country's 100 most-sighted wild species from GBIF's copy of iNaturalist
    research-grade sightings, per group up to the quota, then topped up by
    count, like build_states.draft_list. `names` (scientific -> English) wins
    over GBIF's names; species with no English name anywhere are skipped."""
    from build_states import QUOTA, RARITY, slugify
    quota, rarity, names = quota or QUOTA, rarity or RARITY, names or {}
    known_names = {r["slug"]: r["common_name"] for f in SPECIES.glob("*_100.csv")
                   for r in csv.DictReader(open(f, encoding="utf-8"))}
    counts = {}
    for g in GBIF_GROUPS:
        fac = get("occurrence/search", country=iso2, datasetKey=INAT_DATASET, limit=0, facet="speciesKey",
                  facetLimit=1500 if "kingdomKey" in g else 300, **g)
        for f in fac.get("facets", []):
            for c in f["counts"]:
                counts[int(c["name"])] = c["count"]
    pools = {}
    with ThreadPoolExecutor(6) as pool:
        taxa = list(pool.map(lambda k: get(f"species/{k}"), counts))
    for t in taxa:
        sci = t.get("canonicalName") or ""
        if t.get("rank") != "SPECIES" or sci in exclude or sci.split()[0] in exclude:
            continue
        pools.setdefault(gbif_category(t), []).append({"key": t["key"], "sci": sci, "count": counts[t["key"]]})
    for cat in pools:
        pools[cat].sort(key=lambda r: -r["count"])
    picked, seen = [], set()

    def take(r, cat):
        if r["key"] in seen:
            return
        common = names.get(r["sci"]) or english_name(r["key"])
        if common:
            seen.add(r["key"]); picked.append((r, cat, common))

    for cat, n in quota.items():
        for r in pools.get(cat, []):
            if sum(1 for _, c, _ in picked if c == cat) >= n:
                break
            take(r, cat)
    rest = sorted(((r, c) for c, rs in pools.items() for r in rs), key=lambda x: -x[0]["count"])
    for r, cat in rest:
        if len(picked) >= 100:
            break
        take(r, cat)
    picked.sort(key=lambda x: -x[0]["count"])
    rows = []
    for r, cat, common in picked[:100]:
        sci = r["sci"]
        slug = slugs.get(sci.lower())
        if slug and slug in known_names:  # one name per species across every list
            common = known_names[slug]
        if not slug:
            slug = slugify(unicodedata.normalize("NFKD", common).encode("ascii", "ignore").decode())
            if used.get(slug, sci) != sci:  # same English name, different species
                slug = slugify(f"{common} {sci.split()[0]}")
        used[slug] = sci
        slugs[sci.lower()] = slug
        rows.append({"slug": slug, "common_name": common[0].upper() + common[1:], "scientific_name": sci,
                     "category": cat, "gbif_key": r["key"], "count": r["count"]})
    for row, rar in zip(rows, rarity):
        row["rarity"] = rar
    return rows


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--only", nargs="*", help="state codes")
    ap.add_argument("--per-species", type=int, default=600, help="sightings to place on the map")
    ap.add_argument("--workers", type=int, default=4)
    args = ap.parse_args()
    sj = json.loads((SPECIES / "states.json").read_text(encoding="utf-8"))
    staged = SPECIES / "europe.json"
    states = sj["states"] + (json.loads(staged.read_text(encoding="utf-8"))["states"]
                             if args.only and staged.exists() else [])
    for st in states:
        if args.only and st["code"] not in args.only:
            continue
        rpath, spath = SPECIES / st["ranges"], SPECIES / st["seasons"]
        if not args.only and rpath.exists() and spath.exists():
            continue
        rows = list(csv.DictReader(open(SPECIES / st["species"], encoding="utf-8")))
        with ThreadPoolExecutor(args.workers) as pool:
            results = list(pool.map(lambda r: species_maps(r["scientific_name"], where(st), st["grid"],
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
