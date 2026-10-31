"""Minigame leaderboards and coins: each player's best points per level, with the animal
they played as. The game (static/minigames.js) sends how many treats a try
collected (finished or not) and the server works out the points from the animal's Speed, so a
score can't be sent straight in. That's the only check: kuro doesn't want heavy
anti-cheat, just nothing too easy.

Every finished level also pays coins (treats x the animal's speed bonus, up to a daily
limit), which buy skins for your animals and decorations for your habitat."""

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
from datetime import date

from .models import AnimalSkin, Badge, GameItem, GameScore, Species, User
from .safety import is_admin
from .social import blocked_ids, friend_ids, revealed_species_ids

router = APIRouter()

LEVEL = re.compile(r"^(sky|trail|river|pool|claw|slide|leap|dig|nectar|plunge|splash|call|echo|feeder|school|freeze)\.[0-9]{1,2}$")
# The newer games use the speed of the place they're set in (MG_PLACE in minigames.js).
PLACE = {"slide": "trail", "leap": "trail", "dig": "trail", "nectar": "sky", "plunge": "sky", "splash": "river", "echo": "sky",
         "feeder": "sky", "school": "river", "freeze": "trail"}
MAX_TREATS = 400  # more than any level has
# Same as mgPhysOf in minigames.js: the game runs faster for a faster animal.
TEMPO = [.75, .88, 1, 1.15, 1.3]
submits = limits.Limit(60, 30)
COINS_PER_DAY = 300

# What coins buy. Skins recolour an animal (drawn in habitat.js); decorations stand in
# your habitat (species/decor.json from tools/make_decor.py, drawn by decor.js), where the
# animals you've caught come to visit them.
SKINS = {
    "skin.frosty": {"kind": "skin", "name": "Frosty", "price": 150},
    "skin.rose": {"kind": "skin", "name": "Rose", "price": 150},
    "skin.midnight": {"kind": "skin", "name": "Midnight", "price": 200},
    "skin.golden": {"kind": "skin", "name": "Golden", "price": 400},
}
# How many decorations can be out at once in each part of the scene (HAB_DECOR_ROOM in decor.js).
ROOM = {"ground": 12, "pond": 3, "sand": 3, "sea": 2, "sky": 2}
ROOM_WORDS = {"ground": "your meadow", "pond": "the pond", "sand": "the beach", "sea": "the water", "sky": "the sky"}


def _decor() -> dict:
    try:
        items = json.loads(settings.decor_json.read_text())
    except (OSError, ValueError):
        return {}
    return {f"decor.{d['key']}": {"kind": "decor", "name": d["name"], "price": d["price"], "group": d["group"],
                                  "area": d["area"], "frames": d.get("frames", 1), "note": d.get("note", "")}
            for d in items}


SHOP = {**SKINS, **_decor()}


@lru_cache(maxsize=1)
def _stats() -> dict:
    try:
        return json.loads((settings.sprites_dir / "game_stats.json").read_text())
    except (OSError, ValueError):
        return {}


def speed_of(slug: str, game: str) -> int:
    """The animal's Speed in this game's place (land, water, air), as minigames.js has it."""
    d = _stats()
    game = PLACE.get(game, game)
    return d.get("speed", {}).get(slug, {}).get(game) or d.get("stats", {}).get(slug, [3])[0]


def points(treats: int, slug: str, game: str) -> int:
    speed = speed_of(slug, game)
    return round(treats * 10 * TEMPO[min(max(speed, 1), 5) - 1])


class ScoreIn(BaseModel):
    level: str = Field(pattern=LEVEL.pattern)
    species: str = Field(max_length=64)
    treats: int = Field(ge=0, le=MAX_TREATS)


@router.post("/games/scores")
def submit_score(body: ScoreIn, user: User = Depends(current_user), db: Session = Depends(get_db)):
    """Record a try, finished or not. Keeps the best per (level, animal); you can only play as
    an animal you've captured."""
    key = str(user.id)
    if submits.blocked(key):
        raise HTTPException(429, "Too many scores, slow down")
    submits.hit(key)
    sp = db.scalar(select(Species).where(Species.slug == body.species))
    if sp is None or not db.scalar(select(Badge.id).where(Badge.user_id == user.id, Badge.species_id == sp.id)):
        raise HTTPException(400, "Capture this animal first")
    pts = points(body.treats, sp.slug, body.level.split(".")[0])
    earned = _pay(user, pts // 10)
    row = db.scalar(select(GameScore).where(GameScore.user_id == user.id, GameScore.level == body.level,
                                            GameScore.species_id == sp.id))
    best = row is None or pts > row.points
    # The board shows the animal in the skin it wore, as the server knows it.
    skin = db.scalar(select(AnimalSkin.skin).where(AnimalSkin.user_id == user.id, AnimalSkin.species_id == sp.id))
    if row is None:
        db.add(GameScore(user_id=user.id, level=body.level, species_id=sp.id, points=pts, skin=skin))
    elif best:
        row.points, row.skin = pts, skin
    db.commit()
    return {"points": pts, "animal_best": best, "coins_earned": earned, "coins": user.coins or 0}


def _pay(user: User, coins: int) -> int:
    """Adds coins, up to COINS_PER_DAY a day. Returns how many were added."""
    today = date.today().isoformat()
    if user.coins_day != today:
        user.coins_day, user.coins_today = today, 0
    coins = max(0, min(coins, COINS_PER_DAY - (user.coins_today or 0)))
    user.coins_today = (user.coins_today or 0) + coins
    user.coins = (user.coins or 0) + coins
    return coins


def _shop(db: Session, user: User) -> dict:
    if is_admin(user):
        _own_everything(db, user)
    owned = {i.item: i for i in db.scalars(select(GameItem).where(GameItem.user_id == user.id).order_by(GameItem.id))}
    skins = {s.species.slug: s.skin for s in db.scalars(select(AnimalSkin).where(AnimalSkin.user_id == user.id))}
    items = [{"key": k, **v, "owned": k in owned, "on": k in owned and owned[k].on} for k, v in SHOP.items()]
    return {"coins": user.coins or 0, "items": items, "skins": skins,
            "decor": [k.split(".", 1)[1] for k, i in owned.items() if k.startswith("decor.") and i.on]}


def _own_everything(db: Session, user: User):
    """Admin accounts (ADMIN_USERNAMES) own every skin and decoration, for trying them out.
    New decorations start hidden so they don't crowd the habitat."""
    have = set(db.scalars(select(GameItem.item).where(GameItem.user_id == user.id)))
    missing = [k for k in SHOP if k not in have]
    for k in missing:
        db.add(GameItem(user_id=user.id, item=k, on=False))
    if missing:
        db.commit()


@router.get("/games/shop")
def shop(user: User = Depends(current_user), db: Session = Depends(get_db)):
    """Your coins, what's for sale, what you own, and your animals' skins."""
    return _shop(db, user)


class BuyIn(BaseModel):
    item: str = Field(max_length=32)


@router.post("/games/shop/buy")
def buy(body: BuyIn, user: User = Depends(current_user), db: Session = Depends(get_db)):
    it = SHOP.get(body.item)
    if it is None:
        raise HTTPException(404, "Nothing like that in the shop")
    if db.scalar(select(GameItem.id).where(GameItem.user_id == user.id, GameItem.item == body.item)):
        raise HTTPException(409, "You already have it")
    if (user.coins or 0) < it["price"]:
        raise HTTPException(400, "Not enough coins yet")
    user.coins = (user.coins or 0) - it["price"]
    # A new decoration goes straight into your habitat if there's room for it there.
    db.add(GameItem(user_id=user.id, item=body.item, on=it["kind"] != "decor" or _room(db, user, it["area"])))
    db.commit()
    return _shop(db, user)


class SkinIn(BaseModel):
    species: str = Field(max_length=64)
    skin: str | None = Field(None, max_length=16)


@router.post("/games/shop/skin")
def wear_skin(body: SkinIn, user: User = Depends(current_user), db: Session = Depends(get_db)):
    """Puts a skin you own on one of your animals (skin null takes it off)."""
    sp = db.scalar(select(Species).where(Species.slug == body.species))
    if sp is None or not db.scalar(select(Badge.id).where(Badge.user_id == user.id, Badge.species_id == sp.id)):
        raise HTTPException(400, "Capture this animal first")
    row = db.scalar(select(AnimalSkin).where(AnimalSkin.user_id == user.id, AnimalSkin.species_id == sp.id))
    if body.skin is None:
        if row:
            db.delete(row)
    else:
        if not db.scalar(select(GameItem.id).where(GameItem.user_id == user.id, GameItem.item == f"skin.{body.skin}")):
            raise HTTPException(400, "Buy that skin first")
        if row:
            row.skin = body.skin
        else:
            db.add(AnimalSkin(user_id=user.id, species_id=sp.id, skin=body.skin))
    db.commit()
    return _shop(db, user)


def _room(db: Session, user: User, area: str) -> bool:
    """Whether another decoration fits in that part of your habitat."""
    out = db.scalars(select(GameItem.item).where(GameItem.user_id == user.id, GameItem.on.is_(True)))
    return sum(1 for k in out if SHOP.get(k, {}).get("area") == area) < ROOM.get(area, 0)


class DecorIn(BaseModel):
    item: str = Field(max_length=32)
    on: bool


@router.post("/games/shop/decor")
def show_decor(body: DecorIn, user: User = Depends(current_user), db: Session = Depends(get_db)):
    """Shows or hides a decoration you own in your habitat."""
    row = db.scalar(select(GameItem).where(GameItem.user_id == user.id, GameItem.item == body.item))
    if row is None or not body.item.startswith("decor.") or body.item not in SHOP:
        raise HTTPException(404, "You don't have that")
    area = SHOP[body.item]["area"]
    if body.on and not row.on and not _room(db, user, area):
        raise HTTPException(409, f"There's no room left in {ROOM_WORDS[area]}. Hide another decoration there first.")
    row.on = body.on
    db.commit()
    return _shop(db, user)


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
                 "skin": s.skin if known else None, "you": u.id == user.id}
        if len(rows) < 10:
            rows.append(entry)
        if u.id == user.id:
            mine = entry
        if len(rows) >= 10 and mine:
            break
    return {"level": level, "scope": scope, "top": rows, "you": mine}
