"""Draw the pixel-art sprite (a 32x32 drawing grid on a 40x40 canvas) and silhouette for every species.

    python tools/make_sprites.py            # writes species/sprites/*.png
    python tools/make_sprites.py --sheet docs/sprites.png   # plus a preview sheet
    python tools/make_sprites.py --state NC --sheet nc.png  # sheet for one state's list
    python tools/make_sprites.py --anim-sheet anim.png     # preview of every animation

Each species also gets an animation sheet, species/sprites/anim/<slug>.png: one row
per pose (idle, walk, fly, swim, sleep) of four 40x40 frames. anim/index.json lists
the poses each species really draws; the others repeat its idle row.

Species come from every list in species/states.json; one sprite per slug is shared
by all states.

Every sprite is drawn from code (no photos), so the art is original to this repo
and has no third-party licence. species/sprites/credits.csv records that per sprite.
"""
from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path

from PIL import Image, ImageDraw

sys.path.insert(0, str(Path(__file__).parent))
import species_ca_tidepool  # noqa: E402,F401  (registers the drawings in these modules)
import species_household  # noqa: E402,F401
import species_nc  # noqa: E402,F401
import species_tx  # noqa: E402,F401
import species_fl  # noqa: E402,F401
import species_ny  # noqa: E402,F401
import species_va  # noqa: E402,F401
import species_pa  # noqa: E402,F401
import species_il  # noqa: E402,F401
from archetypes import (BLACK, NOSE, PINK, WHITE, beetle_top, bee, bird, butterfly,  # noqa: E402
                        dragonfly, duck, frog, goose, hummingbird, lizard, mammal, owl, pelican,
                        mantis, pinniped, quad, S, snake, sprite, star, turtle, vulture, wader, whale)
from pixel import ACTS, FRAMES, N, Sprite, mix, silhouette  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
STATES_JSON = ROOT / "species" / "states.json"
OUT = ROOT / "species" / "sprites"

# --------------------------------------------------------------------------- mammals
@sprite("mountain_lion")
def _(s):
    def m(s, b):
        hx, hy = b["head"][:2]
        s.px([(round(hx - 3), round(hy + 2)), (round(hx - 2), round(hy + 3))], "#5a4030")
    quad(s, "#c99a62", "#f3e6d0", build="cat", ears="round", ear_in="#8a6040", tail="long",
         tail_tip="#4a3426", nose="#c46a6a", markings=m)


@sprite("bobcat")
def _(s):
    def spots(s, b):
        s.paint(s.m_px([(14, 19), (17, 18), (20, 19), (23, 18), (16, 21), (21, 21), (25, 20), (12, 21),
                        (19, 23), (24, 23), (14, 24)]), "#6a4a30")
        s.paint(s.m_px([(9, 13), (11, 12)]), "#6a4a30")
    quad(s, "#c49a6c", "#f2e8da", build="cat", ears="tuft", ear_in="#e8c8a8", tail="short",
         tail_tip=BLACK, nose="#c46a6a", markings=spots)


@sprite("coyote")
def _(s):
    def m(s, b):
        s.paint(s.m_ellipse(20, 16.5, 6, 1.8), "#9c8064", within=s.m_ellipse(*b["body"]))
    quad(s, "#b59673", "#efe3cf", build="dog", ears="big", ear_in="#d8a882", tail="bushy",
         tail_tip=BLACK, tail_col="#9c8064", markings=m)


@sprite("gray_fox")
def _(s):
    def m(s, b):
        s.paint(s.m_ellipse(20, 16.5, 6.5, 1.8), "#7d7d84", within=s.m_ellipse(*b["body"]))
        s.paint(s.m_ellipse(19, 22.5, 6, 1.4), "#c27848", within=s.m_ellipse(*b["body"]))
    quad(s, "#9a9aa2", "#f4efe6", build="dog", ears="big", ear_in="#d08a60", tail="bushy",
         tail_col="#8a8a92", tail_tip=BLACK, legs="#c27848", markings=m)


@sprite("american_black_bear")
def _(s):
    quad(s, "#3a3036", "#c9a27a", build="bear", ears="round", ear_in="#5a4a50", tail="none",
         muzzle="#c9a27a", nose="#1d1418", belly=False, eye_col="#120c10")


@sprite("mule_deer")
def _(s):
    def antlers(s, b):
        hx, hy = b["head"][:2]
        c = "#d8c49a"
        for dx, col in ((1.5, mix(c, "#1a1420", 0.25)), (0, c)):
            x, y = hx + 1 + dx, hy - 2.5
            s.path([(x, y), (x + 1.5, y - 4), (x + 0.5, y - 7.5)], 0.7, col, shade=False)
            s.path([(x + 1.5, y - 4), (x + 4, y - 6.5)], 0.6, col, shade=False)
    quad(s, "#a98c6c", "#f2e9dc", build="deer", ears="mule", ear_in="#e5b8a4", tail="cotton",
         tail_col=WHITE, tail_tip=BLACK, nose="#2b2226", feet="#4a3a30", behind=antlers)


@sprite("elk")
def _(s):
    def antlers(s, b):
        hx, hy = b["head"][:2]
        c = "#e0d0aa"
        for dx, col in ((1.5, mix(c, "#1a1420", 0.25)), (0, c)):
            x, y = hx + 1 + dx, hy - 2.5
            s.path([(x, y), (x + 3, y - 4), (x + 6, y - 7), (x + 9, y - 8)], 0.75, col, shade=False)
            for k, (tx, ty) in enumerate(((x + 1.5, y - 2), (x + 3, y - 4), (x + 6, y - 7))):
                s.path([(tx, ty), (tx - 1.5, ty - 3 - k * 0.5)], 0.55, col, shade=False)

    def mane(s, b):
        (nx0, ny0), (nx1, ny1), nr = b["neck"]
        s.paint(s.m_path([(nx0, ny0), (nx1, ny1)], nr + 0.2), "#6e4a30")
    quad(s, "#b08454", "#5e3e28", build="deer", ears="side", ear_in="#e2b694", tail="cotton",
         tail_col="#f0dcb0", head="#6e4a30", muzzle="#8a6448", legs="#6e4a30", nose="#2b2226",
         belly=False, behind=antlers, markings=mane)


@sprite("bighorn_sheep")
def _(s):
    def horns(s, b):
        hx, hy = b["head"][:2]
        x, y = hx + 1.5, hy - 2.5
        s.path([(x - 1, y), (x + 2.5, y - 1.5), (x + 5, y + 0.5), (x + 5, y + 4), (x + 2.5, y + 5.5), (x + 0.5, y + 4)],
               (2.0, 0.9), "#d2bc92", edge=True)
        s.paint(s.m_path([(x + 2.5, y - 0.6), (x + 4.2, y + 1), (x + 4, y + 3.5)], 0.5), "#a99068")
    quad(s, "#9c7c5c", "#f2eadb", build="sheep", ears="small", ear_in="#d8b090", tail="cotton",
         tail_col=WHITE, muzzle="#f2eadb", feet="#3a3036", front=horns)


@sprite("raccoon")
def _(s):
    def mask(s, b):
        hx, hy, hrx, hry = b["head"]
        s.paint(s.m_poly([(hx - 5, hy - 1.5), (hx + 3, hy - 1.5), (hx + 2, hy + 1.5), (hx - 4, hy + 1)]), "#3a3238",
                within=s.m_ellipse(hx, hy, hrx, hry) | s.m_path([(6, 21.8), (1.8, 23)], (1.8, 0.8)))
    quad(s, "#8e8a8e", "#efeaea", build="low", ears="round", ear_in=WHITE, tail="ringed",
         tail_col="#a8a2a6", tail_tip="#3a3238", legs="#4a4448", markings=mask)


@sprite("striped_skunk")
def _(s):
    def stripe(s, b):
        s.paint(s.m_path([(8, 16.8), (13, 17.5), (19, 17), (26, 18.5)], (0.8, 1.6)), WHITE)
    quad(s, "#2b2630", "#2b2630", build="low", ears="small", ear_in="#4a424e", tail="skunk",
         tail_col="#2b2630", tail_tip=WHITE, muzzle="#3a3440", nose="#e88a9a", belly=False,
         markings=stripe)


@sprite("virginia_opossum")
def _(s):
    def face(s, b):
        hx, hy, hrx, hry = b["head"]
        s.paint(s.m_ellipse(hx - 1.6, hy - 1, 1.8, 1.5), "#55505a", within=s.m_ellipse(hx, hy, hrx, hry))
    quad(s, "#a7a3aa", "#f3f0f2", build="low", ears="round", ear_in=PINK, tail="rat", tail_col="#efb6bf",
         head="#f3f0f2", muzzle="#f3f0f2", nose="#e88a9a", legs="#3a3438", feet="#f3c6cc", markings=face)


@sprite("western_gray_squirrel")
def _(s):
    mammal(s, "#8f939c", "#f4f1ea", ears="small", ear_in="#d6b0a8", tail="squirrel", tail_col="#7f838c",
           tail_tip="#d6d6dc", head_r=(8, 7))


@sprite("fox_squirrel")
def _(s):
    mammal(s, "#b67a4a", "#eebb88", ears="small", ear_in="#e8a888", tail="squirrel", tail_col="#c4834e",
           tail_tip="#e8a868", head_r=(8, 7))


@sprite("california_ground_squirrel")
def _(s):
    def specks(s):
        s.px([(9, 10), (22, 10), (12, 8), (19, 8), (8, 14), (23, 14)], "#e4d6c0")
    mammal(s, "#8a7058", "#e4d6c0", ears="small", ear_in="#c8a088", tail="squirrel", tail_col="#8a7562",
           tail_tip="#bcab98", head_r=(8, 7), markings=specks)
    s.px([(11, 23), (13, 21), (20, 22), (18, 20), (22, 25)], "#e4d6c0")
    s.paint(s.m_ellipse(10, 11, 2.5, 2.5) | s.m_ellipse(21, 11, 2.5, 2.5), "#f0e6d6")
    s.eye(11, 12, mirror=True)


@sprite("desert_cottontail")
def _(s):
    mammal(s, "#b8a083", "#f5efe4", ears="long", ear_in="#efb6b0", tail="cotton", tail_col=WHITE,
           nose="#e08a96", head_r=(8, 7))


@sprite("brush_rabbit")
def _(s):
    def ears(s):
        s.ellipse(11.5, 5.5, 2.6, 4.6, "#7a6250", rot=-10, mirror=True)
        s.ellipse(11.5, 5.8, 1.0, 3.2, "#d6a0a0", rot=-10, mirror=True, shade=False)
    mammal(s, "#7a6250", "#d8c8b4", ears="none", tail="cotton", tail_col="#c4b4a0",
           nose="#e08a96", head_r=(8.5, 7.5), behind=ears)


@sprite("black_tailed_jackrabbit")
def _(s):
    mammal(s, "#b39a78", "#efe6d6", ears="xlong", ear_in="#e8b4ac", tail="short", tail_col=BLACK,
           nose="#d88a8a", head_r=(7.5, 7))


@sprite("sea_otter")
def _(s):
    mammal(s, "#6a4c3a", "#d8c8b0", ears="small", ear_in="#4a3428", tail="none", head="#d8c8b0",
           muzzle="#efe4d2", nose="#2b2226", belly=False, head_r=(9, 7.5))
    s.ellipse(16, 25, 4, 3.2, "#8a6a56")
    s.ellipse(12.5, 23, 1.8, 1.4, "#4e3628", mirror=True)
    s.px([(12, 17), (11, 18), (20, 17), (21, 18)], WHITE)


@sprite("north_american_river_otter")
def _(s):
    mammal(s, "#6a4a36", "#c8ac90", ears="small", ear_in="#4a3428", tail="long", tail_col="#5e4230",
           muzzle="#c8ac90", nose="#2b2226", head_r=(8.5, 7))
    s.px([(12, 17), (11, 18), (20, 17), (21, 18)], WHITE)


@sprite("california_sea_lion")
def _(s):
    pinniped(s, "#7a5a3e", "#9a7656", ears=True, belly=False)


@sprite("harbor_seal")
def _(s):
    spots = [(9, 8), (21, 7), (12, 5), (19, 5), (7, 13), (24, 12), (9, 20), (22, 19), (10, 26), (23, 25),
             (13, 18), (20, 27), (8, 23)]
    pinniped(s, "#9aa0aa", "#d6d8de", spots=spots, belly=False)


@sprite("northern_elephant_seal")
def _(s):
    pinniped(s, "#8a7a6c", "#b8a898", proboscis="#9a8a7c", belly=False)


@sprite("humpback_whale")
def _(s):
    whale(s, "#3a4658", "#dfe4ea")


@sprite("yellow_bellied_marmot")
def _(s):
    mammal(s, "#7a6248", "#e8b04a", ears="small", ear_in="#5a4a3a", tail="short", tail_col="#6a5240",
           muzzle="#efe4d2", head_r=(9, 7.5),
           markings=lambda s: s.paint(s.m_poly([(13, 10), (19, 10), (17, 12), (15, 12)]), "#efe4d2", within=s.last))
    s.ellipse(16, 25, 5, 4.2, "#e8b04a")


@sprite("american_pika")
def _(s):
    mammal(s, "#9c8a76", "#d6c8b4", ears="round", ear_in="#e8d8c4", tail="none", head_r=(9.5, 8),
           belly=False, nose="#2b2226")
    s.ellipse(16, 24, 8, 6, "#9c8a76")
    s.ellipse(16, 13, 9.5, 8, "#9c8a76", edge=True)
    s.ellipse(16, 17, 4.2, 2.8, "#d6c8b4")
    s.px([(15, 15), (16, 15)], "#2b2226")
    s.eye(11, 12, mirror=True)
    s.blush(9, 15, mirror=True)
    s.px([(5, 3), (26, 3)], "#f4ecdf")


# --------------------------------------------------------------------------- birds
@sprite("california_quail")
def _(s):
    def face(s):
        s.paint(s.m_ellipse(9, 15, 4, 2.6), BLACK, within=s.last)
        s.paint(s.m_poly([(5, 13), (12, 12), (13, 13), (6, 14)]), WHITE, within=s.last)
        s.paint(s.m_ellipse(13, 7, 3.5, 2), "#7a5038", within=s.last)
    def scales(s, m):
        s.paint(s.m_px([(10, 23), (13, 24), (16, 23), (11, 26), (15, 26), (12, 21)]), "#5a4a3a", within=m)
    bird(s, "#7a8090", "#e8d4a4", head="#7a8090", wing="#8a7660", tail="short", crest="quail",
         face=face, belly_mark=scales, beak="cone", beak_col=BLACK)


@sprite("red_tailed_hawk")
def _(s):
    def belly(s, m):
        s.paint(s.m_px([(10, 22), (12, 23), (14, 22), (16, 23), (11, 24), (15, 24)]), "#6a4a34", within=m)
    bird(s, "#7a5238", "#f2e6d2", head="#7a5238", tail_col="#c4583a", beak="hook", beak_col="#e0c070",
         legs="#e8c04a", tail="fan", belly_mark=belly, big=True,
         face=lambda s: s.paint(s.m_ellipse(10, 14.5, 4, 2), "#f2e6d2", within=s.last))


@sprite("red_shouldered_hawk")
def _(s):
    def belly(s, m):
        for y in (19, 21, 23, 25):
            s.paint(s.m_line(9, y, 19, y), "#f2e6d2", within=m)
    def wing(s, m):
        s.paint(s.m_ellipse(17, 17, 3, 2), "#c45a34", within=m)
        s.paint(s.m_px([(20, 21), (22, 20), (24, 19), (21, 18)]), WHITE, within=m)
    bird(s, "#6a4a38", "#c86a44", head="#8a5a40", tail_col="#3a2e2a", beak="hook", beak_col="#e0c070",
         legs="#e8c04a", tail="fan", belly_mark=belly, wing_mark=wing, big=True)


@sprite("coopers_hawk")
def _(s):
    def belly(s, m):
        for y in (19, 21, 23, 25):
            s.paint(s.m_line(9, y, 19, y), "#d8885a", within=m)
    bird(s, "#5e6a7c", "#f6eee4", head="#5e6a7c", tail_col="#4e5868", beak="hook", beak_col="#e0c070",
         legs="#e8c04a", tail="long", belly_mark=belly, eye_col="#c8302a",
         face=lambda s: s.paint(s.m_ellipse(10, 15, 4, 2.2), "#d8b49a", within=s.last))
    s.paint(s.m_line(23, 13, 29, 6) | s.m_line(24, 14, 30, 7), "#3a4250")


@sprite("american_kestrel")
def _(s):
    def face(s):
        s.paint(s.m_ellipse(12, 7, 4, 2), "#6a84b8", within=s.last)
        s.paint(s.m_line(8, 13, 8, 15) | s.m_line(13, 12, 13, 15), BLACK, within=s.last)
    def wing(s, m):
        s.paint(s.m_ellipse(21, 18, 5, 2.4, rot=-15), "#6a84b8", within=m)
    bird(s, "#c86a3a", "#f4e4cc", head=WHITE, tail_col="#c86a3a", beak="hook", beak_col="#7a8aa0",
         legs="#e8c04a", tail="mid", face=face, wing_mark=wing)


@sprite("bald_eagle")
def _(s):
    bird(s, "#4a3428", "#5a4030", head=WHITE, wing="#3e2a20", tail_col=WHITE, beak="hook",
         beak_col="#f0c030", legs="#f0c030", tail="fan", big=True, eye_col="#6a4a10")
    s.eye(8, 10, color="#5a3a10")


@sprite("golden_eagle")
def _(s):
    bird(s, "#5a3e2a", "#6a4a32", head="#5a3e2a", wing="#4a321f", tail_col="#4a321f", beak="hook",
         beak_col="#3a3438", legs="#f0c030", tail="fan", big=True,
         face=lambda s: s.paint(s.m_ellipse(14, 9, 4, 4), "#d8a04a", within=s.last))
    s.px([(5, 10), (5, 11)], "#f0c030")


@sprite("osprey")
def _(s):
    def face(s):
        s.paint(s.m_poly([(7, 11), (17, 10), (17, 13), (8, 12)]), "#3a2e2a", within=s.last)
    bird(s, "#4a3a30", WHITE, head=WHITE, wing="#3e3028", tail_col="#5a4a3e", beak="hook",
         beak_col="#2b2630", legs="#b8c0c8", tail="mid", face=face, big=True, eye_col="#c8a020")
    s.eye(8, 10, color="#1d1428")


@sprite("turkey_vulture")
def _(s):
    vulture(s, head_col="#d4483e", body="#2f2a2e", beak="#f0e6dc",
            wing_patch="#8c8690")


@sprite("california_condor")
def _(s):
    vulture(s, head_col="#e8946a", body="#24202a", ruff="#14111a", wing_patch=WHITE, beak="#f0e6dc")


@sprite("great_horned_owl")
def _(s):
    owl(s, "#8a6a4e", "#c89a6a", tufts=True, belly="#d8c4a4", bars="#8a6a4e")
    s.px([(14, 17), (15, 17), (16, 17), (17, 17)], WHITE)


@sprite("barn_owl")
def _(s):
    owl(s, "#d8a868", WHITE, eye_col=None, belly="#fbf3e4", beak="#e8c8b0")
    s.px([(9, 21), (13, 24), (20, 22), (17, 26), (22, 26)], "#a87850")


@sprite("annas_hummingbird")
def _(s):
    hummingbird(s)


@sprite("acorn_woodpecker")
def _(s):
    def face(s):
        s.paint(s.m_ellipse(13, 6.5, 4.5, 2.6), "#d42a2a", within=s.last)
        s.paint(s.m_ellipse(10, 11, 4.5, 2.5), WHITE, within=s.last)
        s.paint(s.m_ellipse(9, 15, 3, 1.6), BLACK, within=s.last)
    bird(s, BLACK, WHITE, head=BLACK, wing="#24202a", tail_col=BLACK, beak="crow", beak_col="#3a3438",
         legs="#6a6a70", tail="short", face=face, eye_col="#f4f0e0",
         belly_mark=lambda s, m: s.paint(s.m_px([(11, 23), (14, 22), (12, 25), (16, 24)]), BLACK, within=m))
    s.px([(8, 10), (9, 10), (8, 11), (9, 11)], "#f4f0e0")
    s.px([(8, 11)], EYE_DOT)


EYE_DOT = "#1d1428"


@sprite("northern_flicker")
def _(s):
    def face(s):
        s.paint(s.m_ellipse(13, 7, 4, 2.4), "#8a7a6a", within=s.last)
        s.paint(s.m_line(7, 14, 10, 15) | s.m_line(7, 15, 9, 15), "#d43a3a", within=s.last)
    def spots(s, m):
        s.paint(s.m_px([(10, 22), (13, 23), (16, 22), (11, 25), (15, 25), (13, 20)]), BLACK, within=m)
        s.paint(s.m_poly([(8, 17), (18, 17), (18, 19), (8, 19)]), BLACK, within=m)
    def bars(s, m):
        s.paint(s.m_px([(18, 17), (20, 16), (22, 17), (19, 19), (21, 20), (23, 19)]), "#3a3030", within=m)
    bird(s, "#a88a6e", "#f2e2cc", head="#c8b8a4", wing="#a08068", tail_col="#d8604a", beak="crow",
         beak_col="#3a3438", legs="#7a7070", tail="mid", face=face, belly_mark=spots, wing_mark=bars)


@sprite("california_scrub_jay")
def _(s):
    def face(s):
        s.paint(s.m_ellipse(9.5, 12, 3.5, 2), "#5a6070", within=s.last)
        s.paint(s.m_px([(10, 8), (11, 8), (12, 8)]), WHITE, within=s.last)
    bird(s, "#4a78c8", "#e8e4e0", head="#4a78c8", wing="#4a78c8", tail_col="#3a68b8", beak="crow",
         beak_col=BLACK, legs="#3a3438", tail="long", face=face,
         belly_mark=lambda s, m: s.paint(s.m_line(9, 19, 15, 19), "#4a78c8", within=m))
    s.paint(s.m_ellipse(20, 22, 4, 2, rot=-15), "#b8a898")


@sprite("stellers_jay")
def _(s):
    def face(s):
        s.paint(s.m_ellipse(11, 12.5, 6.5, 4), "#24283a", within=s.last)
        s.paint(s.m_px([(9, 7), (10, 7)]), "#7ab0e8", within=s.last)
    bird(s, "#2a5aa8", "#3a6ab8", head="#24283a", wing="#2f62b0", tail_col="#2a52a0", beak="crow",
         beak_col=BLACK, legs="#3a3438", tail="long", crest="jay", face=face,
         wing_mark=lambda s, m: s.paint(s.m_line(17, 17, 24, 15) | s.m_line(18, 20, 25, 18), "#14204a", within=m))


@sprite("american_crow")
def _(s):
    bird(s, "#2a2633", "#34303e", head="#2a2633", wing="#252130", tail_col="#252130", beak="crow",
         beak_col="#18161e", legs="#2a2633", tail="short")


@sprite("common_raven")
def _(s):
    bird(s, "#25203a", "#2e2a42", head="#25203a", wing="#211c36", tail_col="#211c36", beak="long",
         beak_col="#141220", legs="#25203a", tail="fan", big=True,
         face=lambda s: s.paint(s.m_px([(10, 16), (12, 16), (11, 17), (13, 17), (14, 16)]), "#3a3550", within=s.last))
    s.paint(s.m_poly([(5, 9), (8, 9), (8, 10), (5, 10)]), "#3a3550")


@sprite("black_phoebe")
def _(s):
    bird(s, "#2b2630", WHITE, head="#2b2630", wing="#3a3440", tail_col="#2b2630", beak="thin",
         beak_col=BLACK, legs="#2b2630", tail="long")
    s.paint(s.m_ellipse(11, 20, 4, 3), "#2b2630")


@sprite("western_bluebird")
def _(s):
    bird(s, "#4a7ad0", "#c8834e", head="#4a7ad0", wing="#5a8ae0", tail_col="#3a6ac0", beak="thin",
         beak_col="#2b2630", legs="#3a3438", tail="short")
    s.paint(s.m_ellipse(11, 26, 3, 2), "#d8d4e0")


@sprite("american_robin")
def _(s):
    def face(s):
        s.paint(s.m_px([(7, 9), (8, 9), (9, 9), (7, 12), (8, 12)]), WHITE, within=s.last)
        s.paint(s.m_line(5, 14, 7, 16), "#f0eee8", within=s.last)
    bird(s, "#5a5260", "#d8653a", head="#2e2a32", wing="#625a68", tail_col="#2e2a32", beak="thin",
         beak_col="#e8b830", legs="#8a7a6a", tail="mid", face=face)
    s.eye(8, 10)


@sprite("northern_mockingbird")
def _(s):
    def wing(s, m):
        s.paint(s.m_line(16, 19, 24, 17) | s.m_line(17, 21, 25, 19), WHITE, within=m)
    bird(s, "#8a8c94", "#eceae6", head="#8a8c94", wing="#5a5c64", tail_col="#3e3f46", beak="thin",
         beak_col="#2b2630", legs="#3a3438", tail="long", wing_mark=wing, eye_col="#c8a030")


@sprite("california_towhee")
def _(s):
    bird(s, "#8a7462", "#a88a74", head="#8a7462", wing="#7e6858", tail_col="#6e5a4c", beak="cone",
         beak_col="#7a6a5a", legs="#a88a74", tail="long",
         face=lambda s: s.paint(s.m_ellipse(9, 15, 3, 1.6), "#d8945a", within=s.last))
    s.paint(s.m_ellipse(15, 27, 4, 1.5), "#d8945a")


@sprite("white_crowned_sparrow")
def _(s):
    def face(s):
        h = s.last
        s.paint(s.m_ellipse(12, 7.5, 5, 2.6), BLACK, within=h)
        s.paint(s.m_line(8, 7, 16, 7), WHITE, within=h)
        s.paint(s.m_line(10, 10, 17, 11), WHITE, within=h)
        s.paint(s.m_line(10, 9, 17, 9), BLACK, within=h)
    bird(s, "#9a9aa2", "#d8d8dc", head="#9a9aa2", wing="#8a6e58", tail_col="#7a6252", beak="cone",
         beak_col="#e8a848", legs="#d8b090", tail="mid", face=face,
         wing_mark=lambda s, m: s.paint(s.m_line(16, 19, 24, 17), "#f0e8dc", within=m))


@sprite("house_finch")
def _(s):
    def stripes(s, m):
        s.paint(s.m_px([(13, 25), (16, 24), (11, 26), (17, 26)]), "#8a6a58", within=m)
    bird(s, "#8a7060", "#f0e2d4", head="#d83a42", wing="#7a6050", tail_col="#6a5244", beak="cone",
         beak_col="#a89080", legs="#a88a74", tail="mid", belly_mark=stripes)
    s.paint(s.m_ellipse(11, 20, 4, 2.5), "#d83a42")
    s.paint(s.m_ellipse(13, 7.5, 3, 1.6), "#8a7060")


@sprite("red_winged_blackbird")
def _(s):
    def wing(s, m):
        s.paint(s.m_ellipse(17, 17, 3.6, 2), "#e02a2a", within=m)
        s.paint(s.m_line(15, 19, 20, 19), "#f0d050", within=m)
    bird(s, "#1f1c26", "#26222e", head="#1f1c26", wing="#1a1820", tail_col="#1a1820", beak="crow",
         beak_col="#141218", legs="#2a2630", tail="mid", wing_mark=wing)


@sprite("yellow_billed_magpie")
def _(s):
    def wing(s, m):
        s.paint(s.m_ellipse(19, 18, 4, 2, rot=-15), WHITE, within=m)
        s.paint(s.m_line(20, 21, 25, 19), "#3a5ab0", within=m)
    bird(s, "#1f1c26", WHITE, head="#1f1c26", wing="#24202c", tail_col="#2a4a6a", beak="crow",
         beak_col="#f0c830", legs="#2a2630", tail="long", wing_mark=wing)
    s.px([(7, 12), (7, 13)], "#f0c830")
    s.paint(s.m_ellipse(11, 20, 4, 2.3), "#1f1c26")


@sprite("great_blue_heron")
def _(s):
    wader(s, "#7a8ca8", neck="#9aa2b0", head=WHITE, beak="#e8b830", legs="#5a5250", plume="#2b2630",
          cap="#2b2630", wing="#6a7c98")


@sprite("great_egret")
def _(s):
    wader(s, WHITE, beak="#f0c030", legs="#2b2630", wing="#eef0f2")


@sprite("brown_pelican")
def _(s):
    pelican(s)


@sprite("mallard")
def _(s):
    duck(s, "#a8a6aa", "#7a4a3a", "#1e7a4a", bill="#f0c22a", tail_col=BLACK)


@sprite("canada_goose")
def _(s):
    goose(s)


@sprite("western_gull")
def _(s):
    def wing(s, m):
        s.paint(s.m_px([(24, 17), (25, 17), (25, 18)]), WHITE, within=m)
        s.paint(s.m_poly([(23, 15), (27, 14), (27, 19), (23, 19)]), "#2b2630", within=m)
    bird(s, WHITE, WHITE, head=WHITE, wing="#5e6270", tail_col=WHITE, beak="crow", beak_col="#f0c830",
         legs="#f0a8a8", tail="short", wing_mark=wing, big=True)
    s.px([(3, 13)], "#e0403a")


@sprite("greater_roadrunner")
def _(s):
    def streaks(s, m):
        s.paint(s.m_px([(10, 20), (12, 22), (14, 20), (16, 22), (13, 24)]), "#4a3a30", within=m)
    def wing(s, m):
        s.paint(s.m_px([(17, 17), (19, 19), (21, 17), (23, 19), (20, 21)]), "#f0e6d6", within=m)
    bird(s, "#7a6448", "#ece2d0", head="#5a4836", wing="#5a4836", tail_col="#3e3a38", beak="crow",
         beak_col="#3a3438", legs="#6a8ab0", tail="long", crest="roadrunner", belly_mark=streaks,
         wing_mark=wing, face=lambda s: s.paint(s.m_line(10, 11, 13, 11), "#6aa0d8", within=s.last))
    s.px([(14, 11)], "#e05a3a")


# --------------------------------------------------------------------------- reptiles
@sprite("western_fence_lizard")
def _(s):
    def pat(s, m):
        s.paint(s.m_px([(10, 20), (13, 19), (16, 20), (19, 19), (12, 21), (18, 21)]), "#3e3a36", within=m)
        s.paint(s.m_ellipse(13, 24.5, 3, 1.3), "#3a7ad8", within=m)
    lizard(s, "#7a7066", "#d8d0c4", throat="#3a7ad8", pattern=pat)


@sprite("southern_alligator_lizard")
def _(s):
    def pat(s, m):
        for x in (10, 13, 16, 19):
            s.paint(s.m_line(x, 19, x, 22), "#5a3a28", within=m)
    lizard(s, "#b08050", "#e6d6b8", pattern=pat, tail_pts=[(20, 22), (27, 25), (31, 24), (31, 18)])
    for x in (23, 27):
        s.paint(s.m_line(x, 21, x, 27), "#5a3a28")


@sprite("side_blotched_lizard")
def _(s):
    def pat(s, m):
        s.paint(s.m_ellipse(10.5, 21, 1.4, 1.4), "#1d1a26", within=m)
        s.paint(s.m_px([(13, 19), (16, 20), (19, 19), (15, 21), (18, 22)]), "#6ab0d8", within=m)
    lizard(s, "#8a7258", "#d6cab4", pattern=pat)


@sprite("western_skink")
def _(s):
    def pat(s, m):
        s.paint(s.m_line(8, 20, 22, 20), "#f0e6c8", within=m)
        s.paint(s.m_line(8, 22, 22, 22), "#3a2e2a", within=m)
    lizard(s, "#5a4a3c", "#c8c0ae", tail_col="#3a7ae0", pattern=pat, smooth=True)
    s.paint(s.m_line(3, 17, 12, 17) | s.m_line(6, 16, 10, 16), "#f0e6c8")
    s.eye(5, 17)


@sprite("coast_horned_lizard")
def _(s):
    def pat(s, m):
        s.paint(s.m_ellipse(13, 20, 1.6, 1.2) | s.m_ellipse(18, 20, 1.6, 1.2), "#5a3e30", within=m)
        s.paint(s.m_px([(9, 18), (11, 18), (14, 18), (17, 18), (20, 18)]), "#e8d8b8", within=m)
    lizard(s, "#b8946a", "#ecdcc0", pattern=pat, horns=True, wide=True,
           tail_pts=[(21, 23), (25, 25), (28, 25)])


@sprite("desert_iguana")
def _(s):
    def pat(s, m):
        s.paint(s.m_px([(10, 20), (12, 19), (14, 21), (16, 19), (18, 21), (20, 20), (13, 22), (17, 22)]),
                "#9a6a4a", within=m)
    lizard(s, "#d8ccb4", "#efe8da", pattern=pat, smooth=True)
    for x in (23, 26, 29):
        s.paint(s.m_line(x, 20, x, 27), "#9a6a4a")


@sprite("gopher_snake")
def _(s):
    snake(s, "#d8b878", belly="#efe2c4", blotch="#7a4e2e", band_period=3.0)


@sprite("california_kingsnake")
def _(s):
    snake(s, "#2b2630", belly="#f2ecd8", bands="#f4eedc", band_period=4.0, band_len=1.6)


@sprite("common_garter_snake")
def _(s):
    snake(s, "#2f3a34", belly="#e8d870", stripe="#f0d850")
    s.paint(s.m_px([(9, 22), (19, 22), (11, 27), (20, 28), (8, 25)]), "#c8402a")


@sprite("western_rattlesnake")
def _(s):
    snake(s, "#a89880", belly="#e8e0cc", blotch="#5a4a3e", band_period=3.2, rattle=True, head_w=5.2)


@sprite("western_pond_turtle")
def _(s):
    turtle(s, "#5a5a3a", "#6a6a4a", speckle="#e8d070", scutes="#6e6e48")


@sprite("desert_tortoise")
def _(s):
    turtle(s, "#a07a4a", "#b89a74", dome=True, scutes="#d0aa6a", rim="#7a5a36")


# --------------------------------------------------------------------------- amphibians
@sprite("sierran_treefrog")
def _(s):
    frog(s, "#5aaa4a", "#eef0d8", stripe="#2b3a2a", pads=True)


@sprite("california_newt")
def _(s):
    lizard(s, "#8a5a36", "#f08a2a", throat="#f08a2a", smooth=True, eye_big=True, legs="#7a4e2e")


@sprite("rough_skinned_newt")
def _(s):
    def pat(s, m):
        s.paint(s.m_px([(10, 19), (13, 20), (16, 19), (19, 20), (12, 21), (18, 21)]), "#4a3424", within=m)
    lizard(s, "#6a4a32", "#f07a2a", throat="#f07a2a", smooth=True, legs="#5a3e2a", pattern=pat)


@sprite("ensatina")
def _(s):
    lizard(s, "#b8683a", "#e8b080", smooth=True, eye_big=True, legs="#d8945a",
           tail_pts=[(21, 22), (26, 24), (30, 22), (30, 17)])
    s.paint(s.m_ellipse(22, 22, 1.5, 3), "#e8a060")


@sprite("american_bullfrog")
def _(s):
    frog(s, "#6a8a3a", "#f0ecc8", tympanum="#4a5a2a", spots=[(13, 22), (20, 23), (9, 20), (23, 20)])
    s.paint(s.m_ellipse(16, 13, 6, 3), "#7aa04a")


@sprite("arboreal_salamander")
def _(s):
    def pat(s, m):
        s.paint(s.m_px([(10, 19), (13, 20), (16, 19), (19, 20), (21, 21), (12, 22)]), "#e8c84a", within=m)
    lizard(s, "#6a5444", "#b8a898", smooth=True, eye_big=True, pattern=pat)


# --------------------------------------------------------------------------- invertebrates
@sprite("monarch")
def _(s):
    def pat(s, fm, hm):
        wings = fm | hm
        edge = wings & ~(s.m_poly([(15, 11), (5.5, 4.5), (3.5, 7), (4, 13.5), (14, 16)])
                         | s.m_poly([(16, 11), (25.5, 4.5), (27.5, 7), (27, 13.5), (17, 16)])
                         | s.m_poly([(15, 17), (6, 17), (6, 22), (10, 25.5), (15, 21)])
                         | s.m_poly([(16, 17), (25, 17), (25, 22), (21, 25.5), (16, 21)]))
        s.paint(edge, BLACK)
        s.paint(s.m_line(15, 12, 6, 8) | s.m_line(14, 15, 6, 12) | s.m_line(14, 19, 8, 22)
                | s.m_line(15, 21, 11, 24), BLACK, mirror=True, within=wings)
        s.paint(s.m_px([(3, 7), (2, 10), (3, 13), (5, 23), (8, 26), (6, 5)]), WHITE, mirror=True, within=edge)
    butterfly(s, "#f08a1a", "#f08a1a", pattern=pat)


@sprite("western_tiger_swallowtail")
def _(s):
    def pat(s, fm, hm):
        w = fm | hm
        for a, b in [((6, 3), (9, 13)), ((10, 6), (12, 13)), ((13, 9), (14, 15))]:
            s.paint(s.m_line(*a, *b) | s.m_line(a[0] + 1, a[1], b[0] + 1, b[1]), BLACK, mirror=True, within=w)
        s.paint(s.m_line(2, 7, 2, 14) | s.m_line(3, 13, 13, 17) | s.m_line(5, 20, 8, 26) | s.m_line(6, 23, 10, 26),
                BLACK, mirror=True, within=w)
        s.px([(10, 25), (11, 25)], "#3a6ae0", mirror=True)
        s.px([(13, 23)], "#e8502a", mirror=True)
    butterfly(s, "#f6d230", "#f6d230", pattern=pat, tails=True)


@sprite("anise_swallowtail")
def _(s):
    def pat(s, fm, hm):
        w = fm | hm
        s.paint(s.m_poly([(14, 9), (7, 5), (4, 9), (5, 13), (14, 16)]) | s.m_poly([(15, 17), (8, 17), (8, 21), (14, 21)]),
                "#f2d040", mirror=True, within=w)
        s.paint(s.m_px([(3, 6), (2, 10), (2, 13), (6, 24), (8, 26)]), "#f2d040", mirror=True, within=w)
        s.px([(13, 24), (14, 24)], "#e8502a", mirror=True)
        s.px([(12, 23)], "#3a6ae0", mirror=True)
    butterfly(s, "#2b2630", "#2b2630", pattern=pat, tails=True)


@sprite("pipevine_swallowtail")
def _(s):
    def pat(s, fm, hm):
        s.paint(s.m_poly([(15, 17), (6, 17), (6, 23), (10, 26), (15, 22)]), "#2f5ab8", mirror=True, within=hm)
        s.paint(s.m_px([(7, 24), (9, 26), (6, 21), (12, 25)]), "#f0a03a", mirror=True, within=hm)
        s.paint(s.m_px([(3, 8), (3, 12)]), WHITE, mirror=True, within=fm)
    butterfly(s, "#2a2836", "#2a2836", pattern=pat, tails=True)


@sprite("mourning_cloak")
def _(s):
    def pat(s, fm, hm):
        w = fm | hm
        inner = (s.m_poly([(15, 11), (6, 5), (3.5, 7.5), (3.5, 13), (14, 16)])
                 | s.m_poly([(15, 17), (6, 17), (5.5, 21.5), (9.5, 25), (15, 21)]))
        inner = inner | inner[:, ::-1]
        s.paint(w & ~inner, "#f0dca0")
        ring = inner & ~(s.m_poly([(15, 11), (7, 6.5), (5, 8.5), (5, 12.5), (14, 15)])
                         | s.m_poly([(15, 17.5), (7, 17.5), (7, 21), (10, 23.5), (15, 20.5)]))
        ring = ring & ~(ring[:, ::-1] & False)
        s.paint(s.m_px([(5, 9), (5, 12), (7, 19), (8, 22), (10, 24)]), "#4a6ae0", mirror=True, within=w)
    butterfly(s, "#6a2e2e", "#6a2e2e", pattern=pat)


@sprite("painted_lady")
def _(s):
    def pat(s, fm, hm):
        s.paint(s.m_poly([(8, 3), (1, 6), (2, 11), (9, 9)]), BLACK, mirror=True, within=fm)
        s.paint(s.m_px([(3, 6), (5, 7), (3, 9)]), WHITE, mirror=True, within=fm)
        s.paint(s.m_line(9, 11, 13, 11) | s.m_line(10, 12, 13, 13), BLACK, mirror=True, within=fm)
        s.paint(s.m_px([(6, 21), (8, 23), (10, 25)]), BLACK, mirror=True, within=hm)
        s.paint(s.m_px([(7, 20), (9, 22)]), "#4a6ae0", mirror=True, within=hm)
    butterfly(s, "#f0904a", "#f0904a", pattern=pat)


@sprite("western_honey_bee")
def _(s):
    bee(s)


@sprite("convergent_lady_beetle")
def _(s):
    beetle_top(s, "#e0402a", spots=[(11, 16), (21, 16), (9, 21), (23, 21), (12, 25), (20, 25)],
               pron=BLACK)
    s.paint(s.m_line(12, 10, 13, 11) | s.m_line(19, 10, 18, 11), WHITE)


@sprite("flame_skimmer")
def _(s):
    dragonfly(s, "#e86a2a", "#f05a2a", wing="#fbe2c8", wing_tint="#f4a060")


@sprite("common_green_darner")
def _(s):
    dragonfly(s, "#4ab04a", "#4a8ad8")


@sprite("california_mantis")
def _(s):
    mantis(s, "#7ab048", "#a8d07a", "#c8e08a")


@sprite("western_black_widow")
def _(s):
    for (a, b, c) in [((12, 15), (6, 9), (3, 13)), ((12, 17), (5, 16), (2, 20)), ((12, 19), (6, 22), (4, 27)),
                      ((13, 20), (9, 25), (8, 30))]:
        s.path([a, b, c], 0.7, BLACK, shade=False)
        s.path([(31 - a[0] - 4, a[1]), (31 - b[0], b[1]), (31 - c[0], c[1])], 0.7, BLACK, shade=False)
    s.ellipse(18, 20, 8.5, 8, "#1f1a24", edge=True)
    s.poly([(16, 18), (20, 18), (18, 21)], "#e0242a", shade=False)
    s.poly([(18, 21), (16, 24), (20, 24)], "#e0242a", shade=False)
    s.paint(s.m_px([(13, 15), (14, 14), (15, 14)]), "#5a5470")
    s.ellipse(10, 14, 4.5, 4, "#2a2430", edge=True)
    s.eye(7, 13)
    s.eye(10, 13)
    s.blush(7, 16)


@sprite("pacific_banana_slug")
def _(s):
    c = "#e8cc3a"
    s.ellipse(17, 25, 13, 4.3, c)
    s.path([(10, 24), (7, 18), (6, 14)], (3.6, 3.2), c)
    s.ellipse(17, 28, 12.5, 1.4, mix(c, "#5a4a1a", 0.3))
    s.paint(s.m_px([(14, 23), (19, 22), (24, 24), (16, 25), (22, 25), (27, 24), (8, 18)]), "#5a4a2a")
    s.line(5, 12, 3, 6, c)
    s.line(8, 12, 9, 6, c)
    s.px([(3, 5), (9, 5)], "#3a3020")
    s.px([(4, 15), (5, 15), (4, 16), (5, 16)], EYE_DOT)
    s.px([(4, 15)], WHITE)
    s.blush(6, 17)


@sprite("ten_lined_june_beetle")
def _(s):
    beetle_top(s, "#7a4a2a", head="#5a3420", stripes=True, fan=True, pron="#6a3e24")


# --------------------------------------------------------------------------- marine
@sprite("ochre_sea_star")
def _(s):
    star(s, "#8a3e8a", dots="#e8d0ec")


@sprite("bat_star")
def _(s):
    star(s, "#e05a3a", arms=0.28, dots="#f0a050")


@sprite("purple_sea_urchin")
def _(s):
    import math
    for k in range(16):
        a = k * math.pi / 8 + 0.1
        s.line(16 + 6 * math.cos(a), 17 + 6 * math.sin(a), 16 + 13.5 * math.cos(a), 17 + 13.5 * math.sin(a),
               "#8a4ab8")
    s.ellipse(16, 17, 8, 7.5, "#6a2e9a", edge=True)
    s.px([(11, 13), (13, 11), (19, 12), (21, 15), (12, 20), (20, 21)], "#9a5ad0")
    s.eye(12, 15)
    s.eye(18, 15)
    s.blush(10, 18)
    s.blush(20, 18)


@sprite("giant_green_anemone")
def _(s):
    c = "#3aa86a"
    s.ellipse(16, 29, 9, 2, "#c8b8a0")
    s.poly([(9, 28), (8, 16), (24, 16), (23, 28)], "#4a8a5a")
    import math
    for k in range(9):
        x = 5 + k * 2.75
        s.path([(x, 15), (x + 0.5 * (-1) ** k, 10), (x - 0.5 * (-1) ** k, 7)], (1.4, 1.1), c if k % 2 else "#5ac88a")
    s.ellipse(16, 15, 9.5, 3, "#7ad8a0", edge=True)
    s.ellipse(16, 15, 2.5, 1.2, "#e89ab0", shade=False)
    s.eye(12, 20)
    s.eye(18, 20)
    s.blush(10, 23)
    s.blush(20, 23)


@sprite("lined_shore_crab")
def _(s):
    shell = "#3a4a3a"
    for y in (19, 22, 25):
        s.path([(8, y), (3, y + 3), (2, y + 6)], 0.7, "#5a4a5a", shade=False, mirror=True)
    s.path([(9, 17), (6, 13)], 1.2, "#7a3a6a", mirror=True)
    s.ellipse(5.5, 10, 3.6, 3, "#a03a7a", rot=-30, mirror=True, edge=True)
    s.px([(3, 8), (4, 7)], "#e8a8c8", mirror=True)
    s.line(13, 13, 12, 9, shell, mirror=True)
    s.ellipse(16, 20, 10, 6.5, shell, edge=True)
    for y in (17, 19, 21, 23):
        s.paint(s.m_line(9, y, 23, y), "#5a6a4a", within=s.last)
    s.px([(11, 8), (12, 8), (19, 8), (20, 8)], EYE_DOT)
    s.px([(11, 8), (19, 8)], WHITE)
    s.blush(10, 21, mirror=True)
    s.px([(15, 22), (16, 22)], "#1d1a20")


@sprite("pacific_sea_nettle")
def _(s):
    for x0 in (8, 13, 18, 23):
        s.path([(x0, 13), (x0 - 1, 19), (x0 + 1, 24), (x0, 30)], 0.6, "#c86a3a", shade=False)
    s.path([(14, 13), (13, 22), (15, 28)], 1.3, "#f0d8c8")
    s.path([(17, 13), (18, 21), (17, 26)], 1.3, "#f0d8c8")
    m = s.fill(s.m_ellipse(16, 13, 11, 10) & s.m_poly([(0, 0), (32, 0), (32, 14), (0, 14)]), "#d8803a", edge=True)
    for x in (8, 12, 16, 20, 24):
        s.paint(s.m_line(16, 4, x, 13), "#b05a2a", within=m)
    s.eye(12, 8)
    s.eye(18, 8)
    s.blush(10, 11)
    s.blush(20, 11)


@sprite("garibaldi")
def _(s):
    c = "#f47a1a"
    s.poly([(24, 16), (31, 9), (29, 16), (31, 23)], c)
    s.poly([(9, 9), (18, 6), (24, 10), (18, 11)], c)
    s.poly([(10, 24), (18, 27), (22, 23)], c)
    s.ellipse(15, 16.5, 10, 8, c, edge=True)
    s.ellipse(15, 20, 3, 2, "#f8a050", rot=30)
    s.eye(8, 13, size=3)
    s.px([(8, 13)], WHITE)
    s.px([(5, 19), (6, 19)], "#c0501a")
    s.blush(9, 18)


@sprite("leopard_shark")
def _(s):
    c = "#8a8c94"
    s.poly([(24, 15), (31, 8), (30, 15), (27, 19)], c)
    s.poly([(13, 13), (17, 8), (19, 13)], c)
    s.poly([(10, 20), (14, 25), (16, 20)], c)
    m = s.ellipse(15, 16.5, 12.5, 5, c, edge=True)
    s.paint(s.m_ellipse(13, 19.5, 10, 2), "#e8e6e2", within=m)
    s.paint(s.m_poly([(12, 12), (14, 12), (14, 15), (12, 15)]) | s.m_poly([(18, 12), (20, 12), (20, 15), (18, 15)])
            | s.m_poly([(23, 13), (25, 13), (25, 16), (23, 16)]), "#3a3a44", within=m)
    s.paint(s.m_px([(9, 15), (16, 16), (21, 16), (26, 14), (11, 13)]), "#3a3a44", within=m)
    s.eye(5, 14)
    s.blush(5, 17)
    s.px([(3, 18), (4, 18)], "#3a3a44")


# --------------------------------------------------------------------------- output
def load_species(state=None):
    """Rows from each state's species list (or just `state`), first occurrence of a slug wins."""
    states = json.loads(STATES_JSON.read_text(encoding="utf-8"))["states"]
    rows, seen = [], set()
    for st in states:
        if state and st["code"] != state.upper():
            continue
        with open(STATES_JSON.parent / st["species"], newline="", encoding="utf-8") as f:
            for r in csv.DictReader(f):
                if r["slug"] not in seen:
                    seen.add(r["slug"])
                    rows.append(r)
    return rows


def draw(slug) -> Image.Image:
    s = Sprite()
    S[slug](s)
    return s.render()


def animate(slug) -> tuple[Image.Image, list[str]]:
    """The animation sheet (a row of frames per pose) and the poses really drawn."""
    out = Image.new("RGBA", (N * FRAMES, N * len(ACTS)), (0, 0, 0, 0))
    probe = Sprite()
    S[slug](probe)
    acts = [a for a in ACTS if a in probe.acts]
    for row, act in enumerate(ACTS):
        for f in range(FRAMES):
            s = Sprite(act if act in acts else "idle", f if act in acts else 0)
            S[slug](s)
            out.alpha_composite(s.render(), (N * f, N * row))
    return out, acts


def sheet(rows, scale=4, cols=10, silhouettes=False):
    cell = N * scale + 8
    n = len(rows)
    lines = (n + cols - 1) // cols
    out = Image.new("RGBA", (cols * cell, lines * (cell + 12)), (246, 244, 238, 255))
    d = ImageDraw.Draw(out)
    for i, r in enumerate(rows):
        img = draw(r["slug"])
        if silhouettes:
            img = silhouette(img)
        big = img.resize((N * scale, N * scale), Image.NEAREST)
        x, y = (i % cols) * cell + 4, (i // cols) * (cell + 12) + 4
        out.alpha_composite(big, (x, y))
        d.text((x, y + N * scale + 1), r["common_name"][:22], fill=(60, 60, 60, 255))
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--out", type=Path, default=OUT)
    ap.add_argument("--sheet", type=Path, help="also write a preview sheet PNG here")
    ap.add_argument("--state", help="only this state's species (e.g. NC)")
    ap.add_argument("--anim-sheet", type=Path, help="also write a preview of every animation here")
    args = ap.parse_args()

    rows = load_species(args.state)
    missing = [r["slug"] for r in rows if r["slug"] not in S]
    if missing:
        # Fine while a state's art is being drawn: the apps show the "?" egg
        # (tools/make_placeholder.py) for these until then.
        print(f"no sprite drawn yet for {len(missing)} species (placeholder shown): {', '.join(missing)}",
              file=sys.stderr)
        rows = [r for r in rows if r["slug"] in S]
    # Every drawing is written, listed or not, so a species can move between lists
    # (or a list branch can land later) without the art going missing.
    slugs = list(S) if not args.state else [r["slug"] for r in rows]
    args.out.mkdir(parents=True, exist_ok=True)
    anim_dir = args.out / "anim"
    anim_dir.mkdir(exist_ok=True)
    index_path = anim_dir / "index.json"
    index = json.loads(index_path.read_text(encoding="utf-8"))["acts"] if index_path.exists() else {}
    anims = {}
    for slug in slugs:
        img = draw(slug)
        img.save(args.out / f"{slug}.png", optimize=True)
        silhouette(img).save(args.out / f"{slug}_silhouette.png", optimize=True)
        anims[slug], index[slug] = animate(slug)
        anims[slug].save(anim_dir / f"{slug}.png", optimize=True)
    index_path.write_text(json.dumps({"frames": FRAMES, "rows": list(ACTS), "acts": dict(sorted(index.items()))},
                                     indent=1) + "\n", encoding="utf-8")
    if args.anim_sheet:
        scale, cols = 3, 2
        cell_w, cell_h = N * FRAMES * scale + 10, N * len(ACTS) * scale + 18
        lines = (len(slugs) + cols - 1) // cols
        prev = Image.new("RGBA", (cols * cell_w, lines * cell_h), (246, 244, 238, 255))
        d = ImageDraw.Draw(prev)
        for i, slug in enumerate(slugs):
            x, y = (i % cols) * cell_w + 4, (i // cols) * cell_h + 4
            big = anims[slug].resize((anims[slug].width * scale, anims[slug].height * scale), Image.NEAREST)
            prev.alpha_composite(big, (x, y + 12))
            d.text((x, y), f"{slug}: {', '.join(index[slug])}", fill=(60, 60, 60, 255))
        args.anim_sheet.parent.mkdir(parents=True, exist_ok=True)
        prev.save(args.anim_sheet, optimize=True)
    if not args.state:
        with open(args.out / "credits.csv", "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(["slug", "file", "silhouette", "source", "license"])
            for slug in sorted(slugs):
                w.writerow([slug, f"{slug}.png", f"{slug}_silhouette.png",
                            "drawn by tools/make_sprites.py (original pixel art, no photo source)", "CC0-1.0"])
    if args.sheet:
        args.sheet.parent.mkdir(parents=True, exist_ok=True)
        color = sheet(rows)
        sil = sheet(rows, silhouettes=True)
        both = Image.new("RGBA", (color.width, color.height * 2 + 16), (255, 255, 255, 255))
        both.alpha_composite(color, (0, 0))
        both.alpha_composite(sil, (0, color.height + 16))
        both.save(args.sheet, optimize=True)
    print(f"wrote {len(slugs) * 2} sprites to {args.out}")


if __name__ == "__main__":
    main()
