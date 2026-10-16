"""A tiny 32x32 pixel-art canvas: filled shapes, automatic shading and outline.

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

N = 32
_YS, _XS = np.mgrid[0:N, 0:N].astype(np.float32) + 0.5

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


class Sprite:
    def __init__(self):
        self.col = np.zeros((N, N, 3), np.int32)
        self.reg = np.zeros((N, N), np.int32)
        self.shaded: dict[int, bool] = {}
        self.edged: set[int] = set()
        self.n = 0
        self.last = np.zeros((N, N), bool)

    # -- masks -----------------------------------------------------------------
    @staticmethod
    def m_ellipse(cx, cy, rx, ry, rot=0.0):
        x, y = _XS - cx, _YS - cy
        if rot:
            c, s = math.cos(math.radians(rot)), math.sin(math.radians(rot))
            x, y = x * c + y * s, -x * s + y * c
        return (x / rx) ** 2 + (y / ry) ** 2 <= 1.0

    @staticmethod
    def m_poly(pts):
        inside = np.zeros((N, N), bool)
        n = len(pts)
        for i in range(n):
            x0, y0 = pts[i]
            x1, y1 = pts[(i + 1) % n]
            if y0 == y1:
                continue
            cond = (y0 > _YS) != (y1 > _YS)
            xint = x0 + (_YS - y0) * (x1 - x0) / (y1 - y0)
            inside ^= cond & (_XS < xint)
        return inside

    @staticmethod
    def m_path(pts, r):
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
                m |= np.hypot(_XS - x, _YS - y) <= rr
            acc += L
        return m

    @staticmethod
    def m_line(x0, y0, x1, y1):
        """1-pixel Bresenham line."""
        m = np.zeros((N, N), bool)
        x0, y0, x1, y1 = (int(round(v)) for v in (x0, y0, x1, y1))
        dx, dy = abs(x1 - x0), -abs(y1 - y0)
        sx, sy = (1 if x0 < x1 else -1), (1 if y0 < y1 else -1)
        err = dx + dy
        while True:
            if 0 <= x0 < N and 0 <= y0 < N:
                m[y0, x0] = True
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

    @staticmethod
    def m_px(pts):
        m = np.zeros((N, N), bool)
        for x, y in pts:
            if 0 <= x < N and 0 <= y < N:
                m[int(y), int(x)] = True
        return m

    # -- painting --------------------------------------------------------------
    def fill(self, mask, color, shade=True, mirror=False, edge=False, clip=None):
        """Paint a new region."""
        if mirror:
            mask = mask | mask[:, ::-1]
        if clip is not None:
            mask = mask & clip
        self.n += 1
        self.col[mask] = rgb(color)
        self.reg[mask] = self.n
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
        m = (_XS >= x0) & (_XS < x1 + 1) & (_YS >= y0) & (_YS < y1 + 1)
        return self.fill(m, color, **kw)

    def erase(self, mask):
        self.reg[mask] = 0
        self.col[mask] = 0

    # -- cute details ----------------------------------------------------------
    def eye(self, x, y, size=2, color="#1d1428", shine="#ffffff", mirror=False):
        pts = [(x + i, y + j) for i in range(size) for j in range(size)]
        self.px(pts, color, mirror=mirror)
        if size >= 2 and shine:
            self.px([(x, y)], shine, mirror=mirror)

    def blush(self, x, y, w=2, color="#f59aa8", mirror=False):
        self.px([(x + i, y) for i in range(w)], color, mirror=mirror)

    # -- output ----------------------------------------------------------------
    def render(self):
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
