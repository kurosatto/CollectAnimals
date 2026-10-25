"""Download a test set of photos with NO animal in them, for the animal gate.

Three groups, each in its own folder under --out:
  plants_fungi/  iNaturalist research-grade plants and fungi from California
                 (the most likely "wrong" nature photo a player takes)
  people/        COCO val2017 photos dominated by a person (selfie-like),
                 no animal annotated anywhere in the photo
  scenes/        COCO val2017 photos with no person and no animal
                 (food, rooms, streets, vehicles, objects)

COCO images are CC-BY etc. per Flickr owner; this set is for evaluation only.

    python ml/fetch_nonanimal.py --out data/nonanimal --per-group 600
"""

from __future__ import annotations

import argparse
import io
import json
import random
import sys
import zipfile
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import requests

sys.path.insert(0, str(Path(__file__).parent))
import fetch_inat  # noqa: E402

COCO_ANN = "http://images.cocodataset.org/annotations/annotations_trainval2017.zip"
COCO_IMG = "http://images.cocodataset.org/val2017/{:012d}.jpg"
COCO_ANIMALS = set(range(16, 26))  # bird, cat, dog, horse, sheep, cow, elephant, bear, zebra, giraffe
COCO_PERSON = 1
PLANTAE, FUNGI = 47126, 47170


def coco_groups(cache: Path, n: int, seed: int):
    ann_path = cache / "instances_val2017.json"
    if not ann_path.exists():
        print("downloading COCO annotations (~240 MB)")
        blob = requests.get(COCO_ANN, timeout=600).content
        with zipfile.ZipFile(io.BytesIO(blob)) as z:
            ann_path.write_bytes(z.read("annotations/instances_val2017.json"))
    ann = json.loads(ann_path.read_text())
    sizes = {im["id"]: im["width"] * im["height"] for im in ann["images"]}
    cats, big_person = {}, {}
    for a in ann["annotations"]:
        cats.setdefault(a["image_id"], set()).add(a["category_id"])
        if a["category_id"] == COCO_PERSON:
            frac = a["area"] / sizes[a["image_id"]]
            big_person[a["image_id"]] = max(big_person.get(a["image_id"], 0), frac)
    no_animal = [i for i in sizes if not (cats.get(i, set()) & COCO_ANIMALS)]
    people = sorted(i for i in no_animal if big_person.get(i, 0) >= 0.25)
    scenes = sorted(i for i in no_animal if COCO_PERSON not in cats.get(i, set()) and i in cats)
    rng = random.Random(seed)
    return rng.sample(people, min(n, len(people))), rng.sample(scenes, min(n, len(scenes)))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="data/nonanimal")
    ap.add_argument("--per-group", type=int, default=600)
    ap.add_argument("--seed", type=int, default=0)
    args = ap.parse_args()
    out = Path(args.out)
    for g in ("plants_fungi", "people", "scenes"):
        (out / g).mkdir(parents=True, exist_ok=True)

    with ThreadPoolExecutor(8) as pool:
        people, scenes = coco_groups(out, args.per_group, args.seed)
        jobs = [pool.submit(fetch_inat.download, COCO_IMG.format(i), out / g / f"coco_{i}.jpg")
                for g, ids in (("people", people), ("scenes", scenes)) for i in ids]

        # Spread plants/fungi over the year like the "other" class.
        per_call = max(1, args.per_group // 24)
        for taxon in (PLANTAE, FUNGI):
            for month in range(1, 13):
                for obs in fetch_inat.iter_observations(per_call, taxon_id=taxon, month=month,
                                                        quality_grade="research"):
                    photo = obs["photos"][0]
                    jobs.append(pool.submit(fetch_inat.download, fetch_inat.photo_url(photo, "small"),
                                            out / "plants_fungi" / f"inat_{photo['id']}.jpg"))
        ok = sum(j.result() for j in jobs)
    print(f"{ok}/{len(jobs)} photos in {out}")


if __name__ == "__main__":
    main()
