"""Pokédex entries: size, weight and fun fact (species/details.csv) plus where
each species has been seen in California (species/ranges.json, built by
ml/build_ranges.py). Both are optional; missing data just leaves fields empty.
"""

from __future__ import annotations

import csv
import json
from pathlib import Path

_details: dict[str, dict] = {}
_ranges: dict | None = None
_hotspots: list[dict] = []
# hotspots.json lists every species with >= 3 sightings at a park; only show the
# ones a visitor has a real chance of finding.
MIN_HOTSPOT_OBSERVATIONS = 20


def load(details_csv: Path, ranges_json: Path, hotspots_json: Path | None = None) -> None:
    global _ranges, _hotspots
    _details.clear()
    if details_csv.exists():
        with open(details_csv, newline="", encoding="utf-8") as fh:
            _details.update({row["slug"]: row for row in csv.DictReader(fh)})
    _ranges = json.loads(ranges_json.read_text(encoding="utf-8")) if ranges_json.exists() else None
    _hotspots = []
    if hotspots_json and hotspots_json.exists():
        _hotspots = json.loads(hotspots_json.read_text(encoding="utf-8"))["parks"]
        for p in _hotspots:
            p["species"] = [sp for sp in p["species"]
                            if sp["observations"] >= MIN_HOTSPOT_OBSERVATIONS]


def hotspots() -> list[dict]:
    return _hotspots


def hotspots_for(slug: str, limit: int = 3) -> list[str]:
    """Names of the parks with the most sightings of this species."""
    hits = [(sp["observations"], p["name"]) for p in _hotspots
            for sp in p["species"] if sp["slug"] == slug]
    return [name for _, name in sorted(hits, reverse=True)[:limit]]


def details(slug: str) -> dict:
    return _details.get(slug, {})


def range_for(slug: str) -> dict | None:
    if not _ranges or slug not in _ranges.get("species", {}):
        return None
    return {"grid": _ranges["grid"], "cells": _ranges["species"][slug]}
