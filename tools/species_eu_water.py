"""Sprites for the European (and Turkish) fish, crabs, crayfish, jellies, anemones,
urchins, sea creatures, woodlice, millipedes, centipedes and springtails that the US lists
don't have. Imported by make_sprites.py, which registers the drawings via @sprite.

fish() markings are drawn on its old oval body: centre (15, 16.5), snout at x 3, tail
wrist at x 25, back at about y 10 and belly at about y 23."""
from __future__ import annotations

import math

from archetypes import EYE, WHITE, _fluke, crab, fish, jelly, sprite, star
from pixel import mix
from species_ak import _anemone
from species_hi import _reef
from species_nw import _crayfish
from species_tx import _segmented
from species_va import _woodlouse


def _dk(c, k=0.3):
    return mix(c, "#141018", k)


def _pts(*p):
    return list(p)


def _bars(xs, col, y0=9, y1=20):
    def pat(s, m):
        for x in xs:
            s.paint(s.m_poly([(x, y0), (x + 1.6, y0), (x + 1.6, y1), (x, y1)]), col, within=m)
    return pat


# --------------------------------------------------------------------------- freshwater fish
@sprite("adriatic_trout")
def _(s):
    # A Balkan trout with a small, soft mouth: olive-silver with small black and red spots.
    def pat(s, m):
        s.paint(s.m_px([(11, 11), (14, 12), (18, 11), (21, 13), (16, 14), (12, 14)]), "#2b2226", within=m)
        s.paint(s.m_px([(15, 17), (19, 16), (22, 17)]), "#d8402a", within=m)
    fish(s, "#8a8a62", "#e8e4c8", fin="#7a7a58", pattern=pat, slim=True)


@sprite("albanian_minnow")
def _(s):
    # A small silvery fish with a dark stripe along its side and a few dark blotches.
    def pat(s, m):
        s.paint(s.m_line(7, 15, 25, 15), "#3a3a3a", within=m)
        s.paint(s.m_px([(12, 12), (17, 12), (21, 13)]), "#4a4a40", within=m)
    fish(s, "#9a9a80", "#e8e8dc", fin="#b0a888", pattern=pat, slim=True)


@sprite("bleak")
def _(s):
    # A small, slim, shining-silver fish with an upturned mouth, that swims near the surface.
    def pat(s, m):
        s.paint(s.m_ellipse(14, 12, 9, 1.5), "#6a8a9a", within=m)
    fish(s, "#c8d4dc", "#f4f6f8", fin="#c8ccc4", pattern=pat, slim=True)


@sprite("cavedano_chub")
def _(s):
    # A stocky chub with big net-patterned scales and a blunt head.
    def pat(s, m):
        for x in (9, 12, 15, 18, 21):
            for y in (12, 15, 18):
                s.paint(s.m_px([(x + (y // 3) % 2, y)]), "#5a5a48", within=m)
    fish(s, "#8a8a6a", "#e4e0cc", fin="#b0784a", pattern=pat)


@sprite("european_chub")
def _(s):
    # A thick-set silvery-bronze fish with dark-edged scales and orange lower fins.
    def pat(s, m):
        for x in (9, 12, 15, 18, 21):
            for y in (12, 15, 18):
                s.paint(s.m_px([(x + (y // 3) % 2, y)]), "#4a4a3a", within=m)
    fish(s, "#9a9070", "#ece4cc", fin="#d0703a", pattern=pat)


@sprite("common_bream")
def _(s):
    # A deep, flat-sided bronze fish with a humped back and a long anal fin.
    _reef(s, "#a8904e", rx=10, ry=8.5, fin="#5a5040", eye=(7, 13),
          dorsal=[(15, 9), (19, 4), (21, 9)], anal=[(11, 22), (21, 27), (24, 21)],
          pattern=lambda s, m: s.paint(s.m_ellipse(14, 21, 8, 3), "#d8c890", within=m), mouth=[(6, 17), (7, 17)])


@sprite("common_roach")
def _(s):
    # A silvery fish with a red eye and orange-red fins.
    fish(s, "#9aa0a0", "#ecece4", fin="#d8603a",
         pattern=lambda s, m: s.paint(s.m_ellipse(14, 11.5, 9, 1.4), "#6a7878", within=m))


@sprite("common_rudd")
def _(s):
    # A golden-bronze fish with blood-red fins and an upturned mouth.
    fish(s, "#b8a050", "#f0e4b0", fin="#d8302a",
         pattern=lambda s, m: s.paint(s.m_ellipse(14, 11.5, 9, 1.4), "#7a6a30", within=m))


@sprite("dalmatian_roach")
def _(s):
    # A small Croatian roach, silvery with a dark stripe along its side and orange fins.
    fish(s, "#9a9e94", "#ecece2", fin="#e0804a",
         pattern=lambda s, m: s.paint(s.m_line(7, 15, 25, 15), "#4a4a44", within=m), slim=True)


@sprite("danubian_minnow")
def _(s):
    # A tiny minnow with dark bars along its golden-green side and a red belly in spring.
    def pat(s, m):
        _bars((9, 12, 15, 18, 21), "#3a4030", 11, 17)(s, m)
        s.paint(s.m_ellipse(13, 21, 7, 1.6), "#d8402a", within=m)
    fish(s, "#8a9a5a", "#f0e4c8", fin="#8a8a5a", pattern=pat, slim=True)


@sprite("ohrid_spirlin")
def _(s):
    # A small silvery fish with a double row of dark dots along its lateral line.
    def pat(s, m):
        s.paint(s.m_px([(x, 14) for x in range(8, 25, 2)] + [(x, 16) for x in range(9, 25, 2)]), "#3a3a3a",
                within=m)
    fish(s, "#a0a898", "#eef0e8", fin="#c8b898", pattern=pat, slim=True)


@sprite("topmouth_gudgeon")
def _(s):
    # A small gray fish with an upturned mouth, a dark stripe, and dark-edged scales.
    def pat(s, m):
        s.paint(s.m_line(6, 15, 25, 15), "#3a3a3a", within=m)
        s.paint(s.m_px([(10, 12), (13, 12), (16, 12), (19, 12), (12, 18), (17, 18)]), "#5a5a50", within=m)
    fish(s, "#8a8a7a", "#e4e2d8", fin="#a8a090", pattern=pat, slim=True)


@sprite("prussian_carp")
def _(s):
    # A deep-bodied, plain bronze-silver carp with big scales and no barbels.
    def pat(s, m):
        for x in (9, 12, 15, 18, 21):
            for y in (12, 15, 18, 21):
                s.paint(s.m_px([(x + (y // 3) % 2, y)]), "#7a6a3a", within=m)
    fish(s, "#b8a468", "#ece0b8", fin="#8a7a4a", pattern=pat)


@sprite("silver_carp")
def _(s):
    # A big silver carp with tiny scales, low-set eyes and an upturned mouth; it leaps from the water.
    fish(s, "#b0b8bc", "#eef0f0", fin="#9aa0a4",
         pattern=lambda s, m: s.paint(s.m_ellipse(14, 11.5, 9, 1.6), "#7a8890", within=m))


@sprite("european_perch")
def _(s):
    # Greenish-gold with dark bars, a spiny black-spotted first dorsal fin and red lower fins.
    def pat(s, m):
        _bars((9, 13, 17, 21), "#2e3a22", 9, 19)(s, m)
        s.paint(s.m_px([(12, 7), (13, 7), (12, 8)]), "#1e1a1e")
    fish(s, "#8aa040", "#f0e8b0", fin="#e0602a", pattern=pat)


@sprite("threespine_stickleback")
def _(s):
    # A tiny fish with three sharp spines on its back; the male turns red-throated and blue-eyed.
    def pat(s, m):
        s.paint(s.m_ellipse(9, 20, 5, 3), "#d8402a", within=m)
    fish(s, "#6a7a5a", "#d8dcc8", fin="#8a9a7a", pattern=pat, slim=True)
    for x, y in ((9, 10), (12, 9.5), (15, 9.5)):
        s.line(x, y, x - 1, y - 3, "#3a4a30")


# --------------------------------------------------------------------------- sea fish
@sprite("atlantic_cod")
def _(s):
    # Mottled olive-brown with a pale lateral line, a chin barbel and three soft back fins.
    def pat(s, m):
        s.paint(s.m_px([(10, 11), (13, 13), (16, 11), (19, 13), (22, 12), (12, 15), (18, 15)]), "#5a5034",
                within=m)
        s.paint(s.m_line(7, 14, 25, 14), "#e8e0c0", within=m)
    fish(s, "#9a8a5a", "#ece6d0", fin="#8a7a50", pattern=pat)
    s.line(5, 20, 5, 22, "#8a7a50")


@sprite("atlantic_pollock")
def _(s):
    # Bronze-brown above with a dark, curved lateral line and a jutting lower jaw.
    def pat(s, m):
        s.paint(s.m_path([(7, 13), (13, 11.5), (25, 14)], 0.45), "#3a3020", within=m)
    fish(s, "#8a7a4a", "#e8e4d8", fin="#7a6a48", pattern=pat)


@sprite("pollock")
def _(s):
    # The saithe: dark green-gray above, silvery below, with a straight pale lateral line.
    def pat(s, m):
        s.paint(s.m_line(7, 14, 25, 14), "#e0e4e0", within=m)
    fish(s, "#4a5a5a", "#dce0dc", fin="#3e4a4a", pattern=pat)


@sprite("european_seabass")
def _(s):
    # A sleek silver bass with a dark spot on the gill cover and spiny back fins.
    def pat(s, m):
        s.paint(s.m_ellipse(14, 11.5, 9, 1.8), "#6a7a84", within=m)
        s.paint(s.m_px([(9, 13), (9, 14)]), "#3a3a44", within=m)
    fish(s, "#a8b4bc", "#eef0f2", fin="#8a949c", pattern=pat)


def _bream(s, body, *, pattern=None, fin=None, tail_spot=None, eye=(7, 13), deep=8):
    """A seabream: a deep, oval silver body with a forked tail and a spiny back fin."""
    def pat(s, m):
        if tail_spot:
            s.paint(s.m_ellipse(23, 16, 1.6, 2.2), tail_spot, within=m)
        if pattern:
            pattern(s, m)
    _reef(s, body, rx=10, ry=deep, fin=fin, eye=eye, lyre=True,
          dorsal=[(9, 10), (13, 5), (21, 7), (24, 12)], anal=[(14, 22), (19, 26), (22, 21)],
          pattern=pat, mouth=[(6, 18), (7, 18)])


@sprite("common_two_banded_seabream")
def _(s):
    # Silver with two broad black bands: one behind the head, one in front of the tail.
    _bream(s, "#b8bcc0", fin="#9a9ea4",
           pattern=lambda s, m: s.paint(s.m_poly([(10, 7), (13, 7), (13, 26), (10, 26)])
                                        | s.m_poly([(21, 7), (24, 7), (24, 26), (21, 26)]), "#2b2a30", within=m))


@sprite("white_sea_bream")
def _(s):
    # Silver with thin dark vertical bars and a black saddle on the tail stalk.
    def pat(s, m):
        for x in (11, 14, 17, 20):
            s.paint(s.m_line(x, 9, x, 23), "#6a6e74", within=m)
    _bream(s, "#c8ccd0", fin="#a8acb0", tail_spot="#1e1e24", pattern=pat)


@sprite("gilthead_seabream")
def _(s):
    # Silver-gray with a gold bar between the eyes and a dark patch on the gill cover.
    def pat(s, m):
        s.paint(s.m_line(6, 10, 9, 10) | s.m_line(6, 11, 9, 11), "#e8c040", within=m)
        s.paint(s.m_ellipse(11, 13, 1, 1.5), "#3a3a44", within=m)
        for y in (13, 16, 19):
            s.paint(s.m_line(12, y, 24, y), "#9aa0a8", within=m)
    _bream(s, "#b8bcc4", fin="#8a9098", pattern=pat)


@sprite("saddled_seabream")
def _(s):
    # A slimmer silver bream with a big black saddle, edged in white, before the tail.
    _bream(s, "#b0b6bc", fin="#8a9098", tail_spot="#1a1a20", deep=6.5,
           pattern=lambda s, m: s.paint(s.m_line(21, 12, 21, 20), WHITE, within=m))


@sprite("salema_porgy")
def _(s):
    # A silver bream striped with golden-yellow lines from head to tail, and a yellow eye.
    def pat(s, m):
        for y in (11, 13.5, 16, 18.5, 21):
            s.paint(s.m_line(6, y, 26, y), "#e8c03a", within=m)
    _bream(s, "#a8b0b8", fin="#8a9098", deep=7, pattern=pat)
    s.px([(7, 13)], "#e8c03a")


@sprite("dusky_grouper")
def _(s):
    # A big, heavy brown grouper splotched with pale blotches, with a huge mouth.
    def pat(s, m):
        s.paint(s.m_px([(9, 12), (13, 11), (17, 12), (21, 13), (11, 16), (15, 15), (19, 17), (13, 20), (18, 21),
                        (23, 17)]), "#d8c8a0", within=m)
        s.paint(s.m_line(4, 18, 9, 18), "#3a2a20", within=m)
    _reef(s, "#6a4a32", rx=11.5, ry=7.5, cx=15, fin="#5a3e2a", eye=(7, 13),
          dorsal=[(10, 10), (14, 6), (22, 7), (25, 12)], anal=[(17, 22), (21, 25), (23, 21)], pattern=pat)


@sprite("painted_comber")
def _(s):
    # A small sea perch with dark bars, a blue patch on its belly and wavy blue lines on its face.
    def pat(s, m):
        _bars((10, 14, 18, 22), "#5a3a2a", 9, 18)(s, m)
        s.paint(s.m_ellipse(14, 20, 3, 2), "#3a6ad0", within=m)
        s.paint(s.m_path([(5, 15), (7, 14), (9, 16)], 0.4), "#4a8ae0", within=m)
    _reef(s, "#c88a5a", rx=10, ry=6.5, cx=15, fin="#b07a4a", eye=(7, 13),
          dorsal=[(9, 11), (13, 6), (22, 7), (24, 12)], anal=[(16, 21), (20, 24), (22, 20)], pattern=pat)


@sprite("mediterranean_damselfish")
def _(s):
    # A small chocolate-brown fish with a deeply forked tail; the young glow electric blue.
    _reef(s, "#4a4038", rx=8.5, ry=7, cx=15, fin="#3a3230", eye=(8, 13), lyre=True,
          dorsal=[(9, 10), (13, 5), (20, 7), (22, 11)], anal=[(13, 21), (18, 25), (21, 20)],
          pattern=lambda s, m: s.paint(s.m_px([(9, 15), (11, 13), (13, 16)]), "#6a7ad0", within=m))


@sprite("european_parrotfish")
def _(s):
    # The female is bright red with a gray back and a yellow saddle; it has a parrot-like beak.
    def pat(s, m):
        s.paint(s.m_ellipse(15, 11, 9, 3), "#6a6a72", within=m)
        s.paint(s.m_ellipse(13, 10, 2.5, 1.5), "#f0d040", within=m)
    _reef(s, "#d8402a", rx=10.5, ry=7, cx=15, fin="#c8402a", eye=(8, 12), pattern=pat,
          dorsal=[(10, 10), (14, 7), (22, 8), (24, 12)])
    s.px([(4, 17), (5, 17), (4, 18)], "#e8e0d0")


def _wrasse(s, body, pattern, fin=None, eye=(6, 14)):
    """A long, cigar-shaped wrasse with one long back fin."""
    _reef(s, body, rx=12, ry=5, cx=15, fin=fin or mix(body, "#000000", 0.15), eye=eye,
          dorsal=[(8, 12.5), (10, 9.5), (24, 10.5), (25, 13)], anal=[(14, 20), (16, 22.5), (24, 21.5), (25, 19)],
          pattern=pattern)


@sprite("mediterranean_rainbow_wrasse")
def _(s):
    # A slender wrasse with a zigzag orange stripe, a blue-and-black patch and a white belly.
    def pat(s, m):
        s.paint(s.m_ellipse(15, 19, 12, 2.4), "#f0eee8", within=m)
        s.paint(s.m_path([(4, 15), (10, 14.5), (14, 16), (19, 15), (27, 16)], 0.6), "#e8702a", within=m)
        s.paint(s.m_ellipse(13, 13, 2, 1.2), "#1e2a5a", within=m)
    _wrasse(s, "#4a7a8a", pat, fin="#3a6a7a")


@sprite("ornate_wrasse")
def _(s):
    # A brilliant green-and-blue wrasse with red-violet bands on its head.
    def pat(s, m):
        for x in (8, 11, 15, 19, 23):
            s.paint(s.m_line(x, 11, x - 1, 21), "#3a7ac8", within=m)
        s.paint(s.m_line(4, 15, 9, 13) | s.m_line(4, 17, 9, 16), "#c84a7a", within=m)
    _wrasse(s, "#3aa070", pat, fin="#2a8a68")


@sprite("east_atlantic_peacock_wrasse")
def _(s):
    # A deeper wrasse with rows of red-and-blue spots on a greenish body and a big lip.
    def pat(s, m):
        for y in (13, 16, 19):
            s.paint(s.m_px([(x + (y % 2), y) for x in range(8, 25, 3)]), "#c84a3a", within=m)
        s.paint(s.m_ellipse(14, 18, 10, 1.4), "#4a8ad0", within=m)
    _reef(s, "#6a9a68", rx=11.5, ry=6.5, cx=15, fin="#5a8a5a", eye=(7, 14), pattern=pat,
          dorsal=[(8, 11), (10, 8), (24, 9), (25, 12)], anal=[(14, 21), (16, 24), (24, 22), (25, 19)])


@sprite("red_sea_goatfish")
def _(s):
    # A pale goatfish with a black stripe from snout to tail, a black spot near the tail and two chin barbels.
    def pat(s, m):
        s.paint(s.m_line(4, 14, 22, 14) | s.m_line(4, 15, 22, 15), "#2b2a30", within=m)
        s.paint(s.m_ellipse(24, 15, 1.4, 1.4), "#2b2a30", within=m)
    fish(s, "#e0c8a8", "#f6f0e4", fin="#e8d0a0", pattern=pat)
    s.path([(4, 19), (6, 23)], 0.4, "#e8d8a0", shade=False)


@sprite("rivulated_rabbitfish")
def _(s):
    # A flat oval fish with golden wavy lines and venomous spines; it grazes algae.
    def pat(s, m):
        for y in (11, 14, 17, 20):
            s.paint(s.m_path([(7, y), (11, y - 1), (15, y), (19, y - 1), (25, y)], 0.4), "#d8b050", within=m)
    _reef(s, "#8a8a6a", rx=10.5, ry=7, cx=15, fin="#7a7a5a", eye=(7, 13), pattern=pat,
          dorsal=[(9, 10), (12, 6), (23, 7), (25, 12)], anal=[(12, 21), (16, 25), (24, 22), (25, 19)])


@sprite("dusky_spinefoot")
def _(s):
    # A plain, olive-brown rabbitfish with a yellowish edge to its fins.
    _reef(s, "#6a6248", rx=10.5, ry=7, cx=15, fin="#c8b050", eye=(7, 13),
          dorsal=[(9, 10), (12, 6), (23, 7), (25, 12)], anal=[(12, 21), (16, 25), (24, 22), (25, 19)])


@sprite("flavimaculosus_puffer")
def _(s):
    # A small puffer, brown above with yellow spots and a white belly, that blows itself up when scared.
    puff = s.act == "sad"
    def pat(s, m):
        s.paint(s.m_ellipse(15, 21, 9, 3.5), "#f4f2ea", within=m)
        s.paint(s.m_px([(9, 12), (12, 11), (15, 12), (18, 11), (21, 13), (11, 15), (17, 15), (20, 16)]), "#f0d040",
                within=m)
    _reef(s, "#7a6a4a", rx=10 if not puff else 11, ry=6.5 if not puff else 9, cx=15, fin="#a89a6a", eye=(7, 13),
          pattern=pat, dorsal=[(19, 11), (21, 8), (23, 11)], anal=[(19, 21), (21, 24), (23, 21)])


@sprite("blue_spotted_cornetfish")
def _(s):
    # A very long, thin fish with a tube snout, blue spots and a whip at the end of its tail.
    s.can("swim")
    w = s.wave() if s.act == "swim" else 0
    c = "#8a9a7a"
    s.path([(28, 17), (31, 17 + w), (35, 18 + w * 2)], 0.35, c, shade=False)
    s.poly([(25, 17), (28, 14 + w), (28, 20 + w)], c)
    m = s.path([(-2, 16.5), (6, 16.5), (16, 17), (26, 17)], (1.0, 2.2), c, edge=True)
    s.paint(s.m_line(-2, 18, 26, 18), "#c8d0b8", within=m)
    s.paint(s.m_px([(10, 16), (14, 16), (18, 16), (22, 16)]), "#3a8ad8", within=m)
    s.poly([(19, 15.5), (22, 13), (23, 15.5)], c)
    s.eye(7, 16, size=1)
    s.px([(7, 15)], "#e8e0c0")


@sprite("indian_lionfish")
def _(s):
    # A red-and-white striped lionfish with long venomous spines and big fan-like fins.
    s.can("swim")
    w = s.wave() if s.act == "swim" else 0
    for k in range(6):  # the tall spines of the back fin
        x = 9 + k * 2.4
        s.path([(x, 11), (x + 1.5, 3 + abs(k - 2) * 0.8)], 0.35, "#c8503a" if k % 2 else "#f0e8e0", shade=False)
    for k in range(5):  # the big pectoral fans
        a = math.radians(40 + k * 22)
        s.path([(14, 19), (14 + 13 * math.cos(a) * 0.7, 19 + 10 * math.sin(a) + w)], 0.5,
               "#d0603a" if k % 2 else "#f0e0d0", shade=False)
    def pat(s, m):
        for x in (7, 10, 13, 16, 19, 22):
            s.paint(s.m_line(x, 9, x + 1, 24), "#a8302a", within=m)
    _reef(s, "#f0e4d8", rx=10, ry=6, cx=15, fin="#e0b0a0", eye=(7, 13), pattern=pat, pec=False)
    s.px([(4, 12), (5, 11)], "#c8503a")


@sprite("madeira_scorpionfish")
def _(s):
    # A small, lumpy red-brown scorpionfish that sits camouflaged on rocks, with frilly flaps.
    def pat(s, m):
        s.paint(s.m_px([(9, 12), (12, 15), (16, 12), (19, 15), (22, 13), (14, 19), (19, 19)]), "#5a2a1e", within=m)
        s.paint(s.m_px([(11, 18), (17, 16), (21, 18)]), "#f0d0b0", within=m)
    _reef(s, "#b0503a", rx=10.5, ry=6.5, cx=15, fin="#9a4a34", eye=(7, 12), pattern=pat,
          dorsal=[(9, 11), (11, 6), (14, 8), (16, 6), (19, 8), (22, 7), (24, 12)])
    s.px([(6, 10), (8, 10)], "#9a4a34")


def _blenny(s, body, pattern, *, crest=None, fin=None):
    """A blenny: a long, blunt-headed, scaleless fish that props itself on its fins."""
    s.can("swim")
    w = s.wave() if s.act == "swim" else 0
    fin = fin or mix(body, "#000000", 0.15)
    _fluke(s, [(25, 17), (31, 13), (31, 21)], fin, w, pivot_x=25)
    s.poly([(9, 15), (11, 11.5), (25, 13), (26, 16)], fin, edge=True)
    s.poly([(14, 21), (25, 20.5), (24, 23), (15, 23)], fin)
    m = s.path([(6, 17.5), (12, 17), (20, 17.5), (26, 17.5)], (5, 2.8), body, edge=True)
    if pattern:
        pattern(s, m)
    if crest:
        crest(s)
    s.ellipse(9, 22, 2.4, 1.2, mix(fin, "#ffffff", 0.2), rot=40, shade=False)
    s.eye(4, 14)
    s.px([(2, 18), (3, 18)], mix(body, "#000000", 0.5))


@sprite("peacock_blenny")
def _(s):
    # A green-gray blenny with blue-edged dark bars, a black eyespot behind the eye and a yellow head crest.
    def pat(s, m):
        _bars((10, 14, 18, 22), "#4a5a4a", 13, 22)(s, m)
        s.paint(s.m_ellipse(8, 15, 1.2, 1.2), "#1e1a22", within=m)
        s.paint(s.m_ellipse(8, 15, 1.9, 1.9) & ~s.m_ellipse(8, 15, 1.2, 1.2), "#4a8ad8", within=m)
    _blenny(s, "#8aa080", pat, crest=lambda s: s.ellipse(5, 11, 2.2, 1.8, "#f0c040", edge=True))


@sprite("ringneck_blenny")
def _(s):
    # A brown-barred blenny with a dark ring around its throat and tiny branched tentacles over its eyes.
    def pat(s, m):
        _bars((11, 15, 19, 23), "#5a4030", 13, 22)(s, m)
        s.paint(s.m_line(6, 13, 6, 22), "#2b2226", within=m)
    _blenny(s, "#b09070", pat, crest=lambda s: s.line(4, 12, 4, 10, "#8a6a4a"))


@sprite("mediterranean_moray")
def _(s):
    # A long, snake-like dark-brown eel speckled with yellow, poking from its rock with an open mouth.
    s.can("swim")
    w = s.wave() if s.act == "swim" else 0
    c = "#4a3a2e"
    pts = [(4, 13), (9, 15 + w), (15, 19 - w), (21, 18 + w), (27, 21 - w), (31, 24)]
    m = s.path(pts, (3.2, 1.2), c, edge=True)
    s.paint(s.m_px([(7, 13), (10, 16), (13, 18), (16, 19), (19, 18), (22, 19), (25, 21), (12, 16), (18, 20)]),
            "#e8c860", within=m)
    s.paint(s.m_path(pts, 0.4), "#6a5440", within=m)
    gape = 1 if s.act in ("idle", "eat") and s.f % 4 < 2 else 0
    s.erase(s.m_poly([(0, 13 + gape * 0.3), (4, 14), (0, 15 + gape)]))
    s.eye(4, 11)


@sprite("small_spotted_catshark")
def _(s):
    # A small, slender sand-colored shark covered in little dark spots, with its back fins set far back.
    s.can("swim")
    w = s.wave() if s.act == "swim" else 0
    c = "#c0a078"
    _fluke(s, [(24, 17), (32, 14), (31, 17), (27, 20)], c, w)
    s.poly([(18, 13), (20, 9), (22, 13)], c)
    s.poly([(22, 14), (23.5, 11), (25, 15)], c)
    s.poly([(9, 20), (14, 25), (15, 20)], c)
    m = s.ellipse(14, 17, 12, 4, c, edge=True)
    s.paint(s.m_ellipse(12, 20, 10, 1.5), "#f0e8dc", within=m)
    s.paint(s.m_px([(6, 15), (9, 14), (12, 16), (15, 14), (18, 16), (21, 15), (10, 17), (24, 17), (16, 17)]),
            "#5a4434", within=m)
    s.paint(s.m_px([(7, 17), (8, 17), (9, 18)]), "#8a7050", within=m)
    s.eye(5, 15)
    s.px([(3, 18), (4, 18)], "#5a4434")


# --------------------------------------------------------------------------- crabs and crayfish
@sprite("edible_crab")
def _(s):
    # A big, red-brown crab with a pie-crust edge to its oval shell and black-tipped claws.
    def pat(s, m):
        s.paint(s.m_px([(7, 17), (8, 15), (24, 15), (25, 17), (10, 14), (22, 14)]), "#7a3a24", within=m)
    crab(s, "#b8603a", "#c06a40", legs="#a0502e", pattern=pat)
    s.px([(2, 8), (3, 8), (29, 8), (28, 8)], "#1e1a1e")


@sprite("velvet_swimming_crab")
def _(s):
    # A fierce, velvety brown crab with blue-lined legs, red eyes and paddle-shaped back legs.
    def pat(s, m):
        s.paint(s.m_line(8, 20, 24, 20), "#3a5ad0", within=m)
    crab(s, "#5a4a3a", "#6a5a46", legs="#4a5a8a", pattern=pat)
    s.px([(11, 9), (20, 9)], "#e02a2a")
    s.ellipse(29, 27, 2, 1.2, "#4a5a8a", mirror=True)


@sprite("marbled_crab")
def _(s):
    # A square-shelled shore crab, olive-green with fine pale marbling.
    def pat(s, m):
        s.paint(s.m_path([(8, 18), (12, 16), (16, 19), (20, 16), (24, 18)], 0.4), "#c8c8a0", within=m)
        s.paint(s.m_path([(9, 22), (14, 21), (19, 23), (23, 21)], 0.4), "#c8c8a0", within=m)
    crab(s, "#4a5a3a", "#5a6a46", legs="#4a5a3a", pattern=pat)


@sprite("warty_crab")
def _(s):
    # A stout crab, dark red-brown and covered in warts, with big black-fingered claws.
    def pat(s, m):
        s.paint(s.m_px([(9, 17), (12, 16), (15, 15), (18, 16), (21, 17), (11, 20), (16, 19), (20, 20), (14, 23)]),
                "#e0a070", within=m)
    crab(s, "#8a3a26", "#9a4a2a", legs="#7a3a26", pattern=pat)
    s.px([(2, 8), (3, 8), (2, 9), (29, 8), (28, 8), (29, 9)], "#1e1a1e")


@sprite("east_atlantic_sally_lightfoot_crab")
def _(s):
    # A flat, nimble shore crab, dark with bright orange-red speckles.
    def pat(s, m):
        s.paint(s.m_px([(9, 17), (12, 16), (16, 17), (20, 16), (23, 18), (11, 20), (15, 21), (19, 20), (22, 22)]),
                "#e8602a", within=m)
    crab(s, "#3a2e2e", "#d0502a", legs="#5a3a2e", pattern=pat)


@sprite("nimble_spray_crab")
def _(s):
    # A flat crab with long, yellow-banded legs and a dark brown-green shell.
    def pat(s, m):
        s.paint(s.m_line(16, 15, 16, 25), "#c8b040", within=m)
    crab(s, "#4a4a30", "#5a5a38", legs="#d8b840", pattern=pat)


@sprite("mediterranean_freshwater_crab")
def _(s):
    # A river crab with a smooth, cream-brown shell and stout claws.
    crab(s, "#b08858", "#a07a4e", legs="#8a6a44",
         pattern=lambda s, m: s.paint(s.m_ellipse(16, 19, 6, 2.5), "#c8a070", within=m))


@sprite("white_tipped_mud_crab")
def _(s):
    # A tiny brown mud crab whose claws have white-tipped fingers.
    crab(s, "#7a6448", "#8a7050", legs="#6a5640")
    s.px([(2, 8), (3, 8), (29, 8), (28, 8)], "#f4f0e8")


@sprite("west_african_fiddler_crab")
def _(s):
    # The male waves one huge orange claw; the shell is purple-brown.
    crab(s, "#6a4a5a", "#e8803a", legs="#8a5a5a", big_claw=True, stalks=3)


def _spider_crab(s, shell, legs, *, spines=False):
    """A spider crab: a pear-shaped shell (narrow at the front) on long, thin legs."""
    s.can("walk")
    w = s.wave() if s.act == "walk" else 0
    for i, y in enumerate((17, 20, 23, 26)):
        d = w * 1.3 * (1 if i % 2 else -1)
        s.path([(10, y - 1), (3, y - 3 + d), (0, y + 4 + d)], 0.6, legs, shade=False, mirror=True)
    s.path([(11, 15), (7, 10)], 0.8, legs, mirror=True)
    s.ellipse(6.5, 9, 1.6, 1.3, legs, mirror=True)
    m = s.poly([(16, 9), (21, 13), (23, 21), (19, 27), (13, 27), (9, 21), (11, 13)], shell, edge=True)
    if spines:
        s.px([(10, 15), (9, 18), (8, 21), (12, 12)], shell, mirror=True)
        s.paint(s.m_px([(13, 15), (16, 14), (19, 15), (12, 19), (15, 18), (18, 19), (14, 22), (17, 23)]),
                mix(shell, "#ffffff", 0.35), within=m)
    s.line(15, 9, 14, 6, shell)
    s.line(17, 9, 18, 6, shell)
    s.px([(13, 10), (19, 10)], EYE)


@sprite("great_spider_crab")
def _(s):
    # The Atlantic lyre crab: a pear-shaped shell, gray-red, often dressed with bits of weed and sponge.
    _spider_crab(s, "#a06a50", "#8a5a44")
    s.paint(s.m_px([(14, 16), (18, 18), (15, 22)]), "#6a8a4a")


@sprite("spiny_spider_crab")
def _(s):
    # A big, spiny red-orange spider crab that marches across the seabed in great herds.
    _spider_crab(s, "#c8603a", "#b0583a", spines=True)


def _cray(s, body, dark, spots, tip, *, narrow=False):
    _crayfish(s, body, dark, spots, tip)
    if narrow:  # long, slim claws
        s.path([(6, 10), (1, 5)], 0.7, body)


@sprite("european_crayfish")
def _(s):
    # The noble crayfish: dark brown-olive with big claws that are red underneath.
    _cray(s, "#5a4a36", "#2e2620", "#3a3024", "#d8402a")


@sprite("narrow_clawed_crayfish")
def _(s):
    # A sand-colored crayfish with long, slender, narrow claws.
    _cray(s, "#a89068", "#5a4a34", "#7a6448", "#e8c8a0", narrow=True)


@sprite("spinycheek_crayfish")
def _(s):
    # An American crayfish gone wild in Europe: brown with rusty-red bands on its tail and spines on its cheeks.
    _cray(s, "#7a6a4a", "#3a3020", "#a8402a", "#e8802a")
    s.paint(s.m_line(20, 17, 20, 24) | s.m_line(26, 17, 26, 24), "#a8402a")


@sprite("stone_crayfish")
def _(s):
    # A small, pale brown crayfish of cold, clean mountain streams.
    _cray(s, "#9a8a6a", "#5a4e3a", "#6a5e48", "#c8b898")


# --------------------------------------------------------------------------- jellies, anemones, urchins, star
@sprite("barrel_jelly")
def _(s):
    # A huge, firm white dome with a violet-blue rim and thick, frilly arms underneath.
    jelly(s, "#e8e8f0", rim="#6a6ad0", arms="#d8d8e8")
    s.ellipse(16, 20, 4, 2, "#c8c8e0")


@sprite("dustbin_lid_jelly")
def _(s):
    # The Atlantic barrel jelly: a thick bluish-white bell with a purple rim and cauliflower arms.
    jelly(s, "#d8e0ec", rim="#8a5ab0", arms="#c8d0e0")
    s.ellipse(14, 22, 2, 1.6, "#b8c0d8")
    s.ellipse(18, 22, 2, 1.6, "#b8c0d8")


@sprite("blue_jelly")
def _(s):
    # A blue-violet bell with a pale center and a curtain of fine tentacles.
    jelly(s, "#6a7ad0", rim="#4a5ab0", arms="#a8b0e8", tentacles="#8a98e0", stripes="#8a9ae0")


@sprite("compass_jelly")
def _(s):
    # A cream bell marked with sixteen brown V-shapes like the points of a compass.
    jelly(s, "#f0e4cc", rim="#a8603a", arms="#f0d8b8", tentacles="#c8885a", stripes="#a8603a")


@sprite("common_moon_jelly")
def _(s):
    # A clear, saucer-shaped jelly with four pale violet rings (its gonads) and a fringe of fine tentacles.
    jelly(s, "#dce8f4", rim="#c8d8ec", arms="#e8eef8", tentacles="#c8d4e8")
    for x in (11, 15, 19, 23):
        s.paint(s.m_ellipse(x - 1, 10, 1.6, 1.6) & ~s.m_ellipse(x - 1, 10, 0.8, 0.8), "#b088c8")


@sprite("jelly_blubber")
def _(s):
    # A firm, milky-white jelly with a brown-dotted bell and short, thick arms.
    jelly(s, "#ece4d8", rim="#c8a880", arms="#d8ccb8")
    s.paint(s.m_px([(9, 9), (12, 7), (16, 6), (20, 7), (23, 9), (11, 12), (16, 11), (21, 12)]), "#8a6a4a")


@sprite("lions_mane_jelly")
def _(s):
    # The biggest jelly in the world: a red-brown bell trailing a huge shaggy mane of tentacles.
    w = s.wave() if s.act == "swim" else 0
    jelly(s, "#a83a26", rim="#d0703a", arms="#e8a050", tentacles="#c85a2a", stripes="#7a2a1a")
    for x0 in (6.5, 10.5, 15.5, 21.5, 25.5):
        s.path([(x0, 15), (x0 + 1 - w, 20), (x0 - 1 + w, 25), (x0 + w, 30)], 0.55, "#b84a26", shade=False)


@sprite("mauve_stinger")
def _(s):
    # A small, glowing pink-mauve jelly covered in warts, with long trailing tentacles.
    jelly(s, "#c88ab8", rim="#a86aa0", arms="#e0a8d0", tentacles="#b878a8")
    s.paint(s.m_px([(9, 10), (12, 8), (16, 7), (20, 8), (23, 10), (14, 11), (19, 11)]), "#e8b8e0")


@sprite("atlantic_beadlet_anemone")
def _(s):
    # A shiny, blood-red blob of an anemone with a ring of blue beads below its tentacles.
    _anemone(s, "#b8202a", "#d0303a", "#c02832", "#a81a26", band="#e04a50")
    s.px([(9, 16), (12, 16), (15, 16), (18, 16), (21, 16), (23, 16)], "#4a6ad8")


@sprite("snakelocks_anemone")
def _(s):
    # Long, wavy green tentacles tipped with purple, which it cannot pull back in.
    _anemone(s, "#8a9a6a", "#6ab84a", "#7ac860", "#5a8a40", band="#b05ab0")
    s.px([(5, 7), (10, 7), (16, 7), (21, 7), (27, 7)], "#b05ab0")


@sprite("atlantic_purple_sea_urchin")
def _(s):
    # The rock urchin: a purple-to-olive ball of short, sharp spines that bores hollows into rock.
    for k in range(18):
        a = k * math.pi / 9 + 0.1
        s.line(16 + 6 * math.cos(a), 18 + 5.5 * math.sin(a), 16 + 11 * math.cos(a), 18 + 9.5 * math.sin(a),
               "#6a3a7a" if k % 2 else "#5a5a3a")
    s.ellipse(16, 18, 8, 7.5, "#4a2a5a", edge=True)
    s.px([(11, 14), (13, 12), (19, 13), (21, 16), (12, 21), (20, 22)], "#7a4a8a")


@sprite("black_longspine_urchin")
def _(s):
    # A black urchin with very long, thin, needle-sharp spines.
    for k in range(18):
        a = k * math.pi / 9 + 0.15
        s.line(16 + 5 * math.cos(a), 21 + 4 * math.sin(a), 16 + 15 * math.cos(a), 21 + 13 * math.sin(a),
               "#2a2630")
    s.ellipse(16, 22, 7, 5.5, "#1e1a22", edge=True)
    s.px([(14, 19), (18, 19)], "#4a6ad8")
    s.px([(16, 18)], "#e8a040")


@sprite("spiny_starfish")
def _(s):
    # A big gray-violet starfish with long arms lined with rows of white spines.
    star(s, "#9a7a9a", arms=0.6, dots="#f4f0f0")


@sprite("bay_barnacle")
def _(s):
    # A small white volcano-shaped shell glued to rock; it kicks out feathery legs to catch food.
    s.can("eat")
    s.ellipse(16, 29, 12, 2, "#8a8a84")
    for x in (8, 16, 24):
        m = s.poly([(x - 6, 28), (x - 3, 19), (x + 3, 19), (x + 6, 28)], "#ece8e0", edge=True)
        s.paint(s.m_line(x - 2, 20, x - 4, 27) | s.m_line(x + 2, 20, x + 4, 27), "#c8c4b8", within=m)
        s.px([(x - 1, 19), (x, 19)], "#5a5a54")
    if s.act in ("eat", "idle") and s.f % 4 < 2:
        for dx in (-2, 0, 2):
            s.path([(16, 18), (16 + dx * 1.5, 12), (16 + dx * 2.5, 9)], 0.35, "#e8d8b0", shade=False)


@sprite("bearded_fireworm")
def _(s):
    # A thick bristle worm with tufts of white stinging bristles along its red-orange sides.
    s.can("walk")
    w = s.wave() if s.act == "walk" else 0
    c = "#c8603a"
    pts = [(4 + i * 3, 21 + 1.6 * math.sin(i * 0.9 + w * 1.5)) for i in range(9)]
    for x, y in pts:
        s.path([(x, y), (x - 0.5, y - 4)], 0.45, "#f4f0ea", shade=False)
        s.path([(x, y), (x - 0.5, y + 4)], 0.45, "#f4f0ea", shade=False)
    m = s.path(pts, (2.6, 1.6), c, edge=True)
    for i, (x, y) in enumerate(pts[1:], 1):
        s.paint(s.m_line(x - 1.5, y - 3, x - 1.5, y + 3), "#9a3a26", within=m)
    s.paint(s.m_ellipse(5, 19, 1.6, 1), "#e85a5a", within=m)
    s.eye(3, 20, size=1)


# --------------------------------------------------------------------------- isopods, woodlice
@sprite("baltic_isopod")
def _(s):
    # A long, flat sea isopod, green or brown with white flecks, clinging to seaweed.
    s.can("swim", "walk")
    w = s.wave() if s.act in ("swim", "walk") else 0
    c = "#5a7a4a"
    for i, x in enumerate((9, 13, 17, 21)):
        d = round(w * (1 if i % 2 else -1))
        s.line(x, 22, x - 1 + d, 26, "#3a4a30")
    m = s.path([(6, 19), (16, 19), (27, 19.5)], (3.5, 2.6), c, edge=True)
    for x in (10, 13, 16, 19, 22):
        s.paint(s.m_line(x, 15, x, 23), _dk(c), within=m)
    s.paint(s.m_px([(11, 18), (17, 17), (21, 19), (14, 20)]), "#e8ece0", within=m)
    s.poly([(27, 17), (31, 19.5), (27, 22)], c)
    s.line(4, 17, 0, 13, "#3a4a30")
    s.eye(5, 18, size=1)


@sprite("italian_sea_slater")
def _(s):
    # A big, fast gray woodlouse of seaside rocks, with long antennae and two forked tail prongs.
    g = "#7a7670"
    m = _woodlouse(s, g, "#a8a49c")
    s.paint(s.m_px([(10, 18), (16, 17), (22, 18)]), "#a8a49c", within=m)
    s.line(27, 21, 31, 18, _dk(g))
    s.line(27, 22, 31, 25, _dk(g))
    s.ellipse(6.5, 21, 3.5, 3.2, _dk(g, 0.15), edge=True)
    s.path([(4, 19), (1, 14), (-1, 12)], 0.4, "#3a3632", shade=False)
    s.eye(5, 20)


@sprite("clown_isopod")
def _(s):
    # A pill woodlouse dotted with bright yellow-orange spots on a dark body.
    roll = s.act == "sleep"
    g = "#3a3438"
    m = _woodlouse(s, g, "#6a6468", roll=True)
    s.paint(s.m_px([(10, 17), (13, 16), (16, 16), (19, 16), (22, 17), (12, 21), (18, 21), (24, 20)]), "#f0b030",
            within=m)
    if not roll:
        s.ellipse(6.5, 22, 3.5, 4, _dk(g, 0.15), edge=True)
        s.line(4, 19, 1, 15, "#2b2626")
        s.eye(5, 21)


@sprite("versicolored_pill_woodlouse")
def _(s):
    # A pill woodlouse marbled gray and pale yellow, that rolls into a ball.
    g = "#6a6660"
    m = _woodlouse(s, g, "#a8a49c", roll=True)
    s.paint(s.m_px([(9, 18), (12, 20), (15, 17), (18, 20), (21, 17), (24, 19), (14, 22), (20, 23)]), "#d8c890",
            within=m)
    if s.act != "sleep":
        s.ellipse(6.5, 22, 3.5, 4, _dk(g, 0.15), edge=True)
        s.line(4, 19, 1, 15, "#2b2626")
        s.eye(5, 21)


@sprite("ratzeburgs_woodlouse")
def _(s):
    # A flat, rough gray-brown woodlouse with pale spots along its edges.
    g = "#6a5a50"
    m = _woodlouse(s, g, "#a89a8a")
    s.paint(s.m_px([(7, 21), (10, 25), (13, 25), (16, 25), (19, 25), (22, 25), (25, 22)]), "#d8ccbc", within=m)
    s.line(27, 22, 30, 24, _dk(g))
    s.ellipse(6.5, 22, 3.5, 3.5, _dk(g, 0.15), edge=True)
    s.line(4, 19, 0, 16, "#3a3430")
    s.eye(5, 21)


# --------------------------------------------------------------------------- millipedes, centipedes, springtails
@sprite("brown_centipede")
def _(s):
    # A shiny chestnut-brown stone centipede with fifteen pairs of legs.
    _segmented(s, 8, "#9a5a2e", "#7a4220", "#b0703e", leg_len=2.6, spacing=3.0, r=2.0, antenna=4,
               tail="#9a5a2e")


@sprite("mediterranean_banded_centipede")
def _(s):
    # A big, venomous centipede with dark bands across a yellow-olive body and orange legs.
    pts = _segmented(s, 9, "#b8a050", "#a87030", "#e0903a", leg_len=2.8, spacing=2.9, r=2.4, antenna=3.5,
                     tail="#e0903a")
    for i, (x, y) in enumerate(pts[1:], 1):
        s.paint(s.m_line(x + 1, y - 3, x + 1, y + 3), "#3a3a2a", within=s.m_ellipse(x, y, 2.4, 2.4))


@sprite("common_pill_millipede")
def _(s):
    # A short, shiny black millipede with pale segment edges, that rolls into a perfect ball like a pill woodlouse.
    roll = s.act == "sleep"
    g = "#2a2628"
    for i, x in enumerate(range(8, 25, 2)):
        s.line(x, 25, x - 1 + (i % 2), 28, "#5a5250")
    m = s.ellipse(16, 21, 11, 7 if roll else 6, g, edge=True)
    for x in (10, 13, 16, 19, 22, 25):
        s.paint(s.m_line(x, 13, x, 29), "#8a7a60", within=m)
    s.paint(s.m_ellipse(16, 27, 11, 1.2), "#e8d090", within=m)
    if not roll:
        s.ellipse(6.5, 22, 3.2, 3.6, "#1e1a1c", edge=True)
        s.line(4, 19, 2, 15, "#5a5250")
        s.eye(5, 21)


@sprite("collared_flat_backed_millipede")
def _(s):
    # A flat-backed brown millipede with keels sticking out at the sides of each segment.
    pts = _segmented(s, 9, "#8a6a4a", "#7a5a3e", "#a88a6a", leg_len=1.8, spacing=2.8, r=2.2, antenna=2.5)
    for x, y in pts[1:]:
        s.px([(round(x), round(y - 3)), (round(x), round(y + 3))], "#6a5038")


@sprite("striped_millipede")
def _(s):
    # A long, shiny dark millipede with two pale stripes running along its back.
    pts = _segmented(s, 10, "#3a3430", "#2b2626", "#b09070", leg_len=1.6, spacing=2.6, r=2.0, antenna=2.4)
    for x, y in pts:
        s.px([(round(x), round(y - 1))], "#d8c8a0")


@sprite("hungarian_pachyiulus")
def _(s):
    # A big, glossy black millipede with fine reddish rings and pale legs.
    pts = _segmented(s, 10, "#2a2426", "#1e1a1c", "#d8c8a8", leg_len=1.8, spacing=2.6, r=2.3, antenna=2.5)
    for x, y in pts[1:]:
        s.px([(round(x + 1), round(y - 1)), (round(x + 1), round(y))], "#8a3a2a")


@sprite("kotor_pachyiulus")
def _(s):
    # A long Balkan millipede, dark brown banded with orange.
    pts = _segmented(s, 10, "#4a3226", "#3a2620", "#e0a060", leg_len=1.8, spacing=2.6, r=2.3, antenna=2.5)
    for x, y in pts[1::2]:
        s.px([(round(x), round(y - 1)), (round(x), round(y))], "#d8803a")


@sprite("yellow_legged_pachyiulus")
def _(s):
    # A big black millipede that walks on rows of bright yellow legs.
    _segmented(s, 10, "#26222a", "#1e1a22", "#f0d040", leg_len=2.2, spacing=2.6, r=2.3, antenna=2.5)


def _springtail(s, body, *, bands=None, spots=None):
    """A springtail: a tiny, long-legged, long-antennaed hexapod that flicks itself into the air."""
    s.can("walk")
    hop = s.act == "walk" and s.f % 8 in (2, 3, 4)
    y0 = -5 if hop else 0
    w = s.wave() if s.act == "walk" else 0
    for i, x in enumerate((10, 14, 18)):
        d = w * (1 if i % 2 else -1)
        s.path([(x, 21 + y0), (x - 1 + d, 25 + y0), (x - 2 + d, 28 + y0)], 0.4, _dk(body, 0.2), shade=False)
    s.path([(25, 21 + y0), (28, 25 + y0), (25, 27 + y0)], 0.4, _dk(body, 0.3), shade=False)  # the spring
    m = s.path([(8, 18 + y0), (16, 19 + y0), (25, 19 + y0)], (3, 3.2), body, edge=True)
    for x0, x1, col in (bands or []):
        s.paint(s.m_poly([(x0, 10), (x1, 10), (x1, 28), (x0, 28)]), col, within=m)
    if spots:
        s.paint(s.m_px([(11, 17 + y0), (15, 18 + y0), (19, 17 + y0), (22, 18 + y0)]), spots, within=m)
    s.ellipse(6, 18 + y0, 2.6, 2.4, body, edge=True)
    s.path([(5, 17 + y0), (3, 11 + y0), (0, 6 + y0)], 0.4, _dk(body, 0.3), shade=False)
    s.path([(6, 16 + y0), (7, 10 + y0), (5, 5 + y0)], 0.4, _dk(body, 0.3), shade=False)
    s.eye(4, 17 + y0, size=1)


@sprite("belted_springtail")
def _(s):
    # A long, hairy springtail, yellow with a black belt around its middle.
    _springtail(s, "#d8b860", bands=[(15, 18, "#2b2226"), (22, 23, "#5a4a3a")])


@sprite("cosmopolitan_springtail")
def _(s):
    # A pale gray-yellow springtail with dark zigzag marks along its back.
    _springtail(s, "#d8d0b0", spots="#3a3430")
