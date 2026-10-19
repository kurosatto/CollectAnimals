"""Fine-tune the last stage of the backbone end to end, with augmentation.

This is the recipe behind the shipped models (models/v4_ca_nc_ft.pt and
models/v5_all_states.pt). train.py trains only a linear head on frozen
features, which is faster but less accurate: on the California/North Carolina
set, fine-tuning the last stage took correct badges from 53% (linear head,
badge at 70%) to 67% (fine-tuned, badge at 80%).

What it does: start from the pretrained timm backbone, freeze every stage but
the last --unfreeze ones, and train those stages plus a new classifier for
--epochs passes with AdamW, a one-cycle schedule, label smoothing 0.1 and
class-balanced loss, on random-crop / flip / colour-jitter photos. The best
epoch by validation accuracy is kept. The checkpoint has the same keys as
train.py's, so the backend and export_onnx.py load it unchanged.

    python ml/finetune.py --data data/images --out models/v5_all_states.pt
    python ml/finetune.py --data D:/data/images_all --epochs 8 --unfreeze 1   # the shipped settings

Same 90/10 split as train.py (split_dataset, seed 0). About an hour per
epoch for ~900 classes / 900k photos on a mid-range GPU.
"""

from __future__ import annotations

import argparse
import time
from collections import Counter
from pathlib import Path

import timm
import torch
from timm.data import resolve_data_config
from torch import nn
from torch.utils.data import DataLoader

from train import ImageList, build_transforms, split_dataset


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--data", default="data/images")
    ap.add_argument("--out", default="models/finetuned.pt")
    ap.add_argument("--model", default="convnext_nano.in12k_ft_in1k")
    ap.add_argument("--img-size", type=int, default=224)
    ap.add_argument("--epochs", type=int, default=8)
    ap.add_argument("--unfreeze", type=int, default=1, help="number of final stages to train")
    ap.add_argument("--lr", type=float, default=2e-4, help="for the unfrozen stages")
    ap.add_argument("--head-lr", type=float, default=2e-3)
    ap.add_argument("--batch-size", type=int, default=96)
    ap.add_argument("--workers", type=int, default=4)
    ap.add_argument("--val-frac", type=float, default=0.1)
    ap.add_argument("--seed", type=int, default=0)
    args = ap.parse_args()
    torch.manual_seed(args.seed)
    dev = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    classes, train_items, val_items = split_dataset(Path(args.data), args.val_frac, args.seed)
    n = len(classes)
    model = timm.create_model(args.model, pretrained=True, num_classes=n).to(dev)
    cfg = resolve_data_config({}, model=model)
    aug_tf, eval_tf = build_transforms(cfg, args.img_size)
    model.requires_grad_(False)
    stage_p = list(model.stages[-args.unfreeze:].parameters())
    head_p = list(model.get_classifier().parameters())
    for p in stage_p + head_p:
        p.requires_grad_(True)
    print(f"{n} classes, {len(train_items)} train / {len(val_items)} val, "
          f"training {sum(p.numel() for p in stage_p + head_p) / 1e6:.1f}M params on {dev}")

    counts = Counter(y for _, y in train_items)
    weight = torch.tensor([len(train_items) / (n * counts[i]) for i in range(n)], device=dev)
    crit = nn.CrossEntropyLoss(weight=weight, label_smoothing=0.1)
    opt = torch.optim.AdamW([{"params": stage_p, "lr": args.lr}, {"params": head_p, "lr": args.head_lr}],
                            weight_decay=0.05)
    loader = DataLoader(ImageList(train_items, aug_tf), args.batch_size, shuffle=True, drop_last=True,
                        num_workers=args.workers, pin_memory=True, persistent_workers=True)
    val_loader = DataLoader(ImageList(val_items, eval_tf), 256, num_workers=args.workers, pin_memory=True)
    sched = torch.optim.lr_scheduler.OneCycleLR(opt, max_lr=[args.lr, args.head_lr],
                                                total_steps=args.epochs * len(loader), pct_start=0.1)
    scaler = torch.amp.GradScaler(enabled=dev.type == "cuda")
    out = Path(args.out); out.parent.mkdir(parents=True, exist_ok=True)
    best, t0 = -1.0, time.time()
    for ep in range(args.epochs):
        model.train()
        for s in model.stages[:-args.unfreeze]:  # frozen stages stay in eval mode
            s.eval()
        total = 0.0
        for x, y in loader:
            x, y = x.to(dev, non_blocking=True), y.to(dev, non_blocking=True)
            with torch.autocast(dev.type, enabled=dev.type == "cuda"):
                loss = crit(model(x), y)
            opt.zero_grad(set_to_none=True)
            scaler.scale(loss).backward(); scaler.step(opt); scaler.update(); sched.step()
            total += loss.item()
        model.eval()
        hit = cnt = 0
        with torch.no_grad(), torch.autocast(dev.type, enabled=dev.type == "cuda"):
            for x, y in val_loader:
                hit += (model(x.to(dev)).argmax(1).cpu() == y).sum().item(); cnt += len(y)
        acc = hit / cnt
        print(f"epoch {ep + 1}/{args.epochs} loss {total / len(loader):.3f} val_top1 {acc:.4f} "
              f"t={time.time() - t0:.0f}s", flush=True)
        if acc > best:
            best = acc
            torch.save({"model_name": args.model, "classes": classes, "img_size": args.img_size,
                        "mean": list(cfg["mean"]), "std": list(cfg["std"]),
                        "state_dict": {k: v.cpu() for k, v in model.state_dict().items()}, "val_top1": acc}, out)
    print(f"best val top1 {best:.3f} -> {out}")


if __name__ == "__main__":
    main()
