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


def load(details_csv: Path, ranges_json: Path) -> None:
    global _ranges
    _details.clear()
    if details_csv.exists():
        with open(details_csv, newline="", encoding="utf-8") as fh:
            _details.update({row["slug"]: row for row in csv.DictReader(fh)})
    _ranges = json.loads(ranges_json.read_text(encoding="utf-8")) if ranges_json.exists() else None


def details(slug: str) -> dict:
    return _details.get(slug, {})


def range_for(slug: str) -> dict | None:
    if not _ranges or slug not in _ranges.get("species", {}):
        return None
    return {"grid": _ranges["grid"], "cells": _ranges["species"][slug]}
