"""Playable states, from species/states.json.

Each state has its own 100-species list (a CSV in species/) and its own map
data: outline, sighting grid (ranges) and park hotspots. A species that lives
in several states (coyote, mallard, ...) keeps one slug, so a badge earned in
one state counts in every state that lists it.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class State:
    code: str
    name: str
    species_csv: Path
    # Per-state Dex text (where_to_find, overrides of the shared facts, caution).
    dex_csv: Path | None
    outline: Path
    ranges: Path
    hotspots: Path
    bounds: dict
    # Sightings by month and hour (ml/build_seasons.py); optional.
    seasons: Path | None = None
    # Hours from UTC (standard time), for "this month" in the state.
    utc_offset: int = 0


_states: dict[str, State] = {}
default_code = "CA"


def load(states_json: Path) -> None:
    global default_code
    data = json.loads(states_json.read_text(encoding="utf-8"))
    root = states_json.parent
    _states.clear()
    for s in data["states"]:
        _states[s["code"]] = State(
            code=s["code"], name=s["name"], species_csv=root / s["species"],
            dex_csv=root / s["dex"] if s.get("dex") else None,
            outline=root / s["outline"], ranges=root / s["ranges"], hotspots=root / s["hotspots"],
            bounds=s["bounds"], seasons=root / s["seasons"] if s.get("seasons") else None,
            utc_offset=s.get("utc_offset", 0))
    default_code = data.get("default", next(iter(_states)))


def all_states() -> list[State]:
    return list(_states.values())


def get(code: str | None) -> State | None:
    return _states.get((code or default_code).upper())
