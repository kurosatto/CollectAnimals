"""Draw the Google Play feature graphic (1024x500) from the game's own pixel sprites.

Run from the repo root: python tools/make_store_graphics.py
Everything is drawn on a 256x125 canvas and scaled up 4x with nearest-neighbour, so it
keeps the crisp pixel look of the game. Writes docs/store/feature-graphic.png.
"""
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent.parent
SPRITES = ROOT / "species" / "sprites"
OUT = ROOT / "docs" / "store" / "feature-graphic.png"
W, H, SCALE = 256, 125, 4
GROUND = 100

SKY = [(255, 214, 153), (255, 226, 176), (255, 236, 198), (240, 244, 214), (214, 238, 230)]
HILL_FAR, HILL_NEAR = (150, 190, 150), (110, 165, 110)
GRASS, GRASS_DARK, DIRT = (86, 150, 76), (66, 124, 60), (120, 92, 60)
INK, CREAM, SHADOW = (40, 52, 40), (255, 248, 230), (196, 120, 60)

# (sprite, x, bottom y): animals standing on the grass, a flier or two in the sky.
CAST = [("red_fox", 160, GROUND + 6), ("raccoon", 191, GROUND + 5), ("california_quail", 216, GROUND + 4),
        ("mule_deer", 241, GROUND + 7), ("bald_eagle", 222, 44), ("annas_hummingbird", 168, 38)]


def sprite(name):
    im = Image.open(SPRITES / f"{name}.png").convert("RGBA")
    return im.crop(im.getbbox())


def text(draw_on, xy, s, scale, fill, shadow):
    """Bitmap-font text scaled by whole pixels, with a one-pixel drop shadow."""
    font = ImageFont.load_default_imagefont()
    l, t, r, b = font.getbbox(s)
    small = Image.new("RGBA", (r + 1, b + 1), (0, 0, 0, 0))
    d = ImageDraw.Draw(small)
    d.text((1, 1), s, font=font, fill=shadow)
    d.text((0, 0), s, font=font, fill=fill)
    big = small.resize((small.width * scale, small.height * scale), Image.NEAREST)
    draw_on.alpha_composite(big, xy)
    return big.width


def main():
    im = Image.new("RGBA", (W, H))
    d = ImageDraw.Draw(im)
    band = GROUND // len(SKY)
    for i, c in enumerate(SKY):
        d.rectangle([0, i * band, W, (i + 1) * band + 1], fill=c)
    d.ellipse([196, 6, 216, 26], fill=(255, 246, 214))  # sun
    for x in range(W):  # rolling hills: two sine-ish rows of blocky steps
        far = 70 + int(8 * __import__("math").sin(x / 23)) + int(4 * __import__("math").sin(x / 7))
        near = 84 + int(6 * __import__("math").sin(x / 17 + 2))
        d.line([x, far, x, GROUND], fill=HILL_FAR)
        d.line([x, near, x, GROUND], fill=HILL_NEAR)
    d.rectangle([0, GROUND, W, H], fill=GRASS)
    d.rectangle([0, GROUND + 14, W, H], fill=DIRT)
    for x in range(0, W, 3):
        d.point([x, GROUND - 1 + (x // 3) % 2], fill=GRASS_DARK)
    for name, x, bottom in CAST:
        s = sprite(name)
        im.alpha_composite(s, (x - s.width // 2, bottom - s.height))
    text(im, (8, 14), "Capture", 3, INK, CREAM)
    text(im, (8, 44), "Animals", 3, INK, CREAM)
    text(im, (10, 78), "Snap real wildlife.", 1, INK, CREAM)
    text(im, (10, 88), "Fill your Field Guide.", 1, INK, CREAM)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    im.convert("RGB").resize((W * SCALE, H * SCALE), Image.NEAREST).save(OUT)
    print("wrote", OUT)


if __name__ == "__main__":
    main()
