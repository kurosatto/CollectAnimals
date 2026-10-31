"""Sprites for the North Carolina species that aren't also on the California list."""
from __future__ import annotations

from archetypes import (BLACK, EYE, PINK, WHITE, alligator, back_stripes, beetle_top, bird, butterfly, crab,
                        critter, dolphin, duck, face_stripes, fish, frog, goose, grasshopper, horseshoe_crab,
                        hummingbird, jelly, lizard, mantis, owl, quad, sea_turtle, snail_shell, snake, spider_top,
                        sprite, teeth, turkey, turtle, vulture, wader)
from pixel import mix


# --------------------------------------------------------------------------- mammals
@sprite("red_wolf")
def _(s):
    def m(s, b):
        s.paint(s.m_ellipse(20, 16.5, 6.5, 2), "#7a6a5e", within=s.m_ellipse(*b["body"]))
    quad(s, "#b07a50", "#efdcc4", build="dog", ears="big", ear_in="#e0a880", tail="bushy",
         tail_col="#8a6a52", tail_tip=BLACK, markings=m)


@sprite("white_tailed_deer")
def _(s):
    def antlers(s, b):
        hx, hy = b["head"][:2]
        c = "#e0cca4"
        for dx, col in ((1.5, mix(c, "#1a1420", 0.25)), (0, c)):
            x, y = hx + 1 + dx, hy - 2.5
            s.path([(x, y), (x + 2.5, y - 3.5), (x + 1, y - 6.5), (x - 2, y - 7.5)], 0.7, col, shade=False)
            s.path([(x + 1.8, y - 4.6), (x + 0.6, y - 7.6)], 0.55, col, shade=False)

    def throat(s, b):
        hx, hy = b["head"][:2]
        s.paint(s.m_ellipse(hx - 1.6, hy - 1, 1.6, 1.2), "#f4ece0", within=s.m_ellipse(*b["head"]))
    quad(s, "#a8764c", "#f4ece0", build="deer", ears="side", ear_in="#e8c0a8", tail="cotton",
         tail_col=WHITE, nose="#2b2226", feet="#4a3a30", behind=antlers, markings=throat)


@sprite("red_fox")
def _(s):
    quad(s, "#dc6a2a", "#fbf3e8", build="dog", ears="big", ear_in="#3a2a2a", tail="bushy",
         tail_col="#d8642a", tail_tip=WHITE, feet=BLACK)


@sprite("eastern_gray_squirrel")
def _(s):
    critter(s, "#94908e", "#f4f1ea", build="squirrel", ear_in="#c8a080", tail="squirrel", tail_col="#8a8480",
            tail_tip="#e8e4dc", markings=lambda s, g: back_stripes(s, g, ["#a8988a"], top=0.3))


@sprite("eastern_chipmunk")
def _(s):
    critter(s, "#c08048", "#f4e8d4", build="ground", ear_in="#e0b090", tail="long", tail_col="#a06a3a",
            markings=lambda s, g: back_stripes(s, g, ["#4a3424", "#9a7a62", "#4a3424", "#f4e8d4", "#4a3424"], top=0.2),
            face=lambda s, g: face_stripes(s, g, "#4a3424", "#f4e8d4"))


@sprite("groundhog")
def _(s):
    critter(s, "#7a5c40", "#9a7c5c", build="marmot", ear_in="#4a3626", tail="short", tail_col="#5a4230",
            muzzle="#c8b298", nose="#2b2226", feet="#3a2a22", face=lambda s, g: teeth(s, g, WHITE))


@sprite("eastern_cottontail")
def _(s):
    def nape(s, g):  # the rusty patch behind the head
        s.paint(s.m_ellipse(g["hx"] + 3, g["hy"] + 1, 2, 1.6), "#c8763a", within=g["body"])
    critter(s, "#9e8466", "#f5efe4", build="rabbit", ears="long", ear_in="#efb6b0", tail="cotton", tail_col=WHITE,
            nose="#e08a96", markings=nape)


@sprite("marsh_rabbit")
def _(s):
    critter(s, "#5e4a3c", "#a8957e", build="rabbit", ears="long", ear_in="#c89490", tail="short", tail_col="#5e4a3c",
            tail_tip="#a8957e", nose="#d88a90", feet="#4a3a30")


@sprite("american_beaver")
def _(s):
    critter(s, "#7a4e30", "#a87a54", build="beaver", ear_in="#4a3020", tail="paddle", tail_col="#4a3a40",
            muzzle="#a87a54", nose="#2b2226", belly=False, face=teeth)


@sprite("common_bottlenose_dolphin")
def _(s):
    dolphin(s, "#7a8a9c", "#e4e8ee")


# --------------------------------------------------------------------------- birds
@sprite("northern_cardinal")
def _(s):
    bird(s, "#d42a2a", "#e04040", head="#d42a2a", wing="#b82424", tail_col="#a82020", beak="cone",
         beak_col="#f08a3a", legs="#a87a6a", tail="long", crest="jay",
         face=lambda s: s.paint(s.m_ellipse(6.5, 12, 3, 3.4), BLACK, within=s.last))
    s.eye(8, 10)


@sprite("carolina_wren")
def _(s):
    def face(s):
        s.paint(s.m_line(7, 8, 15, 9), "#f4eadc", within=s.last)
        s.paint(s.m_line(9, 10, 15, 11), "#5a3a26", within=s.last)
    bird(s, "#9a5a30", "#e8b880", head="#9a5a30", wing="#8a4e28", tail_col="#7a4424", beak="thin",
         beak_col="#4a3a3a", legs="#d8b090", tail="long", face=face,
         wing_mark=lambda s, m: s.paint(s.m_px([(18, 17), (20, 18), (22, 17), (19, 20), (21, 21)]),
                                        "#4a2e1e", within=m))


@sprite("carolina_chickadee")
def _(s):
    def face(s):
        h = s.last
        s.paint(s.m_ellipse(12, 7, 6, 3.4), BLACK, within=h)
        s.paint(s.m_ellipse(11, 12.5, 4.5, 2.4), WHITE, within=h)
        s.paint(s.m_ellipse(8.5, 16, 3, 1.6), BLACK, within=h)
    bird(s, "#8a8c92", "#efe6d8", head=WHITE, wing="#7a7c84", tail_col="#6a6c74", beak="cone",
         beak_col=BLACK, legs="#5a5a62", tail="mid", face=face)
    s.eye(8, 10)


@sprite("tufted_titmouse")
def _(s):
    bird(s, "#8a909c", "#f2eee8", head="#8a909c", wing="#7a808c", tail_col="#6a707c", beak="cone",
         beak_col="#3a3438", legs="#6a6a72", tail="mid", crest="jay",
         face=lambda s: s.px([(6, 9), (6, 10)], BLACK))
    s.paint(s.m_ellipse(17, 23, 3, 2.5), "#e0a07a")


@sprite("blue_jay")
def _(s):
    def face(s):
        s.paint(s.m_ellipse(10, 13, 4.5, 2.5), WHITE, within=s.last)
        s.paint(s.m_path([(5, 13), (8, 16.5), (13, 16)], 0.5), BLACK, within=s.last)
    def wing(s, m):
        s.paint(s.m_line(17, 18, 24, 16) | s.m_line(17, 21, 25, 19), WHITE, within=m)
        s.paint(s.m_px([(19, 18), (21, 17), (23, 17), (20, 21), (22, 20)]), BLACK, within=m)
    bird(s, "#4a7ad8", "#eef0f2", head="#4a7ad8", wing="#3a6ac8", tail_col="#3a68c0", beak="crow",
         beak_col=BLACK, legs="#3a3438", tail="long", crest="jay", face=face, wing_mark=wing)


@sprite("eastern_bluebird")
def _(s):
    bird(s, "#3a6ad8", "#d8763a", head="#3a6ad8", wing="#4a7ae8", tail_col="#2a5ac8", beak="thin",
         beak_col="#2b2630", legs="#3a3438", tail="short")
    s.paint(s.m_ellipse(13, 27, 4, 1.8), WHITE)


@sprite("american_goldfinch")
def _(s):
    def wing(s, m):
        s.paint(s.m_line(16, 19, 24, 17) | s.m_line(17, 21, 25, 19), WHITE, within=m)
    bird(s, "#f6d21e", "#f8e04a", head="#f6d21e", wing=BLACK, tail_col=BLACK, beak="cone",
         beak_col="#f0a070", legs="#d8a890", tail="short", wing_mark=wing,
         face=lambda s: s.paint(s.m_ellipse(8, 7.5, 3.5, 2), BLACK, within=s.last))
    s.eye(8, 10)


@sprite("ruby_throated_hummingbird")
def _(s):
    hummingbird(s, head="#5a9a5a", crown="#5a9a5a", throat="#e01e3c")


@sprite("red_bellied_woodpecker")
def _(s):
    def face(s):
        s.paint(s.m_ellipse(13, 7, 5.5, 3.2), "#e0302a", within=s.last)
    def bars(s, m):
        for x in (17, 19, 21, 23, 25):
            s.paint(s.m_line(x, 15, x, 23), WHITE, within=m)
    bird(s, "#2b2630", "#ece2d2", head="#ece2d2", wing="#2b2630", tail_col="#2b2630", beak="crow",
         beak_col="#3a3438", legs="#6a6a70", tail="short", face=face, wing_mark=bars)
    s.paint(s.m_ellipse(13, 27, 3, 1.5), "#f0a8a0")


@sprite("pileated_woodpecker")
def _(s):
    def face(s):
        h = s.last
        s.paint(s.m_line(5, 12, 16, 12) | s.m_line(6, 13, 16, 13), WHITE, within=h)
        s.paint(s.m_line(6, 15, 10, 15), "#e0302a", within=h)
    bird(s, "#24202a", "#2e2a34", head="#24202a", wing="#1e1a24", tail_col="#1e1a24", beak="crow",
         beak_col="#4a4448", legs="#5a5a60", tail="mid", crest="roadrunner", face=face)
    s.paint(s.m_poly([(12, 6), (19, 1), (17, 7)]) | s.m_ellipse(12, 6, 5, 2.4), "#e0302a")
    s.eye(8, 10)


@sprite("red_cockaded_woodpecker")
def _(s):
    def face(s):
        h = s.last
        s.paint(s.m_ellipse(12, 7, 6, 3.2), BLACK, within=h)
        s.paint(s.m_ellipse(12, 12, 5, 2.5), WHITE, within=h)
        s.px([(16, 9)], "#e0302a")
    def bars(s, m):
        for y in (16, 18, 20, 22):
            s.paint(s.m_line(15, y, 26, y - 2), WHITE, within=m)
    bird(s, "#2b2630", "#f2eee8", head=BLACK, wing="#2b2630", tail_col="#2b2630", beak="crow",
         beak_col="#3a3438", legs="#5a5a60", tail="short", face=face, wing_mark=bars)
    s.eye(8, 10)


@sprite("brown_headed_nuthatch")
def _(s):
    def face(s):
        s.paint(s.m_ellipse(12, 7.5, 6, 4), "#8a5a3a", within=s.last)
        s.px([(14, 4)], WHITE)
    bird(s, "#6a7a90", "#efe8e0", head=WHITE, wing="#5a6a80", tail_col="#5a6a80", beak="thin",
         beak_col="#3a3438", legs="#6a6a72", tail="short", face=face)
    s.eye(8, 10)


@sprite("painted_bunting")
def _(s):
    bird(s, "#e03a3a", "#e83a3a", head="#3a5ad8", wing="#6ab040", tail_col="#7a4a6a", beak="cone",
         beak_col="#8a8a90", legs="#a88a74", tail="mid",
         face=lambda s: s.paint(s.m_ellipse(9, 10.5, 1.8, 1.8), "#e03a3a", within=s.last))
    s.eye(8, 10)


@sprite("prothonotary_warbler")
def _(s):
    bird(s, "#f0b81e", "#f6c830", head="#f6c22a", wing="#7a8aa0", tail_col="#6a7a90", beak="thin",
         beak_col=BLACK, legs="#7a7a80", tail="short")
    s.paint(s.m_ellipse(14, 27, 3, 1.4), WHITE)


@sprite("wild_turkey")
def _(s):
    turkey(s)


@sprite("black_vulture")
def _(s):
    vulture(s, head_col="#5a585e", body="#262228", beak="#c8c0b8", wing_patch="#d8d4d0")


@sprite("barred_owl")
def _(s):
    owl(s, "#8a7a6a", "#d8cec0", eye_col=None, belly="#ece4d8", beak="#e8c060", bars="#8a6a50")
    for x in (11, 15, 19):
        s.paint(s.m_line(x, 23, x, 28), "#7a5a40")


@sprite("belted_kingfisher")
def _(s):
    def face(s):
        h = s.last
        s.paint(s.m_ellipse(11, 16.5, 5, 1.8), WHITE, within=h)
        s.px([(9, 9)], WHITE)
    bird(s, "#4a6a98", WHITE, head="#4a6a98", wing="#3e5a88", tail_col="#3e5a88", beak="long",
         beak_col="#2b2630", legs="#5a5a60", tail="short", face=face)
    s.poly([(12, 6), (14, 1), (16, 4), (19, 2), (18, 8)], "#4a6a98")
    s.paint(s.m_ellipse(13, 20, 5, 1.5), "#4a6a98")
    s.ellipse(11, 11, 6.5, 6, "#4a6a98", edge=True)
    s.paint(s.m_ellipse(11, 16.5, 5, 1.8), WHITE, within=s.last)
    s.px([(9, 9)], WHITE)
    s.poly([(6, 10.5), (-1, 12.5), (6, 13.5)], "#2b2630")
    s.eye(8, 10)
    s.blush(7, 13)


@sprite("white_ibis")
def _(s):
    wader(s, WHITE, beak="#f0603a", legs="#f0603a", wing="#eef0f2", curved=True, face="#f0603a")
    s.px([(28, 15), (29, 16)], "#2b2630")


@sprite("royal_tern")
def _(s):
    def face(s):
        h = s.last
        s.paint(s.m_ellipse(13, 7, 5.5, 3) | s.m_poly([(14, 5), (20, 7), (16, 9)]), BLACK, within=h)
    bird(s, WHITE, WHITE, head=WHITE, wing="#c8ccd4", tail_col=WHITE, beak="long", beak_col="#f08a2a",
         legs=BLACK, tail="long", face=face)
    s.poly([(16, 5), (21, 6), (17, 9)], BLACK)
    s.eye(8, 10)


@sprite("black_skimmer")
def _(s):
    def face(s):
        s.paint(s.m_ellipse(11, 7.5, 7, 4.5), "#24202a", within=s.last)
    bird(s, "#24202a", WHITE, head=WHITE, wing="#1e1a24", tail_col="#2a2630", beak="thin",
         beak_col="#e0302a", legs="#e0302a", tail="short", face=face)
    s.poly([(6, 12.5), (-1, 15), (0, 16), (6, 14.5)], "#e0302a")
    s.px([(0, 15), (1, 15)], BLACK)
    s.eye(8, 10, shine="#ffffff")


@sprite("american_oystercatcher")
def _(s):
    bird(s, "#7a6250", WHITE, head=BLACK, wing="#6a5444", tail_col="#5a4638", beak="long",
         beak_col="#f0602a", legs="#f0b0a0", tail="short",
         belly_mark=lambda s, m: s.paint(s.m_ellipse(11, 19, 4, 1.8), BLACK, within=m))
    s.px([(8, 10), (9, 10), (8, 11), (9, 11)], "#f6d030")
    s.px([(9, 11)], EYE)


@sprite("tundra_swan")
def _(s):
    goose(s)
    s.paint(s.m_ellipse(19, 23, 10.5, 6.5) | s.m_ellipse(14, 25, 5, 4) | s.m_poly([(25, 20), (31, 17), (30, 23)]),
            "#f4f4f2")
    s.paint(s.m_ellipse(22, 21, 7, 3.5, rot=-8), "#e6e8ec")
    s.paint(s.m_path([(12, 19), (10, 13), (10, 8)], 2.3) | s.m_ellipse(9.5, 7, 5, 4.2), "#f6f6f4")
    s.ellipse(4, 8.2, 2.6, 1.5, BLACK)
    s.px([(6, 8)], "#f0c830")
    s.eye(8, 5)


@sprite("wood_duck")
def _(s):
    duck(s, "#c8b088", "#8a3a3a", "#2a6a5a", bill="#e04a3a", ring=WHITE, speculum="#3a5ab8",
         tail_col="#2a2630")
    s.poly([(10, 6), (19, 9), (15, 12)], "#2a6a5a")
    s.paint(s.m_line(8, 7, 17, 9), WHITE)
    s.paint(s.m_line(9, 14, 13, 12), WHITE)
    s.px([(8, 10), (9, 10), (8, 11), (9, 11)], "#e0302a")
    s.px([(8, 10)], WHITE)
    s.px([(2, 12)], WHITE)


# --------------------------------------------------------------------------- reptiles
@sprite("eastern_box_turtle")
def _(s):
    turtle(s, "#4a3a28", "#8a5a3a", dome=True, scutes="#e8a030", speckle="#f0a030", rim="#3a2a1e")
    s.px([(3, 17)], "#e0302a")


@sprite("loggerhead_sea_turtle")
def _(s):
    sea_turtle(s, "#a0582e", "#d8a870", scutes="#b86a3a")


@sprite("american_alligator")
def _(s):
    alligator(s)


@sprite("pond_slider")
def _(s):
    turtle(s, "#4e5a32", "#3e4a2e", speckle="#e8d040", scutes="#6a7a40")
    s.paint(s.m_ellipse(6.5, 18.5, 1.8, 1), "#f0d030")
    s.paint(s.m_line(9, 21, 9, 24) | s.m_line(10, 26, 11, 29), "#e8d040")


@sprite("common_snapping_turtle")
def _(s):
    turtle(s, "#5a5240", "#6a6248", scutes="#4a4232", rim="#3e3828")
    for x in (11, 17, 23):
        s.px([(x, 15 if x == 17 else 17), (x, 14 if x == 17 else 16)], "#3a3428")
    s.poly([(26, 23), (31, 28), (27, 26)], "#6a6248")
    s.px([(28, 25), (30, 27)], "#4a4232")
    s.poly([(2, 18), (0, 20), (3, 20)], "#4a4232")


@sprite("diamondback_terrapin")
def _(s):
    turtle(s, "#6a6a70", "#b8bcc4", scutes="#8a8a92", speckle="#4a4a56")
    for cx, cy in ((11, 21), (17, 19), (23, 21)):
        s.paint(s.m_ellipse(cx, cy, 1.2, 1) , "#5a5a62")


@sprite("green_anole")
def _(s):
    lizard(s, "#4ab84a", "#c8e8a8", throat="#f05a8a")
    s.ellipse(8, 23.5, 2.6, 2.2, "#f05a8a", shade=False)
    s.eye(5, 17)


@sprite("eastern_fence_lizard")
def _(s):
    def pat(s, m):
        for x in (10, 13, 16, 19):
            s.paint(s.m_path([(x, 19), (x + 1, 20), (x, 21)], 0.5), "#3a3430", within=m)
        s.paint(s.m_ellipse(13, 24.5, 3, 1.2), "#3a7ad8", within=m)
    lizard(s, "#8a7a6a", "#d8d0c4", throat="#3a6ac8", pattern=pat)


@sprite("five_lined_skink")
def _(s):
    def pat(s, m):
        for y in (19, 21, 23):
            s.paint(s.m_line(8, y, 22, y), "#f0e0a0", within=m)
    lizard(s, "#2e2a2c", "#d8d0b8", tail_col="#3a70e8", pattern=pat, smooth=True)
    s.paint(s.m_line(3, 17, 12, 17) | s.m_line(4, 19, 11, 19), "#f0e0a0")
    s.eye(5, 17)


@sprite("eastern_ratsnake")
def _(s):
    snake(s, "#26222a", belly="#f4f0e8")


@sprite("red_cornsnake")
def _(s):
    snake(s, "#e8904a", belly="#f4e8d0", blotch="#c0302a", band_period=3.0)


@sprite("northern_water_snake")
def _(s):
    snake(s, "#8a7058", belly="#e8d8b8", bands="#4a3828", band_period=3.5, band_len=1.5)


@sprite("eastern_kingsnake")
def _(s):
    snake(s, "#1e1a22", belly="#f0e8c8", bands="#f0e8b0", band_period=4.0, band_len=0.8)


@sprite("rough_green_snake")
def _(s):
    snake(s, "#6ac04a", belly="#e8f0a0")


@sprite("eastern_hognose_snake")
def _(s):
    snake(s, "#b8944a", belly="#e8d8a8", blotch="#4a3a2a", band_period=3.0, head_w=6)
    s.px([(6, 9), (7, 9), (6, 8)], "#b8944a")


# --------------------------------------------------------------------------- amphibians
@sprite("green_frog")
def _(s):
    frog(s, "#7a8a4a", "#f0ecd0", tympanum="#5a6a34", spots=3, lip="#6ab04a", ridges="#8aa058")


@sprite("green_treefrog")
def _(s):
    frog(s, "#5ac04a", "#f4f4e0", build="tree", pads=True, side="#f4f4e0")


@sprite("copes_gray_treefrog")
def _(s):
    frog(s, "#8a8c88", "#e8e8e0", build="tree", pads=True, spots=5, thigh="#a8a49a", under_eye=WHITE,
         markings=lambda s, g: s.paint(s.m_ellipse(g["bx"] + 3, g["by"] + 3, 2, 1), "#f0b030", within=g["body"]))


@sprite("spring_peeper")
def _(s):
    # The dark X on its back.
    def x_mark(s, g):
        x, y = g["bx"] + 1, g["by"] - g["bry"] * 0.45
        s.paint(s.m_line(x - 2, y - 1, x + 2, y + 1) | s.m_line(x - 2, y + 1, x + 2, y - 1), "#7a5034",
                within=g["body"])
    frog(s, "#c89a6a", "#f2e6d0", build="tree", pads=True, markings=x_mark)


@sprite("american_toad")
def _(s):
    frog(s, "#8a6a4a", "#e8dcc4", build="toad", spots=7, warts="#c8a070", parotoid="#a07a50")


@sprite("pine_barrens_treefrog")
def _(s):
    frog(s, "#5aa84a", "#f2eee0", build="tree", pads=True, side="#7a4a6a",
         markings=lambda s, g: s.paint(s.m_ellipse(g["bx"] + 4, g["by"] + 2.5, 1.6, 1), "#f0a030", within=g["body"]))


@sprite("eastern_newt")
def _(s):
    def pat(s, m):
        for x, y in ((11, 20), (15, 19), (19, 20)):
            s.paint(s.m_ellipse(x, y, 1.2, 1.2), "#2a1e1e", within=m)
            s.paint(s.m_px([(x, y)]), "#f04020", within=m)
    lizard(s, "#f0702a", "#f8a050", smooth=True, eye_big=True, legs="#e0602a", pattern=pat)


@sprite("marbled_salamander")
def _(s):
    def pat(s, m):
        for x in (10, 15, 20):
            s.paint(s.m_ellipse(x, 21, 1.4, 3), "#d8dce4", within=m)
    lizard(s, "#26222c", "#3a3640", smooth=True, eye_big=True, legs="#2e2a34", pattern=pat)
    for x in (24, 28):
        s.paint(s.m_line(x, 21, x, 27), "#d8dce4")
    s.paint(s.m_ellipse(8, 16, 2, 1.2), "#d8dce4")
    s.eye(5, 16, size=3)
    s.px([(5, 16)], WHITE)


@sprite("red_cheeked_salamander")
def _(s):
    lizard(s, "#2a2a30", "#3a3a44", smooth=True, eye_big=True, legs="#323238")
    s.paint(s.m_ellipse(9, 20, 2, 1.4), "#e0403a")


@sprite("eastern_hellbender")
def _(s):
    c = "#7a6a4a"
    s.path([(20, 23), (26, 25), (30, 23), (31, 19)], (3, 1.2), c)
    s.path([(20, 25), (22, 28), (24, 28)], 1.2, mix(c, "#000000", 0.2))
    s.path([(10, 25), (9, 28), (7, 28)], 1.2, mix(c, "#000000", 0.2))
    m = s.ellipse(15, 23.5, 8.5, 3.6, c)
    s.paint(s.m_path([(9, 26), (12, 27.5), (15, 26), (18, 27.5), (21, 26)], 0.6), mix(c, "#000000", 0.25), within=m)
    s.paint(s.m_px([(11, 21), (15, 22), (19, 21), (13, 23)]), "#4a3e2a", within=m)
    s.path([(17, 26), (17, 29), (15, 29)], 1.2, c)
    s.path([(12, 26), (12, 29), (10, 29)], 1.2, c)
    s.ellipse(7, 22, 6.5, 3.6, c, edge=True)
    s.paint(s.m_line(1, 23, 8, 24), mix(c, "#000000", 0.4))
    s.px([(4, 20)], EYE)
    s.blush(6, 23)


# --------------------------------------------------------------------------- invertebrates
@sprite("eastern_tiger_swallowtail")
def _(s):
    def pat(s, fm, hm):
        w = fm | hm
        for a, b in [((6, 3), (9, 13)), ((10, 6), (12, 13)), ((13, 9), (14, 15))]:
            s.paint(s.m_line(*a, *b) | s.m_line(a[0] + 1, a[1], b[0] + 1, b[1]), BLACK, mirror=True, within=w)
        s.paint(s.m_line(2, 7, 2, 14) | s.m_line(3, 13, 13, 17) | s.m_line(5, 20, 8, 26) | s.m_line(6, 23, 10, 26),
                BLACK, mirror=True, within=w)
        s.paint(s.m_poly([(5, 20), (9, 26), (12, 25), (8, 20)]), BLACK, mirror=True, within=hm)
        s.px([(9, 24), (10, 25)], "#4a7ae8", mirror=True)
        s.px([(13, 23)], "#f0802a", mirror=True)
    butterfly(s, "#f8d82a", "#f8d82a", pattern=pat, tails=True)


@sprite("zebra_swallowtail")
def _(s):
    def pat(s, fm, hm):
        w = fm | hm
        for a, b in [((5, 3), (4, 13)), ((8, 5), (8, 14)), ((11, 7), (12, 15)), ((14, 10), (14, 16))]:
            s.paint(s.m_line(*a, *b) | s.m_line(a[0] + 1, a[1], b[0] + 1, b[1]), BLACK, mirror=True, within=w)
        s.paint(s.m_line(13, 17, 13, 22) | s.m_line(6, 20, 9, 26), BLACK, mirror=True, within=hm)
        s.px([(11, 24), (12, 24)], "#e0302a", mirror=True)
    butterfly(s, "#e8f2ec", "#e8f2ec", pattern=pat, tails=True)
    s.path([(10, 23), (9, 30)], (1, 0.6), "#2b2630", mirror=True)


@sprite("gulf_fritillary")
def _(s):
    def pat(s, fm, hm):
        s.paint(s.m_px([(6, 7), (9, 9), (12, 11), (5, 11), (9, 13)]), BLACK, mirror=True, within=fm)
        s.paint(s.m_px([(6, 6), (6, 12)]), WHITE, mirror=True, within=fm)
        s.paint(s.m_px([(7, 20), (9, 23), (11, 20), (6, 23)]), BLACK, mirror=True, within=hm)
        s.paint(s.m_line(15, 12, 7, 8), "#c8501a", mirror=True, within=fm)
    butterfly(s, "#f07a1a", "#f08a2a", pattern=pat)


@sprite("luna_moth")
def _(s):
    def pat(s, fm, hm):
        s.paint(s.m_line(4, 4, 14, 10), "#9a6a7a", mirror=True, within=fm)
        s.paint(s.m_ellipse(8.5, 11, 1.6, 1.6) | s.m_ellipse(9, 21, 1.6, 1.6), "#e8d06a", mirror=True)
        s.paint(s.m_px([(8, 11), (9, 21)]), "#5a3a5a", mirror=True)
    s.path([(10, 24), (8, 28), (10, 31)], (1.4, 1.0), "#b8e8a0", mirror=True)
    butterfly(s, "#b8e8a0", "#b8e8a0", body=WHITE, pattern=pat)
    s.path([(15, 8), (12, 3), (10, 2)], 0.8, "#c8b88a", shade=False)
    s.path([(16, 8), (19, 3), (21, 2)], 0.8, "#c8b88a", shade=False)
    s.px([(14, 9), (17, 9)], EYE)


@sprite("common_eastern_firefly")
def _(s):
    beetle_top(s, "#2e2a30", head="#2b2630", pron="#f0c040")
    s.paint(s.m_ellipse(16, 11, 2, 1.5), "#e0302a")
    s.paint(s.m_line(7, 15, 7, 24) | s.m_line(25, 15, 25, 24), "#e8c84a")
    s.paint(s.m_ellipse(16, 20, 10, 10) & s.m_poly([(0, 26), (32, 26), (32, 32), (0, 32)]), "#f4f06a")
    s.px([(14, 27), (17, 28)], "#fcfcd0")


@sprite("carolina_mantis")
def _(s):
    mantis(s, "#9a9070", "#b8ac88", "#d8d0a8")
    s.paint(s.m_px([(21, 20), (24, 22), (26, 21)]), "#6a6448")


@sprite("eastern_lubber_grasshopper")
def _(s):
    grasshopper(s, "#2e2a2c", "#f0b030", legs="#3a3436")
    s.paint(s.m_ellipse(21, 17, 6, 2, rot=-8), "#e0503a")


@sprite("yellow_garden_spider")
def _(s):
    def pat(s, m):
        s.paint(s.m_ellipse(16, 22, 6, 8) & ~s.m_ellipse(16, 22, 3.5, 6.5), "#f6d02a", within=m)
        s.paint(s.m_px([(15, 17), (17, 17), (16, 20), (15, 24), (17, 24)]), "#f6d02a", within=m)
    spider_top(s, BLACK, "#3a3034", pattern=pat, ceph="#d8d0c0", leg_bands="#e0a07a", web=True)


@sprite("joro_spider")
def _(s):
    def pat(s, m):
        for y in (17, 20, 23, 26):
            s.paint(s.m_line(10, y, 22, y), "#f0d040", within=m)
        s.paint(s.m_line(10, 18, 22, 18) | s.m_line(10, 24, 22, 24), "#5a7a9a", within=m)
        s.paint(s.m_px([(16, 28), (15, 28)]), "#e0302a", within=m)
    spider_top(s, "#2e3440", "#2b2630", pattern=pat, ceph="#a8a8b0", leg_bands="#f0d040")


# --------------------------------------------------------------------------- marine
@sprite("atlantic_ghost_crab")
def _(s):
    crab(s, "#e8d8b4", "#d8c49a", legs="#c8b48e", stalks=3, eye_big=True)


@sprite("atlantic_sand_fiddler_crab")
def _(s):
    def pat(s, m):
        s.paint(s.m_ellipse(16, 18, 5, 3), "#a890c0", within=m)
    crab(s, "#8a7a9a", "#f0e2c8", legs="#7a6a80", stalks=3, big_claw=True, pattern=pat)


@sprite("atlantic_horseshoe_crab")
def _(s):
    horseshoe_crab(s)


@sprite("cannonball_jellyfish")
def _(s):
    jelly(s, "#f2ead8", rim="#9a6a4a", arms="#e8dcc8")


@sprite("scotch_bonnet")
def _(s):
    snail_shell(s, "#f4e6cc", "#d0803a")


@sprite("red_drum")
def _(s):
    def pat(s, m):
        s.paint(s.m_ellipse(22, 14, 1.6, 1.6), BLACK, within=m)
    fish(s, "#c8743a", "#f0d8c0", fin="#b06030", pattern=pat, slim=True)


@sprite("brook_trout")
def _(s):
    def pat(s, m):
        s.paint(s.m_px([(10, 11), (13, 10), (16, 11), (19, 10), (22, 12), (12, 13), (18, 13)]), "#c8d080", within=m)
        for x, y in ((12, 16), (17, 15), (21, 17), (15, 18)):
            s.paint(s.m_px([(x, y)]), "#e0302a", within=m)
            s.paint(s.m_px([(x - 1, y), (x + 1, y)]), "#6a90d0", within=m)
    fish(s, "#4a6a4a", "#f08a3a", fin="#e07a3a", pattern=pat, slim=True)
    s.paint(s.m_line(12, 25, 16, 25), WHITE)
