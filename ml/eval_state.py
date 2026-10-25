"""Compare checkpoints the way the game plays: for each state, only that state's
Field Guide animals (+ "other") count, rescaled, and a badge needs --t confidence.

    python ml/eval_state.py models/v5_all_states.pt models/v6_200_pets.pt \\
        --data D:/data/images_all --states CA NC VA --fair

Test photos are the ones split_dataset (seed 0, 10%) held out. Its shuffle depends on
the whole class list, so models trained on different class lists held out different
photos: --fair keeps only the photos every checkpoint held out. It also reports how
often a photo with no animal (--nonanimal, from fetch_nonanimal.py) would earn a badge.
"""
import argparse, csv, json, sys
from pathlib import Path

import timm
import torch
from torch.utils.data import DataLoader
from torchvision import transforms

sys.path.insert(0, str(Path(__file__).parent))
from train import ImageList, split_dataset, IMG_EXTS  # noqa

SPECIES = Path(__file__).resolve().parents[1] / "species"
DEV = torch.device("cuda")


def state_slugs(code):
    sj = json.loads((SPECIES / "states.json").read_text(encoding="utf-8"))
    st = next(s for s in sj["states"] if s["code"] == code)
    return [r["slug"] for r in csv.DictReader(open(SPECIES / st["species"], encoding="utf-8"))]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("ckpts", nargs="+")
    ap.add_argument("--states", nargs="+", default=["CA", "NC"])
    ap.add_argument("--data", default="data/images")
    ap.add_argument("--nonanimal", default="data/nonanimal")
    ap.add_argument("--t", type=float, default=0.8)
    ap.add_argument("--fair", action="store_true", help="only photos every checkpoint held out")
    a = ap.parse_args()
    keep = None
    if a.fair:
        # split_dataset shares one RNG across classes, so a model trained on a different class list
        # held out different photos. Rebuild each checkpoint's split and keep the photos all held out.
        import random
        for path in a.ckpts:
            cl = torch.load(path, map_location="cpu", weights_only=False)["classes"]
            # v5 was trained with the horse photos in a folder named domestic_horse.
            cl = sorted("domestic_horse" if c == "horse" and "v5" in path else c for c in cl)
            rng, held = random.Random(0), set()
            for c in cl:
                d = Path(a.data) / ("horse" if c == "domestic_horse" else c)
                files = sorted(p for p in d.iterdir() if p.suffix.lower() in IMG_EXTS) if d.is_dir() else []
                rng.shuffle(files)
                held |= set(files[:max(1, int(len(files) * 0.1))])
            keep = held if keep is None else keep & held
        print(f"{len(keep)} photos held out by every model", flush=True)
    nonanimal = []
    for g in ("plants_fungi", "people", "scenes"):
        d = Path(a.nonanimal) / g
        if d.is_dir():
            nonanimal += [p for p in sorted(d.iterdir()) if p.suffix.lower() in IMG_EXTS]
    for path in a.ckpts:
        ck = torch.load(path, map_location="cpu", weights_only=False)
        classes = ck["classes"]
        m = timm.create_model(ck["model_name"], pretrained=False, num_classes=len(classes))
        m.load_state_dict(ck["state_dict"]); m = m.eval().to(DEV)
        s = ck["img_size"]
        tf = transforms.Compose([transforms.Resize(int(s / 0.875)), transforms.CenterCrop(s), transforms.ToTensor(),
                                 transforms.Normalize(ck["mean"], ck["std"])])
        dclasses, _, val = split_dataset(Path(a.data), 0.1, 0)

        def probs(paths):
            out = []
            with torch.no_grad(), torch.autocast("cuda"):
                for x, _ in DataLoader(ImageList([(p, 0) for p in paths], tf), 128, num_workers=4):
                    out.append(m(x.to(DEV)).float().softmax(-1).cpu())
            return torch.cat(out)

        pna = probs(nonanimal) if nonanimal else None
        for code in a.states:
            slugs = [x for x in state_slugs(code) if x in classes]
            allowed = torch.tensor([classes.index(x) for x in slugs] + [classes.index("other")])
            items = [(p, dclasses[y]) for p, y in val if dclasses[y] in slugs and (keep is None or p in keep)]
            pv = probs([p for p, _ in items])

            def badges(pr):
                r = pr[:, allowed]; r = r / r.sum(1, keepdim=True)
                conf, idx = r.max(1)
                lab = [classes[allowed[i]] for i in idx.tolist()]
                return lab, conf

            lab, conf = badges(pv)
            truth = [t for _, t in items]
            badge = [(l != "other" and c >= a.t) for l, c in zip(lab, conf.tolist())]
            correct = sum(b and l == t for b, l, t in zip(badge, lab, truth)) / len(items)
            wrong = sum(b and l != t for b, l, t in zip(badge, lab, truth)) / len(items)
            top1 = sum(l == t for l, t in zip(lab, truth)) / len(items)
            line = (f"{Path(path).stem} {code}: {len(items)} photos, top1 {top1:.3f}, correct badge {correct:.3f}, "
                    f"wrong badge {wrong:.3f}")
            if pna is not None:
                nl, nc = badges(pna)
                line += f", non-animal badge {sum(l != 'other' and c >= a.t for l, c in zip(nl, nc.tolist())) / len(nl):.3f}"
            print(line, flush=True)


if __name__ == "__main__":
    main()
