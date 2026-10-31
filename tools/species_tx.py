"""Sprites for the Texas species that aren't on an earlier state's list. Many of them
(doves, sparrows, herons, sunfish) are common across the South and East, so later
states reuse them."""
from __future__ import annotations

from archetypes import (BLACK, EYE, WHITE, beetle_top, bird, butterfly, crab, critter, dragonfly, duck, fish,
                        flecks, frog, lizard, quad, snake, sprite, teeth, wader)
from pixel import mix


# --------------------------------------------------------------------------- mammals
@sprite("mexican_long_nosed_armadillo")
def _(s):
    s.can("walk")
    w = s.wave() if s.act == "walk" else 0
    skin, shell, band = "#c8aea4", "#a8968c", "#6e5e58"
    s.path([(26, 24), (30, 26), (33, 29)], (2.0, 0.6), shell)  # tapering tail
    for x, sw in ((12, w), (23, -w)):
        s.path([(x, 24), (x - sw, 29.5)], 1.4, mix(skin, "#1a1420", 0.25))
    for x, sw in ((10, -w), (21, w)):
        s.path([(x, 24), (x - sw, 29.5)], 1.4, skin)
        s.px([(round(x - sw) - 1, 30), (round(x - sw), 30)], "#6a4a44")
    m = s.ellipse(18, 21, 9.5, 6.5, shell, edge=True)
    s.paint(s.m_ellipse(18, 26.5, 9.5, 1.6), mix(shell, "#ffffff", 0.2), within=m)
    for x in range(13, 24, 2):
        s.paint(s.m_line(x, 14, x, 26), band, within=m)
    s.paint(s.m_px([(10, 17), (12, 16), (25, 17), (27, 19), (11, 20), (26, 22)]), mix(shell, "#ffffff", 0.3), within=m)
    s.poly([(9, 13), (10, 7.5), (12.5, 13)], skin)  # ears
    s.poly([(10, 12), (10.4, 9), (11.6, 12)], "#e8b0b0", shade=False)
    s.ellipse(8.5, 17, 3.6, 3.4, skin, edge=True)
    s.path([(6, 18), (0.5, 21)], (1.4, 0.8), skin)  # the long nose
    s.px([(0, 21)], "#7a5a5a")
    s.eye(7, 16)
    if s.act == "walk" and s.f % 2:
        s.shift(0, -1)


@sprite("wild_boar")
def _(s):
    def tusk(s, b):
        sx, sy = b["snout"][1]
        s.px([(round(sx) + 1, round(sy) + 1), (round(sx) + 1, round(sy))], "#f4ecd8")

    def bristles(s, b):
        bx, by, brx, bry = b["body"]
        s.paint(s.m_ellipse(bx - 2, by - bry + 0.5, brx * 0.8, 1.4), "#2a2220",
                within=s.m_ellipse(bx, by, brx, bry) | s.m_ellipse(bx - 3.5, by - bry + 1.5, 4.5, 2.6))
    quad(s, "#4a3c34", "#6a5a50", build="bear", ears="point", ear_in="#8a6a5a", tail="rat", tail_col="#3a2e28",
         head="#4a3c34", muzzle="#5a4a42", nose="#c89088", feet="#2a2220", markings=bristles, front=tusk)


@sprite("collared_peccary")
def _(s):
    def collar(s, b):
        nx0, ny0 = b["neck"][0]
        s.paint(s.m_path([(nx0 - 0.5, ny0 - 4), (nx0 + 0.5, ny0 + 3)], 1.3), "#f0e8d8",
                within=s.m_ellipse(*b["body"]) | s.m_path([b["neck"][0], b["neck"][1]], b["neck"][2]))
    quad(s, "#5e5652", "#7a706a", build="low", ears="point", ear_in="#3a3230", tail="short", head="#56504c",
         muzzle="#6a625c", nose="#2b2630", feet="#2b2630", belly=False, markings=collar)


@sprite("coypu")
def _(s):
    critter(s, "#7a5a3c", "#b89a7c", build="beaver", ear_in="#5a3e2a", tail="rat", tail_col="#5a4232",
            muzzle="#d8ccc0", nose="#3a2a2a", feet="#3a2a22", face=lambda s, g: teeth(s, g, "#f08a2a"))


@sprite("rock_squirrel")
def _(s):
    critter(s, "#9a8a7a", "#ece4d8", build="squirrel", ear_in="#c8a080", tail="squirrel", tail_col="#8a7a6c",
            tail_tip="#d8d0c4", markings=lambda s, g: flecks(s, g["body"], "#7a6a5c", every=6))


@sprite("black_tailed_prairie_dog")
def _(s):
    critter(s, "#c8a070", "#f0e0c4", build="marmot", ear_in="#a87a50", tail="short", tail_col="#c8a070",
            tail_tip=BLACK, nose="#5a3a2a", feet="#8a6a4a")


@sprite("swamp_rabbit")
def _(s):
    critter(s, "#7a6450", "#e8dccc", build="rabbit", ears="long", ear_in="#d8a8a0", tail="cotton", tail_col=WHITE,
            nose="#d88a90", feet="#5a4838")


# --------------------------------------------------------------------------- birds
@sprite("great_tailed_grackle")
def _(s):
    def sheen(s, m):
        s.paint(s.m_ellipse(18, 18, 3, 1.5), "#4a3a8a", within=m)
    bird(s, "#1e1a2c", "#26203a", head="#2a2248", wing="#1a1630", tail_col="#1a1630", beak="crow",
         beak_col="#141218", legs="#2a2630", tail="long", eye_col="#f0d040", wing_mark=sheen)


@sprite("white_winged_dove")
def _(s):
    def wing(s, m):
        s.paint(s.m_line(16, 21, 24, 18) | s.m_line(16, 22, 24, 19), WHITE, within=m)

    def face(s):
        s.ellipse(8, 10, 1.6, 1.6, "#3a7ad8", shade=False)
        s.px([(7, 13), (8, 13)], "#2b2630")
    bird(s, "#b0a090", "#d8c8b8", head="#b8a090", wing="#a09080", tail_col="#8a7a6c", beak="thin",
         beak_col="#2b2630", legs="#e86a6a", tail="mid", wing_mark=wing, face=face)


@sprite("mourning_dove")
def _(s):
    def spots(s, m):
        s.paint(s.m_px([(18, 18), (21, 17), (20, 20)]), "#2b2630", within=m)

    def face(s):
        s.px([(7, 13), (8, 13)], "#2b2630")
    bird(s, "#c4ae96", "#e4d0bc", head="#c8b29a", wing="#b09a84", tail_col="#a08a76", beak="thin",
         beak_col="#2b2630", legs="#e88a8a", tail="long", wing_mark=spots, face=face)


@sprite("eastern_phoebe")
def _(s):
    bird(s, "#7a7268", "#f2eed8", head="#4a443e", wing="#6a625a", tail_col="#4a443e", beak="thin",
         beak_col="#2b2630", legs="#3a3430", tail="mid")


@sprite("house_sparrow")
def _(s):
    def wing(s, m):
        s.paint(s.m_line(16, 18, 23, 16), "#3a2a20", within=m)
        s.paint(s.m_line(17, 21, 21, 20), WHITE, within=m)

    def face(s):
        s.paint(s.m_ellipse(11, 7, 4, 2), "#8a8a8a", within=s.last)
        s.paint(s.m_ellipse(7, 14.5, 2.4, 1.6), BLACK)
        s.paint(s.m_ellipse(14, 12, 2.5, 1.6), "#a0603a", within=s.last)
    bird(s, "#a0704a", "#d8d0c4", head="#a0603a", wing="#a8784c", tail_col="#7a5a40", beak="cone",
         beak_col="#3a3430", legs="#c99060", tail="short", wing_mark=wing, face=face)


@sprite("yellow_rumped_warbler")
def _(s):
    def wing(s, m):
        s.paint(s.m_ellipse(23, 17, 1.8, 1.4), "#f2d22a")
        s.paint(s.m_line(16, 19, 21, 18), WHITE, within=m)

    def belly(s, m):
        s.paint(s.m_ellipse(11, 20, 2, 1.6) | s.m_ellipse(17, 20, 2, 1.6), "#f2d22a", within=m)
        s.paint(s.m_px([(12, 23), (14, 24), (16, 23)]), "#3a3a44", within=m)

    def face(s):
        s.paint(s.m_ellipse(10, 7, 2, 1.2), "#f2d22a", within=s.last)
        s.px([(9, 13), (10, 13)], WHITE)
    bird(s, "#6a7280", "#f0eee8", head="#5a6270", wing="#4a5260", tail_col="#3a404c", beak="thin",
         beak_col="#2b2630", legs="#3a3430", tail="mid", wing_mark=wing, belly_mark=belly, face=face)


@sprite("scissor_tailed_flycatcher")
def _(s):
    def wing(s, m):
        s.paint(s.m_ellipse(14, 22, 3, 1.6), "#f0a0a0")
    bird(s, "#c8ccd0", "#f4f0ec", head="#d4d8dc", wing="#3a3a44", tail_col="#2b2630", beak="thin",
         beak_col="#2b2630", legs="#2b2630", tail="short", wing_mark=wing)
    # the long forked tail, streaming out behind
    s.path([(22, 19), (27, 15), (32, 11), (35, 8)], (1.2, 0.5), "#2b2630")
    s.path([(22, 21), (28, 21), (32, 20), (35, 19)], (1.2, 0.5), "#2b2630")


@sprite("killdeer")
def _(s):
    def bands(s, m):
        s.paint(s.m_line(8, 17, 17, 17) | s.m_line(8, 18, 17, 18), BLACK, within=m)
        s.paint(s.m_line(9, 21, 16, 21), BLACK, within=m)

    def face(s):
        s.paint(s.m_ellipse(9, 13.5, 3.5, 1.4), WHITE, within=s.last)
        s.paint(s.m_line(5, 11, 11, 11), BLACK, within=s.last)
        s.paint(s.m_ellipse(10, 7, 2.5, 1.2), WHITE, within=s.last)
        s.eye(8, 10, color="#e0502a")
    bird(s, "#9a7a58", WHITE, head="#9a7a58", wing="#8a6a4a", tail_col="#d0782a", beak="thin",
         beak_col="#1d1a20", legs="#d8c8a0", tail="mid", belly_mark=bands, face=face)


@sprite("downy_woodpecker")
def _(s):
    def wing(s, m):
        for x in (17, 19, 21, 23):
            s.paint(s.m_px([(x, 18), (x + 1, 20)]), WHITE, within=m)

    def face(s):
        h = s.last
        s.paint(s.m_ellipse(11, 7, 4.5, 2.2), BLACK, within=h)
        s.paint(s.m_ellipse(14.5, 7.5, 2, 1.4), "#e02a2a", within=h)
        s.paint(s.m_line(6, 12, 15, 12), BLACK, within=h)
    bird(s, BLACK, WHITE, head=WHITE, wing=BLACK, tail_col=BLACK, beak="thin", beak_col="#3a3430",
         legs="#5a5a62", tail="short", wing_mark=wing, face=face)


@sprite("european_starling")
def _(s):
    def spots(s, m):
        s.paint(s.m_px([(14, 20), (17, 23), (19, 19), (12, 23), (16, 17), (21, 21)]), "#f4ecd8", within=m)

    def sheen(s, m):
        s.paint(s.m_ellipse(17, 17, 2.4, 1.4), "#5a3a7a", within=m)
        s.paint(s.m_px([(19, 19), (22, 18)]), "#e0c8a0", within=m)
    bird(s, "#2a2a36", "#323244", head="#2a3a3a", wing="#24242e", tail_col="#1e1e28", beak="thin",
         beak_col="#f2d22a", legs="#e89a8a", tail="short", belly_mark=spots, wing_mark=sheen)


@sprite("laughing_gull")
def _(s):
    def wing(s, m):
        s.paint(s.m_ellipse(25, 17, 3, 1.6), BLACK, within=m)

    def face(s):
        s.paint(s.m_px([(7, 8), (9, 8), (8, 12)]), WHITE, within=s.last)
    bird(s, WHITE, WHITE, head="#2b2630", wing="#6a6a74", tail_col=WHITE, beak="thin", beak_col="#a8202a",
         legs="#3a2a2a", tail="mid", wing_mark=wing, face=face)


@sprite("yellow_crowned_night_heron")
def _(s):
    wader(s, "#8a96a4", neck="#9aa4b0", head="#2b2630", beak="#2b2630", legs="#e0c84a",
          plume=WHITE, cap="#f4ecc8", face=WHITE)


@sprite("snowy_egret")
def _(s):
    wader(s, WHITE, beak="#2b2630", legs="#2b2630", wing="#eef0f2", plume="#f4f4f4", face="#f2d22a")
    s.px([(16, 30), (17, 30), (22, 30), (23, 30)], "#f2d22a")


@sprite("green_heron")
def _(s):
    wader(s, "#3e5a50", neck="#8a4a3a", head="#8a4a3a", beak="#2b2630", legs="#f0a03a",
          cap="#1e3a30", wing="#2e4a40")


@sprite("little_blue_heron")
def _(s):
    wader(s, "#3a4a7a", neck="#6a4a6a", head="#6a4a6a", beak="#8aa0c0", legs="#5a7a6a", wing="#34426e")


@sprite("black_bellied_whistling_duck")
def _(s):
    def legs(s):
        s.line(15, 29, 15, 31, "#f08aa0")
        s.line(19, 29, 19, 31, "#f08aa0")
    duck(s, "#b0603a", "#c07850", "#a89a8a", bill="#f05a5a", ring=None, speculum=WHITE, tail_col=BLACK)
    s.paint(s.m_ellipse(17, 27.5, 9, 2.5), BLACK, within=s.m_ellipse(17, 23, 11, 6.5))
    s.paint(s.m_ellipse(7, 13, 2.2, 1.4), "#e8e4dc")


@sprite("northern_shoveler")
def _(s):
    duck(s, "#b8582a", WHITE, "#1e6a4a", bill="#2b2630", ring=None, speculum="#6a9ad8", tail_col=BLACK)
    s.ellipse(3, 13, 4, 2.3, "#2b2630")  # the big spoon bill
    s.eye(7, 10, color="#f0d040")


@sprite("american_coot")
def _(s):
    duck(s, "#3e3e48", "#4a4a54", "#24242a", bill=WHITE, ring=None, speculum="#3e3e48", tail_col="#2a2a30")
    s.ellipse(5.5, 8.5, 1.5, 1.4, "#a8202a")
    s.eye(7, 10, color="#c8202a")


@sprite("neotropic_cormorant")
def _(s):
    duck(s, "#2a2a30", "#34343c", "#2a2a30", bill="#6a5a4a", ring=None, speculum="#3a3a44", tail_col="#1e1e24")
    s.px([(5, 15), (6, 15), (6, 14)], "#e8c070")
    s.px([(0, 13), (0, 14)], "#4a3a2a")
    s.eye(7, 10, color="#3ac8a0")


# --------------------------------------------------------------------------- reptiles
@sprite("texas_spiny_lizard")
def _(s):
    def pat(s, m):
        for x in (10, 13, 16, 19):
            s.paint(s.m_path([(x, 19), (x + 1, 20), (x, 21)], 0.5), "#3a3a34", within=m)
        s.paint(s.m_px([(9, 22), (12, 21), (15, 22), (18, 21), (21, 22)]), "#c8c0a8", within=m)
    lizard(s, "#8a8470", "#d8d4c4", throat="#d8d4c4", pattern=pat, wide=True, horns=True)


@sprite("mediterranean_house_gecko")
def _(s):
    def pat(s, m):
        s.paint(s.m_px([(10, 20), (13, 21), (16, 19), (19, 21), (12, 23), (18, 23)]), "#c88a80", within=m)
    lizard(s, "#ecd0c4", "#f8ece4", throat="#f8ece4", pattern=pat, smooth=True, eye_big=True,
           legs="#e0c0b4", tail_col="#e4c4b8")
    s.px([(7, 28), (8, 28), (16, 29), (17, 29)], "#f4dcd0")


@sprite("common_spotted_whiptail")
def _(s):
    def pat(s, m):
        for y in (19, 21, 23):
            s.paint(s.m_line(9, y, 22, y), "#f0e6c4", within=m)
        s.paint(s.m_px([(10, 20), (14, 22), (18, 20), (21, 22)]), "#f8f0d8", within=m)
    lizard(s, "#5a4a36", "#e8eef4", throat="#e8eef4", pattern=pat, tail_col="#8a6a4a",
           tail_pts=[(20, 22), (27, 25), (33, 24), (36, 19)])


@sprite("brown_anole")
def _(s):
    def pat(s, m):
        for x in (11, 15, 19):
            s.paint(s.m_poly([(x, 19), (x + 1.5, 20.5), (x, 22), (x - 1.5, 20.5)]), "#d8c098", within=m)
    lizard(s, "#7a5a3a", "#d8c8a8", pattern=pat)
    s.ellipse(8, 23.5, 2.6, 2.2, "#f07a2a", shade=False)
    s.px([(8, 23)], "#f8d040")


@sprite("western_ratsnake")
def _(s):
    snake(s, "#8a8a7a", belly="#d8d4c4", blotch="#3a3a34", band_period=4.5, band_len=2.5, head="#5a5a50")


@sprite("plain_bellied_watersnake")
def _(s):
    snake(s, "#5a4a40", belly="#f0a050", bands="#4e4038", band_period=3.0, band_len=1.0, head="#5a4a40")


@sprite("western_diamond_backed_rattlesnake")
def _(s):
    snake(s, "#a8987a", belly="#e4dcc4", blotch="#5a4a3a", band_period=4.0, band_len=2.4, rattle=True,
          head="#a8987a", head_w=6)
    s.paint(s.m_line(6, 9, 12, 12), "#e4dcc4", within=s.m_ellipse(12.5, 10.5, 6, 4.2))


@sprite("western_ribbon_snake")
def _(s):
    snake(s, "#2b2630", belly="#e8f0d8", stripe="#f0c040", head="#2b2630")
    s.px([(11, 8), (12, 8)], "#f0c040")


@sprite("rough_earthsnake")
def _(s):
    snake(s, "#8a7a68", belly="#d8ccbc", bands="#7a6a5a", band_period=2.5, band_len=0.8, head="#7a6a5a",
          head_w=4.6)


# --------------------------------------------------------------------------- amphibians
@sprite("gulf_coast_toad")
def _(s):
    frog(s, "#8a6a4a", "#e8dcc4", build="toad", side="#f0e4c4", spots=6, parotoid="#7a5a3a")


@sprite("texas_toad")
def _(s):
    frog(s, "#a89a7a", "#f0e8d8", build="toad", spots=7)


@sprite("blanchards_cricket_frog")
def _(s):
    frog(s, "#8a7a5a", "#f0ecd8", mask="#5a8a4a", spots=3, crown="#4a3a2a")


@sprite("southern_leopard_frog")
def _(s):
    frog(s, "#6aa05a", "#f4f0e0", tympanum="#d8c8a0", spots=8, spot_big=True, ridges="#d8e0a0", lip="#f4f0e0")


@sprite("rio_grande_leopard_frog")
def _(s):
    frog(s, "#8a9a6a", "#f0ecd8", spots=6, spot_big=True, ridges="#c8c8a0")


@sprite("squirrel_tree_frog")
def _(s):
    frog(s, "#7ab85a", "#eef0d8", build="tree", pads=True, spots=2)


# --------------------------------------------------------------------------- fish
@sprite("bluegill")
def _(s):
    def pat(s, m):
        for x in (12, 16, 20):
            s.paint(s.m_line(x, 11, x - 1, 20), "#4a5a6a", within=m)
        s.paint(s.m_ellipse(10, 15, 1.6, 1.4), "#1e2a3a", within=m)
    fish(s, "#6a8aa0", "#f0b050", pattern=pat)


@sprite("largemouth_bass")
def _(s):
    def pat(s, m):
        s.paint(s.m_path([(8, 16), (14, 17), (19, 16), (24, 17)], 1.0), "#2a4a2a", within=m)
        s.paint(s.m_poly([(3, 17), (8, 18), (8, 19), (3, 19)]), "#e8e4cc", within=m)
    fish(s, "#5a8a4a", "#e8ecd0", fin="#4a7a3a", pattern=pat, slim=True)


@sprite("western_mosquitofish")
def _(s):
    def pat(s, m):
        s.paint(s.m_px([(14, 14), (18, 13), (20, 16), (16, 17)]), "#5a5a5a", within=m)
    fish(s, "#a8a89a", "#e8e8dc", fin="#9a9a8a", pattern=pat, slim=True)


@sprite("plains_longear_sunfish")
def _(s):
    def pat(s, m):
        s.paint(s.m_path([(4, 15), (8, 18), (11, 15)], 0.6), "#5ac8e8", within=m)
        s.paint(s.m_px([(14, 12), (17, 14), (20, 12), (15, 16), (19, 17), (22, 15)]), "#5ac8e8", within=m)
        s.paint(s.m_ellipse(10.5, 13.5, 1.8, 1.2), "#1e2a3a", within=m)
    fish(s, "#e8782a", "#f0a040", fin="#c8602a", pattern=pat)


@sprite("green_sunfish")
def _(s):
    def pat(s, m):
        s.paint(s.m_path([(3, 15), (8, 17)], 0.5), "#5ab8d8", within=m)
        s.paint(s.m_ellipse(10, 14, 1.6, 1.4), "#1e2a3a", within=m)
        s.paint(s.m_px([(15, 13), (18, 15), (21, 13)]), "#7ab8a0", within=m)
    fish(s, "#5a8a6a", "#e8c860", fin="#4a7a5a", pattern=pat)


@sprite("texas_cichlid")
def _(s):
    def pat(s, m):
        s.paint(s.m_px([(9, 13), (12, 15), (15, 12), (18, 14), (21, 13), (13, 18), (17, 17), (20, 18),
                        (10, 17), (23, 16)]), "#bfe8f4", within=m)
        s.paint(s.m_ellipse(20, 17, 1.4, 1.4), "#1e2a3a", within=m)
    fish(s, "#5a7a8a", "#8aa0a8", fin="#4a6a7a", pattern=pat)


# --------------------------------------------------------------------------- insects and other small animals
@sprite("queen")
def _(s):
    def pat(s, fm, hm):
        w = fm | hm
        s.paint(s.m_poly([(1.5, 6), (5, 3), (7, 5), (3, 9)]) | s.m_line(4, 21, 9, 26), "#3a2418", mirror=True, within=w)
        s.paint(s.m_px([(5, 8), (7, 9), (6, 11), (9, 10), (4, 12)]), WHITE, mirror=True, within=fm)
        s.paint(s.m_line(9, 18, 12, 21), "#3a2418", mirror=True, within=hm)
    butterfly(s, "#b0581e", "#c8682a", pattern=pat)


@sprite("common_buckeye")
def _(s):
    def pat(s, fm, hm):
        s.paint(s.m_line(5, 9, 10, 12) | s.m_line(5, 10, 10, 13), "#f0e8d8", mirror=True, within=fm)
        s.paint(s.m_ellipse(5.5, 12.5, 1.8, 1.8), "#3a6ad8", mirror=True, within=fm)
        for x, y in ((7, 21), (10, 24)):
            s.paint(s.m_ellipse(x, y, 2, 2), "#f0a040", mirror=True, within=hm)
            s.paint(s.m_ellipse(x, y, 1, 1), "#2a3a8a", mirror=True, within=hm)
        s.paint(s.m_line(10, 4, 13, 9), "#e8782a", mirror=True, within=fm)
    butterfly(s, "#7a5a3a", "#7a5a3a", pattern=pat)


@sprite("gray_hairstreak")
def _(s):
    def pat(s, fm, hm):
        s.paint(s.m_line(4, 12, 12, 14) | s.m_line(5, 21, 12, 20), "#ffffff", mirror=True, within=fm | hm)
        s.paint(s.m_ellipse(9, 24, 1.6, 1.4), "#f07a2a", mirror=True, within=hm)
        s.px([(9, 24)], BLACK, mirror=True)
    butterfly(s, "#9aa0a8", "#a4aab2", pattern=pat, tails=True)


@sprite("salt_marsh_moth")
def _(s):
    def pat(s, fm, hm):
        s.paint(s.m_px([(5, 6), (8, 8), (4, 10), (10, 11), (7, 13), (12, 14), (6, 4)]), BLACK, mirror=True, within=fm)
        s.paint(s.m_ellipse(10, 21, 4, 4), "#f0b050", mirror=True, within=hm)
    butterfly(s, "#f8f6f0", "#f8f4ec", body="#f0a03a", pattern=pat)
    s.px([(16, 14), (16, 17), (16, 20), (15, 23)], BLACK)


@sprite("eastern_pondhawk")
def _(s):
    dragonfly(s, "#4aa04a", "#7ab8e0")
    s.paint(s.m_ellipse(16, 5.5, 4, 3), "#5ac05a", within=s.m_ellipse(16, 5.5, 4, 3)
            & ~s.m_ellipse(13.8, 5, 1.9, 2.1) & ~s.m_ellipse(18.2, 5, 1.9, 2.1))


@sprite("asian_lady_beetle")
def _(s):
    beetle_top(s, "#e8781e", spots=[(11, 16), (21, 16), (12, 22), (20, 22), (16, 26)], pron="#f4ecd8")
    s.px([(15, 11), (16, 11), (14, 12), (17, 12), (15, 12), (16, 12)], BLACK)


@sprite("american_bumble_bee")
def _(s):
    s.can("fly")
    up = not (s.act == "fly" and s.f % 2)
    s.ellipse(20, 8 if up else 11, 4.5, 6.5 if up else 4, "#e6f4fc", rot=25 if up else 70, shade=False, edge=True)
    s.ellipse(25, 11 if up else 13, 3.5, 5 if up else 3, "#d6ecfa", rot=40 if up else 80, shade=False, edge=True)
    m = s.ellipse(18, 19, 9, 7.5, "#f2c22a")
    s.paint(s.m_poly([(22, 8), (30, 8), (30, 30), (24, 30)]), "#2b2226", within=m)
    s.paint(s.m_poly([(12, 8), (15, 8), (15, 30), (12, 30)]), "#2b2226", within=m)
    s.paint(s.m_px([(19, 14), (21, 18), (18, 22), (20, 24), (16, 17)]), "#f8dc5a", within=m)
    s.line(9, 25, 8, 29, "#2b2226")
    s.line(13, 25, 13, 29, "#2b2226")
    s.ellipse(8.5, 17, 5.5, 5.5, "#2b2226", edge=True)
    s.paint(s.m_ellipse(9, 13, 4, 2), "#f2c22a", within=s.last)
    s.line(6, 12, 4, 6, "#2b2226")
    s.line(9, 12, 10, 6, "#2b2226")
    s.eye(5, 16, color="#11080f", shine="#ffffff")


@sprite("red_swamp_crayfish")
def _(s):
    s.can("walk")
    w = s.wave() if s.act == "walk" else 0
    red, dark = "#c8302a", "#8a1e1a"
    for i, y in enumerate((17, 20, 23)):
        d = w * 1.2 * (1 if i % 2 else -1)
        s.path([(13, y), (8, y + 2 + d), (6, y + 5 + d)], 0.6, dark, shade=False)
    # tail fan and segmented tail, curving away to the right
    s.poly([(29, 20), (33, 16), (34, 21), (33, 26)], red)
    m = s.path([(14, 20), (20, 20), (26, 20), (30, 21)], (4, 2.6), red)
    for x in (19, 22, 25, 28):
        s.paint(s.m_line(x, 16, x, 25), dark, within=m)
    # big claws up front
    s.path([(10, 18), (7, 13)], 1.1, red)
    s.ellipse(5.5, 9, 3.4, 2.4, red, rot=-60, edge=True)
    s.paint(s.m_px([(4, 6), (5, 6), (5, 7)]), dark)
    s.path([(10, 22), (6, 25)], 1.1, red)
    s.ellipse(4, 27, 3.2, 2.2, red, rot=30, edge=True)
    s.ellipse(12, 20, 5.5, 4.5, red, edge=True)
    s.paint(s.m_px([(12, 18), (14, 19), (11, 22)]), "#e8604a", within=s.last)
    s.line(9, 17, 4, 13, dark)
    s.line(8, 18, 2, 16, dark)
    s.eye(9, 18)


@sprite("common_pill_woodlouse")
def _(s):
    s.can("walk")
    w = s.wave() if s.act == "walk" else 0
    g = "#7a7a84"
    for i, x in enumerate((9, 13, 17, 21)):
        d = round(w * (1 if i % 2 else -1))
        s.line(x, 26, x - 1 + d, 29, "#3a3a44")
    m = s.ellipse(16, 21, 11, 7, g, edge=True)
    for x in (10, 13, 16, 19, 22, 25):
        s.paint(s.m_line(x, 13, x, 29), mix(g, "#000000", 0.3), within=m)
    s.paint(s.m_px([(12, 17), (18, 16), (24, 18)]), "#b0b0b8", within=m)
    s.ellipse(6.5, 22, 3.5, 4, "#5a5a64", edge=True)
    s.line(4, 19, 1, 15, "#3a3a44")
    s.eye(5, 21)


def _segmented(s, n, body, head, legs, *, leg_len=3, spacing=3.2, r=2.6, antenna=4, tail=None):
    """A long many-legged animal winding across the frame (centipedes, millipedes)."""
    s.can("walk")
    w = s.wave() if s.act == "walk" else 0
    import math
    pts = [(6 + i * spacing, 20 + 2.5 * math.sin(i * 0.9 + w)) for i in range(n)]
    for i, (x, y) in enumerate(pts):
        d = (1 if i % 2 else -1) * w
        s.line(x, y + r - 0.5, x - 1 + d, y + r + leg_len, legs)
        s.line(x, y - r + 0.5, x - 1 - d, y - r - leg_len, legs)
    if tail:
        x, y = pts[-1]
        s.line(x, y, x + 4, y - 3, tail)
        s.line(x, y, x + 4, y + 3, tail)
    for i, (x, y) in enumerate(reversed(pts)):
        c = body if i % 2 else mix(body, "#000000", 0.15)
        s.ellipse(x, y, r, r, c)
    hx, hy = pts[0]
    s.ellipse(hx - 1, hy, r + 0.8, r + 0.4, head, edge=True)
    s.line(hx - 2, hy - 2, hx - 2 - antenna, hy - 2 - antenna, legs)
    s.line(hx - 3, hy - 1, hx - 4 - antenna, hy - 1, legs)
    s.eye(round(hx - 2), round(hy - 1))
    return pts


@sprite("giant_desert_centipede")
def _(s):
    _segmented(s, 8, "#e88a2a", "#a8202a", "#f0c040", leg_len=3.5, tail="#a8202a")


@sprite("greenhouse_millipede")
def _(s):
    _segmented(s, 9, "#8a5a3a", "#6a4430", "#d8b090", leg_len=1.8, spacing=2.8, r=2.2, antenna=2.5)
