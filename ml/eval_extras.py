"""Photos of a state's model-only animals (species/model_extras.json): how often does
each checkpoint hand out a wrong badge from the state's Field Guide list?

A model that never saw an animal may squeeze its photo onto a look-alike. A model that
knows it is scored two ways: as the game worked before (only the Field Guide list
counts) and as the server does now (the state's extras count as "not in the collection
yet", backend/app/extras.py), which is the second number.

    python ml/eval_extras.py models/v5_all_states.pt models/v6_200_pets.pt --data D:/data/images_all
"""

import argparse
import json
from pathlib import Path

import timm
import torch
from torch.utils.data import DataLoader
from torchvision import transforms

from eval_state import DEV, SPECIES, ImageList, split_dataset, state_slugs


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("ckpts", nargs="+")
    ap.add_argument("--states", nargs="+", default=["CA", "NC", "VA", "TX", "FL", "NY"])
    ap.add_argument("--data", default="data/images")
    ap.add_argument("--t", type=float, default=0.8)
    a = ap.parse_args()
    extra = json.loads((SPECIES / "model_extras.json").read_text(encoding="utf-8"))["states"]
    # The photos held out by a model trained on the current folder; older models never saw the extras.
    dclasses, _, val = split_dataset(Path(a.data), 0.1, 0)
    for path in a.ckpts:
        ck = torch.load(path, map_location="cpu", weights_only=False)
        classes = ck["classes"]
        m = timm.create_model(ck["model_name"], pretrained=False, num_classes=len(classes))
        m.load_state_dict(ck["state_dict"]); m = m.eval().to(DEV)
        s = ck["img_size"]
        tf = transforms.Compose([transforms.Resize(int(s / 0.875)), transforms.CenterCrop(s), transforms.ToTensor(),
                                 transforms.Normalize(ck["mean"], ck["std"])])
        for code in a.states:
            game = [x for x in state_slugs(code) if x in classes]
            ex = set(extra.get(code, [])) - set(game)
            paths = [p for p, y in val if dclasses[y] in ex]
            with torch.no_grad(), torch.autocast("cuda"):
                pr = torch.cat([m(x.to(DEV)).float().softmax(-1).cpu()
                                for x, _ in DataLoader(ImageList([(p, 0) for p in paths], tf), 128, num_workers=4)])

            def wrong(allowed):
                idx = torch.tensor([classes.index(x) for x in allowed])
                r = pr[:, idx]; r = r / r.sum(1, keepdim=True); c, i = r.max(1)
                return sum(allowed[j] in game and cc >= a.t for j, cc in zip(i.tolist(), c.tolist())) / len(paths)

            line = f"{Path(path).stem} {code}: {len(paths)} photos, wrong badge {wrong(game + ['other']):.3f}"
            known = sorted(ex & set(classes))
            if known:
                line += f", with extras as 'not in the collection yet' {wrong(game + known + ['other']):.3f}"
            print(line, flush=True)


if __name__ == "__main__":
    main()
