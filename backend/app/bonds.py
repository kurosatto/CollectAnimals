"""Bonds: how well a player knows each animal they've captured.

Every captured species has up to six field notes, small observation goals met
by photographing it again in a new situation: on another day, at another time
of day, somewhere else, in another season, or in a 4-star photo. Each note is a
heart; the hearts are the bond.

Repeats only count when something is new, so a burst of photos in one sitting
ticks at most one note. Nothing asks for a closer photo: "Great shot" uses the
photo score, which never rewards getting close (see scoring.py).

Animals with a safety rating (caution or danger, from details.csv) only get the
notes that don't send a player back to them: "First meeting" and "Great shot".
No repeat visits, no night outings, no tracking one down somewhere else.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

DAYS_GOAL = 3
TIMES_GOAL = 2
PLACES_GOAL = 2
SEASONS_GOAL = 2
PLACE_KM = 1.0
# The "Great shot" note: a photo with at least this many stars (of 5).
GREAT_SHOT_STARS = 4

TITLES = ["Met", "Familiar", "Regular", "Friend", "Good friend", "Lifelong friend"]

# (id, title, how it's ticked)
NOTES = [
    ("first", "First meeting", "Capture it once"),
    ("days", "Regular visitor", f"Photograph it on {DAYS_GOAL} different days"),
    ("times", "Early and late", f"Photograph it at {TIMES_GOAL} times of day (morning, midday, evening, night)"),
    ("places", "New ground", f"Photograph it in {PLACES_GOAL} places at least {PLACE_KM:g} km apart"),
    ("seasons", "Through the seasons", f"Photograph it in {SEASONS_GOAL} different seasons"),
    ("star", "Great shot", f"Take a {GREAT_SHOT_STARS}-star photo of it"),
]
NOTE_TITLES = {n[0]: n[1] for n in NOTES}
# The notes for animals with a safety rating.
SAFE_NOTES = {"first", "star"}
SAFE_TIP = "Watch from far away with zoom, and stay with an adult."
GOALS = {"first": 1, "days": DAYS_GOAL, "times": TIMES_GOAL, "places": PLACES_GOAL,
         "seasons": SEASONS_GOAL, "star": 1}


@dataclass
class Sighting:
    """One capture of the species: when (local time in the player's state),
    where (if known) and its stars."""
    local: datetime
    lat: float | None = None
    lon: float | None = None
    stars: int | None = None


@dataclass
class Note:
    id: str
    title: str
    hint: str
    progress: int
    goal: int

    @property
    def done(self) -> bool:
        return self.progress >= self.goal


def local_time(taken_at: datetime | None, created_at: datetime, utc_offset: int) -> datetime:
    """The photo's local wall time. EXIF times are already local (camera clock);
    otherwise use the upload time shifted to the state's time."""
    if taken_at is not None:
        return taken_at.replace(tzinfo=None)
    c = created_at if created_at.tzinfo else created_at.replace(tzinfo=timezone.utc)
    return (c.astimezone(timezone.utc) + timedelta(hours=utc_offset)).replace(tzinfo=None)


def time_of_day(t: datetime) -> str:
    h = t.hour
    if 5 <= h < 11:
        return "morning"
    if 11 <= h < 16:
        return "midday"
    if 16 <= h < 20:
        return "evening"
    return "night"


def season(t: datetime) -> str:
    return ("winter", "winter", "spring", "spring", "spring", "summer", "summer", "summer",
            "fall", "fall", "fall", "winter")[t.month - 1]


def km(a: tuple[float, float], b: tuple[float, float]) -> float:
    la1, lo1, la2, lo2 = map(math.radians, (*a, *b))
    h = math.sin((la2 - la1) / 2) ** 2 + math.cos(la1) * math.cos(la2) * math.sin((lo2 - lo1) / 2) ** 2
    return 12742 * math.asin(math.sqrt(h))


def _places(sightings: list[Sighting]) -> int:
    """How many spots at least PLACE_KM apart (greedy, enough for small goals)."""
    spots: list[tuple[float, float]] = []
    for s in sightings:
        if s.lat is None or s.lon is None:
            continue
        p = (s.lat, s.lon)
        if all(km(p, q) >= PLACE_KM for q in spots):
            spots.append(p)
    return len(spots)


def careful(safety: str | None) -> bool:
    """Whether the animal has a safety rating (caution or danger)."""
    return safety in ("caution", "danger")


def notes(sightings: list[Sighting], safety: str | None = "none") -> list[Note]:
    """The field notes for one species, from the player's captures of it: all
    six, or just the safe ones for an animal with a safety rating."""
    progress = {
        "first": 1 if sightings else 0,
        "days": len({s.local.date() for s in sightings}),
        "times": len({time_of_day(s.local) for s in sightings}),
        "places": _places(sightings),
        "seasons": len({season(s.local) for s in sightings}),
        "star": 1 if any((s.stars or 0) >= GREAT_SHOT_STARS for s in sightings) else 0,
    }
    keep = SAFE_NOTES if careful(safety) else set(GOALS)
    return [Note(i, title, f"{hint}. {SAFE_TIP}" if careful(safety) and i == "star" else hint,
                 min(progress[i], GOALS[i]), GOALS[i]) for i, title, hint in NOTES if i in keep]


def level(ns: list[Note]) -> int:
    return sum(n.done for n in ns)


def title(lvl: int) -> str | None:
    return TITLES[lvl - 1] if lvl > 0 else None


def newly_done(before: list[Sighting], after: list[Sighting], safety: str | None = "none") -> list[str]:
    """Titles of the notes the latest capture ticked."""
    was = {n.id for n in notes(before, safety) if n.done}
    return [n.title for n in notes(after, safety) if n.done and n.id not in was and n.id != "first"]
