"""Sprites for the European (and Turkish) insects, spiders, snails, slugs, sea snails,
sea slugs and the octopus that the US lists don't have.
Imported by make_sprites.py, which registers the drawings via @sprite.

Butterfly patterns are painted on the left wings in butterfly()'s coordinates and
mirrored: forewing (15, 11) (5, 3) (1.5, 6) (2, 14) (14, 17), hindwing (15, 16)
(5, 16) (4, 22) (9, 27) (15, 22)."""
from __future__ import annotations

import math

from archetypes import (BLACK, EYE, WHITE, beetle_top, butterfly, dragonfly, grasshopper, mantis, snail_shell,
                        spider_top, sprite)
from pixel import mix
from species_east import _bumble
from species_east import _delta_moth
from species_oh import _damsel


def _dk(c, k=0.28):
    return mix(c, "#1a1420", k)


# --------------------------------------------------------------------------- butterflies
def _bf(fore, hind, *marks, body="#2b2630", tails=False):
    """butterfly() with marks: (kind, shape, colour) where kind is 'f' (forewing),
    'h' (hindwing) or 'b' (both) and shape a mask builder taking s."""
    def draw(s):
        def pat(s, fm, hm):
            for kind, shape, col in marks:
                within = fm if kind == "f" else hm if kind == "h" else (fm | hm)
                s.paint(shape(s), col, mirror=True, within=within)
        butterfly(s, fore, hind, body=body, pattern=pat, tails=tails)
    return draw


def E(x, y, rx, ry=None, rot=0.0):
    return lambda s: s.m_ellipse(x, y, rx, ry if ry is not None else rx, rot)


def P(*pts):
    return lambda s: s.m_poly(list(pts))


def L(x0, y0, x1, y1):
    return lambda s: s.m_line(x0, y0, x1, y1)


def D(*pts):
    return lambda s: s.m_px(list(pts))


TIP = P((1.5, 6), (5, 3), (7, 5), (3, 10))          # the forewing tip
EDGE_F = P((1.5, 6), (2, 14), (3.5, 14), (3, 7))       # the forewing outer edge
EDGE_H = P((4, 22), (9, 27), (10, 25.5), (5.5, 21))    # the hindwing outer edge
EYESPOT_F = (5.5, 7.5)


def _reg(slug, fn, doc=None):
    sprite(slug)(lambda s: fn(s))


_reg("large_white", _bf("#f6f4ec", "#f2f0e2", ("f", TIP, "#2b2630"), ("f", E(8, 11, 1.3), "#2b2630")))
_reg("green_veined_white", _bf("#f6f4ec", "#f0ecc8", ("f", D((3, 6), (4, 5)), "#4a4a4a"),
                                ("h", L(14, 17, 6, 20), "#8a9a6a"), ("h", L(14, 19, 6, 24), "#8a9a6a"),
                                ("h", L(14, 21, 9, 26), "#8a9a6a")))
_reg("black_veined_white", _bf("#f6f4f0", "#f4f2ec", ("f", L(14, 12, 4, 4), "#2b2630"),
                                ("f", L(14, 14, 2, 9), "#2b2630"), ("h", L(14, 18, 5, 18), "#2b2630"),
                                ("h", L(14, 20, 6, 24), "#2b2630"), ("b", EDGE_F, "#2b2630")))
_reg("clouded_yellow", _bf("#f0a830", "#f0b840", ("f", EDGE_F, "#2b2630"), ("h", EDGE_H, "#2b2630"),
                            ("f", E(9, 10, 1.2), "#2b2630"), ("h", E(11, 20, 1.2), "#f0d080")))
_reg("common_brimstone", _bf("#e8e840", "#e4e650", ("f", E(9, 10, 0.9), "#e8802a"),
                              ("h", E(10, 20, 0.9), "#e8802a")))
_reg("marbled_white", _bf("#f4f0e4", "#f2eee0", ("f", P((14, 11), (5, 3), (7, 6), (13, 13)), "#2b2630"),
                           ("f", EDGE_F, "#2b2630"), ("f", E(8, 12, 1.5), "#2b2630"),
                           ("h", EDGE_H, "#2b2630"), ("h", E(9, 19, 1.4), "#2b2630")))
_reg("common_blue", _bf("#6a8ae8", "#7a98ec", ("f", EDGE_F, "#2a2a4a"), ("h", EDGE_H, "#2a2a4a"),
                         ("b", D((3, 13), (5, 23), (7, 25)), WHITE), body="#3a3a5a"))
_reg("paphos_blue", _bf("#7aa0e8", "#8aa8ec", ("f", EDGE_F, "#3a3a5a"), ("h", EDGE_H, "#3a3a5a"),
                         ("f", E(9, 10, 0.8), "#2a2a4a"), body="#3a3a5a"))
_reg("langs_short_tailed_blue", _bf("#8a8ad0", "#9a98d8", ("f", EDGE_F, "#5a5a8a"),
                                     ("h", E(8, 25, 1.1), "#2b2630"), ("h", E(6, 23, 0.9), "#e8a040"),
                                     body="#4a4a6a", tails=True))
_reg("small_copper", _bf("#f07a20", "#3a2e28", ("f", EDGE_F, "#3a2e28"),
                          ("f", D((6, 8), (9, 9), (8, 12), (11, 13), (5, 11)), "#2b2226"),
                          ("h", EDGE_H, "#f07a20")))
_reg("green_hairstreak", _bf("#6aa848", "#5a9a40", ("f", D((7, 12), (9, 13)), WHITE),
                              ("h", D((8, 22), (10, 23)), WHITE), body="#4a5a3a"))
_reg("european_peacock_butterfly", _bf("#b8302a", "#8a2a22",
                                        ("f", E(5.5, 7, 2.4, 2.2), "#f0dca0"), ("f", E(5.5, 7, 1.6), "#4a6ad0"),
                                        ("f", E(5.5, 7, 0.8), "#1e1a22"), ("h", E(9, 21, 2.6, 2.4), "#2b2630"),
                                        ("h", E(9, 21, 1.6), "#6a8ad8"), ("f", L(14, 12, 8, 5), "#2b2630"),
                                        body="#3a2622"))
_reg("small_tortoiseshell", _bf("#e8702a", "#e8702a", ("f", D((7, 6), (8, 6), (11, 9), (10, 12), (12, 12)),
                                                       "#1e1a1e"), ("f", E(5, 4.5, 1.2), WHITE),
                                 ("h", P((15, 16), (8, 16), (9, 20), (15, 21)), "#2b2630"),
                                 ("b", EDGE_F, "#3a5ad0"), ("h", EDGE_H, "#3a5ad0"), body="#3a2a22"))
_reg("european_comma", _bf("#d8782e", "#d07028", ("f", D((7, 8), (10, 9), (9, 12), (12, 13), (6, 12)), "#3a2216"),
                            ("h", D((9, 20), (11, 22)), "#3a2216"), ("f", EDGE_F, "#7a3e1e"),
                            ("h", EDGE_H, "#7a3e1e"), body="#4a3020"))
_reg("map", _bf("#2b2226", "#2b2226", ("f", L(14, 13, 3, 11), WHITE), ("h", L(15, 19, 5, 19), WHITE),
                 ("f", D((4, 6), (6, 5), (8, 5)), "#e8803a"), ("h", D((6, 24), (8, 25), (10, 25)), "#e8803a")))
_reg("queen_of_spain_fritillary", _bf("#e88a30", "#e09030",
                                      ("f", D((6, 7), (8, 8), (10, 10), (7, 11), (11, 13), (5, 10), (9, 6)),
                                       "#2b2226"),
                                      ("h", D((7, 19), (9, 21), (11, 19), (8, 23), (12, 22)), "#2b2226"),
                                      ("h", E(10, 24, 1), "#e8e4dc")))
_reg("silver_washed_fritillary", _bf("#e8902e", "#e08a2a",
                                     ("f", L(13, 12, 6, 6), "#3a2216"), ("f", L(12, 15, 4, 10), "#3a2216"),
                                     ("f", D((5, 6), (4, 9), (3, 12)), "#3a2216"),
                                     ("h", D((7, 19), (9, 22), (12, 20), (7, 24), (11, 25)), "#3a2216")))
_reg("meadow_brown", _bf("#7a5a3a", "#6a4e34", ("f", E(9, 10, 3, 2.4), "#d8903e"),
                          ("f", E(6, 7.5, 1.1), "#1e1a1e"), ("f", D((6, 7)), WHITE), body="#4a3424"))
_reg("gatekeeper", _bf("#e8883a", "#e08a3a", ("f", EDGE_F, "#6a4a30"), ("h", EDGE_H, "#6a4a30"),
                        ("f", E(5.5, 7, 1.2), "#1e1a1e"), ("f", D((5, 6), (6, 7)), WHITE), body="#4a3424"))
_reg("ringlet", _bf("#3a2e28", "#3a2e28", ("f", E(7, 9, 0.9), "#d8c8a0"), ("h", E(8, 21, 0.9), "#d8c8a0"),
                     ("h", E(11, 24, 0.8), "#d8c8a0"), body="#2b2226"))
_reg("arran_brown", _bf("#4a3426", "#4a3426", ("f", P((3, 7), (10, 9), (9, 13), (3, 12)), "#c8602a"),
                         ("f", D((5, 9), (7, 10), (5, 11)), "#1e1a1e"),
                         ("h", P((5, 18), (12, 19), (11, 22), (5, 22)), "#c8602a"), body="#2b2226"))
_reg("small_heath", _bf("#e0a850", "#c8a070", ("f", EDGE_F, "#8a7050"), ("f", E(5, 6.5, 1), "#1e1a1e"),
                         body="#5a4a34"))
_reg("speckled_wood", _bf("#5a4430", "#5a4430",
                           ("f", D((6, 8), (8, 9), (10, 11), (9, 13), (12, 13), (7, 11)), "#e8d090"),
                           ("h", D((8, 19), (10, 21), (7, 22), (11, 24)), "#e8d090"),
                           ("f", E(5, 6.5, 0.9), "#1e1a1e"), body="#3a2a1e"))
_reg("wall_brown", _bf("#e09040", "#d88a3a", ("f", L(13, 11, 6, 5), "#4a2e1e"), ("f", L(12, 14, 4, 9), "#4a2e1e"),
                        ("f", E(5, 6.5, 1.2), "#1e1a1e"), ("h", L(14, 19, 6, 19), "#4a2e1e"),
                        ("h", D((7, 22), (9, 24), (11, 25)), "#1e1a1e")))
_reg("southern_white_admiral", _bf("#2a2a3a", "#2a2a3a", ("f", D((7, 7), (10, 11), (12, 13), (9, 13)), WHITE),
                                    ("h", P((15, 18), (6, 19), (7, 21), (15, 20.5)), WHITE),
                                    ("h", EDGE_H, "#3a4a7a"), body="#1e1a22"))
_reg("old_world_swallowtail", _bf("#f0d850", "#f0d850", ("f", EDGE_F, "#2b2630"),
                                   ("f", P((14, 11), (6, 4), (8, 4), (15, 9)), "#2b2630"),
                                   ("f", L(12, 15, 8, 9), "#2b2630"), ("h", EDGE_H, "#2b2630"),
                                   ("h", E(12.5, 22.5, 1.3), "#e0402a"), ("h", D((6, 21), (8, 24)), "#5a8ad8"),
                                   tails=True))
_reg("scarce_swallowtail", _bf("#f4ecd0", "#f2e8c8", ("f", L(14, 12, 6, 4), "#2b2630"),
                                ("f", L(12, 15, 3, 8), "#2b2630"), ("f", L(10, 16, 2, 12), "#2b2630"),
                                ("h", L(15, 18, 6, 20), "#2b2630"), ("h", EDGE_H, "#2b2630"),
                                ("h", E(9, 25, 1), "#4a6ad0"), tails=True))

# --------------------------------------------------------------------------- moths
_reg("cinnabar_moth", _bf("#3a3a42", "#e0302a", ("f", L(14, 12, 5, 5), "#e0302a"),
                           ("f", E(4, 11, 1.4), "#e0302a"), ("f", E(5, 5, 1.2), "#e0302a"), body="#1e1c22"))
_reg("six_spot_burnet", _bf("#1e2a3a", "#e02a2a", ("f", E(12, 12, 1.2), "#e02a2a"), ("f", E(9, 9, 1.2), "#e02a2a"),
                             ("f", E(5, 7, 1.2), "#e02a2a"), ("f", E(10, 14, 1.0), "#e02a2a"),
                             ("f", E(6, 11, 1.0), "#e02a2a"), ("h", EDGE_H, "#1e2a3a"), body="#1e2a3a"))
_reg("crimson_speckled_flunkey", _bf("#f4f0e6", "#f6f6f6", ("f", D((5, 6), (8, 7), (11, 10), (6, 10), (9, 13),
                                                                  (4, 12)), "#e0302a"),
                                      ("f", D((7, 5), (10, 9), (7, 12), (12, 13)), "#1e1a1e"),
                                      ("h", EDGE_H, "#2b2630"), body="#e8e4dc"))
_reg("japanese_silk_moth", _bf("#d8a850", "#d0a048", ("f", E(9, 10, 1.6), "#f4e8c0"), ("f", E(9, 10, 0.8), "#8a5a30"),
                                ("h", E(10, 21, 1.6), "#f4e8c0"), ("h", E(10, 21, 0.8), "#8a5a30"),
                                ("f", L(13, 15, 3, 8), "#a87a3a"), body="#b8883e"))
_reg("oleander_hawkmoth", _bf("#5a8a48", "#6a7a50", ("f", L(13, 13, 3, 6), "#e8e0c8"), ("f", L(12, 15, 4, 11), "#c8a0b0"),
                               ("f", P((14, 11), (9, 7), (12, 8)), "#3a5a30"), ("h", L(14, 19, 6, 21), "#e8e0c8"),
                               body="#5a7a48"))
_reg("cotton_bollworm_moth", _bf("#c8a870", "#e8dcc0", ("f", E(9, 10, 1), "#8a6a40"),
                                  ("f", L(13, 15, 3, 9), "#a88858"), ("h", EDGE_H, "#6a5a48"), body="#b09460"))
_reg("cyprus_processionary_moth", _bf("#a8a49a", "#ece8e0", ("f", L(13, 12, 4, 6), "#5a5650"),
                                       ("f", L(12, 15, 3, 10), "#5a5650"), body="#8a867c"))
_reg("double_striped_pug", _bf("#8a7a68", "#9a8a78", ("f", L(14, 12, 3, 8), "#3a2e24"), ("f", L(13, 15, 2, 12),
                                                                                       "#3a2e24"),
                                ("h", L(14, 20, 5, 20), "#5a4a3a"), body="#6a5a48"))
_reg("jasmine_moth", _bf("#f6f8f4", "#f4f6f2", ("f", L(14, 11, 6, 4), "#c8a070"),
                          ("f", D((9, 10), (11, 11)), "#3a3a3a"), body="#f0f0ea"))
_reg("old_world_webworm", _bf("#b8a080", "#d8ccb8", ("f", L(13, 12, 4, 7), "#6a5440"),
                               ("f", L(12, 15, 3, 11), "#6a5440"), ("f", E(9, 10, 0.8), "#4a3a2a"), body="#9a8466"))
_reg("four_spotted_moth", _bf("#2b2226", "#2b2226", ("f", E(8, 9, 1.6), "#f4f0e8"), ("f", E(5, 11, 1), "#f4f0e8"),
                               ("h", E(9, 21, 1.6), "#f4f0e8"), body="#1e1a1e"))
_reg("spotted_sulphur", _bf("#f0e050", "#f2ec90", ("f", D((5, 6), (8, 8), (11, 11), (6, 10), (9, 13)), "#2b2226"),
                             ("h", EDGE_H, "#4a4a30"), body="#d8c840"))
_reg("pale_shoulder", _bf("#e8e4dc", "#6a5a50", ("f", P((3, 8), (9, 9), (8, 14), (3, 13)), "#5a4a40"),
                           ("f", E(10, 9, 1), "#8a7a6a"), body="#d8d0c4"))


def _moth(wing, mark, body):
    return lambda s: _delta_moth(s, wing, mark, body)


@sprite("heart_and_dart")
def _(s):
    # A brown moth with a black "heart" kidney spot and a short black dart on each wing.
    def mark(s, m):
        s.paint(s.m_ellipse(12, 17, 1.2, 1.2) | s.m_line(12, 21, 10, 22), "#1e1a16", mirror=True, within=m)
        s.paint(s.m_line(9, 24, 14, 22), "#6a5034", mirror=True, within=m)
    _delta_moth(s, "#8a6a48", mark, "#6a5034")


@sprite("beaded_chestnut")
def _(s):
    # A rusty-chestnut autumn moth with rows of tiny dark dots like beads.
    def mark(s, m):
        s.paint(s.m_px([(12, 15), (11, 18), (10, 21), (9, 24), (13, 22)]), "#3a2014", mirror=True, within=m)
        s.paint(s.m_ellipse(13, 18, 1, 1.3), "#d89a5a", mirror=True, within=m)
    _delta_moth(s, "#a8582e", mark, "#8a4a26")


@sprite("broom_moth")
def _(s):
    # Rich chestnut-brown with a wavy white line near the wing edge.
    def mark(s, m):
        s.paint(s.m_path([(13, 22), (11, 24), (9, 25), (7, 26)], 0.45), "#f0e8d0", mirror=True, within=m)
        s.paint(s.m_ellipse(13, 16, 1.1, 1.3), "#d8a878", mirror=True, within=m)
    _delta_moth(s, "#7a4a2e", mark, "#6a3e26")


@sprite("nutmeg_moth")
def _(s):
    # A mottled gray-brown moth with a pale kidney mark and a pale zigzag near the edge.
    def mark(s, m):
        s.paint(s.m_ellipse(12.5, 17, 1.2, 1.4), "#d8ccb4", mirror=True, within=m)
        s.paint(s.m_path([(13, 23), (11, 24), (9, 23), (7, 25)], 0.4), "#d8ccb4", mirror=True, within=m)
    _delta_moth(s, "#7a6c5a", mark, "#6a5c4a")


@sprite("eurasian_hummingbird_hawkmoth")
def _(s):
    # A day-flying hawkmoth that hovers at flowers like a hummingbird: gray-brown forewings,
    # orange hindwings, a furry body with a black-and-white tail fan and a long tongue.
    s.can("fly", "eat")
    fast = s.act in ("fly", "eat")
    up = fast and s.f % 2 == 0
    for d in (-1, 1):
        x = lambda v: 16 + d * v  # noqa: E731
        lift = -3 if up else 0
        s.poly([(x(2), 13), (x(13), 9 + lift), (x(12), 14 + lift), (x(3), 17)], "#7a7468", edge=True)
        s.poly([(x(2), 16), (x(9), 16 + lift * 0.5), (x(8), 20), (x(2), 20)], "#e8882a", edge=True)
    m = s.ellipse(16, 18, 3.2, 7.5, "#8a8074", edge=True)
    s.paint(s.m_line(13, 21, 19, 21), "#f4f0e8", within=m)
    s.paint(s.m_line(13, 22, 19, 22) | s.m_line(13, 24, 19, 24), "#1e1a1e", within=m)
    s.poly([(13.5, 25), (16, 30), (18.5, 25)], "#3a3430")
    s.ellipse(16, 10, 3, 2.5, "#7a7468", edge=True)
    s.path([(16, 8), (16, 2)], 0.4, "#2b2226", shade=False)  # the long tongue
    s.eye(14, 9)
    s.eye(17, 9)


# --------------------------------------------------------------------------- dragonflies, damselflies
@sprite("broad_scarlet")
def _(s):
    # A broad, flattened scarlet-red abdomen and red veins; amber patches at the base of the hindwings.
    dragonfly(s, "#d83a2a", "#e83a2a", wing_tint="#f0c070")


@sprite("common_darter")
def _(s):
    # A slim orange-red darter with brownish thorax stripes.
    dragonfly(s, "#a85a32", "#d8502a")


@sprite("ruddy_darter")
def _(s):
    # Blood-red with a club-shaped, waisted abdomen and black legs.
    dragonfly(s, "#9a3a24", "#c82a22")


@sprite("vagrant_darter")
def _(s):
    # Orange-red with a black "moustache" line on the face.
    dragonfly(s, "#a8582e", "#d04a28")


@sprite("nomad")
def _(s):
    # The red-veined darter: red with crimson wing veins and blue-gray underneath the eyes.
    dragonfly(s, "#b8503a", "#e04a32", wing_tint="#f0b8a0")


@sprite("violet_dropwing")
def _(s):
    # The male is powdered violet-pink, with dark-red wing bases.
    dragonfly(s, "#8a3a6a", "#c85a9a", wing_tint="#c8607a")


@sprite("small_pincertail")
def _(s):
    # A yellow-and-black club-tailed dragonfly whose tail ends in a pair of pincers.
    dragonfly(s, "#d8c030", "#2b2630")
    s.paint(s.m_px([(16, 17), (16, 20), (16, 23), (16, 26)]), "#e8d040")
    s.px([(14, 30), (18, 30), (14, 31), (18, 31)], "#2b2630")


@sprite("azure_damselfly")
def _(s):
    # Sky-blue banded black, with a black U-mark at the front of the abdomen.
    _damsel(s, "#3a9ad8", "#4ab0e8", tip="#1e2a3a")
    s.paint(s.m_px([(16, 15), (16, 18), (16, 21), (16, 24)]), "#1e1a22")


@sprite("common_blue_damselfly")
def _(s):
    # Bright blue with neat black rings and a black spot like a mushroom near the front.
    _damsel(s, "#3a98e0", "#48aaf0", tip="#3a98e0")
    s.paint(s.m_px([(16, 14), (16, 17), (16, 20), (16, 23), (16, 26)]), "#1e1a22")


@sprite("beautiful_demoiselle")
def _(s):
    # A metallic blue-green body and dark smoky-blue wings.
    _damsel(s, "#2a8a7a", "#2a7aa0", wing="#3a4a6a")


# --------------------------------------------------------------------------- bees, wasps, flies, ants
@sprite("common_carder_bumble_bee")
def _(s):
    # A small, ginger-brown furry bumble bee with no bands.
    _bumble(s, [(9, 30, "#c8823a"), (22, 30, "#b07030")])


@sprite("heath_bumble_bee")
def _(s):
    # Yellow collar and band, a white tail.
    _bumble(s, [(9, 13, "#f2c42a"), (13, 17, "#2b2226"), (17, 20, "#f2c42a"), (20, 24, "#2b2226"),
                (24, 30, "#f6f2e8")])


@sprite("tree_bumble_bee")
def _(s):
    # Ginger-brown thorax, black abdomen and a white tail.
    _bumble(s, [(9, 16, "#b8682e"), (16, 24, "#2b2226"), (24, 30, "#f4f0e6")])


@sprite("white_tailed_bumble_bee")
def _(s):
    # Lemon-yellow collar and band, black between, and a pure white tail.
    _bumble(s, [(9, 13, "#f2d02a"), (13, 18, "#2b2226"), (18, 21, "#f2d02a"), (21, 25, "#2b2226"),
                (25, 30, "#f8f6f0")])


def _wasp(s, body, stripes, head, *, head_marks=None, legs=None, waist="#1e1a1e", size=1.0, wing="#e8eef8"):
    """A wasp or hornet from the side: narrow waist, banded abdomen, dangling legs."""
    s.can("fly")
    up = not (s.act == "fly" and s.f % 2)
    s.ellipse(18, 9 if up else 12, 3 * size, 7 * size if up else 3.5, wing, rot=20 if up else 75, shade=False,
              edge=True)
    s.ellipse(22, 11 if up else 14, 2.4 * size, 5 * size if up else 2.6, mix(wing, "#8aa0c0", 0.1),
              rot=35 if up else 85, shade=False, edge=True)
    for x0, x1 in ((12, 13), (15, 17), (19, 22)):
        s.line(x0, 21, x1, 28, legs or body)
    m = s.ellipse(22, 20, 7 * size, 3.8 * size, body, rot=12)
    s.poly([(27, 21), (32, 24), (27, 24)], body)
    for x0, x1, col in stripes:
        s.paint(s.m_poly([(x0, 10), (x1, 10), (x1, 30), (x0, 30)]), col, within=m)
    s.ellipse(14.5, 19, 1.4, 1.1, waist)
    th = s.ellipse(11.5, 18, 3.2 * size, 3, mix(body, "#1a1420", 0.2) if head != body else body, edge=True)
    s.paint(s.m_px([(11, 16), (12, 16)]), mix(head, WHITE, 0.2), within=th)
    hm = s.ellipse(6.5, 17, 4 * size, 4, head, edge=True)
    if head_marks:
        s.paint(head_marks(s), mix(head, "#1a1420", 0.45), within=hm)
    s.line(5, 13, 2, 6, "#4a2e1e")
    s.line(8, 13, 9, 6, "#4a2e1e")
    s.eye(4, 16, color="#11080f", shine="#ffffff")


@sprite("european_hornet")
def _(s):
    # A huge wasp: chestnut-brown and yellow, with a yellow face and a reddish-brown thorax.
    _wasp(s, "#f0c020", [(15, 18, "#6a3a1e"), (19, 20.5, "#3a2016")], "#f0c030", legs="#b0602a", size=1.15)
    s.paint(s.m_ellipse(11.5, 18, 3.6, 3.2), "#8a3a1e")


@sprite("oriental_hornet")
def _(s):
    # A reddish-brown hornet with a broad yellow band near the end of its abdomen and a yellow face.
    _wasp(s, "#8a3a1e", [(23.5, 26.5, "#f2c42a")], "#e8b030", legs="#8a3a1e", size=1.1)


@sprite("yellow_legged_hornet")
def _(s):
    # The Asian hornet: almost black, with one orange band near the tail, an orange face and yellow legs.
    _wasp(s, "#26222a", [(24, 27, "#e8902a"), (21, 22, "#c8702a")], "#e8902a", legs="#f0d040", size=1.05)


@sprite("norwegian_wasp")
def _(s):
    # A tree wasp: black and yellow bands, with red patches near the waist.
    _wasp(s, "#f2c820", [(16.5, 18, "#1e1a1e"), (20, 21.5, "#1e1a1e"), (24, 25.5, "#1e1a1e"), (15, 16.5, "#c84a2a")],
          "#f2c820", legs="#f0c020",
          head_marks=lambda s: s.m_ellipse(7, 14, 3.4, 1.4))


@sprite("longleaf_wattle_gall_wasp")
def _(s):
    # A tiny, shiny black wasp with smoky wings; it raises galls on wattle trees.
    _wasp(s, "#1e1a22", [], "#1e1a22", legs="#c8a040", size=0.85, wing="#d8dce8")


@sprite("common_drone_fly")
def _(s):
    # A honey-bee mimic hoverfly: brown with orange side patches and huge eyes.
    s.can("fly")
    up = not (s.act == "fly" and s.f % 2)
    s.ellipse(9.5, 14 if up else 18, 7, 2.6, "#e6f2fa", rot=-18 if up else 12, shade=False, edge=True, mirror=True)
    for y in (16, 19):
        s.line(13, y, 9, y + 3, "#2b2226")
        s.line(18, y, 22, y + 3, "#2b2226")
    m = s.ellipse(16, 22, 5, 7.5, "#3a2a20", edge=True)
    s.paint(s.m_ellipse(12, 20, 2, 2.5) | s.m_ellipse(20, 20, 2, 2.5), "#d8802a", within=m)
    s.paint(s.m_line(13, 24, 19, 24) | s.m_line(13, 27, 19, 27), "#b8a080", within=m)
    s.ellipse(16, 13, 4.2, 3.2, "#5a4a36", edge=True)
    s.ellipse(16, 8.5, 5, 3.4, "#4a3a2a", edge=True)
    s.ellipse(13, 8, 2.6, 2.8, "#5a3a22", shade=False, mirror=True)
    s.px([(12, 7)], WHITE, mirror=True)
    s.px([(13, 9)], EYE, mirror=True)


@sprite("marmalade_hover_fly")
def _(s):
    # A slim orange hoverfly with double black bands like mustaches across its abdomen.
    s.can("fly")
    up = not (s.act == "fly" and s.f % 2)
    s.ellipse(9.5, 14 if up else 18, 7, 2.4, "#e6f2fa", rot=-18 if up else 12, shade=False, edge=True, mirror=True)
    for y in (16, 19):
        s.line(13, y, 9, y + 3, "#c88a3a")
        s.line(18, y, 22, y + 3, "#c88a3a")
    m = s.ellipse(16, 22.5, 3.6, 8, "#f0902a", edge=True)
    for y in (18, 22.5, 26.5):
        s.paint(s.m_line(12, y, 20, y), "#1e1a1e", within=m)
        s.paint(s.m_line(15, y + 1.5, 17, y + 1.5), "#1e1a1e", within=m)
    s.ellipse(16, 13, 3.8, 3, "#5a5040", edge=True)
    s.ellipse(16, 8.5, 4.6, 3.2, "#e8a040", edge=True)
    s.ellipse(13, 8, 2.4, 2.8, "#a83a22", shade=False, mirror=True)
    s.px([(12, 7)], WHITE, mirror=True)
    s.px([(13, 9)], EYE, mirror=True)


@sprite("nodal_desert_ant")
def _(s):
    # A long-legged, fast desert ant: red-brown head and thorax, a black abdomen held up high.
    s.can("walk")
    w = s.wave() if s.act == "walk" else 0
    c, d = "#b8502a", "#7a2e18"
    for i, (x, dx) in enumerate(((12, -3.5), (14, 0), (16, 3.5))):
        sw = w * 1.8 * (1 if i % 2 else -1)
        s.path([(x, 19), (x + dx + sw, 24), (x + dx * 1.4 + sw, 29)], 0.5, d, shade=False)
    s.ellipse(23, 16.5, 4.5, 3.6, "#1e1a1e", rot=-25, edge=True)
    s.ellipse(18, 18.5, 1.3, 1.6, c)
    s.ellipse(13.5, 18.5, 3.6, 2.2, c, edge=True)
    s.path([(6, 14), (4, 8), (1, 6)], 0.5, d, shade=False)
    s.path([(8, 14), (9, 8), (7, 5)], 0.5, d, shade=False)
    s.ellipse(7.5, 17, 3.2, 3, c, edge=True)
    s.eye(5, 16)


# --------------------------------------------------------------------------- beetles
@sprite("european_stag_beetle")
def _(s):
    # Europe's biggest beetle: chestnut wing cases, a black head and huge red-brown antler jaws.
    for d in (-1, 1):
        x = lambda v: 16 + d * v  # noqa: E731
        s.path([(x(2.5), 5.5), (x(5), 1), (x(4.5), -2.5), (x(2), -3.5)], (1.3, 0.7), "#7a3a20")
        s.px([(round(x(5.4)), 0)], "#7a3a20")
    beetle_top(s, "#7a3a1e", head="#2b2226", pron="#2b2226")
    s.px([(11, 18), (20, 17), (12, 24)], "#a8603a")


@sprite("lesser_stag_beetle")
def _(s):
    # A dull black stag beetle with short, stout jaws and a broad head.
    beetle_top(s, "#26222a", head="#26222a", pron="#2b2730")
    for d in (-1, 1):
        s.path([(16 + d * 2.5, 5.5), (16 + d * 3.5, 3), (16 + d * 2, 2)], (0.9, 0.6), "#26222a")


@sprite("european_rose_chafer")
def _(s):
    # A shining metallic-green beetle with a few white flecks on its wing cases.
    beetle_top(s, "#3ab05a", head="#2a8a48", pron="#34a052")
    s.paint(s.m_px([(11, 22), (13, 25), (20, 23), (19, 27), (12, 19)]), "#f0f0e8", within=s.m_ellipse(16, 20, 10, 10))


@sprite("mediterranean_spotted_chafer")
def _(s):
    # A small, hairy black chafer covered in neat white spots.
    beetle_top(s, "#1e1a22", head="#1e1a22", pron="#26222a")
    s.paint(s.m_px([(10, 15), (12, 19), (11, 24), (13, 27), (21, 15), (19, 19), (20, 24), (18, 27),
                    (14, 11), (18, 11)]), "#f4f2ea")


@sprite("alder_leaf_beetle")
def _(s):
    # A small, glossy metallic violet-blue leaf beetle.
    beetle_top(s, "#3a3a9a", head="#2a2a6a", pron="#33338a")
    s.paint(s.m_ellipse(12, 16, 1.5, 3), "#6a6ad0", within=s.m_ellipse(16, 20, 10, 10))


@sprite("woodland_dor_beetle")
def _(s):
    # A round, shiny dung beetle of the woods, glowing deep blue-violet.
    beetle_top(s, "#2a3070", head="#1e2250", pron="#283070")
    for x in (10, 13, 19, 22):
        s.paint(s.m_line(x, 13, x, 28), "#3a46a0", within=s.m_ellipse(16, 20, 10, 10))


@sprite("red_pine_longhorn_beetle")
def _(s):
    # A long, slim beetle with red wing cases, a black head and long jointed antennae.
    s.path([(13, 6), (8, 2), (4, 2), (1, 6)], 0.5, "#2b2226", shade=False)
    s.path([(18, 6), (23, 2), (27, 2), (30, 6)], 0.5, "#2b2226", shade=False)
    beetle_top(s, "#d8402a", head="#1e1a22", pron="#1e1a22")


# --------------------------------------------------------------------------- true bugs, cicada
def _shield(s, body, *, pron=None, marks=None, legs="#3a4a2a", head=None, round_=False):
    """A shield bug from above: a broad shield shape, a small head, six legs and antennae."""
    s.can("walk")
    w = s.wave() if s.act == "walk" else 0
    for i, y in enumerate((15, 19, 23)):
        d = round(w * (1 if i % 2 else -1))
        s.line(9, y, 5, y + 3 + d, legs)
        s.line(22, y, 26, y + 3 - d, legs)
    s.line(14, 6, 11, 1, legs)
    s.line(17, 6, 20, 1, legs)
    s.ellipse(15.5, 7, 3, 2.4, head or body, edge=True)
    pts = [(6, 13), (9, 9), (22, 9), (25, 13), (23, 22), (15.5, 30), (8, 22)] if not round_ else \
        [(6, 13), (9, 9), (22, 9), (25, 13), (25, 22), (19, 29), (12, 29), (6, 22)]
    m = s.poly(pts, body, edge=True)
    if pron:
        s.paint(s.m_poly([(6, 13), (25, 13), (24, 16), (7, 16)]), pron, within=m)
    s.paint(s.m_poly([(11, 25), (20, 25), (15.5, 30)]), _dk(body, 0.3), within=m)
    if marks:
        marks(s, m)
    s.px([(13, 6), (18, 6)], EYE)
    s.px([(13, 6)], WHITE)


@sprite("green_shield_bug")
def _(s):
    # Bright leaf-green and shield-shaped, with dark-brown wing tips.
    _shield(s, "#5aa83a")


@sprite("southern_green_stink_bug")
def _(s):
    # Plain green with three tiny pale dots along the front of the shield.
    _shield(s, "#6ab040", marks=lambda s, m: s.paint(s.m_px([(10, 17), (15.5, 17), (21, 17)]), "#f0ecd0", within=m))


@sprite("brown_marmorated_stink_bug")
def _(s):
    # Mottled gray-brown with banded antennae and a checkered edge.
    _shield(s, "#8a7458", legs="#6a5a48", marks=lambda s, m: (
        s.paint(s.m_px([(10, 12), (13, 14), (18, 13), (21, 15), (12, 19), (19, 19), (15, 22)]), "#5a4a38", within=m),
        s.paint(s.m_px([(6, 13), (7, 17), (8, 21), (25, 13), (24, 17), (23, 21)]), "#f0ece0", within=m)))


@sprite("sloe_bug")
def _(s):
    # A hairy, purple-brown shield bug with a cream tip to its triangle and checkered edges.
    _shield(s, "#9a5a4a", legs="#6a4a3a", marks=lambda s, m: (
        s.paint(s.m_ellipse(15.5, 22, 2, 2.6), "#f0e0c0", within=m),
        s.paint(s.m_px([(6, 13), (7, 17), (8, 21), (25, 13), (24, 17), (23, 21)]), "#2b2226", within=m)))


@sprite("yellow_spotted_stink_bug")
def _(s):
    # A big black stink bug sprinkled with yellow dots and a yellow line down its head.
    _shield(s, "#2a2a2e", legs="#2a2a2e", marks=lambda s, m: s.paint(
        s.m_px([(9, 12), (13, 11), (18, 11), (22, 12), (10, 17), (15, 15), (21, 17), (12, 21), (19, 21),
                (15, 25)]), "#f0d040", within=m))


@sprite("indian_milkweed_bug")
def _(s):
    # A red-orange bug with a black cross-shaped pattern and black wing membranes.
    _shield(s, "#d8502a", legs="#1e1a1e", head="#1e1a1e", marks=lambda s, m: (
        s.paint(s.m_line(15.5, 10, 15.5, 24) | s.m_line(15, 10, 15, 24), "#1e1a1e", within=m),
        s.paint(s.m_ellipse(11, 15, 1.5, 1.5) | s.m_ellipse(20, 15, 1.5, 1.5), "#1e1a1e", within=m)))


@sprite("mediterranean_red_bug")
def _(s):
    # A slim red bug with black spots and a pale wing edge, crowding together in the sun.
    _shield(s, "#d0402a", legs="#3a2a2a", head="#2b2226", marks=lambda s, m: s.paint(
        s.m_ellipse(11, 18, 1.4, 1.4) | s.m_ellipse(20, 18, 1.4, 1.4) | s.m_ellipse(15.5, 13, 1.8, 1.4),
        "#1e1a1e", within=m))


@sprite("ash_cicada")
def _(s):
    # A big gray-brown cicada with clear, dark-veined wings folded like a tent over its back,
    # and wide-set eyes on a broad head.
    s.can("fly")
    up = s.act == "fly" and s.f % 2 == 0
    for d in (-1, 1):
        x = lambda v: 16 + d * v  # noqa: E731
        sp = 4 if up else 0
        m = s.poly([(x(1), 11), (x(8 + sp), 14), (x(9 + sp), 22), (x(5 + sp * 0.5), 30), (x(0.5), 30)],
                   "#cfdcd6", shade=False, edge=True)
        s.paint(s.m_line(x(2), 13, x(7 + sp), 24) | s.m_line(x(6 + sp), 15, x(4 + sp * 0.5), 29), "#6a6258", within=m)
        s.paint(s.m_px([(round(x(6 + sp)), 20), (round(x(4.5 + sp * 0.5)), 26)]), "#3a3028", within=m)
    s.ellipse(16, 19, 4.4, 8.5, "#7a6a58", edge=True)
    s.paint(s.m_ellipse(16, 14, 3.4, 2), "#4a3c30", within=s.last)
    s.paint(s.m_line(16, 18, 16, 26), "#5a4c3e")
    s.ellipse(16, 9.5, 5, 3.4, "#8a7a66", edge=True)
    s.poly([(14, 6), (16, 4.5), (18, 6)], "#6a5a48")
    s.ellipse(11, 9, 1.6, 1.8, "#3a2e26", shade=False)
    s.ellipse(21, 9, 1.6, 1.8, "#3a2e26", shade=False)
    s.px([(11, 8), (21, 8)], WHITE)


# --------------------------------------------------------------------------- grasshoppers, crickets, mantises
@sprite("italian_locust")
def _(s):
    # A stout brown grasshopper with pale stripes and pink-red hindwings and inner hind legs.
    grasshopper(s, "#9a7a58", "#6a5038", legs="#b08a64")
    s.paint(s.m_line(9, 13, 14, 16) | s.m_line(14, 16, 26, 16), "#e8dcc0")
    s.paint(s.m_line(21, 18, 26, 14), "#e07a7a")


@sprite("egyptian_bird_grasshopper")
def _(s):
    # A huge gray-brown locust with striped eyes and long wings reaching past its tail.
    grasshopper(s, "#a08e74", "#7a6a54", legs="#b0a084")
    s.path([(16, 17), (32, 16)], (1.6, 1.0), "#8a7a62")
    s.paint(s.m_px([(5, 14), (5, 16), (7, 15)]), "#3a3028")


@sprite("lamenting_grasshopper")
def _(s):
    # A slim tan grasshopper with pale bands on its hind legs.
    grasshopper(s, "#b09a72", "#8a7454", legs="#c8b088")
    s.paint(s.m_px([(23, 16), (25, 19), (27, 22)]), "#f0e8d0")


@sprite("great_green_bush_cricket")
def _(s):
    # A huge leaf-green katydid with very long antennae and wings longer than its body.
    grasshopper(s, "#5aa840", "#3a8a30", legs="#6ab848")
    s.path([(16, 18), (33, 15)], (1.8, 1.0), "#6ab848")
    s.paint(s.m_line(14, 15, 26, 15), "#8a6a3a")
    s.line(7, 12, 2, -1, "#4a8a3a")
    s.line(9, 12, 14, -1, "#4a8a3a")


@sprite("dark_bush_cricket")
def _(s):
    # A chunky dark-brown bush cricket with a yellow-green belly, tiny wings and long antennae.
    grasshopper(s, "#5a4232", "#3a2a1e", legs="#6a5040")
    s.paint(s.m_ellipse(20, 23, 7, 1.4), "#c8c060")
    s.line(7, 12, 2, -1, "#3a2a1e")
    s.line(9, 12, 14, -1, "#3a2a1e")


@sprite("schmidts_marbled_bush_cricket")
def _(s):
    # A plump, marbled brown-and-cream bush cricket of the Balkans.
    grasshopper(s, "#a08868", "#6a5040", legs="#b09874")
    s.paint(s.m_px([(18, 19), (21, 20), (24, 19), (19, 22), (23, 22)]), "#f0e4cc")
    s.line(7, 12, 2, -1, "#5a4434")
    s.line(9, 12, 14, -1, "#5a4434")


@sprite("giant_african_mantis")
def _(s):
    # A big bright-green mantis with a pale spot on each wing.
    mantis(s, "#6ab040", "#8ac860", "#c8e07a")
    s.px([(25, 18), (26, 18)], "#f4f0d8")


@sprite("transcaucasian_giant_mantis")
def _(s):
    # A broad, leaf-green mantis with a cream stripe along the wing edge.
    mantis(s, "#5aa83a", "#7ac050", "#c0d870")
    s.paint(s.m_line(20, 19, 29, 17), "#f0ecc0")


# --------------------------------------------------------------------------- spiders and harvestmen
@sprite("european_nursery_web_spider")
def _(s):
    # A long-legged brown hunting spider with a pale stripe down its middle.
    spider_top(s, "#8a6a4a", "#7a5a40", ceph="#8a6a4a",
               pattern=lambda s, m: s.paint(s.m_line(16, 15, 16, 29), "#e8dcc4", within=m))
    s.paint(s.m_line(16, 10, 16, 16), "#e8dcc4")


@sprite("mediterranean_spiny_false_wolf_spider")
def _(s):
    # A big hairy fawn spider with dark markings and spiny legs.
    spider_top(s, "#b09070", "#9a7a5a", ceph="#a08060", leg_bands="#5a4434",
               pattern=lambda s, m: s.paint(s.m_px([(15, 17), (17, 17), (14, 21), (18, 21), (15, 25), (17, 25)]),
                                            "#4a3626", within=m))


@sprite("middle_east_black_tarantula")
def _(s):
    # A big, velvety black tarantula with thick hairy legs.
    spider_top(s, "#1e1a1e", "#26222a", ceph="#2b2630", leg_bands="#3a3438")


@sprite("half_edged_wall_jumping_spider")
def _(s):
    # A flat gray jumping spider of sunny walls, with a white-edged face.
    spider_top(s, "#8a8478", "#6a645a", ceph="#5a544c",
               pattern=lambda s, m: s.paint(s.m_line(16, 16, 16, 28), "#3a3630", within=m))
    s.px([(13, 10), (14, 10), (17, 10), (18, 10)], WHITE)


@sprite("pantropical_jumping_spider")
def _(s):
    # A dark-brown jumping spider with a white band down the middle of its back.
    spider_top(s, "#4a3a2e", "#5a4a3a", ceph="#3a2e24",
               pattern=lambda s, m: s.paint(s.m_line(15, 15, 15, 28) | s.m_line(16, 15, 16, 28), "#f0ece0", within=m))


@sprite("red_bellied_jumping_spider")
def _(s):
    # A jumping spider with a bright orange-red back marked black and white.
    spider_top(s, "#e0502a", "#2b2226", ceph="#2b2226", leg_bands="#e8e4dc",
               pattern=lambda s, m: s.paint(s.m_line(16, 15, 16, 28) | s.m_ellipse(16, 27, 2, 1.2), "#1e1a1e",
                                            within=m))


@sprite("saddleback_harvestman")
def _(s):
    # A harvestman (not a true spider): a small round body with a dark saddle, on eight very long thin legs.
    s.can("walk")
    w = s.wave() if s.act == "walk" else 0
    for i, (a, b) in enumerate([((14, 17), (4, 4)), ((14, 18), (0, 12)), ((14, 19), (0, 26)), ((15, 19), (6, 30))]):
        d = w * 1.5 * (1 if i % 2 else -1)
        s.path([a, ((a[0] + b[0]) / 2, min(a[1], b[1]) - 3 + d), (b[0], b[1] + d)], 0.45, "#5a4a3a", shade=False,
               mirror=True)
    m = s.ellipse(16, 19, 4.5, 3.8, "#b89a74", edge=True)
    s.paint(s.m_ellipse(16, 19, 3, 2.4), "#4a3628", within=m)
    s.eye(15, 17, size=1)
    s.eye(17, 17, size=1)


# --------------------------------------------------------------------------- land snails and slugs
def _land_snail(s, shell, bands=None, *, body="#d8c8b0", flecks=None, tall=False):
    """A land snail gliding left, its spiral shell banded or flecked."""
    s.can("walk")
    st = s.cyc(0, 1, 2, 1) if s.act == "walk" else 0
    inside = s.act == "sleep"
    s.ellipse(15 - st / 2, 27.5, 12 + st / 2, 2.4, body)
    if tall:  # a tall cone (decollate snail)
        m = s.poly([(9, 26), (12, 10), (16, 4), (20, 10), (23, 26)], shell, edge=True)
        for y in (9, 14, 19, 24):
            s.paint(s.m_line(10, y + 1, 22, y - 1), _dk(shell, 0.3), within=m)
    else:
        m = s.ellipse(17, 18, 9.5, 9, shell, edge=True)
        for k, r in enumerate((7.5, 5, 2.5)):
            s.paint(s.m_ellipse(18 + k * 0.5, 17.5, r + 0.6, r + 0.5) & ~s.m_ellipse(18 + k * 0.5, 17.5, r, r),
                    _dk(shell, 0.25), within=m)
        for col, r in (bands or []):
            s.paint(s.m_ellipse(17, 18, r + 0.7, r + 0.7) & ~s.m_ellipse(17, 18, r - 0.2, r - 0.2), col, within=m)
        if flecks:
            s.paint(s.m_px([(11, 13), (14, 11), (20, 12), (23, 16), (12, 21), (22, 22), (16, 24), (19, 15)]), flecks,
                    within=m)
    if inside:
        return
    s.ellipse(6 - st, 24, 5, 3.3, body, edge=True)
    s.line(4 - st, 21, 3 - st, 16, body)
    s.line(7 - st, 21, 8 - st, 16, body)
    s.px([(3 - st, 15), (8 - st, 15)], _dk(body, 0.5))


@sprite("roman_snail")
def _(s):
    # The big edible snail: a creamy-brown globe of a shell with faint bands.
    _land_snail(s, "#c8ac80", [("#a88a5e", 7), ("#a88a5e", 4)], body="#d8ccb4")


@sprite("turkish_snail")
def _(s):
    # A large snail with broad brown bands on a cream shell.
    _land_snail(s, "#e0c898", [("#7a5634", 7.5), ("#7a5634", 4.5)], body="#c8b8a0")


@sprite("chocolate_band_snail")
def _(s):
    # A cream shell crossed by bold chocolate-brown bands.
    _land_snail(s, "#ece0c4", [("#5a3a24", 7.5), ("#5a3a24", 5.5), ("#5a3a24", 3)], body="#d0c0a8")


@sprite("vineyard_snail")
def _(s):
    # A pale shell with five neat dark-brown bands.
    _land_snail(s, "#f0e8d4", [("#4a3020", 8), ("#4a3020", 6.2), ("#4a3020", 4.4), ("#4a3020", 2.6)],
                body="#d8ccb4")


@sprite("copse_snail")
def _(s):
    # A brown shell flecked with yellow, with one dark band, and a dark body.
    _land_snail(s, "#8a6a40", [("#3a2618", 6)], body="#4a4442", flecks="#e8c860")


@sprite("white_italian_snail")
def _(s):
    # A chalky-white shell with thin broken brown lines; it gathers on plants in summer.
    _land_snail(s, "#f4f0e4", [("#a88a6a", 7), ("#a88a6a", 3.5)], body="#e8dccb", flecks="#8a6a4a")


@sprite("decollate_snail")
def _(s):
    # A tall, tapering tan shell with its tip snapped off on purpose; it eats other snails.
    _land_snail(s, "#c8a878", body="#4a3e36", tall=True)
    s.erase(s.m_ellipse(16, 3, 4, 2.5))


@sprite("ash_black_slug")
def _(s):
    # The world's biggest land slug: long and black or ash-gray, with a pale keel down its back.
    c = "#3a383c"
    st = s.cyc(0, 1, 2, 1) if s.act == "walk" else 0
    s.can("walk")
    s.ellipse(17 - st / 2, 25, 13.5 + st / 2, 4.3, c)
    s.path([(12, 24), (8 - st, 21), (4 - st, 19.5)], (3.6, 3.0), c)
    s.ellipse(17, 28, 13, 1.4, "#c8c4c0")
    s.paint(s.m_ellipse(11, 22, 5, 3), mix(c, "#ffffff", 0.12))
    s.paint(s.m_line(16, 21, 30, 23), "#8a8890", within=s.m_ellipse(17, 25, 13.5, 4.3))
    s.line(3 - st, 17, 1 - st, 13, c)
    s.line(5 - st, 17, 6 - st, 13, c)
    s.px([(1 - st, 12), (6 - st, 12)], "#6a6870")


# --------------------------------------------------------------------------- sea snails and a clam
def _whelk(s, shell, *, body="#e8d8c0", ridges=None, spines=False, bands=None):
    """A sea snail with a tall spiral shell (pointing up and back), crawling left."""
    s.can("walk")
    st = s.cyc(0, 1, 2, 1) if s.act == "walk" else 0
    s.ellipse(14 - st / 2, 28, 11 + st / 2, 2.2, mix(body, "#000000", 0.15))
    s.ellipse(7 - st, 25, 5, 3, body, edge=True)
    s.line(5 - st, 22, 4 - st, 18, body)
    s.line(8 - st, 22, 9 - st, 18, body)
    m = s.poly([(9, 27), (9, 19), (13, 12), (17, 4), (21, 10), (25, 18), (26, 26)], shell, edge=True)
    for y in (10, 15, 20):
        s.paint(s.m_line(10, y + 1.5, 25, y - 1.5), ridges or _dk(shell, 0.3), within=m)
    for y in (bands or []):
        s.paint(s.m_line(10, y + 1, 25, y - 1) | s.m_line(10, y + 2, 25, y), bands[y], within=m)
    if spines:
        for x, y in ((11, 19), (25, 17), (22, 9), (26, 24)):
            s.px([(x - 1 if x < 17 else x + 1, y)], shell)
    s.paint(s.m_ellipse(15, 24, 3, 2), mix(shell, WHITE, 0.5), within=m)
    s.px([(4 - st, 17), (9 - st, 17)], "#2b2226")


@sprite("common_whelk")
def _(s):
    # A big, cream-to-brown spiral shell with fine ridges, from the North Atlantic.
    _whelk(s, "#d8c098", ridges="#a8885e", body="#f0e4cc")


@sprite("atlantic_dogwhelk")
def _(s):
    # A thick, pointed shell, white, yellow or banded brown, on rocky shores.
    _whelk(s, "#e8dcc0", body="#f0e8d8", bands={13: "#8a6a4a", 19: "#8a6a4a"})


@sprite("banded_dye_murex")
def _(s):
    # A spiny murex shell with dark purple-brown bands; it was once used to make purple dye.
    _whelk(s, "#c8b8a0", ridges="#6a4a5a", body="#e0d0c0", spines=True, bands={16: "#5a3a4a"})


@sprite("turbinate_monodont")
def _(s):
    # A round top shell with zigzag dark-green-and-cream checks and a pearly mouth.
    s.can("walk")
    st = s.cyc(0, 1, 2, 1) if s.act == "walk" else 0
    s.ellipse(14 - st / 2, 28, 11 + st / 2, 2.2, "#4a4a40")
    s.ellipse(7 - st, 25, 5, 3, "#d8c8b0", edge=True)
    s.line(5 - st, 22, 4 - st, 18, "#d8c8b0")
    s.line(8 - st, 22, 9 - st, 18, "#d8c8b0")
    m = s.poly([(8, 27), (11, 17), (17, 9), (23, 17), (26, 27)], "#e8e0c8", edge=True)
    for y in (13, 17, 21, 25):
        s.paint(s.m_px([(x, y) for x in range(10, 26, 2)]), "#3a5a40", within=m)
    s.paint(s.m_ellipse(14, 25, 2.5, 1.8), "#e8f0f4", within=m)
    s.px([(4 - st, 17), (9 - st, 17)], "#2b2226")


@sprite("rough_periwinkle")
def _(s):
    # A small, ridged periwinkle of the high shore, yellow-brown to gray.
    s.ellipse(14, 28, 12, 2.2, "#5a5048")
    s.ellipse(7, 25, 5, 3, "#6a605a", edge=True)
    s.line(5, 22, 3, 17, "#2b2626")
    s.line(8, 22, 9, 17, "#2b2626")
    s.poly([(17, 13), (22, 5), (25, 13)], "#9a8058", edge=True)
    m = s.ellipse(18, 19, 9.5, 8.5, "#a88a5e", edge=True)
    for r in (3, 5.5, 8):
        s.paint(s.m_ellipse(20, 17, r + 0.8, r + 0.7) & ~s.m_ellipse(20, 17, r, r), "#6a5434", within=m)
    s.paint(s.m_ellipse(11, 24, 3, 2.2), "#ece0cc", within=m)


@sprite("ocean_quahog")
def _(s):
    # A thick, rounded clam with a dark brown-black skin, half buried, its siphons up.
    s.ellipse(16, 29, 14, 2, "#c8b48a")
    if s.act != "sleep":
        s.path([(22, 17), (24, 12)], (1.2, 0.9), "#e8c8a8")
    m = s.ellipse(16, 22, 11.5, 8, "#3a2e26", edge=True)
    for r in (3, 6, 9):
        s.paint(s.m_ellipse(13, 28, r + 3.5, r + 0.6) & ~s.m_ellipse(13, 28, r + 2.8, r), "#5a4a3a", within=m)
    s.paint(s.m_ellipse(11, 16, 2, 1.2), "#6a5a48", within=m)


# --------------------------------------------------------------------------- sea slugs and the octopus
def _sea_slug(s, body, *, gills=None, rhino=None, stripes=None, cerata=None, tip=None, spots=None, clubs=None):
    """A nudibranch crawling left: a soft body, two rhinophores, and gills or cerata."""
    s.can("walk")
    st = s.cyc(0, 1, 2, 1) if s.act == "walk" else 0
    if cerata:
        for i in range(7):
            x = 9 + i * 2.8
            top = 15 + (i % 2) * 2
            p = s.path([(x, 22), (x + 0.8, 18), (x + 1.4, top)], (1.0, 0.7), cerata, edge=True)
            if tip:
                s.paint(s.m_ellipse(x + 1.4, top, 0.9, 1), tip, within=p)
    if clubs:
        for x in (8, 12, 19, 23, 27):
            s.path([(x, 22), (x, 17)], (0.6, 0.5), clubs, shade=False)
            s.ellipse(x, 16.5, 1, 1, clubs)
    if gills:
        for dx in (-2, 0, 2):
            s.path([(25, 21), (25 + dx, 16)], (0.6, 0.4), gills, shade=False)
    r = rhino or body
    s.path([(5 - st, 21), (4 - st, 16)], (0.8, 0.6), r, shade=False)
    s.path([(8 - st, 21), (8 - st, 16)], (0.8, 0.6), r, shade=False)
    m = s.ellipse(15 - st / 2, 24.5, 13.5 + st / 2, 4.5, body, edge=True)
    if stripes:
        for y in (22, 24.5, 27):
            s.paint(s.m_line(3, y, 28, y), stripes, within=m)
    if spots:
        s.paint(s.m_px([(9, 22), (13, 21), (17, 22), (21, 21), (12, 25), (19, 25), (24, 23)]), spots, within=m)


@sprite("four_lined_polycera")
def _(s):
    # A see-through white sea slug with yellow lines and yellow-tipped rhinophores and gills.
    _sea_slug(s, "#e8eef0", gills="#f0d020", rhino="#f0d020", stripes="#f0d020")


@sprite("orange_clubbed_sea_slug")
def _(s):
    # A white sea slug fringed with bright orange-tipped clubs.
    _sea_slug(s, "#f4f2ec", rhino="#f08a20", gills="#f08a20", clubs="#f08a20", spots="#f0a050")


@sprite("red_fingered_coryphella")
def _(s):
    # A slender, see-through sea slug covered in finger-like red cerata with white tips.
    _sea_slug(s, "#ece8f0", cerata="#d8402a", tip=WHITE)


@sprite("velvet_dorid")
def _(s):
    # A soft, velvety cream-gray sea slug with brown blotches and a frilly gill tuft.
    _sea_slug(s, "#d8ccb4", gills="#a89a80", rhino="#8a7a62", spots="#6a5a46")


@sprite("common_octopus")
def _(s):
    # A mottled reddish-brown octopus with curling arms and gold eyes.
    s.can("swim")
    w = s.wave() if s.act == "swim" else 0
    c, dark = "#a8604a", "#7a4232"
    for i, (x0, x1, x2) in enumerate(((10, 5, 1), (12, 9, 5), (15, 14, 12), (17, 18, 20), (20, 23, 27), (22, 27, 31))):
        d = w * (1 if i % 2 else -1)
        m = s.path([(x0, 18), (x1 + d, 24), (x2, 28), (x2 + (2 if x2 < 16 else -2), 25 + d)], (2.0, 0.7),
                   c if i % 2 else dark)
        s.paint(s.m_px([(round(x1 + d), 25), (x2, 27)]), "#f0c8b0", within=m)
    s.ellipse(16, 10, 8.5, 9.5, c, edge=True)
    s.paint(s.m_px([(14, 4), (18, 3), (20, 6), (15, 8), (12, 11), (21, 12), (17, 17), (11, 16), (22, 16)]), dark)
    s.paint(s.m_px([(16, 5), (19, 9), (13, 14)]), "#d8a080")
    s.ellipse(11.5, 12.5, 2.2, 2.2, "#e8c060", shade=False)
    s.ellipse(20.5, 12.5, 2.2, 2.2, "#e8c060", shade=False)
    s.eye(11, 12)
    s.eye(20, 12)
