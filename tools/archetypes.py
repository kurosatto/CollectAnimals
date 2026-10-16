"""Body plans for the sprites. Each function draws one kind of animal onto a Sprite,
with colours and features passed in so one plan covers many species."""
from __future__ import annotations

import math

import numpy as np

from pixel import _XS, _YS, Sprite, mix

PINK = "#f2a7b4"

# slug -> drawing function; filled by @sprite in make_sprites.py and species_nc.py
S: dict = {}


# --------------------------------------------------------------------------- animation
# The habitat animates each animal with a few frames drawn from the same plan:
# s.pose is "idle", "walk" (frames 0-1), "sleep", "fly" (0 level, 1 up, 2 down)
# or "swim" (0-1). Plans that don't move a part for a pose just draw it as idle;
# every plan closes its eyes when asleep (Sprite.eye).
def _swing(s: Sprite, a=1.0):
    """How far a leg swings forward on this walking frame (0 when not walking)."""
    if s.pose != "walk":
        return 0.0
    return a if s.frame == 0 else -a


def _wing(s: Sprite, x, y, col, *, size=1.0, far=False):
    """A wing spread from the shoulder at (x, y) for the flying frames."""
    k = size
    if far:
        col = mix(col, "#1a1420", 0.3)
        x, y = x + 2.5, y - 1
    if s.frame == 1:    # up
        pts, r = [(x, y), (x + 2 * k, y - 6 * k), (x + 3.5 * k, y - 12 * k)], (3.0 * k, 1.3)
    elif s.frame == 2:  # down
        pts, r = [(x, y + 1), (x + 2.5 * k, y + 6 * k), (x + 3.5 * k, y + 10 * k)], (2.8 * k, 1.2)
    else:               # level, gliding
        pts, r = [(x, y), (x + 5 * k, y - 2.5 * k), (x + 10 * k, y - 4 * k)], (3.0 * k, 1.2)
    return s.path(pts, r, col, edge=not far)


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
def mammal(s: Sprite, fur, light=WHITE, *, ears="point", ear_in=PINK, tail="long",
           tail_col=None, tail_tip=None, nose=NOSE, muzzle=None, belly=True, feet=None,
           head=None, head_r=(9, 7.5), blush=True, behind=None, markings=None, eye_col=EYE):
    """Front-facing chibi: big head, small body, tail peeking out on the right."""
    tail_col = tail_col or fur
    head = head or fur
    muzzle = muzzle or light
    if behind:
        behind(s)

    # tail
    if tail == "long":
        s.path([(21, 27), (26, 24), (28, 18), (27, 14)], (1.8, 1.4), tail_col)
        if tail_tip:
            s.paint(s.m_ellipse(27, 14.5, 2, 2.5), tail_tip, within=s.last)
    elif tail == "bushy":
        s.ellipse(25, 19, 4.2, 7.5, tail_col, rot=15)
        if tail_tip:
            s.paint(s.m_ellipse(27, 13, 3.5, 3.5), tail_tip, within=s.last)
    elif tail == "ringed":
        m = s.ellipse(25, 19, 3.6, 7.5, tail_col, rot=12)
        for y in (13, 17, 21, 25):
            s.paint(s.m_poly([(18, y), (32, y - 2), (32, y - 0.5), (18, y + 1.5)]), tail_tip or BLACK, within=m)
    elif tail == "squirrel":
        m = s.path([(20, 27), (26, 25), (28, 18), (26, 9), (21, 6)], (3.2, 4.2), tail_col)
        if tail_tip:
            s.paint(m & ~s.m_path([(20, 27), (26, 25), (28, 18), (26, 9), (21, 6)], (2.2, 3.0)), tail_tip, within=m)
    elif tail == "short":
        s.ellipse(22.5, 24, 2.2, 2, tail_col)
        if tail_tip:
            s.paint(s.m_ellipse(23.5, 23, 1.2, 1.2), tail_tip, within=s.last)
    elif tail == "cotton":
        s.ellipse(23, 27, 2.5, 2.2, tail_col)
    elif tail == "rat":
        s.path([(21, 27), (26, 28), (29, 25), (29, 21)], (1.3, 0.6), tail_col)
    elif tail == "skunk":
        m = s.ellipse(24.5, 16, 5.5, 9.5, tail_col, rot=10)
        s.paint(s.m_ellipse(24.5, 15, 1.8, 8.5, rot=10), tail_tip or WHITE, within=m)

    # body
    s.ellipse(16, 24, 7, 5.5, fur)
    if belly:
        s.ellipse(16, 25.5, 4, 3.5, light)
    foot = feet or mix(fur, "#000000", 0.15)
    if s.pose == "walk":
        # one foot up, then the other
        s.ellipse(12, 29 - (s.frame == 0), 2.4, 1.6, foot)
        s.ellipse(20, 29 - (s.frame == 1), 2.4, 1.6, foot)
    else:
        s.ellipse(12, 29, 2.4, 1.6, foot, mirror=True)

    # ears
    _ears(s, ears, fur if head == fur else head, ear_in)

    # head
    rx, ry = head_r
    s.ellipse(16, 13, rx, ry, head, edge=True)
    if markings:
        markings(s)
    s.ellipse(16, 17, 4.2, 2.8, muzzle)
    s.px([(15, 15), (16, 15)], nose)
    s.px([(15, 16), (16, 16)], mix(muzzle, nose, 0.35))
    s.eye(11, 12, color=eye_col, mirror=True)
    if blush:
        s.blush(9, 15, mirror=True)


def _ears(s: Sprite, kind, fur, inner):
    if kind == "point":
        s.poly([(7.5, 10), (8, 1.5), (14, 6)], fur, mirror=True)
        s.poly([(9, 8), (9.3, 4), (12, 6.5)], inner, mirror=True, shade=False)
    elif kind == "big":
        s.poly([(6.5, 10), (6, 0.5), (14, 5.5)], fur, mirror=True)
        s.poly([(8, 8), (7.6, 3), (12, 6)], inner, mirror=True, shade=False)
    elif kind == "tuft":
        s.poly([(7.5, 10), (8, 2.5), (14, 6)], fur, mirror=True)
        s.poly([(9, 8), (9.2, 4.5), (12, 6.5)], inner, mirror=True, shade=False)
        s.px([(8, 1), (8, 2), (7, 0)], BLACK, mirror=True)
    elif kind == "round":
        s.ellipse(8.5, 6, 3.4, 3.4, fur, mirror=True)
        s.ellipse(8.5, 6, 1.8, 1.8, inner, mirror=True, shade=False)
    elif kind == "small":
        s.ellipse(9, 6.5, 2.3, 2.3, fur, mirror=True)
        s.ellipse(9, 6.5, 1.0, 1.0, inner, mirror=True, shade=False)
    elif kind == "long":
        s.ellipse(11.5, 4.5, 2.4, 6, fur, rot=-8, mirror=True)
        s.ellipse(11.5, 4.8, 1.0, 4.5, inner, rot=-8, mirror=True, shade=False)
    elif kind == "xlong":
        s.ellipse(11, 3.8, 2.4, 7, fur, rot=-12, mirror=True)
        s.ellipse(11, 4.2, 1.0, 5.2, inner, rot=-12, mirror=True, shade=False)
        s.paint(s.m_ellipse(10.2, -1.5, 3, 2.6, rot=-12), BLACK, mirror=True)
    elif kind == "mule":
        s.ellipse(5.5, 8, 4.6, 2.6, fur, rot=-20, mirror=True)
        s.ellipse(5.8, 8, 2.8, 1.2, inner, rot=-20, mirror=True, shade=False)
    elif kind == "side":
        s.ellipse(6.5, 9, 3, 2, fur, rot=-25, mirror=True)
        s.ellipse(6.7, 9, 1.5, 0.8, inner, rot=-25, mirror=True, shade=False)


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
         belly=True, eye_col=EYE, blush=True, markings=None, behind=None, front=None):
    """Side view of a four-legged animal walking left. `build` sets the proportions;
    behind, markings and front are called with (s, build dict) to add patterns, horns
    and antlers at the right places."""
    b = BUILDS[build]
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

    lying = s.pose == "sleep"
    if lying:
        s.shift_y = max(0, round(ground - (by + bry) - 2))
    sw = _swing(s, 1.8)
    for x, back, k in ((b["fx"] + 2.2, False, -1), (b["bx"] + 1.6, True, 1)):
        if not lying:
            _leg(s, x, b["top"], ground, b["leg"], far(legs), back, build, far(feet) if feet else None, k * sw)
    _tail(s, tail, bx + brx - 1, by - bry * 0.3, tail_col, tail_tip)
    ear_x = hx + (0.8 if build == "bear" else 2.6)
    _side_ear(s, ears, ear_x - 1, hy - hry + 0.6, far(head), None)

    for x, back, k in ((b["fx"], False, 1), (b["bx"], True, -1)):
        if not lying:
            _leg(s, x, b["top"], ground, b["leg"], legs, back, build, feet, k * sw)
    body = s.ellipse(bx, by, brx, bry, fur)
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
    if lying:
        s.closed_eye(ex, ey)
    else:
        s.px([(ex, ey), (ex + 1, ey), (ex, ey + 1), (ex + 1, ey + 1)], eye_col)
        s.px([(ex, ey)], "#ffffff")
    if blush:
        s.px([(ex + 1, ey + 2), (ex + 2, ey + 2)], "#f59aa8")
    if front:
        front(s, b)


def _leg(s: Sprite, x, top, ground, r, col, back, build, feet, swing=0.0):
    """swing moves the foot forward (negative, toward the head) or back."""
    lift = 0.8 if swing < 0 else 0  # the leg swinging forward is off the ground
    if back and build in ("deer", "dog", "cat", "sheep"):
        # back legs bend at the hock
        pts = [(x, top - 1), (x + 1.4 + swing * 0.5, top + (ground - top) * 0.45), (x + 0.4 + swing, ground - 0.8 - lift)]
    else:
        pts = [(x, top - 1), (x - 0.2 + swing, ground - 0.8 - lift)]
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
             flipper=None, belly=True):
    """Seal / sea lion sitting up, front view."""
    flipper = flipper or mix(fur, "#000000", 0.2)
    s.ellipse(10, 29, 4, 1.8, flipper, rot=20, mirror=True)
    s.ellipse(16, 21, 9, 8.5, fur)
    if belly:
        s.ellipse(16, 23, 5.5, 6, light)
    s.ellipse(6.5, 22, 2, 4.5, flipper, rot=25, mirror=True)
    s.ellipse(16, 11, 8.5, 7.5, fur, edge=True)
    if spots:
        s.paint(s.m_px(spots), mix(fur, "#000000", 0.4))
    if ears:
        s.px([(8, 9), (8, 10)], flipper, mirror=True)
    s.ellipse(16, 15, 4.5, 2.8, light)
    s.eye(10, 10, size=3, mirror=True)
    s.px([(10, 10)], WHITE, mirror=True)
    if proboscis:
        s.ellipse(16, 15.5, 2.6, 4, proboscis)
    s.px([(15, 14), (16, 14)], NOSE)
    s.px([(13, 15), (13, 17)], whisker or mix(light, "#000000", 0.35), mirror=True)
    s.blush(9, 14, mirror=True)


def whale(s: Sprite, body, belly, *, flipper=WHITE):
    s.px([(6, 2), (8, 1), (10, 2), (7, 4), (9, 4), (8, 6)], "#8fd3ff")
    t = (-2 if s.frame == 0 else 2) if s.pose == "swim" else 0
    s.poly([(25, 15), (31, 9 + t), (30, 15 + t), (31, 21 + t)], body)
    s.ellipse(14, 17, 12, 7.5, body, edge=True)
    m = s.ellipse(13, 21, 9.5, 3.5, belly)
    for x in range(6, 21, 3):
        s.paint(s.m_line(x, 19, x + 1, 24), mix(belly, body, 0.4), within=m)
    s.ellipse(15, 24, 7, 1.8, flipper, rot=20)
    s.px([(3, 14), (5, 13), (4, 15), (9, 12), (10, 11)], mix(body, WHITE, 0.4))
    s.eye(6, 16)
    s.blush(6, 19)


# --------------------------------------------------------------------------- birds
def bird(s: Sprite, body, belly, *, head=None, wing=None, tail_col=None, beak="cone",
         beak_col="#4a3d3a", legs="#c99060", tail="mid", crest=None, eye_col=EYE,
         face=None, wing_mark=None, belly_mark=None, big=False):
    """Side view, facing left, round and chubby."""
    head = head or body
    wing = wing or mix(body, "#000000", 0.15)
    tail_col = tail_col or wing
    cy = 19 if not big else 18
    if tail == "mid":
        s.poly([(20, cy), (29, cy - 6), (31, cy - 3), (23, cy + 4)], tail_col)
    elif tail == "long":
        s.poly([(20, cy), (30, cy - 12), (32, cy - 9), (23, cy + 4)], tail_col)
    elif tail == "short":
        s.poly([(20, cy), (27, cy - 3), (28, cy + 1), (22, cy + 4)], tail_col)
    elif tail == "fan":
        s.poly([(20, cy), (29, cy - 9), (31, cy - 1), (23, cy + 4)], tail_col)
    fly = s.pose == "fly"
    if fly:
        if s.frame == 1:
            _wing(s, 19, cy - 1, wing, far=True)
    elif s.pose == "sleep":
        s.shift_y = 3  # sitting down, legs tucked under
    else:
        sw = _swing(s, 1.5)
        s.line(13, 25, 13 - sw, 29, legs)
        s.line(17, 25, 17 + sw, 29, legs)
        s.px([(round(12 - sw), 29), (round(16 + sw), 29)], legs)
    rb = 8.5 if big else 8
    s.ellipse(16.5, cy + 1, rb, 7, body)
    s.ellipse(13.5, cy + 3, 5.5, 4.5, belly)
    if belly_mark:
        belly_mark(s, s.last)
    if fly:
        _wing(s, 19, cy - 1, wing)
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
    s.eye(8, 10, color=eye_col)
    s.blush(7, 13)


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
    belly = belly or mix(body, WHITE, 0.4)
    if tufts:
        s.poly([(6, 9), (5, 0.5), (12, 5)], body, mirror=True)
    s.px([(12, 30), (14, 30)], "#b88a4a", mirror=True)
    s.ellipse(16, 20, 10.5, 10.5, body)
    s.ellipse(16, 23, 6.5, 6.5, belly)
    if bars:
        for y in range(19, 30, 2):
            s.paint(s.m_line(11, y, 21, y), bars, within=s.last)
    wing = mix(body, "#000000", 0.18)
    if s.pose == "fly":
        cx, cy, rx, ry, rot = {0: (2.5, 17, 5, 2.6, -10), 1: (3.5, 10, 2.6, 7, 30), 2: (4, 25, 2.6, 6.5, -30)}[s.frame]
        s.ellipse(cx, cy, rx, ry, wing, rot=rot, mirror=True, edge=True)
    else:
        s.ellipse(5.5, 20, 3, 6.5, wing, rot=-10, mirror=True)
    s.ellipse(16, 10, 10, 8, body, edge=True)
    s.ellipse(11.5, 10.5, 4.5, 4.8, face, mirror=True, edge=disk_edge is not None)
    if s.pose == "sleep":
        s.closed_eye(10, 10, 3, mirror=True)
    elif eye_col:
        s.ellipse(11.5, 10.5, 2.4, 2.4, eye_col, mirror=True, shade=False)
        s.px([(11, 10), (12, 10), (11, 11), (12, 11)], EYE, mirror=True)
        s.px([(11, 10)], WHITE, mirror=True)
    else:
        s.ellipse(11.5, 10.5, 1.9, 2.2, EYE, mirror=True, shade=False)
        s.px([(11, 9)], WHITE, mirror=True)
    s.poly([(14.5, 13), (17.5, 13), (16, 16.5)], beak, shade=False)
    s.blush(7, 14, mirror=True)


def wader(s: Sprite, body, *, neck=None, head=None, beak="#e8b830", legs="#3d3532", plume=None,
          cap=None, wing=None, curved=False, face=None):
    neck = neck or body
    head = head or neck
    wing = wing or mix(body, "#000000", 0.12)
    if s.pose == "fly":
        # legs trail out behind
        s.line(21, 18, 31, 21, legs)
        s.line(20, 19, 31, 23, legs)
        if s.frame == 1:
            _wing(s, 21, 13, wing, far=True)
    elif s.pose == "sleep":
        # resting on one leg
        s.line(19, 19, 19, 30, legs)
        s.px([(18, 30), (20, 30)], legs)
    else:
        sw = _swing(s, 2)
        s.line(18, 19, 17 - sw, 30, legs)
        s.line(21, 19, 22 + sw, 30, legs)
        s.px([(round(16 - sw), 30), (round(23 + sw), 30)], legs)
    s.ellipse(20, 15, 7, 5, body)
    if s.pose == "fly":
        _wing(s, 21, 13, wing)
    else:
        s.ellipse(22, 14, 5, 3.3, wing, rot=-10, edge=True)
    s.poly([(26, 14), (31, 17), (25, 18)], wing)
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
    s.px([(2, 29), (4, 30), (27, 30), (29, 29), (8, 30), (22, 30)], "#8fd3ff")
    s.poly([(24, 20), (30, 16), (29, 22)], tail_col or body)
    s.ellipse(17, 23, 11, 6.5, body)
    s.ellipse(10, 22, 5, 5, chest)
    m = s.ellipse(20, 21, 7, 3.5, mix(body, "#000000", 0.12), rot=-8, edge=True)
    s.paint(s.m_poly([(17, 22), (24, 21), (24, 23), (17, 24)]), speculum, within=m)
    s.ellipse(10, 11, 6, 5.5, head, edge=True)
    if ring:
        s.paint(s.m_ellipse(10, 16.8, 4, 1), ring)
    s.ellipse(3.5, 13, 3.4, 1.8, bill)
    s.eye(7, 10)
    s.blush(7, 13)


def goose(s: Sprite):
    s.px([(2, 30), (6, 29), (25, 30), (29, 29)], "#8fd3ff")
    s.poly([(25, 20), (31, 17), (30, 23)], BLACK)
    s.ellipse(19, 23, 10.5, 6.5, "#9a8670")
    s.ellipse(14, 25, 5, 4, "#e2d8c8")
    s.ellipse(22, 21, 7, 3.5, "#6e5c4c", rot=-8, edge=True)
    s.path([(12, 19), (10, 13), (10, 8)], 2.3, BLACK)
    s.ellipse(9.5, 7, 5, 4.2, BLACK, edge=True)
    s.paint(s.m_ellipse(10.5, 9.5, 2.6, 1.6, rot=-20), WHITE)
    s.ellipse(4, 8.2, 2.6, 1.5, BLACK)
    s.paint(s.m_ellipse(13, 19.5, 2.6, 1.2), "#e2d8c8")
    s.eye(8, 5, shine="#ffffff", color="#000000")
    s.px([(8, 5)], "#9a9aa8")


def hummingbird(s: Sprite, *, head="#d93a8a", crown="#6aa56e", throat=None):
    s.ellipse(22, 9, 7, 3, "#cfe8f7", rot=-35, shade=False)
    s.poly([(18, 20), (24, 28), (20, 29)], "#4d7a52")
    s.ellipse(16, 18, 5.5, 6.5, "#6aa56e", rot=20)
    s.ellipse(14, 20, 3.5, 4, "#c9d6c0")
    wx, wy, rot = {0: (21, 13, -25), 1: (19, 11, -65), 2: (21, 17, 15)}[s.frame] if s.pose == "fly" else (19, 12, -55)
    s.ellipse(wx, wy, 6, 2.6, "#e6f4fc", rot=rot, shade=False)
    s.ellipse(12, 11, 5.2, 5, head, edge=True)
    s.paint(s.m_ellipse(13.5, 8.3, 4, 2.3), crown, within=s.last)
    if throat:
        s.paint(s.m_ellipse(11, 14.5, 3.5, 2), throat, within=s.last)
    _beak(s, "needle", "#2b2630")
    s.line(7, 11, 1, 13, "#2b2630")
    s.eye(10, 9)
    s.px([(10, 9)], WHITE)


def pelican(s: Sprite):
    """Standing, so it reads as a bird whether it's perched or flying."""
    s.poly([(25, 17), (31, 15), (30, 21)], "#3f3b3d")
    fly = s.pose == "fly"
    if fly:
        if s.frame == 1:
            _wing(s, 20, 17, "#b9b4ac", size=1.1, far=True)
    elif s.pose == "sleep":
        s.shift_y = 2
    else:
        sw = _swing(s, 1.5)
        s.line(15, 24, 15 - sw, 28, "#3d3a3c")
        s.line(19, 24, 19 + sw, 28, "#3d3a3c")
        s.px([(round(13 - sw), 29), (round(14 - sw), 29), (round(15 - sw), 29),
              (round(17 + sw), 29), (round(18 + sw), 29), (round(19 + sw), 29)], "#3d3a3c")
    s.ellipse(18.5, 20, 9.5, 6, "#6f6a6c")
    s.ellipse(16, 22.5, 5.5, 3.4, "#8a8486")
    if fly:
        m = _wing(s, 20, 17, "#b9b4ac", size=1.1)
        s.paint(s.m_ellipse(*{0: (30, 13), 1: (24, 4), 2: (24, 28)}[s.frame], 2.5, 2.5), "#3f3b3d", within=m)
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
    s.blush(11, 9)


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
    head = head or body
    tail_col = tail_col or body
    legs = legs or mix(body, "#000000", 0.15)
    tp = tail_pts or [(20, 22), (26, 25), (30, 22), (30, 16)]
    s.path(tp, (2.4, 0.7), tail_col)
    sw = _swing(s, 1.5)
    s.path([(20, 23), (22 + sw, 27), (24 + sw, 27)], 1.1, mix(legs, "#000000", 0.15))
    s.path([(10, 23), (9 + sw, 27), (7 + sw, 27)], 1.1, mix(legs, "#000000", 0.15))
    ry = 4.3 if wide else 3.6
    body_m = s.ellipse(15, 22, 7.5, ry, body)
    s.paint(s.m_ellipse(15, 24.8, 6.5, 1.6), belly, within=body_m)
    if pattern:
        pattern(s, body_m)
    s.path([(17, 24), (17 - sw, 28), (15 - sw, 28)], 1.1, legs)
    s.path([(12, 24), (12 - sw, 28), (10 - sw, 28)], 1.1, legs)
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
    s.blush(7, 20)


def snake(s: Sprite, body, *, belly=None, bands=None, band_period=4.0, band_len=2.0,
          stripe=None, blotch=None, rattle=False, head=None, head_w=5.4):
    """Coiled snake looking left, with a big round head and a tongue."""
    pts = [(25, 28.5), (14, 28.8), (7, 27), (5.5, 23.5), (9, 20.5), (17, 20), (24, 21.5), (25.5, 24.5),
           (21, 26), (16, 25), (14, 21), (15, 17), (13.5, 13)]
    r = 2.6
    if rattle:
        for i, (x, y) in enumerate([(27, 28), (29, 27), (30.3, 25.3)]):
            s.ellipse(x, y, 1.4, 1.2, "#d9c08a" if i % 2 == 0 else "#b89b62")
    # Stamp discs along the path; each pixel remembers the arc length and centre
    # distance of the last disc covering it, so the front of the coil wins.
    tmap = np.full((32, 32), -1.0)
    dmap = np.full((32, 32), 99.0)
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
    hm = s.ellipse(12.5, 10.5, head_w, 4.2, head or body, edge=True)
    if belly:
        s.paint(s.m_ellipse(11, 13.6, 4, 1.3), belly, within=hm)
    s.px([(6, 13), (5, 13), (4, 14), (4, 12)], "#e04a5a")
    s.eye(9, 9)
    s.blush(9, 12)


def turtle(s: Sprite, shell, skin, *, dome=False, scutes=None, speckle=None, rim=None):
    s.ellipse(8, 22, 4.5, 3.5, skin)
    s.ellipse(5, 18.5, 4.5, 4, skin, edge=True)
    if speckle:
        s.px([(3, 17), (6, 16), (5, 20), (7, 19)], speckle)
    sw = _swing(s, 1)
    s.ellipse(11 - sw, 27 - (sw > 0), 2.4, 3.2, skin, mirror=False)
    s.ellipse(22 + sw, 27 - (sw < 0), 2.4, 3.2, skin)
    s.poly([(26, 23), (30, 25), (26, 26)], skin)
    ry = 10 if dome else 7.5
    m = s.fill(s.m_ellipse(17, 25, 11, ry) & (s.m_poly([(0, 0), (32, 0), (32, 25.5), (0, 25.5)])), shell, edge=True)
    s.ellipse(17, 25.5, 11.5, 1.6, rim or mix(shell, "#000000", 0.25))
    if scutes:
        cy = 18 if dome else 20
        for cx in (11, 17, 23):
            s.paint(s.m_ellipse(cx, cy + (1 if cx != 17 else -1), 2.4, 2.2), scutes, within=m)
    s.eye(3, 17)
    s.blush(4, 20)


def frog(s: Sprite, skin, belly, *, stripe=None, pads=False, tympanum=None, spots=None):
    s.ellipse(6, 27, 5, 3, skin, rot=-15, mirror=True)
    s.ellipse(16, 22, 9.5, 7, skin)
    s.ellipse(16, 25, 6, 4.5, belly)
    s.ellipse(16, 15, 11, 6.5, skin, edge=True)
    s.ellipse(10, 10.5, 4, 4, skin, mirror=True)
    s.ellipse(10, 10.5, 2.6, 2.6, "#f3d26a" if not stripe else "#d8b84a", mirror=True, shade=False)
    s.px([(9, 10), (10, 10), (11, 10), (9, 11), (10, 11), (11, 11)], EYE, mirror=True)
    s.px([(9, 10)], WHITE, mirror=True)
    if stripe:
        s.paint(s.m_poly([(1, 14), (6, 12), (7, 14), (2, 17)]), stripe, mirror=True)
    if tympanum:
        s.paint(s.m_ellipse(5, 15, 1.8, 1.8), tympanum, mirror=True)
    if spots:
        s.paint(s.m_px(spots), mix(skin, "#000000", 0.35))
    s.paint(s.m_poly([(10, 17.5), (16, 19), (22, 17.5), (22, 18.5), (16, 20), (10, 18.5)]), mix(skin, "#000000", 0.5))
    s.blush(6, 16, mirror=True)
    s.ellipse(11, 29.5, 2.3, 1.4, skin, mirror=True)
    if pads:
        s.px([(9, 30), (11, 30), (13, 30)], mix(skin, "#ffffff", 0.35), mirror=True)


# --------------------------------------------------------------------------- invertebrates
def butterfly(s: Sprite, fore, hind, *, body="#2b2630", pattern=None, tails=False):
    """Top view, wings spread."""
    if tails:
        s.path([(11, 23), (10, 28)], (1.2, 0.8), hind, mirror=True)
    k = {1: 0.45, 2: 0.75}.get(s.frame, 1.0) if s.pose == "fly" else 1.0
    sq = lambda pts: [(16 - (16 - x) * k, y) for x, y in pts]  # noqa: E731
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
    w = {1: -25, 2: 25}.get(s.frame, 0) if s.pose == "fly" else 0
    s.ellipse(20, 8, 4.5, 6.5, "#e6f4fc", rot=25 + w, shade=False, edge=True)
    s.ellipse(25, 11, 3.5, 5, "#d6ecfa", rot=40 + w, shade=False, edge=True)
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
    s.blush(5, 19, color="#ff8fa8")


def beetle_top(s: Sprite, shell, *, head=BLACK, spots=(), stripes=False, fan=False, pron=None):
    for y in (17, 21, 25):
        s.line(6, y - 2, 4, y + 1, BLACK)
        s.line(25, y - 2, 27, y + 1, BLACK)
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
    for cy in (10, 14):
        rot = (-8 if cy == 10 else 10) + ({1: -14, 2: 14}.get(s.frame, 0) if s.pose == "fly" else 0)
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
    s.eye(12, 14)
    s.eye(18, 14)
    s.px([(15, 18), (16, 18)], mix(color, "#000000", 0.55))
    s.blush(10, 17)
    s.blush(20, 17)


# --------------------------------------------------------------------------- added for North Carolina
def fish(s: Sprite, body, belly, *, fin=None, pattern=None, slim=False):
    """Side view facing left."""
    fin = fin or mix(body, "#000000", 0.15)
    ry = 6 if slim else 7.5
    t = (-2 if s.frame == 0 else 2) if s.pose == "swim" else 0
    s.poly([(24, 16.5), (31, 10 + t), (29.5, 16.5 + t), (31, 23 + t)], fin)
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
    s.blush(6, 17)


def dolphin(s: Sprite, body, belly):
    t = (-2 if s.frame == 0 else 2) if s.pose == "swim" else 0
    s.poly([(24, 16), (31, 9 + t), (29, 16 + t), (31, 21 + t)], body)
    s.poly([(14, 11), (20, 4), (21, 12)], body)
    m = s.ellipse(15, 17, 11.5, 6, body, edge=True)
    s.paint(s.m_ellipse(12, 20.5, 9, 2.8), belly, within=m)
    s.ellipse(1.8, 18.5, 3, 1.6, body)
    s.paint(s.m_ellipse(1.8, 19.5, 2.5, 0.8), belly, within=s.last)
    s.ellipse(14, 23, 4, 1.6, mix(body, "#000000", 0.15), rot=30)
    s.px([(4, 19), (5, 20), (6, 20)], mix(body, "#000000", 0.5))
    s.eye(7, 15)
    s.blush(8, 18)


def sea_turtle(s: Sprite, shell, skin, *, scutes=None):
    stroke = s.pose == "swim" and s.frame == 1
    s.ellipse(9, 24, 6, 2.5, skin, rot=25)
    s.ellipse(24, 25, 3.5, 2, skin, rot=-20 if not stroke else 10)
    m = s.ellipse(18, 17, 11, 7.5, shell, edge=True)
    for cx, cy in ((13, 15), (18, 13), (23, 15), (15, 19), (21, 19)):
        s.paint(s.m_ellipse(cx, cy, 2.2, 1.8), scutes or mix(shell, "#ffffff", 0.2), within=m)
    s.ellipse(18, 23.5, 10, 1.5, mix(skin, "#ffffff", 0.3))
    # Front flipper sweeps back along the shell, or reaches forward mid-stroke.
    s.ellipse(14, 23.5, 7, 2.4, skin, rot=-12, edge=True) if not stroke else s.ellipse(9, 22, 6, 2.6, skin, rot=40, edge=True)
    s.ellipse(5.5, 16.5, 5, 4.2, skin, edge=True)
    s.paint(s.m_px([(4, 14), (7, 14), (6, 16), (3, 17)]), mix(skin, "#000000", 0.25))
    s.eye(3, 15)
    s.blush(4, 18)


def alligator(s: Sprite, body="#4a5a3a", belly="#e8e0b8"):
    s.path([(20, 22), (26, 24), (30, 22), (31, 17)], (2.8, 0.8), body)
    sw = _swing(s, 1.5)
    s.path([(20, 23), (22 + sw, 27), (24 + sw, 27)], 1.2, mix(body, "#000000", 0.2))
    s.path([(10, 23), (9 + sw, 27), (7 + sw, 27)], 1.2, mix(body, "#000000", 0.2))
    m = s.ellipse(15, 21.5, 8, 4, body)
    s.paint(s.m_ellipse(15, 24.6, 7, 1.6), belly, within=m)
    for x in (10, 13, 16, 19, 22, 25, 28):
        s.px([(x, 18 if x < 22 else 19 + (x - 22) // 3)], mix(body, "#000000", 0.4))
    s.path([(17, 24), (17 - sw, 28), (15 - sw, 28)], 1.2, body)
    s.path([(12, 24), (12 - sw, 28), (10 - sw, 28)], 1.2, body)
    s.ellipse(8, 18.5, 4.5, 3.6, body, edge=True)
    s.poly([(5, 18), (-1, 19.5), (-1, 22.5), (6, 22)], body)
    s.paint(s.m_line(0, 21, 6, 21), mix(body, "#000000", 0.5))
    s.px([(1, 22), (3, 22), (5, 22), (2, 20)], WHITE)
    s.ellipse(8.5, 15.5, 2, 1.6, body)
    s.eye(8, 15)
    s.blush(9, 19)


def turkey(s: Sprite):
    for i, c in enumerate(("#c8a06a", "#5a3e2a", "#8a6440", "#3e2a1e")):
        s.ellipse(20, 15, 11 - i * 1.7, 12 - i * 1.7, c, shade=False)
    sw = _swing(s, 1.5)
    s.line(14, 25, 13 - sw, 30, "#c86a5a")
    s.line(18, 25, 19 + sw, 30, "#c86a5a")
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
    for (a, b, c) in [((14, 11), (8, 5), (5, 1)), ((13, 13), (6, 10), (2, 9)), ((13, 15), (6, 17), (2, 20)),
                      ((14, 16), (9, 22), (6, 27))]:
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
    s.blush(12, 15)
    s.blush(18, 15)


def grasshopper(s: Sprite, body, stripe, *, legs=None):
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
    s.blush(6, 18)


def crab(s: Sprite, shell, claw, *, legs=None, stalks=2, big_claw=False, pattern=None, eye_big=False):
    legs = legs or mix(shell, "#000000", 0.2)
    for y in (19, 22, 25):
        s.path([(8, y), (3, y + 3), (2, y + 6)], 0.7, legs, shade=False, mirror=True)
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
    s.blush(10, 21, mirror=True)
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
    s.blush(8, 14)
    s.blush(22, 14)


def snail_shell(s: Sprite, shell, spots):
    s.ellipse(15, 27, 12, 2.6, "#e8d8c0")
    m = s.ellipse(16, 17, 10, 10, shell, edge=True)
    s.poly([(20, 8), (25, 2), (24, 10)], shell, edge=True)
    for y in (11, 15, 19, 23):
        for x in range(8 + (y // 2) % 3, 26, 3):
            s.paint(s.m_px([(x, y), (x + 1, y)]), spots, within=m)
    s.paint(s.m_path([(16, 17), (19, 14), (22, 17), (19, 21), (14, 20), (12, 15)], 0.4), mix(shell, "#000000", 0.3), within=m)
    s.ellipse(6, 23, 5, 3.5, "#f0e0c8", edge=True)
    s.line(4, 20, 3, 16, "#f0e0c8")
    s.line(7, 20, 8, 16, "#f0e0c8")
    s.eye(4, 22)
    s.blush(6, 24)


def jelly(s: Sprite, bell, *, rim=None, arms="#e8dcc8", tentacles=None, stripes=None):
    if tentacles:
        for x0 in (8, 13, 18, 23):
            s.path([(x0, 13), (x0 - 1, 19), (x0 + 1, 24), (x0, 30)], 0.6, tentacles, shade=False)
    s.path([(14, 13), (13, 20), (15, 25)], 1.6, arms)
    s.path([(18, 13), (19, 20), (17, 24)], 1.6, arms)
    m = s.fill(s.m_ellipse(16, 14, 11, 11) & s.m_poly([(0, 0), (32, 0), (32, 15), (0, 15)]), bell, edge=True)
    if rim:
        s.paint(s.m_ellipse(16, 14, 11, 11) & ~s.m_ellipse(16, 14, 11, 8.5), rim, within=m)
    if stripes:
        for x in (8, 12, 16, 20, 24):
            s.paint(s.m_line(16, 4, x, 14), stripes, within=m)
    s.eye(12, 9)
    s.eye(18, 9)
    s.blush(10, 12)
    s.blush(20, 12)


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
    s.blush(10, 9)
