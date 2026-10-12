"""Turn a catch's GPS point into what other players may see.

Other players never get exact coordinates of someone else's catch. They get a
place name (a hotspot park, "near <town>", or a region) and, for common
animals, coordinates rounded to about 10 km. Rarer animals are blurred more,
both to protect the animals and so a rare find doesn't pinpoint anyone.

| Viewer          | common / uncommon            | rare                          | legendary   |
|-----------------|------------------------------|-------------------------------|-------------|
| you             | exact (~100 m) + place       | exact + place                 | exact + place |
| your friends    | ~100 m + place               | park or "around <town>"       | region only |
| everyone else   | ~10 km + place               | park or "around <town>"       | region only |
"""

from __future__ import annotations

import json
import math
from dataclasses import dataclass
from pathlib import Path

from . import dex

_towns: list[tuple[str, float, float]] = []
_regions: list[tuple[str, float, float]] = []


def load(path: Path) -> None:
    _towns.clear()
    _regions.clear()
    if path.exists():
        data = json.loads(path.read_text(encoding="utf-8"))
        _towns.extend(tuple(t) for t in data.get("towns", []))
        _regions.extend(tuple(r) for r in data.get("regions", []))


def _km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp, dl = p2 - p1, math.radians(lon2 - lon1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 6371 * 2 * math.asin(math.sqrt(a))


def _nearest(items, lat, lon):
    return min(((_km(lat, lon, la, lo), name) for name, la, lo in items), default=(math.inf, None))


def region(lat: float, lon: float) -> str:
    return _nearest(_regions, lat, lon)[1] or "California"


def park(lat: float, lon: float) -> str | None:
    for p in dex.hotspots():
        if _km(lat, lon, p["lat"], p["lon"]) <= p.get("radius_km", 5):
            return p["name"]
    return None


def place_name(lat: float, lon: float, town_km: float = 25, prefix: str = "near") -> str:
    """A hotspot park if the point is inside one, else the nearest town, else the region."""
    name = park(lat, lon)
    if name:
        return name
    dist, town = _nearest(_towns, lat, lon)
    return f"{prefix} {town}" if town and dist <= town_km else f"in {region(lat, lon)}"


@dataclass
class Location:
    latitude: float | None = None
    longitude: float | None = None
    precise: bool = False
    place: str | None = None


def for_viewer(lat: float | None, lon: float | None, rarity: str, mine: bool, friend: bool) -> Location:
    if lat is None or lon is None:
        return Location()
    if mine:
        return Location(round(lat, 3), round(lon, 3), True, place_name(lat, lon))
    if rarity == "legendary":
        return Location(place=f"somewhere in {region(lat, lon)}")
    if rarity == "rare":
        return Location(place=place_name(lat, lon, town_km=40, prefix="around"))
    if friend:
        return Location(round(lat, 3), round(lon, 3), True, place_name(lat, lon))
    return Location(round(lat, 1), round(lon, 1), False, place_name(lat, lon))
