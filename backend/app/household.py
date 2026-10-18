"""Pets and pests: animals the model can recognise that aren't wild animals for the
Field Guide (a dog, a cat, a pigeon, a cockroach...).

People often photograph their pets. Instead of "we couldn't match this", the
capture screen says what it is, kindly, and that it doesn't count. The list is
species/household.csv; ml/fetch_inat.py downloads training photos for it and keeps
these animals out of the "other" class.
"""

from __future__ import annotations

import csv
from dataclasses import dataclass
from functools import lru_cache

from .config import settings


@dataclass(frozen=True)
class HouseholdAnimal:
    slug: str
    common_name: str
    scientific_name: str
    kind: str  # "pet" or "pest"
    note: str


@lru_cache
def animals() -> dict[str, HouseholdAnimal]:
    path = settings.states_json.parent / "household.csv"
    if not path.is_file():
        return {}
    with open(path, newline="", encoding="utf-8") as fh:
        return {r["slug"]: HouseholdAnimal(r["slug"], r["common_name"], r["scientific_name"], r["kind"], r["note"])
                for r in csv.DictReader(fh)}


_PROPER = {"european": "European", "german": "German", "american": "American"}


def _in_sentence(name: str) -> str:
    """'House sparrow' -> 'house sparrow', keeping words like 'European' capitalised."""
    return " ".join(_PROPER.get(w, w) for w in name.lower().split())


def message(a: HouseholdAnimal) -> str:
    """What the capture screen says for a pet or a pest."""
    name = _in_sentence(a.common_name)
    if a.kind == "pet":
        return f"That's a {name}! Pets aren't wild animals, so they don't go in the Field Guide. {a.note}"
    return f"That's a {name}. It's a pest, not one of the wild animals in the Field Guide. {a.note}"
