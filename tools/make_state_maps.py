"""Draw each state's Field Guide map: a field-journal atlas plate per state.

    pip install shapely numpy pillow playwright
    python tools/make_state_maps.py            # all 50 states
    python tools/make_state_maps.py --only MI CA

For every state in species/states.json it writes

  backend/app/static/maps/<CODE>.webp   the drawn map (shipped to web and Android)
  species/<state>_outline.json          the state's outline rings ([lon, lat]) plus
                                        "frame": the lon/lat box the map image covers

Layers, bottom to top: water with engraved coastline ripples, neighbouring states
and Canada/Mexico washed out, the state in parchment with shaded relief and a
gentle elevation tint, lakes, rivers, a hand-tinted border band, the biggest
towns and the capital, neighbour and water names, a compass rose and scale bar.
The sighting grid is drawn on top by the apps, so the map has no species on it.

Sources (downloaded once into --cache):
  Natural Earth 1:10m (public domain): states with the Great Lakes cut out,
    countries, lakes, rivers, populated places. github.com/nvkelso/natural-earth-vector
  Terrain Tiles on AWS Open Data (terrarium PNGs; in the US from USGS 3DEP/NED and
    SRTM, public domain). Attribution: "Terrain Tiles: Mapzen, AWS Open Data".
"""
from __future__ import annotations

import argparse
import base64
import io
import json
import math
import urllib.request
from pathlib import Path

import numpy as np
from PIL import Image
from shapely.geometry import MultiPolygon, Polygon, box, shape
from shapely.ops import unary_union

ROOT = Path(__file__).resolve().parent.parent
SPECIES = ROOT / "species"
OUT = ROOT / "backend" / "app" / "static" / "maps"
FONT = ROOT / "backend" / "app" / "static" / "vendor" / "fonts" / "spacegrotesk.woff2"
NE = "https://raw.githubusercontent.com/nvkelso/natural-earth-vector/master/geojson/"
TERRAIN = "https://s3.amazonaws.com/elevation-tiles-prod/terrarium/{z}/{x}/{y}.png"
W = 900  # image width in px; the apps show it ~430 css px wide, so it's sharp at 2x

# Field Journal palette.
WATER, WATER_LINE, WATER_TEXT = "#dfe8e4", "#9fb9b6", "#6e8f92"
NEIGHBOR, NEIGHBOR_LINE, NEIGHBOR_TEXT = "#efe9da", "#c4b79c", "#a39478"
INK, BAND, RIVER = "#5a4630", "#c49a5a", "#7fa3ad"

# Elevation tint (metres -> colour), deliberately quiet so the green sightings read.
TINT = [(-50, (226, 230, 204)), (150, (232, 230, 202)), (600, (238, 228, 196)),
        (1500, (233, 214, 178)), (2600, (222, 203, 171)), (3600, (226, 218, 204)),
        (5000, (240, 238, 232))]

# Names drawn on the water. (lon, lat) are just a starting point; a label moves to
# the nearest open water inside the frame.
SEAS = [("Pacific Ocean", -125.5, 36), ("Pacific Ocean", -158.5, 19.4), ("Gulf of Alaska", -146, 57.5),
        ("Bering Sea", -172, 58), ("Arctic Ocean", -155, 72), ("Gulf of Mexico", -89.5, 27.5),
        ("Atlantic Ocean", -72.5, 38), ("Atlantic Ocean", -79, 31), ("Gulf of Maine", -68.6, 43.4), ("Atlantic Ocean", -67.5, 42.4),
        ("Atlantic Ocean", -80, 25.6), ("Chesapeake Bay", -76.2, 37.5), ("Long Island Sound", -72.9, 41.1),
        ("Puget Sound", -122.45, 47.7)]


def fetch(url: str, path: Path) -> Path:
    if not path.exists():
        path.parent.mkdir(parents=True, exist_ok=True)
        print("download", url)
        req = urllib.request.Request(url, headers={"User-Agent": "CaptureAnimals map builder"})
        path.write_bytes(urllib.request.urlopen(req, timeout=300).read())
    return path


def ne(name: str, cache: Path) -> list[dict]:
    return json.loads(fetch(NE + name + ".geojson", cache / (name + ".geojson")).read_text(encoding="utf-8"))["features"]


def west_hemisphere(g):
    """Alaska's Aleutians cross the date line; shift the eastern-hemisphere bits west."""
    polys = list(g.geoms) if isinstance(g, MultiPolygon) else [g]
    out = []
    for p in polys:
        if p.bounds[0] > 0:
            p = Polygon([(x - 360, y) for x, y in p.exterior.coords], [[(x - 360, y) for x, y in r.coords] for r in p.interiors])
        out.append(p)
    return unary_union(out)


def state_geom(code: str, g):
    if code == "AK":
        g = west_hemisphere(g)
        g = g.intersection(box(-180, 50, -129, 72))  # main state + Aleutians to ~Atka
    if code == "HI":
        g = g.intersection(box(-160.6, 18.5, -154.5, 22.5))  # main islands, not the chain to Midway
    return g


# --- frame ------------------------------------------------------------------

class Frame:
    def __init__(self, west, east, south, north):
        self.k = math.cos(math.radians((south + north) / 2))
        # Keep the plate between 2.1:1 wide and 1:1.25 tall by widening the view.
        dx, dy = (east - west) * self.k, north - south
        if dx / dy > 2.1:
            pad = (dx / 2.1 - dy) / 2; south, north = south - pad, north + pad
        elif dy / dx > 1.25:
            pad = (dy / 1.25 - dx) / 2 / self.k; west, east = west - pad, east + pad
        self.west, self.east, self.south, self.north = west, east, south, north
        self.w = W
        self.h = round(W * (north - south) / ((east - west) * self.k))

    def x(self, lon): return (lon - self.west) / (self.east - self.west) * self.w
    def y(self, lat): return (self.north - lat) / (self.north - self.south) * self.h
    def lon(self, x): return self.west + x / self.w * (self.east - self.west)
    def lat(self, y): return self.north - y / self.h * (self.north - self.south)
    def km_per_px(self): return (self.east - self.west) * 111.32 * self.k / self.w
    def box(self, grow=0.0):
        gx, gy = (self.east - self.west) * grow, (self.north - self.south) * grow
        return box(self.west - gx, self.south - gy, self.east + gx, self.north + gy)


CORNER_W, CORNER_H = 270, 250  # room for the compass rose and scale bar


def corners(f: Frame) -> dict:
    return {"br": (f.w - CORNER_W, f.h - CORNER_H, f.w, f.h), "bl": (0, f.h - CORNER_H, CORNER_W, f.h),
            "tr": (f.w - CORNER_W, 0, f.w, CORNER_H), "tl": (0, 0, CORNER_W, CORNER_H)}


def best_corner(f: Frame, g):
    """The corner with the least of the state under it, and how much (0..1) that is."""
    def cover(c):
        x0, y0, x1, y1 = corners(f)[c]
        b = box(f.lon(x0), f.lat(y1), f.lon(x1), f.lat(y0))
        return b.intersection(g).area / b.area
    c = min(corners(f), key=lambda c: (round(cover(c), 3), list(corners(f)).index(c)))
    return c, cover(c)


def frame_for(g) -> Frame:
    w, s, e, n = g.bounds
    px, py = (e - w) * 0.06 + 0.15, (n - s) * 0.06 + 0.12
    f = Frame(w - px, e + px, s - py, n + py)
    if best_corner(f, g)[1] < 0.01:
        return f
    # Boxy states (Colorado, Wyoming...) fill every corner: open a strip for the compass.
    tries = []
    for side in ("south", "east", "west", "north"):
        dx = (f.east - f.west) * (CORNER_W + 10) / f.w
        dy = (f.north - f.south) * (CORNER_H + 10) / f.h
        box_ = dict(west=f.west, east=f.east, south=f.south, north=f.north)
        if side == "south": box_["south"] -= dy
        if side == "north": box_["north"] += dy
        if side == "east": box_["east"] += dx
        if side == "west": box_["west"] -= dx
        g2 = Frame(box_["west"], box_["east"], box_["south"], box_["north"])
        tries.append((round(best_corner(g2, g)[1], 3), g2))
    return min(tries, key=lambda t: t[0])[1]


def path_d(g, f: Frame) -> str:
    polys = list(g.geoms) if hasattr(g, "geoms") else [g]
    out = []
    for p in polys:
        if p.is_empty or not isinstance(p, Polygon):
            continue
        for ring in [p.exterior, *p.interiors]:
            pts = [f"{f.x(x):.1f},{f.y(y):.1f}" for x, y in ring.coords]
            out.append("M" + "L".join(pts) + "Z")
    return "".join(out)


def line_d(g, f: Frame) -> str:
    lines = list(g.geoms) if hasattr(g, "geoms") else [g]
    out = []
    for l in lines:
        if l.is_empty or l.geom_type != "LineString":
            continue
        out.append("M" + "L".join(f"{f.x(x):.1f},{f.y(y):.1f}" for x, y in l.coords))
    return "".join(out)


# --- terrain ----------------------------------------------------------------

def merc_px(lon, lat, z):
    n = 256 * 2 ** z
    x = (lon + 180) / 360 * n
    lat = np.clip(lat, -85, 85)
    y = (1 - np.log(np.tan(np.radians(lat)) + 1 / np.cos(np.radians(lat))) / math.pi) / 2 * n
    return x, y


def elevation(f: Frame, cache: Path) -> np.ndarray:
    """Elevation in metres for every map pixel, from terrarium tiles."""
    deg_per_px = (f.east - f.west) / f.w
    z = max(3, min(11, math.ceil(math.log2(360 / (256 * deg_per_px)))))
    x0, y0 = merc_px(f.west, f.north, z)
    x1, y1 = merc_px(f.east, f.south, z)
    tx0, ty0, tx1, ty1 = int(x0 // 256), int(y0 // 256), int(x1 // 256), int(y1 // 256)
    mosaic = np.zeros(((ty1 - ty0 + 1) * 256, (tx1 - tx0 + 1) * 256), np.float32)
    for ty in range(ty0, ty1 + 1):
        for tx in range(tx0, tx1 + 1):
            p = fetch(TERRAIN.format(z=z, x=tx % 2 ** z, y=ty), cache / "terrain" / f"{z}_{tx % 2 ** z}_{ty}.png")
            a = np.asarray(Image.open(p).convert("RGB"), np.float32)
            mosaic[(ty - ty0) * 256:(ty - ty0 + 1) * 256, (tx - tx0) * 256:(tx - tx0 + 1) * 256] = \
                a[..., 0] * 256 + a[..., 1] + a[..., 2] / 256 - 32768
    lons = f.lon(np.arange(f.w) + 0.5)
    lats = f.lat(np.arange(f.h) + 0.5)
    mx, _ = merc_px(lons, np.zeros_like(lons), z)
    _, my = merc_px(np.zeros_like(lats), lats, z)
    mx -= tx0 * 256; my -= ty0 * 256
    # Bilinear sample.
    X, Y = np.meshgrid(mx - 0.5, my - 0.5)
    xi = np.clip(np.floor(X).astype(int), 0, mosaic.shape[1] - 2); yi = np.clip(np.floor(Y).astype(int), 0, mosaic.shape[0] - 2)
    fx = np.clip(X - xi, 0, 1); fy = np.clip(Y - yi, 0, 1)
    e = (mosaic[yi, xi] * (1 - fx) * (1 - fy) + mosaic[yi, xi + 1] * fx * (1 - fy)
         + mosaic[yi + 1, xi] * (1 - fx) * fy + mosaic[yi + 1, xi + 1] * fx * fy)
    return e


def relief_png(f: Frame, cache: Path) -> str:
    e = elevation(f, cache)
    m = f.km_per_px() * 1000
    # Exaggerate flat states more so the Ozarks and Driftless still show.
    ve = 2.2 * (m / 250) ** 0.35
    gy, gx = np.gradient(e * ve, m)
    shade = np.zeros_like(e)
    for az, wgt in ((315, 0.55), (270, 0.2), (360, 0.25)):  # soft multi-directional light
        a, alt = math.radians(az), math.radians(45)
        slope = np.arctan(np.hypot(gx, gy)); aspect = np.arctan2(-gx, gy)
        shade += wgt * (np.sin(alt) * np.cos(slope) + np.cos(alt) * np.sin(slope) * np.cos(a - aspect))
    shade = np.clip(shade, 0, 1)
    flat = math.sin(math.radians(45))
    # Tint by elevation.
    ks = np.array([t[0] for t in TINT], np.float32)
    rgb = np.stack([np.interp(e, ks, [t[1][c] for t in TINT]) for c in range(3)], -1)
    # Light slopes brighten a little, shadowed slopes darken toward warm brown.
    d = (shade - flat)[..., None]
    shadow = np.array([92, 70, 48], np.float32)
    rgb = np.where(d < 0, rgb + (shadow - rgb) * np.clip(-d * 1.5, 0, 0.75), rgb + (255 - rgb) * np.clip(d * 0.9, 0, 0.5))
    img = Image.fromarray(np.clip(rgb, 0, 255).astype(np.uint8))
    buf = io.BytesIO(); img.save(buf, "PNG")
    return "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode()


# --- labels -----------------------------------------------------------------

class Placer:
    """Greedy label placement: skip anything that would overlap what's placed."""
    def __init__(self, f: Frame):
        self.f, self.boxes = f, []

    def free(self, x0, y0, x1, y1):
        if x0 < 8 or y0 < 8 or x1 > self.f.w - 8 or y1 > self.f.h - 8:
            return False
        return all(x1 < a or x0 > c or y1 < b or y0 > d for a, b, c, d in self.boxes)

    def take(self, *b):
        self.boxes.append(b)


def text_w(s: str, size: float, spacing: float = 0) -> float:
    return len(s) * size * 0.56 + len(s) * spacing


def esc(s: str) -> str:
    return s.replace("&", "&amp;").replace("<", "&lt;")


# --- one state --------------------------------------------------------------

def draw_state(code, name, geoms, data, cache: Path):
    g = geoms[code]
    f = frame_for(g)
    view = f.box(0.02)
    big = f.box(0.3)
    others = {c: o.intersection(big) for c, o in geoms.items() if c != code and o.intersects(big)}
    countries = [c.intersection(big) for c in data["countries"] if c.intersects(big)]
    land_all = unary_union([g, *others.values(), *countries])
    lakes = [(n, l.intersection(big), r) for n, l, r in data["lakes"] if l.intersects(view)]
    lake_u = unary_union([l for _, l, _ in lakes]) if lakes else Polygon()
    land_all = land_all.difference(lake_u)
    rivers = [(r.intersection(big), rank) for r, rank in data["rivers"] if r.intersects(view)]

    land_d, state_d = path_d(land_all, f), path_d(g, f)
    neighbor_d = path_d(unary_union([*others.values(), *countries]).difference(lake_u), f)
    lakes_d = path_d(lake_u, f)
    state_borders = line_d(unary_union([o.boundary for o in others.values()]).intersection(land_all.buffer(-0.001)), f)
    nation_borders = line_d(unary_union([c.boundary for c in countries]).intersection(land_all.buffer(-0.001)), f) if countries else ""

    # Engraved ripple lines along every shore (outside the land, inside lakes).
    ripples = []
    for i, d in enumerate((5, 11, 18, 27)):
        op = 0.9 - i * 0.18
        ripples.append(f'<path d="{land_d}" fill="none" stroke="{WATER_LINE}" stroke-opacity="{op:.2f}" '
                       f'stroke-width="{2 * d + 1.3}" stroke-linejoin="round"/>'
                       f'<path d="{land_d}" fill="none" stroke="{WATER}" stroke-width="{2 * d - 0.2}" stroke-linejoin="round"/>')
    ripples.reverse()

    # Rivers: bigger rivers (low scalerank) wider.
    river_svg = []
    for r, rank in rivers:
        dd = line_d(r, f)
        if dd:
            wdt = max(0.7, 2.6 - rank * 0.22)
            river_svg.append(f'<path d="{dd}" stroke-width="{wdt:.2f}"/>')

    pl = Placer(f)
    labels = []
    # Compass and scale bar go in the emptiest bottom/top corner.
    corner = best_corner(f, g)[0]
    cx0, cy0, cx1, cy1 = corners(f)[corner]
    pl.take(cx0, cy0, cx1, cy1)
    rose_x, rose_y = (cx0 + cx1) / 2, cy0 + 100
    km = f.km_per_px()
    target_mi = 170 * km / 1.609
    nice = min((1, 2, 5, 10, 20, 25, 50, 100, 200, 250, 500), key=lambda v: abs(v - target_mi))
    bar = nice * 1.609 / km

    # Towns: the capital plus the biggest few.
    towns = [t for t in data["places"] if t["state"] == name and g.buffer(0.02).contains(t["pt"])]
    towns.sort(key=lambda t: (not t["capital"], -t["pop"]))
    shown = []
    for t in towns:
        if len(shown) >= 5 or (not t["capital"] and t["pop"] < 60000 and shown):
            continue
        x, y = f.x(t["pt"].x), f.y(t["pt"].y)
        size = 30 if t["capital"] or len(shown) < 2 else 26
        tw = text_w(t["name"], size)
        for dx, anchor in ((13, "start"), (-13, "end")):
            x0 = x + dx if anchor == "start" else x + dx - tw
            if pl.free(x0 - 2, y - size * 0.8, x0 + tw + 2, y + size * 0.35) and pl.free(x - 8, y - 8, x + 8, y + 8):
                pl.take(x0 - 2, y - size * 0.8, x0 + tw + 2, y + size * 0.35); pl.take(x - 8, y - 8, x + 8, y + 8)
                mark = (f'<path d="M0,-7l2,5.4h5.7l-4.6,3.4l1.8,5.5l-4.9,-3.4l-4.9,3.4l1.8,-5.5l-4.6,-3.4h5.7z" class="cap" transform="translate({x:.1f},{y:.1f}) scale(1.6)"/>'
                        if t["capital"] else f'<circle cx="{x:.1f}" cy="{y:.1f}" r="5.5" class="town"/>')
                labels.append(mark + f'<text x="{x + dx:.1f}" y="{y + size * 0.33:.1f}" text-anchor="{anchor}" '
                              f'class="town-t" font-size="{size}">{esc(t["name"])}</text>')
                shown.append(t)
                break

    # Neighbour names, in their own land inside the frame.
    def place_in(region, text, size, cls, spacing=0.0, tries=None):
        if region.is_empty:
            return
        tw, th = text_w(text, size, spacing), size
        pts = tries or []
        rp = region.representative_point()
        pts = pts + [(rp.x, rp.y)]
        # A few more candidates on a grid inside the region.
        x0, y0, x1, y1 = region.bounds
        for i in range(1, 6):
            for j in range(1, 6):
                pts.append((x0 + (x1 - x0) * i / 6, y0 + (y1 - y0) * j / 6))
        for lon, lat in pts:
            x, y = f.x(lon), f.y(lat)
            bx = box(f.lon(x - tw / 2), f.lat(y + th * 0.4), f.lon(x + tw / 2), f.lat(y - th * 0.8))
            if region.contains(bx) and pl.free(x - tw / 2, y - th * 0.8, x + tw / 2, y + th * 0.4):
                pl.take(x - tw / 2, y - th * 0.8, x + tw / 2, y + th * 0.4)
                labels.append(f'<text x="{x:.1f}" y="{y:.1f}" text-anchor="middle" class="{cls}" font-size="{size}" '
                              f'letter-spacing="{spacing}">{esc(text)}</text>')
                return

    for c, o in others.items():
        place_in(o.intersection(view).difference(lake_u), data["names"][c].upper(), 22, "nb", 3)
    for cname, c in zip(data["country_names"], data["countries"]):
        place_in(c.intersection(view), cname.upper(), 24, "nb", 3.5)
    water = view.difference(land_all.buffer(0.05)) if not land_all.is_empty else view
    for lname, l, rank in sorted(lakes, key=lambda t: t[2]):
        if lname and l.area > 0.02 * (f.east - f.west) ** 2 * 0.02:
            place_in(l.intersection(view).buffer(-0.02), lname, 25, "sea")
    seen = set()
    reach = (f.east - f.west) * 0.3
    for sname, lon, lat in SEAS:
        anchor = box(lon - reach, lat - reach, lon + reach, lat + reach)
        if sname in seen or not anchor.intersects(view):
            continue
        before = len(labels)
        place_in(water.intersection(anchor), sname, 28, "sea", 1.0, tries=[(lon, lat)])
        if len(labels) > before:
            seen.add(sname)


    rose = f'''<g transform="translate({rose_x:.0f},{rose_y:.0f}) scale(1.45)" class="rose">
  <circle r="34" class="r1"/><circle r="28" class="r2"/>
  <path d="M0,-46 L7,-7 L0,0 Z" class="dark"/><path d="M0,-46 L-7,-7 L0,0 Z" class="light"/>
  <path d="M0,46 L-7,7 L0,0 Z" class="dark"/><path d="M0,46 L7,7 L0,0 Z" class="light"/>
  <path d="M46,0 L7,7 L0,0 Z" class="dark"/><path d="M46,0 L7,-7 L0,0 Z" class="light"/>
  <path d="M-46,0 L-7,-7 L0,0 Z" class="dark"/><path d="M-46,0 L-7,7 L0,0 Z" class="light"/>
  <path d="M0,-26 L4,-4 L0,0 Z M26,0 L4,4 L0,0Z M0,26 L-4,4 L0,0Z M-26,0 L-4,-4 L0,0Z" class="dark" transform="rotate(45)"/>
  <text y="-52" text-anchor="middle" font-size="15" class="n">N</text>
</g>
<g transform="translate({rose_x - bar / 2:.1f},{rose_y + 90:.0f})" class="scale">
  <rect width="{bar / 2:.1f}" height="9" class="sd"/><rect x="{bar / 2:.1f}" width="{bar / 2:.1f}" height="9" class="sl"/>
  <text x="0" y="32" text-anchor="start" font-size="20">0</text>
  <text x="{bar:.1f}" y="32" text-anchor="end" font-size="20">{nice} mi</text>
</g>'''

    # Graticule every 1, 2 or 5 degrees.
    step = 1 if f.east - f.west < 12 else 2 if f.east - f.west < 25 else 5
    grat = []
    for lon in range(math.ceil(f.west / step) * step, math.floor(f.east) + 1, step):
        grat.append(f"M{f.x(lon):.1f},0V{f.h}")
    for lat in range(math.ceil(f.south / step) * step, math.floor(f.north) + 1, step):
        grat.append(f"M0,{f.y(lat):.1f}H{f.w}")

    font = base64.b64encode(FONT.read_bytes()).decode()
    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="{f.w}" height="{f.h}" viewBox="0 0 {f.w} {f.h}">
<defs>
  <style>
    @font-face {{ font-family: SG; src: url(data:font/woff2;base64,{font}); }}
    text {{ font-family: SG, sans-serif; paint-order: stroke; stroke-linejoin: round; }}
    .town {{ fill: {INK}; stroke: #fff8e8; stroke-width: 1.6; }}
    .cap {{ fill: #9c3b25; stroke: #fff8e8; stroke-width: 1.2; }}
    .town-t {{ fill: #3c2e1f; stroke: #f6eedb; stroke-width: 5; font-weight: 600; }}
    .nb {{ fill: {NEIGHBOR_TEXT}; stroke: {NEIGHBOR}; stroke-width: 4; font-weight: 600; }}
    .sea {{ fill: {WATER_TEXT}; stroke: {WATER}; stroke-width: 4; font-style: italic; font-family: 'Liberation Serif', serif; }}
    .rose .r1 {{ fill: none; stroke: {INK}; stroke-width: 1.2; opacity: .7 }}
    .rose .r2 {{ fill: none; stroke: {INK}; stroke-width: .7; stroke-dasharray: 2 3; opacity: .7 }}
    .rose .dark {{ fill: {INK}; }} .rose .light {{ fill: #f3ead3; stroke: {INK}; stroke-width: .8; }}
    .rose .n {{ fill: {INK}; font-weight: 700; stroke: #f3ead3; stroke-width: 3; }}
    .scale rect {{ stroke: {INK}; stroke-width: 1; }} .scale .sd {{ fill: {INK}; }} .scale .sl {{ fill: #f6eedb; }}
    .scale text {{ fill: {INK}; stroke: #f3ead3; stroke-width: 4; font-weight: 600; }}
  </style>
  <clipPath id="land"><path d="{land_d}" clip-rule="evenodd"/></clipPath>
  <clipPath id="state"><path d="{state_d}" clip-rule="evenodd"/></clipPath>
  <filter id="paper" x="0" y="0" width="100%" height="100%">
    <feTurbulence type="fractalNoise" baseFrequency=".9" numOctaves="2" seed="3"/>
    <feColorMatrix values="0 0 0 0 .35  0 0 0 0 .27  0 0 0 0 .18  0 0 0 .07 0"/>
    <feComposite in2="SourceGraphic" operator="in"/>
  </filter>
  <filter id="blotch" x="0" y="0" width="100%" height="100%">
    <feTurbulence type="fractalNoise" baseFrequency=".012" numOctaves="3" seed="8"/>
    <feColorMatrix values="0 0 0 0 .55  0 0 0 0 .42  0 0 0 0 .25  0 0 0 .10 -.02"/>
  </filter>
</defs>
<rect width="{f.w}" height="{f.h}" fill="{WATER}"/>
<path d="{''.join(grat)}" stroke="{WATER_LINE}" stroke-width=".8" stroke-dasharray="1 4" opacity=".8" fill="none"/>
{''.join(ripples)}
<g clip-path="url(#land)">
  <image href="{relief_png(f, cache)}" width="{f.w}" height="{f.h}" preserveAspectRatio="none"/>
  <path d="{neighbor_d}" fill="{NEIGHBOR}" fill-opacity=".78" fill-rule="evenodd"/>
</g>
<g clip-path="url(#land)" fill="none" stroke="{RIVER}" stroke-linecap="round" stroke-linejoin="round" opacity=".9">{''.join(river_svg)}</g>
<path d="{lakes_d}" fill="none" stroke="{WATER_LINE}" stroke-width="1" fill-rule="evenodd"/>
<path d="{state_borders}" fill="none" stroke="{NEIGHBOR_LINE}" stroke-width="1.1" stroke-dasharray="5 3"/>
<path d="{nation_borders}" fill="none" stroke="{NEIGHBOR_LINE}" stroke-width="1.6" stroke-dasharray="8 3 2 3"/>
<g clip-path="url(#state)"><path d="{state_d}" fill="none" stroke="{BAND}" stroke-opacity=".45" stroke-width="18" stroke-linejoin="round"/></g>
<path d="{state_d}" fill="none" stroke="{INK}" stroke-width="2.4" stroke-linejoin="round"/>
<rect width="{f.w}" height="{f.h}" filter="url(#blotch)"/>
<rect width="{f.w}" height="{f.h}" fill="#000" filter="url(#paper)"/>
{''.join(labels)}
{rose}
<rect x="3" y="3" width="{f.w - 6}" height="{f.h - 6}" fill="none" stroke="{INK}" stroke-width="1.4"/>
<rect x="8" y="8" width="{f.w - 16}" height="{f.h - 16}" fill="none" stroke="{INK}" stroke-width=".6"/>
</svg>'''
    return f, svg


def rings_of(g, min_area: float) -> list:
    polys = list(g.geoms) if hasattr(g, "geoms") else [g]
    out = []
    for p in polys:
        if isinstance(p, Polygon) and not p.is_empty and p.area > min_area:
            out.append([[round(x, 4), round(y, 4)] for x, y in p.exterior.coords])
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--only", nargs="*")
    ap.add_argument("--cache", default=str(Path.home() / ".cache" / "capture-animals-maps"))
    ap.add_argument("--svg", help="also save the SVGs in this folder")
    args = ap.parse_args()
    cache = Path(args.cache)
    sj = json.loads((SPECIES / "states.json").read_text(encoding="utf-8"))["states"]

    feats = [x for x in ne("ne_10m_admin_1_states_provinces_lakes", cache) if x["properties"].get("adm0_a3") == "USA"]
    by_name = {x["properties"]["name"]: x for x in feats}
    geoms, names = {}, {}
    for x in feats:
        c = x["properties"]["postal"]
        if c == "DC":
            continue
        geoms[c] = state_geom(c, shape(x["geometry"]).buffer(0))
        names[c] = x["properties"]["name"]
    # Fold DC into Maryland's neighbourhood so it isn't a hole.
    dc = next(shape(x["geometry"]) for x in feats if x["properties"]["postal"] == "DC")
    countries, country_names = [], []
    for x in ne("ne_10m_admin_0_countries_lakes", cache):
        if x["properties"]["ADM0_A3"] in ("CAN", "MEX", "RUS", "BHS", "CUB"):
            countries.append(west_hemisphere(shape(x["geometry"]).buffer(0)) if x["properties"]["ADM0_A3"] == "RUS"
                             else shape(x["geometry"]).buffer(0))
            country_names.append({"CAN": "Canada", "MEX": "Mexico", "RUS": "Russia", "BHS": "Bahamas", "CUB": "Cuba"}[x["properties"]["ADM0_A3"]])
    countries.append(dc); country_names.append("")
    lakes = [(x["properties"].get("name") or "", shape(x["geometry"]).buffer(0), x["properties"].get("scalerank", 9))
             for x in ne("ne_10m_lakes", cache) if x["geometry"]]
    lakes = [l for l in lakes if l[1].bounds[0] < -60 and l[1].bounds[1] > 15]
    rivers = [(shape(x["geometry"]), x["properties"].get("scalerank", 9))
              for x in ne("ne_10m_rivers_lake_centerlines", cache)
              if x["geometry"] and x["properties"].get("featurecla") != "Lake Centerline"]
    rivers = [r for r in rivers if r[0].bounds[0] < -60 and r[0].bounds[1] > 15]
    from shapely.geometry import Point
    places = []
    for x in ne("ne_10m_populated_places_simple", cache):
        p = x["properties"]
        if p.get("adm0_a3") == "USA":
            places.append({"name": p["name"], "state": p.get("adm1name"), "pop": p.get("pop_max") or 0,
                           "capital": p.get("featurecla") == "Admin-1 capital",
                           "pt": Point(x["geometry"]["coordinates"])})
    data = {"countries": countries, "country_names": country_names, "lakes": lakes, "rivers": rivers,
            "places": places, "names": names}

    from playwright.sync_api import sync_playwright
    OUT.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as pw:
        # CHROMIUM=/path/to/chrome when Playwright's own browser isn't installed.
        import os
        browser = pw.chromium.launch(executable_path=os.environ.get("CHROMIUM") or None)
        page = browser.new_page()
        for s in sj:
            code = s["code"]
            if args.only and code not in args.only:
                continue
            f, svg = draw_state(code, s["name"], geoms, data, cache)
            if args.svg:
                Path(args.svg).mkdir(parents=True, exist_ok=True)
                (Path(args.svg) / f"{code}.svg").write_text(svg, encoding="utf-8")
            page.set_viewport_size({"width": f.w, "height": f.h})
            page.set_content(f"<html><body style='margin:0'>{svg}</body></html>")
            page.wait_for_timeout(150)
            png = page.screenshot(clip={"x": 0, "y": 0, "width": f.w, "height": f.h})
            Image.open(io.BytesIO(png)).convert("RGB").save(OUT / f"{code}.webp", "WEBP", quality=82, method=6)
            # Outline (simplified a little) and the frame the image covers.
            # About half a map pixel: plenty for the apps, and keeps Alaska's file small.
            tol = (f.east - f.west) / f.w * 0.5
            g = geoms[code].simplify(tol, preserve_topology=True)
            outline = SPECIES / s["outline"]
            outline.write_text(json.dumps({
                "source": "Natural Earth 1:10m admin-1, Great Lakes cut out (public domain)",
                "frame": {"west": round(f.west, 4), "east": round(f.east, 4), "south": round(f.south, 4),
                          "north": round(f.north, 4), "width": f.w, "height": f.h},
                "rings": rings_of(g, (tol * 3) ** 2)}, separators=(",", ":")), encoding="utf-8")
            print(code, f"{f.w}x{f.h}", f"{(OUT / f'{code}.webp').stat().st_size // 1024} KB")
        browser.close()


if __name__ == "__main__":
    main()
