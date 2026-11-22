"""Sprites for Singapore's animals that no other list has (2026-11): 87 species.
Imported by make_sprites.py, which registers the drawings via @sprite. Drawn with
the shared body plans (archetypes.py, mammal.py) and the European helpers, plus a
primate plan (_primate) for the macaque and the langurs and new plans for the
colugo, the slow loris, the pangolin and the mudskipper."""
from __future__ import annotations

import math

from archetypes import BLACK, EYE, PINK, WHITE, alligator, bird, butterfly, crab, critter, dragonfly, duck, fish, \
    frog, grasshopper, lizard, raptor, snake, sprite, star, wader
from mammal import quad
from pixel import mix
from species_east import _hermit
from species_eu_birds import _song
from species_eu_bugs import EDGE_F, EDGE_H, TIP, D, E, L, P, _bf
from species_eu_herps import NET, SPOTS, _both, _dots, _lines
from species_eu_water import _bars


def _dk(c, k=0.28):
    return mix(c, "#1a1420", k)


# =========================================================================== birds
@sprite("yellow_vented_bulbul")
def _(s):
    # Gray-brown above, white below, a white face with a dark eye stripe, a little crest
    # and bright yellow under the tail.
    s.poly([(10, 7), (12, 2), (15, 7)], "#5a5048")
    _song(s, "#8a8070", "#f2efe6", head="#f2efe6", wing="#7a7062", tail_col="#5a5048", legs="#3a3438",
          cap="#5a5048", mask="#2b2630", tail="long",
          bellym=lambda s, m: s.paint(s.m_ellipse(19, 25.5, 2.8, 1.6), "#f2d02a", within=m))


@sprite("javan_myna")
def _(s):
    # Sooty gray-black with a tufted forehead, a yellow bill and legs, white wing patches
    # and a white-tipped tail.
    s.poly([(4.5, 8), (6, 4.5), (8, 8)], "#26242a")
    bird(s, "#3a3840", "#4a4850", head="#26242a", wing="#2e2c34", tail_col="#26242a", beak="cone",
         beak_col="#f0c82a", legs="#f0c82a", tail="mid",
         wing_mark=lambda s, m: s.paint(s.m_ellipse(22, 22, 2.5, 1.3), WHITE, within=m))
    s.paint(s.m_ellipse(13.5, 25.5, 3, 1.5), WHITE)
    s.px([(29, 14), (30, 15)], WHITE)


@sprite("white_breasted_waterhen")
def _(s):
    # A rail that walks more than it swims: slate-gray back, a white face, throat and
    # breast, a yellow-green bill with a red base, rusty-cinnamon under the stubby
    # cocked tail and long yellow legs.
    _song(s, "#3e4248", "#f2f0ea", head="#3e4248", wing="#363a40", tail_col="#2e3238", beak="cone",
          beak_col="#c8c84a", legs="#c8b84a", tail="short", big=True, eye_col="#c02020",
          face=lambda s, h: s.paint(s.m_ellipse(7.5, 13, 3.8, 4.2), "#f4f2ec", within=h),
          bellym=lambda s, m: s.paint(s.m_ellipse(19.5, 25, 3, 1.8), "#c87a3a", within=m))
    s.px([(5, 10), (5, 11)], "#d8302a")


@sprite("pink_necked_green_pigeon")
def _(s):
    # The male: a soft green pigeon with a gray crown, a lilac neck, an orange breast,
    # black-and-yellow wing edges and a gray tail with a black band.
    _song(s, "#7a9a4a", "#e89a3a", head="#9aa6a0", wing="#6a8a3e", tail_col="#8a9490", beak="dove",
          beak_col="#9ab0b8", legs="#d8708a", tail="mid", big=True,
          face=lambda s, h: s.paint(s.m_ellipse(11, 15, 5, 2.6), "#c88aa8", within=h),
          wingm=lambda s, m: (s.paint(s.m_line(16, 21, 24, 19) | s.m_line(17, 23, 24, 21), BLACK, within=m),
                              s.paint(s.m_line(16, 22, 24, 20), "#e8d040", within=m)))


@sprite("oriental_magpie_robin")
def _(s):
    # Glossy blue-black head, breast and back, a white belly, a long white wing stripe and
    # white edges to the cocked tail.
    _song(s, "#1e2230", "#f4f2ec", head="#1e2230", wing="#1e2230", tail_col="#1e2230", legs="#3a3438",
          tail="long", breast="#1e2230",
          wingm=lambda s, m: s.paint(s.m_line(15, 19, 24, 17) | s.m_line(15, 20, 24, 18), WHITE, within=m))
    s.px([(31, 8), (30, 10)], WHITE)


@sprite("collared_kingfisher")
def _(s):
    # Turquoise-blue crown, back and wings, a crisp white collar and underparts and a
    # big black-and-pale bill.
    def face(s):
        h = s.last
        s.paint(s.m_ellipse(11, 7.5, 6, 3.4), "#2a9ab8", within=h)
        s.paint(s.m_line(6, 10.5, 14, 11), "#1e3a58", within=h)
        s.paint(s.m_ellipse(9, 15, 5, 2.6) | s.m_ellipse(15, 14, 2.2, 1.8), WHITE, within=h)
    bird(s, "#2a9ab8", "#f6f4ee", head="#2a9ab8", wing="#2a8ab8", tail_col="#2a7ab0", beak="long",
         beak_col="#2b2630", legs="#4a4048", tail="short", face=face)
    s.px([(2, 12), (3, 13)], "#e8dcc8")


@sprite("black_naped_oriole")
def _(s):
    # Brilliant golden yellow with a broad black band through the eye round the nape,
    # black in the wings and tail and a pink bill.
    _song(s, "#f0c828", "#f4d838", head="#f0c828", wing="#2b2630", tail_col="#2b2630", beak="cone",
          beak_col="#e07a8a", legs="#5a5058", tail="mid", big=True, eye_col="#a01818",
          face=lambda s, h: s.paint(s.m_line(4, 10, 17, 10) | s.m_line(6, 11, 17, 11) | s.m_line(14, 9, 17, 9),
                                     "#1e1a22", within=h),
          wingm=lambda s, m: s.paint(s.m_line(16, 17, 23, 15), "#f0c828", within=m))
    s.px([(30, 11), (31, 12)], "#f0c828")


@sprite("oriental_pied_hornbill")
def _(s):
    # Black above with a white belly and face patch, white tail edges, and a huge
    # cream bill under a tall casque.
    s.path([(22, 18), (30, 12), (35, 7)], (2.4, 1.2), "#1e1c22")
    s.path([(25, 16), (30, 12)], (0.6, 0.4), WHITE)
    _song(s, "#1e1c22", "#f4f2ec", head="#1e1c22", wing="#1e1c22", tail_col="#1e1c22", beak="crow",
          beak_col="#e8dca8", legs="#3a3438", tail="long", big=True, breast="#1e1c22",
          face=lambda s, h: s.paint(s.m_ellipse(10.5, 12.5, 1.6, 1.4), "#c8d8e8", within=h))
    # the big cream bill, curved down, under a tall casque with a black patch
    s.poly([(6.5, 10.5), (2, 11), (-2, 13.5), (-1, 14.2), (3, 13.6), (6.5, 13.6)], "#e8dca8")
    s.poly([(7, 7.5), (3, 7.6), (0, 9.5), (-1.5, 11.2), (3, 10.8), (7, 10.6)], "#f0e6b8")
    s.px([(3, 9), (4, 9), (1, 10)], "#2b2630")
    s.px([(-1, 13), (0, 13)], "#4a4038")


@sprite("house_crow")
def _(s):
    # A slim black crow with a smoky gray neck and breast and a glossy black face, crown and throat.
    bird(s, "#2a282e", "#6a6870", head="#1e1c22", wing="#22202a", tail_col="#1e1c22", beak="crow",
         beak_col="#1e1c22", legs="#1e1c22", tail="mid", big=True,
         face=lambda s: s.paint(s.m_ellipse(14, 13, 3, 4) | s.m_ellipse(13, 17, 3, 2), "#7a7880", within=s.last))


@sprite("asian_glossy_starling")
def _(s):
    # Glossy green-black all over, with a ruby-red eye.
    bird(s, "#1e2a2a", "#22302e", head="#1a2624", wing="#1e2a2a", tail_col="#18201e", beak="cone",
         beak_col="#1e1c22", legs="#1e1c22", tail="mid", eye_col="#d02020",
         wing_mark=lambda s, m: s.paint(s.m_px([(17, 18), (20, 17), (22, 19)]), "#3a6a5a", within=m))
    s.px([(14, 8), (12, 7)], "#4a7a6a")


@sprite("brown_throated_sunbird")
def _(s):
    # The male: a short curved bill, a dull brown throat, an iridescent green and purple
    # crown and back, maroon shoulders and a yellow belly.
    _song(s, "#3a6a4a", "#f0d030", head="#4a3a6a", wing="#6a5a3a", tail_col="#2a3a3a", beak="thin",
          beak_col="#1e1c22", legs="#3a3438", tail="mid", throat="#9a7a5a",
          face=lambda s, h: s.paint(s.m_ellipse(11.5, 7, 5.5, 2.4), "#3a8a6a", within=h),
          wingm=lambda s, m: s.paint(s.m_ellipse(17, 16, 3, 1.6), "#7a2a3a", within=m))
    s.path([(5.5, 11.5), (2, 12.5), (0, 14)], (0.5, 0.4), "#1e1c22", shade=False)


@sprite("crimson_sunbird")
def _(s):
    # The male: crimson head, breast and back, an olive belly, a purple mustache, a long
    # curved bill and a long dark tail.
    _song(s, "#c82828", "#8a8a5a", head="#c82828", wing="#5a5a3a", tail_col="#3a3a4a", beak="thin",
          beak_col="#1e1c22", legs="#3a3438", tail="long", breast="#d83030",
          face=lambda s, h: s.paint(s.m_line(6, 14, 10, 16), "#6a3a9a", within=h))
    s.path([(5.5, 11.5), (2, 12.5), (-1, 14.5)], (0.5, 0.4), "#1e1c22", shade=False)


@sprite("scarlet_backed_flowerpecker")
def _(s):
    # Tiny and dumpy: the male glossy blue-black on the sides of the head, wings and tail,
    # a scarlet stripe from crown to rump and pale buff-gray underparts.
    _song(s, "#1e2438", "#e4dcc8", head="#1e2438", wing="#1e2438", tail_col="#1e2438", beak="cone",
          beak_col="#1e1c22", legs="#3a3438", tail="short",
          face=lambda s, h: s.paint(s.m_ellipse(12, 7, 5.5, 2.4), "#d82828", within=h))
    s.paint(s.m_ellipse(19, 14.5, 5, 1.6, rot=-10), "#d82828")


@sprite("white_bellied_sea_eagle")
def _(s):
    # White head and underparts, gray back and wings with black flight feathers and a short white wedge tail.
    raptor(s, "#7a7e86", WHITE, head=WHITE, wing="#6a6e76", tail=WHITE, build="eagle", bill="#5a5a64",
           cere="#8a8a92", legs="#d8d8c8", eye_col="#5a3a20")


@sprite("brahminy_kite")
def _(s):
    # Rich chestnut with a white head and breast finely streaked, and black wingtips.
    raptor(s, "#a8502a", WHITE, head=WHITE, wing="#9a4826", tail="#b05a2e", build="kite", bill="#e8d8a0",
           cere="#e8d070", legs="#e8d070", eye_col="#8a5a20",
           chest=lambda s, m: s.paint(s.m_px([(11, 17), (13, 19), (12, 21)]), "#c8b8a8", within=m))


@sprite("crested_honey_buzzard")
def _(s):
    # A slim-headed buzzard with a little crest: brown above, pale below barred with
    # rufous, a pale throat with a dark mustache and a banded tail.
    raptor(s, "#6a4e36", "#d8c0a0", head="#8a7a6a", wing="#5a402c", tail="#7a6450", build="buteo", bill="#2b2630",
           cere="#4a4a50", legs="#e8c040", eye_col="#e0a030",
           chest=lambda s, m: s.paint(s.m_line(10, 18, 15, 18) | s.m_line(10, 21, 15, 21) | s.m_line(11, 24, 15, 24),
                                       "#a8704a", within=m),
           tail_mark=lambda s, m: s.paint(s.m_line(16, 26, 24, 26) | s.m_line(17, 29, 24, 29), "#3a2a20", within=m))


@sprite("white_throated_kingfisher")
def _(s):
    # Chocolate-brown head and belly, a white throat and bib, electric-blue back, wings
    # and tail and a huge red bill.
    def face(s):
        h = s.last
        s.paint(s.m_ellipse(8.5, 15.5, 4, 3), WHITE, within=h)
    bird(s, "#2a7ac8", "#6a3a22", head="#6a3a22", wing="#2a8ad8", tail_col="#2a7ac8", beak="long",
         beak_col="#d82a22", legs="#d82a22", tail="short", face=face,
         wing_mark=lambda s, m: s.paint(s.m_ellipse(16, 16, 3, 1.6), "#6a3a22", within=m),
         belly_mark=lambda s, m: s.paint(s.m_ellipse(12.5, 20, 3, 2.2), WHITE, within=m))


@sprite("asian_koel")
def _(s):
    # The male: glossy blue-black all over with a long tail, a pale green bill and a red eye.
    bird(s, "#1a1c28", "#1e202c", head="#161822", wing="#1a1c28", tail_col="#161822", beak="cone",
         beak_col="#b8c8a0", legs="#5a5a6a", tail="long", eye_col="#d02020",
         wing_mark=lambda s, m: s.paint(s.m_px([(17, 17), (20, 18)]), "#3a4a6a", within=m))
    s.path([(28, 10), (33, 6)], (1.2, 0.8), "#161822")


@sprite("asian_openbill")
def _(s):
    # A grayish-white stork with black wings and tail and a dull horn bill with a gap
    # between its two halves.
    wader(s, "#e0ddd4", neck="#e8e6de", head="#e8e6de", beak="#9a8a6a", legs="#c87a6a", wing="#d8d4ca")
    s.paint(s.m_ellipse(23, 16, 5, 2.4, rot=-10) | s.m_poly([(26, 14), (31, 17), (25, 18)]), BLACK)
    s.eye(8, 4)


@sprite("purple_heron")
def _(s):
    # Slimmer than the grey heron: a chestnut neck with a black stripe down each side, a
    # black cap and plume, gray-purple back and wings.
    wader(s, "#6a5a7a", neck="#b0643a", head="#b0643a", beak="#e8b830", legs="#a8804a", plume="#1e1c22",
          cap="#1e1c22", wing="#5a5068")
    s.paint(s.m_line(13, 7, 14, 14), "#2b2630")
    s.paint(s.m_ellipse(24, 15, 3, 1.5, rot=-10), "#8a4a2a")


@sprite("greater_racket_tailed_drongo")
def _(s):
    # Glossy blue-black with a tuft of feathers over the bill and two long bare tail wires
    # ending in twisted rackets.
    s.path([(24, 19), (29, 22), (33, 25)], (0.6, 0.5), "#1e1c22", shade=False)
    s.ellipse(33.5, 26, 1.6, 1.2, "#1e1c22")
    s.path([(24, 18), (30, 20), (34, 21.5)], (0.6, 0.5), "#2a2830", shade=False)
    s.ellipse(34.5, 22.5, 1.6, 1.2, "#2a2830")
    _song(s, "#1e2030", "#1e2030", head="#1a1c28", wing="#1e2030", tail_col="#1a1c28", beak="crow",
          beak_col="#1e1c22", legs="#1e1c22", tail="mid", eye_col="#c02020")
    s.poly([(6, 9), (5, 4.5), (8.5, 8)], "#1a1c28")


@sprite("pacific_swallow")
def _(s):
    # Glossy blue-black above, a rusty-red face and throat, a dusky gray belly and a short forked tail.
    def face(s):
        s.paint(s.m_ellipse(8.5, 14.5, 4, 2.4) | s.m_px([(5, 10), (5, 11)]), "#c0582e", within=s.last)
    s.path([(22, 19), (28, 17), (32, 16)], (1.2, 0.4), "#1e3466")
    s.path([(22, 21), (28, 22), (32, 23)], (1.2, 0.4), "#1e3466")
    bird(s, "#2a4a8a", "#b8b4ae", head="#2a4a8a", wing="#22407a", tail_col="#1e3466", beak="thin",
         beak_col="#1a1820", legs="#3a3034", tail="short", face=face)


def _bee_eater(s, body, belly, head, throat, *, band=None, tail_col=None, face=None):
    s.path([(24, 18), (31, 15.5), (36, 15)], (0.8, 0.4), tail_col or body)
    _song(s, body, belly, head=head, wing=body, tail_col=tail_col or body, beak="long", beak_col="#1e1c22",
          legs="#4a3e36", mask="#1e1c22", throat=throat, eye_col="#c02a2a",
          face=lambda s, h: (s.paint(s.m_line(6, 17, 12, 17), band, within=h) if band else None,
                             face(s, h) if face else None))


@sprite("blue_throated_bee_eater")
def _(s):
    # Green with a chestnut crown and nape, a sky-blue throat, a black mask and long central tail streamers.
    _bee_eater(s, "#3aa05a", "#6ac08a", "#8a3a22", "#5ac0e8", tail_col="#3a9a6a")


@sprite("blue_tailed_bee_eater")
def _(s):
    # Green all over with a chestnut throat over a yellow chin, a black mask edged in blue
    # and a blue tail with long streamers.
    _bee_eater(s, "#4aa04a", "#7ab86a", "#4aa04a", "#b8602a", tail_col="#3a7ac8",
               face=lambda s, h: s.paint(s.m_ellipse(6.5, 14, 2.2, 1.2), "#f0d040", within=h))


@sprite("malaysian_pied_fantail")
def _(s):
    # Sooty black above with a white eyebrow, a white throat over a black breast band, a
    # buff-white belly and a long fanned tail tipped white.
    _song(s, "#2a2830", "#f2ece0", head="#1e1c22", wing="#2a2830", tail_col="#1e1c22", legs="#2b2630",
          tail="fan", brow=WHITE, throat=WHITE,
          bellym=lambda s, m: s.paint(s.m_ellipse(12, 19, 3.5, 1.4), "#1e1c22", within=m))
    s.px([(29, 11), (30, 13), (31, 15)], WHITE)


@sprite("ashy_tailorbird")
def _(s):
    # A tiny dark-gray warbler with a rusty-red face and forehead, a long thin bill and a cocked tail.
    _song(s, "#5a5e66", "#7a7e86", head="#5a5e66", wing="#4e5258", tail_col="#4a4e56", legs="#c8a08a",
          tail="long", face=lambda s, h: s.paint(s.m_ellipse(8, 11, 4, 3.4), "#c0582e", within=h))
    s.path([(5.5, 11.5), (1.5, 12)], (0.5, 0.4), "#2b2630", shade=False)


@sprite("olive_winged_bulbul")
def _(s):
    # Plain olive-brown above with yellow-olive edges to the wing feathers, pale gray-buff
    # below, a faint pale streak on the ear and a red eye.
    _song(s, "#7a7258", "#d8d2bc", head="#7a7258", wing="#8a8a4a", tail_col="#6a6450", legs="#5a5058",
          tail="long", eye_col="#b02020",
          face=lambda s, h: s.paint(s.m_line(10, 13, 13, 14), "#b8b4a0", within=h),
          wingm=lambda s, m: s.paint(s.m_line(16, 20, 24, 18), "#a8a848", within=m))


@sprite("common_flameback")
def _(s):
    # Golden-olive back, a red crest (male), black-and-white striped face and neck,
    # scaly black-and-white underparts and a black rump and tail.
    def face(s, h):
        s.paint(s.m_ellipse(12, 6.5, 5, 2.6), "#d82828", within=h)
        s.paint(s.m_line(6, 11, 16, 11) | s.m_line(7, 14, 15, 14), BLACK, within=h)
    _song(s, "#c8a838", "#f0ece0", head="#f0ece0", wing="#c89a30", tail_col="#1e1c22", beak="long",
          beak_col="#2b2630", legs="#5a5a60", tail="mid", face=face,
          bellym=lambda s, m: s.paint(s.m_px([(10, 20), (13, 21), (16, 20), (11, 23), (14, 23), (17, 22)]),
                                      "#1e1c22", within=m))
    s.poly([(11, 5), (14, 0), (16, 5)], "#d82828")


@sprite("red_breasted_parakeet")
def _(s):
    # Green with a gray-lilac head, a black mustache and chin band, a rosy-pink breast, a red bill and a long blue-green tail.
    def face(s):
        s.paint(s.m_line(6, 14, 11, 16) | s.m_line(4, 10, 9, 10.5), BLACK, within=s.last)
    s.path([(22, 18), (30, 12), (35, 4)], (2.2, 0.8), "#3a9a9a")
    bird(s, "#5ab04a", "#e890a8", head="#a8a8c8", wing="#4aa04a", tail_col="#3a9a9a", beak="hook",
         beak_col="#d82a2a", legs="#8a8a90", tail="long", face=face,
         wing_mark=lambda s, m: s.paint(s.m_ellipse(18, 17, 3, 1.6), "#d8c848", within=m))


@sprite("oriental_dollarbird")
def _(s):
    # A stocky dark blue-green roller with a dark head, a broad red bill and a pale blue coin-shaped patch on each wing.
    _song(s, "#2a5a6a", "#3a6a7a", head="#22303a", wing="#1e3a5a", tail_col="#1e2a3a", beak="crow",
          beak_col="#d83a2a", legs="#d85a3a", big=True, tail="mid",
          wingm=lambda s, m: s.paint(s.m_ellipse(21, 19, 1.8, 1.3), "#a8d0e8", within=m))


# =========================================================================== reptiles
def _tongue(s, x=1, y=19.5, col="#c84a7a"):
    """A monitor's long forked tongue, flicking out now and then."""
    if s.act in ("idle", "walk", "eat") and s.t % 0.5 < 0.2:
        s.path([(x + 1, y), (x - 2.5, y)], 0.35, col, shade=False)
        s.px([(round(x - 3), round(y - 1)), (round(x - 3), round(y + 1))], col)


@sprite("asian_water_monitor")
def _(s):
    # A huge dark lizard: sooty gray-black with rows of pale yellow spots, a long neck,
    # a long narrow snout and a thick tail flattened for swimming.
    def pat(s, m):
        s.paint(s.m_px([(x, y) for y in (19, 21, 23) for x in range(9 + (y % 4), 23, 3)]), "#d8c870", within=m)
    lizard(s, "#3a3a30", "#a8a070", head="#3e3e34", throat="#c8c090", pattern=pat, wide=True,
           legs="#34342c", tail_col="#34342c", tail_pts=[(20, 22), (27, 25), (33, 25), (37, 21)])
    _tongue(s)


@sprite("clouded_monitor")
def _(s):
    # Smaller and slimmer than the water monitor: gray-brown, clouded all over with pale
    # yellowish flecks, and a more rounded tail.
    def pat(s, m):
        s.paint(s.m_px([(x + (y % 2), y) for y in range(18, 25) for x in range(8, 23, 2) if (x + y) % 3]),
                "#c8b888", within=m)
    lizard(s, "#6a6050", "#d8ccb0", head="#6e6454", throat="#d8ccb0", pattern=pat, legs="#5e5646",
           tail_col="#5e5646", tail_pts=[(20, 22), (27, 25), (33, 24), (36, 20)])
    _tongue(s)


@sprite("oriental_garden_lizard")
def _(s):
    # The changeable lizard: tan with dark bands, a crest of spines down the neck and back,
    # and a male's head flushed orange-red.
    lizard(s, "#a08a5a", "#e8dcbc", head="#d0603a", throat="#d85a3a",
           pattern=_dots([(10, 19), (10, 20), (14, 19), (14, 20), (18, 19), (18, 20), (21, 20)], "#4a3a24"),
           horns=True, tail_col="#8a7650", tail_pts=[(20, 22), (27, 25), (33, 24), (37, 20)])


@sprite("common_sun_skink")
def _(s):
    # A glossy bronze-brown skink with dark flanks and a yellow-orange wash on its sides.
    lizard(s, "#8a6a40", "#e8dcb8",
           pattern=_both(_lines((21.5,), "#3a2a1e"), _lines((22.5,), "#e0a040"), _dots(SPOTS[:4], "#5a4228")),
           smooth=True, wide=True, tail_col="#7a5c38", throat="#e8c070")


@sprite("common_gliding_lizard")
def _(s):
    # A slim gray-brown flying lizard: the folded "wing" along its side is orange with
    # dark bars, and a yellow throat flag hangs under its chin.
    def pat(s, m):
        s.paint(s.m_ellipse(15, 21.5, 6.5, 1.6), "#d8803a", within=m)
        for x in (11, 14, 17, 20):
            s.paint(s.m_line(x, 20, x - 1, 23), "#4a2e1e", within=m)
        s.paint(s.m_px([(9, 19), (13, 18), (17, 19)]), "#8a8474", within=m)
    lizard(s, "#7a7064", "#d8d0c0", pattern=pat, legs="#6a6256", tail_col="#6e665a",
           tail_pts=[(20, 22), (28, 24), (35, 24), (39, 22)])
    if s.act in ("idle", "look") and 0.25 < s.t < 0.75:  # the flag flicks out in display
        s.poly([(4, 20), (7, 20.5), (5.5, 24), (4, 22.5)], "#f0d030")


@sprite("estuarine_crocodile")
def _(s):
    # The saltwater crocodile: the biggest reptile alive, olive-gray with darker bands
    # and a long, broad snout.
    alligator(s, "#6a6a44", "#e8e0b0")


@sprite("waglers_pit_viper")
def _(s):
    # A stout, sleepy tree viper with a big triangular head: green crossed by thin yellow
    # bands edged in black, with a yellow stripe behind the eye.
    snake(s, "#4a8a3a", belly="#d8d060", bands="#e8d040", band_period=3.4, band_len=0.9, head="#4a8a3a",
          head_w=6.4)


@sprite("asian_vine_snake")
def _(s):
    # A whip-thin, bright leaf-green snake with a long pointed snout and a pale yellow
    # line along its side.
    snake(s, "#5ab040", belly="#c8e070", stripe="#e8f0a0", head="#5ab040", head_w=3.8)


@sprite("paradise_tree_snake")
def _(s):
    # The flying snake: black, each scale edged in bright green, with a row of red-orange
    # spots down its back.
    snake(s, "#26302a", belly="#a8d050", blotch="#e8602a", band_period=3.0, stripe="#6ab040", head="#2a3a2a",
          head_w=4.4)


# =========================================================================== frogs
@sprite("asian_common_toad")
def _(s):
    # The black-spined toad: warty brown with black-tipped warts, black ridges over
    # the eyes and big glands behind them.
    frog(s, "#8a6a44", "#e8dcc0", build="toad", ridges="#2b2226", parotoid="#7a5a38", warts="#2b2226",
         spots=3, spot_col="#4a3424", iris="#d8a040", crown="#2b2226")


@sprite("four_lined_tree_frog")
def _(s):
    # A slim, long-legged tan tree frog with four dark lines down its back.
    frog(s, "#b8986a", "#f2ead8", build="tree", lines="#5a4228", mask="#6a4a30", pads=True, iris="#c8a060")


@sprite("white_lipped_frog")
def _(s):
    # Olive-brown with a bright white stripe along the upper lip and long legs.
    frog(s, "#6a6a3a", "#f0ecd8", lip=WHITE, mask="#3a3a24", spots=2, thigh="#5a5a32", pads=True)


@sprite("banded_bullfrog")
def _(s):
    # A round, tiny-headed frog: chocolate brown with a broad tan band from the eye
    # down each side.
    frog(s, "#4a3424", "#e8dcc4", build="toad", side="#d8a060", dorsal=None, iris="#3a2a20", spots=0)


@sprite("malesian_frog")
def _(s):
    # A chunky forest-stream frog: plain brown with a dark mask and a thick head.
    frog(s, "#7a5a3c", "#ece0cc", mask="#3a2a1e", tympanum="#5a3e28", spots=3, thigh="#6a4e34",
         ridges="#9a7a54")


@sprite("green_paddy_frog")
def _(s):
    # A slim frog with a bright green back, brown sides and a pale line between them.
    frog(s, "#8a6a44", "#f0ecdc", dorsal="#5aa040", ridges="#f0ecd0", lip="#f0ecd0", spots=0)


@sprite("arcuate_spotted_pygmy_frog")
def _(s):
    # A tiny gray-brown narrow-mouthed frog with dark, pale-edged arcs on its back.
    frog(s, "#9a8a74", "#ece4d8", build="toad", spots=5, spot_col="#3a3026", spot_big=True, iris="#5a4a3a")


# =========================================================================== fish
@sprite("striped_snakehead")
def _(s):
    # A long, round-bodied predator: dark olive-brown with darker chevrons, a long
    # dorsal fin and a flat, snake-like head.
    def pat(s, m):
        for x in (10, 13.5, 17, 20.5):
            s.paint(s.m_path([(x, 9), (x + 1.5, 13), (x, 17)], 0.6), "#2e2a20", within=m)
    fish(s, "#5a5a3c", "#d8d0b0", fin="#4a4a32", pattern=pat, slim=True)


@sprite("banded_archerfish")
def _(s):
    # Silver-white and deep-bodied, with black wedges hanging down its back and a
    # pointed, upturned mouth for spitting water at insects.
    fish(s, "#d8dcd8", "#f6f6f2", fin="#c8c8a0", pattern=_bars((9, 13, 17, 21), "#1e1c22", y0=7, y1=13))


@sprite("giant_mudskipper")
def _(s):
    # A fish that lives on the mud: gray-brown with pale blue spots, eyes bulging on top of
    # its blunt head, strong arm-like front fins and a tall spiny fin it flicks up.
    s.can("walk")
    walk = s.act == "walk"
    hop = s.cyc(0, -1.5, 0, 0) if walk else 0
    fin = s.cyc(0.6, 1, 0.6, 0.3) if s.act in ("idle", "look") else 0.5
    body, lite, dark = "#7a6e5a", "#c8bca4", "#4a4234"
    s.path([(22, 25 + hop), (29, 26.5), (34, 26)], (2.6, 1.0), body)
    s.poly([(33, 26), (38, 23), (39, 26.5), (37.5, 29), (33, 27)], dark)  # tail fin
    s.poly([(20, 22.5 + hop), (21, 18.5 + hop), (30, 23), (30, 25.5)], dark)  # second dorsal
    top = 20.5 - 7 * fin
    m1 = s.poly([(12, 20.5 + hop), (13, top + hop), (17, top + 1 + hop), (20, 20.5 + hop)], dark, edge=True)
    s.paint(s.m_px([(14, round(top + 3 + hop)), (16, round(top + 4 + hop)), (18, round(top + 5 + hop))]),
            "#a8c8e0", within=m1)
    m = s.ellipse(16, 24 + hop, 9, 4, body, edge=True)
    s.paint(s.m_ellipse(16, 27 + hop, 8, 1.4), lite, within=m)
    s.paint(s.m_px([(14, 22), (17, 23), (20, 22), (12, 24), (18, 25), (22, 24)]), "#a8c8e0", within=m)
    hm = s.ellipse(8, 23.5 + hop, 5, 4.2, body, edge=True)
    s.paint(s.m_ellipse(7, 26.5 + hop, 4, 1.4), lite, within=hm)
    s.paint(s.m_line(3, 25 + hop, 6, 25.5 + hop), dark, within=hm)
    reach = s.cyc(0, 2, 1, 0) if walk else 0
    s.path([(11, 25 + hop), (9 - reach, 28.5)], (1.6, 1.2), mix(body, lite, 0.3))  # front fin "arm"
    s.ellipse(9.8, 19 + hop, 2.0, 2.0, _dk(body, 0.1), edge=True)  # eye turrets on top of the head
    s.ellipse(7, 18.6 + hop, 2.5, 2.5, body, edge=True)
    s.ellipse(7, 18.2 + hop, 1.7, 1.7, "#d8d0b8", shade=False)
    s.eye(6, 17 + round(hop))


# =========================================================================== insects
sprite("brown_pansy")(_bf("#5a3020", "#5e3424", ("b", L(14, 9, 3, 13), "#d8603a"),
                           ("f", E(5, 8, 1.1), "#e8a04a"), ("h", E(8, 21, 1.4), "#2b2226"),
                           ("h", E(8, 21, 0.7), "#e8a04a"), ("h", L(14, 20, 6, 24), "#d8603a")))
sprite("peacock_pansy")(_bf("#e08a2a", "#e4922e", ("f", E(6, 9, 1.8), "#2b2630"), ("f", E(6, 9, 0.9), "#e8b050"),
                             ("h", E(9, 21, 2.6), "#2b2630"), ("h", E(9, 21, 1.6), "#e8902a"),
                             ("h", E(9.5, 20.5, 0.7), "#6a8ac8"), ("b", EDGE_F, "#7a4a24"),
                             ("h", EDGE_H, "#7a4a24")))
sprite("tawny_coster")(_bf("#d8803a", "#e08a40", ("f", TIP, "#2b2630"), ("f", D((8, 9), (10, 11), (11, 8)), "#2b2630"),
                            ("h", EDGE_H, "#2b2630"), ("h", D((6, 24), (8, 26)), WHITE),
                            ("h", D((10, 19), (12, 21)), "#2b2630")))
sprite("plain_tiger")(_bf("#e8902a", "#ec9a34", ("f", TIP, "#2b2630"), ("f", D((4, 7), (5, 8), (6, 6), (3, 9)), WHITE),
                           ("f", EDGE_F, "#2b2630"), ("h", EDGE_H, "#2b2630"), ("h", D((6, 23), (8, 25)), WHITE),
                           ("h", D((11, 19), (12, 18), (13, 19)), "#2b2630"), body="#2b2630"))
sprite("common_palmfly")(_bf("#3a2a22", "#4a3024", ("f", D((3, 8), (4, 10), (5, 12), (4, 6)), "#a8c0e8"),
                              ("h", EDGE_H, "#b8683a"), ("h", D((7, 24), (9, 25)), "#e8d0a0")))
sprite("common_mormon")(_bf("#22201e", "#24201e", ("f", D((3, 12), (4, 13), (5, 14)), "#f0ece0"),
                             ("h", P((5, 19), (13, 17), (13, 19.5), (6, 22)), "#f0ece0"),
                             ("h", D((5, 24), (7, 26)), "#d84a3a"), tails=True))
sprite("flambeau")(_bf("#f08a28", "#f09434", ("f", L(10, 6, 7, 11), "#2b2630"), ("f", D((2, 7), (3, 8)), "#2b2630"),
                        ("h", EDGE_H, "#c8601e")))
sprite("hubners_wasp_moth")(_bf("#24202a", "#26222a", ("f", E(9, 8, 1.6, 1.1), "#d8e0e8"),
                                 ("f", E(6, 11, 1.4, 1.0), "#d8e0e8"), ("f", E(11, 12, 1.2), "#d8e0e8"),
                                 ("h", E(10, 19, 1.6, 1.2), "#d8e0e8"), body="#e8a030"))


@sprite("common_parasol")
def _(s):
    # A small red skimmer whose wings are stained rusty red almost to the tips.
    dragonfly(s, "#8a2a1e", "#c8382a", wing_tint="#a8402a")


@sprite("scarlet_skimmer")
def _(s):
    # Bright scarlet all over, with a thin black line down the abdomen and amber wing bases.
    dragonfly(s, "#c8302a", "#e8302a", wing_tint="#f0c070")


@sprite("asian_crimson_dropwing")
def _(s):
    # The crimson marsh glider: a magenta-crimson body and pink wing veins.
    dragonfly(s, "#8a2a4a", "#d0306a", wing_tint="#e888b0")


@sprite("rufous_legged_grasshopper")
def _(s):
    # A small brown grasshopper with a pale stripe and rusty-red hind legs.
    grasshopper(s, "#8a7656", "#5a4a34", legs="#c0502a")


# =========================================================================== shore and sea
@sprite("blue_swimming_crab")
def _(s):
    # The flower crab: sky-blue mottled with white, long slim claws and paddle-shaped back legs.
    crab(s, "#4a7ab0", "#5a8ac8", legs="#3a68a0",
         pattern=lambda s, m: s.paint(s.m_px([(10, 17), (13, 16), (17, 15), (21, 17), (12, 20), (16, 19), (20, 20),
                                               (14, 23), (19, 23)]), "#e8f0f8", within=m))


@sprite("violet_tree_climbing_crab")
def _(s):
    # A square-backed mangrove crab, purple-brown with violet claws, that climbs the trunks.
    crab(s, "#5a3a52", "#9a5ab0", legs="#4a2e46",
         pattern=lambda s, m: s.paint(s.m_line(9, 15, 23, 15), "#7a5070", within=m))


@sprite("pink_fingered_vinegar_crab")
def _(s):
    # A dark brown mangrove crab with pink-tipped claws.
    crab(s, "#4a3a2e", "#c87a7a", legs="#3e3026",
         pattern=lambda s, m: s.paint(s.m_line(9, 15, 23, 15), "#6a5444", within=m))
    s.px([(2, 9), (3, 9), (29, 9), (30, 9)], "#f0b0c0")


@sprite("orange_striped_hermit_crab")
def _(s):
    # A dark hermit crab in a borrowed shell, its legs ringed with orange stripes.
    _hermit(s, "#a89a84", "#6a6050", "#3a2e2a", "#4a3a32", leg_mark="#e8802a")


@sprite("chocolate_chip_sea_star")
def _(s):
    # A stout cream-tan sea star studded with knobs like chocolate chips.
    star(s, "#d8b888", arms=0.35, dots="#3a2418")


@sprite("haddons_carpet_anemone")
def _(s):
    # A flat, broad carpet of short sticky tentacles, green with pinkish patches.
    sway = s.cyc(0, 0.5, 0, -0.5) if s.act == "idle" else 0
    s.ellipse(16, 29, 15, 1.8, "#c8b8a0")
    m = s.ellipse(16, 25, 15, 4.2, "#5a8a4a", edge=True)
    for k, x in enumerate(range(2, 31, 3)):  # the ruffled, folded rim of the carpet
        y = 21.5 + 1.2 * math.sin(k * 1.7) + (1.5 if x < 5 or x > 27 else 0)
        m |= s.ellipse(x + sway * 0.5, y, 2.0, 1.8, "#6a9a52" if k % 2 else "#5a8a4a", shade=False)
    s.paint(s.m_ellipse(16, 27.5, 14, 1.4), "#3a5a30", within=m)
    for y in (20, 22, 24, 26):
        for x in range(2 + y % 2, 31, 2):
            col = "#e8a8c0" if (x // 2 + y) % 7 == 0 else "#a8d080" if (x + y) % 4 == 0 else "#7ab060"
            s.paint(s.m_px([(x + round(sway * (26 - y) / 6), y)]), col, within=m)
    s.ellipse(16, 23, 2.2, 0.9, "#c8d888", shade=False)


@sprite("pink_warty_sea_cucumber")
def _(s):
    # A plump pink sea cucumber covered in round, darker warts.
    s.can("walk")
    st = s.cyc(0, 1, 2, 1) if s.act == "walk" else 0
    c = "#e08a9a"
    m = s.ellipse(17 - st / 2, 23, 13 + st / 2, 5.5, c, edge=True)
    s.paint(s.m_ellipse(17, 27, 12, 1.6), "#f0b8c0", within=m)
    for x, y in ((8, 20), (12, 18), (17, 18), (22, 19), (26, 21), (10, 23), (15, 22), (20, 22), (25, 24), (14, 25)):
        s.paint(s.m_ellipse(x, y, 1.1, 1.0), "#b8506a", within=m)
        s.paint(s.m_px([(x, y - 1)]), "#f4c8d0", within=m)
    for x in (3, 5, 7):
        s.ellipse(x - st, 21 + abs(x - 5) * 0.6, 1.1, 1.1, "#f0c8d0")
