"""Sprites for the Southwest (Arizona, New Mexico, Utah, Nevada) species that aren't on an
earlier state's list: desert lizards and toads, Sky Island birds, chipmunks and
antelope squirrels, and the bugs of the creosote flats."""
from __future__ import annotations

from archetypes import (BLACK, EYE, WHITE, back_stripes, bird, butterfly, critter, dragonfly, duck, face_stripes,
                        fish, flecks, frog, grasshopper, lizard, mantis, quad, snail_shell, spider_top, sprite,
                        wader)
from pixel import mix
from species_household import cockroach
from species_tx import _segmented
from species_va import _woodlouse


# --------------------------------------------------------------------------- mammals
def _ground_squirrel(s, fur, light, *, tail_col, tail_tip=None, tail="squirrel", side=None, ears="small"):
    """Ground squirrel with an optional pale stripe along each side and a pale eye ring."""
    critter(s, fur, light, build="ground", ears=ears, ear_in=mix(fur, "#f0b0a0", 0.5),
            tail="bushy" if tail == "squirrel" else tail, tail_col=tail_col, tail_tip=tail_tip,
            eye_ring=mix(light, WHITE, 0.4),
            markings=(lambda s, g: back_stripes(s, g, [side], top=g["bry"] * 0.9)) if side else None)


def _chipmunk(s, fur, light, dark, pale, *, head=None, tail_col=None):
    """Chipmunk: dark and pale stripes on the face and down the back."""
    critter(s, fur, light, build="ground", ear_in=mix(fur, "#f0c0a0", 0.5), tail="long",
            tail_col=tail_col or mix(fur, "#000000", 0.15), head=head,
            markings=lambda s, g: back_stripes(s, g, [dark, fur, dark, pale, dark], top=0.2),
            face=lambda s, g: face_stripes(s, g, dark, pale))


@sprite("round_tailed_ground_squirrel")
def _(s):
    # Plain sandy cinnamon all over, with a thin round tail.
    _ground_squirrel(s, "#c8a06e", "#f0e2c8", tail_col="#b88e5e", tail="long")


@sprite("harris_antelope_squirrel")
def _(s):
    # Grizzled gray with one white stripe each side and a gray tail edged in white.
    _ground_squirrel(s, "#9a9088", "#f0ece6", tail_col="#6e6862", tail_tip="#f4f2ee", side=WHITE)


@sprite("white_tailed_antelope_squirrel")
def _(s):
    # Cinnamon-gray, white side stripe, and a tail with a bright white underside.
    _ground_squirrel(s, "#b89878", "#f4ece0", tail_col=WHITE, tail_tip="#a08a74", side=WHITE)


@sprite("cliff_chipmunk")
def _(s):
    # A gray chipmunk whose stripes are faint and blurry.
    _chipmunk(s, "#9a948c", "#e8e4dc", "#7a706a", "#c8c2b8", tail_col="#a07a5a")


@sprite("hopi_chipmunk")
def _(s):
    # Bright orange with pale stripes, a red-rock chipmunk.
    _chipmunk(s, "#d88a4a", "#f4e8d4", "#a85a2a", "#f4e4cc", tail_col="#c87a3a")


@sprite("palmers_chipmunk")
def _(s):
    _chipmunk(s, "#9a7a5a", "#ece4d8", "#4a3428", "#e0d4c0", head="#8a7a6c", tail_col="#7a5e48")


@sprite("uinta_chipmunk")
def _(s):
    _chipmunk(s, "#b07a4a", "#f0e8dc", "#3a2a22", WHITE, head="#9a948e", tail_col="#8a6a4a")


@sprite("arizona_gray_squirrel")
def _(s):
    critter(s, "#8e9098", "#f4f2ee", build="squirrel", ear_in="#d6b0a8", tail="squirrel", tail_col="#7a7c84",
            tail_tip=WHITE, markings=lambda s, g: back_stripes(s, g, ["#b0957a"], top=0.2))


@sprite("aberts_squirrel")
def _(s):
    # Tall tufted ears, a rusty stripe down the back and a dark line along the side.
    critter(s, "#6e7078", "#f4f2ee", build="squirrel", ears="tuft", ear_in="#d6b0a8", tail="squirrel",
            tail_col="#5e6068", tail_tip=WHITE,
            markings=lambda s, g: (back_stripes(s, g, ["#9a5a3a"], top=0.1),
                                   back_stripes(s, g, ["#2b2630"], top=g["bry"] * 1.1)))


@sprite("gunnisons_prairie_dog")
def _(s):
    # Like the black-tailed, but its short tail is tipped white and its face darker.
    critter(s, "#c4a072", "#f0e2c8", build="marmot", ear_in="#a87a50", tail="short", tail_col="#c4a072",
            tail_tip="#f4ece0", nose="#5a3a2a", feet="#8a6a4a", eye_ring="#5a4430",
            markings=lambda s, g: flecks(s, g["body"], "#8a6a48", every=7))


@sprite("white_nosed_coati")
def _(s):
    # Long pointed white-tipped snout and a tall striped tail held straight up.
    def tail(s, b):
        m = s.path([(26, 20), (29.5, 15), (30.5, 9), (30, 3)], (1.9, 1.4), "#8a6a48")
        for y in (5, 9, 13, 17):
            s.paint(s.m_line(26, y, 33, y - 1) | s.m_line(26, y + 1, 33, y), "#4a3628", within=m)

    def face(s, b):
        hx, hy = b["head"][:2]
        s.paint(s.m_ellipse(hx - 1.6, hy - 1.4, 1.6, 1.2), "#f4ece0")
        s.paint(s.m_path([(5, 22.5), (1.5, 23.5)], 1.0), "#f4ece0")
    quad(s, "#8a6a48", "#c8ac8c", build="low", ears="small", ear_in="#4a3628", tail="none",
         muzzle="#f4ece0", nose="#2b2226", legs="#4a3628", feet="#2b2226", behind=tail, markings=face)


@sprite("pronghorn")
def _(s):
    # Tan and white, with black pronged horns and white bands on the throat.
    def horns(s, b):
        hx, hy = b["head"][:2]
        for dx, col in ((1.4, "#4a4048"), (0, "#1e1a20")):
            x, y = hx + 0.5 + dx, hy - 2.5
            s.path([(x, y), (x, y - 5), (x + 1.8, y - 7)], 0.7, col, shade=False)
            s.path([(x, y - 3), (x - 1.4, y - 4)], 0.5, col, shade=False)

    def bands(s, b):
        (x0, y0), (x1, y1), r = b["neck"]
        neck = s.m_path([(x0, y0), (x1, y1)], r)
        s.paint(s.m_line(9, 12, 13, 11) | s.m_line(11, 15, 15, 14), WHITE, within=neck)
        bx, by, brx, bry = b["body"]
        s.paint(s.m_ellipse(bx + brx - 1.5, by, 2.2, 3.2), WHITE, within=s.m_ellipse(bx, by, brx, bry))
        hx, hy, hrx, hry = b["head"]
        s.paint(s.m_path([(6.5, 10), (2.6, 11)], 0.8), "#3a2a24")
    quad(s, "#c8884a", WHITE, build="deer", ears="side", ear_in="#f0d0b0", tail="cotton", tail_col=WHITE,
         nose="#2b2226", legs="#c8884a", feet="#2b2226", behind=horns, markings=bands)


# --------------------------------------------------------------------------- birds
def _hummer(s, body, belly, head, crown, throat, *, bill="#2b2630", tail=None):
    """The archetype hummingbird with its body, belly and tail colours free too."""
    s.can("fly")
    down = s.act == "fly" and s.f % 2 == 1
    if down:
        s.ellipse(23, 17, 7, 3, "#cfe8f7", rot=20, shade=False)
    else:
        s.ellipse(22, 9, 7, 3, "#cfe8f7", rot=-35, shade=False)
    s.poly([(18, 20), (24, 28), (20, 29)], tail or mix(body, "#000000", 0.25))
    s.ellipse(16, 18, 5.5, 6.5, body, rot=20)
    s.ellipse(14, 20, 3.5, 4, belly)
    if down:
        s.ellipse(20, 18, 6, 2.6, "#e6f4fc", rot=35, shade=False)
    else:
        s.ellipse(19, 12, 6, 2.6, "#e6f4fc", rot=-55, shade=False)
    s.ellipse(12, 11, 5.2, 5, head, edge=True)
    s.paint(s.m_ellipse(13.5, 8.3, 4, 2.3), crown, within=s.last)
    if throat:
        s.paint(s.m_ellipse(11, 14.5, 3.5, 2), throat, within=s.last)
    s.line(4, 12, 0, 13, bill)
    s.px([(5, 12)], bill)
    s.line(7, 11, 1, 13, bill)
    s.px([(0, 13)], "#2b2630")
    s.eye(10, 9)
    s.px([(10, 9)], WHITE)


@sprite("broad_billed_hummingbird")
def _(s):
    # Dark green with a sapphire-blue throat and a bright red bill.
    _hummer(s, "#2a7a5a", "#3a8a6a", "#2a7a5a", "#2a6a50", "#2a6ae0", bill="#e8402a", tail="#2a3440")


@sprite("costas_hummingbird")
def _(s):
    # A violet cap and a violet gorget flaring out at the sides.
    _hummer(s, "#6aa56e", "#e8ece0", "#7a3aa8", "#7a3aa8", "#8a3ac0")
    s.paint(s.m_ellipse(13, 15.5, 2, 2.6, rot=-30), "#8a3ac0")
    s.paint(s.m_line(10, 11, 13, 11), WHITE, within=s.m_ellipse(12, 11, 5.2, 5))


@sprite("black_chinned_hummingbird")
def _(s):
    # A black chin over a thin band of glittering purple.
    _hummer(s, "#6a9a6e", "#e8ece4", "#4a7a5a", "#4a7a5a", "#1e1a24")
    s.paint(s.m_ellipse(11, 16, 3.2, 0.9), "#7a3ad0", within=s.m_ellipse(12, 11, 5.2, 5))


@sprite("rivolis_hummingbird")
def _(s):
    # Big and dark: a violet crown, a green throat and a blackish belly.
    _hummer(s, "#2a4a3a", "#1e2a24", "#1e2a24", "#8a3ad8", "#3ad88a")
    s.px([(12, 8), (11, 9)], WHITE)


@sprite("gambels_quail")
def _(s):
    def face(s):
        h = s.last
        s.paint(s.m_ellipse(9, 15, 4, 2.6), BLACK, within=h)
        s.paint(s.m_poly([(5, 13), (12, 12), (13, 13), (6, 14)]), WHITE, within=h)
        s.paint(s.m_ellipse(12, 6.5, 4.5, 2.4), "#b8502a", within=h)
        s.paint(s.m_line(7, 8, 14, 8), WHITE, within=h)

    def belly(s, m):
        s.paint(s.m_ellipse(14.5, 25, 3, 1.8), BLACK, within=m)

    def flank(s, m):
        s.paint(s.m_ellipse(20, 21, 4.5, 2.2, rot=-15), "#a8502a", within=m)
        s.paint(s.m_line(17, 20, 22, 19) | s.m_line(18, 22, 23, 21), WHITE, within=m)
    bird(s, "#7a8090", "#efe0b8", head="#7a8090", wing="#8a8478", tail="short", crest="quail",
         face=face, belly_mark=belly, wing_mark=flank, beak="cone", beak_col=BLACK)


@sprite("gila_woodpecker")
def _(s):
    # Plain tan head and front, a zebra-barred back and (the male) a small red cap.
    def bars(s, m):
        for x in (16, 18, 20, 22, 24):
            s.paint(s.m_line(x, 15, x, 23), WHITE, within=m)

    def cap(s):
        s.paint(s.m_ellipse(12, 6.5, 2.4, 1.6), "#e0302a", within=s.last)
    bird(s, "#c4ae8a", "#d8c8a8", head="#c8b490", wing="#2b2630", tail_col="#2b2630", beak="crow",
         beak_col="#2b2630", legs="#6a6a70", tail="short", face=cap, wing_mark=bars)


@sprite("ladder_backed_woodpecker")
def _(s):
    # Black-and-white ladder back, a red crown and a striped face.
    def bars(s, m):
        for x in (16, 18, 20, 22, 24):
            s.paint(s.m_line(x, 15, x, 23), WHITE, within=m)

    def face(s):
        h = s.last
        s.paint(s.m_ellipse(12, 6.5, 5, 2.6), "#d82a2a", within=h)
        s.paint(s.m_line(9, 11, 16, 11) | s.m_line(6, 14, 14, 13), BLACK, within=h)
        s.paint(s.m_line(13, 9, 16, 15), BLACK, within=h)

    def spots(s, m):
        s.paint(s.m_px([(11, 22), (14, 21), (13, 24), (16, 23), (10, 25)]), BLACK, within=m)
    bird(s, BLACK, "#ece4d4", head="#f0eae0", wing=BLACK, tail_col=BLACK, beak="crow", beak_col="#3a3438",
         legs="#6a6a70", tail="short", face=face, wing_mark=bars, belly_mark=spots)


@sprite("vermilion_flycatcher")
def _(s):
    # Blazing red with a dark brown mask, back and wings.
    def face(s):
        s.paint(s.m_line(4, 11, 16, 11) | s.m_line(5, 10, 16, 10), "#4a3a34", within=s.last)
        s.paint(s.m_ellipse(16, 11, 2, 3), "#4a3a34", within=s.last)
    bird(s, "#e0302a", "#ee3a2a", head="#e83228", wing="#4a3a34", tail_col="#3a2e2a", beak="thin",
         beak_col="#1e1a20", legs="#2b2630", tail="mid", face=face)


@sprite("curve_billed_thrasher")
def _(s):
    # Gray-brown with a long down-curved bill, faint spots and a fierce orange eye.
    def spots(s, m):
        s.paint(s.m_px([(10, 21), (13, 20), (12, 23), (15, 22), (10, 24), (16, 25)]), "#8a7e70", within=m)
    bird(s, "#8a7e72", "#cec2b0", head="#857a6e", wing="#7a6e62", tail_col="#6a6058", beak="thin",
         beak_col="#2b2630", legs="#4a4440", tail="long", belly_mark=spots, eye_col="#e87a1e")
    s.path([(6, 11.5), (2, 12.5), (0, 15)], (0.9, 0.5), "#2b2630", shade=False)
    s.px([(8, 10)], "#f0a030")


@sprite("cactus_wren")
def _(s):
    # Bold white eyebrow, rusty cap, heavily spotted chest and a barred tail.
    def face(s):
        h = s.last
        s.paint(s.m_ellipse(12.5, 6.5, 4.5, 2.4), "#8a4a2a", within=h)
        s.paint(s.m_line(6, 8, 16, 9), WHITE, within=h)

    def spots(s, m):
        s.paint(s.m_px([(9, 20), (11, 19), (13, 20), (10, 22), (12, 21), (14, 22), (9, 24), (11, 23),
                        (13, 24), (15, 24), (16, 21)]), "#2b2226", within=m)

    def wing(s, m):
        s.paint(s.m_px([(17, 17), (19, 19), (21, 17), (23, 19), (20, 21), (18, 21)]), WHITE, within=m)
    bird(s, "#7a5a3e", "#f2e8d8", head="#6a4a32", wing="#6a4c34", tail_col="#5a4030", beak="thin",
         beak_col="#3a3034", legs="#a08070", tail="mid", face=face, belly_mark=spots, wing_mark=wing)
    s.paint(s.m_line(24, 16, 27, 14) | s.m_line(25, 18, 29, 15), "#2b2226")


@sprite("lesser_goldfinch")
def _(s):
    # Bright yellow below, olive back, black cap and black wings with a white flash.
    def cap(s):
        s.paint(s.m_ellipse(11, 6.5, 5, 3), BLACK, within=s.last)

    def wing(s, m):
        s.paint(s.m_ellipse(19, 20, 2, 1.2), WHITE, within=m)
    bird(s, "#7a8a2a", "#f2d828", head="#7a8a2a", wing="#24222a", tail_col="#24222a", beak="cone",
         beak_col="#5a5a60", legs="#8a7a70", tail="mid", face=cap, wing_mark=wing)


@sprite("verdin")
def _(s):
    # A tiny gray bird with a yellow head and a chestnut shoulder spot.
    def wing(s, m):
        s.paint(s.m_ellipse(16, 18, 1.6, 1.2), "#b0402a", within=m)
    bird(s, "#8e8e8a", "#d0d0ca", head="#f0d020", wing="#7e7e7a", tail_col="#6e6e6a", beak="thin",
         beak_col="#2b2630", legs="#4a4a50", tail="mid", wing_mark=wing)


@sprite("phainopepla")
def _(s):
    # Silky glossy black with a tall crest and a red eye; white wing patches flash in flight.
    def wing(s, m):
        s.paint(s.m_ellipse(20, 19, 2, 1.2), "#d8d8e0", within=m)
    bird(s, "#1e1c2a", "#262434", head="#1e1c2a", wing="#16141e", tail_col="#16141e", beak="thin",
         beak_col="#16141e", legs="#2b2630", tail="long", crest="jay", eye_col="#d8202a", wing_mark=wing)
    s.paint(s.m_ellipse(14, 9, 2, 1.2), "#3a3a5a")


@sprite("black_throated_sparrow")
def _(s):
    # Neat gray with a black bib and bold white eyebrow and whisker.
    def face(s):
        h = s.last
        s.paint(s.m_ellipse(8, 15, 3.5, 2.5), BLACK, within=h)
        s.paint(s.m_line(6, 8, 15, 8), WHITE, within=h)
        s.paint(s.m_line(5, 13, 12, 13), WHITE, within=h)
    bird(s, "#8a8478", "#eeeae2", head="#7a7c80", wing="#8a7a6a", tail_col="#2b2630", beak="cone",
         beak_col="#3a3a42", legs="#6a6060", tail="mid", face=face)
    s.paint(s.m_ellipse(10, 18.5, 3, 1.6), BLACK)


@sprite("aberts_towhee")
def _(s):
    # Plain warm brown with a black face around the bill.
    def face(s):
        s.paint(s.m_ellipse(5.5, 12, 2.6, 2.8), "#2b2226", within=s.last)
    bird(s, "#a08068", "#c4a48a", head="#9a7a62", wing="#8e7058", tail_col="#7a5e4a", beak="cone",
         beak_col="#c8b8a0", legs="#a88a74", tail="long", face=face)
    s.paint(s.m_ellipse(15, 27, 4, 1.5), "#d0844a")


@sprite("canyon_towhee")
def _(s):
    # Gray-brown with a rusty cap and a buff throat with a dark spot.
    def face(s):
        h = s.last
        s.paint(s.m_ellipse(12, 6.5, 5, 2.5), "#b0603a", within=h)
        s.paint(s.m_ellipse(8, 15, 2.6, 1.4), "#e8d0aa", within=h)
    bird(s, "#9a8e80", "#cbbfae", head="#9a8e80", wing="#8a7e70", tail_col="#7a6e62", beak="cone",
         beak_col="#8a8078", legs="#a88a74", tail="long", face=face)
    s.px([(10, 19), (11, 19)], "#4a3a30")
    s.paint(s.m_ellipse(15, 27, 4, 1.5), "#d0905a")


@sprite("mexican_jay")
def _(s):
    # A crestless blue jay: blue head and wings, gray back, pale gray front.
    bird(s, "#6a84b8", "#c8ccd4", head="#5a7ac0", wing="#4a6ab8", tail_col="#4a6ab8", beak="crow",
         beak_col="#1e1a20", legs="#2b2630", tail="long", big=True)
    s.paint(s.m_ellipse(9, 14.5, 3, 1.4), "#b8c0cc", within=s.m_ellipse(11, 11, 6.5, 6))


@sprite("says_phoebe")
def _(s):
    # Soft gray-brown with a warm cinnamon belly and a black tail.
    bird(s, "#8a8076", "#d8946a", head="#7a7068", wing="#6e6660", tail_col="#2b2630", beak="thin",
         beak_col="#1e1a20", legs="#2b2630", tail="mid")


@sprite("eurasian_collared_dove")
def _(s):
    # Pale sandy-gray dove with a thin black half collar on the back of the neck.
    def face(s):
        s.paint(s.m_line(12, 15, 16, 13) | s.m_line(12, 16, 16, 14), BLACK, within=s.last)
        s.paint(s.m_line(12, 14, 16, 12), WHITE, within=s.last)

    def wing(s, m):
        s.paint(s.m_ellipse(25, 17, 2.4, 1.6), "#6a6460", within=m)
    bird(s, "#d6cabc", "#e8dcd2", head="#ddd2c6", wing="#cabdb0", tail_col="#b8ab9e", beak="thin",
         beak_col="#2b2630", legs="#d88a8a", tail="long", face=face, wing_mark=wing, eye_col="#a0202a")


@sprite("black_headed_grosbeak")
def _(s):
    # Black head, cinnamon-orange chest and collar, black-and-white wings, a big pale bill.
    def wing(s, m):
        s.paint(s.m_line(16, 18, 23, 16) | s.m_px([(18, 21), (21, 20), (24, 19)]), WHITE, within=m)

    def collar(s):
        s.paint(s.m_ellipse(14.5, 15, 2, 2), "#e08a2a", within=s.last)
    bird(s, "#2b2630", "#e8902a", head="#1e1a20", wing="#24202a", tail_col="#1e1a20", beak="cone",
         beak_col="#d8ccb8", legs="#7a7a84", tail="mid", wing_mark=wing, face=collar)
    s.poly([(6, 9.5), (1.5, 11.8), (6, 14)], "#d8ccb8")
    s.px([(5, 12)], "#a8988a")


@sprite("lazuli_bunting")
def _(s):
    # Sky-blue head and back, an orange chest band, white belly and white wing bars.
    def chest(s, m):
        s.paint(s.m_ellipse(11, 19.5, 4, 2), "#e8984a", within=m)

    def wing(s, m):
        s.paint(s.m_line(16, 18, 23, 16) | s.m_line(17, 21, 23, 19), WHITE, within=m)
    bird(s, "#3a8ad8", "#f4f0e8", head="#4a9ae0", wing="#2a5a9a", tail_col="#2a4a7a", beak="cone",
         beak_col="#5a6a7a", legs="#5a5a62", tail="mid", belly_mark=chest, wing_mark=wing)


@sprite("california_gull")
def _(s):
    # Medium gray back, black wingtips, and a yellow bill with a red and a black spot.
    def wing(s, m):
        s.paint(s.m_px([(24, 17), (25, 17), (25, 18)]), WHITE, within=m)
        s.paint(s.m_poly([(23, 15), (27, 14), (27, 19), (23, 19)]), "#2b2630", within=m)
    bird(s, WHITE, WHITE, head=WHITE, wing="#9a9eaa", tail_col=WHITE, beak="crow", beak_col="#f0d030",
         legs="#c8cc4a", tail="short", wing_mark=wing, big=True)
    s.px([(3, 13)], "#e0403a")
    s.px([(2, 12)], BLACK)


@sprite("white_faced_ibis")
def _(s):
    # Glossy maroon and bronze, a curved bill, red legs and a thin white edge to the face.
    wader(s, "#6a3a3a", neck="#7a3a34", head="#7a3a34", beak="#9a7a70", legs="#c84a4a", wing="#3a5a4a",
          curved=True, face="#c84a5a")
    s.paint(s.m_ellipse(8, 5, 3, 3) & ~s.m_ellipse(8, 5, 2, 2), WHITE, within=s.m_ellipse(10.5, 5, 4, 3.4))
    s.px([(8, 4)], "#d8202a")


@sprite("ruddy_duck")
def _(s):
    # Chestnut body, black cap, big white cheek, sky-blue bill and a stiff upright tail.
    s.poly([(24, 20), (27, 9), (30, 10), (28, 21)], "#3a2a24")
    duck(s, "#a84a2a", "#b0502e", "#2b2226", bill="#4a9ae0", ring=None, speculum="#a84a2a", tail_col="#3a2a24")
    s.paint(s.m_ellipse(9.5, 13.5, 4.5, 2.6), WHITE, within=s.m_ellipse(10, 11, 6, 5.5))
    s.eye(7, 10)


@sprite("cinnamon_teal")
def _(s):
    # Rich cinnamon-red all over with a red eye and a blue wing patch.
    duck(s, "#b0482a", "#b8502e", "#a8402a", bill="#2b2630", ring=None, speculum="#6a9ae0", tail_col="#5a3a2a")
    s.eye(7, 10, color="#d82a2a")


# --------------------------------------------------------------------------- reptiles
def _blue_belly(s, m, col="#3a6ad8"):
    s.paint(s.m_ellipse(14, 24.6, 3.5, 1.2), col, within=m)


@sprite("ornate_tree_lizard")
def _(s):
    # Slim and gray with dark crossbands, a blue belly patch and a yellow throat.
    def pat(s, m):
        for x in (10, 13, 16, 19):
            s.paint(s.m_line(x, 19, x + 1, 23), "#3a3a3a", within=m)
        _blue_belly(s, m)
    lizard(s, "#8a8478", "#d8d4c8", throat="#e8c84a", pattern=pat, tail_col="#7a7468",
           tail_pts=[(20, 22), (27, 25), (32, 24), (35, 19)])


@sprite("yarrows_spiny_lizard")
def _(s):
    # Dark and spiny with a black collar edged in white and a blue belly.
    def pat(s, m):
        s.paint(s.m_px([(10, 20), (13, 19), (16, 20), (19, 19), (12, 21), (18, 21)]), "#8a8a7a", within=m)
        _blue_belly(s, m)
    lizard(s, "#3e3a34", "#8aa0c0", throat="#4a7ad8", pattern=pat, wide=True, horns=True)
    s.paint(s.m_line(11, 16, 11, 22), BLACK)
    s.paint(s.m_line(10, 16, 10, 22) | s.m_line(12, 17, 12, 22), "#f0ece0")


@sprite("clarks_spiny_lizard")
def _(s):
    # Big, spiny, blue-green, with black bars across its forearms.
    def pat(s, m):
        s.paint(s.m_px([(10, 20), (13, 19), (16, 20), (19, 19), (12, 21), (18, 21)]), "#5a8a8a", within=m)
        _blue_belly(s, m)
    lizard(s, "#7a9a88", "#c8d8d0", throat="#4a7ad8", pattern=pat, wide=True, horns=True)
    s.paint(s.m_line(9, 25, 11, 25) | s.m_line(10, 27, 12, 27), "#1e1a20")


@sprite("southwestern_fence_lizard")
def _(s):
    # Brown with dark chevrons down the back and bright blue belly patches.
    def pat(s, m):
        for x in (10, 14, 18):
            s.paint(s.m_path([(x, 19), (x + 1.5, 20.5), (x + 3, 19)], 0.5), "#3a2e26", within=m)
        _blue_belly(s, m)
    lizard(s, "#8a7058", "#d8ccb8", throat="#4a7ad8", pattern=pat)


@sprite("plateau_fence_lizard")
def _(s):
    # Brown with two pale stripes down the back and blue belly patches.
    def pat(s, m):
        s.paint(s.m_line(8, 19, 22, 19), "#e8dcc0", within=m)
        s.paint(s.m_px([(11, 20), (15, 20), (19, 20)]), "#4a3a2a", within=m)
        _blue_belly(s, m)
    lizard(s, "#9a7a58", "#e0d4c0", throat="#4a7ad8", pattern=pat)
    s.paint(s.m_line(4, 17, 10, 17), "#e8dcc0", within=s.m_ellipse(7.5, 18.5, 5.2, 3.8))


@sprite("zebra_tailed_lizard")
def _(s):
    # Pale gray, two black bars on the side, and a curled tail with zebra stripes.
    def pat(s, m):
        s.paint(s.m_line(14, 21, 13, 25) | s.m_line(16, 21, 15, 25), BLACK, within=m)
        s.paint(s.m_px([(10, 20), (13, 19), (17, 19), (20, 20), (11, 22)]), "#e8d888", within=m)
    lizard(s, "#bab4a6", "#f4f2ec", pattern=pat, tail_col="#e8e4dc", smooth=True,
           tail_pts=[(20, 22), (27, 25), (31, 22), (31, 15)])
    tail = s.m_path([(20, 22), (27, 25), (31, 22), (31, 15)], (2.6, 0.9))
    for y in (16, 19):
        s.paint(s.m_line(28, y, 34, y), BLACK, within=tail)
    for x in (24, 27):
        s.paint(s.m_line(x, 21, x, 28), BLACK, within=tail)


@sprite("greater_earless_lizard")
def _(s):
    # Sandy and speckled with yellow-orange flanks crossed by two black bars.
    def pat(s, m):
        s.paint(s.m_ellipse(15, 23, 4.5, 1.6), "#f0b040", within=m)
        s.paint(s.m_line(14, 21, 13, 25) | s.m_line(17, 21, 16, 25), BLACK, within=m)
        s.paint(s.m_px([(9, 19), (12, 20), (16, 19), (20, 20), (22, 21)]), "#f0ece0", within=m)
    lizard(s, "#b8a080", "#f0ece0", pattern=pat, smooth=True, wide=True)
    tail = s.m_path([(20, 22), (26, 25), (30, 22), (30, 16)], (2.4, 0.7))
    for x, y in ((24, 25), (28, 24)):
        s.paint(s.m_line(x, y - 1, x, y + 2), BLACK, within=tail)


def _whiptail(s, body, belly, stripe, spot, tail_col, throat=None):
    def pat(s, m):
        for y in (19, 21, 23):
            s.paint(s.m_line(9, y, 22, y), stripe, within=m)
        if spot:
            s.paint(s.m_px([(10, 20), (13, 22), (16, 20), (19, 22), (21, 20), (12, 20)]), spot, within=m)
    lizard(s, body, belly, throat=throat or belly, pattern=pat, tail_col=tail_col,
           tail_pts=[(20, 22), (27, 25), (33, 24), (36, 19)])
    s.paint(s.m_line(4, 17, 10, 17), stripe, within=s.m_ellipse(7.5, 18.5, 5.2, 3.8))


@sprite("western_whiptail")
def _(s):
    # Gray-tan, checkered with dark spots, faint stripes and a long gray tail.
    _whiptail(s, "#9a8a70", "#e8e4dc", "#c8bca0", "#3a2e24", "#8a8478")


@sprite("sonoran_spotted_whiptail")
def _(s):
    # Dark brown with six yellow stripes, pale spots and a greenish tail.
    _whiptail(s, "#4a3a2a", "#f0f0e0", "#e8d870", "#f0e8b0", "#7a9a6a")


@sprite("chihuahuan_spotted_whiptail")
def _(s):
    # Brown with cream stripes and spots, a bluish throat and a brownish tail.
    _whiptail(s, "#6a4e36", "#dce4ec", "#e8dcc0", "#f8f0d8", "#a07a5a", throat="#8aa8d8")


def _horned(s, body, belly, *, spots, edge, tail_pts, stripe=None):
    def pat(s, m):
        for x, y in spots:
            s.paint(s.m_ellipse(x, y, 1.6, 1.2), "#4a3428", within=m)
            s.paint(s.m_line(x - 1, y + 1.5, x + 1, y + 1.5), edge, within=m)
        if stripe:
            s.paint(s.m_line(9, 18, 22, 18), stripe, within=m)
        s.paint(s.m_px([(8, 19), (12, 19), (16, 19), (20, 19)]), mix(body, WHITE, 0.4), within=m)
    lizard(s, body, belly, pattern=pat, horns=True, wide=True, tail_pts=tail_pts)
    # a fringe of side spines
    s.px([(9, 25), (12, 26), (15, 26), (18, 26), (21, 25)], mix(body, WHITE, 0.45))


@sprite("texas_horned_lizard")
def _(s):
    # Long horns, dark spots edged in white, and a pale stripe down the back.
    _horned(s, "#b88a5e", "#ecdcc0", spots=[(12, 20), (17, 20), (21, 21)], edge="#f4ece0",
            tail_pts=[(21, 23), (25, 25), (28, 25)], stripe="#e8d4a8")
    s.px([(8, 13), (10, 13), (12, 14), (7, 13)], "#f0e4c8")


@sprite("greater_short_horned_lizard")
def _(s):
    # Round as a pancake, with tiny stubby horns.
    def pat(s, m):
        for x, y in ((12, 20), (17, 20)):
            s.paint(s.m_ellipse(x, y, 1.6, 1.2), "#4a3e34", within=m)
        s.paint(s.m_px([(9, 19), (13, 18), (16, 18), (20, 19), (14, 22)]), "#d8ccb4", within=m)
    lizard(s, "#9a8c7a", "#e8e0d0", pattern=pat, wide=True, tail_pts=[(21, 23), (25, 25), (27, 25)])
    s.px([(9, 14), (11, 14), (12, 15)], "#d8ccb4")
    s.px([(9, 25), (12, 26), (15, 26), (18, 26), (21, 25)], "#d8ccb4")


@sprite("roundtail_horned_lizard")
def _(s):
    # Small and gray-pink with dark blotches and a thin round tail.
    _horned(s, "#b8a094", "#ece4dc", spots=[(11, 20), (15, 21), (19, 20)], edge="#e8dcd4",
            tail_pts=[(21, 23), (26, 25), (29, 23)])


@sprite("desert_collared_lizard")
def _(s):
    # A big-headed lizard with two black collars and pale spots on its back.
    def pat(s, m):
        s.paint(s.m_px([(14, 19), (17, 20), (20, 19), (15, 22), (19, 22), (22, 21)]), "#f0e8c8", within=m)
    lizard(s, "#8a8a5a", "#e8e4cc", head="#a89a6a", pattern=pat, tail_col="#9a8a5a",
           tail_pts=[(20, 22), (27, 25), (33, 24), (35, 18)])
    s.paint(s.m_line(11, 16, 11, 23) | s.m_line(13, 17, 13, 24), BLACK)
    s.paint(s.m_line(12, 17, 12, 23), "#f4f0e0")


@sprite("common_chuckwalla")
def _(s):
    # A big, fat, flat lizard: black front and a thick orange tail.
    lizard(s, "#2e2a2c", "#5a4e48", head="#2e2a2c", tail_col="#e09048", wide=True,
           tail_pts=[(20, 23), (26, 26), (31, 25), (33, 21)])
    s.path([(19, 23), (25, 25.5)], (3.2, 2.4), "#d88a44")
    s.paint(s.m_ellipse(20, 21, 4, 3.6), "#c87a3e", within=s.m_ellipse(15, 22, 7.5, 4.3))
    s.paint(s.m_px([(9, 20), (12, 19), (15, 21), (8, 22)]), "#4a4246", within=s.m_ellipse(15, 22, 7.5, 4.3))


# --------------------------------------------------------------------------- amphibians
@sprite("sonoran_desert_toad")
def _(s):
    # Huge, smooth and olive, with long glands behind the eyes and a white wart at each jaw.
    frog(s, "#6a6e3e", "#ece4cc", spots=[(13, 21), (19, 21), (16, 24)])
    s.paint(s.m_ellipse(5, 15, 3, 1.5, rot=-20) | s.m_ellipse(27, 15, 3, 1.5, rot=20), "#8a8a52")
    s.px([(3, 18), (28, 18)], "#f8f4ea")


@sprite("red_spotted_toad")
def _(s):
    # A small flat gray toad sprinkled with red-orange warts.
    frog(s, "#9a948a", "#ece8e0")
    s.paint(s.m_px([(10, 20), (13, 18), (19, 18), (22, 20), (16, 22), (12, 24), (20, 24), (8, 24), (24, 23),
                    (14, 13), (18, 13)]), "#e05a3a")


@sprite("couchs_spadefoot")
def _(s):
    # Bright yellow-green with dark blotches and gold cat-like eyes.
    frog(s, "#b8c050", "#f4f0dc")
    s.paint(s.m_ellipse(12, 20, 2, 1.5) | s.m_ellipse(20, 21, 2.2, 1.5) | s.m_ellipse(16, 24, 1.8, 1.3)
            | s.m_ellipse(9, 24, 1.5, 1.2) | s.m_ellipse(23, 24, 1.5, 1.2) | s.m_ellipse(16, 13, 2, 1.2), "#4a4a24")
    s.px([(9, 11), (10, 11), (11, 11), (21, 11), (22, 11), (23, 11)], "#d8b030")


@sprite("canyon_tree_frog")
def _(s):
    # Rock-colored and blotchy, with toe pads for climbing canyon walls.
    frog(s, "#a49a88", "#f0ece0", pads=True,
         spots=[(11, 20), (14, 22), (18, 19), (21, 22), (16, 25), (9, 24), (23, 25), (13, 18)])
    s.paint(s.m_ellipse(14, 21, 1.6, 1.2) | s.m_ellipse(20, 23, 1.6, 1.2), "#6a7a5a")


@sprite("woodhouses_toad")
def _(s):
    # Brown and warty with a pale stripe down the middle of the back.
    frog(s, "#9a7e5a", "#f0e8d4", spots=[(10, 20), (13, 22), (19, 21), (22, 23), (12, 25), (20, 25), (8, 24)])
    s.paint(s.m_line(16, 12, 16, 27), "#ecdcb4")
    s.paint(s.m_ellipse(5, 14, 2, 1.4) | s.m_ellipse(27, 14, 2, 1.4), "#7a6040")


@sprite("great_plains_toad")
def _(s):
    # Big dark green-gray blotches, each outlined in pale cream.
    frog(s, "#c8c0a4", "#f4f0e4")
    for x, y in ((11, 20), (20, 20), (12, 25), (19, 25), (16, 14)):
        s.paint(s.m_ellipse(x, y, 2.4, 1.8), "#f4f0e0")
        s.paint(s.m_ellipse(x, y, 1.7, 1.2), "#5a6a4a")


@sprite("chiricahua_leopard_frog")
def _(s):
    # Green-brown with many small dark spots and tiny raised bumps.
    frog(s, "#7a8a4a", "#f0ecd8", tympanum="#8a7a4a",
         spots=[(10, 20), (12, 22), (14, 19), (17, 21), (20, 19), (22, 22), (11, 25), (15, 25), (19, 24),
                (23, 25), (8, 23), (16, 17)])
    s.px([(13, 21), (18, 23), (21, 20)], "#a8b06a")


@sprite("relict_leopard_frog")
def _(s):
    # A plain olive-brown leopard frog with faint, fuzzy spots.
    frog(s, "#8a7a52", "#f0ecd8", tympanum="#7a6a42", spots=[(12, 20), (19, 21), (15, 24), (22, 24)])
    s.paint(s.m_line(9, 17, 12, 27) | s.m_line(23, 17, 20, 27), "#a08e60")


@sprite("chihuahuan_green_toad")
def _(s):
    # Small, bright green, laced with a black network.
    frog(s, "#7ab83a", "#f0f0dc")
    net = (s.m_line(9, 19, 14, 22) | s.m_line(14, 22, 20, 19) | s.m_line(20, 19, 24, 23)
           | s.m_line(14, 22, 13, 27) | s.m_line(20, 19, 19, 26) | s.m_line(12, 14, 20, 14)
           | s.m_line(9, 19, 7, 24))
    s.paint(net, "#1e2a14", within=s.m_ellipse(16, 22, 9.5, 7) | s.m_ellipse(16, 15, 11, 6.5))


@sprite("arizona_toad")
def _(s):
    # Pale and plain, pinkish tan with a light band between the eyes and few warts.
    frog(s, "#c8ae8a", "#f6f0e4", spots=[(12, 21), (20, 21), (16, 24)])
    s.paint(s.m_line(12, 12, 20, 12) | s.m_line(12, 13, 20, 13), "#ecdcc0")


@sprite("great_basin_spadefoot")
def _(s):
    # Gray-olive with pale stripes making an hourglass, and cat-like eyes.
    frog(s, "#8a8a6a", "#f0ece0")
    s.paint(s.m_line(10, 17, 14, 22) | s.m_line(14, 22, 10, 27) | s.m_line(22, 17, 18, 22)
            | s.m_line(18, 22, 22, 27), "#c8c4a0")
    s.px([(9, 11), (10, 11), (11, 11), (21, 11), (22, 11), (23, 11)], "#d8b030")


@sprite("amargosa_toad")
def _(s):
    # Olive with dark spots and a pale stripe down the back, found in one desert river.
    frog(s, "#8a8a5a", "#f0ecd8", spots=[(10, 20), (13, 23), (19, 20), (22, 23), (12, 26), (20, 26)])
    s.paint(s.m_line(16, 14, 16, 26), "#e0dcb0")
    s.paint(s.m_ellipse(11, 21, 1.2, 1.2) | s.m_ellipse(21, 21, 1.2, 1.2), "#3a3a24")


# --------------------------------------------------------------------------- insects and other small animals
@sprite("white_lined_sphinx")
def _(s):
    # A fat-bodied moth: brown forewings slashed with white, pink hindwings.
    def pat(s, fm, hm):
        s.paint(s.m_line(13, 13, 3, 5) | s.m_line(12, 13, 2, 6), "#f4ecd8", mirror=True, within=fm)
        s.paint(s.m_line(5, 9, 8, 13) | s.m_line(9, 8, 11, 13), "#f4ecd8", mirror=True, within=fm)
        s.paint(s.m_poly([(4, 22), (9, 27), (15, 22), (15, 21), (9, 25), (5, 21)]), "#3a2a24", mirror=True,
                within=hm)
        s.paint(s.m_ellipse(14, 18, 2, 2), "#3a2a24", mirror=True, within=hm)
    butterfly(s, "#6a5a3a", "#e87a8a", body="#6a5a3a", pattern=pat)
    m = s.ellipse(16, 18, 2.6, 8, "#7a6a4a", edge=True)
    for y in (16, 19, 22):
        s.paint(s.m_line(14, y, 18, y), "#f4ecd8", within=m)
    s.ellipse(16, 9.5, 2.6, 2.3, "#7a6a4a")
    s.px([(14, 9), (17, 9)], WHITE)


@sprite("american_snout")
def _(s):
    # Brown wings with orange patches, white spots near the tips, and a long beak-like snout.
    def pat(s, fm, hm):
        s.paint(s.m_ellipse(10, 12, 3, 2.2), "#e8902a", mirror=True, within=fm)
        s.paint(s.m_px([(4, 6), (6, 5), (5, 8)]), WHITE, mirror=True, within=fm)
        s.paint(s.m_ellipse(11, 19, 3, 2.6), "#e8902a", mirror=True, within=hm)
    butterfly(s, "#5a3e2a", "#5a3e2a", body="#4a3424", pattern=pat)
    s.path([(16, 8), (16, 3)], (1.2, 0.6), "#7a5a3a")


@sprite("marine_blue")
def _(s):
    # Lavender-blue with fine brown wavy bands and two dark eyespots on each hindwing.
    def pat(s, fm, hm):
        s.paint(s.m_line(3, 8, 12, 14) | s.m_line(4, 12, 12, 16) | s.m_line(5, 19, 12, 23), "#8a7a8a",
                mirror=True, within=fm | hm)
        s.paint(s.m_poly([(1.5, 6), (5, 3), (5, 5), (2.5, 14)]), "#5a4a5a", mirror=True, within=fm)
        s.paint(s.m_px([(7, 25), (9, 26)]), BLACK, mirror=True, within=hm)
    butterfly(s, "#a08ad0", "#a890d0", body="#4a3e5a", pattern=pat, tails=True)


@sprite("desert_blonde_tarantula")
def _(s):
    # A big, furry spider: golden-blonde front, dark legs and a dark rusty-haired rear.
    def pat(s, m):
        s.paint(s.m_px([(13, 18), (19, 18), (12, 22), (20, 22), (14, 25), (18, 25), (16, 20), (16, 27)]),
                "#a8603a", within=m)
    spider_top(s, "#3a2a24", "#3a2c26", pattern=pat, ceph="#dcbc7a", leg_bands="#c8a060")
    s.path([(14, 11), (13, 13)], 0.7, "#c8a868", shade=False)
    s.path([(18, 11), (19, 13)], 0.7, "#c8a868", shade=False)


@sprite("stripe_tailed_scorpion")
def _(s):
    # Straw-yellow with dark stripes down the curled tail, pincers out front.
    s.can("walk")
    w = s.wave() if s.act == "walk" else 0
    body, dark = "#d8b860", "#6a5030"
    for i, x in enumerate((12, 15, 18, 21)):
        d = w * 1.2 * (1 if i % 2 else -1)
        s.path([(x, 24), (x - 2 + d, 27), (x - 3 + d, 30)], 0.55, mix(body, "#000000", 0.2), shade=False)
    tail = s.path([(22, 23), (27, 22), (30, 17), (29, 11), (25, 8)], (2.0, 1.3), body)
    s.paint(s.m_path([(22, 23.6), (27, 22.6), (30.6, 17), (29.6, 11), (25, 8.6)], 0.45), dark, within=tail)
    for x, y in ((25, 22), (29, 19), (30, 14), (28, 10)):
        s.px([(x, y)], mix(body, "#000000", 0.35))
    s.poly([(25, 7), (21, 8), (23, 10.5)], "#9a6a30")
    s.px([(20, 9)], "#3a2a20")
    s.path([(10, 22), (6, 20), (5, 17)], 0.9, body)
    s.ellipse(4, 15, 2.6, 2, body, rot=-30, edge=True)
    s.paint(s.m_line(1, 13, 3, 14), dark)
    m = s.ellipse(16, 22.5, 7.5, 3.6, body, edge=True)
    for x in (14, 17, 20):
        s.paint(s.m_line(x, 19, x, 26), mix(body, "#000000", 0.2), within=m)
    s.ellipse(9.5, 22.5, 3.6, 3.2, mix(body, "#000000", 0.1), edge=True)
    s.eye(8, 21)
    s.blush(9, 24)
    if s.act == "walk" and s.f % 2:
        s.shift(-1, 0)


@sprite("empress_leilia")
def _(s):
    # Orange-brown hackberry butterfly with dark spots and black eyespots on each hindwing.
    def pat(s, fm, hm):
        s.paint(s.m_poly([(1.5, 6), (5, 3), (6, 5), (2, 9)]), "#4a3020", mirror=True, within=fm)
        s.paint(s.m_ellipse(9, 9, 1.4, 1.2) | s.m_ellipse(6, 11, 1.2, 1.2), "#3a2418", mirror=True, within=fm)
        s.paint(s.m_px([(4, 6), (6, 7)]), WHITE, mirror=True, within=fm)
        for x, y in ((7, 22), (10, 24)):
            s.paint(s.m_ellipse(x, y, 1.4, 1.4), BLACK, mirror=True, within=hm)
            s.px([(x, y)], "#4a7ad8")
            s.px([(31 - x, y)], "#4a7ad8")
    butterfly(s, "#c07a3a", "#b8723a", body="#5a3e2a", pattern=pat)


@sprite("pallid_winged_grasshopper")
def _(s):
    # Mottled gray-brown, perfect desert-dirt camouflage.
    grasshopper(s, "#a8987e", "#7a6a54", legs="#9a8a70")
    s.paint(s.m_px([(17, 18), (21, 17), (24, 19), (19, 21), (23, 22), (12, 17)]), "#5a4c3c")
    s.paint(s.m_ellipse(22, 16.5, 3, 1), "#e0dcd0")


@sprite("arizona_mantis")
def _(s):
    # A green bordered mantis with a dark spot on each wing.
    mantis(s, "#6aa04a", "#8ac06a", "#d0e89a")
    s.paint(s.m_ellipse(24, 19, 1.2, 1), "#3a4a2a")
    s.paint(s.m_line(19, 19, 29, 17), "#c8e0a0")


@sprite("checkered_white")
def _(s):
    # White, checkered with black squares on the forewings.
    def pat(s, fm, hm):
        s.paint(s.m_px([(x + dx, y + dy) for x, y in ((3, 6), (6, 5), (4, 9), (7, 8), (10, 10), (4, 12),
                                                       (8, 12)) for dx in (0, 1) for dy in (0, 1)]),
                "#2b2630", mirror=True, within=fm)
        s.paint(s.m_px([(5, 21), (7, 24), (10, 26), (5, 18)]), "#8a8a8a", mirror=True, within=hm)
    butterfly(s, "#f8f6f0", "#f4f2ea", pattern=pat)


@sprite("variegated_fritillary")
def _(s):
    # Tawny orange with black zigzag lines and a row of dark dots.
    def pat(s, fm, hm):
        s.paint(s.m_line(3, 8, 13, 12) | s.m_line(4, 12, 13, 15) | s.m_line(5, 18, 13, 19), "#3a2418",
                mirror=True, within=fm | hm)
        s.paint(s.m_px([(5, 22), (7, 24), (9, 25), (11, 25)]), "#3a2418", mirror=True, within=hm)
        s.paint(s.m_poly([(1.5, 6), (5, 3), (5, 5), (2.5, 14)]), "#5a3a22", mirror=True, within=fm)
        s.paint(s.m_ellipse(11, 20, 2, 1.4), "#f0c070", mirror=True, within=hm)
    butterfly(s, "#d8863a", "#d07e34", body="#5a3e2a", pattern=pat)


@sprite("rough_harvester_ant")
def _(s):
    # A big red-brown ant with a square head and strong jaws for carrying seeds.
    s.can("walk")
    w = s.wave() if s.act == "walk" else 0
    c, d = "#a8402a", "#6a2418"
    for i, (x, dx) in enumerate(((12, -3), (14, 0), (16, 3))):
        sw = w * 1.5 * (1 if i % 2 else -1)
        s.path([(x, 20), (x + dx + sw, 24), (x + dx * 1.3 + sw, 29)], 0.55, d, shade=False)
    s.ellipse(23, 19, 5.5, 4.5, mix(c, "#000000", 0.15), edge=True)
    s.paint(s.m_line(21, 15, 21, 23) | s.m_line(25, 15, 25, 23), mix(c, "#000000", 0.35), within=s.last)
    s.ellipse(17.5, 20, 1.6, 1.6, c)
    s.ellipse(13.5, 19, 3.5, 2.3, c, edge=True)
    s.path([(6, 15), (4, 9), (1, 7)], 0.5, d, shade=False)
    s.path([(8, 15), (9, 9), (7, 6)], 0.5, d, shade=False)
    s.rect(4, 14, 10, 21, c, edge=True)
    s.poly([(4, 20), (1, 22), (4, 22)], d)
    s.px([(5, 22), (6, 23), (7, 22), (8, 23)], "#d8b890")  # a beard of hairs for carrying sand
    s.eye(5, 16)
    s.blush(7, 19)


@sprite("eastern_boxelder_bug")
def _(s):
    # Black with bright red lines along the edges of its wings and back.
    cockroach(s, "#2b2630", "#2b2630", "#2b2630")
    m = s.m_ellipse(16, 18.5, 6.5, 11.5)
    s.paint(m & ~s.m_ellipse(16, 18.5, 5.4, 10.6), "#e0402a")
    s.paint(s.m_line(13, 12, 16, 22) | s.m_line(19, 12, 16, 22), "#e0402a", within=m)
    s.paint(s.m_line(16, 6, 16, 11) | s.m_line(11, 9, 12, 11) | s.m_line(21, 9, 20, 11), "#e0402a",
            within=s.m_ellipse(16, 8.5, 6, 3.6))
    s.px([(13, 5), (18, 5)], WHITE)


@sprite("european_firebug")
def _(s):
    # Red and black, with a big black spot on each wing like a face on its back.
    cockroach(s, "#d8302a", "#d8302a", "#1e1a20")
    m = s.m_ellipse(16, 18.5, 6.5, 11.5)
    s.paint((s.m_ellipse(12.5, 20, 1.8, 1.8) | s.m_ellipse(19.5, 20, 1.8, 1.8)
             | s.m_poly([(12, 11), (20, 11), (16, 15)]) | s.m_ellipse(16, 28, 4, 2.6)), BLACK, within=m)
    s.paint(s.m_ellipse(16, 8.5, 2.4, 2), BLACK, within=s.m_ellipse(16, 8.5, 6, 3.6))
    s.px([(13, 5), (18, 5)], WHITE)


@sprite("garden_snail")
def _(s):
    # A brown shell with darker wavy bands and flecks.
    snail_shell(s, "#a87e4a", "#5a3e22")
    s.paint(s.m_path([(9, 12), (14, 9), (21, 9), (25, 14)], 0.5), "#6a4626",
            within=s.m_ellipse(16, 17, 10, 10))


@sprite("large_creosote_gall_midge")
def _(s):
    # A tiny orange fly perched on the round leafy gall it made on a creosote bush.
    s.can("fly")
    up = not (s.act == "fly" and s.f % 2)
    s.ellipse(16, 27, 5, 4, "#7a9a4a", edge=True)
    for x, y in ((12, 25), (16, 24), (20, 25), (14, 28), (18, 28)):
        s.paint(s.m_ellipse(x, y, 1.6, 1.0, rot=30), "#9ab85a", within=s.last)
    s.ellipse(10, 9 if up else 13, 6, 2.4, "#e6f0f6", rot=-30 if up else 15, shade=False, edge=True, mirror=True)
    for y in (16, 18):
        s.line(13, y, 9, y + 6, "#5a3a2a")
        s.line(18, y, 22, y + 6, "#5a3a2a")
    m = s.ellipse(16, 16, 3, 5.5, "#e8782a", edge=True)
    s.paint(s.m_line(14, 15, 18, 15) | s.m_line(14, 18, 18, 18), "#c8582a", within=m)
    s.ellipse(16, 9, 3, 2.6, "#d0602a", edge=True)
    s.line(15, 7, 12, 1, "#5a3a2a")
    s.line(17, 7, 20, 1, "#5a3a2a")
    s.px([(14, 8), (17, 8)], EYE)
    s.px([(14, 7), (17, 7)], WHITE)


@sprite("mormon_cricket")
def _(s):
    # A huge wingless katydid: fat body, a saddle-like shield and very long antennae.
    grasshopper(s, "#5a4a52", "#3e3238", legs="#4a3c42")
    s.path([(26, 22), (31, 19), (35, 18)], 0.6, "#3a2e34", shade=False)
    s.ellipse(20, 20, 9, 5, "#5a4a52")
    for x in (17, 21, 25):
        s.paint(s.m_line(x, 16, x, 24), "#3e3238", within=s.last)
    s.ellipse(14.5, 17, 4, 3.6, "#6a7a4a", edge=True)
    s.paint(s.m_line(12, 17, 17, 17), "#4a5a34", within=s.last)
    s.line(7, 13, 2, 3, "#3a2e34")
    s.line(2, 3, 1, -2, "#3a2e34")
    s.line(9, 13, 12, 2, "#3a2e34")
    s.line(12, 2, 14, -2, "#3a2e34")


@sprite("western_pygmy_blue")
def _(s):
    # One of the tiniest butterflies: coppery brown with blue near the body and a white fringe.
    def pat(s, fm, hm):
        s.paint(s.m_ellipse(14, 15, 5, 5), "#6a7ad0", mirror=True, within=fm | hm)
        s.paint(s.m_px([(5, 24), (7, 25), (9, 26), (11, 26)]), BLACK, mirror=True, within=hm)
        s.paint(s.m_line(2, 6, 2, 13) | s.m_line(4, 22, 8, 26), WHITE, mirror=True, within=fm | hm)
    butterfly(s, "#a8683a", "#a8683a", body="#4a3424", pattern=pat)


@sprite("variegated_meadowhawk")
def _(s):
    # A reddish dragonfly with a row of pale spots along its tail and amber wing bases.
    dragonfly(s, "#9a5a3a", "#c8483a", wing_tint="#f0c88a")
    s.px([(15, 17), (17, 20), (15, 23), (17, 26)], "#f0e8c8")
    s.px([(16, 18), (16, 21), (16, 24), (16, 27)], "#2b2226")


@sprite("common_desert_centipede")
def _(s):
    # Tan with a dark band on every segment, a red-orange head and yellow legs.
    pts = _segmented(s, 8, "#d8a858", "#c8502a", "#e8c870", leg_len=3.5, tail="#c8502a")
    for x, y in pts[1:]:
        s.paint(s.m_line(round(x) + 1, round(y) - 2, round(x) + 1, round(y) + 2), "#4a3424",
                within=s.m_ellipse(x, y, 2.6, 2.6))


@sprite("desert_millipede")
def _(s):
    # A long, thick, dark millipede ringed with tan bands, curling up when disturbed.
    pts = _segmented(s, 10, "#3a2a24", "#2a1e1a", "#d8a868", leg_len=1.8, spacing=2.6, r=2.6, antenna=2.5)
    for x, y in pts[1:]:
        s.paint(s.m_line(round(x) + 1, round(y) - 2, round(x) + 1, round(y) + 2), "#c8925a",
                within=s.m_ellipse(x, y, 2.6, 2.6))


@sprite("virile_crayfish")
def _(s):
    # Rusty brown with blue-green claws dotted with white knobs and orange tips.
    s.can("walk")
    w = s.wave() if s.act == "walk" else 0
    red, dark, claw = "#8a5a3a", "#5a3a24", "#4a8a8a"
    for i, y in enumerate((17, 20, 23)):
        d = w * 1.2 * (1 if i % 2 else -1)
        s.path([(13, y), (8, y + 2 + d), (6, y + 5 + d)], 0.6, dark, shade=False)
    s.poly([(29, 20), (33, 16), (34, 21), (33, 26)], red)
    m = s.path([(14, 20), (20, 20), (26, 20), (30, 21)], (4, 2.6), red)
    for x in (19, 22, 25, 28):
        s.paint(s.m_line(x, 16, x, 25), dark, within=m)
    s.path([(10, 18), (7, 13)], 1.1, claw)
    s.ellipse(5.5, 9, 3.4, 2.4, claw, rot=-60, edge=True)
    s.paint(s.m_px([(4, 6), (5, 6), (5, 7)]), "#f08a2a")
    s.px([(6, 9), (5, 11)], "#f0f4f0")
    s.path([(10, 22), (6, 25)], 1.1, claw)
    s.ellipse(4, 27, 3.2, 2.2, claw, rot=30, edge=True)
    s.paint(s.m_px([(1, 28), (1, 29)]), "#f08a2a")
    s.px([(4, 26), (5, 28)], "#f0f4f0")
    s.ellipse(12, 20, 5.5, 4.5, red, edge=True)
    s.paint(s.m_px([(12, 18), (14, 19), (11, 22)]), "#a87050", within=s.last)
    s.line(9, 17, 4, 13, dark)
    s.line(8, 18, 2, 16, dark)
    s.eye(9, 18)
    s.blush(10, 21)


@sprite("longfin_dace")
def _(s):
    # A small olive-silver minnow with a dark stripe and a dark spot at the tail.
    def pat(s, m):
        s.paint(s.m_path([(5, 16), (15, 16.5), (25, 16)], 0.6), "#3a3a30", within=m)
        s.paint(s.m_ellipse(24, 16, 1.4, 1.4), "#1e1e22", within=m)
        s.paint(s.m_px([(12, 12), (16, 11), (20, 12)]), "#8a8a5a", within=m)
    fish(s, "#a8a07a", "#ece8d8", fin="#c8a070", pattern=pat, slim=True)


@sprite("swift_woodlouse")
def _(s):
    # A slim, speedy woodlouse with long antennae and a mottled brown back.
    g = "#8a6e58"
    m = _woodlouse(s, g, "#c8b098")
    s.paint(s.m_px([(9, 18), (12, 20), (15, 18), (18, 20), (21, 18), (24, 20), (11, 17), (20, 17)]), "#d8c4a8",
            within=m)
    s.line(27, 22, 31, 24, mix(g, "#000000", 0.2))
    s.line(27, 20, 31, 18, mix(g, "#000000", 0.2))
    s.ellipse(6.5, 21, 3.4, 3.2, mix(g, "#000000", 0.15), edge=True)
    s.path([(4, 19), (1, 14), (-2, 12)], 0.45, "#3a3028", shade=False)
    s.path([(5, 18), (5, 13), (3, 10)], 0.45, "#3a3028", shade=False)
    s.eye(5, 20)
    s.blush(6, 23)
