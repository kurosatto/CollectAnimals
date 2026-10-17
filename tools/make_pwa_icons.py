"""Draw the web app icons: the Android launcher's white paw print on forest green.

Run from the repo root: python tools/make_pwa_icons.py
Writes backend/app/static/icons/{icon,maskable}-{192,512}.png and apple-touch-icon.png.
"""
from pathlib import Path

from PIL import Image, ImageDraw

GREEN = (46, 107, 63, 255)  # #2E6B3F, as in android/.../ic_launcher.xml
WHITE = (255, 255, 255, 255)
OUT = Path(__file__).resolve().parent.parent / "backend" / "app" / "static" / "icons"


def paw(draw, s, cx=54, cy=54, scale=1.0):
    """The paw from ic_launcher.xml (a 108-unit viewport), scaled by s px per unit."""
    def p(x, y):
        return ((cx + (x - 54) * scale) * s, (cy + (y - 54) * scale) * s)

    def oval(x, y, rx, ry):
        (x0, y0), (x1, y1) = p(x - rx, y - ry), p(x + rx, y + ry)
        draw.ellipse([x0, y0, x1, y1], fill=WHITE)

    oval(54, 70, 20, 12)  # main pad
    for x, y, rx, ry in [(37, 48, 7, 8), (47, 36, 7, 9), (61, 36, 7, 9), (71, 48, 7, 8)]:
        oval(x, y, rx, ry)


def render(size, kind):
    ss = 4  # supersample, then shrink for smooth edges
    big = size * ss
    im = Image.new("RGBA", (big, big), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    s = big / 108
    if kind == "any":
        d.ellipse([4 * s, 4 * s, 104 * s, 104 * s], fill=GREEN)
        paw(d, s)
    else:  # maskable / apple: full bleed, paw inside the 80% safe zone
        d.rectangle([0, 0, big, big], fill=GREEN)
        paw(d, s)  # stays within the 40%-radius safe circle
    return im.resize((size, size), Image.LANCZOS)


if __name__ == "__main__":
    OUT.mkdir(parents=True, exist_ok=True)
    for size in (192, 512):
        render(size, "any").save(OUT / f"icon-{size}.png", optimize=True)
        render(size, "maskable").save(OUT / f"maskable-{size}.png", optimize=True)
    render(180, "maskable").convert("RGB").save(OUT / "apple-touch-icon.png", optimize=True)
    render(32, "any").save(OUT / "favicon-32.png", optimize=True)
    print("wrote", sorted(p.name for p in OUT.iterdir()))
