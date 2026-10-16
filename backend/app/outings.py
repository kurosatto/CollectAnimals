"""Outing days and the seasons.

Outing days: a day with at least one capture is an outing. The weekly goal is a
few outing days, not a daily streak, so a busy day costs nothing.

Seasons: animals arriving this month (in season now but not last month, from
real sightings) and seasonal events (species/events.json), short windows such as
Spring Migration where capturing the event's animals fills an event ribbon.
Events are computed from dates and captures, so they need no storage, and they
never include an animal rated danger.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path

from . import dex

OUTING_GOAL = 3
EVENT_GOAL = 3
_events: list[dict] = []


def load(path: Path) -> None:
    _events.clear()
    if path.exists():
        _events.extend(json.loads(path.read_text(encoding="utf-8"))["events"])


@dataclass
class Event:
    id: str
    title: str
    description: str
    start: date
    end: date  # inclusive
    slugs: list[str] = field(default_factory=list)

    @property
    def goal(self) -> int:
        return min(EVENT_GOAL, len(self.slugs))


def _md(s: str) -> tuple[int, int]:
    m, d = s.split("-")
    return int(m), int(d)


def _window(today: date, start: str, end: str) -> tuple[date, date] | None:
    """This year's (or the one wrapping the new year) window holding today."""
    (sm, sd), (em, ed) = _md(start), _md(end)
    for year in (today.year - 1, today.year):
        a = date(year, sm, sd)
        b = date(year + ((em, ed) < (sm, sd)), em, min(ed, 28) if em == 2 else ed)
        if a <= today <= b:
            return a, b
    return None


def events_for(state: str, members: dict[str, str], today: date) -> list[Event]:
    """Events running in the state today. `members` maps the state's slugs to categories."""
    out = []
    for e in _events:
        if e.get("states") and state not in e["states"]:
            continue
        win = _window(today, e["start"], e["end"])
        if not win:
            continue
        rx = re.compile(e["match"]) if e.get("match") else None
        cats = set(e.get("categories", []))
        slugs = [s for s, cat in members.items()
                 if (cat in cats or (rx and rx.search(s))) and dex.details(s, state).get("safety") != "danger"]
        if slugs:
            out.append(Event(e["id"], e["title"], e.get("description", ""), win[0], win[1], slugs))
    return out


def event_progress(ev: Event, captures: list[tuple[str, date]]) -> int:
    """Different event animals captured during the event (slug, local date)."""
    return len({s for s, d in captures if s in ev.slugs and ev.start <= d <= ev.end})


def arrivals(state: str, slugs: list[str], month: int) -> list[str]:
    """Animals in season this month that weren't last month."""
    prev = 12 if month == 1 else month - 1
    return [s for s in slugs if dex.season_for(s, state)
            and dex.in_season(s, state, month) and not dex.in_season(s, state, prev)
            and dex.details(s, state).get("safety") != "danger"]
