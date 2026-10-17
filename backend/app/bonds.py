"""Bonds: how well a player knows each animal they've captured.

Every captured species has up to six field notes, small observation goals met
by photographing it again in a new situation: on another day, at another time
of day, somewhere else, in another season, or in a 4-star photo. Each note is a
heart; the hearts are the bond.

Repeats only count when something is new, so a burst of photos in one sitting
ticks at most one note. Nothing asks for a closer photo: "Great shot" uses the
photo score, which never rewards getting close (see scoring.py).

The buddy is one captured animal the player picks to keep them company. Its
mood comes from recent outings and never drops below napping: no hunger, no
guilt.
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


def notes(sightings: list[Sighting]) -> list[Note]:
    """The six field notes for one species, from the player's captures of it."""
    progress = {
        "first": 1 if sightings else 0,
        "days": len({s.local.date() for s in sightings}),
        "times": len({time_of_day(s.local) for s in sightings}),
        "places": _places(sightings),
        "seasons": len({season(s.local) for s in sightings}),
        "star": 1 if any((s.stars or 0) >= GREAT_SHOT_STARS for s in sightings) else 0,
    }
    return [Note(i, title, hint, min(progress[i], GOALS[i]), GOALS[i]) for i, title, hint in NOTES]


def level(ns: list[Note]) -> int:
    return sum(n.done for n in ns)


def title(lvl: int) -> str | None:
    return TITLES[lvl - 1] if lvl > 0 else None


def newly_done(before: list[Sighting], after: list[Sighting]) -> list[str]:
    """Titles of the notes the latest capture ticked."""
    was = {n.id for n in notes(before) if n.done}
    return [n.title for n in notes(after) if n.done and n.id not in was and n.id != "first"]


# --- buddy ----------------------------------------------------------------------

def mood(outing_days: int) -> str:
    """From the number of days with a capture in the last 7."""
    return "napping" if outing_days == 0 else "happy" if outing_days < 3 else "excited"


def buddy_line(mood_: str, ns: list[Note], suggestion: str | None = None) -> str:
    """What the buddy says: a nudge towards its next field note, or another
    animal to look for once its own notes are done."""
    if mood_ == "napping":
        opener = "Zzz... oh, hi! Take me outside sometime?"
    elif mood_ == "excited":
        opener = "What a week of outings!"
    else:
        opener = "That was a nice outing."
    todo = next((n for n in ns if not n.done), None)
    if todo is None:
        if suggestion:
            return f"{opener} We're lifelong friends now. Have you met {suggestion} yet? It's around this month."
        return f"{opener} We're lifelong friends now."
    ask = {
        "days": f"Come find me on another day: {todo.progress} of {todo.goal} days so far.",
        "times": "I'd love a photo of me at a different time of day.",
        "places": "Let's look for me somewhere new, at least a kilometer away.",
        "seasons": "Visit me again in another season.",
        "star": f"Try for a {GREAT_SHOT_STARS}-star photo of me. Steady hands, good light.",
        "first": "Let's go outside!",
    }[todo.id]
    return f"{opener} {ask}"
