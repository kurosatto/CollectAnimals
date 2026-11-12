"""Sprites for the European (and Turkish) birds that the US lists don't have.
Imported by make_sprites.py, which registers the drawings via @sprite.

Songbirds go through _song(), a bird() call plus the usual field marks drawn on
the head (cap, eye stripe, brow, bib, cheek, eye ring) in bird()'s own head
coordinates (head centre 11, 11, eye at 8, 10), so they follow the head in every pose."""
from __future__ import annotations

from archetypes import (BLACK, EYE, WHITE, _far_wing, _ripples, _slim, _wing_beat, bird, cormorant, duck,
                        flying_waterbird, gull, owl, pelican, raptor, sprite, vulture, wader)
from pixel import mix

HEAD = (11, 11, 6.5, 6)


def _dk(c, k=0.28):
    return mix(c, "#1a1420", k)


def _song(s, body, belly, *, head=None, wing=None, tail_col=None, beak="thin", beak_col="#2b2630",
          legs="#6a5a50", tail="mid", cap=None, mask=None, brow=None, bib=None, throat=None, cheek=None,
          ring=None, stache=None, nape=None, wingbar=None, wingbar2=None, wingpatch=None, streaks=None,
          breast=None, spots=None, flank=None, crest=None, eye_col=EYE, big=False, face=None, wingm=None,
          bellym=None):
    """bird() with the common field marks; each mark is a colour (or None)."""
    def _face(s):
        h = s.last
        if throat:
            s.paint(s.m_ellipse(8.5, 15, 4.2, 2.8), throat, within=h)
        if cheek:
            s.paint(s.m_ellipse(10.5, 13, 3.4, 2.2), cheek, within=h)
        if cap:
            s.paint(s.m_ellipse(11.5, 6.8, 6.5, 3.3), cap, within=h)
        if nape:
            s.paint(s.m_ellipse(15.5, 10, 2.4, 3.4), nape, within=h)
        if brow:
            s.paint(s.m_line(6, 8, 15, 8.5), brow, within=h)
        if mask:
            s.paint(s.m_line(4, 10, 14, 10.5) | s.m_line(5, 11, 13, 11.5), mask, within=h)
        if stache:
            s.paint(s.m_line(6, 13.5, 10, 15.5), stache, within=h)
        if bib:
            s.paint(s.m_ellipse(6.5, 15.5, 3.2, 2.2), bib, within=h)
        if ring:
            s.paint(s.m_ellipse(8.4, 10.4, 1.9, 1.9) & ~s.m_ellipse(8.4, 10.4, 1.1, 1.1), ring, within=h)
        if face:
            face(s, h)

    def _wing(s, m):
        if wingpatch:
            s.paint(s.m_ellipse(19, 19.5, 3, 1.8, rot=-15), wingpatch, within=m)
        if wingbar:
            s.paint(s.m_line(16, 19, 23, 16.5), wingbar, within=m)
        if wingbar2:
            s.paint(s.m_line(17, 21.5, 23, 19.5), wingbar2, within=m)
        if wingm:
            wingm(s, m)

    def _belly(s, m):
        if breast:
            s.paint(s.m_ellipse(11.5, 19.5, 4.6, 2.6), breast, within=m)
        if flank:
            s.paint(s.m_ellipse(16, 23, 3, 2), flank, within=m)
        if streaks:
            s.paint(s.m_px([(10, 20), (12, 21), (14, 20), (11, 23), (13, 24), (15, 22), (9, 22), (16, 24)]),
                    streaks, within=m)
        if spots:
            s.paint(s.m_px([(10, 19), (12, 20), (14, 19), (10, 22), (13, 23), (15, 21), (11, 25), (14, 25),
                            (16, 23)]), spots, within=m)
        if bellym:
            bellym(s, m)
    bird(s, body, belly, head=head, wing=wing, tail_col=tail_col, beak=beak, beak_col=beak_col, legs=legs,
         tail=tail, crest=crest, eye_col=eye_col, face=_face, wing_mark=_wing, belly_mark=_belly, big=big)


# --------------------------------------------------------------------------- thrushes, chats, flycatchers
@sprite("european_robin")
def _(s):
    # Round and olive-brown with an orange-red face and breast edged in blue-gray.
    _song(s, "#8a7458", "#f2ece2", head="#8a7458", wing="#7a644a", tail_col="#6e5a44", legs="#a08a7a",
          face=lambda s, h: (s.paint(s.m_ellipse(8, 14, 5, 4.6), "#9ab0c0", within=h),
                             s.paint(s.m_ellipse(7.5, 13.5, 4.4, 4.2), "#e0702e", within=h)),
          breast="#e0702e")


@sprite("eurasian_blackbird")
def _(s):
    # The male: all glossy black, with a bright orange-yellow bill and eye ring.
    _song(s, "#1e1c22", "#26242a", head="#1e1c22", wing="#1a181e", tail_col="#141218", beak_col="#f0a020",
          legs="#4a3e36", ring="#f0b020", tail="long")


@sprite("song_thrush")
def _(s):
    # Warm brown above, cream below covered in neat dark arrowhead spots.
    _song(s, "#8a6c4c", "#f4ecd8", wing="#7a5e40", tail_col="#7a5e40", legs="#d8a8a0", spots="#4a3424",
          breast="#f0d8a8", beak_col="#4a3a30")


@sprite("mistle_thrush")
def _(s):
    # Bigger and grayer than the song thrush, with bold round black spots and pale wing edges.
    _song(s, "#8a8070", "#f4f0e4", wing="#7a7060", tail_col="#7a7060", legs="#d8b0a0", spots="#2b2226",
          wingbar="#d8d0c0", beak_col="#4a3a30", big=True)


@sprite("fieldfare")
def _(s):
    # A colorful thrush: blue-gray head and rump, chestnut back, a rusty-yellow spotted breast.
    _song(s, "#8a5a3a", "#f4f0ea", head="#8a909c", wing="#7a4e32", tail_col="#2b2630", legs="#4a3e36",
          breast="#e8b060", spots="#2b2226", beak_col="#e8c040", mask="#4a4a54")


@sprite("redwing")
def _(s):
    # A small thrush with a bold cream eyebrow and rusty-red flanks under the wing.
    _song(s, "#7a6248", "#f4f0e8", wing="#6a5440", tail_col="#6a5440", legs="#d8b0a0", brow="#f4ead0",
          streaks="#4a3a2c", flank="#c8402a", beak_col="#3a302a")


@sprite("blue_rock_thrush")
def _(s):
    # The male is dusky blue all over, with darker wings.
    _song(s, "#3e5a8a", "#4a6898", head="#4a6898", wing="#2e3e5e", tail_col="#2a3450", legs="#2b2630",
          beak_col="#1e1c22", tail="long")


@sprite("black_redstart")
def _(s):
    # Sooty gray-black with a white wing flash and a shivering rusty-red tail.
    _song(s, "#4a4a50", "#3a3a40", head="#3e3e44", wing="#3a3a40", tail_col="#d0602a", legs="#2b2630",
          bib="#1e1c22", throat="#2a282e", wingpatch="#e8e8e8")


@sprite("common_redstart")
def _(s):
    # Gray back, black face, white forehead, an orange breast and a fiery red-orange tail.
    _song(s, "#7a7e88", "#e8783a", head="#7a7e88", wing="#6a6058", tail_col="#d8582a", legs="#2b2630",
          throat="#1e1c22", cap="#7a7e88",
          face=lambda s, h: s.paint(s.m_line(5, 8, 10, 8), WHITE, within=h))


@sprite("northern_wheatear")
def _(s):
    # Blue-gray back, a black mask, a white eyebrow, buff breast and black wings.
    _song(s, "#8a929c", "#f2e8d8", head="#8a929c", wing="#2b2630", tail_col="#2b2630", legs="#1e1c22",
          mask="#1e1c22", brow=WHITE, breast="#e8c89a")


@sprite("eastern_black_eared_wheatear")
def _(s):
    # Creamy-buff with a black eye patch and black wings.
    _song(s, "#e8d8b8", "#f6f0e4", head="#ecdcc0", wing="#1e1c22", tail_col="#2b2630", legs="#1e1c22",
          mask="#1e1c22", cheek="#1e1c22")


@sprite("cyprus_wheatear")
def _(s):
    # Black and white like a little magpie: black back and throat, white crown and belly, buff breast.
    _song(s, "#1e1c22", "#f4ead8", head="#1e1c22", wing="#1a181e", tail_col="#1e1c22", legs="#1e1c22",
          cap=WHITE, throat="#1e1c22", breast="#e8c890")


@sprite("european_stonechat")
def _(s):
    # A black head, white half-collar, orange breast and dark back, perched upright.
    _song(s, "#3a3230", "#f0e4d4", head="#1e1c22", wing="#2e2826", tail_col="#2b2630", legs="#1e1c22",
          breast="#d8682e", wingpatch="#f0ece4",
          face=lambda s, h: s.paint(s.m_ellipse(13, 15.5, 3, 1.6), WHITE, within=h))


@sprite("whinchat")
def _(s):
    # Streaky brown with a bold cream eyebrow and an apricot-orange throat and breast.
    _song(s, "#8a6a48", "#f4ecdc", head="#6a5038", wing="#6a5038", tail_col="#4a3a2a", legs="#2b2630",
          brow="#f4ecd8", cheek="#3a2a1e", breast="#e8a060", throat="#ecb070", wingbar=WHITE)


@sprite("european_pied_flycatcher")
def _(s):
    # The male: black above and white below, a white forehead spot and a big white wing patch.
    _song(s, "#1e1c22", "#f6f4f0", head="#1e1c22", wing="#1e1c22", tail_col="#1e1c22", legs="#2b2630",
          wingpatch="#f6f4f0", face=lambda s, h: s.paint(s.m_ellipse(6.5, 8, 1.5, 1.2), WHITE, within=h))


@sprite("spotted_flycatcher")
def _(s):
    # Plain gray-brown, upright, with fine streaks on the crown and breast.
    _song(s, "#8a8070", "#f2eee6", wing="#7a7060", tail_col="#6a6050", legs="#2b2630", streaks="#9a8e7e",
          face=lambda s, h: s.paint(s.m_px([(9, 6), (11, 5), (13, 6), (10, 7), (12, 7)]), "#5a5040", within=h))


@sprite("dunnock")
def _(s):
    # A quiet, sparrow-like bird with a slate-gray head and breast and a streaky brown back.
    _song(s, "#7a5a40", "#8a8a92", head="#7a7c86", wing="#6a4a32", tail_col="#5a4430", legs="#d8a080",
          breast="#7a7c86", streaks="#5a4a3e", cheek="#8a6a50",
          wingm=lambda s, m: s.paint(s.m_px([(17, 17), (19, 19), (21, 17), (23, 18), (18, 21)]), "#2e2218",
                                     within=m))


@sprite("eurasian_wren")
def _(s):
    # A tiny round brown ball with a cocked-up tail, a pale eyebrow and fine dark barring.
    _song(s, "#8a5c38", "#c8a07a", head="#8a5c38", wing="#7a4e2e", tail_col="#7a4e2e", legs="#c8a080",
          brow="#e8d4b8", tail="short",
          wingm=lambda s, m: s.paint(s.m_px([(17, 18), (19, 18), (21, 18), (18, 20), (20, 20), (22, 20)]),
                                     "#3a2618", within=m))
    s.poly([(20, 19), (27, 9), (29, 10), (23, 21)], "#7a4e2e")


@sprite("white_throated_dipper")
def _(s):
    # A plump dark brown stream bird with a big white bib, bobbing on rocks.
    _song(s, "#3a2e2a", "#5a3a2a", head="#5a4030", wing="#2e2622", tail_col="#2e2622", legs="#6a5a52",
          throat=WHITE, breast=WHITE, tail="short", big=True)


# --------------------------------------------------------------------------- warblers, tits and kin
@sprite("eurasian_blackcap")
def _(s):
    # Plain gray-olive with a neat black cap (brown on the female).
    _song(s, "#8a8a80", "#d8d8d0", head="#9a9a94", wing="#7a7a70", tail_col="#6a6a62", cap="#1e1c22")


@sprite("common_chiffchaff")
def _(s):
    # A small olive-brown leaf warbler with a short pale eyebrow and dark legs.
    _song(s, "#8a8a62", "#e8e4cc", wing="#7a7a54", tail_col="#6a6a4a", legs="#2b2630", brow="#e8e4c4",
          mask="#6a6a4a")


@sprite("wood_warbler")
def _(s):
    # Bright green above with a yellow eyebrow and throat and a clean white belly.
    _song(s, "#8aa04a", "#f8f6ee", wing="#7a8e40", tail_col="#6a7a3a", legs="#d8b080", brow="#f0e040",
          throat="#f0e450", mask="#6a7a3a")


@sprite("greater_whitethroat")
def _(s):
    # Gray head, a puffed white throat, rusty-brown wings and a long tail.
    _song(s, "#9a8a70", "#f0e4d8", head="#8a8a90", wing="#b07a48", tail_col="#6a5a4a", legs="#d8b090",
          throat=WHITE, ring="#e8e0d0", tail="long")


@sprite("sardinian_warbler")
def _(s):
    # Gray with a glossy black hood, a white throat and a bright red eye ring.
    _song(s, "#6a6a72", "#e8e6e6", head="#1e1c22", wing="#5a5a62", tail_col="#2b2630", legs="#d0a890",
          throat=WHITE, ring="#e0302a", eye_col="#8a2018", tail="long")


@sprite("zitting_cisticola")
def _(s):
    # A tiny streaky buff warbler with a short fanned tail tipped in black and white.
    _song(s, "#c8a070", "#f4ead8", wing="#a07a50", tail_col="#6a4a30", legs="#e0b8a0", tail="short",
          wingm=lambda s, m: s.paint(s.m_px([(17, 17), (19, 18), (21, 17), (23, 18), (18, 20), (22, 20)]),
                                     "#3a2a1e", within=m),
          face=lambda s, h: s.paint(s.m_px([(10, 6), (12, 6), (14, 7), (11, 7)]), "#3a2a1e", within=h))


@sprite("great_tit")
def _(s):
    # A black head with white cheeks, a yellow belly with a black stripe down the middle, and a green back.
    _song(s, "#6a8a5a", "#f0d840", head="#1e1c22", wing="#5a6a7a", tail_col="#4a5a6a", legs="#6a7080",
          cheek=WHITE, wingbar=WHITE,
          bellym=lambda s, m: s.paint(s.m_line(13, 18, 14, 27) | s.m_line(12, 18, 13, 27), "#1e1c22", within=m))


@sprite("eurasian_blue_tit")
def _(s):
    # Tiny and bright: a sky-blue cap, white face with a dark eye stripe, yellow belly, blue wings.
    _song(s, "#8aa060", "#f2dc4a", head=WHITE, wing="#4a80c8", tail_col="#3a6ab0", legs="#6a7080",
          cap="#3a80d0", mask="#1e2a4a", wingbar=WHITE,
          face=lambda s, h: s.paint(s.m_ellipse(9, 16, 3.5, 1.4), "#1e2a4a", within=h))


@sprite("coal_tit")
def _(s):
    # A tiny tit with a glossy black cap and bib, white cheeks and a white patch on the nape.
    _song(s, "#7a7e88", "#ecdcc8", head="#1e1c22", wing="#6a6e78", tail_col="#5a5e68", legs="#5a5e68",
          cheek=WHITE, nape=WHITE, wingbar=WHITE, wingbar2=WHITE, tail="short")


@sprite("marsh_tit")
def _(s):
    # Plain brown with a neat glossy black cap, a tiny black bib and pale cheeks.
    _song(s, "#9a8a74", "#ece6dc", head="#ece6dc", wing="#8a7a64", tail_col="#7a6a56", legs="#4a4a54",
          cap="#1e1c22", bib="#1e1c22")


@sprite("long_tailed_tit")
def _(s):
    # A tiny pink, black and white ball with a very long tail.
    _song(s, "#e8c0c8", "#f4ecec", head=WHITE, wing="#2b2630", tail_col="#1e1c22", legs="#2b2630",
          beak="cone", beak_col="#1e1c22", tail="long", brow="#1e1c22",
          wingm=lambda s, m: s.paint(s.m_line(17, 18, 23, 16) | s.m_line(17, 19, 23, 17), "#e8a8b8", within=m))
    s.path([(22, 19), (31, 12), (35, 8)], (1.1, 0.6), "#1e1c22")


@sprite("eurasian_nuthatch")
def _(s):
    # Blue-gray above, apricot below, with a long black eye stripe and a dagger bill; it climbs down trees headfirst.
    _song(s, "#6a80a0", "#e8b880", head="#6a80a0", wing="#5a7090", tail_col="#4a5a78", legs="#a08a7a",
          beak="crow", beak_col="#2b2630", mask="#1e1c22", throat=WHITE, tail="short", flank="#b8603a")


# --------------------------------------------------------------------------- finches, sparrows, buntings
@sprite("common_chaffinch")
def _(s):
    # The male: a blue-gray cap, pinkish-orange face and breast, chestnut back and two white wing bars.
    _song(s, "#8a5a3a", "#e8b0a0", head="#d88a70", wing="#3a3a44", tail_col="#3a3a44", beak="cone",
          beak_col="#9aa0b0", legs="#a08070", cap="#6a80a0", nape="#6a80a0", wingbar=WHITE, wingbar2="#f0e8a0",
          breast="#d88a70")


@sprite("brambling")
def _(s):
    # A black head and back, orange shoulders and breast, a white rump and belly.
    _song(s, "#2b2226", "#f6f0e8", head="#2b2226", wing="#2b2226", tail_col="#1e1a1e", beak="cone",
          beak_col="#e8c050", legs="#a08070", breast="#e8902e", wingbar="#e8902e", wingbar2=WHITE,
          flank="#2b2226")


@sprite("european_goldfinch")
def _(s):
    # A red face, black and white head, buff back and black wings with a broad gold bar.
    _song(s, "#c8a07a", "#f6f0e6", head=WHITE, wing="#1e1c22", tail_col="#1e1c22", beak="cone",
          beak_col="#f0dcc8", legs="#d8b0a0", nape="#1e1c22", breast="#d8b08a",
          face=lambda s, h: (s.paint(s.m_ellipse(6.5, 11, 3, 3.3), "#d8202a", within=h),
                             s.paint(s.m_ellipse(14, 9, 2.6, 4.5), "#1e1c22", within=h)),
          wingpatch="#f2cc20")


@sprite("european_greenfinch")
def _(s):
    # Olive-green with bright yellow flashes on the wing and tail edges and a thick pale bill.
    _song(s, "#7a9a40", "#b8cc50", head="#7a9a40", wing="#6a7a50", tail_col="#5a6a40", beak="cone",
          beak_col="#e8c8b0", legs="#d8b0a0", wingbar="#f0e020", mask="#5a6a40")


@sprite("european_serin")
def _(s):
    # A tiny streaky canary: bright yellow head and breast, a stubby bill, streaky flanks.
    _song(s, "#a8a050", "#f2ec80", head="#e8e040", wing="#7a7a40", tail_col="#6a6a3a", beak="cone",
          beak_col="#8a8a80", legs="#d8b0a0", breast="#f0e030", streaks="#6a6a3a", tail="short",
          cheek="#a8a050")


@sprite("eurasian_siskin")
def _(s):
    # A small yellow-green finch with a black cap and bib and yellow wing bars.
    _song(s, "#90a040", "#f0f0b0", head="#d8d840", wing="#2b2630", tail_col="#2b2630", beak="cone",
          beak_col="#c8b8a0", legs="#a08070", cap="#1e1c22", bib="#1e1c22", wingbar="#f0e030",
          streaks="#6a6a3a", tail="short")


@sprite("eurasian_linnet")
def _(s):
    # Chestnut back, gray head, a crimson forehead and breast on the male.
    _song(s, "#a06a40", "#f0e4d8", head="#8a8a90", wing="#8a5a36", tail_col="#3a3034", beak="cone",
          beak_col="#7a7a80", legs="#a08070", breast="#d8304a", wingbar=WHITE,
          face=lambda s, h: s.paint(s.m_ellipse(7, 6.5, 2.2, 1.5), "#d8304a", within=h))


@sprite("eurasian_bullfinch")
def _(s):
    # A plump finch with a glossy black cap, gray back, rose-red breast and a stubby black bill.
    _song(s, "#8a8a92", "#e85a4a", head="#e85a4a", wing="#2b2630", tail_col="#1e1c22", beak="cone",
          beak_col="#1e1c22", legs="#6a5a50", cap="#1e1c22", wingbar=WHITE, big=True,
          face=lambda s, h: s.paint(s.m_ellipse(5.5, 11, 1.8, 2.5), "#1e1c22", within=h))


@sprite("eurasian_tree_sparrow")
def _(s):
    # A chestnut cap, white cheeks with a black spot, a small black bib and streaky brown back.
    _song(s, "#a0704a", "#ece4d8", head=WHITE, wing="#a07048", tail_col="#7a5a40", beak="cone",
          beak_col="#2b2630", legs="#c8a080", cap="#8a4a28", bib="#1e1c22", wingbar=WHITE,
          face=lambda s, h: s.paint(s.m_ellipse(11.5, 13, 1.4, 1.2), "#1e1c22", within=h),
          wingm=lambda s, m: s.paint(s.m_line(16, 18, 23, 16), "#3a2a20", within=m))


@sprite("italian_sparrow")
def _(s):
    # Like a house sparrow with a rich chestnut crown and clean white cheeks.
    _song(s, "#a0704a", "#ece6dc", head=WHITE, wing="#a8784c", tail_col="#7a5a40", beak="cone",
          beak_col="#3a3430", legs="#c99060", cap="#8a4a28", bib="#1e1c22", mask="#8a4a28", wingbar=WHITE)


@sprite("spanish_sparrow")
def _(s):
    # A chestnut crown, a big black bib running into heavy black streaks down the flanks.
    _song(s, "#a0704a", "#f0ece4", head=WHITE, wing="#a8784c", tail_col="#5a4430", beak="cone",
          beak_col="#3a3430", legs="#c99060", cap="#8a4a28", bib="#1e1c22", breast="#1e1c22",
          streaks="#1e1c22", wingbar=WHITE)


@sprite("yellowhammer")
def _(s):
    # The male: a bright yellow head and belly, a chestnut-streaked back and rump.
    _song(s, "#a8703a", "#f2d830", head="#f2d830", wing="#8a5a30", tail_col="#5a4430", beak="cone",
          beak_col="#7a7a80", legs="#d8b090", streaks="#b8682a",
          face=lambda s, h: s.paint(s.m_line(9, 12, 14, 12) | s.m_px([(12, 6), (14, 7)]), "#8a7a3a", within=h),
          wingm=lambda s, m: s.paint(s.m_px([(17, 17), (19, 19), (21, 17), (23, 18)]), "#3a2a1e", within=m))


@sprite("cirl_bunting")
def _(s):
    # A yellow face crossed by a black eye stripe and black throat, an olive-gray breast band.
    _song(s, "#9a6a40", "#f2dc50", head="#f0dc50", wing="#8a5a36", tail_col="#5a4430", beak="cone",
          beak_col="#6a6a70", legs="#d8b090", cap="#7a7a5a", mask="#1e1c22", bib="#1e1c22", breast="#8a9a6a",
          flank="#b8703a")


@sprite("corn_bunting")
def _(s):
    # A chunky, plain streaky-brown bunting with a big pale bill.
    _song(s, "#a08a68", "#ece4d0", head="#a08a68", wing="#8a7656", tail_col="#7a6648", beak="cone",
          beak_col="#e0c8a0", legs="#e0b8a0", streaks="#5a4a38", big=True,
          wingm=lambda s, m: s.paint(s.m_px([(17, 17), (19, 19), (21, 17), (23, 18), (20, 21)]), "#5a4a38",
                                     within=m))


@sprite("reed_bunting")
def _(s):
    # The male: a black head and bib, a white collar and moustache, a streaky brown back.
    _song(s, "#9a6e48", "#ece8e0", head="#1e1c22", wing="#8a5e3a", tail_col="#4a3a2e", beak="cone",
          beak_col="#3a3430", legs="#a08070", stache=WHITE, streaks="#8a7a6a",
          face=lambda s, h: s.paint(s.m_ellipse(14, 16, 3, 1.4), WHITE, within=h),
          wingm=lambda s, m: s.paint(s.m_px([(17, 17), (19, 19), (21, 17), (23, 18)]), "#2b2226", within=m))


@sprite("snow_bunting")
def _(s):
    # Mostly snow-white, with a black back and black wing tips in summer.
    _song(s, "#1e1c22", "#f8f8f6", head="#f8f8f6", wing="#f4f4f2", tail_col="#1e1c22", beak="cone",
          beak_col="#1e1c22", legs="#1e1c22",
          wingm=lambda s, m: s.paint(s.m_ellipse(24, 18, 3, 2, rot=-15), "#1e1c22", within=m))


# --------------------------------------------------------------------------- larks, pipits, wagtails, swallows
@sprite("crested_lark")
def _(s):
    # Sandy-brown and streaky, with a tall spiky crest and a long bill.
    _song(s, "#a89070", "#ece4d4", wing="#988060", tail_col="#7a6648", beak="thin", beak_col="#8a7a6a",
          legs="#d8b090", streaks="#6a5640", crest="jay", brow="#e8dcc4",
          wingm=lambda s, m: s.paint(s.m_px([(17, 17), (19, 19), (21, 17), (23, 18)]), "#5a4630", within=m))


@sprite("meadow_pipit")
def _(s):
    # A small streaky olive-brown bird with a spotted breast and long hind claws.
    _song(s, "#8a7a5a", "#ece4d0", wing="#7a6a4a", tail_col="#5a4a38", legs="#e0b8a0", streaks="#3a2e22",
          brow="#e0d4bc",
          wingm=lambda s, m: s.paint(s.m_px([(17, 17), (19, 19), (21, 17), (23, 18)]), "#3a2e22", within=m))


@sprite("rock_pipit")
def _(s):
    # A darker, grayer coastal pipit with smudgy streaks and dark legs.
    _song(s, "#6e6a5e", "#cfc8b4", wing="#5e5a4e", tail_col="#4a463e", legs="#4a3e36", streaks="#3a362e",
          brow="#c8c0ac")


@sprite("white_wagtail")
def _(s):
    # Black, white and gray, with a long tail it wags constantly.
    _song(s, "#8a8c92", WHITE, head=WHITE, wing="#4a4a50", tail_col="#1e1c22", legs="#1e1c22", tail="long",
          cap="#1e1c22", bib="#1e1c22", throat="#1e1c22", wingbar=WHITE)


@sprite("grey_wagtail")
def _(s):
    # Blue-gray back, a bright lemon-yellow belly and rump, a black throat and a very long tail.
    _song(s, "#7a8090", "#f2dc40", head="#7a8090", wing="#2b2630", tail_col="#2b2630", legs="#d8b0a0",
          tail="long", brow=WHITE, throat="#1e1c22")


@sprite("western_yellow_wagtail")
def _(s):
    # Olive-green above, canary-yellow below, with a blue-gray head on many males.
    _song(s, "#8a9a48", "#f4e030", head="#7a8aa8", wing="#4a4a3a", tail_col="#2b2630", legs="#2b2630",
          tail="long", brow=WHITE, throat="#f4e030", wingbar="#e8e8c0")


@sprite("western_house_martin")
def _(s):
    # Glossy blue-black above with a bright white rump and pure white underparts; a short forked tail.
    _song(s, "#1e2a4a", WHITE, head="#1e2a4a", wing="#1a2440", tail_col="#1a2440", legs=WHITE, beak="thin",
          beak_col="#1e1c22", tail="short", throat=WHITE)
    s.px([(28, 17), (29, 18), (28, 21), (29, 21)], "#1a2440")


@sprite("european_red_rumped_swallow")
def _(s):
    # A dark-blue swallow with a rusty collar and rump, streaky buff underparts and long tail streamers.
    s.path([(22, 19), (28, 16), (35, 15)], (1.3, 0.4), "#1e2a4a")
    s.path([(22, 21), (28, 22), (35, 24)], (1.3, 0.4), "#1e2a4a")
    _song(s, "#1e2a4a", "#f2e0c4", head="#1e2a4a", wing="#1a2440", tail_col="#1a2440", legs="#3a3034",
          beak_col="#1a1820", tail="short", throat="#f2e0c4", nape="#d8783a", streaks="#a08a70")


# --------------------------------------------------------------------------- shrikes, starlings, others
@sprite("red_backed_shrike")
def _(s):
    # A chestnut back, a blue-gray head with a black bandit mask and a hooked bill.
    _song(s, "#a85a38", "#f2dcd4", head="#8a909c", wing="#9a5232", tail_col="#2b2630", beak="hook",
          beak_col="#1e1c22", legs="#2b2630", mask="#1e1c22", tail="long")


@sprite("woodchat_shrike")
def _(s):
    # A rusty-chestnut crown and nape, a black mask and back, white shoulders and belly.
    _song(s, "#1e1c22", WHITE, head="#d0682e", wing="#1e1c22", tail_col="#1e1c22", beak="hook",
          beak_col="#1e1c22", legs="#2b2630", mask="#1e1c22", wingpatch=WHITE, tail="long",
          face=lambda s, h: s.paint(s.m_ellipse(7, 14.5, 3.5, 2.2), WHITE, within=h))


@sprite("masked_shrike")
def _(s):
    # Black and white with a white forehead and eyebrow, a black mask and orange flanks.
    _song(s, "#1e1c22", WHITE, head="#1e1c22", wing="#1e1c22", tail_col="#1e1c22", beak="hook",
          beak_col="#1e1c22", legs="#2b2630", brow=WHITE, throat=WHITE, wingpatch=WHITE, flank="#e8902e",
          tail="long", face=lambda s, h: s.paint(s.m_ellipse(6, 8, 1.6, 1.2), WHITE, within=h))


@sprite("spotless_starling")
def _(s):
    # Like a starling but glossy all-black with no spots, and pink legs.
    _song(s, "#1e1a24", "#26222c", head="#1e1a2a", wing="#1a1820", tail_col="#141218", beak_col="#f0d020",
          legs="#e8a090", tail="short",
          wingm=lambda s, m: s.paint(s.m_ellipse(18, 18, 2.4, 1.4), "#3a2a4a", within=m))


@sprite("white_spectacled_bulbul")
def _(s):
    # Gray-brown with a dark head, a white ring round the eye and bright yellow under the tail.
    _song(s, "#8a8070", "#e8e4dc", head="#2b2630", wing="#7a7060", tail_col="#5a5048", legs="#2b2630",
          ring=WHITE, tail="long",
          bellym=lambda s, m: s.paint(s.m_ellipse(18, 25, 2.5, 1.6), "#f0d020", within=m))


@sprite("common_hoopoe")
def _(s):
    # Pinkish-cinnamon with a big black-tipped fan crest, bold black-and-white zebra wings and a long curved bill.
    def crest(s, h):
        s.poly([(10, 6), (8, -1), (12, -2), (15, -1), (18, 2), (16, 6)], "#e0a070")
        s.px([(8, -1), (12, -2), (15, -1), (18, 2)], "#1e1c22")
    def bars(s, m):
        for x in (16, 19, 22, 25):
            s.paint(s.m_line(x, 14, x - 1, 24) | s.m_line(x + 1, 14, x, 24), WHITE, within=m)
    _song(s, "#e0a070", "#ecc4a0", head="#e0a070", wing="#1e1c22", tail_col="#1e1c22", beak="thin",
          beak_col="#2b2630", legs="#4a4a50", face=crest, wingm=bars)
    s.path([(5.5, 11.5), (2, 12.5), (-1, 14), (-2, 15.5)], (0.6, 0.4), "#2b2630", shade=False)


@sprite("european_bee_eater")
def _(s):
    # A rainbow: chestnut crown and back, golden shoulders, yellow throat edged in black, turquoise belly, a long curved bill.
    s.path([(24, 18), (31, 15.5), (34, 15)], (0.8, 0.4), "#3a9a8a")
    _song(s, "#c87a3a", "#4ab8b0", head="#8a3a20", wing="#5aa06a", tail_col="#4a9a7a", beak="long",
          beak_col="#1e1c22", legs="#4a3e36", mask="#1e1c22", throat="#f2d040",
          face=lambda s, h: s.paint(s.m_line(6, 17, 12, 17), "#1e1c22", within=h),
          wingm=lambda s, m: s.paint(s.m_ellipse(18, 16.5, 3.5, 1.6), "#e0a830", within=m),
          eye_col="#c02a2a")


@sprite("european_roller")
def _(s):
    # A crow-sized turquoise bird with a chestnut back and dazzling blue wings.
    _song(s, "#a8683e", "#5ac0d0", head="#5ac0d0", wing="#2a5ab0", tail_col="#3a8ab8", beak="crow",
          beak_col="#1e1c22", legs="#4a3e36", mask="#3a3a40", big=True,
          wingm=lambda s, m: s.paint(s.m_ellipse(18, 17, 3, 1.8), "#a8683e", within=m))


@sprite("common_kingfisher")
def _(s):
    # A dazzling blue back and crown, orange cheeks and belly, a white throat and a long dagger bill.
    def face(s):
        h = s.last
        s.paint(s.m_ellipse(10.5, 7, 6, 3), "#2a7ac8", within=h)
        s.paint(s.m_ellipse(10, 11, 5, 1.6), "#e8782e", within=h)
        s.paint(s.m_ellipse(7, 15, 3, 1.8), WHITE, within=h)
        s.paint(s.m_ellipse(14.5, 12.5, 1.6, 1.4), WHITE, within=h)
    bird(s, "#2a90c8", "#e8782e", head="#2a7ac8", wing="#1e70a8", tail_col="#1e5a98", beak="long",
         beak_col="#1e1c22", legs="#e04a2a", tail="short", face=face,
         wing_mark=lambda s, m: s.paint(s.m_px([(17, 17), (19, 18), (21, 17), (18, 20)]), "#6ad0f0", within=m))
    s.px([(20, 12), (21, 13)], "#5ad8f0")


@sprite("monk_parakeet")
def _(s):
    # A bright green parrot with a pale gray forehead, face and scalloped breast, and a long pointed tail.
    s.path([(22, 18), (30, 13), (34, 7)], (2.0, 0.8), "#4aa04a")
    _song(s, "#5ab05a", "#b8c0b8", head="#6ab86a", wing="#3a8a4a", tail_col="#4aa04a", beak="hook",
          beak_col="#e8b890", legs="#8a8a90", tail="long",
          face=lambda s, h: s.paint(s.m_ellipse(8, 12.5, 4.5, 5), "#c8ccc8", within=h),
          breast="#c0c8c0",
          wingm=lambda s, m: s.paint(s.m_line(20, 22, 26, 20), "#2a5ab0", within=m))


# --------------------------------------------------------------------------- crows
@sprite("carrion_crow")
def _(s):
    # All glossy black, a stout bill with bristles at the base.
    bird(s, "#1e1c24", "#26242c", head="#1e1c24", wing="#1a1820", tail_col="#1a1820", beak="crow",
         beak_col="#141218", legs="#1e1c24", tail="mid", big=True)


@sprite("hooded_crow")
def _(s):
    # Ash-gray body with a black head, bib, wings and tail.
    bird(s, "#a0a0a6", "#a8a8ae", head="#1e1c24", wing="#1e1c24", tail_col="#1a1820", beak="crow",
         beak_col="#141218", legs="#1e1c24", tail="mid", big=True,
         face=lambda s: s.paint(s.m_ellipse(9, 16, 4, 2.6), "#1e1c24", within=s.last))
    s.paint(s.m_ellipse(11, 19.5, 3, 1.8), "#1e1c24")


@sprite("rook")
def _(s):
    # Glossy purple-black with a bare, whitish face at the base of its slender bill, and baggy "trousers".
    bird(s, "#221e2c", "#2a2636", head="#221e2c", wing="#1e1a28", tail_col="#1e1a28", beak="crow",
         beak_col="#2b2630", legs="#1e1c24", tail="mid", big=True,
         face=lambda s: s.paint(s.m_ellipse(5.5, 12.5, 2, 2.2), "#d8d0c8", within=s.last))
    s.paint(s.m_ellipse(5, 12.5, 1.6, 1.6), "#d8d0c8")


@sprite("eurasian_jackdaw")
def _(s):
    # A small crow, black with a silvery-gray nape and a pale, staring eye.
    bird(s, "#2a2830", "#34323a", head="#2a2830", wing="#24222a", tail_col="#24222a", beak="cone",
         beak_col="#141218", legs="#1e1c24", tail="mid", eye_col="#e8eef0",
         face=lambda s: s.paint(s.m_ellipse(14, 11, 3.5, 4.5), "#8a8c94", within=s.last))


@sprite("eurasian_magpie")
def _(s):
    # Black and white with a long glossy blue-green tail.
    def wing(s, m):
        s.paint(s.m_ellipse(19, 18, 4, 2, rot=-15), WHITE, within=m)
        s.paint(s.m_line(20, 21, 25, 19), "#3a5ab0", within=m)
    bird(s, "#1f1c26", WHITE, head="#1f1c26", wing="#24202c", tail_col="#2a5a6a", beak="crow",
         beak_col=BLACK, legs="#2a2630", tail="long", wing_mark=wing)
    s.poly([(28, 7), (33, 2), (32, 6)], "#2a5a6a")
    s.paint(s.m_ellipse(11, 20, 4, 2.3), "#1f1c26")


@sprite("eurasian_jay")
def _(s):
    # Pinkish-brown with a black moustache, a streaky crown, a white rump and a patch of bright blue barred wing.
    def wing(s, m):
        s.paint(s.m_ellipse(17.5, 16.5, 3, 1.8), "#3a7ad8", within=m)
        s.paint(s.m_px([(16, 16), (18, 16), (17, 17)]), "#1e1c22", within=m)
        s.paint(s.m_ellipse(22, 19, 2, 1.4), WHITE, within=m)
    def face(s):
        s.paint(s.m_line(6, 13.5, 10, 16), "#1e1c22", within=s.last)
        s.paint(s.m_px([(10, 6), (12, 5), (14, 6), (11, 7)]), "#3a3030", within=s.last)
    bird(s, "#c89a84", "#e8cfc0", head="#d8b8a8", wing="#1e1c22", tail_col="#1e1c22", beak="crow",
         beak_col="#2b2630", legs="#c8a090", tail="mid", crest="jay", face=face, wing_mark=wing,
         eye_col="#7aa0d0")


@sprite("yellow_billed_chough")
def _(s):
    # The Alpine chough: glossy black with a short yellow bill and red legs.
    bird(s, "#1e1c24", "#26242c", head="#1e1c24", wing="#1a1820", tail_col="#1a1820", beak="cone",
         beak_col="#f0d020", legs="#e0302a", tail="long")


# --------------------------------------------------------------------------- doves, woodpeckers, gamebirds
@sprite("common_wood_pigeon")
def _(s):
    # A big blue-gray pigeon with a white neck patch, a pinkish breast and a white bar across the wing.
    _song(s, "#8a8e9c", "#c8a8b0", head="#8a8e9c", wing="#7a7e8c", tail_col="#5a5e6a", beak="thin",
          beak_col="#e8a040", legs="#d88a8a", tail="mid", big=True, breast="#c8a0a8",
          face=lambda s, h: s.paint(s.m_ellipse(14, 15, 2.2, 1.6), WHITE, within=h),
          wingm=lambda s, m: s.paint(s.m_line(16, 19, 22, 17), WHITE, within=m), eye_col="#e8d8a0")


@sprite("european_turtle_dove")
def _(s):
    # A small dove with a black-and-white striped neck patch and scaly rufous-and-black wings.
    def wing(s, m):
        s.paint(s.m_ellipse(20, 19, 5, 3.4, rot=-15), "#c87a40", within=m)
        s.paint(s.m_px([(17, 18), (20, 17), (23, 18), (19, 20), (22, 20), (25, 19)]), "#1e1c22", within=m)
    _song(s, "#a8a0a0", "#e8c8c0", head="#a8a8b0", wing="#8a8890", tail_col="#5a5860", beak="thin",
          beak_col="#3a3438", legs="#d88a8a", tail="long", breast="#d8b0a8", wingm=wing, eye_col="#e0702a",
          face=lambda s, h: s.paint(s.m_line(13, 13, 15, 12) | s.m_line(13, 15, 15, 14), "#1e1c22", within=h))


@sprite("laughing_dove")
def _(s):
    # A small, slim dove: pinkish-brown with a speckled copper-and-black necklace and blue-gray wings.
    _song(s, "#b8826a", "#e8c8b8", head="#c89a8a", wing="#8a96a8", tail_col="#7a7a84", beak="thin",
          beak_col="#3a3438", legs="#d88a8a", tail="long",
          face=lambda s, h: s.paint(s.m_px([(8, 16), (10, 16), (12, 16), (9, 17), (11, 17)]), "#3a2a20",
                                    within=h),
          wingm=lambda s, m: s.paint(s.m_ellipse(17, 17, 3, 1.8, rot=-15), "#b8705a", within=m))


@sprite("great_spotted_woodpecker")
def _(s):
    # Black and white with big white shoulder patches, a red patch under the tail and (on the male) the nape.
    def face(s, h):
        s.paint(s.m_ellipse(11, 7, 4.5, 2.2), BLACK, within=h)
        s.paint(s.m_ellipse(15, 9, 1.8, 1.6), "#e02a2a", within=h)
        s.paint(s.m_path([(6, 14.5), (11, 15), (15, 12)], 0.8), BLACK, within=h)
    _song(s, BLACK, "#f0ece4", head=WHITE, wing=BLACK, tail_col=BLACK, beak="crow", beak_col="#3a3430",
          legs="#5a5a62", tail="short", face=face, wingpatch=WHITE,
          wingm=lambda s, m: s.paint(s.m_px([(22, 21), (24, 20), (20, 22)]), WHITE, within=m),
          bellym=lambda s, m: s.paint(s.m_ellipse(18, 26, 2.6, 1.6), "#e02a2a", within=m))


@sprite("syrian_woodpecker")
def _(s):
    # Like the great spotted woodpecker but without the black bar across its white cheek.
    def face(s, h):
        s.paint(s.m_ellipse(11, 7, 4.5, 2.2), BLACK, within=h)
        s.paint(s.m_ellipse(15, 9, 1.8, 1.6), "#e02a2a", within=h)
        s.paint(s.m_path([(6, 14.5), (11, 15.5)], 0.7), BLACK, within=h)
    _song(s, BLACK, "#f0e8dc", head=WHITE, wing=BLACK, tail_col=BLACK, beak="crow", beak_col="#3a3430",
          legs="#5a5a62", tail="short", face=face, wingpatch=WHITE,
          bellym=lambda s, m: s.paint(s.m_ellipse(18, 26, 2.6, 1.6), "#e87a8a", within=m))


@sprite("eurasian_green_woodpecker")
def _(s):
    # Green above, pale below, with a red crown, a black mask round the white eye and a yellow rump.
    def face(s, h):
        s.paint(s.m_ellipse(11.5, 6.5, 5.5, 2.6), "#e02a2a", within=h)
        s.paint(s.m_ellipse(7.5, 11, 3.5, 2), "#1e1c22", within=h)
        s.paint(s.m_line(6, 14, 10, 15.5), "#1e1c22", within=h)
    _song(s, "#6a9a3a", "#d8e0b0", head="#7aa84a", wing="#5a8a32", tail_col="#4a6a2e", beak="crow",
          beak_col="#3a3430", legs="#6a6a62", tail="short", face=face, eye_col="#f0f0e0",
          wingm=lambda s, m: s.paint(s.m_ellipse(24, 20, 2, 1.4), "#e8e040", within=m))


@sprite("grey_headed_woodpecker")
def _(s):
    # Green with a plain gray head, a thin black moustache and (on the male) a small red forehead.
    def face(s, h):
        s.paint(s.m_ellipse(7, 7, 2.2, 1.4), "#e02a2a", within=h)
        s.paint(s.m_line(6, 14, 9.5, 15), "#1e1c22", within=h)
    _song(s, "#7a9a4a", "#c8d0b0", head="#9aa0a4", wing="#6a8a3e", tail_col="#4a5a3a", beak="crow",
          beak_col="#3a3430", legs="#6a6a62", tail="short", face=face, eye_col="#d8b0a0")


@sprite("chukar")
def _(s):
    # A plump gray-buff partridge, a black line framing a creamy throat, bold black-barred flanks, red bill and legs.
    def bars(s, m):
        for x in (14, 16.5, 19):
            s.paint(s.m_line(x, 20, x + 1, 26), "#1e1c22", within=m)
            s.paint(s.m_line(x + 1, 20, x + 2, 26), "#c8803a", within=m)
    _song(s, "#a89a8a", "#c8b8a8", head="#b0a69a", wing="#9a8e80", tail_col="#a06a40", beak="cone",
          beak_col="#e0302a", legs="#e0302a", tail="short", big=True, bellym=bars, ring="#e04a2a",
          face=lambda s, h: (s.paint(s.m_ellipse(9, 14.5, 4, 2.6), "#f0e4c8", within=h),
                             s.paint(s.m_path([(5, 10.5), (8, 17), (13, 15), (14, 12)], 0.6), "#1e1c22",
                                     within=h)))


@sprite("gray_partridge")
def _(s):
    # A round brown-gray partridge with an orange face and a dark chestnut horseshoe on the belly.
    def bars(s, m):
        for x in (15, 17.5, 20):
            s.paint(s.m_line(x, 20, x + 1, 26), "#8a4a2a", within=m)
        s.paint(s.m_ellipse(12.5, 24, 2.6, 1.8), "#5a2a1a", within=m)
    _song(s, "#8a7a68", "#a8a49c", head="#e08a4a", wing="#7a6a56", tail_col="#a05a30", beak="cone",
          beak_col="#8a8a80", legs="#a09080", tail="short", big=True, bellym=bars, cap="#8a7a68",
          wingm=lambda s, m: s.paint(s.m_px([(17, 17), (19, 18), (21, 17), (23, 18), (20, 20)]), "#e8dcc0",
                                     within=m))


@sprite("rock_ptarmigan")
def _(s):
    # Mottled gray-brown above in summer with white wings and belly, red combs over the eyes, feathered feet.
    _song(s, "#7a705e", WHITE, head="#7a705e", wing=WHITE, tail_col=BLACK, beak="cone", beak_col=BLACK,
          legs=WHITE, tail="short", big=True,
          face=lambda s, h: (s.paint(s.m_line(6, 8, 10, 8) | s.m_line(7, 7, 9, 7), "#e0302a", within=h),
                             s.paint(s.m_line(4, 10, 8, 10.5), "#1e1c22", within=h)),
          bellym=lambda s, m: s.paint(s.m_ellipse(12, 18.5, 4.6, 2.2), "#7a705e", within=m))
    s.ellipse(15, 28.5, 3.5, 1.6, WHITE)


# --------------------------------------------------------------------------- waders and shorebirds
@sprite("northern_lapwing")
def _(s):
    # Glossy green-black back and breast band, white belly and face, and a long wispy crest.
    def face(s, h):
        s.paint(s.m_ellipse(11, 7, 6, 3), "#1e1c22", within=h)
        s.paint(s.m_ellipse(8.5, 15.5, 4, 2.4), "#1e1c22", within=h)
        s.paint(s.m_line(8, 12, 12, 13), "#1e1c22", within=h)
    _song(s, "#2a4a3a", WHITE, head=WHITE, wing="#2a5a42", tail_col="#1e1c22", beak="thin", beak_col="#1e1c22",
          legs="#d88a7a", tail="short", face=face, breast="#1e1c22",
          wingm=lambda s, m: s.paint(s.m_ellipse(19, 17, 2.4, 1.2), "#6a3a6a", within=m),
          bellym=lambda s, m: s.paint(s.m_ellipse(18, 26, 2.6, 1.4), "#e0a060", within=m))
    s.path([(13, 6), (16, 3.5), (19.5, 3)], (0.7, 0.4), "#1e1c22", shade=False)  # the long wispy crest


@sprite("spur_winged_lapwing")
def _(s):
    # A black cap, throat and breast, white cheeks, a sandy-brown back and black legs.
    def face(s, h):
        s.paint(s.m_ellipse(11, 7, 6.5, 4), "#1e1c22", within=h)
        s.paint(s.m_ellipse(7.5, 15.5, 4, 2.6), "#1e1c22", within=h)
    _song(s, "#a89070", WHITE, head=WHITE, wing="#988060", tail_col="#1e1c22", beak="thin", beak_col="#1e1c22",
          legs="#1e1c22", tail="short", face=face, breast="#1e1c22",
          wingm=lambda s, m: s.paint(s.m_ellipse(24, 19, 3, 1.8, rot=-15), "#1e1c22", within=m))


@sprite("european_golden_plover")
def _(s):
    # Spangled gold and black above; in summer, a black face and belly edged in white.
    def gold(s, m):
        s.paint(s.m_px([(16, 17), (18, 18), (20, 17), (22, 18), (24, 19), (17, 20), (21, 20), (19, 21)]),
                "#e8c040", within=m)
    _song(s, "#5a5030", "#1e1c22", head="#6a6040", wing="#4a4228", tail_col="#4a4228", beak="thin",
          beak_col="#1e1c22", legs="#3a3438", tail="short", wingm=gold,
          face=lambda s, h: (s.paint(s.m_ellipse(9, 14, 4.5, 3.6), "#1e1c22", within=h),
                             s.paint(s.m_path([(6, 8.5), (12, 9.5), (15, 15)], 0.6), WHITE, within=h)),
          bellym=lambda s, m: s.paint(s.m_ellipse(14, 18, 5, 1.2), WHITE, within=m))


@sprite("common_ringed_plover")
def _(s):
    # Sandy back, white below, a black breast band and mask, and orange legs and bill base.
    def face(s, h):
        s.paint(s.m_line(4, 10, 13, 11) | s.m_line(5, 11, 12, 12), "#1e1c22", within=h)
        s.paint(s.m_line(6, 7, 10, 7), "#1e1c22", within=h)
        s.paint(s.m_ellipse(8.5, 14, 3, 1.5), WHITE, within=h)
    _song(s, "#a08a6a", WHITE, head="#a08a6a", wing="#968060", tail_col="#7a6a50", beak="thin",
          beak_col="#f08a2a", legs="#f08a2a", tail="short", face=face,
          bellym=lambda s, m: s.paint(s.m_line(8, 17, 17, 17) | s.m_line(8, 18, 17, 18), "#1e1c22", within=m))
    s.px([(1, 12)], "#1e1c22")


@sprite("little_ringed_plover")
def _(s):
    # Smaller than the ringed plover, with a bright yellow eye ring and dull legs.
    def face(s, h):
        s.paint(s.m_line(4, 10, 13, 11) | s.m_line(5, 11, 12, 12), "#1e1c22", within=h)
        s.paint(s.m_line(6, 7, 10, 7), "#1e1c22", within=h)
    _song(s, "#9a8868", WHITE, head="#9a8868", wing="#907e60", tail_col="#7a6a50", beak="thin",
          beak_col="#1e1c22", legs="#c8b070", tail="short", face=face, ring="#f0d020",
          bellym=lambda s, m: s.paint(s.m_line(8, 17, 17, 17), "#1e1c22", within=m))


@sprite("eurasian_oystercatcher")
def _(s):
    # Boldly black and white, with a long straight orange-red bill, red eye and pink legs.
    _song(s, "#1e1c22", WHITE, head="#1e1c22", wing="#1e1c22", tail_col="#1e1c22", beak="long",
          beak_col="#f05a20", legs="#e8a0a0", tail="short", ring="#e0402a", eye_col="#c02020", breast="#1e1c22",
          big=True, wingm=lambda s, m: s.paint(s.m_line(17, 21, 24, 19), WHITE, within=m))
    s.poly([(4, 11), (-3, 12.5), (4, 13.5)], "#f05a20")


def _shorebird(s, back, belly, *, head=None, bill="#1e1c22", bill_len=3, curved=False, legs="#3a3438",
               marks="#3a2e22", breast=None, brow=None, wing_marks=True, tail_col=None, rufous=None):
    """A sandpiper-like bird: bird() with the bill drawn longer (straight or down-curved)."""
    def wing(s, m):
        if wing_marks:
            s.paint(s.m_px([(16, 17), (18, 18), (20, 17), (22, 18), (24, 19), (17, 20), (21, 20), (19, 21)]),
                    marks, within=m)
    _song(s, back, belly, head=head or back, wing=back, tail_col=tail_col or _dk(back, 0.1), beak="thin",
          beak_col=bill, legs=legs, tail="short", wingm=wing, breast=breast, brow=brow,
          streaks=marks if breast else None, cap=rufous)
    if bill_len:  # drawn in bird()'s head coordinates so it follows the head in every pose
        if curved:
            s.path([(5.5, 12), (2.5, 12.6), (0, 14), (-1.5 - bill_len * 0.4, 15.5 + bill_len * 0.4)], (0.8, 0.45),
                   bill, shade=False)
        else:
            s.path([(5.5, 12), (max(-4.5, 1.5 - bill_len), 12.5)], (0.8, 0.45), bill, shade=False)


@sprite("black_tailed_godwit")
def _(s):
    # Long-legged with a very long straight bill, a brick-orange neck and breast in summer.
    _shorebird(s, "#8a6a4a", WHITE, head="#d8783a", bill="#e8a080", bill_len=5, legs="#2b2630", breast="#d8783a",
               marks="#2b2226")


@sprite("common_redshank")
def _(s):
    # Streaky gray-brown with bright orange-red legs and a red base to its bill.
    _shorebird(s, "#8a7a68", "#f0ece4", bill="#c84a2a", bill_len=2, legs="#e8502a", breast="#d8d0c4",
               marks="#4a3e32")


@sprite("eurasian_curlew")
def _(s):
    # A big streaky brown wader with a very long down-curved bill.
    _shorebird(s, "#9a8060", "#ece4d4", bill="#4a3a34", bill_len=5, curved=True, legs="#6a7a80",
               breast="#d8c8a8", marks="#4a3624")


@sprite("eurasian_whimbrel")
def _(s):
    # Like a smaller curlew with a striped crown and a shorter curved bill.
    _shorebird(s, "#8a7458", "#ece4d4", bill="#3a3030", bill_len=2.5, curved=True, legs="#6a7a80",
               breast="#d8c8a8", marks="#3a2a1e", rufous="#4a3a2a", brow="#e8dcc4")


@sprite("common_sandpiper")
def _(s):
    # Olive-brown above and white below, with a white notch in front of the wing; it bobs its tail.
    _shorebird(s, "#7a705a", WHITE, bill="#3a3438", bill_len=0, legs="#9a9a7a", breast="#a8a090",
               marks="#4a4232", brow="#e8e4d8")
    s.paint(s.m_ellipse(14.5, 18.5, 1.2, 1.6), WHITE)


@sprite("wood_sandpiper")
def _(s):
    # Brown back speckled with white, a bold pale eyebrow and yellowish legs.
    _shorebird(s, "#6a5e4a", WHITE, bill="#2b2630", bill_len=0.5, legs="#c8c06a", breast="#d8d4c8",
               marks="#f0ece0", brow="#f4f0e4")


@sprite("purple_sandpiper")
def _(s):
    # A dark slaty, chunky sandpiper of rocky shores, with yellow-orange legs and bill base.
    _shorebird(s, "#4a4650", "#e8e4e4", bill="#e0a040", bill_len=0.5, legs="#e8b030", breast="#8a8690",
               marks="#2b2630")


@sprite("little_stint")
def _(s):
    # A tiny sparrow-sized sandpiper, rusty-orange and black above with a short black bill.
    _shorebird(s, "#b8703a", WHITE, head="#c88048", bill="#1e1c22", bill_len=0, legs="#1e1c22",
               breast="#e8b888", marks="#2b2226")


@sprite("red_knot")
def _(s):
    # A stocky sandpiper with a brick-red face and belly in summer and a mottled back.
    _shorebird(s, "#8a6a4a", "#d0683a", head="#d0683a", bill="#1e1c22", bill_len=1, legs="#4a4a40",
               marks="#2b2226")


@sprite("common_snipe")
def _(s):
    # Cryptic brown with bold buff stripes on the head and back, and a very long straight bill.
    _shorebird(s, "#7a5a3a", "#f0ece4", bill="#8a6a50", bill_len=6, legs="#a0a070", breast="#c8a880",
               marks="#e8d0a0", brow="#e8d0a0", rufous="#3a2a1e")


@sprite("black_winged_stilt")
def _(s):
    # Black wings, white body and absurdly long pink legs; a needle-thin black bill.
    wader(s, WHITE, neck=WHITE, head=WHITE, beak="#1d1a20", legs="#f07aa0", wing=BLACK)
    s.paint(s.m_ellipse(20, 12, 7, 2.6), BLACK)
    s.paint(s.m_ellipse(13, 3.5, 2.8, 2), "#3a3a42")
    s.eye(8, 4, color="#a01818")


# --------------------------------------------------------------------------- herons, storks, cranes, flamingo
@sprite("grey_heron")
def _(s):
    # Gray with a white neck streaked black down the front, a black stripe and plume from the eye, a yellow dagger bill.
    wader(s, "#9aa0aa", neck="#eceef0", head=WHITE, beak="#e8b830", legs="#a89a70", plume="#1e1c22",
          wing="#8a909c")
    s.paint(s.m_ellipse(12.5, 3.6, 3, 1.4), "#1e1c22")
    s.paint(s.m_px([(14, 9), (13, 11), (14, 13)]), "#3a3a42")
    s.paint(s.m_ellipse(24, 15, 3, 1.5, rot=-10), "#2b2630")


@sprite("little_egret")
def _(s):
    # Snow white with a black bill, black legs, yellow feet and long lacy plumes.
    wader(s, WHITE, beak="#1d1a20", legs="#1d1a20", plume=WHITE, face="#e8d050")
    s.px([(16, 30), (17, 30), (22, 30), (23, 30)], "#f0d040")


@sprite("squacco_heron")
def _(s):
    # A small, hunched buff heron with a streaky mane; it flashes white wings in flight.
    wader(s, "#d8b080", neck="#e0b888", head="#d8a870", beak="#6a8ab0", legs="#d8c070", plume="#c8a070",
          wing="#f0ece4")
    s.paint(s.m_px([(11, 3), (13, 4), (12, 2)]), "#6a4a2a")


@sprite("white_stork")
def _(s):
    # White with black flight feathers, a long red bill and long red legs.
    wader(s, WHITE, neck=WHITE, head=WHITE, beak="#e0302a", legs="#e0302a", wing="#f0eee8")
    s.paint(s.m_ellipse(23, 16, 5, 2.4, rot=-10) | s.m_poly([(26, 14), (31, 17), (25, 18)]), BLACK)
    s.eye(8, 4)


@sprite("eurasian_spoonbill")
def _(s):
    # All white with a shaggy crest, a yellow wash on the breast and a long black spoon-tipped bill.
    wader(s, WHITE, neck=WHITE, head=WHITE, beak="#2b2630", legs="#2b2630", plume="#f4f0e4", wing="#f4f2ec")
    s.ellipse(-1, 6.5, 2.2, 1.6, "#e8c040")  # the yellow-tipped spoon
    s.paint(s.m_ellipse(16, 11, 2, 1.6), "#f0dca0")


@sprite("common_crane")
def _(s):
    # Tall and gray with a black-and-white head and neck, a red crown and a bushy drooping tail.
    wader(s, "#9a9ca4", neck="#2b2630", head="#2b2630", beak="#c8c0a8", legs="#2b2630", cap="#e0302a",
          wing="#7a7c84")
    s.paint(s.m_path([(11.5, 6), (13.5, 9), (15, 13)], 0.8), WHITE)
    s.ellipse(26, 17, 3.5, 2.6, "#4a4a52")


@sprite("greater_flamingo")
def _(s):
    # Pale pink with a long S-shaped neck, a bent pink bill with a black tip and coral-red wing patches.
    wader(s, "#f4d0d4", neck="#f4d4d8", head="#f4d4d8", beak="#f0a0b0", legs="#e8809a", wing="#f0b0b8",
          curved=True)
    s.paint(s.m_ellipse(23, 15, 4, 1.8, rot=-10), "#e04a5a")
    s.px([(0, 11), (0, 12), (1, 12)], "#1e1c22")


# --------------------------------------------------------------------------- geese, swans, ducks, grebes
def _goose(s, body, belly, wing, tail, neck, head, bill, *, cheek=None, tip=None, rump=None, face=None,
           swan=False, knob=None):
    """A goose (or swan) swimming side on; flies with the long neck stretched out."""
    s.can("swim", "fly")
    flying = s.act == "fly"
    w = s.wave()
    if flying:
        hm, bob = flying_waterbird(s, body=body, belly=belly, wing=wing, tip=tip or _dk(wing, 0.3), tail=tail,
                                   neck=[(11, 18), (7, 16.5), (4, 15.5)] if not swan else
                                   [(11, 18), (6, 16.5), (2, 15.5)], neck_col=neck, head=(2.5, 15) if not swan
                                   else (0.5, 15), head_col=head, head_r=(2.6, 2.1), cy=19, body_r=(9, 4.2),
                                   size=1.15 if not swan else 1.3)
        hx = 2.5 if not swan else 0.5
        if cheek:
            s.paint(s.m_ellipse(hx + 0.5, 15.2, 1.8, 1.2), cheek, within=hm)
        s.ellipse(hx - 3.3, 15.4, 1.7, 0.9, bill)
        s.px([(round(hx - 1.5), 14)], "#000000")
        s.shift(0, bob)
        return
    _slim(s, (9.5, 7), (9.5, 8.5), 0.8, (19, 23), (19, 24), 1.04, 0.84, 29.5, (13, 15))
    _ripples(s, s.t * 4 if s.act == "swim" else 0, ((2, 30), (6, 29), (25, 30), (29, 29)))
    s.poly([(25, 20), (31, 17), (30, 23)], tail)
    if rump:
        s.ellipse(27, 21.5, 2.2, 1.6, rump)
    s.ellipse(19, 23, 10.5, 6.5, body)
    s.ellipse(14, 25, 5, 4, belly)
    s.ellipse(22, 21, 7, 3.5, wing, rot=-8, edge=True)
    s.paint(s.m_line(17, 21, 27, 19), mix(wing, WHITE, 0.35))
    if swan:
        s.path([(12, 19), (13, 13), (11, 8)], 2.3, neck)
    else:
        s.path([(12, 19), (10, 13), (10, 8)], 2.3, neck)
    hm = s.ellipse(9.5, 7, 5, 4.2, head, edge=True)
    if cheek:
        s.paint(s.m_ellipse(9.5, 8.5, 3.2, 2.4), cheek, within=hm)
    if face:
        face(s, hm)
    s.ellipse(4, 8.2, 2.6, 1.5, bill)
    if knob:
        s.ellipse(6.5, 7.6, 1.5, 1.5, knob)
    s.eye(8, 5, shine="#ffffff", color="#000000")


@sprite("greylag_goose")
def _(s):
    # The wild ancestor of farm geese: gray-brown, barred on the back, with a big orange bill and pink legs.
    _goose(s, "#8a8478", "#d8d4cc", "#7a7468", "#f4f2ee", "#8a8478", "#8a8478", "#f08a3a", rump=WHITE,
           tip="#9aa0a8")


@sprite("greater_white_fronted_goose")
def _(s):
    # Gray-brown with a white blaze round the base of a pink bill and black bars across the belly.
    def face(s, hm):
        s.paint(s.m_ellipse(5.5, 8, 1.5, 2), WHITE, within=hm)
    _goose(s, "#7a7064", "#c8c0b4", "#6a6054", "#f4f2ee", "#7a7064", "#7a7064", "#f0a0a8", rump=WHITE, face=face)
    s.paint(s.m_line(13, 25, 17, 25) | s.m_line(14, 27, 19, 27), "#2b2630")
    s.ellipse(4, 8.2, 2.6, 1.5, "#f0a0a8")


@sprite("pink_footed_goose")
def _(s):
    # A neat gray goose with a dark brown head and neck and a small pink-banded bill.
    _goose(s, "#9a9690", "#d8d4cc", "#8a8680", "#f4f2ee", "#5a4a40", "#5a4a40", "#e898a0", rump=WHITE)
    s.ellipse(4, 8.2, 2.6, 1.5, "#2b2630")
    s.paint(s.m_ellipse(4, 8.2, 1, 1.4), "#e898a0")


@sprite("barnacle_goose")
def _(s):
    # A black neck and breast, a creamy-white face, and a silvery-gray back barred in black.
    _goose(s, "#9aa0a8", WHITE, "#8a9098", "#1e1c22", "#1e1c22", "#1e1c22", "#1e1c22", cheek="#f6f2e8")
    s.paint(s.m_line(17, 19, 26, 18) | s.m_line(17, 22, 26, 21), "#2b2630")
    s.paint(s.m_ellipse(12, 19.5, 3.2, 2.2), "#1e1c22")


@sprite("egyptian_goose")
def _(s):
    # Sandy-brown with a dark chocolate eye patch, a brown spot on the breast, pink bill and legs.
    def face(s, hm):
        s.paint(s.m_ellipse(8, 5.5, 2, 1.6), "#6a3a2a", within=hm)
    _goose(s, "#b8946a", "#d8c4a4", "#a07a50", "#2b2630", "#c8a888", "#e0d4c0", "#f0a0a0", face=face)
    s.paint(s.m_ellipse(14, 24, 1.8, 1.6), "#6a3a2a")
    s.paint(s.m_ellipse(22, 20, 3, 1.4, rot=-8), WHITE)


@sprite("whooper_swan")
def _(s):
    # All white with a long straight neck and a black bill with a big wedge of lemon-yellow at the base.
    _goose(s, "#f6f6f4", WHITE, "#eef0f2", "#f0f0ee", "#f8f8f6", "#f8f8f6", "#1e1c22", swan=True, tip="#e8e8ea")
    s.paint(s.m_poly([(3.5, 6.8), (6.6, 6.6), (6.6, 9.2), (4.5, 9)]), "#f0d828")


@sprite("common_shelduck")
def _(s):
    # A big goose-like duck: white with a green-black head, a chestnut breast band and a red bill.
    duck(s, WHITE, "#b8602a", "#1e3a30", bill="#e0302a", ring=None, speculum="#1e6a4a", tail_col="#1e1c22")
    s.paint(s.m_ellipse(20, 20, 6, 1.8, rot=-8), "#1e1c22")
    s.paint(s.m_ellipse(3.5, 11, 1.4, 1.2), "#e0302a")


@sprite("ruddy_shelduck")
def _(s):
    # Rich orange-chestnut with a pale buff head, black wingtips and a black bill.
    duck(s, "#c8682e", "#c8682e", "#e8d0b0", bill="#1e1c22", ring=None, speculum="#1e6a4a", tail_col="#1e1c22")
    s.paint(s.m_ellipse(10, 16.8, 4, 0.8), "#2b2226")


@sprite("eurasian_wigeon")
def _(s):
    # A chestnut head with a cream forehead stripe, a gray body, a pink breast and a small blue-gray bill.
    duck(s, "#a8a8b0", "#d8b0a8", "#b0502a", bill="#8a9aaa", ring=None, speculum="#2a7a4a", tail_col="#1e1c22")
    s.paint(s.m_ellipse(11, 6.5, 2, 3.2, rot=60), "#f0e0a0")
    s.paint(s.m_ellipse(20, 19, 4, 1.4, rot=-8), WHITE)
    s.px([(1, 13)], "#1e1c22")


@sprite("common_pochard")
def _(s):
    # A rusty-red head, black breast and tail, a pale gray body and a dark bill with a gray band.
    duck(s, "#b8bcc4", "#1e1c22", "#b0482a", bill="#2b2630", ring=None, speculum="#9aa0a8", tail_col="#1e1c22")
    s.paint(s.m_ellipse(3.5, 13, 1.2, 1.6), "#8a9aaa")
    s.eye(7, 10, color="#e0302a")


@sprite("red_crested_pochard")
def _(s):
    # A big fluffy orange head, a bright red bill, a black breast and white flanks.
    duck(s, "#8a7a68", "#1e1c22", "#e0802e", bill="#e0302a", ring=None, speculum=WHITE, tail_col="#1e1c22")
    s.paint(s.m_ellipse(19, 24, 7, 2.6), WHITE)
    s.ellipse(11, 7, 5, 3.6, "#f0a040")
    s.eye(7, 10, color="#e0302a")


@sprite("tufted_duck")
def _(s):
    # Black with bright white flanks, a golden eye and a droopy tuft on the back of the head.
    duck(s, "#1e1c22", "#1e1c22", "#2a2236", bill="#8a9aaa", ring=None, speculum=WHITE, tail_col="#1e1c22")
    s.paint(s.m_ellipse(18, 24, 7.5, 3), WHITE)
    s.path([(14, 8), (17, 9.5), (18.5, 12)], (1.0, 0.5), "#1e1c22")
    s.px([(1, 13)], "#1e1c22")
    s.eye(7, 10, color="#f0d020")


@sprite("greater_scaup")
def _(s):
    # A green-glossed black head, a pale gray vermiculated back, white flanks and a blue-gray bill.
    duck(s, "#c8ccd0", "#1e1c22", "#1e3a32", bill="#8a9ab0", ring=None, speculum=WHITE, tail_col="#1e1c22")
    s.paint(s.m_ellipse(18, 24, 7.5, 3), WHITE)
    s.px([(1, 13)], "#1e1c22")
    s.eye(7, 10, color="#f0d020")


@sprite("long_tailed_duck")
def _(s):
    # A white winter drake with a gray face, dark cheek patch, dark breast and long thin tail spikes.
    s.path([(26, 19), (32, 13), (35, 10)], (0.8, 0.4), "#1e1c22")
    duck(s, "#e8e4dc", "#3a2a24", WHITE, bill="#e88aa0", ring=None, speculum="#5a4a3e", tail_col="#1e1c22")
    s.paint(s.m_ellipse(12, 13, 2.4, 2.2), "#4a3a2e")
    s.paint(s.m_ellipse(21, 21, 6, 2, rot=-8), "#3a2a24")
    s.paint(s.m_ellipse(3.5, 13, 1.2, 1.6), "#2b2630")


@sprite("great_crested_grebe")
def _(s):
    # A slender diving bird with a black double crest, chestnut-and-black frills on its cheeks and a pink bill.
    duck(s, "#6a5a4a", WHITE, WHITE, bill="#e8a0a0", ring=None, speculum="#6a5a4a", tail_col="#6a5a4a")
    s.paint(s.m_ellipse(12.5, 13.5, 3, 2.6), "#c8602a")
    s.paint(s.m_ellipse(14, 14.5, 1.8, 1.8), "#2b2226")
    s.poly([(10, 6), (12, 1), (14, 6)], "#1e1c22")
    s.paint(s.m_ellipse(10.5, 6.5, 5, 2), "#1e1c22", within=s.m_ellipse(10, 11, 6, 5.5))
    s.poly([(5, 12), (-1, 13.2), (5, 14.2)], "#e8a0a0")
    s.eye(7, 10, color="#c02020")


@sprite("horned_grebe")
def _(s):
    # The Slavonian grebe: a black head with golden "horns" behind the eyes, a red neck and a red eye.
    duck(s, "#2b2630", "#b8402a", "#1e1c22", bill="#1e1c22", ring=None, speculum="#2b2630", tail_col="#2b2630")
    s.paint(s.m_path([(7, 9), (13, 8), (16, 6)], (0.9, 0.6)), "#f0b030")
    s.poly([(5, 12), (0, 13), (5, 14)], "#1e1c22")
    s.eye(7, 10, color="#e02020")


@sprite("little_grebe")
def _(s):
    # The dabchick: a tiny round dark grebe with chestnut cheeks and a yellow spot at the base of its bill.
    duck(s, "#3a3028", "#6a4a34", "#2b2622", bill="#1e1c22", ring=None, speculum="#3a3028", tail_col="#6a5a4a")
    s.paint(s.m_ellipse(10, 14, 3.2, 2.4), "#a8482a")
    s.paint(s.m_ellipse(5, 13, 1, 1.2), "#f0e040")
    s.eye(7, 10, color="#c8a020")


@sprite("red_throated_loon")
def _(s):
    # A slim loon: a gray head with a dark-red throat patch, a striped nape and a slightly upturned bill.
    duck(s, "#5a5a58", WHITE, "#9aa0a8", bill="#1e1c22", ring=None, speculum="#5a5a58", tail_col="#5a5a58")
    s.paint(s.m_ellipse(10, 15.5, 2.4, 2.4), "#8a2a2a")
    s.paint(s.m_line(14, 9, 15, 15) | s.m_line(16, 9, 16, 15), "#2b2630")
    s.poly([(5, 11.5), (-1, 11.5), (5, 13.5)], "#1e1c22")
    s.paint(s.m_px([(18, 19), (21, 18), (24, 19), (20, 21), (23, 20)]), WHITE)
    s.eye(7, 10, color="#a01818")


@sprite("eurasian_coot")
def _(s):
    # Sooty black with a pure white bill and forehead shield and lobed gray feet.
    duck(s, "#26242a", "#2e2c32", "#1e1c22", bill="#f4f2ec", ring=None, speculum="#26242a", tail_col="#1e1c22")
    s.ellipse(6, 7.5, 1.6, 2.2, "#f4f2ec")
    s.eye(7, 10, color="#c02020")


@sprite("eurasian_moorhen")
def _(s):
    # Dark slate with a red forehead shield, a yellow-tipped red bill, a white line on the flank and white under the tail.
    duck(s, "#3a3a44", "#3e4250", "#2b2a34", bill="#e0302a", ring=None, speculum="#4a4038", tail_col="#2b2630")
    s.ellipse(6, 7.5, 1.6, 2.2, "#e0302a")
    s.px([(0, 13), (1, 13)], "#f0d020")
    s.paint(s.m_line(14, 21, 24, 19), WHITE)
    s.paint(s.m_ellipse(28, 18, 1.8, 1.4), WHITE)


# --------------------------------------------------------------------------- seabirds
@sprite("great_cormorant")
def _(s):
    # Big and black with a bronze sheen, a white cheek and throat and a white thigh patch in spring.
    cormorant(s, "#1e1e24", throat="#f4f2ec", eye_col="#2a8a6a", bill="#5a5a5a", flank=WHITE)


@sprite("pygmy_cormorant")
def _(s):
    # A small cormorant with a short bill, a chocolate-brown head and white speckles in spring.
    cormorant(s, "#262428", face="#5a3a2a", eye_col="#5a3a2a", bill="#3a3438")
    s.paint(s.m_px([(17, 15), (19, 17), (21, 16), (18, 19), (20, 20)]), "#e8e4dc")


@sprite("european_shag")
def _(s):
    # Slimmer than a cormorant, glossy green-black with a forward curling crest and yellow gape.
    cormorant(s, "#1e2622", throat="#f0d030", eye_col="#40c890", bill="#2b2630", crest=True)


@sprite("great_white_pelican")
def _(s):
    # Huge and white flushed with pink, black flight feathers, a pink face and a yellow pouch.
    pelican(s, body="#f6eef0", belly="#f6eef0", wing="#f4ecec", tip="#2b2630", neck="#f6eef0", head="#f6eef0",
            crown=None, bill="#e8a0a8", pouch="#f0c040", legs="#f0a0a0", tail="#ece8e0")


@sprite("dalmatian_pelican")
def _(s):
    # The biggest pelican: silvery-white with curly nape feathers, gray legs and an orange-red pouch.
    pelican(s, body="#e8e8ea", belly="#ecebec", wing="#e2e2e6", tip="#3a3a40", neck="#eeeef0", head="#f0f0f2",
            crown="#d8d8dc", bill="#c8c0a8", pouch="#e8682a", legs="#7a7a80", tail="#d8d8dc")


@sprite("northern_gannet")
def _(s):
    # A big white seabird with a buttery-yellow head, black wingtips and a long dagger bill.
    def wing(s, m):
        s.paint(s.m_ellipse(25, 20, 4, 3), "#1e1a22", within=m)
    def face(s):
        s.paint(s.m_ellipse(12, 9, 5, 4), "#f0d890", within=s.last)
        s.paint(s.m_line(4, 11, 8, 10), "#2b2630", within=s.last)
    bird(s, WHITE, WHITE, head="#f4f0e0", wing="#eeeef0", tail_col=WHITE, beak="long", beak_col="#a8b0c0",
         legs="#3a3a42", tail="mid", wing_mark=wing, face=face, big=True)
    s.eye(8, 10, color="#a8c8e8")


@sprite("northern_fulmar")
def _(s):
    # A stocky gull-like petrel with a thick neck, pale gray back, and a stubby yellow tube-nosed bill.
    def face(s):
        s.paint(s.m_ellipse(9.5, 10.5, 2.4, 1.4), "#7a7880", within=s.last)
    bird(s, "#a0a8b4", WHITE, head=WHITE, wing="#8a94a2", tail_col="#a0a8b4", beak="hook", beak_col="#e8d070",
         legs="#c8b8b0", tail="short", face=face, big=True)
    s.px([(4, 10), (5, 10)], "#c8a040")


@sprite("great_skua")
def _(s):
    # A heavy, dark brown pirate of the seas with white flashes at the base of its wing feathers.
    def wing(s, m):
        s.paint(s.m_ellipse(23, 18.5, 2.4, 1.2, rot=-15), WHITE, within=m)
    def face(s):
        s.paint(s.m_px([(12, 9), (14, 10), (11, 12), (13, 13)]), "#c8a87a", within=s.last)
    bird(s, "#5a4436", "#6a5244", head="#5a4436", wing="#4a382c", tail_col="#3a2c22", beak="hook",
         beak_col="#1e1c22", legs="#1e1c22", tail="short", wing_mark=wing, face=face, big=True)


@sprite("parasitic_jaeger")
def _(s):
    # A slim dark-capped seabird, pale below, with two pointed central tail feathers.
    s.path([(22, 19), (31, 17), (35, 17)], (1.0, 0.4), "#3a3432")
    def face(s):
        s.paint(s.m_ellipse(11, 7.5, 6.5, 4), "#2b2630", within=s.last)
        s.paint(s.m_ellipse(11, 14, 5, 2.2), "#f0e4b0", within=s.last)
    bird(s, "#4a4442", "#f2eee4", head=WHITE, wing="#3a3432", tail_col="#3a3432", beak="hook",
         beak_col="#1e1c22", legs="#1e1c22", tail="mid", face=face)


@sprite("razorbill")
def _(s):
    # Black above and white below, standing upright, with a deep blunt bill crossed by a white line.
    def face(s):
        s.paint(s.m_line(5, 9, 8, 9), WHITE, within=s.last)
    bird(s, "#1e1c22", WHITE, head="#1e1c22", wing="#1a181e", tail_col="#1a181e", beak="hook", beak_col=BLACK,
         legs="#1e1c22", tail="short", big=True, face=face)
    s.paint(s.m_line(3, 10, 3, 14), WHITE)
    s.paint(s.m_ellipse(12, 19, 4, 1.8), "#1e1c22")
    s.eye(8, 10, color="#000000")


@sprite("thick_billed_murre")
def _(s):
    # Like a common murre but blacker, with a thicker bill marked by a white line along the gape.
    bird(s, "#1a181e", WHITE, head="#1a181e", wing="#161418", tail_col="#161418", beak="long", beak_col=BLACK,
         legs="#2b2630", tail="short", big=True)
    s.paint(s.m_ellipse(12, 19, 4, 1.8), "#1a181e")
    s.paint(s.m_line(2, 13, 5, 13), WHITE)
    s.eye(8, 10, color="#000000")


@sprite("whiskered_tern")
def _(s):
    # A marsh tern: gray body, a black cap, white cheeks, a dark red bill and red legs.
    def face(s):
        s.paint(s.m_ellipse(13, 7, 6, 3.2) | s.m_poly([(13, 5), (17, 6), (17, 9)]), BLACK, within=s.last)
    bird(s, "#6a6e78", "#5a5e68", head=WHITE, wing="#a8acb6", tail_col="#c8ccd6", beak="long", beak_col="#c02a2a",
         legs="#c02a2a", tail="mid", face=face)


# --------------------------------------------------------------------------- gulls
@sprite("european_herring_gull")
def _(s):
    # Big and pale gray-backed with pink legs and a yellow bill with a red spot.
    gull(s, "#a8b2c0", bill="#f0d040", legs="#f0a8a8", big=True, bill_spot="#e0302a", eye_col="#f0e070")


@sprite("lesser_black_backed_gull")
def _(s):
    # A slate-gray back, yellow legs and a yellow bill with a red spot.
    gull(s, "#4a4e5a", bill="#f0d040", legs="#f0d040", big=True, bill_spot="#e0302a", eye_col="#f0e070")


@sprite("yellow_legged_gull")
def _(s):
    # The Mediterranean's big gull: a mid-gray back, bright yellow legs, a red bill spot and red eye ring.
    gull(s, "#8a94a2", bill="#f0d040", legs="#f0d030", big=True, bill_spot="#e0302a", eye_col="#f0e070")


@sprite("common_gull")
def _(s):
    # The mew gull: gentle-faced, a medium gray back, a thin plain yellow bill and yellow-green legs.
    gull(s, "#98a2b0", bill="#e8e060", legs="#d8d860", thin_bill=True)


@sprite("iceland_gull")
def _(s):
    # A pale, ghostly gull with no black at all: the wingtips are white.
    gull(s, "#c8d0dc", tips="#f4f6f8", spots=False, bill="#f0d040", legs="#f0a8a8", bill_spot="#e0302a",
         eye_col="#f0e070")


@sprite("black_headed_gull")
def _(s):
    # A chocolate-brown hood in summer, a dark red bill and legs, and white flashes on the wing.
    gull(s, "#b8c0cc", bill="#a0202a", legs="#c0303a", thin_bill=True, hood="#4a2e28")


@sprite("mediterranean_gull")
def _(s):
    # A jet-black hood, white eye crescents, pure white wingtips and a heavy red bill.
    gull(s, "#c8d0dc", tips="#f6f6f8", spots=False, bill="#d02a2a", legs="#c0303a", hood="#1e1c22")


@sprite("slender_billed_gull")
def _(s):
    # A long-necked, long-billed gull with no hood, a pink blush on the breast and a dark red bill.
    gull(s, "#b8c0cc", bill="#8a1e24", legs="#c0303a", thin_bill=True, head="#f8f0f0")


# --------------------------------------------------------------------------- birds of prey and owls
@sprite("common_buzzard")
def _(s):
    # A chunky brown hawk with a pale band across the breast and a finely barred tail.
    def chest(s, m):
        s.paint(s.m_ellipse(12, 17, 3.6, 1.6), "#f0e4d0", within=m)
        s.paint(s.m_px([(10, 20), (12, 21), (14, 20), (11, 23), (13, 23)]), "#5a3a26", within=m)
    raptor(s, "#6a4a32", "#a07a58", head="#6e4e36", wing="#5a3e2a", tail="#7a5a40", build="buteo",
           cere="#e8c860", chest=chest,
           tail_mark=lambda s, m: [s.paint(s.m_line(17, y, 26, y), "#4a3020", within=m) for y in (22, 25, 28)])


@sprite("long_legged_buzzard")
def _(s):
    # A big pale buzzard with a cinnamon head and chest, a darker belly and a plain orange tail.
    raptor(s, "#8a6040", "#d8a878", head="#e0c098", wing="#7a5234", tail="#e0a060", build="buteo",
           cere="#e8c860", chest=lambda s, m: s.paint(s.m_ellipse(13, 23, 4, 2.6), "#7a4a2a", within=m))


@sprite("european_honey_buzzard")
def _(s):
    # A slim-headed, pigeon-faced raptor that raids wasp nests: gray head, brown back, barred breast.
    def chest(s, m):
        for y in (16, 18.5, 21, 23.5):
            s.paint(s.m_line(9, y, 16, y), "#6a4a32", within=m)
    raptor(s, "#5a4434", "#f0e4d4", head="#8a909a", wing="#4e3a2c", tail="#6a5444", build="kite",
           cere="#3a3a40", eye_col="#f0c020", brow=False, chest=chest,
           tail_mark=lambda s, m: [s.paint(s.m_line(17, y, 26, y), "#2b2226", within=m) for y in (22, 27)])


@sprite("black_kite")
def _(s):
    # Dark brown with a pale streaky head and a slightly forked tail; a scavenger of rivers and towns.
    raptor(s, "#5a4232", "#7a5a40", head="#b0a090", wing="#4a3628", tail="#5a4232", build="kite",
           cere="#f0c840", legs="#f0c840", eye_col="#c8a040",
           face=lambda s, m: s.paint(s.m_px([(11, 5), (13, 6), (12, 8), (14, 8)]), "#6a5a4a", within=m))


@sprite("red_kite")
def _(s):
    # Rusty red with a pale gray head, a deeply forked orange tail and white patches under long wings.
    raptor(s, "#a8502a", "#c8683a", head="#d8d4cc", wing="#7a3e22", tail="#d8782e", build="kite",
           cere="#f0c840", legs="#f0c840", eye_col="#e8d070",
           chest=lambda s, m: s.paint(s.m_px([(11, 17), (13, 19), (12, 21), (14, 22)]), "#3a2016", within=m),
           face=lambda s, m: s.paint(s.m_px([(11, 5), (13, 6), (12, 8)]), "#6a6460", within=m))


@sprite("western_marsh_harrier")
def _(s):
    # A long-winged harrier: chestnut body, a creamy streaked head, gray wings with black tips and a gray tail.
    def wing(s, m):
        s.paint(s.m_ellipse(24, 26, 3, 2.2, rot=50), BLACK, within=m)
    raptor(s, "#7a4a2a", "#9a5a32", head="#e8d8b8", wing="#9aa0aa", tail="#9aa0aa", build="harrier",
           bill="#2b2630", cere="#e0c040", legs="#f0c040", eye_col="#e0b020", wing_mark=wing)


@sprite("eurasian_kestrel")
def _(s):
    # A small falcon that hovers: a blue-gray head and tail, a spotted chestnut back and a dark moustache.
    def face(s, m):
        s.paint(s.m_line(10, 7.5, 10, 10.5), BLACK, within=m)
    def chest(s, m):
        s.paint(s.m_px([(11, 19), (13, 21), (11, 23), (14, 18), (12, 17)]), "#3a2a20", within=m)
    raptor(s, "#c0663a", "#f2dcc0", head="#8a94a8", wing="#b45c34", tail="#8a94a8", build="falcon",
           bill="#5a6a80", cere="#e8c040", face=face, chest=chest,
           wing_mark=lambda s, m: s.paint(s.m_px([(17, 15), (19, 17), (21, 16), (18, 20), (21, 21)]), "#2b2226",
                                          within=m),
           tail_mark=lambda s, m: s.paint(s.m_line(17, 28, 26, 28), BLACK, within=m))


@sprite("white_tailed_eagle")
def _(s):
    # Europe's biggest eagle: brown with a pale head, a huge yellow bill and a short white wedge tail.
    raptor(s, "#5a4232", "#5a4232", head="#d8ccb4", wing="#4a3628", tail=WHITE, build="eagle", bill="#f0c830",
           cere="#f0c830", legs="#f0c830", eye_col="#e8d070")


@sprite("eastern_imperial_eagle")
def _(s):
    # Very dark brown with a golden crown and nape, white "braces" on the shoulders and a gray tail.
    raptor(s, "#3a2a20", "#3a2a20", head="#3a2a20", wing="#2e2018", tail="#6a6460", build="eagle",
           cere="#f0c030", legs="#f0c030", eye_col="#8a5a20",
           face=lambda s, m: s.paint(s.m_ellipse(13, 5, 3.6, 3.4), "#e8c890", within=m),
           wing_mark=lambda s, m: s.paint(s.m_ellipse(17, 14, 1.8, 1.2), WHITE, within=m))


@sprite("short_toed_snake_eagle")
def _(s):
    # An owl-faced eagle with a big round head, a brown hood and bib, a white belly barred brown and big yellow eyes.
    def chest(s, m):
        s.paint(s.m_ellipse(11, 13.5, 4, 2.4), "#7a5a40", within=m)
        for y in (18, 20.5, 23):
            s.paint(s.m_line(9, y, 16, y), "#a0806a", within=m)
    raptor(s, "#7a5a40", "#f2ece4", head="#8a6a50", wing="#6a4c36", tail="#8a6a50", build="buteo",
           cere="#9aa0aa", legs="#c8ccd0", eye_col="#f0c020", chest=chest)


@sprite("eurasian_griffon")
def _(s):
    # A huge pale sandy-brown vulture with a downy white head and neck, a fluffy white ruff and dark flight feathers.
    vulture(s, head_col="#f0ece4", body="#b08a60", ruff="#f8f4ec", beak="#c8c0b0")


@sprite("little_owl")
def _(s):
    # A small, flat-headed owl, brown spotted with white, with fierce yellow eyes and white brows.
    def front(s):
        s.paint(s.m_line(11, 7, 15, 7), "#f4ecdc", mirror=True)
        s.paint(s.m_px([(12, 5), (16, 4), (20, 5), (10, 18), (22, 18), (10, 22), (22, 22)]), "#f4ecdc")
    owl(s, "#7a6248", "#a88a68", eye_col="#f6d030", belly="#e8dcc8", streaks="#7a6248", spots="#f4ecdc",
        throat="#f4ecdc", brows="#f4ecdc", front=front)


@sprite("eurasian_scops_owl")
def _(s):
    # A tiny gray-brown owl with short ear tufts, bark-like streaks and yellow eyes.
    owl(s, "#8a8072", "#a89a88", tufts=True, eye_col="#f6d030", belly="#c8beb0", streaks="#4a4036",
        bars="#8a7e70", spots="#e8e0d4")


@sprite("long_eared_owl")
def _(s):
    # A slim, streaky buff owl with tall ear tufts, an orange facial disc and orange eyes.
    owl(s, "#a07a50", "#e0a060", tufts=True, eye_col="#f08a20", belly="#e8c890", streaks="#5a3e26",
        disk_edge="#3a2a1e", spots="#d8c0a0")
