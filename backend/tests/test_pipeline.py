"""End-to-end check that a checkpoint written by ml/train.py loads in the backend.

Trains a tiny randomly initialised model on synthetic images, so it needs
torch/timm but no network. Skipped when they aren't installed.
"""

import subprocess
import sys
from pathlib import Path

import pytest
from PIL import Image

pytest.importorskip("torch")
pytest.importorskip("timm")

from app.classifier import TorchClassifier  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
COLORS = {"coyote": (200, 60, 40), "gray_fox": (40, 160, 60), "other": (50, 70, 200)}


def test_train_checkpoint_loads_in_backend(tmp_path):
    for cls, rgb in COLORS.items():
        (tmp_path / "images" / cls).mkdir(parents=True)
        for i in range(6):
            Image.new("RGB", (64, 64), tuple(min(255, c + 5 * i) for c in rgb)).save(
                tmp_path / "images" / cls / f"{i}.jpg")
    out = tmp_path / "model.pt"
    subprocess.run([
        sys.executable, str(ROOT / "ml" / "train.py"), "--data", str(tmp_path / "images"),
        "--out", str(out), "--model", "resnet18", "--no-pretrained", "--img-size", "64",
        "--epochs", "2", "--batch-size", "8", "--workers", "0", "--aug-views", "1",
    ], check=True, capture_output=True)

    assert out.exists() and out.with_suffix(".metrics.json").exists()
    clf = TorchClassifier(out)
    assert clf.classes == sorted(COLORS)
    preds = clf.predict(Image.new("RGB", (100, 80), COLORS["coyote"]), k=3)
    assert [p.label for p in preds] and sorted(p.label for p in preds) == sorted(COLORS)
    assert abs(sum(p.probability for p in preds) - 1) < 1e-4
