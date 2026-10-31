"""Sprites for the eastern states' species that aren't on an earlier state's list
(Alabama, Arkansas, Connecticut, Delaware, Indiana, Louisiana, Maine, Massachusetts,
Mississippi, New Hampshire, Rhode Island, South Carolina, Tennessee, West Virginia)."""
from __future__ import annotations

import math

from archetypes import (BLACK, EYE, WHITE, _fluke, beetle_top, bird, butterfly, crab, critter, dragonfly, duck,
                        fish, flecks, frog, goose, jelly, lizard, pinniped, snake, spider_top, sprite, star, turtle,
                        wader)
from pixel import _XS, _YS, mix
from species_tx import _segmented


def _speckle(s, mask, col, k=3):
    """Paint a fine, even sprinkle of dots inside mask."""
    xi, yi = _XS.astype(int), _YS.astype(int)
    s.paint(mask & (yi % 2 == 0) & ((xi + (yi // 2) * 2) % k == 0), col)


# --------------------------------------------------------------------------- mammals
def _bat(s, fur, wing, bone, *, belly=None, ears=None):
    s.can("fly")
    up = s.act == "fly" and s.f % 2 == 0
    lift = -5 if up else 0
    for side in (-1, 1):
        x = lambda v: 16 + side * v  # noqa: E731
        tip = (x(15), 9 + lift)
        pts = [(x(3), 13), tip, (x(13), 19 + lift * .4), (x(10), 17 + lift * .2), (x(8), 21), (x(5), 19), (x(3), 23)]
        s.poly(pts, wing, edge=True)
        for end in (tip, (x(13), 19 + lift * .4), (x(8), 21)):
            s.path([(x(3), 13.5), end], 0.45, bone, shade=False)
    s.poly([(12, 23), (20, 23), (18, 28), (16, 30), (14, 28)], wing)
    m = s.ellipse(16, 19, 4, 6, fur, edge=True)
    s.paint(s.m_ellipse(16, 21, 2.6, 3.4), belly or mix(fur, "#ffffff", 0.25), within=m)
    s.poly([(12.5, 9.5), (12, 5), (15, 8.5)], ears or wing)
    s.poly([(19.5, 9.5), (20, 5), (17, 8.5)], ears or wing)
    s.ellipse(16, 11.5, 4, 3.6, fur, edge=True)
    s.px([(15, 13), (17, 13)], "#2b2226")
    s.eye(14, 11)
    s.eye(18, 11)
    return m


@sprite("tri_coloured_bat")
def _(s):
    # A tiny golden-brown bat with pinkish-orange forearms that stand out against dark wings.
    _bat(s, "#c09058", "#4a3a34", "#d8846a", belly="#d8b07a", ears="#c88a6a")


@sprite("white_footed_mouse")
def _(s):
    # Warm brown back, snowy white belly and feet, big ears and bulging eyes.
    critter(s, "#a8683a", WHITE, build="mouse", ears="big", ear_in="#f2b0bc", tail="rat", tail_col="#c89a80",
            feet=WHITE, nose="#e88a9a", eye_size=3)


@sprite("grey_seal")
def _(s):
    # Darker than a harbor seal, with pale blotches and a long, sloping "horse head" nose.
    pinniped(s, "#767a84", "#b4b8c0", belly=False, blotch=lambda s, body: flecks(s, body, "#a8acb6", every=9))


@sprite("harbour_porpoise")
def _(s):
    # Small and chunky with no beak, a low triangle fin, dark back and pale belly.
    s.can("swim")
    w = s.wave() if s.act == "swim" else 0
    body, belly = "#4a5262", "#dfe3ea"
    _fluke(s, [(24, 16), (31, 10), (29, 16), (31, 22)], body, w)
    s.poly([(14, 12), (18, 6), (21, 12)], body)
    m = s.ellipse(15, 17, 11.5, 6.5, body, edge=True)
    s.paint(s.m_ellipse(12, 21, 9.5, 3), belly, within=m)
    s.ellipse(12, 23, 3.6, 1.5, mix(body, "#000000", 0.2), rot=30)
    s.px([(5, 19), (6, 19), (7, 18)], mix(body, "#000000", 0.5))
    s.eye(7, 15)


# --------------------------------------------------------------------------- birds
@sprite("red_headed_woodpecker")
def _(s):
    # An all-red head, inky black back and big white wing patches.
    def wing(s, m):
        s.paint(s.m_poly([(19, 14), (27, 14), (27, 24), (19, 24)]), WHITE, within=m)
    bird(s, BLACK, WHITE, head="#d0202e", wing=BLACK, tail_col=BLACK, beak="crow", beak_col="#6a6a74",
         legs="#5a5a62", tail="short", wing_mark=wing)


@sprite("indigo_bunting")
def _(s):
    def wing(s, m):
        s.paint(s.m_line(17, 17, 24, 15), "#1e3a8a", within=m)
    bird(s, "#2a5ad8", "#3a6ae4", head="#2a52d4", wing="#2448b8", tail_col="#1e3a9a", beak="cone",
         beak_col="#8a8a9a", legs="#3a3a44", tail="mid", wing_mark=wing)


@sprite("summer_tanager")
def _(s):
    # The male: rosy red all over, with a big pale bill.
    bird(s, "#d8343a", "#e64a48", head="#de3a3e", wing="#c42c34", tail_col="#c02a32", beak="crow",
         beak_col="#e0c49a", legs="#8a7a7a", tail="mid")


@sprite("eastern_kingbird")
def _(s):
    # Dark above, clean white below, and a black tail tipped with a white band.
    bird(s, "#3a3a44", WHITE, head="#1e1c24", wing="#3a3a44", tail_col="#1e1c24", beak="thin",
         beak_col="#1a1820", legs="#2b2630", tail="mid")
    s.paint(s.m_line(29, 13, 31, 16) | s.m_line(28, 13, 30, 16), WHITE)


@sprite("blue_grosbeak")
def _(s):
    # Deep blue with two chestnut wing bars and a big silvery bill.
    def wing(s, m):
        s.paint(s.m_line(16, 18, 24, 15) | s.m_line(17, 20, 24, 18), "#b8682a", within=m)
    bird(s, "#2a48b0", "#3456bc", head="#2a4ab8", wing="#24388a", tail_col="#1e2e70", beak="crow",
         beak_col="#b8bcc8", legs="#3a3a44", tail="mid", wing_mark=wing)
    s.px([(6, 11), (6, 12)], BLACK)


def _tern(s, bill, legs, belly, wingtip):
    def face(s):
        s.paint(s.m_ellipse(13, 7, 6, 3.2) | s.m_poly([(13, 5), (17, 6), (17, 9)]), BLACK, within=s.last)

    def wing(s, m):
        s.paint(s.m_ellipse(25, 17, 2.6, 1.3, rot=-15), wingtip, within=m)
    bird(s, WHITE, belly, head=WHITE, wing="#c8ccd6", tail_col=WHITE, beak="long", beak_col=bill,
         legs=legs, tail="long", face=face, wing_mark=wing)
    s.px([(29, 8), (30, 7), (31, 10)], "#e6e8ee")  # deep tail fork


@sprite("forsters_tern")
def _(s):
    # Orange bill with a black tip and frosty-white wingtips.
    _tern(s, "#f08a2a", "#f08a2a", WHITE, "#eef0f4")
    s.px([(-1, 12), (0, 12), (0, 13)], BLACK)


@sprite("common_tern")
def _(s):
    # Red bill with a black tip, red legs, a grey wash below and dark wingtips.
    _tern(s, "#e0302a", "#e0302a", "#e4e6ec", "#5a5e6a")
    s.px([(-1, 12), (0, 12), (0, 13)], BLACK)


@sprite("northern_harrier")
def _(s):
    # The "grey ghost": pale grey male with black wingtips, white rump and an owlish face.
    def wing(s, m):
        s.paint(s.m_ellipse(25, 16.5, 2.8, 1.8, rot=-15), BLACK, within=m)

    def face(s):
        s.paint(s.m_ellipse(10, 12, 4.6, 4.4) & ~s.m_ellipse(10, 12, 3.6, 3.4), "#8a8e98", within=s.last)
    bird(s, "#a4a8b2", WHITE, head="#a8acb6", wing="#9ca0aa", tail_col="#9aa0aa", beak="hook",
         beak_col="#3a3a44", legs="#f0c040", tail="long", wing_mark=wing, face=face, big=True, eye_col="#e0b020")
    s.ellipse(22.5, 22.5, 2.4, 1.6, WHITE)
    for k in (0, 3, 6):
        s.paint(s.m_line(23 + k * 0.8, 12 - k * 1.1, 25 + k * 0.8, 13 - k * 1.1), "#5a5e68")


@sprite("mississippi_kite")
def _(s):
    # Sleek and grey with a pale silvery head, ruby eyes and a black tail.
    bird(s, "#6a6e78", "#8e949e", head="#cdd1d6", wing="#5a5e68", tail_col="#1e1c24", beak="hook",
         beak_col="#2b2630", legs="#d8a050", tail="long", eye_col="#c02a2a")
    s.px([(7, 10), (8, 9), (9, 9)], "#2b2630")  # dark smudge round the eye


@sprite("broad_winged_hawk")
def _(s):
    # Brown with a rusty-barred chest and a bold black-and-white banded tail.
    def bars(s, m):
        for y in (20, 22, 24):
            s.paint(s.m_line(9, y, 18, y), "#b8603a", within=m)

    def face(s):
        s.paint(s.m_ellipse(9, 15, 3.5, 1.6), "#f2e6d2", within=s.last)
    bird(s, "#6a4630", "#f2e6d2", head="#6a4630", wing="#5e3e2a", tail_col="#2b2630", beak="hook",
         beak_col="#e0c070", legs="#e8c04a", tail="fan", belly_mark=bars, face=face, big=True)
    s.paint(s.m_line(25, 13, 28, 18) | s.m_line(28, 11, 30, 16), WHITE)


@sprite("hairy_woodpecker")
def _(s):
    # Like a big downy, with a much longer bill and a white stripe down the back.
    def wing(s, m):
        for x in (17, 19, 21, 23):
            s.paint(s.m_px([(x, 18), (x + 1, 20)]), WHITE, within=m)

    def face(s):
        h = s.last
        s.paint(s.m_ellipse(11, 7, 4.5, 2.2), BLACK, within=h)
        s.paint(s.m_ellipse(14.5, 7.5, 2, 1.4), "#e02a2a", within=h)
        s.paint(s.m_line(6, 12, 15, 12), BLACK, within=h)
    bird(s, BLACK, WHITE, head=WHITE, wing=BLACK, tail_col=BLACK, beak="long", beak_col="#3a3430",
         legs="#5a5a62", tail="short", wing_mark=wing, face=face)
    s.paint(s.m_line(16, 14, 22, 15), WHITE)


@sprite("yellow_bellied_sapsucker")
def _(s):
    # Red forehead and red throat, a stripy black-and-white face and a pale yellow belly.
    def face(s):
        h = s.last
        s.paint(s.m_ellipse(11, 6.5, 4.5, 2.2), "#d8202a", within=h)
        s.paint(s.m_line(6, 11, 16, 11) | s.m_line(6, 12, 16, 12), BLACK, within=h)
        s.paint(s.m_ellipse(8, 15, 3, 2), "#d8202a", within=h)
        s.paint(s.m_line(9, 15, 15, 14), BLACK, within=h)

    def wing(s, m):
        s.paint(s.m_line(16, 16, 22, 21) | s.m_line(17, 16, 23, 21), WHITE, within=m)
        s.paint(s.m_px([(21, 17), (23, 18), (24, 20)]), WHITE, within=m)
    bird(s, "#2b2630", "#f0e4a0", head=WHITE, wing="#2b2630", tail_col="#2b2630", beak="crow",
         beak_col="#3a3430", legs="#5a5a62", tail="short", face=face, wing_mark=wing)


@sprite("red_breasted_nuthatch")
def _(s):
    # Black cap, white eyebrow, black eye line and a rusty-orange belly.
    def face(s):
        h = s.last
        s.paint(s.m_ellipse(12, 6.5, 6, 2.4), BLACK, within=h)
        s.paint(s.m_line(5, 9, 16, 9), WHITE, within=h)
        s.paint(s.m_line(5, 10, 16, 11) | s.m_line(6, 11, 16, 12), BLACK, within=h)
    bird(s, "#6a7c94", "#d8905a", head=WHITE, wing="#5e7088", tail_col="#3a4050", beak="long",
         beak_col="#3a3a44", legs="#6a5a50", tail="short", face=face)


@sprite("hermit_thrush")
def _(s):
    # Soft brown, a rusty tail, a white eye ring and a spotted chest.
    def spots(s, m):
        s.paint(s.m_px([(10, 20), (12, 21), (14, 20), (11, 23), (13, 23), (15, 22), (16, 20)]), "#4a3a2e", within=m)
    bird(s, "#8a6e54", "#f2ebe0", head="#8a6e54", wing="#7e6248", tail_col="#b45a34", beak="thin",
         beak_col="#4a3a34", legs="#e0b0a0", tail="mid", belly_mark=spots)
    s.px([(7, 9), (8, 9), (9, 9), (10, 10), (10, 11), (7, 12), (8, 12), (9, 12)], "#f2ebe0")


@sprite("dunlin")
def _(s):
    # Breeding plumage: rusty back, a black belly patch and a long, drooping bill.
    def patch(s, m):
        s.paint(s.m_ellipse(15, 24, 3.5, 2.2), "#1e1c22", within=m)

    def wing(s, m):
        s.paint(s.m_px([(17, 17), (19, 19), (21, 16), (23, 18), (18, 21), (22, 20)]), "#3a2a22", within=m)
    bird(s, "#b87048", "#f0ece4", head="#c8c0b4", wing="#b06a40", tail_col="#6a6a70", beak="long",
         beak_col="#1d1a20", legs="#1d1a20", tail="short", belly_mark=patch, wing_mark=wing)
    s.px([(-1, 13), (-2, 14)], "#1d1a20")


@sprite("american_avocet")
def _(s):
    # Cinnamon head and neck, black-and-white back, blue legs and an upturned bill.
    wader(s, WHITE, neck="#d8945e", head="#d8945e", beak="#1d1a20", legs="#7a9ac8", wing=WHITE)
    beak = s.reg == s.n - 2
    s.erase(beak)
    s.path([(7, 6), (3, 6.6), (0, 5.6), (-2, 3.5)], (0.7, 0.3), "#1d1a20", shade=False)
    s.paint(s.m_poly([(17, 11), (26, 12), (26, 14), (17, 13.5)]) | s.m_poly([(20, 15), (27, 15), (27, 17), (20, 16.5)]),
            BLACK)
    s.paint(s.m_poly([(26, 14), (31, 17), (25, 18)]), BLACK)
    s.eye(8, 4)


@sprite("black_necked_stilt")
def _(s):
    # Tuxedo black and white on very long, bright pink legs.
    wader(s, WHITE, neck=WHITE, head=WHITE, beak="#1d1a20", legs="#f07aa0", wing=BLACK)
    s.paint(s.m_ellipse(20, 12, 7, 2.6), BLACK)
    s.paint(s.m_ellipse(12.5, 3.6, 3.4, 2.4) | s.m_path([(13, 6), (15, 9), (16, 13)], 0.9), BLACK)
    s.px([(8, 2), (9, 2)], WHITE)
    s.eye(8, 4)


@sprite("snow_goose")
def _(s):
    # All white with black wingtips and a pink bill with a dark "grin".
    goose(s)
    s.paint(s.m_ellipse(19, 23, 10.5, 6.5) | s.m_ellipse(14, 25, 5, 4), "#f6f6f4")
    s.paint(s.m_poly([(25, 20), (31, 17), (30, 23)]), "#f0f0ee")
    s.paint(s.m_ellipse(22, 21, 7, 3.5, rot=-8), "#e8eaee")
    s.paint(s.m_ellipse(27, 20.5, 2.4, 1.6, rot=-8), "#2b2630")
    s.paint(s.m_path([(12, 19), (10, 13), (10, 8)], 2.3) | s.m_ellipse(9.5, 7, 5, 4.2), "#f8f8f6")
    s.ellipse(4, 8.2, 2.6, 1.5, "#f08aa0")
    s.paint(s.m_line(2, 9, 5, 9), "#3a2a30")
    s.eye(8, 5)


@sprite("brant")
def _(s):
    # A small dark sea goose: black head and neck with a little white necklace.
    goose(s)
    s.paint(s.m_ellipse(19, 23, 10.5, 6.5), "#5a524c")
    s.paint(s.m_ellipse(22, 21, 7, 3.5, rot=-8), "#4a4440")
    s.paint(s.m_ellipse(14, 25, 5, 4), "#2b2630")
    s.paint(s.m_ellipse(25, 26, 3, 1.6), WHITE)
    s.paint(s.m_ellipse(10.5, 9.5, 2.6, 1.6, rot=-20), BLACK)
    s.paint(s.m_ellipse(13, 19.5, 2.6, 1.2), BLACK)
    s.paint(s.m_line(9, 12, 12, 12) | s.m_px([(8, 13), (12, 13)]), WHITE)
    s.eye(8, 5, color="#000000", shine="#ffffff")


@sprite("bufflehead")
def _(s):
    # Tiny black-and-white diving duck with a big white patch on the back of its head.
    duck(s, WHITE, WHITE, "#24203a", bill="#8a8ea0", ring=None, speculum=WHITE, tail_col="#3a3a44")
    s.paint(s.m_poly([(17, 17), (29, 17), (29, 20), (17, 20.5)]), "#1e1c24")
    s.paint(s.m_ellipse(12.5, 10, 3.3, 2.8), WHITE)
    s.paint(s.m_px([(7, 7), (8, 8), (6, 13)]), "#3a6a5a")
    s.eye(7, 10)


@sprite("common_eider")
def _(s):
    # The drake: white back, black sides, black cap, a mint-green nape and a long wedge bill.
    duck(s, "#1e1c22", WHITE, WHITE, bill="#a8b48a", ring=None, speculum="#1e1c22", tail_col="#1e1c22")
    s.paint(s.m_ellipse(17, 19.5, 9, 2.8), WHITE)
    s.paint(s.m_ellipse(10, 8, 5.5, 2.6), BLACK, within=s.m_ellipse(10, 11, 6, 5.5))
    s.paint(s.m_ellipse(14, 12, 2.2, 2.2), "#a8d8a8", within=s.m_ellipse(10, 11, 6, 5.5))
    s.eye(7, 10)


@sprite("pied_billed_grebe")
def _(s):
    # A chunky brown little diver; its pale bill wears a black ring.
    duck(s, "#7a5e44", "#a08a6a", "#6a523c", bill="#e0dcc8", ring=None, speculum="#6a523c", tail_col="#a08a6a")
    s.paint(s.m_line(3, 11, 3, 14) | s.m_line(4, 11, 4, 14), BLACK)
    s.paint(s.m_ellipse(8, 15, 2, 1.4), BLACK)
    s.px([(6, 9), (7, 9), (8, 9), (6, 12), (8, 12)], WHITE)
    s.eye(7, 10)


@sprite("black_guillemot")
def _(s):
    # Sooty black with a big white wing patch and bright red feet.
    def wing(s, m):
        s.paint(s.m_ellipse(20, 18, 4.5, 2.6, rot=-15), WHITE, within=m)
    bird(s, "#1e1c22", "#26242a", head="#1e1c22", wing="#1e1c22", tail_col="#1e1c22", beak="thin",
         beak_col="#141218", legs="#e8302a", tail="short", wing_mark=wing)
    s.px([(12, 29), (13, 29), (16, 29), (17, 29)], "#e8302a")
    s.px([(4, 12)], "#e8302a")


@sprite("atlantic_puffin")
def _(s):
    # Black back, white face and belly, orange feet and a big rainbow bill.
    def face(s):
        s.paint(s.m_ellipse(9, 12, 4.6, 3.8), "#eef0f0", within=s.last)
    bird(s, "#1e1c22", WHITE, head="#1e1c22", wing="#1e1c22", tail_col="#1e1c22", beak="cone",
         beak_col="#f06a2a", legs="#f08a2a", tail="short", face=face)
    m = s.poly([(6, 8.5), (1, 12), (6, 15.5)], "#f0602a", edge=True)
    s.paint(s.m_poly([(6, 8), (4.2, 9.3), (4.2, 14.7), (6, 16)]), "#4a5a7a", within=m)
    s.paint(s.m_line(4, 9, 4, 15), "#f2d040", within=m)
    s.px([(7, 9), (9, 9)], "#e8302a")
    s.eye(8, 10)


# --------------------------------------------------------------------------- reptiles
@sprite("three_toed_box_turtle")
def _(s):
    # A high olive-tan dome with faint markings, and an orange-spotted head.
    turtle(s, "#8a7a48", "#7a5e40", dome=True, scutes="#9a8a5a", speckle="#e8902a", rim="#5a4a2a")
    s.px([(4, 22), (6, 21)], "#e8902a")


@sprite("eastern_musk_turtle")
def _(s):
    # The "stinkpot": a small dark dome and two yellow stripes on its head.
    turtle(s, "#3a3226", "#4a4038", dome=True, rim="#2a221a")
    s.paint(s.m_line(1, 16, 7, 16) | s.m_line(1, 19, 7, 19), "#e8d060")
    s.px([(3, 17)], EYE)


@sprite("eastern_mud_turtle")
def _(s):
    # Smooth plain olive-brown shell and a pale, speckled chin.
    turtle(s, "#6a5432", "#7a6a4a", dome=True, rim="#4a3a22")
    s.paint(s.m_px([(2, 20), (4, 21), (6, 20), (5, 22)]), "#e8d8a0")


@sprite("river_cooter")
def _(s):
    # Dark shell with yellow "C" swirls, and yellow stripes on its head and legs.
    turtle(s, "#3e4630", "#2e3a28", rim="#d8c060")
    for cx in (11, 17, 23):
        s.paint(s.m_ellipse(cx, 20, 2.4, 2.2) & ~s.m_ellipse(cx + 0.8, 20, 1.6, 1.4), "#d8c060")
    s.paint(s.m_line(1, 17, 7, 18) | s.m_line(2, 20, 8, 21) | s.m_line(10, 25, 11, 29), "#e8d070")
    s.eye(3, 17)


@sprite("prairie_lizard")
def _(s):
    # A spiny brown fence lizard with pale side stripes and dark wavy bars.
    def pat(s, m):
        s.paint(s.m_line(8, 19, 22, 19), "#e8d8b0", within=m)
        for x in (10, 14, 18):
            s.paint(s.m_path([(x, 20), (x + 1, 21), (x, 22)], 0.5), "#3a2a1e", within=m)
    lizard(s, "#8a6a48", "#5a8ad8", pattern=pat, tail_col="#7a5c3e", throat="#7ab0e8")


@sprite("six_lined_racerunner")
def _(s):
    # Six pale yellow stripes down a dark body, a greenish front and a very long tail.
    def pat(s, m):
        for y in (19, 21, 23):
            s.paint(s.m_line(8, y, 23, y), "#f0e070", within=m)
    lizard(s, "#3a3022", "#eef2f4", head="#6a8a3a", throat="#eef2f4", pattern=pat, tail_col="#8a6a4a",
           tail_pts=[(20, 22), (27, 25), (33, 24), (36, 19)])
    s.paint(s.m_line(4, 17, 10, 16), "#f0e070")


@sprite("little_brown_skink")
def _(s):
    # A tiny shiny bronze skink with a dark stripe along each side.
    def pat(s, m):
        s.paint(s.m_line(7, 21, 22, 21) | s.m_line(7, 22, 22, 22), "#3a2a1a", within=m)
    lizard(s, "#9a7448", "#ece0c8", pattern=pat, smooth=True, tail_col="#8a6a42", legs="#7a5c3a")
    s.paint(s.m_line(3, 18, 10, 18), "#3a2a1a")
    s.eye(5, 17)


@sprite("spotted_house_gecko")
def _(s):
    # Pale and bumpy, dotted with dark and white spots, with a banded tail and big eyes.
    def pat(s, m):
        s.paint(s.m_px([(9, 20), (12, 19), (15, 20), (18, 19), (21, 20), (11, 22), (17, 22)]), "#6a4a3a", within=m)
        s.paint(s.m_px([(10, 21), (14, 22), (19, 21), (13, 19), (20, 22)]), WHITE, within=m)
    lizard(s, "#d8c0a8", "#f4ece0", throat="#f4ece0", pattern=pat, smooth=True, eye_big=True, legs="#c8b098",
           tail_col="#d0b8a0")
    s.paint(s.m_line(24, 22, 25, 26) | s.m_line(28, 22, 29, 25) | s.m_line(29, 18, 31, 19), "#6a4a3a")


@sprite("speckled_kingsnake")
def _(s):
    # The "salt-and-pepper" snake: black with a yellow dot on nearly every scale.
    snake(s, "#1e1a22", belly="#f0e080", head="#1e1a22")
    _speckle(s, (s.reg == 1) | s.m_ellipse(12.5, 9.5, 5, 2.5), "#f0e070")


@sprite("black_kingsnake")
def _(s):
    # Shiny black with faint rows of yellow speckles crossing its back.
    snake(s, "#1e1a22", belly="#e8e0a0", bands="#2e2a26", band_period=4.0, band_len=0.8, head="#1e1a22")
    s.paint(s.m_px([(8, 27), (12, 29), (17, 28), (22, 29), (6, 23), (10, 21), (19, 20), (24, 23), (19, 25),
                    (15, 19), (14, 15)]), "#e0d070")


@sprite("eastern_ratsnake_pantherophis")
def _(s):
    # The coastal "yellow rat snake": olive-yellow with four dark stripes.
    snake(s, "#c8b04a", belly="#f0e8b8", stripe="#4a4030", head="#b8a040")
    body = s.reg == 1
    s.paint(body & (s.m_path([(25, 30.3), (14, 30.5), (7, 28.8), (4, 23.5), (9, 22.2), (17, 21.8), (24, 23.2)], 0.4)),
            "#4a4030")


@sprite("banded_watersnake")
def _(s):
    # Wide dark crossbands on a tan body, and a dark stripe from eye to jaw.
    snake(s, "#c8925a", belly="#f0d8a0", bands="#5a2e22", band_period=4.0, band_len=2.0, head="#9a6a4a")
    s.paint(s.m_line(8, 10, 10, 13), "#3a2018")


@sprite("diamondback_watersnake")
def _(s):
    # A chain of dark diamond shapes on an olive-brown back.
    snake(s, "#9a8a5a", belly="#ece0a8", blotch="#3a2e22", band_period=3.4, band_len=1.8, head="#8a7a4a")
    body = s.reg == 1
    xi, yi = _XS.astype(int), _YS.astype(int)
    s.paint(body & (((xi + yi) % 7) == 0), "#3a2e22")


@sprite("smooth_greensnake")
def _(s):
    # Bright, glossy grass-green with a pale belly.
    snake(s, "#6ad04a", belly="#f4f8c8", head="#72d652", head_w=4.8)


@sprite("common_ribbon_snake")
def _(s):
    # Slim and dark with bright yellow stripes, and a white spot in front of each eye.
    snake(s, "#3a2a26", belly="#f0e8a0", stripe="#f0d040", head="#3a2a26", head_w=4.8)
    body = s.reg == 1
    s.paint(body & s.m_path([(25, 30.5), (14, 30.8), (7, 29), (3.6, 23.5), (9, 22.4), (17, 22), (24, 23.4)], 0.5),
            "#f0d040")
    s.px([(7, 10), (7, 11)], WHITE)


# --------------------------------------------------------------------------- amphibians
def _sally(s, body, belly, pat, *, tail=None, legs=None, flecks=None):
    lizard(s, body, belly, head=body, throat=belly, pattern=pat, smooth=True, eye_big=True,
           legs=legs or mix(body, "#000000", 0.1), tail_col=tail or body)
    if flecks:
        s.px(flecks[0], flecks[1])


@sprite("western_slimy_salamander")
def _(s):
    # Glossy black, heavily dusted with brassy-white flecks.
    def pat(s, m):
        _speckle(s, m, "#e0d8b0", 4)
    _sally(s, "#1e1e26", "#3a3a44", pat, flecks=([(24, 23), (27, 23), (29, 20), (30, 17), (5, 15), (8, 15),
                                                   (10, 17), (21, 23)], "#e0d8b0"))


@sprite("mississippi_slimy_salamander")
def _(s):
    # Black with small, scattered silvery-white spots and a grey belly.
    def pat(s, m):
        s.paint(s.m_px([(9, 20), (13, 19), (17, 20), (21, 19), (11, 23), (19, 23)]), "#e8ecf4", within=m)
    _sally(s, "#1a1a22", "#5a5a66", pat, flecks=([(26, 24), (30, 19), (9, 16)], "#e8ecf4"))


@sprite("ozark_zigzag_salamander")
def _(s):
    # Dark grey with a bright orange zigzag stripe down its back.
    def pat(s, m):
        s.paint(s.m_path([(8, 19.5), (10, 18.5), (12, 20), (14, 18.5), (16, 20), (18, 18.5), (20, 20), (22, 19)],
                         0.8), "#f0902a", within=m)
    _sally(s, "#3a3640", "#8a8690", pat)
    s.paint(s.m_path([(21, 21.5), (26, 24), (29, 21)], 0.5), "#f0902a")


@sprite("northern_zigzag_salamander")
def _(s):
    # Brown-black with a red zigzag back stripe and pale flecks on its sides.
    def pat(s, m):
        s.paint(s.m_path([(8, 19.5), (10, 18.5), (12, 20), (14, 18.5), (16, 20), (18, 18.5), (20, 20), (22, 19)],
                         0.8), "#c8402a", within=m)
        s.paint(s.m_px([(10, 22), (14, 23), (18, 22)]), "#c8c4cc", within=m)
    _sally(s, "#2e2628", "#6a6268", pat)
    s.paint(s.m_path([(21, 21.5), (26, 24), (29, 21)], 0.5), "#c8402a")


@sprite("southern_two_lined_salamander")
def _(s):
    # Bright yellow-orange with a dark line down each side of its back.
    def pat(s, m):
        s.paint(s.m_line(8, 19, 22, 19) | s.m_line(8, 21, 22, 21), "#3a2a1a", within=m)
        s.paint(s.m_px([(11, 20), (15, 20), (19, 20)]), "#4a3220", within=m)
    _sally(s, "#f0b030", "#f8e090", pat, tail="#e8a828")
    s.paint(s.m_path([(20, 21), (26, 23.5), (30, 20)], 0.5), "#3a2a1a")


@sprite("cave_salamander")
def _(s):
    # Bright orange with scattered black spots and a long tail.
    def pat(s, m):
        s.paint(s.m_ellipse(10, 20, 1, 1) | s.m_ellipse(14, 19, 1, 1) | s.m_ellipse(18, 20, 1, 1)
                | s.m_ellipse(12, 22, 0.8, 0.8) | s.m_ellipse(20, 22, 0.8, 0.8), "#1e1a1c", within=m)
    _sally(s, "#ec6a2a", "#f8b070", pat, tail="#e4642a",
           flecks=([(6, 15), (9, 16), (24, 23), (27, 22), (29, 19), (30, 16)], "#1e1a1c"))


@sprite("allegheny_mountain_dusky_salamander")
def _(s):
    # Brown with a wavy-edged tan stripe down its back and a pale line from eye to jaw.
    def pat(s, m):
        s.paint(s.m_path([(8, 19), (11, 18.6), (14, 19.4), (17, 18.6), (20, 19.4), (22, 19)], 1.0), "#c8a46a",
                within=m)
    _sally(s, "#5a4a3a", "#a8a090", pat, tail="#5a4a3a")
    s.paint(s.m_line(5, 19, 8, 21), "#d8ccb0")


@sprite("northern_dusky_salamander")
def _(s):
    # Mottled tan-brown, with a pale line from eye to jaw and a keeled tail.
    def pat(s, m):
        s.paint(s.m_px([(9, 19), (12, 20), (15, 19), (18, 20), (21, 19), (11, 22), (17, 22)]), "#4a3a2a", within=m)
    _sally(s, "#8a7050", "#d8ccb4", pat, tail="#7a6044")
    s.paint(s.m_line(5, 19, 8, 21), "#e0d4b8")
    s.paint(s.m_line(26, 23, 29, 20), "#5a4a34")


@sprite("eastern_spadefoot")
def _(s):
    # Smooth brown toad with yellow lines curving down its back and cat-like golden eyes.
    frog(s, "#6a5a3a", "#ece4d4", build="toad", spots=2, lines="#e8d060", iris="#e8c040", cat=True)


@sprite("eastern_narrow_mouthed_toad")
def _(s):
    # A tiny teardrop-shaped toad with a pointed snout and a fold of skin behind its head.
    s.can("walk")
    hop = s.act == "walk" and s.f == 2
    c = "#5a4a42"
    s.ellipse(23, 27, 5, 2.4, mix(c, "#000000", 0.15))
    m = s.fill(s.m_ellipse(18, 22, 10, 7) | s.m_poly([(10, 17), (1, 24), (10, 28)]), c, edge=True)
    s.paint(s.m_ellipse(17, 27, 8, 2.6), "#8a7a72", within=m)
    s.paint(s.m_px([(15, 18), (20, 17), (23, 20), (18, 22)]), "#4a3a34", within=m)
    s.paint(s.m_path([(10, 16), (10.5, 20), (10, 24)], 0.5), "#3a2e2a", within=m)
    s.ellipse(9, 28, 2.4, 1.4, mix(c, "#000000", 0.1))
    s.eye(5, 21)
    if hop:
        s.shift(0, -2)


# --------------------------------------------------------------------------- fish
def _longear(body, belly, spot, squig):
    def pat(s, m):
        s.paint(s.m_path([(3, 15), (6, 18), (9, 15)], 0.5) | s.m_path([(4, 18), (8, 20)], 0.5), squig, within=m)
        s.paint(s.m_px([(14, 12), (17, 14), (20, 12), (15, 16), (19, 17), (22, 15), (23, 12), (13, 18)]), spot,
                within=m)
        s.paint(s.m_path([(9, 13), (13.5, 12.5)], 1.1), "#1e2430", within=m)
        s.paint(s.m_px([(14, 12), (14, 13)]), WHITE, within=m)
    return pat


@sprite("longear_sunfish")
def _(s):
    # Teal and orange with turquoise squiggles on its cheek and a long, white-edged black ear flap.
    fish(s, "#3a8a7e", "#f08030", fin="#2e7468", pattern=_longear("#3a8a7e", "#f08030", "#f0a040", "#7ae0f0"))


@sprite("gulf_longear_sunfish")
def _(s):
    fish(s, "#8a6a3a", "#e8582a", fin="#7a5a30", pattern=_longear("#8a6a3a", "#e8582a", "#5ad0c8", "#5ad0f0"))


@sprite("warmouth")
def _(s):
    # Mottled brown with a big mouth, red eye and dark lines fanning back from the eye.
    def pat(s, m):
        s.paint(s.m_px([(13, 12), (16, 14), (19, 12), (22, 14), (15, 18), (20, 18), (24, 17), (17, 11)]), "#4a3a22",
                within=m)
        s.paint(s.m_line(8, 14, 11, 14) | s.m_line(8, 16, 11, 17) | s.m_line(7, 17, 10, 20), "#5a3a22", within=m)
    fish(s, "#8a7440", "#e0c890", fin="#6a5a34", pattern=pat)
    s.px([(7, 15)], "#d02a2a")
    s.px([(2, 18), (3, 18), (4, 18), (5, 18)], "#3a2a1a")


@sprite("blackbanded_darter")
def _(s):
    # Sandy with a row of black blotches joined into a band along its side.
    def pat(s, m):
        s.paint(s.m_path([(5, 16.5), (26, 16.5)], 0.6), "#2a2620", within=m)
        for x in (10, 14.5, 19, 23.5):
            s.paint(s.m_ellipse(x, 16.5, 1.5, 2), "#2a2620", within=m)
            s.paint(s.m_ellipse(x + 2, 11.5, 1.2, 1), "#5a4a30", within=m)
    fish(s, "#c8b878", "#f0e8c8", fin="#a89860", pattern=pat, slim=True)


def _stoneroller(s, body, fin, band):
    def pat(s, m):
        _speckle(s, m & s.m_ellipse(16, 13, 10, 4), mix(body, "#000000", 0.35), 3)
        s.paint(s.m_px([(5, 12), (7, 11), (4, 14)]), "#f4f0e0", within=m)  # breeding bumps on the head
    fish(s, body, "#ece0c4", fin=fin, pattern=pat, slim=True)
    s.paint(s.m_line(12, 10, 20, 8) | s.m_line(13, 23, 18, 23), band)


@sprite("largescale_stoneroller")
def _(s):
    # A brown minnow with big dark-edged scales and orange fins.
    _stoneroller(s, "#8a7a5a", "#d8803a", "#b05a2a")


@sprite("highland_stoneroller")
def _(s):
    # Darker olive, with bright orange fins crossed by a black band.
    _stoneroller(s, "#5e6248", "#f06a2a", "#1e1c1a")


@sprite("greenside_darter")
def _(s):
    # Pale green with dark green "W" bars along its sides.
    def pat(s, m):
        for x in (10, 14, 18, 22):
            s.paint(s.m_path([(x - 1, 15), (x, 19), (x + 1, 16), (x + 2, 19), (x + 3, 15)], 0.55), "#2a7a3a",
                    within=m)
        s.paint(s.m_px([(12, 12), (16, 11), (20, 12)]), "#6a8a4a", within=m)
    fish(s, "#a8c474", "#ecf2d0", fin="#4a9a4a", pattern=pat, slim=True)


@sprite("redline_darter")
def _(s):
    # Rows of little red dashes on a tan body, with dark blotches in between.
    def pat(s, m):
        for y in (13, 15, 17, 19):
            s.paint(s.m_px([(x, y) for x in range(9 + (y % 4), 26, 3)]), "#d82a2a", within=m)
        for x in (12, 18, 23):
            s.paint(s.m_ellipse(x, 16, 1.1, 1.4), "#3a2e22", within=m)
    fish(s, "#c8b48a", "#efe4cc", fin="#c86040", pattern=pat, slim=True)


@sprite("spotted_gar")
def _(s):
    # Long and olive, peppered with dark spots everywhere, even on its snout and fins.
    def pat(s, m):
        _speckle(s, m, "#2a2a1e", 4)
    fish(s, "#8a8450", "#e0dcb8", fin="#6a6a40", pattern=pat, slim=True)
    snout = s.path([(4, 16), (-3, 16.5)], (1.4, 0.8), "#8a8450")
    s.paint(s.m_px([(1, 16), (-1, 17), (3, 17)]), "#2a2a1e", within=snout)
    _speckle(s, s.m_poly([(22, 8), (34, 8), (34, 26), (26, 26)]) & ~s.m_ellipse(15, 16.5, 11, 6), "#2a2a1e", 2)


@sprite("sailfin_molly")
def _(s):
    # The male raises a huge sail-like back fin, speckled with orange.
    def pat(s, m):
        for y in (13, 16, 19):
            s.paint(s.m_px([(x, y) for x in range(10 + y % 2, 25, 3)]), "#f0a040", within=m)
    fish(s, "#7a90b0", "#dfe6ee", fin="#6a80a0", pattern=pat, slim=True)
    sail = s.poly([(8, 11.5), (10, 2), (19, 1), (25, 5), (24, 11.5)], "#7a8cb0", edge=True)
    s.paint(s.m_path([(10, 2.5), (19, 1.5), (24.5, 5.5)], 0.6), "#f0a040", within=sail)
    s.paint(s.m_px([(12, 5), (15, 4), (18, 5), (21, 6), (13, 8), (17, 8), (21, 9)]), "#2a3a5a", within=sail)


@sprite("clearnose_skate")
def _(s):
    # A brown diamond with dark spots and bars, and two see-through patches beside its snout.
    s.can("swim")
    w = s.wave() if s.act == "swim" else 0
    c = "#a07a52"
    tail = s.path([(16, 22), (16 + w, 27), (16 - w, 31)], (1.4, 0.6), c)
    s.paint(s.m_px([(16, 24), (16, 27)]), "#e8dcc4", within=tail)
    s.ellipse(12, 22.5, 2.6, 1.6, c, mirror=True)
    m = s.poly([(16, 1), (24, 9), (30 - w, 14), (17, 23), (15, 23), (2 + w, 14), (8, 9)], c, edge=True)
    s.paint(s.m_ellipse(13.4, 6.5, 1, 3, rot=25) | s.m_ellipse(18.6, 6.5, 1, 3, rot=-25), "#f0e8d8", within=m)
    s.paint(s.m_px([(8, 13), (10, 16), (22, 13), (24, 16), (13, 19), (19, 19), (6, 14), (26, 14)]), "#4a3424", within=m)
    s.paint(s.m_line(9, 11, 11, 13) | s.m_line(23, 11, 21, 13), "#4a3424", within=m)
    s.px([(16, 11), (16, 14), (16, 17)], "#e8dcc4")
    s.eye(12, 11)
    s.eye(19, 11)


# --------------------------------------------------------------------------- butterflies and moths
@sprite("cloudless_sulphur")
def _(s):
    # Big and lemon-yellow, with just a tiny dark dot on each forewing.
    def pat(s, fm, hm):
        s.paint(s.m_px([(10, 10)]), "#9a6a2a", mirror=True, within=fm)
        s.paint(s.m_px([(9, 21)]), "#e09a3a", mirror=True, within=hm)
    butterfly(s, "#f6e43a", "#f2da30", body="#c8b040", pattern=pat)


@sprite("spicebush_swallowtail")
def _(s):
    # Black wings edged with cream spots, a blue-green glow on the hindwings, and tails.
    def pat(s, fm, hm):
        s.paint(s.m_px([(3, 7), (3, 10), (4, 13), (7, 14), (10, 15)]), "#f4ecc0", mirror=True, within=fm)
        s.paint(s.m_ellipse(9, 22, 4.5, 3), "#4aa0b8", mirror=True, within=hm)
        s.paint(s.m_px([(5, 21), (6, 24), (9, 26)]), "#f4ecc0", mirror=True, within=hm)
        s.paint(s.m_px([(14, 21)]), "#f08a2a", mirror=True, within=hm)
    butterfly(s, "#1e1e28", "#222630", body="#1e1e28", pattern=pat, tails=True)


@sprite("hackberry_emperor")
def _(s):
    # Tan-brown with dark, white-spotted wingtips, one eyespot on the forewing and a row on the hindwing.
    def pat(s, fm, hm):
        s.paint(s.m_poly([(1.5, 6), (5, 3), (8, 6), (3, 12)]), "#3a2a20", mirror=True, within=fm)
        s.paint(s.m_px([(3, 6), (4, 8), (5, 5), (3, 9)]), WHITE, mirror=True, within=fm)
        s.paint(s.m_ellipse(7, 12, 1.2, 1.2), "#1e1a1a", mirror=True, within=fm)
        s.paint(s.m_px([(5, 21), (7, 23), (9, 25), (11, 25)]), "#1e1a1a", mirror=True, within=hm)
    butterfly(s, "#b4885a", "#a47c52", body="#6a5040", pattern=pat)


@sprite("american_lady")
def _(s):
    # Orange with a black-and-white tip, a little white spot in the orange, and two big blue-eyed spots below.
    def pat(s, fm, hm):
        s.paint(s.m_poly([(8, 3), (1, 6), (2, 11), (9, 9)]), BLACK, mirror=True, within=fm)
        s.paint(s.m_px([(3, 6), (5, 7), (3, 9)]), WHITE, mirror=True, within=fm)
        s.paint(s.m_px([(9, 12)]), WHITE, mirror=True, within=fm)
        s.paint(s.m_line(10, 11, 13, 11), BLACK, mirror=True, within=fm)
        for x, y in ((7, 22), (10, 24)):
            s.paint(s.m_ellipse(x, y, 1.6, 1.6), BLACK, mirror=True, within=hm)
            s.paint(s.m_px([(x, y)]), "#5a8ae8", mirror=True, within=hm)
    butterfly(s, "#f08a3a", "#f08a3a", pattern=pat)


@sprite("american_copper")
def _(s):
    # Tiny and fiery: bright copper forewings with black dots, grey hindwings with an orange border.
    def pat(s, fm, hm):
        s.paint(s.m_poly([(1.5, 6), (5, 3), (5, 4.5), (3, 14), (2, 14)]), "#5a5a62", mirror=True, within=fm)
        s.paint(s.m_px([(7, 7), (10, 9), (6, 11), (9, 13), (12, 12)]), BLACK, mirror=True, within=fm)
        s.paint(s.m_poly([(4, 21), (8, 26), (10, 25), (6, 20)]), "#f0602a", mirror=True, within=hm)
    butterfly(s, "#f06a2a", "#6a6a72", body="#4a4a52", pattern=pat)


@sprite("common_ringlet")
def _(s):
    # Small, soft ochre-tan with one little eyespot near each forewing tip.
    def pat(s, fm, hm):
        s.paint(s.m_ellipse(5, 7, 1.2, 1.2), "#2a2220", mirror=True, within=fm)
        s.paint(s.m_px([(5, 7)]), WHITE, mirror=True, within=fm)
    butterfly(s, "#dcb878", "#cfa868", body="#7a6248", pattern=pat)


@sprite("gulf_coast_buck_moth")
def _(s):
    # Black wings crossed by a broad white band, and a red-orange tail tip.
    def pat(s, fm, hm):
        s.paint(s.m_poly([(4, 5), (7, 4), (13, 13), (9, 15)]), "#f2efe8", mirror=True, within=fm)
        s.paint(s.m_ellipse(9, 9.5, 1, 1.4, rot=-35), BLACK, mirror=True, within=fm)
        s.paint(s.m_ellipse(9, 21, 3.5, 2.5), "#f2efe8", mirror=True, within=hm)
        s.paint(s.m_ellipse(10, 21, 0.8, 1.3), BLACK, mirror=True, within=hm)
    butterfly(s, "#1e1c22", "#1e1c22", body="#2b2630", pattern=pat)
    s.ellipse(16, 23.5, 1.4, 1.8, "#e0502a")


@sprite("fall_webworm_moth")
def _(s):
    # A fluffy snow-white moth with a few black dots and orange "knees".
    def pat(s, fm, hm):
        s.paint(s.m_px([(6, 8), (9, 11), (11, 7)]), "#3a3434", mirror=True, within=fm)
    butterfly(s, "#f8f6f0", "#f2f0ea", body="#f0ece0", pattern=pat)
    s.ellipse(16, 11, 2.4, 2.6, "#fbfaf6")
    s.px([(13, 12), (18, 12)], "#f0a030")
    s.px([(15, 9), (17, 9)], EYE)


@sprite("rosy_maple_moth")
def _(s):
    # A fuzzy pink-and-yellow moth, like a little strawberry lemonade.
    def pat(s, fm, hm):
        s.paint(s.m_poly([(5, 8), (8, 5), (13, 12), (9, 14)]), "#f6e070", mirror=True, within=fm)
    butterfly(s, "#ec6aa0", "#f6e070", body="#f2d850", pattern=pat)
    s.ellipse(16, 11, 2.6, 2.8, "#f6e070")
    s.path([(15, 8), (12, 3), (10, 2)], 0.7, "#ec6aa0", shade=False)
    s.path([(16, 8), (19, 3), (21, 2)], 0.7, "#ec6aa0", shade=False)
    s.px([(14, 9), (17, 9)], EYE)


def _delta_moth(s, wing, mark, body):
    """A small moth resting with its wings folded into a flat triangle (top view)."""
    s.can("fly")
    k = (1.0, 1.35, 1.6, 1.35)[s.f] if s.act == "fly" else 1.0
    sq = lambda pts: [(16 + (x - 16) * k, y) for x, y in pts]  # noqa: E731
    m = s.poly(sq([(15.5, 9), (5, 25), (9, 28), (16, 24)]), wing, mirror=True, edge=True)
    mark(s, m)
    s.ellipse(16, 15, 2, 7, body)
    s.ellipse(16, 8.5, 3, 2.4, body, edge=True)
    s.path([(15, 8), (11, 12), (8, 18)], 0.5, mix(body, "#000000", 0.3), shade=False)
    s.path([(17, 8), (21, 12), (24, 18)], 0.5, mix(body, "#000000", 0.3), shade=False)
    s.eye(13, 8, size=2)
    s.eye(17, 8, size=2)


@sprite("celery_leaftier_moth")
def _(s):
    # A little brown triangle of a moth, with dark wavy lines across its wings.
    def mark(s, m):
        s.paint(s.m_path([(13, 15), (11, 18), (9, 18), (8, 21)], 0.45) | s.m_path([(14, 20), (12, 23), (10, 24)], 0.45),
                "#4a2e1e", mirror=True, within=m)
        s.paint(s.m_px([(12, 16), (13, 21)]), "#e0b080", mirror=True, within=m)
    _delta_moth(s, "#a8703a", mark, "#8a5a30")


def _caterpillar(s, n, body, head, fn):
    pts = _segmented(s, n, body, head, mix(body, "#000000", 0.4), leg_len=1.2, spacing=2.8, r=2.8, antenna=0)
    for i, (x, y) in enumerate(pts):
        fn(s, i, x, y)
    hx, hy = pts[0]
    s.ellipse(hx - 1, hy, 3.3, 3, head, edge=True)
    s.eye(round(hx - 2), round(hy - 1))
    return pts


@sprite("eastern_tent_caterpillar_moth")
def _(s):
    # The caterpillar: black and hairy with a white line down its back and blue spots on its sides.
    def seg(s, i, x, y):
        if i:
            s.px([(round(x), round(y - 2)), (round(x) - 1, round(y - 2))], WHITE)
            s.px([(round(x), round(y) + 1)], "#4a90e0")
            s.px([(round(x) + 1, round(y - 3))], "#c8783a")
    _caterpillar(s, 9, "#2a2228", "#1e1a1e", seg)


@sprite("banded_tussock_moth")
def _(s):
    # The caterpillar: a fuzzy pale tan bottlebrush with long black and white hair-pencils at each end.
    def seg(s, i, x, y):
        s.px([(round(x), round(y - 4)), (round(x + 1), round(y - 4))], "#f4ecd4")
        if i in (0, 1):
            s.path([(x, y - 2), (x - 3 + i, y - 8)], 0.45, BLACK if i == 0 else WHITE, shade=False)
        if i in (8, 9):
            s.path([(x, y - 2), (x + 3, y - 8 + (i - 8))], 0.45, BLACK if i == 9 else WHITE, shade=False)
        if 2 <= i <= 7 and i % 2 == 0:
            s.px([(round(x), round(y))], "#4a3a2a")
    _caterpillar(s, 10, "#d8c494", "#2b2226", seg)


# --------------------------------------------------------------------------- bees, flies and beetles
def _bumble(s, bands, wing="#e6f4fc"):
    """A side-view bee; bands is a list of (x0, x1, colour) stripes across the body."""
    s.can("fly")
    up = not (s.act == "fly" and s.f % 2)
    s.ellipse(20, 8 if up else 11, 4.5, 6.5 if up else 4, wing, rot=25 if up else 70, shade=False, edge=True)
    s.ellipse(25, 11 if up else 13, 3.5, 5 if up else 3, mix(wing, "#8aa0c0", 0.15), rot=40 if up else 80,
              shade=False, edge=True)
    m = s.ellipse(18, 19, 9, 7.5, bands[0][2])
    for x0, x1, c in bands:
        s.paint(s.m_poly([(x0, 8), (x1, 8), (x1, 30), (x0, 30)]), c, within=m)
    s.line(9, 25, 8, 29, "#2b2226")
    s.line(13, 25, 13, 29, "#2b2226")
    s.ellipse(8.5, 17, 5.5, 5.5, "#2b2226", edge=True)
    s.line(6, 12, 4, 6, "#2b2226")
    s.line(9, 12, 10, 6, "#2b2226")
    s.eye(5, 16, color="#11080f", shine="#ffffff")
    return m


@sprite("tricolored_bumble_bee")
def _(s):
    # Yellow, then a bright orange-red belt, then yellow and a black tail.
    _bumble(s, [(9, 16, "#f2c42a"), (16, 17.5, "#2b2226"), (17.5, 19.5, "#f2c42a"), (19.5, 24, "#e8602a"),
                (24, 25.5, "#f2c42a"), (25.5, 30, "#2b2226")])


@sprite("ligated_furrow_bee")
def _(s):
    # A small, slim dark bee with neat pale bands of hair across its abdomen.
    s.can("fly")
    up = not (s.act == "fly" and s.f % 2)
    s.ellipse(19, 10 if up else 12, 4, 6 if up else 3.6, "#e2ecf6", rot=25 if up else 70, shade=False, edge=True)
    m = s.ellipse(20, 20, 8.5, 5, "#3a3430", edge=True)
    for x in (16, 20, 24):
        s.paint(s.m_line(x, 14, x, 26) | s.m_line(x + 1, 14, x + 1, 26), "#e8dcc0", within=m)
    s.line(10, 23, 9, 28, "#2b2226")
    s.line(14, 23, 14, 28, "#2b2226")
    s.ellipse(12, 18, 4, 4, "#5a4a3a", edge=True)
    s.ellipse(6.5, 17, 4.2, 4.5, "#2b2226", edge=True)
    s.line(5, 13, 3, 7, "#2b2226")
    s.line(7, 13, 8, 7, "#2b2226")
    s.eye(4, 16, color="#11080f", shine="#ffffff")


def _hoverfly(s, marks):
    """A calligrapher flower fly from above: big red-brown eyes, clear wings, a slim yellow abdomen."""
    s.can("fly")
    up = not (s.act == "fly" and s.f % 2)
    s.ellipse(9.5, 14 if up else 18, 7, 2.4, "#e6f2fa", rot=-18 if up else 12, shade=False, edge=True, mirror=True)
    for y in (16, 19):
        s.line(13, y, 9, y + 3, "#3a2e22")
        s.line(18, y, 22, y + 3, "#3a2e22")
    m = s.ellipse(16, 22.5, 4, 8, "#f2c42a", edge=True)
    marks(s, m)
    s.ellipse(16, 13, 4, 3.2, "#4a4030", edge=True)
    s.paint(s.m_line(12, 12, 12, 14) | s.m_line(20, 12, 20, 14), "#f2c42a", within=s.last)
    s.ellipse(16, 8.5, 5, 3.4, "#f2d040", edge=True)
    s.ellipse(13, 8, 2.4, 2.8, "#9a3a22", shade=False, mirror=True)
    s.px([(12, 7)], WHITE, mirror=True)
    s.px([(13, 9)], EYE, mirror=True)


@sprite("margined_calligrapher")
def _(s):
    # A tiny flower fly: yellow abdomen neatly edged in black.
    def marks(s, m):
        s.paint(s.m_ellipse(16, 22.5, 4, 8) & ~s.m_ellipse(16, 22.5, 2.6, 7), "#1e1a1c", within=m)
        s.paint(s.m_line(13, 16, 19, 16) | s.m_px([(16, 20), (16, 23), (16, 26)]), "#1e1a1c", within=m)
    _hoverfly(s, marks)


@sprite("eastern_calligrapher")
def _(s):
    # Yellow abdomen with fancy black bands and loops, like handwriting.
    def marks(s, m):
        for y in (17, 21, 25):
            s.paint(s.m_path([(12, y + 1), (14, y), (16, y + 1), (18, y), (20, y + 1)], 0.5), "#1e1a1c", within=m)
        s.paint(s.m_px([(14, 23), (18, 23), (15, 27), (17, 27), (16, 29)]), "#1e1a1c", within=m)
    _hoverfly(s, marks)


@sprite("winter_firefly")
def _(s):
    # A dull black firefly with no light, and pink-and-yellow edges on its shield.
    beetle_top(s, "#26222a", head="#2b2630", pron="#e8b840")
    s.paint(s.m_ellipse(14, 11, 1.6, 1.2) | s.m_ellipse(18, 11, 1.6, 1.2), "#e86a8a")
    s.paint(s.m_line(16, 9, 16, 13), "#26222a")


@sprite("oriental_beetle")
def _(s):
    # A straw-coloured scarab splotched with black.
    beetle_top(s, "#d4b46a", head="#6a4a2a", pron="#b8904e",
               spots=[(10, 15), (21, 14), (12, 21), (19, 20), (9, 25), (22, 25), (15, 27)])
    s.paint(s.m_px([(13, 10), (19, 11), (16, 12)]), "#4a3220")


@sprite("reddish_brown_stag_beetle")
def _(s):
    # Shiny reddish-brown, with big curved jaws like antlers.
    s.path([(14, 5.5), (11, 2), (11, -1), (13, -2.5)], (1.1, 0.6), "#5a2414", mirror=True)
    s.px([(12, 0)], "#5a2414", mirror=True)
    beetle_top(s, "#8e3c1e", head="#6e2c16", pron="#7c3418")
    s.px([(11, 18), (20, 17), (12, 24)], "#c8704a")


@sprite("tan_jumping_spider")
def _(s):
    # Flat and fuzzy, mottled tan and grey with dark chevrons and big shiny front eyes.
    def pat(s, m):
        for y in (19, 23, 27):
            s.paint(s.m_path([(12, y - 1.5), (16, y + 0.5), (20, y - 1.5)], 0.5), "#4a3e30", within=m)
        s.paint(s.m_px([(14, 17), (18, 17), (16, 21), (16, 25)]), "#ece4d4", within=m)
    spider_top(s, "#b0a080", "#8a7a5e", pattern=pat, ceph="#a8987a", leg_bands="#4a3e30")
    s.eye(13, 11, size=2)
    s.eye(17, 11, size=2)


@sprite("seaside_dragonlet")
def _(s):
    # A small all-black salt-marsh dragonfly with smoky wing bases.
    dragonfly(s, "#2a2a36", "#24242e")
    s.paint(s.m_ellipse(14, 10, 2.5, 1.8) | s.m_ellipse(18, 10, 2.5, 1.8) | s.m_ellipse(14, 14, 2.5, 1.8)
            | s.m_ellipse(18, 14, 2.5, 1.8), "#6a6a7a")
    s.ellipse(16, 11, 2.6, 3.5, "#2a2a36", edge=True)
    s.px([(16, 9), (16, 10)], "#6a7aa0")


# --------------------------------------------------------------------------- crabs, lobsters and hermits
@sprite("asian_shore_crab")
def _(s):
    # A small square-ish mottled crab with banded legs and red dots on its claws.
    def pat(s, m):
        s.paint(s.m_px([(10, 17), (13, 19), (17, 17), (21, 19), (12, 23), (19, 22), (23, 21), (15, 21)]), "#7a4a6a",
                within=m)
        s.paint(s.m_px([(11, 20), (16, 19), (20, 23), (14, 24)]), "#9aa070", within=m)
    crab(s, "#5e6a48", "#8a6a5a", legs="#7a6a56", pattern=pat)
    legs = (s.reg >= 1) & (s.reg <= 6)
    s.paint(legs & ((_XS.astype(int) % 3) == 0), "#e0d4b0")
    s.px([(4, 9), (6, 10), (25, 10), (27, 9)], "#d02a2a")


@sprite("european_green_crab")
def _(s):
    # Mottled green with five little spikes along each side of its shell.
    def pat(s, m):
        s.paint(s.m_px([(11, 17), (15, 16), (19, 18), (22, 16), (13, 21), (18, 21)]), "#2e4a22", within=m)
        s.paint(s.m_ellipse(16, 25, 8, 2), "#c8b84a", within=m)
    crab(s, "#4e7a36", "#5a8a3a", legs="#4a6e30", pattern=pat)
    s.px([(7, 14), (6, 15), (5, 17), (5, 19), (5, 21)], "#4e7a36", mirror=True)


@sprite("jonah_crab")
def _(s):
    # A hefty brick-red crab with a rough, bumpy shell and black-tipped claws.
    def pat(s, m):
        s.paint(s.m_px([(10, 16), (13, 15), (17, 16), (21, 15), (12, 19), (19, 19), (23, 18)]), "#e89a6a", within=m)
        s.paint(s.m_ellipse(16, 25.5, 8, 1.8), "#f0c890", within=m)
    crab(s, "#c0583a", "#c86040", legs="#b05034", pattern=pat)
    s.px([(2, 8), (3, 8), (2, 9), (29, 8), (28, 8), (29, 9)], "#1e1a1c")


@sprite("atlantic_rock_crab")
def _(s):
    # Pale yellow, packed with tiny purple-red freckles.
    def pat(s, m):
        _speckle(s, m, "#a83a4a", 2)
    crab(s, "#ecc480", "#e4b470", legs="#d8a868", pattern=pat)
    _speckle(s, s.m_ellipse(5.5, 10, 3.6, 3) | s.m_ellipse(26.5, 10, 3.6, 3), "#a83a4a", 3)


@sprite("speckled_swimming_crab")
def _(s):
    # Sandy brown covered in white spots, with paddle-shaped back legs for swimming.
    def pat(s, m):
        _speckle(s, m, WHITE, 3)
    s.ellipse(2.5, 28, 2.4, 1.4, "#c49a6a", rot=-30)
    s.ellipse(29.5, 28, 2.4, 1.4, "#c49a6a", rot=30)
    crab(s, "#a8784e", "#b88a5c", legs="#a07454", pattern=pat)
    s.px([(5, 19), (4, 20), (26, 19), (27, 20)], "#a8784e")
    _speckle(s, s.m_ellipse(5.5, 10, 3.6, 3) | s.m_ellipse(26.5, 10, 3.6, 3), WHITE, 3)


@sprite("american_lobster")
def _(s):
    # Dark green-brown with orange speckles, one big crusher claw, a fan tail and long antennae.
    s.can("walk")
    w = s.wave() if s.act == "walk" else 0
    c, dark, acc = "#3e4e3a", "#26302a", "#e0803a"
    s.path([(9, 16), (13, 7), (22, 3), (33, 4)], 0.45, acc, shade=False)
    s.path([(8, 17), (11, 11), (17, 8), (26, 8)], 0.45, acc, shade=False)
    for i, y in enumerate((20, 22, 24)):
        d = w * 1.2 * (1 if i % 2 else -1)
        s.path([(14 + i, y), (12 + i, y + 4 + d), (11 + i, y + 7 + d)], 0.6, dark, shade=False)
    s.poly([(28, 20), (33, 15), (35, 21), (33, 26)], c)
    m = s.path([(14, 20), (20, 20.5), (25, 21), (29, 21)], (4, 2.4), c)
    for x in (19, 22, 25, 28):
        s.paint(s.m_line(x, 16, x, 25), dark, within=m)
    s.path([(9, 18), (6, 14)], 1.2, c)
    s.ellipse(3.5, 10, 4.5, 3, c, rot=-50, edge=True)
    s.paint(s.m_line(1, 8, 3, 11), dark)
    s.path([(9, 23), (5, 25)], 1.1, c)
    s.ellipse(2.5, 27, 4, 2, c, rot=20, edge=True)
    s.px([(0, 7), (-1, 26)], acc)
    hm = s.ellipse(12, 20, 5.5, 4.6, c, edge=True)
    s.paint(s.m_px([(12, 17), (14, 19), (11, 22), (15, 22)]), acc, within=hm)
    s.eye(9, 18)


def _hermit(s, shell, spiral, body, claw, *, long_claw=False, leg_mark=None):
    m = s.ellipse(20, 18, 9, 9, shell, edge=True)
    s.poly([(24, 10), (30, 6), (28, 13)], shell, edge=True)
    s.paint(s.m_path([(20, 18), (23, 15), (26, 18), (23, 23), (17, 22), (15, 16), (19, 11)], 0.5), spiral, within=m)
    for y in (23, 26):
        p = s.path([(11, y), (7, y + 2), (5, y + 5)], 0.8, body, shade=False)
        if leg_mark:
            s.paint(s.m_path([(11, y - 0.6), (7, y + 1.4), (5, y + 4.4)], 0.3), leg_mark, within=p)
    s.ellipse(9, 19, 5, 4, body, edge=True)
    if long_claw:
        cm = s.ellipse(3, 14.5, 5, 1.8, claw, rot=-25, edge=True)
        s.paint(s.m_line(0, 16, 6, 13), mix(claw, "#8a4a2a", 0.6), within=cm)
    else:
        s.ellipse(5, 14, 2.8, 2.2, claw, rot=-20)
    s.ellipse(7.5, 24, 2.2, 1.8, claw)
    s.line(8, 15, 4, 8, mix(body, "#000000", 0.2))
    s.line(10, 15, 11, 8, mix(body, "#000000", 0.2))
    s.px([(7, 17), (10, 17)], EYE)


@sprite("long_claw_hermit_crab")
def _(s):
    # A tiny pale hermit in a borrowed grey snail shell, waving one long, thin, striped claw.
    _hermit(s, "#9a948a", "#5a5650", "#e0d4c0", "#e8dcc8", long_claw=True, leg_mark="#c08a4a")


@sprite("thinstripe_hermit_crab")
def _(s):
    # Olive-brown legs and claws with thin white stripes, in a whelk shell.
    _hermit(s, "#c8a878", "#8a6a44", "#6a5a3a", "#6e5e3e", leg_mark="#f0ece0")
    s.paint(s.m_line(3, 13, 7, 15) | s.m_line(6, 23, 9, 24), "#f0ece0")


# --------------------------------------------------------------------------- snails and other shells
@sprite("shark_eye")
def _(s):
    # A round, glossy moon snail with a dark spiral "eye", gliding on a big foot.
    s.can("walk")
    st = (0, 1, 2, 1)[s.f] if s.act == "walk" else 0
    s.ellipse(15 - st / 2, 27, 14 + st / 2, 3, "#ecdcc8")
    m = s.ellipse(17, 17, 11, 10, "#c8b8a8", edge=True)
    s.paint(s.m_ellipse(20, 13, 5.5, 5) & ~s.m_ellipse(20.5, 13.3, 3.6, 3.2), "#5a4a6a", within=m)
    s.paint(s.m_ellipse(20.5, 13.3, 1.8, 1.6), "#3a2e48", within=m)
    s.paint(s.m_path([(26, 18), (24, 23), (17, 26), (9, 22)], 0.4), "#a89888", within=m)
    s.eye(10, 19)
    s.eye(16, 20)


@sprite("common_periwinkle")
def _(s):
    # A small, plump olive-brown snail shell with darker spiral bands and black-striped tentacles.
    s.ellipse(14, 28, 12, 2.2, "#5a5048")
    s.ellipse(7, 25, 5, 3, "#6a605a", edge=True)
    s.line(5, 22, 3, 17, "#2b2626")
    s.line(8, 22, 9, 17, "#2b2626")
    s.poly([(17, 13), (22, 5), (25, 13)], "#7a6448", edge=True)
    m = s.ellipse(18, 19, 9.5, 8.5, "#8a7254", edge=True)
    for r in (3, 5.5, 8):
        s.paint(s.m_ellipse(20, 17, r + 0.8, r + 0.7) & ~s.m_ellipse(20, 17, r, r), "#5a4634", within=m)
    s.paint(s.m_line(19, 7, 23, 11) | s.m_line(21, 6, 24, 10), "#5a4634")
    s.paint(s.m_ellipse(11, 24, 3, 2.2), "#ece0cc", within=m)
    s.eye(13, 19)
    s.eye(19, 19)


@sprite("common_atlantic_slippersnail")
def _(s):
    # Slipper-shaped shells that stack up on top of one another, streaked with brown.
    m = s.fill(s.m_ellipse(16, 26, 13, 7) & s.m_poly([(0, 0), (32, 0), (32, 28), (0, 28)]), "#ecdcc4", edge=True)
    s.paint(s.m_line(6, 22, 9, 27) | s.m_line(23, 21, 25, 27) | s.m_line(27, 24, 28, 27), "#a8704a", within=m)
    s.ellipse(16, 28.5, 13, 1.6, "#d8c8b0")
    t = s.fill(s.m_ellipse(19, 18, 9, 5.5) & s.m_poly([(0, 0), (32, 0), (32, 20), (0, 20)]), "#e4d0b0", edge=True)
    s.paint(s.m_line(13, 15, 15, 19) | s.m_line(21, 13, 23, 19), "#a8704a", within=t)
    s.eye(11, 23)
    s.eye(17, 23)


@sprite("brown_lipped_snail")
def _(s):
    # A lemon-yellow shell wrapped in dark brown bands, with a chocolate-brown lip.
    import numpy as np
    from archetypes import snail_shell
    sh = "#f0d850"
    snail_shell(s, sh, sh)
    shell = np.all(s.col == (240, 216, 80), axis=-1) & s.m_ellipse(16, 17, 10, 10)
    for r in (3.2, 6, 8.6):
        s.paint(s.m_ellipse(16.5, 17, r + 0.8, r + 0.8) & ~s.m_ellipse(16.5, 17, r, r), "#5a3a22", within=shell)
    s.paint(s.m_ellipse(16, 17, 10, 10) & ~s.m_ellipse(16, 17, 8.8, 8.8) & s.m_poly([(0, 18), (16, 18), (16, 32), (0, 32)]),
            "#3a2216")


# --------------------------------------------------------------------------- sea stars, jellies and others
@sprite("common_sea_star")
def _(s):
    # Orange-tan with a bright orange spot (its sieve plate) near the middle.
    star(s, "#d8783a", arms=0.48, dots="#f0b060")
    s.px([(19, 18), (20, 18), (19, 19)], "#f8a018")


@sprite("gray_sea_star")
def _(s):
    # Long slender lilac-grey arms, each with a dark stripe down the middle.
    star(s, "#b4aabd", arms=0.66, dots=None)
    for k in range(5):
        a = math.radians(-90 + k * 72)
        s.paint(s.m_line(16 + 7 * math.cos(a), 16.5 + 7 * math.sin(a), 16 + 13 * math.cos(a), 16.5 + 13 * math.sin(a)),
                "#5a4a6a")


@sprite("bay_nettle")
def _(s):
    # A milky-white sea nettle with long, fine white tentacles.
    jelly(s, "#eee6f0", rim="#e2d2e4", arms="#f6eef6", tentacles="#e8dcea", stripes="#dcc8de")


@sprite("atlantic_lions_mane_jelly")
def _(s):
    # A big red-orange bell trailing a shaggy mane of tentacles.
    w = s.wave() if s.act == "swim" else 0
    jelly(s, "#c8602a", rim="#e8a040", arms="#f0c060", tentacles="#e08a3a", stripes="#a04a20")
    for x0 in (6.5, 10.5, 15.5, 21.5, 25.5):
        s.path([(x0, 15), (x0 + 1 - w, 20), (x0 - 1 + w, 25), (x0 + w, 29)], 0.55, "#d8702a", shade=False)


@sprite("red_beard_sponge")
def _(s):
    # A bright red-orange sponge that grows in branching, beard-like fingers.
    c = "#e04a2a"
    s.ellipse(16, 29.5, 12, 2, "#8a8478")
    for pts in ([(14, 24), (9, 18), (7, 11)], [(18, 24), (23, 19), (25, 12)], [(15, 20), (13, 12), (12, 5)],
                [(17, 20), (19, 11), (21, 4)], [(10, 19), (4, 15), (2, 10)], [(22, 19), (28, 16), (30, 11)]):
        m = s.path(pts, (2.2, 1.3), c)
        s.paint(s.m_px([(round(pts[2][0]), round(pts[2][1]))]), "#f08a5a", within=m)
    m = s.ellipse(16, 23.5, 7, 5.5, c, edge=True)
    s.paint(s.m_px([(11, 21), (20, 20), (13, 27), (21, 26)]), "#b8301e", within=m)
    s.eye(13, 22)
    s.eye(18, 22)


@sprite("northern_acorn_barnacle")
def _(s):
    # Little white volcano shells on a rock; one is sweeping its feathery legs out to feed.
    s.ellipse(16, 29.5, 15, 2, "#6a6460")
    if s.act != "sleep":
        k = s.f % 2
        for dx in (-2, 0, 2):
            s.path([(16 + dx * 0.5, 10), (16 + dx * 1.5, 6 - k), (16 + dx * 2.5 + 1, 4 - k)], 0.45, "#e8c8a8",
                   shade=False)
    for x, top, hw in ((6, 21, 4.5), (26, 20, 4.5), (16, 11, 8)):
        m = s.poly([(x - hw, 29), (x - hw * 0.4, top), (x + hw * 0.4, top), (x + hw, 29)], "#ece8de", edge=True)
        for dx in (-0.5, 0, 0.5):
            s.paint(s.m_line(x + dx * hw * 0.8, top + 1, x + dx * hw * 1.6, 29), "#c8c0b0", within=m)
        s.paint(s.m_ellipse(x, top + 0.5, hw * 0.35, 0.9), "#4a4040", within=m)
    s.eye(13, 19)
    s.eye(18, 19)


@sprite("magnificent_bryozoan")
def _(s):
    # A wobbly jelly-like blob made of many tiny animals, patterned with little rosettes.
    w = s.wave() if s.act == "idle" else 0
    m = s.ellipse(16, 19.5 - w * 0.3, 13.5, 10 + w * 0.3, "#b8d0a0", edge=True)
    for cx, cy in ((8, 15), (14, 12), (21, 13), (26, 18), (7, 22), (24, 25), (16, 27), (10, 28)):
        for k in range(6):
            a = k * math.pi / 3
            s.paint(s.m_px([(round(cx + 2 * math.cos(a)), round(cy + 2 * math.sin(a)))]), "#5a8a4a", within=m)
        s.paint(s.m_px([(cx, cy)]), "#e8f0d8", within=m)
    s.eye(12, 19)
    s.eye(18, 19)
