"""Pokédex entries: size, weight and fun fact (species/details.csv, shared by
all states) plus, per state, where each species has been seen (ranges), the
parks it shows up at (hotspots) and state-specific text (the state's dex CSV:
where_to_find, and overrides of shared facts that only make sense
in another state). All files are optional; missing data just leaves fields empty.
"""

from __future__ import annotations

import csv
import json
import re
from pathlib import Path

from .states import State

_details: dict[str, dict] = {}
# More fun facts per species (species/facts.json, true in every state), told
# after the main one when you tap an animal in your habitat.
_facts: dict[str, list[str]] = {}
# state code -> data
_ranges: dict[str, dict] = {}
_hotspots: dict[str, list[dict]] = {}
_state_text: dict[str, dict[str, dict]] = {}
_seasons: dict[str, dict[str, dict]] = {}
_avg_night_share: dict[str, float] = {}
# Hours counted as "night" for the day/night hint (local time of the sighting).
NIGHT_HOURS = set(range(0, 6)) | {20, 21, 22, 23}
# The state whose where_to_find text lives in details.csv (the original list).
_base_state: str | None = None
# hotspots.json lists every species with >= 3 sightings at a park; only show the
# ones a visitor has a real chance of finding.
MIN_HOTSPOT_OBSERVATIONS = 20
STATE_FIELDS = ("where_to_find", "fun_fact", "active_time", "spotting_tip",
                "safety", "safe_distance", "safety_note")


def _read_csv(path: Path) -> dict[str, dict]:
    with open(path, newline="", encoding="utf-8") as fh:
        return {row["slug"]: row for row in csv.DictReader(fh)}


def load(details_csv: Path, states: list[State]) -> None:
    global _base_state
    _details.clear()
    _ranges.clear()
    _hotspots.clear()
    _state_text.clear()
    _seasons.clear()
    _avg_night_share.clear()
    _facts.clear()
    if details_csv.exists():
        _details.update(_read_csv(details_csv))
    facts_json = details_csv.parent / "facts.json"
    if facts_json.exists():
        _facts.update(json.loads(facts_json.read_text(encoding="utf-8")))
    _base_state = next((s.code for s in states if s.dex_csv is None), None)
    for st in states:
        if st.ranges and st.ranges.exists():
            _ranges[st.code] = json.loads(st.ranges.read_text(encoding="utf-8"))
        parks = []
        if st.hotspots and st.hotspots.exists():
            parks = json.loads(st.hotspots.read_text(encoding="utf-8"))["parks"]
            for p in parks:
                p["species"] = [sp for sp in p["species"]
                                if sp["observations"] >= MIN_HOTSPOT_OBSERVATIONS]
        _hotspots[st.code] = parks
        if st.dex_csv and st.dex_csv.exists():
            _state_text[st.code] = _read_csv(st.dex_csv)
        if st.seasons and st.seasons.exists():
            seasons = json.loads(st.seasons.read_text(encoding="utf-8"))["species"]
            _seasons[st.code] = seasons
            shares = [s for s in map(_night_share, seasons.values()) if s is not None]
            if shares:
                _avg_night_share[st.code] = sum(shares) / len(shares)


def _night_share(entry: dict) -> float | None:
    hours = entry.get("hours") or []
    total = sum(hours)
    return sum(hours[h] for h in NIGHT_HOURS if h < len(hours)) / total if total >= 30 else None


def facts_for(slug: str, state: str) -> list[str]:
    """The species' fun facts: the state's main one first, then the shared extras."""
    main = details(slug, state).get("fun_fact")
    return [f for f in [main, *_facts.get(slug, [])] if f]


def season_for(slug: str, state: str) -> dict | None:
    """Sightings per month and hour in this state, plus night_ratio: how much more
    often than the state's average listed species it's reported at night (people
    mostly look by day, so raw counts would call everything a daytime animal)."""
    entry = _seasons.get(state, {}).get(slug)
    if not entry:
        return None
    share, avg = _night_share(entry), _avg_night_share.get(state)
    ratio = round(share / avg, 2) if share is not None and avg else None
    return {"months": entry["months"], "hours": entry["hours"], "night_ratio": ratio}


# A month counts as "maybe visible" when it has at least this share of the
# species' best month's sightings.
IN_SEASON_SHARE = 0.25


def in_season(slug: str, state: str, month: int) -> bool:
    """Could the species turn up in this state this month (1-12)? True without
    season data, since nothing rules it out."""
    entry = _seasons.get(state, {}).get(slug)
    months = entry["months"] if entry else None
    if not months or not max(months):
        return True
    return months[month - 1] >= IN_SEASON_SHARE * max(months)


def activity(slug: str, state: str) -> str:
    """When the animal is up and about: "day", "night" or "any" (dawn/dusk
    animals and ones out day and night). From the entry's active_time text,
    else from how often it's reported at night. Used by the Habitat scene."""
    text = details(slug, state).get("active_time", "").lower().split(";")[0]
    if text:
        if text.startswith(("night", "dusk")):
            return "night"
        if any(w in text for w in ("night", "dawn", "dusk", "all day", "any time")):
            return "any"
        return "day"
    season = season_for(slug, state)
    ratio = season and season["night_ratio"]
    return "night" if ratio and ratio >= 3 else "day"


def hotspots(state: str) -> list[dict]:
    return _hotspots.get(state, [])


def all_hotspots() -> list[dict]:
    """Every state's parks, for naming where a photo was taken."""
    return [p for parks in _hotspots.values() for p in parks]


def hotspots_for(slug: str, state: str, limit: int = 3) -> list[str]:
    """Names of the state's parks with the most sightings of this species."""
    hits = [(sp["observations"], p["name"]) for p in hotspots(state)
            for sp in p["species"] if sp["slug"] == slug]
    return [name for _, name in sorted(hits, reverse=True)[:limit]]


def details(slug: str, state: str) -> dict:
    """Shared facts with the state's own text laid over them."""
    d = dict(_details.get(slug, {}))
    if state != _base_state:
        d["where_to_find"] = ""  # details.csv's where_to_find is about the base state
    for k, v in _state_text.get(state, {}).get(slug, {}).items():
        if k in STATE_FIELDS and v:
            d[k] = v
    return d


def range_for(slug: str, state: str) -> dict | None:
    r = _ranges.get(state)
    if not r or slug not in r.get("species", {}):
        return None
    return {"grid": r["grid"], "cells": r["species"][slug]}



def mask_name(text: str | None, common_name: str, scientific_name: str = "") -> str | None:
    """Hide which animal a tip is about while its name isn't revealed: the common
    name, its shorter endings ("Black Bear", "Bear") and the scientific name
    become "???", the same mark the Field Guide uses for hidden names."""
    if not text:
        return text
    words = common_name.replace("-", " ").split()
    names = {common_name, scientific_name, *(" ".join(words[i:]) for i in range(len(words)))}
    alts = "|".join(re.escape(n).replace(r"\ ", r"[\s-]+") for n in sorted(filter(None, names), key=len, reverse=True))
    return re.sub(rf"\b(?:{alts})(?:e?s)?\b", "???", text, flags=re.IGNORECASE)
