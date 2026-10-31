"""A tiny pixel-art canvas: filled shapes, automatic shading and outline.

Drawings use a 32x32 grid (W, ground at y = 31), but the canvas has PAD_X spare
pixels left and right and PAD_TOP above, so wide wings, long tails, antlers and tall
ears can reach past the grid instead of being cut off. Nothing goes below the ground
line. Coordinates run from -PAD_X to W + PAD_X across and -PAD_TOP to W - 1 down;
the image is N x N pixels.

Shapes are painted in order (later ones on top). Each shape is a "region"; after
drawing, every shaded region is lit as a rounded form from the upper left: a warm
highlight on the lit side, cool hue-shifted shadows on the far side, and a contact
shadow where a later shape sits on top of it. The whole sprite gets a 1-pixel
outline tinted from the colour it borders, darker along the bottom and right.
"""
from __future__ import annotations

import math

import numpy as np
from PIL import Image

W = 32
PAD_X = 4
PAD_TOP = 8
N = W + 2 * PAD_X
assert N == W + PAD_TOP  # square
_YS, _XS = np.mgrid[0:N, 0:N].astype(np.float32) + 0.5
_YS -= PAD_TOP
_XS -= PAD_X

OUTLINE_INK = (38, 26, 46)
SILHOUETTE = (74, 76, 102)
LIGHT = np.array([-0.45, -0.62, 0.64], np.float32)  # from the upper left, toward the viewer
LIGHT /= np.linalg.norm(LIGHT)
WARM = np.array([255, 244, 214], np.float32)        # highlights lean warm
COOL = np.array([62, 44, 112], np.float32)          # shadows lean cool purple


def rgb(c) -> tuple[int, int, int]:
    if isinstance(c, str):
        c = c.lstrip("#")
        return tuple(int(c[i:i + 2], 16) for i in (0, 2, 4))
    return tuple(c)


def mix(a, b, t: float):
    a, b = rgb(a), rgb(b)
    return tuple(round(a[i] * (1 - t) + b[i] * t) for i in range(3))


def _shift(m: np.ndarray, dx: int, dy: int) -> np.ndarray:
    """out[y, x] = m[y + dy, x + dx], False outside the canvas."""
    out = np.zeros_like(m)
    ys = slice(max(0, -dy), N - max(0, dy))
    yd = slice(max(0, dy), N - max(0, -dy))
    xs = slice(max(0, -dx), N - max(0, dx))
    xd = slice(max(0, dx), N - max(0, -dx))
    out[ys, xs] = m[yd, xd]
    return out


def _blur(m: np.ndarray, r: int) -> np.ndarray:
    """Two box blurs of radius r (close to a gaussian), zero outside the canvas."""
    a = m.astype(np.float32)
    k = 2 * r + 1
    for _ in range(2):
        c = np.cumsum(np.pad(a, ((0, 0), (r + 1, r))), axis=1)
        a = (c[:, k:] - c[:, :-k]) / k
        c = np.cumsum(np.pad(a, ((r + 1, r), (0, 0))), axis=0)
        a = (c[k:, :] - c[:-k, :]) / k
    return a


def _lum(R: np.ndarray) -> np.ndarray:
    """How directly each pixel of region R faces the light, treating R as a rounded form."""
    ys, xs = np.where(R)
    size = min(ys.max() - ys.min(), xs.max() - xs.min()) + 1
    h = _blur(R, 2 if size >= 8 else 1)
    gy, gx = np.gradient(h)
    z = 0.22 if size >= 8 else 0.35
    n = np.stack([-gx, -gy, np.full_like(gx, z)], axis=-1)
    n /= np.linalg.norm(n, axis=-1, keepdims=True)
    flat = LIGHT[2]
    return (n @ LIGHT) - flat  # 0 where the surface faces the viewer


def _tone(col: np.ndarray, k: float) -> np.ndarray:
    """k > 0 lightens toward a warm highlight, k < 0 darkens toward a cool shadow."""
    if k > 0:
        return col * (1 - k) + WARM * k
    k = -k
    return col * (1 - 0.3 * k) * (1 - 0.18 * k) + COOL * 0.18 * k


def _seg_dist(x0, y0, x1, y1):
    dx, dy = x1 - x0, y1 - y0
    L = dx * dx + dy * dy or 1e-9
    t = np.clip(((_XS - x0) * dx + (_YS - y0) * dy) / L, 0, 1)
    return np.hypot(_XS - (x0 + t * dx), _YS - (y0 + t * dy))


# Animation: every body plan can draw itself in these poses, 4 frames each.
ACTS = ("idle", "walk", "fly", "swim", "sleep", "sit", "look", "back")
FRAMES = 4


class Sprite:
    def __init__(self, act: str = "idle", f: int = 0):
        self.col = np.zeros((N, N, 3), np.int32)
        self.reg = np.zeros((N, N), np.int32)
        self.shaded: dict[int, bool] = {}
        self.edged: set[int] = set()
        self.n = 0
        self.last = np.zeros((N, N), bool)
        # The pose being drawn, and the poses this body plan really draws (the rest
        # fall back to idle). Eyes are found as they're drawn so sleep can close them.
        self.act, self.f = act, f
        self.acts = {"idle", "sleep"}
        self.eye_px = np.zeros((N, N), bool)
        self.eye_boxes: list[tuple[int, int, int, int]] = []
        self.fwd, self.xs, self.ys = None, _XS, _YS

    def wave(self, off: float = 0.0) -> float:
        """Goes 0, 1, 0, -1 over the four frames (shifted by off, in cycles)."""
        return math.sin((self.f / FRAMES + off) * 2 * math.pi)

    def can(self, *acts):
        """Declare poses this body plan draws."""
        self.acts.update(acts)

    def shift(self, dx: int, dy: int):
        """Move everything drawn so far."""
        self.col = np.roll(np.roll(self.col, dy, axis=0), dx, axis=1)
        self.reg = np.roll(np.roll(self.reg, dy, axis=0), dx, axis=1)
        self.eye_px = np.roll(np.roll(self.eye_px, dy, axis=0), dx, axis=1)
        self.eye_boxes = [(x0 + dx, y0 + dy, x1 + dx, y1 + dy) for x0, y0, x1, y1 in self.eye_boxes]
        for a in (self.col, self.reg, self.eye_px):
            if dy > 0:
                a[:dy] = 0
            elif dy < 0:
                a[dy:] = 0
            if dx > 0:
                a[:, :dx] = 0
            elif dx < 0:
                a[:, dx:] = 0

    def eye_box(self, x0, y0, x1, y1, mirror=False):
        """Mark a big eye (x0..x1, y0..y1 inclusive) to be closed when asleep."""
        if self.fwd is not None:
            (x0, y0), (x1, y1) = (tuple(round(v) for v in self._to(x, y)) for x, y in ((x0, y0), (x1, y1)))
        x0, y0, x1, y1 = x0 + PAD_X, y0 + PAD_TOP, x1 + PAD_X, y1 + PAD_TOP  # stored as canvas pixels
        self.eye_boxes.append((x0, y0, x1, y1))
        if mirror:
            self.eye_boxes.append((N - 1 - x1, y0, N - 1 - x0, y1))

    def _close_eyes(self):
        """Asleep: paint over each eye with the face around it and draw a closed lid."""
        boxes = list(self.eye_boxes)
        seen = np.zeros((N, N), bool)
        for y, x in zip(*np.where(self.eye_px)):
            if seen[y, x] or any(x0 <= x <= x1 and y0 <= y <= y1 for x0, y0, x1, y1 in boxes):
                continue
            stack, pts = [(y, x)], []
            while stack:  # one cluster of eye pixels = one eye
                cy, cx = stack.pop()
                if 0 <= cy < N and 0 <= cx < N and self.eye_px[cy, cx] and not seen[cy, cx]:
                    seen[cy, cx] = True
                    pts.append((cy, cx))
                    stack += [(cy + 1, cx), (cy - 1, cx), (cy, cx + 1), (cy, cx - 1)]
            ys, xs = zip(*pts)
            boxes.append((min(xs), min(ys), max(xs), max(ys)))
        for x0, y0, x1, y1 in boxes:
            x0, y0, x1, y1 = max(x0, 0), max(y0, 0), min(x1, N - 1), min(y1, N - 1)
            sx, sy = (x0 + x1) // 2, y0 - 1
            if sy < 0 or self.reg[sy, sx] == 0 or self.eye_px[sy, sx]:
                sx, sy = x0 - 1, (y0 + y1) // 2
            if sx < 0 or self.reg[sy, sx] == 0:
                continue
            self.col[y0:y1 + 1, x0:x1 + 1] = self.col[sy, sx]
            self.reg[y0:y1 + 1, x0:x1 + 1] = self.reg[sy, sx]
            lid = np.zeros((N, N), bool)
            ly = y1 if y1 - y0 < 2 else (y0 + y1 + 1) // 2
            lid[ly, x0:x1 + 1] = True
            if x1 - x0 >= 3:
                lid[ly - 1, x0], lid[ly - 1, x1], lid[ly, x0], lid[ly, x1] = True, True, False, False
            self.n += 1
            self.col[lid] = np.array(mix(tuple(self.col[sy, sx]), OUTLINE_INK, 0.75))
            self.reg[lid] = self.n
            self.shaded[self.n] = False

    # -- masks -----------------------------------------------------------------
    def set_warp(self, fwd):
        """Bend everything drawn from now on through fwd(x, y) -> (x', y') (numpy arrays
        in, arrays out): a body plan uses it to re-proportion a drawing without moving
        the details each species adds in the plan's own coordinates."""
        self.fwd = fwd
        qx, qy = _XS.copy(), _YS.copy()
        for _ in range(40):  # invert fwd numerically: the source point of each pixel
            fx, fy = fwd(qx, qy)
            qx, qy = qx + 0.7 * (_XS - fx), qy + 0.7 * (_YS - fy)
        self.xs, self.ys = qx, qy

    def unwarped(self):
        """Context manager: draw in plain canvas coordinates for a while."""
        sprite = self

        class _Plain:
            def __enter__(self):
                self.saved = sprite.fwd, sprite.xs, sprite.ys
                sprite.fwd, sprite.xs, sprite.ys = None, _XS, _YS

            def __exit__(self, *exc):
                sprite.fwd, sprite.xs, sprite.ys = self.saved
        return _Plain()

    def _to(self, x, y):
        """Where a drawing coordinate lands on the canvas."""
        if self.fwd is None:
            return x, y
        fx, fy = self.fwd(np.float32(x), np.float32(y))
        return float(fx), float(fy)

    def m_ellipse(self, cx, cy, rx, ry, rot=0.0):
        x, y = self.xs - cx, self.ys - cy
        if rot:
            c, s = math.cos(math.radians(rot)), math.sin(math.radians(rot))
            x, y = x * c + y * s, -x * s + y * c
        return (x / rx) ** 2 + (y / ry) ** 2 <= 1.0

    def m_poly(self, pts):
        inside = np.zeros((N, N), bool)
        n = len(pts)
        for i in range(n):
            x0, y0 = pts[i]
            x1, y1 = pts[(i + 1) % n]
            if y0 == y1:
                continue
            cond = (y0 > self.ys) != (y1 > self.ys)
            xint = x0 + (self.ys - y0) * (x1 - x0) / (y1 - y0)
            inside ^= cond & (self.xs < xint)
        return inside

    def m_path(self, pts, r):
        """Thick polyline; r may be a number or a (start, end) taper."""
        r0, r1 = (r, r) if not isinstance(r, tuple) else r
        segs = list(zip(pts, pts[1:]))
        lens = [math.dist(a, b) for a, b in segs]
        total = sum(lens) or 1
        m = np.zeros((N, N), bool)
        acc = 0.0
        for (a, b), L in zip(segs, lens):
            steps = max(2, int(L * 2))
            for k in range(steps + 1):
                t = k / steps
                x, y = a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t
                rr = r0 + (r1 - r0) * (acc + L * t) / total
                m |= np.hypot(self.xs - x, self.ys - y) <= rr
            acc += L
        return m

    def m_line(self, x0, y0, x1, y1):
        """1-pixel Bresenham line."""
        m = np.zeros((N, N), bool)
        (x0, y0), (x1, y1) = self._to(x0, y0), self._to(x1, y1)
        x0, y0, x1, y1 = (int(round(v)) for v in (x0, y0, x1, y1))
        dx, dy = abs(x1 - x0), -abs(y1 - y0)
        sx, sy = (1 if x0 < x1 else -1), (1 if y0 < y1 else -1)
        err = dx + dy
        while True:
            if 0 <= x0 + PAD_X < N and 0 <= y0 + PAD_TOP < N:
                m[y0 + PAD_TOP, x0 + PAD_X] = True
            if x0 == x1 and y0 == y1:
                break
            e2 = 2 * err
            if e2 >= dy:
                err += dy
                x0 += sx
            if e2 <= dx:
                err += dx
                y0 += sy
        return m

    def m_px(self, pts):
        m = np.zeros((N, N), bool)
        for x, y in pts:
            if self.fwd is not None:
                x, y = (round(v) for v in self._to(x, y))
            if 0 <= x + PAD_X < N and 0 <= y + PAD_TOP < N:
                m[int(y) + PAD_TOP, int(x) + PAD_X] = True
        return m

    # -- painting --------------------------------------------------------------
    def fill(self, mask, color, shade=True, mirror=False, edge=False, clip=None):
        """Paint a new region."""
        if mirror:
            mask = mask | mask[:, ::-1]
        if clip is not None:
            mask = mask & clip
        self.n += 1
        c = rgb(color)
        self.col[mask] = c
        self.reg[mask] = self.n
        # small near-black dots are eyes (pupils); anything drawn on top later isn't
        if not shade and sum(c) < 100 and 0 < mask.sum() <= 12:
            self.eye_px |= mask
        else:
            self.eye_px &= ~mask
        self.shaded[self.n] = shade
        if edge:
            self.edged.add(self.n)
        self.last = mask
        return mask

    def paint(self, mask, color, mirror=False, within=None):
        """Recolour pixels without creating a region (patterns on an existing shape)."""
        if mirror:
            mask = mask | mask[:, ::-1]
        if within is not None:
            mask = mask & within
        mask = mask & (self.reg > 0)
        self.col[mask] = rgb(color)
        return mask

    def ellipse(self, cx, cy, rx, ry, color, rot=0.0, **kw):
        return self.fill(self.m_ellipse(cx, cy, rx, ry, rot), color, **kw)

    def poly(self, pts, color, **kw):
        return self.fill(self.m_poly(pts), color, **kw)

    def path(self, pts, r, color, **kw):
        return self.fill(self.m_path(pts, r), color, **kw)

    def line(self, x0, y0, x1, y1, color, **kw):
        kw.setdefault("shade", False)
        return self.fill(self.m_line(x0, y0, x1, y1), color, **kw)

    def px(self, pts, color, **kw):
        kw.setdefault("shade", False)
        return self.fill(self.m_px(pts), color, **kw)

    def rect(self, x0, y0, x1, y1, color, **kw):
        m = (self.xs >= x0) & (self.xs < x1 + 1) & (self.ys >= y0) & (self.ys < y1 + 1)
        return self.fill(m, color, **kw)

    def erase(self, mask):
        self.reg[mask] = 0
        self.col[mask] = 0

    # -- details -----------------------------------------------------------------
    def eye(self, x, y, size=2, color="#1d1428", shine="#ffffff", mirror=False):
        pts = [(x + i, y + j) for i in range(size) for j in range(size)]
        self.px(pts, color, mirror=mirror)
        if size >= 2 and shine:
            self.px([(x, y)], shine, mirror=mirror)

    # -- output ----------------------------------------------------------------
    def render(self):
        if self.act == "sleep":
            self._close_eyes()
        col = self.col.astype(np.float32)
        filled = self.reg > 0
        for r in range(1, self.n + 1):
            R = self.reg == r
            if not R.any():
                continue
            if r in self.edged:
                # Darken this region's border against regions painted before it.
                below = filled & ~R & (self.reg < r)
                border = R & (_shift(below, 1, 0) | _shift(below, -1, 0)
                              | _shift(below, 0, 1) | _shift(below, 0, -1))
                col[border] = col[border] * 0.72 + np.array(OUTLINE_INK) * 0.28
            if not self.shaded.get(r):
                continue
            lum = _lum(R)
            # A later shape resting on this one casts a small shadow just below it.
            above = (self.reg > r) & np.isin(self.reg, [q for q, v in self.shaded.items() if v and q > r])
            contact = R & (_shift(above, 0, -1) | _shift(above, 0, -2))
            hi = R & (lum > 0.2)
            sh = R & (lum < -0.18)
            deep = R & (lum < -0.42)
            col[hi] = _tone(col[hi], 0.28)
            col[sh & ~deep] = _tone(col[sh & ~deep], -0.75)
            col[deep] = _tone(col[deep], -1.25)
            col[contact & ~sh] = _tone(col[contact & ~sh], -0.7)
            col[contact & sh] = _tone(col[contact & sh], -0.45)
        col = np.clip(col, 0, 255)

        img = np.zeros((N, N, 4), np.uint8)
        img[filled, :3] = col[filled].astype(np.uint8)
        img[filled, 3] = 255
        # Outline: empty pixels touching the sprite take a dark tint of their neighbour,
        # darkest on the shadowed bottom and right.
        for dx, dy, k in ((0, -1, .82), (-1, 0, .76), (0, 1, .6), (1, 0, .64)):
            nb = _shift(filled, dx, dy) & ~filled & (img[..., 3] == 0)
            src = np.roll(np.roll(col, -dy, axis=0), -dx, axis=1)
            tint = src * (1 - k) + np.array(OUTLINE_INK) * k
            img[nb, :3] = tint[nb].astype(np.uint8)
            img[nb, 3] = 255
        return Image.fromarray(img, "RGBA")


def _fill_holes(on: np.ndarray) -> np.ndarray:
    """Mark transparent pockets that can't be reached from the canvas edge as solid."""
    outside = np.zeros_like(on)
    stack = [(y, x) for y in range(N) for x in (0, N - 1)] + [(y, x) for x in range(N) for y in (0, N - 1)]
    while stack:
        y, x = stack.pop()
        if 0 <= y < N and 0 <= x < N and not on[y, x] and not outside[y, x]:
            outside[y, x] = True
            stack += [(y + 1, x), (y - 1, x), (y, x + 1), (y, x - 1)]
    return ~outside


def silhouette(img: Image.Image) -> Image.Image:
    """The shape alone, softly lit so it reads as a form rather than a flat blob."""
    a = np.array(img)
    out = np.zeros_like(a)
    on = _fill_holes(a[..., 3] > 0)
    lum = _lum(on)
    col = np.zeros((N, N, 3), np.float32) + SILHOUETTE
    col[on & (lum > 0.2)] += 16
    col[on & (lum < -0.18)] *= 0.84
    rim = on & ~(_shift(on, 0, 1) & _shift(on, 1, 0) & _shift(on, 0, -1) & _shift(on, -1, 0))
    col[rim] = col[rim] * 0.72 + np.array(OUTLINE_INK) * 0.28
    out[on, :3] = np.clip(col[on], 0, 255).astype(np.uint8)
    out[on, 3] = 255
    return Image.fromarray(out, "RGBA")
