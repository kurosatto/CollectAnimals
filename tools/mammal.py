"""Four-legged mammals from the side, facing left: archetypes.quad.

Every pose is drawn fresh, part by part, from a skeleton. Each leg is two bones
(upper and lower leg) put in place by inverse kinematics from where its foot is
in the gait, then a paw or hoof. The torso is chest, barrel and haunch, so the
waist, shoulder and thigh read; the head has a skull, muzzle, chin, nose, mouth,
eye with a catchlight and ears that turn. Nothing is stretched, squashed or
rotated as an image: breathing swells the chest as it is drawn, a tail swishes
by bending its drawn curve, an ear flicks by drawing it at another angle.

Poses: idle (breathing, tail swish, an ear flick), walk (four-beat gait, head
nod), run (gallop, or a bounding lope for the low animals and a lumbering
gallop for bears), eat (grazing or nose to the ground), sit (dogs, cats, bears
and the low animals sit up; deer and sheep lie with the head up), look (head
turned to you), back (glance over the shoulder), groom (a dog scratches its
ear, a cat washes, a deer licks its flank, a bear scratches, a raccoon rubs its
hands) and sleep (curled up, or bedded down with the head on the flank).
"""
from __future__ import annotations

import math

import numpy as np

from archetypes import BLACK, EYE, NOSE, PINK, WHITE
from pixel import _XS, _YS, Sprite, mix

GROUND = 30.5

# The skeleton of each build. chest, barrel and haunch are ellipses (cx, cy, rx, ry);
# fore and hind are where each leg's upper bone starts (the elbow and the stifle),
# with the two bone lengths (upper, lower) and radii. head is the skull ellipse;
# snout runs from (dx, dy) to (dx, dy) off the head centre with radii (base, tip);
# neck joins the withers to the head. stride/lift shape the walk; paw or hoof the foot.
G = {
    "dog": dict(chest=(12.8, 19.2, 4.4, 4.3), barrel=(18.2, 19.2, 6.4, 3.3), haunch=(23.5, 18.8, 3.8, 3.9),
                fore=(12.2, 21.2), fore_l=(5.0, 4.4), fore_r=(1.25, 0.8), hind=(24.2, 21.0), hind_l=(5.1, 4.5),
                hind_r=(1.3, 0.8), head=(8.8, 12.4, 3.9, 3.4), snout=((-2.4, 1.3), (-6.9, 2.6), (1.85, 0.95)),
                neck=((13.2, 16.5), 2.6), ear_at=(1.0, -2.6), stride=4.4, lift=1.6, foot="paw", eye=(-1.8, -0.9),
                rest_y=12.4),
    "cat": dict(chest=(13.2, 21.0, 4.0, 3.8), barrel=(18.6, 21.0, 6.4, 3.2), haunch=(24.0, 20.6, 3.8, 3.9),
                fore=(12.8, 23.0), fore_l=(4.0, 3.7), fore_r=(1.2, 0.8), hind=(24.6, 22.8), hind_l=(4.2, 3.8),
                hind_r=(1.35, 0.8), head=(9.0, 15.6, 4.4, 3.9), snout=((-2.8, 1.4), (-4.9, 1.8), (1.75, 1.35)),
                neck=((13.4, 18.6), 2.7), ear_at=(0.6, -2.8), stride=4.0, lift=1.4, foot="paw", eye=(-2.0, -0.6),
                rest_y=15.6),
    "deer": dict(chest=(13.4, 17.4, 3.9, 4.2), barrel=(19.0, 17.4, 6.6, 3.5), haunch=(24.2, 16.9, 3.6, 4.0),
                 fore=(13.0, 19.6), fore_l=(5.6, 5.6), fore_r=(1.15, 0.7), hind=(24.8, 19.4), hind_l=(5.6, 6.0),
                 hind_r=(1.25, 0.7), head=(8.4, 8.6, 3.2, 2.8), snout=((-2.0, 1.4), (-6.0, 2.6), (1.7, 1.05)),
                 neck=((13.6, 14.6), 2.0), ear_at=(1.6, -2.0), stride=5.0, lift=2.2, foot="hoof", eye=(-1.0, -0.6),
                 rest_y=8.6),
    "sheep": dict(chest=(13.0, 18.8, 4.6, 4.8), barrel=(19.0, 18.6, 7.0, 4.6), haunch=(24.2, 18.4, 4.0, 4.8),
                  fore=(13.0, 22.0), fore_l=(4.6, 4.2), fore_r=(1.3, 0.8), hind=(24.6, 21.8), hind_l=(4.6, 4.4),
                  hind_r=(1.4, 0.8), head=(8.6, 11.2, 3.4, 3.2), snout=((-2.0, 1.4), (-5.0, 2.4), (1.9, 1.5)),
                  neck=((13.0, 16.2), 2.6), ear_at=(1.4, -1.6), stride=4.0, lift=1.6, foot="hoof", eye=(-1.0, -0.8),
                  rest_y=11.2),
    "bear": dict(chest=(12.2, 19.6, 5.2, 5.4), barrel=(18.6, 19.6, 7.4, 5.6), haunch=(24.6, 19.8, 4.8, 5.4),
                 hump=(13.2, 14.8, 4.2, 2.6), fore=(12.0, 23.2), fore_l=(4.0, 3.6), fore_r=(2.1, 1.6),
                 hind=(24.8, 23.4), hind_l=(3.8, 3.6), hind_r=(2.2, 1.6), head=(8.0, 17.0, 4.3, 3.9),
                 snout=((-2.6, 1.4), (-5.6, 2.2), (2.0, 1.45)), neck=((12.4, 17.6), 3.8), ear_at=(1.4, -3.0),
                 stride=4.0, lift=1.4, foot="bear", eye=(-1.6, -1.0), rest_y=17.0),
    "low": dict(chest=(13.6, 22.2, 4.0, 3.8), barrel=(19.4, 21.4, 7.0, 4.4), haunch=(24.6, 21.6, 4.2, 4.4),
                fore=(13.2, 25.0), fore_l=(3.0, 2.7), fore_r=(1.3, 0.95), hind=(25.0, 25.0), hind_l=(3.0, 2.8),
                hind_r=(1.45, 0.95), head=(8.6, 20.8, 3.9, 3.3), snout=((-2.6, 1.2), (-6.8, 2.2), (1.8, 0.85)),
                neck=((13.6, 20.2), 3.0), ear_at=(1.4, -2.6), stride=3.4, lift=1.2, foot="paw", eye=(-1.8, -0.9),
                rest_y=20.8),
}
HOOFED = ("deer", "sheep")


def _smooth(u):
    u = min(1.0, max(0.0, u))
    return u * u * (3 - 2 * u)


def _ik(root, foot, l1, l2, bend):
    """The joint between two bones from root to foot; bend +1 puts it behind (+x)."""
    dx, dy = foot[0] - root[0], foot[1] - root[1]
    d = max(abs(l1 - l2) + 1e-3, min(l1 + l2 - 1e-3, math.hypot(dx, dy)))
    a = math.atan2(dy, dx)
    b = math.acos(max(-1.0, min(1.0, (l1 * l1 + d * d - l2 * l2) / (2 * l1 * d))))
    t = a - bend * b
    return root[0] + l1 * math.cos(t), root[1] + l1 * math.sin(t)


def _gait(p, x0, stride, lift, duty):
    """Where a foot is at gait phase p: on the ground sliding back, or swinging forward."""
    p %= 1.0
    if p < duty:
        return x0 - stride / 2 + stride * (p / duty), 0.0
    u = (p - duty) / (1 - duty)
    return x0 + stride / 2 - stride * _smooth(u), lift * math.sin(math.pi * u)


def _rot(dx, dy, deg):
    a = math.radians(deg)
    c, s_ = math.cos(a), math.sin(a)
    return dx * c - dy * s_, dx * s_ + dy * c


class _Q:
    """One frame of a quadruped: where every part is."""


def quad(s: Sprite, fur, light=WHITE, *, build="dog", ears="point", ear_in=PINK, tail="bushy",
         tail_col=None, tail_tip=None, nose=NOSE, muzzle=None, head=None, legs=None, feet=None,
         belly=True, eye_col=EYE, markings=None, behind=None, front=None):
    """Side view of a four-legged animal facing left. `build` sets the skeleton;
    behind, markings and front are called with (s, b) to add patterns, horns and
    antlers: b holds "head" (x, y, rx, ry), "snout", "neck", "body" (x, y, rx, ry)
    and "view" ("side", "front" or "back") for the pose being drawn."""
    g = G[build]
    s.can("walk", "eat", "sit", "look", "back", "run", "groom")
    # No warp at all: breathing is drawn (the chest swells), never a stretch of the image.
    s.base, s.fwd, s.xs, s.ys = None, None, _XS, _YS
    act, t = s.act, s.t
    head_c = head or fur
    legs_c = legs or fur
    tail_col = tail_col or fur
    muzzle = muzzle or light
    dark = lambda c, k=0.28: mix(c, "#1a1420", k)  # noqa: E731
    hoofed = build in HOOFED
    foot_c = feet or (dark(legs_c, 0.55) if hoofed else dark(legs_c, 0.12))
    breath = 0.5 - 0.5 * math.cos(2 * math.pi * t) if act in ("idle", "sit", "look", "back", "sleep") else 0.0

    q = _pose(s, g, build, act, t, hoofed)
    hx, hy = q.head
    hrx, hry = g["head"][2:]
    sx0, sy0 = g["snout"][0]
    sx1, sy1 = g["snout"][1]
    hd = q.hdir  # -1: facing left (normal), +1: turned back over the shoulder
    b = dict(head=(hx, hy, hrx, hry),
             snout=((hx - hd * -sx0, hy + sy0), (hx - hd * -sx1, hy + sy1), g["snout"][2]),
             neck=(q.withers, (hx + (1.0 if hd < 0 else -1.0), hy + 1.0), g["neck"][1]),
             body=q.body_ell, fx=q.fore_root[0], bx=q.hind_root[0], top=q.fore_root[1], leg=g["fore_r"][1],
             view=q.view, build=build, act=act)
    if q.head_down:
        b["head_down"] = True

    if behind:
        behind(s, b)

    # far side: legs, ear, a tail that hangs behind the body
    for leg in q.far_legs:
        _draw_leg(s, leg, dark(legs_c), dark(foot_c, 0.2), g, build, edge=False)
    if q.tail_behind:
        _tail(s, tail, q, tail_col, tail_tip, build)
    if q.view != "front" and ears != "none":
        _ear(s, ears, *q.ear_far, dark(head_c), None, q.ear_tilt, hd, far=True)

    # torso
    _torso(s, g, q, fur, light, belly, breath, build, dark)
    if not q.tail_behind:
        _tail(s, tail, q, tail_col, tail_tip, build)

    # near legs
    for leg in q.near_legs:
        _draw_leg(s, leg, legs_c, foot_c, g, build, edge=True)

    # neck and head
    if q.view != "front":
        (nx0, ny0), nr = q.withers, g["neck"][1]
        s.path([(nx0, ny0), ((nx0 + hx) / 2, (ny0 + hy) / 2 + 0.6), (hx - hd * 0.8, hy + 1.2)], (nr, nr * 0.85), fur)
        if belly and build in ("dog", "sheep", "cat", "deer") and q.view == "side":
            s.fill(s.m_path([(nx0 - 2.4 + q.dx_neck, ny0 + 3.4), (hx + 0.2, hy + 2.2)], nr * 0.5) & s.last, light,
                   shade=False)
    if q.view == "front":
        _head_front(s, g, build, hx, hy, hrx, hry, head_c, muzzle, nose, ears, ear_in, eye_col, q)
    else:
        _head_side(s, g, build, hx, hy, hrx, hry, hd, head_c, muzzle, nose, ears, ear_in, eye_col, q)
    if markings:
        markings(s, b)
    if q.view != "front" and ears != "none":
        _ear(s, ears, *q.ear_near, head_c, ear_in, q.ear_tilt, hd)
    _eye_and_nose(s, g, build, hx, hy, hrx, hry, hd, nose, eye_col, q, light)
    if front:
        front(s, b)
    for extra in q.after:  # a paw raised over the head (washing, scratching)
        extra(s, legs_c, foot_c)
    # Some species add a face detail after this (a white chin, a whisker) where the
    # head stood in the first drawing: carry it to where the head is in this pose.
    from archetypes import BUILDS
    ohx, ohy = BUILDS[build]["head"][:2]
    if q.view == "side" and hd < 0:
        dx, dy = hx - ohx, hy - ohy
        s.fwd, s.xs, s.ys = (lambda x, y, dx=dx, dy=dy: (x + dx, y + dy)), _XS - dx, _YS - dy


# --------------------------------------------------------------------------- the skeleton per pose
def _pose(s, g, build, act, t, hoofed):
    q = _Q()
    q.view, q.hdir, q.head_down, q.after = "side", -1, False, []
    q.tail_behind = True
    q.ear_tilt = 0.0
    q.dx_neck = 0.0
    cx, cy = 0.0, 0.0             # how far the whole torso moves (bob, gallop)
    lean = 0.0                    # gallop: chest and haunch apart (+) or gathered (-)
    hx, hy = g["head"][:2]
    stride, lift = g["stride"], g["lift"]
    fore_x, hind_x = g["fore"][0] - 0.3, g["hind"][0] + 0.4
    q.tail_a, q.tail_curl = 0.0, 0.0  # tail angle / curl offsets
    feet = None
    low_body = 0.0
    q.sit = q.lie = q.curl = False

    if act == "walk":
        # four-beat walk: near hind, near fore, far hind, far fore
        duty = 0.62
        ph = dict(nh=t, nf=t + 0.25, fh=t + 0.5, ff=t + 0.75)
        feet = {k: _gait(p, fore_x if k[1] == "f" else hind_x, stride, lift, duty) for k, p in ph.items()}
        cy = 0.35 * math.cos(4 * math.pi * t)
        nod = (1.0 if hoofed else 0.5) * math.sin(4 * math.pi * (t + 0.1))
        hy += nod
        q.tail_a = 6 * math.sin(2 * math.pi * t)
    elif act == "run":
        if build == "low":
            # bound: the hind feet land together where the fore feet were, back arching
            duty = 0.38
            ph = dict(nf=t, ff=t + 0.06, nh=t + 0.5, fh=t + 0.56)
            arch = math.sin(2 * math.pi * t)
            lean = 1.4 * arch
            cy = -0.9 * max(0.0, math.sin(2 * math.pi * (t + 0.25)))
        else:
            # rotary gallop: hinds, then fores, a moment of suspension gathered up
            duty = 0.34 if build != "bear" else 0.42
            ph = dict(nh=t, fh=t + 0.1, nf=t + 0.42, ff=t + 0.52)
            lean = (2.0 if build != "bear" else 1.0) * math.cos(2 * math.pi * (t - 0.2))
            cy = -1.1 * max(0.0, math.sin(2 * math.pi * (t - 0.75))) - 0.3
        k = 1.6 if build not in ("bear", "low") else 1.4
        feet = {kk: _gait(p, (fore_x - lean if kk[1] == "f" else hind_x + lean), stride * k, lift * 1.8, duty)
                for kk, p in ph.items()}
        hx -= 1.4
        hy += 1.6 - 0.8 * math.sin(2 * math.pi * t)
        if hoofed:
            hy -= 1.2
        q.tail_a = -22 if build in ("dog", "cat") else -25
        q.tail_curl = -0.5
        q.ear_tilt = 35 if build in ("dog", "cat", "deer", "low") else 15
    elif act == "eat":
        # head down to the grass (grazers chew; the rest sniff along)
        ny = GROUND - g["head"][3] - 1.2
        hx -= 1.4 if hoofed else 2.2
        if hoofed:
            hy = ny - 0.7 * abs(math.sin(2 * math.pi * t))  # nibble, lift a touch, nibble
        else:
            hy = ny - 0.4 * abs(math.sin(4 * math.pi * t))
            hx += 0.8 * math.sin(2 * math.pi * t)            # sniffing along the ground
        q.head_down = True
        q.tail_a = 8 * math.sin(2 * math.pi * t)
    elif act in ("idle", "look", "back"):
        q.tail_a = 10 * math.sin(2 * math.pi * t) if build in ("dog", "cat", "low") else 0
        if build == "deer":  # the short tail flicks now and then
            q.tail_a = -30 * max(0.0, math.sin(2 * math.pi * (t - 0.55)) * (0.55 < t < 1.0))
        # an ear flicks back and forth once in the cycle
        q.ear_tilt = 28 * max(0.0, math.sin(2 * math.pi * (t * 3 - 1.25))) if 0.42 < t < 0.75 else 0
        if act == "look":
            q.view = "front"
            hx += 1.2
            hy -= 0.4
        if act == "back":
            q.hdir = 1
            hx = g["chest"][0] + 0.4
            hy = g["head"][1] - (0.5 if build != "low" else 1.6)
            q.dx_neck = 3
    elif act == "sit":
        q.sit = True
    elif act == "groom":
        q.sit = build in ("dog", "cat", "bear", "low")
    elif act == "sleep":
        q.lie = True
        q.curl = build in ("dog", "cat", "low")

    chest, barrel, haunch = list(g["chest"]), list(g["barrel"]), list(g["haunch"])
    fore_root, hind_root = list(g["fore"]), list(g["hind"])
    withers = list(g["neck"][0])
    chest[0] -= lean * 0.5
    fore_root[0] -= lean * 0.5
    withers[0] -= lean * 0.5
    haunch[0] += lean * 0.5
    hind_root[0] += lean * 0.5
    for part in (chest, barrel, haunch, fore_root, hind_root, withers):
        part[1] += cy
    hx -= lean * 0.5
    if act in ("walk", "run", "idle", "look", "back", "eat"):
        hy += cy if act != "eat" else 0

    q.near_legs, q.far_legs = [], []
    if q.sit or q.lie:
        hx, hy = _rest_pose(q, g, build, act, t, chest, barrel, haunch, fore_root, hind_root, withers, hx, hy)
    else:
        if feet is None:
            feet = dict(nf=(fore_x, 0.0), ff=(fore_x + 1.3, 0.0), nh=(hind_x, 0.0), fh=(hind_x + 1.3, 0.0))
            if act == "eat" and hoofed:
                feet["nf"] = (fore_x - 1.0, 0.0)
        for key, near in (("nf", True), ("ff", False), ("nh", True), ("fh", False)):
            fx_, fy_ = feet[key]
            fore = key[1] == "f"
            root = fore_root if fore else hind_root
            off = 0.0 if near else 1.3
            foot = (fx_ + (0 if near else 0.0), GROUND - 0.6 - fy_)
            leg = dict(root=(root[0] + off, root[1]), foot=foot, fore=fore, lifted=fy_ > 0.2,
                       swing=fy_)
            (q.near_legs if near else q.far_legs).append(leg)
        if act == "groom" and hoofed:
            # a deer turns its head back along its side to lick its flank
            q.hdir = 1
            hx = barrel[0] + 2.5 + 0.8 * math.sin(2 * math.pi * t)
            hy = barrel[1] - barrel[3] - 1.0 + 0.7 * abs(math.sin(4 * math.pi * t))
            q.groom_lick = True
    q.chest, q.barrel, q.haunch = chest, barrel, haunch
    q.fore_root, q.hind_root, q.withers = tuple(fore_root), tuple(hind_root), tuple(withers)
    q.head = (hx, hy)
    hrx, hry = g["head"][2:]
    ex, ey = g["ear_at"]
    if q.hdir > 0:
        ex = -ex
    q.ear_near = (hx + ex, hy + ey)
    q.ear_far = (hx + ex + (1.4 if q.hdir < 0 else -1.4), hy + ey + 0.2)
    left = chest[0] - chest[2]
    right = haunch[0] + haunch[2]
    q.body_ell = ((left + right) / 2, barrel[1], (right - left) / 2, max(chest[3], barrel[3], haunch[3]))
    q.tail_root = (haunch[0] + haunch[2] * 0.82, haunch[1] - haunch[3] * 0.5)
    q.tail_behind = q.tail_behind and False
    if q.sit and build in ("dog", "cat", "bear", "low"):
        q.tail_root = (haunch[0] + haunch[2] * 0.6, GROUND - 1.2)
    if q.lie and not q.curl:
        q.tail_root = (haunch[0] + haunch[2] * 0.8, haunch[1] - haunch[3] * 0.2)
    return q


def _rest_pose(q, g, build, act, t, chest, barrel, haunch, fore_root, hind_root, withers, hx, hy):
    """Sitting up, lying down, curled asleep, and the grooming poses built on them."""
    upright = build in ("dog", "cat", "bear", "low")
    hry = g["head"][3]
    if q.sit and upright:
        # On the haunches: the haunch rests on the ground with the hind foot forward
        # under it, the chest rises over straight front legs, the head comes up.
        hgt = haunch[3]
        haunch[:] = [haunch[0] - 3.0, GROUND - hgt * 0.95, hgt * 1.05, hgt * 0.95]
        rise = {"dog": 6.0, "cat": 5.0, "bear": 4.5, "low": 4.0}[build]
        chest[:] = [chest[0] + 2.4, chest[1] - rise * 0.55, chest[2] * 0.95, chest[3] * 1.05]
        barrel[:] = [(chest[0] + haunch[0]) / 2 + 1.2, (chest[1] + haunch[1]) / 2, chest[2] * 0.85,
                     (haunch[1] - chest[1]) / 2 + 0.8]
        q.barrel_rot = -62
        withers[:] = [chest[0] + 0.8, chest[1] - chest[3] * 0.6]
        hx, hy = chest[0] - 2.6, chest[1] - chest[3] - hry * 0.7
        fore_root[:] = [chest[0] - chest[2] * 0.45, chest[1] + chest[3] * 0.35]
        hind_root[:] = [haunch[0] - 0.6, haunch[1] + 0.2]
        fl = sum(g["fore_l"])
        q.near_legs = [dict(root=tuple(fore_root), foot=(fore_root[0] - 0.4, GROUND - 0.6), fore=True)]
        q.far_legs = [dict(root=(fore_root[0] + 1.4, fore_root[1]), foot=(fore_root[0] + 0.9, GROUND - 0.6),
                           fore=True)]
        # the folded hind leg: hock flat on the ground, the foot ahead of the haunch
        q.near_legs.insert(0, dict(hind_sit=True, at=(haunch[0] - haunch[2] * 0.6, GROUND - 0.6)))
        if fl < GROUND - fore_root[1] - 0.6:
            fore_root[1] = GROUND - 0.6 - fl + 0.3
        q.tail_behind = False
        if act == "sit":
            hy += 0.4 * math.sin(2 * math.pi * t)
            q.ear_tilt = 25 * max(0.0, math.sin(2 * math.pi * (t * 3 - 1.25))) if 0.42 < t < 0.75 else 0
            q.tail_a = 8 * math.sin(2 * math.pi * t)
        else:
            _groom(q, g, build, t, chest, haunch, fore_root, hx, hy)
            hx, hy = q.groom_head
    elif q.sit:
        # deer and sheep: lying down, legs folded under, head up and alert (chewing)
        _lie(q, g, build, chest, barrel, haunch, withers)
        hx, hy = hx + 1.5, g["head"][1] + (GROUND - g["haunch"][1] - g["haunch"][3]) * 0.75 + 0.3 * math.sin(4 * math.pi * t)
        hy = min(hy, chest[1] - chest[3] - 2.5)
        q.ear_tilt = 25 * max(0.0, math.sin(2 * math.pi * (t * 3 - 1.25))) if 0.42 < t < 0.75 else 0
    else:
        # asleep
        _lie(q, g, build, chest, barrel, haunch, withers)
        if q.curl:
            # curled nose to tail: the head lies along the front of the body on the paws
            hx, hy = chest[0] - 1.2, GROUND - hry - 0.2
            q.tail_behind = False
            q.curl_tail = True
        elif build == "bear":
            hx, hy = chest[0] - chest[2] - 1.5, GROUND - hry - 0.1
        else:
            # deer, sheep: bedded down, the head lowered with the chin on the ground
            hx, hy = chest[0] - chest[2] - 1.8, GROUND - hry - 0.3
        q.head_down = True
    return hx, hy


def _lie(q, g, build, chest, barrel, haunch, withers):
    """Lower the torso onto the ground, legs folded under."""
    bottom = max(chest[1] + chest[3], barrel[1] + barrel[3], haunch[1] + haunch[3])
    drop = GROUND - 0.2 - bottom
    for part in (chest, barrel, haunch, withers):
        part[1] += drop
    if q.curl:
        # curled: shorter and rounder
        chest[0] += 2.0
        haunch[0] -= 2.0
        barrel[2] -= 1.6
        for part in (chest, barrel, haunch):
            part[3] += 1.0
            part[1] -= 1.0
    q.near_legs = [dict(folded=True, at=(chest[0] - chest[2] * 0.5, GROUND - 0.7), fore=True),
                   dict(folded=True, at=(haunch[0] - haunch[2] * 0.8, GROUND - 0.7), fore=False)]
    q.far_legs = []


def _groom(q, g, build, t, chest, haunch, fore_root, hx, hy):
    """Groom, sitting up. Sets q.groom_head and adds the moving paw to q.after."""
    hry = g["head"][3]
    if build == "dog":
        # scratching behind the ear with a hind foot, fast, the head tipped toward it
        q.groom_head = (hx + 0.6, hy + 1.2)
        q.ear_tilt = 30
        hip = (haunch[0] - 0.4, haunch[1] - 0.6)
        sc = math.sin(2 * math.pi * t * 3)  # three scratches per cycle
        foot = (q.groom_head[0] + 5.2 + 0.7 * sc, q.groom_head[1] + 0.2 - 0.9 * sc)
        q.near_legs = [L for L in q.near_legs if not L.get("hind_sit")]

        def paw(s, legs_c, foot_c, hip=hip, foot=foot):
            knee = _ik(hip, foot, 5.0, 4.8, -1)
            c = mix(legs_c, "#1a1420", 0.14)
            s.fill(s.m_path([hip, knee], (2.2, 1.1)) | s.m_path([knee, foot], (1.0, 0.8)), c, edge=True)
            s.ellipse(foot[0] - 0.4, foot[1], 1.5, 1.0, foot_c, edge=True)
        q.after.append(paw)
        q.tail_a = 5 * sc
    else:
        # washing: a front paw comes up to the mouth (cat licks it, then wipes the face),
        # a bear scratches its chest, a raccoon rubs its hands together
        u = t
        if build == "cat":
            q.groom_head = (hx + 0.2 + 0.3 * math.sin(2 * math.pi * u), hy + 1.0 + 0.5 * math.sin(4 * math.pi * u))
            px = q.groom_head[0] - 3.0 + (0.8 * math.sin(2 * math.pi * u) if u > 0.5 else 0.0)
            py = q.groom_head[1] + hry * 0.6 - (1.2 * math.sin(math.pi * (u - 0.5) * 2) if u > 0.5 else 0.6)
        elif build == "bear":
            q.groom_head = (hx + 0.6, hy - 0.4)
            px = chest[0] - 1.0 + 0.6 * math.sin(6 * math.pi * u)
            py = chest[1] + 1.0 + 1.2 * math.sin(6 * math.pi * u)
        else:
            q.groom_head = (hx + 0.4, hy + 0.8)
            px = chest[0] - chest[2] - 0.4 + 0.7 * math.sin(4 * math.pi * u)
            py = chest[1] + chest[3] * 0.2

        q.near_legs = [L for L in q.near_legs if not (L.get("fore") and not L.get("hind_sit"))]
        sh = (fore_root[0] + 0.4, fore_root[1] - 1.4)
        q.ear_tilt = 0

        def paw(s, legs_c, foot_c, sh=sh, p=(px, py), fore_r=g["fore_r"]):
            elbow = _ik(sh, p, 3.2, 3.2, 1)
            s.path([sh, elbow], (fore_r[0], fore_r[0] * 0.9), legs_c, edge=True)
            s.path([elbow, p], (fore_r[0] * 0.9, fore_r[1]), legs_c, edge=True)
            s.ellipse(p[0], p[1], 1.3, 1.1, foot_c, edge=True)
        q.after.append(paw)


# --------------------------------------------------------------------------- drawing parts
def _torso(s, g, q, fur, light, belly, breath, build, dark):
    chest, barrel, haunch = q.chest, q.barrel, q.haunch
    rot = getattr(q, "barrel_rot", 0)
    br = 0.35 * breath
    m = s.m_ellipse(chest[0], chest[1], chest[2] + br * 0.5, chest[3] + br) \
        | s.m_ellipse(barrel[0], barrel[1], barrel[2], barrel[3] + br * 0.6, rot=rot) \
        | s.m_ellipse(haunch[0], haunch[1], haunch[2], haunch[3])
    if "hump" in g and not q.sit:
        hx, hy, hrx, hry = g["hump"]
        m |= s.m_ellipse(hx + (chest[0] - g["chest"][0]), hy + (chest[1] - g["chest"][1]), hrx, hry)
    if q.curl:
        m |= s.m_ellipse(barrel[0], barrel[1] - 0.6, barrel[2] + 1.0, barrel[3] + 0.4 + br)
    body = s.fill(m, fur)
    q.body_mask = body
    if build == "sheep":
        # wool: a scatter of soft curls over the fleece
        rng = np.random.default_rng(7)
        pts = [(barrel[0] + rng.uniform(-barrel[2], barrel[2]), barrel[1] + rng.uniform(-barrel[3], barrel[3] * 0.6))
               for _ in range(26)]
        s.paint(s.m_px([(round(x), round(y)) for x, y in pts]), mix(fur, "#ffffff", 0.35), within=body)
        s.paint(s.m_px([(round(x) + 1, round(y) + 1) for x, y in pts[::2]]), dark(fur, 0.14), within=body)
    if belly:
        if q.sit and build in ("dog", "cat", "bear", "low"):
            s.fill(s.m_ellipse(chest[0] - chest[2] * 0.5, chest[1] + 0.5, chest[2] * 0.6, chest[3] * 1.0) & body,
                   light, shade=False)
        else:
            # a pale underside and throat, left unshaded so it doesn't read as a stripe
            low_y = barrel[1] + barrel[3]
            s.fill(s.m_ellipse(barrel[0] - 1.0, low_y - 0.2, barrel[2] * 0.8, barrel[3] * 0.42) & body, light,
                   shade=False)
            s.fill(s.m_ellipse(chest[0] - chest[2] * 0.6, chest[1] + 0.6, chest[2] * 0.45, chest[3] * 0.7) & body,
                   light, shade=False)
    if False:
        # muscle: the line of the shoulder blade and of the thigh, in a slightly darker fur
        line = dark(fur, 0.16)
        cx, cy, crx, cry = chest
        s.paint(s.m_path([(cx + 1.6, cy - cry * 0.75), (cx + 0.6, cy + 0.2), (cx - 0.6, cy + cry * 0.55)], 0.45),
                line, within=body)
        hx, hy, hrx, hry = haunch
        s.paint(s.m_path([(hx - hrx * 0.7, hy - hry * 0.35), (hx - hrx * 0.45, hy + hry * 0.35),
                          (hx + 0.2, hy + hry * 0.85)], 0.45), line, within=body)


def _draw_leg(s, leg, col, foot_c, g, build, edge):
    hoofed = build in HOOFED
    if leg.get("folded"):
        # a leg folded under the body while lying: just the bent wrist / hock and the foot
        x, y = leg["at"]
        if hoofed:
            s.ellipse(x, y, 2.2, 1.0, col, edge=edge)
            s.ellipse(x - 2.0, y + 0.1, 0.9, 0.7, foot_c)
        else:
            s.ellipse(x, y, 2.4, 1.2, col, edge=edge)
            _paw(s, x - 1.6, y + 0.1, foot_c, build, flat=True)
        return
    if leg.get("hind_sit"):
        # sitting: the long hind foot flat on the ground ahead of the haunch
        x, y = leg["at"]
        s.ellipse(x + 1.2, y - 0.2, 3.0, 1.2, col, edge=edge)
        _paw(s, x - 1.6, y + 0.1, foot_c, build, flat=True)
        return
    fore = leg["fore"]
    root, foot = leg["root"], leg["foot"]
    l1, l2 = g["fore_l"] if fore else g["hind_l"]
    r1, r2 = g["fore_r"] if fore else g["hind_r"]
    if build in ("bear", "low") or fore:
        bend = -1 if fore else 1
    else:
        bend = 1  # the hock points back
    # A planted fore leg stands nearly straight; lift it and the wrist folds.
    if fore and not leg.get("lifted"):
        dist = math.dist(root, foot)
        l1, l2 = l1 * dist / (l1 + l2) * 1.02 + 0.01, l2 * dist / (l1 + l2) * 1.02 + 0.01
    joint = _ik(root, foot, l1, l2, bend)
    # upper leg: thick at the body, the lower leg slim down to the foot
    s.fill(s.m_path([root, joint], (r1 * 1.15, r1 * 0.8)) | s.m_path([joint, foot], (r2 * 1.05, r2 * 0.85)), col,
           edge=edge)
    if hoofed:
        # dew claws and hoof: the pastern, then a dark wedge
        dx = 0.3 if not leg.get("lifted") else 0.6
        s.poly([(foot[0] - 1.2 - dx, foot[1] + 0.9), (foot[0] - 0.9, foot[1] - 0.6), (foot[0] + 0.8, foot[1] - 0.6),
                (foot[0] + 0.9, foot[1] + 0.9)], foot_c, shade=False)
    elif build == "bear":
        _paw(s, foot[0] - (0.6 if fore else 1.0), foot[1] + 0.2, foot_c, build, big=not fore)
    else:
        _paw(s, foot[0] - 0.5, foot[1] + 0.2, foot_c, build, lifted=leg.get("lifted"))


def _paw(s, x, y, col, build, flat=False, big=False, lifted=False):
    w = 1.7 if build != "bear" else (2.6 if big else 2.0)
    m = s.ellipse(x, y, w, 0.95 if not lifted else 0.85, col)
    # toes: dark gaps between the toes, and claws on a bear
    s.paint(s.m_px([(round(x - w * 0.35), round(y))]), mix(col, "#1a1420", 0.4), within=m)
    if build == "bear":
        s.px([(round(x - w) - 1, round(y)), (round(x - w) - 1, round(y) - 1)], "#e8e0d0")


def _tail(s, kind, q, col, tip, build):
    if kind == "none":
        return
    x, y = q.tail_root
    if getattr(q, "curl_tail", False):
        # asleep, curled: the tail wraps around the front of the body, over the paws
        pts = [(x, y + 1.2), (x - 2, GROUND - 1.3), (x - 7, GROUND - 0.9), (x - 12, GROUND - 1.2), (x - 14, GROUND - 2.2)]
        if kind in ("short", "cotton"):
            pts = pts[:2]
        r = {"bushy": (1.6, 2.2), "ringed": (1.6, 1.8), "skunk": (2.2, 2.8), "rat": (0.9, 0.5)}.get(kind, (1.1, 0.9))
        m = s.path(pts, r, col, edge=True)
        if tip:
            s.paint(s.m_ellipse(pts[-1][0], pts[-1][1], 2.0, 1.8), tip, within=m)
        if kind == "ringed":
            for k in range(1, 4):
                px_ = pts[0][0] - k * 3.2
                s.paint(s.m_poly([(px_, GROUND - 4), (px_ + 1, GROUND - 4), (px_ + 1, GROUND), (px_, GROUND)]),
                        tip or BLACK, within=m)
        return
    spec = {
        # length, start angle (0 = straight back, 90 = straight down), curl per unit, radii
        "bushy": (10.5, 48, 3.0, (1.3, 2.5, 1.5)),
        "long": (10.0, 82, -8, (1.0, 0.95, 0.85)),
        "short": (2.6, -25, 0, (1.4, 1.1, 0.9)),
        "cotton": (2.4, 55, 0, (1.3, 1.2, 1.0)),
        "ringed": (8.0, 52, 3.0, (1.5, 2.0, 1.5)),
        "skunk": (12.0, -70, -11, (1.7, 3.2, 2.6)),
        "rat": (10.0, 70, -7, (1.0, 0.7, 0.35)),
    }[kind]
    length, a0, curl, (r0, r1, r2) = spec
    a0 += q.tail_a
    curl += q.tail_curl * 6
    if q.sit and build in ("dog", "cat", "bear", "low"):
        # sitting: the tail lies along the ground in front of the hind foot
        a0, curl = {"skunk": (-80, -10), "short": (-10, 0)}.get(kind, (178, 0))
        a0 += q.tail_a * 0.4
    n = 7
    pts = [(x, y)]
    a = a0
    for _ in range(n):
        x += math.cos(math.radians(a)) * length / n
        y += math.sin(math.radians(a)) * length / n
        y = min(y, GROUND - r2 * 0.6)
        pts.append((x, y))
        a += curl * length / n
    mid = len(pts) // 2
    m = s.path(pts[:mid + 1], (r0, r1), col, edge=True)
    m |= s.path(pts[mid:], (r1, r2), col, edge=True)
    if kind == "ringed":
        for k in range(1, len(pts) - 1, 2):
            s.paint(s.m_ellipse(pts[k][0], pts[k][1], 1.0, 2.6, rot=-math.degrees(math.atan2(pts[k + 1][1] - pts[k][1],
                                                                                              pts[k + 1][0] - pts[k][0]))),
                    tip or BLACK, within=m)
    elif kind == "skunk":
        s.paint(s.m_path(pts[1:-1], (0.7, 1.4)), tip or WHITE, within=m)
    elif kind == "bushy":
        s.paint(s.m_path(pts[1:-2], 0.5), mix(col, "#1a1420", 0.18), within=m)  # the darker line along the top
        if tip:
            s.paint(s.m_ellipse(pts[-1][0], pts[-1][1], r2 + 0.9, r2 + 1.2), tip, within=m)
    elif tip and kind in ("long", "short", "cotton"):
        s.paint(s.m_ellipse(pts[-1][0], pts[-1][1], r2 + 0.6, r2 + 1.0), tip, within=m)
    elif kind == "cotton" or (kind == "short" and tip is None):
        pass


def _ear(s, kind, x, y, col, inner, tilt, hd, far=False):
    """An ear standing on the head at (x, y), turned back by `tilt` degrees."""
    shade = inner is not None
    flip = 1 if hd < 0 else -1  # turned back means toward +x when facing left

    def tr(pts):
        return [(x + dx * -flip, y + dy) for dx, dy in (_rot(px, py, tilt) for px, py in pts)] if flip < 0 else \
               [(x + dx, y + dy) for dx, dy in (_rot(px, py, tilt) for px, py in pts)]
    if kind in ("point", "big", "tuft"):
        h = {"point": 3.6, "big": 4.6, "tuft": 3.8}[kind]
        w = {"point": 1.9, "big": 2.2, "tuft": 1.9}[kind]
        s.poly(tr([(-w, 1.4), (0.3, -h), (w + 0.2, 1.2)]), col, shade=shade, edge=not far)
        if inner:
            s.poly(tr([(-w + 1.0, 0.8), (0.3, -h + 1.8), (w - 0.6, 0.8)]), inner, shade=False)
        if kind == "tuft":
            tip = tr([(0.4, -h - 1.2), (0.5, -h - 2.2)])
            s.px([(round(a), round(b)) for a, b in tip], BLACK)
        elif kind == "big":
            # the dark back-edge of a fox or coyote ear
            s.paint(s.m_poly(tr([(-0.4, -h + 1.0), (0.3, -h), (0.9, -h + 1.0)])), mix(col, "#1a1420", 0.45))
    elif kind in ("round", "small"):
        r = 2.0 if kind == "round" else 1.5
        (cx, cy), = tr([(0.2, -0.6)])
        s.ellipse(cx, cy, r, r * 0.95, col, shade=shade, edge=not far)
        if inner:
            s.ellipse(cx - 0.3 * flip, cy + 0.2, r * 0.5, r * 0.5, inner, shade=False)
    elif kind in ("mule", "side"):
        rx, ry = (4.0, 2.0) if kind == "mule" else (2.9, 1.4)
        (cx, cy), = tr([(1.6, -0.6)])
        rot = (-32 + tilt) * flip if flip > 0 else (32 - tilt)
        s.ellipse(cx, cy, rx, ry, col, rot=rot, shade=shade, edge=not far)
        if inner:
            s.ellipse(cx + 0.2 * flip, cy, rx * 0.6, ry * 0.45, inner, rot=rot, shade=False)


def _head_side(s, g, build, hx, hy, hrx, hry, hd, head_c, muzzle, nose, ears, ear_in, eye_col, q):
    (sx0, sy0), (sx1, sy1), (sr0, sr1) = g["snout"]
    if hd > 0:
        sx0, sx1 = -sx0, -sx1
    skull = s.ellipse(hx, hy, hrx, hry, head_c, edge=True)
    snout = s.path([(hx + sx0, hy + sy0), (hx + sx1, hy + sy1)], (sr0, sr1), head_c)
    # the muzzle and chin, paler; the jaw line under the cheek
    jaw = s.m_path([(hx + sx0 * 0.6, hy + sy0 + sr0 * 0.55), (hx + sx1 - hd * 0.3, hy + sy1 + sr1 * 0.55)],
                   (sr0 * 0.62, sr1 * 0.6))
    s.fill((jaw | s.m_ellipse(hx + sx0 * 0.4, hy + hry * 0.62, hrx * 0.55, hry * 0.36)) & (skull | snout), muzzle,
           shade=False)
    q.skull = skull | snout
    if build == "cat":
        # whisker pad and the whisker dots
        s.paint(s.m_ellipse(hx + sx1 + hd * -0.6, hy + sy1 + 0.3, 1.4, 1.0), mix(muzzle, "#ffffff", 0.3),
                within=snout)
    # cheek fluff on cats and bears, the ruff on a dog
    if build in ("cat", "bear", "dog") and q.view == "side":
        s.paint(s.m_px([(round(hx + hrx * 0.6 * -hd), round(hy + hry * 0.75))]), mix(head_c, "#1a1420", 0.2),
                within=skull)


def _eye_and_nose(s, g, build, hx, hy, hrx, hry, hd, nose, eye_col, q, light):
    if q.view == "front":
        return
    (sx0, sy0), (sx1, sy1), (sr0, sr1) = g["snout"]
    ex, ey = g["eye"]
    if hd > 0:
        sx1, ex = -sx1, -ex - 1
    tipx, tipy = hx + sx1, hy + sy1
    # nose: a dark pad at the tip, with a glint on top
    nx = round(tipx - hd * 0.0 + (0.2 if hd < 0 else -0.6))
    ny = round(tipy - sr1 * 0.6)
    big = build in ("dog", "bear", "low", "deer", "sheep")
    pts = [(nx, ny), (nx + (1 if hd < 0 else -1), ny)] + ([(nx, ny + 1)] if big else [])
    s.px(pts, nose)
    if big:
        s.px([(nx + (1 if hd < 0 else -1), ny)], mix(nose, "#ffffff", 0.35))
    # mouth: a short dark line back from under the nose
    my = round(tipy + sr1 * 0.55)
    mouth = [(nx + (1 if hd < 0 else -1) * k, my) for k in range(1, 3 if build != "cat" else 2)]
    s.px(mouth, mix(light, "#1a1420", 0.55))
    if build in ("cat", "dog", "low"):
        # whisker spots
        wx = nx + (2 if hd < 0 else -2)
        s.px([(wx, my - 1)], mix(light, "#1a1420", 0.35))
    eye_x, eye_y = round(hx + ex), round(hy + ey)
    if q.head_down and q.lie:
        return  # asleep: eyes closed by the sleep pose itself
    s.eye(eye_x, eye_y, color=eye_col)
    s.eye_box(eye_x, eye_y, eye_x + 1, eye_y + 1)
    if build in ("deer", "sheep"):
        # the pale ring around a deer's eye
        ring = [(eye_x - 1, eye_y + 1), (eye_x, eye_y + 2), (eye_x + 1, eye_y + 2)]
        s.paint(s.m_px(ring), mix(light, "#ffffff", 0.2), within=q.skull)


def _head_front(s, g, build, hx, hy, hrx, hry, head_c, muzzle, nose, ears, ear_in, eye_col, q):
    """The head turned to face you: both ears, both eyes, the muzzle between them."""
    long_face = build in HOOFED
    fw, fh = hrx * 0.82, hry * (1.05 if not long_face else 1.0)
    if ears != "none":
        for side in (-1, 1):
            ex = hx + side * (fw * 0.85)
            ey = hy - fh * 0.75
            tilt = side * 28 + (q.ear_tilt if side > 0 else 0)
            if ears in ("mule", "side"):
                rx, ry = (3.6, 1.8) if ears == "mule" else (2.6, 1.3)
                s.ellipse(ex + side * 1.8, ey + 0.4, rx, ry, head_c, rot=side * -20, edge=True)
                s.ellipse(ex + side * 2.0, ey + 0.4, rx * 0.6, ry * 0.45, ear_in, rot=side * -20, shade=False)
            elif ears in ("round", "small"):
                r = 2.0 if ears == "round" else 1.5
                s.ellipse(ex, ey - 0.4, r, r, head_c, edge=True)
                s.ellipse(ex, ey - 0.2, r * 0.5, r * 0.5, ear_in, shade=False)
            else:
                h = {"point": 4.0, "big": 5.2, "tuft": 4.0}[ears]
                pts = [(-1.8, 1.0), (0.0, -h), (1.8, 1.0)]
                rp = [(ex + a, ey + b) for a, b in (_rot(px, py, side * 14) for px, py in pts)]
                s.poly(rp, head_c, edge=True)
                ip = [(ex + a, ey + b) for a, b in (_rot(px * 0.5, py * 0.6 + 0.3, side * 14) for px, py in pts)]
                s.poly(ip, ear_in, shade=False)
                if ears == "tuft":
                    tx_, ty_ = rp[1]
                    s.px([(round(tx_), round(ty_) - 1)], BLACK)
    face = s.ellipse(hx, hy, fw, fh, head_c, edge=True)
    my = hy + fh * (0.45 if not long_face else 0.55)
    mrx, mry = (fw * 0.55, fh * 0.5) if not long_face else (fw * 0.45, fh * 0.7)
    s.ellipse(hx, my + (0.0 if not long_face else 1.4), mrx, mry, muzzle, edge=True)
    q.skull = face | s.last
    # eyes
    eo = round(fw * 0.5)
    ey = round(hy - fh * 0.2)
    for x in (round(hx) - eo - 1, round(hx) + eo):
        s.eye(x, ey, color=eye_col)
        s.eye_box(x, ey, x + 1, ey + 1)
    # nose and mouth
    ny = round(my + (0.0 if not long_face else 1.6) - mry * 0.35)
    s.px([(round(hx) - 1, ny), (round(hx), ny)], nose)
    if build in ("dog", "bear", "low", "deer", "sheep"):
        s.px([(round(hx) - 1, ny + 1), (round(hx), ny + 1)], mix(nose, "#000000", 0.1))
    s.px([(round(hx) - 1, ny + 2), (round(hx), ny + 2)], mix(muzzle, "#1a1420", 0.45))
