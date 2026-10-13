"""A tiny 32x32 pixel-art canvas: filled shapes, automatic shading and outline.

Shapes are painted in order (later ones on top). Each shape is a "region"; after
drawing, every shaded region gets a darker underside and a lighter top edge, and
the whole sprite gets a 1-pixel outline tinted from the colour it borders.
"""
from __future__ import annotations

import math

import numpy as np
from PIL import Image

N = 32
_YS, _XS = np.mgrid[0:N, 0:N].astype(np.float32) + 0.5

OUTLINE_INK = (38, 26, 46)
SILHOUETTE = (74, 76, 102)


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
            h = np.where(R.any(axis=1))[0]
            k = 2 if (h.max() - h.min()) >= 6 else 1
            shadow = R & (~_shift(R, 0, k) | ~_shift(R, 1, 1))
            light = R & ~_shift(R, 0, -1) & ~shadow & _shift(R, 0, 1)
            col[shadow] = col[shadow] * np.array([0.78, 0.76, 0.86])
            col[light] = col[light] * 0.75 + 255 * 0.25
        col = np.clip(col, 0, 255)

        img = np.zeros((N, N, 4), np.uint8)
        img[filled, :3] = col[filled].astype(np.uint8)
        img[filled, 3] = 255
        # Outline: empty pixels touching the sprite take a dark tint of their neighbour.
        for dx, dy in ((0, 1), (0, -1), (1, 0), (-1, 0)):
            nb = _shift(filled, dx, dy) & ~filled & (img[..., 3] == 0)
            src = np.roll(np.roll(col, -dy, axis=0), -dx, axis=1)
            tint = src * 0.35 + np.array(OUTLINE_INK) * 0.65
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
    a = np.array(img)
    out = np.zeros_like(a)
    on = _fill_holes(a[..., 3] > 0)
    out[on, :3] = SILHOUETTE
    out[on, 3] = 255
    return Image.fromarray(out, "RGBA")
