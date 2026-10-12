"""Classify images with a trained checkpoint (handy for sanity-checking a model).

    python ml/predict.py models/ca100.pt photo1.jpg photo2.jpg
"""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))

from PIL import Image  # noqa: E402

from app.classifier import TorchClassifier  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("checkpoint")
    ap.add_argument("images", nargs="+")
    ap.add_argument("-k", type=int, default=3)
    args = ap.parse_args()
    clf = TorchClassifier(args.checkpoint)
    for path in args.images:
        with Image.open(path) as im:
            preds = clf.predict(im.convert("RGB"), k=args.k)
        print(path)
        for p in preds:
            print(f"  {p.label:32s} {p.probability:.3f}")


if __name__ == "__main__":
    main()
