"""Fine-tune an ImageNet-pretrained backbone on the downloaded species photos.

Expects the layout produced by fetch_inat.py:
    data/images/<class_slug>/*.jpg     (100 species + "other")

Writes a single checkpoint (weights + class list + preprocessing config) that
the backend loads directly:
    python ml/train.py --data data/images --out models/ca100.pt

Any timm model name works. Good starting points:
  convnext_tiny.fb_in22k_ft_in1k     (default; fast, strong)
  efficientnet_b0.ra_in1k            (smallest / CPU-friendly)
  convnext_base.fb_in22k_ft_in1k_384 (more accurate, needs a bigger GPU)
"""

from __future__ import annotations

import argparse
import json
import random
import time
from collections import Counter
from pathlib import Path

import timm
import torch
from PIL import Image
from timm.data import resolve_data_config
from torch import nn
from torch.utils.data import DataLoader, Dataset
from torchvision import transforms

IMG_EXTS = {".jpg", ".jpeg", ".png", ".webp"}


class ImageList(Dataset):
    def __init__(self, items, transform):
        self.items = items
        self.transform = transform

    def __len__(self):
        return len(self.items)

    def __getitem__(self, i):
        path, label = self.items[i]
        with Image.open(path) as im:
            return self.transform(im.convert("RGB")), label


def split_dataset(root: Path, val_frac: float, seed: int):
    classes = sorted(d.name for d in root.iterdir() if d.is_dir())
    rng = random.Random(seed)
    train, val = [], []
    for idx, cls in enumerate(classes):
        files = sorted(p for p in (root / cls).iterdir() if p.suffix.lower() in IMG_EXTS)
        rng.shuffle(files)
        n_val = max(1, int(len(files) * val_frac))
        val += [(p, idx) for p in files[:n_val]]
        train += [(p, idx) for p in files[n_val:]]
    return classes, train, val


def build_transforms(cfg, img_size):
    mean, std = cfg["mean"], cfg["std"]
    train_tf = transforms.Compose([
        transforms.RandomResizedCrop(img_size, scale=(0.35, 1.0)),
        transforms.RandomHorizontalFlip(),
        transforms.ColorJitter(0.3, 0.3, 0.2, 0.02),
        transforms.ToTensor(),
        transforms.Normalize(mean, std),
    ])
    eval_tf = transforms.Compose([
        transforms.Resize(int(img_size / 0.875)),
        transforms.CenterCrop(img_size),
        transforms.ToTensor(),
        transforms.Normalize(mean, std),
    ])
    return train_tf, eval_tf


@torch.no_grad()
def evaluate(model, loader, device, num_classes):
    model.eval()
    correct = total = top5 = 0
    per_class = Counter()
    per_class_total = Counter()
    for x, y in loader:
        x, y = x.to(device), y.to(device)
        with torch.autocast(device.type, enabled=device.type == "cuda"):
            logits = model(x)
        pred5 = logits.topk(min(5, num_classes), dim=1).indices
        hit1 = pred5[:, 0] == y
        correct += hit1.sum().item()
        top5 += (pred5 == y[:, None]).any(1).sum().item()
        total += y.numel()
        for label, hit in zip(y.tolist(), hit1.tolist()):
            per_class_total[label] += 1
            per_class[label] += hit
    acc = {c: per_class[c] / per_class_total[c] for c in per_class_total}
    return correct / total, top5 / total, acc


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--data", default="data/images")
    ap.add_argument("--out", default="models/ca100.pt")
    ap.add_argument("--model", default="convnext_tiny.fb_in22k_ft_in1k")
    ap.add_argument("--img-size", type=int, default=224)
    ap.add_argument("--epochs", type=int, default=12)
    ap.add_argument("--batch-size", type=int, default=64)
    ap.add_argument("--lr", type=float, default=3e-4, help="head LR; backbone uses lr/10")
    ap.add_argument("--weight-decay", type=float, default=0.05)
    ap.add_argument("--val-frac", type=float, default=0.1)
    ap.add_argument("--workers", type=int, default=8)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--no-pretrained", action="store_true",
                    help="start from random weights (offline smoke tests only)")
    args = ap.parse_args()

    torch.manual_seed(args.seed)
    device = torch.device("cuda" if torch.cuda.is_available()
                          else "mps" if torch.backends.mps.is_available() else "cpu")
    classes, train_items, val_items = split_dataset(Path(args.data), args.val_frac, args.seed)
    print(f"{len(classes)} classes, {len(train_items)} train / {len(val_items)} val, device={device}")

    model = timm.create_model(args.model, pretrained=not args.no_pretrained, num_classes=len(classes))
    data_cfg = resolve_data_config({}, model=model)
    train_tf, eval_tf = build_transforms(data_cfg, args.img_size)

    # Classes are imbalanced (rare species have fewer photos, "other" has more);
    # weight the loss so the model doesn't just learn the class prior.
    counts = Counter(label for _, label in train_items)
    weights = torch.tensor([len(train_items) / (len(classes) * counts[i]) for i in range(len(classes))])
    criterion = nn.CrossEntropyLoss(weight=weights.to(device), label_smoothing=0.1)

    train_dl = DataLoader(ImageList(train_items, train_tf), args.batch_size, shuffle=True,
                          num_workers=args.workers, pin_memory=True, drop_last=True)
    val_dl = DataLoader(ImageList(val_items, eval_tf), args.batch_size,
                        num_workers=args.workers, pin_memory=True)

    head_params = list(model.get_classifier().parameters())
    head_ids = {id(p) for p in head_params}
    backbone_params = [p for p in model.parameters() if id(p) not in head_ids]
    optimizer = torch.optim.AdamW(
        [{"params": backbone_params, "lr": args.lr / 10}, {"params": head_params, "lr": args.lr}],
        weight_decay=args.weight_decay,
    )
    steps = args.epochs * len(train_dl)
    scheduler = torch.optim.lr_scheduler.OneCycleLR(
        optimizer, max_lr=[args.lr / 10, args.lr], total_steps=steps, pct_start=0.1)
    scaler = torch.amp.GradScaler(enabled=device.type == "cuda")
    model.to(device)

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    best = -1.0
    for epoch in range(args.epochs):
        model.train()
        t0, running = time.time(), 0.0
        for x, y in train_dl:
            x, y = x.to(device, non_blocking=True), y.to(device, non_blocking=True)
            with torch.autocast(device.type, enabled=device.type == "cuda"):
                loss = criterion(model(x), y)
            optimizer.zero_grad(set_to_none=True)
            scaler.scale(loss).backward()
            scaler.step(optimizer)
            scaler.update()
            scheduler.step()
            running += loss.item()
        top1, top5, per_class = evaluate(model, val_dl, device, len(classes))
        print(f"epoch {epoch + 1}/{args.epochs} loss={running / len(train_dl):.3f} "
              f"val_top1={top1:.3f} val_top5={top5:.3f} ({time.time() - t0:.0f}s)")
        if top1 > best:
            best = top1
            torch.save({
                "model_name": args.model,
                "classes": classes,
                "img_size": args.img_size,
                "mean": list(data_cfg["mean"]),
                "std": list(data_cfg["std"]),
                "state_dict": model.state_dict(),
                "val_top1": top1,
                "val_top5": top5,
            }, out)
            worst = sorted(per_class.items(), key=lambda kv: kv[1])[:10]
            report = {"val_top1": top1, "val_top5": top5,
                      "per_class_top1": {classes[c]: round(a, 3) for c, a in sorted(per_class.items())}}
            out.with_suffix(".metrics.json").write_text(json.dumps(report, indent=2))
            print("  saved; weakest classes: " + ", ".join(f"{classes[c]}={a:.2f}" for c, a in worst))
    print(f"best val top1 {best:.3f} -> {out}")


if __name__ == "__main__":
    main()
