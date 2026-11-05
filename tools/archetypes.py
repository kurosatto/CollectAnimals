"""Body plans for the sprites. Each function draws one kind of animal onto a Sprite,
with colours and features passed in so one plan covers many species."""
from __future__ import annotations

import math
import re

import numpy as np

from pixel import N, PAD_TOP, PAD_X, SS, _XS, _YS, Sprite, idx, mix, units

PINK = "#f2a7b4"

# slug -> drawing function; filled by @sprite in make_sprites.py and species_nc.py
S: dict = {}


def sprite(slug):
    def deco(fn):
        def draw(s):
            s.slug = slug  # body plans that vary by kind of animal read it
            return fn(s)
        S[slug] = draw
        return fn
    return deco

NOSE = "#3a2a33"
WHITE = "#fbf7ef"
BLACK = "#2b2630"
EYE = "#1d1428"


# --------------------------------------------------------------------------- mammals
def _lift(s: Sprite, dy: int):
    """Raise everything but the bottom row of feet (a bob in the stride)."""
    r = (28 + PAD_TOP) * SS
    keep_col, keep_reg = s.col[r:].copy(), s.reg[r:].copy()
    s.shift(0, -dy)
    feet = keep_reg > 0
    s.col[r:][feet], s.reg[r:][feet] = keep_col[feet], keep_reg[feet]


# --------------------------------------------------------------------------- small mammals
# Side-view proportions for the small mammals, all facing left with feet on the ground
# line. body/hip/head are ellipses (cx, cy, rx, ry[, rot]); hip is the hind thigh.
# snout runs from the head to its tip with (radius at the head, radius at the tip).
# fx is where the front leg starts and hx where the hind foot sits; tail is where the
# tail joins the rump. sit is the same animal up on its haunches.
CRITTERS = {
    # tree squirrels: slim, arched, big plumed tail
    "squirrel": dict(body=(17, 24, 6.2, 3.6, -14), hip=(21, 25.5, 3.6, 3.6), head=(9.5, 20.5, 3.6, 3.2),
                     snout=((7.5, 21), (5, 21.8), (2.0, 1.3)), fx=12.5, hx=20.5, leg=0.9, foot=2.6,
                     tail=(23.5, 24), ear=(1.2, -3.2),
                     sit=dict(body=(19, 22, 3.8, 5.6, 12), hip=(20, 27, 4, 3.4), head=(15.5, 15, 3.5, 3.1))),
    # ground squirrels and chipmunks: a little lower and longer, smaller tail
    "ground": dict(body=(17, 24.5, 6.6, 3.5, -8), hip=(21.5, 25.8, 3.5, 3.4), head=(9.2, 21.5, 3.6, 3.1),
                   snout=((7.2, 22), (4.8, 22.8), (2.0, 1.3)), fx=12.5, hx=21, leg=0.9, foot=2.6,
                   tail=(24, 24.5), ear=(1.2, -3.0),
                   sit=dict(body=(19, 22, 3.8, 5.6, 12), hip=(20, 27, 4, 3.4), head=(15.5, 15, 3.5, 3.1))),
    # marmots, groundhogs and prairie dogs: heavy, low, short legs
    "marmot": dict(body=(17.5, 24.5, 8.2, 4.6, -4), hip=(22.5, 25.5, 4.4, 4.2), head=(8.2, 22, 4.0, 3.5),
                   snout=((6, 22.8), (3.4, 23.5), (2.4, 1.6)), fx=12, hx=22, leg=1.3, foot=2.6,
                   tail=(25.5, 23.5), ear=(1.3, -3.2),
                   sit=dict(body=(18.5, 21.5, 4.6, 6.4, 8), hip=(19.5, 26.8, 4.8, 3.8), head=(15.5, 13.5, 4.0, 3.5))),
    # rabbits and hares: hunched, rump high, long hind feet
    "rabbit": dict(body=(18, 23.5, 7.0, 4.8, -12), hip=(22, 25, 4.6, 4.8), head=(9.5, 19.5, 3.8, 3.4),
                   snout=((7.5, 20.5), (5.6, 21.3), (2.2, 1.6)), fx=12.5, hx=22, leg=1.0, foot=3.6,
                   tail=(25.5, 21), ear=(2.0, -2.6),
                   sit=dict(body=(18.5, 21.5, 4.6, 6.4, 8), hip=(20, 26.5, 5, 4), head=(15, 13.5, 3.8, 3.4))),
    "hare":   dict(body=(18, 21.5, 7.4, 4.4, -14), hip=(22.5, 23, 4.4, 4.6), head=(9.2, 17, 3.6, 3.2),
                   snout=((7.2, 18), (5.2, 18.8), (2.0, 1.5)), fx=13, hx=22.5, leg=1.0, foot=4.0,
                   tail=(25.8, 19), ear=(2.0, -2.4),
                   sit=dict(body=(18.5, 20.5, 4.4, 6.6, 8), hip=(20, 26, 5, 4.4), head=(15, 12, 3.6, 3.2))),
    # mice, rats and voles: low, pointed nose, long thin tail
    "mouse":  dict(body=(16.5, 26, 6.0, 3.6, -6), hip=(20, 27, 3.2, 3.0), head=(9.5, 24.5, 3.4, 2.9),
                   snout=((7.5, 25.2), (4.6, 26.2), (1.9, 0.9)), fx=12, hx=20, leg=0.7, foot=2.2,
                   tail=(22.5, 26), ear=(1.0, -3.0),
                   sit=dict(body=(18, 24, 3.6, 4.8, 10), hip=(19, 28, 3.6, 2.8), head=(14.5, 18.5, 3.4, 2.9))),
    "vole":   dict(body=(16.5, 26, 6.6, 4.0, -2), hip=(20.5, 27, 3.4, 3.2), head=(9.6, 25, 3.6, 3.2),
                   snout=((7.5, 25.6), (5.2, 26.4), (2.2, 1.2)), fx=12, hx=20.5, leg=0.7, foot=2.0,
                   tail=(23, 26.5), ear=(1.2, -2.6),
                   sit=dict(body=(18, 24, 3.8, 4.8, 10), hip=(19, 28, 3.8, 2.8), head=(14.5, 18.5, 3.6, 3.2))),
    # hamsters and pikas: round, no neck, tiny legs
    "round":  dict(body=(17.5, 25, 7.2, 5.0, 0), hip=(21.5, 26, 4.0, 4.0), head=(10.5, 23, 4.4, 4.0),
                   snout=((8, 24), (6.2, 24.6), (2.6, 1.6)), fx=13, hx=21, leg=0.9, foot=2.0,
                   tail=(24.5, 25), ear=(1.0, -3.4),
                   sit=dict(body=(18, 23.5, 5.0, 6.0, 6), hip=(19, 28, 4.6, 2.8), head=(15, 16, 4.4, 4.0))),
    # otters: long and low, thick tapering tail
    "otter":  dict(body=(16.5, 25, 9.0, 3.4, -3), hip=(23, 25.5, 3.4, 3.2), head=(6.2, 23.5, 3.2, 2.8),
                   snout=((4.2, 24.2), (2.2, 24.8), (2.0, 1.4)), fx=10, hx=23, leg=1.1, foot=2.2,
                   tail=(25, 26), ear=(1.0, -2.6),
                   sit=dict(body=(17, 22, 3.6, 6.2, 6), hip=(18, 27.5, 4, 3), head=(14, 13.5, 3.2, 2.8))),
    # beavers, muskrats and coypu: a big humped back, short legs, nose low
    "beaver": dict(body=(17.5, 24.5, 8.4, 5.0, -2), hip=(22.5, 25.5, 4.6, 4.2), head=(8, 23, 3.8, 3.4),
                   snout=((6, 24), (3.4, 24.8), (2.4, 1.6)), fx=12, hx=22, leg=1.2, foot=2.6,
                   tail=(25.5, 26), ear=(1.2, -3.0),
                   sit=dict(body=(18.5, 21.5, 4.6, 6.4, 8), hip=(19.5, 26.8, 4.8, 3.8), head=(15, 13.5, 3.8, 3.4))),
    # badgers: flat and wide, wedge head, very short legs
    "badger": dict(body=(17.5, 25, 9.5, 4.2, 0), hip=(23.5, 25.8, 4.0, 3.6), head=(7, 25, 4.0, 3.2),
                   snout=((4.6, 25.8), (2.0, 26.6), (2.2, 1.2)), fx=11, hx=23.5, leg=1.6, foot=2.4,
                   tail=(27, 23.5), ear=(1.6, -2.6),
                   sit=dict(body=(17.5, 22, 4.6, 6, 6), hip=(18.5, 27, 5, 3.4), head=(14, 15, 4, 3.2))),
    # ringtails: slim cat-like body on longer legs, fox face, huge tail
    "ringtail": dict(body=(15.5, 23, 6.4, 3.2, -4), hip=(19.5, 23.5, 3.2, 3.2), head=(7.6, 19.5, 3.4, 3.0),
                     snout=((5.6, 20.4), (3.0, 21.2), (1.8, 0.9)), fx=11, hx=19.5, leg=0.9, foot=1.8,
                     tail=(21.5, 22), ear=(1.0, -3.0),
                     sit=dict(body=(17, 21.5, 3.8, 5.6, 8), hip=(18, 26.5, 4, 3.4), head=(13.5, 14, 3.4, 3))),
}


def critter(s: Sprite, fur, light=WHITE, *, build="ground", ears="small", ear_in=PINK, tail="long",
            tail_col=None, tail_tip=None, nose=NOSE, muzzle=None, belly=True, feet=None, head=None,
            eye_col=EYE, eye_size=2, eye_ring=None, cheeks=None, ear_tip=None, markings=None,
            face=None, behind=None, floats=False):
    """A small mammal from the side, walking left: squirrels, chipmunks, rabbits,
    mice, marmots, otters and the like.

    Poses: idle, walk (a bounding gait), sleep (curled up), sit (up on its haunches,
    nibbling), look (head turned to you) and back (looking back over its shoulder).
    Otters and beavers also swim, low in the water with the head up; floats=True
    (the sea otter) lies on its back in the water instead.
    markings(s, g) and face(s, g) add patterns to the body and head; g holds the
    proportions, the body and head masks and the way the head is turned
    (g["view"]: "side", "front" or "back")."""
    if floats:
        s.can("swim")
        return _floating(s, fur, light, head or fur, muzzle or light, nose, feet or mix(fur, "#1a1420", 0.12),
                         tail_col or fur, eye_col)
    s.can("walk", "sit", "look", "back", "eat")
    if build in ("otter", "beaver"):
        s.can("swim")
    b = CRITTERS[build]
    act, f = s.act, s.f
    tail_col = tail_col or fur
    head = head or fur
    muzzle = muzzle or light
    feet = feet or mix(fur, "#1a1420", 0.12)
    far = lambda c: mix(c, "#1a1420", 0.3)  # noqa: E731  (limbs and ear on the far side)
    sitting = act == "sit"
    lying = act == "sleep"
    swimming = act == "swim"
    view = {"look": "front", "back": "back"}.get(act, "side")
    ground = 30.5
    geo = dict(b["sit"]) if sitting else {}
    bx, by, brx, bry, brot = geo.get("body", b["body"])
    hx, hy, hrx, hry = geo.get("head", b["head"])
    px_, py_, prx, pry = geo.get("hip", b["hip"])
    tx, ty = b["tail"]
    if sitting:
        tx, ty = px_ + prx - 0.5, py_ + 1.5
    if swimming:
        # Low in the water, back and head showing, tail trailing out behind.
        by, py_, ty = 24.5, 25, 25
        bry *= 0.9
        brot = 0
        hy -= 1.5
    if act == "eat":
        # Head down, nibbling the grass in front of its front paws.
        hx, hy = hx - 1.2, 30.5 - hry - 0.4 - s.cyc(0, 0.6, 0, 0.6)
    if lying:
        # Curled up low: the head drops onto the front paws.
        drop = round(ground - 0.4 - (by + bry))
        by, py_, ty = by + drop, py_ + drop, ty + drop
        hy = min(ground - hry - 0.3, hy + drop + 1.5)
        hx += 1
    # Bounding gait: gather, push off, stretch out in the air, land.
    reach, push, lift = s.cyc((0, 0, 0), (0.6, 1.8, 1), (2.4, 2.6, 2), (1.6, 0.4, 1)) if act == "walk" else (0, 0, 0)
    if swimming:
        reach, push = 1.2 * s.wave(), -1.2 * s.wave()
    g = dict(b, view=view, build=build, act=act, hx=hx, hy=hy, hrx=hrx, hry=hry, bx=bx, by=by, brx=brx, bry=bry,
             brot=brot)
    if behind:
        behind(s, g)

    # far legs
    if swimming:
        s.ellipse(b["fx"] + 1 - reach, 28, 1.6, 1.0, far(feet))
    elif not lying and not sitting:
        _critter_leg(s, b["fx"] + 1.6, by, ground, b["leg"], far(fur), reach * 0.6 - 0.8, far(feet))
        s.ellipse(b["hx"] + 2.2 + push * 0.6, ground - 0.6, b["foot"] * 0.9, 0.9, far(feet))
    _critter_tail(s, tail, tx, ty, tail_col, tail_tip, act, f)
    # far ear peeks out behind the head
    if view != "front":
        _critter_ear(s, ears, hx, hy, hrx, hry, b["ear"], far(head), None, view, ear_tip, near=False)

    # body
    breath = 0.35 * max(0, s.wave()) if lying else 0
    body = s.ellipse(bx, by, brx + breath, bry + breath, fur, rot=brot)
    if belly:
        s.fill(s.m_ellipse(bx - 0.5, by + bry * 0.8, brx * 0.78, bry * 0.5, brot) & body, light, shade=False)
    if swimming:
        hip = s.ellipse(px_, py_, prx, pry * 0.8, fur)
    elif not lying:
        hip = s.ellipse(px_, py_, prx, pry, fur)
        if belly and sitting:
            s.fill(s.m_ellipse(bx - 2, by + 1, 2.2, bry * 0.8, brot) & body, light, shade=False)
    else:
        hip = s.ellipse(px_ + 0.5, py_ + 0.5, prx * 0.9, pry * 0.8, fur)
    g["body"] = body | hip
    if markings:
        markings(s, g)

    # near legs
    if sitting:
        s.ellipse(px_ - 1.5, ground - 0.6, b["foot"] + 0.6, 1.0, feet)
        # front paws held up to the mouth, nibbling
        up = s.cyc(0, 1, 0, 1)
        s.path([(bx - 2, by - 2.5), (hx + 0.5, hy + hry + 1.2 - up)], 0.9, fur)
        s.ellipse(hx + 0.2, hy + hry + 1.2 - up, 1.3, 1.1, feet)
    elif swimming:
        s.ellipse(b["fx"] - reach, 28.5, 1.8, 1.0, feet)
        s.ellipse(px_ + 1 - push, 29, 2.2, 1.0, feet)
    elif lying:
        s.ellipse(hx - 1.2, ground - 0.8, 2.0, 1.0, feet)
        s.ellipse(px_ - 1.5, ground - 0.6, b["foot"], 0.9, feet)
    else:
        _critter_leg(s, b["fx"], by, ground, b["leg"], fur, reach - 0.4 * push, feet)
        s.ellipse(b["hx"] - push * 0.4 - 1 + push, ground - 0.6, b["foot"], 1.0, feet)

    # neck, head and face
    if not lying:
        s.path([(bx - brx * 0.55, by - bry * 0.35), (hx + 0.8, hy + 0.8)], min(hry, bry) * 0.75, fur)
    _critter_head(s, g, head, muzzle, nose, ears, ear_in, ear_tip, eye_col, eye_size, eye_ring, cheeks, face)
    if lift:
        s.shift(0, -lift)


def _floating(s: Sprite, fur, light, head, muzzle, nose, feet, tail_col, eye_col):
    """A sea otter on its back in the water, paws folded on its chest, looking at you.
    It sleeps the same way; walking and swimming paddle the hind feet."""
    w = s.wave() if s.act in ("walk", "swim") else 0
    breath = 0.3 * max(0, s.wave()) if s.act == "sleep" else 0
    s.path([(24, 27), (28, 26.5 - w * 0.6), (31, 25.5)], (1.8, 1.0), tail_col)
    s.ellipse(25.5, 23.6 + w * 0.8, 1.6, 2.2, feet, rot=-25)
    s.ellipse(16.5, 27, 8.6, 3.2 + breath, fur)
    s.fill(s.m_ellipse(16, 25.2, 6.5, 1.3), mix(fur, light, 0.25), shade=False)
    s.ellipse(23.5, 24.2 - w * 0.8, 1.6, 2.2, feet, rot=-30)
    hm = s.ellipse(7, 23.8, 3.6, 3.3, head, edge=True)
    s.ellipse(6.6, 25.4, 1.9, 1.3, muzzle, shade=False)
    s.ellipse(3.8, 21.5, 1.1, 1.1, head)
    s.ellipse(10.2, 21.5, 1.1, 1.1, head)
    s.px([(6, 24)], nose)
    s.eye(4, 22, color=eye_col)
    s.eye(8, 22, color=eye_col)
    s.ellipse(12, 24.4, 1.5, 1.2, feet)
    s.ellipse(14.4, 24.6, 1.5, 1.2, feet)
    return hm


def back_stripes(s: Sprite, g, cols, top=0.5, width=1.0):
    """Lengthwise stripes along the back, one per colour from the spine down."""
    bx, by, brx, bry = g["bx"], g["by"], g["brx"], g["bry"]
    rot = g["brot"]
    m = s.m_ellipse(bx + 0.5, by, brx * 0.85, bry, rot)
    for k, col in enumerate(cols):
        off = top + k * width
        band = s.m_ellipse(bx, by + off, brx, bry, rot) & ~s.m_ellipse(bx, by + off + width, brx, bry, rot)
        s.paint(band & m, col, within=g["body"])


def flecks(s: Sprite, mask, col, every=5, seed=0):
    """A scatter of single-pixel flecks inside mask."""
    pts = [(x, y) for x, y in units(mask) if ((x + PAD_X) * 7 + (y + PAD_TOP) * 13 + seed) % every == 0]
    s.paint(s.m_px(pts), col, within=mask)


def face_stripes(s: Sprite, g, dark, pale):
    """Chipmunk face: a dark stripe through the eye with pale ones above and below."""
    ey = round(g["hy"] - g["hry"] * 0.35)
    h = g["head_m"]
    s.paint(s.m_line(-4, ey - 1, 40, ey - 1) | s.m_line(-4, ey + 2, 40, ey + 2), pale, within=h)
    s.paint(s.m_line(-4, ey + 1, 40, ey + 1), dark, within=h)


def teeth(s: Sprite, g, col="#f0a030"):
    """Big orange gnawing teeth below the nose (beavers and their kin)."""
    (sx0, sy0), (sx1, sy1), (r0, r1) = g["snout"]
    dx, dy = g["hx"] - g["head"][0], g["hy"] - g["head"][1]
    if g["view"] == "front":
        x, y = round(g["hx"] + 0.1), round(g["hy"] + g["hry"] + 0.2)
        s.px([(x, y), (x, y + 1)], col)
        return
    d = 1 if g["view"] == "back" else -1
    x = round((sx1 if d < 0 else 2 * g["hx"] - sx1) + dx - d * 0.4)
    y = round(sy1 + dy + r1 + 0.2)
    s.px([(x, y), (x, y + 1)], col)


def _critter_leg(s: Sprite, x, top_y, ground, r, col, reach, foot):
    """A front leg from the chest down to a small paw; reach > 0 swings it forward."""
    fx = x - reach
    lift = 0.8 * max(0.0, reach - 1)
    s.path([(x + 0.4, top_y), (fx, ground - 0.8 - lift)], (r * 1.3, r), col)
    s.ellipse(fx - 0.6, ground - 0.6 - lift, r + 0.8, 0.9, foot)


def _critter_head(s: Sprite, g, head, muzzle, nose, ears, ear_in, ear_tip, eye_col, eye_size, eye_ring, cheeks,
                  face):
    hx, hy, hrx, hry, view = g["hx"], g["hy"], g["hrx"], g["hry"], g["view"]
    (sx0, sy0), (sx1, sy1), (sr0, sr1) = g["snout"]
    if (hx, hy) != tuple(g["head"][:2]):
        dx, dy = hx - g["head"][0], hy - g["head"][1]
        sx0, sx1, sy0, sy1 = sx0 + dx, sx1 + dx, sy0 + dy, sy1 + dy
    if view == "front":
        # Turned to face you: a rounder head, both eyes, the nose in the middle.
        cx = hx + 0.6
        if ears != "none":
            for d in (-1, 1):
                _critter_ear(s, ears, cx + d * hrx * 0.55, hy, hrx * 0.6, hry, (0, -3.0), head, ear_in, "front",
                             ear_tip)
        hm = s.ellipse(cx, hy, hrx * 1.05, hry * 1.02, head, edge=True)
        s.ellipse(cx, hy + hry * 0.5, max(1.6, sr0 * 0.95), max(1.2, sr0 * 0.6), muzzle, shade=False)
        g["head_m"] = hm
        if face:
            face(s, g)
        if cheeks:
            s.paint(s.m_ellipse(cx - hrx * 0.7, hy + hry * 0.3, 1.4, 1.2)
                    | s.m_ellipse(cx + hrx * 0.7, hy + hry * 0.3, 1.4, 1.2), cheeks, within=hm)
        ex = [round(cx - hrx * 0.5 - 0.5), round(cx + hrx * 0.5 - 0.5)]
        ey = round(hy - hry * 0.3)
        for x in ex:
            if eye_ring:
                r = eye_size / 2
                s.paint(s.m_ellipse(x + r, ey + r, r + 1, r + 1), eye_ring, within=hm)
            s.eye(x, ey, size=eye_size, color=eye_col)
        n = round(cx - 0.5)
        s.px([(n, round(hy + hry * 0.35))], nose)
        return
    d = 1 if view == "back" else -1  # which way the face points
    if d > 0:  # mirror the snout around the head's centre
        sx0, sx1 = 2 * hx - sx0, 2 * hx - sx1
    hm = s.ellipse(hx, hy, hrx, hry, head, edge=True)
    sm = s.path([(sx0, sy0), (sx1, sy1)], (sr0, sr1), head)
    jaw = s.m_path([(sx0, sy0 + sr0 * 0.55), (sx1 - d * 0.3, sy1 + sr1 * 0.5)], (sr0 * 0.55, sr1 * 0.5))
    s.paint(jaw, muzzle, within=sm | hm)
    g["head_m"] = hm | sm
    if face:
        face(s, g)
    if cheeks:
        s.paint(s.m_ellipse(hx + d * 0.2, hy + hry * 0.45, 1.8, 1.3), cheeks, within=hm)
    _critter_ear(s, ears, hx, hy, hrx, hry, g["ear"], head, ear_in, view, ear_tip)
    # nose at the tip
    tip = round(sx1 + d * (sr1 - 0.6))
    s.px([(tip, round(sy1 - sr1 * 0.4))], nose)
    ex = round(hx + d * hrx * 0.38 - (eye_size - 1) * (d < 0))
    ey = round(hy - hry * 0.35)
    if eye_ring:
        r = eye_size / 2
        s.paint(s.m_ellipse(ex + r, ey + r, r + 1, r + 0.9), eye_ring, within=hm)
    s.eye(ex, ey, size=eye_size, color=eye_col)


def _critter_ear(s: Sprite, kind, hx, hy, hrx, hry, off, col, inner, view, tip_col=None, near=True):
    """One ear (tip_col colours its tip). Rabbits' long ears sweep back; the rest stand up."""
    if kind == "none":
        return
    d = 1 if view == "back" else -1
    ox, oy = off
    if view == "front":
        x, y = hx, hy + oy
    else:
        x, y = hx - d * ox * (1 if near else 0.3) + (0 if near else 1.0 * -d), hy + oy + (0 if near else 0.4)
    shade = inner is not None
    if kind in ("long", "xlong"):
        L = 5.6 if kind == "long" else 7.2
        if view == "front":
            tip = (x + (x - hx) * 0.4, y - L)
        else:
            tip = (x - d * 2.4, y - L)
            if not near:
                tip = (tip[0] - d * 1.6, tip[1] + 0.6)
        m = s.path([(x, y + 1), tip], (1.5, 1.2), col, shade=shade)
        if inner:
            s.path([(x, y), (tip[0] + (0.2 if view == "front" else -d * 0.3), tip[1] + 1.4)], (0.7, 0.5), inner,
                   shade=False)
        if tip_col:
            s.paint(s.m_ellipse(tip[0], tip[1] + 0.3, 1.7, 1.5), tip_col, within=m)
        return
    if kind == "tuft":
        s.poly([(x - 1.5, y + 1.2), (x - d * 0.3, y - 2.8), (x + 1.5, y + 1.2)], col, shade=shade)
        s.px([(round(x - d * 0.3), round(y - 3.8)), (round(x - d * 0.3), round(y - 4.8))], tip_col or col)
        if inner:
            s.px([(round(x), round(y))], inner)
        return
    if kind == "point":
        s.poly([(x - 1.8, y + 1.4), (x - d * 0.4, y - 3.4), (x + 1.8, y + 1.4)], col, shade=shade)
        if inner:
            s.poly([(x - 0.8, y + 0.8), (x - d * 0.4, y - 1.6), (x + 0.8, y + 0.8)], inner, shade=False)
        return
    r = {"small": 1.5, "round": 2.3, "big": 2.8, "tiny": 1.0}[kind]
    s.ellipse(x, y - 0.3, r, r * 1.05, col, shade=shade)
    if inner and r >= 1.5:
        s.ellipse(x - d * 0.2, y - 0.1, r * 0.5, r * 0.55, inner, shade=False)


def _critter_tail(s: Sprite, kind, x, y, col, tip, act, f):
    """The tail, joined to the rump at (x, y). Bushy tails sway a little as they go."""
    sway = s.cyc(0, 0.6, 1, 0.4) if act == "walk" else 0.5 * s.wave() if act in ("idle", "look") else 0
    if act == "sleep" and kind in ("squirrel", "bushy", "ringed"):
        # wrapped over the back like a blanket
        m = s.path([(x, y + 1), (x - 3, y - 3.5), (x - 8, y - 4.5), (x - 12, y - 3)], (2.6, 2.2), col)
        if tip:
            s.paint(s.m_path([(x - 3, y - 5.5), (x - 8, y - 6.5), (x - 12, y - 5)], 1.0), tip, within=m)
        return
    if kind == "squirrel":
        pts = [(x - 1, y + 0.5), (x + 3, y - 2), (x + 4.5 + sway, y - 7), (x + 3 + sway, y - 12),
               (x - 0.5 + sway, y - 14.5), (x - 2.5 + sway * 0.5, y - 13)]
        m = s.path(pts, (1.6, 3.4), col)
        if tip:
            s.paint(m & ~s.m_path([(x - 1, y), (x + 2, y - 2), (x + 3 + sway, y - 7), (x + 1.8 + sway, y - 11.5),
                                   (x - 0.5 + sway, y - 13)], (1.0, 2.2)), tip, within=m)
    elif kind == "bushy":
        m = s.path([(x - 1, y), (x + 3, y - 1.5), (x + 6, y - 4 - sway), (x + 7, y - 7 - sway)], (1.6, 2.6), col)
        if tip:
            s.paint(s.m_ellipse(x + 6.5, y - 6.5 - sway, 2.2, 2.0), tip, within=m)
    elif kind == "long":  # chipmunks and ground squirrels hold theirs up and out
        m = s.path([(x - 1, y), (x + 3, y - 1.5), (x + 5.5, y - 4.5 - sway), (x + 6.5, y - 8 - sway)], (1.2, 1.6), col)
        if tip:
            s.paint(m & ~s.m_path([(x - 1, y), (x + 3, y - 1.5), (x + 5.5, y - 4.5 - sway), (x + 6.5, y - 8 - sway)],
                                  (0.6, 0.8)), tip, within=m)
    elif kind == "short":
        m = s.ellipse(x + 1.6, y - 0.6, 2.2, 1.3, col, rot=-30)
        if tip:
            s.paint(s.m_ellipse(x + 3.2, y - 1.5, 1.2, 1.1), tip, within=m)
    elif kind == "cotton":
        s.ellipse(x + 0.8, y, 1.8, 1.9, col)
    elif kind == "rat":
        s.path([(x - 1, y), (x + 3, y + 2), (x + 6, y + 4.2), (x + 9.5, y + 4.5 - sway)], (1.0, 0.5), col)
    elif kind == "otter":
        s.path([(x - 2, y - 1), (x + 3, y + 1), (x + 7.5, y + 3.5 - sway)], (2.4, 0.8), col)
    elif kind == "paddle":
        m = s.ellipse(x + 4.5, y + 3.4, 4.6, 1.4, col, rot=8)
        for k in (2.5, 4.5, 6.5):
            s.paint(s.m_line(x + k, y + 2.5, x + k + 0.5, y + 4.5), mix(col, "#000000", 0.25), within=m)
    elif kind == "ringed":
        pts = [(x - 1, y), (x + 3, y - 1), (x + 7, y - 4 - sway), (x + 8, y - 10 - sway)]
        m = s.path(pts, (1.6, 2.2), col)
        for k in range(4):
            yy = y - 1.5 - k * 2.6
            s.paint(s.m_poly([(x, yy), (x + 12, yy - 2.5), (x + 12, yy - 1.2), (x, yy + 1.3)]), tip or BLACK, within=m)


# Proportions for the side-view walkers: body (cx, cy, rx, ry), leg radius, front and
# back leg x, where the legs start, the neck (from, to, radius), the head (cx, cy, rx, ry)
# and the snout (from, tip, (radius at the head, radius at the tip)).
BUILDS = {
    "deer":  dict(body=(19, 17.5, 7.5, 4.4), leg=0.9, fx=13.5, bx=23.5, top=19, neck=((13.5, 15), (9.5, 9.5), 2.1),
                  head=(8.5, 8.5, 3.4, 3.0), snout=((6.5, 10), (2.6, 11), (1.7, 1.2))),
    "sheep": dict(body=(19, 18.5, 8.2, 5.4), leg=1.2, fx=13.5, bx=24, top=21, neck=((13, 16), (10, 12), 2.6),
                  head=(8.5, 11, 3.6, 3.4), snout=((6.5, 12.5), (3.6, 13.5), (1.9, 1.5))),
    "dog":   dict(body=(18, 19.5, 8, 4.2), leg=1.05, fx=12, bx=23.5, top=21, neck=((12, 18), (9.5, 14), 2.7),
                  head=(9, 12.5, 4.1, 3.6), snout=((6.5, 13.8), (1.8, 15), (1.8, 0.9))),
    "cat":   dict(body=(19, 21, 8.2, 4.2), leg=1.2, fx=13, bx=24.5, top=23, neck=((13, 20), (10.5, 17), 2.8),
                  head=(9, 15.5, 4.7, 4.3), snout=((6, 17), (4.2, 17.3), (1.7, 1.4))),
    "bear":  dict(body=(19, 19.5, 9.5, 6.4), leg=2.2, fx=12.5, bx=25, top=22, neck=((12.5, 18), (10, 17.5), 4.0),
                  head=(8, 17.5, 4.6, 4.2), snout=((5, 19), (2.4, 19.6), (2.0, 1.5))),
    "low":   dict(body=(19.5, 21.5, 8.5, 4.8), leg=1.3, fx=13.5, bx=25, top=24, neck=((13.5, 21), (11, 20.5), 3.2),
                  head=(8.5, 20.5, 4.1, 3.6), snout=((6, 21.8), (1.8, 23), (1.8, 0.8))),
}


def quad(s: Sprite, fur, light=WHITE, *, build="dog", ears="point", ear_in=PINK, tail="bushy",
         tail_col=None, tail_tip=None, nose=NOSE, muzzle=None, head=None, legs=None, feet=None,
         belly=True, eye_col=EYE, markings=None, behind=None, front=None):
    """Side view of a four-legged animal walking left. `build` sets the proportions;
    behind, markings and front are called with (s, build dict) to add patterns, horns
    and antlers at the right places."""
    b = BUILDS[build]
    s.can("walk", "eat")
    if s.act == "eat":
        # Grazing (or sniffing the ground): the head comes down to the grass and
        # nibbles; the neck reaches down to it. Antlers and markings that place
        # themselves by b["head"] follow it down.
        b = dict(b)
        hx0, hy0, hrx0, hry0 = b["head"]
        ny = 30.5 - hry0 - 1.6 - s.cyc(0, 0.7, 0, 0.7)
        dx, dy = -1.0, ny - hy0
        b["head"] = (hx0 + dx, ny, hrx0, hry0)
        (sx0, sy0), (sx1, sy1), sr = b["snout"]
        b["snout"] = ((sx0 + dx, sy0 + dy), (sx1 + dx + 1.0, sy1 + dy + 1.0), sr)
        (n0, (nx1, ny1), nr) = b["neck"]
        b["neck"] = (n0, (nx1 + dx, ny1 + dy * 0.85), nr)
    w = s.wave() if s.act == "walk" else 0
    lying = s.act == "sleep"
    head = head or fur
    legs = legs or fur
    tail_col = tail_col or fur
    muzzle = muzzle or light
    far = lambda c: mix(c, "#1a1420", 0.28)  # noqa: E731  (the legs and ear on the far side)
    bx, by, brx, bry = b["body"]
    hx, hy, hrx, hry = b["head"]
    ground = 30.5
    if behind:
        behind(s, b)

    # Diagonal gait: near front leg moves with the far back leg.
    if not lying:
        for x, back, sw in ((b["fx"] + 2.2, False, -w), (b["bx"] + 1.6, True, w)):
            _leg(s, x, b["top"], ground, b["leg"], far(legs), back, build, far(feet) if feet else None, sw)
    tw = w if s.act == "walk" else 0.6 * s.wave() if s.act == "idle" else 0  # an idle tail swishes
    _tail(s, tail, bx + brx - 1, by - bry * 0.3 + 0.8 * tw, tail_col, tail_tip)
    ear_x = hx + (0.8 if build == "bear" else 2.6)
    _side_ear(s, ears, ear_x - 1, hy - hry + 0.6, far(head), None)

    if not lying:
        for x, back, sw in ((b["fx"], False, w), (b["bx"], True, -w)):
            _leg(s, x, b["top"], ground, b["leg"], legs, back, build, feet, sw)
    breath = 0.35 * max(0, s.wave()) if lying else 0
    body = s.ellipse(bx, by, brx + breath, bry + breath, fur)
    if build == "bear":
        s.ellipse(bx - 3.5, by - bry + 1.5, 4.5, 2.6, fur)  # shoulder hump
    if belly:
        # a pale underside, left unshaded so it doesn't read as a stripe
        s.fill(s.m_ellipse(bx - 0.5, by + bry * 0.95, brx * 0.8, bry * 0.5) & body, light, shade=False)
    (nx0, ny0), (nx1, ny1), nr = b["neck"]
    s.path([(nx0, ny0), (nx1, ny1)], nr, fur)
    if belly and build in ("dog", "sheep"):
        s.paint(s.m_path([(nx0 - 1.2, ny0 + 1.5), (nx1 - 1.5, ny1 + 1.8)], nr * 0.55), light, within=s.last)

    hm = s.ellipse(hx, hy, hrx, hry, head, edge=True)
    (sx0, sy0), (sx1, sy1), (sr0, sr1) = b["snout"]
    sm = s.path([(sx0, sy0), (sx1, sy1)], (sr0, sr1), head)
    jaw = s.m_path([(sx0, sy0 + sr0 * 0.6), (sx1 + 0.5, sy1 + sr1 * 0.5)], (sr0 * 0.6, sr1 * 0.55))
    s.paint(jaw | s.m_ellipse(hx - 1, hy + hry * 0.7, hrx * 0.6, hry * 0.35), muzzle, within=sm | hm)
    if markings:
        markings(s, b)
    _side_ear(s, ears, ear_x, hy - hry + 0.8, head, ear_in)
    ny = round(sy1 - sr1 + 0.3)
    s.px([(round(sx1 - sr1 + 0.4), ny), (round(sx1 - sr1 + 1.4), ny)], nose)
    ex, ey = round(hx - hrx * 0.45), round(hy - hry * 0.45)
    s.eye(ex, ey, color=eye_col)
    if front:
        front(s, b)
    if lying:
        # Lie down: drop onto the ground and tuck the front paws in under the chin.
        s.shift(0, round(ground - 0.5 - (by + bry)))
        paw = feet or mix(legs, "#1a1420", 0.1)
        for dx in (0, 3.5):
            s.ellipse(b["fx"] - 2.5 + dx, ground - 1.2, 2.4, 1.3, paw)
    elif s.act == "walk":
        _lift(s, 0.5 + 0.5 * math.cos(4 * math.pi * s.t))  # up as the legs pass


def _leg(s: Sprite, x, top, ground, r, col, back, build, feet, swing=0.0):
    """swing -1..1 moves the foot back or forward; a forward-swinging foot lifts."""
    fx = x - swing * 2.2
    lift = 1.2 * max(0.0, swing)
    if back and build in ("deer", "dog", "cat", "sheep"):
        # back legs bend at the hock
        pts = [(x, top - 1), (x + 1.4 - swing * 0.8, top + (ground - top) * 0.45), (fx + 0.4, ground - 0.8 - lift)]
    else:
        pts = [(x, top - 1), (fx - 0.2, ground - 0.8 - lift)]
    ground -= lift
    m = s.path(pts, (r * 1.35, r * 0.9) if build != "bear" else r, col)
    if feet:
        s.paint(s.m_ellipse(pts[-1][0] - 0.3, ground - 0.9, r + 0.6, 1.3), feet, within=m)
    if build in ("bear", "low", "cat"):
        s.ellipse(pts[-1][0] - 0.8, ground - 0.9, r + 0.9, 1.0, feet or col)


def _side_ear(s: Sprite, kind, x, y, fur, inner):
    shade = inner is not None
    if kind in ("point", "big", "tuft"):
        h = {"point": 4.2, "big": 5.6, "tuft": 4.4}[kind]
        s.poly([(x - 2, y + 1.5), (x + 0.6, y - h), (x + 2.2, y + 1.2)], fur, shade=shade)
        if inner:
            s.poly([(x - 0.8, y + 0.8), (x + 0.5, y - h + 2), (x + 1.2, y + 0.8)], inner, shade=False)
        if kind == "tuft":
            s.px([(round(x + 0.6), round(y - h - 1)), (round(x + 0.6), round(y - h - 2))], BLACK)
    elif kind in ("round", "small"):
        r = 2.2 if kind == "round" else 1.6
        s.ellipse(x, y - 0.5, r, r, fur, shade=shade)
        if inner:
            s.ellipse(x - 0.2, y - 0.3, r * 0.5, r * 0.5, inner, shade=False)
    elif kind in ("mule", "side"):
        rx, ry = (4.2, 2.2) if kind == "mule" else (3.0, 1.6)
        s.ellipse(x + 1.5, y + 0.5, rx, ry, fur, rot=-35, shade=shade)
        if inner:
            s.ellipse(x + 1.7, y + 0.4, rx * 0.6, ry * 0.45, inner, rot=-35, shade=False)


def _tail(s: Sprite, kind, x, y, col, tip):
    if kind == "bushy":
        m = s.path([(x - 1, y + 1), (x + 3, y + 2.5), (x + 4.8, y + 6), (x + 4.4, y + 9)], (1.6, 2.5), col)
        if tip:
            s.paint(s.m_ellipse(x + 4.6, y + 9.4, 2.4, 2.0), tip, within=m)
    elif kind == "long":
        m = s.path([(x - 1, y + 1), (x + 3, y + 2), (x + 5, y - 2), (x + 4.4, y - 6)], (1.2, 1.0), col)
        if tip:
            s.paint(s.m_ellipse(x + 4.4, y - 6, 1.6, 2.0), tip, within=m)
    elif kind == "short":
        m = s.ellipse(x + 1.2, y + 0.5, 1.8, 1.3, col, rot=-30)
        if tip:
            s.paint(s.m_ellipse(x + 2.4, y - 0.2, 0.9, 0.9), tip, within=m)
    elif kind == "cotton":
        s.ellipse(x + 1, y + 0.5, 1.6, 1.8, col)
        if tip:
            s.paint(s.m_ellipse(x + 0.6, y + 1.6, 1.4, 1.0), tip, within=s.last)
    elif kind == "ringed":
        m = s.path([(x - 1, y + 2), (x + 3, y + 3), (x + 5, y + 6), (x + 5.4, y + 10)], (2.0, 1.6), col)
        for k in (2.5, 5.5, 8.5):
            s.paint(s.m_poly([(x, y + k), (x + 8, y + k - 1.5), (x + 8, y + k + 0.2), (x, y + k + 1.7)]), tip or BLACK, within=m)
    elif kind == "skunk":
        m = s.path([(x - 1, y + 2), (x + 2, y - 2), (x + 3.4, y - 8), (x + 1.4, y - 13)], (2.8, 3.6), col)
        s.paint(s.m_path([(x + 0.4, y - 1), (x + 1.8, y - 7), (x + 0.6, y - 12)], (0.9, 1.6)), tip or WHITE, within=m)
    elif kind == "rat":
        s.path([(x - 1, y + 2), (x + 3, y + 4), (x + 5.5, y + 3), (x + 6.5, y)], (1.1, 0.5), col)

def pinniped(s: Sprite, fur, light, *, spots=None, ears=False, proboscis=None, whisker=None,
             flipper=None, belly=True, upright=None, blotch=None):
    """Seal or sea lion from the side, facing left. Seals lie along the ground with
    the head raised; sea lions (ears=True) prop themselves up on their front flippers.
    Walking humps the body along, swimming stretches it out and beats the hind
    flippers. look and back turn the head to you or over the shoulder. Seals also
    rest in the "banana" pose (the sit row): head and hind flippers both held up."""
    s.can("walk", "swim", "look", "back")
    act, f = s.act, s.f
    upright = ears if upright is None else upright
    if not upright:
        s.can("sit")
    flipper = flipper or mix(fur, "#000000", 0.25)
    view = {"look": "front", "back": "back"}.get(act, "side")
    ground = 30.5
    swim = act == "swim"
    w = s.wave() if act in ("walk", "swim") else 0
    hump = s.cyc(0, 1.6, 0.6, -0.4) if act == "walk" else 0
    if swim:
        # stretched out and rippling, the neck arched and the head held up out of the
        # water (not level like a fish), hind flippers sweeping side to side
        spine = [(28.5, 21.5 + w), (22, 20 - 0.5 * w), (14.5, 18.6), (9.5, 16)]
        rad = (1.6, 4.0)
        head = (6.5, 11.5 + 0.4 * w, 3.3, 2.8)
    elif act == "sit":
        # banana: belly on the ground, both ends curled up (the tail end bobs a little)
        lift = s.cyc(0, 0.5, 1, 0.5)
        spine = [(28, 23 - lift), (23.5, 27.6), (16, 28.6), (9.5, 26.6)]
        rad = (1.8, 4.0)
        head = (6, 20.5, 3.4, 2.9)
    elif act == "sleep":
        spine = [(28.5, 28.6), (21, 27.2), (13, 26.8), (8, 27.4)]
        rad = (1.8, 4.0)
        head = (5.5, 27.2, 3.3, 2.8)
    elif upright:
        spine = [(28.5, 28.4), (22, 27.2 - hump), (15.5, 25.5), (11.5, 21.5)]
        rad = (1.8, 4.0)
        head = (9, 14.5, 3.0, 2.6)
    else:
        spine = [(28.5, 28.4), (21, 27 - hump), (13, 26.4), (8.5, 25)]
        rad = (1.8, 4.2)
        head = (6.2, 21.5, 3.4, 2.9)
    hx, hy, hrx, hry = head
    if act == "back":
        hx += 2.5

    # hind flippers: a fan behind the tail, beating when it swims
    tx, ty = spine[0]
    beat = 2.4 * w if swim else 3.0 if act == "sit" else 0
    s.poly([(tx - 1, ty - 0.8), (tx + 4.2, ty - 2.6 - beat), (tx + 3.4, ty - 0.2 - beat * 0.6)], flipper)
    s.poly([(tx - 1, ty + 0.4), (tx + 4.2, ty + 1.8 - beat), (tx + 3.0, ty - 0.2 - beat * 0.6)],
           mix(flipper, "#1a1420", 0.2))
    # far front flipper
    fx, fy = spine[-2][0] - 1, spine[-2][1] + 1.5
    if upright and not swim and act != "sleep":
        s.path([(fx + 1.5, fy - 1), (fx + 2.6, ground - 0.4)], (1.4, 1.0), mix(flipper, "#1a1420", 0.25))

    body = s.path(spine, rad, fur)
    neck = s.path([spine[-1], (hx + 1, hy + 1)], (3.6, 2.2) if upright else 3.2, fur)
    body = body | neck
    if belly:
        s.paint(s.m_path([(x - 0.5, y + 2.6) for x, y in spine[1:]], rad[1] * 0.45), light, within=body)
    if spots:
        k = 0
        for x in range(4, 30):
            for y in range(10, 31):
                if body[idx(x, y)] and (x * 7 + y * 13) % 11 == 0 and k < spots:
                    s.paint(s.m_px([(x, y)]), mix(fur, "#000000", 0.4))
                    k += 1
    if blotch:
        blotch(s, body)

    # near front flipper
    if swim:
        s.ellipse(fx + 0.5 + 0.8 * w, fy + 3.6 - 0.6 * w, 3.4, 1.2, flipper, rot=35 + 25 * w)  # a breast stroke
    elif act == "sleep":
        s.ellipse(fx + 1, ground - 0.8, 2.8, 1.0, flipper, rot=10)
    elif upright:
        s.path([(fx, fy - 1.5), (fx - 0.8 + 0.8 * w, ground - 0.5)], (1.6, 1.1), flipper)
        s.ellipse(fx - 1.6 + 0.8 * w, ground - 0.5, 2.0, 0.8, flipper)
    else:
        s.ellipse(fx + 0.5, ground - 0.9 + 0.3 * hump, 2.6, 1.1, flipper, rot=25)

    # head
    if view == "front":
        cx = hx + 0.6
        hm = s.ellipse(cx, hy, hrx * 1.05, hry * 1.05, fur, edge=True)
        s.ellipse(cx, hy + hry * 0.55, 2.0, 1.3, light, shade=False)
        if proboscis:
            s.ellipse(cx, hy + 1.2, 1.4, 2.2, proboscis)
        if ears:
            s.px([(round(cx - hrx), round(hy - 0.5)), (round(cx + hrx - 1), round(hy - 0.5))], flipper)
        ey = round(hy - hry * 0.3)
        for x in (round(cx - hrx * 0.5 - 0.8), round(cx + hrx * 0.5 - 0.6)):
            s.eye(x, ey, size=2)
        s.px([(round(cx - 0.5), round(hy + hry * 0.3))], NOSE)
        s.px([(round(cx - 2.5), round(hy + hry * 0.7)), (round(cx + 1.5), round(hy + hry * 0.7))],
             whisker or mix(light, "#000000", 0.35))
        return
    d = 1 if view == "back" else -1
    long_nose = 3.6 if proboscis else 2.6 if upright else 3.0
    tip = (hx + d * (hrx + long_nose - 1.2), hy + 1.0)
    hm = s.ellipse(hx, hy, hrx, hry, fur, edge=True)
    sm = s.path([(hx + d * 1.2, hy + 0.6), tip], (2.2, 1.4), fur)
    s.paint(s.m_path([(hx + d * 1.2, hy + 1.8), (tip[0] - d * 0.4, tip[1] + 0.8)], (1.2, 0.9)), light, within=hm | sm)
    if proboscis:
        s.path([(tip[0] - d * 1.2, tip[1] - 1), (tip[0] + d * 0.6, tip[1] + 0.4), (tip[0] + d * 0.4, tip[1] + 2.8)],
               (1.4, 1.2), proboscis)
    else:
        s.px([(round(tip[0] + d * 0.6), round(tip[1] - 0.8))], NOSE)
    s.px([(round(tip[0] - d * 1.5), round(tip[1] + 0.6))], whisker or mix(light, "#000000", 0.35))
    if ears:
        s.px([(round(hx - d * 1.8), round(hy - 1)), (round(hx - d * 1.8), round(hy))], flipper)
    ex = round(hx + d * hrx * 0.25 - (d < 0))
    ey = round(hy - hry * 0.4)
    s.eye(ex, ey, size=2)


def _fluke(s: Sprite, pts, col, w, pivot_x=24):
    """A tail fin that beats up and down around where it joins the body."""
    return s.poly([(x, y - w * 2.5 * max(0.0, (x - pivot_x)) / 7) for x, y in pts], col)


def whale(s: Sprite, body, belly, *, flipper=WHITE):
    s.can("swim")
    w = s.wave() if s.act == "swim" else 0
    if s.act != "sleep":
        s.px([(6, 2 - (s.f % 2)), (8, 1), (10, 2), (7, 4), (9, 4), (8, 6)], "#8fd3ff")
    _fluke(s, [(25, 15), (31, 9), (30, 15), (31, 21)], body, w)
    s.ellipse(14, 17, 12, 7.5, body, edge=True)
    m = s.ellipse(13, 21, 9.5, 3.5, belly)
    for x in range(6, 21, 3):
        s.paint(s.m_line(x, 19, x + 1, 24), mix(belly, body, 0.4), within=m)
    s.ellipse(15, 24, 7, 1.8, flipper, rot=20)
    s.px([(3, 14), (5, 13), (4, 15), (9, 12), (10, 11)], mix(body, WHITE, 0.4))
    s.eye(6, 16)


# --------------------------------------------------------------------------- birds
def _smooth(t):
    t = np.clip(t, 0.0, 1.0)
    return t * t * (3 - 2 * t)


def _slim(s: Sprite, head_c, head_to, head_k, body_c, body_to, body_kx, body_ky, body_bottom, neck,
          tilt=0.0, beak_k=1.0):
    """Re-proportion a bird drawn in a plan's chubby coordinates: the head (around
    head_c) shrinks by head_k and moves to head_to; the body (around body_c) stretches
    by body_kx and flattens by body_ky to body_to; the legs below body_bottom lengthen
    to keep the feet on the ground. neck = (x, y) where head and body blend. tilt drops
    the tail end (an upright hawk) or raises it; beak_k makes the beak, out in front of
    the head, bigger or smaller than the head around it."""
    hx, hy = head_c
    tx, ty = head_to
    bx, by = body_c
    ux, uy = body_to
    nx, ny = neck
    low = uy + body_ky * (body_bottom - by)  # where the body's bottom ends up
    front, root = hx - 4, hy + 1  # where the beak leaves the face
    def fwd(x, y):  # noqa: E306
        kb = _smooth((front - 1 - x) / 1.5)
        hxp = tx + head_k * (np.maximum(x, front) - hx) + head_k * (1 + kb * (beak_k - 1)) * np.minimum(x - front, 0)
        hyp = ty + head_k * (root - hy) + head_k * (1 + kb * (beak_k - 1)) * (y - root)
        bxp = ux + body_kx * (x - bx)
        lean = tilt * (x - bx)
        byp = np.where(y <= body_bottom, uy + body_ky * (y - by) + lean,
                       low + (y - body_bottom) * (31 - low) / (31 - body_bottom)
                       + lean * (31 - y) / (31 - body_bottom))
        # the beak, out in front of the head, always goes with the head
        k = np.maximum(_smooth((ny - y) / 2.5) * _smooth((nx - x) / 2.5), _smooth((hx - 4 - x) / 1.5))
        return k * hxp + (1 - k) * bxp, k * hyp + (1 - k) * byp
    s.set_warp(fwd)


# How each kind of bird is built, so a gull, a crow and a hawk read as themselves and not
# all as one pigeon: head size, where the head sits (x, and y above the body's middle),
# body length and depth, tilt (tail end down for upright perchers), beak size against the
# head, and how thick the neck is. First match on the slug wins; songbirds are the default.
BIRD_FORMS = [
    # pattern, head_k, head_x, head_dy, body_kx, body_ky, tilt, beak_k, neck
    (r"eagle", 0.76, 10.5, -8, 1.02, 0.86, 0.3, 1.3, 2.4),
    (r"hawk|kite|harrier|osprey", 0.74, 10.5, -8, 1.0, 0.82, 0.25, 1.35, 2.2),
    (r"gull|kittiwake|albatross|shearwater|booby|frigatebird", 0.72, 9.5, -6.5, 1.22, 0.7, 0.0, 1.6, 2.3),
    (r"tern|skimmer|tropicbird", 0.64, 9.5, -6, 1.22, 0.6, 0.0, 1.45, 2.0),
    (r"crow|raven|grackle|magpie|nutcracker|blackbird|cowbird|myna|starling", 0.78, 9.5, -6.5, 1.12, 0.74, 0.12, 1.5, 2.4),
    (r"jay", 0.74, 9.5, -7, 1.1, 0.74, 0.1, 1.2, 2.3),
    (r"dove|pigeon", 0.62, 10.5, -5.5, 1.06, 0.82, 0.0, 1.2, 2.2),
    (r"woodpecker|flicker|sapsucker|nuthatch", 0.76, 11.5, -8, 0.92, 0.84, 0.55, 1.55, 2.2),
    (r"puffin|murre|guillemot|murrelet", 0.84, 10.5, -8, 0.95, 0.88, 0.5, 1.35, 2.6),
    (r"killdeer|plover|dunlin|sanderling|willet|tattler|turnstone|oystercatcher|phalarope", 0.64, 10, -6, 1.1, 0.64,
     -0.05, 1.7, 1.9),
    (r"swallow|martin|swift", 0.7, 10, -6, 1.25, 0.6, 0.0, 0.7, 2.2),
    (r"kingfisher", 0.9, 10, -7, 0.98, 0.76, 0.2, 1.5, 2.6),
    (r"anhinga", 0.55, 8, -9, 1.2, 0.62, 0.0, 1.5, 1.4),
]
SONGBIRD = (0.72, 10, -7, 1.08, 0.74, 0.0, 1.0, 2.2)


def _bird_form(slug):
    for pattern, *form in BIRD_FORMS:
        if re.search(rf"(?:^|_)(?:{pattern})(?:_|$)", slug):
            return form
    return SONGBIRD


def bird(s: Sprite, body, belly, *, head=None, wing=None, tail_col=None, beak="cone",
         beak_col="#4a3d3a", legs="#c99060", tail="mid", crest=None, eye_col=EYE,
         face=None, wing_mark=None, belly_mark=None, big=False):
    """Side view, facing left. Walks on alternating legs and flies with its wing
    beating up and down (legs tucked). Drawn in round, roomy coordinates (which the
    species' own markings use too) and then re-proportioned: a smaller head held up on
    a short neck, a longer body, and longer legs. Pecking at the ground ("eat") it bends
    forward from the hips over its standing legs."""
    s.can("walk", "fly", "eat")
    if s.act == "eat":
        s.bend(48 * s.cyc(0.45, 1, 0.45, 1), 15.5, 25.5, 4)
    flying = s.act == "fly"
    w = s.wave()
    head = head or body
    wing = wing or mix(body, "#000000", 0.15)
    tail_col = tail_col or wing
    cy = 19 if not big else 18
    head_k, head_x, head_dy, body_kx, body_ky, tilt, beak_k, neck_r = _bird_form(getattr(s, "slug", ""))
    _slim(s, (11, 11), (head_x, cy + head_dy), head_k, (16.5, cy + 1), (17.5, cy + 3.5), body_kx, body_ky, cy + 8,
          (17.5, cy - 3), tilt=0.0 if flying else tilt, beak_k=beak_k)
    if flying and w > -0.5:
        with s.unwarped():
            _flight_wing(s, cy, w, mix(wing, "#1a1420", 0.3), dx=2.5)
    # Perched, the tail flicks up now and then (and dips back) like a real bird's.
    tb = -1.4 * (0.5 - 0.5 * math.cos(2 * math.pi * s.t)) ** 2 if s.act == "idle" else 0
    if tail == "mid":
        s.poly([(20, cy), (29, cy - 6 + tb), (31, cy - 3 + tb), (23, cy + 4)], tail_col)
    elif tail == "long":
        s.poly([(20, cy), (30, cy - 12 + tb), (32, cy - 9 + tb), (23, cy + 4)], tail_col)
    elif tail == "short":
        s.poly([(20, cy), (27, cy - 3 + tb), (28, cy + 1 + tb), (22, cy + 4)], tail_col)
    elif tail == "fan":
        s.poly([(20, cy), (29, cy - 9 + tb), (31, cy - 1 + tb), (23, cy + 4)], tail_col)
    if not flying:
        _bird_legs(s, (13, 17), 25, 29, legs, w if s.act == "walk" else 0)
    rb = 8.5 if big else 8
    s.ellipse(16.5, cy + 1, rb, 7, body)
    s.ellipse(13.5, cy + 3, 5.5, 4.5, belly)
    if belly_mark:
        belly_mark(s, s.last)
    if flying:
        with s.unwarped():
            _flight_wing(s, cy, w, wing)
    else:
        s.ellipse(20, cy, 5.8, 4.2, wing, rot=-15, edge=True)
    if wing_mark:
        wing_mark(s, s.last)
    # a smooth neck from the shoulders up to the head, so the two don't just meet
    with s.unwarped():
        sx, sy = s._to(12.5, cy - 1)
        hx, hy = s._to(11, 12.5)
        s.path([(sx, sy), (hx, hy)], neck_r, head)
    if crest == "jay":
        s.poly([(12, 6), (17, -1), (17, 7)], head)
    elif crest == "quail":
        s.path([(11, 6), (10, 2), (8, 1)], (0.9, 1.2), BLACK, shade=False)
    elif crest == "roadrunner":
        s.poly([(12, 6), (19, 1), (17, 7)], head)
    elif crest == "sparrow":
        pass
    s.ellipse(11, 11, 6.5, 6, head, edge=True)
    if face:
        face(s)
    _beak(s, "dove" if re.search(r"dove|pigeon", getattr(s, "slug", "")) else beak, beak_col)
    s.eye(8, 10, color=eye_col, shine=None)


def _lerp_pts(a, b, k):
    return [(x0 + (x1 - x0) * k, y0 + (y1 - y0) * k) for (x0, y0), (x1, y1) in zip(a, b)]


# The flight wing at the top of the beat, spread level and at the bottom: the same
# eight points (shoulder, leading edge, tip at index 4, trailing edge) so the frames
# in between blend from one to the next instead of snapping.
_WING_UP = [(14, 0), (15, -6), (17, -12), (20, -17), (23.5, -20), (24, -15), (23.5, -7), (22, 0)]
_WING_LEVEL = [(13, -0.5), (16, -2), (20, -2.8), (25, -3), (30, -1.5), (25, 0.5), (21, 1.2), (18, 1.5)]
_WING_DOWN = [(14, 1), (14.5, 4), (15, 6), (17, 11), (19.5, 13.5), (21, 10), (21.5, 5), (22, 1)]
# Plunging: folded back tight along the body, tips past the tail.
_WING_TUCK = [(13, -0.5), (16, -2.2), (20, -3), (25, -3.2), (31, -2.5), (26, -1), (21, 0.2), (17, 0.8)]


def _flight_wing(s: Sprite, cy, w, col, dx=0, tip=None):
    """A long, pointed wing through the beat: raised high (w=1), spread level along the
    body (0) and swept down below it (-1), blending smoothly in between. In canvas
    coordinates (after the bird is slimmed)."""
    y = cy + 2  # the shoulder
    k = abs(w) ** 1.3
    src = _WING_TUCK if getattr(s, "diving", False) else _lerp_pts(_WING_LEVEL, _WING_UP if w >= 0 else _WING_DOWN, k)
    pts = [(x + dx, y + py) for x, py in src]
    m = s.poly(pts, col, edge=not dx)
    if not dx:  # darker flight feathers toward the tip
        mid = ((pts[2][0] + pts[6][0]) / 2, (pts[2][1] + pts[6][1]) / 2)
        s.paint(s.m_poly([pts[3], pts[4], pts[5], mid]), tip or mix(col, "#1a1420", 0.22), within=m)
    return m


def _bird_legs(s: Sprite, xs, top, ground, col, w, toes=(-2, -1, 1), toe_dy=0):
    """Two thin legs with feet (two toes forward, one back); when walking, one lifts
    and steps forward at a time."""
    for i, x in enumerate(xs):
        step = max(0.0, w if i == 0 else -w)
        foot = ground - round(step * 1.5)
        fx = x - round(step * 1.5)
        s.line(x, top, fx, foot, col)
        s.px([(fx + t, foot + toe_dy) for t in toes], col)


# A big bird's broad wing through the beat, relative to its shoulder (facing left):
# raised high, spread back level along the body, and swept down below it. The same
# eleven points in each (leading edge, the fingered tip at 4..6, the trailing edge),
# so every frame in between is a real blend of the stroke.
_BIG_UP = [(0, 0), (0.5, -4), (2, -8), (4.5, -11.5), (8, -14.5), (10, -15), (10.5, -13), (9, -9.5), (7.5, -5.5),
           (6.5, -2.5), (6, 0)]
_BIG_LEVEL = [(-1, 0), (2, -1.5), (6, -2.2), (10, -2.4), (13, -2.2), (15.5, -1.4), (16, -0.4), (14, 0.5), (10, 1.1),
              (6.5, 1.3), (3.5, 1.2)]
_BIG_DOWN = [(0, 1), (1, 4), (2.5, 7.5), (4.5, 10.5), (7, 12.5), (8.5, 12.8), (9, 11), (8.5, 8), (8, 5), (7, 2.5),
             (6, 1)]


# Plunging: the wing folded back tight along the body, its tip past the tail.
_BIG_TUCK = [(-1, 0), (2, -1.3), (5.5, -2), (9.5, -2.4), (13.5, -2.4), (17, -1.8), (17.5, -0.8), (14, 0.2), (10, 0.8),
             (6, 1), (3, 1)]


def _big_wing_pts(sx, sy, w, size=1.0, tuck=False):
    k = abs(w) ** 1.2
    pts = _BIG_TUCK if tuck else _lerp_pts(_BIG_LEVEL, _BIG_UP if w >= 0 else _BIG_DOWN, k)
    return [(sx + x * size, sy + y * size) for x, y in pts]


def _big_wing(s: Sprite, sx, sy, w, col, *, size=1.0, tip=None, coverts=None, far=False):
    """A broad wing from the shoulder (sx, sy): pale coverts along the leading edge,
    darker flight feathers toward the tip. far=True draws the dim far wing (only
    while it shows above the body)."""
    pts = _big_wing_pts(sx, sy, w, size, tuck=getattr(s, "diving", False))
    if far:
        return s.poly([(x + 2, y - 0.5) for x, y in pts], mix(col, "#1a1420", 0.32))
    m = s.poly(pts, col, edge=True)
    tip = tip or mix(col, "#1a1420", 0.25)
    # the primaries: the outer part of the wing, from the bend to the tip
    s.paint(s.m_poly([pts[3], pts[4], pts[5], pts[6], pts[7], (pts[3][0] * 0.4 + pts[7][0] * 0.6,
                                                              pts[3][1] * 0.4 + pts[7][1] * 0.6)]), tip, within=m)
    # a line of coverts along the leading edge, catching the light
    s.paint(s.m_path(pts[0:4], 0.7), coverts or mix(col, "#ffffff", 0.2), within=m)
    return m


def _ell_lerp(a, b, k):
    """Blend two ellipses (cx, cy, rx, ry, rot), turning the shorter way round."""
    out = [p + (q - p) * k for p, q in zip(a[:4], b[:4])]
    d = (b[4] - a[4] + 90) % 180 - 90
    return out + [a[4] + d * k]


def _wing_beat(s: Sprite, x, y, w, col, size=1.0):
    """The near wing through a beat: raised (w=1), spread level (0) and swept down (-1).
    (x, y) is the middle of the folded wing; it beats from the shoulder in front of it."""
    return _big_wing(s, x - 6 * size, y, w, col, size=1.05 * size)


def _far_wing(s: Sprite, x, y, w, col, size=1.0):
    """The far wing, darker and behind the body, peeking out when raised or level."""
    if w < -0.35:
        return
    _big_wing(s, x - 7 * size, y, w, col, size=1.05 * size, far=True)


def flying_waterbird(s: Sprite, *, body, belly, wing, tip=None, tail, neck, neck_col, head, head_col,
                     head_r=(3.2, 2.8), cy=18, body_r=(8.5, 4), legs=None, size=1.0, coverts=None):
    """A big bird in flight, side on and level: the far wing, the body (belly paler
    below), the tail, the neck (a list of points, thick to thin) and the head at
    `head`, then the near wing, with legs trailing behind for herons. The body rides
    up a touch on each downstroke. The caller adds the bill, eye and markings at the
    head and should call s.shift(0, bob) last (the bob is returned)."""
    w = s.wave()
    bx, by = 18, cy
    _big_wing(s, bx - 4, by - 1.5, w, wing, size=size, far=True)
    if legs:
        s.line(bx + body_r[0] - 2, by + 1, 31, by + 1.5, legs)
        s.line(bx + body_r[0] - 2, by + 2, 31, by + 3, legs)
    s.poly([(bx + body_r[0] - 2, by - 1.5), (31, by - 1), (31, by + 1.5), (bx + body_r[0] - 2, by + 2)], tail)
    b = s.ellipse(bx, by, body_r[0], body_r[1], body)
    s.fill(s.m_ellipse(bx - 1.5, by + body_r[1] * 0.7, body_r[0] * 0.75, body_r[1] * 0.45) & b, belly, shade=False)
    s.path(neck, (2.4 * size, 1.8 * size), neck_col)
    hm = s.ellipse(head[0], head[1], head_r[0], head_r[1], head_col, edge=True)
    _big_wing(s, bx - 4, by - 1.5, w, wing, size=size, tip=tip, coverts=coverts)
    return hm, round(0.6 * w)


def _ripples(s: Sprite, k, pts=((2, 29), (4, 30), (27, 30), (29, 29), (8, 30), (22, 30))):
    """Little water marks around a swimming bird, drifting back as it paddles."""
    s.px([((x + k) % 32, y) for x, y in pts], "#8fd3ff")


def _beak(s: Sprite, kind, c):
    if kind == "cone":
        s.poly([(5.5, 10), (2, 11.8), (5.5, 13.5)], c)
    elif kind == "thin":
        s.poly([(5.5, 10.5), (1, 11.8), (5.5, 13)], c)
    elif kind == "hook":
        s.poly([(6, 9.5), (2.2, 10.5), (2.2, 14), (5.5, 13.5)], c)
        s.px([(2, 13)], mix(c, "#000000", 0.4))
    elif kind == "crow":
        s.poly([(6, 9.5), (0.5, 11.5), (6, 13.8)], c)
    elif kind == "long":
        s.poly([(6, 10.5), (-1, 12.5), (6, 13.5)], c)
    elif kind == "needle":
        s.line(4, 12, 0, 13, c)
        s.px([(5, 12)], c)
    elif kind == "duck":
        s.ellipse(3, 12.5, 3.2, 1.8, c)
    elif kind == "dove":  # a slim bill with the pale fleshy cere at its base
        s.poly([(5.6, 10.6), (0, 11.8), (0.3, 12.7), (5.6, 13)], c)
        s.fill(s.m_ellipse(4.4, 11.2, 1.3, 0.8), mix(c, "#f4ece4", 0.55), shade=False)


def owl(s: Sprite, body, face, *, tufts=False, eye_col="#f6c33c", belly=None, beak="#e8c070",
        disk_edge=None, bars=None, streaks=None, spots=None, throat=None, brows=None, long_legs=False, front=None):
    """An owl perched upright in profile; it flies in profile too (see _owl_flying), turns
    its head right round to look behind, and faces you when it looks at you, which
    front(s) can mark. bars/streaks cross or run down the breast, spots dot the wings,
    throat is a pale throat patch, brows pale eyebrows; long_legs for a burrowing owl."""
    s.can("fly", "look", "back")
    belly = belly or mix(body, WHITE, 0.4)
    if s.act == "fly":
        return _owl_flying(s, body, face, belly, tufts, eye_col, beak, bars)
    if s.act == "look":
        _owl_front(s, body, face, tufts, eye_col, belly, beak, disk_edge, bars)
        if front:
            front(s)
        return
    wc = mix(body, "#000000", 0.15)
    lift = 4 if long_legs else 0
    if long_legs:
        for x in (14, 17):
            s.line(x, 26, x, 30, "#c8b890")
            s.px([(x - 1, 30), (x - 2, 30)], "#c8b890")
    else:
        s.px([(13, 30), (14, 30), (16, 30), (17, 30)], "#b88a4a")  # talons on the branch
    s.poly([(18, 25 - lift), (25, 31 - lift), (21, 31 - lift), (17, 27 - lift)], wc)  # tail
    m = s.ellipse(16, 21 - lift, 6.5, 8.5, body, rot=-8)
    br = s.paint(s.m_ellipse(12.8, 22.5 - lift, 3.6, 6.8, rot=-8), belly, within=m)
    if bars:
        for y in range(18 - lift, 29 - lift, 2):
            s.paint(s.m_line(9, y, 16, y), bars, within=br)
    if streaks:
        for x, y in ((11, 20), (13, 22), (11, 25), (14, 26), (12, 28)):
            s.paint(s.m_line(x, y - lift, x, y + 1 - lift), streaks, within=br)
    wm = s.ellipse(18.5, 21 - lift, 4.8, 7.8, wc, rot=-12, edge=True)  # the folded wing
    for i, y in enumerate(range(17 - lift, 28 - lift, 3)):
        s.paint(s.m_line(16 + i % 2, y, 21, y + 1), mix(wc, "#000000", 0.18), within=wm)
    if spots:
        s.paint(s.m_px([(17, 17 - lift), (20, 19 - lift), (18, 22 - lift), (21, 24 - lift), (17, 26 - lift),
                        (14, 7 - lift), (17, 9 - lift), (16, 5 - lift)]), spots)
    back = s.act == "back"
    hx = 15 if back else 14
    if tufts:
        s.poly([(hx - 2.5, 6 - lift), (hx - 2, 0.5 - lift), (hx + 0.5, 5 - lift)] if not back else
               [(hx + 2.5, 6 - lift), (hx + 2, 0.5 - lift), (hx - 0.5, 5 - lift)], body)
    s.ellipse(hx, 10 - lift, 6.6, 6, body, edge=True)
    # the facial disk, the eye and the hooked beak, at the front (or over the back)
    fx = hx + 4 if back else hx - 4
    s.ellipse(fx, 10.5 - lift, 3.4, 4.6, face, shade=False)
    if disk_edge:
        s.paint(s.m_ellipse(fx, 10.5 - lift, 3.6, 4.8) & ~s.m_ellipse(fx, 10.5 - lift, 2.7, 3.9), disk_edge)
    ex = fx + 1 if back else fx - 2
    if throat:
        s.ellipse(fx + (1 if back else -1), 16 - lift, 2.6, 1.3, throat, shade=False)
    if brows:
        s.paint(s.m_line(ex - 1, 8 - lift, ex + 2, 8 - lift), brows)
    if eye_col:
        s.px([(ex, 9 - lift), (ex + 1, 9 - lift), (ex, 10 - lift), (ex + 1, 10 - lift)], eye_col)
        s.px([(ex + back, 10 - lift)], EYE)  # the pupil looks the way the face points
    else:
        s.px([(ex, 9 - lift), (ex + 1, 9 - lift), (ex, 10 - lift), (ex + 1, 10 - lift)], EYE)
        s.px([(ex, 9 - lift)], WHITE)
    s.eye_box(ex, 9 - lift, ex + 1, 10 - lift)
    if back:
        s.poly([(fx + 3, 11.5 - lift), (fx + 4.6, 13 - lift), (fx + 2.8, 14 - lift)], beak, shade=False)
    else:
        s.poly([(fx - 3, 11.5 - lift), (fx - 4.6, 13 - lift), (fx - 2.8, 14 - lift)], beak, shade=False)


def _owl_front(s: Sprite, body, face, tufts, eye_col, belly, beak, disk_edge, bars):
    """The owl turned to face you: as slim as it is side-on, wings folded at its sides."""
    if tufts:
        s.poly([(10, 7), (10, 1), (13.5, 5)], body, mirror=True)
    s.px([(13, 30), (14, 30)], "#b88a4a", mirror=True)
    s.ellipse(16, 21, 6.5, 9, body)
    s.ellipse(16, 23, 4, 6.2, belly)
    if bars:
        for y in range(18, 30, 2):
            s.paint(s.m_line(12, y, 20, y), bars, within=s.last)
    s.ellipse(10.5, 21.5, 2.2, 7, mix(body, "#000000", 0.18), rot=-6, mirror=True)
    s.ellipse(16, 10, 7, 6.3, body, edge=True)
    s.ellipse(13.2, 10.5, 3, 3.6, face, mirror=True, edge=disk_edge is not None)
    if eye_col:
        s.ellipse(13.2, 10.5, 1.7, 1.7, eye_col, mirror=True, shade=False)
        s.px([(13, 10), (13, 11)], EYE, mirror=True)
    else:
        s.px([(12, 10), (13, 10), (12, 11), (13, 11)], EYE, mirror=True)
        s.px([(12, 10)], WHITE, mirror=True)
    s.poly([(15, 12.5), (17, 12.5), (16, 15)], beak, shade=False)
    s.eye_box(12, 9, 14, 12, mirror=True)


def _owl_flying(s: Sprite, body, face, belly, tufts, eye_col, beak, bars):
    """An owl flying left in profile: a round head with the facial disk at the front,
    broad rounded wings beating slowly, legs tucked under a short tail."""
    w = s.wave()
    wc = mix(body, "#000000", 0.15)
    y = 18  # the shoulder

    def wing(dx, col):
        up = [(13, y), (13.5, y - 6), (16, y - 11), (20, y - 13.5), (23.5, y - 12), (24.5, y - 6), (23, y)]
        down = [(13, y + 1), (14, y + 6), (17, y + 10), (21, y + 10.5), (23, y + 7), (23, y + 4), (23, y + 1)]
        level = [(12, y - 1), (17, y - 3.5), (25, y - 4), (30, y - 2), (26, y + 1), (22, y + 1.6), (18, y + 2)]
        pts = _lerp_pts(level, up if w >= 0 else down, abs(w) ** 1.3)  # blended through the beat
        m = s.poly([(x + dx, yy) for x, yy in pts], col, edge=not dx)
        # the pale flight-feather tips
        s.paint(m & ~s.m_poly([(x + dx - 0.6 * (x > 18), yy + (0.8 if yy < y else -0.8)) for x, yy in pts]),
                mix(col, WHITE, 0.3), within=m)
    if w > -0.5:
        wing(2.5, mix(wc, "#1a1420", 0.3))
    s.poly([(23, 17), (29.5, 17.5), (29, 21), (23, 21)], wc)
    m = s.ellipse(17.5, 19.5, 7.5, 4.3, body, rot=-4)
    s.fill(s.m_ellipse(16.5, 21.5, 6, 2.2) & m, belly, shade=False)
    if bars:
        for x in range(12, 22, 2):
            s.paint(s.m_line(x, 20, x, 23), bars, within=m)
    s.ellipse(11, 22.5, 1.6, 1.0, "#b88a4a")  # feet tucked under
    if tufts:
        s.poly([(10, 13.5), (11.5, 9.5), (13, 13.5)], body)
    s.ellipse(10.5, 16.5, 4.4, 4.2, body, edge=True)
    s.ellipse(8.6, 16.8, 2.8, 3.4, face, shade=False)
    ex, ey = 7, 15
    if eye_col:
        s.px([(ex, ey), (ex + 1, ey)], eye_col)
        s.px([(ex, ey)], EYE)
    else:
        s.px([(ex, ey), (ex, ey + 1)], EYE)
    s.eye_box(ex - 1, ey - 1, ex + 2, ey + 2)
    s.poly([(6.2, 17), (4.6, 18.4), (6.2, 19.6)], beak, shade=False)
    wing(0, wc)


def wader(s: Sprite, body, *, neck=None, head=None, beak="#e8b830", legs="#3d3532", plume=None,
          cap=None, wing=None, curved=False, face=None):
    s.can("walk", "fly", "eat")
    if s.act == "eat":  # stabbing down at a fish
        s.bend(45 * s.cyc(0.3, 1, 0.3, 0.3), 19, 19.5, 3)
    flying = s.act == "fly"
    w = s.wave()
    neck = neck or body
    head = head or neck
    wc = wing or mix(body, "#000000", 0.12)
    if flying:
        # Herons and egrets fly with the neck folded back into an S and the legs
        # trailing; ibises (curved bills) stretch the neck straight out.
        hx, hy = (5, 16.5) if curved else (10, 14.5)
        npts = [(12, 18), (8, 17), (hx + 1, hy)] if curved else [(13, 17.5), (11, 18.5), (10.5, 16.5), (hx + 1, hy + 0.5)]
        hm, bob = flying_waterbird(s, body=body, belly=mix(body, "#ffffff", 0.12), wing=wc, tail=wc, neck=npts,
                                   neck_col=neck, head=(hx, hy), head_col=head, head_r=(2.8, 2.4), cy=18,
                                   body_r=(7.5, 3.6), legs=legs, size=1.15)
        if plume:
            s.path([(hx + 2, hy - 1.5), (hx + 6, hy - 1.5)], (0.8, 0.4), plume, shade=False)
        if cap:
            s.paint(s.m_ellipse(hx + 0.5, hy - 1.8, 2.6, 1.1), cap, within=hm)
        if face:
            s.paint(s.m_ellipse(hx - 2, hy, 1.5, 1.5), face, within=hm)
        if curved:
            s.path([(hx - 2, hy + 0.5), (hx - 5, hy + 1.5), (hx - 7, hy + 3.5)], (1.0, 0.5), beak, shade=False)
        else:
            s.poly([(hx - 2, hy - 1), (hx - 10, hy + 0.5), (hx - 2, hy + 1)], beak)
        s.eye(round(hx - 1.5), round(hy - 1))
        s.shift(0, bob)
        return
    if flying:  # legs trail out behind
        _far_wing(s, 22, 15, w, mix(wc, "#1a1420", 0.3))
        s.line(24, 17, 31, 19, legs)
        s.line(24, 18, 31, 21, legs)
    else:
        a, b = (max(0, w), max(0, -w)) if s.act == "walk" else (0, 0)
        s.line(18, 19, 17 - round(a * 2), 30 - round(a), legs)
        s.line(21, 19, 22 - round(b * 3), 30 - round(b), legs)
        s.px([(16 - round(a * 2), 30 - round(a)), (23 - round(b * 3), 30 - round(b))], legs)
    s.ellipse(20, 15, 7, 5, body)
    if flying:
        _wing_beat(s, 21, 14, w, wc)
    else:
        s.ellipse(22, 14, 5, 3.3, wc, rot=-10, edge=True)
    s.poly([(26, 14), (31, 17), (25, 18)], wing or mix(body, "#000000", 0.12))
    s.path([(15, 14), (13, 11), (14, 8), (11, 5)], 1.8, neck)
    if plume:
        s.path([(12, 3), (17, 2), (20, 3)], (1, 0.5), plume, shade=False)
    s.ellipse(10.5, 5, 4, 3.4, head, edge=True)
    if cap:
        s.paint(s.m_ellipse(11, 2.6, 3.5, 1.4), cap, within=s.last)
    if face:
        s.paint(s.m_ellipse(8, 5, 2, 2), face, within=s.last)
    if curved:
        s.path([(7, 6), (3, 7), (1, 10), (0.5, 12)], (1.1, 0.6), beak, shade=False)
    else:
        s.poly([(7, 4.5), (-1, 6.5), (7, 7)], beak)
    s.eye(8, 4)


def duck(s: Sprite, body, chest, head, *, bill="#f0c22a", ring=WHITE, speculum="#4a5fd0",
         tail_col=None):
    s.can("swim", "fly")
    flying = s.act == "fly"
    w = s.wave()
    if flying:  # neck stretched out in front, fast stiff wingbeats
        wc = mix(body, "#000000", 0.12)
        hm, bob = flying_waterbird(s, body=body, belly=mix(body, "#ffffff", 0.15), wing=wc, tail=tail_col or body,
                                   neck=[(11, 18.5), (7.5, 17)], neck_col=head, head=(5.5, 16), head_col=head,
                                   head_r=(3.2, 2.7), cy=19, body_r=(8, 4), size=0.95)
        s.ellipse(11, 19.5, 3.4, 3, chest)
        if ring:
            s.paint(s.m_ellipse(9, 18.4, 1, 1.8), ring)
        s.ellipse(1.5, 17, 2.4, 1.2, bill)
        s.eye(4, 15, shine=None)
        pts = _big_wing_pts(14, 17.5, w, 0.95)
        s.paint(s.m_path(pts[7:10], 0.8), speculum, within=s.last)  # the speculum on the trailing edge
        s.shift(0, bob)
        return
    _slim(s, (10, 11), (9.5, 13.5), 0.74, (17, 23), (17.5, 24), 1.04, 0.82, 29.5, (15, 17))
    if flying:
        _far_wing(s, 21, 20, w, mix(body, "#1a1420", 0.35))
    else:
        _ripples(s, s.t * 4 if s.act == "swim" else 0)
    s.poly([(24, 20), (30, 16), (29, 22)], tail_col or body)
    s.ellipse(17, 23, 11, 6.5, body)
    s.ellipse(10, 22, 5, 5, chest)
    if flying:
        m = _wing_beat(s, 20, 21, w, mix(body, "#000000", 0.12))
    else:
        m = s.ellipse(20, 21, 7, 3.5, mix(body, "#000000", 0.12), rot=-8, edge=True)
    s.paint(s.m_poly([(17, 22), (24, 21), (24, 23), (17, 24)]), speculum, within=m)
    s.ellipse(10, 11, 6, 5.5, head, edge=True)
    if ring:
        s.paint(s.m_ellipse(10, 16.8, 4, 1), ring)
    s.ellipse(3.5, 13, 3.4, 1.8, bill)
    s.eye(7, 10, shine=None)


def goose(s: Sprite):
    s.can("swim", "fly")
    flying = s.act == "fly"
    w = s.wave()
    if flying:  # the long black neck stretched straight out
        hm, bob = flying_waterbird(s, body="#9a8670", belly="#e2d8c8", wing="#6e5c4c", tip="#3e342c", tail=BLACK,
                                   neck=[(11, 18), (7, 16.5), (4, 15.5)], neck_col=BLACK, head=(2.5, 15),
                                   head_col=BLACK, head_r=(2.6, 2.1), cy=19, body_r=(9, 4.2), size=1.15)
        s.paint(s.m_ellipse(3.5, 16.2, 1.6, 0.9), WHITE, within=hm)  # the white chinstrap
        s.ellipse(-0.8, 15.4, 1.6, 0.9, BLACK)
        s.px([(1, 14)], "#000000")
        s.shift(0, bob)
        return
    _slim(s, (9.5, 7), (9.5, 8.5), 0.8, (19, 23), (19, 24), 1.04, 0.84, 29.5, (13, 15))
    if flying:
        _far_wing(s, 23, 20, w, "#4e4036")
    else:
        _ripples(s, s.t * 4 if s.act == "swim" else 0, ((2, 30), (6, 29), (25, 30), (29, 29)))
    s.poly([(25, 20), (31, 17), (30, 23)], BLACK)
    s.ellipse(19, 23, 10.5, 6.5, "#9a8670")
    s.ellipse(14, 25, 5, 4, "#e2d8c8")
    if flying:
        _wing_beat(s, 22, 21, w, "#6e5c4c")
    else:
        s.ellipse(22, 21, 7, 3.5, "#6e5c4c", rot=-8, edge=True)
    s.path([(12, 19), (10, 13), (10, 8)], 2.3, BLACK)
    s.ellipse(9.5, 7, 5, 4.2, BLACK, edge=True)
    s.paint(s.m_ellipse(10.5, 9.5, 2.6, 1.6, rot=-20), WHITE)
    s.ellipse(4, 8.2, 2.6, 1.5, BLACK)
    s.paint(s.m_ellipse(13, 19.5, 2.6, 1.2), "#e2d8c8")
    s.eye(8, 5, shine="#ffffff", color="#000000")
    s.px([(8, 5)], "#9a9aa8")


def hummingbird(s: Sprite, *, head="#d93a8a", crown="#6aa56e", throat=None):
    s.can("fly")
    down = s.act == "fly" and s.frame % 2 == 1  # a blur of wingbeats
    _slim(s, (12, 11), (11.5, 12), 0.78, (16, 18), (16.5, 18.5), 1.0, 0.9, 29, (15, 15))
    if down:
        s.ellipse(23, 17, 7, 3, "#cfe8f7", rot=20, shade=False)
    else:
        s.ellipse(22, 9, 7, 3, "#cfe8f7", rot=-35, shade=False)
    s.poly([(18, 20), (24, 28), (20, 29)], "#4d7a52")
    s.ellipse(16, 18, 5.5, 6.5, "#6aa56e", rot=20)
    s.ellipse(14, 20, 3.5, 4, "#c9d6c0")
    if down:
        s.ellipse(20, 18, 6, 2.6, "#e6f4fc", rot=35, shade=False)
    else:
        s.ellipse(19, 12, 6, 2.6, "#e6f4fc", rot=-55, shade=False)
    s.ellipse(12, 11, 5.2, 5, head, edge=True)
    s.paint(s.m_ellipse(13.5, 8.3, 4, 2.3), crown, within=s.last)
    if throat:
        s.paint(s.m_ellipse(11, 14.5, 3.5, 2), throat, within=s.last)
    _beak(s, "needle", "#2b2630")
    s.line(7, 11, 1, 13, "#2b2630")
    s.eye(10, 9)
    s.px([(10, 9)], WHITE)


def pelican(s: Sprite, *, body="#6f6a6c", belly="#8a8486", wing="#b9b4ac", tip="#3f3b3d", neck="#5a3a2e",
            head="#f4efe2", crown="#f2d878", bill="#d9a050", pouch="#6a4a3e", legs="#3d3a3c", knob=False,
            tail="#3f3b3d"):
    """Standing, walking, and flying the way pelicans do: head drawn back onto the
    shoulders, the long bill resting on the chest, broad wings with dark tips."""
    s.can("walk", "fly")
    w = s.wave()
    if s.act == "fly":
        hm, bob = flying_waterbird(s, body=body, belly=belly, wing=wing, tip=tip, tail=tail,
                                  neck=[(12, 17), (10, 15.5)], neck_col=neck, head=(10, 14), head_col=head,
                                  head_r=(3.2, 2.7), cy=19, body_r=(9.5, 3.3), size=1.3)
        if crown:
            s.paint(s.m_ellipse(10.8, 11.6, 2.2, 0.9), crown, within=hm)
        s.poly([(7.5, 13.5), (-2, 15.5), (-1.5, 16.8), (7.5, 15.5)], bill)       # the bill, laid along the chest
        s.poly([(7.5, 15.5), (-1.5, 16.8), (2, 18.5), (8, 17.5)], pouch)         # and the pouch under it
        s.px([(-2, 16)], "#c25a4a")
        if knob:
            s.px([(4, 13)], "#f0d080")
        s.eye(9, 13)
        s.shift(0, bob)
        return
    s.poly([(25, 17), (31, 15), (30, 21)], tail)
    _bird_legs(s, (15, 19), 24, 28, legs, w if s.act == "walk" else 0, toes=(-2, -1, 0), toe_dy=1)
    s.ellipse(18.5, 19.5, 9, 4.6, body, rot=-6)  # long and lean, not round
    s.ellipse(16, 21.5, 5.5, 2.4, belly)
    m = s.ellipse(20.5, 18, 7.5, 3, wing, rot=-10, edge=True)
    s.paint(s.m_poly([(24, 16), (29, 15), (28, 21), (24, 21)]), tip, within=m)
    if body == "#6f6a6c":
        for x in range(16, 24, 3):
            s.paint(s.m_line(x, 17, x + 2, 20), "#8f8a84", within=m)
    s.path([(12.5, 19), (10.5, 15), (12, 10)], (2.2, 1.8), neck)
    if body == "#6f6a6c":
        s.paint(s.m_path([(13.5, 18), (11.8, 15), (13, 11)], 0.6), "#f4efe2")
    s.ellipse(12.5, 7.8, 3.8, 3.2, head, edge=True)
    if crown:
        s.paint(s.m_ellipse(13, 5.2, 3, 1.4), crown, within=s.last)
    s.poly([(10, 6.5), (-1, 9), (0, 10.5), (10, 9)], bill)
    s.poly([(10, 9), (0, 10.5), (3, 14 if body == "#6f6a6c" else 13.5), (10, 12.5)], pouch)
    if body == "#6f6a6c":
        s.px([(0, 10)], "#c25a4a")
    if knob:
        s.px([(13, 4), (14, 3)], "#f0d080")  # breeding knob on the bill top
    s.eye(11, 6)


def gull(s: Sprite, mantle, *, tips=BLACK, spots=True, bill="#f0d040", legs="#f0a8a8", big=False, eye_col=EYE,
         head=WHITE, bill_spot=None, hood=None, thin_bill=False, bill_ring=None):
    """A gull standing side on: a white body, the gray (or black) mantle running back
    into long folded wings that cross past the tail with black, white-spotted tips, a
    rounded head with a sloping forehead, a stout hooked bill (thin for the small
    hooded gulls) and pink, yellow or black webbed feet. Flies on long, narrow,
    pointed wings with the same dark tips."""
    s.can("walk", "fly", "eat")
    if s.act == "eat":  # picking at something on the beach
        s.bend(50 * s.cyc(0.4, 1, 0.4, 1), 17, 24.5, 4)
    w = s.wave()
    if s.act == "fly":
        _flight_wing(s, 16, w, mix(mantle, "#1a1420", 0.3), dx=2.5, tip=mix(tips, "#1a1420", 0.2))
        s.poly([(23, 16.5), (30, 16.5), (30.5, 19), (23, 19.5)], WHITE)  # tail
        s.ellipse(17, 18, 8, 3.2, WHITE)
        s.path([(12, 17.5), (9, 16)], 2.2, head)
        hm = s.ellipse(7.5, 15.5, 3.1, 2.6, head, edge=True)
        if hood:
            s.paint(s.m_ellipse(6.5, 15, 3.2, 2.6), hood, within=hm)
        bx, by = 4.6, 15.4
        s.poly([(bx, by - 0.6), (bx - (3 if thin_bill else 3.6), by + 0.2), (bx, by + 1)], bill)
        s.eye(6, 14, size=1, color=eye_col if not hood else EYE)
        _flight_wing(s, 16, w, mantle, tip=tips)
        s.shift(0, round(0.6 * w))
        return
    # legs and webbed feet
    _bird_legs(s, (15.5, 19), 24, 30, legs, w if s.act == "walk" else 0, toes=(-2, -1, 0, 1))
    s.poly([(21, 20), (28, 19), (28.5, 21.5), (21, 23)], WHITE)                   # tail, under the wingtips
    body = s.ellipse(17, 20.5, 7.5, 4.2, WHITE)
    s.path([(13, 18.5), (10.5, 14.5)], 2.7, head)                              # thick neck
    m = s.poly([(11.5, 18), (14, 16), (20, 15.5), (26, 16.5), (31, 18.4), (29, 19.6), (22, 21), (15, 21.3)],
               mantle, edge=True)                                              # mantle and folded wing
    s.paint(s.m_poly([(24, 15), (32, 17), (31, 21), (24, 21)]), tips, within=m)
    s.paint(s.m_path([(15, 20.8), (23, 20.3)], 0.5), mix(mantle, WHITE, 0.6), within=m)  # white tertial edge
    if spots and tips != WHITE:
        s.paint(s.m_px([(27, 18), (30, 18)]), WHITE, within=m)
    hm = s.ellipse(9.5, 12.5, 3.7, 3.1, head, rot=-12, edge=True)
    if hood:
        s.paint(s.m_ellipse(9, 12, 3.9, 3.1, rot=-12) & ~s.m_ellipse(12, 15.5, 2.5, 1.2), hood, within=hm)
        s.paint(s.m_px([(7, 10), (9, 10)]), WHITE, within=hm)                  # white eye crescents
    by = 12.6
    if thin_bill:
        s.poly([(6.2, by - 0.6), (2, by + 0.3), (6.2, by + 0.9)], bill)
    else:
        k = 1.15 if big else 1.0
        s.poly([(6.3, by - 0.8), (6.3 - 4.6 * k, by - 0.3), (6.3 - 5.2 * k, by + 0.5), (6.3 - 4.6 * k, by + 1.2),
                (6.3 - 3 * k, by + 1.1), (6.3, by + 1.2)], bill)
        s.px([(round(6.3 - 4.8 * k), round(by))], mix(bill, "#000000", 0.35))  # the hooked tip
        if bill_spot:
            s.px([(round(6.3 - 3.6 * k), round(by + 1))], bill_spot)          # the red gonys spot
        if bill_ring:
            s.px([(round(6.3 - 3.8 * k), round(by)), (round(6.3 - 3.8 * k), round(by + 1))], bill_ring)
    if eye_col != EYE and not hood:  # a pale, staring eye
        s.px([(8, 11)], eye_col)
        s.eye_box(8, 11, 8, 11)
    else:
        s.eye(8, 11, size=1)


def cormorant(s: Sprite, body="#26262c", *, wing=None, scale=None, throat=None, face=None, eye_col="#3ac8a0",
              bill="#4a4a50", crest=False, flank=None):
    """A cormorant: long and dark, standing tall with the body leaning up, a long
    neck in a gentle S, a slim hooked bill tilted up, a stiff tail propped behind
    and short black webbed feet. Swims low with only back, neck and head out of the
    water; flies neck outstretched on long dark wings."""
    s.can("walk", "fly", "swim")
    w = s.wave()
    wing = wing or mix(body, "#5a4a30", 0.25)
    scale = scale or mix(wing, "#000000", 0.35)
    if s.act == "fly":
        hm, bob = flying_waterbird(s, body=body, belly=body, wing=wing, tip=mix(body, "#000000", 0.2),
                                   tail=mix(body, "#000000", 0.15), neck=[(11, 18.5), (7, 17.5), (4, 17)],
                                   neck_col=body, head=(3, 16.6), head_col=body, head_r=(2.4, 1.9), cy=19,
                                   body_r=(8.5, 3.2), size=1.1)
        s.poly([(1, 16.2), (-4, 16.8), (-4.5, 17.6), (1, 17.4)], bill)
        if throat:
            s.px([(2, 17), (2, 18)], throat)
        if face:
            s.px([(2, 16)], face)
        s.px([(2, 16)], eye_col)
        s.shift(0, bob)
        return
    if s.act == "swim":
        # low in the water: back awash, neck up, bill tilted up a little
        _ripples(s, s.t * 4, ((2, 30), (6, 29), (25, 30), (29, 29)))
        s.ellipse(19, 27.5, 9, 2.6, body)
        s.ellipse(21, 26.8, 6, 1.6, wing, edge=True)
        s.poly([(27, 26.5), (31, 25), (31, 27), (27, 28)], mix(body, "#000000", 0.15))
        s.path([(13, 27), (11, 22), (12, 17)], (2.0, 1.6), body)
        hx, hy = 11, 15.5
    else:
        a, b = (max(0, w), max(0, -w)) if s.act == "walk" else (0, 0)
        for i, (x, k) in enumerate(((17, a), (20, b))):  # short legs, black webbed feet
            fx = x - round(k * 1.5)
            s.line(x, 26, fx, 30 - round(k), "#1a1a1e")
            s.px([(fx - 2, 30 - round(k)), (fx - 1, 30 - round(k)), (fx + 1, 30 - round(k))], "#1a1a1e")
        s.poly([(20, 24), (25.5, 30.5), (24, 31), (18.5, 26.5)], mix(body, "#000000", 0.2))  # stiff tail propped down
        s.ellipse(18, 20.5, 4.6, 7.6, body, rot=28)                                         # body, leaning up
        if flank:
            s.paint(s.m_ellipse(19.5, 24, 1.6, 1.2), flank)
        m = s.ellipse(19.5, 19.5, 3.4, 6.4, wing, rot=26, edge=True)                        # folded wing
        for y in range(15, 25, 2):  # the scaly wing coverts, each feather edged dark
            s.paint(s.m_px([(18 + (y - 15) // 3, y), (20 + (y - 15) // 3, y + 1)]), scale, within=m)
        s.path([(16, 15), (13.5, 11.5), (13.5, 8.5)], (2.1, 1.6), body)                   # neck in a gentle S
        hx, hy = 12.5, 6.8
    hm = s.ellipse(hx, hy, 2.8, 2.3, body, edge=True)
    if crest:
        s.px([(hx + 1, hy - 3), (hx + 2, hy - 3), (hx - 1, hy - 3)], body)
    s.poly([(hx - 2, hy - 0.4), (hx - 8.5, hy - 1.5), (hx - 8.5, hy - 0.6), (hx - 2, hy + 1.2)], bill)  # long slim bill
    s.px([(round(hx - 9), round(hy - 0.5))], mix(bill, "#000000", 0.4))                          # hooked tip
    if throat:
        s.fill(s.m_ellipse(hx - 2.2, hy + 1.4, 1.4, 1.2), throat, shade=False)
    if face:
        s.paint(s.m_ellipse(hx - 1.5, hy, 1.0, 0.8), face, within=hm)
    s.px([(round(hx - 1), round(hy - 1))], eye_col)
    s.eye_box(round(hx - 1), round(hy - 1), round(hx - 1), round(hy - 1))


def vulture(s: Sprite, *, head_col, body="#2f2a2e", ruff=None, wing_patch=None, beak="#e8dccb"):
    """A perched vulture, hunched: a big dark body under long folded wings that reach
    past the tail, and a small bare head pushed forward on a bare neck, with a pale
    hooked bill. Soars on long, broad wings."""
    s.can("walk", "fly")
    w = s.wave()
    wing = mix(body, "#ffffff", 0.06)
    if s.act == "fly":
        _flight_wing(s, 16, w, mix(wing, "#1a1420", 0.3), dx=2.5)
        s.poly([(23, 17), (30, 16.5), (30, 20), (23, 20)], body)
        s.ellipse(17.5, 18.5, 8.5, 3.6, body)
        m = _flight_wing(s, 16, w, wing)
        if wing_patch:
            s.paint(m & ~s.m_ellipse(17, 14, 9, 7), wing_patch, within=m)
        hx, hy = 7.5, 17
        s.path([(11, 18), (hx + 1, hy)], 1.4, head_col)
    else:
        legs = "#c8b8b0"
        step = w if s.act == "walk" else 0
        for i, x in enumerate((15, 18)):
            lift = max(0.0, step if i == 0 else -step)
            s.line(x, 25, x - round(lift), 30 - round(lift), legs)
            s.px([(x - 1 - round(lift), 30 - round(lift))], legs)
        s.poly([(23, 21.5), (30.5, 25.5), (29.5, 27.5), (22.5, 24.5)], mix(body, "#000000", 0.1))  # tail
        s.ellipse(18, 20, 8.5, 6, body, rot=-12)
        m = s.ellipse(21, 19, 8.6, 4.4, wing, rot=-14, edge=True)  # folded wing, tips past the tail
        for x in range(17, 29, 3):
            s.paint(s.m_line(x, 17 + (x - 17) * 0.25, x + 2, 19.5 + (x - 17) * 0.25), mix(wing, "#000000", 0.2), within=m)
        if wing_patch:
            s.paint(s.m_ellipse(22, 22, 7.5, 1.5, rot=-14), wing_patch, within=m)
        hx, hy = 7.5, 14.5
        s.path([(12, 17), (hx + 1.5, hy + 0.5)], 1.5, head_col)  # bare neck
    if ruff:
        s.ellipse(12.5, 17.5 if s.act != "fly" else 18.5, 2.8, 2.2, ruff)
    else:
        s.ellipse(12.5, 17.5 if s.act != "fly" else 18.5, 2.2, 1.8, mix(body, "#000000", 0.15))
    s.ellipse(hx, hy, 2.9, 2.3, head_col, edge=True)
    s.poly([(5.6, hy - 1), (2.6, hy - 0.4), (2.2, hy + 1.2), (3.2, hy + 1.6), (5.6, hy + 1.4)], beak, shade=False)
    s.px([(2, hy + 1)], mix(beak, "#000000", 0.45))  # the hook
    s.eye(7, round(hy) - 1, size=1)
    s.eye_box(7, round(hy) - 1, 7, round(hy) - 1)


# How each kind of bird of prey is built: overall size, body length and depth, tail
# length, how far the folded wingtips reach, head size, bill size, and feathered legs.
RAPTORS = {
    #           k     body_rx body_ry tail  wing  head_r      bill  trousers
    "eagle":   (1.0,  6.4,    9.2,    7.0,  1.0,  (3.7, 3.2), 1.25, True),
    "buteo":   (0.9,  6.2,    8.6,    7.0,  0.92, (3.5, 3.1), 1.0,  True),
    "osprey":  (0.92, 5.4,    8.6,    7.0,  1.08, (3.3, 2.9), 1.0,  False),
    "accip":   (0.84, 5.4,    8.4,    10.0, 0.8,  (3.3, 2.9), 0.9,  False),
    "harrier": (0.88, 5.4,    8.4,    10.0, 0.95, (3.4, 3.1), 0.85, False),
    "kite":    (0.8,  5.2,    8.0,    9.0,  1.1,  (3.2, 2.9), 0.85, False),
    "falcon":  (0.72, 5.6,    8.2,    8.5,  1.0,  (3.4, 3.1), 0.9,  False),
}


def raptor(s: Sprite, back, front, *, head=None, wing=None, tail=None, build="buteo", bill="#2b2630",
           cere="#e8c040", legs="#e8c040", eye_col="#5a3a10", brow=True, chest=None, wing_mark=None,
           tail_mark=None, face=None, flight_under=None):
    """A bird of prey from the side, facing left. Perched it sits upright: the body
    leaning back, long wings folded along its sides reaching down the tail, a flat-
    crowned head with a shading brow over the eye and a deep hooked bill with a
    coloured cere, feathered 'trousers' (eagles and buteos) and strong yellow feet
    with dark talons. It flies and soars on broad wings with fingered tips, legs
    tucked up under the tail. build picks the proportions (RAPTORS). chest(s, m),
    wing_mark(s, m), tail_mark(s, m) and face(s, head_mask) add a species' markings
    in the perched drawing's coordinates; flight_under(s, body_mask) in flight."""
    s.can("walk", "fly", "eat")
    k, brx, bry, tail_len, wing_k, (hrx, hry), bill_k, trousers = RAPTORS[build]
    head = head or back
    wing = wing or mix(back, "#1a1420", 0.12)
    tail = tail or back
    dark = mix(wing, "#1a1420", 0.35)
    if s.act == "eat":
        s.bend(38 + 10 * s.cyc(0, 1, 0, 1), 15, 25)  # tearing at a meal on the ground
    if s.act == "fly":
        _raptor_flight(s, back, front, head, wing, tail, dark, k, wing_k, hrx, hry, bill, bill_k, cere, legs, eye_col,
                       brow, flight_under, build)
        return
    # Scaled about the feet, so smaller hawks stand on the same ground.
    s.set_warp(lambda x, y: (16 + (x - 16) * k, 31 - (31 - y) * k))
    step = s.wave() if s.act == "walk" else 0
    # tail, hanging down behind
    ty = min(30.5, 23.5 + tail_len)
    tx = 21 + (ty - 22) * 0.4
    tm = s.poly([(16.5, 20), (tx, ty), (tx + 3.6, ty - 1.3), (21, 18.5)], tail, edge=True)
    if tail_mark:
        tail_mark(s, tm)
    # far foot
    s.line(16.5, 26, 16 - round(max(0, -step)), 30, mix(legs, "#1a1420", 0.25))
    # body, leaning back
    body = s.ellipse(16, 17.5, brx, bry, back, rot=25)
    chest_m = s.m_ellipse(13.4, 18.5, brx * 0.62, bry * 0.86, rot=25) & body
    s.fill(chest_m, front, shade=False)
    if chest:
        chest(s, chest_m)
    # legs: feathered thighs, then bare yellow legs to the feet
    lift = max(0, step)
    if trousers:
        s.ellipse(14, 25, 2.9, 2.6, front if front != back else back, rot=10)
    s.path([(13.6, 26), (13.2 - lift, 29.6 - lift)], 0.9, legs)
    fy = round(30 - lift)
    s.px([(round(10.8 - lift) + i, fy) for i in range(3)] + [(round(14 - lift), fy)], legs)  # toes
    s.px([(round(10 - lift), fy), (round(15 - lift), fy)], "#1a1420")  # talons
    # long wing folded along the side, the primaries reaching down over the tail
    tip_x, tip_y = 15.5 + 7.5 * wing_k, 17.5 + 8 * wing_k
    wm = s.poly([(12.5, 11.5), (17.5, 11), (21, 15), (tip_x + 1.5, tip_y - 1), (tip_x, tip_y + 1.2), (19, 25),
                 (15.5, 22.5), (13, 17)], wing, edge=True)
    s.paint(s.m_poly([(19.8, 18.5), (tip_x + 1.5, tip_y - 1), (tip_x, tip_y + 1.2), (18.5, 23)]), dark, within=wm)
    # rows of coverts catching the light along the top of the wing
    s.paint(s.m_path([(13, 12.5), (17.5, 12), (20, 15)], 0.6), mix(wing, "#ffffff", 0.18), within=wm)
    for y in (16.5, 19.5):
        s.paint(s.m_line(15, y, 19.5, y + 0.6), mix(wing, "#1a1420", 0.2), within=wm)
    if wing_mark:
        wing_mark(s, wm)
    # head on a thick neck: flat crown, brow over the eye, deep hooked bill
    hx, hy = 10, 9.5
    s.path([(14, 13.5), (hx + 1, hy + 1)], 3.0, head)
    hm = s.ellipse(hx, hy, hrx, hry, head, edge=True)
    if face:
        face(s, hm)
    _raptor_bill(s, hx - hrx + 1.0, hy - 0.6, bill_k, bill, cere)
    ex, ey = round(hx - 1.6), round(hy - 0.8)
    s.px([(ex, ey), (ex + 1, ey)], eye_col)
    s.px([(ex, ey)], "#1a1420")
    if brow:  # the bony brow that gives hawks and eagles their fierce look
        s.paint(s.m_line(ex - 1, ey - 1, ex + 2, ey - 1), mix(head, "#1a1420", 0.45), within=hm)
    s.eye_box(ex, ey, ex + 1, ey)
    if s.act == "walk":
        _lift(s, 0.5 + 0.5 * math.cos(4 * math.pi * s.t))


def _raptor_bill(s: Sprite, x, y, k, bill, cere):
    """A deep hooked bill pointing left from (x, y) at the face, with the cere at its base."""
    s.poly([(x + 0.6, y - 1.2 * k), (x - 2.2 * k, y - 0.9 * k), (x - 3.4 * k, y + 0.4 * k), (x - 3.3 * k, y + 2.1 * k),
            (x - 2.6 * k, y + 1.4 * k), (x - 1.6 * k, y + 1.5 * k), (x + 0.6, y + 1.6 * k)], bill, edge=True)
    s.fill(s.m_poly([(x + 0.6, y - 1.2 * k), (x - 0.8 * k, y - 1.1 * k), (x - 0.8 * k, y + 0.6 * k),
                     (x + 0.6, y + 0.6 * k)]), cere, shade=False)


def _raptor_flight(s, back, front, head, wing, tail, dark, k, wing_k, hrx, hry, bill, bill_k, cere, legs, eye_col,
                   brow, under, build):
    """Side on, level, on broad wings: the far wing, a fanned tail, the body with its
    paler underside, the head and bill, and the near wing with fingered primaries."""
    s.set_warp(lambda x, y: (16 + (x - 16) * (0.6 + 0.4 * k), 18 + (y - 18) * (0.6 + 0.4 * k)))
    w = s.wave()
    size = 1.25 * wing_k
    bx, by = 17.5, 18
    _big_wing(s, bx - 5, by - 2, w, mix(wing, "#1a1420", 0.1), size=size, far=True)
    s.poly([(bx + 6, by - 1.8), (31, by - 3), (31.5, by + 2.5), (bx + 6, by + 2)], tail, edge=True)  # tail, fanned
    s.px([(bx + 4, by + 3), (bx + 5, by + 3)], legs)  # feet tucked up under the tail
    b = s.ellipse(bx, by, 8.2, 3.4, back)
    bm = s.m_ellipse(bx - 1.5, by + 1.6, 6.4, 2.0) & b
    s.fill(bm, front, shade=False)
    if under:
        under(s, bm)
    hx, hy = bx - 9.5, by - 1.4
    s.path([(bx - 6, by - 0.5), (hx + 1, hy + 0.3)], 2.6, head)
    hm = s.ellipse(hx, hy, hrx * 0.95, hry * 0.9, head, edge=True)
    _raptor_bill(s, hx - hrx * 0.95 + 1.0, hy - 0.2, bill_k * 0.9, bill, cere)
    ex, ey = round(hx - 1.4), round(hy - 0.8)
    s.px([(ex, ey), (ex + 1, ey)], eye_col)
    s.px([(ex, ey)], "#1a1420")
    if brow:
        s.paint(s.m_line(ex - 1, ey - 1, ex + 2, ey - 1), mix(head, "#1a1420", 0.45), within=hm)
    s.eye_box(ex, ey, ex + 1, ey)
    _big_wing(s, bx - 5, by - 2, w, wing, size=size, tip=dark, coverts=mix(wing, "#ffffff", 0.16))
    s.shift(0, round(0.6 * w))


# --------------------------------------------------------------------------- reptiles & amphibians
def lizard(s: Sprite, body, belly, *, head=None, pattern=None, tail_col=None, throat=None,
           horns=False, wide=False, smooth=False, eye_big=False, legs=None, tail_pts=None):
    """Side view facing left, big head, tail curling up on the right."""
    s.can("walk")
    w = s.wave() if s.act == "walk" else 0
    head = head or body
    tail_col = tail_col or body
    legs = legs or mix(body, "#000000", 0.15)
    tp = tail_pts or [(20, 22), (26, 25), (30, 22), (30, 16)]
    tp = [(x, y + w * 1.2 * i / len(tp)) for i, (x, y) in enumerate(tp)]
    s.path(tp, (2.4, 0.7), tail_col)
    far = mix(legs, "#000000", 0.15)
    s.path([(20, 23), (22 - w * 1.5, 27), (24 - w * 1.5, 27)], 1.1, far)
    s.path([(10, 23), (9 + w * 1.5, 27), (7 + w * 1.5, 27)], 1.1, far)
    ry = 4.3 if wide else 3.6
    body_m = s.ellipse(15, 22, 7.5, ry, body)
    s.paint(s.m_ellipse(15, 24.8, 6.5, 1.6), belly, within=body_m)
    if pattern:
        pattern(s, body_m)
    s.path([(17, 24), (17 + w * 1.5, 28), (15 + w * 1.5, 28)], 1.1, legs)
    s.path([(12, 24), (12 - w * 1.5, 28), (10 - w * 1.5, 28)], 1.1, legs)
    hm = s.ellipse(7.5, 18.5, 5.5 if smooth else 5.2, 4.3 if smooth else 3.8, head, edge=True)
    s.paint(s.m_ellipse(6, 21.5, 4.5, 1.3), throat or belly, within=hm)
    if horns:
        s.px([(9, 14), (11, 14), (12, 15), (13, 16), (7, 14)], mix(body, "#ffffff", 0.3))
        s.px([(9, 13), (11, 13), (13, 15), (14, 16)], mix(body, "#ffffff", 0.45))
    if eye_big:
        s.eye(5, 16, size=3)
        s.px([(5, 16)], WHITE)
    else:
        s.eye(5, 17)
    s.px([(2, 20), (3, 20)], mix(head, "#000000", 0.45))


def snake(s: Sprite, body, *, belly=None, bands=None, band_period=4.0, band_len=2.0,
          stripe=None, blotch=None, rattle=False, head=None, head_w=5.4):
    """Coiled snake looking left, with a big round head and a tongue. Slithering
    ripples the coil and sways the head; asleep, the tongue stays in."""
    s.can("walk")
    moving = s.act == "walk"
    w = 0
    if moving:
        # Stretched out along the ground, slithering: S-bends that travel from the
        # head back to the tail, the head held a little up and steady.
        ph = s.t * 2 * math.pi
        pts = [(x, 28.4 - 1.9 * math.sin(x * 0.45 + ph) * min(1.0, (x - 5) / 6)) for x in range(31, 6, -1)]
        pts += [(6, 27.4), (4.5, 26.2)]
        r = 1.7
    else:
        pts = [(25, 28.5), (14, 28.8), (7, 27), (5.5, 23.5), (9, 20.5), (17, 20), (24, 21.5), (25.5, 24.5),
               (21, 26), (16, 25), (14, 21), (15, 17), (13.5, 13)]
        r = 2.6
    if rattle:
        rat = [(31.5, pts[0][1] - 0.5), (33, pts[0][1] - 1)] if moving else [(27, 28), (29, 27), (30.3, 25.3)]
        for i, (x, y) in enumerate(rat):
            s.ellipse(x, y, 1.4 if not moving else 1.1, 1.2 if not moving else 1.0, "#d9c08a" if i % 2 == 0 else "#b89b62")
    # Stamp discs along the path; each pixel remembers the arc length and centre
    # distance of the last disc covering it, so the front of the coil wins.
    tmap = np.full((N, N), -1.0)
    dmap = np.full((N, N), 99.0)
    t = 0.0
    for a, b in zip(pts, pts[1:]):
        L = math.dist(a, b)
        steps = max(2, int(L * 3))
        for k in range(steps):
            u = k / steps
            x, y = a[0] + (b[0] - a[0]) * u, a[1] + (b[1] - a[1]) * u
            d = np.hypot(_XS - x, _YS - y)
            tt = t + L * u
            # a later loop always covers; within one loop keep the nearest centre
            m = (d <= r) & ((tmap < 0) | (tt - tmap > 2 * r) | (d < dmap))
            tmap[m] = tt
            dmap[m] = d[m]
        t += L
    body_m = tmap >= 0
    s.fill(body_m, body)
    phase = tmap % band_period
    if bands:
        s.paint(body_m & (phase < band_len), bands)
    if blotch:
        s.paint(body_m & (phase < band_len) & (dmap < 1.7), blotch)
    if stripe:
        s.paint(body_m & (dmap < 0.75), stripe)
    # dark seam where one loop of the coil lies on another
    seam = np.zeros_like(body_m)
    for dx, dy in ((0, 1), (0, -1), (1, 0), (-1, 0)):
        nb = np.roll(np.roll(tmap, -dy, axis=0), -dx, axis=1)
        seam |= body_m & (nb >= 0) & (nb > tmap + 6)
    s.paint(seam, mix(body, "#1d1428", 0.6))
    if moving:
        hm = s.ellipse(3.2, 25.6, head_w * 0.62, 2.3, head or body, rot=-8, edge=True)
        if belly:
            s.paint(s.m_ellipse(2.5, 27, 2.6, 0.8), belly, within=hm)
        if s.frame % 3 == 0:  # the tongue flicks out now and then
            s.px([(-1, 26), (-2, 26), (-3, 25), (-3, 27)], "#e04a5a")
        s.eye(1, 24, size=1)
        return
    hx = 12.5 - w
    hm = s.ellipse(hx, 10.5, head_w, 4.2, head or body, edge=True)
    if belly:
        s.paint(s.m_ellipse(hx - 1.5, 13.6, 4, 1.3), belly, within=hm)
    if s.act != "sleep" and s.f % 2 == 0:
        dx = round(hx - 12.5)
        s.px([(6 + dx, 13), (5 + dx, 13), (4 + dx, 14), (4 + dx, 12)], "#e04a5a")
    s.eye(round(9 - w), 9)


def turtle(s: Sprite, shell, skin, *, dome=False, scutes=None, speckle=None, rim=None):
    s.can("walk", "swim")
    w = s.wave() if s.act in ("walk", "swim") else 0
    tucked = s.act == "sleep"
    hx = 9 if tucked else 5  # asleep, the head pulls in under the shell
    s.ellipse(hx + 3, 22, 4.5, 3.5, skin)
    s.ellipse(hx, 18.5 + (2 if tucked else 0), 4.5, 4, skin, edge=True)
    if speckle and not tucked:
        s.px([(3, 17), (6, 16), (5, 20), (7, 19)], speckle)
    s.ellipse(11 - w * 1.5, 27 - max(0, w), 2.4, 3.2, skin)
    s.ellipse(22 + w * 1.5, 27 - max(0, -w), 2.4, 3.2, skin)
    s.poly([(26, 23), (30, 25), (26, 26)], skin)
    ry = 10 if dome else 7.5
    m = s.fill(s.m_ellipse(17, 25, 11, ry) & (s.m_poly([(0, 0), (32, 0), (32, 25.5), (0, 25.5)])), shell, edge=True)
    s.ellipse(17, 25.5, 11.5, 1.6, rim or mix(shell, "#000000", 0.25))
    if scutes:
        cy = 18 if dome else 20
        for cx in (11, 17, 23):
            s.paint(s.m_ellipse(cx, cy + (1 if cx != 17 else -1), 2.4, 2.2), scutes, within=m)
    if not tucked:
        s.eye(3, 17)


# Side-view frog builds: body (cx, cy, rx, ry, rot), head (cx, cy, rx, ry), eye bump
# (cx, cy, r), thigh (cx, cy, rx, ry, rot), and how far the hind foot reaches forward.
FROGS = {
    "frog": dict(body=(16.5, 22.8, 9.8, 5.8, -16), head=(7.5, 23, 5.6, 4.3), eye=(7.8, 18.4, 2.8),
                 thigh=(21.5, 26, 5.8, 3.4, -28), foot=12.5, leg=1.3),
    "toad": dict(body=(16.5, 23, 10.0, 6.6, -8), head=(7.5, 23.6, 5.4, 4.5), eye=(8.0, 19.2, 2.5),
                 thigh=(21, 26.6, 5.0, 3.2, -22), foot=13.5, leg=1.5),
    "tree": dict(body=(17, 22.6, 9.2, 5.4, -20), head=(8, 23, 5.2, 4.1), eye=(8.2, 18.6, 2.9),
                 thigh=(22, 25.8, 6.0, 3.2, -30), foot=12, leg=1.1),
}


def frog(s: Sprite, skin, belly, *, build="frog", head=None, mask=None, side=None, lip=None, dorsal=None,
         ridges=None, lines=None, thigh=None, crown=None, parotoid=None, under_eye=None, spots=0, spot_col=None,
         spot_big=False, warts=None, iris="#f3d26a", cat=False, pads=False, tympanum=None, markings=None):
    """A frog or toad from the side, sitting and facing left.

    Walking hops (crouch, leap with the hind legs kicked out, land); swimming
    stretches out and kicks. look turns the head to you, back over the shoulder.
    The keywords add the usual field marks: mask (dark stripe through the eye), side
    (stripe along the flank), lip, dorsal (pale line down the middle of the back),
    ridges (pale folds along the back), lines (dark lines along the back), thigh
    (colour of the hind legs), crown (patch between the eyes), parotoid (the toad's
    swollen gland behind the eye), spots (how many, on the back), warts (pale dots)."""
    s.can("walk", "swim", "look", "back")
    b = FROGS[build]
    act, f = s.act, s.f
    view = {"look": "front", "back": "back"}.get(act, "side")
    hopping = act == "walk"
    swimming = act == "swim"
    leap = (hopping and f == 2) or (swimming and f in (1, 2))
    crouch = hopping and f == 1
    head = head or skin
    legs = thigh or skin
    far = lambda c: mix(c, "#1a1420", 0.3)  # noqa: E731
    ground = 30.5
    bx, by, brx, bry, brot = b["body"]
    hx, hy, hrx, hry = b["head"]
    ex, ey, er = b["eye"]
    if swimming:
        brot, by, hy, ey = -4, 20, 20.5, 16.8
    elif leap:
        brot = -30
    if crouch:
        bry *= 0.9
    g = dict(view=view, act=act, bx=bx, by=by, brx=brx, bry=bry, brot=brot, hx=hx, hy=hy, hrx=hrx, hry=hry)

    # hind legs: folded alongside the body, or kicked out behind in a leap or stroke
    tx, ty, trx, tryy, trot = b["thigh"]
    if swimming:
        ty = by + 2
    kick = leap or (swimming and f == 1)
    if kick:
        hip = (bx + brx * 0.6, by + 1)
        knee = (hip[0] + 5, hip[1] + (4 if not swimming else 1.5))
        heel = (knee[0] + 4, knee[1] + (2 if not swimming else -0.5))
        for dy, col in ((-1.2, far(legs)), (0, legs)):
            s.path([(hip[0], hip[1] + dy), (knee[0], knee[1] + dy)], (b["leg"] * 1.9, b["leg"] * 1.3), col)
            s.path([(knee[0], knee[1] + dy), (heel[0], heel[1] + dy)], b["leg"], col)
            s.ellipse(heel[0] + 1.5, heel[1] + dy + 0.3, 2.4, 0.9, col, rot=20)
    else:
        s.ellipse(b["foot"] + 2.5, ground - 0.6, 3.0, 0.9, far(legs))
    # far front leg
    if not swimming:
        s.path([(hx + 3, hy + 1.5), (hx + 2.4 - (1.5 if leap else 0), ground - 0.6 - (1 if leap else 0))],
               b["leg"], far(skin))

    body = s.ellipse(bx, by, brx, bry, skin, rot=brot)
    s.fill(s.m_ellipse(bx - 1, by + bry * 0.75, brx * 0.85, bry * 0.5, brot) & body, belly, shade=False)
    g["body"] = body
    if dorsal:
        back_stripes(s, g, [dorsal], top=0.1, width=0.9)
    if ridges:
        back_stripes(s, g, [ridges], top=1.6, width=0.8)
    if lines:
        back_stripes(s, g, [lines, skin, lines], top=0.8, width=1.0)
    if side:
        s.paint(s.m_ellipse(bx, by + bry * 0.35, brx * 0.95, 0.9, brot), side, within=body)
    if spots:
        _frog_spots(s, body & ~s.m_ellipse(bx - 1, by + bry * 0.75, brx * 0.85, bry * 0.55, brot), spots,
                    spot_col or mix(skin, "#000000", 0.42), spot_big)
    if warts:
        flecks(s, body, warts, every=9, seed=4)
    if markings:
        markings(s, g)

    # near hind leg, folded: thigh along the flank, shin and long foot forward
    if not kick:
        th = s.ellipse(tx, ty + (0.5 if crouch else 0), trx, tryy, legs, rot=trot)
        s.path([(tx + trx * 0.7, ty + 2.2), (b["foot"] + 3.5, ground - 1)], b["leg"] * 1.1, legs)
        s.ellipse(b["foot"], ground - 0.6, 3.2, 0.9, legs)
        if pads:
            s.px([(round(b["foot"] - 3), round(ground - 0.5))], mix(legs, WHITE, 0.4))
        if spots:
            _frog_spots(s, th, max(1, spots // 3), spot_col or mix(skin, "#000000", 0.42), spot_big)

    # head
    if view == "front":
        cx = hx + 0.8
        hm = s.ellipse(cx, hy, hrx * 1.1, hry, head, edge=True)
        s.fill(s.m_ellipse(cx, hy + hry * 0.6, hrx * 0.8, hry * 0.45) & hm, belly, shade=False)
        g["head_m"] = hm
        if crown:
            s.paint(s.m_ellipse(cx, hy - hry * 0.5, 1.6, 1.0), crown, within=hm)
        s.px([(round(cx - hrx * 0.6) + i, round(hy + 0.8 + (0 if i in (0, 5) else 0.6))) for i in range(6)],
             mix(head, "#000000", 0.5))
        for d in (-1, 1):
            _frog_eye(s, cx + d * (hrx * 0.62), hy - hry * 0.75, er * 0.95, head, iris, cat, mask)
    else:
        d = 1 if view == "back" else -1
        if d > 0:
            hx, ex = hx + 1.5, 2 * hx - ex + 3.0
        hm = s.ellipse(hx, hy, hrx, hry, head, edge=True)
        s.fill(s.m_ellipse(hx + d * 0.5, hy + hry * 0.65, hrx * 0.85, hry * 0.45) & hm, belly, shade=False)
        g["head_m"] = hm
        if lip:
            s.paint(s.m_line(hx + d * hrx, hy + 0.8, hx - d * 1, hy + 1.6), lip, within=hm)
        if mask:
            s.paint(s.m_path([(hx + d * (hrx - 0.5), hy - 1.2), (hx - d * 2.5, hy + 0.2)], 0.9), mask, within=hm | body)
        s.paint(s.m_line(hx + d * (hrx - 0.4), hy + 1.2, hx - d * 1.5, hy + 2), mix(head, "#000000", 0.5), within=hm)
        if tympanum:
            s.paint(s.m_ellipse(hx - d * 2.2, hy - 0.6, 1.3, 1.3), tympanum, within=hm)
        if parotoid:
            s.ellipse(hx - d * 3.2, hy - 1.6, 2.4, 1.2, parotoid, rot=d * 20)
        if under_eye:
            s.px([(round(ex), round(hy + 0.6))], under_eye)
        if crown:
            s.paint(s.m_ellipse(ex - d * 1.5, hy - hry + 0.4, 1.6, 0.9), crown, within=hm)
        _frog_eye(s, ex, ey, er, head, iris, cat, None)

    # near front leg
    if swimming:
        s.ellipse(hx + 2, hy + 3.2, 2.2, 0.8, skin, rot=-15)
    else:
        lean = 1.5 if leap else 0
        s.path([(hx + 1.6, hy + 1.5), (hx + 0.6 - lean, ground - 0.6 - (1 if leap else 0))], b["leg"], skin)
        s.ellipse(hx - 0.6 - lean, ground - 0.5 - (1 if leap else 0), 1.8, 0.8, skin)
        if pads:
            s.px([(round(hx - 2.2 - lean), round(ground - 0.5 - (1 if leap else 0)))], mix(skin, WHITE, 0.4))
    if leap and hopping:
        s.shift(0, -3)
    elif hopping and f == 3:
        s.shift(0, -1)


def _frog_eye(s: Sprite, x, y, r, skin, iris, cat, mask):
    """A bulging eye on top of the head: skin lid, coloured iris, dark pupil."""
    s.ellipse(x, y, r, r * 0.95, skin)
    s.ellipse(x, y - 0.1, r * 0.72, r * 0.7, iris, shade=False)
    if mask:
        s.paint(s.m_ellipse(x, y + r * 0.5, r, 0.6), mask)
    px, py = round(x - 0.5), round(y - 0.5)
    s.px([(px, py), (px, py + 1)] if cat else [(px, py), (px - 1, py)], EYE)
    s.eye_box(px - 1, py - 1, px + 1, py + 1)


def _frog_spots(s: Sprite, mask, n, col, big):
    """n spots spread over mask, always in the same places."""
    pts = [(x + PAD_X, y + PAD_TOP) for x, y in units(mask)]
    if not pts:
        return
    xs, ys = [p[0] for p in pts], [p[1] for p in pts]
    order = sorted(range(len(xs)), key=lambda i: (xs[i] * 37 + ys[i] * 61) % 97)
    picked = []
    for i in order:
        x, y = xs[i], ys[i]
        if all(abs(x - a) + abs(y - b) > (3 if big else 2) for a, b in picked):
            picked.append((x, y))
        if len(picked) == n:
            break
    for x, y in picked:
        x, y = x - PAD_X, y - PAD_TOP
        m = s.m_px([(x, y), (x + 1, y), (x, y + 1), (x + 1, y + 1)] if big else [(x, y)])
        s.paint(m, col, within=mask)


# --------------------------------------------------------------------------- invertebrates
def butterfly(s: Sprite, fore, hind, *, body="#2b2630", pattern=None, tails=False):
    """Top view, wings spread. Flying, the wings fold up and open again; asleep
    they're held closed."""
    s.can("fly")
    k = {"fly": s.cyc(1, 0.6, 0.25, 0.6), "sleep": 0.25}.get(s.act, 1)
    sq = lambda pts: [(16 + (x - 16) * k, y) for x, y in pts]  # noqa: E731
    if tails:
        s.path(sq([(11, 23), (10, 28)]), (1.2, 0.8), hind, mirror=True)
    fm = s.poly(sq([(15, 11), (5, 3), (1.5, 6), (2, 14), (14, 17)]), fore, mirror=True, edge=True)
    hm = s.poly(sq([(15, 16), (5, 16), (4, 22), (9, 27), (15, 22)]), hind, mirror=True, edge=True)
    if pattern:
        pattern(s, fm, hm)
    s.line(15, 8, 11, 2, body)
    s.line(16, 8, 20, 2, body)
    s.px([(11, 1), (20, 1)], body)
    s.ellipse(16, 17, 1.6, 8, body)
    s.ellipse(16, 9.5, 2.5, 2.2, body)
    s.px([(14, 9), (17, 9)], WHITE)


def bee(s: Sprite):
    s.can("fly")
    up = not (s.act == "fly" and s.f % 2)
    s.ellipse(20, 8 if up else 11, 4.5, 6.5 if up else 4, "#e6f4fc", rot=25 if up else 70, shade=False, edge=True)
    s.ellipse(25, 11 if up else 13, 3.5, 5 if up else 3, "#d6ecfa", rot=40 if up else 80, shade=False, edge=True)
    s.poly([(26, 21), (31, 23), (26, 24)], "#3a2a22")
    m = s.ellipse(18, 19, 8.5, 7, "#f0b429")
    for x in (16, 21, 25):
        s.paint(s.m_poly([(x, 10), (x + 2.2, 10), (x + 1.2, 28), (x - 1, 28)]), "#3a2a22", within=m)
    s.line(9, 25, 8, 29, "#3a2a22")
    s.line(13, 25, 13, 29, "#3a2a22")
    s.ellipse(8.5, 17, 5.5, 5.5, "#3a2a22", edge=True)
    s.line(6, 12, 4, 6, "#3a2a22")
    s.line(9, 12, 10, 6, "#3a2a22")
    s.eye(5, 16, color="#11080f", shine="#ffffff")


def beetle_top(s: Sprite, shell, *, head=BLACK, spots=(), stripes=False, fan=False, pron=None):
    s.can("walk")
    w = s.wave() if s.act == "walk" else 0
    for i, y in enumerate((17, 21, 25)):
        d = round(w * (1 if i % 2 else -1))
        s.line(6, y - 2, 4, y + 1 + d, BLACK)
        s.line(25, y - 2, 27, y + 1 - d, BLACK)
    if fan:
        s.path([(13, 5), (10, 1)], 0.6, "#7a5a3a", shade=False)
        s.path([(18, 5), (21, 1)], 0.6, "#7a5a3a", shade=False)
        s.px([(8, 0), (9, 0), (9, 1), (22, 0), (23, 0), (22, 1)], "#9a7a5a")
    else:
        s.line(13, 6, 11, 2, BLACK)
        s.line(18, 6, 20, 2, BLACK)
    s.ellipse(16, 7.5, 4.5, 3, head, edge=True)
    s.px([(13, 7), (18, 7)], WHITE)
    if pron:
        s.ellipse(16, 11, 7, 3, pron, edge=True)
    m = s.ellipse(16, 20, 10, 10 if not stripes else 10.5, shell, edge=True)
    s.paint(s.m_line(16, 11, 16, 30) | s.m_line(15, 11, 15, 30), mix(shell, "#000000", 0.5) if not stripes else "#4a3020", within=m)
    for x, y in spots:
        s.paint(s.m_ellipse(x, y, 1.7, 1.7), BLACK, within=m)
    if stripes:
        for x in (9, 12, 19, 22):
            s.paint(s.m_line(x, 12, x, 29), "#f4efe6", within=m)
        s.paint(s.m_line(6, 16, 6, 25) | s.m_line(25, 16, 25, 25), "#f4efe6", within=m)


def dragonfly(s: Sprite, thorax, abdomen, *, wing="#e6f4fc", wing_tint=None):
    s.can("fly")
    flap = s.cyc(0, 14, 0, -14) if s.act == "fly" else 0
    for cy in (10, 14):
        rot = (-8 if cy == 10 else 10) + (flap if cy == 10 else -flap)
        m = s.ellipse(8, cy, 7.5, 2.1, wing, rot=rot, shade=False, edge=True, mirror=True)
        if wing_tint:
            s.paint(s.m_ellipse(13, cy, 3.5, 2.3, rot=rot), wing_tint, within=m, mirror=True)
    s.path([(16, 14), (16, 30)], (1.6, 1.1), abdomen)
    s.ellipse(16, 11, 2.6, 3.5, thorax, edge=True)
    s.ellipse(16, 5.5, 4, 3, thorax, edge=True)
    s.ellipse(13.8, 5, 1.9, 2.1, mix(thorax, "#000000", 0.35), mirror=True, shade=False)
    s.px([(13, 4), (18, 4)], WHITE)


# --------------------------------------------------------------------------- marine
def lying_flat(s: Sprite, shape, color):
    """A flat animal lying on the rock, seen from a little above, not straight down:
    shape(x, y) -> mask, in the plan's top-view coordinates around (16, 16.5), is squashed
    to a low oval with a darker rim of thickness under it. The species details that follow
    are squashed the same way."""
    for top, col in ((24.5, mix(color, "#000000", 0.35)), (23, color)):
        s.set_warp(lambda x, y, top=top: (x, top + (y - 16.5) * 0.6))
        m = s.fill(shape(s.xs - 16, s.ys - 16.5), col, edge=True)
    return m


def star(s: Sprite, color, *, arms=0.45, dots=WHITE, rot=-90):
    def shape(x, y):
        ang = np.arctan2(y, x) - math.radians(rot)
        return np.hypot(x, y) <= 14.5 * ((1 - arms) + arms * (0.5 + 0.5 * np.cos(5 * ang)) ** 1.6)
    m = lying_flat(s, shape, color)
    if dots:
        pts = []
        for k in range(5):
            a = math.radians(rot) + k * 2 * math.pi / 5
            for d in (4, 7, 10):
                pts.append((round(16 + d * math.cos(a) - 0.5), round(16.5 + d * math.sin(a) - 0.5)))
        s.paint(s.m_px(pts), dots, within=m)
    s.paint(s.m_ellipse(16, 16.5, 1.6, 1.6), mix(color, WHITE, 0.25), within=m)  # the central disk


# --------------------------------------------------------------------------- added for North Carolina
def fish(s: Sprite, body, belly, *, fin=None, pattern=None, slim=False):
    """Side view facing left."""
    s.can("swim")
    w = s.wave() if s.act == "swim" else 0
    fin = fin or mix(body, "#000000", 0.15)
    ry = 6 if slim else 7.5
    _fluke(s, [(24, 16.5), (31, 10), (29.5, 16.5), (31, 23)], fin, w)
    s.poly([(10, 11 if slim else 9.5), (17, 7 if slim else 6), (22, 11)], fin)
    s.poly([(12, 22), (16, 26), (19, 22)], fin)
    m = s.ellipse(15, 16.5, 11, ry, body, edge=True)
    s.paint(s.m_ellipse(13, 16.5 + ry * 0.6, 9, ry * 0.45), belly, within=m)
    if pattern:
        pattern(s, m)
    s.ellipse(15, 18, 2.6, 1.6, mix(fin, "#ffffff", 0.2), rot=25)
    s.paint(s.m_line(9, 13, 9, 20), mix(body, "#000000", 0.3), within=m)
    s.eye(6, 14, size=2)
    s.px([(3, 18), (4, 18)], mix(body, "#000000", 0.45))


def dolphin(s: Sprite, body, belly):
    s.can("swim")
    w = s.wave() if s.act == "swim" else 0
    _fluke(s, [(24, 16), (31, 9), (29, 16), (31, 21)], body, w)
    s.poly([(14, 11), (20, 4), (21, 12)], body)
    m = s.ellipse(15, 17, 11.5, 6, body, edge=True)
    s.paint(s.m_ellipse(12, 20.5, 9, 2.8), belly, within=m)
    s.ellipse(1.8, 18.5, 3, 1.6, body)
    s.paint(s.m_ellipse(1.8, 19.5, 2.5, 0.8), belly, within=s.last)
    s.ellipse(14, 23, 4, 1.6, mix(body, "#000000", 0.15), rot=30)
    s.px([(4, 19), (5, 20), (6, 20)], mix(body, "#000000", 0.5))
    s.eye(7, 15)


def sea_turtle(s: Sprite, shell, skin, *, scutes=None):
    s.can("swim")
    w = s.wave() if s.act == "swim" else 0
    s.ellipse(9, 24 - w * 2, 6, 2.5, skin, rot=25 - w * 30)
    s.ellipse(24, 25, 3.5, 2, skin, rot=-20 + w * 15)
    m = s.ellipse(18, 17, 11, 7.5, shell, edge=True)
    for cx, cy in ((13, 15), (18, 13), (23, 15), (15, 19), (21, 19)):
        s.paint(s.m_ellipse(cx, cy, 2.2, 1.8), scutes or mix(shell, "#ffffff", 0.2), within=m)
    s.ellipse(18, 23.5, 10, 1.5, mix(skin, "#ffffff", 0.3))
    # Front flipper sweeps back along the shell (pointing up, it read as rabbit ears).
    s.ellipse(14 - w * 4, 23.5 - w * 1.5, 7, 2.4, skin, rot=-12 + w * 50, edge=True)
    s.ellipse(5.5, 16.5, 5, 4.2, skin, edge=True)
    s.paint(s.m_px([(4, 14), (7, 14), (6, 16), (3, 17)]), mix(skin, "#000000", 0.25))
    s.eye(3, 15)


def alligator(s: Sprite, body="#4a5a3a", belly="#e8e0b8"):
    s.can("walk", "swim")
    w = s.wave() if s.act in ("walk", "swim") else 0
    s.path([(20, 22), (26, 24 + w), (30, 22 + w * 1.5), (31, 17 + w * 2)], (2.8, 0.8), body)
    s.path([(20, 23), (22 - w * 1.5, 27), (24 - w * 1.5, 27)], 1.2, mix(body, "#000000", 0.2))
    s.path([(10, 23), (9 + w * 1.5, 27), (7 + w * 1.5, 27)], 1.2, mix(body, "#000000", 0.2))
    m = s.ellipse(15, 21.5, 8, 4, body)
    s.paint(s.m_ellipse(15, 24.6, 7, 1.6), belly, within=m)
    for x in (10, 13, 16, 19, 22, 25, 28):
        s.px([(x, 18 if x < 22 else 19 + (x - 22) // 3)], mix(body, "#000000", 0.4))
    s.path([(17, 24), (17 + w * 1.5, 28), (15 + w * 1.5, 28)], 1.2, body)
    s.path([(12, 24), (12 - w * 1.5, 28), (10 - w * 1.5, 28)], 1.2, body)
    s.ellipse(8, 18.5, 4.5, 3.6, body, edge=True)
    s.poly([(5, 18), (-1, 19.5), (-1, 22.5), (6, 22)], body)
    s.paint(s.m_line(0, 21, 6, 21), mix(body, "#000000", 0.5))
    s.px([(1, 22), (3, 22), (5, 22), (2, 20)], WHITE)
    s.ellipse(8.5, 15.5, 2, 1.6, body)
    s.eye(8, 15)


def turkey(s: Sprite):
    for i, c in enumerate(("#c8a06a", "#5a3e2a", "#8a6440", "#3e2a1e")):
        s.ellipse(20, 15, 11 - i * 1.7, 12 - i * 1.7, c, shade=False)
    s.can("walk")
    w = s.wave() if s.act == "walk" else 0
    a, b = max(0.0, w), max(0.0, -w)
    s.line(14, 25, 13 - round(a * 2), 30 - round(a * 1.5), "#c86a5a")
    s.line(18, 25, 19 - round(b * 2), 30 - round(b * 1.5), "#c86a5a")
    s.ellipse(16, 21, 7, 6.5, "#4e3a30")
    s.paint(s.m_px([(12, 19), (15, 18), (18, 20), (14, 22), (17, 23), (20, 22)]), "#8a6a3a")
    s.ellipse(19, 21, 4.5, 3.5, "#3a2a24", rot=-20, edge=True)
    s.path([(12, 18), (10, 13), (10, 9)], 1.6, "#7ab0d8")
    s.ellipse(9.5, 8, 3.5, 3.2, "#7ab0d8", edge=True)
    s.poly([(6.5, 7.5), (4, 9), (6.5, 9.5)], "#e8c890")
    s.path([(7, 10), (6.5, 13), (8, 15)], 0.8, "#d83a3a", shade=False)
    s.path([(11, 18), (11, 22)], 0.6, "#2a1e1a", shade=False)
    s.eye(8, 7)


def spider_top(s: Sprite, abdomen, legs, *, pattern=None, ceph=None, leg_bands=None, web=False):
    if web:
        for a in range(0, 360, 45):
            import math as _m
            s.line(16, 16, 16 + 16 * _m.cos(_m.radians(a)), 16 + 16 * _m.sin(_m.radians(a)), "#e6eef4")
        s.path([(16, 1), (14, 4), (18, 7)], 0.6, "#f4f4f0", shade=False)
        s.path([(16, 31), (18, 28), (14, 25)], 0.6, "#f4f4f0", shade=False)
    s.can("walk")
    w = s.wave() if s.act == "walk" else 0
    for i, (a, b, c) in enumerate([((14, 11), (8, 5), (5, 1)), ((13, 13), (6, 10), (2, 9)), ((13, 15), (6, 17), (2, 20)),
                                   ((14, 16), (9, 22), (6, 27))]):
        d = w * 1.5 * (1 if i % 2 else -1)
        c = (c[0], c[1] + d)
        m = s.path([a, b, c], 0.7, legs, shade=False, mirror=True)
        if leg_bands:
            s.paint(s.m_ellipse(b[0], b[1], 1.2, 1.2) | s.m_ellipse(c[0], c[1], 1.4, 1.4), leg_bands,
                    mirror=True, within=m)
    s.ellipse(16, 13, 4, 3.6, ceph or "#d8d4cc", edge=True)
    am = s.ellipse(16, 22, 6, 8, abdomen, edge=True)
    if pattern:
        pattern(s, am)
    s.eye(13, 12, size=1)
    s.eye(18, 12, size=1)
    s.px([(14, 11), (17, 11)], EYE)


def grasshopper(s: Sprite, body, stripe, *, legs=None):
    s.can("walk")
    legs = legs or body
    s.line(14, 22, 12, 28, legs)
    s.line(17, 22, 18, 28, legs)
    s.ellipse(20, 20, 9, 4, body)
    for x in (16, 20, 24):
        s.paint(s.m_line(x, 17, x, 23), stripe, within=s.last)
    s.ellipse(21, 17, 6, 2, mix(body, stripe, 0.3), rot=-8, edge=True)
    s.path([(19, 20), (26, 13), (29, 15), (27, 26)], 1.3, legs)
    s.paint(s.m_line(21, 18, 26, 14), stripe)
    s.ellipse(9, 17, 5, 5, body, edge=True)
    s.paint(s.m_ellipse(10, 14, 3.5, 1.4), stripe, within=s.last)
    s.line(7, 12, 3, 3, legs)
    s.line(9, 12, 9, 3, legs)
    s.eye(6, 15)
    if s.act == "walk" and s.f in (1, 2):
        _lift(s, 2 if s.f == 1 else 3)


def crab(s: Sprite, shell, claw, *, legs=None, stalks=2, big_claw=False, pattern=None, eye_big=False):
    s.can("walk")
    w = s.wave() if s.act == "walk" else 0
    legs = legs or mix(shell, "#000000", 0.2)
    for i, y in enumerate((19, 22, 25)):
        d = w * 1.3 * (1 if i % 2 else -1)
        s.path([(8, y), (3, y + 3 + d), (2, y + 6 + d)], 0.7, legs, shade=False)
        s.path([(24, y), (29, y + 3 - d), (30, y + 6 - d)], 0.7, legs, shade=False)
    if big_claw:
        s.path([(23, 18), (26, 13)], 1.4, claw)
        s.ellipse(25, 8.5, 6, 4.5, claw, rot=-20, edge=True)
        s.paint(s.m_poly([(26, 8), (32, 7), (32, 10)]), mix(claw, "#000000", 0.4))
        s.path([(9, 17), (6, 14)], 1, claw)
        s.ellipse(5.5, 12, 2, 1.6, claw)
    else:
        s.path([(9, 17), (6, 13)], 1.2, claw, mirror=True)
        s.ellipse(5.5, 10, 3.6, 3, claw, rot=-30, mirror=True, edge=True)
    top = 13 - stalks * 2
    s.line(12, 15, 12, top, legs, mirror=True)
    m = s.ellipse(16, 20, 10, 6.5, shell, edge=True)
    if pattern:
        pattern(s, m)
    if eye_big:
        s.ellipse(12, top - 1, 2, 2.2, EYE, mirror=True, shade=False)
        s.px([(11, top - 2)], WHITE, mirror=True)
    else:
        s.px([(11, top), (12, top)], EYE, mirror=True)
        s.px([(11, top)], WHITE, mirror=True)
    s.px([(15, 22), (16, 22)], "#1d1a20")


def horseshoe_crab(s: Sprite):
    s.path([(16, 22), (16, 31)], (1.2, 0.5), "#6a4a30")
    s.fill(s.m_ellipse(16, 15, 12.5, 11) & s.m_poly([(0, 0), (32, 0), (32, 19), (0, 19)]), "#8a6440", edge=True)
    s.poly([(8, 18), (24, 18), (21, 25), (11, 25)], "#7a5636", edge=True)
    s.paint(s.m_line(16, 6, 16, 18), "#6a4a30")
    s.paint(s.m_poly([(5, 17), (16, 12), (27, 17)]) & ~s.m_poly([(6, 18), (16, 13.5), (26, 18)]), "#6a4a30")
    for x in (12, 15, 18, 21):
        s.px([(x, 21)], "#5a3e26")
    s.eye(9, 11)
    s.eye(21, 11)


def snail_shell(s: Sprite, shell, spots):
    s.can("walk")
    stretch = s.cyc(0, 1, 2, 1) if s.act == "walk" else 0
    inside = s.act == "sleep"
    s.ellipse(15 - stretch / 2, 27, 12 + stretch / 2, 2.6, "#e8d8c0")
    m = s.ellipse(16, 17, 10, 10, shell, edge=True)
    s.poly([(20, 8), (25, 2), (24, 10)], shell, edge=True)
    for y in (11, 15, 19, 23):
        for x in range(8 + (y // 2) % 3, 26, 3):
            s.paint(s.m_px([(x, y), (x + 1, y)]), spots, within=m)
    s.paint(s.m_path([(16, 17), (19, 14), (22, 17), (19, 21), (14, 20), (12, 15)], 0.4), mix(shell, "#000000", 0.3), within=m)
    if inside:
        return
    s.ellipse(6 - stretch, 23, 5, 3.5, "#f0e0c8", edge=True)
    s.line(4 - stretch, 20, 3 - stretch, 16, "#f0e0c8")
    s.line(7 - stretch, 20, 8 - stretch, 16, "#f0e0c8")
    s.eye(4 - stretch, 22)


def jelly(s: Sprite, bell, *, rim=None, arms="#e8dcc8", tentacles=None, stripes=None):
    s.can("swim")
    w = s.wave() if s.act == "swim" else 0
    if tentacles:
        for x0 in (8, 13, 18, 23):
            s.path([(x0, 13), (x0 - 1 + w, 19), (x0 + 1 - w, 24), (x0 + w, 30)], 0.6, tentacles, shade=False)
    s.path([(14, 13), (13, 20), (15, 25)], 1.6, arms)
    s.path([(18, 13), (19, 20), (17, 24)], 1.6, arms)
    m = s.fill(s.m_ellipse(16, 14, 11 - w, 11 + w) & s.m_poly([(0, 0), (32, 0), (32, 15), (0, 15)]), bell, edge=True)
    if rim:
        s.paint(s.m_ellipse(16, 14, 11, 11) & ~s.m_ellipse(16, 14, 11, 8.5), rim, within=m)
    if stripes:
        for x in (8, 12, 16, 20, 24):
            s.paint(s.m_line(16, 4, x, 14), stripes, within=m)
    s.eye(12, 9)
    s.eye(18, 9)


def mantis(s: Sprite, c, wing, eyes):
    d = mix(c, "#000000", 0.2)
    s.line(18, 22, 14, 30, d)
    s.line(21, 22, 24, 30, d)
    s.line(23, 21, 29, 28, d)
    s.ellipse(23, 21, 8, 3.2, c, rot=-15)
    s.ellipse(24, 19, 6, 2.2, wing, rot=-15, edge=True)
    s.path([(17, 22), (13, 14)], 1.4, c)
    s.path([(12, 16), (8, 19), (7, 14)], 1.1, d)
    s.path([(14, 17), (11, 21), (10, 16)], 1.1, c)
    s.poly([(7, 6), (17, 6), (12, 14)], c, edge=True)
    s.ellipse(8, 6.5, 2.2, 2.2, eyes, shade=False)
    s.ellipse(16, 6.5, 2.2, 2.2, eyes, shade=False)
    s.px([(8, 6), (16, 6)], EYE)
    s.line(10, 5, 6, 0, d)
    s.line(14, 5, 18, 0, d)
