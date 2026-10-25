"""Minigame leaderboards: each player's best points per level, with the animal
they played as. The game (static/minigames.js) sends how many treats a finished
run collected and the server works out the points from the animal's Speed, so a
score can't be sent straight in. That's the only check: kuro doesn't want heavy
anti-cheat, just nothing too easy."""

import json
import re
from functools import lru_cache

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from . import limits
from .auth import current_user
from .config import settings
from .db import get_db
from .models import Badge, GameScore, Species, User
from .social import blocked_ids, friend_ids, revealed_species_ids

router = APIRouter()

LEVEL = re.compile(r"^(sky|trail|river)\.[0-9]{1,2}$")
MAX_TREATS = 400  # more than any level has
# Same as mgPhysOf in minigames.js: the game runs faster for a faster animal.
TEMPO = [.75, .88, 1, 1.15, 1.3]
submits = limits.Limit(60, 30)


@lru_cache(maxsize=1)
def _speeds() -> dict[str, int]:
    try:
        stats = json.loads((settings.sprites_dir / "game_stats.json").read_text())["stats"]
    except (OSError, ValueError, KeyError):
        return {}
    return {slug: s[0] for slug, s in stats.items()}


def points(treats: int, slug: str) -> int:
    speed = _speeds().get(slug, 3)
    return round(treats * 10 * TEMPO[min(max(speed, 1), 5) - 1])


class ScoreIn(BaseModel):
    level: str = Field(pattern=LEVEL.pattern)
    species: str = Field(max_length=64)
    treats: int = Field(ge=0, le=MAX_TREATS)


@router.post("/games/scores")
def submit_score(body: ScoreIn, user: User = Depends(current_user), db: Session = Depends(get_db)):
    """Record a finished run. Keeps the best per (level, animal); you can only play as
    an animal you've captured."""
    key = str(user.id)
    if submits.blocked(key):
        raise HTTPException(429, "Too many scores, slow down")
    submits.hit(key)
    sp = db.scalar(select(Species).where(Species.slug == body.species))
    if sp is None or not db.scalar(select(Badge.id).where(Badge.user_id == user.id, Badge.species_id == sp.id)):
        raise HTTPException(400, "Capture this animal first")
    pts = points(body.treats, sp.slug)
    row = db.scalar(select(GameScore).where(GameScore.user_id == user.id, GameScore.level == body.level,
                                            GameScore.species_id == sp.id))
    best = row is None or pts > row.points
    if row is None:
        db.add(GameScore(user_id=user.id, level=body.level, species_id=sp.id, points=pts))
    elif best:
        row.points = pts
    db.commit()
    return {"points": pts, "animal_best": best}


@router.get("/games/scores/{level}")
def leaderboard(level: str, scope: str = Query("all", pattern="^(all|friends)$"),
                user: User = Depends(current_user), db: Session = Depends(get_db)):
    """Top 10 players on a level (everyone, or you and your friends), each with
    their best score and the animal they got it with. Animals you haven't revealed
    show as "a mystery <category>", like the news feed."""
    if not LEVEL.match(level):
        raise HTTPException(404, "No such level")
    friends, blocked = friend_ids(db, user.id), blocked_ids(db, user.id)
    q = select(GameScore, User, Species).join(User, GameScore.user_id == User.id) \
        .join(Species, GameScore.species_id == Species.id).where(GameScore.level == level)
    if scope == "friends":
        q = q.where(User.id.in_(friends | {user.id}))
    else:  # private players only show to their friends
        q = q.where(User.id.not_in(blocked), or_(User.is_private.is_(None), ~User.is_private,
                                                 User.id.in_(friends | {user.id})))
    q = q.order_by(GameScore.points.desc(), GameScore.created_at)
    revealed = revealed_species_ids(db, user)
    seen, rows, mine = set(), [], None
    for s, u, sp in db.execute(q):
        if u.id in seen:
            continue  # each player once, with their best animal
        seen.add(u.id)
        known = sp.id in revealed
        entry = {"rank": len(seen), "username": u.username, "avatar": u.avatar, "points": s.points,
                 "species": {"slug": sp.slug if known else None,
                             "common_name": sp.common_name if known else f"a mystery {sp.category}"},
                 "you": u.id == user.id}
        if len(rows) < 10:
            rows.append(entry)
        if u.id == user.id:
            mine = entry
        if len(rows) >= 10 and mine:
            break
    return {"level": level, "scope": scope, "top": rows, "you": mine}
