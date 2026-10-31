"""Sprites for the Ohio species that aren't on an earlier state's list."""
from __future__ import annotations

from archetypes import (BLACK, WHITE, critter, dragonfly, fish, frog, lizard, sprite, turtle)
from pixel import mix


# --------------------------------------------------------------------------- mammals
@sprite("southern_flying_squirrel")
def _(s):
    # Huge dark eyes and the furry gliding flap stretched between its legs.
    def flap(s, g):
        if g["act"] in ("idle", "walk", "look", "back"):
            s.paint(s.m_ellipse(g["bx"], g["by"] + g["bry"] * 0.75, g["brx"] * 0.85, 1.3), "#7a6a5a", within=g["body"])
    critter(s, "#a8927a", "#f4ece0", build="squirrel", ear_in="#d8b8a0", tail="squirrel", tail_col="#9a8670",
            eye_size=3, markings=flap)


@sprite("eastern_meadow_vole")
def _(s):
    critter(s, "#6a5440", "#b8a890", build="vole", ear_in="#a08070", tail="short", nose="#3a2a24")


# --------------------------------------------------------------------------- reptiles
@sprite("northern_map_turtle")
def _(s):
    # Fine yellow lines like a map on its shell and skin.
    turtle(s, "#5a6a4a", "#4a5a3a", scutes="#6e7e58", rim="#d8c060")
    s.paint(s.m_path([(9, 22), (13, 20), (17, 22), (21, 20), (25, 22)], 0.45), "#d8c060")
    s.paint(s.m_line(3, 19, 8, 21) | s.m_line(3, 21, 8, 23), "#e8d070")


@sprite("common_wall_lizard")
def _(s):
    # Brown back with a dark net pattern; a city escapee that loves old walls.
    def pat(s, m):
        s.paint(s.m_px([(9, 20), (11, 21), (13, 20), (15, 21), (17, 20), (19, 21), (21, 20), (12, 23), (18, 23)]),
                "#2e2a22", within=m)
    lizard(s, "#8a7a54", "#e8e0c0", head="#7a6c4a", pattern=pat, tail_col="#7a6c4a", throat="#f0e8c8")


# --------------------------------------------------------------------------- amphibians
@sprite("gray_treefrog")
def _(s):
    # The dark star on its back and a white spot under each eye.
    frog(s, "#9aa090", "#f4f0e4", build="tree", pads=True, under_eye=WHITE,
         markings=lambda s, g: s.paint(s.m_ellipse(g["bx"], g["by"] - g["bry"] * 0.4, 2.6, 1.4, g["brot"]), "#5a6050",
                                       within=g["body"]))


# --------------------------------------------------------------------------- fish
@sprite("creek_chub")
def _(s):
    def pat(s, m):
        s.paint(s.m_path([(5, 16), (15, 16.5), (25, 16)], 0.8), "#4a4a3e", within=m)
        s.paint(s.m_ellipse(24, 16, 1.4, 1.4), "#1e1e22", within=m)
    fish(s, "#9a9070", "#ece4cc", fin="#8a8060", pattern=pat, slim=True)


@sprite("rainbow_darter")
def _(s):
    # A breeding male: blue-green bars over orange.
    def pat(s, m):
        for x in (10, 14, 18, 22):
            s.paint(s.m_line(x, 11, x, 21) | s.m_line(x + 1, 11, x + 1, 21), "#3a7a8a", within=m)
    fish(s, "#e07a3a", "#f4c88a", fin="#4a8aa0", pattern=pat, slim=True)


# --------------------------------------------------------------------------- insects
def _damsel(s, thorax, abdomen, *, tip=None, wing="#eef6fc"):
    """A damselfly: slimmer than a dragonfly, wide-set eyes, a thin tail."""
    s.can("fly")
    flap = (0, 12, 0, -12)[s.f] if s.act == "fly" else 0
    for cy in (10, 13):
        rot = (-10 if cy == 10 else 8) + (flap if cy == 10 else -flap)
        s.ellipse(9, cy, 6.5, 1.5, wing, rot=rot, shade=False, edge=True, mirror=True)
    s.path([(16, 13), (16, 30)], (1.0, 0.8), abdomen)
    if tip:
        s.path([(16, 26), (16, 30)], (1.0, 0.8), tip, shade=False)
    s.ellipse(16, 10.5, 1.8, 3, thorax, edge=True)
    s.ellipse(16, 5.5, 3.2, 2, thorax, edge=True)
    s.ellipse(13, 5.2, 1.6, 1.8, mix(thorax, "#000000", 0.3), mirror=True, shade=False)
    s.px([(12, 4), (19, 4)], WHITE)


@sprite("eastern_forktail")
def _(s):
    _damsel(s, "#3a7a3a", "#1e2a22", tip="#4aa8e0")


@sprite("fragile_forktail")
def _(s):
    _damsel(s, "#4a8a3a", "#2a3428", tip="#6ab8d8")
    s.px([(15, 9), (17, 9)], "#d8e840")  # the broken "exclamation" stripes on its shoulders


@sprite("widow_skimmer")
def _(s):
    dragonfly(s, "#4a4a5a", "#b8c4d4")
    wings = s.m_ellipse(8, 10, 7.5, 2.1) | s.m_ellipse(8, 14, 7.5, 2.1)
    wings |= s.m_ellipse(24, 10, 7.5, 2.1) | s.m_ellipse(24, 14, 7.5, 2.1)
    s.paint(wings & s.m_poly([(8, 6), (24, 6), (24, 18), (8, 18)]), "#3a3034")  # dark inner half of each wing
    s.paint(wings & (s.m_poly([(4, 6), (7, 6), (7, 18), (4, 18)]) | s.m_poly([(25, 6), (28, 6), (28, 18), (25, 18)])),
            "#f4f6f8")


@sprite("eastern_amberwing")
def _(s):
    dragonfly(s, "#b87a2a", "#c88a3a", wing="#f8d890")


@sprite("autumn_meadowhawk")
def _(s):
    dragonfly(s, "#a83a2a", "#d8402a")
    s.path([(16, 15), (16, 29)], 0.4, BLACK, shade=False)
