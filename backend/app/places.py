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

from . import dex

# Per state: (name, bounds, towns, regions). A point only gets names from the
# state it falls in, so a North Carolina photo never reads "in the California deserts".
_states: list[tuple[str, dict, list, list]] = []
# How far outside a state's bounding box still counts as that state (degrees).
_MARGIN = 0.3


def load(states) -> None:
    _states.clear()
    for st in states:
        towns, regions = [], []
        if st.places and st.places.exists():
            data = json.loads(st.places.read_text(encoding="utf-8"))
            towns = [tuple(t) for t in data.get("towns", [])]
            regions = [tuple(r) for r in data.get("regions", [])]
        _states.append((st.name, st.bounds, towns, regions))


def _km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp, dl = p2 - p1, math.radians(lon2 - lon1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 6371 * 2 * math.asin(math.sqrt(a))


def _nearest(items, lat, lon):
    return min(((_km(lat, lon, la, lo), name) for name, la, lo in items), default=(math.inf, None))


def _state_at(lat: float, lon: float):
    """The state whose bounds hold the point; the one with the nearer town if two do."""
    inside = [s for s in _states
              if s[1]["south"] - _MARGIN <= lat <= s[1]["north"] + _MARGIN
              and s[1]["west"] - _MARGIN <= lon <= s[1]["east"] + _MARGIN]
    return min(inside, key=lambda s: _nearest(s[2] + s[3], lat, lon)[0], default=None)


def region(lat: float, lon: float) -> str:
    state = _state_at(lat, lon)
    if state is None:
        return "another state"
    return _nearest(state[3], lat, lon)[1] or state[0]


def park(lat: float, lon: float) -> str | None:
    for p in dex.all_hotspots():
        if _km(lat, lon, p["lat"], p["lon"]) <= p.get("radius_km", 5):
            return p["name"]
    return None


def place_name(lat: float, lon: float, town_km: float = 25, prefix: str = "near") -> str:
    """A hotspot park if the point is inside one, else the nearest town, else the region."""
    name = park(lat, lon)
    if name:
        return name
    state = _state_at(lat, lon)
    dist, town = _nearest(state[2], lat, lon) if state else (math.inf, None)
    return f"{prefix} {town}" if town and dist <= town_km else f"in {region(lat, lon)}"


# Smallest radius for the "near me" feed, so it can't be narrowed down to a house.
MIN_RADIUS_KM = 10


def blurred_point(lat: float, lon: float, rarity: str) -> tuple[float, float]:
    """The position used for distance filters: a ~10 km grid for most animals,
    a ~50 km grid for rare and legendary ones."""
    step = 0.5 if rarity in ("rare", "legendary") else 0.1
    return round(lat / step) * step, round(lon / step) * step


def blurred_distance_km(lat, lon, rarity: str, from_lat: float, from_lon: float) -> float:
    if lat is None or lon is None:
        return math.inf
    return _km(*blurred_point(lat, lon, rarity), from_lat, from_lon)


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
