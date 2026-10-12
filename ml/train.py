"""Train a species classifier head on top of a frozen ImageNet-pretrained backbone.

Expects the layout produced by fetch_inat.py:
    data/images/<class_slug>/*.jpg     (100 species + "other")

The backbone is never updated. Its pooled embeddings are computed once per
image (plus a few augmented views of each training image) and cached next to
the output, so re-running with different head settings takes seconds. Only a
linear head is trained on those embeddings.

Writes a single checkpoint (weights + class list + preprocessing config) that
the backend loads directly:
    python ml/train.py --data data/images --out models/ca100.pt

Any timm model name works. Small options:
  efficientnet_b0.ra_in1k        (default; 5M params, ~20 MB)
  convnext_nano.in12k_ft_in1k    (15M params, stronger embeddings)
  mobilenetv3_large_100.ra_in1k  (5M params, fastest on phones)
"""

from __future__ import annotations

import argparse
import hashlib
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
    aug_tf = transforms.Compose([
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
    return aug_tf, eval_tf


@torch.no_grad()
def embed(model, items, transform, device, batch_size, workers):
    """Pooled backbone features (pre-logits) for every item."""
    loader = DataLoader(ImageList(items, transform), batch_size,
                        num_workers=workers, pin_memory=device.type == "cuda")
    feats, labels = [], []
    for x, y in loader:
        with torch.autocast(device.type, enabled=device.type == "cuda"):
            f = model.forward_head(model.forward_features(x.to(device)), pre_logits=True)
        feats.append(f.float().cpu())
        labels.append(y)
    return torch.cat(feats), torch.cat(labels)


def cached_embeddings(model, args, classes, train_items, val_items, aug_tf, eval_tf, device):
    """Embed the dataset once and reuse it while the image set and backbone are unchanged."""
    key = hashlib.sha1(json.dumps([
        args.model, args.img_size, args.aug_views, classes,
        [str(p) for p, _ in train_items], [str(p) for p, _ in val_items],
    ]).encode()).hexdigest()[:12]
    cache = Path(args.out).with_suffix(f".feats-{key}.pt")
    if cache.exists():
        print(f"using cached embeddings {cache}")
        return torch.load(cache)

    t0 = time.time()
    views = [embed(model, train_items, eval_tf, device, args.batch_size, args.workers)]
    for v in range(args.aug_views):
        print(f"  augmented view {v + 1}/{args.aug_views}")
        views.append(embed(model, train_items, aug_tf, device, args.batch_size, args.workers))
    data = {
        "train_x": torch.cat([x for x, _ in views]),
        "train_y": torch.cat([y for _, y in views]),
        "val": embed(model, val_items, eval_tf, device, args.batch_size, args.workers),
    }
    torch.save(data, cache)
    print(f"embedded {len(train_items)} train x{1 + args.aug_views} views, "
          f"{len(val_items)} val in {time.time() - t0:.0f}s -> {cache}")
    return data


@torch.no_grad()
def evaluate(head, x, y, num_classes):
    pred5 = head(x).topk(min(5, num_classes), dim=1).indices
    hit1 = pred5[:, 0] == y
    top1 = hit1.float().mean().item()
    top5 = (pred5 == y[:, None]).any(1).float().mean().item()
    per_class = {c: hit1[y == c].float().mean().item() for c in y.unique().tolist()}
    return top1, top5, per_class


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--data", default="data/images")
    ap.add_argument("--out", default="models/ca100.pt")
    ap.add_argument("--model", default="efficientnet_b0.ra_in1k")
    ap.add_argument("--img-size", type=int, default=224)
    ap.add_argument("--aug-views", type=int, default=2,
                    help="extra augmented embeddings per training image")
    ap.add_argument("--epochs", type=int, default=30)
    ap.add_argument("--batch-size", type=int, default=128, help="batch size for embedding")
    ap.add_argument("--head-batch-size", type=int, default=512)
    ap.add_argument("--lr", type=float, default=1e-3)
    ap.add_argument("--weight-decay", type=float, default=1e-4)
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
    model.requires_grad_(False)
    model.eval().to(device)
    data_cfg = resolve_data_config({}, model=model)
    aug_tf, eval_tf = build_transforms(data_cfg, args.img_size)

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    data = cached_embeddings(model, args, classes, train_items, val_items, aug_tf, eval_tf, device)
    train_x, train_y = data["train_x"].to(device), data["train_y"].to(device)
    val_x, val_y = (t.to(device) for t in data["val"])

    # The head is timm's own classifier layer, so the saved state_dict loads
    # straight into timm.create_model(..., num_classes=N) in the backend.
    head = model.get_classifier()
    head.reset_parameters()
    head.requires_grad_(True)

    # Classes are imbalanced (rare species have fewer photos, "other" has more);
    # weight the loss so the model doesn't just learn the class prior.
    counts = Counter(train_y.tolist())
    weights = torch.tensor([len(train_y) / (len(classes) * counts[i]) for i in range(len(classes))])
    criterion = nn.CrossEntropyLoss(weight=weights.to(device), label_smoothing=0.1)
    optimizer = torch.optim.AdamW(head.parameters(), lr=args.lr, weight_decay=args.weight_decay)
    steps_per_epoch = (len(train_y) + args.head_batch_size - 1) // args.head_batch_size
    scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(optimizer, args.epochs * steps_per_epoch)

    best = -1.0
    for epoch in range(args.epochs):
        head.train()
        perm = torch.randperm(len(train_y), device=device)
        running = 0.0
        for i in range(0, len(perm), args.head_batch_size):
            idx = perm[i:i + args.head_batch_size]
            loss = criterion(head(train_x[idx]), train_y[idx])
            optimizer.zero_grad(set_to_none=True)
            loss.backward()
            optimizer.step()
            scheduler.step()
            running += loss.item()
        head.eval()
        top1, top5, per_class = evaluate(head, val_x, val_y, len(classes))
        print(f"epoch {epoch + 1}/{args.epochs} loss={running / steps_per_epoch:.3f} "
              f"val_top1={top1:.3f} val_top5={top5:.3f}")
        if top1 > best:
            best = top1
            torch.save({
                "model_name": args.model,
                "classes": classes,
                "img_size": args.img_size,
                "mean": list(data_cfg["mean"]),
                "std": list(data_cfg["std"]),
                "state_dict": {k: v.cpu() for k, v in model.state_dict().items()},
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
