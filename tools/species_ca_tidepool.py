"""Sprites for the species added to the California list in the species review
(Ringtail, Black Oystercatcher and the tide-pool animals)."""
from __future__ import annotations

from archetypes import (BLACK, EYE, WHITE, bird, critter, fish, sprite)
from pixel import mix


@sprite("ringtail")
def _(s):
    # Cat-sized, slim, with a huge black-and-white ringed tail and white eye rings.
    critter(s, "#a88a6a", "#f0e6d6", build="ringtail", ears="round", ear_in="#e8c8b0", tail="ringed",
            tail_col="#f2ecdf", tail_tip="#2b2630", nose="#3a2a2a", eye_ring="#f4ece0")


@sprite("black_oystercatcher")
def _(s):
    bird(s, "#2a2430", "#322c38", head="#2a2430", wing="#241f2a", tail_col="#241f2a", beak="long",
         beak_col="#f0502a", legs="#f0c0b0", tail="short")
    s.px([(8, 10), (9, 10), (8, 11), (9, 11)], "#f6d030")
    s.px([(9, 11)], EYE)


@sprite("blue_banded_hermit_crab")
def _(s):
    shell = "#8a6a50"
    m = s.ellipse(20, 18, 9, 9, shell, edge=True)
    s.poly([(24, 10), (30, 6), (28, 13)], shell, edge=True)
    s.paint(s.m_path([(20, 18), (23, 15), (26, 18), (23, 23), (17, 22), (15, 16), (19, 11)], 0.5),
            mix(shell, "#000000", 0.35), within=m)
    s.paint(s.m_px([(14, 21), (18, 25), (24, 24), (26, 14)]), "#b8987a", within=m)
    for i, y in enumerate((23, 26)):
        p = s.path([(11, y), (7, y + 2), (5, y + 5)], 0.8, "#c8604a", shade=False)
        s.paint(s.m_px([(7, y + 2), (6, y + 3)]), "#4a8ae0", within=p)
    s.ellipse(9, 19, 5, 4, "#c8604a", edge=True)
    s.ellipse(5, 14, 2.8, 2.2, "#d8704a", rot=-20)
    s.ellipse(7.5, 24, 2.2, 1.8, "#d8704a")
    s.line(8, 15, 4, 8, "#f0903a")
    s.line(10, 15, 11, 8, "#f0903a")
    s.px([(7, 17), (10, 17)], EYE)
    s.blush(7, 20)


@sprite("black_turban_snail")
def _(s):
    s.ellipse(14, 28, 11, 2.2, "#4a3a4a")
    s.ellipse(8, 25, 5, 3, "#3a3036", edge=True)
    s.line(5, 22, 4, 18, "#3a3036")
    s.line(8, 22, 9, 18, "#3a3036")
    m = s.poly([(9, 27), (25, 27), (21, 9), (17, 5), (13, 9)], "#3a2a40", edge=True)
    for y in (12, 17, 22):
        s.paint(s.m_line(9, y + 1, 25, y - 1), "#5a4a64", within=m)
    s.paint(s.m_px([(17, 6), (18, 7)]), "#c8b8d8", within=m)
    s.eye(13, 18)
    s.eye(19, 18)
    s.blush(11, 21)
    s.blush(20, 21)
    s.px([(16, 21), (17, 21)], "#c8b8d8")


@sprite("california_mussel")
def _(s):
    s.ellipse(17, 18, 13, 7.5, "#2e3448", rot=-30, edge=True)
    for k, c in enumerate(("#3e4a66", "#4a5a7a")):
        s.paint(s.m_ellipse(17, 18, 11 - k * 3, 5.5 - k * 1.5, rot=-30) & ~s.m_ellipse(17, 18, 10 - k * 3, 4.5 - k * 1.5, rot=-30),
                c)
    s.paint(s.m_ellipse(23, 13, 4, 2.5, rot=-30), "#8a6a4a")
    s.path([(7, 26), (4, 29), (2, 30)], 0.5, "#b89a6a", shade=False)
    s.eye(12, 17)
    s.eye(18, 14)
    s.blush(12, 20)
    s.blush(20, 17)


@sprite("gooseneck_barnacle")
def _(s):
    s.ellipse(16, 29, 13, 2.5, "#6a6460")
    for x, top, lean in ((9, 12, -2), (16, 7, 0), (23, 12, 2)):
        s.path([(x, 29), (x + lean / 2, (29 + top) / 2), (x + lean, top + 4)], 2.4, "#6a5446")
        hm = s.poly([(x + lean - 3.5, top + 5), (x + lean - 2, top), (x + lean, top - 2), (x + lean + 2, top),
                     (x + lean + 3.5, top + 5)], "#ece6d8", edge=True)
        s.paint(s.m_line(x + lean, top - 1, x + lean, top + 4), "#b8b0a0", within=hm)
        s.paint(s.m_line(x + lean - 3, top + 5, x + lean + 3, top + 5), "#2b2630", within=hm)
    s.eye(13, 11)
    s.eye(18, 11)
    s.blush(12, 13)
    s.blush(19, 13)


@sprite("owl_limpet")
def _(s):
    s.ellipse(16, 26, 14, 3, "#8a8478")
    m = s.fill(s.m_ellipse(16, 24, 13, 13) & s.m_poly([(0, 0), (32, 0), (32, 25), (0, 25)]), "#7a5a3e", edge=True)
    s.paint(s.m_px([(9, 18), (12, 15), (16, 13), (21, 16), (23, 20), (8, 22), (19, 21), (14, 19)]), "#c8b090",
            within=m)
    s.paint(s.m_ellipse(16, 24, 13, 13) & ~s.m_ellipse(16, 24, 11.5, 11.5), "#a88a66", within=m)
    s.eye(12, 18)
    s.eye(18, 18)
    s.blush(10, 21)
    s.blush(20, 21)


@sprite("california_sea_hare")
def _(s):
    c = "#9a4a5a"
    s.ellipse(17, 23, 13, 5.5, c)
    s.ellipse(19, 18, 8, 5, mix(c, "#ffffff", 0.1), edge=True)
    s.paint(s.m_px([(15, 16), (19, 15), (23, 17), (13, 22), (20, 22), (26, 23), (9, 24)]), "#d8a0a8")
    s.ellipse(7, 18, 5, 4.2, c, edge=True)
    s.ellipse(6, 11, 1.6, 4, c, rot=-15)
    s.ellipse(10, 11, 1.6, 4, c, rot=15)
    s.paint(s.m_px([(6, 9), (10, 9)]), "#d8a0a8")
    s.eye(5, 17)
    s.blush(6, 20)


@sprite("hopkins_rose")
def _(s):
    c = "#f0709a"
    for x in range(6, 27, 3):
        for y0 in (16, 13):
            s.ellipse(x + (1 if y0 == 13 else 0), y0, 1.3, 2.6, mix(c, "#ffffff", 0.2 if y0 == 13 else 0.0))
    s.ellipse(16, 22, 12, 5, c, edge=True)
    s.ellipse(17, 26, 11, 1.6, "#e0507a")
    s.line(7, 17, 5, 11, c)
    s.line(10, 17, 11, 11, c)
    s.eye(9, 20)
    s.eye(14, 20)
    s.blush(8, 23)
    s.blush(15, 23)


@sprite("tidepool_sculpin")
def _(s):
    def pat(s, m):
        for x in (12, 17, 22):
            s.paint(s.m_poly([(x - 1.5, 9), (x + 1.5, 9), (x + 0.5, 17), (x - 1, 17)]), "#3e4a30", within=m)
        s.paint(s.m_px([(10, 13), (15, 15), (20, 14), (24, 16)]), "#c8b880", within=m)
    fish(s, "#6a7a4a", "#d8d0a8", fin="#5a6a40", pattern=pat, slim=True)
    s.ellipse(15, 22, 3.5, 1.6, "#b8a060", rot=30)


@sprite("by_the_wind_sailor")
def _(s):
    s.px([(2, 29), (6, 30), (25, 30), (29, 29)], "#8fd3ff")
    s.poly([(10, 21), (24, 4), (23, 21)], "#e6f2fa", shade=False, edge=True)
    s.paint(s.m_line(11, 20, 23, 6), "#c8dcea")
    s.path([(9, 27), (12, 29), (16, 28), (20, 29), (23, 27)], 0.6, "#3a5ab8", shade=False)
    s.ellipse(16, 23, 12, 4.5, "#3a6ad8", edge=True)
    s.paint(s.m_ellipse(16, 23, 9, 2.6) & ~s.m_ellipse(16, 23, 7.5, 1.6), "#6a9ae8")
    s.eye(11, 22)
    s.eye(19, 22)
    s.blush(9, 24)
    s.blush(21, 24)
    s.px([(15, 25), (16, 25)], "#1d2a5a")
