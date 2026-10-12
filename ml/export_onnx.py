"""Export a trained checkpoint to ONNX for the Android app (on-device inference).

Writes two files into the app's assets folder:
    model.onnx      the network, with softmax folded in (input: 1x3xSxS float, output: 1xC probs)
    model.json      class list, preprocessing config, match threshold, and species metadata

    python ml/export_onnx.py models/ca100.pt --out android/app/src/main/assets

--quantize stores weights as int8 (about 4x smaller) via ONNX Runtime dynamic
quantization. The script then checks the exported model against PyTorch on a
few validation photos and reports top-1 agreement, so you can see what (if
anything) quantization costs before shipping it.
"""

from __future__ import annotations

import argparse
import csv
import json
import random
from pathlib import Path

import numpy as np
import timm
import torch
from PIL import Image
from torch import nn
from torchvision import transforms


class WithSoftmax(nn.Module):
    def __init__(self, model):
        super().__init__()
        self.model = model

    def forward(self, x):
        return self.model(x).softmax(-1)


def load_species(csv_path: Path) -> dict:
    with open(csv_path, newline="", encoding="utf-8") as fh:
        return {r["slug"]: {k: r[k] for k in ("common_name", "scientific_name", "category", "rarity")}
                for r in csv.DictReader(fh)}


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("checkpoint")
    ap.add_argument("--out", default="android/app/src/main/assets")
    ap.add_argument("--species", default="species/california_100.csv")
    ap.add_argument("--threshold", type=float, default=0.7,
                    help="confidence needed to award a badge (backend default MATCH_THRESHOLD)")
    ap.add_argument("--quantize", action="store_true", help="int8 weights (smaller APK)")
    ap.add_argument("--check-data", default="data/images",
                    help="photos to compare ONNX vs PyTorch on (skipped if missing)")
    ap.add_argument("--check-n", type=int, default=300)
    args = ap.parse_args()

    ckpt = torch.load(args.checkpoint, map_location="cpu", weights_only=False)
    classes = ckpt["classes"]
    model = timm.create_model(ckpt["model_name"], pretrained=False, num_classes=len(classes))
    model.load_state_dict(ckpt["state_dict"])
    model = WithSoftmax(model).eval()
    size = ckpt["img_size"]

    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    onnx_path = out / "model.onnx"
    fp32_path = out / "model.fp32.onnx" if args.quantize else onnx_path
    torch.onnx.export(model, torch.zeros(1, 3, size, size), fp32_path,
                      input_names=["image"], output_names=["probs"], opset_version=17, dynamo=False)
    if args.quantize:
        from onnxruntime.quantization import QuantType, quantize_dynamic
        quantize_dynamic(str(fp32_path), str(onnx_path), weight_type=QuantType.QUInt8)
    print(f"wrote {onnx_path} ({onnx_path.stat().st_size / 1e6:.1f} MB)")

    species = load_species(Path(args.species))
    meta = {
        "model_name": ckpt["model_name"],
        "classes": classes,
        "img_size": size,
        "resize": int(size / 0.875),  # shorter side, then center crop (same as training eval)
        "mean": list(ckpt["mean"]),
        "std": list(ckpt["std"]),
        "match_threshold": args.threshold,
        "other_label": "other",
        "species": [{"slug": s, **species[s]} for s in species],  # CSV order
        "val_top1": ckpt.get("val_top1"),
    }
    (out / "model.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")
    print(f"wrote {out / 'model.json'}")

    check = Path(args.check_data)
    if check.is_dir():
        import onnxruntime as ort
        tf = transforms.Compose([transforms.Resize(meta["resize"]), transforms.CenterCrop(size),
                                 transforms.ToTensor(), transforms.Normalize(meta["mean"], meta["std"])])
        paths = sorted(check.glob("*/*.jpg"))
        random.Random(0).shuffle(paths)
        sess = {"onnx": ort.InferenceSession(str(onnx_path))}
        if args.quantize:
            sess["onnx_fp32"] = ort.InferenceSession(str(fp32_path))
        agree = {k: 0 for k in sess}
        max_diff = {k: 0.0 for k in sess}
        for p in paths[:args.check_n]:
            with Image.open(p) as im:
                x = tf(im.convert("RGB")).unsqueeze(0)
            with torch.inference_mode():
                ref = model(x)[0].numpy()
            for k, s in sess.items():
                got = s.run(None, {"image": x.numpy()})[0][0]
                agree[k] += int(got.argmax() == ref.argmax())
                max_diff[k] = max(max_diff[k], float(np.abs(got - ref).max()))
        n = min(args.check_n, len(paths))
        for k in sess:
            print(f"{k} vs pytorch on {n} photos: top-1 agreement {agree[k] / n:.3f}, "
                  f"max prob diff {max_diff[k]:.4f}")
        if args.quantize:
            fp32_path.unlink()


if __name__ == "__main__":
    main()
