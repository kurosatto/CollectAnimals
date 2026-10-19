"""Draw the 10 profile pictures: small curious nature lovers in the animal
sprites' pixel style (same outline ink, warm palette), each on a round coloured
badge. Every player gets one at random when they sign up (app/avatars.py).

    python tools/make_avatars.py   # writes species/sprites/avatar_<n>.png (n = 1..10)

Each picture is drawn on a 32x32 grid from simple shapes painted in order, then
gets the sprites' 1-pixel outline and a highlight/shadow on the badge.
"""
from __future__ import annotations

from pathlib import Path

from PIL import Image

N = 32
SCALE = 4  # saved at 128 px so browsers and Android don't have to upscale tiny files
OUT = Path(__file__).resolve().parent.parent / "species" / "sprites"

INK = (38, 26, 46)          # outline, as on the sprites
WHITE = (250, 248, 240)
EYE = (44, 34, 52)
BLUSH = (240, 140, 140)
MOUTH = (150, 70, 70)
SKIN = [(255, 214, 178), (232, 180, 130), (198, 140, 96), (150, 98, 64), (108, 70, 46)]
HAIR = {"black": (46, 38, 44), "brown": (110, 70, 42), "auburn": (168, 82, 46),
        "blond": (236, 196, 108), "dark": (70, 48, 36)}


def shade(c, t):
    """Darker (t < 0, toward cool purple) or lighter (t > 0, toward warm white)."""
    to = (62, 44, 112) if t < 0 else (255, 244, 214)
    t = abs(t)
    return tuple(round(c[i] * (1 - t) + to[i] * t) for i in range(3))


class Pic:
    def __init__(self, bg):
        self.px: dict[tuple[int, int], tuple] = {}
        self.bg = bg

    def put(self, x, y, c):
        if 0 <= x < N and 0 <= y < N:
            self.px[(x, y)] = c

    def ellipse(self, cx, cy, rx, ry, c, where=lambda x, y: True):
        for y in range(N):
            for x in range(N):
                if ((x + .5 - cx) / rx) ** 2 + ((y + .5 - cy) / ry) ** 2 <= 1 and where(x, y):
                    self.put(x, y, c)

    def rect(self, x0, y0, x1, y1, c):
        for y in range(y0, y1 + 1):
            for x in range(x0, x1 + 1):
                self.put(x, y, c)

    def dots(self, pts, c):
        for x, y in pts:
            self.put(x, y, c)

    def render(self) -> Image.Image:
        img = Image.new("RGBA", (N, N), (0, 0, 0, 0))
        # The badge: a disc with a lit upper left and a darker rim at the lower right.
        r = 15.5
        for y in range(N):
            for x in range(N):
                d = ((x + .5 - 16) ** 2 + (y + .5 - 16) ** 2) ** .5
                if d <= r:
                    c = self.bg
                    if d > r - 1.5 and x + y > 30:
                        c = shade(self.bg, -.25)
                    elif d > r - 2.5 and x + y < 22:
                        c = shade(self.bg, .3)
                    img.putpixel((x, y), (*c, 255))
        # The figure, cut to the badge, with a 1-pixel ink outline where it meets the badge.
        inside = {(x, y) for y in range(N) for x in range(N) if img.getpixel((x, y))[3]}
        fig = {p for p in self.px if p in inside}
        for (x, y) in fig:
            img.putpixel((x, y), (*self.px[(x, y)], 255))
        for (x, y) in inside - fig:
            if any((x + dx, y + dy) in fig for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))):
                img.putpixel((x, y), (*INK, 255))
        # The badge's own rim.
        for y in range(N):
            for x in range(N):
                if (x, y) in inside and any((x + dx, y + dy) not in inside
                                            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))):
                    img.putpixel((x, y), (*INK, 255))
        return img.resize((N * SCALE, N * SCALE), Image.NEAREST)


def kid(p: Pic, skin, shirt, hair=None, hair_style="short", eyes="open"):
    """A round-faced kid looking at you: shoulders, face, hair, eyes, cheeks, smile."""
    # Shoulders and shirt.
    p.ellipse(16, 33, 11, 8, shirt)
    p.ellipse(16, 33, 11, 8, shade(shirt, -.2), where=lambda x, y: x >= 22)
    p.rect(14, 24, 17, 25, skin)  # neck
    if hair and hair_style in ("long", "pony", "curly"):
        # Hair behind the head, down to the shoulders.
        p.ellipse(16, 18, 10, 9 if hair_style != "curly" else 10, hair)
        if hair_style == "long":
            p.rect(7, 18, 9, 26, hair)
            p.rect(23, 18, 25, 26, hair)
    p.ellipse(16, 16, 8, 8, skin)                                  # face
    p.ellipse(16, 16, 8, 8, shade(skin, -.12), where=lambda x, y: x >= 21 and y >= 17)
    p.dots([(8, 16), (8, 17), (23, 16), (23, 17)], shade(skin, -.08))  # ears
    if hair:
        if hair_style == "curly":
            for cx, cy in ((10, 10), (14, 8), (18, 8), (22, 10), (9, 14), (23, 14)):
                p.ellipse(cx, cy, 3, 3, hair)
            p.dots([(13, 7), (17, 7)], shade(hair, .25))
        else:
            p.ellipse(16, 12, 9, 6, hair, where=lambda x, y: y <= 12)  # top of the head
            p.dots([(9, 13), (10, 13), (22, 13), (23, 13), (9, 14), (23, 14)], hair)
            p.dots([(13, 13), (14, 13), (15, 13), (19, 13), (20, 13)], hair)  # bangs
            p.dots([(12, 8), (13, 8), (14, 8), (12, 9)], shade(hair, .25))
        if hair_style == "pony":
            p.ellipse(25, 14, 3, 5, hair)
            p.dots([(24, 11), (25, 11)], (232, 90, 120))  # hair tie
    # Eyes: dark with a white glint, looking a little up and to the side (curious).
    if eyes == "open":
        for ex in (12, 19):
            p.rect(ex, 16, ex + 1, 18, EYE)
            p.put(ex, 16, WHITE)
    else:  # happy closed eyes
        for ex in (12, 19):
            p.dots([(ex - 1, 17), (ex, 16), (ex + 1, 16), (ex + 2, 17)], EYE)
    p.dots([(10, 19), (11, 19), (21, 19), (22, 19)], BLUSH)
    p.dots([(15, 20), (16, 21), (17, 20)], MOUTH)


def binoculars(p, y=25):
    """Hanging on a strap around the neck, ready to look."""
    p.dots([(11, 23), (12, 24), (20, 24), (21, 23)], (150, 98, 60))
    for bx in (10, 18):
        p.rect(bx, y, bx + 3, y + 4, (60, 64, 80))
        p.rect(bx + 1, y + 4, bx + 2, y + 4, (120, 180, 210))
    p.rect(14, y + 1, 17, y + 2, (90, 94, 110))


def make() -> list[Image.Image]:
    pics = []

    # 1. Safari hat and binoculars.
    p = Pic((140, 200, 160))
    kid(p, SKIN[1], (110, 140, 70), HAIR["brown"])
    p.ellipse(16, 10, 13, 3, (214, 180, 120), where=lambda x, y: y >= 9)  # brim
    p.ellipse(16, 9, 7, 5, (226, 196, 136), where=lambda x, y: y <= 10)    # crown
    p.rect(9, 9, 23, 9, (150, 98, 60))                                   # band
    p.dots([(12, 6), (13, 6), (12, 7)], (246, 222, 170))
    binoculars(p)
    pics.append(p)

    # 2. Red beanie and a magnifying glass.
    p = Pic((150, 196, 236))
    kid(p, SKIN[3], (70, 120, 190), HAIR["black"])
    p.ellipse(16, 11, 9, 6, (210, 70, 70), where=lambda x, y: y <= 11)
    p.rect(7, 11, 25, 12, (240, 240, 230))
    p.ellipse(16, 4, 2.5, 2.5, (240, 240, 230))  # pompom
    p.dots([(11, 8), (12, 7)], (240, 120, 110))
    p.ellipse(24, 23, 4, 4, (200, 160, 70))       # lens rim
    p.ellipse(24, 23, 2.6, 2.6, (190, 230, 245))
    p.dots([(23, 22)], WHITE)
    p.rect(21, 26, 21, 30, (150, 98, 60))         # handle
    p.rect(20, 28, 20, 31, (150, 98, 60))
    pics.append(p)

    # 3. Curly hair and a flower crown.
    p = Pic((246, 200, 150))
    kid(p, SKIN[4], (230, 120, 150), HAIR["black"], "curly", eyes="closed")
    for fx, col in ((10, (255, 230, 90)), (14, (250, 130, 160)), (18, (255, 255, 255)), (22, (250, 130, 160))):
        p.ellipse(fx, 8 + (1 if fx in (10, 22) else 0), 1.6, 1.6, col)
        p.put(fx - 1 if fx < 16 else fx, 8 + (1 if fx in (10, 22) else 0), (240, 180, 60))
    p.dots([(12, 8), (16, 7), (20, 8)], (90, 170, 90))
    pics.append(p)

    # 4. A frog hood.
    p = Pic((190, 226, 150))
    kid(p, SKIN[0], (90, 170, 90), None)
    green = (96, 176, 96)
    p.ellipse(16, 16, 10, 10, green, where=lambda x, y: y <= 13 or x <= 8 or x >= 23)
    p.ellipse(16, 16, 10, 10, shade(green, -.18), where=lambda x, y: x >= 24)
    p.ellipse(16, 16, 8, 8, SKIN[0], where=lambda x, y: y >= 14 and 9 <= x <= 22)
    for ex in (10, 21):  # frog eyes on top of the hood
        p.ellipse(ex + 1, 6, 3, 3, green)
        p.ellipse(ex + 1, 6, 1.8, 1.8, WHITE)
        p.rect(ex + 1, 5, ex + 1, 6, EYE)
    p.dots([(13, 11), (14, 12), (15, 12), (16, 12), (17, 12), (18, 11)], shade(green, -.35))  # smile on the hood
    # Its own face (redrawn over the hood's edge).
    for ex in (12, 19):
        p.rect(ex, 16, ex + 1, 18, EYE)
        p.put(ex, 16, WHITE)
    p.dots([(10, 19), (11, 19), (21, 19), (22, 19)], BLUSH)
    p.dots([(15, 20), (16, 21), (17, 20)], MOUTH)
    pics.append(p)

    # 5. Ranger hat and a little bird on the brim.
    p = Pic((236, 214, 140))
    kid(p, SKIN[2], (90, 120, 80), HAIR["dark"])
    p.ellipse(16, 10, 13, 2.5, (90, 110, 70), where=lambda x, y: y >= 9)
    p.ellipse(16, 8, 6, 5, (110, 134, 86), where=lambda x, y: y <= 9)
    p.dots([(16, 3), (16, 4)], shade((110, 134, 86), -.3))  # crease
    p.rect(10, 9, 22, 9, (150, 98, 60))
    # bluebird on the brim
    p.ellipse(24, 6, 3, 2.5, (80, 140, 220))
    p.ellipse(23, 7, 1.6, 1.2, (240, 150, 90))
    p.put(25, 5, EYE)
    p.put(27, 6, (240, 180, 60))
    pics.append(p)

    # 6. A bear-ear hood.
    p = Pic((214, 186, 230))
    kid(p, SKIN[0], (120, 80, 60), None)
    fur = (120, 78, 52)
    for ex in (8, 24):
        p.ellipse(ex, 7, 3, 3, fur)
        p.ellipse(ex, 7, 1.6, 1.6, (230, 170, 140))
    p.ellipse(16, 16, 10, 10, fur, where=lambda x, y: y <= 12 or x <= 8 or x >= 23)
    p.ellipse(16, 16, 10, 10, shade(fur, -.18), where=lambda x, y: x >= 24)
    p.ellipse(16, 16, 8, 8, SKIN[0], where=lambda x, y: y >= 13 and 9 <= x <= 22)
    p.dots([(13, 13), (14, 13), (18, 13), (19, 13)], fur)  # hood edge
    for ex in (12, 19):
        p.rect(ex, 16, ex + 1, 18, EYE)
        p.put(ex, 16, WHITE)
    p.dots([(10, 19), (11, 19), (21, 19), (22, 19)], BLUSH)
    p.dots([(15, 20), (16, 21), (17, 20)], MOUTH)
    pics.append(p)

    # 7. Yellow bucket hat with a butterfly.
    p = Pic((140, 214, 210))
    kid(p, SKIN[3], (240, 150, 70), HAIR["dark"], "long")
    hat = (246, 200, 80)
    p.ellipse(16, 11, 11, 3, shade(hat, -.15), where=lambda x, y: y >= 10)
    p.ellipse(16, 10, 8, 6, hat, where=lambda x, y: y <= 10)
    p.dots([(11, 6), (12, 5)], shade(hat, .4))
    # butterfly on the hat
    p.ellipse(21, 4, 2, 2, (180, 110, 230))
    p.ellipse(25, 4, 2, 2, (180, 110, 230))
    p.dots([(23, 3), (23, 4), (23, 5)], EYE)
    p.dots([(21, 4), (25, 4)], (250, 220, 120))
    pics.append(p)

    # 8. Ponytail with a ladybug clip.
    p = Pic((250, 180, 170))
    kid(p, SKIN[0], (80, 170, 150), HAIR["auburn"], "pony")
    p.ellipse(11, 9, 2, 2, (220, 60, 60))
    p.dots([(10, 8), (12, 10)], EYE)
    p.put(11, 7, EYE)
    pics.append(p)

    # 9. Glasses and a leafy cap.
    p = Pic((180, 220, 120))
    kid(p, SKIN[2], (60, 110, 160), HAIR["black"])
    cap = (70, 140, 90)
    p.ellipse(16, 11, 9, 6, cap, where=lambda x, y: y <= 11)
    p.rect(16, 11, 26, 12, shade(cap, -.15))  # brim to the side
    p.dots([(15, 4), (16, 3), (17, 4), (16, 5)], (140, 210, 110))  # leaf on top
    p.put(16, 6, (90, 60, 40))
    for gx in (11, 18):  # round glasses
        p.dots([(gx, 15), (gx + 1, 15), (gx + 2, 15), (gx + 3, 15), (gx, 19), (gx + 1, 19), (gx + 2, 19), (gx + 3, 19),
                (gx - 1, 16), (gx - 1, 17), (gx - 1, 18), (gx + 4, 16), (gx + 4, 17), (gx + 4, 18)], (60, 50, 70))
    p.dots([(15, 17), (16, 17), (17, 17)], (60, 50, 70))
    pics.append(p)

    # 10. A camera, ready to capture.
    p = Pic((246, 226, 120))
    kid(p, SKIN[4], (200, 80, 80), HAIR["brown"])
    p.rect(9, 21, 22, 27, (70, 76, 92))       # camera body
    p.rect(9, 21, 22, 21, (110, 116, 130))
    p.rect(19, 19, 21, 20, (70, 76, 92))      # flash
    p.put(20, 19, (250, 230, 140))
    p.ellipse(15.5, 24.5, 3, 3, (40, 44, 58))
    p.ellipse(15.5, 24.5, 1.8, 1.8, (110, 170, 220))
    p.put(15, 24, WHITE)
    p.rect(7, 23, 8, 27, SKIN[4])             # hands
    p.rect(23, 23, 24, 27, SKIN[4])
    pics.append(p)

    return [q.render() for q in pics]


if __name__ == "__main__":
    OUT.mkdir(parents=True, exist_ok=True)
    for i, img in enumerate(make(), 1):
        img.save(OUT / f"avatar_{i}.png", optimize=True)
    print(f"wrote 10 avatars to {OUT}")
