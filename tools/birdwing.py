"""Bird wings in flight, drawn from a jointed 3-D wing (0.96 remake).

The old flight frames swung one flat wing shape up and down like a flag over a
perched bird's body. Here each wing is a small skeleton seen from a camera a
little above the bird (VIEW_DEG), so a level wing shows its upper side spread out
and a raised near wing turns its underside to you, the way a real bird looks from
the side:

* the arm (shoulder to wrist) and the hand (wrist to tip) each have their own
  stroke angle: on the downstroke the hand lags behind the arm and bends up, on
  the upstroke it trails down, so the wing curves through the beat;
* on the upstroke the wing flexes at the wrist and the hand folds back toward the
  body (a lot for a songbird, a little for a soaring eagle), and the primaries
  slide together; on the downstroke the wing is fully spread and the primaries
  fan out (fingered "slots" on eagles, buzzards, vultures, storks and crows);
* every flight feather is drawn as its own feather (secondaries along the arm,
  primaries along the hand), so the trailing edge is feathered and the tip shape
  (pointed, rounded, slotted) belongs to the kind of bird;
* each wing part is lit by how it faces the light, and the far wing is drawn
  dimmer, behind the body;
* the timing belongs to the kind of bird (FLIGHT_KINDS): songbirds flap in quick
  bursts and close their wings between them (bounding flight), ducks and pigeons
  beat steadily, gulls, herons, hawks, eagles and vultures flap slowly and glide.
  Frame 0 of the cycle is always a good gliding frame (the habitat holds it while
  a big bird glides), and every pose is a real drawing (nothing is stretched).

Coordinates: canvas drawing units (x right, y down); birds face left, so "back"
along the body is +x.
"""
from __future__ import annotations

import math
import re

import numpy as np
from dataclasses import dataclass, field, replace

from pixel import Sprite, mix

VIEW_DEG = 36.0
_CE, _SE = math.cos(math.radians(VIEW_DEG)), math.sin(math.radians(VIEW_DEG))
# Light from the upper left and in front (x, y down, z toward you).
_L = (-0.35, -0.8, 0.48)
_LN = math.sqrt(sum(c * c for c in _L))
_L = tuple(c / _LN for c in _L)
INK = "#1a1420"


@dataclass
class Wing:
    """The planform of one wing, in units of its full extended length span."""
    span: float = 10.0        # shoulder to wingtip, fully spread (drawing units)
    arm: float = 0.42         # shoulder to wrist, as a share of span
    chord: float = 0.30       # secondaries' length (wing depth at the arm)
    sweep: float = 6.0        # arm swept back (deg) when spread
    hand_sweep: float = 14.0  # the hand swept back further from the arm (deg)
    prims: int = 6            # primaries drawn
    tip: str = "round"        # pointed | round | slotted | sickle
    fingers: int = 0          # slotted wings: separate outer primaries
    secs: int = 5             # secondaries drawn
    covert: float = 0.45      # how far the coverts reach down the flight feathers


@dataclass
class Beat:
    """How a kind of bird flaps: stroke angles (deg, up positive), how much the wing
    folds on the upstroke, how far the hand lags, and the frame layout of the loop:
    a list of ("beat", n) / ("glide", n) / ("bound", n) segments over FRAMES frames."""
    top: float = 62.0
    bottom: float = -42.0
    fold_up: float = 0.55
    lag: float = 18.0
    spread_up: float = 0.45
    down: float = 0.55        # share of each beat that is the downstroke
    layout: tuple = (("beat", 16),)
    offset: float = 0.32      # where in the beat frame 0 falls (0 = top of the stroke)
    glide_phi: float = 4.0    # wings held this far up while gliding (dihedral)
    glide_fold: float = 0.0
    bob: float = 0.8          # body rises this far on each downstroke
    hand_trail: float = 26.0  # how far the hand hangs below the arm as the wrist flexes (deg)
    swing: float = 18.0       # the tips swing back at the top of the stroke, forward at the bottom (deg)


@dataclass
class Colors:
    coverts: str               # upper wing coverts (the wing colour)
    flight: str = None         # secondaries, upper side
    tip: str = None            # primaries, upper side
    lining: str = None         # underwing coverts
    under: str = None          # flight feathers seen from below
    leading: str = None        # a pale (or dark) leading edge / lesser coverts
    bar: str = None            # a wing bar across the tips of the greater coverts
    bar2: str = None           # a second, thinner bar on the median coverts
    trailing: str = None       # a pale trailing edge to the secondaries
    speculum: str = None       # ducks: the coloured patch on the secondaries
    patch: str = None          # a patch at the base of the primaries (white in many birds)
    tips: str = None           # dark ends to the primaries only (gulls, white geese)
    mirrors: str = None        # white spots in dark tips (gulls)
    under_tip: str = None      # dark ends to the primaries seen from below
    carpal: str = None         # a dark mark at the wrist on the underwing (buzzards, ospreys)
    bars_under: str = None     # barring across the flight feathers (hawks, owls)
    extra: list = field(default_factory=list)


def _ease(k):
    return 0.5 - 0.5 * math.cos(math.pi * min(1.0, max(0.0, k)))


def wing_state(t: float, beat: Beat, diving=False, landing=None):
    """Arm angle, hand angle, fold, primary spread and body bob at cycle time t (0..1)."""
    if diving:  # plunging: folded back tight along the body
        return dict(phi=8.0, phih=4.0, fold=0.9, spread=0.0, bob=0.0, mode="tuck", tail=0.0)
    if landing is not None:
        # coming in to land: short braking beats with the wings spread wide and swung
        # forward, the tail fanned and pressed down; at the very end the wings rise high
        # and open as the feet reach for the perch
        k = landing
        q = (k * 2.2) % 1.0
        brake = 0.5 - 0.5 * math.cos(2 * math.pi * q)
        settle = max(0.0, (k - 0.72) / 0.28)
        phi = (50 - 50 * brake) * (1 - settle) + 64 * settle
        return dict(phi=phi, phih=phi + 6 + 10 * settle, fold=0.05, spread=1.0, bob=0.0, mode="land", tail=1.0,
                    lam=12 - 6 * brake + 4 * settle)
    total = sum(n for _, n in beat.layout)
    pos = t * total
    acc = 0
    for kind, n in beat.layout:
        if pos < acc + n:
            k = (pos - acc) / n
            break
        acc += n
    else:
        kind, k = beat.layout[-1][0], 0.999
    if kind == "glide":
        return dict(phi=beat.glide_phi, phih=beat.glide_phi - 4, fold=beat.glide_fold, spread=1.0, bob=0.0,
                    mode="glide", tail=1.0)
    if kind == "bound":
        # wings shut against the body; they close as it begins and open again at its end
        c = min(1.0, k * 4, (1 - k) * 3.2)
        phi = -38 * c + (beat.top * 0.8) * (1 - c) * (k > 0.5) - 10 * (1 - c) * (k <= 0.5)
        return dict(phi=phi, phih=phi - 8, fold=0.6 + 0.4 * c, spread=0.0, bob=0.0, mode="bound", tail=0.0, lam=0.0)
    u = (k + beat.offset) % 1.0
    phi, fold, spread, bob = _stroke(u, beat)
    # the hand follows the arm a moment later (it lags at each turn of the stroke), and
    # trails down as the wrist flexes on the upstroke
    phih = _stroke((u - 0.075) % 1.0, beat)[0] - beat.hand_trail * fold - 4
    # the stroke runs down and forward, then up and back: at the top the tips point
    # back over the tail, at the bottom forward under the head
    mid = (beat.top + beat.bottom) / 2
    lam = -beat.swing * (phi - mid) / max(1.0, (beat.top - beat.bottom) / 2)
    return dict(phi=phi, phih=phih, fold=fold, spread=spread, bob=bob, mode="beat", tail=0.3, lam=lam)


def _stroke(u, beat):
    """Arm angle, wrist fold, primary spread and body bob at beat time u (0 = top)."""
    D = beat.down
    if u < D:
        q = u / D
        phi = beat.top + (beat.bottom - beat.top) * _ease(q)
        fold = 0.1 * q ** 3 + 0.25 * (1 - q) ** 3 * beat.fold_up
        spread = 1.0
        bob = -beat.bob * math.sin(math.pi * q)
    else:
        q = (u - D) / (1 - D)
        phi = beat.bottom + (beat.top - beat.bottom) * _ease(q)
        sq = math.sin(math.pi * q)
        fold = beat.fold_up * sq ** 0.7
        spread = 1.0 - (1.0 - beat.spread_up) * sq
        bob = 0.45 * beat.bob * sq
    return phi, fold, spread, bob


def _rot(a, deg):
    r = math.radians(deg)
    return (a[0] * math.cos(r) - a[1] * math.sin(r), a[0] * math.sin(r) + a[1] * math.cos(r))


def _span_vec(phi, far, lam=0.0):
    """The span direction for stroke angle phi (up +) and fore-aft swing lam (tip
    forward +), for the near (toward you) or far wing."""
    p, l = math.radians(phi), math.radians(lam)
    c = math.cos(l)
    return (-math.sin(l), -math.sin(p) * c, (-1 if far else 1) * math.cos(p) * c)


YAW = float(__import__("os").environ.get("BW_YAW", "-0.38"))  # seen a little from the front: the near wing reaches forward


def _project(p):
    x, y, z = p
    return (x + z * YAW, y * _CE + z * _SE)


def _cross(a, b):
    return (a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0])


def _facing(span, far):
    """+1 when the upper side of a wing part (spanned by span and the chord, back
    along +x) faces the camera, -1 for the underside, and how brightly it's lit."""
    up = _cross((1.0, 0.0, 0.0), span)  # the upper side's normal, for the near wing
    if far:
        up = tuple(-c for c in up)
    if up[1] > 0:  # make sure it's the side that points up (y down) when level
        up = tuple(-c for c in up)
    cam = (0.0, -_SE, _CE)
    side = 1 if sum(a * b for a, b in zip(up, cam)) >= 0 else -1
    n = tuple(side * c for c in up)
    lit = max(0.0, sum(a * b for a, b in zip(n, _L)))
    return side, lit


def _lit(col, lit, far):
    """Tone a colour by how much light the wing part catches (and dim the far wing)."""
    c = mix(col, "#fff4d6", 0.2 * max(0.0, lit - 0.55) / 0.45) if lit > 0.55 else mix(col, "#3e2c70", 0.3 * (0.55 - lit))
    if far:
        c = mix(c, INK, 0.28)
    return c


class _WingGeom:
    """One wing in its own plane (u out along the span, v back along the body): the
    wrist, the hand, the secondaries' tips along the arm and the primaries' bases and
    tips along the hand."""

    def __init__(self, wing: Wing, st: dict, size: float):
        L = wing.span * size
        f = st["fold"]
        spread = st["spread"]
        self.L, self.f, self.wing, self.spread = L, f, wing, spread
        a_len = wing.arm * L * (1 - 0.4 * f)
        alpha = wing.sweep + 50 * f
        self.wrist = _rot((a_len, 0.0), alpha)
        beta = alpha + wing.hand_sweep + (102 - wing.hand_sweep - alpha) * min(1.0, f ** 1.1)
        self.hand_len = (1 - wing.arm) * L * 0.4
        hd = _rot((1.0, 0.0), beta)
        self.hand_end = (self.wrist[0] + hd[0] * self.hand_len, self.wrist[1] + hd[1] * self.hand_len)
        chord = wing.chord * L * (1 - 0.3 * f)
        n = wing.secs
        self.secs = []  # (base, tip) inner (at the body) to outer (at the wrist)
        for i in range(n + 1):
            k = i / n
            base = (self.wrist[0] * k, self.wrist[1] * k)
            d = _rot((1.0, 0.0), 92 - 8 * k + 28 * f)
            ln = chord * (0.9 + 0.1 * math.sin(math.pi * k))
            self.secs.append((base, (base[0] + d[0] * ln, base[1] + d[1] * ln)))
        reach = (1 - wing.arm) * L
        n = wing.prims
        self.prims = []  # inner to outer
        fing = wing.fingers if wing.tip == "slotted" else 0
        for i in range(n):
            k = i / (n - 1)
            base = (self.wrist[0] + hd[0] * self.hand_len * k, self.wrist[1] + hd[1] * self.hand_len * k)
            fk = max(0.0, (i - (n - 1 - fing)) / max(1, fing)) if fing else 0.0  # 0..1 over the fingers
            if wing.tip == "pointed":
                ln, out = reach * (0.5 + 0.55 * k ** 1.3), 8
            elif wing.tip == "sickle":
                ln, out = reach * (0.45 + 0.62 * k ** 1.15), 20
            elif wing.tip == "slotted":
                ln, out = reach * (0.6 + 0.42 * min(1.0, k * 1.5)) * (1 - 0.16 * fk * fk), -2 - 18 * spread * fk
            else:  # round
                ln, out = reach * (0.66 + 0.36 * math.sin(math.pi * (0.2 + 0.62 * k))), 2
            ln *= (1 - 0.3 * f)
            inner = 86 - 8 * k
            ang_spread = alpha + inner + (beta - alpha + out - inner) * k ** 0.85
            ang_fold = beta + 3 - 3 * k
            ang = ang_fold + (ang_spread - ang_fold) * max(0.0, spread - 0.6 * f)
            d = _rot((1.0, 0.0), ang)
            self.prims.append((base, (base[0] + d[0] * ln, base[1] + d[1] * ln)))
        self.fingers = fing

    def place(self, sh, st, far):
        """3-D placement: the arm in the plane of its stroke angle, the hand in the plane
        of its own, joined at the wrist; returns projectors for arm and hand points."""
        lam = st.get("lam", 0.0)
        sa = _span_vec(st["phi"], far, lam)
        shv = _span_vec(st["phih"], far, lam * 1.3)
        self.span_arm, self.span_hand = sa, shv
        wr = self.wrist
        sx, sy, sz = sh

        # projected about the shoulder, which stays where the body plan put it
        def P(q):
            x, y = _project(q)
            return (sx + x, sy + y)

        def arm(p):
            u, v = p
            return P((v + sa[0] * u, sa[1] * u, sz + sa[2] * u))
        W3 = (wr[1] + sa[0] * wr[0], sa[1] * wr[0], sz + sa[2] * wr[0])

        def hand(p):
            u, v = p[0] - wr[0], p[1] - wr[1]
            return P((W3[0] + v + shv[0] * u, W3[1] + shv[1] * u, W3[2] + shv[2] * u))
        return arm, hand


def _hull(pts):
    """The convex hull of some points (Andrew's monotone chain)."""
    pts = sorted(set((round(x, 3), round(y, 3)) for x, y in pts))
    if len(pts) < 3:
        return pts

    def half(ps):
        out = []
        for p in ps:
            while len(out) >= 2 and ((out[-1][0] - out[-2][0]) * (p[1] - out[-2][1])
                                     - (out[-1][1] - out[-2][1]) * (p[0] - out[-2][0])) <= 0:
                out.pop()
            out.append(p)
        return out
    lo, hi = half(pts), half(pts[::-1])
    return lo[:-1] + hi[:-1]


def _lerp(a, b, k):
    return (a[0] + (b[0] - a[0]) * k, a[1] + (b[1] - a[1]) * k)


def draw_wing(s: Sprite, sh, wing: Wing, beat: Beat, cols: Colors, *, far=False, size=1.0, st=None):
    """Draw one wing from the shoulder sh = (x, y, z) (z: + toward you for the near
    wing, - for the far one). Returns the wing's mask."""
    st = st or wing_state(s.t, beat, diving=getattr(s, "diving", False), landing=getattr(s, "landing", None))
    s.has_wings = True
    if far and st["mode"] == "bound" and st["fold"] > 0.8:
        return s.m_px([])  # shut against the far side, out of sight
    g = _WingGeom(wing, st, size)
    arm, hand = g.place(sh, st, far)
    side_a, lit_a = _facing(g.span_arm, far)
    side_h, lit_h = _facing(g.span_hand, far)
    flight = cols.flight or mix(cols.coverts, INK, 0.12)
    tipc = cols.tip or mix(flight, INK, 0.22)
    lining = cols.lining or mix(cols.coverts, "#ffffff", 0.3)
    under = cols.under or mix(mix(flight, "#ffffff", 0.25), "#b8bcc8", 0.18)
    under_tip = cols.under_tip or mix(tipc, "#ffffff", 0.2)
    upper_a, upper_h = side_a > 0, side_h > 0

    def tone(c, lit):
        return _lit(c, lit, far)

    secs, prims = g.secs, g.prims
    W = g.wrist
    with s.unwarped():
        # the arm: leading edge from the shoulder to the wrist, the secondaries' tips
        # back along the trailing edge to the body
        arm_pts = [arm((0.0, -0.6)), arm((W[0] * 0.55, W[1] - 0.9)), arm((W[0], W[1] - 0.5))]
        arm_pts += [arm(t) for _, t in reversed(secs)] + [arm((0.0, secs[0][1][1] * 0.9))]
        msec = s.m_poly(arm_pts)
        # the hand: leading edge out to the outer primary, then around the primaries'
        # tips (notched between the fingers of a slotted wing, scalloped a little on
        # a big wing) back to the wrist
        folded = g.f > 0.45  # flexed for the upstroke: the feathers slide together into one smooth blade
        notch = 0.0 if g.L < 11 or folded else 0.06
        lead = [hand((W[0], W[1] - 0.5))] + [hand((b[0], b[1] - 0.6)) for b, _ in prims[1:]]
        trail = []
        for i in range(len(prims) - 1, -1, -1):
            b, t = prims[i]
            trail.append(hand(t))
            if i > 0:
                b2, t2 = prims[i - 1]
                deep = 0.42 * g.spread if (g.fingers and i >= len(prims) - g.fingers and not folded) else notch
                mid = _lerp(_lerp(b, t, 1 - deep), _lerp(b2, t2, 1 - deep), 0.5)
                trail.append(hand(mid))
        trail.append(hand(secs[-1][1]))
        hand_pts = lead + trail
        mprim = (s.m_poly(hand_pts) | s.m_path([hand(W), hand(prims[-1][0])], 0.6)
                 | s.m_path([hand(W), hand(_lerp(*prims[-1], 0.6)), hand(prims[-1][1])], (0.75, 0.5)))
        if folded:
            # flexed, the wing is one smooth folded shape: its outline is the hull of it all
            hull = _hull(arm_pts + hand_pts)
            mhull = s.m_poly(hull)
            msec = msec & ~mprim
            tipzone = s.m_poly(_hull([hand(_lerp(b, t, 0.45)) for b, t in prims] + [hand(t) for _, t in prims]))
            mprim = (mhull & tipzone) | (mprim & ~msec)
            msec = mhull & ~mprim
        # coverts: the feathered front of the wing, over the flight feathers' bases
        cd = wing.covert
        cov = ([arm((0.0, -0.6)), arm((W[0] * 0.55, W[1] - 0.9)), arm((W[0], W[1] - 0.5))]
               + [hand((b[0], b[1] - 0.6)) for b, _ in prims[1:-1]]
               + [hand(_lerp(b, t, cd * 0.55)) for b, t in reversed(prims[1:-1])]
               + [arm(_lerp(b, t, cd)) for b, t in reversed(secs)])
        mcov = s.m_poly(cov)
        m_all = msec | mprim | mcov
        sec_col = tone(flight if upper_a else under, lit_a)
        prim_col = tone(tipc if upper_h else under_tip, lit_h)
        s.fill(msec & ~mprim, sec_col, shade=False)
        s.fill(mprim, prim_col, shade=False, edge=True)
        # the gaps between flight feathers, as fine darker lines toward the tips
        if g.L >= 12 and g.spread > 0.4 and not folded:
            for b, t in prims[1:-1]:
                p, q = hand(_lerp(b, t, 0.55)), hand(_lerp(b, t, 0.95))
                s.paint(s.m_line(p[0], p[1], q[0], q[1]), mix(prim_col, INK, 0.3), within=mprim)
        if g.L >= 14 and not folded:
            for b, t in secs[1:-1:2]:
                p, q = arm(_lerp(b, t, 0.6)), arm(_lerp(b, t, 0.95))
                s.paint(s.m_line(p[0], p[1], q[0], q[1]), mix(sec_col, INK, 0.25), within=msec & ~mprim)
        cov_col = tone(cols.coverts if upper_a else lining, lit_a)
        s.fill(mcov, cov_col, shade=False, edge=True)
        # the leading edge catches the light (a soft pale line from shoulder to wrist)
        if g.L >= 9 and not folded:
            s.paint(s.m_path([arm((0.0, -0.4)), arm((W[0], W[1] - 0.4))], 0.5),
                    tone(mix(cols.coverts if upper_a else lining, "#fff4d6", 0.22), lit_a), within=mcov)
        # markings
        if upper_a and cols.leading:
            s.paint(s.m_path([arm((0.0, -0.3)), arm((W[0], W[1] - 0.2))], max(0.6, g.L * 0.04)),
                    tone(cols.leading, lit_a), within=mcov)
        if upper_a and cols.bar:
            bar = [arm(_lerp(b, t, cd * 0.95)) for b, t in secs] + [hand(_lerp(b, t, cd * 0.5)) for b, t in prims[1:3]]
            s.paint(s.m_path(bar, 0.6), tone(cols.bar, lit_a), within=m_all)
        if upper_a and cols.bar2:
            bar = [arm(_lerp(b, t, cd * 0.45)) for b, t in secs]
            s.paint(s.m_path(bar, 0.5), tone(cols.bar2, lit_a), within=m_all)
        if cols.speculum and upper_a:
            spec = [arm(_lerp(b, t, 0.7)) for b, t in secs]
            s.paint(s.m_path(spec, max(0.8, g.L * 0.05)), tone(cols.speculum, lit_a), within=msec & ~mcov & ~mprim)
        if cols.trailing:
            s.paint(s.m_path([arm(t) for _, t in secs], 0.6), tone(cols.trailing, lit_a), within=msec & ~mprim)
        if cols.patch and upper_h:
            pp = [hand(_lerp(b, t, 0.3)) for b, t in prims]
            s.paint(s.m_path(pp, max(0.7, g.L * 0.055)), tone(cols.patch, lit_h), within=mprim & ~mcov)
        tcol = cols.tips if upper_h else (cols.tips or cols.under_tip)
        if tcol:
            k0 = 0.5 if cols.tips else 0.72
            tip_poly = [hand(_lerp(b, t, k0)) for b, t in prims] + [hand(t) for _, t in reversed(prims)]
            s.paint(s.m_poly(tip_poly) | s.m_path([hand(t) for _, t in prims], 0.7), tone(tcol, lit_h),
                    within=mprim & ~mcov)
            if cols.mirrors and upper_h and g.L >= 12 and g.spread > 0.5:
                p = hand(_lerp(*prims[-1], 0.86))
                s.paint(s.m_px([(round(p[0]), round(p[1]))]), cols.mirrors, within=mprim)
        if cols.carpal and not upper_h:
            p = hand((W[0] + 0.4, W[1] + 0.8))
            s.paint(s.m_ellipse(p[0], p[1], max(0.8, g.L * 0.055), max(0.8, g.L * 0.05)), tone(cols.carpal, lit_h),
                    within=m_all)
        if cols.bars_under and g.L >= 12:
            for kk in (0.5, 0.8):
                band = [arm(_lerp(b, t, kk)) for b, t in secs] + [hand(_lerp(b, t, kk)) for b, t in prims]
                s.paint(s.m_path(band, 0.45), tone(cols.bars_under, lit_h), within=(msec | mprim) & ~mcov)
        for fn in cols.extra:
            fn(s, dict(arm=arm, hand=hand, geom=g, upper_arm=upper_a, upper_hand=upper_h, mask=m_all,
                       prim=mprim, sec=msec, cov=mcov, tone=tone, lit=(lit_a, lit_h)))
        if not far:
            # a crisp darker edge where the near wing lies over the body, so it reads
            from pixel import _shift
            other = (s.reg > 0) & ~m_all
            near = _shift(other, 1, 0) | _shift(other, -1, 0) | _shift(other, 0, 1) | _shift(other, 0, -1)
            edge = m_all & near
            s.col[edge] = (s.col[edge] * 0.6 + np.array([26, 20, 32]) * 0.4).astype(s.col.dtype)
    return m_all


_FIT: dict = {}


def fit_size(wing: Wing, beat: Beat, sy: float, top=-7.6, bottom=30.6):
    """The wing size (1 or less) that keeps both wings inside the canvas all through
    the beat, for a shoulder at height sy."""
    key = (id(wing), id(beat), round(sy, 1))
    if key not in _FIT:
        up, down = wings_extent(wing, beat)
        k = 1.0
        if up > 0:
            k = min(k, (sy - top) / up)
        if down > 0:
            k = min(k, (bottom - sy) / down)
        _FIT[key] = k
    return _FIT[key]


def wings_extent(wing: Wing, beat: Beat, size=1.0):
    """How far above and below the shoulder the wings reach over the whole cycle."""
    up, down = 0.0, 0.0
    for i in range(32):
        st = wing_state(i / 32, beat)
        for far in (False, True):
            g = _WingGeom(wing, st, size)
            arm, hand = g.place((0.0, 0.0, 2.0 if not far else -2.0), st, far)
            for _, tipp in g.prims:
                y = hand(tipp)[1]
                up, down = min(up, y), max(down, y)
    return -up, down


# --------------------------------------------------------------------------- kinds
# How each kind of bird flies: its wing planform and its beat. First match on the slug
# wins. Spans are for a bird drawn the usual size (scaled with the body by the caller).
SONG_BEAT = Beat(top=70, bottom=-48, fold_up=0.85, lag=20, spread_up=0.25, layout=(("beat", 5), ("beat", 5), ("bound", 6)),
                 offset=0.08, bob=1.0)
FLAPPER = Beat(top=64, bottom=-46, fold_up=0.6, lag=18, spread_up=0.35, layout=(("beat", 8), ("beat", 8)), offset=0.32,
               bob=0.8)
WATERFOWL = Beat(top=52, bottom=-44, fold_up=0.35, lag=14, spread_up=0.5, layout=(("beat", 8), ("beat", 8)), offset=0.32,
                 bob=0.7)
SLOW = Beat(top=56, bottom=-40, fold_up=0.5, lag=16, spread_up=0.45, layout=(("beat", 16),), offset=0.32, bob=1.0,
            glide_phi=3)
SOAR = Beat(top=46, bottom=-34, hand_trail=8, fold_up=0.36, lag=20, spread_up=0.55, layout=(("beat", 16),), offset=0.33, bob=1.0,
            glide_phi=8)
SWALLOW = Beat(top=64, bottom=-40, fold_up=0.7, lag=14, spread_up=0.3, layout=(("beat", 5), ("beat", 5), ("glide", 6)),
               offset=0.32, bob=0.6, glide_fold=0.25, glide_phi=2)
CROW = Beat(top=58, bottom=-46, fold_up=0.38, lag=18, spread_up=0.35, layout=(("beat", 8), ("beat", 8)), offset=0.32,
            bob=0.8)
GULL = Beat(top=52, bottom=-38, hand_trail=4, fold_up=0.3, lag=18, spread_up=0.4, layout=(("beat", 16),), offset=0.32, bob=0.9,
            glide_phi=6, glide_fold=0.22)
WOODPECKER = Beat(top=70, bottom=-50, fold_up=0.9, lag=18, spread_up=0.25, layout=(("beat", 5), ("beat", 5), ("bound", 6)),
                  offset=0.08, bob=1.4)
GAMEBIRD = Beat(top=58, bottom=-50, fold_up=0.5, lag=12, spread_up=0.4, layout=(("beat", 4), ("beat", 4), ("glide", 8)),
                offset=0.32, bob=0.6, glide_phi=-6)
OWL = Beat(top=55, bottom=-45, fold_up=0.45, lag=16, spread_up=0.5, layout=(("beat", 10), ("glide", 6)), offset=0.32,
           bob=0.9, glide_phi=2)

SONG_WING = Wing(span=15.2, arm=0.42, chord=0.46, sweep=6, hand_sweep=12, prims=6, tip="round", secs=5)
SOAR_GLIDE = replace(SOAR, glide_phi=14)  # turkey vultures and harriers hold a shallow V
STORK = replace(SOAR, top=48, bottom=-36, glide_phi=4)
HERON = Beat(top=50, bottom=-46, hand_trail=12, fold_up=0.42, lag=18, spread_up=0.5, layout=(("beat", 16),), offset=0.32, bob=1.2,
             glide_phi=0, swing=14)
DUCK = Beat(top=46, bottom=-44, fold_up=0.3, lag=12, spread_up=0.55, layout=(("beat", 8), ("beat", 8)), offset=0.32,
            bob=0.8, swing=12)
GOOSE = Beat(top=48, bottom=-42, fold_up=0.35, lag=14, spread_up=0.5, layout=(("beat", 8), ("beat", 8)), offset=0.32,
             bob=1.0, swing=12, glide_phi=2)
FALCON = Beat(top=56, bottom=-44, fold_up=0.5, lag=14, spread_up=0.4, layout=(("beat", 6), ("beat", 6), ("glide", 4)),
              offset=0.32, bob=0.8, glide_phi=2, glide_fold=0.15)
ACCIP = Beat(top=58, bottom=-44, fold_up=0.5, lag=16, spread_up=0.4, layout=(("beat", 5), ("beat", 5), ("glide", 6)),
             offset=0.32, bob=0.8, glide_phi=2)

FLIGHT_KINDS = [
    # pattern, wing, beat
    # big birds first: their names hold songbird words (heron, "swallow-tailed kite")
    (r"vulture|condor|griffon", Wing(span=22, arm=0.44, chord=0.42, sweep=0, hand_sweep=0, prims=7, tip="slotted", fingers=6,
                                    secs=6, covert=0.4), SOAR_GLIDE),
    (r"eagle", Wing(span=22, arm=0.44, chord=0.42, sweep=0, hand_sweep=2, prims=7, tip="slotted", fingers=6, secs=6), SOAR),
    (r"osprey", Wing(span=21, arm=0.42, chord=0.34, sweep=4, hand_sweep=26, prims=7, tip="slotted", fingers=4, secs=6),
     replace(SOAR, glide_fold=0.3, glide_phi=6)),
    (r"harrier", Wing(span=21, arm=0.42, chord=0.34, sweep=2, hand_sweep=8, prims=7, tip="slotted", fingers=4), SOAR_GLIDE),
    (r"falcon|kestrel|merlin|hobby", Wing(span=19, arm=0.38, chord=0.3, sweep=6, hand_sweep=22, prims=7, tip="pointed"),
     FALCON),
    (r"kite", Wing(span=20, arm=0.4, chord=0.3, sweep=4, hand_sweep=18, prims=7, tip="slotted", fingers=4), SOAR),
    (r"accipiter|goshawk|sparrowhawk|coopers|sharp_shinned",
     Wing(span=17.5, arm=0.44, chord=0.4, sweep=2, hand_sweep=6, prims=7, tip="slotted", fingers=4), ACCIP),
    (r"hawk|buzzard|buteo", Wing(span=20, arm=0.44, chord=0.42, sweep=0, hand_sweep=4, prims=7, tip="slotted", fingers=5,
                               secs=6), SOAR),
    (r"owl", Wing(span=19, arm=0.44, chord=0.46, sweep=2, hand_sweep=6, prims=7, tip="slotted", fingers=3, secs=6), OWL),
    (r"pelican", Wing(span=22, arm=0.48, chord=0.36, sweep=0, hand_sweep=4, prims=7, tip="slotted", fingers=5, secs=7),
     STORK),
    (r"stork|crane|spoonbill|ibis|flamingo", Wing(span=21, arm=0.46, chord=0.38, sweep=0, hand_sweep=4, prims=7,
                                                 tip="slotted", fingers=4, secs=6), STORK),
    (r"heron|egret|bittern|limpkin", Wing(span=20, arm=0.46, chord=0.42, sweep=2, hand_sweep=6, prims=7, tip="round",
                                         secs=6), HERON),
    (r"swan", Wing(span=21, arm=0.42, chord=0.32, sweep=4, hand_sweep=12, prims=7, tip="round", secs=6), GOOSE),
    (r"goose|brant", Wing(span=19.5, arm=0.42, chord=0.32, sweep=4, hand_sweep=14, prims=7, tip="pointed", secs=6), GOOSE),
    (r"cormorant|shag|anhinga|gannet|booby", Wing(span=18, arm=0.44, chord=0.3, sweep=4, hand_sweep=14, prims=7,
                                                 tip="round", secs=6), DUCK),
    (r"loon|diver|grebe", Wing(span=15, arm=0.4, chord=0.26, sweep=6, hand_sweep=18, prims=6, tip="pointed"),
     replace(DUCK, top=40, bottom=-40)),
    (r"coot|gallinule|moorhen|rail|crake|swamphen", Wing(span=13.5, arm=0.44, chord=0.4, sweep=2, hand_sweep=6, prims=6,
                                                        tip="round"), replace(DUCK, top=56, bottom=-46, fold_up=0.4)),
    (r"duck|teal|mallard|wigeon|shoveler|pintail|gadwall|merganser|scaup|bufflehead|goldeneye|scoter|eider|canvasback"
     r"|redhead|pochard|smew|shelduck|garganey|mandarin|whistling",
     Wing(span=16, arm=0.4, chord=0.3, sweep=6, hand_sweep=18, prims=6, tip="pointed"), DUCK),
    (r"swallow|martin|swift", Wing(span=18.8, arm=0.32, chord=0.22, sweep=8, hand_sweep=26, prims=6, tip="sickle", secs=4),
     SWALLOW),
    (r"woodpecker|flicker|sapsucker", Wing(span=15.9, arm=0.42, chord=0.38, sweep=4, hand_sweep=8, prims=6, tip="round"),
     WOODPECKER),
    (r"crow|raven|rook|jackdaw|chough|nutcracker", Wing(span=18.8, arm=0.44, chord=0.38, sweep=4, hand_sweep=4, prims=7,
                                                        tip="slotted", fingers=4), CROW),
    (r"magpie|jay", Wing(span=15.2, arm=0.44, chord=0.4, sweep=4, hand_sweep=6, prims=6, tip="round"), FLAPPER),
    (r"dove|pigeon", Wing(span=18.1, arm=0.4, chord=0.32, sweep=6, hand_sweep=18, prims=7, tip="pointed"), FLAPPER),
    (r"gull|kittiwake|fulmar|skua|jaeger|shearwater|albatross",
     Wing(span=21.8, arm=0.4, chord=0.26, sweep=4, hand_sweep=24, prims=7, tip="pointed"), GULL),
    (r"tern|skimmer|tropicbird", Wing(span=21.8, arm=0.38, chord=0.24, sweep=4, hand_sweep=26, prims=7, tip="pointed"), GULL),
    (r"killdeer|plover|dunlin|sanderling|willet|tattler|turnstone|oystercatcher|phalarope|lapwing|godwit|redshank|curlew"
     r"|whimbrel|stint|knot|snipe|sandpiper|yellowlegs|dowitcher|avocet|stilt",
     Wing(span=18.1, arm=0.38, chord=0.26, sweep=6, hand_sweep=22, prims=7, tip="pointed"), FLAPPER),
    (r"kingfisher|bee_eater|roller|hoopoe", Wing(span=14.5, arm=0.42, chord=0.34, sweep=4, hand_sweep=10, prims=6, tip="round"),
     FLAPPER),
    (r"quail|grouse|pheasant|partridge|chicken|turkey|ptarmigan|chukar|prairie_chicken|bobwhite|francolin",
     Wing(span=13.8, arm=0.44, chord=0.42, sweep=2, hand_sweep=4, prims=6, tip="round"), GAMEBIRD),
    (r"puffin|murre|guillemot|murrelet|razorbill|auklet", Wing(span=13.0, arm=0.42, chord=0.24, sweep=4, hand_sweep=14,
                                                                prims=6, tip="pointed"),
     Beat(top=50, bottom=-46, fold_up=0.3, lag=10, spread_up=0.5, layout=(("beat", 4),) * 4, offset=0.32, bob=0.5)),
    (r"parakeet|parrot|budgerigar|lovebird|conure", Wing(span=15.2, arm=0.38, chord=0.28, sweep=6, hand_sweep=20, prims=6,
                                                        tip="pointed"), FLAPPER),
    (r"starling|myna", Wing(span=15.9, arm=0.4, chord=0.3, sweep=6, hand_sweep=18, prims=6, tip="pointed"),
     Beat(top=64, bottom=-46, fold_up=0.6, lag=16, spread_up=0.35, layout=(("beat", 5), ("beat", 5), ("glide", 6)),
          offset=0.32, bob=0.7, glide_phi=2)),
    (r"roadrunner|cuckoo|ani$", Wing(span=14.5, arm=0.44, chord=0.4, sweep=2, hand_sweep=6, prims=6, tip="round"), GAMEBIRD),
    (r"nightjar|nighthawk|poorwill|whip", Wing(span=18.8, arm=0.36, chord=0.28, sweep=6, hand_sweep=22, prims=7, tip="pointed"),
     SWALLOW),
    (r"hummingbird", Wing(span=12.3, arm=0.25, chord=0.2, sweep=0, hand_sweep=10, prims=6, tip="pointed", secs=3), FLAPPER),
]


def flight_kind(slug: str):
    for pattern, wing, beat in FLIGHT_KINDS:
        if re.search(rf"(?:^|_)(?:{pattern})(?:_|$)", slug):
            return wing, beat
    return SONG_WING, SONG_BEAT
