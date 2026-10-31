"""Sprites for the Oregon, Washington, South Dakota, Kansas, Iowa and Minnesota species
that aren't on an earlier state's list."""
from __future__ import annotations

from archetypes import (BLACK, EYE, WHITE, _fluke, back_stripes, beetle_top, bird, butterfly, crab, critter, duck,
                        face_stripes, fish, flecks, frog, grasshopper, lizard, owl, quad, snail_shell, snake,
                        spider_top, sprite, turtle, wader)
from pixel import mix
from species_tx import _segmented
from species_va import _woodlouse


# --------------------------------------------------------------------------- mammals
def _chipmunk(s, fur, dark, light, tail_col, *, head=None):
    """Chipmunk with stripes on the face and down the back."""
    critter(s, fur, light, build="ground", ear_in="#e0b090", tail="long", tail_col=tail_col, head=head,
            markings=lambda s, g: back_stripes(s, g, [dark, light, dark, light, dark], top=0.2),
            face=lambda s, g: face_stripes(s, g, dark, light))


@sprite("townsends_chipmunk")
def _(s):
    # A big, dark rainforest chipmunk with blurry stripes.
    _chipmunk(s, "#7a5234", "#3a261a", "#c8b090", "#5a3c26")


@sprite("yellow_pine_chipmunk")
def _(s):
    # Bright tawny orange with crisp black and white stripes.
    _chipmunk(s, "#d0803a", "#2b2226", "#f6f0e4", "#b86a30")


@sprite("least_chipmunk")
def _(s):
    # The smallest: pale and grayish, with stripes right down to the nose.
    _chipmunk(s, "#b8946a", "#4a3a2e", "#f2ece0", "#a8885e", head="#a8a090")


@sprite("douglass_squirrel")
def _(s):
    # Dark olive-brown back, rusty-orange belly, white eye rings and tufted ears.
    critter(s, "#5e4a34", "#e0904a", build="squirrel", ears="tuft", ear_in="#a87050", tail="squirrel",
            tail_col="#4e3c2a", tail_tip="#c88a4a", muzzle="#e8a868", eye_ring=WHITE,
            markings=lambda s, g: back_stripes(s, g, ["#2b2226"], top=g["bry"] * 1.0))  # black side line


@sprite("douglass_ground_squirrel")
def _(s):
    # Speckled gray-brown with a dark wedge between the shoulders.
    def wedge(s, g):
        s.paint(s.m_ellipse(g["bx"] - g["brx"] * 0.45, g["by"] - g["bry"] * 0.6, 2.6, 1.6), "#3a2e26", within=g["body"])
        flecks(s, g["body"], "#e8e0d2", every=6)
    critter(s, "#8a7a68", "#e8e0d2", build="ground", ear_in="#c8a080", tail="bushy", tail_col="#7a6c5c",
            tail_tip="#d8d0c4", markings=wedge)


@sprite("cascade_golden_mantled_ground_squirrel")
def _(s):
    # A coppery head (the "mantle") and a white side stripe edged in black; no face stripes.
    critter(s, "#9a8a74", "#ece4d4", build="ground", ear_in="#d8a070", tail="long", tail_col="#8a7a64",
            head="#c8783a", eye_ring="#f4e8d0",
            markings=lambda s, g: back_stripes(s, g, ["#2b2226", WHITE, "#2b2226"], top=1.0))


@sprite("beldings_ground_squirrel")
def _(s):
    # Plain gray-buff with a reddish-brown band down its back; a short tail.
    critter(s, "#b0a088", "#ece2d0", build="ground", ear_in="#c89a80", tail="short", tail_col="#a07050",
            tail_tip="#c88a5a", markings=lambda s, g: back_stripes(s, g, ["#a0704a", "#a0704a"], top=0.1))


@sprite("franklins_ground_squirrel")
def _(s):
    # Gray head and a bushy gray tail on a brown, speckled body.
    def specks(s, g):
        flecks(s, g["body"], "#3a2e24", every=5)
        flecks(s, g["body"], "#e0d6c4", every=7, seed=3)
    critter(s, "#8a7458", "#e0d6c4", build="ground", ear_in="#c0a088", tail="bushy", tail_col="#8a8884",
            tail_tip="#b0aeaa", head="#8e8c88", markings=specks)


@sprite("bushy_tailed_woodrat")
def _(s):
    # The packrat: big round ears, big eyes and a fluffy squirrel-like tail.
    critter(s, "#9a8670", WHITE, build="mouse", ears="big", ear_in="#e8b0b0", tail="bushy", tail_col="#8a7660",
            nose="#d88a96", eye_size=3)


@sprite("american_badger")
def _(s):
    # Grizzled gray, low and wide, with a white stripe up its nose and black cheek badges.
    def face(s, g):
        h = g["head_m"]
        if g["view"] == "front":
            s.paint(s.m_ellipse(g["hx"] + 0.6, g["hy"] - 0.5, 1.0, g["hry"] + 1), WHITE, within=h)
            return
        d = 1 if g["view"] == "back" else -1
        s.paint(s.m_ellipse(g["hx"] - d * 1.5, g["hy"] + 1.2, 1.6, 1.4), "#2b2226", within=h)
        s.paint(s.m_path([(g["hx"] - d * 1, g["hy"] - g["hry"] + 0.3), (g["hx"] + d * 4, g["hy"] - 0.8)], 0.7), WHITE, within=h)
    def back(s, g):
        flecks(s, g["body"], "#c8c0b0", every=5)
        back_stripes(s, g, [WHITE], top=0.1, width=0.8)
    critter(s, "#8a8278", "#e8e0d0", build="badger", ear_in="#4a3e36", tail="short", tail_col="#a89a80",
            feet="#2b2226", face=face, markings=back)


@sprite("american_bison")
def _(s):
    # Huge shaggy shoulder hump, a bearded dark head and short curved horns.
    shag = "#7a5636"

    def hump(s, b):
        bx, by, brx, bry = b["body"]
        s.ellipse(bx - 4.5, by - bry + 0.5, 6, 4.5, shag)

    def coat(s, b):
        bx, by, brx, bry = b["body"]
        s.paint(s.m_ellipse(bx - 5, by - 1, 6, 7), shag, within=s.m_ellipse(bx, by, brx, bry)
                | s.m_ellipse(bx - 3.5, by - bry + 1.5, 4.5, 2.6))

    def horns(s, b):
        hx, hy, hrx, hry = b["head"]
        s.path([(hx + 1.5, hy - 3), (hx + 1, hy - 6), (hx - 1, hy - 6.8)], (0.8, 0.5), "#a89c8a", shade=False)
        s.path([(hx - 1.5, hy + 3), (hx - 1, hy + 6.5)], (1.4, 0.8), "#2a1e16")
    quad(s, "#4a3424", "#5a4030", build="bear", ears="small", ear_in="#3a2a1e", tail="short", tail_col="#2a1e16",
         tail_tip="#1e1610", head="#4e3624", muzzle="#3a2a1e", nose="#1a1410", feet="#2a2020", belly=False,
         behind=hump, markings=coat, front=horns)


# --------------------------------------------------------------------------- birds
@sprite("golden_crowned_sparrow")
def _(s):
    def face(s):
        h = s.last
        s.paint(s.m_ellipse(12, 7.5, 5.5, 2.8), BLACK, within=h)
        s.paint(s.m_ellipse(11, 6.5, 3.4, 1.4), "#f2c830", within=h)  # the golden crown

    def wing(s, m):
        s.paint(s.m_line(16, 18, 23, 16) | s.m_px([(18, 20), (21, 19)]), "#4a3220", within=m)
        s.paint(s.m_line(16, 20, 22, 19), "#f0e8dc", within=m)
    bird(s, "#8a6a4a", "#c8c4bc", head="#8e8e90", wing="#8a6448", tail_col="#6a5240", beak="cone",
         beak_col="#a09080", legs="#d0a888", tail="mid", face=face, wing_mark=wing)


@sprite("bushtit")
def _(s):
    # A tiny plain gray-brown puffball with a brown face, a stubby bill and a long tail.
    def face(s):
        s.paint(s.m_ellipse(11, 11, 5, 3.4), "#a08a6a", within=s.last)
    bird(s, "#8e8e86", "#d4d0c4", head="#8e8e86", wing="#7e7e76", tail_col="#6e6e66", beak="thin",
         beak_col="#2b2630", legs="#3a3a40", tail="long", face=face)
    s.eye(8, 10, color="#f0e8a0")  # females have pale eyes
    s.px([(9, 11)], EYE)


@sprite("chestnut_backed_chickadee")
def _(s):
    def face(s):
        h = s.last
        s.paint(s.m_ellipse(11, 7, 6.5, 3.2), "#3a2a24", within=h)
        s.paint(s.m_ellipse(6, 15, 3, 2), BLACK, within=h)

    def flanks(s, m):
        s.paint(s.m_ellipse(17, 24, 4, 2.6), "#a8502a", within=m)
    bird(s, "#a04a26", "#f0eae0", head=WHITE, wing="#70747c", tail_col="#5a5e66", beak="thin",
         beak_col="#1a1820", legs="#3a3a44", tail="mid", face=face, belly_mark=flanks)


@sprite("cliff_swallow")
def _(s):
    # Square tail, a pale forehead, chestnut cheeks and a buff rump.
    def face(s):
        h = s.last
        s.paint(s.m_ellipse(9, 14, 4.5, 2.6), "#9a3e22", within=h)
        s.paint(s.m_ellipse(7, 7.5, 2.4, 1.6), "#f0e4c4", within=h)
        s.paint(s.m_ellipse(10, 16.5, 2.5, 1), "#2a2a3a", within=h)

    def rump(s, m):
        s.ellipse(22, 23.5, 2.4, 1.6, "#e0b880")
    bird(s, "#2a3a5c", "#ece0cc", head="#2a3a5c", wing="#22304a", tail_col="#22304a", beak="thin",
         beak_col="#1a1820", legs="#3a3034", tail="short", face=face, belly_mark=rump)


@sprite("barn_swallow")
def _(s):
    # Steel-blue back, rusty throat, and a deeply forked tail with long streamers.
    def face(s):
        s.paint(s.m_ellipse(8.5, 14.5, 4, 2.4) | s.m_px([(5, 10), (5, 11)]), "#b04a26", within=s.last)
    s.path([(22, 19), (28, 16), (35, 14)], (1.3, 0.4), "#1e3466")
    s.path([(22, 21), (28, 22), (35, 25)], (1.3, 0.4), "#1e3466")
    bird(s, "#2a4a8a", "#ecc090", head="#2a4a8a", wing="#22407a", tail_col="#1e3466", beak="thin",
         beak_col="#1a1820", legs="#3a3034", tail="short", face=face)
    s.px([(28, 17), (28, 21)], WHITE)


@sprite("harriss_sparrow")
def _(s):
    # A big sparrow with a black crown, face and bib, buff cheeks and a pink bill.
    def face(s):
        h = s.last
        s.paint(s.m_ellipse(11, 6.5, 6, 3), BLACK, within=h)
        s.paint(s.m_ellipse(13, 11, 3, 2.2), "#c89a6a", within=h)
        s.paint(s.m_ellipse(6.5, 14, 3.4, 2.6), BLACK, within=h)

    def bib(s, m):
        s.paint(s.m_ellipse(9, 17, 3, 2.2), BLACK, within=m)
        s.paint(s.m_px([(16, 21), (18, 22), (17, 24)]), "#5a3a26", within=m)

    def wing(s, m):
        s.paint(s.m_line(16, 18, 23, 16) | s.m_px([(18, 20), (21, 19)]), "#4a3220", within=m)
        s.paint(s.m_line(16, 20, 22, 19), WHITE, within=m)
    bird(s, "#8a6448", WHITE, head="#a89c94", wing="#946a48", tail_col="#6a4c38", beak="cone",
         beak_col="#f09a9a", legs="#d0a888", tail="mid", face=face, belly_mark=bib, wing_mark=wing, big=True)


@sprite("dickcissel")
def _(s):
    # A mini meadowlark: yellow breast with a black V, yellow eyebrow and a chestnut shoulder.
    def face(s):
        h = s.last
        s.paint(s.m_line(6, 8, 14, 9), "#f2d040", within=h)
        s.paint(s.m_ellipse(7, 15, 2.6, 1.5), WHITE, within=h)

    def bib(s, m):
        s.paint(s.m_ellipse(12, 21, 5, 3.5), "#f2d040", within=m)
        s.paint(s.m_poly([(8, 16), (12, 16), (11, 20), (10, 20)]), BLACK, within=m)

    def wing(s, m):
        s.paint(s.m_ellipse(16, 17, 2.4, 1.6), "#a8502a", within=m)
        s.paint(s.m_line(18, 19, 24, 17), "#4a3220", within=m)
    bird(s, "#8a7458", "#ece6da", head="#8a9098", wing="#9a7a58", tail_col="#6a5440", beak="cone",
         beak_col="#7a8090", legs="#c8a888", tail="mid", face=face, belly_mark=bib, wing_mark=wing)


@sprite("northern_house_wren")
def _(s):
    # Plain brown with fine dark barring on the wings and its cocked-up tail.
    def wing(s, m):
        for x in (17, 19, 21, 23):
            s.paint(s.m_line(x, 16, x + 1, 22), "#4a3424", within=m)

    def face(s):
        s.paint(s.m_line(7, 8, 14, 9), "#c8b498", within=s.last)
    bird(s, "#8a6a4c", "#cdb89c", head="#866448", wing="#7a5a40", tail_col="#7a5a40", beak="thin",
         beak_col="#4a3a34", legs="#d8b090", tail="fan", face=face, wing_mark=wing)
    s.paint(s.m_line(23, 16, 27, 12) | s.m_line(24, 18, 29, 14) | s.m_line(25, 19, 30, 16), "#4a3424",
            within=s.m_poly([(20, 19), (29, 10), (31, 18), (23, 23)]))


@sprite("burrowing_owl")
def _(s):
    # A long-legged little ground owl: brown with white spots, white brows and a white chin.
    def front(s):
        s.paint(s.m_line(8, 6, 14, 6) | s.m_line(9, 5, 13, 5), "#f4ecdc", mirror=True,
                within=s.m_ellipse(16, 10, 10, 8))
        s.paint(s.m_ellipse(16, 16.5, 4.5, 1.2), "#f4ecdc")
        s.paint(s.m_px([(9, 4), (16, 3), (23, 4), (7, 17), (25, 17), (6, 22), (26, 22), (8, 26), (24, 26), (5, 19),
                        (27, 19)]), "#f4ecdc")
        s.shift(0, -3)
        for x in (13, 19):
            s.line(x, 26, x, 30, "#c8b890")
            s.px([(x - 1, 30), (x + 1, 30)], "#c8b890")
    owl(s, "#8a6a48", "#b8966c", eye_col="#f6d030", belly="#ecdcc0", bars="#a08058", spots="#f4ecdc",
        throat="#f4ecdc", brows="#f4ecdc", long_legs=True, front=front)


@sprite("upland_sandpiper")
def _(s):
    # A grassland shorebird: small head on a thin neck, big dark eye, short bill, yellow legs.
    wader(s, "#a88a64", neck="#c4a882", head="#b89a74", beak="#d8b860", legs="#e0c850", wing="#8a6a48")
    s.erase(s.m_poly([(-5, 0), (3, 0), (3, 12), (-5, 12)]))
    s.px([(3, 6)], "#3a3034")
    s.paint(s.m_px([(14, 9), (13, 11), (15, 12), (14, 13), (17, 13), (19, 12), (21, 11)]), "#5a4430")
    s.paint(s.m_px([(17, 18), (20, 18), (23, 17), (25, 15), (22, 14), (19, 15)]), "#3a2a1e")
    s.eye(8, 4)


@sprite("gadwall")
def _(s):
    # A quiet gray-brown duck with a black rear end and a white wing patch.
    duck(s, "#8a847c", "#6e665e", "#9a8a76", bill="#3a3434", ring=None, speculum=WHITE, tail_col=BLACK)
    s.paint(s.m_ellipse(26, 22.5, 3.6, 4), BLACK, within=s.m_ellipse(17, 23, 11, 6.5))
    s.paint(s.m_px([(8, 21), (11, 20), (9, 24), (12, 23), (7, 23)]), "#4a443e")


@sprite("blue_winged_teal")
def _(s):
    # Slate-blue head with a white crescent, speckled brown body, white flank spot.
    duck(s, "#8a6a4a", "#9a7a58", "#5a6a8a", bill="#2b2630", ring=None, speculum="#3a8a5a", tail_col="#2b2630")
    s.paint(s.m_poly([(16, 19), (21, 18), (21, 20), (16, 21)]), "#8ab8e0")  # the blue shoulder
    s.paint(s.m_path([(6, 7), (5.5, 10), (6, 14)], 0.6), WHITE)
    s.paint(s.m_ellipse(25.5, 25, 1.6, 1.8), WHITE)
    s.paint(s.m_px([(9, 21), (12, 22), (10, 24), (14, 25), (17, 26), (20, 26), (8, 23), (13, 19)]), "#4a3424")
    s.eye(7, 10)


@sprite("hooded_merganser")
def _(s):
    # The male: a big black-edged white fan crest, golden eye, chestnut sides.
    duck(s, "#a8582a", WHITE, BLACK, bill=BLACK, ring=None, speculum=WHITE, tail_col=BLACK)
    s.paint(s.m_poly([(18, 17), (28, 18), (28, 21), (18, 21)]), "#2a2a30")
    s.paint(s.m_line(13, 18, 14, 26) | s.m_line(14, 18, 15, 26), BLACK, within=s.m_ellipse(17, 23, 11, 6.5))
    s.ellipse(13, 8, 6.5, 5.5, BLACK, edge=True)
    s.paint(s.m_ellipse(14.5, 8, 3.8, 2.8), WHITE)
    s.eye(7, 10, color="#f0d040")
    s.px([(8, 11)], EYE)


# --------------------------------------------------------------------------- reptiles
@sprite("northwestern_garter_snake")
def _(s):
    snake(s, "#2a2a30", belly="#a8b0b8", stripe="#e8662a", head="#2a2a30")
    s.px([(11, 13), (12, 13)], "#e8e0c8")


@sprite("western_foxsnake")
def _(s):
    snake(s, "#d8bc80", belly="#f0e4b0", blotch="#4e3420", bands="#c8a46a", band_period=4.4, band_len=2.4,
          head="#b8844a")


@sprite("pygmy_short_horned_lizard")
def _(s):
    # A round little pancake of a lizard with tiny horns and dark blotches.
    def pat(s, m):
        s.paint(s.m_ellipse(11, 20, 1.6, 1.2) | s.m_ellipse(15.5, 19.5, 1.6, 1.2) | s.m_ellipse(20, 20, 1.6, 1.2),
                "#4a3e34", within=m)
        s.paint(s.m_px([(9, 18), (13, 18), (18, 18), (21, 19), (12, 22), (17, 22)]), "#d8ccb4", within=m)
    lizard(s, "#9a8a74", "#e0d6c4", pattern=pat, wide=True, horns=True, tail_pts=[(21, 23), (25, 25), (27, 25)])
    s.px([(8, 25), (10, 26), (19, 26), (21, 25)], "#d8ccb4")  # the fringe of side scales


@sprite("great_plains_skink")
def _(s):
    # Tan with every scale edged in black, making a checkerboard.
    def pat(s, m):
        s.paint(s.m_px([(x, y) for y in (19, 21, 23) for x in range(9 + (y // 2) % 2, 23, 2)]), "#3a2e22",
                within=m)
    lizard(s, "#b8a070", "#e8dcc0", pattern=pat, smooth=True, tail_col="#a89060")
    s.paint(s.m_px([(5, 15), (7, 15), (9, 16), (6, 19), (8, 20)]), "#3a2e22")


@sprite("prairie_skink")
def _(s):
    # Brown with pale stripes edged in dark; breeding males get an orange-red chin.
    def pat(s, m):
        s.paint(s.m_line(8, 19, 22, 19) | s.m_line(8, 22, 22, 22), "#e8d8a8", within=m)
        s.paint(s.m_line(8, 20, 22, 20) | s.m_line(8, 21, 22, 21), "#3a2a20", within=m)
    lizard(s, "#7a5a3a", "#d8ccae", throat="#e8602a", pattern=pat, smooth=True, tail_col="#6a4a30")
    s.paint(s.m_line(3, 17, 12, 17), "#e8d8a8")


@sprite("ornate_box_turtle")
def _(s):
    # A high dark shell with bright yellow lines raying out of each plate.
    turtle(s, "#3e2c1c", "#7a6a4a", dome=True, speckle="#f0c040", rim="#2e2014")
    shell = s.m_ellipse(17, 25, 11, 10)
    for cx, cy in ((11, 20), (17, 17), (23, 20)):
        for dx, dy in ((-3, -3), (0, -4), (3, -3), (-3, 2), (3, 2)):
            s.paint(s.m_line(cx, cy, cx + dx, cy + dy), "#f0c84a", within=shell)
    s.px([(9, 27), (11, 26), (22, 27), (23, 26)], "#f0c040")


# --------------------------------------------------------------------------- amphibians
@sprite("western_red_backed_salamander")
def _(s):
    def stripe(s, m):
        s.paint(s.m_line(8, 19, 22, 19) | s.m_line(8, 20, 22, 20), "#d8823a", within=m)
        s.paint(s.m_px([(10, 23), (14, 24), (18, 23), (21, 22)]), "#e8e8ec", within=m)
    lizard(s, "#2e2a30", "#7a7a80", head="#2e2a30", throat="#7a7a80", pattern=stripe, smooth=True,
           eye_big=True, legs="#2a262c", tail_col="#d8823a")
    s.paint(s.m_line(5, 15, 11, 15), "#d8823a")


@sprite("pacific_giant_salamander")
def _(s):
    # Big and chunky, coppery brown marbled with dark blotches.
    def pat(s, m):
        s.paint(s.m_px([(9, 19), (10, 20), (13, 19), (14, 21), (17, 19), (18, 20), (21, 20), (11, 22), (16, 22),
                        (20, 22)]), "#3a2a20", within=m)
    lizard(s, "#9a6e44", "#d8c8a8", pattern=pat, smooth=True, eye_big=True, wide=True, tail_col="#8a603a")
    s.paint(s.m_px([(7, 15), (9, 16), (11, 17), (25, 23), (28, 21)]), "#3a2a20")


@sprite("dunns_salamander")
def _(s):
    # Dark brown with a ragged greenish-tan stripe down its back.
    def pat(s, m):
        s.paint(s.m_path([(8, 19), (11, 18.5), (14, 19.5), (17, 18.5), (20, 19.5), (23, 19)], 0.9), "#a8a858",
                within=m)
    lizard(s, "#3a3028", "#5a5048", smooth=True, eye_big=True, legs="#342a24", pattern=pat, tail_col="#3a3028")
    s.paint(s.m_path([(21, 21), (26, 23.5), (30, 20)], 0.6), "#a8a858")
    s.paint(s.m_line(6, 15, 11, 15), "#a8a858")


@sprite("eastern_tiger_salamander")
def _(s):
    # A big dark salamander covered in bold yellow blotches.
    def pat(s, m):
        s.paint(s.m_ellipse(10, 20, 1.6, 1.4) | s.m_ellipse(15, 21.5, 1.5, 1.3) | s.m_ellipse(19, 19.5, 1.6, 1.4)
                | s.m_ellipse(13, 19, 1, 1) | s.m_ellipse(21, 22, 1, 1), "#e8c83a", within=m)
    lizard(s, "#2a2a24", "#a89a5a", head="#2a2a24", pattern=pat, smooth=True, eye_big=True, wide=True,
           legs="#2e2e28", tail_col="#2a2a24")
    s.paint(s.m_ellipse(8, 16, 1.4, 1.2) | s.m_ellipse(25, 24, 1.2, 1.2) | s.m_ellipse(29, 20, 1, 1.2), "#e8c83a")
    s.eye(5, 16, size=3)
    s.px([(5, 16)], WHITE)


@sprite("plains_leopard_frog")
def _(s):
    # Tan-green with dark spots, a white upper lip and pale back ridges that break near the hips.
    frog(s, "#9a9a5a", "#f4f0e0", tympanum="#7a7a40", spots=8, spot_big=True, ridges="#e8e0a8", lip=WHITE)


@sprite("western_narrow_mouthed_toad")
def _(s):
    # A small plump teardrop with a pointy little head, tiny eyes and a skin fold behind them.
    s.can("walk")
    hop = s.act == "walk" and s.f == 2
    c = "#8a7e6a"
    s.ellipse(22, 28, 4.5, 2, mix(c, "#000000", 0.2), rot=-10)
    m = s.ellipse(18, 23, 10, 7, c, edge=True)
    s.paint(s.m_ellipse(17, 27.5, 8, 2), "#d8d0c0", within=m)
    s.paint(s.m_px([(15, 19), (19, 18), (22, 20), (17, 22), (24, 23)]), "#6e6252", within=m)
    s.poly([(10, 19), (2, 24), (3, 25.5), (11, 27)], c, edge=True)
    s.paint(s.m_path([(11, 18), (10, 23), (11, 27)], 0.5), "#6e6252")  # the fold behind the head
    s.ellipse(9, 28.5, 2.4, 1.4, c)
    s.eye(6, 21)
    if hop:
        s.shift(0, -2)


# --------------------------------------------------------------------------- insects
def _bumble(s, bands, *, head="#2b2226", cap=None):
    """A bumble bee side view; bands are (x0, x1, colour) stripes across the body, front to back."""
    s.can("fly")
    up = not (s.act == "fly" and s.f % 2)
    s.ellipse(20, 8 if up else 11, 4.5, 6.5 if up else 4, "#e6f4fc", rot=25 if up else 70, shade=False, edge=True)
    s.ellipse(25, 11 if up else 13, 3.5, 5 if up else 3, "#d6ecfa", rot=40 if up else 80, shade=False, edge=True)
    m = s.ellipse(18, 19, 9, 7.5, bands[0][2])
    for x0, x1, c in bands:
        s.paint(s.m_poly([(x0, 8), (x1, 8), (x1, 30), (x0, 30)]), c, within=m)
    s.line(9, 25, 8, 29, "#2b2226")
    s.line(13, 25, 13, 29, "#2b2226")
    s.ellipse(8.5, 17, 5.5, 5.5, head, edge=True)
    if cap:
        s.paint(s.m_ellipse(9, 13, 4, 2), cap, within=s.last)
    s.line(6, 12, 4, 6, "#2b2226")
    s.line(9, 12, 10, 6, "#2b2226")
    s.eye(5, 16, color="#11080f", shine="#ffffff")


@sprite("fuzzy_horned_bumble_bee")
def _(s):
    # Shaggy yellow front, a black band between the wings, and an orange tail.
    _bumble(s, [(8, 14, "#f2c83a"), (14, 17.5, "#2b2226"), (17.5, 22, "#f2c83a"), (22, 24, "#2b2226"),
                (24, 30, "#e8782a")], cap="#f2c83a")
    s.paint(s.m_px([(12, 14), (19, 15), (21, 20), (13, 20)]), "#f8e070")


@sprite("black_and_gold_bumble_bee")
def _(s):
    _bumble(s, [(8, 12.5, "#e8b82a"), (12.5, 19, "#2b2226"), (19, 24, "#e8b82a"), (24, 30, "#2b2226")])


@sprite("red_belted_bumble_bee")
def _(s):
    _bumble(s, [(8, 13.5, "#f2c83a"), (13.5, 16.5, "#2b2226"), (16.5, 19.5, "#f2c83a"), (19.5, 24.5, "#c8402a"),
                (24.5, 30, "#2b2226")])


@sprite("northern_paper_wasp")
def _(s):
    # A slim reddish-brown wasp with thin yellow bands and dangling legs.
    s.can("fly")
    up = not (s.act == "fly" and s.f % 2)
    body, band = "#8a3a22", "#f0c83a"
    s.ellipse(18, 8 if up else 12, 3.5, 7 if up else 3.5, "#e0eaf4", rot=20 if up else 75, shade=False, edge=True)
    for x0, x1 in ((10, 9), (12, 13), (14, 16)):
        s.path([(x0, 19), (x1 - 1, 24), (x1, 29)], 0.5, "#c88a3a", shade=False)
    m = s.ellipse(23, 21, 6.5, 4, body, rot=25, edge=True)
    for x in (20, 23, 26):
        s.paint(s.m_line(x + 1, 16, x - 2, 26), band, within=m)
    s.ellipse(16.5, 18, 1.4, 1, body)  # the thin waist
    s.ellipse(12, 17, 3.8, 3, body, edge=True)
    s.paint(s.m_px([(11, 15), (13, 15), (14, 17)]), band, within=s.last)
    s.ellipse(20, 10 if up else 13, 3, 6 if up else 3, "#eef4fa", rot=30 if up else 80, shade=False, edge=True)
    s.ellipse(6.5, 15, 3.4, 3.2, body, edge=True)
    s.paint(s.m_ellipse(5, 17, 2, 1.4), band, within=s.last)
    s.path([(6, 12), (4, 8), (1, 6)], 0.5, "#e0802a", shade=False)
    s.path([(8, 12), (8, 7), (6, 4)], 0.5, "#e0802a", shade=False)
    s.eye(4, 14, color="#11080f", shine="#ffffff")


@sprite("woodland_skipper")
def _(s):
    def pat(s, fm, hm):
        s.paint(s.m_poly([(1.5, 6), (5, 3), (6, 5), (3, 14)]) | s.m_line(9, 8, 12, 12), "#5a3a1e", mirror=True,
                within=fm)
        s.paint(s.m_poly([(4, 20), (5, 23), (9, 27), (6, 19)]), "#5a3a1e", mirror=True, within=hm)
        s.paint(s.m_line(8, 19, 11, 24), "#f0b050", mirror=True, within=hm)
    butterfly(s, "#d8862a", "#c87a2a", body="#7a5a34", pattern=pat)


@sprite("goldenrod_soldier_beetle")
def _(s):
    # Orange-yellow with a big black spot near the end of each wing cover.
    beetle_top(s, "#eaa832", head="#2b2226", pron="#eaa832")
    s.paint(s.m_ellipse(11.5, 24, 2.6, 3.2) | s.m_ellipse(20.5, 24, 2.6, 3.2), BLACK,
            within=s.m_ellipse(16, 20, 10, 10))
    s.paint(s.m_ellipse(16, 11, 2, 1.2), BLACK)


@sprite("north_american_wheel_bug")
def _(s):
    # An assassin bug with a toothed half-wheel crest on its back and a long curved beak.
    import math
    s.can("walk")
    w = s.wave() if s.act == "walk" else 0
    body, leg = "#6a6460", "#8a5a3a"
    far = mix(leg, "#000000", 0.3)
    for x, k, d in ((11, -1, w), (17, 1, -w), (23, 1, w)):
        s.path([(x + 1, 21), (x + 1 + 3 * k, 25), (x + 1 + 4 * k + d, 29)], 0.45, far, shade=False)
    m = s.ellipse(19, 19, 10.5, 3.4, body, edge=True)
    s.paint(s.m_ellipse(22, 17.8, 7.5, 1.8), "#4a4440", within=m)
    s.paint(s.m_line(13, 22, 28, 21), "#c8602a", within=m)  # orange edge of the belly
    cx, cy = 12.5, 16
    s.fill(s.m_ellipse(cx, cy, 4.5, 4.5) & s.m_poly([(0, 0), (32, 0), (32, 16.5), (0, 16.5)]), "#8a847c", edge=True)
    s.px([(round(cx + 5 * math.cos(a)), round(cy - 5 * math.sin(a))) for a in
          (math.radians(d) for d in (20, 55, 90, 125, 160))], "#8a847c")  # the cog teeth
    for x, k, d in ((9, -1, -w), (15, 1, w), (21, 1, -w)):
        s.path([(x, 21), (x + 3 * k, 25), (x + 4 * k + d, 30)], 0.5, leg, shade=False)
    s.path([(9, 18), (3.5, 18)], (1.8, 1.3), body)  # long narrow head
    s.path([(3, 19), (2, 22), (4, 24)], 0.4, "#3a3430", shade=False)  # the beak
    s.path([(4, 16.5), (2, 12), (0, 7)], 0.4, "#3a3430", shade=False)
    s.path([(6, 16.5), (6, 11), (4, 7)], 0.4, "#3a3430", shade=False)
    s.eye(5, 17)


@sprite("western_boxelder_bug")
def _(s):
    # Top view: black with bright red edges and veins on its back.
    s.can("walk")
    w = s.wave() if s.act == "walk" else 0
    red = "#e04a2a"
    for i, y in enumerate((13, 17, 21)):
        d = round(w * (1 if i % 2 else -1))
        s.line(11, y, 6, y + 3 + d, BLACK)
        s.line(20, y, 25, y + 3 - d, BLACK)
    s.line(14, 5, 10, 0, BLACK)
    s.line(17, 5, 21, 0, BLACK)
    m = s.ellipse(16, 20, 6.5, 10, "#2b2630", edge=True)
    s.paint(m & ~s.m_ellipse(16, 20, 5.3, 9), red)
    s.paint(s.m_line(16, 21, 11, 27) | s.m_line(15, 21, 20, 27), red, within=m)
    s.paint(s.m_line(16, 12, 16, 21) | s.m_line(15, 12, 15, 21), "#1a161e", within=m)
    s.poly([(10.5, 13), (21.5, 13), (19, 9), (13, 9)], "#2b2630", edge=True)
    s.paint(s.m_line(11, 12, 13, 9) | s.m_line(20, 12, 19, 9), red)
    s.ellipse(16, 7, 2.6, 2.2, "#2b2630", edge=True)
    s.px([(14, 6), (17, 6)], WHITE)


@sprite("differential_grasshopper")
def _(s):
    # Olive-yellow with black chevrons on its big jumping legs.
    grasshopper(s, "#a8a040", "#6a6a2a")
    s.paint(s.m_px([(21, 17), (22, 16), (23, 15), (24, 14), (25, 13)]), BLACK)
    s.paint(s.m_px([(21, 18), (23, 16), (25, 14)]), "#f0e070")


# --------------------------------------------------------------------------- spiders and other small animals
@sprite("cross_orbweaver")
def _(s):
    # The garden spider: a white cross of dots on its round orange-brown back.
    def pat(s, m):
        s.paint(s.m_px([(16, 17), (16, 19), (16, 21), (16, 23), (14, 19), (18, 19), (13, 19), (19, 19)]), WHITE,
                within=m)
        s.paint(s.m_px([(12, 24), (20, 24), (13, 27), (19, 27)]), "#f0e0c0", within=m)
        s.paint(s.m_ellipse(16, 22, 6, 8) & ~s.m_ellipse(16, 22, 4.6, 7), "#7a4a24", within=m)
    spider_top(s, "#b8783a", "#8a5a34", pattern=pat, ceph="#9a6a3e", leg_bands="#e0c090", web=True)


@sprite("giant_house_spider")
def _(s):
    # Brown and hairy with long legs and a row of pale chevrons on its back.
    def pat(s, m):
        s.paint(s.m_line(16, 15, 16, 21), "#c8a87a", within=m)
        for y in (21, 24, 27):
            s.paint(s.m_line(12, y - 2, 16, y) | s.m_line(20, y - 2, 16, y), "#c8a87a", within=m)
    spider_top(s, "#7a5a3e", "#6a4e36", pattern=pat, ceph="#8a6a48", leg_bands="#a8865e")
    s.paint(s.m_line(16, 10, 16, 15), "#c8a87a")


@sprite("pacific_sideband")
def _(s):
    # A brown land snail with one dark band spiralling round the shell.
    snail_shell(s, "#a07c4a", "#b8925e")
    s.paint(s.m_ellipse(16, 17, 7.6, 7.6) & ~s.m_ellipse(16, 17, 6.6, 6.6), "#4a3018",
            within=s.m_ellipse(16, 17, 10, 10))


@sprite("black_slug")
def _(s):
    c = "#2e2a2e"
    s.ellipse(17, 25, 13, 4.3, c)
    s.path([(12, 24), (8, 21), (5, 19.5)], (3.6, 3.0), c)
    s.ellipse(17, 28, 12.5, 1.4, "#e07a3a")  # orange-fringed foot
    s.paint(s.m_ellipse(11, 22, 5, 3), mix(c, "#ffffff", 0.12))  # the smooth mantle
    for x in range(16, 30, 3):
        s.paint(s.m_line(x, 22, x + 1, 26), "#4a454a", within=s.m_ellipse(17, 25, 13, 4.3))
    s.line(4, 17, 2, 13, c)
    s.line(6, 17, 7, 13, c)
    s.px([(2, 12), (7, 12)], "#5a5458")
    s.px([(4, 19), (5, 19), (4, 20), (5, 20)], EYE)
    s.px([(4, 19)], WHITE)


@sprite("yellow_spotted_millipede")
def _(s):
    # Shiny black with a bright yellow spot on each side of every segment (it smells of almonds).
    pts = _segmented(s, 9, "#1e1a22", "#1e1a22", "#e8b84a", leg_len=1.8, spacing=2.8, r=2.4, antenna=2.5)
    for x, y in pts[1:]:
        s.px([(round(x) - 1, round(y) - 2), (round(x) - 1, round(y) + 1)], "#f2d040")


@sprite("brickwork_woodlouse")
def _(s):
    # Dark with rows of pale yellow patches like brickwork.
    g = "#5a4a3e"
    m = _woodlouse(s, g, "#d8b860")
    s.paint(s.m_px([(x + (y % 2) * 1, y) for y in (17, 19, 22) for x in (9, 12, 15, 18, 21, 24)]), "#e0c070",
            within=m)
    s.ellipse(6.5, 22, 3.5, 3.5, "#2b2226", edge=True)
    s.line(4, 19, 0, 16, "#3a3028")
    s.eye(5, 21)


# --------------------------------------------------------------------------- freshwater mussels
def _mussel(s, shell, *, rx=13, ry=8, rot=-15, rays=None, ridges=None, bumps=None, wing=False, rings=True,
            chevrons=None):
    """A clam seen from the side: the shell with growth rings, a pale foot peeking out below."""
    s.ellipse(11, 26, 4, 2, "#f0c8a0")
    if wing:
        s.poly([(14, 12), (24, 3), (27, 12)], shell, edge=True)
    m = s.ellipse(16, 18, rx, ry, shell, rot=rot, edge=True)
    if rings:
        for k, c in ((0.75, mix(shell, "#000000", 0.18)), (0.5, mix(shell, "#000000", 0.12))):
            s.paint(s.m_ellipse(16, 18, rx * k, ry * k, rot=rot) & ~s.m_ellipse(16, 18, rx * k - 1, ry * k - 1, rot=rot),
                    c, within=m)
    ux, uy = 13, 18 - ry * 0.75
    if rays:
        for dx in (-10, -2, 6, 14):
            s.paint(s.m_line(ux, uy, ux + dx, 30), mix(shell, rays, 0.7), within=m)
    if ridges:
        for k in (-4, 0, 4):
            s.paint(s.m_path([(4 + k, 18 + k * 0.6), (12 + k, 13 + k * 0.6), (20 + k, 15 + k * 0.6),
                              (28 + k, 13 + k * 0.6)], 0.7), ridges, within=m)
    if bumps:
        s.paint(s.m_px([(x, y) for x, y in ((11, 15), (14, 17), (17, 19), (20, 21), (13, 22), (16, 24),
                                            (18, 13), (21, 15), (24, 18))]), bumps, within=m)
    if chevrons:
        for x in (9, 15, 21):
            s.paint(s.m_path([(x - 2, 14), (x, 17), (x + 2, 14)], 0.6) | s.m_path([(x - 2, 20), (x, 23), (x + 2, 20)],
                                                                                   0.6), chevrons, within=m)
    s.paint(s.m_ellipse(ux, uy + 1, 2.4, 1.6), mix(shell, "#ffffff", 0.35), within=m)  # the worn beak (umbo)
    s.eye(12, 18)
    s.eye(18, 17)


@sprite("three_ridge_mussel")
def _(s):
    _mussel(s, "#3a3024", ridges="#7e6848", rings=False)


@sprite("plain_pocketbook")
def _(s):
    _mussel(s, "#c8a858", rx=11.5, ry=10, rot=-10, rays="#b0a050")


@sprite("fatmucket")
def _(s):
    _mussel(s, "#b8a850", rx=13.5, ry=7, rot=-12, rays="#4a7a3a")


@sprite("giant_floater")
def _(s):
    _mussel(s, "#6a7a3a", rx=14.5, ry=9, rot=-8, rays="#5a6a30")
    s.paint(s.m_ellipse(10, 15, 3, 1.2, rot=-8), "#9aa860")  # its thin, shiny shell


@sprite("fragile_papershell")
def _(s):
    _mussel(s, "#c8c070", rx=13, ry=7.5, rot=-5, rays="#3a6a3a", wing=True)


@sprite("mapleleaf")
def _(s):
    _mussel(s, "#7a5a34", rx=12, ry=10, rot=-5, bumps="#b08a54")


@sprite("deertoe_mussel")
def _(s):
    _mussel(s, "#d0b860", rx=12.5, ry=9, rot=-18, chevrons="#4a7a3a")


# --------------------------------------------------------------------------- sea life
def _anemone(s, cx, base, k, tent, tip, disk):
    """One anemone: a column, a ring of tentacles with coloured tips and an oral disk."""
    s.poly([(cx - 6 * k, base), (cx - 7 * k, base - 10 * k), (cx + 7 * k, base - 10 * k), (cx + 6 * k, base)],
           mix(tent, "#000000", 0.25))
    top = base - 10 * k
    for i in range(7):
        x = cx - 9 * k + i * 3 * k
        p = s.path([(x, top), (x + 0.5 * (-1) ** i, top - 4 * k), (x - 0.5 * (-1) ** i, top - 7 * k)], (1.3, 1.0),
                   tent)
        s.paint(s.m_ellipse(x - 0.5 * (-1) ** i, top - 7 * k, 1.2, 1.4), tip, within=p)
    s.ellipse(cx, top, 9 * k, 2.6 * k, disk, edge=True)
    s.ellipse(cx, top, 2 * k, 1, tip, shade=False)


@sprite("aggregating_anemone")
def _(s):
    # Green anemones with pink-tipped tentacles that clone into big crowded patches.
    s.ellipse(16, 29, 14, 2, "#a8a090")
    _anemone(s, 7, 29, 0.6, "#a8d8a0", "#f08ab0", "#7ab87a")
    _anemone(s, 25, 29, 0.6, "#a8d8a0", "#f08ab0", "#7ab87a")
    _anemone(s, 16, 30, 1.0, "#b8e0a8", "#f07aa8", "#6aa86a")
    s.eye(12, 24)
    s.eye(18, 24)


@sprite("horned_nudibranch")
def _(s):
    # A see-through white sea slug with an orange stripe edged in electric blue and
    # rows of orange-and-white tipped spikes.
    s.can("walk")
    st = (0, 1, 2, 1)[s.f] if s.act == "walk" else 0
    for i in range(7):
        x = 10 + i * 2.8
        top = 14 + (i % 2) * 2
        p = s.path([(x, 22), (x + 0.8, 18), (x + 1.8, top)], (1.0, 0.7), "#c88a50", edge=True)
        s.paint(s.m_ellipse(x + 1.8, top, 0.9, 1), WHITE, within=p)
        s.paint(s.m_ellipse(x + 1.2, top + 2.2, 1, 0.8), "#f07a2a", within=p)
    s.path([(5 - st, 21), (4 - st, 16), (5 - st, 13)], 0.6, "#e8eef4", shade=False)  # the "horns"
    s.path([(8 - st, 21), (8 - st, 16), (9 - st, 13)], 0.6, "#e8eef4", shade=False)
    m = s.ellipse(15 - st / 2, 24.5, 13.5 + st / 2, 4.5, "#e8f0f6", edge=True)
    s.paint(s.m_ellipse(16, 21.5, 11, 1.4), "#f08a2a", within=m)
    s.paint(s.m_ellipse(16, 21.5, 12, 2.2) & ~s.m_ellipse(16, 21.5, 11, 1.4), "#3a8ae8", within=m)
    s.line(3 - st, 27, 0 - st, 29, "#e8eef4")
    s.eye(5 - st, 24)
    s.eye(10 - st, 24)


@sprite("orange_sea_cucumber")
def _(s):
    # A bright orange cucumber with rows of tube feet and a bushy crown of tentacles.
    c = "#e8702a"
    for x, y in ((3, 10), (6, 7), (10, 8), (12, 12), (2, 15)):
        p = s.path([(8, 17), (x, y)], 0.8, "#f09040")
        s.ellipse(x, y, 2.2, 2, "#f0a050")
    m = s.ellipse(18, 22, 12, 6.5, c, rot=8, edge=True)
    for y in (18, 23, 27):
        s.paint(s.m_px([(x, y + (x - 18) // 6) for x in range(9, 29, 2)]), "#f8b070", within=m)
    s.ellipse(8.5, 17.5, 3.6, 3.2, mix(c, "#ffffff", 0.1), edge=True)
    s.eye(14, 20)
    s.eye(20, 21)


@sprite("frilled_dogwinkle")
def _(s):
    # A sea snail whose cream-and-rust shell is covered in frilly ridges.
    s.ellipse(14, 28, 11, 2.2, "#c8a890")
    s.ellipse(8, 25, 5, 3, "#e8d8c0", edge=True)
    s.line(5, 22, 4, 18, "#e8d8c0")
    s.line(8, 22, 9, 18, "#e8d8c0")
    m = s.poly([(9, 27), (7.5, 24.5), (10, 23), (8.5, 19.5), (11, 18), (10, 14.5), (12.5, 13), (13, 9), (17, 3),
                (21, 9), (21.5, 13), (24, 14.5), (23, 18), (25.5, 19.5), (24, 23), (26.5, 24.5), (25, 27)],
               "#ece2cc", edge=True)
    for y in (9, 14, 19, 24):
        s.paint(s.m_line(9, y + 1, 25, y - 1) | s.m_line(9, y + 2, 25, y), "#c87a3a", within=m)
    s.eye(13, 18)
    s.eye(19, 18)


@sprite("dungeness_crab")
def _(s):
    # A broad purple-tan crab with white-tipped claws.
    crab(s, "#b07a64", "#c08c6e", legs="#a06c56")
    s.paint(s.m_ellipse(2.8, 8, 1.6, 1.3), WHITE, mirror=True)
    s.paint(s.m_px([(10, 17), (13, 16), (19, 16), (22, 17)]), "#d8a888")


@sprite("purple_shore_crab")
def _(s):
    def pat(s, m):
        s.paint(s.m_px([(9, 18), (12, 17), (20, 17), (23, 18), (16, 16)]), "#8a5aa8", within=m)
    crab(s, "#5a3a78", "#6a4a8a", legs="#4a2e66", pattern=pat)
    s.paint(s.m_px([(4, 10), (6, 9), (25, 9), (27, 10), (5, 12), (26, 12)]), "#d84a7a")  # spotted claws


@sprite("red_rock_crab")
def _(s):
    # Brick red with black-tipped claws.
    crab(s, "#b83a2a", "#c8402a", legs="#9a2e22")
    s.paint(s.m_ellipse(2.8, 8, 1.8, 1.5), "#1e1a1e", mirror=True)


@sprite("yellow_shore_crab")
def _(s):
    def pat(s, m):
        s.paint(s.m_px([(9, 17), (12, 19), (15, 17), (18, 19), (21, 17), (23, 20), (11, 22), (20, 22)]),
                "#9a9a50", within=m)
    crab(s, "#d8d48a", "#e0dc9a", legs="#b8b46a", pattern=pat)


@sprite("northern_kelp_crab")
def _(s):
    # Shield-shaped, smooth and olive-red, with long legs and a pointed nose.
    s.can("walk")
    w = s.wave() if s.act == "walk" else 0
    c, leg = "#8a5a2a", "#7a4a24"
    for i, y in enumerate((17, 20, 23)):
        d = w * 1.3 * (1 if i % 2 else -1)
        s.path([(10, y), (4, y + 2 + d), (1, y + 7 + d)], 0.7, leg, shade=False, mirror=True)
    s.path([(10, 13), (6, 10)], 1, c, mirror=True)
    s.ellipse(5, 8.5, 2.6, 1.8, c, rot=-30, mirror=True, edge=True)
    s.poly([(14, 11), (15, 5), (16.5, 11)], c, mirror=True)  # the two-horned beak
    m = s.poly([(8, 10), (24, 10), (23, 21), (16, 28), (9, 21)], c, edge=True)
    s.paint(s.m_poly([(10, 11), (22, 11), (21, 15), (11, 15)]), "#a86a34", within=m)
    s.px([(11, 9), (20, 9)], EYE)
    s.eye(12, 16)
    s.eye(18, 16)


def _crayfish(s, body, dark, spots, tip):
    """A crayfish, side view facing left, big claws up front, after red_swamp_crayfish."""
    s.can("walk")
    w = s.wave() if s.act == "walk" else 0
    for i, y in enumerate((17, 20, 23)):
        d = w * 1.2 * (1 if i % 2 else -1)
        s.path([(13, y), (8, y + 2 + d), (6, y + 5 + d)], 0.6, dark, shade=False)
    s.poly([(29, 20), (33, 16), (34, 21), (33, 26)], body)
    m = s.path([(14, 20), (20, 20), (26, 20), (30, 21)], (4, 2.6), body)
    for x in (19, 22, 25, 28):
        s.paint(s.m_line(x, 16, x, 25), dark, within=m)
    s.path([(10, 18), (7, 13)], 1.1, body)
    s.ellipse(5.5, 9, 3.4, 2.4, body, rot=-60, edge=True)
    s.paint(s.m_px([(4, 6), (5, 6), (5, 7)]), tip)
    s.path([(10, 22), (6, 25)], 1.1, body)
    s.ellipse(4, 27, 3.2, 2.2, body, rot=30, edge=True)
    s.paint(s.m_px([(1, 26), (1, 27), (2, 26)]), tip)
    s.ellipse(12, 20, 5.5, 4.5, body, edge=True)
    s.paint(s.m_px([(12, 18), (14, 19), (11, 22), (21, 18), (24, 19), (27, 18)]), spots)
    s.line(9, 17, 4, 13, dark)
    s.line(8, 18, 2, 16, dark)
    s.eye(9, 18)


@sprite("calico_crayfish")
def _(s):
    # Olive-gray with dark speckles, and orange-tipped claws.
    _crayfish(s, "#8a8a6a", "#4a4a36", "#3a3a2a", "#f08a2a")


# --------------------------------------------------------------------------- fish
@sprite("white_sucker")
def _(s):
    # Olive-brown back, white belly and fleshy sucker lips under its nose.
    def pat(s, m):
        s.paint(s.m_px([(x, y) for x in range(11, 24, 3) for y in (12, 15)]), "#6a5a42", within=m)
    fish(s, "#8a7656", "#eeece2", fin="#a08a6a", pattern=pat, slim=True)
    s.ellipse(4, 20.5, 2.2, 1.3, "#e8c0a0")


@sprite("brook_stickleback")
def _(s):
    # A little olive fish with pale spots and a row of short spines on its back.
    def pat(s, m):
        s.paint(s.m_px([(10, 13), (14, 14), (18, 12), (21, 15), (13, 17), (19, 18)]), "#c8d080", within=m)
    for x in (9, 12, 15, 18, 21):
        s.line(x, 11, x + 1, 7, "#4a5a2a")
    fish(s, "#6a7a3a", "#dcdca8", fin="#5a6a30", pattern=pat, slim=True)


def _catfish(s, body, belly, *, square=False, spots=None):
    """A catfish: whiskery barbels, and a forked or square tail."""
    def pat(s, m):
        if spots:
            s.paint(s.m_px([(12, 13), (16, 12), (19, 14), (22, 12), (14, 16), (21, 16)]), spots, within=m)
    fin = mix(body, "#000000", 0.15)
    if square:
        w = s.wave() if s.act == "swim" else 0
        _fluke(s, [(24, 16.5), (31, 11), (31.5, 16.5), (31, 22)], fin, w)
    fish(s, body, belly, fin=fin, pattern=pat, slim=True)
    whisk = mix(body, "#000000", 0.35)
    s.path([(3, 15), (0, 13), (-2, 14)], 0.4, whisk, shade=False)
    s.path([(3, 19), (1, 22), (-1, 23)], 0.4, whisk, shade=False)
    s.path([(5, 20), (4, 23)], 0.4, whisk, shade=False)


@sprite("channel_catfish")
def _(s):
    # Blue-gray with scattered black spots and a deeply forked tail.
    _catfish(s, "#7a8a9c", "#e8ecf0", spots="#1e2228")


@sprite("black_bullhead")
def _(s):
    # Dark olive-black with a yellowish belly and a square tail.
    _catfish(s, "#3a3628", "#d8d098", square=True)


@sprite("orangespotted_sunfish")
def _(s):
    def pat(s, m):
        s.paint(s.m_px([(13, 12), (16, 14), (19, 12), (22, 14), (14, 17), (18, 18), (21, 17), (16, 10), (24, 16)]),
                "#f08a2a", within=m)
        s.paint(s.m_ellipse(10, 14, 1.6, 1.3), "#1e2228", within=m)
        s.paint(s.m_px([(11, 13), (11, 15), (12, 14)]), WHITE, within=m)
    fish(s, "#5a8a8a", "#f2b060", fin="#4a7a7a", pattern=pat)


@sprite("red_shiner")
def _(s):
    # Breeding male: steel-blue sides, red fins and a pink bar behind the head.
    def pat(s, m):
        s.paint(s.m_path([(10, 11), (11, 15), (10, 19)], 0.8), "#e05a7a", within=m)
        s.paint(s.m_ellipse(17, 12, 6, 2), "#3a5aa8", within=m)
    fish(s, "#6a8ac8", "#e8ecf4", fin="#e04a3a", pattern=pat)


@sprite("johnny_darter")
def _(s):
    # Sandy tan with little dark W and X marks along its side.
    def pat(s, m):
        for x in (11, 15, 19, 23):
            s.paint(s.m_px([(x - 1, 15), (x, 16), (x + 1, 15), (x + 2, 16), (x + 3, 15)]), "#5a4430", within=m)
        s.paint(s.m_px([(12, 11), (17, 11), (22, 12)]), "#7a6448", within=m)
    fish(s, "#c8b490", "#f2ecdc", fin="#b8a480", pattern=pat, slim=True)


@sprite("common_shiner")
def _(s):
    # Silvery with big outlined scales and pinkish fins.
    def pat(s, m):
        s.paint(s.m_px([(x + (y % 2), y) for x in range(10, 25, 3) for y in (12, 14, 16)]), "#6a7480", within=m)
        s.paint(s.m_ellipse(16, 10.5, 9, 1.3), "#5a6a78", within=m)
    fish(s, "#a8b2b8", "#eef0f0", fin="#e8a0a0", pattern=pat, slim=True)


@sprite("fantail_darter")
def _(s):
    # Brown with dark bars, a fan-shaped banded tail and gold knobs on its back fin.
    def pat(s, m):
        for x in (11, 15, 19, 23):
            s.paint(s.m_line(x, 12, x, 20), "#5a4630", within=m)
    fish(s, "#9a8060", "#e8dcc0", fin="#b09670", pattern=pat, slim=True)
    for x in (26, 28, 30):
        s.paint(s.m_line(x, 8, x, 25), "#4a3826", within=s.m_poly([(25, 5), (34, 5), (34, 27), (25, 27)]))
    s.px([(13, 9), (15, 8), (17, 7)], "#f0c040")


@sprite("northern_pike")
def _(s):
    # Long and slim, green with rows of pale bean-shaped spots, a duck-bill snout and reddish fins.
    s.can("swim")
    w = s.wave() if s.act == "swim" else 0
    fin = "#c8703a"
    _fluke(s, [(25, 17), (31, 11), (30, 17), (31, 23)], fin, w)
    s.poly([(18, 14), (23, 10), (25, 14)], fin)
    s.poly([(18, 20), (23, 24), (25, 20)], fin)
    m = s.ellipse(14, 17, 13, 4.5, "#5a7a3a", edge=True)
    s.paint(s.m_ellipse(12, 20, 11, 1.8), "#e8ecc0", within=m)
    s.paint(s.m_px([(9, 15), (12, 14), (15, 15), (18, 14), (21, 15), (10, 17), (13, 18), (16, 17), (19, 18),
                    (22, 17), (24, 16)]), "#d8e4a0", within=m)
    s.ellipse(12, 21, 2, 1.2, fin, rot=20)
    s.paint(s.m_line(2, 18, 7, 18), "#2a3a1e", within=m)
    s.eye(5, 15)


@sprite("walleye")
def _(s):
    # Olive-gold with dark saddles, a big glassy eye and a white tip on its tail.
    def pat(s, m):
        for x in (11, 15, 19, 23):
            s.paint(s.m_line(x, 10, x - 1, 14) | s.m_line(x + 1, 10, x, 14), "#4a4224", within=m)
    fish(s, "#a8984a", "#f0ecd2", fin="#8a7a40", pattern=pat, slim=True)
    s.paint(s.m_ellipse(19.5, 9, 1.4, 1.2), "#1e1e22")  # black spot on the back fin
    s.paint(s.m_ellipse(30.5, 22, 1.4, 1.4), WHITE)
    s.ellipse(6.5, 14.5, 2.2, 2.1, "#dce8ea", shade=False)
    s.px([(6, 14), (7, 14), (6, 15), (7, 15)], EYE)
    s.px([(6, 14)], WHITE)


@sprite("black_crappie")
def _(s):
    # Silvery and deep-bodied, mottled all over with black, with big speckled fins.
    fin = "#7a8070"
    s.poly([(9, 12), (14, 4), (22, 5), (24, 12)], fin, edge=True)
    s.poly([(11, 21), (16, 27), (23, 21)], fin, edge=True)

    def pat(s, m):
        s.paint(s.m_px([(11, 12), (12, 12), (15, 14), (16, 13), (19, 11), (20, 12), (22, 15), (13, 17), (17, 18),
                        (18, 17), (21, 19), (24, 13), (14, 20)]), "#26282a", within=m)
    fish(s, "#b0b8a8", "#ecf0e4", fin=fin, pattern=pat)
    s.paint(s.m_px([(13, 7), (16, 6), (19, 7), (15, 9), (21, 9), (14, 25), (17, 24), (19, 23)]), "#26282a")
