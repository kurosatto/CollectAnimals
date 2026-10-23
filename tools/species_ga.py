"""Sprites for the Georgia species that aren't on an earlier state's list."""
from __future__ import annotations

from archetypes import BLACK, WHITE, bird, butterfly, crab, lizard, sprite


# --------------------------------------------------------------------------- birds
@sprite("brown_thrasher")
def _(s):
    # Foxy red-brown back, a streaky cream front, yellow eyes and a long tail.
    def streaks(s, m):
        s.paint(s.m_px([(10, 21), (13, 22), (11, 24), (14, 25), (9, 23), (12, 20)]), "#6a3a1e", within=m)

    def wing(s, m):
        s.paint(s.m_line(17, 17, 23, 16) | s.m_line(17, 19, 22, 18), WHITE, within=m)
    bird(s, "#a8522a", "#f2e2c0", wing="#984a26", tail_col="#a8522a", beak="long", beak_col="#3a2a24",
         legs="#c8906a", tail="long", eye_col="#e8b020", belly_mark=streaks, wing_mark=wing)


@sprite("eastern_towhee")
def _(s):
    # Black hood and back, rusty sides, white belly and red eyes.
    def sides(s, m):
        s.paint(s.m_ellipse(17, 23, 4, 2.5), "#c8642a", within=m)
    bird(s, "#1e1a1e", WHITE, head="#1e1a1e", wing="#1a161a", tail_col="#1a161a", beak="cone",
         beak_col="#2a2630", legs="#c8a088", tail="long", eye_col="#c8302a", belly_mark=sides)


@sprite("pine_warbler")
def _(s):
    def wing(s, m):
        s.paint(s.m_line(17, 18, 23, 17) | s.m_line(18, 20, 22, 19), "#e8ecd8", within=m)
    bird(s, "#8a9a4a", "#f0dc4a", head="#a0ac4a", wing="#6a7258", tail_col="#6a7258", beak="thin",
         beak_col="#3a3a3a", legs="#5a5a54", tail="mid", wing_mark=wing)


@sprite("ruby_crowned_kinglet")
def _(s):
    # A tiny olive bird with a white eye-ring; the male flashes a red crown patch.
    def face(s):
        h = s.last
        s.paint(s.m_ellipse(11, 5.5, 2.2, 1.2), "#e0302a", within=h)
        s.paint(s.m_ellipse(8, 10, 2, 2) & ~s.m_ellipse(8, 10, 1.2, 1.2), WHITE, within=h)

    def wing(s, m):
        s.paint(s.m_line(17, 18, 22, 17), WHITE, within=m)
    bird(s, "#7a8a58", "#d8dcb8", head="#7a8a58", wing="#4e5a3a", tail_col="#4e5a3a", beak="thin",
         beak_col="#2a2a2a", legs="#4a4440", tail="short", face=face, wing_mark=wing)


# --------------------------------------------------------------------------- amphibians
@sprite("northern_slimy_salamander")
def _(s):
    # Glossy black, sprinkled with silvery-white flecks.
    def pat(s, m):
        s.paint(s.m_px([(9, 20), (12, 19), (15, 21), (18, 19), (21, 20), (11, 23), (17, 23)]), "#d8dce4", within=m)
    lizard(s, "#1e1e26", "#2e2e38", smooth=True, eye_big=True, legs="#26262e", pattern=pat)
    s.px([(25, 22), (28, 21), (29, 18), (7, 15), (10, 16)], "#d8dce4")


# --------------------------------------------------------------------------- crabs and insects
@sprite("squareback_marsh_crab")
def _(s):
    def pat(s, m):
        s.paint(s.m_line(10, 18, 22, 18), "#2a3a2a", within=m)
    crab(s, "#4a5a3a", "#b0603a", legs="#3e4a32", stalks=3, pattern=pat)


@sprite("fiery_skipper")
def _(s):
    def pat(s, fm, hm):
        s.paint(s.m_poly([(1.5, 6), (5, 3), (5, 5), (2.5, 14)]) | s.m_px([(9, 9), (11, 11), (7, 12)]), "#4a2a14",
                mirror=True, within=fm)
        s.paint(s.m_px([(6, 22), (8, 24), (10, 23), (5, 25)]), "#4a2a14", mirror=True, within=hm)
    butterfly(s, "#f0902a", "#e8822a", body="#7a4a24", pattern=pat)
    s.px([(16, 3)], BLACK)
