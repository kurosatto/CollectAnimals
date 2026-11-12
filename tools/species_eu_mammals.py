"""Sprites for the European (and Turkish) mammals that the US lists don't have.
Imported by make_sprites.py, which registers the drawings via @sprite."""
from __future__ import annotations

import math

from archetypes import BLACK, EYE, PINK, WHITE, _fluke, back_stripes, critter, dolphin, face_stripes, flecks, \
    pinniped, sprite, teeth
from mammal import quad
from pixel import mix


def _dk(c, k=0.28):
    return mix(c, "#1a1420", k)


# --------------------------------------------------------------------------- hoofed
def _ibex_horns(col, ridge, *, size=1.0, spread=0.0):
    """Long horns sweeping back over the neck in a curve, ridged across the front."""
    def horns(s, b):
        hx, hy = b["head"][:2]
        for dx, c in ((1.4, _dk(col, 0.25)), (0, col)):
            x, y = hx + 1 + dx, hy - 2.5
            pts = [(x - 0.5, y), (x + 1.2 * size, y - 4 * size - spread), (x + 4.2 * size, y - 6.6 * size - spread),
                   (x + 7.4 * size, y - 6 * size - spread * 0.6), (x + 9 * size, y - 4 * size - spread * 0.3)]
            m = s.path(pts, (1.9, 0.7), c, edge=True)
            if ridge and dx == 0:
                for k in range(1, 4):
                    p0 = pts[k]
                    s.paint(s.m_px([(round(p0[0] - 0.6), round(p0[1] - 0.8))]), ridge, within=m)
    return horns


@sprite("alpine_ibex")
def _(s):
    # Stocky brown-gray mountain goat with huge ridged horns swept back over its neck and a short beard.
    def beard(s, b):
        hx, hy = b["head"][:2]
        s.path([(hx - 2, hy + 2.5), (hx - 2.2, hy + 4.8)], (1.0, 0.5), "#5a4a3a")
        bx, by, brx, bry = b["body"]
        s.paint(s.m_ellipse(bx, by + bry * 0.7, brx, 1.4), "#6a5848", within=s.m_ellipse(bx, by, brx, bry))
    quad(s, "#8a7a64", "#d8ccb4", build="sheep", ears="small", ear_in="#c8b49a", tail="short",
         tail_col="#4a3e32", muzzle="#a89880", nose="#2b2226", feet="#2b2630", legs="#6a5c4c",
         markings=beard, front=_ibex_horns("#a08a6a", "#6a5a44", size=1.1))


@sprite("iberian_ibex")
def _(s):
    # Lighter tan with black markings on the legs and flanks, horns curving up and outward like a lyre.
    def marks(s, b):
        bx, by, brx, bry = b["body"]
        s.paint(s.m_ellipse(bx - 2, by + bry * 0.6, brx * 0.8, 1.3), "#2e2622", within=s.m_ellipse(bx, by, brx, bry))
        hx, hy = b["head"][:2]
        s.path([(hx - 2, hy + 2.5), (hx - 2.2, hy + 4.2)], (0.9, 0.5), "#4a3e32")
    quad(s, "#a88a64", "#e8dcc4", build="sheep", ears="small", ear_in="#d8c0a0", tail="short",
         tail_col="#2e2622", muzzle="#c0a884", nose="#2b2226", feet="#2b2630", legs="#4a3e34",
         markings=marks, front=_ibex_horns("#8a7458", "#5a4a38", size=0.95, spread=1.5))


@sprite("wild_goat")
def _(s):
    # The bezoar: silver-tan with a dark stripe down the spine and across the shoulders,
    # a long black beard and tall scimitar horns.
    def marks(s, b):
        bx, by, brx, bry = b["body"]
        body = s.m_ellipse(bx, by, brx, bry)
        s.paint(s.m_ellipse(bx, by - bry + 0.6, brx, 0.9) | s.m_path([(bx - brx * 0.6, by - bry),
                                                                    (bx - brx * 0.7, by + bry)], 0.9),
                "#3a2e26", within=body)
        hx, hy = b["head"][:2]
        s.path([(hx - 2, hy + 2.5), (hx - 2.5, hy + 5.5)], (1.1, 0.5), "#2b2226")
    quad(s, "#b8a080", "#ece4d4", build="sheep", ears="small", ear_in="#d8c4a4", tail="short",
         tail_col="#2b2226", head="#a08a6c", muzzle="#c8b494", nose="#2b2226", feet="#2b2630", legs="#7a6650",
         markings=marks, front=_ibex_horns("#8a7a60", "#5a4c3a", size=1.15, spread=-0.5))


@sprite("northern_chamois")
def _(s):
    # A nimble goat-antelope: brown coat, a white face with black stripes through the eyes,
    # and short black horns hooked back at the tips.
    def face(s, b):
        hx, hy, hrx, hry = b["head"]
        hm = s.m_ellipse(hx, hy, hrx, hry)
        s.paint(hm, "#f0e8dc", within=hm)
        s.paint(s.m_path([(hx + 2, hy - 2), (hx - 2.5, hy + 1.8)], 0.7), "#2b2226", within=hm)
        bx, by, brx, bry = b["body"]
        s.paint(s.m_ellipse(bx, by - bry + 0.5, brx, 1), "#3a2a20", within=s.m_ellipse(bx, by, brx, bry))
    def horns(s, b):
        hx, hy = b["head"][:2]
        for dx, c in ((1.3, "#3a3436"), (0, "#1e1a1e")):
            s.path([(hx + dx, hy - 2.5), (hx + dx + 0.3, hy - 6), (hx + dx + 1.8, hy - 6.5), (hx + dx + 2.2, hy - 5)],
                   (0.7, 0.4), c, shade=False)
    quad(s, "#7a5a3c", "#c8a882", build="deer", ears="point", ear_in="#e0c8a8", tail="short",
         tail_col="#2b2226", muzzle="#f0e8dc", nose="#2b2226", feet="#2b2630", legs="#4a3628",
         markings=face, front=horns)


def _antler(points, tines, col, w=0.7):
    def antlers(s, b):
        hx, hy = b["head"][:2]
        for dx, c in ((1.5, _dk(col, 0.25)), (0, col)):
            x, y = hx + 1 + dx, hy - 2.5
            s.path([(x + px, y + py) for px, py in points], w, c, shade=False)
            for (ax, ay), (bx_, by_) in tines:
                s.path([(x + ax, y + ay), (x + bx_, y + by_)], w * 0.75, c, shade=False)
    return antlers


@sprite("red_deer")
def _(s):
    # A big red-brown stag with a shaggy neck mane, a pale rump and tall branching antlers.
    def mane(s, b):
        (nx0, ny0), (nx1, ny1), nr = b["neck"]
        s.paint(s.m_path([(nx0, ny0), (nx1, ny1)], nr + 0.3), "#6a4430")
        bx, by, brx, bry = b["body"]
        s.paint(s.m_ellipse(bx + brx * 0.85, by - 1, 1.8, 2.4), "#e8d4b0", within=s.m_ellipse(bx, by, brx, bry))
    quad(s, "#9a5c38", "#d8c0a0", build="deer", ears="side", ear_in="#e0b494", tail="short", tail_col="#e8d4b0",
         nose="#2b2226", feet="#3a2a22", legs="#7a4a30", belly=False, markings=mane,
         behind=_antler([(0, 0), (2.5, -3.5), (4, -7), (5, -10)],
                        [((0.6, -1), (-2, -1.6)), ((3.4, -5.5), (1.4, -6.8)), ((4.6, -8.6), (6.8, -10))],
                        "#d8c49c", w=0.6))


@sprite("european_fallow_deer")
def _(s):
    # Chestnut with rows of white spots, a black-edged white rump and broad, flat (palmate) antlers.
    def spots(s, b):
        bx, by, brx, bry = b["body"]
        pts = [(15, 15), (18, 14), (21, 14.5), (24, 15), (16, 17.5), (19, 17), (22, 17.5), (25, 18)]
        body = s.m_ellipse(bx, by, brx, bry)
        s.paint(s.m_px([(round(x + bx - 19), round(y + by - 17.4)) for x, y in pts]), "#f8f0e0", within=body)
        s.paint(s.m_line(bx - brx + 2, by + bry * 0.55, bx + brx - 2, by + bry * 0.55), "#f8f0e0", within=body)
    def antlers(s, b):
        hx, hy = b["head"][:2]
        c = "#d8c49a"
        for dx, col in ((1.5, _dk(c, 0.25)), (0, c)):
            x, y = hx + 1 + dx, hy - 2.5
            s.path([(x, y), (x + 1.5, y - 3.5)], 0.7, col, shade=False)
            s.path([(x + 0.5, y - 1.2), (x - 1.8, y - 2.5)], 0.5, col, shade=False)
            s.ellipse(x + 3.6, y - 5.5, 3.2, 1.7, col, rot=-40, shade=False)
            s.px([(round(x + 2), round(y - 8)), (round(x + 4), round(y - 8.5)), (round(x + 6), round(y - 7))], col)
    quad(s, "#a86a3c", "#f0e4d0", build="deer", ears="side", ear_in="#e8c0a0", tail="short", tail_col=BLACK,
         nose="#2b2226", feet="#3a2a22", behind=antlers, markings=spots)


@sprite("western_roe_deer")
def _(s):
    # A small, dainty red deer with a black nose and white chin, a white rump patch,
    # no tail to speak of, and short rough three-pointed antlers.
    def face(s, b):
        hx, hy, hrx, hry = b["head"]
        sx, sy = b["snout"][1]
        s.paint(s.m_ellipse(sx + 0.5, sy + 0.8, 1.4, 0.9), WHITE)
        s.paint(s.m_ellipse(sx, sy - 0.2, 1.0, 0.9), "#1e1a1e")
        bx, by, brx, bry = b["body"]
        s.paint(s.m_ellipse(bx + brx * 0.9, by - 0.5, 1.6, 2.4), "#f6efe4", within=s.m_ellipse(bx, by, brx, bry))
    quad(s, "#b0603a", "#e8d4bc", build="deer", ears="side", ear_in="#e8c0a8", tail="none",
         nose="#1e1a1e", feet="#3a2a22", markings=face,
         behind=_antler([(0, 0), (0.8, -3), (1.2, -5.5)], [((0.8, -2.5), (-1.2, -3.5)), ((1.1, -4.4), (2.6, -5.4))],
                        "#c8b08a", w=0.8))


@sprite("reevess_muntjac")
def _(s):
    # A small, hunched barking deer, ginger-brown with a dark V on its face and tiny spike antlers.
    def face(s, b):
        hx, hy, hrx, hry = b["head"]
        hm = s.m_ellipse(hx, hy, hrx, hry)
        s.paint(s.m_path([(hx + 1.5, hy - 2.5), (hx - 1.5, hy + 0.5)], 0.6), "#3a2418", within=hm)
    quad(s, "#a8683c", "#e0c8a8", build="deer", ears="side", ear_in="#e0b494", tail="short", tail_col="#a8683c",
         nose="#2b2226", feet="#3a2a22", markings=face,
         behind=_antler([(0, 0), (0.5, -2.2), (1.6, -3.4)], [], "#b89a72", w=0.6))


@sprite("wisent")
def _(s):
    # The European bison: taller and leaner than the American, a shaggy dark-brown hump and
    # short hooked horns, with a beard under the chin.
    shag = "#5a3c26"
    def hump(s, b):
        bx, by, brx, bry = b["body"]
        s.ellipse(bx - 4.5, by - bry + 0.8, 5.5, 4, shag)
    def coat(s, b):
        bx, by, brx, bry = b["body"]
        s.paint(s.m_ellipse(bx - 5, by - 1, 5.5, 6.5), shag, within=s.m_ellipse(bx, by, brx, bry)
                | s.m_ellipse(bx - 4.5, by - bry + 0.8, 5.5, 4))
    def horns(s, b):
        hx, hy, hrx, hry = b["head"]
        s.path([(hx + 1.5, hy - 3), (hx + 0.5, hy - 6), (hx - 1.2, hy - 6.4)], (0.8, 0.5), "#c8bca8", shade=False)
        s.path([(hx - 1.5, hy + 3), (hx - 1.2, hy + 5.5)], (1.2, 0.7), "#3a2618")
    quad(s, "#6a4a30", "#7a5a3c", build="bear", ears="small", ear_in="#4a3020", tail="short", tail_col="#3a2618",
         tail_tip="#2a1a10", head="#5e4028", muzzle="#4a3220", nose="#1a1410", feet="#2a2020", legs="#5a3c28",
         belly=False, behind=hump, markings=coat, front=horns)


# --------------------------------------------------------------------------- dogs, cats, mustelids
@sprite("arctic_fox")
def _(s):
    # Thick snow-white winter coat, short round ears, a short muzzle and a huge bushy tail.
    quad(s, "#f2f0ec", WHITE, build="dog", ears="round", ear_in="#d8d0c8", tail="bushy", tail_col="#ecebe6",
         nose="#2b2226", feet="#e4e0d8", eye_col="#4a3a20",
         markings=lambda s, b: flecks(s, s.m_ellipse(*b["body"]), "#dcd8d0", every=7))


@sprite("golden_jackal")
def _(s):
    # A slim golden-gray wild dog with a darker grizzled saddle and a black-tipped tail.
    def m(s, b):
        body = s.m_ellipse(*b["body"])
        s.paint(s.m_ellipse(b["body"][0] + 1, b["body"][1] - b["body"][3] * 0.55, 6.5, 1.8), "#6a5a48", within=body)
        flecks(s, body, "#e8d4b0", every=7)
    quad(s, "#c09a64", "#f2e8d4", build="dog", ears="big", ear_in="#e8c8a0", tail="bushy", tail_col="#a88858",
         tail_tip=BLACK, nose="#2b2226", eye_col="#7a5a20", markings=m)


@sprite("mainland_raccoon_dog")
def _(s):
    # Fox-like but low and fluffy, with a raccoon's dark mask, short rounded ears and dark legs.
    def m(s, b):
        hx, hy, hrx, hry = b["head"]
        s.paint(s.m_ellipse(hx - 1.5, hy + 0.3, 2.6, 1.3), "#2e2622", within=s.m_ellipse(hx, hy, hrx, hry))
        bx, by, brx, bry = b["body"]
        s.paint(s.m_ellipse(bx - brx * 0.4, by - bry * 0.4, 2.8, 2.8), "#3a302a", within=s.m_ellipse(bx, by, brx, bry))
        flecks(s, s.m_ellipse(bx, by, brx, bry), "#d8c4a4", every=6)
    quad(s, "#9a8468", "#c8b494", build="low", ears="round", ear_in="#d8c4a4", tail="bushy", tail_col="#8a7458",
         tail_tip="#3a302a", muzzle="#e8dcc8", legs="#3a302a", feet="#2a2220", nose="#1e1a1e", markings=m)


@sprite("eurasian_lynx")
def _(s):
    # A long-legged spotted cat with black ear tufts, a ruff of side whiskers and a short black-tipped tail.
    def spots(s, b):
        bx, by, brx, bry = b["body"]
        s.paint(s.m_px([(round(bx + dx), round(by + dy)) for dx, dy in
                        ((-5, -1), (-2, -2), (1, -1), (4, -2), (6, 0), (-3, 1), (0, 1), (3, 1), (-1, 3), (5, 2))]),
                "#7a5232", within=s.m_ellipse(bx, by, brx, bry))
        hx, hy, hrx, hry = b["head"]
        s.paint(s.m_ellipse(hx + 1.5, hy + 1.8, 2, 1.6), "#e8dcc4")
    quad(s, "#b89068", "#f0e6d4", build="cat", ears="tuft", ear_in="#e8d0b0", tail="short", tail_tip=BLACK,
         nose="#c47a6a", feet="#a8845e", eye_col="#8a7020", markings=spots)


@sprite("iberian_lynx")
def _(s):
    # Smaller than the Eurasian lynx and boldly spotted all over, with a big pointed beard and long ear tufts.
    def spots(s, b):
        bx, by, brx, bry = b["body"]
        s.paint(s.m_px([(round(bx + dx), round(by + dy)) for dx, dy in
                        ((-6, -2), (-3, -2), (0, -2), (3, -2), (6, -1), (-5, 0), (-2, 0), (1, 0), (4, 0),
                         (-4, 2), (-1, 2), (2, 2), (5, 2))]), "#2e2420", within=s.m_ellipse(bx, by, brx, bry))
        hx, hy, hrx, hry = b["head"]
        s.paint(s.m_poly([(hx + 0.5, hy + 1), (hx + 3, hy + 1.5), (hx + 1.5, hy + 4.5)]), "#e8dcc8")
        s.paint(s.m_px([(round(hx + 1.5), round(hy + 3))]), "#2e2420")
    quad(s, "#c09a62", "#f2e8d4", build="cat", ears="tuft", ear_in="#e8d0b0", tail="short", tail_tip=BLACK,
         nose="#c47a6a", feet="#b08a58", eye_col="#8a7020", markings=spots)


@sprite("european_wildcat")
def _(s):
    # Like a big, stocky gray tabby with faint stripes and a thick, blunt tail ringed in black.
    def stripes(s, b):
        bx, by, brx, bry = b["body"]
        body = s.m_ellipse(bx, by, brx, bry)
        for k in range(-3, 4):
            x = bx + k * 2.2
            s.paint(s.m_line(x, by - bry, x - 0.6, by), "#5a5048", within=body)
        s.paint(s.m_ellipse(bx, by - bry + 0.5, brx, 0.8), "#3a322c", within=body)
        hx, hy, hrx, hry = b["head"]
        s.paint(s.m_line(hx - 0.5, hy - hry + 0.5, hx - 0.5, hy - 1) | s.m_line(hx + 1, hy - hry + 0.5, hx + 1, hy - 1),
                "#5a5048", within=s.m_ellipse(hx, hy, hrx, hry))
    quad(s, "#9a8c78", "#e8dcc8", build="cat", ears="point", ear_in="#d8b8a0", tail="ringed", tail_col="#9a8c78",
         tail_tip="#2b2226", nose="#d0807a", eye_col="#8aa030", markings=stripes)


@sprite("eurasian_pine_marten")
def _(s):
    # A sleek chocolate-brown climber with a creamy-yellow bib, rounded pale-rimmed ears and a bushy tail.
    def bib(s, b):
        hx, hy, hrx, hry = b["head"]
        s.paint(s.m_ellipse(hx + 1.5, hy + 3, 2.6, 2.4), "#f0c870")
    quad(s, "#6a4428", "#7a5232", build="low", ears="round", ear_in="#e8d0a0", tail="bushy", tail_col="#5a3820",
         muzzle="#7a5232", nose="#1a1210", belly=False, markings=bib)


@sprite("stone_marten")
def _(s):
    # Grayer brown than the pine marten, with a white bib that forks down onto the front legs.
    def bib(s, b):
        hx, hy, hrx, hry = b["head"]
        s.paint(s.m_ellipse(hx + 1.5, hy + 3, 2.4, 2.2) | s.m_path([(hx + 2, hy + 4), (hx + 3.5, hy + 7)], 0.9),
                "#f6f2ea")
    quad(s, "#7a6250", "#8a7260", build="low", ears="round", ear_in="#e8dcc8", tail="bushy", tail_col="#5a4636",
         muzzle="#8a7260", nose="#d89a9a", belly=False, markings=bib)


@sprite("eurasian_stoat")
def _(s):
    # A slim, long-bodied hunter: ginger-brown above, cream below, with a black tip to its tail.
    quad(s, "#a8683a", "#f6eedc", build="low", ears="small", ear_in="#e8c8a8", tail="long", tail_col="#a8683a",
         tail_tip=BLACK, muzzle="#f6eedc", nose="#2b2226", feet="#f0e4cc", eye_col=EYE)


@sprite("least_weasel")
def _(s):
    # The smallest carnivore: tiny and low, brown above and white below, with a short brown tail.
    critter(s, "#9a643a", WHITE, build="otter", ears="small", ear_in="#e8c8a8", tail="short", tail_col="#9a643a",
            muzzle=WHITE, nose="#2b2226", feet="#e8dcc8")


@sprite("european_polecat")
def _(s):
    # Dark brown-black with buff underfur showing on the flanks, and a white bandit mask on its face.
    def mask(s, b):
        hx, hy, hrx, hry = b["head"]
        hm = s.m_ellipse(hx, hy, hrx, hry)
        s.paint(s.m_ellipse(hx + 0.5, hy - 1.8, 2.4, 0.8) | s.m_ellipse(hx - 2, hy + 1.6, 2.6, 1), "#f2ece0",
                within=hm | s.m_path(list(b["snout"][:2]), 1.8))
        bx, by, brx, bry = b["body"]
        s.paint(s.m_ellipse(bx, by, brx * 0.8, bry * 0.6), "#a8885e", within=s.m_ellipse(bx, by, brx, bry))
    quad(s, "#3a2a20", "#4a3828", build="low", ears="round", ear_in="#f0e8d8", tail="bushy", tail_col="#2a1e16",
         muzzle="#f2ece0", nose="#e0a0a0", belly=False, legs="#2a1e16", markings=mask)


@sprite("eurasian_otter")
def _(s):
    # A brown river otter with a pale cream throat, a flat head and a thick tapering tail.
    critter(s, "#6e4c34", "#e0ceb0", build="otter", ear_in="#4a3428", tail="otter", tail_col="#5e4230",
            muzzle="#e0ceb0", nose="#2b2226")


@sprite("european_badger")
def _(s):
    # Gray and stocky, with a black-and-white striped head and black legs.
    def face(s, g):
        h = g["head_m"]
        if g["view"] == "front":
            s.paint(s.m_ellipse(g["hx"] - 1.6, g["hy"], 0.9, g["hry"] + 1)
                    | s.m_ellipse(g["hx"] + 1.6, g["hy"], 0.9, g["hry"] + 1), "#1e1a1e", within=h)
            return
        d = 1 if g["view"] == "back" else -1
        s.paint(h, WHITE, within=h)
        s.paint(s.m_path([(g["hx"] + d * 3, g["hy"] - 0.6), (g["hx"] - d * 3.5, g["hy"] + 0.4)], 0.9), "#1e1a1e",
                within=h)
    critter(s, "#8a8a8c", "#3a363a", build="badger", ears="small", ear_in=WHITE, ear_tip=WHITE, tail="short",
            tail_col="#b0aeac", feet="#1e1a1e", belly=False, face=face,
            markings=lambda s, g: flecks(s, g["body"], "#b8b6b4", every=4))


@sprite("southwest_asian_badger")
def _(s):
    # The Caucasian badger: paler and browner-gray than the European one, the same striped face.
    def face(s, g):
        h = g["head_m"]
        if g["view"] == "front":
            s.paint(s.m_ellipse(g["hx"] - 1.6, g["hy"], 0.9, g["hry"] + 1)
                    | s.m_ellipse(g["hx"] + 1.6, g["hy"], 0.9, g["hry"] + 1), "#2e2622", within=h)
            return
        d = 1 if g["view"] == "back" else -1
        s.paint(h, "#f4efe4", within=h)
        s.paint(s.m_path([(g["hx"] + d * 3, g["hy"] - 0.6), (g["hx"] - d * 3.5, g["hy"] + 0.4)], 0.85), "#2e2622",
                within=h)
    critter(s, "#a89a88", "#4a4038", build="badger", ears="small", ear_in=WHITE, ear_tip=WHITE, tail="short",
            tail_col="#c8bcaa", feet="#2e2622", belly=False, face=face,
            markings=lambda s, g: flecks(s, g["body"], "#cfc4b4", every=4))


@sprite("egyptian_mongoose")
def _(s):
    # The ichneumon: long, low and grizzled gray, with dark legs and a black tuft at the end of its tail.
    def grizzle(s, b):
        flecks(s, s.m_ellipse(*b["body"]), "#c8c0b0", every=4)
    quad(s, "#7a7268", "#8a8278", build="low", ears="small", ear_in="#5a5048", tail="long", tail_col="#7a7268",
         tail_tip="#1e1a1e", legs="#3a3430", feet="#2b2226", nose="#2b2226", belly=False, markings=grizzle)


@sprite("northern_small_spotted_genet")
def _(s):
    # A slender cat-like hunter, pale gray with rows of dark spots, a dark crest and a long black-ringed tail.
    def spots(s, b):
        bx, by, brx, bry = b["body"]
        body = s.m_ellipse(bx, by, brx, bry)
        s.paint(s.m_ellipse(bx, by - bry + 0.6, brx, 0.7), "#2b2226", within=body)
        for row, dy in enumerate((-1.5, 0.5, 2.5)):
            s.paint(s.m_px([(round(bx - 6 + k * 2.4 + row), round(by + dy)) for k in range(5)]), "#2b2226",
                    within=body)
        hx, hy, hrx, hry = b["head"]
        s.paint(s.m_px([(round(hx), round(hy - 1)), (round(hx - 1), round(hy + 1))]), WHITE)
    quad(s, "#c8bca4", "#ece4d4", build="low", ears="big", ear_in="#e0c8b8", tail="ringed", tail_col="#c8bca4",
         tail_tip="#2b2226", nose="#2b2226", eye_col="#5a4a20", markings=spots)


# --------------------------------------------------------------------------- spiny ones
def _hedgehog(s, spine, tip, face, *, belly=None, ears=1.3, ear_col=None, legs="#4a3a32", mask=None):
    """A hedgehog from the side, walking left: a domed coat of pale-tipped spines,
    a pointed face and small legs. It sleeps rolled into a ball."""
    s.can("walk", "eat", "run")
    w = s.wave() if s.act in ("walk", "run") else 0
    rolled = s.act == "sleep"
    if rolled:
        m = s.ellipse(16, 22, 9.5, 8.5, spine, edge=True)
        for k in range(18):
            a = -math.pi * 0.95 + k * (2 * math.pi / 18)
            x0, y0 = 16 + 7 * math.cos(a), 22 + 6 * math.sin(a)
            s.line(round(x0), round(y0), round(16 + 10 * math.cos(a)), round(22 + 9 * math.sin(a)), tip)
        s.paint(s.m_ellipse(12, 26, 2.2, 1.6), face, within=m)
        s.px([(10, 27)], "#2b2226")
        return
    dip = 1.5 * s.cyc(0, 1, 1, 0) if s.act == "eat" else 0
    for x, sw in ((12, w), (22, -w)):  # far legs
        s.ellipse(x + sw * 1.2, 29, 1.6, 1.2, _dk(legs, 0.3))
    s.ellipse(17, 25, 9, 4.5, belly or face)
    # a fringe of spines standing out round the edge of the coat, pale at the very tips
    for k in range(13):
        a = math.pi * (1.02 + k * 0.85 / 12)
        x0, y0 = 18 + 9.2 * math.cos(a), 22 + 6.4 * math.sin(a)
        x1, y1 = 18 + 11.3 * math.cos(a - 0.12), 22 + 8.3 * math.sin(a - 0.12)
        s.line(round(x0), round(y0), round(x1), round(y1), _dk(spine, 0.2))
        s.px([(round(x1), round(y1))], tip)
    m = s.ellipse(18, 22, 10, 6.8, spine, edge=True)
    s.paint(s.m_px([(12, 19), (15, 17), (18, 16), (21, 17), (24, 19), (14, 21), (17, 20), (20, 20), (23, 22),
                    (16, 23), (19, 24), (26, 22), (11, 22)]), tip, within=m)
    s.paint(s.m_px([(13, 18), (16, 19), (19, 18), (22, 20), (25, 21), (15, 22), (18, 22), (21, 23)]),
            _dk(spine, 0.25), within=m)
    for x, sw in ((10, -w), (20, w)):
        s.ellipse(x + sw * 1.2, 29, 1.7, 1.2, legs)
    # face: a cone-shaped snout poking out under the spines
    hx, hy = 8.5, 24 + dip
    s.ellipse(hx + 1, hy, 3.6, 3, face, edge=True)
    s.path([(hx, hy + 0.5), (hx - 5, hy + 2 + dip * 0.4)], (2.2, 0.8), face)
    if mask:
        s.paint(s.m_ellipse(hx - 0.5, hy, 2.2, 1.4), mask)
    s.ellipse(hx - 5.3, hy + 2.1 + dip * 0.4, 0.9, 0.8, "#2b2226", shade=False)
    s.ellipse(hx + 1.6, hy - 2.6, ears, ears * 1.1, ear_col or _dk(face, 0.15))
    s.eye(round(hx - 1.5), round(hy - 1))
    if s.act in ("walk", "run") and s.f % 2:
        s.shift(0, -1)


@sprite("common_hedgehog")
def _(s):
    # Brown spines with pale tips, a brown face and dark beady eyes.
    _hedgehog(s, "#6a5440", "#e8dcc4", "#8a6c50", belly="#a88a6a")


@sprite("northern_white_breasted_hedgehog")
def _(s):
    # Like the common hedgehog but with a bright white chest patch.
    _hedgehog(s, "#6a5642", "#ece2cc", "#8a7058", belly="#f4f0e8")


@sprite("southern_white_breasted_hedgehog")
def _(s):
    # The eastern Mediterranean hedgehog: pale spines and a white throat and chest.
    _hedgehog(s, "#7a6650", "#f0e8d4", "#9a7e62", belly="#f6f2ea")


@sprite("north_african_hedgehog")
def _(s):
    # Pale spines, a white face with a dark mask round the eyes and big ears.
    _hedgehog(s, "#8a7a68", "#f4eee0", "#f0ebe2", belly="#f6f2ea", ears=1.8, ear_col="#d8c8b8", mask="#6a5444",
              legs="#6a5444")


@sprite("long_eared_hedgehog")
def _(s):
    # A small desert hedgehog with long ears, a pale face and sandy spines.
    _hedgehog(s, "#a08a6a", "#f2e8d4", "#e8dccb", belly="#f4efe6", ears=2.4, ear_col="#e8b8a8",
              legs="#c8a888")


def _porcupine(s, crest):
    s.can("walk")
    w = s.wave() if s.act == "walk" else 0
    fur = "#2a2422"
    for x, sw in ((11, w), (22, -w)):
        s.ellipse(x - sw, 28, 2.6, 1.6, "#1e1a18")
    # long banded quills sweeping back off the body
    for i in range(10):
        x = 10 + i * 1.8
        y = 17 - 4 * math.sin(i / 9 * math.pi)
        s.path([(x, y + 2), (x + 6, y - 5 + i * 0.4)], 0.5, WHITE, shade=False)
        s.px([(round(x + 3), round(y - 1.5 + i * 0.2)), (round(x + 4.5), round(y - 3.3 + i * 0.3))], "#2b2226")
    m = s.ellipse(18, 21, 10.5, 7, fur, edge=True)
    for i in range(12):
        x = 9 + i * 1.7
        top = 21 - 7 * max(0.0, 1 - ((x - 18) / 10.5) ** 2) ** 0.5
        s.line(round(x), round(top + 3), round(x + 2.5), round(top - 2.5), "#f0eae0" if i % 2 else "#3a3230")
    s.paint(s.m_px([(14, 18), (19, 16), (23, 19), (12, 22), (20, 22)]), "#e8e0d4", within=m)
    # the crest: long pale bristles standing up from the head and neck
    for k in range(5):
        x = 8 + k * 1.4
        s.path([(x, 17), (x + 2.5, 9 + k * 0.6)], 0.4, crest, shade=False)
    s.ellipse(7.5, 22, 4.8, 4.2, "#3a302c", edge=True)
    s.ellipse(4, 23.5, 2, 1.6, "#2b2226")
    s.eye(6, 21)
    if s.act == "walk" and s.f % 2:
        s.shift(0, -1)


@sprite("crested_porcupine")
def _(s):
    # Africa's and Italy's big porcupine: black with long black-and-white banded quills and a crest of white bristles.
    _porcupine(s, "#f0ece4")


@sprite("indian_crested_porcupine")
def _(s):
    # Like the crested porcupine, with a browner crest of long bristles.
    _porcupine(s, "#c8b8a0")


# --------------------------------------------------------------------------- moles and shrews
def _mole(s, fur, pink):
    s.can("walk")
    w = s.wave() if s.act == "walk" else 0
    s.path([(28, 25), (31, 25.5)], (1.1, 0.6), fur)  # stubby furred tail
    for x, sw in ((22, -w), (25, w)):
        s.ellipse(x - sw, 28, 2, 1.3, pink)
    m = s.ellipse(18, 22, 11, 6.5, fur, edge=True)
    s.paint(s.m_ellipse(17, 18, 8, 2), mix(fur, "#ffffff", 0.14), within=m)
    s.paint(s.m_px([(14, 21), (20, 19), (24, 22), (11, 24)]), mix(fur, "#ffffff", 0.22), within=m)
    s.ellipse(10 + w, 27, 3.6, 2.2, pink, rot=-15, edge=True)  # broad digging hands
    s.px([(7 + round(w), 28), (8 + round(w), 29), (10 + round(w), 29)], mix(pink, "#000000", 0.25))
    s.path([(9, 21), (2, 23)], (2.6, 1.0), fur)
    s.ellipse(1.5, 23.5, 1.4, 1.2, pink)
    s.px([(6, 20)], "#1a1418")
    if s.act == "walk" and s.f % 2:
        s.shift(0, -1)


@sprite("european_mole")
def _(s):
    # Velvety black, with huge pink spade hands, a pink snout and eyes hidden in the fur.
    _mole(s, "#2e2a30", "#f0b0b0")


@sprite("iberian_mole")
def _(s):
    # A little smaller and grayer than the European mole.
    _mole(s, "#3e3a40", "#eeb2ae")


def _shrew(s, fur, belly=None, *, tail=7.0, side=None, snout="#d8a0a8", size=1.0, ears=False):
    """A shrew: a tiny velvety body, a long twitching snout, beady eyes and a thin tail."""
    s.can("walk", "eat")
    w = s.wave() if s.act == "walk" else 0
    sniff = 0.5 * s.cyc(0, 1, 0, 1) if s.act in ("idle", "eat") else 0
    dip = 1.5 if s.act == "eat" else 0
    k = size
    s.path([(26 * k + 2, 24), (26 * k + 2 + tail * 0.6, 25), (26 * k + 2 + tail, 24.5 - w * 0.5)], (0.9, 0.5),
           _dk(fur, 0.1))
    for x, sw in ((12, w), (22 * k, -w)):
        s.ellipse(x - sw, 28.5, 1.6, 1.0, "#e0b8b8")
    m = s.ellipse(17 * k + 1, 23.5, 9 * k, 5 * k, fur, edge=True)
    if belly:
        s.paint(s.m_ellipse(17 * k + 1, 27, 8 * k, 2.5), belly, within=m)
    if side:
        s.paint(s.m_ellipse(17 * k + 1, 24.5, 8 * k, 1.4), side, within=m)
    s.paint(s.m_ellipse(17 * k, 19.5, 6 * k, 1.5), mix(fur, "#ffffff", 0.15), within=m)
    s.path([(10, 23 + dip), (3 - sniff, 24.5 + dip)], (2.4, 0.8), fur)
    s.ellipse(2.4 - sniff, 24.6 + dip, 1.0, 0.9, snout)
    if ears:
        s.ellipse(10.5, 20, 1.4, 1.3, _dk(fur, 0.1))
    s.px([(7, 21 + round(dip))], "#120c10")
    if s.act == "walk" and s.f % 2:
        s.shift(0, -1)


@sprite("common_shrew")
def _(s):
    # Three-toned: a dark brown back, paler brown flanks and a gray-white belly.
    _shrew(s, "#3a2a22", "#c8beb4", side="#8a6a4e", tail=6)


@sprite("eurasian_pygmy_shrew")
def _(s):
    # Tiny, two-toned brown above and grayish below, with a relatively thick, hairy tail.
    _shrew(s, "#7a5a42", "#d0c8bc", tail=6, size=0.85)


@sprite("bicoloured_shrew")
def _(s):
    # A white-toothed shrew with a crisp line between its dark gray-brown back and white belly.
    _shrew(s, "#5a4a42", WHITE, tail=5.5, ears=True)


@sprite("greater_white_toothed_shrew")
def _(s):
    # Gray-brown all over, a bit paler below, with visible ears and long whiskers.
    _shrew(s, "#7a6a5e", "#b8aea4", tail=6, ears=True)


@sprite("lesser_white_toothed_shrew")
def _(s):
    # Smaller and browner than its greater cousin.
    _shrew(s, "#8a6e58", "#c8bcae", tail=5.5, ears=True, size=0.9)


@sprite("pygmy_white_toothed_shrew")
def _(s):
    # The Etruscan shrew, one of the world's smallest mammals: gray-brown with big ears.
    _shrew(s, "#8a7a6e", "#c0b6aa", tail=6, ears=True, size=0.75)


@sprite("sicilian_shrew")
def _(s):
    # Dark gray-brown above, a pale belly and pale feet.
    _shrew(s, "#4a3e38", "#d8d2c8", tail=5.5, ears=True)


# --------------------------------------------------------------------------- rodents
@sprite("alpine_marmot")
def _(s):
    # A big ground squirrel of the Alps: golden-brown and grizzled, with a darker head and a pale muzzle.
    critter(s, "#9a7850", "#d8c0a0", build="marmot", ear_in="#6a5038", tail="short", tail_col="#5a4430",
            tail_tip="#2b2226", head="#6a5440", muzzle="#e0d4c0", feet="#4a3a2a",
            markings=lambda s, g: flecks(s, g["body"], "#c8a878", every=5))


@sprite("bobak_marmot")
def _(s):
    # The steppe marmot: sandy yellow-brown with a short tail and a reddish face.
    critter(s, "#c09a64", "#e8d4b0", build="marmot", ear_in="#8a6840", tail="short", tail_col="#8a6a44",
            head="#b08050", muzzle="#ead8b8", feet="#7a5a38")


@sprite("eurasian_red_squirrel")
def _(s):
    # Bright russet with a white belly, a big bushy tail and long ear tufts.
    critter(s, "#c05a28", "#f6efe4", build="squirrel", ears="tuft", ear_in="#d88a5a", ear_tip="#8a3a18",
            tail="squirrel", tail_col="#b04e22", tail_tip="#d8803a", eye_ring="#f0d8c0")


@sprite("caucasian_squirrel")
def _(s):
    # The Persian squirrel: grizzled gray-brown above, a rusty-orange belly and tail, no ear tufts.
    critter(s, "#8a7058", "#d88a4a", build="squirrel", ear_in="#d89a6a", tail="squirrel", tail_col="#b0683a",
            tail_tip="#d89a5a", eye_ring="#e8c8a0")


@sprite("siberian_flying_squirrel")
def _(s):
    # Silky silver-gray with huge black eyes and a furry gliding flap between its legs.
    def flap(s, g):
        if g["act"] in ("idle", "walk", "look", "back"):
            s.paint(s.m_ellipse(g["bx"], g["by"] + g["bry"] * 0.75, g["brx"] * 0.85, 1.3), "#8a8a90", within=g["body"])
    critter(s, "#b0b0b4", "#f6f4ee", build="squirrel", ear_in="#d8c8c0", tail="squirrel", tail_col="#a0a0a6",
            tail_tip="#c8c8cc", eye_size=3, eye_ring="#4a4a50", markings=flap)


@sprite("siberian_chipmunk")
def _(s):
    # Golden-brown with five black stripes down its back and a striped face.
    critter(s, "#c8904e", "#f4ead8", build="ground", ear_in="#e0b090", tail="long", tail_col="#a8783e",
            markings=lambda s, g: back_stripes(s, g, ["#2e2420", "#d8b890", "#2e2420", "#d8b890", "#2e2420"], top=0.15),
            face=lambda s, g: face_stripes(s, g, "#3a2a20", "#f4ead8"))


@sprite("european_ground_squirrel")
def _(s):
    # The souslik: a slim, sandy-gray ground squirrel with faint pale flecks and big eyes.
    critter(s, "#b09a78", "#ece4d0", build="ground", ear_in="#c8a888", tail="short", tail_col="#9a8462",
            eye_ring="#f0e8d8", markings=lambda s, g: flecks(s, g["body"], "#e0d4bc", every=6))


@sprite("asia_minor_ground_squirrel")
def _(s):
    # The Anatolian souslik: plain sandy-yellow with a pale eye ring and a short tail.
    critter(s, "#c4a678", "#f0e6d0", build="ground", ear_in="#d8b890", tail="short", tail_col="#b09062",
            eye_ring="#f6eedc")


@sprite("barbary_ground_squirrel")
def _(s):
    # A gray-brown ground squirrel with white stripes down its sides and a bushy gray tail.
    critter(s, "#8a7462", "#ece4d8", build="ground", ear_in="#c8a888", tail="bushy", tail_col="#8a8078",
            tail_tip="#c8c0b8", eye_ring="#f0e8d8",
            markings=lambda s, g: back_stripes(s, g, ["#f4f0e8", "#8a7462", "#f4f0e8"], top=0.45, width=0.8))


@sprite("brown_hare")
def _(s):
    # A big tawny hare with long black-tipped ears, long legs and a tail black on top.
    critter(s, "#b08454", "#f0e4d0", build="hare", ears="xlong", ear_in="#e8b8a0", ear_tip=BLACK, tail="cotton",
            tail_col="#2b2226", eye_col="#8a6020", eye_ring="#e8d8b8",
            markings=lambda s, g: flecks(s, g["body"], "#6a4a30", every=6))


@sprite("mountain_hare")
def _(s):
    # Snow white in winter, with black ear tips and an all-white tail.
    critter(s, "#f2f0ea", WHITE, build="hare", ears="long", ear_in="#efc0b8", ear_tip=BLACK, tail="cotton",
            tail_col=WHITE, nose="#d08a90", feet="#e8e4dc", eye_col="#6a4a20")


@sprite("cape_hare")
def _(s):
    # A slim sandy desert hare with very long ears.
    critter(s, "#c4a476", "#f4ecdc", build="hare", ears="xlong", ear_in="#e8c0a8", ear_tip="#4a3a2a", tail="cotton",
            tail_col="#3a2e26", eye_col="#8a6020", eye_ring="#f0e4cc")


@sprite("granada_hare")
def _(s):
    # The Iberian hare: tawny with a white belly that reaches up its flanks, black ear tips.
    critter(s, "#b88c5a", WHITE, build="hare", ears="xlong", ear_in="#e8b8a0", ear_tip=BLACK, tail="cotton",
            tail_col="#2b2226", eye_col="#8a6020", eye_ring="#ecdcbc")


@sprite("eurasian_beaver")
def _(s):
    # Rich brown with a flat scaly paddle tail and orange front teeth.
    critter(s, "#6e4428", "#a07450", build="beaver", ear_in="#4a3020", tail="paddle", tail_col="#3a3036",
            muzzle="#a07450", nose="#2b2226", belly=False, face=teeth)


@sprite("european_water_vole")
def _(s):
    # A big, chubby brown vole with a blunt nose, small ears and a furry tail; it swims well.
    critter(s, "#6a4e36", "#a89078", build="vole", ear_in="#8a6a54", tail="rat", tail_col="#5a4230",
            nose="#2b2226", eye_size=2)


@sprite("bank_vole")
def _(s):
    # A small vole with a bright chestnut back, gray sides and a medium-length tail.
    critter(s, "#a85a32", "#d8d0c8", build="vole", ear_in="#c88a70", tail="rat", tail_col="#8a6a5a",
            nose="#3a2a24", markings=lambda s, g: back_stripes(s, g, ["#9a9088"], top=0.65, width=1.4))


@sprite("common_vole")
def _(s):
    # Sandy gray-brown, round and short-tailed, with small ears hidden in its fur.
    critter(s, "#9a8468", "#cfc4b2", build="vole", ear_in="#b89a80", tail="short", nose="#3a2a24")


@sprite("field_vole")
def _(s):
    # Darker, shaggier gray-brown than the common vole, with a very short tail.
    critter(s, "#6e5a44", "#b4a898", build="vole", ear_in="#9a7a64", tail="short", nose="#3a2a24",
            markings=lambda s, g: flecks(s, g["body"], "#8a7660", every=5))


@sprite("european_snow_vole")
def _(s):
    # A pale silvery-gray vole of high rocky slopes, with long whiskers and a whitish tail.
    critter(s, "#a8a49c", "#e6e2da", build="vole", ear_in="#c8b8b0", tail="rat", tail_col="#e8e4dc",
            nose="#5a4a4a")


@sprite("northern_red_backed_vole")
def _(s):
    # Gray sides with a broad rusty-red band down its back and a short tail.
    critter(s, "#8a8278", "#d0c8bc", build="vole", ear_in="#b89a80", tail="short", nose="#3a2a24",
            markings=lambda s, g: back_stripes(s, g, ["#b8602e"], top=0.0, width=2.0))


@sprite("norway_brown_lemming")
def _(s):
    # The Norway lemming: bold black head and shoulders, a golden-orange back and a pale belly.
    def pat(s, g):
        s.paint(s.m_ellipse(g["bx"] - g["brx"] * 0.6, g["by"] - g["bry"] * 0.3, 3.5, 2.5), "#1e1a1e",
                within=g["body"])
        back_stripes(s, g, ["#2b2226"], top=0.2, width=0.8)
    def face(s, g):
        s.paint(s.m_ellipse(g["hx"], g["hy"] - g["hry"] * 0.4, g["hrx"], g["hry"] * 0.8), "#1e1a1e", within=g["head_m"])
    critter(s, "#d08a3a", "#ecdcc0", build="vole", ear_in="#d8a070", tail="short", nose="#3a2a24", head="#d08a3a",
            markings=pat, face=face)


@sprite("eurasian_hamster")
def _(s):
    # The wild hamster: orange-brown above, a black belly, and white patches on its cheeks and sides.
    def pat(s, g):
        s.paint(s.m_ellipse(g["bx"], g["by"] + g["bry"] * 0.6, g["brx"] * 0.8, g["bry"] * 0.5), "#1e1a1e",
                within=g["body"])
        s.paint(s.m_ellipse(g["bx"] - g["brx"] * 0.55, g["by"], 1.8, 1.5), WHITE, within=g["body"])
    critter(s, "#c07a3e", "#1e1a1e", build="round", ears="small", ear_in="#e0a8a0", tail="none", nose="#e0909a",
            cheeks=WHITE, belly=False, feet=WHITE, markings=pat)


@sprite("european_wood_mouse")
def _(s):
    # Warm brown with a white belly, big ears, big black eyes and a long tail.
    critter(s, "#9a6a40", WHITE, build="mouse", ears="big", ear_in="#f0b0b8", tail="rat", tail_col="#c09a84",
            feet="#f0e8e0", nose="#e88a9a", eye_size=3)


@sprite("yellow_necked_field_mouse")
def _(s):
    # Like the wood mouse but bigger and redder, with a yellow collar across its white chest.
    def collar(s, g):
        if g["view"] == "side":
            s.paint(s.m_ellipse(g["bx"] - g["brx"] * 0.7, g["by"] + g["bry"] * 0.3, 1.8, 1.6), "#e8b84a",
                    within=g["body"])
    critter(s, "#a86a3a", WHITE, build="mouse", ears="big", ear_in="#f0b0b8", tail="rat", tail_col="#c09a84",
            feet="#f0e8e0", nose="#e88a9a", eye_size=3, markings=collar)


@sprite("striped_field_mouse")
def _(s):
    # Reddish-brown with a crisp black stripe down the middle of its back and smaller ears.
    critter(s, "#a8703e", "#ece6dc", build="mouse", ears="round", ear_in="#e8b0b0", tail="rat", tail_col="#b89482",
            nose="#e88a9a", markings=lambda s, g: back_stripes(s, g, ["#1e1a1e"], top=0.0, width=0.7))


@sprite("mound_building_mouse")
def _(s):
    # The steppe mouse that stores seeds under earth mounds: gray-brown and pale below, small and neat.
    critter(s, "#8a7a68", "#e4ded4", build="mouse", ears="round", ear_in="#e8b8b8", tail="rat", tail_col="#a8968a",
            nose="#e0909a", eye_size=2)


@sprite("hazel_dormouse")
def _(s):
    # A tiny golden-orange dormouse with big black eyes, a cream throat and a fluffy tail.
    critter(s, "#d8903e", "#f6ead2", build="mouse", ears="round", ear_in="#f0b8a8", tail="bushy", tail_col="#c8823a",
            nose="#d0808a", eye_size=3)


@sprite("european_fat_dormouse")
def _(s):
    # The edible dormouse: soft gray like a small squirrel, dark eye rings and a big bushy tail.
    critter(s, "#8e8c8c", "#f2f0ea", build="squirrel", ears="round", ear_in="#d8c0c0", tail="squirrel",
            tail_col="#7e7c7c", eye_size=3, eye_ring="#3a3436")


@sprite("european_garden_dormouse")
def _(s):
    # Rusty-gray with a bold black bandit mask, big ears and a long tail ending in a black-and-white tuft.
    def mask(s, g):
        if g["view"] == "side":
            s.paint(s.m_path([(g["hx"] - g["hrx"] - 1, g["hy"]), (g["hx"] + g["hrx"], g["hy"] - 0.6)], 0.9),
                    "#1e1a1e", within=g["head_m"])
    critter(s, "#a07a5e", WHITE, build="mouse", ears="big", ear_in="#e8b0b0", tail="long", tail_col="#a08a7a",
            tail_tip="#1e1a1e", nose="#e0909a", eye_size=3, face=mask)


@sprite("eurasian_forest_dormouse")
def _(s):
    # Gray-brown with a black stripe through the eye, a white belly and a bushy, flattened tail.
    def mask(s, g):
        if g["view"] == "side":
            s.paint(s.m_path([(g["hx"] - g["hrx"], g["hy"] - 0.2), (g["hx"] + g["hrx"] - 1, g["hy"] - 0.5)], 0.6),
                    "#2b2226", within=g["head_m"])
    critter(s, "#8a7a6a", WHITE, build="mouse", ears="round", ear_in="#e8b8b0", tail="bushy", tail_col="#7a6a5a",
            nose="#e0909a", eye_size=3, face=mask)


# --------------------------------------------------------------------------- bats
def _bat(s, fur, wing, bone, *, belly=None, ears="short", ear_col=None, face=None, leaf=None, big_eyes=False):
    """A bat from the front with its wings spread (tips up on the upbeat frames).
    ears: short, mouse (tall and pointed), long (huge rabbit ears), round, horseshoe."""
    s.can("fly")
    up = s.act == "fly" and s.f % 2 == 0
    lift = -5 if up else 0
    for side in (-1, 1):
        x = lambda v: 16 + side * v  # noqa: E731
        tip = (x(15), 9 + lift)
        pts = [(x(3), 13), tip, (x(13), 19 + lift * .4), (x(10), 17 + lift * .2), (x(8), 21), (x(5), 19), (x(3), 23)]
        s.poly(pts, wing, edge=True)
        for end in (tip, (x(13), 19 + lift * .4), (x(8), 21)):
            s.path([(x(3), 13.5), end], 0.45, bone, shade=False)
    s.poly([(12, 23), (20, 23), (18, 28), (16, 30), (14, 28)], wing)
    m = s.ellipse(16, 19, 4, 6, fur, edge=True)
    s.paint(s.m_ellipse(16, 21, 2.6, 3.4), belly or mix(fur, "#ffffff", 0.25), within=m)
    ec = ear_col or wing
    inner = mix(ec, "#e8a0a0", 0.45)
    if ears == "long":  # long-eared bats: ears nearly as long as the body
        for d in (-1, 1):
            e = s.path([(16 + d * 2.2, 10), (16 + d * 4.5, 4), (16 + d * 5, -1)], (1.8, 1.0), ec)
            s.paint(s.m_path([(16 + d * 2.4, 9), (16 + d * 4.4, 4), (16 + d * 4.8, 0.5)], (0.8, 0.4)), inner, within=e)
    elif ears == "mouse":
        s.poly([(12.5, 10), (11.5, 3.5), (14.8, 8.5)], ec)
        s.poly([(19.5, 10), (20.5, 3.5), (17.2, 8.5)], ec)
        s.poly([(12.9, 9.3), (12.3, 5.5), (14, 8.6)], inner, shade=False)
        s.poly([(19.1, 9.3), (19.7, 5.5), (18, 8.6)], inner, shade=False)
    elif ears == "horseshoe":  # broad, pointed and leaf-like, tips flicking out
        s.poly([(11.5, 11), (10, 4.5), (11.5, 3.5), (15, 9)], ec)
        s.poly([(20.5, 11), (22, 4.5), (20.5, 3.5), (17, 9)], ec)
    elif ears == "round":
        s.ellipse(12.5, 8, 2, 2.4, ec)
        s.ellipse(19.5, 8, 2, 2.4, ec)
    else:
        s.poly([(12.5, 9.5), (12, 5), (15, 8.5)], ec)
        s.poly([(19.5, 9.5), (20, 5), (17, 8.5)], ec)
    s.ellipse(16, 11.5, 4, 3.6, fur, edge=True)
    if face:
        s.ellipse(16, 12.8, 2.4, 1.6, face)
    if leaf:  # the horseshoe-shaped nose leaf
        s.ellipse(16, 13, 2.2, 1.8, leaf, shade=False)
        s.px([(16, 11), (16, 12)], mix(leaf, "#000000", 0.2))
        s.px([(15, 13), (17, 13)], "#2b2226")
    else:
        s.px([(15, 13), (17, 13)], "#2b2226")
    size = 2 if not big_eyes else 2
    s.eye(14, 11 if not leaf else 10, size=size)
    s.eye(18, 11 if not leaf else 10, size=size)
    return m


@sprite("common_pipistrelle")
def _(s):
    # A tiny dark brown bat with a blackish face, ears and wings.
    _bat(s, "#7a5a40", "#2e2420", "#1a1210", face="#3a2a24")


@sprite("kuhls_pipistrelle")
def _(s):
    # Sandy-brown with a neat white edge along the trailing edge of each wing.
    m = _bat(s, "#a07a54", "#3a2e28", "#1e1612", face="#4a3a2e")
    up = s.act == "fly" and s.f % 2 == 0
    lift = -5 if up else 0
    for side in (-1, 1):
        x = lambda v: 16 + side * v  # noqa: E731
        s.path([(x(13), 19 + lift * .4), (x(10), 17 + lift * .2), (x(8), 21), (x(5), 19), (x(3), 23)], 0.4,
               "#f0ece4", shade=False)


@sprite("nathusius_pipistrelle")
def _(s):
    # A little bigger and more chestnut than the common pipistrelle, with a frosty back.
    _bat(s, "#8a5e3c", "#3a2a22", "#1e1410", face="#4a3428", belly="#c8a080")


@sprite("savis_pipistrelle")
def _(s):
    # A mountain bat: golden-brown fur, a pale belly and a jet-black face, ears and wings.
    _bat(s, "#a8845a", "#1e1a1c", "#0e0a0c", face="#1a1418", belly="#ece4d4", ear_col="#1a1418")


@sprite("common_noctule")
def _(s):
    # A big, fast bat with sleek golden-brown fur, short rounded ears and long narrow wings.
    _bat(s, "#b07a40", "#3a2a1e", "#22180e", ears="round", face="#4a3020")


@sprite("lesser_noctule")
def _(s):
    # Smaller than the noctule, dark brown with golden tips to its fur.
    _bat(s, "#7a5232", "#2e2218", "#1a120c", ears="round", belly="#a8805a", face="#3a2a1e")


@sprite("azores_noctule")
def _(s):
    # The only bat of the Azores, often flying by day: dark brown with a paler belly.
    _bat(s, "#6a4a32", "#2a1e18", "#160e0a", ears="round", belly="#9a7a5a", face="#2e2018")


@sprite("eurasian_serotine")
def _(s):
    # A large, broad-winged bat with dark brown fur, a paler belly and a dark face.
    _bat(s, "#6a4a32", "#2a2220", "#160e0c", belly="#a88a6a", face="#2a1e1a")


@sprite("northern_serotine")
def _(s):
    # Dark brown with golden-tipped fur on the back; the bat that lives farthest north.
    m = _bat(s, "#4a3428", "#221a18", "#120c0a", belly="#c8a870", face="#221a18")
    s.paint(s.m_px([(14, 16), (17, 15), (15, 18), (18, 18)]), "#d8b060", within=m)


@sprite("particoloured_bat")
def _(s):
    # Frosted: dark fur with silvery-white tips on the back, a white belly and throat.
    m = _bat(s, "#5a4436", "#2a2020", "#160e0c", belly="#f4f0e8", face="#2a2020")
    s.paint(s.m_px([(14, 15), (17, 14), (13, 18), (18, 17), (15, 16)]), "#e8e4dc", within=m)


@sprite("daubentons_bat")
def _(s):
    # The water bat that skims ponds for insects: brown above, gray-white below, big feet.
    _bat(s, "#8a6a52", "#3e322e", "#22181a", belly="#e0dcd4", ears="mouse", face="#c89a8a")


@sprite("natterers_bat")
def _(s):
    # Light brown with a white belly, a pink face and long pale-based ears.
    _bat(s, "#a08066", "#4a3a34", "#2a1e1a", belly="#f2eee6", ears="mouse", ear_col="#c8a090", face="#e0a8a0")


@sprite("geoffroys_bat")
def _(s):
    # Woolly reddish-brown fur, a notch in each ear and a pale belly.
    _bat(s, "#a8683e", "#4a3428", "#2a1c14", belly="#d8b890", ears="mouse", ear_col="#8a5a40", face="#b07a60")


@sprite("mouse_eared_bat")
def _(s):
    # The greater mouse-eared bat: big, gray-brown above, white below, with long ears.
    _bat(s, "#8a7464", "#3e3430", "#22181a", belly="#f0ece4", ears="mouse", ear_col="#a08070", face="#c8a090")


@sprite("hovels_myotis")
def _(s):
    # A small Near Eastern mouse-eared bat: gray-brown with a pale belly.
    _bat(s, "#8a7a6a", "#3e3632", "#22181a", belly="#e4e0d8", ears="mouse", face="#c09a8a")


@sprite("schreibers_long_fingered_bat")
def _(s):
    # Very long, narrow wings, a short domed head and short ears; smoky gray fur.
    _bat(s, "#6a6260", "#2e2a2a", "#181414", belly="#a8a29c", ears="round", face="#3a3434")


@sprite("brown_long_eared_bat")
def _(s):
    # Fluffy brown, with enormous ears nearly as long as its body.
    _bat(s, "#9a7a5c", "#4a3a32", "#2a1e18", belly="#d8c8b4", ears="long", ear_col="#b09080", face="#c8a090")


@sprite("gaislers_long_eared_bat")
def _(s):
    # A paler, sandy long-eared bat of North Africa and Malta.
    _bat(s, "#b8a080", "#5a4a40", "#2e221c", belly="#f0e8dc", ears="long", ear_col="#c8ac98", face="#d8b0a0")


@sprite("kolombatovics_long_eared_bat")
def _(s):
    # A gray-brown Mediterranean long-eared bat with a white belly.
    _bat(s, "#9a8a7a", "#4a403a", "#2a201c", belly="#f2eee8", ears="long", ear_col="#b8a090", face="#d0a8a0")


@sprite("greater_horseshoe_bat")
def _(s):
    # Big and fluffy gray-brown, with a horseshoe-shaped flap of skin around its nose.
    _bat(s, "#a08470", "#5a4a42", "#2e221e", belly="#d8c8b8", ears="horseshoe", ear_col="#8a7060", leaf="#d8a090")


@sprite("lesser_horseshoe_bat")
def _(s):
    # Tiny and delicate, a plum-sized horseshoe bat that wraps itself in its wings to sleep.
    _bat(s, "#8a7464", "#4a3e38", "#2a201c", belly="#c8bcae", ears="horseshoe", ear_col="#7a6656", leaf="#d0a090")


@sprite("mediterranean_horseshoe_bat")
def _(s):
    # Gray-brown with a paler belly and a pointed upper nose leaf.
    _bat(s, "#9a8474", "#4e423c", "#2a201c", belly="#d8ccc0", ears="horseshoe", ear_col="#8a7466", leaf="#d8a898")


@sprite("blasiuss_horseshoe_bat")
def _(s):
    # A pale horseshoe bat, creamy below, with a long pointed nose leaf.
    _bat(s, "#b8a08c", "#5a4a42", "#2e221e", belly="#f0e8dc", ears="horseshoe", ear_col="#a08a7a", leaf="#e0b0a0")


@sprite("egyptian_rousette")
def _(s):
    # A fruit bat with a dog-like face: big dark eyes, a long muzzle and short round ears.
    s.can("fly")
    up = s.act == "fly" and s.f % 2 == 0
    fur, wing, bone = "#7a6250", "#4a3a34", "#2a1e1a"
    lift = -5 if up else 0
    for side in (-1, 1):
        x = lambda v: 16 + side * v  # noqa: E731
        tip = (x(15.5), 8 + lift)
        pts = [(x(3), 13), tip, (x(14), 19 + lift * .4), (x(11), 17 + lift * .2), (x(9), 22), (x(6), 20), (x(3), 24)]
        s.poly(pts, wing, edge=True)
        for end in (tip, (x(14), 19 + lift * .4), (x(9), 22)):
            s.path([(x(3), 13.5), end], 0.45, bone, shade=False)
        s.px([(round(x(15.5)), round(8 + lift) - 1)], bone)
    m = s.ellipse(16, 19.5, 4.2, 6.5, fur, edge=True)
    s.paint(s.m_ellipse(16, 15.5, 3.2, 1.8), "#a89070", within=m)
    s.ellipse(13, 7.5, 1.4, 2, "#3a2e2a")
    s.ellipse(19, 7.5, 1.4, 2, "#3a2e2a")
    s.ellipse(16, 10.5, 3.8, 3.4, fur, edge=True)
    s.path([(16, 11.5), (16, 15)], (1.9, 1.3), mix(fur, "#000000", 0.15))  # the dog-like muzzle
    s.px([(15, 15), (17, 15)], "#2b2226")
    s.eye(13, 9, size=2)
    s.eye(18, 9, size=2)


# --------------------------------------------------------------------------- whales and dolphins
def _rorqual(s, body, belly, *, dorsal=(21, 1.5), throat=True, pale=None, flipper=None, mottle=None, blow=True,
             head=None):
    """A long baleen whale side on: a slim body, a small dorsal fin set far back, a flat
    head with throat grooves and a tail stock tapering to the flukes."""
    s.can("swim")
    w = s.wave() if s.act == "swim" else 0
    if blow and s.act != "sleep":
        s.px([(7, 9 - (s.f % 2)), (8, 8), (9, 9), (8, 10), (8, 12)], "#8fd3ff")
    _fluke(s, [(27, 18), (32, 14), (31.5, 18.5), (32, 22)], body, w, pivot_x=27)
    s.path([(15, 18.4), (22, 18.6), (28.5, 18.3)], (3.8, 1.2), body)
    m = s.ellipse(13, 18.4, 11.5, 3.9, body, edge=True)
    s.path([(0.5, 18.6), (7, 17.6)], (1.6, 3.3), head or body)  # the long, flat head
    dx, dh = dorsal
    s.poly([(dx - 1.5, 14.6), (dx + 1, 14.6 - dh), (dx + 1.8, 14.8)], body)
    bm = s.m_ellipse(11, 21.2, 10.5, 1.9)
    s.paint(bm, belly, within=m)
    if throat:
        for x in range(3, 15, 2):
            s.paint(s.m_line(x, 20, x + 1, 22.5), mix(belly, body, 0.45), within=m)
    if mottle:
        s.paint(s.m_px([(10, 16), (14, 15), (18, 16), (8, 15), (21, 17), (16, 17), (12, 17)]), mottle, within=m)
    if pale:
        pale(s, m)
    s.ellipse(12, 22.5, 3.6, 1.1, flipper or mix(body, "#000000", 0.15), rot=25)
    s.px([(3, 18), (4, 18), (5, 18.5)], mix(body, "#000000", 0.45))  # the long mouth line
    s.eye(7, 17)


@sprite("blue_whale")
def _(s):
    # The biggest animal ever: long and slender, mottled blue-gray, with a tiny dorsal fin far back.
    _rorqual(s, "#5a7088", "#8aa0b4", dorsal=(23, 1.0), mottle="#8aa0b8")


@sprite("fin_whale")
def _(s):
    # Sleek dark gray with a white belly and a pale chevron behind the head; its right jaw is white.
    def pale(s, m):
        s.paint(s.m_ellipse(9, 16, 2, 1.2, rot=-30), "#a8b0bc", within=m)
        s.paint(s.m_poly([(1, 18.5), (6, 18.5), (6, 20), (1.5, 19.5)]), "#e8ecf0")
    _rorqual(s, "#3e4652", "#eef0f2", dorsal=(21, 2.4), pale=pale)


@sprite("sei_whale")
def _(s):
    # Dark steel-gray with a tall hooked dorsal fin and pale oval scars on its sides.
    _rorqual(s, "#4a525e", "#c8ccd4", dorsal=(20, 3.2), mottle="#8a929e")


@sprite("common_minke_whale")
def _(s):
    # The smallest rorqual: dark gray, a pointed snout and a white band on each flipper.
    def pale(s, m):
        s.paint(s.m_ellipse(11, 16.5, 2.6, 1.2, rot=-20), "#9aa2ae", within=m)
    _rorqual(s, "#3e4450", "#eceef0", dorsal=(20, 2.6), pale=pale, flipper=WHITE, blow=False)


@sprite("north_atlantic_bottlenose_whale")
def _(s):
    # A beaked whale with a huge rounded forehead, a short beak and a hooked fin; brown-gray, paler with age.
    s.can("swim")
    w = s.wave() if s.act == "swim" else 0
    body, belly = "#7a6e66", "#bcb2a8"
    _fluke(s, [(24, 16), (31, 10), (29.5, 16.5), (31, 22)], body, w)
    s.poly([(18, 13), (21, 7.5), (22.5, 13)], body)
    m = s.ellipse(15, 17, 11.5, 6, body, edge=True)
    s.paint(s.m_ellipse(13, 21, 9, 2.4), belly, within=m)
    s.ellipse(6.5, 15, 4.5, 4.4, mix(body, WHITE, 0.25), edge=True)  # the bulging melon
    s.path([(3, 18), (-0.5, 18.6)], (1.3, 0.9), body)
    s.ellipse(12, 22.5, 3, 1.2, mix(body, "#000000", 0.2), rot=30)
    s.eye(7, 17)


@sprite("long_finned_pilot_whale")
def _(s):
    # Jet black with a round bulbous head, a broad low hooked fin set forward, and long flippers.
    s.can("swim")
    w = s.wave() if s.act == "swim" else 0
    body = "#26262c"
    _fluke(s, [(24, 16), (31, 10), (29.5, 16.5), (31, 22)], body, w)
    s.poly([(11, 13), (15, 7), (18, 8), (17, 13)], body)
    m = s.ellipse(15, 17, 12, 5.8, body, edge=True)
    s.paint(s.m_ellipse(9, 21.5, 4, 1.2), "#7a7a84", within=m)  # pale anchor patch on the throat
    s.ellipse(4.5, 16.5, 4.2, 4.6, body, edge=True)
    s.ellipse(11, 23, 5, 1.2, mix(body, "#000000", 0.2), rot=28)
    s.eye(6, 16)


@sprite("common_dolphin")
def _(s):
    # The hourglass pattern: a tan-yellow front flank and a gray rear flank under a dark back.
    dolphin(s, "#2e3440", "#f2f2f0")
    body = s.m_ellipse(15, 17, 11.5, 6)
    s.paint(s.m_ellipse(10, 17.5, 5.5, 2), "#d8b870", within=body)
    s.paint(s.m_ellipse(20, 18, 5.5, 1.8), "#8a94a2", within=body)
    s.path([(2, 18.5), (-2.5, 19)], (1.0, 0.7), "#2e3440")
    s.eye(7, 15)


@sprite("striped_dolphin")
def _(s):
    # Blue-gray with a dark stripe running from the eye to the belly and a pale blaze sweeping up toward the fin.
    dolphin(s, "#4a5668", "#f2f2f4")
    body = s.m_ellipse(15, 17, 11.5, 6)
    s.paint(s.m_ellipse(17, 15.5, 5, 1.4, rot=-25), "#c8d0dc", within=body)
    s.paint(s.m_path([(7, 16.5), (14, 19.5), (24, 20)], 0.6), "#2a3240", within=body)
    s.path([(2, 18.5), (-2, 19)], (1.0, 0.7), "#4a5668")
    s.eye(7, 15)


@sprite("atlantic_spotted_dolphin")
def _(s):
    # Chunky, dark gray above and covered in pale spots, with a pale blaze on the flank.
    dolphin(s, "#4a5462", "#e8ebef")
    body = s.m_ellipse(15, 17, 11.5, 6)
    s.paint(s.m_px([(9, 13), (12, 12), (15, 12), (18, 13), (21, 14), (11, 15), (16, 15), (20, 16), (24, 16),
                    (13, 19), (18, 20), (22, 19)]), "#d8dde4", within=body)
    s.path([(2, 18.5), (-1.5, 19)], (1.0, 0.7), "#4a5462")
    s.eye(7, 15)


@sprite("white_beaked_dolphin")
def _(s):
    # A stocky northern dolphin, black with gray-white flank patches and a short white beak.
    dolphin(s, "#22242a", "#e8eaee")
    body = s.m_ellipse(15, 17, 11.5, 6)
    s.paint(s.m_ellipse(22, 15.5, 3.5, 2, rot=-20) | s.m_ellipse(11, 17.5, 3.5, 1.5), "#b8bec8", within=body)
    s.path([(2.5, 18.5), (0, 19)], (1.1, 0.8), "#eef0f2")
    s.eye(7, 15)


# --------------------------------------------------------------------------- seals
@sprite("bearded_seal")
def _(s):
    # A big gray-brown Arctic seal with a small head, square front flippers and a bushy mustache of long whiskers.
    pinniped(s, "#8a7a6c", "#b8aa9c", belly=False, whisker="#f4f0e4",
             blotch=lambda s, body: flecks(s, body, "#6e6054", every=11))


@sprite("ringed_seal")
def _(s):
    # The smallest Arctic seal: dark gray covered in pale rings.
    def rings(s, body):
        for x, y in ((12, 22), (17, 21), (22, 22), (15, 24), (20, 24), (25, 23), (10, 24)):
            s.paint(s.m_ellipse(x, y, 1.3, 1) & ~s.m_ellipse(x, y, 0.6, 0.4), "#d8dce2", within=body)
    pinniped(s, "#4a5058", "#a0a6ae", belly=False, blotch=rings)


@sprite("mediterranean_monk_seal")
def _(s):
    # One of the rarest seals: dark brown-black with a pale belly patch and a short, rounded face.
    pinniped(s, "#3e3632", "#c8c0b4", belly=True,
             blotch=lambda s, body: flecks(s, body, "#5a504a", every=12))
