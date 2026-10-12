"""Find which listed species can be spotted at well-known California parks.

For each park in PARKS (a centre point and a radius), asks iNaturalist how many
research-grade observations of each of our species fall within the radius, and
writes species/hotspots.json:

    {"source": "...", "min_observations": 3,
     "parks": [{"id": "pinnacles", "name": "Pinnacles National Park", "lat": 36.49,
                "lon": -121.18, "radius_km": 10, "blurb": "...",
                "species": [{"slug": "california_condor", "observations": 812}, ...]}]}

A species is listed for a park once it has at least --min-observations there,
most-observed first. One API call per park (~30 s for the whole list).

Usage:
    python ml/build_hotspots.py
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from fetch_inat import api_get, resolve_taxon  # noqa: E402

# id, name, lat, lon, radius_km, blurb
PARKS = [
    ("point_reyes", "Point Reyes National Seashore", 38.07, -122.88, 18,
     "Tule elk, seals, bobcats and huge flocks of shorebirds on wild coastal bluffs."),
    ("marin_headlands", "Marin Headlands", 37.83, -122.51, 6,
     "Hawk Hill's fall raptor migration, coyotes and harbor seals right by the Golden Gate."),
    ("muir_woods_tam", "Muir Woods & Mount Tamalpais", 37.91, -122.58, 7,
     "Old-growth redwoods with banana slugs, newts and Steller's jays."),
    ("golden_gate_park", "Golden Gate Park & Presidio", 37.78, -122.47, 4,
     "City nature: coyotes, hawks, hummingbirds and herons without leaving San Francisco."),
    ("mount_diablo", "Mount Diablo State Park", 37.88, -121.91, 9,
     "Oak woodland and chaparral full of lizards, raptors, tarantulas and acorn woodpeckers."),
    ("big_basin", "Big Basin Redwoods", 37.17, -122.22, 8,
     "California's oldest state park, with redwoods, salamanders and banana slugs."),
    ("elkhorn_slough", "Elkhorn Slough & Moss Landing", 36.82, -121.76, 6,
     "Sea otters, harbor seals, pelicans and herons in a calm coastal estuary."),
    ("monterey_point_lobos", "Monterey & Point Lobos", 36.56, -121.93, 8,
     "Tide pools, kelp forests, sea otters and sea lions along a rocky coast."),
    ("pinnacles", "Pinnacles National Park", 36.49, -121.18, 10,
     "Volcanic spires where California condors soar, plus bats, lizards and raptors."),
    ("big_sur", "Big Sur Coast", 36.24, -121.78, 15,
     "Condors, whales and sea otters along one of the world's most dramatic coastlines."),
    ("yosemite_valley", "Yosemite Valley", 37.74, -119.59, 8,
     "Black bears, mule deer, Steller's jays and western gray squirrels under granite cliffs."),
    ("tuolumne_tioga", "Tuolumne Meadows & Tioga Pass", 37.88, -119.33, 10,
     "High Sierra meadows with marmots, pikas and Belding's ground squirrels."),
    ("sequoia", "Sequoia National Park", 36.56, -118.77, 12,
     "Giant sequoias, black bears and mountain wildlife."),
    ("lake_tahoe", "Lake Tahoe (California shore)", 38.95, -120.07, 12,
     "Alpine lake with ospreys, bald eagles, bears and Steller's jays."),
    ("prairie_creek", "Prairie Creek Redwoods", 41.36, -124.02, 10,
     "Roosevelt elk grazing in meadows beside towering redwoods."),
    ("sacramento_nwr", "Sacramento National Wildlife Refuge", 39.43, -122.18, 8,
     "Winter home of huge flocks of geese, ducks, egrets and bald eagles."),
    ("carrizo_plain", "Carrizo Plain National Monument", 35.19, -119.79, 25,
     "Wide-open grassland with pronghorn, kestrels, golden eagles and spring wildflowers."),
    ("santa_monica_mtns", "Santa Monica Mountains", 34.09, -118.83, 15,
     "Chaparral canyons with bobcats, rattlesnakes, newts and roadrunners near Los Angeles."),
    ("griffith_park", "Griffith Park", 34.13, -118.29, 5,
     "LA's big urban park, home to coyotes, hawks, lizards and the famous mountain lion P-22."),
    ("bolsa_chica", "Bolsa Chica Ecological Reserve", 33.70, -118.04, 4,
     "Southern California wetland packed with herons, egrets, pelicans and shorebirds."),
    ("la_jolla", "La Jolla Cove & Torrey Pines", 32.87, -117.25, 6,
     "Sea lions, seals, garibaldi and leopard sharks, plus coastal sage scrub trails."),
    ("anza_borrego", "Anza-Borrego Desert State Park", 33.26, -116.40, 30,
     "Bighorn sheep, roadrunners, desert iguanas and spring wildflower blooms."),
    ("joshua_tree", "Joshua Tree National Park", 33.92, -115.93, 30,
     "Desert lizards, jackrabbits, roadrunners and ravens among Joshua trees."),
    ("mono_lake", "Mono Lake", 38.00, -119.03, 12,
     "Salty lake with tufa towers, gulls, and sagebrush wildlife on the Sierra's east side."),
]


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--species", default="species/california_100.csv")
    ap.add_argument("--taxa", default="data/images/taxa.json",
                    help="taxon ids cached by fetch_inat.py (resolved from the API if missing)")
    ap.add_argument("--out", default="species/hotspots.json")
    ap.add_argument("--min-observations", type=int, default=3)
    args = ap.parse_args()

    species = list(csv.DictReader(open(args.species, encoding="utf-8")))
    taxa_path = Path(args.taxa)
    taxa = json.loads(taxa_path.read_text(encoding="utf-8")) if taxa_path.exists() else {}
    slug_by_taxon = {}
    for s in species:
        tid = taxa[s["slug"]]["taxon_id"] if s["slug"] in taxa else resolve_taxon(s["scientific_name"])["id"]
        slug_by_taxon[tid] = s["slug"]
    taxon_ids = ",".join(str(t) for t in slug_by_taxon)

    parks = []
    for pid, name, lat, lon, radius, blurb in PARKS:
        data = api_get("/observations/species_counts", lat=lat, lng=lon, radius=radius,
                       taxon_id=taxon_ids, quality_grade="research", per_page=500)
        counts = {}
        for r in data["results"]:
            taxon = r["taxon"]
            # Counts come back per species; map renamed/merged taxa back via ancestors.
            ids = [taxon["id"], *taxon.get("ancestor_ids", [])]
            slug = next((slug_by_taxon[i] for i in ids if i in slug_by_taxon), None)
            if slug:
                counts[slug] = counts.get(slug, 0) + r["count"]
        listed = sorted(((s, n) for s, n in counts.items() if n >= args.min_observations),
                        key=lambda kv: -kv[1])
        print(f"{name}: {len(listed)} species")
        parks.append({"id": pid, "name": name, "lat": lat, "lon": lon, "radius_km": radius,
                      "blurb": blurb,
                      "species": [{"slug": s, "observations": n} for s, n in listed]})

    out = {"source": "iNaturalist research-grade observations (species_counts by radius)",
           "min_observations": args.min_observations, "parks": parks}
    Path(args.out).write_text(json.dumps(out, indent=1), encoding="utf-8")
    print(f"wrote {args.out}")


if __name__ == "__main__":
    main()
