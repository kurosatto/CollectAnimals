"""Draw the habitat decorations sold in the minigame shop, and write their catalog.

    python tools/make_decor.py                    # species/sprites/decor/<key>.png + species/decor.json
    python tools/make_decor.py --sheet sheet.png  # also a preview of every decoration

Each decoration is drawn on the animals' 40x40 canvas (tools/pixel.py: a 32x32 grid,
ground at y = 31) with the same shading and outline, so it sits in the habitat like
another sprite and dims at night the same way. Animated ones are a row of four frames.

species/decor.json is the catalog the server sells from (app/games.py) and the habitat
places and fills with visitors (habitat.js): for each decoration its name, price, group,
where it goes (area and row), how many frames it has, a line on who visits, and the
visits themselves: which animals come, what they do there, and where (in grid
coordinates of the drawing). Only animals the player has caught ever visit.
"""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

from PIL import Image

from pixel import N, Sprite, mix

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "species" / "sprites" / "decor"
CATALOG = ROOT / "species" / "decor.json"

WOOD, WOOD_DK, WOOD_LT = "#a8743f", "#74502e", "#c99a62"
STONE, STONE_DK, STONE_LT = "#a9a59b", "#7f7b74", "#c9c5b8"
METAL, METAL_DK = "#8f98aa", "#5d6474"
WHITE = "#f3efe4"
RED, YELLOW, PINK, PURPLE, BLUE, ORANGE = "#d8493b", "#f2c14e", "#ee7ea0", "#9a6ad6", "#4f8fdc", "#ee8a35"
LEAF, LEAF_DK, LEAF_LT = "#4f9a48", "#3a7638", "#79bd5e"
SOIL = "#7a5232"
WATER, WATER_LT = "#4b9ad6", "#8cc8ee"
GLOW = "#ffe27a"

ITEMS: list[dict] = []


def item(key, name, price, group, area, note, *, row="any", frames=1, visits=(), fx=None):
    """Register a decoration; the decorated function draws it (frame f of `frames`)."""
    def deco(fn):
        ITEMS.append({"key": key, "name": name, "price": price, "group": group, "area": area, "row": row,
                      "frames": frames, "note": note, "visits": [dict(v) for v in visits], "fx": fx, "draw": fn})
        return fn
    return deco


def V(who, act, x, y, when="any", n=1):
    """A visit: animals in group `who` come and `act` with their feet at grid (x, y)."""
    return {"who": who, "act": act, "x": x, "y": y, "when": when, "n": n}


# -- shared bits ----------------------------------------------------------------------
def post(s, x, top, col=WOOD, w=1.0, bottom=31):
    s.rect(x - w / 2, top, x + w / 2 - .01, bottom, col)


def board(s, x0, y0, x1, y1, col=WOOD, **kw):
    s.rect(x0, y0, x1, y1, col, **kw)


def flower(s, x, y, col, center=YELLOW, stem=True, h=4):
    if stem:
        s.line(x, y + 1, x, y + h, LEAF_DK)
    s.px([(x - 1, y), (x + 1, y), (x, y - 1), (x, y + 1)], col)
    s.px([(x, y)], center)


def tuft(s, x, y=31, col=LEAF):
    s.px([(x, y), (x - 1, y - 1), (x + 1, y - 2), (x + 2, y)], col)


def bush(s, cx, cy, rx, ry, col=LEAF, lt=None):
    s.ellipse(cx, cy, rx, ry, col)
    for i, (dx, dy) in enumerate(((-.5, -.4), (.45, -.3), (0, -.6))):
        s.ellipse(cx + dx * rx, cy + dy * ry, rx * .55, ry * .55, lt or col)


def mushroom(s, x, y, r, cap=RED, dots=True, stem=WHITE):
    s.rect(x - max(1, r * .35), y - r * .9, x + max(1, r * .35), y, stem)
    s.ellipse(x, y - r, r, r * .6, cap)
    s.erase(s.m_ellipse(x, y - r + r * .6, r + 1, r * .25) & (s.reg == s.n) & ~s.m_ellipse(x, y - r, r, r * .45))
    if dots and r >= 2.5:
        s.px([(round(x - r * .45), round(y - r * 1.2)), (round(x + r * .4), round(y - r * 1.05))], WHITE)


def water(s, cx, cy, rx, ry):
    s.ellipse(cx, cy, rx, ry, WATER, shade=False)
    s.px([(round(cx - rx * .4), round(cy - ry * .2)), (round(cx - rx * .4) + 1, round(cy - ry * .2))], WATER_LT)


def roof(s, x0, x1, y_eave, y_peak, col=RED):
    mid = (x0 + x1) / 2
    s.poly([(x0 - 1, y_eave + .5), (mid, y_peak), (x1 + 1, y_eave + .5)], col)


def sway(f, amp=1.0):
    return round(math.sin(f / 4 * 2 * math.pi) * amp)


# == Garden =============================================================================
@item("sunflowers", "Sunflowers", 120, "Garden", "ground", "Songbirds perch on the heads; bees visit",
      row="back", frames=4, visits=[V("songbird", "perch", 10, 1, "day"), V("bee", "hover", 22, 4, "day")])
def d_sunflowers(s, f):
    for x, top, lean in ((10, 2, 0), (17, -3, 1), (23, 5, -1)):
        dx = sway(f + x, 1) + lean
        s.path([(x, 31), (x + dx * .5, (31 + top) / 2), (x + dx, top + 3)], .6, LEAF_DK)
        s.ellipse(x - 2 + dx * .5, (31 + top) / 2 + 2, 2, 1, LEAF, rot=-20)
        s.ellipse(x + dx, top, 3.4, 3.4, YELLOW)
        s.ellipse(x + dx, top, 1.8, 1.8, "#6b3f22")


@item("tulips", "Tulip row", 90, "Garden", "ground", "Butterflies and bees land on them",
      row="front", visits=[V("bug", "hover", 12, 22, "day"), V("bee", "hover", 21, 22, "day")])
def d_tulips(s, f):
    s.ellipse(16, 31, 13, 2, SOIL, shade=False)
    for i, (x, col) in enumerate(zip(range(5, 29, 4), (RED, YELLOW, PINK, PURPLE, RED, ORANGE))):
        h = 22 + (i % 2) * 2
        s.line(x, h, x, 30, LEAF_DK)
        s.ellipse(x - 1, 28, 1.5, .8, LEAF, rot=-40)
        s.poly([(x - 1.5, h - 3), (x + 1.5, h - 3), (x + 1.4, h), (x - 1.4, h)], col)
        s.px([(x, h - 4)], col)


@item("rose_bush", "Rose bush", 110, "Garden", "ground", "Small birds hide inside; rabbits nibble the leaves",
      visits=[V("smallbird", "hide", 16, 26), V("rabbit", "eat", 4, 31)])
def d_rose_bush(s, f):
    bush(s, 16, 22, 12, 9.5, LEAF_DK, LEAF)
    for x, y in ((9, 18), (15, 15), (22, 17), (12, 24), (20, 23), (25, 22), (17, 20)):
        s.ellipse(x, y, 1.6, 1.4, "#d63a4e")
        s.px([(x, y)], "#ff8a98")


@item("lavender", "Lavender patch", 90, "Garden", "ground", "Bees and butterflies hover over it",
      row="front", visits=[V("bee", "hover", 12, 20, "day"), V("bug", "hover", 21, 19, "day")])
def d_lavender(s, f):
    s.ellipse(16, 30, 13, 3, LEAF_DK)
    for i, x in enumerate(range(5, 29, 3)):
        top = 20 + (i * 7) % 5
        s.line(x, top + 3, x + (i % 3 - 1), 29, "#6f8f5a")
        s.ellipse(x, top + 1, 1, 2.6, PURPLE)


@item("mushroom_ring", "Mushroom ring", 80, "Garden", "ground", "Toads sit in the middle; snails come in the rain",
      row="front", visits=[V("frog", "sit", 16, 30), V("snail", "sit", 22, 31)])
def d_mushroom_ring(s, f):
    s.ellipse(16, 30, 14, 2.5, "#5d9d4a", shade=False)
    for x, y, r in ((3, 30, 2.5), (8, 28, 2), (24, 28, 2), (29, 30, 2.5), (11, 31, 3), (21, 31, 3)):
        mushroom(s, x, y, r, "#c9573c" if r >= 3 else "#e2a35a", dots=r >= 3)


@item("toadstool", "Giant toadstool", 120, "Garden", "ground", "Frogs sit on top; lizards shelter under it",
      visits=[V("frog", "perch", 16, 11), V("lizard", "sit", 9, 31)])
def d_toadstool(s, f):
    s.rect(13, 16, 19, 31, "#efe6d0")
    s.ellipse(16, 30, 5, 1.5, "#e2d6b8")
    s.ellipse(16, 15, 14, 6, RED)
    s.erase(s.m_ellipse(16, 21, 15, 2.5) & ~s.m_ellipse(16, 15, 14, 4.5) & (s.reg == s.n))
    s.px([(10, 12), (11, 12), (10, 13), (20, 11), (21, 11), (16, 13), (24, 14), (6, 15)], WHITE)


@item("veggies", "Vegetable patch", 130, "Garden", "ground", "Rabbits and squirrels sneak in for a nibble",
      row="front", visits=[V("rabbit", "eat", 10, 31), V("squirrel", "eat", 22, 31)])
def d_veggies(s, f):
    s.rect(1, 25, 30, 31, SOIL)
    board(s, 0, 29, 31, 31, WOOD_DK)
    for x in (5, 13, 21, 28):
        s.poly([(x - 1, 25), (x + 1, 25), (x, 29)], ORANGE)
        s.path([(x, 25), (x - 1, 21)], .5, LEAF)
        s.path([(x, 25), (x + 1, 20)], .5, LEAF_LT)
    for x in (9, 17, 25):
        s.ellipse(x, 23, 2.5, 2.2, "#8ccf5c")
        s.ellipse(x, 23, 1.2, 1, "#b6e88a")


@item("strawberries", "Strawberry patch", 100, "Garden", "ground", "Songbirds and box turtles stop to eat berries",
      row="front", visits=[V("songbird", "eat", 8, 31, "day"), V("turtle", "eat", 22, 31)])
def d_strawberries(s, f):
    for x in (6, 14, 22, 28):
        bush(s, x, 27, 4.5, 3.5, LEAF_DK, LEAF)
    for x, y in ((4, 29), (9, 28), (13, 30), (19, 29), (24, 30), (29, 28)):
        s.poly([(x - 1, y - 1), (x + 1, y - 1), (x, y + 1)], "#e23c3c")
        s.px([(x, y - 2)], LEAF_LT)


@item("cactus", "Potted cactus", 80, "Garden", "ground", "Lizards bask beside it; desert birds perch on top",
      visits=[V("lizard", "bask", 25, 31, "day"), V("bird", "perch", 16, 5)])
def d_cactus(s, f):
    s.poly([(9, 23), (23, 23), (21, 31), (11, 31)], "#c8693c")
    s.rect(8, 22, 24, 24, "#d97c4a")
    s.rect(13, 6, 19, 22, "#5a9e54")
    s.ellipse(16, 6.5, 3, 2.5, "#5a9e54")
    s.path([(13, 15), (9, 15), (9, 10)], 1.4, "#5a9e54")
    s.path([(19, 12), (23, 12), (23, 7)], 1.4, "#5a9e54")
    s.px([(15, 9), (17, 13), (15, 17), (17, 20), (10, 12), (22, 9)], "#d9f0b0")
    s.px([(16, 3), (15, 4), (17, 4)], PINK)


@item("ferns", "Fern corner", 80, "Garden", "ground", "Salamanders and newts rest in the shade",
      row="front", visits=[V("salamander", "sit", 16, 31)])
def d_ferns(s, f):
    for ang in (-70, -45, -20, 0, 20, 45, 70):
        a = math.radians(ang)
        tip = (16 + math.sin(a) * 15, 31 - math.cos(a) * 13)
        mid = (16 + math.sin(a) * 8, 31 - math.cos(a) * 11)
        s.path([(16, 31), mid, tip], (1.6, .5), LEAF if ang % 40 else LEAF_LT)


@item("flower_basket", "Hanging flower basket", 130, "Garden", "ground", "Hummingbirds hover and sip",
      row="back", visits=[V("hummingbird", "hover", 24, 6)])
def d_flower_basket(s, f):
    post(s, 8, 0, WOOD_DK, 2)
    board(s, 8, 0, 20, 1, WOOD_DK)
    s.line(18, 2, 15, 7, METAL_DK)
    s.line(18, 2, 21, 7, METAL_DK)
    s.ellipse(18, 9, 5, 3.5, "#9a6a3a")
    for x, y, c in ((14, 6, PINK), (18, 5, RED), (22, 6, PURPLE), (16, 12, PINK), (21, 12, WHITE)):
        s.ellipse(x, y, 1.6, 1.4, c)
    s.path([(14, 9), (13, 15)], .5, LEAF)
    s.path([(22, 9), (23, 14)], .5, LEAF)


@item("berry_bush", "Berry bush", 120, "Garden", "ground", "Bears, foxes and songbirds stop to eat berries",
      visits=[V("bear", "eat", 2, 31), V("fox", "eat", 30, 31), V("songbird", "perch", 16, 9, "day")])
def d_berry_bush(s, f):
    bush(s, 16, 21, 13, 10, LEAF_DK, LEAF)
    for x, y in ((8, 18), (12, 14), (19, 13), (24, 18), (14, 22), (21, 24), (9, 25), (26, 24), (17, 18)):
        s.px([(x, y), (x + 1, y), (x, y + 1)], "#4a3fb8")
        s.px([(x, y)], "#8a80f0")


@item("cherry_tree", "Cherry blossom sapling", 250, "Garden", "ground", "Songbirds perch in the branches",
      row="back", fx="petals", visits=[V("songbird", "perch", 9, 6, "day"), V("songbird", "perch", 23, 4, "day")])
def d_cherry_tree(s, f):
    s.path([(16, 31), (16, 18), (12, 12)], (2.2, 1), "#7a5038")
    s.path([(16, 20), (21, 13)], (1.2, .6), "#7a5038")
    for cx, cy, r in ((10, 8, 6.5), (22, 7, 7), (16, 3, 6), (16, 11, 6)):
        s.ellipse(cx, cy, r, r * .8, "#f2a8c4")
    for x, y in ((8, 6), (13, 2), (20, 4), (24, 9), (17, 10), (11, 11), (19, 1)):
        s.px([(x, y)], "#ffe0ec")


@item("hedge_tunnel", "Hedge tunnel", 150, "Garden", "ground", "Rabbits and small mammals run through it",
      visits=[V("smallmammal", "through", 16, 31)])
def d_hedge_tunnel(s, f):
    s.ellipse(16, 22, 15, 11, LEAF_DK)
    s.ellipse(12, 17, 7, 5, LEAF)
    s.ellipse(21, 16, 6, 5, LEAF)
    s.ellipse(16, 28, 5, 6, "#1d2a18", shade=False)
    s.erase(s.m_ellipse(16, 36, 20, 4))


@item("clover", "Clover patch", 100, "Garden", "ground", "Rabbits and deer graze on it; one clover sparkles",
      row="front", fx="sparkle", visits=[V("rabbit", "eat", 10, 31), V("deer", "eat", 24, 31)])
def d_clover(s, f):
    s.ellipse(16, 30, 14, 2.6, "#4e9442", shade=False)
    for x, y in ((4, 29), (8, 28), (13, 29), (18, 28), (23, 29), (27, 28), (10, 31), (21, 31), (29, 31)):
        s.px([(x, y - 1), (x - 1, y), (x + 1, y)], "#6cc04e")
        s.px([(x, y)], "#4b8a3a")
    s.px([(15, 26), (16, 26), (15, 27), (16, 27)], WHITE)
    s.px([(24, 26), (25, 26), (24, 27)], "#f5f5f5")


@item("rose_arch", "Rose arch", 220, "Garden", "ground", "Birds perch on top; a spider spins a web inside",
      row="back", visits=[V("bird", "perch", 16, -3, "day"), V("spider", "dangle", 16, 14)])
def d_rose_arch(s, f):
    s.path([(5, 31), (5, 8), (9, 1), (16, -2), (23, 1), (27, 8), (27, 31)], 1.2, WHITE)
    s.path([(5, 28), (4, 20), (6, 12), (8, 4), (14, -1), (20, -1), (25, 4), (27, 12), (28, 22), (27, 29)], .7, LEAF)
    for x, y in ((4, 22), (6, 13), (9, 3), (16, -2), (22, 0), (26, 7), (28, 17), (26, 27), (5, 28)):
        s.ellipse(x, y, 1.4, 1.3, "#e84a66")


# == Water ==============================================================================
@item("lily_pads", "Lily pads", 200, "Water", "pond", "Frogs sit on the pads; ducks paddle between them",
      visits=[V("frog", "sit", 9, 29, n=1), V("frog", "sit", 24, 30, n=1), V("duck", "swim", 16, 31)])
def d_lily_pads(s, f):
    for x, y, r in ((8, 30, 5.5), (24, 31, 5), (17, 27, 3.5), (3, 26, 3)):
        s.ellipse(x, y, r, r * .45, "#4e9f45")
        s.poly([(x, y), (x + r, y - r * .25), (x + r, y + r * .15)], "#3d8a3a", shade=False)
    s.ellipse(17, 25.5, 2, 1.2, "#f6d6e6")
    s.px([(16, 24), (18, 24), (17, 23)], "#ffffff")
    s.px([(17, 25)], YELLOW)


@item("fountain", "Pond fountain", 260, "Water", "pond", "Birds splash in the spray; ducks circle it",
      fx="spray", visits=[V("smallbird", "bathe", 9, 25, "day"), V("duck", "swim", 26, 31)])
def d_fountain(s, f):
    s.ellipse(16, 29, 11, 3, STONE)
    s.ellipse(16, 28, 9, 2, WATER, shade=False)
    s.rect(14, 18, 18, 28, STONE)
    s.ellipse(16, 18, 7, 2, STONE_LT)
    s.ellipse(16, 17.5, 5.5, 1.2, WATER, shade=False)
    s.rect(15, 11, 17, 17, STONE_LT)


@item("waterfall", "Rock waterfall", 280, "Water", "pond", "Herons fish at the bottom; birds bathe in the trickle",
      fx="trickle", visits=[V("wader", "fish", 26, 31), V("smallbird", "bathe", 7, 18, "day")])
def d_waterfall(s, f):
    s.ellipse(9, 22, 9, 10, STONE_DK)
    s.ellipse(22, 25, 9, 7, STONE)
    s.ellipse(14, 13, 8, 7, STONE)
    s.rect(15, 9, 18, 29, WATER, shade=False)
    s.px([(16, 12 + (f * 4 + k * 5) % 16) for k in range(3)], "#d8f0ff")
    s.ellipse(17, 30, 6, 1.6, WATER_LT, shade=False)
    s.px([(8, 12), (9, 11), (24, 20)], LEAF)


@item("footbridge", "Footbridge", 240, "Water", "pond", "Ground animals walk across; ducks swim underneath",
      visits=[V("walker", "cross", 16, 22), V("duck", "swim", 16, 31)])
def d_footbridge(s, f):
    s.path([(-3, 31), (4, 25), (16, 22), (28, 25), (35, 31)], 1.6, WOOD)
    for x in (2, 8, 14, 20, 26, 32):
        y = 22 + abs(x - 16) * .38
        post(s, x, y - 6, WOOD_DK, 1, y)
    s.path([(1, 22), (8, 18.5), (16, 16), (24, 18.5), (31, 22)], .6, WOOD_LT)


@item("rowboat", "Rowboat", 220, "Water", "pond", "Turtles climb on to bask; ducks stand on the bow",
      fx="bob", visits=[V("turtle", "ride", 12, 25, "day"), V("duck", "ride", 23, 24)])
def d_rowboat(s, f):
    s.poly([(2, 24), (30, 23), (27, 30), (6, 30)], "#d06a3a")
    s.rect(3, 23, 29, 24, WHITE)
    s.rect(14, 24, 18, 25, WOOD_DK)
    s.path([(10, 25), (2, 31)], .5, WOOD_LT)


@item("basking_rock", "Basking rock", 180, "Water", "pond", "Turtles, lizards and snakes sun on it by day",
      visits=[V("turtle", "bask", 11, 22, "day"), V("lizard", "bask", 21, 21, "day"), V("snake", "bask", 17, 24, "day")])
def d_basking_rock(s, f):
    s.ellipse(16, 27, 14, 7, STONE)
    s.ellipse(12, 23, 7, 3, STONE_LT)
    s.ellipse(16, 31, 15, 1.5, WATER_LT, shade=False)
    s.px([(22, 26), (23, 25), (8, 28)], "#7aa55a")


@item("trough", "Drinking trough", 120, "Water", "ground", "Deer, foxes and other land animals stop to drink",
      visits=[V("deer", "drink", 1, 31), V("walker", "drink", 31, 31)])
def d_trough(s, f):
    s.rect(4, 21, 28, 29, WOOD)
    s.rect(5, 21, 27, 23, WATER, shade=False)
    for x in (5, 27):
        post(s, x, 27, WOOD_DK, 2)
    s.line(4, 25, 28, 25, WOOD_DK)


@item("puddle", "Puddle", 90, "Water", "ground", "Fills when it rains; birds bathe and frogs hop in",
      row="front", fx="rainfill", visits=[V("smallbird", "bathe", 12, 30, "day"), V("frog", "sit", 20, 31)])
def d_puddle(s, f):
    s.ellipse(16, 30, 13, 2.4, "#6f5638", shade=False)
    s.ellipse(15, 30, 10, 1.6, "#6aa6d8", shade=False)
    s.px([(11, 29), (12, 29)], "#c8e8ff")


@item("rubber_duck", "Rubber duck", 100, "Water", "pond", "Real ducks swim beside it; a frog sometimes rides it",
      fx="bob", visits=[V("duck", "swim", 26, 31), V("frog", "ride", 14, 21)])
def d_rubber_duck(s, f):
    s.ellipse(15, 27, 7, 4, YELLOW)
    s.ellipse(11, 21, 4, 3.6, YELLOW)
    s.poly([(7, 21), (4, 22), (7, 23)], ORANGE)
    s.px([(10, 20)], "#2a2030")
    s.ellipse(17, 25, 3, 1.6, "#f6d870")
    s.ellipse(15, 31, 9, 1, WATER_LT, shade=False)


@item("sailboat", "Sailboat", 400, "Water", "sea", "Gulls and pelicans ride the mast as it drifts",
      fx="drift", visits=[V("seabird", "ride", 16, -6)])
def d_sailboat(s, f):
    s.poly([(2, 24), (30, 24), (26, 30), (6, 30)], "#3b5f9a")
    s.rect(3, 23, 29, 24, WHITE)
    post(s, 16, -5, WOOD_DK, 1, 23)
    s.poly([(17, -4), (29, 20), (17, 20)], WHITE)
    s.poly([(15, 0), (15, 20), (6, 20)], "#f0e0c0")
    s.px([(16, -6), (17, -6), (18, -6)], RED)


@item("dock", "Wooden dock", 300, "Water", "sand", "Seals and sea lions haul out on it; gulls stand on the posts",
      visits=[V("seal", "sit", 15, 25), V("seabird", "perch", 3, 18), V("seabird", "perch", 30, 18)])
def d_dock(s, f):
    for x in (3, 30):
        post(s, x, 18, WOOD_DK, 2)
    s.poly([(-2, 25), (35, 25), (35, 28), (-2, 28)], WOOD)
    for x in range(1, 34, 4):
        s.line(x, 25, x, 27, WOOD_DK)
    post(s, 9, 28, WOOD_DK, 1.5)
    post(s, 24, 28, WOOD_DK, 1.5)


@item("buoy", "Buoy", 120, "Water", "sea", "A seal naps on it; gulls perch on top; it blinks at night",
      fx="bob", visits=[V("seabird", "perch", 16, 5), V("seal", "ride", 16, 22)])
def d_buoy(s, f):
    s.ellipse(16, 27, 8, 4, RED)
    s.rect(12, 18, 20, 25, WHITE)
    s.rect(12, 21, 20, 22, RED)
    s.poly([(13, 18), (19, 18), (16, 8)], RED)
    s.ellipse(16, 7, 2, 2, GLOW)
    s.ellipse(16, 31, 10, 1, WATER_LT, shade=False)


# == Animal homes =======================================================================
@item("birdhouse", "Birdhouse", 160, "Animal homes", "ground", "A songbird moves in and sleeps inside at night",
      row="back", visits=[V("songbird", "home", 16, 6), V("songbird", "perch", 16, 9)])
def d_birdhouse(s, f):
    post(s, 16, 14, WOOD_DK, 2)
    s.rect(10, 1, 22, 14, "#e2c08a")
    roof(s, 9, 23, 2, -6, RED)
    s.ellipse(16, 6, 2, 2, "#2a1c18", shade=False)
    s.rect(15, 9, 17, 10, WOOD_DK)


@item("bird_feeder", "Bird feeder", 180, "Animal homes", "ground", "Songbirds eat; dropped seeds draw quail, doves and squirrels",
      row="back", fx="seeds", visits=[V("songbird", "perch", 9, 13, "day"), V("songbird", "perch", 23, 13, "day"),
                                      V("groundbird", "eat", 7, 31, "day"), V("squirrel", "eat", 25, 31)])
def d_bird_feeder(s, f):
    post(s, 16, 0, METAL_DK, 1.5)
    s.rect(11, 3, 21, 12, "#d7eef4")
    s.rect(12, 6, 20, 12, "#c79a50")
    s.poly([(10, 4), (16, -1), (22, 4)], "#3e7a52")
    s.rect(8, 12, 24, 13, WOOD)


@item("hummingbird_feeder", "Hummingbird feeder", 160, "Animal homes", "ground", "Hummingbirds hover and sip",
      row="back", visits=[V("hummingbird", "hover", 9, 12), V("hummingbird", "hover", 23, 12)])
def d_hummingbird_feeder(s, f):
    post(s, 16, -2, METAL_DK, 1)
    s.path([(16, -2), (16, -5), (20, -5), (20, -1)], .5, METAL_DK)
    s.rect(18, 0, 22, 9, "#f05068")
    s.ellipse(20, 11, 5, 2, RED)
    s.px([(16, 11), (24, 11), (20, 12)], YELLOW)


@item("bug_hotel", "Bug hotel", 140, "Animal homes", "ground", "Bees and beetles go in and out",
      visits=[V("bee", "home", 16, 14), V("beetle", "home", 16, 22)])
def d_bug_hotel(s, f):
    roof(s, 7, 25, 6, 0, WOOD_DK)
    s.rect(8, 6, 24, 29, WOOD)
    for y in (10, 15, 20, 25):
        for x in range(10, 23, 3):
            s.ellipse(x + (y % 2), y, 1.2, 1.2, "#5a3a20" if (x + y) % 2 else "#c99a62", shade=False)
    post(s, 10, 29, WOOD_DK, 2)
    post(s, 22, 29, WOOD_DK, 2)


@item("bat_box", "Bat box", 160, "Animal homes", "ground", "Bats sleep inside by day and fly out at dusk",
      row="back", visits=[V("bat", "home", 16, 8)])
def d_bat_box(s, f):
    post(s, 16, 12, WOOD_DK, 2)
    s.rect(10, -2, 22, 12, "#6e4a30")
    s.poly([(9, -2), (23, -2), (23, -4), (9, -4)], "#4a3020")
    s.rect(12, 10, 20, 11, "#2a1c18")
    for y in (1, 4, 7):
        s.line(11, y, 21, y, "#5e3e28")


@item("beehive", "Beehive box", 200, "Animal homes", "ground", "Honey bees fly between the hive and flowers",
      fx="bees", visits=[V("bee", "home", 16, 21)])
def d_beehive(s, f):
    s.rect(7, 26, 25, 31, WOOD_DK)
    for y0, col in ((19, WHITE), (12, "#f2e6c8")):
        s.rect(8, y0, 24, y0 + 7, col)
    s.rect(7, 9, 25, 12, WOOD)
    s.rect(13, 24, 19, 25, "#2a1c18")


@item("milkweed", "Milkweed patch", 140, "Animal homes", "ground", "Butterflies land and rest; monarchs love it",
      visits=[V("butterfly", "perch", 10, 9, "day"), V("butterfly", "perch", 22, 12, "day")])
def d_milkweed(s, f):
    for x, top in ((9, 10), (16, 5), (23, 13)):
        s.line(x, top + 2, x, 31, "#6e9a52")
        for y in range(top + 6, 30, 5):
            s.ellipse(x - 2, y, 2.5, 1, "#79a85e", rot=-25)
            s.ellipse(x + 2, y + 1, 2.5, 1, "#79a85e", rot=25)
        s.ellipse(x, top, 3, 2.5, "#e48ab0")
        s.px([(x - 1, top - 1), (x + 1, top)], "#ffc0d8")


@item("owl_box", "Owl nest box", 170, "Animal homes", "ground", "Owls sleep inside by day and peek out at dusk",
      row="back", visits=[V("owl", "home", 16, 3)])
def d_owl_box(s, f):
    post(s, 16, 12, WOOD_DK, 2)
    s.rect(9, -4, 23, 12, "#8a6242")
    s.poly([(8, -4), (24, -4), (24, -6), (8, -6)], "#5e4028")
    s.ellipse(16, 1, 3, 3, "#1e1410", shade=False)
    s.rect(14, 6, 18, 7, WOOD_DK)


@item("corn_feeder", "Squirrel corn feeder", 140, "Animal homes", "ground", "Squirrels and chipmunks sit and munch",
      visits=[V("squirrel", "eat", 9, 22), V("squirrel", "eat", 25, 31)])
def d_corn_feeder(s, f):
    post(s, 16, 4, WOOD_DK, 2)
    board(s, 8, 22, 24, 23, WOOD)
    s.line(16, 8, 21, 12, METAL_DK)
    s.ellipse(22, 15, 2, 4.5, YELLOW)
    s.px([(21, 12), (22, 14), (23, 16), (21, 17)], "#e8a830")
    s.path([(22, 11), (24, 8)], .6, "#c8d080")


@item("toad_house", "Toad house", 110, "Animal homes", "ground", "Toads and frogs hide inside and peek out",
      row="front", visits=[V("frog", "hide", 16, 31)])
def d_toad_house(s, f):
    s.ellipse(16, 25, 10, 8, "#c8693c")
    s.erase(s.m_ellipse(16, 36, 20, 4))
    s.ellipse(16, 29, 4, 4, "#2a1810", shade=False)
    s.erase(s.m_ellipse(16, 36, 20, 4))
    s.px([(10, 22), (21, 20), (14, 19)], "#e2955f")
    s.px([(23, 27), (24, 26)], LEAF)


@item("nest_platform", "Nest platform", 220, "Animal homes", "ground", "Hawks, eagles and ospreys land and rest",
      row="back", visits=[V("raptor", "perch", 16, -2)])
def d_nest_platform(s, f):
    post(s, 16, 4, WOOD_DK, 2)
    board(s, 8, 2, 24, 3, WOOD)
    s.ellipse(16, 0, 9, 3, "#8a6a40")
    for x in range(8, 25, 3):
        s.line(x, -1, x + 2, 1, "#5e4528")


@item("brush_pile", "Brush pile", 70, "Animal homes", "ground", "Rabbits, mice, snakes and lizards dart in to hide",
      row="front", visits=[V("smallmammal", "hide", 16, 31), V("reptile", "hide", 16, 31)])
def d_brush_pile(s, f):
    for (x0, y0, x1, y1) in ((2, 30, 30, 22), (4, 22, 29, 30), (6, 26, 26, 17), (10, 18, 22, 29), (14, 31, 24, 20)):
        s.path([(x0, y0), (x1, y1)], 1, "#7a5a3a" if x0 % 4 else "#94704a")
    s.px([(9, 21), (20, 19), (25, 24), (13, 26)], "#a08a4a")


# == Picnic and seats ===================================================================
@item("bench", "Garden bench", 120, "Picnic and seats", "ground", "Birds perch on the back; small animals nap underneath",
      visits=[V("bird", "perch", 8, 13, "day"), V("smallmammal", "sit", 16, 31)])
def d_bench(s, f):
    board(s, 2, 21, 30, 23, WOOD)
    board(s, 2, 14, 30, 16, WOOD)
    board(s, 2, 17, 30, 18, WOOD)
    for x in (4, 28):
        post(s, x, 14, METAL_DK, 1.5)
    for x in (5, 27):
        post(s, x, 23, METAL_DK, 1.5)


@item("picnic", "Picnic blanket and basket", 150, "Picnic and seats", "ground",
      "Squirrels, raccoons and birds sneak a snack", row="front",
      visits=[V("squirrel", "eat", 6, 29), V("raccoon", "eat", 26, 31), V("songbird", "eat", 15, 28, "day")])
def d_picnic(s, f):
    s.poly([(0, 31), (6, 25), (34, 25), (30, 31)], "#e8e2d8", shade=False)
    for x in range(1, 33, 4):
        s.paint(s.m_poly([(x, 31), (x + 2, 31), (x + 7, 25), (x + 5, 25)]), RED, within=s.last)
    s.ellipse(20, 24, 5, 3.5, "#c8964a")
    s.path([(16, 23), (20, 17), (24, 23)], .5, WOOD_DK)
    s.ellipse(11, 28, 2, 1.2, "#f2d48a")


@item("picnic_table", "Picnic table", 170, "Picnic and seats", "ground", "Raccoons climb on top; birds perch on the edge",
      visits=[V("raccoon", "sit", 16, 16), V("bird", "perch", 4, 16, "day")])
def d_picnic_table(s, f):
    board(s, 1, 15, 31, 17, WOOD)
    board(s, -1, 23, 33, 24, WOOD_DK)
    s.path([(6, 17), (3, 31)], .9, WOOD_DK)
    s.path([(26, 17), (29, 31)], .9, WOOD_DK)
    s.path([(8, 17), (11, 31)], .9, WOOD_DK)
    s.path([(24, 17), (21, 31)], .9, WOOD_DK)


@item("hammock", "Hammock", 220, "Picnic and seats", "ground", "A raccoon, opossum or squirrel naps in it",
      row="back", frames=4, visits=[V("napper", "ride", 16, 24)])
def d_hammock(s, f):
    for x in (1, 31):
        post(s, x, 8, WOOD_DK, 2)
    d = sway(f, 1)
    s.path([(2, 12), (8, 22 + d * .5), (16, 25 + d), (24, 22 + d * .5), (30, 12)], 1.4, "#e8a040")
    s.path([(4, 13), (9, 21 + d * .5), (16, 23.5 + d), (23, 21 + d * .5), (28, 13)], .5, "#f6d080")


@item("leaf_pile", "Leaf pile", 80, "Picnic and seats", "ground", "Squirrels jump in; animals sleep in it at night",
      row="front", visits=[V("squirrel", "hide", 16, 31), V("smallmammal", "sleep", 16, 30, "night")])
def d_leaf_pile(s, f):
    s.ellipse(16, 29, 14, 6, "#c46a2c")
    s.erase(s.m_ellipse(16, 38, 20, 6))
    for i, (x, y) in enumerate(((5, 28), (9, 25), (14, 24), (19, 25), (24, 27), (12, 28), (21, 29), (27, 30))):
        s.ellipse(x, y, 2, 1.2, ("#e8a032", "#d4502c", "#a8742a", "#f0c040")[i % 4], rot=i * 30)


@item("beach_umbrella", "Beach umbrella and chair", 180, "Picnic and seats", "sand", "Crabs and shorebirds rest in the shade",
      visits=[V("crab", "sit", 14, 31), V("shorebird", "sit", 24, 31)])
def d_beach_umbrella(s, f):
    s.path([(10, 31), (17, 3)], .6, WHITE)
    s.poly([(4, 6), (17, -4), (30, 2), (17, 2)], RED)
    s.paint(s.m_poly([(10, 4), (17, -4), (21, 1)]), WHITE, within=s.last)
    s.poly([(18, 31), (21, 23), (29, 23), (27, 31)], "#4f8fdc")
    s.path([(20, 25), (19, 31)], .4, WOOD_DK)


@item("sandcastle", "Sandcastle", 140, "Picnic and seats", "sand", "Crabs climb on it; shorebirds peck around it",
      row="front", visits=[V("crab", "perch", 16, 17), V("shorebird", "eat", 3, 31)])
def d_sandcastle(s, f):
    s.ellipse(16, 30, 13, 2.5, "#e2c890")
    s.rect(6, 20, 26, 29, "#e8cf96")
    s.rect(12, 13, 20, 20, "#efd8a4")
    for x in (6, 10, 22, 26):
        s.rect(x - 1, 18, x, 20, "#efd8a4")
    s.rect(14, 24, 18, 29, "#b89660")
    post(s, 16, 7, WOOD_DK, 1, 13)
    s.poly([(17, 7), (21, 8.5), (17, 10)], RED)


@item("driftwood", "Driftwood log", 110, "Picnic and seats", "sand", "Seals and shorebirds rest on it",
      visits=[V("seal", "sit", 16, 31), V("shorebird", "perch", 22, 23)])
def d_driftwood(s, f):
    s.path([(1, 29), (16, 27), (31, 26)], (3, 2.2), "#c8b8a0")
    s.path([(6, 28), (3, 22)], .7, "#b8a890")
    s.path([(26, 27), (29, 23)], .6, "#b8a890")
    s.line(8, 28, 22, 27, "#a8987e")


@item("stumps", "Stump stools and table", 90, "Picnic and seats", "ground", "Squirrels and chipmunks sit on the stumps to eat",
      visits=[V("squirrel", "sit", 5, 24), V("squirrel", "sit", 27, 24)])
def d_stumps(s, f):
    for x, top, r in ((5, 25, 3.5), (27, 25, 3.5), (16, 20, 5.5)):
        s.rect(x - r, top, x + r, 31, "#8a5e3a")
        s.ellipse(x, top, r, 1.4, "#d8b07a")
        s.ellipse(x, top, r * .45, .6, "#b88a58", shade=False)


@item("bird_swing", "Swinging perch", 150, "Picnic and seats", "ground", "Birds land on a little swing and ride it",
      row="back", frames=4, visits=[V("smallbird", "ride", 16, 21)])
def d_bird_swing(s, f):
    post(s, 4, -1, WOOD_DK, 1.5)
    post(s, 28, -1, WOOD_DK, 1.5)
    board(s, 3, -2, 29, -1, WOOD_DK)
    d = sway(f, 2)
    s.line(12, -1, 12 + d, 20, METAL_DK)
    s.line(20, -1, 20 + d, 20, METAL_DK)
    board(s, 11 + d, 21, 21 + d, 21, WOOD)


# == Play ===============================================================================
@item("pinwheel", "Pinwheel", 150, "Play", "ground", "Spins; curious animals stop to watch it",
      frames=4, visits=[V("walker", "watch", 4, 31), V("walker", "watch", 28, 31)])
def d_pinwheel(s, f):
    post(s, 16, 10, "#e8e0d0", 1)
    cols = (RED, YELLOW, BLUE, LEAF_LT)
    for i in range(4):
        a = (i / 4 + f / 16) * 2 * math.pi
        tip = (16 + math.cos(a) * 7, 8 + math.sin(a) * 7)
        side = (16 + math.cos(a + .9) * 4, 8 + math.sin(a + .9) * 4)
        s.poly([(16, 8), tip, side], cols[i])
    s.px([(16, 8)], WHITE)


@item("kite", "Kite", 300, "Play", "ground", "Flies over the meadow by day; birds fly alongside it",
      row="back", frames=4, fx="kite", visits=[V("flier", "escort", 0, -60, "day")])
def d_kite(s, f):
    s.rect(15, 26, 17, 31, WOOD_DK)
    s.ellipse(16, 25, 3, 2, "#e8e0d0")
    s.px([(15, 25), (17, 25)], "#c8b890")  # the reel; the string and the flying kite are drawn live
    if f == 0:  # frame 0: at night (and in the shop) the kite rests against its stake
        s.poly([(22, 14), (27, 21), (22, 31), (17, 21)], BLUE)
        s.poly([(17, 21), (27, 21), (22, 14)], RED)
        s.path([(22, 31), (25, 27), (28, 31)], .4, YELLOW)


@item("bubbles", "Bubble maker", 220, "Play", "ground", "Animals look up and chase the bubbles",
      fx="bubbles", visits=[V("walker", "watch", 30, 31, "day"), V("smallmammal", "chase", 8, 31, "day")])
def d_bubbles(s, f):
    s.rect(9, 20, 23, 31, "#6ac0e8")
    s.rect(9, 20, 23, 22, "#4a90c8")
    s.ellipse(16, 18, 5, 3, "#f2a8c4")
    s.ellipse(25, 15, 3, 3, "#e8f6ff", shade=False)
    s.erase(s.m_ellipse(25, 15, 2, 2))


@item("beach_ball", "Beach ball", 70, "Play", "ground", "Animals bump it and it rolls across the meadow",
      row="front", frames=4, fx="ball", visits=[V("walker", "bump", 16, 31)])
def d_beach_ball(s, f):
    s.ellipse(16, 25, 6, 6, WHITE)
    for i, c in enumerate((RED, BLUE, YELLOW)):
        a = (i / 3 + f / 12) * 2 * math.pi
        s.paint(s.m_ellipse(16 + math.cos(a) * 3.5, 25 + math.sin(a) * 3.5, 2.6, 2.6), c, within=s.m_ellipse(16, 25, 6, 6))


@item("acorn_wagon", "Acorn wagon", 110, "Play", "ground", "Squirrels and jays carry acorns off",
      visits=[V("squirrel", "eat", 4, 31), V("jay", "perch", 20, 20, "day")])
def d_acorn_wagon(s, f):
    s.rect(6, 21, 26, 27, RED)
    for x, y in ((10, 20), (14, 19), (18, 20), (22, 19), (16, 17), (12, 18)):
        s.ellipse(x, y, 1.8, 1.6, "#9a6a34")
        s.px([(x, y - 2), (x - 1, y - 1), (x + 1, y - 1)], "#5e3e20")
    for x in (10, 22):
        s.ellipse(x, 29, 2.5, 2.5, "#3a3440")
    s.path([(26, 24), (32, 28)], .5, METAL_DK)


@item("stepping_stones", "Stepping stones", 80, "Play", "ground", "Frogs hop across from stone to stone",
      row="front", visits=[V("frog", "hopacross", 16, 30)])
def d_stepping_stones(s, f):
    for x, y in ((3, 30), (11, 28), (20, 30), (28, 28)):
        s.ellipse(x, y, 3.5, 1.6, STONE)


@item("tunnel", "Tunnel tube", 120, "Play", "ground", "Small mammals run through it",
      visits=[V("smallmammal", "through", 16, 31)])
def d_tunnel(s, f):
    s.rect(2, 21, 30, 31, "#4fb0d8")
    for x in range(5, 30, 5):
        s.line(x, 21, x, 31, "#3a90b8")
    s.ellipse(2, 26, 2.5, 5, "#2a5a78")
    s.ellipse(2, 26, 1.5, 4, "#18303e", shade=False)


@item("soccer", "Soccer goal and ball", 160, "Play", "ground", "Animals nudge the ball; a sparkle when it goes in",
      fx="soccer", visits=[V("walker", "bump", 28, 31)])
def d_soccer(s, f):
    s.path([(1, 31), (1, 12), (22, 12), (22, 31)], .7, WHITE)
    for x in range(3, 22, 3):
        s.line(x, 13, x - 1, 30, "#d8d8d8")
    for y in range(15, 31, 3):
        s.line(2, y, 21, y, "#d8d8d8")


@item("sprinkler", "Sprinkler", 160, "Play", "ground", "Birds bathe, frogs and ducks play, others shake off",
      row="front", fx="sprinkler", visits=[V("smallbird", "bathe", 7, 31, "day"), V("frog", "sit", 25, 31),
                                           V("duck", "sit", 27, 31)])
def d_sprinkler(s, f):
    s.ellipse(16, 30, 4, 1.6, "#3a9a4a")
    s.rect(15, 25, 17, 29, "#e8c040")
    s.path([(17, 30), (30, 31)], .5, "#3a9a4a")


@item("swing_set", "Swing set", 250, "Play", "ground", "Birds ride the swings, which sway when they land",
      row="back", frames=4, visits=[V("smallbird", "ride", 10, 21), V("smallbird", "ride", 23, 21)])
def d_swing_set(s, f):
    s.path([(0, 31), (4, -3), (8, 31)], .7, BLUE)
    s.path([(24, 31), (28, -3), (32, 31)], .7, BLUE)
    board(s, 3, -4, 29, -3, RED)
    for x, k in ((10, 0), (23, 2)):
        d = sway(f + k, 2)
        s.line(x - 2, -2, x - 2 + d, 20, METAL_DK)
        s.line(x + 2, -2, x + 2 + d, 20, METAL_DK)
        board(s, x - 3 + d, 21, x + 3 + d, 21, YELLOW)


@item("seesaw", "Seesaw", 200, "Play", "ground", "Two animals ride it up and down",
      frames=4, visits=[V("smallmammal", "ride", 3, 23), V("smallmammal", "ride", 29, 23)])
def d_seesaw(s, f):
    s.poly([(12, 31), (20, 31), (16, 25)], RED)
    t = math.sin(f / 4 * 2 * math.pi) * 3
    s.path([(1, 25 + t), (31, 25 - t)], .9, YELLOW)
    for x, y in ((3, 25 + t), (29, 25 - t)):
        s.path([(x, y - 1), (x, y - 3)], .4, METAL_DK)


@item("slide", "Slide", 220, "Play", "ground", "Small animals slide down; otters especially",
      row="back", visits=[V("slider", "slide", 6, 3)])
def d_slide(s, f):
    s.path([(4, 31), (4, 3)], .7, METAL)
    s.path([(9, 31), (9, 3)], .7, METAL)
    for y in range(8, 31, 5):
        s.line(4, y, 9, y, METAL_DK)
    board(s, 3, 3, 10, 4, BLUE)
    s.path([(9, 4), (16, 12), (24, 25), (31, 29)], 1.2, YELLOW)


@item("sandbox", "Sandbox", 160, "Play", "ground", "Quail take dust baths; small animals dig",
      row="front", visits=[V("groundbird", "bathe", 12, 30, "day"), V("smallmammal", "dig", 22, 30)])
def d_sandbox(s, f):
    s.rect(1, 25, 31, 31, WOOD)
    s.rect(3, 25, 29, 28, "#ead29a", shade=False)
    s.ellipse(9, 26, 3, 1.5, "#e0c486", shade=False)
    s.poly([(20, 25), (24, 25), (22, 21)], RED)
    s.rect(25, 22, 27, 25, BLUE)


@item("tire_swing", "Tire swing", 180, "Play", "ground", "A raccoon sits in it and swings",
      row="back", frames=4, visits=[V("raccoon", "ride", 16, 23)])
def d_tire_swing(s, f):
    post(s, 2, -4, WOOD_DK, 2)
    board(s, 1, -5, 24, -3, WOOD_DK)
    d = sway(f, 2)
    s.line(18, -3, 16 + d, 18, "#d8c8a0")
    s.ellipse(16 + d, 23, 6, 4, "#2e2a30")
    s.ellipse(16 + d, 23, 3, 1.5, "#141016", shade=False)


# == Lights and night ===================================================================
@item("string_lights", "String lights", 250, "Lights and night", "ground",
      "Birds perch on the wire by day; moths gather at night", row="back", fx="lights",
      visits=[V("smallbird", "perch", 10, 4, "day"), V("smallbird", "perch", 22, 4, "day"), V("moth", "hover", 16, 4, "night")])
def d_string_lights(s, f):
    post(s, 1, -3, WOOD_DK, 2)
    post(s, 31, -3, WOOD_DK, 2)
    pts = [(1, -2), (6, 2), (11, 4), (16, 5), (21, 4), (26, 2), (31, -2)]
    s.path(pts, .4, "#3a3a44")
    for i, (x, y) in enumerate(pts[1:-1]):
        s.ellipse(x, y + 2, 1.2, 1.5, (GLOW, PINK, "#9ee8a0", "#a8d8ff", GLOW)[i])


@item("paper_lanterns", "Paper lanterns", 220, "Lights and night", "ground", "Moths flutter around them at night",
      row="back", fx="lanterns", visits=[V("moth", "hover", 8, 8, "night"), V("moth", "hover", 24, 8, "night")])
def d_paper_lanterns(s, f):
    post(s, 1, -4, WOOD_DK, 2)
    post(s, 31, -4, WOOD_DK, 2)
    s.path([(1, -3), (16, 1), (31, -3)], .4, "#3a3a44")
    for x, y, c in ((8, 3), (16, 5), (24, 3)) and ((8, 3, RED), (16, 5, ORANGE), (24, 3, RED)):
        s.ellipse(x, y + 2, 3, 3.5, c)
        s.rect(x - 1, y - 1.5, x + 1, y - 1, "#3a3a44")
        s.line(x - 2, y + 2, x + 2, y + 2, "#a83020")


@item("path_lights", "Garden path lights", 140, "Lights and night", "ground",
      "Frogs and toads wait under them at night to catch bugs", row="front", fx="pathlights",
      visits=[V("frog", "sit", 9, 31, "night"), V("frog", "sit", 23, 31, "night")])
def d_path_lights(s, f):
    for x in (5, 16, 27):
        post(s, x, 22, "#3a3a44", 1)
        s.rect(x - 2, 19, x + 2, 22, "#f0e8c0")
        s.poly([(x - 3, 19), (x, 17), (x + 3, 19)], "#3a3a44")


@item("glow_mushrooms", "Glowing mushrooms", 200, "Lights and night", "ground",
      "Glow at night; salamanders and frogs sit beside them", row="front", fx="glowshrooms",
      visits=[V("salamander", "sit", 16, 31, "night"), V("frog", "sit", 27, 31, "night")])
def d_glow_mushrooms(s, f):
    for x, y, r in ((6, 31, 3.5), (12, 30, 2.5), (19, 31, 4), (25, 30, 2)):
        mushroom(s, x, y, r, "#6ad0d8", dots=False, stem="#d8f4f0")
    s.px([(5, 26), (18, 26), (20, 25)], "#c8ffff")


@item("moon_lamp", "Moon lamp", 200, "Lights and night", "ground", "Owls and night birds perch on it",
      row="back", fx="moonglow", visits=[V("owl", "perch", 19, -3, "night"), V("nightbird", "perch", 19, -3, "night")])
def d_moon_lamp(s, f):
    post(s, 16, 8, "#3a3a44", 1.5)
    s.ellipse(16, 30, 4, 1.5, "#3a3a44")
    s.ellipse(16, 3, 6, 6, "#f6eebc")
    s.erase(s.m_ellipse(19, 1, 5, 5.5))
    s.px([(12, 3), (13, 6)], "#e0d498")


@item("telescope", "Telescope", 250, "Lights and night", "ground", "Owls perch on it at night",
      visits=[V("owl", "perch", 21, 8, "night")])
def d_telescope(s, f):
    for x in (10, 22):
        s.line(16, 17, x, 31, WOOD_DK)
    s.line(16, 17, 16, 31, WOOD_DK)
    s.path([(9, 22), (24, 9)], (1.6, 2.6), "#3a5a9a")
    s.path([(22, 11), (25, 8)], 2.8, "#c8a040")


@item("night_flowers", "Night flowers", 160, "Lights and night", "ground", "Open at dusk; moths and bats visit at night",
      row="front", visits=[V("moth", "hover", 10, 20, "night"), V("bat", "hover", 22, 14, "night")])
def d_night_flowers(s, f):
    for x, top in ((7, 22), (13, 19), (19, 21), (25, 18)):
        s.line(x, top, x, 31, LEAF_DK)
        s.ellipse(x - 2, 28, 2, .8, LEAF, rot=-30)
        s.ellipse(x, top - 1, 2.6, 2.2, "#f4f0ff")
        s.px([(x, top - 1)], "#f2e090")


@item("porch_light", "Porch light post", 120, "Lights and night", "ground", "Moths and bats circle it at night",
      row="back", fx="porchlight", visits=[V("moth", "hover", 16, 0, "night"), V("bat", "hover", 22, -4, "night")])
def d_porch_light(s, f):
    post(s, 16, 4, "#3a3a44", 1.5)
    s.ellipse(16, 30, 4, 1.5, "#3a3a44")
    s.rect(13, -3, 19, 4, "#f6e8a8")
    s.poly([(12, -3), (16, -7), (20, -3)], "#3a3a44")
    s.line(12, 4, 20, 4, "#3a3a44")


@item("hollow_log", "Hollow log", 120, "Lights and night", "ground", "Squirrels run through it; foxes nap inside",
      row="front", visits=[V("smallmammal", "through", 16, 31), V("fox", "hide", 16, 31)])
def d_hollow_log(s, f):
    s.path([(3, 26), (29, 26)], 5, "#8a5e3a")
    s.ellipse(3, 26, 2.5, 5, "#c89a68")
    s.ellipse(3, 26, 1.5, 3.6, "#2a1a10", shade=False)
    s.line(8, 23, 26, 23, "#6e4a2c")
    s.px([(14, 21), (15, 20), (22, 21)], LEAF)


@item("wind_chimes", "Wind chimes", 150, "Lights and night", "ground", "Sway with the wind; birds flutter off when they ring",
      row="back", frames=4, visits=[V("smallbird", "perch", 8, -2, "day")])
def d_wind_chimes(s, f):
    post(s, 4, -4, WOOD_DK, 2)
    board(s, 4, -4, 20, -3, WOOD_DK)
    s.ellipse(16, -1, 3, 1, WOOD)
    for i, x in enumerate((13, 15, 17, 19)):
        d = sway(f + i, 1)
        s.line(x, 0, x + d, 3, "#d8d8d8")
        s.rect(x + d, 3, x + d + .9, 8 + i % 2 * 3, "#c0c8d8")


# == Camping and explorers ==============================================================
@item("tent", "Camping tent", 300, "Camping and explorers", "ground", "A fox or raccoon peeks out and sleeps inside",
      row="back", fx="tentglow", visits=[V("fox", "home", 16, 31), V("raccoon", "home", 16, 31)])
def d_tent(s, f):
    s.poly([(0, 31), (16, 6), (32, 31)], "#e86a3a")
    s.poly([(11, 31), (16, 17), (21, 31)], "#5a2a18", shade=False)
    s.path([(16, 6), (16, 3)], .4, WOOD_DK)
    s.line(1, 31, 16, 7, "#f6a070")


@item("cabin", "Log cabin", 450, "Camping and explorers", "ground", "Squirrels run along the roof; birds nest under the eaves",
      row="back", fx="windows", visits=[V("squirrel", "perch", 9, 6), V("songbird", "perch", 30, 12, "day")])
def d_cabin(s, f):
    s.rect(2, 12, 30, 31, "#9a6a3e")
    for y in range(14, 31, 3):
        s.line(2, y, 30, y, "#74502e")
    roof(s, 0, 32, 12, -2, "#5e4a3a")
    s.rect(6, 17, 11, 22, GLOW)
    s.rect(20, 20, 25, 31, "#5e3e24")
    s.rect(24, -3, 27, 4, STONE_DK)


@item("canoe", "Canoe on the shore", 180, "Camping and explorers", "ground", "Turtles and frogs climb in",
      row="front", visits=[V("turtle", "sit", 12, 27), V("frog", "sit", 21, 27)])
def d_canoe(s, f):
    s.poly([(-2, 25), (34, 25), (29, 30), (3, 30)], "#2f8a6a")
    s.rect(2, 25, 30, 26, "#c8a060")
    s.path([(26, 23), (34, 31)], .5, WOOD)


@item("signpost", "Trail signpost", 90, "Camping and explorers", "ground", "Birds perch on the arrows; animals stop to look",
      visits=[V("bird", "perch", 25, 4, "day"), V("walker", "watch", 6, 31)])
def d_signpost(s, f):
    post(s, 16, -3, WOOD_DK, 2)
    s.poly([(10, 0), (26, 0), (29, 3), (26, 6), (10, 6)], WOOD_LT)
    s.poly([(22, 9), (6, 9), (3, 12), (6, 15), (22, 15)], WOOD_LT)
    s.line(12, 3, 23, 3, WOOD_DK)
    s.line(8, 12, 19, 12, WOOD_DK)


@item("trail_camera", "Trail camera", 200, "Camping and explorers", "ground",
      "Flashes and says \"Caught on camera!\" when an animal walks past", fx="camera",
      visits=[V("walker", "pose", 28, 31)])
def d_trail_camera(s, f):
    post(s, 12, 12, WOOD_DK, 3)
    s.rect(8, 10, 17, 19, "#4a5a3a")
    s.ellipse(16, 14, 2, 2, "#1a2030")
    s.px([(16, 13)], "#8ab0e0")
    s.rect(9, 11, 10, 12, "#e04030")


@item("salt_lick", "Salt lick", 120, "Camping and explorers", "ground", "Deer, elk, moose and sheep visit and lick it",
      row="front", visits=[V("deer", "drink", 1, 31), V("deer", "drink", 31, 31)])
def d_salt_lick(s, f):
    post(s, 16, 18, WOOD_DK, 3)
    s.rect(10, 20, 22, 26, "#ece6dc")
    s.ellipse(16, 20, 6, 1.2, "#faf6f0")


@item("duck_house", "Duck house", 180, "Camping and explorers", "pond", "Sits on the pond; ducks rest inside",
      visits=[V("duck", "home", 16, 30)])
def d_duck_house(s, f):
    s.rect(4, 26, 28, 29, WOOD_DK)
    s.rect(8, 15, 24, 26, "#e2c08a")
    roof(s, 7, 25, 16, 7, "#3e7a52")
    s.ellipse(16, 22, 3, 3.5, "#2a1c18", shade=False)
    s.ellipse(16, 30.5, 13, 1, WATER_LT, shade=False)


@item("lookout_tower", "Lookout tower", 450, "Camping and explorers", "ground", "Hawks and eagles perch on top",
      row="back", visits=[V("raptor", "perch", 16, -7)])
def d_lookout_tower(s, f):
    s.path([(6, 31), (11, -1)], .8, WOOD_DK)
    s.path([(26, 31), (21, -1)], .8, WOOD_DK)
    for y in (8, 18, 26):
        w = (31 - y) * .16
        s.line(7 + (31 - y) * .1 - w * 0 + 1, y, 25 - (31 - y) * .1, y, WOOD)
    s.path([(8, 26), (23, 8)], .4, WOOD)
    board(s, 8, -2, 24, 0, WOOD)
    roof(s, 9, 23, -4, -8, "#5e4a3a")


@item("fossil_dig", "Fossil dig", 260, "Camping and explorers", "ground", "Small animals dig there; lizards bask on the bones",
      row="front", visits=[V("lizard", "bask", 16, 26, "day"), V("smallmammal", "dig", 28, 31)])
def d_fossil_dig(s, f):
    s.ellipse(16, 29, 15, 3.5, "#b88a5a")
    s.path([(4, 28), (8, 26), (14, 26), (20, 27), (27, 28)], .9, "#f0e6d0")
    for x in (8, 11, 14, 17):
        s.path([(x, 26), (x - 1, 22), (x + 2, 20)], .5, "#f0e6d0")
    s.ellipse(27, 27, 3, 2, "#f0e6d0")
    s.px([(26, 27)], "#3a2a20")
    s.path([(30, 31), (33, 22)], .4, WOOD)


@item("rock_pile", "Rock pile", 100, "Camping and explorers", "ground", "Chipmunks, pikas and marmots sit on top as lookouts",
      visits=[V("lookout", "sit", 15, 15)])
def d_rock_pile(s, f):
    for x, y, rx, ry in ((7, 27, 7, 5), (24, 27, 8, 5), (15, 22, 7, 6), (11, 17, 4, 3), (19, 17, 4, 3)):
        s.ellipse(x, y, rx, ry, STONE if x % 2 else STONE_DK)


# == Farm and village ===================================================================
@item("barn", "Red barn", 450, "Farm and village", "ground", "Barn owls sleep in the loft and fly out at night",
      row="back", visits=[V("owl", "home", 16, 5), V("bird", "perch", 16, -7, "day")])
def d_barn(s, f):
    s.rect(2, 12, 30, 31, "#c0392b")
    s.poly([(0, 13), (6, 2), (16, -5), (26, 2), (32, 13)], "#7a3a30")
    s.rect(9, 18, 23, 31, WHITE)
    s.rect(10, 19, 22, 31, "#9a2a20")
    s.line(10, 19, 22, 31, WHITE)
    s.line(22, 19, 10, 31, WHITE)
    s.rect(13, 3, 19, 8, "#2a1410")


@item("hay_bales", "Hay bales", 90, "Farm and village", "ground", "Rabbits and deer nibble; mice hide",
      visits=[V("rabbit", "eat", 3, 31), V("deer", "eat", 30, 31), V("mouse", "hide", 16, 31)])
def d_hay_bales(s, f):
    for x0, y0, x1, y1 in ((2, 23, 15, 31), (17, 23, 30, 31), (9, 15, 23, 23)):
        s.rect(x0, y0, x1, y1, "#e8c45a")
        s.line(x0, (y0 + y1) // 2, x1, (y0 + y1) // 2, "#c8a040")
        s.px([(x0 + 3, y0 + 2), (x1 - 3, y1 - 2)], "#f6dc8a")


@item("wheelbarrow", "Wheelbarrow of flowers", 100, "Farm and village", "ground", "Butterflies and bees visit",
      visits=[V("bug", "hover", 12, 13, "day"), V("bee", "hover", 20, 14, "day")])
def d_wheelbarrow(s, f):
    s.poly([(3, 18), (24, 18), (21, 26), (7, 26)], "#4f8f6a")
    for x, c in ((6, PINK), (10, YELLOW), (14, WHITE), (18, PURPLE), (22, RED)):
        s.ellipse(x, 17, 2, 1.8, c)
        s.px([(x, 17)], YELLOW if c != YELLOW else ORANGE)
    s.ellipse(9, 28, 3, 3, "#3a3440")
    s.path([(23, 22), (31, 25)], .6, WOOD)
    s.line(20, 26, 21, 31, METAL_DK)


@item("nut_basket", "Nut basket", 90, "Farm and village", "ground", "Squirrels and jays carry nuts off and bury them",
      row="front", visits=[V("squirrel", "eat", 4, 31), V("jay", "eat", 27, 31, "day")])
def d_nut_basket(s, f):
    s.poly([(8, 23), (24, 23), (22, 31), (10, 31)], "#c8964a")
    for y in (25, 28):
        s.line(9, y, 23, y, "#9a6a34")
    for x in (11, 14, 17, 20, 13, 18):
        s.ellipse(x, 22 - (x % 3 == 0), 1.6, 1.4, "#8a5a2a")
    s.path([(9, 23), (16, 15), (23, 23)], .5, "#9a6a34")


@item("shed", "Garden shed", 300, "Farm and village", "ground", "Animals shelter under the roof when it rains",
      row="back", visits=[V("walker", "shelter", 4, 31), V("walker", "shelter", 28, 31)])
def d_shed(s, f):
    s.rect(5, 10, 27, 31, "#6a9ab8")
    for x in range(7, 27, 3):
        s.line(x, 11, x, 31, "#5a88a4")
    s.poly([(-1, 11), (16, 1), (33, 11)], "#4a4a54")
    s.rect(12, 17, 20, 31, WHITE)
    s.rect(13, 18, 19, 31, "#5a88a4")
    s.px([(18, 24)], YELLOW)


@item("greenhouse", "Greenhouse", 400, "Farm and village", "ground", "Butterflies and hummingbirds visit the flowers inside",
      row="back", visits=[V("butterfly", "hover", 9, 16, "day"), V("hummingbird", "hover", 24, 12, "day")])
def d_greenhouse(s, f):
    s.rect(2, 10, 30, 31, "#cfeef0", shade=False)
    s.poly([(1, 11), (16, -1), (31, 11)], "#dff6f6", shade=False)
    for x in (2, 9, 16, 23, 30):
        s.line(x, 10, x, 31, WHITE)
    s.line(1, 10, 31, 10, WHITE)
    s.line(1, 11, 16, -1, WHITE)
    s.line(31, 11, 16, -1, WHITE)
    for x, c in ((5, RED), (12, PINK), (20, YELLOW), (27, PURPLE)):
        bush(s, x, 27, 3, 3, LEAF)
        s.ellipse(x, 24, 1.4, 1.2, c)


@item("mailbox", "Mailbox", 90, "Farm and village", "ground", "A small bird nests in it and pops out",
      visits=[V("smallbird", "home", 16, 12)])
def d_mailbox(s, f):
    post(s, 16, 18, WOOD_DK, 2)
    s.rect(8, 10, 24, 18, "#4a7ac8")
    s.ellipse(16, 10, 8, 3.5, "#4a7ac8")
    s.rect(24, 9, 25, 15, RED)
    s.rect(24, 9, 27, 11, RED)
    s.ellipse(9, 14, 2, 2.5, "#1e2238", shade=False)


@item("fence", "Picket fence", 100, "Farm and village", "ground", "Birds perch along it; squirrels run along the top",
      row="back", visits=[V("bird", "perch", 6, 17, "day"), V("bird", "perch", 22, 17, "day"), V("squirrel", "perch", 14, 17)])
def d_fence(s, f):
    board(s, -2, 21, 34, 22, WHITE)
    board(s, -2, 27, 34, 28, WHITE)
    for x in range(-1, 34, 4):
        s.poly([(x, 31), (x, 18), (x + 1, 16.5), (x + 2, 18), (x + 2, 31)], WHITE)


# == Sky ================================================================================
@item("balloon", "Hot air balloon", 500, "Sky", "sky", "Drifts across by day; birds fly alongside and ride the basket",
      fx="drift", visits=[V("flier", "ride", 16, 26, "day")])
def d_balloon(s, f):
    s.ellipse(16, 6, 13, 13, RED)
    for x, c in ((10, YELLOW), (22, YELLOW)):
        s.paint(s.m_ellipse(x, 6, 3.5, 13), c, within=s.m_ellipse(16, 6, 13, 13))
    s.paint(s.m_ellipse(16, 6, 3, 13), WHITE, within=s.m_ellipse(16, 6, 13, 13))
    s.line(9, 16, 13, 26, "#5e4028")
    s.line(23, 16, 19, 26, "#5e4028")
    s.rect(12, 26, 20, 31, "#a8743f")


@item("paper_plane", "Paper airplane", 150, "Sky", "sky", "Glides past now and then; birds chase it",
      fx="glide", visits=[V("flier", "escort", 10, 0, "day")])
def d_paper_plane(s, f):
    s.poly([(4, 18), (28, 13), (14, 20)], WHITE)
    s.poly([(14, 20), (28, 13), (16, 23)], "#d8d8e0")


@item("windsock", "Windsock", 100, "Sky", "ground", "Points with the real wind; birds perch on its pole",
      row="back", frames=4, visits=[V("bird", "perch", 4, -6, "day")])
def d_windsock(s, f):
    post(s, 4, -6, METAL_DK, 1.5)
    s.ellipse(4, 30, 3, 1.2, STONE_DK)
    droop = math.radians((70, 45, 20, 4)[f])  # still air hangs down; a strong wind holds it out
    for i in range(5):
        t = i / 5
        x, y = 5.5 + math.cos(droop) * (2 + t * 14), -4 + math.sin(droop) * (2 + t * 14)
        s.ellipse(x, y, 2, 2.8 - t * 1.4, ORANGE if i % 2 == 0 else WHITE, rot=math.degrees(droop))


@item("weathervane", "Weathervane", 200, "Sky", "ground", "A bird rides it as it turns with the wind",
      row="back", frames=4, visits=[V("bird", "perch", 16, -6, "day")])
def d_weathervane(s, f):
    s.ellipse(16, 30, 5, 1.5, STONE_DK)
    post(s, 16, 4, METAL_DK, 1.2)
    s.line(10, 9, 22, 9, METAL_DK)
    s.px([(9, 9), (23, 9)], "#c8a040")
    s.ellipse(16, 3, 1.5, 1.5, "#c8a040")
    w = [10, 7, 3, 7][f]  # the arrow turning, seen from the side
    s.line(16 - w, 0, 16 + w, 0, "#2e2a30")
    if w > 3:
        s.poly([(16 - w - 3, 0), (16 - w + 1, -2.5), (16 - w + 1, 2.5)], "#2e2a30")
        s.poly([(16 + w - 2, 0), (16 + w + 2, -4), (16 + w + 3, -4), (16 + w + 3, 4), (16 + w + 2, 4)], "#2e2a30")
    else:
        s.ellipse(16, 0, 1.6, 3, "#2e2a30")


# == Landmarks ==========================================================================
@item("gnome", "Garden gnome", 100, "Landmarks", "ground", "Animals sniff it; a bird sits on its hat",
      visits=[V("smallbird", "perch", 16, 8, "day"), V("walker", "watch", 28, 31)])
def d_gnome(s, f):
    s.ellipse(16, 25, 5, 6, "#3a6ad0")
    s.ellipse(16, 18, 3.5, 3, "#f6c8a0")
    s.poly([(16, 26), (12, 19), (20, 19)], WHITE)
    s.poly([(11, 17), (21, 17), (16, 8)], RED)
    s.rect(12, 29, 15, 31, "#5a3a20")
    s.rect(17, 29, 20, 31, "#5a3a20")
    s.px([(15, 18), (17, 18)], "#2a2030")


@item("owl_statue", "Stone owl statue", 150, "Landmarks", "ground", "Real owls perch beside it",
      visits=[V("owl", "perch", 25, 23, "night")])
def d_owl_statue(s, f):
    s.rect(9, 24, 23, 31, STONE_DK)
    s.ellipse(16, 18, 6, 7, STONE)
    s.poly([(10, 12), (12, 9), (13, 12)], STONE)
    s.poly([(22, 12), (20, 9), (19, 12)], STONE)
    for x in (13, 19):
        s.ellipse(x, 15, 2, 2, STONE_LT)
        s.px([(x, 15)], "#4a4640")
    s.px([(16, 17), (16, 18)], STONE_DK)


@item("sundial", "Sundial", 160, "Landmarks", "ground", "Lizards bask on it; its shadow follows the real sun",
      fx="sundial", visits=[V("lizard", "bask", 13, 18, "day")])
def d_sundial(s, f):
    s.rect(12, 20, 20, 31, STONE)
    s.ellipse(16, 30, 6, 1.5, STONE_DK)
    s.ellipse(16, 19, 9, 2.2, STONE_LT)
    s.poly([(16, 19), (16, 13), (20, 19)], "#c8a040")


@item("golden_acorn", "Golden acorn statue", 1000, "Landmarks", "ground", "Squirrels gather around it; it sparkles",
      row="back", fx="sparkle", visits=[V("squirrel", "watch", 4, 31), V("squirrel", "watch", 28, 31), V("jay", "perch", 16, -3)])
def d_golden_acorn(s, f):
    s.rect(8, 25, 24, 31, STONE)
    s.rect(7, 24, 25, 25, STONE_LT)
    s.ellipse(16, 15, 7, 8.5, "#f2c440")
    s.ellipse(16, 6, 8.5, 4, "#c8901c")
    s.path([(16, 3), (17, -1)], .8, "#c8901c")
    s.px([(13, 11), (13, 12), (12, 14)], "#fff2b0")


# == The shop's first three, redrawn ====================================================
@item("flowers", "Flower bed", 100, "Garden", "ground", "Butterflies and bees visit",
      row="front", visits=[V("bug", "hover", 10, 22, "day"), V("bee", "hover", 22, 23, "day")])
def d_flowers(s, f):
    s.rect(1, 27, 31, 31, SOIL)
    board(s, 0, 30, 32, 31, WOOD_DK)
    for x, col, h in ((4, RED, 23), (9, YELLOW, 21), (14, PURPLE, 24), (19, WHITE, 22), (24, PINK, 23), (28, ORANGE, 21)):
        s.line(x, h + 1, x, 28, LEAF_DK)
        s.ellipse(x - 1, 26, 1.4, .7, LEAF, rot=-30)
        s.ellipse(x, h, 2, 1.8, col)
        s.px([(x, h)], YELLOW if col != YELLOW else ORANGE)


@item("birdbath", "Bird bath", 150, "Water", "ground", "Birds drink and splash in it",
      visits=[V("smallbird", "bathe", 10, 16, "day"), V("smallbird", "bathe", 22, 16, "day")])
def d_birdbath(s, f):
    s.ellipse(16, 30, 6, 1.6, STONE_DK)
    s.rect(14, 18, 18, 30, STONE)
    s.ellipse(16, 17, 10, 2.6, STONE_LT)
    s.ellipse(16, 16.5, 8, 1.4, WATER, shade=False)


@item("lantern", "Lantern", 200, "Lights and night", "ground", "Moths flutter around it at night",
      row="back", fx="lanternglow", visits=[V("moth", "hover", 16, 2, "night")])
def d_lantern(s, f):
    post(s, 16, 4, "#3a3a44", 1.5)
    s.ellipse(16, 30, 4, 1.5, "#3a3a44")
    s.rect(12, -2, 20, 7, "#f6e8a8")
    s.rect(12, -2, 20, -1, "#3a3a44")
    s.rect(12, 6, 20, 7, "#3a3a44")
    s.line(16, -1, 16, 6, "#3a3a44")
    s.poly([(11, -2), (16, -6), (21, -2)], "#3a3a44")


ORDER = ["flowers", "birdbath", "lantern"]  # the first three keep their place at the top of the shop


def render(it) -> Image.Image:
    sheet = Image.new("RGBA", (N * it["frames"], N))
    for f in range(it["frames"]):
        s = Sprite()
        it["draw"](s, f)
        sheet.paste(s.render(), (f * N, 0))
    return sheet


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--sheet", type=Path, help="also write a preview of every decoration here")
    ap.add_argument("--only", help="comma-separated keys to draw (for quick previews)")
    args = ap.parse_args()
    items = sorted(ITEMS, key=lambda it: (it["key"] not in ORDER, ORDER.index(it["key"]) if it["key"] in ORDER else 0))
    keys = [it["key"] for it in items]
    assert len(keys) == len(set(keys)), "duplicate decoration key"
    if args.only:
        items = [it for it in items if it["key"] in args.only.split(",")]
    OUT.mkdir(parents=True, exist_ok=True)
    sheets = {}
    for it in items:
        sheets[it["key"]] = render(it)
        if not args.only:
            sheets[it["key"]].save(OUT / f"{it['key']}.png", optimize=True)
    if not args.only:
        catalog = [{k: v for k, v in it.items() if k != "draw" and v not in (None, [])} for it in items]
        CATALOG.write_text(json.dumps(catalog, indent=1) + "\n")
        print(f"{len(catalog)} decorations")
    if args.sheet:
        cols, scale = 10, 3
        rows = math.ceil(len(items) / cols)
        prev = Image.new("RGBA", (cols * N * scale, rows * N * scale), (120, 178, 96, 255))
        for i, it in enumerate(items):
            first = sheets[it["key"]].crop((0, 0, N, N)).resize((N * scale, N * scale), Image.NEAREST)
            prev.alpha_composite(first, ((i % cols) * N * scale, (i // cols) * N * scale))
        args.sheet.parent.mkdir(parents=True, exist_ok=True)
        prev.save(args.sheet)


if __name__ == "__main__":
    main()
