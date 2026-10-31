"""Sprites for the Pennsylvania species that aren't on an earlier state's list."""
from __future__ import annotations

from archetypes import BLACK, WHITE, bird, fish, frog, lizard, snake, sprite, turtle
from pixel import mix


# --------------------------------------------------------------------------- mammals
@sprite("big_brown_bat")
def _(s):
    s.can("fly")
    up = s.act == "fly" and s.f % 2 == 0
    fur, wing, bone = "#8a5e3a", "#3a2a24", "#22180f"
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
    s.paint(s.m_ellipse(16, 21, 2.6, 3.4), mix(fur, "#ffffff", 0.25), within=m)
    s.poly([(12.5, 9.5), (12, 5), (15, 8.5)], wing)  # dark, rounded ears
    s.poly([(19.5, 9.5), (20, 5), (17, 8.5)], wing)
    s.ellipse(16, 11.5, 4, 3.6, fur, edge=True)
    s.ellipse(16, 13.3, 2, 1.3, wing)  # its dark face
    s.px([(15, 13), (17, 13)], "#1a1210")
    s.eye(14, 11)
    s.eye(18, 11)
    s.blush(13, 13)
    s.blush(19, 13)


# --------------------------------------------------------------------------- birds
@sprite("tree_swallow")
def _(s):
    # Glossy blue-green back, snowy white front, short notched tail.
    def sheen(s, m):
        s.paint(s.m_ellipse(18, 17, 3, 1.6), "#3a8ab0", within=m)

    def face(s):
        s.paint(s.m_ellipse(9, 14.5, 5, 2.4), WHITE, within=s.last)
    bird(s, "#2a6a8a", WHITE, head="#2a6a8a", wing="#1e3a5a", tail_col="#1e3a5a", beak="thin",
         beak_col="#1a1a22", legs="#5a4a44", tail="mid", wing_mark=sheen, face=face)


@sprite("brown_headed_cowbird")
def _(s):
    # The male: glossy black with a chocolate-brown head.
    def sheen(s, m):
        s.paint(s.m_ellipse(18, 18, 3, 1.5), "#2a3a4a", within=m)
    bird(s, "#1c1a22", "#24222a", head="#6a4630", wing="#18161e", tail_col="#18161e", beak="cone",
         beak_col="#22202a", legs="#2a2630", tail="mid", wing_mark=sheen)


# --------------------------------------------------------------------------- reptiles
@sprite("timber_rattlesnake")
def _(s):
    # Yellow phase: dark chevron bands and a black tail ending in the rattle.
    snake(s, "#c8a65a", belly="#eadcae", bands="#3a2e22", band_period=4.6, band_len=1.8, head="#c09a50",
          head_w=5.8, rattle=True)
    s.paint(s.m_ellipse(25, 28.5, 2.4, 1.6), "#1e1a16")


@sprite("wood_turtle")
def _(s):
    # Sculpted brown shell and bright orange neck and legs.
    turtle(s, "#6a5238", "#d8682a", scutes="#7e6446", rim="#4a3826")
    s.paint(s.m_px([(10, 22), (16, 20), (22, 22)]), "#4a3826")


# --------------------------------------------------------------------------- amphibians
@sprite("northern_two_lined_salamander")
def _(s):
    def pat(s, m):
        s.paint(s.m_line(9, 19, 22, 19), "#3a2a1a", within=m)
        s.paint(s.m_px([(11, 21), (14, 22), (17, 21), (20, 22)]), "#5a3e1e", within=m)
    lizard(s, "#e0b040", "#f4e090", smooth=True, eye_big=True, legs="#d0a038", pattern=pat,
           tail_col="#d8a83a")
    s.paint(s.m_path([(20, 21), (26, 23.5), (30, 20)], 0.5), "#3a2a1a")  # the dark line runs down the tail


@sprite("pickerel_frog")
def _(s):
    # Square brown spots in two neat rows on a tan back.
    frog(s, "#b8a070", "#f4ecd8", tympanum="#a08a5a", spots=7, spot_big=True, spot_col="#5a3818", ridges="#d8c890")


# --------------------------------------------------------------------------- fish
@sprite("smallmouth_bass")
def _(s):
    # Bronze with dark vertical bars and a red eye.
    def pat(s, m):
        for x in (11, 15, 19, 23):
            s.paint(s.m_line(x, 11, x - 1, 19), "#5a4a2a", within=m)
        s.paint(s.m_path([(4, 15), (8, 14)], 0.5), "#5a4a2a", within=m)
    fish(s, "#9a7a40", "#ece0b8", fin="#7a6034", pattern=pat, slim=True)
    s.px([(6, 14)], "#c8302a")
    s.px([(6, 13)], BLACK)
