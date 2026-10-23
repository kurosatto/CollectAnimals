"""Sprites for the New Jersey species that aren't on an earlier state's list."""
from __future__ import annotations

from archetypes import WHITE, bird, crab, sprite, turtle


# --------------------------------------------------------------------------- birds
@sprite("great_black_backed_gull")
def _(s):
    # The biggest gull: a black back and wings, white head and a heavy yellow bill.
    def wing(s, m):
        s.paint(s.m_px([(24, 17), (25, 17), (25, 18)]), WHITE, within=m)
    bird(s, WHITE, WHITE, head=WHITE, wing="#26242a", tail_col=WHITE, beak="crow", beak_col="#f0c830",
         legs="#f0c0c0", tail="short", wing_mark=wing, big=True)
    s.px([(3, 13)], "#e0403a")


# --------------------------------------------------------------------------- reptiles
@sprite("northern_red_bellied_cooter")
def _(s):
    turtle(s, "#4a4434", "#3a3a2e", dome=True, scutes="#8a4a2a", speckle="#e8d070", rim="#c8502a")


@sprite("spotted_turtle")
def _(s):
    # A small black shell sprinkled with round yellow spots.
    turtle(s, "#1e1e24", "#2a2a30", scutes="#26262c", speckle="#f0d040", rim="#141418")
    s.paint(s.m_px([(9, 21), (12, 19), (15, 21), (18, 19), (21, 21), (24, 22), (11, 23), (17, 23), (22, 19)]),
            "#f0d040")


# --------------------------------------------------------------------------- crabs
@sprite("atlantic_sand_crab")
def _(s):
    # The mole crab: a smooth egg-shaped shell for digging into the wet sand.
    def pat(s, m):
        s.paint(s.m_line(10, 17, 22, 17) | s.m_line(10, 20, 22, 20), "#b8a88a", within=m)
    crab(s, "#d8ccb0", "#d8ccb0", legs="#c8b898", stalks=1, pattern=pat)


@sprite("ocellate_lady_crab")
def _(s):
    # The calico crab: pale shell covered in purple-ringed spots, paddle back legs.
    def pat(s, m):
        for x, y in ((11, 17), (16, 16), (21, 17), (13, 21), (19, 21), (16, 23)):
            s.paint(s.m_ellipse(x, y, 1.6, 1.4), "#8a4a9a", within=m)
            s.paint(s.m_px([(x, y)]), "#e8dcc8", within=m)
    crab(s, "#e8dcc8", "#d8b0d0", legs="#c8a8c0", stalks=2, pattern=pat)


@sprite("mud_fiddler_crab")
def _(s):
    def pat(s, m):
        s.paint(s.m_ellipse(16, 18, 5, 3), "#4a6a8a", within=m)
    crab(s, "#4a4a44", "#e8d8b8", legs="#3e3e38", stalks=3, big_claw=True, pattern=pat)
