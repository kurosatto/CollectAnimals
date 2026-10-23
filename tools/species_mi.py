"""Sprites for the Michigan species that aren't on an earlier state's list."""
from __future__ import annotations

from archetypes import (BLACK, WHITE, _far_wing, _ripples, _wing_beat, beetle_top, bird, duck, fish, lizard,
                        quad, spider_top, sprite, turtle)
from pixel import mix
from species_oh import _damsel
from species_tx import _segmented


# --------------------------------------------------------------------------- mammals
@sprite("moose")
def _(s):
    # Tall and dark with a shoulder hump, a long droopy nose, a dewlap and wide flat antlers.
    def antlers(s, b):
        hx, hy = b["head"][:2]
        c = "#d8c49a"
        for dx, col in ((2, mix(c, "#1a1420", 0.25)), (0, c)):
            x, y = hx + 2 + dx, hy - 3
            s.path([(x, y), (x + 2, y - 2)], 0.7, col, shade=False)
            s.ellipse(x + 4.5, y - 3.5, 3.6, 1.8, col, rot=-25, shade=False)
            s.px([(round(x + 2), round(y - 6)), (round(x + 4), round(y - 7)), (round(x + 6), round(y - 7)),
                  (round(x + 8), round(y - 6))], col)

    def hump(s, b):
        bx, by, brx, bry = b["body"]
        s.ellipse(bx - brx * .45, by - bry * .8, 3.5, 2.2, "#3e2a1e")
        hx, hy = b["head"][:2]
        s.path([(hx, hy + 3), (hx - .5, hy + 6)], 0.9, "#3e2a1e", shade=False)  # the dewlap
    quad(s, "#4a3224", "#6a5240", build="deer", ears="side", ear_in="#8a6a54", tail="cotton", tail_col="#4a3224",
         head="#4a3224", muzzle="#5e4434", legs="#8a7a6a", nose="#1e1612", belly=False, behind=antlers,
         markings=hump)


# --------------------------------------------------------------------------- birds
@sprite("trumpeter_swan")
def _(s):
    s.can("swim", "fly")
    flying = s.act == "fly"
    w = s.wave()
    if flying:
        _far_wing(s, 23, 20, w, "#c8ccd4")
    else:
        _ripples(s, s.f if s.act == "swim" else 0, ((2, 30), (6, 29), (25, 30), (29, 29)))
    s.poly([(25, 20), (31, 17), (30, 23)], "#e8eaee")
    s.ellipse(19, 23, 10.5, 6.5, WHITE)
    if flying:
        _wing_beat(s, 22, 21, w, "#e8eaee")
    else:
        s.ellipse(22, 21, 7, 3.5, "#e8eaee", rot=-8, edge=True)
    s.path([(12, 20), (9, 14), (10, 8)], 2.3, WHITE)
    s.ellipse(9.5, 7, 4.6, 3.8, WHITE, edge=True)
    s.poly([(7, 5.5), (1, 8), (1.5, 9.5), (7, 9)], "#1e1a1e")  # the long black bill
    s.eye(8, 6, shine="#ffffff", color="#000000")


@sprite("rose_breasted_grosbeak")
def _(s):
    def bib(s, m):
        s.paint(s.m_poly([(8, 16), (14, 16), (11, 22)]), "#e0304a", within=m)

    def wing(s, m):
        s.paint(s.m_ellipse(19, 19, 1.8, 1.2) | s.m_line(17, 17, 22, 17), WHITE, within=m)
    bird(s, "#1e1a1e", WHITE, head="#1e1a1e", wing="#1a161a", tail_col="#1a161a", beak="cone", beak_col="#f0e8d8",
         legs="#8a8090", tail="mid", belly_mark=bib, wing_mark=wing)


@sprite("cedar_waxwing")
def _(s):
    # Silky tan with a crest, a black bandit mask, a yellow tail tip and red wax on the wing.
    def face(s):
        s.paint(s.m_line(4, 10, 13, 9) | s.m_line(4, 11, 12, 10), "#1e1a1e", within=s.last)

    def wing(s, m):
        s.paint(s.m_px([(22, 17), (23, 18)]), "#e0302a", within=m)
    bird(s, "#b8946a", "#e8d898", head="#b8946a", wing="#8a8478", tail_col="#7a7470", beak="cone",
         beak_col="#1e1a1e", legs="#3a3434", tail="mid", crest="jay", face=face, wing_mark=wing)
    s.px([(29, 13), (30, 14), (30, 15)], "#f0d02a")


@sprite("common_merganser")
def _(s):
    duck(s, WHITE, WHITE, "#1e4a3a", bill="#d8302a", ring=None, speculum="#e8eaee", tail_col="#8a8e94")
    s.paint(s.m_poly([(20, 18), (28, 18), (28, 21), (20, 21)]), "#2a2a30")  # black back


# --------------------------------------------------------------------------- reptiles and amphibians
@sprite("blandings_turtle")
def _(s):
    # A high dark shell freckled with yellow, and a bright yellow chin and throat.
    turtle(s, "#2a3030", "#3a4038", dome=True, scutes="#343a3a", speckle="#e8d040", rim="#1e2222")
    s.paint(s.m_px([(10, 18), (14, 16), (19, 17), (23, 19), (12, 22), (17, 21), (21, 23), (8, 22)]), "#e8d040")
    s.paint(s.m_ellipse(5, 21, 3, 1.4), "#f0d84a")


@sprite("blue_spotted_salamander")
def _(s):
    def pat(s, m):
        s.paint(s.m_px([(9, 19), (12, 21), (15, 19), (18, 21), (21, 19), (13, 23), (19, 23)]), "#7aa8e0", within=m)
    lizard(s, "#26283a", "#3a3e54", smooth=True, eye_big=True, legs="#2e3044", pattern=pat)
    s.px([(25, 22), (28, 21), (29, 18), (8, 15), (10, 17)], "#7aa8e0")


# --------------------------------------------------------------------------- fish
@sprite("yellow_perch")
def _(s):
    def pat(s, m):
        for x in (10, 14, 18, 22):
            s.paint(s.m_line(x, 9, x - 1, 19) | s.m_line(x + 1, 9, x, 19), "#3a4a2a", within=m)
    fish(s, "#d8c03a", "#f4ecb8", fin="#e8702a", pattern=pat, slim=True)


@sprite("rock_bass")
def _(s):
    def pat(s, m):
        s.paint(s.m_px([(x, y) for x in (11, 14, 17, 20, 23) for y in (13, 16, 19)]), "#3a2e22", within=m)
    fish(s, "#8a7a54", "#d8c8a0", fin="#6a5e44", pattern=pat)
    s.px([(6, 14)], "#d8302a")


@sprite("pumpkinseed")
def _(s):
    def pat(s, m):
        s.paint(s.m_path([(3, 15), (8, 13)], 0.5) | s.m_path([(3, 18), (8, 17)], 0.5), "#3ab8d8", within=m)
        s.paint(s.m_ellipse(10, 14, 1.4, 1.2), "#1e1e24", within=m)
        s.px([(11, 14)], "#e8302a")
        s.paint(s.m_px([(14, 11), (17, 13), (20, 11), (16, 16), (19, 18), (22, 15)]), "#e8902a", within=m)
    fish(s, "#6a9a6a", "#f0a030", fin="#5a8a5a", pattern=pat)


@sprite("round_goby")
def _(s):
    # A mottled little bottom fish with a black spot on its back fin.
    def pat(s, m):
        s.paint(s.m_px([(10, 14), (13, 17), (16, 13), (19, 16), (22, 14), (12, 20), (18, 20)]), "#4a4234", within=m)
    fish(s, "#8a8268", "#c8c0a4", fin="#6a6450", pattern=pat, slim=True)
    s.ellipse(14, 9.5, 1.6, 1.2, "#1e1e22")


# --------------------------------------------------------------------------- insects and spiders
@sprite("japanese_beetle")
def _(s):
    beetle_top(s, "#b86a2a", head="#2a8a5a", pron="#2a8a5a")
    s.px([(9, 26), (23, 26), (10, 28), (22, 28)], WHITE)  # white tufts along its sides


@sprite("milkweed_tussock_moth")
def _(s):
    # The caterpillar: fuzzy tufts of black, orange and white.
    pts = _segmented(s, 8, "#e8902a", "#1e1a1c", "#3a2a22", leg_len=1.2, spacing=2.8, r=2.8, antenna=0)
    for i, (x, y) in enumerate(pts):
        col = ("#1e1a1c", "#f0f0f0", "#e8902a", "#1e1a1c")[i % 4]
        s.ellipse(x, y - 1, 2.6, 2.6, col)
        s.px([(round(x), round(y - 4)), (round(x + 1), round(y - 4))], col)
    hx, hy = pts[0]
    s.ellipse(hx - 1, hy, 3.4, 3, "#1e1a1c", edge=True)
    s.eye(round(hx - 2), round(hy - 1))


@sprite("bold_jumping_spider")
def _(s):
    def pat(s, m):
        s.paint(s.m_ellipse(16, 21, 1.6, 1.6) | s.m_ellipse(13, 24, 1.2, 1.2) | s.m_ellipse(19, 24, 1.2, 1.2),
                WHITE, within=m)
    spider_top(s, "#1e1a1e", "#2a2428", pattern=pat, ceph="#2a2428", leg_bands="#e8e8e8")
    s.px([(15, 12), (17, 12)], "#3ad8a0")  # iridescent green fangs


@sprite("ebony_jewelwing")
def _(s):
    _damsel(s, "#1a8a6a", "#1a7a5a", wing="#2a2428")
