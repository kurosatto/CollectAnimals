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
from species_eu_birds import _song


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
