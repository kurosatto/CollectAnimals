"""Field card duels: a quick card game against a friend (or a bot) using the
animals each of you has captured.

Every captured animal is a card with four stats from 1 to 99: Size, Weight
(both from the Field Guide entry), Rarity, and Photo (your best photo score of
it). A duel is five rounds. Each round you see your card, pick the stat you
think wins, and then see the card drawn from your opponent's collection. The
opponent doesn't have to be online: their cards come from their collection.
It's all cards, so nothing asks anyone to go near a real animal.
"""

from __future__ import annotations

import json
import math
import random
import re
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, func, or_, select
from sqlalchemy.orm import Mapped, Session, mapped_column

from . import dex
from .auth import current_user
from .db import Base, get_db
from .models import Badge, Capture, StateSpecies, User
from .schemas import SpeciesOut
from .social import _user_by_name, friend_ids, species_out

router = APIRouter()

ROUNDS = 5
STATS = ("size", "weight", "rarity", "photo")
RARITY_STAT = {"common": 20, "uncommon": 45, "rare": 70, "legendary": 95}
# Size and weight on a log scale: 1 cm / 0.5 g score low, a humpback whale 99.
SIZE_RANGE_CM = (1.0, 1500.0)
WEIGHT_RANGE_G = (0.5, 30_000_000.0)
TO_CM = {"mm": 0.1, "cm": 1, "m": 100, "in": 2.54, "ft": 30.48}
TO_G = {"g": 1, "gram": 1, "grams": 1, "kg": 1000, "oz": 28.35, "lb": 453.6, "lbs": 453.6,
        "ton": 907_185, "tons": 907_185, "t": 1_000_000}


class Duel(Base):
    __tablename__ = "duels"

    id: Mapped[int] = mapped_column(primary_key=True)
    challenger_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    opponent_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    # State list the cards come from (the challenger's state).
    state: Mapped[str] = mapped_column(String(2))
    # JSON lists of species ids, one per round, and the stat picked each round.
    challenger_cards: Mapped[str] = mapped_column(Text)
    opponent_cards: Mapped[str] = mapped_column(Text)
    picks: Mapped[str] = mapped_column(Text, default="[]")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True),
                                                 default=lambda: datetime.now(timezone.utc))
    finished: Mapped[bool] = mapped_column(default=False)
    winner_id: Mapped[int | None] = mapped_column(Integer, nullable=True)


# --- card stats -----------------------------------------------------------------

def _first_amount(text: str, units: dict[str, float]) -> float | None:
    """The first amount in a Field Guide string, e.g. '2.5–3.5 ft long' -> the middle of the range."""
    t = (text or "").lower().replace(",", "")
    if "few grams" in t:
        return 3.0
    if "under 1 gram" in t:
        return 0.5
    m = re.search(r"([\d.]+)(?:\s*[–-]\s*([\d.]+))?\s*(" + "|".join(sorted(units, key=len, reverse=True))
                  + r")\b", t)
    if not m:
        return None
    lo = float(m.group(1))
    hi = float(m.group(2)) if m.group(2) else lo
    return (lo + hi) / 2 * units[m.group(3)]


def _log_stat(value: float | None, lo: float, hi: float) -> int:
    if not value or value <= 0:
        return 50
    k = (math.log10(value) - math.log10(lo)) / (math.log10(hi) - math.log10(lo))
    return max(1, min(99, round(1 + 98 * k)))


def card_stats(slug: str, rarity: str, state: str, best_score: int | None) -> dict[str, int]:
    d = dex.details(slug, state)
    return {
        "size": _log_stat(_first_amount(d.get("size", ""), TO_CM), *SIZE_RANGE_CM),
        "weight": _log_stat(_first_amount(d.get("weight", ""), TO_G), *WEIGHT_RANGE_G),
        "rarity": RARITY_STAT.get(rarity, 20),
        # Photo scores run to about 1,500 with bonuses; old photos without a score get 40.
        "photo": max(1, min(99, round(best_score / 15))) if best_score is not None else 40,
    }


# --- API --------------------------------------------------------------------------

class DuelStart(BaseModel):
    opponent: str


class CardOut(BaseModel):
    species: SpeciesOut
    stats: dict[str, int]


class RoundOut(BaseModel):
    mine: CardOut
    theirs: CardOut
    stat: str
    # "win", "lose" or "tie", from the viewer's side.
    result: str


class DuelOut(BaseModel):
    id: int
    opponent: str
    you_started: bool
    rounds: list[RoundOut]
    # The viewer's card for the next round (challenger only, while the duel is on).
    next_card: CardOut | None = None
    round: int
    total_rounds: int = ROUNDS
    your_points: int
    their_points: int
    finished: bool
    # "win", "lose" or "tie" once finished.
    outcome: str | None = None
    created_at: datetime


class DuelListOut(BaseModel):
    duels: list[DuelOut]
    wins: int
    played: int


class PlayIn(BaseModel):
    stat: str


def _deck(db: Session, user: User, state: str) -> list[int]:
    """Species ids the player has captured that are on this state's list."""
    on_list = select(StateSpecies.species_id).where(StateSpecies.state == state)
    return list(db.scalars(select(Badge.species_id).where(Badge.user_id == user.id,
                                                         Badge.species_id.in_(on_list))))


def _draw(deck: list[int], rng: random.Random) -> list[int]:
    if len(deck) >= ROUNDS:
        return rng.sample(deck, ROUNDS)
    return [rng.choice(deck) for _ in range(ROUNDS)]


def _card(db: Session, owner_id: int, species_id: int, state: str) -> CardOut:
    m = db.scalar(select(StateSpecies).where(StateSpecies.state == state, StateSpecies.species_id == species_id))
    best = db.scalar(select(func.max(Capture.score)).where(Capture.user_id == owner_id,
                                                          Capture.species_id == species_id))
    return CardOut(species=species_out(m.species, True, m),
                   stats=card_stats(m.species.slug, m.rarity, state, best))


def _result(mine: int, theirs: int) -> str:
    return "win" if mine > theirs else "lose" if mine < theirs else "tie"


def _flip(r: str) -> str:
    return {"win": "lose", "lose": "win"}.get(r, r)


def duel_out(db: Session, d: Duel, viewer: User) -> DuelOut:
    challenger = viewer.id == d.challenger_id
    mine_ids = json.loads(d.challenger_cards if challenger else d.opponent_cards)
    theirs_ids = json.loads(d.opponent_cards if challenger else d.challenger_cards)
    mine_owner, theirs_owner = (d.challenger_id, d.opponent_id) if challenger else (d.opponent_id, d.challenger_id)
    picks = json.loads(d.picks)
    rounds = []
    for i, stat in enumerate(picks):
        a = _card(db, mine_owner, mine_ids[i], d.state)
        b = _card(db, theirs_owner, theirs_ids[i], d.state)
        rounds.append(RoundOut(mine=a, theirs=b, stat=stat, result=_result(a.stats[stat], b.stats[stat])))
    you = sum(r.result == "win" for r in rounds)
    them = sum(r.result == "lose" for r in rounds)
    finished = len(picks) >= ROUNDS
    other = db.get(User, theirs_owner)
    return DuelOut(
        id=d.id, opponent=other.username if other else "?", you_started=challenger, rounds=rounds,
        next_card=(_card(db, mine_owner, mine_ids[len(picks)], d.state)
                   if challenger and not finished else None),
        round=len(picks), your_points=you, their_points=them, finished=finished,
        outcome=_result(you, them) if finished else None, created_at=d.created_at)


@router.post("/duels", response_model=DuelOut, status_code=201)
def start_duel(body: DuelStart, user: User = Depends(current_user), db: Session = Depends(get_db)):
    """Challenge a friend (bots included). Both of you need at least one captured
    animal on your state's list."""
    other = _user_by_name(db, body.opponent)
    if other.id == user.id or other.id not in friend_ids(db, user.id):
        raise HTTPException(400, "You can only duel your friends")
    mine, theirs = _deck(db, user, user.state), _deck(db, other, user.state)
    if not mine:
        raise HTTPException(400, "Capture an animal first: your captures are your cards")
    if not theirs:
        raise HTTPException(400, f"{other.username} hasn't captured any animals on your state's list yet")
    rng = random.Random()
    d = Duel(challenger_id=user.id, opponent_id=other.id, state=user.state,
             challenger_cards=json.dumps(_draw(mine, rng)), opponent_cards=json.dumps(_draw(theirs, rng)),
             picks="[]")
    db.add(d)
    db.commit()
    return duel_out(db, d, user)


def _my_duel(db: Session, duel_id: int, user: User) -> Duel:
    d = db.get(Duel, duel_id)
    if d is None or user.id not in (d.challenger_id, d.opponent_id):
        raise HTTPException(404, "Duel not found")
    return d


@router.get("/duels/{duel_id}", response_model=DuelOut)
def get_duel(duel_id: int, user: User = Depends(current_user), db: Session = Depends(get_db)):
    return duel_out(db, _my_duel(db, duel_id, user), user)


@router.post("/duels/{duel_id}/play", response_model=DuelOut)
def play_round(duel_id: int, body: PlayIn, user: User = Depends(current_user), db: Session = Depends(get_db)):
    """Pick the stat for this round; the opponent's card is revealed."""
    d = _my_duel(db, duel_id, user)
    if user.id != d.challenger_id:
        raise HTTPException(403, "Only the player who started the duel picks the stats")
    if body.stat not in STATS:
        raise HTTPException(400, f"Pick one of: {', '.join(STATS)}")
    picks = json.loads(d.picks)
    if len(picks) >= ROUNDS:
        raise HTTPException(400, "This duel is over")
    d.picks = json.dumps(picks + [body.stat])
    out = duel_out(db, d, user)
    if out.finished:
        d.finished = True
        d.winner_id = (user.id if out.outcome == "win" else d.opponent_id if out.outcome == "lose" else None)
    db.commit()
    return duel_out(db, d, user)


@router.get("/duels", response_model=DuelListOut)
def my_duels(user: User = Depends(current_user), db: Session = Depends(get_db)):
    """Recent duels you started or were challenged to, and your win count."""
    mine = or_(Duel.challenger_id == user.id, Duel.opponent_id == user.id)
    recent = db.scalars(select(Duel).where(mine).order_by(Duel.id.desc()).limit(10)).all()
    finished = select(func.count()).select_from(Duel).where(mine, Duel.finished)
    return DuelListOut(duels=[duel_out(db, d, user) for d in recent],
                       wins=db.scalar(select(func.count()).select_from(Duel).where(Duel.winner_id == user.id)),
                       played=db.scalar(finished))
