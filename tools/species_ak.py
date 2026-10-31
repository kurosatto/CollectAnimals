"""Sprites for the Alaska species (and a few stragglers from other states) that aren't on an
earlier state's list."""
from __future__ import annotations

import math

import numpy as np

from archetypes import (BLACK, EYE, S, WHITE, _far_wing, _ripples, _wing_beat, back_stripes, beetle_top, bird,
                        butterfly, critter, dolphin, duck, fish, flecks, frog, jelly, lizard, pinniped, quad,
                        sea_turtle, sprite, star, wader)
from pixel import _XS, _YS, mix
from species_tx import _segmented


# --------------------------------------------------------------------------- mammals
@sprite("brown_bear")
def _(s):
    # Big and golden-brown with the shoulder hump; paler tips on the fur.
    def grizzle(s, b):
        bx, by, brx, bry = b["body"]
        s.paint(s.m_ellipse(bx - 3.5, by - bry + 1.5, 4.5, 2.2), "#b8875a")
    quad(s, "#7a5232", "#c89a6a", build="bear", ears="round", ear_in="#4a3020", tail="none",
         muzzle="#c49a6c", nose="#1d1418", belly=False, eye_col="#120c10", markings=grizzle)


@sprite("steller_sea_lion")
def _(s):
    # The biggest sea lion: golden-tan with a thick neck and tiny ears.
    pinniped(s, "#c8985a", "#e0bc84", ears=True, belly=False, flipper="#6a4a30")


@sprite("caribou")
def _(s):
    # Brown with a creamy white neck mane and big swept-back antlers.
    def antlers(s, b):
        hx, hy = b["head"][:2]
        c = "#e0d0aa"
        for dx, col in ((1.5, mix(c, "#1a1420", 0.25)), (0, c)):
            x, y = hx + 1 + dx, hy - 2.5
            s.path([(x, y), (x + 3, y - 4), (x + 4, y - 8), (x + 2, y - 11)], 0.7, col, shade=False)
            s.path([(x + 3, y - 4), (x + 6, y - 6)], 0.55, col, shade=False)
            s.path([(x + 4, y - 8), (x + 7, y - 10)], 0.55, col, shade=False)
            s.path([(x + 0.5, y - 1), (x - 2.5, y - 3)], 0.55, col, shade=False)

    def mane(s, b):
        (nx0, ny0), (nx1, ny1), nr = b["neck"]
        s.paint(s.m_path([(nx0, ny0), (nx1, ny1)], nr + 0.3), "#efe6d2")
    quad(s, "#7a5a40", "#efe6d2", build="deer", ears="side", ear_in="#c8a080", tail="cotton", tail_col=WHITE,
         head="#6a4a34", muzzle="#8a6a50", legs="#5a4030", feet="#efe6d2", nose="#2b2226", behind=antlers,
         markings=mane)


@sprite("arctic_ground_squirrel")
def _(s):
    # Tawny-orange face, gray-brown back sprinkled with white spots.
    critter(s, "#9a7a5a", "#e8c8a0", build="ground", ear_in="#c8906a", tail="long", tail_col="#8a6a4a",
            head="#c08050", markings=lambda s, g: flecks(s, g["body"] & s.m_ellipse(g["bx"], g["by"] - 1.5, g["brx"], 2.5),
                                                        "#f0e6d6", every=4))


@sprite("snowshoe_hare")
def _(s):
    # Winter white, with black-tipped ears and big snowshoe feet.
    critter(s, "#f4f2ee", "#ffffff", build="hare", ears="long", ear_in="#efb6b0", ear_tip=BLACK, tail="cotton",
            tail_col=WHITE, nose="#e08a96", feet="#e2e0dc")


@sprite("orca")
def _(s):
    # Black and white: white eye patch, white belly and a tall dorsal fin.
    dolphin(s, "#1e1c24", WHITE)
    s.poly([(14, 12), (16, 1), (20, 12)], "#1e1c24")
    s.paint(s.m_ellipse(9.5, 14.5, 2.6, 1.3, rot=-10), WHITE)
    s.paint(s.m_ellipse(20, 15, 2, 1.2), "#a8a8b4")
    s.paint(s.m_ellipse(18, 20.5, 4, 1.8), WHITE)
    s.eye(7, 15)


@sprite("mountain_goat")
def _(s):
    # Shaggy white with short black horns and a beard.
    def horns(s, b):
        hx, hy = b["head"][:2]
        for dx, col in ((1.5, "#3a3436"), (0, "#1e1a1e")):
            s.path([(hx + dx, hy - 2.5), (hx + 1 + dx, hy - 6), (hx + 3 + dx, hy - 7.5)], (0.9, 0.5), col, shade=False)

    def beard(s, b):
        hx, hy = b["head"][:2]
        s.path([(hx - 2, hy + 3), (hx - 2.5, hy + 6)], (1.2, 0.6), "#f4f2ea")
        bx, by, brx, bry = b["body"]
        s.ellipse(bx - 4, by - bry + 1.5, 4, 2.2, "#f4f2ea")
    quad(s, "#eeeae0", "#f8f6ee", build="sheep", ears="point", ear_in="#d8c8b8", tail="short", muzzle="#f8f6ee",
         nose="#3a3438", feet="#2b2630", markings=beard, front=horns)


@sprite("hoary_marmot")
def _(s):
    # Silver-gray with a black and white face and dark feet.
    def mask(s, g):
        s.paint(s.m_ellipse(g["hx"], g["hy"] - 0.6, g["hrx"] + 3, 1.4), "#2b2630", within=g["head_m"])
    critter(s, "#b8b4ae", "#efece6", build="marmot", ear_in="#6a6460", tail="short", tail_col="#7a5a3e",
            muzzle=WHITE, head="#d0ccc4", feet="#2b2630", eye_col="#120c10", face=mask,
            markings=lambda s, g: back_stripes(s, g, ["#8a8680"], top=0.4, width=1.6))


@sprite("thinhorn_sheep")
def _(s):
    # Dall's sheep: all white with curling amber horns.
    def horns(s, b):
        hx, hy = b["head"][:2]
        x, y = hx + 1.5, hy - 2.5
        s.path([(x - 1, y), (x + 2.5, y - 1.5), (x + 5, y + 0.5), (x + 5, y + 4), (x + 2.5, y + 5.5), (x + 0.5, y + 4)],
               (1.6, 0.7), "#e0b870", edge=True)
        s.paint(s.m_path([(x + 2.5, y - 0.6), (x + 4.2, y + 1), (x + 4, y + 3.5)], 0.4), "#b8904a")
    quad(s, "#f2eee4", "#faf8f2", build="sheep", ears="small", ear_in="#e0c8b8", tail="cotton",
         tail_col=WHITE, muzzle="#faf8f2", nose="#a89890", feet="#c8b8a0", front=horns)


@sprite("muskox")
def _(s):
    # A shaggy dark-brown skirt of fur, a pale saddle and horns that hook down.
    def skirt(s, b):
        bx, by, brx, bry = b["body"]
        s.poly([(bx - brx - 1, by), (bx + brx, by), (bx + brx - 1, 28), (bx - brx + 2, 28)], "#3a2a22")

    def horns(s, b):
        hx, hy = b["head"][:2]
        s.ellipse(hx + 0.5, hy - 3.2, 3.5, 1.6, "#e8dcc4")
        s.path([(hx - 2.5, hy - 3), (hx - 4, hy), (hx - 2.5, hy + 2)], (1.1, 0.6), "#d8c8a8", shade=False)
    quad(s, "#4a362a", "#4a362a", build="bear", ears="small", ear_in="#3a2a22", tail="none", head="#4a362a",
         muzzle="#6a5444", nose="#1d1418", legs="#5a4a3a", feet="#e8dcc4", belly=False, behind=skirt,
         front=horns)
    s.paint(s.m_ellipse(20, 14.5, 4, 1.5), "#b89a7a")


# --------------------------------------------------------------------------- gulls and terns
def _gull(s, mantle, *, tips=BLACK, spots=True, bill="#f0d040", legs="#f0d040", big=False, eye_col=EYE,
          head=WHITE, bill_spot=None):
    def wing(s, m):
        s.paint(s.m_poly([(23, 15), (27, 14), (27, 19), (23, 19)]), tips, within=m)
        if spots:
            s.paint(s.m_px([(25, 16)]), WHITE, within=m)
    bird(s, WHITE, WHITE, head=head, wing=mantle, tail_col=WHITE, beak="crow" if big else "cone", beak_col=bill,
         legs=legs, tail="short", wing_mark=wing, big=big, eye_col=eye_col)
    if bill_spot:
        s.px([(3, 13)], bill_spot)


@sprite("short_billed_gull")
def _(s):
    # Small and gentle-faced: a short plain yellow bill and a dark eye.
    _gull(s, "#9aa2b0", bill="#f0e060", legs="#e8e060")


@sprite("glaucous_winged_gull")
def _(s):
    # Big gull whose wingtips are the same soft gray as its back.
    _gull(s, "#a8b0bc", tips="#8a92a0", bill="#f0c830", legs="#f0a8a8", big=True, bill_spot="#e0403a")


@sprite("glaucous_gull")
def _(s):
    # The palest gull of all: pale silver back and pure white wingtips.
    _gull(s, "#d4dae2", tips=WHITE, spots=False, bill="#f0d040", legs="#f0b0b0", big=True, bill_spot="#e0403a",
          eye_col="#d8c040")


@sprite("black_legged_kittiwake")
def _(s):
    # Ink-dipped black wingtips, a plain yellow bill and short black legs.
    _gull(s, "#9aa4b4", spots=False, bill="#f0e040", legs=BLACK)


@sprite("bonapartes_gull")
def _(s):
    # Small, with a black hood, thin black bill and orange-red legs.
    def wing(s, m):
        s.paint(s.m_poly([(24, 15), (27, 14), (27, 19), (24, 19)]), BLACK, within=m)
        s.paint(s.m_line(16, 17, 23, 16), WHITE, within=m)

    def hood(s):
        s.paint(s.m_ellipse(10, 11, 6.5, 6) & ~s.m_ellipse(14, 17, 4, 2.5), BLACK, within=s.last)
    bird(s, WHITE, WHITE, head=WHITE, wing="#b0b8c4", tail_col=WHITE, beak="thin", beak_col=BLACK,
         legs="#f0603a", tail="short", wing_mark=wing, face=hood)
    s.px([(8, 9), (9, 9)], WHITE)
    s.eye(8, 10, shine=None)


@sprite("arctic_tern")
def _(s):
    # Black cap, blood-red bill and legs, long forked tail streamers.
    def face(s):
        s.paint(s.m_ellipse(13, 7, 5.5, 3.2), BLACK, within=s.last)
    bird(s, WHITE, "#dfe2e8", head=WHITE, wing="#c0c6d0", tail_col=WHITE, beak="long", beak_col="#e0302a",
         legs="#e0302a", tail="long", face=face)
    s.poly([(24, 13), (32, 3), (27, 13)], WHITE)
    s.eye(8, 10)


# --------------------------------------------------------------------------- seabirds
@sprite("common_murre")
def _(s):
    # Like a little penguin: chocolate-black head and back, white belly, pointed bill.
    bird(s, "#2e2628", WHITE, head="#2e2628", wing="#262022", tail_col="#262022", beak="long", beak_col=BLACK,
         legs="#2b2630", tail="short", big=True)
    s.paint(s.m_ellipse(12, 19, 4, 1.8), "#2e2628")
    s.eye(8, 10, color="#000000")


@sprite("tufted_puffin")
def _(s):
    # Black with a white face, a big orange bill and golden tufts.
    def face(s):
        s.paint(s.m_ellipse(9.5, 11.5, 4.2, 3.6), WHITE, within=s.last)
    bird(s, "#25202a", "#2e2a34", head="#25202a", wing="#1e1a22", tail_col="#1e1a22", beak="cone",
         beak_col=BLACK, legs="#f0702a", tail="short", face=face, big=True)
    s.path([(12, 8), (17, 8), (22, 11)], (1.2, 0.6), "#f0d050", shade=False)
    s.poly([(6, 8), (0, 11.5), (1, 13.5), (6, 15)], "#f06a2a")
    s.paint(s.m_line(6, 8, 6, 15), "#f0d050")
    s.eye(8, 10)


@sprite("horned_puffin")
def _(s):
    # White face and belly, black collar, and a yellow bill with a red tip.
    def face(s):
        s.paint(s.m_ellipse(9.5, 11, 4.4, 4.2), WHITE, within=s.last)
        s.paint(s.m_px([(8, 7), (8, 8)]), BLACK, within=s.last)
    bird(s, "#25202a", WHITE, head="#25202a", wing="#1e1a22", tail_col="#1e1a22", beak="cone",
         beak_col=BLACK, legs="#f0702a", tail="short", face=face, big=True)
    s.paint(s.m_ellipse(13, 18.5, 5, 1.8), "#25202a")
    s.poly([(6, 8), (0, 11.5), (1, 13.5), (6, 15)], "#f0d040")
    s.paint(s.m_poly([(3, 10), (0, 11.5), (1, 13.5), (3, 14)]), "#e0402a")
    s.eye(8, 10)


@sprite("pigeon_guillemot")
def _(s):
    # Sooty black with a big white wing patch and bright red feet.
    def wing(s, m):
        s.paint(s.m_ellipse(19, 18, 4, 2.2, rot=-15), WHITE, within=m)
        s.paint(s.m_line(17, 18, 22, 17), "#2b2630", within=m)
    bird(s, "#25222a", "#2e2a34", head="#25222a", wing="#1e1c22", tail_col="#1e1c22", beak="long",
         beak_col=BLACK, legs="#e0302a", tail="short", wing_mark=wing)
    s.px([(16, 29), (17, 29), (12, 29), (13, 29)], "#e0302a")


@sprite("marbled_murrelet")
def _(s):
    # A tiny chunky seabird in mottled brown "marbled" summer plumage.
    def mottle(s, m):
        s.paint(s.m_px([(10, 21), (13, 22), (16, 21), (11, 24), (15, 24), (13, 26), (17, 23)]), "#6a4a34", within=m)
    bird(s, "#6a4e3a", "#d8c4a8", head="#5a4232", wing="#5e4434", tail_col="#4a3628", beak="thin",
         beak_col=BLACK, legs="#c8a090", tail="short", belly_mark=mottle,
         wing_mark=lambda s, m: s.paint(s.m_px([(18, 18), (21, 17), (23, 19), (20, 20)]), "#a08060", within=m))


@sprite("pelagic_cormorant")
def _(s):
    # Slim and glossy green-black with a thin bill and a red face patch.
    duck(s, "#1e2428", "#242c30", "#1e2428", bill="#2b2630", ring=None, speculum="#2a3a34", tail_col="#14181a")
    s.ellipse(3, 12.8, 3.6, 1, "#2b2630")
    s.px([(5, 13), (6, 13), (6, 14)], "#d8302a")
    s.paint(s.m_ellipse(25, 24, 1.6, 1.2), WHITE)
    s.px([(11, 6), (12, 5)], "#1e2428")
    s.eye(7, 10, color="#2a8a6a")


# --------------------------------------------------------------------------- loons and grebes
def _checks(s, x0=14, x1=26, y0=18, y1=23):
    s.paint(s.m_px([(x, y) for y in range(y0, y1 + 1, 2) for x in range(x0 + (y // 2) % 2, x1 + 1, 2)]), WHITE,
            within=s.m_ellipse(17, 23, 11, 6.5) | s.m_ellipse(20, 21, 7, 3.5, rot=-8))


@sprite("common_loon")
def _(s):
    # Black head with a striped white necklace, checkerboard back and red eye.
    duck(s, "#1e2228", "#f2f2f0", "#1a2a24", bill=BLACK, ring=None, speculum="#1e2228", tail_col="#1e2228")
    s.poly([(5, 11.5), (-2, 13), (5, 14.5)], BLACK)
    _checks(s)
    for x in (8, 10, 12):
        s.px([(x, 16), (x + 1, 17)], WHITE)
    s.px([(7, 10), (8, 10), (7, 11), (8, 11)], "#d8202a")


@sprite("pacific_loon")
def _(s):
    # Soft silver-gray head, dark throat and a checkered black back.
    duck(s, "#1e2228", "#f2f2f0", "#b8bcc4", bill=BLACK, ring=None, speculum="#1e2228", tail_col="#1e2228")
    s.poly([(5, 11.5), (-1, 13), (5, 14)], BLACK)
    s.paint(s.m_ellipse(10, 16.5, 3, 1.4), "#3a2a4a")
    s.px([(13, 15), (13, 17)], WHITE)
    _checks(s, 16, 26, 19, 23)
    s.px([(7, 10), (8, 10), (7, 11), (8, 11)], "#c8202a")


@sprite("red_necked_grebe")
def _(s):
    # Rusty red neck, pale gray cheeks, a black cap and a yellow-based bill.
    duck(s, "#4a4a50", "#b8502a", "#2b2630", bill="#2b2630", ring=None, speculum="#4a4a50", tail_col="#4a4a50")
    s.paint(s.m_ellipse(9, 13.5, 4.5, 2.6), "#d8dadc")
    s.paint(s.m_ellipse(12, 16.5, 4, 1.4), "#b8502a")
    s.poly([(5, 12), (-1, 13.2), (5, 14.5)], "#2b2630")
    s.px([(4, 13), (5, 13), (4, 14)], "#f0c830")
    s.eye(7, 10, color="#a01818")


# --------------------------------------------------------------------------- ducks
@sprite("american_wigeon")
def _(s):
    # White forehead, a green swoosh behind the eye and pinky-brown sides.
    duck(s, "#b88470", "#c8907a", "#a8a8a8", bill="#a8b8d0", ring=None, speculum="#2a7a4a", tail_col=BLACK)
    s.paint(s.m_ellipse(11, 6.5, 3, 1.6), WHITE)
    s.paint(s.m_poly([(8, 9), (15, 9), (16, 13), (10, 12)]), "#2a7a4a")
    s.px([(0, 13), (1, 13)], BLACK)
    s.paint(s.m_ellipse(25, 23, 2, 2), WHITE)
    s.eye(7, 10)


@sprite("harlequin_duck")
def _(s):
    # Slate blue with chestnut sides and bold white "clown" stripes.
    duck(s, "#3e4a6a", "#3e4a6a", "#34405e", bill="#5a6070", ring=None, speculum="#4a3a8a", tail_col="#2a3048")
    s.paint(s.m_ellipse(21, 25.5, 6, 2.2), "#b85a30")
    s.paint(s.m_line(13, 7, 13, 9) | s.m_ellipse(12, 6.5, 3.5, 0.9), "#b85a30")
    s.paint(s.m_ellipse(5.8, 10, 1, 1.4) | s.m_px([(12, 12), (12, 13)]), WHITE)
    s.paint(s.m_line(10, 17, 13, 21) | s.m_line(13, 17, 15, 21) | s.m_line(18, 19, 25, 19), WHITE)
    s.eye(7, 10)


@sprite("green_winged_teal")
def _(s):
    # Tiny gray duck: chestnut head, green eye patch and a white bar on the side.
    duck(s, "#a8a8ae", "#e8d8b8", "#a8482a", bill="#2b2630", ring=None, speculum="#2a8a5a", tail_col="#d8c890")
    s.paint(s.m_poly([(7, 9), (14, 9), (16, 13), (10, 13)]), "#2a7a4a")
    s.paint(s.m_line(13, 19, 13, 25) | s.m_line(14, 19, 14, 25), WHITE)
    s.px([(9, 22), (11, 24), (8, 25)], "#5a4a3a")
    s.eye(7, 10)


@sprite("northern_pintail")
def _(s):
    # Chocolate head, a white stripe up the neck and a long pin-like tail.
    duck(s, "#b0b0b6", WHITE, "#5a3e2e", bill="#5a6070", ring=None, speculum="#3a7a5a", tail_col=BLACK)
    s.poly([(25, 20), (33, 9), (31, 13), (28, 21)], BLACK)
    s.paint(s.m_path([(13, 16), (12, 12), (13.5, 8)], 0.6), WHITE)
    s.px([(2, 13), (1, 13), (2, 12)], "#a8b8c8")
    s.eye(7, 10)


@sprite("barrows_goldeneye")
def _(s):
    # Purple-black head with a white crescent, golden eye, black back with white spots.
    duck(s, "#24222a", WHITE, "#2a2240", bill=BLACK, ring=None, speculum=WHITE, tail_col="#24222a")
    s.paint(s.m_ellipse(17, 25.5, 9, 2.4), WHITE)
    s.paint(s.m_px([(17, 20), (19, 20), (21, 20), (23, 20), (18, 22), (20, 22), (22, 22)]), WHITE)
    s.paint(s.m_ellipse(5.5, 11.5, 1.2, 2.2, rot=10), WHITE)
    s.px([(8, 10), (9, 10), (8, 11), (9, 11)], "#f0c830")
    s.px([(9, 11)], EYE)


# --------------------------------------------------------------------------- land birds
@sprite("black_billed_magpie")
def _(s):
    # Black and white with a very long glossy blue-green tail.
    def wing(s, m):
        s.paint(s.m_ellipse(19, 18, 4, 2, rot=-15), WHITE, within=m)
        s.paint(s.m_line(20, 21, 25, 19), "#3a5ab0", within=m)
    bird(s, "#1f1c26", WHITE, head="#1f1c26", wing="#24202c", tail_col="#2a5a6a", beak="crow",
         beak_col=BLACK, legs="#2a2630", tail="long", wing_mark=wing)
    s.poly([(28, 7), (33, 2), (32, 6)], "#2a5a6a")
    s.paint(s.m_ellipse(11, 20, 4, 2.3), "#1f1c26")


@sprite("willow_ptarmigan")
def _(s):
    # The state bird in spring: chestnut head, white wings and belly, red eyebrow combs.
    def face(s):
        s.paint(s.m_line(6, 8, 10, 8) | s.m_line(7, 7, 9, 7), "#e0302a", within=s.last)
    bird(s, "#9a5a32", WHITE, head="#a8582a", wing=WHITE, tail_col=BLACK, beak="cone", beak_col=BLACK,
         legs=WHITE, tail="short", face=face)
    s.paint(s.m_ellipse(13, 18, 5, 2.2), "#a8582a")
    s.ellipse(15, 28.5, 3.5, 1.6, WHITE)
    s.eye(8, 10)


@sprite("spruce_grouse")
def _(s):
    # Dark gray with a black throat, white-spotted sides and a red eyebrow.
    def face(s):
        s.paint(s.m_ellipse(9, 15, 4, 2.5), BLACK, within=s.last)
        s.paint(s.m_line(6, 7, 10, 7) | s.m_line(7, 8, 9, 8), "#e0302a", within=s.last)

    def spots(s, m):
        s.paint(s.m_ellipse(13, 22, 5, 4), BLACK, within=m)
        s.paint(s.m_px([(10, 23), (12, 25), (15, 24), (14, 21), (11, 21), (16, 26)]), WHITE, within=m)
    bird(s, "#5a5a5e", "#2b2630", head="#4a4a50", wing="#5e5a52", tail_col=BLACK, beak="cone", beak_col=BLACK,
         legs="#8a8a8a", tail="fan", face=face, belly_mark=spots, big=True)
    s.px([(28, 11), (29, 13), (30, 15)], "#c8743a")
    s.eye(8, 10)


@sprite("redpoll")
def _(s):
    # A streaky little finch with a red cap, black chin and pink breast.
    def streaks(s, m):
        s.paint(s.m_ellipse(11, 20, 4, 2.2), "#f08aa0", within=m)
        s.paint(s.m_px([(15, 24), (17, 22), (12, 25), (16, 26)]), "#7a5a48", within=m)

    def face(s):
        s.paint(s.m_ellipse(9, 7, 3, 1.6), "#e0283a", within=s.last)
        s.paint(s.m_px([(5, 14), (6, 14), (6, 15)]), BLACK, within=s.last)
    bird(s, "#9a7e66", "#f4ece4", head="#a89078", wing="#7a5e48", tail_col="#5a4434", beak="cone",
         beak_col="#f0c830", legs="#3a3434", tail="mid", belly_mark=streaks, face=face,
         wing_mark=lambda s, m: s.paint(s.m_line(16, 19, 23, 17) | s.m_px([(19, 16), (22, 15)]), WHITE, within=m))


@sprite("canada_jay")
def _(s):
    # Fluffy gray "camp robber" with a white face and a dark cap at the back.
    def face(s):
        s.paint(s.m_ellipse(14, 9, 4, 4.5), "#3a3a40", within=s.last)
    bird(s, "#8a8c92", "#d8d8da", head=WHITE, wing="#7a7c84", tail_col="#6a6c74", beak="cone",
         beak_col=BLACK, legs="#2b2630", tail="long", face=face)
    s.eye(8, 10)


@sprite("savannah_sparrow")
def _(s):
    # A streaky brown sparrow with a little yellow eyebrow.
    def streaks(s, m):
        s.paint(s.m_px([(10, 21), (12, 20), (14, 22), (11, 23), (13, 24), (15, 20), (16, 23)]), "#6a4a34", within=m)

    def face(s):
        s.paint(s.m_line(5, 8, 10, 8), "#f0d040", within=s.last)
        s.paint(s.m_line(10, 9, 14, 9), "#e8e0d0", within=s.last)
        s.paint(s.m_line(13, 5, 16, 5), "#5a3a26", within=s.last)
    bird(s, "#9a7a58", "#f2ece0", head="#8a6a4a", wing="#8a6a4e", tail_col="#6a5240", beak="cone",
         beak_col="#d8b0a0", legs="#e0b0a0", tail="short", belly_mark=streaks, face=face,
         wing_mark=lambda s, m: s.paint(s.m_line(16, 18, 23, 16) | s.m_px([(18, 20), (21, 19)]), "#4a3220", within=m))


@sprite("greater_yellowlegs")
def _(s):
    # Speckled gray shorebird on long bright yellow legs.
    wader(s, "#8a8c90", neck="#c8c8cc", head="#b8b8bc", beak="#2b2630", legs="#f0c830", wing="#6a6c70")
    s.paint(s.m_px([(17, 13), (20, 12), (23, 13), (25, 15), (19, 15), (22, 16)]), WHITE,
            within=s.m_ellipse(20, 15, 7, 5))
    s.paint(s.m_px([(12, 8), (13, 10), (11, 7)]), "#6a6c70")


@sprite("red_necked_phalarope")
def _(s):
    # Slate head, white throat, a rusty-red neck and a needle-thin bill.
    def face(s):
        s.paint(s.m_ellipse(9, 14.5, 3, 1.8), WHITE, within=s.last)
        s.paint(s.m_ellipse(14, 15, 3, 3.5), "#c8582a", within=s.last)

    def wing(s, m):
        s.paint(s.m_line(16, 17, 24, 15) | s.m_line(17, 20, 25, 18), "#e8b870", within=m)
    bird(s, "#4a4c56", WHITE, head="#4a4c56", wing="#3a3c46", tail_col="#3a3c46", beak="thin",
         beak_col=BLACK, legs="#5a5a62", tail="short", face=face, wing_mark=wing)
    s.paint(s.m_ellipse(12, 18.5, 4, 2), "#c8582a")
    s.px([(9, 9)], WHITE)


@sprite("american_dipper")
def _(s):
    # Chunky slate-gray stream bird with a stubby cocked tail and white eyelids.
    bird(s, "#6a6c74", "#7a7c84", head="#7a6a62", wing="#5e6068", tail_col="#5a5c64", beak="thin",
         beak_col="#2b2630", legs="#e0b0b0", tail="short", big=True)
    s.px([(8, 9), (9, 9)], WHITE)


@sprite("orange_crowned_warbler")
def _(s):
    # Plain olive-yellow with a faint dark eyeline (the orange crown is usually hidden).
    def face(s):
        s.paint(s.m_line(5, 10, 12, 10), "#7a7a3a", within=s.last)
        s.paint(s.m_px([(12, 6), (13, 6)]), "#e88a2a", within=s.last)
    bird(s, "#9aa040", "#e0dc60", head="#a4a848", wing="#8a903a", tail_col="#7a8034", beak="thin",
         beak_col="#4a4a3a", legs="#6a6a5a", tail="mid", face=face)
    s.px([(8, 12), (9, 12)], "#f0ec90")
    s.eye(8, 10)


@sprite("northern_yellow_warbler")
def _(s):
    # Bright egg-yolk yellow with thin red streaks on the chest.
    def streaks(s, m):
        s.paint(s.m_px([(10, 20), (12, 21), (14, 20), (11, 23), (13, 24), (15, 22)]), "#d8502a", within=m)
    bird(s, "#e8d030", "#f8e848", head="#f0dc3a", wing="#c8b030", tail_col="#c0a830", beak="thin",
         beak_col="#4a4a3a", legs="#c8a070", tail="mid", belly_mark=streaks,
         wing_mark=lambda s, m: s.paint(s.m_line(16, 18, 23, 16), "#f8ec80", within=m))


@sprite("varied_thrush")
def _(s):
    # Orange eyebrow, throat and wing bars, with a black band across the chest.
    def face(s):
        s.paint(s.m_line(9, 8, 15, 9), "#f0882a", within=s.last)
        s.paint(s.m_line(5, 11, 13, 12) | s.m_line(6, 12, 12, 13), "#2b2a34", within=s.last)
        s.paint(s.m_ellipse(9, 15.5, 3, 1.5), "#f0882a", within=s.last)

    def band(s, m):
        s.paint(s.m_ellipse(11, 19.5, 4.5, 1.4), "#2b2a34", within=m)
    bird(s, "#4e5a6a", "#f0882a", head="#4e5a6a", wing="#44505e", tail_col="#3a4450", beak="thin",
         beak_col="#2b2630", legs="#d8a080", tail="mid", face=face, belly_mark=band,
         wing_mark=lambda s, m: s.paint(s.m_line(16, 18, 23, 16) | s.m_line(17, 21, 24, 19), "#f0882a", within=m))


@sprite("lapland_longspur")
def _(s):
    # Black face and bib, white stripe behind the eye and a chestnut nape.
    def face(s):
        s.paint(s.m_ellipse(9, 13, 5, 4.5), BLACK, within=s.last)
        s.paint(s.m_path([(9, 9), (13, 11), (12, 16)], 0.6), WHITE, within=s.last)
        s.paint(s.m_ellipse(16, 11, 2.4, 3), "#b85a2a", within=s.last)
    bird(s, "#8a6a4a", WHITE, head="#5a4a3a", wing="#7a5a3e", tail_col="#5a4430", beak="cone",
         beak_col="#f0c830", legs="#3a3434", tail="mid", face=face,
         belly_mark=lambda s, m: s.paint(s.m_ellipse(11, 19, 4.5, 2) | s.m_px([(17, 23), (18, 25)]), BLACK, within=m),
         wing_mark=lambda s, m: s.paint(s.m_px([(18, 17), (21, 18), (23, 16), (19, 20)]), "#2b2630", within=m))
    s.eye(8, 10, color="#000000")


# --------------------------------------------------------------------------- amphibians and reptiles
@sprite("western_toad")
def _(s):
    # Warty gray-green toad with a pale stripe down its back.
    frog(s, "#7a8060", "#ecead8", build="toad", spots=9, dorsal="#ece6c8", parotoid="#9a8a5a", warts="#c88a4a")


@sprite("columbia_spotted_frog")
def _(s):
    # Brown with black spots, a pale jaw stripe and a salmon-orange belly.
    frog(s, "#8a6a40", "#f0905a", tympanum="#7a5a34", spots=9, spot_big=True, spot_col="#2e2218", lip="#e8d0a0")


@sprite("pacific_chorus_frog")
def _(s):
    # A small bright green treefrog with a black mask stripe through each eye.
    frog(s, "#6ab84a", "#f2f0dc", build="tree", pads=True, mask="#2b2a26", crown="#3a7a2a")


@sprite("northern_red_legged_frog")
def _(s):
    # Brown back with a few dark flecks and red-washed legs and belly.
    frog(s, "#9a7048", "#f0b090", tympanum="#7a5434", spots=3, thigh="#d8503a", lip="#e8c8a0")


@sprite("long_toed_salamander")
def _(s):
    # Dark with a wavy yellow-green stripe down the back and white flecks.
    def stripe(s, m):
        s.paint(s.m_path([(8, 19.5), (12, 19), (16, 20), (20, 19), (22, 20)], 0.8), "#c8d04a", within=m)
        s.paint(s.m_px([(10, 23), (14, 24), (18, 23)]), "#e8e8f0", within=m)
    lizard(s, "#2a2a30", "#4a4a54", head="#2a2a30", throat="#4a4a54", pattern=stripe, smooth=True, eye_big=True,
           legs="#26262c", tail_col="#2a2a30")
    s.paint(s.m_path([(21, 21), (26, 23.5), (30, 20)], 0.5), "#c8d04a")
    s.paint(s.m_path([(4, 15.5), (9, 16)], 0.5), "#c8d04a")
    s.eye(5, 16, size=3)
    s.px([(5, 16)], WHITE)


@sprite("northwestern_salamander")
def _(s):
    # Plump chocolate-brown with big bumpy glands behind the eyes.
    lizard(s, "#6a4a34", "#9a7a5e", head="#6a4a34", smooth=True, eye_big=True, legs="#5a3e2a", wide=True,
           tail_pts=[(20, 22), (26, 25), (31, 23), (31, 17)])
    s.ellipse(11, 16.5, 2.4, 1.8, "#7e5a40")
    s.paint(s.m_px([(10, 16), (12, 17)]), "#a08060")
    s.paint(s.m_line(25, 20, 30, 18), "#8a6a4e")


@sprite("green_sea_turtle")
def _(s):
    sea_turtle(s, "#6a5a3a", "#8a9a5a", scutes="#8a7448")
    s.paint(s.m_px([(12, 14), (17, 12), (22, 14), (14, 18), (20, 18)]), "#a89060")


# --------------------------------------------------------------------------- fish
@sprite("pink_salmon")
def _(s):
    # A spawning "humpy": big hump, pale pink sides and spots all over the tail.
    def pat(s, m):
        s.paint(s.m_ellipse(13, 18, 10, 2), "#f0a8a8", within=m)
        s.paint(s.m_px([(14, 11), (18, 12), (22, 13), (16, 14), (20, 14), (24, 15)]), "#2b2a30", within=m)
    s.ellipse(15, 11, 8, 4.5, "#5a6a6a")
    fish(s, "#6a7a7a", "#f0e8e8", fin="#4a5656", pattern=pat)
    s.px([(26, 11), (28, 13), (27, 19), (29, 21), (28, 16)], "#2b2a30")
    s.path([(3, 18), (2, 20)], 0.6, "#4a5656")


@sprite("sockeye_salmon")
def _(s):
    # Spawning colours: bright red body, green head and a hooked jaw.
    def pat(s, m):
        s.paint(s.m_ellipse(5, 16.5, 5.5, 8), "#4a7a4a", within=m)
    s.ellipse(14, 10.5, 6, 3.5, "#d8302a")
    fish(s, "#d8302a", "#e85040", fin="#b02020", pattern=pat)
    s.path([(3, 18), (1.5, 20.5), (3, 21)], 0.7, "#e8e0d0")
    s.eye(6, 14, size=2, color="#1d1428")


@sprite("eastern_blacknose_dace")
def _(s):
    # A little minnow with one black stripe from its nose to its tail.
    def pat(s, m):
        s.paint(s.m_path([(2, 16), (15, 16.5), (26, 16)], 0.9), "#2b2630", within=m)
        s.paint(s.m_px([(10, 12), (14, 11), (18, 12), (22, 13), (16, 13)]), "#4a4a3a", within=m)
    fish(s, "#9a9a7a", "#f2eee0", fin="#b8a890", pattern=pat, slim=True)
    s.paint(s.m_line(1, 16, 4, 16), "#2b2630")


@sprite("orangethroat_darter")
def _(s):
    # Blue-green bars, an orange throat and an orange-edged back fin.
    def pat(s, m):
        for x in (12, 16, 20, 24):
            s.paint(s.m_line(x, 11, x, 20) | s.m_line(x + 1, 11, x + 1, 20), "#3a6a9a", within=m)
        s.paint(s.m_ellipse(8, 20, 4, 2), "#f08a2a", within=m)
    fish(s, "#b8a070", "#f0d8a8", fin="#4a7aa8", pattern=pat, slim=True)
    s.paint(s.m_line(11, 10, 20, 8), "#f08a2a")


# --------------------------------------------------------------------------- insects and other small animals
def _bumble(s, bands):
    """Side-view bumble bee; bands is a list of (x0, x1, colour) across the abdomen."""
    s.can("fly")
    up = not (s.act == "fly" and s.f % 2)
    s.ellipse(20, 8 if up else 11, 4.5, 6.5 if up else 4, "#e6f4fc", rot=25 if up else 70, shade=False, edge=True)
    s.ellipse(25, 11 if up else 13, 3.5, 5 if up else 3, "#d6ecfa", rot=40 if up else 80, shade=False, edge=True)
    m = s.ellipse(18, 19, 9, 7.5, "#2b2226")
    for x0, x1, c in bands:
        s.paint(s.m_poly([(x0, 8), (x1, 8), (x1, 30), (x0, 30)]), c, within=m)
    s.line(9, 25, 8, 29, "#2b2226")
    s.line(13, 25, 13, 29, "#2b2226")
    s.ellipse(8.5, 17, 5.5, 5.5, "#2b2226", edge=True)
    s.line(6, 12, 4, 6, "#2b2226")
    s.line(9, 12, 10, 6, "#2b2226")
    s.eye(5, 16, color="#11080f", shine="#ffffff")
    s.blush(5, 19, color="#ff8fa8")


@sprite("black_tailed_bumble_bee")
def _(s):
    # Yellow up front, a bright orange middle and a black tail end.
    _bumble(s, [(9, 17, "#f2c42a"), (17, 23, "#f07a2a")])


@sprite("yellow_fronted_bumble_bee")
def _(s):
    # A yellow fuzzy face and front, a black band, then a red-orange tail.
    _bumble(s, [(9, 15, "#f2c42a"), (19, 22, "#f2c42a"), (22, 30, "#d8502a")])
    s.paint(s.m_ellipse(7, 15, 3, 2.5), "#f2c42a")
    s.eye(5, 16, color="#11080f", shine="#ffffff")


@sprite("canadian_tiger_swallowtail")
def _(s):
    # A smaller northern cousin of the tiger swallowtail: yellow with black tiger stripes.
    S["western_tiger_swallowtail"](s)


@sprite("great_spangled_fritillary")
def _(s):
    # Tawny orange with black chevrons and spots, darker near the body.
    def pat(s, fm, hm):
        s.paint(s.m_px([(5, 6), (8, 7), (11, 9), (4, 10), (7, 11), (10, 12), (3, 13)]), BLACK, mirror=True, within=fm)
        s.paint(s.m_px([(6, 20), (8, 22), (10, 24), (5, 22), (12, 22)]), BLACK, mirror=True, within=hm)
        s.paint(s.m_ellipse(14, 15, 3, 5), "#8a4a1a", mirror=True, within=fm | hm)
        s.paint(s.m_line(4, 23, 8, 26), "#f0d8a0", mirror=True, within=hm)
    butterfly(s, "#e8862a", "#e08028", body="#5a3a1e", pattern=pat)


@sprite("milberts_tortoiseshell")
def _(s):
    # Dark brown wings with a fiery orange-to-yellow band and orange spots on the edge.
    def pat(s, fm, hm):
        band = s.m_poly([(3, 9), (6, 7), (9, 14), (9, 19), (6, 24), (4, 21), (5, 15)])
        s.paint(band, "#f08a2a", mirror=True, within=fm | hm)
        s.paint(s.m_poly([(3, 9), (5, 8), (6, 14), (5, 16), (3.5, 13)]), "#f0c040", mirror=True, within=fm)
        s.paint(s.m_px([(9, 5), (11, 7)]), "#f08a2a", mirror=True, within=fm)
        s.paint(s.m_px([(7, 26), (9, 27)]), "#6a8ae0", mirror=True, within=hm)
    butterfly(s, "#4a2e22", "#4a2e22", body="#3a241a", pattern=pat)


@sprite("zabulon_skipper")
def _(s):
    # A little golden-orange skipper with dark brown borders.
    def pat(s, fm, hm):
        s.paint(s.m_poly([(1.5, 6), (5, 3), (6, 5), (3, 14)]) | s.m_line(10, 10, 13, 12), "#5a3a1e",
                mirror=True, within=fm)
        s.paint(s.m_poly([(4, 18), (5, 23), (9, 27), (7, 20)]), "#5a3a1e", mirror=True, within=hm)
    butterfly(s, "#f0b030", "#f0b838", body="#6a4a24", pattern=pat)
    s.ellipse(16, 9.5, 3, 2.6, "#6a4a24")
    s.px([(14, 9), (17, 9)], WHITE)


@sprite("large_yellow_underwing")
def _(s):
    # Plain brown forewings over bright yellow hindwings with a black edge.
    def pat(s, fm, hm):
        s.paint(s.m_poly([(5, 17), (4, 22), (9, 27), (10, 24), (6, 21)]), BLACK, mirror=True, within=hm)
        s.paint(s.m_ellipse(9, 9, 1.4, 1.2) | s.m_ellipse(12, 12, 1, 1), "#4a3020", mirror=True, within=fm)
        s.paint(s.m_px([(3, 6), (4, 7)]), "#2a1a12", mirror=True, within=fm)
    butterfly(s, "#9a7048", "#f0c020", body="#6a4a30", pattern=pat)


@sprite("variable_carpet_moth")
def _(s):
    # Grayish-white moth with a dark wavy band across the forewings.
    def pat(s, fm, hm):
        s.paint(s.m_poly([(7, 4), (10, 6), (13, 13), (9, 15), (7, 11), (4, 13), (3, 10), (6, 8)]), "#5a4a44",
                mirror=True, within=fm)
        s.paint(s.m_line(3, 13, 14, 16), "#8a7a74", mirror=True, within=fm)
        s.paint(s.m_line(6, 19, 13, 19) | s.m_line(6, 22, 12, 22), "#a89a94", mirror=True, within=hm)
    butterfly(s, "#d8d4cc", "#e2ded6", body="#6a5e58", pattern=pat)


@sprite("virginia_ctenucha_moth")
def _(s):
    # Smoky blue-black wings, a metallic blue body and a bright orange head.
    def pat(s, fm, hm):
        s.paint(s.m_line(15, 11, 6, 6), "#4a4a5a", mirror=True, within=fm)
    butterfly(s, "#3a3a46", "#34343e", body="#3a6ae0", pattern=pat)
    s.ellipse(16, 9.5, 2.5, 2.2, "#f08a2a")
    s.px([(14, 9), (17, 9)], WHITE)
    s.path([(15, 8), (12, 3)], 0.6, "#2b2630", shade=False)
    s.path([(16, 8), (19, 3)], 0.6, "#2b2630", shade=False)


@sprite("spotted_tussock_moth")
def _(s):
    # The fuzzy caterpillar: black at both ends, yellow-orange tufts in the middle.
    pts = _segmented(s, 8, "#f0b030", "#1e1a1c", "#3a2a22", leg_len=1.2, spacing=2.8, r=2.8, antenna=0)
    for i, (x, y) in enumerate(pts):
        col = "#1e1a1c" if i < 2 or i > 5 else "#f0b030"
        s.ellipse(x, y - 1, 2.6, 2.6, col)
        s.px([(round(x), round(y - 4)), (round(x + 1), round(y - 4))], col)
        if 1 < i < 6:
            s.px([(round(x), round(y - 1))], "#1e1a1c")
    hx, hy = pts[0]
    s.ellipse(hx - 1, hy, 3.4, 3, "#1e1a1c", edge=True)
    s.eye(round(hx - 2), round(hy - 1))
    s.path([(pts[-1][0], pts[-1][1] - 3), (pts[-1][0] + 2, pts[-1][1] - 7)], 0.6, "#f4f0e8", shade=False)
    s.path([(pts[1][0], pts[1][1] - 3), (pts[1][0] - 1, pts[1][1] - 7)], 0.6, "#f4f0e8", shade=False)


@sprite("birch_shield_bug")
def _(s):
    # A shield-shaped bug, leaf green with rusty red shoulders and wingtips.
    s.can("walk")
    w = s.wave() if s.act == "walk" else 0
    for i, y in enumerate((15, 19, 23)):
        d = round(w * (1 if i % 2 else -1))
        s.line(9, y, 5, y + 3 + d, "#3a4a2a")
        s.line(22, y, 26, y + 3 - d, "#3a4a2a")
    s.line(14, 6, 11, 1, "#3a4a2a")
    s.line(17, 6, 20, 1, "#3a4a2a")
    s.ellipse(15.5, 7, 3, 2.4, "#6a9a3a", edge=True)
    m = s.poly([(6, 13), (9, 9), (22, 9), (25, 13), (23, 22), (15.5, 30), (8, 22)], "#7ab040", edge=True)
    s.paint(s.m_poly([(6, 13), (25, 13), (24, 16), (7, 16)]), "#b8603a", within=m)
    s.paint(s.m_poly([(8, 17), (12, 17), (12, 23), (9, 22)]) | s.m_poly([(23, 17), (19, 17), (19, 23), (22, 22)]),
            "#c06a40", within=m)
    s.paint(s.m_poly([(12, 16), (19, 16), (15.5, 25)]), "#5a9a30", within=m)
    s.paint(s.m_poly([(11, 25), (20, 25), (15.5, 30)]), "#5a3a2a", within=m)
    s.px([(13, 6), (18, 6)], EYE)
    s.px([(13, 6)], WHITE)
    s.blush(12, 9)
    s.blush(18, 9)


@sprite("pacific_banana_slug_ariolimax")
def _(s):
    # Banana yellow, often with dark spots, and two pairs of feelers.
    S["pacific_banana_slug"](s)
    s.paint(s.m_px([(12, 22), (21, 23), (25, 22), (18, 25), (11, 25)]), "#3a3020")


@sprite("northern_bay_mussel")
def _(s):
    # A small, smooth blue-black mussel with a purple sheen.
    s.ellipse(17, 18, 12, 7, "#2a2a44", rot=-30, edge=True)
    for k, c in enumerate(("#3a3a5e", "#4a4a7a")):
        s.paint(s.m_ellipse(17, 18, 10 - k * 3, 5 - k * 1.5, rot=-30)
                & ~s.m_ellipse(17, 18, 9 - k * 3, 4 - k * 1.5, rot=-30), c)
    s.paint(s.m_ellipse(22, 14, 3, 1.8, rot=-30), "#6a5a9a")
    s.path([(8, 25), (5, 28), (3, 29)], 0.5, "#b89a6a", shade=False)
    s.eye(12, 17)
    s.eye(18, 14)
    s.blush(12, 20)
    s.blush(20, 17)


def _chiton(s, girdle, plate, *, lines=None, plate_w=7):
    """Top view: an oval girdle with eight plates down the middle."""
    s.can("walk")
    stretch = (0, 0.5, 1, 0.5)[s.f] if s.act == "walk" else 0
    s.ellipse(16, 17, 9 - stretch * 0.5, 14 + stretch, girdle, edge=True)
    for i in range(8):
        y = 5.5 + i * 3.2
        m = s.ellipse(16, y, plate_w * (0.75 if i in (0, 7) else 1), 1.6, plate, edge=True)
        if lines:
            s.paint(s.m_line(16 - plate_w + 1, y, 16 + plate_w - 1, y), lines, within=m)
    s.eye(13, 4, size=1)
    s.eye(18, 4, size=1)


@sprite("lined_chiton")
def _(s):
    # Shiny red-orange plates painted with zigzag blue and white lines.
    _chiton(s, "#c87a5a", "#e05a3a", lines="#3a3a6a", plate_w=6)
    s.paint(s.m_px([(12, 9), (20, 12), (13, 18), (19, 21), (14, 27)]), WHITE)
    s.blush(11, 7)
    s.blush(19, 7)


@sprite("black_leather_chiton")
def _(s):
    # The "katy chiton": shiny black leathery skin with a row of pale plates showing.
    _chiton(s, "#24222a", "#e0d0b8", plate_w=2.4)
    s.px([(13, 4), (18, 4)], WHITE)
    s.paint(s.m_px([(10, 10), (22, 14), (11, 22), (21, 24)]), "#4a4652")
    s.blush(11, 7)
    s.blush(19, 7)


@sprite("golden_crayfish")
def _(s):
    # Golden-tan with dark-tipped claws.
    s.can("walk")
    w = s.wave() if s.act == "walk" else 0
    gold, dark = "#c8a04a", "#7a5a2a"
    for i, y in enumerate((17, 20, 23)):
        d = w * 1.2 * (1 if i % 2 else -1)
        s.path([(13, y), (8, y + 2 + d), (6, y + 5 + d)], 0.6, dark, shade=False)
    s.poly([(29, 20), (33, 16), (34, 21), (33, 26)], gold)
    m = s.path([(14, 20), (20, 20), (26, 20), (30, 21)], (4, 2.6), gold)
    for x in (19, 22, 25, 28):
        s.paint(s.m_line(x, 16, x, 25), dark, within=m)
    s.path([(10, 18), (7, 13)], 1.1, gold)
    s.ellipse(5.5, 9, 3.4, 2.4, gold, rot=-60, edge=True)
    s.paint(s.m_px([(4, 6), (5, 6), (5, 7), (4, 7)]), "#2b2226")
    s.path([(10, 22), (6, 25)], 1.1, gold)
    s.ellipse(4, 27, 3.2, 2.2, gold, rot=30, edge=True)
    s.paint(s.m_px([(1, 28), (2, 28), (1, 27)]), "#2b2226")
    s.ellipse(12, 20, 5.5, 4.5, gold, edge=True)
    s.paint(s.m_px([(12, 18), (14, 19), (11, 22)]), "#e8c870", within=s.last)
    s.line(9, 17, 4, 13, dark)
    s.line(8, 18, 2, 16, dark)
    s.eye(9, 18)
    s.blush(10, 21)


# --------------------------------------------------------------------------- marine
@sprite("mottled_star")
def _(s):
    # Five long slender arms, mottled in browns and oranges.
    star(s, "#c8784a", arms=0.62, dots="#7a4a3a")
    s.paint(s.m_px([(9, 12), (22, 11), (14, 22), (20, 21), (16, 9), (11, 19)]), "#e8b08a")


def _many_arms(s, color, n, arms, rot=-90):
    x, y = _XS - 16, _YS - 16.5
    ang = np.arctan2(y, x) - math.radians(rot)
    r = np.hypot(x, y)
    rr = 14.5 * ((1 - arms) + arms * (0.5 + 0.5 * np.cos(n * ang)) ** 1.6)
    return s.fill(r <= rr, color, edge=True)


@sprite("sunflower_sea_star")
def _(s):
    # A huge soft star with up to twenty-four arms, purple and orange.
    m = _many_arms(s, "#a8508a", 18, 0.35)
    s.paint(s.m_ellipse(16, 16.5, 8, 8), "#d87a5a", within=m)
    s.paint(s.m_ellipse(16, 16.5, 4, 4), "#e8a070", within=m)
    s.eye(12, 14)
    s.eye(18, 14)
    s.px([(15, 18), (16, 18)], "#5a2a3a")
    s.blush(10, 17)
    s.blush(20, 17)


@sprite("leather_star")
def _(s):
    # Smooth, slippery blue-gray star with red-orange mottling and short arms.
    star(s, "#6a7a9a", arms=0.3, dots=None)
    s.paint(s.m_px([(8, 10), (9, 11), (23, 10), (22, 11), (10, 22), (21, 23), (16, 6), (16, 26), (7, 16),
                    (25, 16), (13, 25), (19, 7)]), "#d8604a")
    s.paint(s.m_ellipse(16, 16.5, 2, 2), "#e8a080")


@sprite("arctic_green_sea_urchin")
def _(s):
    # A green spiny ball.
    for k in range(16):
        a = k * math.pi / 8 + 0.1
        s.line(16 + 6 * math.cos(a), 17 + 6 * math.sin(a), 16 + 12 * math.cos(a), 17 + 12 * math.sin(a), "#7aa84a")
    s.ellipse(16, 17, 8, 7.5, "#4a7a3a", edge=True)
    s.px([(11, 13), (13, 11), (19, 12), (21, 15), (12, 20), (20, 21)], "#8ab85a")
    s.eye(12, 15)
    s.eye(18, 15)
    s.blush(10, 18)
    s.blush(20, 18)


def _anemone(s, column, tent_a, tent_b, disk, *, band=None, column_spots=None):
    s.ellipse(16, 29, 9, 2, "#c8b8a0")
    m = s.poly([(9, 28), (8, 16), (24, 16), (23, 28)], column)
    if column_spots:
        s.paint(s.m_px([(11, 19), (14, 22), (19, 20), (21, 25), (12, 26), (17, 25)]), column_spots, within=m)
    for k in range(9):
        x = 5 + k * 2.75
        t = s.path([(x, 15), (x + 0.5 * (-1) ** k, 10), (x - 0.5 * (-1) ** k, 7)], (1.4, 1.1), tent_a if k % 2 else tent_b)
        if band:
            s.paint(s.m_line(0, 11, 32, 11), band, within=t)
    s.ellipse(16, 15, 9.5, 3, disk, edge=True)
    s.paint(s.m_line(9, 15, 23, 15), mix(disk, "#ffffff", 0.5), within=s.last)
    s.ellipse(16, 15, 2.5, 1.2, "#e89ab0", shade=False)
    s.eye(12, 20)
    s.eye(18, 20)
    s.blush(10, 23)
    s.blush(20, 23)


@sprite("painted_anemone")
def _(s):
    # A red column blotched with green, and thick banded tentacles.
    _anemone(s, "#c83a3a", "#e8606a", "#f0a0a0", "#d84a50", band=WHITE, column_spots="#6a9a4a")


@sprite("moonglow_anemone")
def _(s):
    # Glowing pale tentacles over a sandy column, rimmed in soft pink and white.
    _anemone(s, "#b8a888", "#d8f0e8", "#f0e0f0", "#a8d8c8", band="#f0a0c0", column_spots="#a09070")


@sprite("pacific_lions_mane_jelly")
def _(s):
    # A big golden-red bell trailing a shaggy mane of tentacles.
    jelly(s, "#d8603a", rim="#f0a050", arms="#f0b080", tentacles="#e88a5a", stripes="#b8402a")
    for x0 in (10, 15.5, 21):
        s.path([(x0, 14), (x0 + 1, 20), (x0 - 1, 26), (x0 + 1, 31)], 0.5, "#f0c090", shade=False)
