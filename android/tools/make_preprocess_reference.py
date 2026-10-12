"""Write PIL/torchvision reference outputs for PreprocessTest (app/src/test/resources).

The test images are synthetic patterns (generated identically in the Kotlin
test), so no photos need to live in the repo. Run from android/:
    python tools/make_preprocess_reference.py
"""

from pathlib import Path

import numpy as np
from PIL import Image
from torchvision import transforms

CASES = [(200, 150), (640, 480), (3000, 2000), (1080, 1920)]
RESIZE, SIZE = 256, 224


def pattern(w: int, h: int) -> np.ndarray:
    y, x = np.mgrid[0:h, 0:w]
    r = (x * 7 + y * 3) % 256
    g = (x * x // 13 + y) % 256
    b = ((x // 4) ^ (y // 4)) % 256
    return np.stack([r, g, b], -1).astype(np.uint8)


out = Path(__file__).resolve().parents[1] / "app/src/test/resources"
out.mkdir(parents=True, exist_ok=True)
tf = transforms.Compose([transforms.Resize(RESIZE), transforms.CenterCrop(SIZE)])
for w, h in CASES:
    crop = np.asarray(tf(Image.fromarray(pattern(w, h))))  # SIZE x SIZE x 3 uint8
    (out / f"preprocess_{w}x{h}.rgb").write_bytes(crop.tobytes())
    print(f"wrote preprocess_{w}x{h}.rgb")
