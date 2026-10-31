"""Body plans for the sprites. Each function draws one kind of animal onto a Sprite,
with colours and features passed in so one plan covers many species."""
from __future__ import annotations

import math

import numpy as np

from pixel import N, PAD_TOP, PAD_X, _XS, _YS, Sprite, mix

PINK = "#f2a7b4"

# slug -> drawing function; filled by @sprite in make_sprites.py and species_nc.py
S: dict = {}


def sprite(slug):
    def deco(fn):
        S[slug] = fn
        return fn
    return deco

NOSE = "#3a2a33"
WHITE = "#fbf7ef"
BLACK = "#2b2630"
EYE = "#1d1428"


# --------------------------------------------------------------------------- mammals
def _lift(s: Sprite, dy: int):
    """Raise everything but the bottom row of feet (a bob in the stride)."""
    keep_col, keep_reg = s.col[28 + PAD_TOP:].copy(), s.reg[28 + PAD_TOP:].copy()
    s.shift(0, -dy)
    feet = keep_reg > 0
    s.col[28 + PAD_TOP:][feet], s.reg[28 + PAD_TOP:][feet] = keep_col[feet], keep_reg[feet]


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
    s.can("walk", "sit", "look", "back")
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
    if lying:
        # Curled up low: the head drops onto the front paws.
        drop = round(ground - 0.4 - (by + bry))
        by, py_, ty = by + drop, py_ + drop, ty + drop
        hy = min(ground - hry - 0.3, hy + drop + 1.5)
        hx += 1
    # Bounding gait: gather, push off, stretch out in the air, land.
    reach, push, lift = ((0, 0, 0), (0.6, 1.8, 1), (2.4, 2.6, 2), (1.6, 0.4, 1))[f] if act == "walk" else (0, 0, 0)
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
        up = (0, 1, 0, 1)[f]
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
    ys, xs = np.where(mask)
    pts = [(x - PAD_X, y - PAD_TOP) for x, y in zip(xs, ys) if (x * 7 + y * 13 + seed) % every == 0]
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
    sway = (0, 0.6, 1, 0.4)[f] if act == "walk" else 0
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
    s.can("walk")
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
    _tail(s, tail, bx + brx - 1, by - bry * 0.3 + 0.8 * w, tail_col, tail_tip)
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
    elif s.act == "walk" and s.f % 2 == 0:
        _lift(s, 1)


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
    hump = (0, 1.6, 0.6, -0.4)[f] if act == "walk" else 0
    if swim:
        # stretched out, level, flippers sweeping up and down
        spine = [(28.5, 19 + w), (22, 18.6), (14, 18.2), (8.5, 18.5)]
        rad = (1.6, 4.0)
        head = (5.5, 18, 3.3, 2.8)
    elif act == "sit":
        # banana: belly on the ground, both ends curled up (the tail end bobs a little)
        lift = (0, 0.5, 1, 0.5)[f]
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
                if body[y + PAD_TOP, x + PAD_X] and (x * 7 + y * 13) % 11 == 0 and k < spots:
                    s.paint(s.m_px([(x, y)]), mix(fur, "#000000", 0.4))
                    k += 1
    if blotch:
        blotch(s, body)

    # near front flipper
    if swim:
        s.ellipse(fx + 1.5, fy + 2 - w, 3.2, 1.1, flipper, rot=20 + 15 * w)
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


def _slim(s: Sprite, head_c, head_to, head_k, body_c, body_to, body_kx, body_ky, body_bottom, neck):
    """Re-proportion a bird drawn in a plan's chubby coordinates: the head (around
    head_c) shrinks by head_k and moves to head_to; the body (around body_c) stretches
    by body_kx and flattens by body_ky to body_to; the legs below body_bottom lengthen
    to keep the feet on the ground. neck = (x, y) where head and body blend."""
    hx, hy = head_c
    tx, ty = head_to
    bx, by = body_c
    ux, uy = body_to
    nx, ny = neck
    low = uy + body_ky * (body_bottom - by)  # where the body's bottom ends up
    def fwd(x, y):  # noqa: E306
        hxp, hyp = tx + head_k * (x - hx), ty + head_k * (y - hy)
        bxp = ux + body_kx * (x - bx)
        byp = np.where(y <= body_bottom, uy + body_ky * (y - by),
                       low + (y - body_bottom) * (31 - low) / (31 - body_bottom))
        k = _smooth((ny - y) / 2.5) * _smooth((nx - x) / 2.5)
        return k * hxp + (1 - k) * bxp, k * hyp + (1 - k) * byp
    s.set_warp(fwd)


def bird(s: Sprite, body, belly, *, head=None, wing=None, tail_col=None, beak="cone",
         beak_col="#4a3d3a", legs="#c99060", tail="mid", crest=None, eye_col=EYE,
         face=None, wing_mark=None, belly_mark=None, big=False):
    """Side view, facing left. Walks on alternating legs and flies with its wing
    beating up and down (legs tucked). Drawn in round, roomy coordinates (which the
    species' own markings use too) and then slimmed to field-guide proportions: a
    small head, a long body and tail, and longer legs."""
    s.can("walk", "fly")
    flying = s.act == "fly"
    w = s.wave()
    head = head or body
    wing = wing or mix(body, "#000000", 0.15)
    tail_col = tail_col or wing
    cy = 19 if not big else 18
    _slim(s, (11, 11), (10, cy - 4), 0.56, (16.5, cy + 1), (17.5, cy + 3), 1.12, 0.62, cy + 8, (17.5, cy - 3))
    if flying and w > -0.5:
        with s.unwarped():
            _flight_wing(s, cy, w, mix(wing, "#1a1420", 0.3), dx=2.5)
    if tail == "mid":
        s.poly([(20, cy), (29, cy - 6), (31, cy - 3), (23, cy + 4)], tail_col)
    elif tail == "long":
        s.poly([(20, cy), (30, cy - 12), (32, cy - 9), (23, cy + 4)], tail_col)
    elif tail == "short":
        s.poly([(20, cy), (27, cy - 3), (28, cy + 1), (22, cy + 4)], tail_col)
    elif tail == "fan":
        s.poly([(20, cy), (29, cy - 9), (31, cy - 1), (23, cy + 4)], tail_col)
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
    _beak(s, beak, beak_col)
    s.eye(8, 10, color=eye_col, shine=None)


def _flight_wing(s: Sprite, cy, w, col, dx=0):
    """A long, pointed wing through the beat: raised high, spread level along the body,
    and swept down below it. In canvas coordinates (after the bird is slimmed)."""
    y = cy + 2  # the shoulder
    if w > 0.5:
        pts = [(14, y), (15, y - 6), (17, y - 12), (20, y - 17), (23.5, y - 20), (24, y - 15), (23.5, y - 7), (22, y)]
    elif w < -0.5:
        pts = [(14, y + 1), (15, y + 6), (17, y + 11), (19.5, y + 13.5), (21, y + 10), (22, y + 1)]
    else:
        pts = [(13, y - 0.5), (18, y - 2.5), (25, y - 3), (30, y - 1.5), (25, y + 0.5), (18, y + 1.5)]
    return s.poly([(x + dx, y) for x, y in pts], col, edge=not dx)


def _bird_legs(s: Sprite, xs, top, ground, col, w, toes=(-1,), toe_dy=0):
    """Two thin legs with toes; when walking, one lifts and steps forward at a time."""
    for i, x in enumerate(xs):
        step = max(0.0, w if i == 0 else -w)
        foot = ground - round(step * 1.5)
        fx = x - round(step * 1.5)
        s.line(x, top, fx, foot, col)
        s.px([(fx + t, foot + toe_dy) for t in toes], col)


def _wing_beat(s: Sprite, x, y, w, col, size=1.0):
    """The near wing through a beat: raised (w=1), spread level (0) and swept down (-1)."""
    if w > 0.5:
        return s.ellipse(x - 1, y - 6 * size, 3.4 * size, 7 * size, col, rot=25, edge=True)
    if w < -0.5:
        return s.ellipse(x - 1, y + 4 * size, 3.2 * size, 6 * size, col, rot=-25, edge=True)
    return s.ellipse(x + 1, y - 1, 8 * size, 2.6 * size, col, rot=-8, edge=True)


def _far_wing(s: Sprite, x, y, w, col, size=1.0):
    """The far wing, darker and behind the body, peeking out when raised or level."""
    if w > 0.5:
        s.ellipse(x + 2, y - 7 * size, 3 * size, 6 * size, col, rot=40)
    elif abs(w) <= 0.5:
        s.ellipse(x + 3, y - 3, 6 * size, 2.2 * size, col, rot=-20)


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


def owl(s: Sprite, body, face, *, tufts=False, eye_col="#f6c33c", belly=None, beak="#e8c070",
        disk_edge=None, bars=None):
    """Perched, an owl faces you; it flies in profile (see _owl_flying)."""
    s.can("fly")
    flying = s.act == "fly"
    belly = belly or mix(body, WHITE, 0.4)
    if flying:
        return _owl_flying(s, body, face, belly, tufts, eye_col, beak, bars)
    if tufts:
        s.poly([(6, 9), (5, 0.5), (12, 5)], body, mirror=True)
    if not flying:
        s.px([(12, 30), (14, 30)], "#b88a4a", mirror=True)
    s.ellipse(16, 20, 10.5, 10.5, body)
    s.ellipse(16, 23, 6.5, 6.5, belly)
    if bars:
        for y in range(19, 30, 2):
            s.paint(s.m_line(11, y, 21, y), bars, within=s.last)
    if not flying:
        s.ellipse(5.5, 20, 3, 6.5, mix(body, "#000000", 0.18), rot=-10, mirror=True)
    s.ellipse(16, 10, 10, 8, body, edge=True)
    s.ellipse(11.5, 10.5, 4.5, 4.8, face, mirror=True, edge=disk_edge is not None)
    if eye_col:
        s.ellipse(11.5, 10.5, 2.4, 2.4, eye_col, mirror=True, shade=False)
        s.px([(11, 10), (12, 10), (11, 11), (12, 11)], EYE, mirror=True)
        s.px([(11, 10)], WHITE, mirror=True)
    else:
        s.ellipse(11.5, 10.5, 1.9, 2.2, EYE, mirror=True, shade=False)
        s.px([(11, 9)], WHITE, mirror=True)
    s.poly([(14.5, 13), (17.5, 13), (16, 16.5)], beak, shade=False)
    s.eye_box(9, 8, 14, 13, mirror=True)


def _owl_flying(s: Sprite, body, face, belly, tufts, eye_col, beak, bars):
    """An owl flying left in profile: a round head with the facial disk at the front,
    broad rounded wings beating slowly, legs tucked under a short tail."""
    w = s.wave()
    wc = mix(body, "#000000", 0.15)
    y = 18  # the shoulder

    def wing(dx, col):
        if w > 0.5:
            pts = [(13, y), (13.5, y - 6), (16, y - 11), (20, y - 13.5), (23.5, y - 12), (24.5, y - 6), (23, y)]
        elif w < -0.5:
            pts = [(13, y + 1), (14, y + 6), (17, y + 10), (21, y + 10.5), (23, y + 7), (23, y + 1)]
        else:
            pts = [(12, y - 1), (17, y - 3.5), (25, y - 4), (30, y - 2), (26, y + 1), (18, y + 2)]
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
    s.can("walk", "fly")
    flying = s.act == "fly"
    w = s.wave()
    neck = neck or body
    head = head or neck
    wc = wing or mix(body, "#000000", 0.12)
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
    _slim(s, (10, 11), (9.5, 15), 0.62, (17, 23), (17.5, 24.5), 1.05, 0.72, 29.5, (15, 17.5))
    if flying:
        _far_wing(s, 21, 20, w, mix(body, "#1a1420", 0.35))
    else:
        _ripples(s, s.f if s.act == "swim" else 0)
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
    _slim(s, (9.5, 7), (9.5, 9.5), 0.72, (19, 23), (19, 24.5), 1.05, 0.75, 29.5, (13, 15))
    if flying:
        _far_wing(s, 23, 20, w, "#4e4036")
    else:
        _ripples(s, s.f if s.act == "swim" else 0, ((2, 30), (6, 29), (25, 30), (29, 29)))
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
    down = s.act == "fly" and s.f % 2 == 1
    _slim(s, (12, 11), (11.5, 13), 0.68, (16, 18), (16.5, 19), 1.0, 0.85, 29, (15, 15))
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


def pelican(s: Sprite):
    """Standing, with a walking and a flying pose."""
    s.can("walk", "fly")
    flying = s.act == "fly"
    w = s.wave()
    if flying:
        _far_wing(s, 22, 19, w, "#2f2b2d", 1.1)
    s.poly([(25, 17), (31, 15), (30, 21)], "#3f3b3d")
    if not flying:
        _bird_legs(s, (15, 19), 24, 28, "#3d3a3c", w if s.act == "walk" else 0, toes=(-2, -1, 0), toe_dy=1)
    s.ellipse(18.5, 20, 9.5, 6, "#6f6a6c")
    s.ellipse(16, 22.5, 5.5, 3.4, "#8a8486")
    if flying:
        m = _wing_beat(s, 21, 18, w, "#b9b4ac", 1.1)
    else:
        m = s.ellipse(20.5, 18, 7.5, 3.8, "#b9b4ac", rot=-10, edge=True)
    s.paint(s.m_poly([(24, 16), (29, 15), (28, 21), (24, 21)]), "#3f3b3d", within=m)
    for x in range(16, 24, 3):
        s.paint(s.m_line(x, 17, x + 2, 20), "#8f8a84", within=m)
    s.path([(12, 20), (10, 15), (12, 10)], 2.4, "#5a3a2e")
    s.paint(s.m_path([(13, 19), (11.5, 15), (13, 11)], 0.6), "#f4efe2")
    s.ellipse(12.5, 7.5, 4.4, 3.8, "#f4efe2", edge=True)
    s.paint(s.m_ellipse(13, 5.2, 3, 1.4), "#f2d878", within=s.last)
    s.poly([(10, 6.5), (-1, 9), (0, 10.5), (10, 9)], "#d9a050")
    s.poly([(10, 9), (0, 10.5), (3, 14), (10, 12.5)], "#6a4a3e")
    s.px([(0, 10)], "#c25a4a")
    s.eye(11, 6)


def vulture(s: Sprite, *, head_col, body="#2f2a2e", ruff=None, wing_patch=None, beak="#e8dccb"):
    bird(s, body, mix(body, "#ffffff", 0.08), head=head_col, wing=mix(body, "#ffffff", 0.06),
         beak="hook", beak_col=beak, legs="#b8a8a0", tail="mid",
         wing_mark=(lambda s2, m: s2.paint(s2.m_ellipse(21, 21.5, 5, 1.4, rot=-15), wing_patch, within=m))
         if wing_patch else None)
    if ruff:
        s.path([(12, 17), (16, 17.5), (19, 15.5)], 1.6, ruff)


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
    w = s.wave() if s.act == "walk" else 0
    pts = [(25, 28.5), (14, 28.8), (7, 27), (5.5, 23.5), (9, 20.5), (17, 20), (24, 21.5), (25.5, 24.5),
           (21, 26), (16, 25), (14, 21), (15, 17), (13.5, 13)]
    pts = [(x + w * 0.9 * math.sin(i * 1.3), y) for i, (x, y) in enumerate(pts)]
    r = 2.6
    if rattle:
        for i, (x, y) in enumerate([(27, 28), (29, 27), (30.3, 25.3)]):
            s.ellipse(x, y, 1.4, 1.2, "#d9c08a" if i % 2 == 0 else "#b89b62")
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
    ys, xs = np.where(mask)
    if not len(xs):
        return
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
    k = {"fly": (1, 0.6, 0.25, 0.6)[s.f], "sleep": 0.25}.get(s.act, 1)
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
    flap = (0, 14, 0, -14)[s.f] if s.act == "fly" else 0
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
def star(s: Sprite, color, *, arms=0.45, dots=WHITE, rot=-90):
    x, y = _XS - 16, _YS - 16.5
    ang = np.arctan2(y, x) - math.radians(rot)
    r = np.hypot(x, y)
    rr = 14.5 * ((1 - arms) + arms * (0.5 + 0.5 * np.cos(5 * ang)) ** 1.6)
    m = s.fill(r <= rr, color, edge=True)
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
    stretch = (0, 1, 2, 1)[s.f] if s.act == "walk" else 0
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
