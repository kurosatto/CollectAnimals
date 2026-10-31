"""Sprites for the Illinois species that aren't on an earlier state's list."""
from __future__ import annotations

from archetypes import (BLACK, WHITE, back_stripes, bird, butterfly, critter, duck, fish, flecks, frog, snake,
                        sprite, turtle, wader)
from pixel import mix
from species_va import _woodlouse


# --------------------------------------------------------------------------- mammals
@sprite("thirteen_lined_ground_squirrel")
def _(s):
    # Rows of pale stripes and dots down its back.
    def stripes(s, g):
        back_stripes(s, g, ["#f0e2c4", "#5a3a1e", "#f0e2c4", "#5a3a1e", "#f0e2c4"], top=0.1)
        flecks(s, g["body"] & s.m_ellipse(g["bx"], g["by"] - 1, g["brx"], 2.2), "#f0e2c4", every=4)
    critter(s, "#9a6e42", "#f0e2c4", build="ground", ear_in="#d0a080", tail="long", tail_col="#8a5e36",
            markings=stripes)


@sprite("silver_haired_bat")
def _(s):
    s.can("fly")
    up = s.act == "fly" and s.f % 2 == 0
    fur, wing, bone = "#2a2228", "#1e1a20", "#0e0a0e"
    lift = -5 if up else 0
    for side in (-1, 1):
        x = lambda v: 16 + side * v  # noqa: E731
        tip = (x(15), 9 + lift)
        pts = [(x(3), 13), tip, (x(13), 19 + lift * .4), (x(10), 17 + lift * .2), (x(8), 21), (x(5), 19), (x(3), 23)]
        s.poly(pts, wing, edge=True)
        for end in (tip, (x(13), 19 + lift * .4), (x(8), 21)):
            s.path([(x(3), 13.5), end], 0.45, bone, shade=False)
    s.poly([(12, 23), (20, 23), (18, 28), (16, 30), (14, 28)], wing)
    m = s.ellipse(16, 19, 4.2, 6, fur, edge=True)
    s.paint(s.m_px([(14, 16), (17, 15), (15, 19), (18, 18), (14, 22), (17, 22), (16, 25)]), "#c8c4cc", within=m)  # frosted tips
    s.poly([(12.5, 9.5), (12.5, 5.5), (15, 8.5)], fur)
    s.poly([(19.5, 9.5), (19.5, 5.5), (17, 8.5)], fur)
    s.ellipse(16, 11.5, 4, 3.6, fur, edge=True)
    s.px([(15, 13), (17, 13)], "#0e0a0e")
    s.eye(14, 11, color="#0e0a0e", shine="#ffffff")
    s.eye(18, 11, color="#0e0a0e", shine="#ffffff")
    s.blush(13, 13)
    s.blush(19, 13)


# --------------------------------------------------------------------------- birds
@sprite("baltimore_oriole")
def _(s):
    def wing(s, m):
        s.paint(s.m_line(17, 18, 23, 17), WHITE, within=m)
    bird(s, "#f08a1a", "#f8a02a", head="#1e1a1e", wing="#1e1a1e", tail_col="#e07a1a", beak="thin",
         beak_col="#5a5a64", legs="#5a5a64", tail="mid", wing_mark=wing)


@sprite("black_crowned_night_heron")
def _(s):
    wader(s, "#c8ccd4", neck="#e8eaee", head="#e8eaee", cap="#1e2a3a", wing="#7a8494", beak="#1e1e24",
          legs="#e8c040", plume=WHITE)
    s.eye(8, 4, color="#e0302a")


@sprite("red_breasted_merganser")
def _(s):
    duck(s, "#5a5a64", "#b8865a", "#1e3a30", bill="#d8402a", ring=WHITE, speculum=WHITE)
    s.poly([(13, 7), (17, 3), (16, 7), (19, 5), (15, 10)], "#1e3a30")  # shaggy crest


# --------------------------------------------------------------------------- reptiles
@sprite("northern_cottonmouth")
def _(s):
    snake(s, "#4a4436", belly="#a89878", bands="#2a2620", band_period=4.4, band_len=2.0, head="#4a4436",
          head_w=5.8)
    s.paint(s.m_line(5, 11, 10, 10), "#2a2620")  # dark mask through the eye


@sprite("plains_garter_snake")
def _(s):
    snake(s, "#2e3428", belly="#d8d0a0", stripe="#f0a02a", bands="#1e2218", band_period=3, band_len=0.8)


@sprite("eastern_foxsnake")
def _(s):
    snake(s, "#d8b46a", belly="#f0e0a0", bands="#5a3a22", band_period=4.4, band_len=2.2, head="#c8783a")


@sprite("spiny_softshell")
def _(s):
    # A flat, leathery, pancake shell with dark spots and a snorkel nose.
    turtle(s, "#8a8a62", "#9a9a72", speckle="#3a3a2a", rim="#a8a880")
    s.paint(s.m_px([(10, 21), (14, 20), (18, 21), (22, 20), (12, 23), (20, 23), (16, 22)]), "#4a4a34")
    if s.act != "sleep":
        s.px([(0, 18), (1, 18)], "#8a8a62")


# --------------------------------------------------------------------------- amphibians
@sprite("northern_leopard_frog")
def _(s):
    frog(s, "#5aa04a", "#f4f0e0", tympanum="#c8b88a", spots=7, spot_big=True, spot_col="#1a3a1e", ridges="#b8d890")


@sprite("boreal_chorus_frog")
def _(s):
    frog(s, "#8a8a6a", "#f0ecd8", build="tree", mask="#3a3a2a", pads=True, lines="#4a4a34")


# --------------------------------------------------------------------------- fish
@sprite("european_carp")
def _(s):
    def pat(s, m):
        s.paint(s.m_path([(9, 15), (16, 14), (24, 15)], 0.5), "#8a6a2a", within=m)
        s.paint(s.m_px([(12, 12), (16, 11), (20, 12), (14, 17), (18, 17), (22, 18)]), "#d8c070", within=m)
    fish(s, "#b8943a", "#e8d48a", fin="#9a6a3a", pattern=pat)
    s.path([(3, 18), (2, 21)], 0.5, "#8a6a2a", shade=False)  # barbel


@sprite("blackstripe_topminnow")
def _(s):
    def pat(s, m):
        s.paint(s.m_path([(5, 16), (14, 17), (25, 16)], 1.2), "#1e1e24", within=m)
    fish(s, "#c8b890", "#f0e8d0", fin="#b8a878", pattern=pat, slim=True)
    s.px([(9, 11)], "#f0f0f8")  # the shiny spot on its head


# --------------------------------------------------------------------------- insects and other small animals
@sprite("two_spotted_bumble_bee")
def _(s):
    s.can("fly")
    up = not (s.act == "fly" and s.f % 2)
    s.ellipse(20, 8 if up else 11, 4.5, 6.5 if up else 4, "#e6f4fc", rot=25 if up else 70, shade=False, edge=True)
    s.ellipse(25, 11 if up else 13, 3.5, 5 if up else 3, "#d6ecfa", rot=40 if up else 80, shade=False, edge=True)
    m = s.ellipse(18, 19, 8.5, 7, "#2a2228")
    s.paint(s.m_poly([(13, 10), (19, 10), (19, 28), (13, 28)]), "#f2c83a", within=m)  # yellow front
    s.paint(s.m_ellipse(21, 18, 1.4, 1.2) | s.m_ellipse(24, 18, 1.4, 1.2), "#c87a2a", within=m)  # the two spots
    s.line(9, 25, 8, 29, "#2a2228")
    s.line(13, 25, 13, 29, "#2a2228")
    s.ellipse(8.5, 17, 5.5, 5.5, "#2a2228", edge=True)
    s.line(6, 12, 4, 6, "#2a2228")
    s.line(9, 12, 10, 6, "#2a2228")
    s.eye(5, 16, color="#11080f", shine="#ffffff")
    s.blush(5, 19, color="#ff8fa8")


@sprite("black_swallowtail")
def _(s):
    def pat(s, fm, hm):
        s.paint(s.m_px([(3, 8), (5, 10), (7, 12), (9, 14), (11, 15), (13, 16)]), "#f8d84a", mirror=True, within=fm)
        s.paint(s.m_px([(5, 20), (7, 22), (9, 23), (11, 24)]), "#f8d84a", mirror=True, within=hm)
        s.px([(7, 25), (9, 26)], "#4a7ae8", mirror=True)
        s.px([(12, 25)], "#f0802a", mirror=True)
    butterfly(s, "#1e1a20", "#1e1a20", pattern=pat, tails=True)


@sprite("red_admiral")
def _(s):
    def pat(s, fm, hm):
        s.paint(s.m_line(4, 12, 12, 8) | s.m_line(4, 13, 12, 9), "#e0502a", mirror=True, within=fm)
        s.paint(s.m_px([(3, 5), (5, 4), (4, 7)]), WHITE, mirror=True, within=fm)
        s.paint(s.m_line(4, 24, 12, 26), "#e0502a", mirror=True, within=hm)
    butterfly(s, "#1e1a20", "#2a2228", pattern=pat)


@sprite("rathkes_woodlouse")
def _(s):
    g = "#7a6a5a"
    m = _woodlouse(s, g, "#b8a890")
    s.paint(s.m_line(9, 18, 24, 18), "#e8d8b8", within=m)  # its two pale side stripes
    s.paint(s.m_px([(10, 21), (14, 22), (18, 21), (22, 22)]), "#c8b89a", within=m)
    s.ellipse(6.5, 22, 3.5, 3.5, mix(g, "#000000", 0.15), edge=True)
    s.line(4, 19, 0, 16, "#3a3028")
    s.eye(5, 21)
    s.blush(6, 24)
