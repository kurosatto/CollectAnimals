"""Draw the things in the minigames (rocks, logs, storm clouds, food...) as pixel art.

    python tools/make_game_art.py                    # species/sprites/game/atlas.png + atlas.json
    python tools/make_game_art.py --sheet sheet.png  # also a big preview of every piece

Every piece is drawn on the animals' canvas (tools/pixel.py) with the same shading and
outline, so the games look like the animals that play them. The pieces are packed into
one atlas; atlas.json says where each one is and its anchor, the point minigames.js
puts at the thing's position. Pieces marked as tiles are cut out of a wider drawing
so they repeat without seams (a long ledge is a left end, middles and a right end).
"""
from __future__ import annotations

import argparse
import json
import math
from contextlib import contextmanager
from pathlib import Path

import numpy as np
from PIL import Image

import pixel
from pixel import PAD_TOP, PAD_X, Sprite

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "species" / "sprites" / "game"

STONE, STONE_DK, STONE_LT = "#8f94a3", "#6a6f80", "#b4b9c6"
BARK, BARK_DK, BARK_LT = "#8a5a35", "#5e3c22", "#a8744a"
WOODCUT, WOODCUT_DK = "#e0bb84", "#b88a54"
LEAF, LEAF_DK, LEAF_LT = "#4f9a48", "#2f6e3a", "#79bd5e"
MOSS, MOSS_LT = "#5c9e4a", "#86c46a"
SOIL, SOIL_DK = "#7a5232", "#4f3620"
CLOUD, CLOUD_DK, CLOUD_LT = "#7a7f92", "#5b6075", "#9da2b4"
WATER, WATER_LT = "#3a8fc0", "#8cc8ee"
SAND = "#d9c18a"
RED, YELLOW = "#d8493b", "#f2c14e"

PIECES: list[dict] = []


def piece(name, anchor, crop=None, size=None, **kw):
    """Register a piece. anchor: the grid point minigames.js places at the thing's
    position. crop: (x0, y0, x1, y1) in grid coordinates for tiles, else the drawing's
    own bounds. size: a bigger canvas than the animals' for big things (a feeder, a
    nest). Other keywords are passed to the drawing."""
    def deco(fn):
        PIECES.append({"name": name, "anchor": anchor, "crop": crop, "size": size, "draw": fn, "kw": kw})
        return fn
    return deco


@contextmanager
def canvas(n):
    """Draw on an n x n canvas instead of the animals' 40 x 40 (same padding)."""
    old = pixel.N, pixel._XS, pixel._YS
    ys, xs = np.mgrid[0:n, 0:n].astype(np.float32) + 0.5
    pixel.N, pixel._YS, pixel._XS = n, ys - PAD_TOP, xs - PAD_X
    try:
        yield
    finally:
        pixel.N, pixel._XS, pixel._YS = old


def lumps(s, cx, cy, rx, ry, col, n=5, seed=0):
    """A lumpy blob: a few overlapping ellipses."""
    s.ellipse(cx, cy, rx, ry, col)
    for i in range(n):
        a = (i / n + seed * .13) * 2 * math.pi
        s.ellipse(cx + math.cos(a) * rx * .45, cy + math.sin(a) * ry * .4 - ry * .1, rx * .6, ry * .6, col)


def mix(a, b, t):
    a, b = pixel.rgb(a), pixel.rgb(b)
    return "#%02x%02x%02x" % tuple(round(a[i] * (1 - t) + b[i] * t) for i in range(3))


def speck(s, pts, col):
    s.px(pts, col)


# == Trail Run ========================================================================
@piece("rock", (16, 31))
def p_rock(s):
    s.ellipse(16, 27, 7, 4.6, STONE)
    s.ellipse(14, 25, 4.5, 3.4, STONE_LT)
    s.ellipse(19, 28, 3, 2.2, STONE_DK)
    speck(s, [(13, 24), (14, 24)], "#d6d9e2")
    speck(s, [(18, 26), (11, 28), (20, 29)], "#5e6272")
    s.px([(10, 30), (11, 30), (12, 31)], MOSS)
    s.px([(21, 31), (22, 30)], MOSS_LT)


@piece("log", (16, 31))
def p_log(s):
    s.rect(5, 23, 25, 31, BARK)
    for x in (8, 13, 18, 22):
        s.line(x, 24, x + 1, 30, BARK_DK)
    s.line(6, 24, 24, 24, BARK_LT)
    s.ellipse(26, 27, 3, 4.4, WOODCUT, shade=False)
    s.ellipse(26, 27, 1.8, 2.8, WOODCUT_DK, shade=False)
    s.px([(26, 27)], WOODCUT)
    s.px([(9, 22), (10, 22), (16, 22), (17, 22), (11, 23)], MOSS)
    s.px([(12, 21)], MOSS_LT)


@piece("stump", (16, 31))
def p_stump(s):
    s.rect(11, 12, 21, 31, BARK)
    s.poly([(9, 31), (11, 27), (11, 31)], BARK)
    s.poly([(23, 31), (21, 27), (21, 31)], BARK)
    for x in (13, 16, 19):
        s.line(x, 14, x, 30, BARK_DK)
    s.ellipse(16, 12, 5.4, 2, WOODCUT, shade=False)
    s.ellipse(16, 12, 3, 1, WOODCUT_DK, shade=False)
    s.px([(16, 12)], WOODCUT)
    s.px([(11, 20), (11, 21), (12, 21)], MOSS)
    s.ellipse(20, 25, 1.4, 1, "#e6d0a0")  # a little mushroom
    s.px([(20, 26)], "#f3efe4")


@piece("acorn", (16, 28))
def p_acorn(s):
    s.ellipse(16, 28.5, 2.6, 3, "#c98a3e")
    s.ellipse(16, 25.5, 3.4, 1.8, "#6b4426")
    s.px([(14, 25), (16, 25), (18, 25)], "#8a5a35")
    s.px([(16, 23)], "#4f3620")
    s.px([(15, 28)], "#f0c27a")


@piece("berry", (16, 28))
def p_berry(s):
    for x, y in ((14.5, 28.5), (17.5, 28.5), (16, 26.5), (16, 29.8)):
        s.ellipse(x, y, 1.7, 1.7, "#c8313b")
    s.px([(14, 28), (17, 26)], "#ff8a90")
    s.poly([(15, 24), (18, 23), (17, 25)], LEAF)


@piece("ledge_l", (16, 26), crop=(10, 21, 15, 30))
@piece("ledge_m", (16, 26), crop=(16, 21, 23, 30))
@piece("ledge_r", (16, 26), crop=(24, 21, 29, 30))
def p_ledge(s):
    # A mossy stone shelf, drawn long and cut into ends and a middle.
    s.rect(12, 23, 27, 27, "#8a7a66")
    s.poly([(12, 27), (27, 27), (25, 29), (14, 29)], "#6e604f")
    s.rect(11, 21, 28, 23, MOSS)
    s.line(12, 21, 27, 21, MOSS_LT)
    for x in (14, 18, 21, 25):
        s.px([(x, 25), (x + 1, 25)], "#a89884")
    for x, h in ((13, 2), (17, 3), (20, 1), (24, 2), (26, 1)):
        s.line(x, 28, x, 28 + h, LEAF_DK)


@piece("stone", (16, 28))
def p_stone(s):
    s.ellipse(16, 28, 11, 2.6, STONE)
    s.ellipse(13, 27, 6, 1.6, STONE_LT)
    speck(s, [(10, 27), (11, 27)], "#d6d9e2")
    s.px([(22, 29), (23, 28)], MOSS)


@piece("thorn_m", (16, 31), crop=(10, 20, 23, 31))
def p_thorns(s):
    for x in range(6, 28, 5):
        s.ellipse(x, 27, 4, 3.4, "#3b5a2e")
    for x in range(8, 28, 5):
        s.ellipse(x, 25.5, 2.4, 2, "#2c4423")
    for x in range(6, 28, 3):
        s.line(x, 23 - (x % 2), x, 22 - (x % 2) - 1, "#d8cfb0")
    s.px([(9, 26), (15, 28), (21, 26), (12, 29), (18, 27)], "#c0392b")
    s.px([(9, 25), (21, 25)], "#ff7a6a")


@piece("branch", (16, 25))
def p_branch(s):
    s.path([(-2, 25), (16, 24.5), (34, 25.5)], 1.6, BARK)
    s.line(0, 24, 32, 24, BARK_LT)
    s.path([(6, 24), (4, 21)], .7, BARK)
    s.path([(25, 25), (28, 22)], .7, BARK)
    for x, y, r in ((3, 20, 3.2), (9, 22, 2.6), (16, 21, 3), (23, 22, 2.8), (29, 20, 3.2)):
        s.ellipse(x, y, r, r * .8, LEAF)
        s.ellipse(x - .8, y - .8, r * .55, r * .45, LEAF_LT)
    s.px([(12, 27), (12, 28), (20, 27)], LEAF_DK)


@piece("canopy", (16, 31), crop=(8, 22, 23, 31))
def p_canopy(s):
    for x in range(2, 32, 6):
        s.ellipse(x, 27, 5, 4, LEAF_DK)
        s.ellipse(x + 1, 25.5, 3, 2.4, LEAF)
    s.px([(5, 24), (17, 24), (11, 25)], LEAF_LT)


@piece("pine0", (16, 31))
@piece("pine1", (16, 31), tall=True)
def p_pine(s, tall=False):
    s.rect(15, 26, 17, 31, BARK)
    top = 3 if tall else 9
    tiers = 4 if tall else 3
    for i in range(tiers):
        y0 = top + i * (22 - top) / tiers
        y1 = y0 + (22 - top) / tiers + 5
        w = 3 + i * 2.6
        s.poly([(16, y0), (16 + w, y1), (16 - w, y1)], "#2f7d4f")
        s.px([(round(16 - w * .5), round(y1 - 1))], "#3f9d5e")
    s.px([(16, top)], "#3f9d5e")


@piece("bush", (16, 31))
def p_bush(s):
    for x, y, r in ((11, 27, 4.5), (16, 25, 5.5), (21, 27, 4.5)):
        s.ellipse(x, y, r, r * .8, LEAF)
    s.ellipse(14, 24, 2, 1.5, LEAF_LT)
    s.px([(12, 27), (19, 26)], "#e86a8a")


# == Sky Glide ========================================================================
@piece("storm_m", (16, 21), crop=(4, 17, 29, 26))
def p_storm_mid(s):
    s.rect(2, 10, 31, 31, CLOUD)
    for y in (17, 22):
        for x in (3, 30):
            s.ellipse(x, y + (x % 3), 3.6, 3, CLOUD_LT if x < 16 else CLOUD)
    s.px([(9, 19), (10, 19), (20, 23), (21, 23), (14, 25)], CLOUD_DK)
    s.px([(7, 23), (17, 18)], CLOUD_LT)


@piece("storm_down", (16, 18))
def p_storm_down(s):
    # The puffy end of a storm wall that hangs down from the top, with a raindrop.
    s.rect(4, 10, 28, 18, CLOUD)
    for x, r in ((6, 4.6), (16, 6.2), (26, 4.6)):
        s.ellipse(x, 19, r, r * .8, CLOUD)
    s.ellipse(12, 17, 3, 2.2, CLOUD_LT)
    s.ellipse(22, 22, 3, 1.6, CLOUD_DK)
    s.line(4, 24, 28, 24, CLOUD_DK)


@piece("storm_up", (16, 22))
def p_storm_up(s):
    s.rect(4, 22, 28, 31, CLOUD)
    for x, r in ((6, 4.6), (16, 6.2), (26, 4.6)):
        s.ellipse(x, 21, r, r * .8, CLOUD)
    s.ellipse(12, 18, 3, 2, CLOUD_LT)
    s.ellipse(20, 17, 2, 1.4, CLOUD_LT)


@piece("cloud", (16, 26))
def p_cloud(s):
    s.ellipse(16, 27, 13, 4, CLOUD)
    s.ellipse(11, 24, 6, 4.2, CLOUD)
    s.ellipse(19, 23, 5, 4, CLOUD_LT)
    s.line(5, 30, 27, 30, CLOUD_DK)


@piece("puff", (16, 26))
def p_puff(s):
    s.ellipse(16, 27, 12, 3.4, "#f4fbff", shade=False)
    s.ellipse(11, 24.5, 5, 3.4, "#ffffff", shade=False)
    s.ellipse(19, 24, 4.4, 3.4, "#ffffff", shade=False)
    s.line(6, 29, 26, 29, "#d8eaf4")


# == River Swim =======================================================================
@piece("roots_m", (16, 21), crop=(5, 16, 26, 25))
def p_roots_mid(s):
    s.rect(3, 10, 28, 31, "#5b4030")
    for x in (7, 12, 18, 23):
        s.line(x, 10, x + (1 if x % 2 else -1), 31, "#3f2a1c")
    s.line(6, 10, 6, 31, "#7a5a40")
    s.px([(14, 18), (15, 19), (20, 22)], "#7a5a40")


@piece("roots_end", (16, 22))
def p_roots_end(s):
    s.rect(5, 16, 26, 22, "#5b4030")
    s.line(6, 16, 6, 22, "#7a5a40")
    for x, h in ((7, 5), (11, 7), (15, 4), (19, 8), (23, 5)):
        s.path([(x, 22), (x + (1 if x % 3 else -1), 22 + h)], .6, "#5b4030")
    s.px([(11, 29), (19, 30)], "#3f8d58")


@piece("boulder_m", (16, 21), crop=(5, 16, 26, 25))
def p_boulder_mid(s):
    s.rect(3, 10, 28, 31, "#6e7380")
    s.line(6, 10, 6, 31, "#8a8f9e")
    s.px([(12, 17), (13, 17), (20, 21), (16, 24), (9, 22)], "#5a5f6c")
    s.px([(18, 18), (10, 19)], "#9ea3b0")


@piece("boulder_top", (16, 24))
def p_boulder_top(s):
    s.rect(5, 26, 26, 31, "#6e7380")
    s.ellipse(15.5, 25.5, 10.5, 3.6, "#8a8f9e")
    s.ellipse(12, 24.5, 4, 1.4, "#a8adba")
    s.px([(8, 22), (9, 22), (10, 22), (9, 21)], "#3f8d58")
    s.px([(21, 23), (22, 22)], "#58a662")


@piece("snag", (16, 26))
def p_snag(s):
    s.path([(3, 27), (16, 26), (29, 25)], 2.2, "#5b4030")
    s.line(4, 25, 28, 24, "#7a5a40")
    s.path([(10, 25), (7, 20)], .8, "#5b4030")
    s.path([(20, 27), (23, 31)], .8, "#5b4030")
    s.path([(25, 25), (28, 21)], .6, "#5b4030")
    s.px([(14, 28), (15, 29), (22, 26)], "#3f8d58")


@piece("snack", (16, 28))
def p_snack(s):
    # A little shrimp.
    s.path([(13, 27), (15, 29), (18, 29), (19, 27)], 1.2, "#f2a541")
    s.px([(14, 26), (13, 25)], "#d87a2a")
    s.px([(18, 28)], "#222222")
    s.px([(15, 28), (17, 28)], "#ffd28a")


@piece("can", (16, 30))
def p_can(s):
    s.rect(13, 24, 19, 31, "#c9ced8")
    s.rect(13, 26, 19, 29, "#d9534f")
    s.line(13, 24, 19, 24, "#9aa0ad")
    s.px([(15, 27), (16, 27)], "#ffffff")


@piece("bottle", (16, 30))
def p_bottle(s):
    s.rect(14, 25, 18, 31, "#86c9a4")
    s.rect(15, 22, 17, 24, "#86c9a4")
    s.rect(15, 21, 17, 21, "#4f8fdc", shade=False)
    s.line(15, 26, 15, 30, "#d8f4e4")


@piece("bag", (16, 30))
def p_bag(s):
    s.poly([(11, 31), (21, 31), (20, 25), (12, 25)], "#e8ecef")
    s.rect(12, 23, 13, 25, "#e8ecef")
    s.rect(19, 23, 20, 25, "#e8ecef")
    s.line(13, 28, 19, 29, "#c4ccd2")


# == Trail Run: the creek ==============================================================
@piece("creek_l", (16, 21), crop=(4, 21, 11, 60), size=64)
@piece("creek_m", (16, 21), crop=(14, 21, 27, 60), size=64)
@piece("creek_r", (16, 21), crop=(40, 21, 47, 60), size=64)
def p_creek(s):
    # A creek cut into the trail, drawn wide and cut into banks and a middle that repeats.
    s.rect(-4, 21, 60, 60, SOIL)
    s.rect(7, 21, 44, 60, SOIL_DK)
    s.rect(9, 30, 42, 60, WATER, shade=False)
    s.rect(9, 30, 42, 31, WATER_LT, shade=False)
    for x, y in ((12, 36), (19, 41), (26, 35), (33, 44), (16, 49), (29, 52), (38, 38)):
        s.line(x, y, x + 3, y, "#62aedc")
    for x, y in ((14, 46), (24, 47), (36, 50)):
        s.ellipse(x, y + 6, 2.4, 1.4, STONE_DK)
    for y in (24, 28, 33, 39):
        s.px([(6, y), (7, y + 1)], "#9a7048")
        s.px([(44, y + 1), (45, y)], "#9a7048")
    s.px([(5, 22), (6, 22), (45, 22), (46, 22)], MOSS)


# == Claw Capture and the sea games: what's caught ======================================
def fish(s, body, belly, fin, spots=None, long=1.0):
    s.poly([(18 - 6 * long, 26), (14 - 8 * long, 22.5), (14 - 8 * long, 29.5)], fin)
    s.ellipse(17, 26, 6.2 * long, 3.2, body)
    s.ellipse(17.5, 27.8, 4.6 * long, 1.2, belly, shade=False)
    s.poly([(14, 23.4), (17, 21.6), (19, 23.2)], fin)
    s.poly([(16, 28.4), (18, 30.4), (19, 28.4)], fin)
    s.line(round(17 + 3.8 * long), 24, round(17 + 3.8 * long), 28, mix(body, "#000000", .25))
    for x, y in spots or []:
        s.px([(x, y)], mix(body, "#000000", .35))
    s.px([(round(18.5 + 4 * long), 25)], "#1d1428")


@piece("fish", (16, 26))
def p_fish(s):
    fish(s, "#9cb8d0", "#e8f2f8", "#6f8fae", spots=[(14, 25), (16, 24)])


@piece("fish_gold", (16, 26))
def p_fish_gold(s):
    fish(s, "#f2a541", "#ffe0a8", "#d8742a", spots=[(15, 25)])


@piece("salmon", (16, 26))
def p_salmon(s):
    fish(s, "#e8806a", "#f8d8c8", "#b8584a", spots=[(13, 24), (16, 24), (19, 24), (14, 26)], long=1.25)


@piece("mouse", (16, 27))
def p_mouse(s):
    s.path([(10, 28), (7, 27), (5, 25)], .6, "#d8a0a0")
    s.ellipse(15, 27, 5, 3.2, "#a09a98")
    s.ellipse(20, 26, 3, 2.4, "#a09a98")
    s.ellipse(19, 23.4, 1.6, 1.6, "#b8b2b0")
    s.px([(19, 23)], "#e8a8b0")
    s.ellipse(15, 28.6, 3.4, 1, "#d8d4d0", shade=False)
    s.px([(23, 26)], "#e88a9a")
    s.px([(21, 25)], "#1d1428")


@piece("fly", (16, 26))
def p_fly(s):
    s.ellipse(13.5, 23.5, 2.6, 1.8, "#d8ecf8", shade=False, rot=30)
    s.ellipse(18.5, 23.5, 2.6, 1.8, "#e8f4ff", shade=False, rot=-30)
    s.ellipse(16, 26.5, 3, 2.2, "#3a4048")
    s.ellipse(19, 26, 1.6, 1.6, "#2a2e36")
    s.px([(19, 25)], "#c84a3a")
    s.px([(15, 26)], "#5f8a5a")


@piece("crayfish", (16, 27))
def p_crayfish(s):
    s.ellipse(14, 27, 6, 2.4, "#c84a3a")
    for x in (10, 13, 16):
        s.line(x, 26, x, 28, "#9a3428")
    s.poly([(7, 27), (5, 24.5), (5, 29.5)], "#b8402f")
    s.path([(19, 26), (22, 24), (25, 23)], .8, "#c84a3a")
    s.path([(19, 28), (22, 30), (25, 30)], .8, "#c84a3a")
    s.ellipse(25, 22.6, 2, 1.4, "#d85a48")
    s.ellipse(25, 30.4, 2, 1.4, "#d85a48")
    s.line(20, 25, 27, 20, "#9a3428")
    s.px([(19, 26)], "#1d1428")


@piece("snail", (16, 29))
def p_snail(s):
    s.path([(9, 29), (22, 29), (24, 27)], 1.2, "#d8c8a8")
    s.line(23, 26, 24, 23, "#b8a888")
    s.line(25, 26, 26, 24, "#b8a888")
    s.ellipse(15, 25.5, 4.6, 4, "#c8904a")
    s.path([(15, 25.5), (16.5, 25), (16, 23.5), (13.6, 24), (13, 26.5), (15.5, 28)], .5, "#8a5a30")
    s.px([(13, 23), (14, 23)], "#f0c88a")


@piece("bee0", (16, 26))
@piece("bee1", (16, 26), up=True)
def p_bee(s, up=False):
    dy = -1.5 if up else 0
    s.ellipse(14, 22.5 + dy, 2.8, 2, "#e8f4ff", shade=False, rot=25)
    s.ellipse(18.5, 22 + dy, 3, 2.2, "#f4faff", shade=False, rot=-25)
    body = s.ellipse(16, 26, 5.2, 3.4, "#f2c14e")
    for x in (14, 17):
        s.paint(s.m_line(x, 22, x, 30) | s.m_line(x + 1, 22, x + 1, 30), "#3a2a1a", within=body)
    s.px([(10, 26), (9, 26)], "#3a2a1a")
    s.ellipse(21.5, 25.6, 2, 2, "#3a2a1a")
    s.px([(22, 25)], "#ffffff")


@piece("wasp0", (16, 26))
@piece("wasp1", (16, 26), up=True)
def p_wasp(s, up=False):
    dy = -1.5 if up else 0
    s.ellipse(14, 22 + dy, 3.2, 1.6, "#e0ecf8", shade=False, rot=20)
    s.ellipse(18, 21.6 + dy, 3.4, 1.8, "#eef6ff", shade=False, rot=-20)
    tail = s.ellipse(12.5, 26.5, 4.2, 2.4, "#f2c14e", rot=-10)
    for x in (11, 14):
        s.paint(s.m_line(x, 23, x, 30), "#2a2228", within=tail)
    s.poly([(8.5, 27), (6.5, 28.5), (9, 28)], "#2a2228")
    s.ellipse(18, 25.5, 2.2, 1.8, "#2a2228")
    s.ellipse(21.5, 25, 2, 2, "#f2c14e")
    s.px([(22, 24)], "#1d1428")
    s.line(22, 23, 24, 21, "#2a2228")
    s.line(18, 27, 17, 30, "#2a2228")
    s.line(19, 27, 20, 30, "#2a2228")


@piece("grub", (16, 27))
def p_grub(s):
    s.path([(11, 26), (13, 28.5), (17, 29), (20, 27)], 2, "#f4ead0")
    for x, y in ((13, 27), (15, 28), (17, 28)):
        s.px([(x, y), (x, y + 1)], "#d8c8a0")
    s.ellipse(21, 26, 1.8, 1.8, "#c8904a")
    s.px([(22, 25)], "#5a3a20")


@piece("moth0", (16, 26))
@piece("moth1", (16, 26), up=True)
def p_moth(s, up=False):
    dy = -2 if up else 0
    for side in (-1, 1):
        s.poly([(16, 25), (16 + side * 6, 21 + dy), (16 + side * 7, 25 + dy / 2), (16 + side * 3, 28)], "#e8dcc0")
    s.px([(12, 24 + round(dy / 2)), (20, 24 + round(dy / 2))], "#a89070")
    s.ellipse(16, 26, 1.4, 3.4, "#8a7a60")
    s.line(15, 22, 14, 20, "#8a7a60")
    s.line(17, 22, 18, 20, "#8a7a60")


@piece("seed", (16, 27))
def p_seed(s):
    s.ellipse(16, 27, 2, 3.2, "#3a3030", rot=15)
    s.line(16, 25, 17, 29, "#e8e0d0")
    s.px([(15, 26)], "#6a5a50")


@piece("hawk0", (16, 25))
@piece("hawk1", (16, 25), up=True)
def p_hawk(s, up=False):
    # A red-tailed hawk swooping straight at you, wings spread.
    tip = 19 if up else 25
    for side in (-1, 1):
        s.poly([(16 + side * 3, 23), (16 + side * 15, tip), (16 + side * 13, tip + 3), (16 + side * 3, 28)], "#7a5a42")
        for k in range(3):
            s.line(16 + side * (12 - k * 2), tip + 2 + k * .6, 16 + side * (13 - k * 2), tip + 4, "#4a3628")
        s.line(16 + side * 5, 25, 16 + side * 12, tip + 1, "#a88a6a")
    s.poly([(13, 28), (19, 28), (20, 33), (12, 33)], "#c8643a")
    s.ellipse(16, 25, 3.6, 5, "#8a6a4e")
    s.ellipse(16, 26.5, 2.4, 3, "#f0e2cc", shade=False)
    s.px([(15, 26), (17, 27), (16, 28)], "#a88a6a")
    s.ellipse(16, 20.5, 2.6, 2.4, "#7a5a42")
    s.px([(15, 20), (17, 20)], "#f2c14e")
    s.px([(16, 22), (16, 23)], "#e8b040")


@piece("jelly0", (16, 24))
@piece("jelly1", (16, 24), sway=1)
def p_jelly(s, sway=0):
    for i, x in enumerate((11, 14, 18, 21)):
        d = (1 if (i + sway) % 2 else -1)
        s.path([(x, 25), (x + d, 28), (x, 31)], .5, "#d8a0d8")
    s.line(15, 25, 15, 31, "#f0c8f0")
    s.line(17, 25, 17, 30, "#f0c8f0")
    s.ellipse(16, 23, 6.4, 4.4, "#e6aae6")
    s.rect(9.6, 23, 22.4, 25, "#e6aae6")
    s.ellipse(16, 22.5, 3, 2, "#f6d0f6", shade=False)
    s.px([(13, 21), (14, 20)], "#ffffff")


@piece("ring", (16, 21))
def p_ring(s):
    hoop = s.ellipse(16, 21, 5, 12, "#f2c14e")
    s.erase(s.m_ellipse(16, 21, 2.6, 9.4))
    s.px([(12, 15), (12, 16), (12, 17)], "#fff4c0")
    s.px([(20, 26), (20, 27)], "#c8902a")
    s.px([(16, 9), (16, 33)], "#f8d878")


@piece("pike", (16, 26))
def p_pike(s):
    # A long hungry pike, coming from the right with its mouth open.
    s.poly([(28, 26), (33, 21.5), (33, 30.5)], "#5a7a3a")
    s.ellipse(17, 26, 11, 3.8, "#6b8a4a")
    s.poly([(26, 22.5), (24, 19.5), (21, 23)], "#5a7a3a")
    s.poly([(25, 29), (23, 32), (21, 29)], "#5a7a3a")
    s.ellipse(17, 28.2, 9, 1.4, "#c8d8a0", shade=False)
    for x, y in ((14, 24), (18, 25), (22, 24), (20, 26), (25, 25), (16, 26)):
        s.px([(x, y)], "#d8e8a8")
    s.poly([(5, 26.5), (8, 25), (8, 28)], "#3a2a2a", shade=False)
    s.px([(7, 25), (7, 28)], "#ffffff")
    s.eye(9, 24, size=2, color="#1d1428")


@piece("plankton", (16, 26))
def p_plankton(s):
    for i, (x, y) in enumerate(((12, 24), (16, 22), (19, 26), (14, 28), (18, 29), (21, 23), (11, 27))):
        s.ellipse(x, y, 1.3, 1.3, "#c8f0aa" if i % 2 else "#a8e0d0", shade=False)
        s.px([(x, y)], "#f4ffe8")


@piece("clover", (16, 30))
def p_clover(s):
    s.path([(16, 31), (16.5, 27)], .5, "#2f7d4f")
    for dx, dy in ((-2.2, -1.2), (2.2, -1.2), (0, -3.6)):
        s.ellipse(16 + dx, 26 + dy, 2.2, 2, "#3f9d48")
    s.px([(14, 24), (18, 24), (16, 22)], "#8ad07a")
    s.ellipse(20, 28.5, 1.4, 1.4, "#f0e8f8")


# == Tide Pool Spin: what each animal eats ===============================================
@piece("food_plankton", (16, 26))
def f_plankton(s):
    p_plankton(s)


@piece("food_mussels", (16, 26))
def f_mussels(s):
    s.ellipse(14.5, 26, 2.4, 4, "#3d4a7a", rot=25)
    s.ellipse(18, 26.5, 2.4, 4, "#34406c", rot=-20)
    s.px([(13, 24), (17, 24)], "#8a98c8")


@piece("food_kelp", (16, 28))
def f_kelp(s):
    s.path([(16, 31), (15, 26), (17, 21)], .6, "#5a7a2a")
    for x, y, r in ((13.5, 27, -40), (18.5, 24, 40), (14, 22, -40)):
        s.ellipse(x, y, 3, 1.4, "#6a9a3a", rot=r)
    s.ellipse(17, 20, 1.2, 1.2, "#a8a040")


@piece("food_barnacles", (16, 27))
def f_barnacles(s):
    for x, y in ((13, 28), (18, 28), (15.5, 25)):
        s.ellipse(x, y, 2.6, 2.2, "#e8e0c8")
        s.px([(round(x), round(y) - 1)], "#5a5048")


@piece("food_sanddollars", (16, 27))
def f_sanddollar(s):
    s.ellipse(16, 27, 4.4, 3.6, "#d8c49a")
    for dx, dy in ((0, -2), (-2, 0), (2, 0), (-1, 2), (1, 2)):
        s.px([(16 + dx, 27 + dy)], "#a89068")


@piece("food_shrimp", (16, 28))
def f_shrimp(s):
    p_snack(s)


@piece("food_mossanimals", (16, 27))
def f_moss(s):
    for x, y in ((13, 27), (16, 25), (19, 27), (15, 29), (18, 29.5)):
        s.ellipse(x, y, 2, 1.8, "#c8a0e0")
        s.px([(round(x), round(y))], "#f0e0ff")


@piece("food_worms", (16, 27))
def f_worms(s):
    s.path([(11, 27), (13, 25), (15, 28), (18, 26), (21, 28)], .9, "#d98a8a")
    s.px([(21, 28)], "#a85a5a")


@piece("food_clams", (16, 27))
def f_clams(s):
    s.ellipse(16, 27, 4.4, 3.2, "#d8c8a8")
    for x in (14, 16, 18):
        s.line(16, 30, x, 25, "#a8987a")
    s.px([(14, 25)], "#f8f0e0")


@piece("food_jellies", (16, 25))
def f_jellies(s):
    s.ellipse(16, 25, 4, 3, "#e0b0e8")
    for x in (13, 15, 17, 19):
        s.line(x, 27, x + (1 if x % 4 else -1), 30, "#c890d0")
    s.px([(14, 24)], "#ffffff")


@piece("food_seagrass", (16, 30))
def f_seagrass(s):
    for x0, x1 in ((13, 11), (15, 15), (17, 19), (19, 21)):
        s.path([(x0, 31), (x1, 23)], .6, "#5aa84a")
    s.px([(15, 23), (19, 22)], "#8ad07a")


@piece("food_fish", (16, 26))
def f_fish(s):
    fish(s, "#9ab8d0", "#e8f2f8", "#6f8fae", long=.7)


@piece("food_flowers", (16, 27))
def f_flowers(s):
    for dx, dy in ((-2.4, 0), (2.4, 0), (0, -2.4), (0, 2.4)):
        s.ellipse(16 + dx, 27 + dy, 2, 2, "#f2c14e")
    s.ellipse(16, 27, 1.4, 1.4, "#c8702a", shade=False)


@piece("food_beetles", (16, 27))
def f_beetles(s):
    for x in (12, 20):
        s.line(x, 25, x, 29, "#3a2a20")
    s.ellipse(16, 27.5, 3.4, 3, "#6a5040")
    s.line(16, 25, 16, 30, "#3a2a20")
    s.ellipse(16, 23.6, 1.8, 1.2, "#3a2a20")
    s.px([(15, 26)], "#a88a70")


@piece("food_leaves", (16, 27))
def f_leaves(s):
    s.ellipse(16, 27, 5, 2.6, "#6aae6e", rot=-30)
    s.line(12, 29, 20, 25, "#3f7a4a")


@piece("food_snails", (16, 28))
def f_snails(s):
    s.path([(11, 29), (20, 29)], .9, "#d8c8a8")
    s.ellipse(15, 26.5, 3.4, 3, "#c8a070")
    s.px([(15, 26), (16, 27)], "#8a6040")


@piece("food_algae", (16, 27))
def f_algae(s):
    for x, y in ((13, 27), (17, 25), (19, 28), (15, 29)):
        s.ellipse(x, y, 2.6, 2, "#4f9a5a")
    s.px([(16, 25), (13, 26)], "#8ad07a")


# == Mud Slide, Claw Capture: the bank and the cliff =====================================
@piece("cliff_m", (16, 21), crop=(6, 14, 25, 29))
def p_cliff(s):
    for i, (x, y) in enumerate(((7, 13), (17, 12), (27, 13), (2, 18), (12, 18), (22, 18), (32, 18),
                                (7, 23), (17, 23), (27, 23), (2, 28), (12, 28), (22, 28), (32, 28),
                                (7, 33), (17, 33), (27, 33))):
        s.rect(x - 5, y - 3, x + 4, y + 1, STONE if i % 3 else "#8088a0", edge=True)
    s.px([(9, 16), (20, 21), (14, 26), (24, 15)], STONE_LT)


@piece("bank", (16, 31))
def p_bank(s):
    s.rect(-4, 22, 35, 31, SOIL)
    s.rect(-4, 20, 35, 23, MOSS)
    s.line(-4, 20, 35, 20, MOSS_LT)
    for x in range(-2, 34, 4):
        s.px([(x, 19), (x + 1, 18)], MOSS_LT)
    s.px([(4, 26), (5, 26), (14, 28), (24, 25), (29, 29)], "#9a7048")
    s.ellipse(22, 28, 2.4, 1.4, STONE)


# == Branch Leap ===========================================================================
@piece("trunk_m", (16, 21), crop=(13, 14, 20, 29))
def p_trunk(s):
    s.rect(12, 8, 21, 31, "#6a4a2e")
    for y in (14, 20, 26):
        s.line(14, y, 15, y + 3, "#4a3220")
        s.line(18, y + 2, 19, y + 5, "#4a3220")
    s.line(13, 8, 13, 31, "#8a6440")


@piece("limb_m", (16, 23), crop=(10, 22, 21, 27))
def p_limb_mid(s):
    s.rect(4, 22, 28, 27, BARK)
    s.line(4, 22, 28, 22, BARK_LT)
    s.line(4, 23, 28, 23, BARK_LT)
    for x in (7, 13, 19, 25):
        s.px([(x, 25), (x + 1, 25), (x + 3, 26)], BARK_DK)


@piece("limb_end", (16, 23))
def p_limb_end(s):
    s.rect(9, 22, 17, 27, BARK)
    s.line(9, 22, 17, 22, BARK_LT)
    s.line(9, 23, 17, 23, BARK_LT)
    s.path([(17, 24.5), (21, 23)], 1.6, BARK)
    for x, y, r in ((18, 20, 3.4), (22, 22, 3.6), (20, 25.5, 3), (24, 26, 2.6)):
        s.ellipse(x, y, r, r * .8, LEAF)
        s.ellipse(x - .7, y - .8, r * .5, r * .4, LEAF_LT)
    s.px([(21, 23), (19, 26)], LEAF_DK)


@piece("vine_m", (16, 21), crop=(14, 14, 18, 29))
def p_vine(s):
    s.rect(16, 8, 16, 31, "#3f8d58", shade=False)
    for y in (15, 22, 29):
        s.ellipse(14.6, y, 1.4, 1, LEAF)
    for y in (18, 25):
        s.ellipse(17.4, y, 1.4, 1, LEAF_LT)


# == Burrow Dig =============================================================================
for _r in (7, 9, 11, 13):
    @piece(f"dstone{_r}", (16, 18), size=40, rad=_r)
    def p_dstone(s, rad):
        s.ellipse(16, 18, rad, rad * .92, "#8a8f9e")
        s.ellipse(16 - rad * .3, 18 - rad * .35, rad * .45, rad * .3, "#a8adba")
        s.px([(round(16 + rad * .3), 18), (round(16 - rad * .1), round(18 + rad * .5))], "#6a6f7c")
        s.px([(round(16 + rad * .5), round(18 - rad * .4))], "#c4c8d2")

    @piece(f"dwater{_r}", (16, 18), size=40, rad=_r)
    def p_dwater(s, rad):
        s.ellipse(16, 18, rad + 2, rad, "#3d8cc0", shade=False)
        s.ellipse(16, 18 + rad * .25, rad + 1, rad * .7, "#2f78ac", shade=False)
        s.line(round(16 - rad * .6), round(18 - rad * .4), round(16), round(18 - rad * .4), "#7cc4e8")
        s.px([(round(16 + rad * .4), round(18 + rad * .1))], "#7cc4e8")
        s.px([(round(16 - rad * .3), round(18 + rad * .5)), (round(16 - rad * .2), round(18 + rad * .5))], "#5aa4d4")


@piece("taproot_m", (16, 21), crop=(13, 14, 19, 29))
def p_taproot(s):
    s.rect(13, 8, 19, 31, "#c8a070")
    s.line(13, 8, 13, 31, "#e0bc8c")
    for y in (12, 19, 26):
        s.line(16, y, 17, y + 2, "#a07a50")


@piece("taproot_end", (16, 22))
def p_taproot_end(s):
    s.rect(13, 14, 19, 22, "#c8a070")
    s.line(13, 14, 13, 22, "#e0bc8c")
    s.path([(16, 22), (15, 26), (16, 29)], (2.4, .5), "#c8a070")
    s.path([(13, 18), (10, 21), (9, 25)], (.9, .4), "#b8905e")
    s.path([(19, 16), (22, 20), (22, 23)], (.9, .4), "#b8905e")


@piece("nest", (30, 30), size=72)
def p_nest(s):
    s.ellipse(30, 26, 26, 18, "#3e2a18", shade=False)
    s.ellipse(30, 30, 20, 11, "#2e1e10", shade=False)
    s.ellipse(30, 36, 17, 5, "#c8a860")
    for x in range(16, 46, 4):
        s.line(x, 33, x + 4, 39, "#a88a48")
        s.line(x + 3, 33, x - 1, 38, "#e0c880")
    s.ellipse(24, 33, 2.4, 1.8, "#f4ead0")
    s.ellipse(29, 32, 2.4, 1.8, "#f0e4c4")


# == Nectar Rush ============================================================================
PETALS = ("#e86a8a", "#f2c14e", "#b58ae0", "#f08a4a")
for _f, _col in enumerate(PETALS):
    for _o in range(4):
        @piece(f"flower{_f}_{_o}", (16, 22), col=_col, stage=_o)
        def p_flower(s, col, stage):
            if stage == 0:  # a closed bud
                s.ellipse(16, 23, 2.6, 3.6, "#3f8d58")
                s.ellipse(16, 21, 1.6, 2.4, col)
                s.line(14, 25, 15, 21, "#2f6e3a")
                return
            n, rad = 5 + (stage > 1) * 3, 2.2 + stage * 1.6
            for i in range(n):
                a = i / n * 2 * math.pi - math.pi / 2
                s.ellipse(16 + math.cos(a) * rad, 22 + math.sin(a) * rad, 1.4 + stage * .8, 1 + stage * .5, col,
                          rot=-math.degrees(a))
            s.ellipse(16, 22, 1.6 + stage * .5, 1.6 + stage * .5, "#f8d050")
            s.px([(15, 21)], "#fff4b0")
            s.px([(17, 23)], "#c8902a")


@piece("stem", (16, 1), size=64)
def p_stem(s):
    s.rect(15, 1, 17, 55, "#3f8d58")
    s.ellipse(11, 28, 5, 1.8, LEAF, rot=20)
    s.ellipse(21, 18, 5, 1.8, LEAF, rot=-20)
    s.line(8, 27, 14, 29, LEAF_DK)
    s.line(18, 19, 24, 17, LEAF_DK)
    s.ellipse(16, 4, 3, 1.8, "#3f8d58")


# == Plunge Dive, Big Splash, School Swim ===================================================
@piece("float", (16, 26))
def p_float(s):
    s.rect(4, 21, 26, 30, BARK)
    for x in (8, 13, 18, 22):
        s.line(x, 22, x + 1, 29, BARK_DK)
    s.line(5, 22, 25, 22, BARK_LT)
    s.ellipse(27, 25.5, 2.6, 4.6, WOODCUT, shade=False)
    s.ellipse(27, 25.5, 1.4, 2.8, WOODCUT_DK, shade=False)
    s.px([(9, 20), (10, 20), (17, 20)], MOSS)
    s.ellipse(12, 19.5, 1.6, 1, "#e8e0d0")


@piece("boulder_bot", (16, 18))
def p_boulder_bot(s):
    s.rect(5, 10, 26, 16, "#6e7380")
    s.line(6, 10, 6, 16, "#8a8f9e")
    s.ellipse(15.5, 16.5, 10.5, 3.6, "#6e7380")
    s.line(7, 19, 24, 19, "#5a5f6c")
    for x, h in ((9, 3), (13, 5), (20, 4), (23, 2)):
        s.line(x, 19, x + (x % 2), 19 + h, "#3f8d58")


# == Call Back ==============================================================================
@piece("big_stump", (20, 31), size=48)
def p_big_stump(s):
    s.rect(6, 14, 33, 31, BARK)
    s.poly([(2, 31), (6, 25), (6, 31)], BARK)
    s.poly([(38, 31), (33, 24), (33, 31)], BARK)
    for x in (9, 14, 20, 25, 30):
        s.line(x, 17, x + (x % 2), 30, BARK_DK)
    s.ellipse(19.5, 14, 13.6, 3.4, WOODCUT, shade=False)
    s.ellipse(19.5, 14, 9, 2.2, WOODCUT_DK, shade=False)
    s.ellipse(19.5, 14, 5, 1.2, WOODCUT, shade=False)
    s.px([(19, 14), (20, 14)], WOODCUT_DK)
    s.px([(6, 20), (6, 21), (7, 21), (33, 26), (32, 27)], MOSS)
    s.ellipse(28, 27, 1.8, 1.2, "#e05a4a")
    s.px([(27, 27), (29, 26)], "#ffffff")
    s.line(28, 28, 28, 29, "#f3efe4")


# == Echo Flight ============================================================================
@piece("tite_m", (16, 21), crop=(6, 14, 25, 29))
def p_tite_mid(s):
    s.rect(4, 8, 27, 31, "#9a90c0")
    for y in (12, 18, 25, 30):
        s.line(7, y, 12, y + 1, "#7a70a0")
        s.line(17, y + 3, 23, y + 2, "#7a70a0")
    s.line(6, 8, 6, 31, "#c8c0e8")
    s.px([(10, 16), (20, 22), (14, 27)], "#c8c0e8")


@piece("tite_tip", (16, 8))
def p_tite_tip(s):
    s.poly([(6, 8), (25, 8), (22, 16), (19, 21), (17, 30), (14, 22), (10, 17)], "#9a90c0")
    s.line(7, 8, 13, 22, "#c8c0e8")
    s.line(19, 12, 21, 15, "#7a70a0")
    s.px([(17, 31)], "#c0f0ff")


@piece("mite_tip", (16, 31))
def p_mite_tip(s):
    s.poly([(6, 31), (25, 31), (22, 24), (18, 18), (16, 8), (13, 17), (9, 23)], "#9a90c0")
    s.line(7, 30, 14, 15, "#c8c0e8")
    s.line(19, 25, 21, 28, "#7a70a0")


@piece("cave_top", (16, 8), crop=(8, 8, 23, 23))
def p_cave_top(s):
    s.rect(-4, 8, 36, 20, "#5a5080")
    for x in range(-2, 36, 5):
        s.poly([(x, 20), (x + 4, 20), (x + 2, 23)], "#5a5080")
    s.px([(10, 13), (18, 16), (22, 11)], "#7a70a0")


@piece("cave_bot", (16, 17), crop=(8, 17, 23, 31))
def p_cave_bot(s):
    s.rect(-4, 20, 36, 31, "#5a5080")
    for x in range(-2, 36, 6):
        s.ellipse(x + 2, 20, 3, 2.4, "#6a6090")
    s.px([(10, 25), (18, 27), (21, 23)], "#7a70a0")


# == Feeder Rush ============================================================================
@piece("feeder", (34, 4), size=80)
def p_feeder(s):
    # A wooden bird feeder: a pitched roof, a seed hopper behind glass and a tray.
    s.poly([(0, 24), (34, 4), (68, 24), (64, 26), (34, 9), (4, 26)], "#b5523b")
    s.rect(9, 24, 59, 46, "#d8b07a")
    s.rect(15, 27, 53, 41, "#cfe8f0", shade=False)
    s.rect(15, 33, 53, 41, "#c78a3e", shade=False)
    for i in range(14):
        s.px([(16 + i * 2.7, 34 + (i * 7) % 6)], "#6e4e30")
        s.px([(17 + i * 2.7, 37 + (i * 5) % 4)], "#e6c48a")
    s.line(16, 28, 20, 28, "#ffffff")
    s.line(16, 29, 18, 29, "#ffffff")
    s.rect(5, 44, 63, 47, "#a8744a")
    s.line(5, 44, 63, 44, "#c8945e")
    s.rect(31, 47, 37, 75, "#7a5232")


@piece("perch_m", (16, 22), crop=(10, 22, 21, 27))
def p_perch(s):
    s.rect(4, 22, 28, 25, BARK)
    s.line(4, 22, 28, 22, BARK_LT)
    s.px([(9, 24), (15, 23), (22, 24)], BARK_DK)


@piece("peg", (16, 22))
def p_peg(s):
    s.rect(11, 22, 21, 24, "#6e4e30")
    s.line(11, 22, 21, 22, "#8a6440")


# == Freeze! ================================================================================
@piece("den", (20, 31), size=48)
def p_den(s):
    s.ellipse(20, 31, 19, 15, "#7a5a40")
    s.ellipse(20, 32, 11, 9, "#2a1c12", shade=False)
    s.ellipse(20, 33, 8, 6, "#1a100a", shade=False)
    for x, y in ((6, 26), (11, 20), (29, 19), (34, 25), (17, 18)):
        s.ellipse(x, y, 2, 1.4, "#9a7a58")
    s.px([(5, 21), (6, 20), (33, 20), (34, 19), (20, 16)], MOSS)
    s.line(3, 30, 9, 30, MOSS_LT)


@piece("fox_rock", (20, 6), size=48)
def p_fox_rock(s):
    lumps(s, 20, 20, 19, 13, STONE, n=4, seed=2)
    s.ellipse(14, 13, 9, 4, STONE_LT)
    s.px([(9, 12), (10, 12)], "#d6d9e2")
    s.px([(26, 22), (13, 25), (30, 15)], STONE_DK)
    s.px([(3, 30), (4, 29), (36, 30)], MOSS)


@piece("fox_back", (16, 26))
@piece("fox_alert", (16, 26), ears=True)
@piece("fox_look", (16, 26), look=True)
def p_fox(s, ears=False, look=False):
    # The fox sits facing right (away from you); looking, it turns its head to the left.
    FOX, FOX_DK, CREAM = "#d9733a", "#a84f22", "#f4e6d4"
    s.path([(10, 31), (5, 29), (3, 25)], (2.4, 2.8), FOX)
    s.ellipse(3, 24, 2.6, 2.4, CREAM)
    s.ellipse(14, 26, 6, 6.4, FOX)
    s.ellipse(15, 29.5, 4, 2.4, FOX_DK)
    s.line(18, 28, 18, 31, "#3a2a20")
    s.line(13, 29, 13, 31, "#3a2a20")
    hx = 12 if look else 18
    tall = 5 if ears or look else 2.6
    for ex in (hx - 3, hx + 2):
        s.poly([(ex - 1.6, 16), (ex + .5, 16 - tall), (ex + 1.8, 16)], FOX)
        s.px([(round(ex), 15)], "#3a2a20")
    s.ellipse(hx, 18, 4.4, 3.6, FOX)
    if look:
        s.poly([(hx - 3, 18), (hx - 8, 20), (hx - 2, 21)], FOX)
        s.ellipse(hx - 3, 20, 2.6, 1.4, CREAM, shade=False)
        s.px([(hx - 8, 20)], "#2a1c12")
        s.eye(hx - 3, 17, size=2)
    else:
        s.poly([(hx + 3, 18), (hx + 7, 20), (hx + 2, 21)], FOX)
        s.px([(hx + 7, 20)], "#2a1c12")
    s.ellipse(12 if look else 16, 23, 2.4, 2, CREAM, shade=False)


def render(p) -> tuple[Image.Image, tuple[int, int]]:
    with canvas(p["size"] or pixel.N):
        s = Sprite()
        p["draw"](s, **p["kw"])
        img = s.render()
    if p["crop"]:
        x0, y0, x1, y1 = p["crop"]
        box = (x0 + PAD_X, y0 + PAD_TOP, x1 + PAD_X + 1, y1 + PAD_TOP + 1)
    else:
        box = img.getbbox()
    ax, ay = p["anchor"]
    return img.crop(box), (ax + PAD_X - box[0], ay + PAD_TOP - box[1])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--sheet", type=Path, help="also write a big preview of every piece here")
    args = ap.parse_args()
    out, x, y, row_h, W = {}, 0, 0, 0, 256
    pieces = [(p["name"], *render(p)) for p in PIECES]
    for name, img, anchor in pieces:
        if x + img.width > W:
            x, y, row_h = 0, y + row_h + 1, 0
        out[name] = [x, y, img.width, img.height, *anchor]
        x += img.width + 1
        row_h = max(row_h, img.height)
    atlas = Image.new("RGBA", (W, y + row_h))
    for name, img, _ in pieces:
        atlas.paste(img, tuple(out[name][:2]))
    OUT.mkdir(parents=True, exist_ok=True)
    atlas.save(OUT / "atlas.png", optimize=True)
    (OUT / "atlas.json").write_text(json.dumps(out, separators=(",", ":")) + "\n")
    print(f"wrote {len(out)} pieces to {(OUT / 'atlas.png').relative_to(ROOT)}")
    if args.sheet:
        atlas.resize((atlas.width * 4, atlas.height * 4), Image.NEAREST).save(args.sheet)


if __name__ == "__main__":
    main()
