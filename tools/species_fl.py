"""Sprites for the Florida species that aren't on an earlier state's list."""
from __future__ import annotations

from archetypes import (BLACK, WHITE, bird, butterfly, critter, dolphin, dragonfly, duck, fish, flecks, frog,
                        lizard, snake, spider_top, sprite, turtle, wader)
from pixel import mix
from species_tx import _segmented


# --------------------------------------------------------------------------- mammals
@sprite("west_indian_manatee")
def _(s):
    s.can("swim")
    w = s.wave() if s.act == "swim" else 0
    body, light = "#8a9096", "#aab0b6"
    # the round paddle tail
    s.ellipse(29, 18 - w * 2, 4, 5.5, mix(body, "#000000", 0.1), rot=10, edge=True)
    m = s.ellipse(16, 18, 13, 7.5, body, edge=True)
    s.paint(s.m_ellipse(14, 22.5, 10, 2.6), light, within=m)
    s.paint(s.m_px([(18, 13), (22, 15), (12, 14), (25, 17)]), mix(body, "#4a6a4a", 0.3), within=m)
    s.ellipse(11, 23, 4, 1.8, mix(body, "#000000", 0.15), rot=35)
    s.ellipse(4, 17.5, 4.2, 3.8, light, edge=True)  # whiskery snout
    s.px([(2, 16), (3, 17), (2, 18), (4, 19)], mix(light, "#000000", 0.35))
    s.px([(1, 17), (1, 18)], "#3a3a40")
    s.eye(8, 14)


@sprite("tamanends_bottlenose_dolphin")
def _(s):
    dolphin(s, "#6a7a8e", "#dfe4ea")


@sprite("hispid_cotton_rat")
def _(s):
    critter(s, "#7a6448", "#c8bca8", build="vole", ears="round", ear_in="#d8a8a0", tail="rat", tail_col="#6a5a4a",
            muzzle="#a89478", nose="#e88a90", feet="#9a8a7a",
            markings=lambda s, g: flecks(s, g["body"], "#5a4a34", every=4))


@sprite("mexican_free_tailed_bat")
def _(s):
    s.can("fly")
    # Seen from the front with its wings spread: tips up on the upbeat frames.
    up = s.act == "fly" and s.f % 2 == 0
    fur, wing, bone = "#6a5444", "#3e3230", "#241c1a"
    lift = -5 if up else 0
    for side in (-1, 1):
        x = lambda v: 16 + side * v
        tip = (x(15), 9 + lift)
        pts = [(x(3), 13), tip, (x(13), 19 + lift * .4), (x(10), 17 + lift * .2), (x(8), 21), (x(5), 19), (x(3), 23)]
        s.poly(pts, wing, edge=True)
        for end in (tip, (x(13), 19 + lift * .4), (x(8), 21)):
            s.path([(x(3), 13.5), end], 0.45, bone, shade=False)
        s.px([(round(x(15)), round(9 + lift) - 1)], bone)  # the thumb claw
    s.poly([(13, 24), (19, 24), (17.5, 28), (16, 30), (14.5, 28)], wing)  # tail membrane
    s.path([(16, 27), (16, 31)], 0.5, fur, shade=False)  # its free tail
    m = s.ellipse(16, 19, 3.8, 6, fur, edge=True)
    s.paint(s.m_ellipse(16, 21, 2.5, 3.5), mix(fur, "#ffffff", 0.22), within=m)
    s.poly([(12, 9.5), (11.5, 3.5), (15, 8.5)], fur)  # big ears
    s.poly([(18, 9.5), (20.5, 3.5), (17, 8.5)], fur)
    s.poly([(12.6, 8.8), (12.3, 5.5), (14.2, 8.4)], "#c88a80", shade=False)
    s.poly([(19.4, 8.8), (19.7, 5.5), (17.8, 8.4)], "#c88a80", shade=False)
    s.ellipse(16, 11.5, 4, 3.6, fur, edge=True)
    s.ellipse(16, 13.5, 1.8, 1.2, mix(fur, "#000000", 0.25))  # wrinkled lips
    s.px([(15, 13), (17, 13)], "#2b2226")
    s.eye(14, 11)
    s.eye(18, 11)


@sprite("eastern_mole")
def _(s):
    s.can("walk")
    w = s.wave() if s.act == "walk" else 0
    fur, pink = "#5a5660", "#f0a8a8"
    s.path([(28, 25), (31, 26)], (1.2, 0.6), pink)  # stubby tail
    for x, sw in ((22, -w), (25, w)):
        s.ellipse(x - sw, 28, 2, 1.3, pink)
    m = s.ellipse(18, 22, 11, 6.5, fur, edge=True)
    s.paint(s.m_ellipse(17, 18, 8, 2), mix(fur, "#ffffff", 0.18), within=m)
    s.paint(s.m_px([(14, 21), (20, 19), (24, 22), (11, 24)]), mix(fur, "#ffffff", 0.3), within=m)
    # Big pink digging hands, turned out to the side.
    s.ellipse(10 + w, 27, 3.6, 2.2, pink, rot=-15, edge=True)
    s.px([(7 + round(w), 28), (8 + round(w), 29), (10 + round(w), 29)], mix(pink, "#000000", 0.25))
    s.path([(9, 21), (2, 23)], (2.6, 1.0), fur)  # pointed snout
    s.ellipse(1.5, 23.5, 1.4, 1.2, pink)
    s.px([(6, 20)], "#2b2226")  # tiny eye in the fur
    if s.act == "walk" and s.f % 2:
        s.shift(0, -1)


# --------------------------------------------------------------------------- birds
@sprite("anhinga")
def _(s):
    def wing(s, m):
        for x, y in ((17, 17), (19, 16), (21, 18), (18, 20), (22, 15)):
            s.paint(s.m_px([(x, y), (x + 1, y)]), "#d8dce0", within=m)
    bird(s, "#1e1e24", "#26262c", head="#2a2a30", wing="#1a1a20", tail_col="#2a2a30", beak="long",
         beak_col="#e8b040", legs="#3a3a40", tail="fan", wing_mark=wing)
    s.eye(8, 10, color="#e05a2a")


@sprite("boat_tailed_grackle")
def _(s):
    bird(s, "#1a1a30", "#22223a", head="#24244a", wing="#16162a", tail_col="#16162a", beak="crow",
         beak_col="#141218", legs="#2a2630", tail="long", eye_col="#6a4a2a")


@sprite("common_gallinule")
def _(s):
    duck(s, "#3a3a46", "#4a4a56", "#2a2a32", bill="#d8302a", ring=None, speculum=WHITE, tail_col=WHITE)
    s.ellipse(5.5, 8.5, 1.6, 1.8, "#d8302a")
    s.px([(1, 13), (0, 13)], "#f2d22a")


@sprite("purple_gallinule")
def _(s):
    duck(s, "#4a6aa0", "#5a4aa8", "#4a3a9a", bill="#d8302a", ring=None, speculum="#3a9a7a", tail_col=WHITE)
    s.ellipse(5.5, 8.5, 1.6, 1.8, "#bcd8f4")
    s.px([(1, 13), (0, 13)], "#f2d22a")


@sprite("double_crested_cormorant")
def _(s):
    duck(s, "#26262c", "#30303a", "#26262c", bill="#5a4a3a", ring=None, speculum="#3a3a44", tail_col="#1a1a20")
    s.px([(5, 14), (6, 14), (5, 15), (6, 15)], "#f0902a")
    s.eye(7, 10, color="#3ac8a0")


@sprite("tricolored_heron")
def _(s):
    wader(s, "#4a5a8a", neck="#5a6a9a", head="#4a5a8a", beak="#e8b830", legs="#e8c84a", plume=WHITE,
          wing="#44527e")
    s.paint(s.m_ellipse(20, 18.5, 6, 1.6), WHITE, within=s.m_ellipse(20, 15, 7, 5))


@sprite("western_cattle_egret")
def _(s):
    wader(s, WHITE, neck=WHITE, head=WHITE, beak="#f0a030", legs="#e8b030", wing="#f2f0ec", cap="#f0c080")
    s.paint(s.m_ellipse(14.5, 10, 2, 3), "#f0c080", within=s.m_path([(15, 14), (13, 11), (14, 8), (11, 5)], 1.8))


@sprite("wood_stork")
def _(s):
    wader(s, WHITE, neck="#8a8478", head="#8a8478", beak="#4a4038", legs="#3a3430", wing="#f0eee8",
          curved=True)
    s.poly([(26, 14), (31, 17), (25, 18)], BLACK)
    s.paint(s.m_ellipse(23, 17, 3, 1.2), BLACK, within=s.m_ellipse(22, 14, 5, 3.3, rot=-10))


@sprite("sandhill_crane")
def _(s):
    wader(s, "#a8a4a0", neck="#b8b4b0", head="#c8c4c0", beak="#3a3430", legs="#3a3430", cap="#d8302a",
          face=WHITE, wing="#988a7a")


@sprite("limpkin")
def _(s):
    wader(s, "#6a4a2e", neck="#7a5a3a", head="#7a5a3a", beak="#c8a050", legs="#4a4a3a", curved=True)
    s.paint(s.m_px([(18, 13), (21, 15), (23, 13), (19, 16), (12, 9), (14, 6), (11, 4)]), WHITE)


@sprite("roseate_spoonbill")
def _(s):
    wader(s, "#f0a0b8", neck=WHITE, head="#e8e0d0", beak="#c8b890", legs="#c84a5a", wing="#e86a90")
    s.ellipse(-1, 6.5, 2.2, 1.6, "#c8b890")  # the spoon
    s.paint(s.m_ellipse(23, 13, 2.5, 1.5), "#d83a5a", within=s.m_ellipse(22, 14, 5, 3.3, rot=-10))


@sprite("palm_warbler")
def _(s):
    def face(s):
        s.paint(s.m_ellipse(11, 7, 3.5, 1.6), "#b8502a", within=s.last)
        s.paint(s.m_line(6, 9, 12, 9), "#f4e48a", within=s.last)

    def belly(s, m):
        s.paint(s.m_px([(12, 21), (15, 22), (13, 24)]), "#a8784a", within=m)
    bird(s, "#8a7a5a", "#f0dc6a", head="#8a7a5a", wing="#7a6a4a", tail_col="#5a4a3a", beak="thin",
         beak_col="#2b2630", legs="#3a3430", tail="mid", face=face, belly_mark=belly)
    s.ellipse(22, 24, 2.4, 1.6, "#f2d22a")


@sprite("sanderling")
def _(s):
    def wing(s, m):
        s.paint(s.m_ellipse(17, 17, 2.6, 1.2), "#2b2630", within=m)
    bird(s, "#d8d8d4", WHITE, head="#e0e0dc", wing="#b8b8b4", tail_col="#8a8a86", beak="thin",
         beak_col="#1d1a20", legs="#1d1a20", tail="short", wing_mark=wing)


@sprite("willet")
def _(s):
    def wing(s, m):
        s.paint(s.m_line(15, 21, 24, 18) | s.m_line(15, 22, 24, 19), WHITE, within=m)
    bird(s, "#9a948a", "#e8e4dc", head="#a8a298", wing="#8a847a", tail_col="#7a746a", beak="long",
         beak_col="#3a3430", legs="#7a8a9a", tail="short", wing_mark=wing)


@sprite("ruddy_turnstone")
def _(s):
    def wing(s, m):
        s.paint(s.m_ellipse(19, 18, 4, 2), "#b8602a", within=m)
        s.paint(s.m_px([(17, 20), (21, 17)]), BLACK, within=m)

    def face(s):
        s.paint(s.m_line(6, 13, 13, 16) | s.m_line(9, 8, 9, 14), BLACK, within=s.last)
    bird(s, "#2b2630", WHITE, head=WHITE, wing="#a85a2a", tail_col="#2b2630", beak="cone", beak_col="#1d1a20",
         legs="#f08a2a", tail="short", wing_mark=wing, face=face)


# --------------------------------------------------------------------------- reptiles
@sprite("gopher_tortoise")
def _(s):
    turtle(s, "#8a7454", "#9a8a6a", dome=True, scutes="#a08a64", rim="#6a5a40")


@sprite("florida_softshell_turtle")
def _(s):
    turtle(s, "#6a6a4a", "#7a7a5a", speckle="#4a4a34", rim="#8a8a64")
    s.path([(4, 19), (0.5, 19.5)], 0.9, "#7a7a5a")  # snorkel snout


@sprite("florida_red_bellied_cooter")
def _(s):
    turtle(s, "#3a3a2e", "#3a3e2a", scutes="#5a3a2a", speckle="#d8402a")
    s.paint(s.m_line(9, 21, 9, 24) | s.m_line(10, 26, 11, 29), "#e8c040")


@sprite("green_iguana")
def _(s):
    def pat(s, m):
        for x in (12, 16, 20):
            s.paint(s.m_line(x, 19, x, 25), "#3a6a2a", within=m)
    lizard(s, "#5aa04a", "#a8d080", throat="#8ac060", pattern=pat, tail_col="#5a8a3a",
           tail_pts=[(20, 22), (27, 25), (33, 24), (36, 20)])
    s.px([(9, 14), (11, 15), (13, 16), (15, 17), (17, 18), (19, 18), (10, 14), (12, 15)], "#7ac05a")
    s.ellipse(7, 23.5, 2.4, 2.4, "#8ac060")  # dewlap
    s.px([(6, 21), (7, 21)], "#d8e8c0")
    for x in (24, 27, 30, 33):
        s.paint(s.m_line(x, 18, x, 30), "#3a5a2a", within=s.m_path([(20, 22), (27, 25), (33, 24), (36, 20)], (2.4, 0.7)))


@sprite("northern_curly_tailed_lizard")
def _(s):
    def pat(s, m):
        s.paint(s.m_px([(10, 20), (13, 21), (16, 20), (19, 21), (12, 23), (18, 23)]), "#4a4034", within=m)
    lizard(s, "#9a8a6a", "#e4dcc4", pattern=pat,
           tail_pts=[(20, 22), (26, 24), (29, 20), (27, 16), (24, 17), (25, 19)])


@sprite("peterss_rock_agama")
def _(s):
    lizard(s, "#3a4a9a", "#5a6ab0", head="#e86a2a", throat="#f0a050", tail_col="#d8702a")


@sprite("tropical_house_gecko")
def _(s):
    def pat(s, m):
        for x in (10, 14, 18, 22):
            s.paint(s.m_path([(x, 19), (x + 1.5, 21), (x, 23)], 0.6), "#6a5a4a", within=m)
    lizard(s, "#b8a88a", "#e8e0cc", pattern=pat, smooth=True, eye_big=True, legs="#a8987a")


@sprite("north_american_racer")
def _(s):
    snake(s, "#26262e", belly="#e8e8ee", head="#26262e")
    s.paint(s.m_ellipse(10, 13.2, 3.5, 1.2), WHITE, within=s.m_ellipse(12.5, 10.5, 5.4, 4.2))


@sprite("florida_cottonmouth")
def _(s):
    snake(s, "#5a5440", belly="#c8bca0", bands="#3a3428", band_period=4.5, band_len=2.0, head="#5a5440",
          head_w=6)
    s.paint(s.m_line(6, 9, 12, 10), "#2a2620", within=s.m_ellipse(12.5, 10.5, 6, 4.2))


# --------------------------------------------------------------------------- amphibians
@sprite("cuban_tree_frog")
def _(s):
    frog(s, "#c8c4a8", "#f4f0e4", build="tree", pads=True, spots=4, spot_big=True)


@sprite("southern_toad")
def _(s):
    frog(s, "#8a5a3a", "#e8d8c0", build="toad", spots=6, crown="#5a3a24", parotoid="#7a4e32")


@sprite("cane_toad")
def _(s):
    frog(s, "#8a6a40", "#e8dcb8", build="toad", tympanum="#6a4a2a", spots=8, parotoid="#a8844e")


@sprite("greenhouse_frog")
def _(s):
    frog(s, "#9a5a3a", "#e8d4c0", mask="#c8945a", spots=2)


@sprite("southern_cricket_frog")
def _(s):
    frog(s, "#7a8a5a", "#f0ecd8", mask="#3a4a2a", spots=2, crown="#a8402a")


# --------------------------------------------------------------------------- fish
@sprite("florida_gar")
def _(s):
    def pat(s, m):
        s.paint(s.m_px([(8, 15), (11, 17), (14, 15), (17, 17), (20, 15), (23, 17), (12, 14), (19, 18)]),
                "#2a2a20", within=m)
    fish(s, "#7a7a4a", "#d8d4b0", fin="#5a5a3a", pattern=pat, slim=True)
    s.path([(4, 16), (-3, 16.5)], (1.3, 0.7), "#7a7a4a")  # long toothy snout


@sprite("florida_bass")
def _(s):
    def pat(s, m):
        s.paint(s.m_path([(8, 16), (14, 17), (19, 16), (24, 17)], 1.0), "#2a4a2a", within=m)
    fish(s, "#4e7a42", "#e8ecd0", fin="#3e6a32", pattern=pat, slim=True)


@sprite("eastern_mosquitofish")
def _(s):
    fish(s, "#9a9a8a", "#e4e4d8", fin="#8a8a7a", slim=True)


@sprite("gray_snapper")
def _(s):
    def pat(s, m):
        s.paint(s.m_line(3, 13, 9, 15), "#5a4a4a", within=m)
    fish(s, "#8a6a6a", "#c8b0a8", fin="#a85a4a", pattern=pat)


@sprite("mayan_cichlid")
def _(s):
    def pat(s, m):
        for x in (12, 16, 20):
            s.paint(s.m_line(x, 11, x - 1, 18), "#3a4a2a", within=m)
        s.paint(s.m_ellipse(22, 15, 1.6, 1.6), BLACK, within=m)
        s.paint(s.m_ellipse(22, 15, 2.4, 2.4) & ~s.m_ellipse(22, 15, 1.6, 1.6), "#4ac8d8", within=m)
    fish(s, "#6a7a4a", "#e05a3a", pattern=pat)


# --------------------------------------------------------------------------- invertebrates
@sprite("white_peacock")
def _(s):
    def pat(s, fm, hm):
        w = fm | hm
        s.paint(s.m_line(2, 7, 2, 14) | s.m_line(5, 20, 9, 26), "#e8a050", mirror=True, within=w)
        s.paint(s.m_ellipse(6, 11, 1.2, 1.2) | s.m_ellipse(8, 21, 1.2, 1.2), BLACK, mirror=True, within=w)
        s.paint(s.m_line(9, 6, 12, 12), "#c8b498", mirror=True, within=fm)
    butterfly(s, "#f4f0e8", "#f0ece0", pattern=pat)


@sprite("zebra_longwing")
def _(s):
    def pat(s, fm, hm):
        s.paint(s.m_line(3, 6, 13, 10) | s.m_line(3, 7, 13, 11), "#f4e050", mirror=True, within=fm)
        s.paint(s.m_line(4, 12, 13, 15), "#f4e050", mirror=True, within=fm)
        s.paint(s.m_line(5, 19, 13, 20) | s.m_px([(7, 24), (9, 25), (11, 24)]), "#f4e050", mirror=True, within=hm)
    butterfly(s, "#1e1a24", "#1e1a24", pattern=pat)


@sprite("golden_silk_spider")
def _(s):
    def pat(s, m):
        s.paint(s.m_px([(14, 18), (18, 18), (14, 22), (18, 22), (15, 25), (17, 25)]), WHITE, within=m)
    spider_top(s, "#e8a02a", "#4a3a2a", pattern=pat, ceph="#d8d0c0", leg_bands="#f0c040", web=True)


@sprite("spinybacked_orbweaver")
def _(s):
    s.can("walk")
    w = s.wave() if s.act == "walk" else 0
    for i, (x0, y0, x1, y1) in enumerate([(12, 13, 7, 9), (12, 15, 6, 15), (12, 17, 7, 21), (13, 18, 9, 23)]):
        d = round(w * (1 if i % 2 else -1))
        s.line(x0, y0, x1, y1 + d, "#2b2630", mirror=True)
    s.ellipse(16, 12, 3, 2.6, "#2b2630", edge=True)
    m = s.ellipse(16, 20, 9, 5.5, WHITE, edge=True)
    s.paint(s.m_px([(10, 18), (13, 21), (16, 18), (19, 21), (22, 18), (12, 23), (20, 23), (16, 22)]), BLACK, within=m)
    for x, y in ((7, 18), (25, 18), (9, 24), (23, 24), (11, 15), (21, 15)):
        s.ellipse(x, y, 1.3, 1.3, "#d8302a")
    s.eye(14, 18)
    s.eye(18, 18)


@sprite("blue_dasher")
def _(s):
    dragonfly(s, "#5a6a3a", "#7ab0e0")
    s.paint(s.m_line(16, 27, 16, 30) | s.m_line(15, 27, 15, 30), BLACK)


@sprite("halloween_pennant")
def _(s):
    dragonfly(s, "#8a5a2a", "#6a4a2a", wing="#f8c860", wing_tint="#8a5a2a")


@sprite("bumblebee_millipede")
def _(s):
    pts = _segmented(s, 9, "#2b2630", "#2b2630", "#f0d040", leg_len=1.8, spacing=2.8, r=2.3, antenna=2.5)
    for i, (x, y) in enumerate(pts[1:], 1):
        if i % 2:
            s.px([(round(x) - 1, round(y) - 1), (round(x), round(y) - 1), (round(x) - 1, round(y))], "#f0d040")


@sprite("rusty_millipede")
def _(s):
    _segmented(s, 9, "#a8502a", "#7a3a20", "#e0a070", leg_len=1.8, spacing=2.8, r=2.3, antenna=2.5)


@sprite("portuguese_man_o_war")
def _(s):
    s.can("swim")
    w = s.wave() if s.act == "swim" else 0
    for x0 in (9, 13, 17, 21, 24):
        s.path([(x0, 19), (x0 - 1 + w, 24), (x0 + 1 - w, 28), (x0 + w, 32)], 0.5, "#7a5ad8", shade=False)
    s.ellipse(16, 19.5, 10, 2.4, "#5a8ae8")
    m = s.ellipse(15, 13, 10, 6.5, "#a8c8f4", edge=True, rot=-10)
    s.paint(s.m_poly([(8, 7), (22, 4), (24, 8), (10, 10)]), "#d080d8", within=m)  # the sail's crest
    s.paint(s.m_ellipse(13, 16, 7, 2), "#c8b0f0", within=m)
    s.eye(11, 13)
    s.eye(17, 12)
