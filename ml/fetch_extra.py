"""Training photos for the model-only animals in species/model_extras.csv (the
animals that bring each state to about 200, before they have entries or art).

Research-grade iNaturalist photos from anywhere in the US, up to --per a class,
into the same folder and attribution.csv as fetch_inat.py:

    python ml/fetch_extra.py --out D:/data/images_all --per 1000
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import requests

sys.path.insert(0, str(Path(__file__).parent))
import fetch_inat as fi  # noqa: E402

SPECIES = Path(__file__).resolve().parents[1] / "species"


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--out", default="data/images")
    ap.add_argument("--per", type=int, default=1000, help="photos per animal")
    args = ap.parse_args()
    out = Path(args.out)
    fi.session.mount("https://", requests.adapters.HTTPAdapter(pool_maxsize=6))
    taxa_path = out / "taxa.json"
    taxa = json.loads(taxa_path.read_text(encoding="utf-8")) if taxa_path.exists() else {}
    rows = list(csv.DictReader(open(SPECIES / "model_extras.csv", encoding="utf-8")))
    with open(out / "attribution.csv", "a", newline="", encoding="utf-8") as fh, ThreadPoolExecutor(6) as pool:
        att = csv.writer(fh)
        for r in rows:
            slug = r["slug"]
            d = out / slug
            if d.is_dir() and len(list(d.glob("*.jpg"))) >= args.per:
                continue
            try:
                if slug not in taxa:
                    t = fi.resolve_taxon(r["scientific_name"])
                    taxa[slug] = {"taxon_id": t["id"], "name": t["name"],
                                  "observations_count": t.get("observations_count")}
                    taxa_path.write_text(json.dumps(taxa, indent=2), encoding="utf-8")
                print(slug, flush=True)
                fi.fetch_class(slug, out, args.per, "small", pool, att, target=args.per, place_id=fi.US_PLACE_ID,
                               taxon_id=taxa[slug]["taxon_id"], quality_grade="research")
            except Exception as e:  # one failed animal shouldn't stop the rest
                print(f"  failed {slug}: {e}", flush=True)
            fh.flush()


if __name__ == "__main__":
    main()
