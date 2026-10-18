"""Download photos for the pets-and-pests classes (species/pets.csv).

People photograph their dog or a pigeon too. These animals get their own model
classes so the game can say "that's a dog" instead of forcing a wild species,
but they are on no state's list and earn no badges. Unlike wild animals,
iNaturalist marks most pet photos "casual" (captive / cultivated), so this
pulls casual and research-grade photos from anywhere in the US.

    python ml/fetch_pets.py --out D:/data/images_all
"""

from __future__ import annotations

import argparse
import csv
import json
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import requests

import fetch_inat as fi

PETS_CSV = Path(__file__).resolve().parents[1] / "species" / "pets.csv"


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--out", default="data/images")
    ap.add_argument("--per-species", type=int, default=1000)
    ap.add_argument("--size", default="small", choices=["small", "medium", "large"])
    ap.add_argument("--workers", type=int, default=8)
    args = ap.parse_args()
    fi.session.mount("https://", requests.adapters.HTTPAdapter(pool_maxsize=args.workers))
    out = Path(args.out)
    taxa_path = out / "taxa.json"
    taxa = json.loads(taxa_path.read_text(encoding="utf-8")) if taxa_path.exists() else {}
    rows = list(csv.DictReader(open(PETS_CSV, encoding="utf-8")))
    with open(out / "attribution.csv", "a", newline="", encoding="utf-8") as fh, \
            ThreadPoolExecutor(args.workers) as pool:
        attribution = csv.writer(fh)
        for r in rows:
            slug = r["slug"]
            if slug not in taxa:
                t = fi.resolve_taxon(r["scientific_name"])
                taxa[slug] = {"taxon_id": t["id"], "name": t["name"], "observations_count": t.get("observations_count")}
                taxa_path.write_text(json.dumps(taxa, indent=2), encoding="utf-8")
            on_disk = len(list((out / slug).glob("*.jpg")))
            if on_disk >= args.per_species:
                print(f"{slug}: {on_disk} on disk, skipping")
                continue
            print(f"{slug} ({taxa[slug]['name']})")
            fi.fetch_class(slug, out, 3 * args.per_species, args.size, pool, attribution, target=args.per_species,
                           place_id=fi.US_PLACE_ID, taxon_id=taxa[slug]["taxon_id"],
                           quality_grade="casual,research", hrank="species")
            fh.flush()


if __name__ == "__main__":
    main()
