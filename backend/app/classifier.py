"""Image classifier behind a small interface so the API doesn't depend on torch.

The backend only needs `predict(image, k) -> [Prediction]`. TorchClassifier
loads a checkpoint written by ml/train.py; torch/timm are imported lazily so
the API (and its tests) run without them.
"""

from __future__ import annotations

import threading
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

from PIL import Image

OTHER_LABEL = "other"


@dataclass
class Prediction:
    label: str
    probability: float


class Classifier(Protocol):
    def predict(self, image: Image.Image, k: int = 3) -> list[Prediction]: ...


class TorchClassifier:
    def __init__(self, checkpoint_path: str | Path):
        import timm
        import torch
        from torchvision import transforms

        self._torch = torch
        ckpt = torch.load(checkpoint_path, map_location="cpu", weights_only=False)
        self.classes: list[str] = ckpt["classes"]
        self.model = timm.create_model(ckpt["model_name"], pretrained=False, num_classes=len(self.classes))
        self.model.load_state_dict(ckpt["state_dict"])
        self.model.eval()
        size = ckpt["img_size"]
        self.transform = transforms.Compose([
            transforms.Resize(int(size / 0.875)),
            transforms.CenterCrop(size),
            transforms.ToTensor(),
            transforms.Normalize(ckpt["mean"], ckpt["std"]),
        ])
        self._lock = threading.Lock()

    def predict(self, image: Image.Image, k: int = 3) -> list[Prediction]:
        torch = self._torch
        x = self.transform(image.convert("RGB")).unsqueeze(0)
        with self._lock, torch.inference_mode():
            probs = self.model(x).softmax(-1)[0]
        top = probs.topk(min(k, len(self.classes)))
        return [Prediction(self.classes[i], float(p)) for p, i in zip(top.values, top.indices)]


_classifier: Classifier | None = None
_load_error: str | None = None


def load_classifier(path: Path) -> None:
    global _classifier, _load_error
    if not path.exists():
        _load_error = f"no model at {path}; train one with ml/train.py"
        return
    try:
        _classifier = TorchClassifier(path)
    except Exception as exc:  # missing torch, bad checkpoint, ...
        _load_error = f"failed to load model: {exc}"


def get_classifier() -> Classifier | None:
    return _classifier


def classifier_status() -> str | None:
    return _load_error
