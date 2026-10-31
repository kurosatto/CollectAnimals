"""Sprites for the New York species that aren't on an earlier state's list."""
from __future__ import annotations

from archetypes import (BLACK, WHITE, back_stripes, bird, butterfly, crab, critter, frog, goose, lizard, quad,
                        snake, sprite, teeth, turtle)
from pixel import mix
from species_tx import _segmented


# --------------------------------------------------------------------------- mammals
@sprite("american_red_squirrel")
def _(s):
    critter(s, "#b0582a", "#f4ece0", build="squirrel", ears="tuft", ear_in="#d8906a", tail="squirrel",
            tail_col="#a04a22", tail_tip="#c87a4a", eye_ring=WHITE,
            markings=lambda s, g: back_stripes(s, g, ["#2b2226"], top=g["bry"] * 1.1))  # black line along the side


@sprite("muskrat")
def _(s):
    critter(s, "#6a4a30", "#a88a6a", build="beaver", ear_in="#4a3020", tail="rat", tail_col="#3a2e2a",
            muzzle="#9a7a5a", nose="#2b2226", face=teeth)


@sprite("northern_short_tailed_shrew")
def _(s):
    s.can("walk")
    w = s.wave() if s.act == "walk" else 0
    fur = "#4a4650"
    s.path([(27, 24), (30, 24)], (1.1, 0.7), fur)
    for x, sw in ((12, w), (23, -w)):
        s.ellipse(x - sw, 28, 1.8, 1.2, "#e0b0b8")
    m = s.ellipse(18, 22, 9.5, 6, fur, edge=True)
    s.paint(s.m_ellipse(17, 18, 7, 2), mix(fur, "#ffffff", 0.18), within=m)
    s.path([(10, 21), (3, 23)], (2.6, 0.9), fur)  # pointy snout
    s.ellipse(2.5, 23.2, 1.1, 1, "#e0a0a8")
    s.px([(7, 20)], "#1a1420")
    s.blush(9, 23)
    if s.act == "walk" and s.f % 2:
        s.shift(0, -1)


@sprite("north_american_porcupine")
def _(s):
    s.can("walk")
    w = s.wave() if s.act == "walk" else 0
    fur, quill = "#3a302a", "#e8dcc4"
    for x, sw in ((11, w), (22, -w)):
        s.ellipse(x - sw, 28, 2.6, 1.6, "#2a221e")
    m = s.ellipse(18, 20, 11, 8.5, fur, edge=True)
    # The quills: pale-tipped spikes all over the back.
    for i in range(14):
        x = 9 + i * 1.5
        top = 20 - 8.5 * (1 - ((x - 18) / 11) ** 2) ** .5
        s.line(round(x), round(top + 3), round(x + 1.5), round(top - 1.5), quill)
        s.px([(round(x + 1.5), round(top - 1.5))], WHITE)
    s.paint(s.m_px([(14, 17), (18, 15), (22, 18), (12, 21), (20, 22), (25, 20)]), quill, within=m)
    s.ellipse(8, 22, 5, 4.5, "#4a3e36", edge=True)
    s.ellipse(4.5, 23.5, 2, 1.6, "#2b2226")
    s.eye(7, 21)
    s.blush(8, 24)
    if s.act == "walk" and s.f % 2:
        s.shift(0, -1)


@sprite("american_mink")
def _(s):
    quad(s, "#3a261c", "#4a3226", build="low", ears="small", ear_in="#5a3e2e", tail="long", tail_col="#2e1e16",
         muzzle="#4a3226", nose="#1a1210", belly=False)
    s.px([(5, 23), (6, 23)], WHITE)  # white chin


@sprite("fisher")
def _(s):
    def frost(s, b):
        hx, hy, hrx, hry = b["head"]
        s.paint(s.m_ellipse(hx, hy - 1, hrx, hry * .7), "#8a7a6a", within=s.m_ellipse(hx, hy, hrx, hry))
    quad(s, "#3a2e26", "#4a3c32", build="low", ears="round", ear_in="#5a4a3e", tail="bushy", tail_col="#2a201a",
         muzzle="#4a3c32", nose="#1a1210", belly=False, markings=frost)


# --------------------------------------------------------------------------- birds
@sprite("ring_billed_gull")
def _(s):
    def wing(s, m):
        s.paint(s.m_poly([(23, 15), (27, 14), (27, 19), (23, 19)]), "#2b2630", within=m)
        s.paint(s.m_px([(25, 16)]), WHITE, within=m)

    def ring(s):
        s.px([(2, 13), (3, 13)], BLACK)
    bird(s, WHITE, WHITE, head=WHITE, wing="#a8b0bc", tail_col=WHITE, beak="crow", beak_col="#f0d040",
         legs="#f0d040", tail="short", wing_mark=wing, face=ring, eye_col="#f0d040")


@sprite("american_herring_gull")
def _(s):
    def wing(s, m):
        s.paint(s.m_poly([(23, 15), (27, 14), (27, 19), (23, 19)]), "#2b2630", within=m)
        s.paint(s.m_px([(24, 17), (26, 17)]), WHITE, within=m)
    bird(s, WHITE, WHITE, head=WHITE, wing="#9aa4b2", tail_col=WHITE, beak="crow", beak_col="#f0c830",
         legs="#f0a8a8", tail="short", wing_mark=wing, big=True, eye_col="#f0d860")
    s.px([(3, 13)], "#e0403a")


@sprite("gray_catbird")
def _(s):
    def face(s):
        s.paint(s.m_ellipse(11, 6.5, 4.5, 2.2), BLACK, within=s.last)

    def rump(s, m):
        s.ellipse(22, 24, 2, 1.4, "#a0482a")
    bird(s, "#6e7480", "#7c828e", head="#6e7480", wing="#626874", tail_col="#2b2630", beak="thin",
         beak_col="#1a1820", legs="#2b2630", tail="long", face=face, belly_mark=rump)


@sprite("song_sparrow")
def _(s):
    def streaks(s, m):
        s.paint(s.m_px([(11, 21), (13, 20), (15, 22), (12, 23), (14, 24), (16, 20)]), "#6a4a34", within=m)
        s.paint(s.m_ellipse(13, 21.5, 1.4, 1.2), "#4a3022", within=m)

    def wing(s, m):
        s.paint(s.m_line(16, 18, 23, 16) | s.m_px([(18, 20), (21, 19)]), "#5a3a26", within=m)

    def face(s):
        s.paint(s.m_line(5, 11, 13, 11), "#c8c0b4", within=s.last)
        s.paint(s.m_line(6, 14, 10, 15), "#6a4a34", within=s.last)
    bird(s, "#9a6e4a", "#efe8dc", head="#8a5e3e", wing="#a07250", tail_col="#7a5a40", beak="cone",
         beak_col="#8a7a6a", legs="#d0a080", tail="mid", belly_mark=streaks, wing_mark=wing, face=face)


@sprite("white_throated_sparrow")
def _(s):
    def face(s):
        h = s.last
        s.paint(s.m_line(5, 8, 15, 8), WHITE, within=h)
        s.paint(s.m_line(5, 7, 15, 7) | s.m_line(6, 11, 15, 11), "#2b2630", within=h)
        s.paint(s.m_px([(6, 9), (7, 9)]), "#f2d22a", within=h)
        s.paint(s.m_ellipse(7, 15, 2.6, 1.6), WHITE, within=h)

    def wing(s, m):
        s.paint(s.m_line(16, 18, 23, 16), "#5a3a26", within=m)
    bird(s, "#8a6448", "#c4c4c4", head="#9a9aa0", wing="#9a6c4a", tail_col="#7a5a40", beak="cone",
         beak_col="#6a6a70", legs="#d0a080", tail="mid", wing_mark=wing, face=face)


@sprite("common_grackle")
def _(s):
    def sheen(s, m):
        s.paint(s.m_ellipse(18, 18, 3, 1.5), "#5a3a2a", within=m)

    def face(s):
        s.paint(s.m_ellipse(11, 9, 5, 4), "#2a4a8a", within=s.last)
    bird(s, "#1e1a24", "#26222c", head="#1e1a24", wing="#1a1620", tail_col="#1a1620", beak="crow",
         beak_col="#141218", legs="#2a2630", tail="long", eye_col="#f0d040", wing_mark=sheen, face=face)


@sprite("black_capped_chickadee")
def _(s):
    def face(s):
        h = s.last
        s.paint(s.m_ellipse(11, 7, 6.5, 3.2), BLACK, within=h)
        s.paint(s.m_ellipse(6, 15, 3, 2), BLACK, within=h)

    def wing(s, m):
        s.paint(s.m_line(16, 20, 23, 17), "#e8e8e8", within=m)
    bird(s, "#8a8e96", "#f0e4d4", head=WHITE, wing="#70747c", tail_col="#5a5e66", beak="thin",
         beak_col="#1a1820", legs="#3a3a44", tail="mid", face=face, wing_mark=wing)


@sprite("dark_eyed_junco")
def _(s):
    bird(s, "#4a4e58", WHITE, head="#40444e", wing="#3e424c", tail_col="#2e3038", beak="cone",
         beak_col="#f0c8c0", legs="#c8a090", tail="mid")
    s.px([(29, 14), (30, 15)], WHITE)  # white outer tail feathers


@sprite("common_yellowthroat")
def _(s):
    def face(s):
        s.paint(s.m_poly([(3, 7), (13, 9), (13, 13), (4, 14)]), BLACK, within=s.last)
        s.paint(s.m_line(5, 6, 15, 7), "#e8e8d8", within=s.last)
    bird(s, "#7a7a3a", "#f2d22a", head="#7a7a3a", wing="#6a6a32", tail_col="#5a5a2a", beak="thin",
         beak_col="#1a1820", legs="#c8a090", tail="mid", face=face)


@sprite("white_breasted_nuthatch")
def _(s):
    def face(s):
        s.paint(s.m_ellipse(13, 6.5, 5, 2.2), BLACK, within=s.last)

    def rump(s, m):
        s.ellipse(21, 25, 2, 1.2, "#b0583a")
    bird(s, "#6a7c94", WHITE, head=WHITE, wing="#5a6c84", tail_col="#2b2630", beak="long",
         beak_col="#3a3a44", legs="#6a5a50", tail="short", face=face, belly_mark=rump)


@sprite("mute_swan")
def _(s):
    goose(s)
    s.paint(s.m_ellipse(19, 23, 10.5, 6.5) | s.m_ellipse(14, 25, 5, 4) | s.m_poly([(25, 20), (31, 17), (30, 23)]),
            "#f6f6f4")
    s.paint(s.m_ellipse(22, 20, 7.5, 4, rot=-12), "#eceef2")  # wings raised a little
    s.paint(s.m_path([(12, 19), (13, 13), (11, 8)], 2.3) | s.m_ellipse(10, 7, 5, 4.2), "#f8f8f6")
    s.ellipse(4.5, 8.5, 3, 1.5, "#f07a2a")  # orange bill
    s.ellipse(7, 7.6, 1.5, 1.5, BLACK)  # the black knob
    s.eye(9, 6)


# --------------------------------------------------------------------------- reptiles
@sprite("painted_turtle")
def _(s):
    turtle(s, "#3a4a3a", "#2e3a2e", scutes="#4e604e", rim="#e04a2a", speckle="#f2d22a")
    s.px([(4, 22), (6, 22), (8, 23)], "#f2d22a")


@sprite("eastern_milksnake")
def _(s):
    snake(s, "#c8c0b0", belly="#f0ece4", blotch="#a8402a", band_period=4.5, band_len=2.6, head="#b0a898")
    s.paint(s.m_poly([(11, 8), (15, 7), (14, 11)]), "#a8402a", within=s.m_ellipse(12.5, 10.5, 5.4, 4))


@sprite("dekays_brownsnake")
def _(s):
    snake(s, "#8a6e56", belly="#e8d4c0", bands="#6a523e", band_period=2.4, band_len=0.7, head="#7a604a",
          head_w=4.6)


@sprite("ring_necked_snake")
def _(s):
    snake(s, "#3a3e48", belly="#f2b42a", head="#3a3e48", head_w=4.8)
    # the yellow ring behind the head
    s.paint(s.m_ellipse(14.5, 14.5, 3.6, 1.2), "#f2c42a", within=s.m_path([(15, 17), (13.5, 13)], 2.8))


@sprite("red_bellied_snake")
def _(s):
    snake(s, "#6a5444", belly="#e04a3a", stripe="#8a7060", head="#5a4638", head_w=4.6)
    s.px([(12, 13), (13, 13)], "#f0e0c8")


@sprite("italian_wall_lizard")
def _(s):
    def pat(s, m):
        s.paint(s.m_line(8, 19, 22, 19), "#3a4a2a", within=m)
        s.paint(s.m_px([(10, 21), (13, 22), (16, 21), (19, 22), (12, 20), (18, 20)]), "#2a3a1e", within=m)
    lizard(s, "#7aa84a", "#f0ecd4", head="#8a7a5a", throat="#f0ecd4", pattern=pat, tail_col="#8a7a5a",
           tail_pts=[(20, 22), (27, 25), (33, 24), (36, 20)])


# --------------------------------------------------------------------------- amphibians
@sprite("eastern_red_backed_salamander")
def _(s):
    def stripe(s, m):
        s.paint(s.m_line(8, 19, 22, 19) | s.m_line(8, 20, 22, 20), "#d8442a", within=m)
        s.paint(s.m_px([(10, 23), (14, 24), (18, 23)]), WHITE, within=m)
    lizard(s, "#2e2a30", "#8a8a90", head="#2e2a30", throat="#8a8a90", pattern=stripe, smooth=True,
           eye_big=True, legs="#2a262c", tail_col="#d8442a")


@sprite("spotted_salamander")
def _(s):
    def spots(s, m):
        s.paint(s.m_ellipse(10, 19.5, 1.3, 1.1) | s.m_ellipse(15, 19, 1.3, 1.1) | s.m_ellipse(20, 19.5, 1.3, 1.1)
                | s.m_ellipse(12, 21.5, 1, 1) | s.m_ellipse(18, 21.5, 1, 1), "#f2c42a", within=m)
    lizard(s, "#2e2e40", "#4a4a5a", head="#2e2e40", throat="#4a4a5a", pattern=spots, smooth=True,
           eye_big=True, legs="#2a2a3a", tail_col="#2e2e40")
    s.px([(5, 14), (8, 14), (27, 23), (30, 20)], "#f2c42a")


@sprite("wood_frog")
def _(s):
    # The dark robber's mask through the eye.
    frog(s, "#b0805a", "#f4ece0", tympanum="#5a3a2a", mask="#4a2e22", spots=2, ridges="#c8a07a")


# --------------------------------------------------------------------------- insects and other small animals
@sprite("common_eastern_bumble_bee")
def _(s):
    s.can("fly")
    up = not (s.act == "fly" and s.f % 2)
    s.ellipse(20, 8 if up else 11, 4.5, 6.5 if up else 4, "#e6f4fc", rot=25 if up else 70, shade=False, edge=True)
    s.ellipse(25, 11 if up else 13, 3.5, 5 if up else 3, "#d6ecfa", rot=40 if up else 80, shade=False, edge=True)
    m = s.ellipse(18, 19, 9, 7.5, "#2b2226")
    s.paint(s.m_poly([(12, 8), (17, 8), (17, 30), (12, 30)]), "#f2c42a", within=m)  # yellow up front only
    s.paint(s.m_poly([(17, 8), (20, 8), (20, 13), (17, 13)]), "#f2c42a", within=m)
    s.line(9, 25, 8, 29, "#2b2226")
    s.line(13, 25, 13, 29, "#2b2226")
    s.ellipse(8.5, 17, 5.5, 5.5, "#2b2226", edge=True)
    s.line(6, 12, 4, 6, "#2b2226")
    s.line(9, 12, 10, 6, "#2b2226")
    s.eye(5, 16, color="#11080f", shine="#ffffff")
    s.blush(5, 19, color="#ff8fa8")


@sprite("brown_belted_bumble_bee")
def _(s):
    s.can("fly")
    up = not (s.act == "fly" and s.f % 2)
    s.ellipse(20, 8 if up else 11, 4.5, 6.5 if up else 4, "#e6f4fc", rot=25 if up else 70, shade=False, edge=True)
    s.ellipse(25, 11 if up else 13, 3.5, 5 if up else 3, "#d6ecfa", rot=40 if up else 80, shade=False, edge=True)
    m = s.ellipse(18, 19, 9, 7.5, "#f2c42a")
    s.paint(s.m_poly([(17, 8), (21, 8), (21, 30), (17, 30)]), "#9a5a2a", within=m)  # the brown belt
    s.paint(s.m_poly([(24, 8), (30, 8), (30, 30), (24, 30)]), "#2b2226", within=m)
    s.line(9, 25, 8, 29, "#2b2226")
    s.line(13, 25, 13, 29, "#2b2226")
    s.ellipse(8.5, 17, 5.5, 5.5, "#2b2226", edge=True)
    s.line(6, 12, 4, 6, "#2b2226")
    s.line(9, 12, 10, 6, "#2b2226")
    s.eye(5, 16, color="#11080f", shine="#ffffff")
    s.blush(5, 19, color="#ff8fa8")


@sprite("eastern_carpenter_bee")
def _(s):
    s.can("fly")
    up = not (s.act == "fly" and s.f % 2)
    s.ellipse(20, 8 if up else 11, 4.5, 6.5 if up else 4, "#d8e0f0", rot=25 if up else 70, shade=False, edge=True)
    s.ellipse(25, 11 if up else 13, 3.5, 5 if up else 3, "#c8d0e8", rot=40 if up else 80, shade=False, edge=True)
    s.ellipse(21, 20, 7.5, 6.5, "#1e1c26", edge=True)  # shiny bare black abdomen
    s.px([(19, 16), (20, 16), (21, 17)], "#6a6a8a")
    s.ellipse(13, 18, 5, 5, "#f2c42a", edge=True)  # fuzzy yellow thorax
    s.line(9, 25, 8, 29, "#2b2226")
    s.line(13, 25, 13, 29, "#2b2226")
    s.ellipse(7, 17, 4.5, 4.5, "#2b2226", edge=True)
    s.line(5, 13, 3, 8, "#2b2226")
    s.line(8, 13, 9, 8, "#2b2226")
    s.eye(4, 16, color="#11080f", shine="#ffffff")
    s.blush(4, 19, color="#ff8fa8")


@sprite("spotted_lanternfly")
def _(s):
    def pat(s, fm, hm):
        s.paint(s.m_px([(5, 6), (8, 5), (4, 10), (7, 9), (10, 8), (6, 13), (9, 12), (12, 11)]), BLACK,
                mirror=True, within=fm)
        s.paint(s.m_line(4, 21, 9, 25) | s.m_line(5, 19, 13, 19), BLACK, mirror=True, within=hm)
        s.paint(s.m_poly([(10, 21), (15, 21), (15, 25), (11, 25)]), WHITE, mirror=True, within=hm)
    butterfly(s, "#d8c8b0", "#d8302a", body="#2b2226", pattern=pat)


@sprite("spongy_moth")
def _(s):
    def pat(s, fm, hm):
        s.paint(s.m_line(4, 8, 13, 12) | s.m_line(4, 12, 13, 15), "#6a5a44", mirror=True, within=fm)
        s.paint(s.m_ellipse(10, 9, 1, 1), "#4a3e30", mirror=True, within=fm)
    butterfly(s, "#b8a888", "#c8b898", body="#7a6a54", pattern=pat)


@sprite("small_white")
def _(s):
    def pat(s, fm, hm):
        s.paint(s.m_poly([(1.5, 6), (5, 3), (6, 6), (2, 9)]), "#4a4a4a", mirror=True, within=fm)
        s.paint(s.m_ellipse(7, 11, 1.2, 1.2), "#3a3a3a", mirror=True, within=fm)
    butterfly(s, "#f6f4ec", "#f2f0dc", pattern=pat)


@sprite("silver_spotted_skipper")
def _(s):
    def pat(s, fm, hm):
        s.paint(s.m_poly([(6, 8), (11, 7), (12, 11), (7, 12)]), "#f0a830", mirror=True, within=fm)
        s.paint(s.m_ellipse(9, 21, 3, 2), WHITE, mirror=True, within=hm)
    butterfly(s, "#5a4430", "#4a3628", body="#4a3a2a", pattern=pat)


@sprite("isabella_tiger_moth")
def _(s):
    # The woolly bear caterpillar: black at both ends, rusty orange in the middle.
    pts = _segmented(s, 8, "#c86a2a", "#1e1a1c", "#3a2a22", leg_len=1.2, spacing=2.8, r=2.8, antenna=0)
    for i, (x, y) in enumerate(pts):
        if i < 2 or i > 5:
            s.ellipse(x, y, 2.8, 2.8, "#1e1a1c")
        s.px([(round(x), round(y - 3)), (round(x + 1), round(y - 3))], mix("#c86a2a", "#ffffff", 0.3)
             if 1 < i < 6 else "#4a4048")
    hx, hy = pts[0]
    s.ellipse(hx - 1, hy, 3.4, 3, "#1e1a1c", edge=True)
    s.eye(round(hx - 2), round(hy - 1))


@sprite("hickory_tussock_moth")
def _(s):
    # The fuzzy white caterpillar with black tufts.
    pts = _segmented(s, 8, "#f0ece4", "#2b2226", "#c8c0b4", leg_len=1.2, spacing=2.8, r=2.8, antenna=0)
    for i, (x, y) in enumerate(pts):
        s.px([(round(x), round(y - 4)), (round(x + 1), round(y - 4))], WHITE)
        if i in (2, 3):
            s.path([(x, y - 3), (x + 1, y - 7)], 0.6, BLACK, shade=False)
        if i in (1, 3, 5):
            s.px([(round(x), round(y))], BLACK)
    hx, hy = pts[0]
    s.ellipse(hx - 1, hy, 3.2, 2.8, "#2b2226", edge=True)
    s.eye(round(hx - 2), round(hy - 1))


@sprite("common_striped_woodlouse")
def _(s):
    s.can("walk")
    w = s.wave() if s.act == "walk" else 0
    g = "#8a7a6a"
    for i, x in enumerate((9, 13, 17, 21)):
        d = round(w * (1 if i % 2 else -1))
        s.line(x, 25, x - 1 + d, 28, "#4a3e34")
    m = s.ellipse(16, 21, 11, 5.5, g, edge=True)
    for x in (10, 13, 16, 19, 22, 25):
        s.paint(s.m_line(x, 13, x, 29), mix(g, "#000000", 0.3), within=m)
    s.paint(s.m_line(6, 21, 27, 21) | s.m_px([(12, 18), (18, 18), (24, 19)]), "#e8dcc4", within=m)
    s.line(27, 22, 30, 24, "#6a5a4a")  # tail prongs
    s.line(27, 20, 30, 18, "#6a5a4a")
    s.ellipse(6.5, 22, 3.5, 3.5, "#6a5a4a", edge=True)
    s.line(4, 19, 0, 16, "#4a3e34")
    s.eye(5, 21)
    s.blush(6, 24)


@sprite("common_shiny_woodlouse")
def _(s):
    s.can("walk")
    w = s.wave() if s.act == "walk" else 0
    g = "#7a7a80"
    for i, x in enumerate((9, 13, 17, 21)):
        d = round(w * (1 if i % 2 else -1))
        s.line(x, 25, x - 1 + d, 28, "#3a3a44")
    m = s.ellipse(16, 21, 11, 5.5, g, edge=True)
    for x in (10, 13, 16, 19, 22, 25):
        s.paint(s.m_line(x, 13, x, 29), mix(g, "#000000", 0.25), within=m)
    s.paint(s.m_line(9, 17, 23, 17) | s.m_px([(11, 18), (17, 18), (21, 18)]), "#e4e4ec", within=m)  # the shine
    s.line(27, 22, 30, 24, "#5a5a64")
    s.line(27, 20, 30, 18, "#5a5a64")
    s.ellipse(6.5, 22, 3.5, 3.5, "#5a5a64", edge=True)
    s.line(4, 19, 0, 16, "#3a3a44")
    s.eye(5, 21)
    s.blush(6, 24)


@sprite("house_centipede")
def _(s):
    s.can("walk")
    w = s.wave() if s.act == "walk" else 0
    body = "#c8b090"
    # Long banded legs, fanning out.
    for i in range(7):
        x, d = 8 + i * 2.6, (1 if i % 2 else -1) * w
        s.path([(x, 20), (x - 3 + d, 25), (x - 5 + d, 30)], 0.45, "#8a7a6a", shade=False)
        s.path([(x, 18), (x - 3 - d, 13), (x - 5 - d, 9)], 0.45, "#8a7a6a", shade=False)
    s.path([(26, 19), (31, 15), (34, 12)], 0.45, "#8a7a6a", shade=False)
    s.path([(26, 19), (31, 22), (34, 25)], 0.45, "#8a7a6a", shade=False)
    m = s.ellipse(17, 19, 10, 2.6, body, edge=True)
    for x in (11, 15, 19, 23):
        s.paint(s.m_line(x, 16, x + 1, 22), "#6a5a8a", within=m)
    s.ellipse(6, 19, 2.6, 2.4, body, edge=True)
    s.path([(5, 18), (1, 12), (-2, 8)], 0.45, "#8a7a6a", shade=False)
    s.path([(5, 20), (1, 25), (-2, 28)], 0.45, "#8a7a6a", shade=False)
    s.eye(5, 18)


@sprite("aromatic_cherry_millipede")
def _(s):
    pts = _segmented(s, 9, "#2a2228", "#2a2228", "#e8a030", leg_len=1.8, spacing=2.8, r=2.4, antenna=2.5)
    for x, y in pts[1:]:
        s.px([(round(x) - 1, round(y) - 2), (round(x) + 1, round(y) - 2)], "#f2c42a")


@sprite("atlantic_blue_crab")
def _(s):
    crab(s, "#4a7a8a", "#4a8ad8", legs="#4a8ad8")
    s.px([(5, 9), (6, 9), (27, 9), (26, 9)], "#e04a3a")  # red claw tips
