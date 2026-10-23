"""Sprites for the Hawaii species that aren't on an earlier state's list (reef fish,
sea life, island birds, geckos and the rest)."""
from __future__ import annotations

import math

from archetypes import (BLACK, WHITE, _fluke, bird, butterfly, crab, dolphin, duck, frog, goose,
                        lizard, mammal, pinniped, quad, spider_top, sprite)
from pixel import mix


# --------------------------------------------------------------------------- helpers
def _bat(s, fur, wing, bone, *, frost=None, throat=None):
    """Front view with wings spread (the big_brown_bat pattern)."""
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
    m = s.ellipse(16, 19, 4.2, 6, fur, edge=True)
    if frost:
        s.paint(s.m_px([(14, 15), (17, 17), (15, 20), (18, 21), (13, 22), (16, 23), (14, 18)]), frost, within=m)
    if throat:
        s.paint(s.m_ellipse(16, 15.5, 2.6, 1.6), throat, within=m)
    s.poly([(12.5, 9.5), (11.5, 5.5), (15, 8.5)], wing)
    s.poly([(19.5, 9.5), (20.5, 5.5), (17, 8.5)], wing)
    s.ellipse(16, 11.5, 4, 3.6, fur, edge=True)
    if frost:
        s.paint(s.m_px([(14, 9), (18, 9), (16, 8)]), frost, within=s.last)
    s.ellipse(16, 13.3, 2, 1.3, wing)
    s.px([(15, 13), (17, 13)], "#1a1210")
    s.eye(14, 11)
    s.eye(18, 11)
    s.blush(13, 13)
    s.blush(19, 13)


def _reef(s, body, *, cx=16, cy=16, rx=9, ry=8, fin=None, tail=None, fins=None, dorsal=None, anal=None,
          snout=None, pattern=None, eye=(9, 12), lyre=False, tail_x=None, pec=True, mouth=None):
    """A reef fish facing left. `fins` (rx, ry) draws one big oval of fin behind the body,
    for the deep, disc-shaped fish; dorsal and anal are extra fin polygons."""
    s.can("swim")
    w = s.wave() if s.act == "swim" else 0
    fin = fin or mix(body, "#000000", 0.15)
    tail = tail or fin
    tx = tail_x or cx + rx - 1.5
    if lyre:
        pts = [(tx, cy - 1), (tx + 8, cy - 8), (tx + 5, cy - 2), (tx + 5, cy + 2), (tx + 8, cy + 8), (tx, cy + 1)]
    else:
        pts = [(tx - 1, cy - 1.5), (tx + 6, cy - 6), (tx + 5, cy), (tx + 6, cy + 6), (tx - 1, cy + 1.5)]
    _fluke(s, pts, tail, w, pivot_x=tx)
    if fins:
        s.ellipse(cx + 1, cy, fins[0], fins[1], fin)
    if dorsal:
        s.poly(dorsal, fin)
    if anal:
        s.poly(anal, fin)
    if snout:
        s.poly(snout, body)
    m = s.ellipse(cx, cy, rx, ry, body, edge=True)
    if pattern:
        pattern(s, m)
    if pec:
        s.ellipse(cx - 1, cy + 2, 2.6, 1.5, mix(fin, "#ffffff", 0.25), rot=25, shade=False)
    ex, ey = eye
    s.eye(ex, ey)
    s.blush(ex, ey + 3)
    if mouth:
        s.px(mouth, mix(body, "#000000", 0.5))
    return m


def _urchin_face(s, y=15):
    s.eye(12, y)
    s.eye(18, y)
    s.blush(10, y + 3)
    s.blush(20, y + 3)


# --------------------------------------------------------------------------- mammals
@sprite("hawaiian_monk_seal")
def _(s):
    pinniped(s, "#8a8c92", "#d8d4c8", flipper="#6a6c72")
    s.paint(s.m_px([(12, 20), (21, 19), (19, 25)]), "#a8a49a")


@sprite("small_indian_mongoose")
def _(s):
    def grizzle(s, b):
        bx, by, brx, bry = b["body"]
        s.paint(s.m_px([(14, 19), (17, 18), (20, 20), (23, 18), (25, 21), (16, 21), (22, 22)]), "#c8b088",
                within=s.m_ellipse(bx, by, brx, bry))
    quad(s, "#8a6a44", "#b89a70", build="low", ears="small", ear_in="#6a5034", tail="long", tail_col="#7a5c3a",
         tail_tip="#5a4028", nose="#2b2226", markings=grizzle)


@sprite("spinner_dolphin")
def _(s):
    # Three-tone: dark grey cape, pale grey flank, white belly, and a long thin beak.
    dolphin(s, "#4a5462", "#f0f0f2")
    s.paint(s.m_ellipse(14, 17.5, 9, 2), "#8a96a6", within=s.m_ellipse(15, 17, 11.5, 6))
    s.path([(2, 18.5), (-2.5, 19)], (1.0, 0.7), "#4a5462")
    s.eye(7, 15)


@sprite("pantropical_spotted_dolphin")
def _(s):
    dolphin(s, "#4a5266", "#9aa4b4")
    s.paint(s.m_px([(10, 13), (14, 12), (18, 13), (22, 14), (12, 16), (16, 15), (20, 16), (24, 17), (9, 19),
                    (13, 20), (17, 19), (21, 20)]), "#e8ecf2", within=s.m_ellipse(15, 17, 11.5, 6))
    s.px([(0, 19), (1, 19)], WHITE)  # white-tipped beak
    s.eye(7, 15)


@sprite("chital")
def _(s):
    # Bright rufous deer covered in white spots, with a white throat and tall antlers.
    def antlers(s, b):
        hx, hy = b["head"][:2]
        c = "#e0cca4"
        for dx, col in ((1.5, mix(c, "#1a1420", 0.25)), (0, c)):
            x, y = hx + 1 + dx, hy - 2.5
            s.path([(x, y), (x + 2, y - 4), (x + 2.5, y - 8)], 0.65, col, shade=False)
            s.path([(x + 0.5, y - 1), (x - 2, y - 2)], 0.5, col, shade=False)
            s.path([(x + 2, y - 5), (x + 0.5, y - 7.5)], 0.5, col, shade=False)

    def spots(s, b):
        bx, by, brx, bry = b["body"]
        pts = [(15, 15), (18, 14), (21, 15), (24, 14), (16, 18), (19, 17), (22, 18), (25, 17), (14, 20), (20, 20), (23, 20)]
        s.paint(s.m_px(pts), "#fbf4e4", within=s.m_ellipse(bx, by, brx, bry))
        hx, hy = b["head"][:2]
        s.paint(s.m_ellipse(hx - 1, hy + 2.5, 1.8, 1.3), WHITE)
    quad(s, "#c8743a", "#f4ece0", build="deer", ears="side", ear_in="#e8c0a8", tail="cotton", tail_col=WHITE,
         nose="#2b2226", feet="#4a3a30", behind=antlers, markings=spots)


@sprite("hawaiian_hoary_bat")
def _(s):
    _bat(s, "#8a7462", "#3e3230", "#241c1a", frost="#ece6dc", throat="#d8b46a")


@sprite("polynesian_rat")
def _(s):
    mammal(s, "#8a6e52", "#d8cab4", ears="round", ear_in="#e8a8a8", tail="rat", tail_col="#b89a8a",
           nose="#e88a90", head_r=(8, 7), feet="#e0c0b0")


# --------------------------------------------------------------------------- birds
@sprite("red_crested_cardinal")
def _(s):
    def face(s):
        s.paint(s.m_ellipse(10, 16.5, 3.5, 3), "#d8202a")
    s.poly([(9, 7), (10, -1), (13, 2), (15, 7)], "#d8202a")
    bird(s, "#7a7a84", WHITE, head="#d8202a", wing="#6a6a74", tail_col="#4a4a54", beak="cone",
         beak_col="#e8dcd0", legs="#5a4a44", tail="mid", face=face)


@sprite("yellow_billed_cardinal")
def _(s):
    def face(s):
        s.paint(s.m_ellipse(10, 16.5, 3, 2.6), "#c8182a")
    bird(s, "#2a2830", WHITE, head="#c8182a", wing="#222028", tail_col="#1a181e", beak="cone",
         beak_col="#f0a02a", legs="#4a3a3a", tail="mid", face=face)


@sprite("zebra_dove")
def _(s):
    # Small grey-brown dove barred black and white, with blue skin around the eye.
    def bars(s, m):
        for y in (15, 17, 19, 21, 23):
            s.paint(s.m_line(9, y, 22, y - 1), "#3a3036", within=m)

    def face(s):
        s.ellipse(8.5, 10.5, 2, 2, "#8ab4e0", shade=False)
        for y in (13, 15):
            s.paint(s.m_line(9, y, 15, y), "#4a4046", within=s.m_ellipse(11, 11, 6.5, 6))
    bird(s, "#a8968a", "#e8c8c0", head="#b0b4c0", wing="#9a8a7a", tail_col="#7a6a5e", beak="thin",
         beak_col="#7a8aa8", legs="#e88a8a", tail="long", wing_mark=bars, face=face)
    s.paint(s.m_line(13, 21, 18, 21) | s.m_line(12, 23, 17, 23), "#5a4a50", within=s.m_ellipse(16.5, 20, 8, 7))


@sprite("spotted_dove")
def _(s):
    # Pinkish-brown dove with a black collar dotted with white.
    def collar(s):
        h = s.last
        s.paint(s.m_ellipse(15, 14.5, 3.5, 3), BLACK, within=h)
        s.paint(s.m_px([(14, 13), (16, 13), (15, 15), (13, 15), (17, 15), (14, 16), (16, 16)]), WHITE, within=h)
    bird(s, "#9a7a66", "#d8b0a8", head="#b0a0a8", wing="#8a6a56", tail_col="#6a5244", beak="thin",
         beak_col="#3a2e30", legs="#e07a7a", tail="long", face=collar,
         wing_mark=lambda s, m: s.paint(s.m_px([(18, 18), (21, 17), (20, 20)]), "#5a4436", within=m))


@sprite("common_myna")
def _(s):
    # Brown with a black head, yellow bill, yellow eye skin and white wing flash.
    def face(s):
        s.ellipse(9, 11, 2.2, 2.2, "#f0c82a", shade=False)

    def wing(s, m):
        s.paint(s.m_ellipse(22, 22, 2.5, 1.3), WHITE, within=m)
    bird(s, "#7a5038", "#9a6a4c", head="#24202a", wing="#5a3a2a", tail_col="#24202a", beak="cone",
         beak_col="#f0c82a", legs="#f0c82a", tail="mid", face=face, wing_mark=wing)
    s.paint(s.m_ellipse(13.5, 25.5, 3, 1.5), WHITE)


@sprite("pacific_golden_plover")
def _(s):
    # Breeding plumage: gold-spangled back, black face and belly, white border between.
    def wing(s, m):
        s.paint(s.m_px([(17, 17), (19, 18), (21, 17), (23, 19), (18, 20), (22, 21), (20, 22)]), "#f0c040", within=m)

    def face(s):
        h = s.last
        s.paint(s.m_ellipse(9, 14, 4.5, 3.4), BLACK, within=h)
        s.paint(s.m_path([(5, 9), (11, 8.5), (15, 12), (15, 17)], 0.7), WHITE, within=h)
        s.paint(s.m_px([(10, 6), (12, 7), (14, 8), (13, 5)]), "#f0c040", within=h)
    bird(s, "#6a5a3a", "#24202a", head="#6a5a3a", wing="#5a4a30", tail_col="#4a3a2a", beak="thin",
         beak_col="#1d1a20", legs="#3a3a40", tail="short", wing_mark=wing, face=face)
    s.paint(s.m_px([(17, 15), (20, 14), (23, 16), (15, 14)]), "#f0c040", within=s.m_ellipse(16.5, 20, 8, 7))


@sprite("hawaiian_goose")
def _(s):
    # Nene: black face and crown, buff cheeks, a creamy neck with dark furrows, barred body.
    goose(s)
    neck = s.m_path([(12, 19), (10, 13), (10, 8)], 2.3)
    s.paint(neck, "#e8d8b0")
    for y in (11, 13, 15, 17):
        s.paint(s.m_line(8, y, 13, y), "#9a8a6a", within=neck)
    s.paint(s.m_ellipse(11, 8.5, 2.8, 2), "#e8c890")
    for x in (19, 22, 25):
        s.paint(s.m_line(x, 19, x + 2, 27), "#7a6a58", within=s.m_ellipse(19, 23, 10.5, 6.5))


@sprite("saffron_finch")
def _(s):
    def face(s):
        s.paint(s.m_ellipse(11, 6.5, 4.5, 2.6), "#f08a1a", within=s.last)

    def wing(s, m):
        for y in (19, 21):
            s.paint(s.m_line(16, y, 24, y - 1), "#8a8a3a", within=m)
    bird(s, "#f2d020", "#f8e24a", head="#f4d424", wing="#c8b030", tail_col="#a8962a", beak="cone",
         beak_col="#9a9088", legs="#c89a7a", tail="mid", face=face, wing_mark=wing)


@sprite("white_rumped_shama")
def _(s):
    # Glossy black above, rich orange belly, a white rump and a very long tail.
    s.path([(20, 18), (28, 10), (35, 2)], (2, 1.6), BLACK)
    s.path([(21, 19), (29, 12), (35, 5)], 0.6, WHITE, shade=False)
    bird(s, "#1e1a24", "#e0782a", head="#1e1a24", wing="#16141c", tail_col="#1e1a24", beak="thin",
         beak_col="#1a1a20", legs="#e8b8a0", tail="long")
    s.ellipse(23, 17, 2.4, 1.6, WHITE)


@sprite("warbling_white_eye")
def _(s):
    def face(s):
        s.paint(s.m_ellipse(9, 15, 3.5, 2.4), "#f0e040", within=s.last)
        s.ellipse(8.5, 10.5, 2.4, 2.4, WHITE, shade=False)
    bird(s, "#8aaa3a", "#e8e4d8", head="#9ab840", wing="#6a8a2a", tail_col="#5a7a2a", beak="thin",
         beak_col="#3a3a40", legs="#5a5a60", tail="mid", face=face)


@sprite("java_sparrow")
def _(s):
    # Soft grey with a black cap, big white cheeks and a huge pink bill.
    def face(s):
        h = s.last
        s.paint(s.m_ellipse(12, 7, 6, 3.4), BLACK, within=h)
        s.paint(s.m_ellipse(10, 13, 3.6, 2.6), WHITE, within=h)
        s.ellipse(8.5, 10.5, 1.7, 1.7, "#e8506a", shade=False)
    bird(s, "#8a96a8", "#d8b8c0", head=BLACK, wing="#7a8698", tail_col="#2a2830", beak="cone",
         beak_col="#e8506a", legs="#e8a0a8", tail="mid", face=face)
    s.poly([(6, 9), (1.5, 11.8), (6, 14.5)], "#e8506a")


@sprite("common_waxbill")
def _(s):
    def face(s):
        s.paint(s.m_poly([(4, 9.5), (13, 9), (13, 11.5), (4, 12)]), "#e02a3a", within=s.last)

    def bars(s, m):
        for y in (21, 23, 25):
            s.paint(s.m_line(9, y, 18, y), "#b89a88", within=m)
    bird(s, "#9a8070", "#e8d4c8", head="#a89080", wing="#8a6e5e", tail_col="#6a5246", beak="cone",
         beak_col="#e02a3a", legs="#8a6a6a", tail="long", face=face, belly_mark=bars)
    s.paint(s.m_ellipse(14, 25, 2, 1.2), "#e85a6a", within=s.m_ellipse(13.5, 22, 5.5, 4.5))


@sprite("red_vented_bulbul")
def _(s):
    # Sooty with a black crested head, scaly breast and a red patch under the tail.
    def scales(s, m):
        s.paint(s.m_px([(10, 20), (13, 21), (16, 20), (11, 23), (14, 23), (17, 22)]), "#d8d0c8", within=m)
    s.poly([(10, 7), (12, 1), (15, 7)], "#1e1a22")
    bird(s, "#6a5a54", "#8a7c76", head="#1e1a22", wing="#5a4a44", tail_col="#2a2228", beak="thin",
         beak_col="#1a1a20", legs="#2a2228", tail="mid", belly_mark=scales)
    s.ellipse(21.5, 24.5, 2.6, 1.8, "#d8202a")
    s.paint(s.m_ellipse(25, 20, 2, 1.2), WHITE)


@sprite("apapane")
def _(s):
    # Crimson honeycreeper with black wings and tail, white under the tail, curved black bill.
    bird(s, "#d01e2e", "#e0303e", head="#d81e30", wing="#1e1a22", tail_col="#1e1a22", beak="thin",
         beak_col="#1d1a20", legs="#2a2228", tail="mid")
    s.path([(5.5, 11.5), (2, 12.5), (0.5, 14.5)], (0.9, 0.5), "#1d1a20", shade=False)
    s.ellipse(21.5, 25, 2.4, 1.5, WHITE)


@sprite("i_iwi")
def _(s):
    # Scarlet with black wings and a long, deeply curved salmon-pink bill.
    def wing(s, m):
        s.paint(s.m_ellipse(17, 18, 1.8, 1), WHITE, within=m)
    bird(s, "#e0322a", "#ea4a3a", head="#e8382c", wing="#1e1a22", tail_col="#1e1a22", beak="thin",
         beak_col="#e8907a", legs="#e8907a", tail="mid", wing_mark=wing)
    s.path([(5.5, 11.5), (1.5, 12.5), (-1, 15), (-1.5, 18)], (1.1, 0.5), "#f09a80", shade=False)


@sprite("hawai_i_amakihi")
def _(s):
    def face(s):
        s.paint(s.m_line(5, 10, 8, 10), "#3a3a2a", within=s.last)
    bird(s, "#a8b82a", "#e8e040", head="#b8c830", wing="#8a9a2a", tail_col="#6a7a2a", beak="thin",
         beak_col="#3a3a40", legs="#4a4a50", tail="mid", face=face)
    s.path([(5.5, 11.5), (2, 12.5), (0.5, 14)], (0.8, 0.45), "#3a3a40", shade=False)


@sprite("yellow_fronted_canary")
def _(s):
    def face(s):
        h = s.last
        s.paint(s.m_ellipse(11, 9, 5, 1.2), "#f8e030", within=h)
        s.paint(s.m_line(6, 13, 10, 14), "#5a6a2a", within=h)
        s.paint(s.m_ellipse(13, 6, 3, 1.4), "#8a9a6a", within=h)
    bird(s, "#9aa83a", "#f6e030", head="#c8c03a", wing="#6a7a2a", tail_col="#5a6a2a", beak="cone",
         beak_col="#c8b8a8", legs="#8a7a6a", tail="mid", face=face)


@sprite("rose_ringed_parakeet")
def _(s):
    def face(s):
        s.paint(s.m_path([(8, 16), (12, 17), (15, 14)], 0.6), BLACK, within=s.last)
        s.paint(s.m_path([(14, 14), (16, 10)], 0.6), "#f08aa8", within=s.last)
    s.path([(22, 18), (30, 12), (35, 4)], (2.2, 0.8), "#4ab04a")
    bird(s, "#5ac85a", "#9ae07a", head="#6ad86a", wing="#3aa04a", tail_col="#4ab04a", beak="hook",
         beak_col="#d8202a", legs="#8a8a90", tail="long", face=face)


@sprite("chestnut_munia")
def _(s):
    def face(s):
        s.paint(s.m_ellipse(9, 14, 4, 3), BLACK, within=s.last)
    bird(s, "#8a4020", "#6a2e18", head=BLACK, wing="#7a3618", tail_col="#6a3016", beak="cone",
         beak_col="#a8b8d0", legs="#6a6a78", tail="short", face=face)
    s.poly([(6, 9), (1.5, 11.8), (6, 14.5)], "#a8b8d0")


@sprite("scaly_breasted_munia")
def _(s):
    def scales(s, m):
        for x, y in ((10, 20), (13, 21), (16, 20), (11, 23), (14, 23), (17, 22), (9, 22)):
            s.paint(s.m_px([(x, y), (x + 1, y + 1), (x - 1, y + 1)]), "#6a4a34", within=m)

    def face(s):
        s.paint(s.m_ellipse(9, 13, 4, 3), "#6a3a20", within=s.last)
    bird(s, "#8a6040", WHITE, head="#8a5a38", wing="#7a5234", tail_col="#a89040", beak="cone",
         beak_col="#3a3436", legs="#6a6a70", tail="short", face=face, belly_mark=scales)
    s.poly([(6, 9.5), (2, 11.8), (6, 14)], "#3a3436")


@sprite("red_billed_leiothrix")
def _(s):
    def face(s):
        h = s.last
        s.paint(s.m_ellipse(10, 16, 4, 2.6), "#f0b030", within=h)
        s.paint(s.m_ellipse(9, 11, 2.4, 1.6), "#e8e0b0", within=h)

    def wing(s, m):
        s.paint(s.m_line(16, 20, 24, 18), "#f0a020", within=m)
        s.paint(s.m_line(16, 21, 22, 20), "#d8402a", within=m)
    bird(s, "#7a8a5a", "#f6d040", head="#8a9a6a", wing="#5a6a4a", tail_col="#3a3a3a", beak="cone",
         beak_col="#e0302a", legs="#d8b090", tail="fan", face=face, wing_mark=wing)
    s.paint(s.m_ellipse(12, 19.5, 4, 2), "#f08a20", within=s.m_ellipse(13.5, 22, 5.5, 4.5))


@sprite("grey_francolin")
def _(s):
    # Chunky game bird finely barred buff and brown, with a rusty-orange throat.
    def bars(s, m):
        for y in (19, 21, 23, 25):
            s.paint(s.m_line(9, y, 19, y), "#7a6248", within=m)

    def wing(s, m):
        s.paint(s.m_px([(17, 17), (19, 18), (21, 17), (18, 20), (22, 20), (20, 21)]), "#e8dcc0", within=m)

    def face(s):
        s.paint(s.m_ellipse(9, 15, 3.6, 2.4), "#e08a3a", within=s.last)
        s.paint(s.m_path([(6, 13), (10, 17.5), (14, 15)], 0.5), BLACK, within=s.last)
    bird(s, "#a89070", "#d8c8a8", head="#b09a76", wing="#8a7458", tail_col="#a0603a", beak="cone",
         beak_col="#4a3a34", legs="#c8603a", tail="short", face=face, belly_mark=bars, wing_mark=wing, big=True)


@sprite("kalij_pheasant")
def _(s):
    # Male: blue-black with white-scaled back, red face skin, a drooping crest, long tail.
    s.path([(22, 18), (29, 22), (35, 28)], (2.4, 1.2), "#1e1e2a")
    s.path([(13, 7), (19, 5), (22, 8)], (1.6, 0.8), "#2a2a3a")

    def wing(s, m):
        for x, y in ((16, 17), (19, 16), (22, 18), (18, 20), (21, 21), (24, 20)):
            s.paint(s.m_px([(x, y), (x + 1, y)]), "#d8d8e0", within=m)

    def face(s):
        s.ellipse(8.5, 11, 2.8, 2.6, "#d8202a", shade=False)
    bird(s, "#2a2a3a", "#4a4a5a", head="#2a2a3a", wing="#24243a", tail_col="#1e1e2a", beak="cone",
         beak_col="#d8ccb8", legs="#8a8a90", tail="mid", face=face, wing_mark=wing, big=True)


@sprite("hawaiian_coot")
def _(s):
    # ʻAlae keʻokeʻo: slate-black with a big white bill and white forehead shield.
    duck(s, "#3e3e48", "#4a4a54", "#24242a", bill=WHITE, ring=None, speculum="#3e3e48", tail_col=WHITE)
    s.ellipse(5.5, 8.5, 2, 2.2, WHITE)
    s.eye(7, 10, color="#c8202a")


@sprite("wandering_tattler")
def _(s):
    def bars(s, m):
        for y in (20, 22, 24):
            s.paint(s.m_line(9, y, 18, y), "#7a8088", within=m)

    def face(s):
        s.paint(s.m_line(5, 9, 11, 9), WHITE, within=s.last)
    bird(s, "#7a828c", "#dcdee2", head="#868e98", wing="#6a727c", tail_col="#5a626c", beak="long",
         beak_col="#2b2630", legs="#e8d040", tail="short", belly_mark=bars, face=face)


@sprite("laysan_albatross")
def _(s):
    # Mōlī: white head and body, dark brown back and wings, a pink hooked bill.
    def face(s):
        s.paint(s.m_ellipse(9.5, 10.5, 2.5, 1.6), "#7a7078", within=s.last)
    bird(s, WHITE, WHITE, head=WHITE, wing="#3a302e", tail_col="#3a302e", beak="hook",
         beak_col="#e8a0a0", legs="#e8b0b8", tail="short", face=face, big=True)
    s.px([(2, 13), (2, 14)], "#5a4a50")


@sprite("red_footed_booby")
def _(s):
    def wing(s, m):
        s.paint(s.m_ellipse(25, 20, 4, 3), "#1e1a22", within=m)

    def face(s):
        s.paint(s.m_ellipse(6.5, 12, 1.8, 2), "#e88aa8", within=s.last)
    bird(s, WHITE, WHITE, head="#f4f0e0", wing="#e8e8ec", tail_col=WHITE, beak="crow",
         beak_col="#8ab0d8", legs="#e8202a", tail="mid", wing_mark=wing, face=face)
    s.px([(12, 29), (13, 29), (16, 29), (17, 29), (11, 29), (15, 29)], "#e8202a")


@sprite("blue_billed_white_tern")
def _(s):
    # Manu-o-Kū: all white with a big black eye and a blue-based black bill.
    bird(s, WHITE, WHITE, head=WHITE, wing="#eceef2", tail_col="#e4e6ec", beak="crow", beak_col=BLACK,
         legs="#3a5a8a", tail="mid")
    s.poly([(6, 10), (4, 11), (4, 13), (6, 13.5)], "#3a6ad8")
    s.ellipse(8.5, 10.5, 2.2, 2.2, BLACK, shade=False)
    s.eye(8, 10)


@sprite("wedge_tailed_shearwater")
def _(s):
    s.poly([(20, 19), (29, 15), (31, 18), (29, 21), (23, 23)], "#4a3e3a")
    bird(s, "#5a4a44", "#f2eee8", head="#5a4a44", wing="#4a3c36", tail_col="#4a3e3a", beak="hook",
         beak_col="#7a7a80", legs="#e8b8b0", tail="short")


@sprite("great_frigatebird")
def _(s):
    # ʻIwa: black, with a forked tail, hooked bill and a big red throat pouch.
    s.poly([(21, 18), (34, 6), (27, 16), (35, 15), (24, 22)], "#1e1a22")
    bird(s, "#26222c", "#2e2a34", head="#26222c", wing="#1e1a24", tail_col="#1e1a22", beak="long",
         beak_col="#8a8a94", legs="#3a3438", tail="short")
    s.px([(-1, 13), (-1, 14)], "#8a8a94")
    s.ellipse(9, 18.5, 4, 3.6, "#e8202a", edge=True)
    s.px([(8, 17), (9, 17)], "#ff8a8a")


@sprite("red_tailed_tropicbird")
def _(s):
    s.path([(26, 14), (31, 9), (35, 3)], (0.6, 0.6), "#e8202a", shade=False)
    s.path([(27, 15), (32, 11), (35, 7)], (0.6, 0.6), "#d81a24", shade=False)

    def face(s):
        s.paint(s.m_poly([(5, 9), (12, 9.5), (13, 11), (6, 11)]), BLACK, within=s.last)
    bird(s, WHITE, WHITE, head=WHITE, wing="#f0f0f2", tail_col="#eceef0", beak="crow", beak_col="#e8202a",
         legs="#4a4a50", tail="short", face=face,
         wing_mark=lambda s, m: s.paint(s.m_px([(17, 18), (19, 17), (21, 19), (23, 18)]), "#3a3a40", within=m))


@sprite("white_tailed_tropicbird")
def _(s):
    s.path([(26, 14), (31, 9), (35, 3)], (0.7, 0.6), WHITE, shade=False)
    s.path([(27, 15), (32, 11), (35, 7)], (0.7, 0.6), "#f0f0f4", shade=False)

    def face(s):
        s.paint(s.m_poly([(5, 9), (12, 9.5), (13, 11), (6, 11)]), BLACK, within=s.last)

    def wing(s, m):
        s.paint(s.m_line(15, 19, 24, 16) | s.m_line(15, 20, 24, 17), BLACK, within=m)
    bird(s, WHITE, WHITE, head=WHITE, wing="#f0f0f2", tail_col="#eceef0", beak="crow", beak_col="#f0c020",
         legs="#4a4a50", tail="short", face=face, wing_mark=wing)


# --------------------------------------------------------------------------- reptiles
@sprite("gold_dust_day_gecko")
def _(s):
    def pat(s, m):
        s.paint(s.m_px([(9, 19), (11, 20), (12, 19), (14, 20), (10, 21)]), "#f0d040", within=m)
        s.paint(s.m_px([(16, 19), (18, 20), (20, 19), (17, 21)]), "#d84a3a", within=m)
    lizard(s, "#4ac83a", "#d8f0a0", smooth=True, eye_big=True, pattern=pat, legs="#3ab030", tail_col="#3ab84a")
    s.paint(s.m_px([(4, 15), (8, 15), (8, 18), (4, 19)]), "#4a8ae8")  # blue eye ring
    s.paint(s.m_px([(9, 15), (10, 16), (11, 15), (10, 17), (12, 17)]), "#f0d040")
    s.paint(s.m_line(2, 18, 4, 18), "#d84a3a")


@sprite("mourning_gecko")
def _(s):
    def pat(s, m):
        for x in (10, 14, 18):
            s.paint(s.m_path([(x, 19), (x + 1.5, 20.5), (x, 22)], 0.5), "#4a3a2a", within=m)
        s.paint(s.m_px([(12, 21), (16, 21), (20, 21)]), "#f0e4c8", within=m)
    lizard(s, "#c8a878", "#f0e4cc", smooth=True, eye_big=True, pattern=pat, legs="#b89868", tail_col="#b89868")
    s.paint(s.m_line(1, 18, 9, 17), "#5a4430")
    s.eye(5, 16, size=3)
    s.px([(5, 16)], WHITE)


@sprite("asian_house_gecko")
def _(s):
    def pat(s, m):
        s.paint(s.m_px([(10, 20), (13, 19), (16, 20), (19, 19), (12, 22), (18, 22)]), "#9a8a7a", within=m)
    lizard(s, "#d8cbb8", "#f4ece0", smooth=True, eye_big=True, pattern=pat, legs="#c8baa6", tail_col="#d0c2ae")
    s.px([(23, 22), (25, 23), (27, 23), (29, 21)], "#f4ece0")  # spiny tail rings
    s.px([(24, 24), (26, 25), (28, 24), (30, 19)], "#9a8a7a")


@sprite("common_four_clawed_gecko")
def _(s):
    def pat(s, m):
        s.paint(s.m_px([(10, 19), (11, 20), (14, 19), (15, 20), (18, 19), (19, 20), (12, 22), (17, 22)]), "#5a4e46",
                within=m)
    lizard(s, "#9a8e84", "#e0d8cc", smooth=True, eye_big=True, wide=True, pattern=pat, legs="#8a7e74",
           tail_col="#8a7e74")
    s.paint(s.m_line(2, 17, 9, 17), "#5a4e46")
    s.eye(5, 16, size=3)
    s.px([(5, 16)], WHITE)


@sprite("dark_flecked_garden_sunskink")
def _(s):
    def pat(s, m):
        s.paint(s.m_px([(9, 20), (12, 19), (15, 20), (18, 19), (21, 20), (11, 22), (17, 22)]), "#2e241c", within=m)
        s.paint(s.m_line(8, 21, 22, 21), "#5a4030", within=m)
    lizard(s, "#8a6a48", "#e8dcc4", smooth=True, pattern=pat, legs="#7a5a3a",
           tail_pts=[(20, 22), (27, 25), (33, 24), (36, 20)])


@sprite("mottled_snake_eyed_skink")
def _(s):
    def pat(s, m):
        s.paint(s.m_px([(9, 19), (11, 20), (13, 19), (16, 20), (18, 19), (20, 20), (12, 22), (17, 22)]), "#4a3e2e",
                within=m)
        s.paint(s.m_px([(10, 19), (14, 20), (19, 19)]), "#d8c8a0", within=m)
        s.paint(s.m_line(8, 18, 22, 18), "#c8b480", within=m)
    lizard(s, "#9a8458", "#d8d0b8", smooth=True, pattern=pat, legs="#8a7448",
           tail_pts=[(20, 22), (27, 25), (33, 24), (36, 20)])


@sprite("jacksons_chameleon")
def _(s):
    # Bright green with three horns, a casque and a coiled tail, holding a twig.
    s.path([(-2, 29), (34, 28)], 1.0, "#7a5a3a")
    s.path([(20, 21), (26, 23), (29, 21), (28, 18), (25, 18), (25, 20)], (2.4, 0.9), "#3aa04a")
    lizard(s, "#4ab84a", "#a8e070", head="#5ac85a", wide=True, eye_big=True, legs="#3aa040",
           tail_pts=[(20, 22), (20.5, 22)], tail_col="#4ab84a",
           pattern=lambda s, m: s.paint(s.m_line(9, 23, 21, 22), "#e8e060", within=m))
    s.poly([(7, 15), (10, 11), (12, 15)], "#5ac85a")  # casque
    s.px([(9, 17), (12, 17), (14, 18), (16, 18), (18, 18)], "#3a8a3a")
    for p in ([(3, 17), (-1, 14)], [(6, 14), (3, 10)], [(9, 14), (7, 10)]):
        s.path(p, (0.8, 0.4), "#d8e0a0", shade=False)


@sprite("brahminy_blindsnake")
def _(s):
    # A tiny shiny worm-like snake, dark brown with a paler snout and a blunt tail.
    s.can("walk")
    w = s.wave() if s.act == "walk" else 0
    pts = [(30, 25), (26, 22 + w), (21, 25), (17, 28 - w), (12, 26), (8, 23 + w * 0.5)]
    s.path(pts, (1.4, 1.9), "#4a3640", edge=True)
    s.paint(s.m_path([(p[0] - 0.5, p[1] - 1) for p in pts], 0.4), "#8a7480")
    s.ellipse(6, 22, 3.6, 2.8, "#5a4450", edge=True)
    s.paint(s.m_ellipse(3.5, 22.5, 1.5, 1.6), "#8a7078")
    s.px([(30, 26)], "#2a1e24")
    if s.act != "sleep" and s.f % 2 == 0:
        s.px([(1, 24), (0, 24), (-1, 23), (-1, 25)], "#e04a5a")
    s.eye(5, 20, size=1)
    s.blush(6, 23)


# --------------------------------------------------------------------------- amphibians
@sprite("common_coqui")
def _(s):
    frog(s, "#a88a64", "#f0e4cc", pads=True, stripe="#d8c09a", spots=[(12, 21), (20, 21), (16, 24)])
    s.paint(s.m_path([(10, 13), (16, 15), (22, 13)], 0.5), "#d8c09a")


@sprite("green_and_black_poison_dart_frog")
def _(s):
    frog(s, "#3ad87a", "#2ac06a", pads=True)
    for x, y, rx, ry in ((9, 14, 2, 1.5), (16, 12.5, 2.4, 1.2), (23, 14, 2, 1.5), (12, 21, 2, 1.6),
                         (20, 21, 2, 1.6), (5, 26, 2, 1.2), (27, 26, 2, 1.2), (16, 26, 2.4, 1.3)):
        s.paint(s.m_ellipse(x, y, rx, ry), "#1a1a22")


@sprite("wrinkled_frog")
def _(s):
    frog(s, "#7a6040", "#d8ccb0", tympanum="#5a4630", spots=[(11, 21), (15, 19), (20, 21), (17, 24), (13, 25)])
    for y in (19, 22):
        s.paint(s.m_line(9, y, 23, y), "#5a4630", within=s.m_ellipse(16, 22, 9.5, 7))


# --------------------------------------------------------------------------- invertebrates
@sprite("african_giant_snail")
def _(s):
    s.can("walk")
    stretch = (0, 1, 2, 1)[s.f] if s.act == "walk" else 0
    s.ellipse(14 - stretch / 2, 27, 13 + stretch / 2, 2.6, "#8a7a6a")
    # a tall spiral shell: whorls getting smaller toward the tip, with dark flame streaks
    for cx, cy, r, c in ((28.5, 3, 1.8, "#e8c890"), (26.5, 6, 2.8, "#c89a5a"), (23.5, 10.5, 4.2, "#a8743a"),
                         (18.5, 17.5, 7.5, "#9a6230")):
        m = s.ellipse(cx, cy, r, r * 0.9, c, edge=True)
        for k in (-1, 1):
            s.paint(s.m_line(cx + k * r * 0.4 - 1, cy - r * 0.7, cx + k * r * 0.4 + 1, cy + r * 0.7), "#5a3418",
                    within=m)
    s.paint(s.m_px([(15, 14), (21, 13), (13, 19), (22, 20), (18, 22)]), "#e8c890", within=m)
    if s.act == "sleep":
        return
    s.ellipse(6 - stretch, 23, 5, 3.5, "#9a8a7a", edge=True)
    s.line(4 - stretch, 20, 2 - stretch, 15, "#9a8a7a")
    s.line(7 - stretch, 20, 8 - stretch, 15, "#9a8a7a")
    s.eye(4 - stretch, 22)
    s.blush(6 - stretch, 24)


@sprite("hawaiian_garden_spider")
def _(s):
    # Argiope: a lobed silver-and-yellow abdomen and banded legs, on a zigzag web.
    def pat(s, m):
        for y in (17, 21, 25):
            s.paint(s.m_line(10, y, 22, y), "#f0c830", within=m)
        s.paint(s.m_line(10, 19, 22, 19) | s.m_line(11, 23, 21, 23), "#3a3036", within=m)
    spider_top(s, "#e0e4e8", "#2a2228", pattern=pat, ceph="#d8dce0", leg_bands="#f0c830", web=True)


@sprite("asian_spinybacked_orbweaver")
def _(s):
    s.can("walk")
    w = s.wave() if s.act == "walk" else 0
    for i, (x0, y0, x1, y1) in enumerate([(12, 13, 7, 9), (12, 15, 6, 15), (12, 17, 7, 21), (13, 18, 9, 23)]):
        d = round(w * (1 if i % 2 else -1))
        s.line(x0, y0, x1, y1 + d, "#2b2630", mirror=True)
    s.ellipse(16, 12, 3, 2.6, "#3a2a24", edge=True)
    for x, y, dx, dy in ((7, 18, -2, 0), (25, 18, 2, 0), (10, 24, -1.5, 1.5), (22, 24, 1.5, 1.5),
                         (10, 15, -1.5, -1.5), (22, 15, 1.5, -1.5)):
        s.path([(x, y), (x + dx, y + dy)], (1.3, 0.5), "#8a2a2a")
    m = s.ellipse(16, 19.5, 9, 5.5, "#f6f0d8", edge=True)
    s.paint(s.m_px([(10, 18), (13, 21), (16, 17), (19, 21), (22, 18), (12, 23), (20, 23), (16, 22)]),
            "#3a2a24", within=m)
    s.paint(s.m_ellipse(16, 22.5, 6, 1.5), "#d87a3a", within=m)
    s.eye(14, 18)
    s.eye(18, 18)
    s.blush(13, 20)
    s.blush(19, 20)


@sprite("black_witch")
def _(s):
    # Huge dark-brown moth with wavy bands and comma-shaped eyespots.
    def pat(s, fm, hm):
        w = fm | hm
        s.paint(s.m_path([(3, 9), (6, 11), (9, 10), (13, 13)], 0.6) | s.m_path([(5, 19), (8, 21), (11, 20), (14, 22)], 0.6),
                "#a8889a", mirror=True, within=w)
        s.paint(s.m_ellipse(9, 7, 1.6, 2), "#1e1418", mirror=True, within=fm)
        s.paint(s.m_px([(8, 6), (9, 5), (10, 8)]), "#d8b8e8", mirror=True, within=fm)
        s.paint(s.m_ellipse(8, 24, 1.6, 1.4), "#1e1418", mirror=True, within=hm)
        s.paint(s.m_px([(8, 24)]), "#4a9ac8", mirror=True, within=hm)
    butterfly(s, "#5a463e", "#4a3a36", body="#2a2024", pattern=pat)


@sprite("valley_carpenter_bee")
def _(s):
    # The female: big, glossy all-black, with smoky violet wings.
    s.can("fly")
    up = not (s.act == "fly" and s.f % 2)
    s.ellipse(20, 8 if up else 11, 4.5, 6.5 if up else 4, "#8a6aa8", rot=25 if up else 70, shade=False, edge=True)
    s.ellipse(25, 11 if up else 13, 3.5, 5 if up else 3, "#7a5a98", rot=40 if up else 80, shade=False, edge=True)
    s.ellipse(21, 20, 7.5, 6.5, "#1e1c26", edge=True)
    s.px([(19, 16), (20, 16), (21, 17)], "#6a6a8a")
    s.ellipse(13, 18, 5, 5, "#24222c", edge=True)
    s.px([(12, 15), (13, 15)], "#5a5a6a")
    s.line(9, 25, 8, 29, "#2b2226")
    s.line(13, 25, 13, 29, "#2b2226")
    s.ellipse(7, 17, 4.5, 4.5, "#2b2226", edge=True)
    s.line(5, 13, 3, 8, "#2b2226")
    s.line(8, 13, 9, 8, "#2b2226")
    s.eye(4, 16, color="#11080f", shine="#ffffff")
    s.blush(4, 19, color="#ff8fa8")


@sprite("hawaiian_black_nerite")
def _(s):
    s.can("walk")
    st = (0, 1, 2, 1)[s.f] if s.act == "walk" else 0
    s.ellipse(15 - st / 2, 27, 12 + st / 2, 2.6, "#5a5a60")
    m = s.fill(s.m_ellipse(17, 22, 10, 9) & s.m_poly([(0, 0), (32, 0), (32, 26), (0, 26)]), "#1e1c22", edge=True)
    s.paint(s.m_path([(24, 18), (21, 15), (17, 15)], 0.5), "#3a3840", within=m)
    s.paint(s.m_px([(13, 16), (14, 15), (15, 15)]), "#6a6a78", within=m)
    if s.act != "sleep":
        s.ellipse(6 - st, 24.5, 3.5, 2.4, "#6a6a70", edge=True)
        s.line(4 - st, 22, 3 - st, 19, "#6a6a70")
        s.line(7 - st, 22, 8 - st, 19, "#6a6a70")
    s.eye(14, 19)
    s.eye(20, 19)
    s.blush(12, 22)
    s.blush(21, 22)


@sprite("hawaiian_snakehead_cowrie")
def _(s):
    # A glossy chocolate dome freckled with white, its front end pale like a snake's head.
    s.ellipse(16, 27, 13, 2.4, "#c8b89a")
    m = s.fill(s.m_ellipse(16, 25, 13, 12) & s.m_poly([(0, 0), (32, 0), (32, 26), (0, 26)]), "#5a3622", edge=True)
    s.paint(s.m_ellipse(5, 23, 5, 6), "#ece4d4", within=m)
    s.paint(s.m_px([(10, 19), (14, 16), (18, 15), (22, 17), (25, 21), (12, 22), (16, 20), (20, 21), (24, 24),
                    (17, 24), (13, 25), (21, 25), (9, 24), (15, 17)]), "#f0e8d8", within=m)
    s.paint(s.m_ellipse(16, 25, 13, 12) & ~s.m_ellipse(16, 25, 12, 11), "#3a2016", within=m)
    s.eye(11, 20)
    s.eye(18, 19)
    s.blush(9, 23)
    s.blush(20, 22)


@sprite("dotted_periwinkle")
def _(s):
    s.ellipse(16, 28, 14, 3, "#6a6460")
    s.ellipse(10, 26, 5, 2.4, "#4a4644", edge=True)
    m = s.poly([(8, 27), (25, 27), (21, 11), (17, 5), (13, 11)], "#8a8e94", edge=True)
    for y in (12, 17, 22):
        s.paint(s.m_line(9, y + 1, 25, y - 1), "#5a5e66", within=m)
    s.paint(s.m_px([(12, 21), (15, 19), (19, 20), (22, 22), (14, 24), (20, 24), (17, 14), (19, 15), (16, 10)]),
            WHITE, within=m)
    s.eye(13, 17)
    s.eye(18, 17)
    s.blush(11, 20)
    s.blush(20, 20)


@sprite("day_octopus")
def _(s):
    # He'e: a mottled red-brown octopus, arms curling out, white spots on its skin.
    s.can("swim")
    w = s.wave() if s.act == "swim" else 0
    c, dark = "#b8503a", "#8a3424"
    for i, (x0, x1, x2) in enumerate(((10, 5, 1), (12, 9, 5), (15, 14, 12), (17, 18, 20), (20, 23, 27), (22, 27, 31))):
        d = w * (1 if i % 2 else -1)
        m = s.path([(x0, 18), (x1 + d, 24), (x2, 28), (x2 + (2 if x2 < 16 else -2), 25 + d)], (2.0, 0.7), c if i % 2 else dark)
        s.paint(s.m_px([(round(x1 + d), 25), (x2, 27)]), "#f0c0a8", within=m)
    s.ellipse(16, 10, 8.5, 9.5, c, edge=True)
    s.paint(s.m_px([(14, 4), (18, 3), (20, 6), (15, 8), (12, 11), (21, 12), (17, 17), (11, 16), (22, 16)]),
            "#f0d8c8")
    s.paint(s.m_px([(16, 5), (19, 8), (13, 13), (20, 14)]), dark)
    s.ellipse(11.5, 12.5, 2.2, 2.2, "#f0e0a0", shade=False)
    s.ellipse(20.5, 12.5, 2.2, 2.2, "#f0e0a0", shade=False)
    s.eye(11, 12)
    s.eye(20, 12)
    s.blush(10, 15)
    s.blush(21, 15)


# --------------------------------------------------------------------------- sea life
@sprite("thin_shelled_rock_crab")
def _(s):
    # ʻAʻama: a flat, near-black rock crab flecked with pale green-gold, fast on wet rocks.
    def pat(s, m):
        s.paint(s.m_px([(10, 17), (13, 19), (17, 16), (20, 19), (23, 17), (12, 22), (16, 21), (21, 22), (15, 18)]),
                "#a8b878", within=m)
    crab(s, "#2a2e2a", "#6a3a3a", legs="#3a3e3a", pattern=pat)
    s.px([(4, 8), (27, 8)], "#e8c8a8")


@sprite("indo_pacific_rock_boring_urchin")
def _(s):
    # Short, sturdy spines, green-brown with purple tips, nestled in a hole in the rock.
    s.ellipse(16, 27, 15, 5, "#8a847a")
    s.ellipse(16, 25, 11, 3, "#4a4440")
    for k in range(18):
        a = math.pi + k * math.pi / 17
        x0, y0 = 16 + 6 * math.cos(a), 19 + 6 * math.sin(a)
        x1, y1 = 16 + 11 * math.cos(a), 19 + 10 * math.sin(a)
        s.line(x0, y0, x1, y1, "#6a7a3a")
        s.px([(round(x1), round(y1))], "#8a3a8a")
    s.fill(s.m_ellipse(16, 20, 8, 6.5) & s.m_poly([(0, 0), (32, 0), (32, 25), (0, 25)]), "#5a6a30", edge=True)
    s.px([(12, 16), (15, 15), (19, 16), (21, 18)], "#7a8a40")
    _urchin_face(s, 18)


@sprite("shingle_urchin")
def _(s):
    # Hāʻukeʻuke: a low dome paved with flat tiles, with paddle spines around the rim.
    c = "#6a2a40"
    s.ellipse(16, 28.5, 14, 2, "#8a8478")
    m = s.fill(s.m_ellipse(16, 26, 12, 13) & s.m_poly([(0, 0), (32, 0), (32, 26), (0, 26)]), c, edge=True)
    # the mosaic of flat tiles
    for row, y in enumerate((15, 19, 23)):
        for x in range(4 + 2 * (row % 2), 30, 4):
            s.paint(s.m_ellipse(x, y, 1.5, 1.4), "#8a3a56", within=m)
    # a skirt of flat paddle spines around the rim
    for x in range(4, 30, 3):
        s.ellipse(x, 26.5, 1.5, 1.8, "#4a1a2c" if x % 2 else "#5a2236")
    s.eye(12, 19)
    s.eye(18, 19)
    s.blush(10, 22)
    s.blush(20, 22)


@sprite("red_pencil_urchin")
def _(s):
    # Thick, blunt red-brown pencil spines banded pale near the tip.
    for k in range(9):
        a = k * 2 * math.pi / 9 - 0.3
        x1, y1 = 16 + 14 * math.cos(a), 17 + 13 * math.sin(a)
        m = s.path([(16 + 6 * math.cos(a), 17 + 6 * math.sin(a)), (x1, y1)], (1.4, 1.7), "#c8402a")
        s.paint(s.m_ellipse(16 + 11 * math.cos(a), 17 + 10.5 * math.sin(a), 1.3, 1.3), "#f0d0b0", within=m)
    s.ellipse(16, 17, 8, 7.5, "#a8322a", edge=True)
    s.px([(11, 13), (13, 11), (19, 12), (21, 15), (12, 20), (20, 21), (16, 22)], "#e8a080")
    _urchin_face(s, 15)


@sprite("pacific_white_spotted_sea_cucumber")
def _(s):
    s.can("walk")
    st = (0, 1, 2, 1)[s.f] if s.act == "walk" else 0
    c = "#6a4a3a"
    s.ellipse(16, 28, 14, 2, "#c8b89a")
    m = s.ellipse(17 - st / 2, 22, 13 + st / 2, 6, c, edge=True)
    s.paint(s.m_ellipse(17, 26.5, 12, 1.6), "#8a6a54", within=m)
    for x, y in ((8, 19), (12, 17), (17, 17), (22, 18), (26, 20), (10, 22), (15, 21), (20, 21), (25, 23), (13, 24)):
        s.paint(s.m_ellipse(x, y, 1.0, 1.0), "#f4ece0", within=m)
    for x in (3, 5, 7):
        s.ellipse(x - st, 18 + abs(x - 5), 1.2, 1.2, "#e8d8c0")
    s.eye(7 - st, 20)
    s.eye(12 - st, 20)
    s.blush(6 - st, 23)
    s.blush(13 - st, 23)


@sprite("hawaiian_convict_surgeonfish")
def _(s):
    # Manini: pale yellow-white with six crisp black bars.
    def pat(s, m):
        for x in (10, 13.5, 17, 20.5, 24):
            s.paint(s.m_poly([(x - 0.7, 0), (x + 0.7, 0), (x + 0.3, 31), (x - 1.1, 31)]), "#1e1a22")
        s.paint(s.m_ellipse(16, 21, 7, 2.5), "#f4f0e0", within=m)
    _reef(s, "#e8e6c8", rx=10, ry=7.5, fin="#e0d8a8", fins=(10, 9.5), eye=(8, 12),
          snout=[(8, 14), (4, 16), (5, 18), (8, 18)], pattern=pat, mouth=[(5, 17)])
    s.px([(8, 12)], WHITE)


@sprite("moorish_idol")
def _(s):
    # Kihikihi: tall black, white and yellow bands, a long white dorsal streamer and tube snout.
    s.can("swim")
    w = s.wave() if s.act == "swim" else 0
    _fluke(s, [(22, 17), (28, 12), (27, 18), (28, 24), (22, 19)], "#1e1a22", w, pivot_x=22)
    s.poly([(10, 12), (16, 3), (21, 6), (24, 13)], "#f4f0e8")
    s.poly([(11, 23), (18, 30), (23, 21)], "#f4f0e8")
    s.poly([(9, 15), (2, 18), (2, 20), (9, 21)], "#f4f0e8")
    m = s.ellipse(16, 18, 8, 7.5, "#f4f0e8", edge=True)
    s.paint(s.m_poly([(8, 0), (13, 0), (13, 31), (9, 31)]), "#1e1a22")
    s.paint(s.m_poly([(15.5, 0), (18, 0), (18, 31), (16, 31)]), "#f4d020")
    s.paint(s.m_poly([(18, 0), (22.5, 0), (22, 31), (18, 31)]), "#1e1a22")
    s.paint(s.m_poly([(23, 0), (25, 0), (25, 31), (23, 31)]), "#f4d020")
    s.paint(s.m_poly([(26, 10), (29, 10), (29, 26), (26, 26)]), "#f4f0e8")
    s.paint(s.m_ellipse(5, 17.5, 2.5, 1.5), "#f08a2a")
    s.paint(s.m_ellipse(14, 23, 2.5, 1.5), "#f4d020", within=m)
    s.path([(16, 4), (20, -2), (27, -5), (34, -3)], (1.1, 0.5), "#f4f0e8")
    s.px([(2, 19)], BLACK)
    s.ellipse(11, 15, 1.4, 1.2, "#f4f0e8", shade=False)
    s.eye(10, 14)
    s.blush(11, 18, color="#f59aa8")


@sprite("yellow_tang")
def _(s):
    # Lauʻīpala: a bright lemon-yellow disc with a pointed snout and a white tail spine.
    _reef(s, "#f8d820", rx=8.5, ry=8, fin="#f0c818", tail="#f0c818", fins=(10, 12), eye=(9, 11),
          snout=[(9, 13), (3, 16), (4, 17.5), (9, 19)], mouth=[(4, 16)])
    s.px([(24, 16), (25, 16)], WHITE)


@sprite("saddle_wrasse")
def _(s):
    # Hīnālea lauwili: blue-green body, a blue head and an orange-red saddle behind it.
    def pat(s, m):
        s.paint(s.m_ellipse(8, 16, 6, 6), "#3a6ad8", within=m)
        s.paint(s.m_poly([(12, 8), (15, 8), (15, 24), (12, 24)]), "#e8502a", within=m)
        for x in (18, 21, 24):
            s.paint(s.m_line(x, 12, x, 19), "#7ac0a0", within=m)
        s.paint(s.m_line(4, 18, 9, 19), "#e070c0", within=m)
    _reef(s, "#2a9a8a", cx=15, cy=16, rx=11.5, ry=5.5, fin="#2a8a7a", tail="#3a8ad8", eye=(6, 13),
          dorsal=[(9, 12), (14, 8.5), (24, 10), (25, 13)], anal=[(12, 20), (16, 23.5), (24, 22), (24, 19)],
          pattern=pat, mouth=[(3, 17), (4, 17)])


@sprite("wedgetail_triggerfish")
def _(s):
    # Humuhumunukunukuāpuaʻa: a black band from the eye to the belly, blue lines between
    # the eyes, yellow lips and a black wedge on the tail base.
    def pat(s, m):
        s.paint(s.m_ellipse(18, 10, 10, 4.5), "#b8a07a", within=m)
        s.paint(s.m_poly([(11, 7), (14.5, 7), (20, 25), (15, 25)]), "#1e1a22", within=m)
        s.paint(s.m_poly([(20, 16), (28, 11), (28, 21)]), "#1e1a22", within=m)
        s.paint(s.m_line(20, 16, 27, 12) | s.m_line(20, 16, 27, 20), "#f0c020", within=m)
        for y in (9, 11, 13):
            s.paint(s.m_line(6, y + 1, 11, y), "#3a7ae8" if y != 11 else "#1e1a22", within=m)
        s.paint(s.m_line(5, 19, 13, 17), "#d8a038", within=m)
    _reef(s, "#f4f0e4", cx=16, cy=16, rx=11, ry=8, fin="#c8b898", tail="#c8b898", eye=(11, 11),
          dorsal=[(16, 9), (22, 5), (25, 11)], anal=[(16, 23), (22, 27), (25, 21)], pattern=pat,
          mouth=[(5, 17)])
    s.px([(4, 17), (5, 18)], "#f0c020")


@sprite("dusky_surgeonfish")
def _(s):
    def pat(s, m):
        s.paint(s.m_px([(7, 11), (9, 14), (6, 14), (10, 10), (11, 13), (8, 16)]), "#e89040", within=m)
    _reef(s, "#7a6070", rx=9.5, ry=7.5, fin="#5a4250", fins=(10.5, 10), eye=(9, 12),
          snout=[(8, 14), (4, 16), (5, 18), (8, 18)], pattern=pat, mouth=[(5, 17)])
    s.paint(s.m_ellipse(17, 16, 11.5, 10) & ~s.m_ellipse(17, 16, 10.5, 9) & ~s.m_ellipse(16, 16, 9.5, 7.5),
            "#7ab0e0")
    s.ellipse(9, 12.5, 2.4, 2.2, "#f0b030", shade=False)
    s.eye(9, 12)
    s.ellipse(23, 9, 1.4, 1.2, "#1e1a22")
    s.ellipse(23, 23, 1.4, 1.2, "#1e1a22")
    s.px([(24, 16), (25, 16)], "#c8c0c8")


@sprite("pacific_orange_spine_unicornfish")
def _(s):
    # Kala: grey-brown, a black dorsal fin edged white, orange lips and face stripe,
    # bright orange tail spines and a lyre tail with long streamers.
    def pat(s, m):
        s.paint(s.m_path([(10, 11), (7, 14), (5, 17)], 0.7), "#f0a020", within=m)
        s.paint(s.m_ellipse(23, 17, 2, 1.2), "#f07a1a", within=m)
        s.paint(s.m_ellipse(20, 17, 1.6, 1.0), "#f07a1a", within=m)
    _reef(s, "#7a7068", rx=10, ry=7.5, fin="#2a2428", tail="#5a5250", lyre=True, eye=(10, 12),
          dorsal=[(7, 10), (14, 3.5), (25, 7.5), (25, 14)], anal=[(9, 21), (16, 27), (25, 23)],
          snout=[(7, 14), (4, 16), (5, 18), (8, 18)], pattern=pat)
    s.paint(s.m_line(8, 9, 14, 4) | s.m_line(14, 4, 25, 8), WHITE)
    s.px([(4, 16), (4, 17), (5, 17)], "#f07a1a")


@sprite("blackspot_sergeant")
def _(s):
    def pat(s, m):
        for x in (10, 13, 16, 19, 22):
            s.paint(s.m_poly([(x - 0.8, 0), (x + 0.8, 0), (x + 0.8, 31), (x - 0.8, 31)]), "#4a4a50", within=m)
    _reef(s, "#d8d8c8", rx=9.5, ry=7, fin="#b8b8a8", fins=(10, 9), eye=(8, 12), pattern=pat,
          snout=[(8, 14), (5, 16), (6, 18), (8, 18)], mouth=[(6, 17)])
    s.ellipse(24.5, 13, 1.5, 1.5, "#1a1a20", shade=False)


@sprite("spotted_boxfish")
def _(s):
    # Moa: a square box with a dark, white-spotted top and blue sides with gold spots.
    s.can("swim")
    w = s.wave() if s.act == "swim" else 0
    _fluke(s, [(24, 15), (30, 11), (29, 17), (30, 23), (24, 19)], "#3a3a4a", w, pivot_x=24)
    s.poly([(18, 9), (22, 5), (23, 10)], "#3a3a4a")
    m = s.poly([(7, 8), (24, 8), (26, 10), (26, 23), (24, 25), (7, 25), (5, 23), (5, 10)], "#3a4ab8", edge=True)
    s.paint(s.m_poly([(4, 4), (28, 4), (28, 14), (4, 14)]), "#3a3240", within=m)
    s.paint(s.m_px([(8, 10), (12, 9), (16, 10), (20, 9), (23, 11), (10, 12), (18, 12), (14, 12), (22, 13)]),
            WHITE, within=m)
    s.paint(s.m_px([(9, 17), (13, 16), (17, 17), (21, 16), (24, 18), (11, 20), (15, 21), (19, 20), (23, 22),
                    (8, 22), (13, 23), (18, 23)]), "#f0c840", within=m)
    s.ellipse(14, 19, 2.4, 1.4, "#6a7ad8", rot=25, shade=False)
    s.ellipse(3.5, 18, 1.6, 1.3, "#f0b0a0")
    s.eye(8, 14)
    s.blush(8, 17)


@sprite("hawaiian_spotted_toby")
def _(s):
    # A tiny puffer, brown above with white freckles, a pointed snout and green eyes.
    def pat(s, m):
        s.paint(s.m_ellipse(15, 21.5, 9, 3.5), "#f4ecdc", within=m)
        s.paint(s.m_px([(10, 11), (13, 10), (16, 11), (19, 10), (22, 12), (12, 14), (15, 15), (18, 13), (21, 15),
                        (24, 16), (17, 17), (13, 17), (20, 18)]), WHITE, within=m)
    _reef(s, "#8a4a2a", cx=16, cy=16, rx=9, ry=7.5, fin="#c8a070", eye=(9, 12),
          dorsal=[(20, 10), (24, 7), (25, 12)], anal=[(20, 22), (24, 25), (25, 20)],
          snout=[(8, 13), (3, 16), (4, 17.5), (8, 19)], pattern=pat, mouth=[(4, 16)])
    s.px([(9, 13)], "#3ac87a")


@sprite("yellowstripe_goatfish")
def _(s):
    # Weke: silvery white with a bright yellow stripe, a yellow tail and chin barbels.
    def pat(s, m):
        s.paint(s.m_line(5, 15, 26, 16) | s.m_line(6, 16, 26, 17), "#f4c820", within=m)
        s.paint(s.m_ellipse(15, 11, 10, 2.4), "#c8ccd4", within=m)
    _reef(s, "#eef0f4", cx=15, rx=11.5, ry=5, fin="#e8e0b8", tail="#f4c820", eye=(6, 13), pec=False,
          dorsal=[(10, 12), (13, 7.5), (16, 12)], anal=[(15, 20), (18, 23), (22, 20)], pattern=pat,
          mouth=[(3, 17)])
    s.path([(5, 19), (6, 22)], 0.5, "#f4e070", shade=False)
    s.path([(6, 19), (8, 22)], 0.5, "#f4e070", shade=False)


@sprite("raccoon_butterflyfish")
def _(s):
    # Yellow with a black mask across the eye, a white band behind it and a dark slash.
    def pat(s, m):
        s.paint(s.m_poly([(6, 4), (12, 4), (12, 16), (8, 16)]), "#1e1a22")
        s.paint(s.m_poly([(12, 4), (14.5, 4), (14.5, 16), (12, 16)]), WHITE)
        s.paint(s.m_poly([(16, 5), (19.5, 5), (26, 18), (23, 20)]), "#2a221e", within=m)
    _reef(s, "#f4c020", rx=9, ry=8, fin="#f0b018", tail="#f0c040", fins=(11, 11.5), eye=(9, 11),
          snout=[(8, 13), (3, 15), (4, 16.5), (8, 18)], mouth=[(4, 15)], pattern=pat)
    s.ellipse(25, 18, 1.5, 1.5, "#1e1a22", shade=False)
    s.px([(8, 10), (9, 10), (10, 11), (10, 12), (8, 13), (9, 13), (7, 11), (7, 12)], "#f4c020")
    s.eye(8, 11)


@sprite("threadfin_butterflyfish")
def _(s):
    # White front with dark chevrons, a yellow back half, a black eye bar,
    # a black spot on the back fin and a trailing thread.
    s.path([(24, 7), (29, 5), (33, 7)], (0.6, 0.4), "#f0c020", shade=False)

    def pat(s, m):
        s.paint(s.m_poly([(16, 0), (32, 0), (32, 31), (19, 31)]), "#f4c820")
        for x in (11, 14, 17):
            s.paint(s.m_path([(x, 9), (x - 2, 14), (x, 19)], 0.4), "#6a6070", within=m)
        s.paint(s.m_poly([(8, 5), (11, 5), (11, 17), (8, 17)]), "#1e1a22", within=m)
        s.paint(s.m_ellipse(23, 9, 1.8, 1.6), "#1e1a22")
    _reef(s, "#f4f2ea", rx=9, ry=8, fin="#ece8d8", tail="#f4c820", fins=(11, 11.5), eye=(9, 11),
          snout=[(8, 13), (3, 15), (4, 16.5), (8, 18)], mouth=[(4, 15)], pattern=pat)
    s.px([(9, 10), (10, 10), (11, 11), (11, 12), (9, 13), (10, 13), (8, 11), (8, 12)], "#f4f2ea")
    s.eye(9, 11)


@sprite("black_triggerfish")
def _(s):
    # Humuhumu ʻeleʻele: inky black-blue with pale blue lines along the fins.
    def pat(s, m):
        s.paint(s.m_ellipse(13, 14, 6, 4), "#2a3248", within=m)
    _reef(s, "#1e2232", cx=16, cy=16, rx=11, ry=8, fin="#2a2e42", tail="#2a2e42", eye=(11, 11), lyre=True,
          dorsal=[(15, 9), (21, 3), (25, 12)], anal=[(15, 23), (21, 29), (25, 20)], pattern=pat)
    s.paint(s.m_line(15, 9, 25, 12) | s.m_line(15, 23, 25, 20), "#8ac8f0")
    s.ellipse(11.5, 11.5, 2.2, 2.2, "#4a5a7a", shade=False)
    s.eye(11, 11)
    s.px([(4, 17), (5, 17)], "#4a5a7a")


@sprite("zebra_blenny")
def _(s):
    # Paoʻo: a blunt-headed little blenny with dark zebra bars and frilly brows.
    def pat(s, m):
        for x in (12, 15, 18, 21, 24):
            s.paint(s.m_poly([(x - 0.8, 0), (x + 0.8, 0), (x + 0.8, 31), (x - 0.8, 31)]), "#3a2e2a", within=m)
    _reef(s, "#a8946a", cx=16, cy=18, rx=12, ry=5, fin="#8a7a58", eye=(5, 14),
          dorsal=[(8, 15), (10, 11), (26, 12), (26, 16)], pattern=pat, mouth=[(4, 19), (5, 19)])
    s.ellipse(7, 17, 5, 5, "#b8a478", edge=True)
    s.paint(s.m_line(4, 20, 9, 20), "#6a5a40")
    s.px([(6, 11), (7, 10), (5, 10)], "#c8b08a")
    s.eye(5, 15)
    s.blush(6, 18)


@sprite("whitemouth_moray")
def _(s):
    # Puhi: a brown eel freckled with white, rising from a rock, mouth open showing white inside.
    s.can("swim")
    w = s.wave() if s.act == "swim" else 0
    s.ellipse(20, 29, 13, 4, "#7a7470")
    s.ellipse(20, 27, 6, 2.5, "#3a3432")
    c = "#6a4a32"
    s.path([(21, 27), (21 + w, 21), (17 - w, 16), (14, 11)], (3.4, 3.6), c, edge=True)
    s.paint(s.m_path([(22, 22), (19, 17), (16, 13)], 0.6), "#d8c8a0")
    s.ellipse(11, 10, 5.5, 4, c, edge=True, rot=-10)
    s.poly([(7, 11), (2, 12), (7, 15)], WHITE)
    s.poly([(6, 9), (1, 11), (7, 11)], c)
    s.paint(s.m_px([(14, 9), (12, 7), (17, 13), (19, 16), (21, 20), (22, 24), (19, 22), (16, 18), (15, 11), (10, 8)]),
            "#f0e8d8")
    s.eye(10, 8)
    s.blush(10, 12)
