"""Sprites for the Virginia species that aren't on an earlier state's list."""
from __future__ import annotations

from archetypes import BLACK, WHITE, bird, butterfly, dragonfly, fish, frog, lizard, quad, snake, sprite
from pixel import mix


# --------------------------------------------------------------------------- mammals
@sprite("sika_deer")
def _(s):
    # Small chestnut deer with white spots (the wild herd on Assateague and Chincoteague).
    def antlers(s, b):
        hx, hy = b["head"][:2]
        c = "#d8c49c"
        for dx, col in ((1.5, mix(c, "#1a1420", 0.25)), (0, c)):
            x, y = hx + 1 + dx, hy - 2.5
            s.path([(x, y), (x + 1.5, y - 4), (x + 1, y - 7)], 0.65, col, shade=False)
            s.path([(x + 1.3, y - 3.5), (x - 1, y - 5)], 0.5, col, shade=False)

    def spots(s, b):
        bx, by, brx, bry = b["body"]
        s.paint(s.m_px([(round(bx - 5 + i * 2.2), round(by - bry * .45 + (i % 2) * 2)) for i in range(6)]),
                "#f4e8d0", within=s.m_ellipse(bx, by, brx, bry))
    quad(s, "#8a4e2c", "#e8dcc4", build="deer", ears="side", ear_in="#e0b8a0", tail="cotton",
         tail_col=WHITE, nose="#2b2226", feet="#3a2a22", behind=antlers, markings=spots)


@sprite("eastern_red_bat")
def _(s):
    s.can("fly")
    up = s.act == "fly" and s.f % 2 == 0
    fur, wing, bone = "#d0582a", "#7a3a24", "#4a2014"
    lift = -5 if up else 0
    for side in (-1, 1):
        x = lambda v: 16 + side * v  # noqa: E731
        tip = (x(15), 9 + lift)
        pts = [(x(3), 13), tip, (x(13), 19 + lift * .4), (x(10), 17 + lift * .2), (x(8), 21), (x(5), 19), (x(3), 23)]
        s.poly(pts, wing, edge=True)
        for end in (tip, (x(13), 19 + lift * .4), (x(8), 21)):
            s.path([(x(3), 13.5), end], 0.45, bone, shade=False)
    s.poly([(12, 23), (20, 23), (18, 28), (16, 30), (14, 28)], fur)  # furry tail membrane
    m = s.ellipse(16, 19, 4, 6, fur, edge=True)
    s.paint(s.m_ellipse(16, 15, 3, 1.5), "#f0e0d0", within=m)  # frosted white shoulders
    s.poly([(12.5, 9.5), (12.5, 5.5), (15, 8.5)], fur)  # short round ears
    s.poly([(19.5, 9.5), (19.5, 5.5), (17, 8.5)], fur)
    s.ellipse(16, 11.5, 4, 3.6, fur, edge=True)
    s.px([(15, 13), (17, 13)], "#2b2226")
    s.eye(14, 11)
    s.eye(18, 11)
    s.blush(13, 13)
    s.blush(19, 13)


# --------------------------------------------------------------------------- birds
@sprite("chipping_sparrow")
def _(s):
    def face(s):
        h = s.last
        s.paint(s.m_ellipse(11, 6.5, 5, 2.4), "#c0502a", within=h)  # rusty cap
        s.paint(s.m_line(5, 10, 15, 10), WHITE, within=h)
        s.paint(s.m_line(4, 12, 14, 12), BLACK, within=h)  # black eye line

    def wing(s, m):
        s.paint(s.m_line(16, 18, 23, 16) | s.m_px([(18, 20), (21, 19)]), "#4a3220", within=m)
    bird(s, "#9a7050", "#d8dadc", head="#c4c6c8", wing="#a07454", tail_col="#6a5240", beak="cone",
         beak_col="#2b2630", legs="#d0a080", tail="mid", wing_mark=wing, face=face)


# --------------------------------------------------------------------------- reptiles
@sprite("eastern_copperhead")
def _(s):
    snake(s, "#d8a878", belly="#f0dcc0", bands="#9a5434", band_period=4.2, band_len=2.2, head="#c87c4a",
          head_w=5.6)


@sprite("broad_headed_skink")
def _(s):
    # A big male in spring: orange-red head on an olive-brown body.
    def pat(s, m):
        s.paint(s.m_line(8, 20, 22, 20), mix("#7a5a3a", "#000000", 0.2), within=m)
    lizard(s, "#7a5a3a", "#d8c8a8", head="#e0562a", throat="#f08a4a", pattern=pat, tail_col="#6a4e34")


# --------------------------------------------------------------------------- amphibians
@sprite("fowlers_toad")
def _(s):
    frog(s, "#9a8a6a", "#f0ece0", build="toad", spots=7, dorsal="#e8e0c8", parotoid="#7a6a4a")


@sprite("northern_cricket_frog")
def _(s):
    frog(s, "#7a8a4a", "#efe8d4", spots=2, crown="#3a4a2a", dorsal="#9ab05a")


# --------------------------------------------------------------------------- fish
@sprite("redbreast_sunfish")
def _(s):
    def pat(s, m):
        s.paint(s.m_path([(9, 13), (13, 13)], 0.9), "#1e2430", within=m)  # long black ear flap
        s.paint(s.m_path([(3, 16), (8, 17)], 0.5), "#5ab8d8", within=m)
        s.paint(s.m_px([(15, 12), (18, 14), (21, 12), (17, 11)]), "#c8a060", within=m)
    fish(s, "#6a7a5a", "#e8602a", fin="#5a6a4a", pattern=pat)


# --------------------------------------------------------------------------- insects and other small animals
@sprite("common_whitetail")
def _(s):
    # The male: chalky white tail and a dark band across each wing.
    dragonfly(s, "#5a4a3a", "#e8ecf0")
    wings = s.m_ellipse(8, 10, 7.5, 2.1) | s.m_ellipse(8, 14, 7.5, 2.1)
    wings |= s.m_ellipse(24, 10, 7.5, 2.1) | s.m_ellipse(24, 14, 7.5, 2.1)
    bands = s.m_poly([(5, 6), (10, 6), (10, 18), (5, 18)]) | s.m_poly([(22, 6), (27, 6), (27, 18), (22, 18)])
    s.paint(bands, "#3a3230", within=wings)
    s.path([(16, 15), (16, 26)], (1.9, 1.5), "#f4f6f8")


@sprite("pearl_crescent")
def _(s):
    def pat(s, fm, hm):
        s.paint(s.m_line(3, 6, 13, 13) | s.m_line(3, 10, 12, 15) | s.m_poly([(1.5, 6), (5, 3), (6, 5), (2, 9)]),
                "#2b2226", mirror=True, within=fm)
        s.paint(s.m_line(5, 22, 13, 23), "#2b2226", mirror=True, within=hm)
        s.paint(s.m_px([(6, 24), (8, 25), (10, 25)]), "#2b2226", mirror=True, within=hm)
    butterfly(s, "#e8862a", "#e8862a", body="#3a2a22", pattern=pat)


@sprite("eastern_tailed_blue")
def _(s):
    def pat(s, fm, hm):
        s.paint(s.m_poly([(1.5, 6), (5, 3), (5, 5), (2.5, 14)]), "#2b2a4a", mirror=True, within=fm)
        s.paint(s.m_px([(9, 25), (10, 24)]), "#f08a2a", mirror=True, within=hm)
    butterfly(s, "#5a6ad8", "#5a6ad8", body="#2b2630", pattern=pat, tails=True)


@sprite("huron_skipper")
def _(s):
    def pat(s, fm, hm):
        s.paint(s.m_poly([(1.5, 6), (5, 3), (5, 5), (2.5, 14)]) | s.m_ellipse(10, 10, 1.4, 1.2), "#6a4a24",
                mirror=True, within=fm)
        s.paint(s.m_poly([(4, 21), (6, 25), (9, 27), (6, 21)]), "#6a4a24", mirror=True, within=hm)
    butterfly(s, "#d8a04a", "#c8903a", body="#7a5a34", pattern=pat)


def _woodlouse(s, g, light, roll=False):
    s.can("walk")
    w = s.wave() if s.act == "walk" else 0
    for i, x in enumerate((9, 13, 17, 21)):
        d = round(w * (1 if i % 2 else -1))
        s.line(x, 26 if roll else 25, x - 1 + d, 29 if roll else 28, mix(g, "#000000", 0.5))
    m = s.ellipse(16, 21, 11, 7 if roll else 5.5, g, edge=True)
    for x in (10, 13, 16, 19, 22, 25):
        s.paint(s.m_line(x, 13, x, 29), mix(g, "#000000", 0.3), within=m)
    return m


@sprite("common_rough_woodlouse")
def _(s):
    g = "#6a6a70"
    m = _woodlouse(s, g, "#a0a0a8")
    # Bumpy all over.
    s.paint(s.m_px([(9, 18), (12, 17), (15, 17), (18, 17), (21, 17), (24, 18), (11, 20), (17, 19), (23, 20)]),
            "#9a9aa2", within=m)
    s.line(27, 22, 30, 24, mix(g, "#000000", 0.2))
    s.line(27, 20, 30, 18, mix(g, "#000000", 0.2))
    s.ellipse(6.5, 22, 3.5, 3.5, mix(g, "#000000", 0.15), edge=True)
    s.line(4, 19, 0, 16, "#3a3a44")
    s.eye(5, 21)
    s.blush(6, 24)


@sprite("nosy_pill_woodlouse")
def _(s):
    g = "#8a8a7a"
    m = _woodlouse(s, g, "#c8c8b4", roll=True)
    s.paint(s.m_px([(10, 18), (13, 19), (17, 17), (20, 19), (24, 18), (15, 22), (21, 23)]), "#d8d4b8", within=m)
    s.ellipse(6, 22, 3.6, 4, mix(g, "#000000", 0.2), edge=True)
    s.ellipse(3.2, 21.5, 1.4, 1.2, mix(g, "#000000", 0.1))  # the "nose" ridge on its head
    s.line(4, 19, 1, 15, "#3a3a34")
    s.eye(5, 21)
    s.blush(6, 24)
