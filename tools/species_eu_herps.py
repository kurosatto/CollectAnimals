"""Sprites for the European (and Turkish) reptiles and amphibians that the US lists
don't have. Imported by make_sprites.py, which registers the drawings via @sprite.

Lizards and salamanders use lizard() (pattern(s, m) paints the body; head details
go in the old head coordinates, eye at 5, 17); snakes snake(); turtles turtle();
frogs and toads frog()."""
from __future__ import annotations

from archetypes import BLACK, WHITE, frog, lizard, sea_turtle, snake, sprite, turtle
from pixel import mix


def _dots(pts, col):
    return lambda s, m: s.paint(s.m_px(pts), col, within=m)


def _lines(ys, col, x0=8, x1=22):
    def pat(s, m):
        for y in ys:
            s.paint(s.m_line(x0, y, x1, y), col, within=m)
    return pat


def _both(*fns):
    def pat(s, m):
        for f in fns:
            f(s, m)
    return pat


NET = [(9, 20), (11, 21), (13, 20), (15, 21), (17, 20), (19, 21), (21, 20), (12, 23), (18, 23), (10, 22), (16, 22)]
SPOTS = [(10, 19), (13, 20), (16, 19), (19, 20), (11, 22), (15, 22), (18, 22), (21, 21)]


# --------------------------------------------------------------------------- wall and rock lizards
def _wall(s, body, belly, *, back=None, net="#2e2a22", stripe=None, throat=None, head=None, tail=None, blue=None,
          long_tail=True):
    pats = []
    if back:
        pats.append(lambda s, m: s.paint(s.m_line(8, 19, 22, 19) | s.m_line(8, 20, 22, 20), back, within=m))
    if stripe:
        pats.append(_lines((21.5,), stripe))
    if net:
        pats.append(_dots(NET, net))
    if blue:
        pats.append(_dots([(10, 23), (13, 23), (16, 23)], blue))
    lizard(s, body, belly, head=head or body, throat=throat or belly, pattern=_both(*pats),
           tail_col=tail or mix(body, "#1a1420", 0.1),
           tail_pts=[(20, 22), (27, 25), (33, 24), (36, 20)] if long_tail else None)


@sprite("balkan_wall_lizard")
def _(s):
    # Green back, brown flanks with a pale stripe and a few dark spots.
    _wall(s, "#8a7a54", "#f0ecd0", back="#7aa04a", stripe="#e8e0b0", net="#3a3022")


@sprite("bocages_wall_lizard")
def _(s):
    # A small Iberian wall lizard, green-backed in males, heavily black-netted.
    _wall(s, "#6a8a44", "#e8d8a8", net="#1e2416", throat="#f0c890")


@sprite("catalonian_wall_lizard")
def _(s):
    # Brown with dark lines along the back and a cream belly.
    _wall(s, "#8a7458", "#f0e8d0", back="#5a4a36", stripe="#d8c8a0", net="#3a2e22")


@sprite("dalmatian_wall_lizard")
def _(s):
    # Brown-green with an orange belly and blue spots on the flanks.
    _wall(s, "#7a7a4a", "#e8903a", back="#6a8a3a", net="#2e2a1e", blue="#4a8ad8")


@sprite("erhards_wall_lizard")
def _(s):
    # Greek island lizard: striped gray-brown, with an orange belly.
    _wall(s, "#8a8060", "#e8a050", back="#6a6a4a", stripe="#e8dcb8", net="#2e2a1e")


@sprite("filfola_lizard")
def _(s):
    # The Maltese wall lizard: green and black netted with a bright orange-red belly.
    _wall(s, "#5a8a3a", "#e8603a", net="#1e2416", throat="#e88a4a")


@sprite("green_iberian_wall_lizard")
def _(s):
    # Bright green back with black spots and brown flanks.
    _wall(s, "#8a7448", "#f0ecd0", back="#5ab04a", net="#1e2416")


@sprite("peloponnese_wall_lizard")
def _(s):
    # Big and bold: a green back, an orange-yellow belly and blue shoulder spots.
    _wall(s, "#7a7048", "#f0b040", back="#7ab04a", net="#2e2a1e", blue="#3a7ad8", throat="#f0d060")


@sprite("tyrrhenian_wall_lizard")
def _(s):
    # Sardinia and Corsica: green with black netting all over.
    _wall(s, "#5a9a4a", "#e8e0b0", net="#1a2014")
    s.paint(s.m_px([(10, 18), (14, 18), (18, 18), (20, 19)]), "#1a2014", within=s.m_ellipse(15, 21, 8, 3.5))


@sprite("crimean_rock_lizard")
def _(s):
    # Brown with a dark-edged pale stripe and green tinge on the back.
    _wall(s, "#7a6a4a", "#d8e0c0", back="#7a8a4a", stripe="#e8dcb0", net="#2e261a")


@sprite("lycian_rock_lizard")
def _(s):
    # A flat-bodied rock lizard of southwest Turkey, gray-brown with pale spots and a blue-tinged belly.
    _wall(s, "#7a705c", "#c8d4d8", net="#ece4cc", stripe="#5a5040")


@sprite("sharp_snouted_rock_lizard")
def _(s):
    # Very flat, with a pointed snout and a blue-black netted back.
    _wall(s, "#4a5a6a", "#a8c0d0", net="#1a1e26", head="#5a6a7a")


@sprite("troodos_rock_lizard")
def _(s):
    # A Cypriot mountain lizard, brown with a pale stripe down each side.
    _wall(s, "#7a6a4e", "#e8e0c8", stripe="#e8dcb0", back="#6a5a40", net="#3a2e1e")


@sprite("lebanon_lizard")
def _(s):
    # Olive-brown with pale stripes and a whitish belly.
    _wall(s, "#8a7a5a", "#ece8d8", stripe="#e8e0c0", net="#3a3020")


@sprite("madeira_lizard")
def _(s):
    # Brown with darker speckles, sometimes a blue throat.
    _wall(s, "#7a6a50", "#c8c4a8", net="#2e261c", throat="#5a8ad8")


@sprite("tenerife_lizard")
def _(s):
    # A big dark lizard of the Canaries with blue spots on the cheeks and flanks.
    _wall(s, "#2e2a28", "#4a4a50", net=None, blue="#4a9ae8", throat="#3a3a40")
    s.paint(s.m_px([(5, 19), (7, 20)]), "#4a9ae8")


@sprite("blue_throated_keeled_lizard")
def _(s):
    # A small brown lizard with rough keeled scales and a bright blue throat in males.
    _wall(s, "#7a5a3a", "#e8c070", throat="#3a8ae8", net="#3a2a1a")


@sprite("snake_eyed_lizard")
def _(s):
    # A small, slim lizard with see-through eyelids, bronze with pale stripes.
    _wall(s, "#9a7a52", "#f0ecd8", stripe="#f0e4c0", back="#7a5a3a", net="#3a2a1a")


@sprite("large_psammodromus")
def _(s):
    # A big Iberian lizard: brown with two cream stripes down each side and a very long tail.
    lizard(s, "#8a6a42", "#ece4cc", pattern=_lines((19.5, 22), "#f0e4c0"), tail_col="#9a7a52",
           tail_pts=[(20, 22), (27, 25), (34, 25), (37, 21)])
    s.paint(s.m_px([(9, 19), (8, 19)]), "#4a8ad8")


@sprite("schreibers_fringe_fingered_lizard")
def _(s):
    # A sandy desert lizard with fringed toes, pale lines and a pink-orange tail.
    lizard(s, "#b89a70", "#f4ece0", pattern=_both(_lines((19.5, 22), "#ece0c0"), _dots(SPOTS, "#5a4632")),
           tail_col="#e08a6a", tail_pts=[(20, 22), (27, 25), (33, 24), (36, 20)])


@sprite("viviparous_lizard")
def _(s):
    # A small brown lizard with a dark stripe down the spine; it gives birth to live young.
    lizard(s, "#7a6040", "#e8b050", pattern=_both(_lines((19,), "#2e2418"), _dots(SPOTS, "#4a3a28")),
           tail_col="#6a5236")


@sprite("sand_lizard")
def _(s):
    # Stocky: a brown back with dark-edged white spots and bright green flanks in males.
    def pat(s, m):
        s.paint(s.m_line(8, 19, 22, 19), "#6a4a2a", within=m)
        s.paint(s.m_px([(10, 20), (13, 20), (16, 20), (19, 20)]), WHITE, within=m)
        s.paint(s.m_ellipse(15, 22.5, 7, 1.5), "#6ab84a", within=m)
    lizard(s, "#8a6a40", "#e8e4a0", head="#6ab84a", throat="#a0d070", pattern=pat, tail_col="#7a5c36", wide=True)


@sprite("green_lizard")
def _(s):
    # The eastern green lizard: bright emerald green with black flecks, a blue throat in spring.
    lizard(s, "#4ab840", "#e8f0a0", head="#4ab840", throat="#3a8ae8", pattern=_dots(NET, "#1e3a18"),
           tail_col="#3aa038", tail_pts=[(20, 22), (27, 25), (34, 25), (37, 20)])


@sprite("western_green_lizard")
def _(s):
    # Like the green lizard: vivid green finely speckled with black, a blue throat.
    lizard(s, "#5ac048", "#f0f0a8", head="#5ab848", throat="#4a90e8", pattern=_dots(SPOTS, "#1e3a18"),
           tail_col="#4aa83c", tail_pts=[(20, 22), (27, 25), (34, 25), (37, 20)])


@sprite("balkan_green_lizard")
def _(s):
    # A big green lizard with a yellow throat; young ones have three pale stripes.
    lizard(s, "#58b048", "#f0e880", head="#58b048", throat="#f0d840", pattern=_dots(SPOTS, "#2e5a24"),
           tail_col="#5a8a42", tail_pts=[(20, 22), (27, 25), (34, 25), (37, 20)])


@sprite("iberian_emerald_lizard")
def _(s):
    # Green with black spots and a vivid blue head and throat in breeding males.
    lizard(s, "#5aa840", "#f0e070", head="#4a7ad8", throat="#3a6ad8", pattern=_dots(NET, "#1a2a14"),
           tail_col="#5a8a3a", tail_pts=[(20, 22), (27, 25), (34, 25), (37, 20)])


@sprite("ocellated_lizard")
def _(s):
    # Europe's biggest lizard: green netted in black with rows of sky-blue eyespots on its flanks.
    def pat(s, m):
        s.paint(s.m_px(NET), "#1a2a14", within=m)
        for x in (10, 14, 18):
            s.paint(s.m_ellipse(x, 22.5, 1.2, 1), "#3a8ae8", within=m)
    lizard(s, "#6aa840", "#f0e8a0", head="#6a9a42", throat="#e8e090", pattern=pat, wide=True, tail_col="#6a8a3e",
           tail_pts=[(20, 22), (27, 25), (34, 25), (37, 20)])


# --------------------------------------------------------------------------- skinks, geckos, agamas, chameleon
@sprite("european_copper_skink")
def _(s):
    # A tiny snake-eyed skink, glossy bronze with dark flanks and very short legs.
    lizard(s, "#a07a40", "#c8c8b8", pattern=_lines((22,), "#3a2a1a"), smooth=True, legs="#8a6a3a",
           tail_col="#9a7440")


@sprite("budaks_snake_eyed_skink")
def _(s):
    # A small glossy olive-brown skink from Cyprus with dark side stripes.
    lizard(s, "#8a7448", "#d8d0b8", pattern=_lines((21.5,), "#3a3020"), smooth=True, tail_col="#8a7044")


@sprite("ocellated_bronze_skink")
def _(s):
    # A plump, shiny skink covered in tiny black-and-white eyespots.
    def pat(s, m):
        s.paint(s.m_px(SPOTS), "#1e1a16", within=m)
        s.paint(s.m_px([(x + 1, y) for x, y in SPOTS]), WHITE, within=m)
    lizard(s, "#a08860", "#e8dcc4", pattern=pat, smooth=True, wide=True, tail_col="#988058")


@sprite("bridled_skink")
def _(s):
    # A shiny olive skink with a bold white stripe along each side, edged in dark brown.
    lizard(s, "#8a7a5a", "#f0ecdc", pattern=_both(_lines((21,), "#3a2e1e"), _lines((22,), WHITE)),
           smooth=True, tail_col="#8a7654")
    s.paint(s.m_line(3, 18.5, 10, 18.5), WHITE)


@sprite("moorish_gecko")
def _(s):
    # A chunky gray-brown gecko covered in rows of bumpy tubercles, with wide sticky toe pads.
    lizard(s, "#8a8478", "#e8e4d8", throat="#e8e4d8", pattern=_dots(NET, "#c8c2b4"), eye_big=True, wide=True,
           legs="#7a7468", tail_col="#7a7468")


@sprite("kotschys_gecko")
def _(s):
    # A slim, bent-toed gecko, gray with dark wavy bands.
    lizard(s, "#9a948a", "#ece8e0", pattern=_dots([(10, 19), (10, 20), (14, 19), (14, 20), (18, 19), (18, 20)],
                                                    "#4a4440"), eye_big=True, legs="#8a847a", tail_col="#8a847a")


@sprite("mediterranean_thin_toed_gecko")
def _(s):
    # A small brown thin-toed gecko with pale bumps and dark bars.
    lizard(s, "#8a7a62", "#e8e0cc", pattern=_dots([(11, 19), (11, 20), (15, 19), (15, 20), (19, 19), (19, 20)],
                                                    "#3a3026"), eye_big=True, tail_col="#7a6a54")


@sprite("eastern_mediterranean_thin_toed_gecko")
def _(s):
    # Pale sandy-gray with dark crossbars on its back and tail.
    lizard(s, "#a8a090", "#f0ece4", pattern=_dots([(10, 19), (10, 20), (14, 19), (14, 20), (18, 19), (18, 20)],
                                                    "#5a5246"), eye_big=True, tail_col="#988f80")


@sprite("roughtail_rock_agama")
def _(s):
    # The stellagama: a spiny gray-brown rock lizard with a big triangular head and a ringed spiky tail.
    lizard(s, "#7a705e", "#c8beaa", head="#8a7e68", pattern=_dots(NET, "#e8dcb8"), wide=True, tail_col="#6a604e",
           horns=True)


@sprite("sling_tailed_agama")
def _(s):
    # The Cyprus agama: rough olive-gray with yellowish blotches and a spiny tail.
    lizard(s, "#6a6450", "#c8c0a0", head="#7a7258", pattern=_dots(SPOTS, "#c8b870"), wide=True, tail_col="#5e584a",
           horns=True)


@sprite("common_chameleon")
def _(s):
    # Green with pale stripes, a pointed casque on its head, turret eyes and a curled tail, holding a twig.
    s.path([(-2, 29), (34, 28)], 1.0, "#7a5a3a")
    s.path([(20, 21), (26, 23), (29, 21), (28, 18), (25, 18), (25, 20)], (2.4, 0.9), "#5aa04a")
    lizard(s, "#6ab04a", "#c8e080", head="#6ab84a", wide=True, eye_big=True, legs="#5aa040",
           tail_pts=[(20, 22), (20.5, 22)], tail_col="#6ab04a",
           pattern=lambda s, m: s.paint(s.m_line(9, 22, 21, 21) | s.m_px([(11, 19), (15, 19), (19, 19)]),
                                        "#e8e8a0", within=m))
    s.poly([(7, 15), (11, 11), (13, 15)], "#6ab84a")  # casque
    s.px([(9, 17), (12, 17), (14, 18), (16, 18), (18, 18)], "#4a8a3a")


# --------------------------------------------------------------------------- legless lizards
@sprite("common_slowworm")
def _(s):
    # A legless lizard, not a snake: smooth glossy coppery-brown with dark sides and a small head.
    snake(s, "#a8784a", belly="#3a2a22", stripe="#7a5232", head="#a8784a", head_w=4.6)


@sprite("eastern_slowworm")
def _(s):
    # Glossy bronze-gray, some with blue spots.
    snake(s, "#9a7a5a", belly="#3a2e26", head="#9a7a5a", head_w=4.6)
    s.paint(s.m_px([(9, 22), (19, 22), (13, 26)]), "#4a8ad8", within=s.reg > 0)


@sprite("greek_slowworm")
def _(s):
    # A Greek slowworm, coppery with a thin dark line down its back.
    snake(s, "#b0804a", belly="#4a3828", stripe="#5a3e24", head="#b0804a", head_w=4.6)


@sprite("italian_slowworm")
def _(s):
    # The Italian slowworm: smooth light-brown with dark flanks.
    snake(s, "#b89060", belly="#2e2420", head="#b89060", head_w=4.6)


@sprite("european_glass_lizard")
def _(s):
    # The sheltopusik: a huge legless lizard, olive-brown with a deep groove along each side.
    snake(s, "#8a6a3a", belly="#c8a870", stripe="#6a4e2a", head="#8a6e40", head_w=6.2)


# --------------------------------------------------------------------------- snakes
@sprite("adder")
def _(s):
    # The common viper: gray or brown with a bold black zigzag down its back and an X on its head.
    snake(s, "#9a948a", belly="#4a4440", bands="#1e1c22", band_period=3.0, band_len=1.6, head="#9a948a",
          head_w=5.6)


@sprite("asp")
def _(s):
    # The asp viper: a gray-brown snake with dark crossbars and a slightly upturned snout.
    snake(s, "#a08a6a", belly="#5a4a3e", bands="#3a2e24", band_period=3.4, band_len=1.4, head="#a08a6a",
          head_w=5.8)


@sprite("long_nosed_viper")
def _(s):
    # Europe's most venomous snake: gray with a dark zigzag and a soft horn on the tip of its nose.
    snake(s, "#a8a49a", belly="#6a6460", bands="#2e2a2a", band_period=3.2, band_len=1.6, head="#a8a49a",
          head_w=6.0)
    s.paint(s.m_px([(4, 19), (4, 18)]), "#a8a49a", within=s.reg > 0)


@sprite("nikolskys_viper")
def _(s):
    # The forest-steppe viper: almost all black.
    snake(s, "#26222a", belly="#1a181e", head="#26222a", head_w=5.6)


@sprite("grass_snake")
def _(s):
    # Olive-green with a yellow-and-black collar behind its head and black bars along its sides.
    snake(s, "#6a7a4a", belly="#e8e0c8", blotch="#2b2630", band_period=4.5, head="#6a7a4a")
    s.paint(s.m_px([(9, 22), (10, 22), (9, 23)]), "#f0d030", within=s.reg > 0)


@sprite("barred_grass_snake")
def _(s):
    # Gray-green with bold black bars down its sides and a faded collar.
    snake(s, "#7a8070", belly="#ece8d8", bands="#2b2630", band_period=4.0, band_len=1.0, head="#7a8070")


@sprite("tessellated_water_snake")
def _(s):
    # The dice snake: gray-olive with a checkerboard of dark squares, often seen fishing.
    snake(s, "#7a7a5a", belly="#e8c860", blotch="#3a3a2a", band_period=3.0, head="#7a7a5a")


@sprite("viperine_snake")
def _(s):
    # A water snake that mimics a viper: brown with a dark zigzag along the back.
    snake(s, "#8a7a52", belly="#d8a860", bands="#3a2e1e", band_period=3.0, band_len=1.4, head="#8a7a52")


@sprite("aesculapian_snake")
def _(s):
    # A long, slim, glossy olive-brown climber with white flecks and a pale yellow belly.
    snake(s, "#6a5a3a", belly="#f0e090", head="#6a5a3a")
    s.paint(s.m_px([(12, 25), (18, 27), (22, 24), (15, 22)]), "#e8e0c8", within=s.reg > 0)


@sprite("european_ratsnake")
def _(s):
    # The leopard snake: pale gray with bright red, black-edged saddles down its back.
    snake(s, "#c8c0b0", belly="#f0ece4", blotch="#c0402a", band_period=3.6, head="#c8c0b0")


@sprite("ladder_snake")
def _(s):
    # Brown with two dark stripes down its back joined like ladder rungs when young.
    snake(s, "#a8885a", belly="#e8dcc0", stripe="#4a3a26", head="#a8885a")


@sprite("manchurian_black_ratsnake")
def _(s):
    # Glossy black with narrow yellow crossbands.
    snake(s, "#1e1c22", belly="#e8d040", bands="#e8d040", band_period=4.5, band_len=0.8, head="#1e1c22")


@sprite("smooth_snake")
def _(s):
    # A small, shy gray-brown snake with a dark line through the eye and pairs of small dark spots.
    snake(s, "#9a8470", belly="#a8603a", blotch="#5a4430", band_period=3.0, head="#9a8470")


@sprite("green_whip_snake")
def _(s):
    # A fast, slim snake, yellow-green crossed with black bars that break into lines toward the tail.
    snake(s, "#c8c050", belly="#f0e8a0", bands="#1e2416", band_period=2.6, band_len=1.4, head="#a8a040")


@sprite("balkan_whip_snake")
def _(s):
    # Brown at the front with dark blotches, fading to plain olive behind.
    snake(s, "#8a7a52", belly="#e8dcb0", blotch="#3a3020", band_period=3.0, head="#7a6a48")


@sprite("caspian_whipsnake")
def _(s):
    # One of Europe's longest snakes: olive-gray, each scale with a pale center, a yellow belly.
    snake(s, "#8a8a6a", belly="#f0dc80", head="#8a8a6a")
    s.paint(s.m_px([(10, 24), (14, 26), (18, 25), (22, 27), (16, 22)]), "#d8d4b0", within=s.reg > 0)


@sprite("large_whip_snake")
def _(s):
    # Glossy black adults with a red-orange throat.
    snake(s, "#1e1c22", belly="#d8603a", head="#1e1c22")


@sprite("algerian_whip_snake")
def _(s):
    # Sandy with a row of dark blotches down the back.
    snake(s, "#c8b088", belly="#f0e8d8", blotch="#5a4a36", band_period=3.0, head="#c8b088")


@sprite("horseshoe_whip_snake")
def _(s):
    # A black net of rings on a yellowish body and a pale horseshoe mark on its head.
    snake(s, "#d8c080", belly="#f0dc90", blotch="#2b2226", band_period=2.6, head="#d8c080")


@sprite("western_montpellier_snake")
def _(s):
    # A big olive snake with a stern "eyebrow" ridge over the eye and a pale throat.
    snake(s, "#6a6a4a", belly="#e8dca0", head="#6a6a4a", head_w=5.8)


@sprite("cat_snake")
def _(s):
    # A night snake with cat-like vertical pupils: gray with dark blotches and a dark collar.
    snake(s, "#a8a090", belly="#e8e4d8", blotch="#3a3430", band_period=3.0, head="#a8a090")


# --------------------------------------------------------------------------- turtles and tortoises
@sprite("hermanns_tortoise")
def _(s):
    # A high-domed tortoise with yellow and black blotched plates and a horny spur at the tail tip.
    turtle(s, "#d8b050", "#c8b080", dome=True, scutes="#2e2618", rim="#2e2618")


@sprite("greek_tortoise")
def _(s):
    # The spur-thighed tortoise: a domed golden-brown shell with dark plate edges.
    turtle(s, "#b8904a", "#b8a078", dome=True, scutes="#4a3a24", rim="#6a5030")


@sprite("marginated_tortoise")
def _(s):
    # The biggest European tortoise: a long, black shell with yellow centers and a flared rear rim.
    turtle(s, "#2e2a24", "#a89a7a", dome=True, scutes="#d8b860", rim="#2a2620")


@sprite("afghan_tortoise")
def _(s):
    # The Russian tortoise: a round, flattened, sandy-olive shell with dark plate centers.
    turtle(s, "#a89a6a", "#b0a080", dome=True, scutes="#4a4228", rim="#6a6040")


@sprite("european_pond_turtle")
def _(s):
    # A dark olive-black pond turtle sprinkled with small yellow dots on the shell and skin.
    turtle(s, "#2e3026", "#3a3a2e", speckle="#e8d040", scutes="#4a4a36")


@sprite("mediterranean_turtle")
def _(s):
    # The Spanish pond turtle: olive-brown shell, with orange-yellow stripes down the neck.
    turtle(s, "#6a6a42", "#6a6a4a", scutes="#8a8a5a")
    s.paint(s.m_line(3, 18, 8, 19) | s.m_line(4, 20, 9, 21), "#e8a040")


@sprite("western_caspian_turtle")
def _(s):
    # The Balkan pond turtle: olive with a net of yellow lines and yellow-striped neck.
    turtle(s, "#5a6040", "#5a5e46", scutes="#c8c070")
    s.paint(s.m_line(3, 18, 8, 19) | s.m_line(4, 20, 9, 21), "#e8d860")


@sprite("red_necked_pond_turtle")
def _(s):
    # A Chinese pond turtle whose neck and face are striped with red.
    turtle(s, "#4a4a3a", "#5a5a4a", scutes="#6a6a50")
    s.paint(s.m_line(3, 18, 8, 19) | s.m_line(4, 20, 9, 21), "#e0402a")


@sprite("chinese_pond_turtle")
def _(s):
    # Reeves' turtle: a brown shell with three ridges, yellow-green squiggles on the head.
    turtle(s, "#5a4a32", "#5a5a4a", scutes="#7a6a48")
    s.paint(s.m_line(3, 18, 8, 19), "#c8d060")


@sprite("chinese_stripe_necked_turtle")
def _(s):
    # A dark shell, the head and neck covered in thin yellow-green stripes.
    turtle(s, "#4a4a3a", "#3e4232", scutes="#5e5e46")
    s.paint(s.m_line(3, 18, 8, 19) | s.m_line(4, 19.5, 9, 20) | s.m_line(4, 21, 9, 22), "#c8e070")


@sprite("false_map_turtle")
def _(s):
    # A sawback: a ridged olive shell with yellow map lines and a yellow crescent behind the eye.
    turtle(s, "#6a6a44", "#4a5038", scutes="#d8c870")
    s.paint(s.m_ellipse(6.5, 18.5, 1.6, 1), "#f0d030")


@sprite("mesoamerican_slider")
def _(s):
    # A green slider with orange eyespots on each plate and yellow-striped skin.
    turtle(s, "#5a6a38", "#4a5a34", speckle="#e8902a", scutes="#7a8a48")
    s.paint(s.m_line(3, 18, 8, 19), "#e8d040")


@sprite("leatherback_sea_turtle")
def _(s):
    # The biggest turtle: a soft, ridged, black leathery shell spotted with white.
    sea_turtle(s, "#26262c", "#3a3a42", scutes="#5a5a64")
    s.paint(s.m_px([(14, 13), (18, 12), (22, 14), (16, 16), (20, 17), (24, 16), (13, 18)]), WHITE,
            within=s.m_ellipse(18, 17, 11, 7.5))


# --------------------------------------------------------------------------- newts and salamanders
def _newt(s, body, belly, *, pat=None, crest=None, legs=None, tail=None, eye_big=True):
    lizard(s, body, belly, head=body, throat=belly, pattern=pat, smooth=True, eye_big=eye_big,
           legs=legs or mix(body, "#000000", 0.1), tail_col=tail or body)
    if crest:
        crest(s)


def _spotted(pts, col, r=1.2):
    def pat(s, m):
        for x, y in pts:
            s.paint(s.m_ellipse(x, y, r, r * 0.9), col, within=m)
    return pat


@sprite("fire_salamander")
def _(s):
    # Glossy black with big bright yellow blotches.
    _newt(s, "#1e1c22", "#2e2c32", pat=_spotted([(9.5, 19.5), (13.5, 18.8), (17.5, 19.5), (21, 19), (11.5, 22.3),
                                                            (16, 22.3), (20, 22)], "#f2c820", 1.7))
    s.paint(s.m_ellipse(6, 17.5, 1.6, 1.2), "#f2c820")


@sprite("alpine_salamander")
def _(s):
    # Jet black all over, glossy and plump, with bumpy glands behind the eyes.
    _newt(s, "#1a181e", "#26242a")
    s.paint(s.m_ellipse(8.5, 17.5, 1.6, 1.1), "#2e2c34")


@sprite("lanzas_alpine_salamander")
def _(s):
    # A jet-black salamander of the western Alps, larger and flatter-headed.
    _newt(s, "#16141a", "#222026", eye_big=True)


@sprite("fazilas_salamander")
def _(s):
    # A Lycian salamander from Turkey: orange-brown with a silvery speckled back and big eyes.
    _newt(s, "#b8602a", "#e8a070", pat=lambda s, m: s.paint(s.m_px(SPOTS), "#e8e0d0", within=m))


@sprite("great_crested_newt")
def _(s):
    # Dark warty brown-black with a jagged crest on the male's back and an orange belly spotted black.
    def crest(s):
        s.path([(9, 17.5), (12, 16), (14, 17.5), (16, 15.5), (18, 17.5), (20, 16)], (0.6, 0.6), "#2a2620",
               shade=False)
    _newt(s, "#2e2a26", "#e8902a", pat=_both(_dots([(10, 23), (14, 23), (18, 23)], BLACK),
                                              _dots([(11, 21), (16, 21)], "#d8d8d8")), crest=crest)


@sprite("italian_crested_newt")
def _(s):
    # Brown with big dark spots, a toothed crest in spring and a yellow-orange belly.
    def crest(s):
        s.path([(9, 17.5), (12, 16), (14, 17.5), (16, 15.5), (18, 17.5)], (0.6, 0.6), "#3a3226", shade=False)
    _newt(s, "#5a4a36", "#f0a830", pat=_spotted([(11, 20), (16, 20), (20, 20)], "#2b2226"), crest=crest)


@sprite("macedonian_crested_newt")
def _(s):
    # Dark brown with black spots, a pale-flecked flank and an orange belly.
    _newt(s, "#4a3e30", "#e88a2a", pat=_both(_spotted([(11, 20), (16, 20)], "#1e1a16"),
                                              _dots([(13, 22), (18, 22)], "#e8e0d0")))


@sprite("marbled_newt")
def _(s):
    # Vivid green marbled with black, with a bright orange stripe down the back.
    def pat(s, m):
        s.paint(s.m_px(NET), "#1a1e14", within=m)
        s.paint(s.m_line(8, 18.5, 22, 18.5), "#f07a2a", within=m)
    _newt(s, "#5aa840", "#3a3434", pat=pat)


@sprite("smooth_newt")
def _(s):
    # Olive-brown with dark spots, an orange belly and a wavy crest on the male.
    def crest(s):
        s.path([(9, 17.5), (13, 16.5), (17, 17), (21, 16.5)], (0.5, 0.5), "#6a5a40", shade=False)
    _newt(s, "#7a6a4a", "#f0a040", pat=_spotted([(11, 20), (15, 20), (19, 20), (13, 22), (17, 22)], "#2b2620",
                                                  0.9), crest=crest)


@sprite("palmate_newt")
def _(s):
    # A small olive newt with a dark stripe through the eye and webbed black hind feet in spring.
    _newt(s, "#8a8a52", "#f0d870", pat=_dots(SPOTS, "#3a3a24"))
    s.paint(s.m_line(3, 17, 9, 17.5), "#3a3a24")


@sprite("alpine_newt")
def _(s):
    # Slate-blue above, a plain bright orange belly, and black-and-white spotted flanks.
    def pat(s, m):
        s.paint(s.m_line(8, 22, 22, 22), WHITE, within=m)
        s.paint(s.m_px([(10, 22), (13, 22), (16, 22), (19, 22)]), BLACK, within=m)
    _newt(s, "#4a5a7a", "#f07a20", pat=pat)


@sprite("greek_newt")
def _(s):
    # A little olive newt with a fine dark stripe through the eye and an orange belly.
    _newt(s, "#7a7a4a", "#f09a3a", pat=_dots(SPOTS, "#3a3a24"))
    s.paint(s.m_line(3, 17, 9, 17.5), "#3a3a24")


@sprite("boscas_newt")
def _(s):
    # The Iberian newt: brown with darker spots and an orange belly.
    _newt(s, "#7a6040", "#f08a2a", pat=_dots(SPOTS, "#3a2a1a"))


# --------------------------------------------------------------------------- frogs and toads
@sprite("european_common_frog")
def _(s):
    # Brown-olive with a dark mask behind the eye and dark bars on its legs.
    frog(s, "#9a7a50", "#f0e4c8", tympanum="#5a3a24", mask="#4a2e1e", spots=4, ridges="#c8a878",
         thigh="#8a6a44")


@sprite("agile_frog")
def _(s):
    # Slim pinkish-brown with very long legs, a dark mask and a plain pale belly.
    frog(s, "#b88a68", "#f6efe6", tympanum="#6a4030", mask="#5a3424", spots=1, ridges="#d8b090")


@sprite("moor_frog")
def _(s):
    # Brown with a pale stripe down the back; males turn sky-blue in spring.
    frog(s, "#8a7458", "#f2ecdc", mask="#4a3424", dorsal="#e8d8b0", spots=3, ridges="#b8a07a")


@sprite("italian_stream_frog")
def _(s):
    # A brown mountain-stream frog with a dark mask and a dark throat.
    frog(s, "#8a6a4a", "#ece0d0", mask="#3e2a1e", spots=3, tympanum="#5a3e2a")


@sprite("iberian_frog")
def _(s):
    # A small, long-legged brown frog with a pale lip stripe.
    frog(s, "#9a7a5a", "#f0e8dc", mask="#5a3e2a", lip="#f0e4cc", spots=2)


@sprite("galician_common_frog")
def _(s):
    # A western cousin of the common frog, reddish-brown with dark spots.
    frog(s, "#a0704a", "#f0e4d0", mask="#4e2e1e", spots=5, ridges="#c89a70")


@sprite("greek_frog")
def _(s):
    # A brown stream frog of the Balkans with a dark mask.
    frog(s, "#8a7a5a", "#f0eadc", mask="#4a3a28", spots=3, tympanum="#5a4630")


@sprite("taurus_frog")
def _(s):
    # The long-legged wood frog of Turkey: brown with a dark mask and barred legs.
    frog(s, "#8a6a48", "#ece4d4", mask="#4a2e1e", spots=4, thigh="#7a5a3a")


@sprite("marsh_frog")
def _(s):
    # Europe's biggest frog: olive-green with dark spots, a green stripe down the back and gray vocal sacs.
    frog(s, "#7a8a4a", "#e8e4d0", dorsal="#9ac050", spots=7, spot_col="#3a3a24", ridges="#a8b070")


@sprite("pool_frog")
def _(s):
    # Bright green with a yellow stripe down the back and dark spots.
    frog(s, "#6ab040", "#f2f0d8", dorsal="#f0e050", spots=5, spot_col="#2a3a1e", ridges="#a8d070")


@sprite("edible_frog")
def _(s):
    # Green with black spots and a pale stripe down the back; a hybrid of pool and marsh frogs.
    frog(s, "#78a840", "#f0eee0", dorsal="#c8e070", spots=6, spot_col="#1e2a16", ridges="#b0d070")


@sprite("iberian_green_frog")
def _(s):
    # Perez's frog: green to brown with dark spots and pale ridges.
    frog(s, "#7a9a48", "#ecead8", spots=6, spot_col="#2a3a1e", ridges="#b8c880")


@sprite("european_tree_frog")
def _(s):
    # Bright leaf-green and smooth, with a dark stripe along each side edged in white, and sticky toe pads.
    frog(s, "#5ac040", "#f4f4e4", build="tree", pads=True, side="#3a3a3a", mask="#3a3a3a")


@sprite("mediterranean_tree_frog")
def _(s):
    # The stripeless tree frog: plain bright green with a short dark stripe behind the eye.
    frog(s, "#60c848", "#f4f4e4", build="tree", pads=True, mask="#3a4a2e")


@sprite("italian_tree_frog")
def _(s):
    # Leaf-green with a dark side stripe and sticky toes.
    frog(s, "#58b840", "#f2f2e0", build="tree", pads=True, side="#4a4a3a", mask="#4a4a3a")


@sprite("eastern_tree_frog")
def _(s):
    # Bright green with a dark side stripe, a tree frog of eastern Europe.
    frog(s, "#5ab83e", "#f2f2e2", build="tree", pads=True, side="#3e3e34", mask="#3e3e34")


@sprite("lemon_yellow_tree_frog")
def _(s):
    # A Middle Eastern tree frog, pale yellow-green with a dark side stripe.
    frog(s, "#b8d050", "#f6f4e4", build="tree", pads=True, side="#5a5a3e", mask="#5a5a3e")


@sprite("european_toad")
def _(s):
    # A big warty brown toad with coppery-red eyes and large glands behind them.
    frog(s, "#8a6a48", "#e8dcc4", build="toad", spots=6, warts="#a8865a", parotoid="#9a7650", iris="#d87a3a")


@sprite("spiny_toad")
def _(s):
    # A huge, very warty brown toad of the southwest, with spiky warts and orange eyes.
    frog(s, "#9a7048", "#ece0c8", build="toad", spots=8, warts="#5a3e26", parotoid="#a87a50", iris="#e08a3a")


@sprite("natterjack_toad")
def _(s):
    # An olive toad with a thin yellow line down its back; it runs instead of hopping.
    frog(s, "#7a8058", "#ecead8", build="toad", spots=7, dorsal="#f0e050", warts="#c87a4a", parotoid="#8a8a5a")


@sprite("green_toad")
def _(s):
    # Pale cream marbled with bright green blotches, red-tipped warts.
    frog(s, "#d8d4bc", "#f4f2e6", build="toad", spots=7, spot_big=True, spot_col="#5a9a4a", warts="#d8603a",
         parotoid="#c8c4a8")


@sprite("cyprian_green_toad")
def _(s):
    # Cyprus' green toad: pale gray with olive-green blotches.
    frog(s, "#c8c8b0", "#f2f0e4", build="toad", spots=6, spot_big=True, spot_col="#6a8a4a", warts="#c87a5a",
         parotoid="#b8b8a0")


@sprite("common_spadefoot")
def _(s):
    # A plump, smooth toad, pale with dark brown blotches, cat-like vertical pupils and a spade on each hind foot.
    frog(s, "#c8b08a", "#f0e8dc", build="toad", spots=6, spot_big=True, spot_col="#6a4a30", iris="#e8a040",
         cat=True)


@sprite("european_fire_bellied_toad")
def _(s):
    # A small dark warty toad with a fiery red-orange belly spotted in black.
    frog(s, "#4a4a3a", "#e8502a", build="toad", spots=4, spot_col="#2a2a20", warts="#6a6a50", iris="#e8c050")


@sprite("yellow_bellied_toad")
def _(s):
    # Muddy olive above, bright yellow belly blotched in blue-black, heart-shaped pupils.
    frog(s, "#6a6440", "#f0d020", build="toad", spots=4, spot_col="#3a3a24", warts="#8a8458", iris="#e8c050")


@sprite("iberian_painted_frog")
def _(s):
    # Brown with darker spots edged in pale cream; a round-snouted, smooth frog.
    frog(s, "#9a7a52", "#ece8dc", spots=6, spot_big=True, spot_col="#5a3e24", ridges=None)


@sprite("mediterranean_painted_frog")
def _(s):
    # Painted with big dark blotches edged in pale lines, or with three pale stripes.
    frog(s, "#a8885a", "#f0eadc", spots=6, spot_big=True, spot_col="#5a3a22", dorsal="#e8d8b0")
