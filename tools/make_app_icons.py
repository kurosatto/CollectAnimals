"""Draw the app logo, Anna's Hummingbird from the game's own pixel art, at every size the app needs.

Run from the repo root: python tools/make_app_icons.py
The sprite is cropped to the bird and scaled up by whole numbers with nearest-neighbour,
so every pixel stays a crisp square, then centred on a warm yellow background.
Writes:
- backend/app/static/icons/{icon,maskable}-{192,512}.png, apple-touch-icon.png, favicon-32.png, logo.png (web header)
- android/app/src/main/res/mipmap-*/ic_launcher_foreground.png (adaptive icon foreground, one per density)
- docs/store/icon-512.png (Google Play listing icon)
"""
from pathlib import Path

from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parent.parent
SPRITE = ROOT / "species" / "sprites" / "annas_hummingbird.png"
WEB = ROOT / "backend" / "app" / "static" / "icons"
RES = ROOT / "android" / "app" / "src" / "main" / "res"
STORE = ROOT / "docs" / "store"
BG = (255, 233, 184, 255)  # #FFE9B8, as ic_launcher_background in android/.../values/colors.xml
# Adaptive icon foregrounds are 108 dp, and launchers may cut them to any shape that holds the
# 66 dp safe circle, so each density gets the biggest whole-number scale that keeps the bird in it.
DENSITIES = {"mdpi": 1, "hdpi": 1.5, "xhdpi": 2, "xxhdpi": 3, "xxxhdpi": 4}


def bird():
    im = Image.open(SPRITE).convert("RGBA")
    return im.crop(im.getbbox())


def reach(b):
    """How far the bird's farthest pixel is from the middle of its box, in sprite pixels."""
    a = b.getchannel("A").load()
    return max(((x + .5 - b.width / 2) ** 2 + (y + .5 - b.height / 2) ** 2) ** .5
               for x in range(b.width) for y in range(b.height) if a[x, y])


def place(canvas, fill=None, radius=None):
    """Pastes the bird, centred, at the largest whole-number scale that fits in fill * canvas width
    (or that keeps every pixel within radius px of the centre)."""
    b = bird()
    s = int(radius / reach(b)) if radius else int(canvas.width * fill / max(b.size))
    s = max(1, s)
    big = b.resize((b.width * s, b.height * s), Image.NEAREST)
    canvas.alpha_composite(big, ((canvas.width - big.width) // 2, (canvas.height - big.height) // 2))
    return canvas


def round_icon(size, fill=.72):
    """A yellow disc with the bird (the 'any' purpose icon and favicon)."""
    im = place(Image.new("RGBA", (size, size), BG), fill)
    mask = Image.new("L", (size * 4, size * 4), 0)
    ImageDraw.Draw(mask).ellipse([0, 0, size * 4 - 1, size * 4 - 1], fill=255)
    im.putalpha(mask.resize((size, size), Image.LANCZOS))
    return im


def square_icon(size, fill=.62):
    """Full bleed, bird inside the maskable safe zone (also the Play icon, which Google rounds)."""
    return place(Image.new("RGBA", (size, size), BG), fill)


if __name__ == "__main__":
    WEB.mkdir(parents=True, exist_ok=True)
    for size in (192, 512):
        round_icon(size).save(WEB / f"icon-{size}.png", optimize=True)
        square_icon(size).save(WEB / f"maskable-{size}.png", optimize=True)
    square_icon(180, .7).convert("RGB").save(WEB / "apple-touch-icon.png", optimize=True)
    # 32 px: the bird at 1x is 30 px wide, so it goes edge to edge without the disc.
    place(Image.new("RGBA", (32, 32), (0, 0, 0, 0)), 1).save(WEB / "favicon-32.png", optimize=True)
    bird().save(WEB / "logo.png", optimize=True)  # 1x: the page scales it by whole numbers
    for name, k in DENSITIES.items():
        d = RES / f"mipmap-{name}"
        d.mkdir(parents=True, exist_ok=True)
        place(Image.new("RGBA", (int(108 * k),) * 2, (0, 0, 0, 0)), radius=33 * k).save(d / "ic_launcher_foreground.png", optimize=True)
    STORE.mkdir(parents=True, exist_ok=True)
    square_icon(512, .72).convert("RGB").save(STORE / "icon-512.png", optimize=True)
    print("wrote web icons, Android mipmaps and docs/store/icon-512.png")
