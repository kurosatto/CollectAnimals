"""Sprites for the pets and pests in species/household.csv (not Field Guide animals,
but the capture screen names them)."""
from __future__ import annotations

from archetypes import BLACK, EYE, WHITE, bird, fish, mammal, quad, sprite
from pixel import mix


# --------------------------------------------------------------------------- pets
@sprite("domestic_dog")
def _(s):
    def collar(s, b):
        (nx0, ny0), (nx1, ny1), nr = b["neck"]
        s.paint(s.m_path([(nx1 + 1.2, ny1 - 1), (nx1 + 0.2, ny1 + 2.6)], 0.9), "#d8413a")
        s.paint(s.m_px([(round(nx1), round(ny1 + 2))]), "#ffd84a")
    quad(s, "#d29a58", "#f6e7cc", build="dog", ears="round", ear_in="#9a6430", tail="long",
         tail_col="#c48a4a", nose="#2b2226", markings=collar)


@sprite("domestic_cat")
def _(s):
    def stripes(s, b):
        for x in (14, 17, 20, 23):
            s.paint(s.m_path([(x, 17.5), (x + 0.8, 21)], 0.5), "#5e5a60")
        hx, hy = b["head"][:2]
        s.paint(s.m_px([(round(hx), round(hy - 3)), (round(hx + 1), round(hy - 3)), (round(hx + 2), round(hy - 2))]), "#5e5a60")
    quad(s, "#9a969c", "#f1eeea", build="cat", ears="point", ear_in="#f2a7b4", tail="long",
         tail_tip="#5e5a60", nose="#e88a9a", markings=stripes)


@sprite("domestic_rabbit")
def _(s):
    mammal(s, "#f1ece4", "#ffffff", ears="xlong", ear_in="#f2b0bc", tail="cotton", tail_col=WHITE,
           nose="#e88a9a", head_r=(8.5, 7.5))
    s.paint(s.m_ellipse(10.2, -1.5, 3, 2.6, rot=-12), "#f1ece4", mirror=True)  # no black ear tips


@sprite("golden_hamster")
def _(s):
    mammal(s, "#e2a35c", "#fbf3e6", ears="small", ear_in="#f2a7b4", tail="none", head_r=(9.5, 8),
           nose="#e88a9a")
    s.paint(s.m_ellipse(9, 16.5, 2.4, 1.8) | s.m_ellipse(23, 16.5, 2.4, 1.8), "#fbf3e6")  # full cheeks


@sprite("budgerigar")
def _(s):
    def bars(s, m):
        for y in (17, 19, 21):
            s.paint(s.m_line(15, y, 24, y - 2), BLACK, within=m)

    def face(s):
        s.paint(s.m_px([(7, 14), (9, 15)]), "#2a4ad0")
    bird(s, "#78cc4e", "#a8e06c", head="#f2e24c", wing="#d8d04a", tail_col="#3a6ad0", beak="hook",
         beak_col="#e8c890", legs="#9a8a9a", tail="long", wing_mark=bars, face=face)


@sprite("domestic_chicken")
def _(s):
    bird(s, "#f4efe4", "#fbf8f0", head="#f4efe4", wing="#e2dccc", tail_col="#e2dccc", beak="cone",
         beak_col="#e8b040", legs="#e8b040", tail="fan", big=True)
    s.px([(9, 4), (10, 3), (11, 4), (12, 3), (13, 4), (10, 4), (11, 5), (12, 4)], "#d83a32")  # comb
    s.px([(5, 14), (5, 15), (6, 15)], "#d83a32")  # wattle


@sprite("horse")
def _(s):
    def mane(s, b):
        (nx0, ny0), (nx1, ny1), nr = b["neck"]
        s.paint(s.m_path([(nx0 + 1.4, ny0 - 1.5), (nx1 + 1.6, ny1 - 1.6)], 1.0), "#3a2620")
        hx, hy = b["head"][:2]
        s.paint(s.m_px([(round(hx - 1), round(hy - 1)), (round(hx - 1), round(hy))]), WHITE)  # blaze
    quad(s, "#8c5a34", "#a8764c", build="deer", ears="point", ear_in="#6a4228", tail="bushy",
         tail_col="#3a2620", nose="#2b2226", feet="#2b2226", belly=False, markings=mane)


@sprite("goldfish")
def _(s):
    fish(s, "#f2862a", "#f8c070", fin="#f6a24a")


# --------------------------------------------------------------------------- pests
@sprite("brown_rat")
def _(s):
    quad(s, "#7a6a5c", "#c8beb0", build="low", ears="round", ear_in="#f2a7b4", tail="rat",
         tail_col="#e2a8b0", nose="#e88a9a", legs="#6a5a4e", feet="#f2c6cc")


@sprite("house_mouse")
def _(s):
    mammal(s, "#9c948c", "#e6e0d8", ears="round", ear_in="#f2b0bc", tail="rat", tail_col="#efb6bf",
           nose="#e88a9a", head_r=(8.5, 7))


@sprite("rock_pigeon")
def _(s):
    def bars(s, m):
        s.paint(s.m_line(16, 20, 23, 18) | s.m_line(17, 22, 24, 20), "#2e3038", within=m)

    def neck(s):
        s.paint(s.m_ellipse(13, 16, 4, 2), "#4c8a7a")
        s.paint(s.m_ellipse(14, 17, 3, 1.2), "#8a5aa0")
    bird(s, "#8a90a0", "#9aa0b0", head="#5c6272", wing="#a4aab8", tail_col="#5c6272", beak="cone",
         beak_col="#3a3438", legs="#d86a6a", wing_mark=bars, face=neck)


@sprite("house_sparrow")
def _(s):
    def face(s):
        s.paint(s.m_ellipse(11, 7.5, 5, 2.2), "#8a8c92")  # grey cap
        s.paint(s.m_ellipse(7, 15, 2.6, 2), BLACK)  # black bib
        s.paint(s.m_ellipse(14, 10, 2.6, 1.4), "#8a5a36")

    def streaks(s, m):
        s.paint(s.m_px([(17, 18), (20, 17), (22, 20), (18, 21), (24, 18)]), "#3a2a20", within=m)
    bird(s, "#a67a4e", "#ddd6c8", head="#b88a5a", wing="#9a6e44", tail_col="#7a5a3a", beak="cone",
         beak_col="#3a3438", legs="#c99060", face=face, wing_mark=streaks)


@sprite("european_starling")
def _(s):
    def spots(s, m):
        s.paint(s.m_px([(12, 21), (15, 23), (18, 22), (14, 19), (20, 24), (11, 24)]), "#f2efe4", within=m)

    def sheen(s):
        s.paint(s.m_ellipse(12, 14, 3, 2), "#4a3a6a")
    bird(s, "#2a2a36", "#2e3040", head="#2a2a36", wing="#3a3448", tail_col="#26242e", beak="long",
         beak_col="#f2c83a", legs="#d88a7a", belly_mark=spots, face=sheen)


def cockroach(s, wings, pron, legs, stripes=False):
    """Top view: a long flat oval of wings, a shield over the head, spiny legs and
    antennae as long as the body. Scuttles when walking."""
    s.can("walk")
    w = s.wave() if s.act == "walk" else 0
    for i, y in enumerate((13, 18, 23)):
        d = w * 1.4 * (1 if i % 2 else -1)
        s.path([(12, y), (7, y + 2 + d), (4, y + 6 + d)], 0.6, legs, shade=False)
        s.path([(20, y), (25, y + 2 - d), (28, y + 6 - d)], 0.6, legs, shade=False)
    s.path([(14, 6), (10, 2), (5, 1), (1, 3)], 0.5, legs, shade=False)
    s.path([(18, 6), (22, 2), (27, 1), (31, 3)], 0.5, legs, shade=False)
    m = s.ellipse(16, 18.5, 6.5, 11.5, wings, edge=True)
    s.paint(s.m_line(16, 11, 16, 30), mix(wings, "#000000", 0.45), within=m)
    s.ellipse(16, 8.5, 6, 3.6, pron, edge=True)
    if stripes:  # the German cockroach's two dark stripes
        s.paint(s.m_line(14, 6, 14, 11) | s.m_line(18, 6, 18, 11), "#3a2618", within=s.last)
    else:
        s.paint(s.m_ellipse(16, 8.5, 3.4, 2), mix(wings, "#000000", 0.25), within=s.last)
    s.px([(14, 5), (18, 5)], BLACK)


@sprite("american_cockroach")
def _(s):
    cockroach(s, "#8a4624", "#c88c4c", "#5a2e18")


@sprite("german_cockroach")
def _(s):
    cockroach(s, "#b47e44", "#e2c08c", "#6a4224", stripes=True)


@sprite("house_fly")
def _(s):
    s.can("fly")
    up = not (s.act == "fly" and s.f % 2)
    s.ellipse(9, 13 if up else 17, 6, 3.4, "#dcecf6", rot=-25 if up else 20, shade=False, edge=True, mirror=True)
    for y in (20, 23, 26):
        s.line(10, y - 2, 6, y + 2, BLACK)
        s.line(21, y - 2, 25, y + 2, BLACK)
    m = s.ellipse(16, 22, 5.5, 7, "#5a5a62")
    s.paint(s.m_line(16, 16, 16, 28), mix("#5a5a62", "#000000", 0.3), within=m)
    s.ellipse(16, 13, 5, 3.5, "#4a4a52", edge=True)
    s.ellipse(16, 8.5, 5.5, 3.8, "#3a3a42", edge=True)
    s.ellipse(12.5, 8, 2.6, 2.8, "#b8322e", shade=False, mirror=True)  # big red eyes
    s.px([(12, 7)], WHITE, mirror=True)
    s.px([(13, 9)], EYE, mirror=True)
