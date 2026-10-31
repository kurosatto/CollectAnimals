"""Sprites for the Mountain West species (Colorado, Wyoming, Montana, Idaho, North Dakota)
that aren't on an earlier state's list."""
from __future__ import annotations

import numpy as np

from archetypes import (BLACK, EYE, WHITE, _bird_legs, _far_wing, _ripples, _wing_beat, back_stripes, beetle_top,
                        bird, butterfly, critter, duck, fish, flecks, frog, grasshopper, hummingbird, lizard,
                        mantis, quad, snake, spider_top, sprite)
from pixel import mix
from species_tx import _segmented


# --------------------------------------------------------------------------- mammals
@sprite("gray_wolf")
def _(s):
    # Big and grizzled gray, with a pale face and a dark saddle.
    def m(s, b):
        s.paint(s.m_ellipse(20, 16.5, 7, 2.2), "#5a5a62", within=s.m_ellipse(*b["body"]))
        hx, hy, hrx, hry = b["head"]
        s.paint(s.m_ellipse(hx - 1, hy - 2.2, 2.5, 1), "#5a5a62", within=s.m_ellipse(hx, hy, hrx, hry))
    quad(s, "#8e8e96", "#f2efe8", build="dog", ears="point", ear_in="#d8c8b8", tail="bushy",
         tail_col="#7a7a84", tail_tip=BLACK, nose="#1d1418", eye_col="#8a6a1a", markings=m)


def _ground_squirrel(s, fur, light, *, head=None, tail="long", tail_col=None, tail_tip=None, ear_in="#c8a080",
                     face=None, markings=None):
    critter(s, fur, light, build="ground", ear_in=ear_in, tail="bushy" if tail == "squirrel" else tail,
            tail_col=tail_col or fur, tail_tip=tail_tip, head=head, face=face, markings=markings)


@sprite("common_golden_mantled_ground_squirrel")
def _(s):
    # Like a big chipmunk, but with a coppery head and NO stripes on its face.
    critter(s, "#8a7a68", "#f0e2c8", build="ground", ear_in="#d8a070", tail="long", tail_col="#8a6a50",
            tail_tip="#c8a070", head="#d8883a", eye_ring="#f4e8d0",
            markings=lambda s, g: back_stripes(s, g, [BLACK, "#f4ecd8", BLACK], top=1.0))


@sprite("fremonts_squirrel")
def _(s):
    # The Rocky Mountain chickaree: gray-brown with a rusty back, white eye ring and a black side line.
    critter(s, "#7a6e64", "#f2ece2", build="squirrel", ear_in="#c8a080", tail="squirrel", tail_col="#6e5a48",
            tail_tip="#c8b8a0", eye_ring="#f4f0e8",
            markings=lambda s, g: (back_stripes(s, g, ["#9a5e3a"], top=0.1, width=1.4),
                                   back_stripes(s, g, [BLACK], top=g["bry"] * 1.1)))


@sprite("wyoming_ground_squirrel")
def _(s):
    # Plain buffy gray with a pinkish-cinnamon belly and a thin tail.
    _ground_squirrel(s, "#a89880", "#e8d0b8", tail="long", tail_col="#9a8670", tail_tip="#d8c8b0",
                     markings=lambda s, g: flecks(s, g["body"], "#c8b8a0", every=7))


@sprite("white_tailed_prairie_dog")
def _(s):
    # Tan, with a dark brow over each eye and a white-tipped tail.
    def brow(s, g):
        s.paint(s.m_ellipse(g["hx"] - (0 if g["view"] == "front" else 1), g["hy"] - g["hry"] * 0.55, 2.4, 1.1),
                "#6a4a30", within=g["head_m"])
    critter(s, "#c8a676", "#f0e2c8", build="marmot", ear_in="#a87a50", tail="short", tail_col="#c8a676",
            tail_tip=WHITE, nose="#5a3a2a", feet="#8a6a4a", face=brow)


@sprite("columbian_ground_squirrel")
def _(s):
    # Gray, flecked back with a bright rusty-orange face and legs.
    _ground_squirrel(s, "#8a8278", "#d88a4a", head="#d8783a", tail="squirrel", tail_col="#a06a3a",
                     tail_tip="#c8b8a0", markings=lambda s, g: flecks(s, g["body"], "#c8c0b4", every=6))


@sprite("uinta_ground_squirrel")
def _(s):
    # Gray with a cinnamon-buff nose and face and a buff-edged tail.
    def face(s, g):
        s.paint(s.m_ellipse(g["hx"] + (0.6 if g["view"] == "front" else -1.5 if g["view"] == "side" else 1.5),
                            g["hy"] + 1, 3, 2), "#c8945a", within=g["head_m"])
    _ground_squirrel(s, "#8e8a84", "#e8dcc8", tail="squirrel", tail_col="#7a7268", tail_tip="#d8b888", face=face,
                     markings=lambda s, g: flecks(s, g["body"], "#b8a890", every=7))


@sprite("richardsons_ground_squirrel")
def _(s):
    # The "flickertail": sandy tan, sitting bolt upright.
    _ground_squirrel(s, "#b89a72", "#efe2c8", tail="long", tail_col="#a8805a", tail_tip="#e8d8b8")


@sprite("mountain_cottontail")
def _(s):
    # Grayer than other cottontails, with shorter, dark-tipped ears.
    def nape(s, g):
        s.paint(s.m_ellipse(g["hx"] + 3, g["hy"] + 1, 2, 1.6), "#b88a5a", within=g["body"])
    critter(s, "#9a8e7e", "#f2ece2", build="rabbit", ears="long", ear_in="#e8b4ac", ear_tip="#4a4038", tail="cotton",
            tail_col=WHITE, nose="#e08a96", markings=nape)


@sprite("white_tailed_jackrabbit")
def _(s):
    # Huge black-tipped ears, pale grayish-buff coat and an all-white tail.
    critter(s, "#b8ae9c", "#f4f0e8", build="hare", ears="xlong", ear_in="#ecbcb4", ear_tip=BLACK, tail="cotton",
            tail_col=WHITE, nose="#d88a8a")


# --------------------------------------------------------------------------- birds
@sprite("spotted_towhee")
def _(s):
    # Black hood and back, rufous sides, white belly, white spots on the wings and a red eye.
    def sides(s, m):
        s.paint(s.m_ellipse(16, 22, 3, 3), "#c8602a", within=m)
        s.paint(s.m_ellipse(9, 16, 5, 1.6), BLACK, within=m)

    def spots(s, m):
        s.paint(s.m_px([(17, 17), (19, 18), (21, 17), (18, 20), (22, 19), (24, 18)]), WHITE, within=m)
    bird(s, "#1e1a22", WHITE, head="#1e1a22", wing="#26222a", tail_col="#1e1a22", beak="cone",
         beak_col="#2b2630", legs="#c8a080", tail="long", eye_col="#c8302a", belly_mark=sides, wing_mark=spots)
    s.paint(s.m_ellipse(17, 24, 3, 2.5), "#d0682e")


@sprite("broad_tailed_hummingbird")
def _(s):
    # Green above with a glowing rose-magenta throat.
    hummingbird(s, head="#5a9a5e", crown="#4a8a50", throat="#e02a6a")


@sprite("american_white_pelican")
def _(s):
    # Huge and snowy white, black flight feathers and a big orange bill.
    s.can("walk", "fly")
    flying = s.act == "fly"
    w = s.wave()
    if flying:
        _far_wing(s, 22, 19, w, "#2b2630", 1.1)
    s.poly([(25, 17), (31, 15), (30, 21)], "#ece8e0")
    if not flying:
        _bird_legs(s, (15, 19), 24, 28, "#f09a3a", w if s.act == "walk" else 0, toes=(-2, -1, 0), toe_dy=1)
    s.ellipse(18.5, 20, 9.5, 6, "#f6f4ee")
    if flying:
        m = _wing_beat(s, 21, 18, w, "#f0ede6", 1.1)
    else:
        m = s.ellipse(20.5, 18, 7.5, 3.8, "#f0ede6", rot=-10, edge=True)
    s.paint(s.m_poly([(24, 14), (30, 14), (30, 22), (24, 22)]), "#2b2630", within=m)
    s.path([(12, 20), (10, 15), (12, 10)], 2.4, "#f6f4ee")
    s.ellipse(12.5, 7.5, 4.4, 3.8, "#f6f4ee", edge=True)
    s.poly([(10, 6.5), (-1, 9), (0, 10.5), (10, 9)], "#f08a2a")
    s.poly([(10, 9), (0, 10.5), (3, 13.5), (10, 12.5)], "#f0a040")
    s.px([(13, 4), (14, 3)], "#f0d080")  # breeding knob on the bill top
    s.eye(11, 6)
    s.blush(11, 9)


@sprite("mountain_bluebird")
def _(s):
    # Sky blue all over, paler underneath.
    bird(s, "#5aa8e8", "#b8dcf4", head="#5aa8e8", wing="#4a90d8", tail_col="#3a7ac8", beak="thin",
         beak_col="#2b2630", legs="#3a3438", tail="mid")
    s.paint(s.m_ellipse(13, 26, 3.5, 1.6), "#e8f2f8")


@sprite("western_meadowlark")
def _(s):
    # Bright yellow breast with a black V, streaky brown back.
    def v(s, m):
        s.paint(s.m_poly([(8, 16), (11, 16), (13, 19), (15, 16), (18, 16), (14, 21), (12, 21)]), BLACK, within=m)

    def streaks(s, m):
        s.paint(s.m_px([(17, 17), (19, 18), (21, 17), (23, 18), (18, 20), (21, 20)]), "#3a2a1e", within=m)

    def face(s):
        h = s.last
        s.paint(s.m_ellipse(11, 6, 5, 1.2), "#3a2a1e", within=h)
        s.paint(s.m_ellipse(10, 8.5, 4, 0.9), "#f2d22a", within=h)
        s.paint(s.m_ellipse(7, 14.5, 3, 1.6), "#f2d22a", within=h)
    bird(s, "#9a7a52", "#f2d22a", head="#b09068", wing="#8a6a46", tail_col="#7a5e40", beak="thin",
         beak_col="#a89070", legs="#d8b890", tail="short", belly_mark=v, wing_mark=streaks, face=face)


@sprite("woodhouses_scrub_jay")
def _(s):
    # Crestless blue jay with a gray-brown back and a dusky gray belly.
    def face(s):
        s.paint(s.m_ellipse(9.5, 12, 3.5, 2), "#3a4258", within=s.last)
        s.paint(s.m_px([(10, 8), (11, 8), (12, 8)]), "#e0e4ec", within=s.last)
    bird(s, "#3a6ab8", "#c8c8cc", head="#3a6ab8", wing="#3a6ab8", tail_col="#2e5aa8", beak="crow",
         beak_col=BLACK, legs="#3a3438", tail="long", face=face)
    s.paint(s.m_ellipse(20, 22, 4, 2, rot=-15), "#8a8a90")


@sprite("swainsons_hawk")
def _(s):
    # A dark brown bib across a pale belly and a white throat.
    def bib(s, m):
        s.paint(s.m_poly([(7, 14), (20, 14), (20, 20), (7, 20)]), "#7a4e30", within=m)
    bird(s, "#5a4232", "#f2e8d8", head="#5a4232", wing="#4e3a2c", tail_col="#7a6a5a", beak="hook",
         beak_col="#e0c070", legs="#e8c04a", tail="fan", belly_mark=bib, big=True,
         face=lambda s: s.paint(s.m_ellipse(9, 14.5, 3.5, 1.8), "#f4ece0", within=s.last))
    s.paint(s.m_line(26, 13, 29, 16), "#3a2a20")


@sprite("mountain_chickadee")
def _(s):
    # A chickadee with a white eyebrow cutting through its black cap.
    def face(s):
        h = s.last
        s.paint(s.m_ellipse(11, 7, 6.5, 3.2), BLACK, within=h)
        s.paint(s.m_line(5, 8, 15, 8), WHITE, within=h)
        s.paint(s.m_line(5, 10, 9, 10), BLACK, within=h)
        s.paint(s.m_ellipse(6, 15, 3, 2), BLACK, within=h)
    bird(s, "#8a8e96", "#e8e4dc", head=WHITE, wing="#70747c", tail_col="#5a5e66", beak="thin",
         beak_col="#1a1820", legs="#3a3a44", tail="mid", face=face)


@sprite("western_kingbird")
def _(s):
    # Pale gray head, lemon-yellow belly and a black tail with white edges.
    def face(s):
        s.paint(s.m_line(5, 11, 11, 11), "#5a5a64", within=s.last)
        s.paint(s.m_ellipse(8, 15, 3, 1.6), "#e8e8e8", within=s.last)
    bird(s, "#9a9c94", "#f2d83a", head="#b8bab8", wing="#6a6a60", tail_col="#26242a", beak="thin",
         beak_col="#2b2630", legs="#2b2630", tail="mid", face=face)
    s.paint(s.m_line(21, 23, 30, 17), WHITE)
    s.paint(s.m_ellipse(10, 18, 3, 1.6), "#d8d8d4")


@sprite("western_tanager")
def _(s):
    # Lemon yellow with a flame-red head and black wings with wing bars.
    def wing(s, m):
        s.paint(s.m_line(16, 17, 22, 15), "#f2e040", within=m)
        s.paint(s.m_line(16, 20, 23, 18), WHITE, within=m)
    bird(s, "#f2d230", "#f6e050", head="#e0402a", wing="#1e1a22", tail_col="#1e1a22", beak="cone",
         beak_col="#d8c890", legs="#5a5a64", tail="mid", wing_mark=wing,
         face=lambda s: s.paint(s.m_ellipse(14, 15, 3.5, 2.5), "#f4c040", within=s.last))


@sprite("clarks_nutcracker")
def _(s):
    # Ash gray with black wings flashing white patches and a long sharp black bill.
    def wing(s, m):
        s.paint(s.m_ellipse(22, 21, 3, 1.5, rot=-15), WHITE, within=m)
    bird(s, "#a4a4a8", "#c4c4c8", head="#b0b0b4", wing="#1e1a22", tail_col="#1e1a22", beak="long",
         beak_col="#1e1a22", legs="#2b2630", tail="short", wing_mark=wing,
         face=lambda s: s.paint(s.m_ellipse(8, 11, 2.4, 2), "#e8e8ec", within=s.last))
    s.eye(8, 10)
    s.px([(28, 17), (29, 18)], WHITE)


@sprite("violet_green_swallow")
def _(s):
    # Shiny green back, violet wings and rump, and white wrapping up around the eye.
    def sheen(s, m):
        s.paint(s.m_ellipse(23, 19, 3, 1.4), "#8a4ab8", within=m)

    def face(s):
        s.paint(s.m_ellipse(9, 14, 5, 3) | s.m_ellipse(9, 10, 2.5, 2.2), WHITE, within=s.last)
    bird(s, "#3a8a5a", WHITE, head="#3a8a5a", wing="#5a3a8a", tail_col="#5a3a8a", beak="thin",
         beak_col="#1a1a22", legs="#5a4a44", tail="mid", wing_mark=sheen, face=face)
    s.eye(8, 10)


@sprite("ruffed_grouse")
def _(s):
    # Mottled brown with a little crest, a black neck ruff and a banded fan tail.
    def bars(s, m):
        for y in (19, 21, 23, 25):
            s.paint(s.m_line(9, y, 18, y + 1), "#8a6a4a", within=m)

    def spots(s, m):
        s.paint(s.m_px([(17, 17), (20, 18), (23, 17), (19, 20), (22, 20)]), "#e8d8b8", within=m)
    bird(s, "#8a6a4a", "#e8d8bc", head="#9a7654", wing="#7a5a3e", tail_col="#a07c56", beak="cone",
         beak_col="#4a3d3a", legs="#b89878", tail="fan", crest="jay", belly_mark=bars, wing_mark=spots, big=True)
    s.paint(s.m_line(25, 11, 30, 17) | s.m_line(26, 11, 31, 17), "#2b2226")  # the dark tail band
    s.ellipse(14, 16.5, 2.4, 2, "#2b2226")  # the ruff


@sprite("dusky_grouse")
def _(s):
    # A big slate-gray grouse with an orange-yellow comb over the eye.
    def spots(s, m):
        s.paint(s.m_px([(17, 18), (20, 19), (23, 18), (19, 21)]), "#a8a8b0", within=m)
    bird(s, "#5a5a66", "#7a7a86", head="#5a5a66", wing="#6a5a4e", tail_col="#2b2630", beak="cone",
         beak_col="#2b2630", legs="#8a8a90", tail="fan", wing_mark=spots, big=True)
    s.paint(s.m_ellipse(9, 7.5, 2.6, 1.2), "#f0a030")
    s.paint(s.m_line(26, 12, 31, 18), "#9a9aa4")
    s.paint(s.m_px([(12, 22), (15, 24), (11, 25), (16, 21)]), WHITE)


@sprite("pine_siskin")
def _(s):
    # A tiny streaky brown finch with yellow flashes in the wing and a sharp bill.
    def streaks(s, m):
        s.paint(s.m_px([(10, 19), (13, 20), (11, 22), (15, 22), (13, 24), (9, 21), (16, 19)]), "#6a5a44", within=m)

    def wing(s, m):
        s.paint(s.m_line(16, 20, 24, 18) | s.m_line(17, 21, 24, 19), "#f2d22a", within=m)
        s.paint(s.m_px([(18, 16), (21, 16)]), "#3a2e22", within=m)
    bird(s, "#9a8462", "#ece2cc", head="#9a8462", wing="#5a4a36", tail_col="#4a3e30", beak="thin",
         beak_col="#5a5050", legs="#8a7060", tail="mid", belly_mark=streaks, wing_mark=wing,
         face=lambda s: s.paint(s.m_px([(9, 7), (12, 8), (14, 10), (11, 6), (13, 13)]), "#6a5a44", within=s.last))
    s.px([(28, 13), (29, 14)], "#f2d22a")


@sprite("yellow_headed_blackbird")
def _(s):
    # Black, with a bright yellow head and chest and a white wing patch.
    def wing(s, m):
        s.paint(s.m_ellipse(17, 18, 3, 1.4), WHITE, within=m)

    def chest(s, m):
        s.paint(s.m_ellipse(10, 17, 4, 3), "#f2c82a", within=m)
    bird(s, "#1e1a22", "#26222a", head="#f2c82a", wing="#1a161e", tail_col="#1a161e", beak="crow",
         beak_col="#141218", legs="#2a2630", tail="mid", belly_mark=chest, wing_mark=wing,
         face=lambda s: s.paint(s.m_ellipse(6, 11, 2.5, 1.6), BLACK, within=s.last))
    s.eye(8, 10)


@sprite("vesper_sparrow")
def _(s):
    # Streaky gray-brown with a white eye ring, a chestnut shoulder and white outer tail feathers.
    def streaks(s, m):
        s.paint(s.m_px([(10, 19), (13, 20), (11, 22), (15, 21), (9, 21), (16, 19)]), "#6a5a48", within=m)

    def wing(s, m):
        s.paint(s.m_ellipse(17, 16.5, 2.2, 1.2), "#a8603a", within=m)
        s.paint(s.m_px([(19, 19), (21, 18), (23, 19), (20, 21)]), "#5a4a38", within=m)

    def face(s):
        s.paint(s.m_ellipse(8.5, 10.5, 2.2, 2.2), "#f4f0e8", within=s.last)
        s.paint(s.m_ellipse(10, 14, 2.5, 1.5), "#7a6a54", within=s.last)
    bird(s, "#9a8a72", "#efe8dc", head="#9a8a72", wing="#8a7660", tail_col="#6a5a48", beak="cone",
         beak_col="#b8a088", legs="#d8b898", tail="mid", belly_mark=streaks, wing_mark=wing, face=face)
    s.eye(8, 10)
    s.paint(s.m_line(22, 23, 30, 17), WHITE)


@sprite("brewers_blackbird")
def _(s):
    # Glossy black with a purple head, green-sheened body and a pale yellow eye.
    def sheen(s, m):
        s.paint(s.m_ellipse(18, 18, 3, 1.5), "#2a5a5a", within=m)
    bird(s, "#1e1e26", "#24262e", head="#2e2246", wing="#1a1c24", tail_col="#1a1c24", beak="cone",
         beak_col="#141218", legs="#2a2630", tail="mid", eye_col="#f4ec9a", wing_mark=sheen)
    s.px([(8, 10)], "#f4ec9a")
    s.px([(9, 11)], EYE)


@sprite("ring_necked_pheasant")
def _(s):
    # The rooster: coppery body, green head, red face, white neck ring and a very long tail.
    s.path([(20, 18), (27, 13), (33, 8), (36, 6)], (1.6, 0.6), "#b8904a")
    s.paint(s.m_px([(26, 13), (29, 11), (32, 9), (34, 7)]), "#5a3a1e")

    def spots(s, m):
        s.paint(s.m_px([(10, 20), (13, 22), (16, 20), (11, 24), (15, 24)]), "#3a2a1e", within=m)

    def wing(s, m):
        s.paint(s.m_px([(18, 17), (21, 18), (23, 17), (19, 20), (22, 20)]), "#e8d8b0", within=m)
    bird(s, "#c0682e", "#b0582a", head="#1e5a4a", wing="#a08a6a", tail_col="#b8904a", beak="cone",
         beak_col="#d8c8a0", legs="#8a8a80", tail="long", belly_mark=spots, wing_mark=wing)
    s.paint(s.m_ellipse(8.5, 11, 2.6, 2.6), "#e02a2a")
    s.paint(s.m_path([(9, 16.5), (16, 16.5)], 0.8), WHITE)
    s.px([(12, 4), (13, 4), (14, 5)], "#1e5a4a")  # ear tufts
    s.eye(8, 10)


@sprite("lark_sparrow")
def _(s):
    # A bold chestnut, white and black face "harlequin" and one dark spot on the chest.
    def face(s):
        h = s.last
        s.paint(s.m_ellipse(11, 6.5, 5.5, 2.2), "#a8502a", within=h)
        s.paint(s.m_line(9, 6, 15, 6), WHITE, within=h)
        s.paint(s.m_line(5, 9, 15, 8), WHITE, within=h)
        s.paint(s.m_ellipse(11, 12, 3, 1.8), "#a8502a", within=h)
        s.paint(s.m_line(5, 14, 13, 15), BLACK, within=h)

    def spot(s, m):
        s.paint(s.m_ellipse(11, 20, 1.4, 1.4), "#2b2226", within=m)
    bird(s, "#9a8068", "#f2eee6", head="#c8c0b4", wing="#8a6e54", tail_col="#3a3028", beak="cone",
         beak_col="#8a8080", legs="#d8b898", tail="fan", face=face, belly_mark=spot,
         wing_mark=lambda s, m: s.paint(s.m_px([(18, 18), (21, 17), (20, 20)]), "#4a3a28", within=m))
    s.eye(8, 10)
    s.paint(s.m_line(27, 13, 31, 18), WHITE)


@sprite("bobolink")
def _(s):
    # The male wears his tuxedo backwards: black below, white on the back, a buttery nape.
    def wing(s, m):
        s.paint(s.m_ellipse(18, 17, 4, 1.8), WHITE, within=m)
    bird(s, "#1e1a22", "#26222a", head="#1e1a22", wing="#1a161e", tail_col="#1a161e", beak="cone",
         beak_col="#2b2630", legs="#5a5050", tail="mid", wing_mark=wing)
    s.paint(s.m_ellipse(14.5, 9, 3.5, 3.5), "#f2e0a0", within=s.m_ellipse(11, 11, 6.5, 6))
    s.paint(s.m_ellipse(24, 16, 2.5, 1.5), WHITE)


@sprite("clay_colored_sparrow")
def _(s):
    # A pale little sparrow with a brown cheek patch outlined in dark and a gray nape.
    def face(s):
        h = s.last
        s.paint(s.m_ellipse(11, 6.5, 5, 2), "#8a6a4a", within=h)
        s.paint(s.m_line(9, 6, 15, 6), "#e8e0cc", within=h)
        s.paint(s.m_ellipse(10.5, 12, 3, 2), "#b08a60", within=h)
        s.paint(s.m_line(8, 14, 13, 14) | s.m_line(8, 10, 13, 10), "#5a4430", within=h)
        s.paint(s.m_ellipse(15, 10, 1.6, 2.4), "#a8a8a8", within=h)
    bird(s, "#a88a6a", "#f2ebe0", head="#d8ccb8", wing="#9a7a5a", tail_col="#7a604a", beak="cone",
         beak_col="#d8a888", legs="#e0c0a0", tail="mid", face=face,
         wing_mark=lambda s, m: s.paint(s.m_px([(18, 17), (21, 17), (19, 19), (22, 19)]), "#4a3a28", within=m))
    s.eye(8, 10)


@sprite("common_goldeneye")
def _(s):
    # Mostly white with a black back, a puffy green-black head, a round white cheek spot and a gold eye.
    duck(s, WHITE, WHITE, "#1e3a32", bill="#26242a", ring=None, speculum=WHITE, tail_col="#2b2630")
    s.paint(s.m_poly([(17, 18), (28, 18), (28, 20.5), (17, 20.5)]), "#1e1a22")
    s.paint(s.m_ellipse(6.5, 13.5, 1.6, 1.4), WHITE)
    s.px([(7, 10), (8, 10), (7, 11), (8, 11)], "#f2c42a")
    s.px([(8, 11)], EYE)


@sprite("ring_necked_duck")
def _(s):
    # Black back and head, pale gray sides with a white notch, and a gray bill ringed in white.
    duck(s, "#a8a8b0", "#1e1a22", "#2a2236", bill="#7a7e8a", ring=None, speculum="#6a6a74", tail_col="#1e1a22")
    s.paint(s.m_poly([(19, 17), (30, 17), (30, 20), (19, 20)]), "#1e1a22")
    s.paint(s.m_poly([(13, 18), (15, 18), (14, 24), (13, 24)]), WHITE)
    s.paint(s.m_line(2, 12, 2, 14), WHITE)
    s.px([(0, 13), (1, 13), (1, 12)], "#1e1a22")
    s.paint(s.m_ellipse(12, 7, 3, 2), "#2a2236")  # peaked crown


@sprite("western_grebe")
def _(s):
    # Black above and white below with a long swan-like neck, a red eye and a yellow bill.
    s.can("swim", "fly")
    flying = s.act == "fly"
    w = s.wave()
    if flying:
        _far_wing(s, 23, 21, w, "#3a3a40")
    else:
        _ripples(s, s.f if s.act == "swim" else 0, ((2, 30), (6, 29), (25, 30), (29, 29)))
    s.poly([(25, 21), (30, 20), (29, 23)], "#3a3a40")
    s.ellipse(19, 24, 10.5, 5.5, "#4a4a52")
    s.ellipse(15, 26, 6, 3, WHITE)
    if flying:
        _wing_beat(s, 22, 21, w, "#2e2e34")
    else:
        s.ellipse(22, 22, 7, 3, "#2e2e34", rot=-8, edge=True)
    m = s.path([(13, 21), (10, 14), (11, 8)], 1.9, WHITE)
    s.paint(s.m_path([(15, 21), (12, 14), (13, 8)], 1.0), "#2b2630", within=m)
    s.ellipse(10.5, 6.5, 4, 3.4, WHITE, edge=True)
    s.paint(s.m_ellipse(12, 4.5, 4, 2.6), "#2b2630", within=s.last)
    s.poly([(7, 6), (0, 7.5), (7, 8.5)], "#d8c82a")
    s.px([(9, 5), (10, 5), (9, 6), (10, 6)], "#e02a2a")
    s.px([(9, 6)], EYE)


# --------------------------------------------------------------------------- reptiles
@sprite("prairie_rattlesnake")
def _(s):
    # Greenish-tan with brown blotches edged in pale, and a rattle.
    snake(s, "#a8a878", belly="#e8e4c4", blotch="#6a5a3a", band_period=3.4, band_len=1.8, rattle=True,
          head="#a0a070", head_w=5.6)
    s.paint(s.m_line(8, 8, 14, 11), "#e8e4c4")


@sprite("western_milksnake")
def _(s):
    # Bright red, black and white rings.
    snake(s, "#f4f0e4", belly="#f0e4dc", bands=BLACK, blotch="#d83a2a", band_period=5.4, band_len=3.8,
          head=BLACK)
    s.paint(s.m_ellipse(8, 11.5, 2.6, 2), "#f4f0e4")  # pale snout
    s.eye(9, 9)


@sprite("plains_hognose_snake")
def _(s):
    # Tan with dark brown blotches and a turned-up shovel snout.
    snake(s, "#c8a870", belly="#2b2226", blotch="#6a4a2a", band_period=2.8, head_w=6, head="#c0a068")
    s.px([(6, 9), (7, 9), (6, 8), (6, 7)], "#c0a068")
    s.paint(s.m_line(9, 11, 15, 8), "#6a4a2a")


@sprite("western_terrestrial_garter_snake")
def _(s):
    # Dark olive with a yellow stripe down the back and dark checkers.
    snake(s, "#4a4a3a", belly="#d8d0a0", stripe="#e8c84a", bands="#2e2e24", band_period=2.6, band_len=0.8,
          head="#4a4a3a")


@sprite("northern_rubber_boa")
def _(s):
    # Smooth and rubbery-looking, plain olive-brown, with a blunt tail that looks like a second head.
    snake(s, "#8a6e52", belly="#f0d080", head="#8a6e52", head_w=4.6, stripe="#a08a6a")
    s.paint(s.m_px([(10, 21), (19, 21), (8, 26), (17, 28), (22, 22)]), "#f0d080")


@sprite("eastern_collared_lizard")
def _(s):
    # A big-headed blue-green lizard with two black collars and a yellow head.
    def pat(s, m):
        s.paint(s.m_px([(12, 20), (15, 21), (18, 20), (21, 21), (14, 23), (19, 23), (10, 21)]), "#e8e8a0", within=m)
    lizard(s, "#3aa08a", "#e8f0d8", head="#e0c040", pattern=pat, tail_col="#5a8a5a", wide=True)
    s.paint(s.m_path([(10, 15), (11, 21)], 0.9), BLACK)
    s.paint(s.m_path([(12.5, 17), (13, 21)], 0.7), BLACK)


@sprite("colorado_checkered_whiptail")
def _(s):
    # Brown with a checkerboard of pale spots and a very long tail.
    def pat(s, m):
        s.paint(s.m_px([(x + (y % 2) * 1, y) for y in (19, 21, 23) for x in range(9, 23, 3)]), "#f0e6c4", within=m)
    lizard(s, "#6a5034", "#ece6d8", pattern=pat, tail_col="#8a6e4e",
           tail_pts=[(20, 22), (27, 25), (33, 24), (36, 19)])


@sprite("plateau_striped_whiptail")
def _(s):
    # Dark brown with six bright yellow stripes and a blue-green tail.
    def pat(s, m):
        for y in (19, 21, 23):
            s.paint(s.m_line(9, y, 22, y), "#f0e060", within=m)
    lizard(s, "#3a3226", "#e8eef4", pattern=pat, tail_col="#5a9ab0",
           tail_pts=[(20, 22), (27, 25), (33, 24), (36, 19)])
    s.paint(s.m_line(4, 17, 11, 17), "#f0e060")


@sprite("common_sagebrush_lizard")
def _(s):
    # Gray-brown with pale side stripes, little dark bars, and blue belly patches.
    def pat(s, m):
        s.paint(s.m_line(9, 19, 22, 19), "#d8d0b8", within=m)
        s.paint(s.m_px([(11, 20), (14, 20), (17, 20), (20, 20)]), "#3a3228", within=m)
        s.paint(s.m_ellipse(15, 24.5, 4, 1.2), "#4a7ad8", within=m)
    lizard(s, "#8a7c64", "#e8e4d8", pattern=pat, tail_col="#7a6c54")
    s.paint(s.m_ellipse(10, 18, 1, 1), "#3a3228")


@sprite("western_earless_lizard")
def _(s):
    # Sandy tan and smooth-headed (no ear openings), with two black bars on its side.
    def pat(s, m):
        s.paint(s.m_px([(10, 19), (13, 20), (16, 19), (19, 20)]), "#9a7a5a", within=m)
        s.paint(s.m_line(12, 22, 12, 24) | s.m_line(14, 22, 14, 24), BLACK, within=m)
    lizard(s, "#c8b088", "#f4ecdc", pattern=pat, tail_col="#b89c76", smooth=True)


@sprite("northern_alligator_lizard")
def _(s):
    # A long, stiff-scaled brown lizard with tiny legs and dark lines along its sides.
    def pat(s, m):
        s.paint(s.m_line(8, 20, 22, 20), "#4a3a2a", within=m)
        s.paint(s.m_line(8, 23, 22, 23), "#4a3a2a", within=m)
        s.paint(s.m_px([(10, 21), (13, 22), (16, 21), (19, 22)]), "#5a4a3a", within=m)
    lizard(s, "#8a6e48", "#c8c4b0", pattern=pat, tail_col="#7a6040", legs="#6a5438",
           tail_pts=[(20, 22), (27, 25), (33, 24), (36, 20)])


@sprite("desert_horned_lizard")
def _(s):
    # A flat, round, sandy "horny toad" with a crown of short horns.
    def pat(s, m):
        s.paint(s.m_ellipse(13, 20, 1.6, 1.2) | s.m_ellipse(18, 20, 1.6, 1.2), "#7a5a40", within=m)
        s.paint(s.m_px([(9, 18), (11, 18), (14, 18), (17, 18), (20, 18), (12, 22), (16, 22)]), "#f4ead8", within=m)
    lizard(s, "#d8bc90", "#f4ead8", pattern=pat, horns=True, wide=True,
           tail_pts=[(21, 23), (25, 25), (28, 25)])


@sprite("long_nosed_leopard_lizard")
def _(s):
    # Pale gray with lots of dark leopard spots and a long tail.
    def pat(s, m):
        s.paint(s.m_px([(9, 19), (12, 20), (15, 19), (18, 20), (21, 19), (10, 22), (14, 22), (17, 23), (20, 22)]),
                "#4a3e34", within=m)
        s.paint(s.m_line(8, 21, 22, 21), "#ece4d0", within=m)
    lizard(s, "#b8b0a0", "#f0ece4", pattern=pat, tail_col="#a8a090",
           tail_pts=[(20, 22), (27, 25), (33, 24), (36, 19)])
    s.paint(s.m_px([(5, 15), (8, 16), (10, 17), (25, 24), (29, 24), (33, 23)]), "#4a3e34")


# --------------------------------------------------------------------------- amphibians
@sprite("western_tiger_salamander")
def _(s):
    # Chunky and dark with bold yellow bars and blotches.
    def pat(s, m):
        for x in (10, 14, 18, 22):
            s.paint(s.m_ellipse(x, 21, 1.3, 3), "#e8c83a", within=m)
    lizard(s, "#2e3428", "#c8b858", smooth=True, eye_big=True, legs="#c8a840", pattern=pat, wide=True)
    for x in (25, 29):
        s.paint(s.m_line(x, 21, x, 26), "#e8c83a")
    s.paint(s.m_ellipse(9, 16, 1.6, 1.2), "#e8c83a")
    s.eye(5, 16, size=3)
    s.px([(5, 16)], WHITE)


@sprite("mexican_spadefoot")
def _(s):
    # A plump gray-green toad with little orange-tipped bumps and cat-like eyes.
    frog(s, "#8a9070", "#efece0", spots=[(11, 21), (14, 23), (19, 21), (22, 23), (8, 24), (24, 24)])
    s.paint(s.m_px([(12, 20), (20, 20), (16, 23), (9, 22), (23, 22)]), "#e09a4a")
    s.px([(10, 9), (10, 10), (10, 11), (21, 9), (21, 10), (21, 11)], EYE)  # vertical pupils
    s.px([(9, 10), (11, 10), (20, 10), (22, 10), (9, 11), (11, 11), (20, 11), (22, 11)], "#d8b84a")


@sprite("plains_spadefoot")
def _(s):
    # Gray-brown with pale stripes down its back and a bump between the eyes.
    frog(s, "#9a8a6a", "#f2ecdc", spots=[(10, 20), (22, 20), (13, 24), (19, 24)])
    s.paint(s.m_line(12, 17, 10, 26) | s.m_line(20, 17, 22, 26), "#d8ccb0")
    s.paint(s.m_ellipse(16, 11.5, 1.6, 1.2), "#7a6a4a")
    s.px([(10, 9), (10, 10), (10, 11), (21, 9), (21, 10), (21, 11)], EYE)
    s.px([(9, 10), (11, 10), (20, 10), (22, 10), (9, 11), (11, 11), (20, 11), (22, 11)], "#c8b06a")


@sprite("rocky_mountain_tailed_frog")
def _(s):
    # A flat brown stream frog with a pale bar between the eyes and a dark eye stripe.
    frog(s, "#8a6e52", "#ece0cc", spots=[(11, 21), (20, 22), (15, 24), (23, 20)])
    s.paint(s.m_line(10, 13, 22, 13), "#d8c8a8")
    s.paint(s.m_poly([(1, 14), (6, 12), (7, 14), (2, 17)]) | s.m_poly([(31, 14), (26, 12), (25, 14), (30, 17)]),
            "#3a2a20")
    s.px([(16, 29), (16, 30), (15, 30), (17, 30)], "#8a6e52")  # the little "tail"


@sprite("canadian_toad")
def _(s):
    # A warty brown-and-green toad with a big bump (boss) between the eyes.
    frog(s, "#7a7a4e", "#ece4d0", spots=[(10, 20), (13, 22), (19, 21), (22, 23), (16, 24), (8, 24), (24, 21)])
    s.paint(s.m_px([(11, 19), (14, 21), (18, 20), (21, 22), (12, 15), (20, 15)]), "#c8784a")
    s.paint(s.m_ellipse(16, 12, 2.4, 1.6), "#9a9a64")
    s.paint(s.m_line(16, 15, 16, 26), "#c8c08a")


# --------------------------------------------------------------------------- fish
@sprite("rainbow_trout")
def _(s):
    # Olive back sprinkled with black spots and a pink-red band down its side.
    def pat(s, m):
        s.paint(s.m_path([(4, 16.5), (14, 17), (25, 16.5)], 1.4), "#e8708a", within=m)
        s.paint(s.m_px([(11, 11), (14, 12), (17, 11), (20, 12), (23, 13), (13, 14), (19, 14), (22, 15)]), BLACK,
                within=m)
    fish(s, "#7a8a5a", "#eef0ec", fin="#8a9070", pattern=pat, slim=True)
    s.px([(28, 12), (29, 15), (28, 19)], BLACK)


@sprite("brown_trout")
def _(s):
    # Golden brown with black spots and red spots wearing pale halos.
    def pat(s, m):
        s.paint(s.m_px([(11, 11), (15, 12), (19, 11), (22, 13), (13, 14), (17, 15), (10, 14)]), "#2b2226", within=m)
        for x, y in ((14, 18), (19, 17), (22, 16)):
            s.paint(s.m_ellipse(x + 0.5, y + 0.5, 1.4, 1.4), "#f0e0c0", within=m)
            s.paint(s.m_px([(x, y)]), "#d8302a", within=m)
    fish(s, "#a87e40", "#f0dca0", fin="#9a7438", pattern=pat, slim=True)


@sprite("rocky_mountain_cutthroat_trout")
def _(s):
    # Golden olive with black spots crowded toward the tail and a red slash under the jaw.
    def pat(s, m):
        s.paint(s.m_px([(16, 12), (19, 11), (21, 13), (23, 12), (24, 15), (20, 15), (22, 17), (25, 18), (18, 14)]),
                BLACK, within=m)
        s.paint(s.m_ellipse(10, 17, 2, 1.6), "#e89070", within=m)
    fish(s, "#9a9a4a", "#f0e8b0", fin="#a8904a", pattern=pat, slim=True)
    s.px([(28, 12), (29, 15), (28, 19), (30, 17)], BLACK)
    s.paint(s.m_line(5, 20, 9, 20) | s.m_line(5, 21, 8, 21), "#e02a2a")


@sprite("westslope_cutthroat_trout")
def _(s):
    # Silvery-yellow with small black spots on the back half and a bright red jaw slash.
    def pat(s, m):
        s.paint(s.m_px([(17, 11), (20, 12), (23, 11), (25, 14), (21, 14), (18, 13)]), BLACK, within=m)
    fish(s, "#a8a87a", "#f4f0d8", fin="#c8a860", pattern=pat, slim=True)
    s.paint(s.m_ellipse(14, 18, 4, 1.4), "#f0c070")
    s.px([(29, 12), (28, 17)], BLACK)
    s.paint(s.m_line(5, 20, 9, 20) | s.m_line(5, 21, 8, 21), "#e02a2a")


@sprite("lake_trout")
def _(s):
    # Dark gray-green covered in pale cream spots, with a deeply forked tail.
    def pat(s, m):
        s.paint(s.m_px([(x + (y % 3), y) for y in (11, 13, 15, 17, 19) for x in range(9, 25, 3)]), "#e8e4c8",
                within=m)
    fish(s, "#4a5a50", "#e8e8dc", fin="#5a6858", pattern=pat, slim=True)
    s.erase(s.m_poly([(28, 16.5), (32, 13), (32, 20)]))


@sprite("utah_sucker")
def _(s):
    # A long olive-brown bottom feeder with fleshy sucking lips underneath.
    fish(s, "#7a6a4a", "#e8dcc0", fin="#8a7050", slim=True)
    s.ellipse(4, 19.5, 2, 1.4, "#e0b098")
    s.paint(s.m_line(5, 15, 25, 15), "#5a4a34")


@sprite("redside_shiner")
def _(s):
    # A small minnow: dark back, a dark side stripe, and a red-orange flush along its sides.
    def pat(s, m):
        s.paint(s.m_path([(5, 15), (15, 15.5), (25, 15)], 0.8), "#3a3a3e", within=m)
        s.paint(s.m_path([(8, 18), (15, 19), (22, 18)], 1.0), "#e0502a", within=m)
        s.paint(s.m_ellipse(15, 12, 9, 2), "#5a6a5a", within=m)
    fish(s, "#b8b8a4", "#f2eedc", fin="#a8a890", pattern=pat, slim=True)


@sprite("mountain_whitefish")
def _(s):
    # Slim and silvery with big scales, a tiny mouth and a pointy snout.
    def pat(s, m):
        s.paint(s.m_ellipse(15, 12, 10, 2.4), "#7a8a94", within=m)
        s.paint(s.m_px([(x + (y % 2) * 1.5, y) for y in (14, 16, 18) for x in range(11, 24, 3)]), "#d8dce4", within=m)
    fish(s, "#b8c0c8", "#f0f2f4", fin="#a0a8b0", pattern=pat, slim=True)
    s.px([(4, 18)], "#c0c8d0")


@sprite("goldeye")
def _(s):
    # A deep silvery fish with a big golden eye.
    fish(s, "#a8b4c0", "#f2f4f6", fin="#c8c0a0")
    s.paint(s.m_ellipse(15, 11, 9, 2), "#6a7a8a")
    s.px([(5, 13), (6, 13), (7, 13), (5, 14), (7, 14), (5, 15), (6, 15), (7, 15)], "#f0c02a")
    s.px([(6, 14)], EYE)


@sprite("fathead_minnow")
def _(s):
    # Small, dark olive and blunt-headed, with a dark smudge on the back fin.
    def pat(s, m):
        s.paint(s.m_path([(5, 16), (15, 16.5), (25, 16)], 0.8), "#3a3e30", within=m)
    fish(s, "#6a704e", "#d8d4b0", fin="#5a5e40", pattern=pat)
    s.paint(s.m_ellipse(15, 8, 2.4, 1.4), "#2b2226")
    s.paint(s.m_ellipse(5, 13, 3, 2), "#4a4e34")  # dark, blunt head


# --------------------------------------------------------------------------- insects and other small animals
@sprite("seven_spotted_lady_beetle")
def _(s):
    # Red with seven black spots and a black-and-white "face" plate.
    beetle_top(s, "#e0302a", spots=[(16, 13.5), (11, 17), (21, 17), (10, 23), (22, 23), (13, 27), (19, 27)],
               pron=BLACK)
    s.paint(s.m_ellipse(11, 11, 1.6, 1.2) | s.m_ellipse(21, 11, 1.6, 1.2), WHITE)


def _bumble(s, bands, *, base="#2b2226"):
    """Side view bumble bee; bands are (x0, x1, colour) stripes across the abdomen."""
    s.can("fly")
    up = not (s.act == "fly" and s.f % 2)
    s.ellipse(20, 8 if up else 11, 4.5, 6.5 if up else 4, "#e6f4fc", rot=25 if up else 70, shade=False, edge=True)
    s.ellipse(25, 11 if up else 13, 3.5, 5 if up else 3, "#d6ecfa", rot=40 if up else 80, shade=False, edge=True)
    m = s.ellipse(18, 19, 9, 7.5, base)
    for x0, x1, c in bands:
        s.paint(s.m_poly([(x0, 8), (x1, 8), (x1, 30), (x0, 30)]), c, within=m)
    s.line(9, 25, 8, 29, "#2b2226")
    s.line(13, 25, 13, 29, "#2b2226")
    s.ellipse(8.5, 17, 5.5, 5.5, "#2b2226", edge=True)
    s.line(6, 12, 4, 6, "#2b2226")
    s.line(9, 12, 10, 6, "#2b2226")
    s.eye(5, 16, color="#11080f", shine="#ffffff")
    s.blush(5, 19, color="#ff8fa8")
    return m


@sprite("hunts_bumble_bee")
def _(s):
    # Yellow up front, then a bright rusty-orange band, yellow again and a black tip.
    _bumble(s, [(9, 16, "#f2c42a"), (16, 21, "#e0642a"), (21, 24, "#f2c42a")])
    s.paint(s.m_ellipse(9, 13, 4, 2), "#f2c42a", within=s.m_ellipse(8.5, 17, 5.5, 5.5))


@sprite("european_paper_wasp")
def _(s):
    # Slim and wasp-waisted, banded black and yellow, with orange antennae and dangling legs.
    s.can("fly")
    up = not (s.act == "fly" and s.f % 2)
    s.ellipse(18, 9 if up else 12, 3, 7 if up else 3.5, "#e8eef8", rot=20 if up else 75, shade=False, edge=True)
    s.ellipse(22, 11 if up else 14, 2.4, 5 if up else 2.6, "#dce6f4", rot=35 if up else 85, shade=False, edge=True)
    for x0, x1 in ((12, 13), (15, 17), (19, 22)):
        s.line(x0, 21, x1, 28, "#f0c020")
    m = s.ellipse(22, 20, 7, 3.8, "#f2c820", rot=12)
    s.poly([(27, 21), (32, 24), (27, 24)], "#f2c820")
    for x in (19, 23, 27):
        s.paint(s.m_poly([(x, 10), (x + 1.4, 10), (x + 1.4, 30), (x, 30)]), "#1e1a1e", within=m)
    s.paint(s.m_ellipse(25, 19, 0.8, 0.8) | s.m_ellipse(21, 18, 0.8, 0.8), "#1e1a1e", within=m)
    s.ellipse(14.5, 19, 1.4, 1.1, "#1e1a1e")  # the narrow waist
    s.ellipse(11.5, 18, 3.2, 3, "#1e1a1e", edge=True)
    s.paint(s.m_px([(11, 16), (12, 16), (13, 18)]), "#f2c820")
    s.ellipse(6.5, 17, 4, 4, "#f2c820", edge=True)
    s.paint(s.m_ellipse(7, 14, 3.5, 1.6), "#1e1a1e", within=s.last)
    s.line(5, 13, 2, 6, "#e8802a")
    s.line(8, 13, 9, 6, "#e8802a")
    s.eye(4, 16, color="#11080f", shine="#ffffff")
    s.blush(4, 19, color="#ff8fa8")


@sprite("two_tailed_swallowtail")
def _(s):
    # Yellow with thin black tiger stripes and TWO tails on each hindwing.
    def pat(s, fm, hm):
        w = fm | hm
        for a, b in [((6, 3), (9, 13)), ((10, 6), (12, 13)), ((13, 9), (14, 15))]:
            s.paint(s.m_line(*a, *b), BLACK, mirror=True, within=w)
        s.paint(s.m_line(2, 7, 2, 14) | s.m_line(3, 13, 13, 17) | s.m_line(5, 20, 8, 26) | s.m_line(6, 23, 10, 26),
                BLACK, mirror=True, within=w)
        s.px([(9, 24), (10, 25)], "#4a7ae8", mirror=True)
        s.px([(13, 23)], "#f0802a", mirror=True)
    s.path([(7, 23), (5, 28)], (1.0, 0.7), "#f6d42a", mirror=True)
    butterfly(s, "#f6d42a", "#f6d42a", pattern=pat, tails=True)


@sprite("two_striped_grasshopper")
def _(s):
    # Olive-green with two pale yellow stripes running from its eyes down its back.
    grasshopper(s, "#7a8a3a", "#5a6a2a", legs="#8a9040")
    s.paint(s.m_line(9, 13, 14, 16) | s.m_line(14, 16, 26, 16), "#f0e070")
    s.paint(s.m_line(20, 21, 26, 15), "#4a3a22")


@sprite("mormon_fritillary")
def _(s):
    # Orange with rows of small black spots and dashes.
    def pat(s, fm, hm):
        s.paint(s.m_px([(5, 6), (8, 7), (11, 9), (4, 10), (7, 11), (10, 12), (13, 13), (6, 14)]), BLACK,
                mirror=True, within=fm)
        s.paint(s.m_line(15, 12, 8, 7), "#c8601a", mirror=True, within=fm)
        s.paint(s.m_px([(6, 20), (9, 21), (12, 20), (6, 23), (9, 24), (12, 23)]), BLACK, mirror=True, within=hm)
        s.paint(s.m_poly([(1.5, 6), (5, 3), (5, 4.5), (2.5, 8)]), "#5a3a1a", mirror=True, within=fm)
    butterfly(s, "#f0902a", "#e88a2a", body="#5a3a1a", pattern=pat)


@sprite("rocky_mountain_parnassian")
def _(s):
    # Creamy white wings with black spots, glassy gray edges and little red eyespots.
    def pat(s, fm, hm):
        s.paint(s.m_poly([(1.5, 6), (5, 3), (6, 5), (2.5, 12)]), "#b8bcc4", mirror=True, within=fm)
        s.paint(s.m_ellipse(9, 8, 1.2, 1.2) | s.m_ellipse(12, 11, 1.2, 1.2) | s.m_ellipse(5, 9, 1, 1), BLACK,
                mirror=True, within=fm)
        for x, y in ((8, 20), (10, 24)):
            s.paint(s.m_ellipse(x, y, 1.6, 1.6), BLACK, mirror=True, within=hm)
            s.paint(s.m_ellipse(x, y, 1, 1), "#e0302a", mirror=True, within=hm)
    butterfly(s, "#f6f2e6", "#f4f0e2", body="#2b2630", pattern=pat)


@sprite("weidemeyers_admiral")
def _(s):
    # Velvety black with a bold white band across all four wings.
    def pat(s, fm, hm):
        s.paint(s.m_poly([(9, 9), (12, 11), (11, 16), (7, 15)]), WHITE, mirror=True, within=fm)
        s.paint(s.m_px([(4, 6), (5, 9)]), WHITE, mirror=True, within=fm)
        s.paint(s.m_poly([(7, 16), (12, 16), (12, 22), (8, 21)]), WHITE, mirror=True, within=hm)
        s.paint(s.m_px([(6, 23), (8, 25)]), "#e0802a", mirror=True, within=hm)
    butterfly(s, "#1e1a20", "#1e1a20", pattern=pat)


@sprite("lorquins_admiral")
def _(s):
    # Black with a white band and bright orange forewing tips.
    def pat(s, fm, hm):
        s.paint(s.m_poly([(1.5, 6), (5, 3), (7, 5), (3, 10)]), "#f08a2a", mirror=True, within=fm)
        s.paint(s.m_poly([(9, 9), (12, 11), (11, 16), (7, 15)]), WHITE, mirror=True, within=fm)
        s.paint(s.m_poly([(7, 16), (12, 16), (12, 22), (8, 21)]), WHITE, mirror=True, within=hm)
    butterfly(s, "#2a2022", "#2a2022", pattern=pat)


@sprite("blue_copper")
def _(s):
    # Not copper at all: a bright lilac-blue with thin black edges and white fringes.
    def pat(s, fm, hm):
        w = fm | hm
        core = w
        for _ in range(2):
            core = core & np.roll(core, 1, 0) & np.roll(core, -1, 0) & np.roll(core, 1, 1) & np.roll(core, -1, 1)
        rim = w & ~core & ~s.m_poly([(14, 0), (18, 0), (18, 32), (14, 32)])
        s.paint(rim, "#26243a")
        s.paint(s.m_px([(2, 8), (2, 11), (3, 13), (4, 4), (6, 3), (5, 22), (7, 25), (9, 26)]), WHITE, mirror=True,
                within=rim)
    butterfly(s, "#7aa0f0", "#7aa0f0", body="#3a3a5a", pattern=pat)


@sprite("boisduvals_blue")
def _(s):
    # Silvery sky blue with a dark border and white fringe.
    def pat(s, fm, hm):
        s.paint(s.m_poly([(1.5, 6), (5, 3), (5, 5), (2.5, 14)]), "#2b2a4a", mirror=True, within=fm)
        s.paint(s.m_line(5, 22, 9, 26), "#2b2a4a", mirror=True, within=hm)
        s.paint(s.m_ellipse(13, 9, 1.4, 0.8), "#2b2a4a", mirror=True, within=fm)
    butterfly(s, "#9ab8f0", "#9ab8f0", body="#3a3a5a", pattern=pat)


@sprite("melissa_blue")
def _(s):
    # Blue with a bright orange band of spots along the hindwing edge.
    def pat(s, fm, hm):
        s.paint(s.m_poly([(1.5, 6), (5, 3), (5, 5), (2.5, 14)]), "#2b2a4a", mirror=True, within=fm)
        s.paint(s.m_path([(5, 20), (7, 24), (11, 26)], 1.0), "#f08a2a", mirror=True, within=hm)
        s.paint(s.m_px([(6, 22), (8, 25)]), BLACK, mirror=True, within=hm)
    butterfly(s, "#6a8ae8", "#6a8ae8", body="#3a3a5a", pattern=pat)


@sprite("small_wood_nymph")
def _(s):
    # Plain brown with two yellow-ringed black eyespots on each forewing.
    def pat(s, fm, hm):
        for x, y in ((7, 7), (9, 11)):
            s.paint(s.m_ellipse(x, y, 1.7, 1.7), "#e8c870", mirror=True, within=fm)
            s.paint(s.m_ellipse(x, y, 1, 1), BLACK, mirror=True, within=fm)
            s.paint(s.m_px([(x, y)]), WHITE, mirror=True, within=fm)
        s.paint(s.m_px([(8, 23)]), BLACK, mirror=True, within=hm)
    butterfly(s, "#7a5e44", "#6e543c", body="#4a3a2a", pattern=pat)


@sprite("california_tortoiseshell")
def _(s):
    # Bright orange with black blotches and dark borders.
    def pat(s, fm, hm):
        w = fm | hm
        inner = s.m_poly([(15, 11), (5, 4.5), (3, 7), (3.5, 13.5), (14, 16)]) \
            | s.m_poly([(15, 16.5), (5.5, 16.5), (5, 21.5), (9.5, 25.5), (15, 21.5)])
        edge = w & ~(inner | inner[:, ::-1])
        s.paint(edge, "#3a2418", within=w)
        s.paint(s.m_ellipse(8, 7, 1.6, 1.2) | s.m_ellipse(11, 10, 1.3, 1.3) | s.m_ellipse(6, 11, 1.2, 1.2),
                "#3a2418", mirror=True, within=fm)
        s.paint(s.m_px([(3, 6)]), WHITE, mirror=True, within=fm)
        s.paint(s.m_ellipse(12, 19, 2, 1.5), "#3a2418", mirror=True, within=hm)
    butterfly(s, "#e8782a", "#e8782a", body="#3a2418", pattern=pat)


@sprite("western_tent_caterpillar_moth")
def _(s):
    # The caterpillar: hairy, blue-gray with orange dashes along its back.
    pts = _segmented(s, 8, "#5a7aa0", "#2b2a34", "#3a3a44", leg_len=1.2, spacing=2.8, r=2.7, antenna=0)
    for i, (x, y) in enumerate(pts):
        s.px([(round(x), round(y - 2)), (round(x) - 1, round(y - 2))], "#f08a2a")
        s.px([(round(x), round(y + 1))], "#a8c8e8")
        s.px([(round(x), round(y - 4)), (round(x + 1), round(y + 4))], "#e8d8c0")
    hx, hy = pts[0]
    s.ellipse(hx - 1, hy, 3.4, 3, "#2b2a34", edge=True)
    s.eye(round(hx - 2), round(hy - 1))


@sprite("leafy_spurge_hawkmoth")
def _(s):
    # The caterpillar: black with yellow and white spots, a red stripe and a red tail horn.
    pts = _segmented(s, 8, "#1e1a1e", "#d8302a", "#d8302a", leg_len=1.2, spacing=2.8, r=2.8, antenna=0)
    for i, (x, y) in enumerate(pts):
        s.px([(round(x), round(y + 1)), (round(x) - 1, round(y + 1))], "#d8302a")
        s.px([(round(x) - 1, round(y - 2))], "#f2d22a" if i % 2 else WHITE)
        s.px([(round(x) + 1, round(y - 1))], WHITE)
    tx, ty = pts[-1]
    s.path([(tx, ty - 2), (tx + 2, ty - 6)], (0.9, 0.5), "#d8302a", shade=False)
    hx, hy = pts[0]
    s.ellipse(hx - 1, hy, 3.4, 3, "#d8302a", edge=True)
    s.eye(round(hx - 2), round(hy - 1))


@sprite("western_conifer_seed_bug")
def _(s):
    # A long brown "stink bug" cousin with a white zigzag and leaf-shaped back legs.
    s.can("walk")
    w = s.wave() if s.act == "walk" else 0
    leg = "#6a4a30"
    for i, y in enumerate((14, 18)):
        d = round(w * (1 if i % 2 else -1))
        s.line(12, y, 7, y + 3 + d, leg, mirror=True)
    s.line(12, 22, 8, 30 - round(w), leg)
    s.line(19, 22, 23, 30 + round(w), leg)
    s.ellipse(7.5, 29, 2.2, 1, "#8a5a36", rot=-20)  # the flattened leafy leg
    s.ellipse(23.5, 29, 2.2, 1, "#8a5a36", rot=20)
    s.poly([(10, 14), (22, 14), (24, 18), (8, 18)], "#7a5838", edge=True)
    m = s.ellipse(16, 22, 6.5, 8, "#8a6440", edge=True)
    s.paint(s.m_ellipse(16, 22, 7, 8) & ~s.m_ellipse(16, 22, 5.5, 8), "#e8a040", within=m)
    s.paint(s.m_px([(10, 20), (10, 24), (21, 20), (21, 24)]), BLACK, within=m)
    s.paint(s.m_line(12, 22, 16, 25) | s.m_line(16, 25, 20, 22), "#f0e8d8", within=m)
    s.paint(s.m_ellipse(16, 28, 3, 2), "#4a3424", within=m)
    s.ellipse(16, 11, 2.6, 3, "#6a4a30", edge=True)
    s.line(14, 9, 10, 2, "#6a4a30")
    s.line(18, 9, 22, 2, "#6a4a30")
    s.px([(14, 10), (17, 10)], WHITE)
    s.px([(15, 10), (18, 10)], EYE)


@sprite("white_spotted_sawyer")
def _(s):
    # A black longhorn beetle with a white dot at the top of its back and super-long antennae.
    beetle_top(s, "#26242a", head="#1e1c22", pron="#1e1c22")
    s.paint(s.m_ellipse(16, 13, 1.2, 1.2), WHITE)
    s.paint(s.m_px([(11, 19), (20, 18), (12, 24), (19, 25), (10, 22), (22, 22)]), "#8a8a90")
    s.path([(13, 6), (8, 1), (3, 2), (-2, 6)], 0.5, "#2b2630", shade=False)
    s.path([(18, 6), (23, 1), (28, 2), (33, 6)], 0.5, "#2b2630", shade=False)


@sprite("european_mantis")
def _(s):
    # A bright green mantis (the "praying mantis") with a black-ringed eyespot on its foreleg.
    mantis(s, "#7ab83a", "#9ad05a", "#c8e07a")
    s.px([(13, 18)], BLACK)
    s.px([(12, 18)], WHITE)


@sprite("zebra_jumping_spider")
def _(s):
    # Tiny and fuzzy with black-and-white zebra stripes and big front eyes.
    def pat(s, m):
        for y in (17, 21, 25):
            s.paint(s.m_line(10, y, 22, y - 1) | s.m_line(10, y + 1, 22, y), WHITE, within=m)
    spider_top(s, "#1e1a1e", "#2a2428", pattern=pat, ceph="#2a2428", leg_bands="#e8e8e8")
    s.paint(s.m_line(13, 15, 19, 15), WHITE)
    s.px([(14, 12), (15, 12), (17, 12), (18, 12)], EYE)
    s.px([(14, 12), (17, 12)], WHITE)


@sprite("signal_crayfish")
def _(s):
    # Blue-brown with big claws that are red underneath and a white "signal" spot at each joint.
    s.can("walk")
    w = s.wave() if s.act == "walk" else 0
    body, dark, under = "#7a6a5c", "#3e342e", "#e0402a"
    for i, y in enumerate((17, 20, 23)):
        d = w * 1.2 * (1 if i % 2 else -1)
        s.path([(13, y), (8, y + 2 + d), (6, y + 5 + d)], 0.6, dark, shade=False)
    s.poly([(29, 20), (33, 16), (34, 21), (33, 26)], body)
    m = s.path([(14, 20), (20, 20), (26, 20), (30, 21)], (4, 2.6), body)
    for x in (19, 22, 25, 28):
        s.paint(s.m_line(x, 16, x, 25), dark, within=m)
    s.path([(10, 18), (7, 13)], 1.1, body)
    s.ellipse(5.5, 9, 3.4, 2.4, body, rot=-60, edge=True)
    s.paint(s.m_ellipse(6.5, 10, 1.4, 2, rot=-60), under, within=s.last)
    s.px([(7, 13), (8, 13)], WHITE)
    s.path([(10, 22), (6, 25)], 1.1, body)
    s.ellipse(4, 27, 3.2, 2.2, body, rot=30, edge=True)
    s.paint(s.m_ellipse(4, 28, 2, 1, rot=30), under, within=s.last)
    s.px([(6, 25)], WHITE)
    s.ellipse(12, 20, 5.5, 4.5, body, edge=True)
    s.paint(s.m_px([(12, 18), (14, 19), (11, 22)]), "#8a8aa0", within=s.last)
    s.line(9, 17, 4, 13, dark)
    s.line(8, 18, 2, 16, dark)
    s.eye(9, 18)
    s.blush(10, 21)
