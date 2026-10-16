"""Collection sets (species/sets.json) and weekly field challenges.

Sets are themed groups from a state's list, such as tide pools or state symbols.
Weekly challenges are three goals that everyone in a state shares each week
(Monday to Sunday, state time). They're picked from the week number, so they
need no storage, and they count captures and likes made during that week.
Nothing asks for a dangerous animal: sets leave out species rated danger, and
challenges only ask for kinds of animals, never a particular one.
"""

from __future__ import annotations

import json
import random
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path

from . import dex

MIN_SET_SIZE = 3
_sets: list[dict] = []


def load(path: Path) -> None:
    _sets.clear()
    if path.exists():
        _sets.extend(json.loads(path.read_text(encoding="utf-8"))["sets"])


@dataclass
class SetDef:
    id: str
    title: str
    description: str
    slugs: list[str]


def sets_for(state: str, members: set[str]) -> list[SetDef]:
    """The state's sets: listed animals in the state, minus dangerous ones."""
    out = []
    for s in _sets:
        slugs = s.get("species_by_state", {}).get(state, s.get("species", []))
        slugs = [x for x in slugs if x in members and dex.details(x, state).get("safety") != "danger"]
        if len(slugs) >= MIN_SET_SIZE:
            out.append(SetDef(s["id"], s["title"], s.get("description", ""), slugs))
    return out


# --- weekly challenges ---------------------------------------------------------

CATEGORY_PLURALS = {"mammal": "mammals", "bird": "birds", "reptile": "reptiles", "amphibian": "amphibians",
                    "invertebrate": "bugs, butterflies or spiders", "marine": "ocean animals", "fish": "fish"}


@dataclass
class Challenge:
    id: str
    title: str
    kind: str
    goal: int
    category: str | None = None
    set_id: str | None = None
    slugs: tuple[str, ...] = ()


def week_bounds(utc_offset: int, now: datetime | None = None) -> tuple[datetime, datetime]:
    """This week's Monday 00:00 to next Monday, in the state's time, as UTC."""
    now = now or datetime.now(timezone.utc)
    local = now + timedelta(hours=utc_offset)
    monday = (local - timedelta(days=local.weekday())).replace(hour=0, minute=0, second=0, microsecond=0)
    start = monday - timedelta(hours=utc_offset)
    return start, start + timedelta(days=7)


def challenges_for(state: str, week_start: datetime, categories: dict[str, int],
                   sets: list[SetDef]) -> list[Challenge]:
    """Three challenges for the week: a kind of animal, a collecting goal, and a
    set or social goal. The same for everyone in the state that week."""
    year, week, _ = (week_start + timedelta(days=1)).isocalendar()
    rng = random.Random(f"{state}-{year}-{week}")
    cats = sorted(c for c, n in categories.items() if n >= 8)
    out = []
    if cats:
        cat = rng.choice(cats)
        goal = 3 if categories[cat] >= 20 else 2
        out.append(Challenge(f"cat_{cat}", f"Capture {goal} different {CATEGORY_PLURALS.get(cat, cat)}",
                             "category", goal, category=cat))
    out.append(rng.choice([
        Challenge("distinct_5", "Capture 5 different animals", "distinct", 5),
        Challenge("new_1", "Add a new animal to your Field Guide", "new", 1),
        Challenge("uncommon_1", "Capture an uncommon, rare or legendary animal", "rarity", 1),
    ]))
    options = [Challenge(f"set_{s.id}", f"Capture an animal from {s.title}", "set", 1,
                         set_id=s.id, slugs=tuple(s.slugs)) for s in sets]
    options.append(Challenge("likes_3", "Like 3 photos by other players", "likes", 3))
    out.append(rng.choice(options))
    return out


@dataclass
class WeekCapture:
    slug: str
    category: str
    rarity: str
    new_badge: bool


def progress(ch: Challenge, captures: list[WeekCapture], likes_given: int) -> int:
    """How far along this week's captures and likes are."""
    if ch.kind == "likes":
        return likes_given
    if ch.kind == "new":
        return sum(c.new_badge for c in captures)
    kept = {c.slug for c in captures if
            (ch.kind == "category" and c.category == ch.category)
            or (ch.kind == "rarity" and c.rarity != "common")
            or (ch.kind == "set" and c.slug in ch.slugs)
            or ch.kind == "distinct"}
    return len(kept)
