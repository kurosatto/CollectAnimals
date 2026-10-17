"""Friends, photo albums, the per-species gallery, likes and comments.

Rules:
- A species' name is hidden until you or one of your friends has caught it.
- Each user shows one album photo per species; it starts as their first
  matching capture and they can swap in a later one.
- Album photos are visible to every logged-in user who has that species
  revealed, ranked by likes in the species gallery. How precisely others see
  where it was taken depends on the animal's rarity (see app/places.py).
- Anyone who can see a photo can like it and comment on it; you don't need
  to be friends. Commenters and the photo's owner can delete comments.
- The news feed lists everyone's newest album photos, unless they opted out.
  Animals the viewer hasn't unlocked show as a mystery with no photo.
"""

from __future__ import annotations

import math
from datetime import datetime, timedelta, timezone
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy import and_, delete, func, or_, select
from sqlalchemy.orm import Session

from . import goals, places
from .scoring import to_local
from . import states
from .auth import current_user
from .db import get_db
from .models import AlbumPhoto, Badge, Capture, Friendship, PhotoComment, PhotoLike, Species, StateSpecies, User
from .schemas import (WhereWhenOut, AchievementOut, AlbumOut, AlbumPick, CommentIn, CommentOut, FeedOut, ProfileOut, SuggestionOut, Tally, FriendOut, FriendRequestIn, FriendsOut,
                      GalleryOut, PhotoOut, SettingsIn, SpeciesOut)
from .storage import get_storage

router = APIRouter()


# --- visibility helpers -----------------------------------------------------

def friend_ids(db: Session, user_id: int) -> set[int]:
    rows = db.execute(select(Friendship.requester_id, Friendship.addressee_id).where(
        Friendship.accepted, or_(Friendship.requester_id == user_id,
                                 Friendship.addressee_id == user_id)))
    return {a if b == user_id else b for a, b in rows}


def revealed_species_ids(db: Session, user: User | None) -> set[int]:
    if user is None:
        return set()
    ids = {user.id} | friend_ids(db, user.id)
    return set(db.scalars(select(Badge.species_id).where(Badge.user_id.in_(ids)).distinct()))


def shown_to(user: User, friends: set[int]):
    """SQL filter: album photos this viewer may see as far as privacy goes
    (everyone's, except private players' unless they're you or a friend).
    Use on a query that joins User on AlbumPhoto.user_id."""
    return or_(User.is_private.is_(None), ~User.is_private, User.id.in_(friends | {user.id}))


def species_out(s: Species, revealed: bool, m: StateSpecies | None = None) -> SpeciesOut:
    """The species card; with a state's list entry, that state's name and rarity."""
    name, rarity = (m.common_name, m.rarity) if m is not None else (s.common_name, s.rarity)
    if revealed:
        return SpeciesOut(number=s.id, slug=s.slug, common_name=name,
                          scientific_name=s.scientific_name, category=s.category,
                          rarity=rarity, revealed=True)
    return SpeciesOut(number=s.id, slug=None, common_name=None, scientific_name=None,
                      category=s.category, rarity=rarity, revealed=False)


def find_species(db: Session, key: str) -> Species:
    """Look a species up by its number (works while hidden) or its slug."""
    s = db.get(Species, int(key)) if key.isdigit() else db.scalar(
        select(Species).where(Species.slug == key))
    if not s:
        raise HTTPException(404, "Unknown species")
    return s


def where_when_out(c: Capture, utc_offset: int) -> WhereWhenOut:
    """A capture's time and place as its owner sees them (exact). Without a photo
    time, the upload time in the state's local time."""
    has_place = c.latitude is not None and c.longitude is not None
    taken = c.taken_at.replace(tzinfo=None) if c.taken_at else to_local(c.created_at, utc_offset)
    return WhereWhenOut(
        capture_id=c.id, state=c.state, taken_at=taken.replace(microsecond=0),
        time_source=c.time_source or ("photo" if c.taken_at else "upload"),
        latitude=round(c.latitude, 5) if has_place else None,
        longitude=round(c.longitude, 5) if has_place else None,
        place=places.place_name(c.latitude, c.longitude) if has_place else None,
        place_source=c.place_source if has_place else None)


def photo_out(p: AlbumPhoto, viewer: User, friends: set[int], likes: int, liked: bool,
              revealed: bool = True, rank: int | None = None, show_image: bool = True,
              comments: int = 0) -> PhotoOut:
    mine = p.user_id == viewer.id
    c = p.capture
    loc = places.for_viewer(c.latitude, c.longitude, p.species.rarity, mine, p.user_id in friends)
    return PhotoOut(
        id=p.id, url=get_storage().url(c.image_path) if show_image else None,
        username=p.user.username, species=species_out(p.species, revealed),
        taken_on=(c.taken_at or c.created_at).date(), caught_at=c.created_at,
        latitude=loc.latitude, longitude=loc.longitude, location_precise=loc.precise,
        place=loc.place, like_count=likes, liked_by_me=liked, comment_count=comments, is_mine=mine,
        by_friend=p.user_id in friends, rank=rank, score=c.score, stars=c.score_stars,
        where_when=where_when_out(c, (states.get(c.state or p.user.state) or states.get(None)).utc_offset)
        if mine else None)


def _like_info(db: Session, photo_ids: list[int], viewer_id: int) -> tuple[dict[int, int], set[int]]:
    if not photo_ids:
        return {}, set()
    counts = dict(db.execute(select(PhotoLike.photo_id, func.count()).where(
        PhotoLike.photo_id.in_(photo_ids)).group_by(PhotoLike.photo_id)).all())
    mine = set(db.scalars(select(PhotoLike.photo_id).where(
        PhotoLike.photo_id.in_(photo_ids), PhotoLike.user_id == viewer_id)))
    return counts, mine


def _comment_counts(db: Session, photo_ids: list[int]) -> dict[int, int]:
    if not photo_ids:
        return {}
    return dict(db.execute(select(PhotoComment.photo_id, func.count()).where(
        PhotoComment.photo_id.in_(photo_ids)).group_by(PhotoComment.photo_id)).all())


def clear_reactions(db: Session, photo_id: int) -> None:
    """Likes and comments belong to one picture: drop them when it changes or goes."""
    db.execute(delete(PhotoLike).where(PhotoLike.photo_id == photo_id))
    db.execute(delete(PhotoComment).where(PhotoComment.photo_id == photo_id))


def ensure_album_photo(db: Session, capture: Capture) -> AlbumPhoto | None:
    """Make this capture the user's album photo for its species if they have none yet."""
    if capture.species_id is None:
        return None
    existing = db.scalar(select(AlbumPhoto).where(AlbumPhoto.user_id == capture.user_id,
                                                  AlbumPhoto.species_id == capture.species_id))
    if existing:
        return None
    photo = AlbumPhoto(user_id=capture.user_id, species_id=capture.species_id, capture_id=capture.id)
    db.add(photo)
    db.flush()
    return photo


# --- captures per state ------------------------------------------------------

def catches_in(db: Session, user_id: int, state: str) -> dict[int, tuple[int, datetime]]:
    """What a player has captured in one state: species id -> (how many times,
    first capture). Captures count only in the state they were made in."""
    return {sid: (n, first) for sid, n, first in db.execute(
        select(Capture.species_id, func.count(), func.min(Capture.created_at))
        .where(Capture.user_id == user_id, Capture.state == state, Capture.species_id.is_not(None))
        .group_by(Capture.species_id))}


def caught_counts(db: Session, users: list[User]) -> dict[int, int]:
    """How many species each player has captured in their own state."""
    out: dict[int, int] = {}
    for u in users:
        out[u.id] = db.scalar(select(func.count(func.distinct(Capture.species_id))).where(
            Capture.user_id == u.id, Capture.state == u.state, Capture.species_id.is_not(None))) or 0
    return out


# --- albums -----------------------------------------------------------------

def _album(db: Session, owner: User, viewer: User) -> AlbumOut:
    friends = friend_ids(db, viewer.id)
    revealed = revealed_species_ids(db, viewer)
    photos = db.scalars(select(AlbumPhoto).where(AlbumPhoto.user_id == owner.id)
                        .order_by(AlbumPhoto.species_id)).all()
    counts, liked = _like_info(db, [p.id for p in photos], viewer.id)
    comments = _comment_counts(db, [p.id for p in photos])
    caught = db.scalar(select(func.count()).select_from(Badge).where(Badge.user_id == owner.id))
    total = db.scalar(select(func.count()).select_from(Species))
    return AlbumOut(username=owner.username, caught=caught, total=total, photos=[
        photo_out(p, viewer, friends, counts.get(p.id, 0), p.id in liked, p.species_id in revealed,
                  comments=comments.get(p.id, 0))
        for p in photos])


@router.get("/me/album", response_model=AlbumOut)
def my_album(user: User = Depends(current_user), db: Session = Depends(get_db)):
    return _album(db, user, user)


@router.get("/users/{username}/album", response_model=AlbumOut)
def user_album(username: str, user: User = Depends(current_user), db: Session = Depends(get_db)):
    owner = user_named(db, username)
    if not owner:
        raise HTTPException(404, "No such user")
    if owner.id != user.id and owner.id not in friend_ids(db, user.id):
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Only friends can see each other's albums")
    return _album(db, owner, user)


@router.put("/me/album/{species_key}", response_model=PhotoOut)
def set_album_photo(species_key: str, body: AlbumPick, user: User = Depends(current_user),
                    db: Session = Depends(get_db)):
    """Swap your album photo for a species to another of your captures of it.
    Likes and comments belong to the old picture, so they are cleared."""
    s = find_species(db, species_key)
    capture = db.get(Capture, body.capture_id)
    if not capture or capture.user_id != user.id or capture.species_id != s.id:
        raise HTTPException(400, "That isn't one of your captures of this species")
    photo = db.scalar(select(AlbumPhoto).where(AlbumPhoto.user_id == user.id,
                                               AlbumPhoto.species_id == s.id))
    if photo is None:
        photo = AlbumPhoto(user_id=user.id, species_id=s.id, capture_id=capture.id)
        db.add(photo)
    elif photo.capture_id != capture.id:
        clear_reactions(db, photo.id)
        photo.capture_id = capture.id
    db.commit()
    db.refresh(photo)
    return photo_out(photo, user, friend_ids(db, user.id), 0, False)


def _delete_album_photo(db: Session, photo: AlbumPhoto) -> None:
    """Delete the photo everywhere (album, gallery, feed, its likes and comments) and un-catch
    the animal: the badge and all of the user's captures of that species go,
    image files included. The animal is locked again unless a friend has
    caught it, and catching it again starts over with a new badge."""
    user_id, species_id = photo.user_id, photo.species_id
    clear_reactions(db, photo.id)
    db.delete(photo)
    db.execute(delete(Badge).where(Badge.user_id == user_id, Badge.species_id == species_id))
    db.flush()
    storage = get_storage()
    for c in db.scalars(select(Capture).where(Capture.user_id == user_id,
                                              Capture.species_id == species_id)).all():
        if c.image_path:
            storage.delete(c.image_path)
        db.delete(c)
    db.commit()


@router.delete("/me/album/{species_key}", status_code=204)
def remove_album_photo(species_key: str, user: User = Depends(current_user),
                       db: Session = Depends(get_db)):
    s = find_species(db, species_key)
    photo = db.scalar(select(AlbumPhoto).where(AlbumPhoto.user_id == user.id,
                                               AlbumPhoto.species_id == s.id))
    if photo:
        _delete_album_photo(db, photo)
    return Response(status_code=204)


@router.delete("/photos/{photo_id}", status_code=204)
def delete_photo(photo_id: int, user: User = Depends(current_user), db: Session = Depends(get_db)):
    photo = db.get(AlbumPhoto, photo_id)
    if not photo or photo.user_id != user.id:
        raise HTTPException(404, "No such photo of yours")
    _delete_album_photo(db, photo)
    return Response(status_code=204)


# --- profiles -----------------------------------------------------------------

RARITIES = ["common", "uncommon", "rare", "legendary"]
CATEGORY_TITLES = {"mammal": "Mammal", "bird": "Bird", "reptile": "Reptile", "amphibian": "Amphibian",
                   "invertebrate": "Bug", "marine": "Ocean"}


def _achievements(caught: int, total: int, by_rarity: dict[str, Tally],
                  by_category: dict[str, Tally], likes: int) -> list[AchievementOut]:
    out = []

    def add(id_, title, description, progress, goal):
        goal = max(goal, 1)
        out.append(AchievementOut(id=id_, title=title, description=description,
                                  earned=progress >= goal, progress=min(progress, goal), goal=goal))

    add("first_catch", "First capture", "Capture your first animal", caught, 1)
    for n in (10, 25, 50):
        add(f"collector_{n}", f"{n} animals", f"Capture {n} different animals", caught, n)
    add("complete", "Field Guide complete", f"Capture all {total} animals", caught, total)
    rare = by_rarity.get("rare", Tally(caught=0, total=0))
    legendary = by_rarity.get("legendary", Tally(caught=0, total=0))
    add("first_rare", "Rare find", "Capture a rare animal", rare.caught, 1)
    add("first_legendary", "Legend", "Capture a legendary animal", legendary.caught, 1)
    add("all_legendaries", "Living legend", "Capture every legendary animal", legendary.caught, legendary.total)
    for cat, t in by_category.items():
        name = CATEGORY_TITLES.get(cat, cat.title())
        add(f"all_{cat}", f"{name} master", f"Capture every {cat} on the list", t.caught, t.total)
    add("liked_10", "Crowd favorite", "Get 10 likes on your photos", likes, 10)
    return out


def _set_achievements(state: str, members: list[StateSpecies], caught_ids: set[int]) -> list[AchievementOut]:
    """One achievement per collection set: capture everything in it."""
    ids = {m.species.slug: m.species_id for m in members}
    out = []
    for s in goals.sets_for(state, set(ids)):
        n = sum(ids[x] in caught_ids for x in s.slugs)
        out.append(AchievementOut(id=f"set_{s.id}", title=s.title, description=f"Complete the {s.title} set",
                                  earned=n == len(s.slugs), progress=n, goal=len(s.slugs)))
    return out


def _friendship(db: Session, viewer: User, other: User) -> str:
    if viewer.id == other.id:
        return "self"
    f = db.scalar(select(Friendship).where(_between(viewer.id, other.id)))
    if not f:
        return "none"
    if f.accepted:
        return "friends"
    return "requested" if f.requester_id == viewer.id else "incoming"


@router.get("/users/{username}", response_model=ProfileOut)
def user_profile(username: str, user: User = Depends(current_user), db: Session = Depends(get_db)):
    """A player's page: achievements, catches by rarity and group, and photos."""
    owner = _user_by_name(db, username)
    friendship = _friendship(db, user, owner)
    friends = friend_ids(db, user.id)
    revealed = revealed_species_ids(db, user)

    # Counted against the owner's state list, with that state's rarities.
    members = db.scalars(select(StateSpecies).where(StateSpecies.state == owner.state)
                         .order_by(StateSpecies.position)).all()
    caught_ids = {m.species_id for m in members} & set(catches_in(db, owner.id, owner.state))
    by_rarity = {r: Tally(caught=0, total=0) for r in RARITIES}
    by_category: dict[str, Tally] = {}
    for m in members:
        for bucket in (by_rarity.setdefault(m.rarity, Tally(caught=0, total=0)),
                       by_category.setdefault(m.species.category, Tally(caught=0, total=0))):
            bucket.total += 1
            bucket.caught += m.species_id in caught_ids

    photos = db.scalars(select(AlbumPhoto).where(AlbumPhoto.user_id == owner.id)
                        .order_by(AlbumPhoto.species_id)).all()
    likes_received = db.scalar(select(func.count()).select_from(PhotoLike).join(
        AlbumPhoto, AlbumPhoto.id == PhotoLike.photo_id).where(AlbumPhoto.user_id == owner.id))
    close = friendship in ("self", "friends")
    visible = [p for p in photos if close or (p.species_id in revealed and not owner.is_private)]
    counts, liked = _like_info(db, [p.id for p in visible], user.id)
    comments = _comment_counts(db, [p.id for p in visible])

    return ProfileOut(
        username=owner.username, joined=owner.created_at, friendship=friendship,
        is_bot=bool(owner.is_bot), is_private=bool(owner.is_private), state=owner.state,
        caught=len(caught_ids), total=len(members), by_rarity=by_rarity, by_category=by_category,
        likes_received=likes_received,
        achievements=_achievements(len(caught_ids), len(members), by_rarity, by_category, likes_received)
        + _set_achievements(owner.state, members, caught_ids),
        legendaries=[species_out(m.species, m.species_id in revealed, m) for m in members
                     if m.rarity == "legendary" and m.species_id in caught_ids],
        photos=[photo_out(p, user, friends, counts.get(p.id, 0), p.id in liked, p.species_id in revealed,
                          comments=comments.get(p.id, 0))
                for p in visible],
        hidden_photos=len(photos) - len(visible))


# --- gallery & likes --------------------------------------------------------

@router.get("/species/{species_key}/photos", response_model=GalleryOut)
def species_gallery(species_key: str,
                    scope: Literal["all", "friends"] = "all",
                    sort: Literal["top", "new"] = "top",
                    limit: int = Query(30, ge=1, le=100), offset: int = Query(0, ge=0),
                    user: User = Depends(current_user), db: Session = Depends(get_db)):
    """Everyone's (or your friends') album photos of one species. With sort=top
    this is the ranking: most liked first, earliest upload breaking ties."""
    s = find_species(db, species_key)
    if s.id not in revealed_species_ids(db, user):
        raise HTTPException(status.HTTP_403_FORBIDDEN,
                            "Capture this animal, or have a friend capture it, to see its photos")
    friends = friend_ids(db, user.id)
    likes = (select(PhotoLike.photo_id, func.count().label("n"))
             .group_by(PhotoLike.photo_id).subquery())
    n = func.coalesce(likes.c.n, 0)
    q = (select(AlbumPhoto, n).outerjoin(likes, likes.c.photo_id == AlbumPhoto.id)
         .join(User, User.id == AlbumPhoto.user_id)
         .where(AlbumPhoto.species_id == s.id, shown_to(user, friends)))
    if scope == "friends":
        q = q.where(AlbumPhoto.user_id.in_(friends | {user.id}))
    total = db.scalar(select(func.count()).select_from(q.subquery()))
    order = ((n.desc(), AlbumPhoto.created_at, AlbumPhoto.id) if sort == "top"
             else (AlbumPhoto.created_at.desc(), AlbumPhoto.id.desc()))
    rows = db.execute(q.order_by(*order).limit(limit).offset(offset)).all()
    _, liked = _like_info(db, [p.id for p, _ in rows], user.id)
    comments = _comment_counts(db, [p.id for p, _ in rows])
    return GalleryOut(species=species_out(s, True), scope=scope, sort=sort, total=total, photos=[
        photo_out(p, user, friends, count, p.id in liked,
                  rank=offset + i + 1 if sort == "top" else None, comments=comments.get(p.id, 0))
        for i, (p, count) in enumerate(rows)])


@router.get("/feed", response_model=FeedOut)
def news_feed(scope: Literal["near", "state", "all", "friends"] = "all",
              state: str | None = None,
              lat: float | None = Query(None, ge=-90, le=90),
              lon: float | None = Query(None, ge=-180, le=180),
              radius_km: float = Query(50, ge=places.MIN_RADIUS_KM, le=500),
              uncaught: bool = False,
              limit: int = Query(20, ge=1, le=50), before: int | None = Query(None, ge=1),
              user: User = Depends(current_user), db: Session = Depends(get_db)):
    """Newest catches first: each album photo, ordered by when it was caught.

    scope=all is global. scope=state keeps catches made inside a state (?state=,
    default the viewer's), or without a location, by players from that state.
    scope=near (needs lat/lon, the viewer's position) keeps catches within
    radius_km. Distances use each catch's blurred position, not its exact
    GPS, so the filter can't be used to pinpoint anyone (see places.py).
    uncaught=true keeps only animals the viewer hasn't caught yet.
    Players who turned off show_in_feed are left out (except to themselves),
    and private players' catches only reach their friends."""
    if scope == "near" and (lat is None or lon is None):
        raise HTTPException(400, "scope=near needs lat and lon")
    friends = friend_ids(db, user.id)
    revealed = revealed_species_ids(db, user)
    q = (select(AlbumPhoto).join(Capture, Capture.id == AlbumPhoto.capture_id)
         .join(User, User.id == AlbumPhoto.user_id)
         .where(or_(User.show_in_feed.is_(None), User.show_in_feed, User.id == user.id),
                shown_to(user, friends)))
    if scope == "friends":
        q = q.where(AlbumPhoto.user_id.in_(friends | {user.id}))
    if scope == "state":
        st = states.get(state or user.state)
        if st is None:
            raise HTTPException(404, f"Unknown state {state!r}")
        b = st.bounds
        q = q.where(or_(and_(Capture.latitude.between(b["south"], b["north"]),
                             Capture.longitude.between(b["west"], b["east"])),
                        and_(Capture.latitude.is_(None), User.state == st.code)))
    if uncaught:
        q = q.where(AlbumPhoto.species_id.not_in(
            select(Badge.species_id).where(Badge.user_id == user.id)))
    if scope == "near":
        # Cheap bounding box in SQL (with slack for the blurring), exact check below.
        dlat = radius_km / 111 + 0.6
        dlon = radius_km / (111 * max(0.2, math.cos(math.radians(lat)))) + 0.6
        q = q.where(Capture.latitude.between(lat - dlat, lat + dlat),
                    Capture.longitude.between(lon - dlon, lon + dlon))

    rows: list[AlbumPhoto] = []
    cursor = before
    while len(rows) <= limit:
        page = q.where(Capture.id < cursor) if cursor else q
        batch = db.scalars(page.order_by(Capture.id.desc()).limit(200)).all()
        if not batch:
            break
        for p in batch:
            c = p.capture
            if scope != "near" or places.blurred_distance_km(
                    c.latitude, c.longitude, p.species.rarity, lat, lon) <= radius_km:
                rows.append(p)
        cursor = batch[-1].capture_id
    more = len(rows) > limit
    rows = rows[:limit]
    counts, liked = _like_info(db, [p.id for p in rows], user.id)
    comments = _comment_counts(db, [p.id for p in rows])
    return FeedOut(scope=scope, next_before=rows[-1].capture_id if more else None, photos=[
        photo_out(p, user, friends, counts.get(p.id, 0), p.id in liked,
                  revealed=p.species_id in revealed, show_image=p.species_id in revealed,
                  comments=comments.get(p.id, 0))
        for p in rows])


@router.patch("/me/settings")
def update_settings(body: SettingsIn, user: User = Depends(current_user),
                    db: Session = Depends(get_db)):
    if body.show_in_feed is not None:
        user.show_in_feed = body.show_in_feed
    if body.is_private is not None:
        user.is_private = body.is_private
    db.commit()
    return {"show_in_feed": user.show_in_feed is not False, "is_private": bool(user.is_private)}


def _visible_photo(db: Session, photo_id: int, user: User) -> AlbumPhoto:
    photo = db.get(AlbumPhoto, photo_id)
    if not photo or photo.species_id not in revealed_species_ids(db, user):
        raise HTTPException(404, "No such photo")
    if photo.user.is_private and photo.user_id != user.id and photo.user_id not in friend_ids(db, user.id):
        raise HTTPException(404, "No such photo")
    return photo


@router.post("/photos/{photo_id}/like", status_code=204)
def like_photo(photo_id: int, user: User = Depends(current_user), db: Session = Depends(get_db)):
    photo = _visible_photo(db, photo_id, user)
    if photo.user_id == user.id:
        raise HTTPException(400, "You can't like your own photo")
    if not db.scalar(select(PhotoLike).where(PhotoLike.photo_id == photo.id,
                                             PhotoLike.user_id == user.id)):
        db.add(PhotoLike(photo_id=photo.id, user_id=user.id))
        db.commit()
    return Response(status_code=204)


@router.delete("/photos/{photo_id}/like", status_code=204)
def unlike_photo(photo_id: int, user: User = Depends(current_user), db: Session = Depends(get_db)):
    photo = _visible_photo(db, photo_id, user)
    db.execute(delete(PhotoLike).where(PhotoLike.photo_id == photo.id, PhotoLike.user_id == user.id))
    db.commit()
    return Response(status_code=204)


# --- comments -----------------------------------------------------------------

# Light spam guard: at most this many comments per player per window.
COMMENT_LIMITS = ((timedelta(minutes=1), 5), (timedelta(days=1), 100))


def _aware(t: datetime) -> datetime:
    return t if t.tzinfo else t.replace(tzinfo=timezone.utc)


def comment_out(c: PhotoComment, photo: AlbumPhoto, viewer: User) -> CommentOut:
    return CommentOut(id=c.id, username=c.user.username, body=c.body, created_at=c.created_at,
                      is_mine=c.user_id == viewer.id, can_delete=viewer.id in (c.user_id, photo.user_id))


@router.get("/photos/{photo_id}/comments", response_model=list[CommentOut])
def photo_comments(photo_id: int, user: User = Depends(current_user), db: Session = Depends(get_db)):
    """Comments on a photo, oldest first. Same visibility as the photo itself."""
    photo = _visible_photo(db, photo_id, user)
    rows = db.scalars(select(PhotoComment).where(PhotoComment.photo_id == photo.id)
                      .order_by(PhotoComment.created_at, PhotoComment.id).limit(500)).all()
    return [comment_out(c, photo, user) for c in rows]


@router.post("/photos/{photo_id}/comments", response_model=CommentOut, status_code=201)
def add_comment(photo_id: int, body: CommentIn, user: User = Depends(current_user),
                db: Session = Depends(get_db)):
    photo = _visible_photo(db, photo_id, user)
    text_ = " ".join(body.body.split())
    if not text_:
        raise HTTPException(422, "Write something first")
    now = datetime.now(timezone.utc)
    recent = [_aware(t) for t in db.scalars(select(PhotoComment.created_at).where(
        PhotoComment.user_id == user.id, PhotoComment.created_at >= now - max(w for w, _ in COMMENT_LIMITS)))]
    for window, most in COMMENT_LIMITS:
        if sum(t >= now - window for t in recent) >= most:
            raise HTTPException(429, "You're commenting too fast. Try again in a bit.")
    c = PhotoComment(photo_id=photo.id, user_id=user.id, body=text_)
    db.add(c)
    db.commit()
    db.refresh(c)
    return comment_out(c, photo, user)


@router.delete("/comments/{comment_id}", status_code=204)
def delete_comment(comment_id: int, user: User = Depends(current_user), db: Session = Depends(get_db)):
    c = db.get(PhotoComment, comment_id)
    photo = c and db.get(AlbumPhoto, c.photo_id)
    if not c or not photo or user.id not in (c.user_id, photo.user_id):
        raise HTTPException(404, "No such comment")
    db.delete(c)
    db.commit()
    return Response(status_code=204)


@router.get("/media/{key}", include_in_schema=False)
def media(key: str, db: Session = Depends(get_db)):
    """Serve album photos from local storage. Keys are random, and only photos
    someone has put in their album are served; other captures stay private."""
    shown = db.scalar(select(AlbumPhoto.id).join(Capture, Capture.id == AlbumPhoto.capture_id)
                      .where(Capture.image_path == key).limit(1))
    try:
        data = get_storage().get(key) if shown else None
    except ValueError:
        data = None
    if data is None:
        raise HTTPException(404, "Not found")
    return Response(data, media_type="image/jpeg",
                    headers={"Cache-Control": "private, max-age=86400"})


# --- friends ----------------------------------------------------------------

def _between(a: int, b: int):
    return or_(and_(Friendship.requester_id == a, Friendship.addressee_id == b),
               and_(Friendship.requester_id == b, Friendship.addressee_id == a))


def user_named(db: Session, username: str) -> User | None:
    """Usernames ignore case ("Kuro" finds "kuro"). An exact match wins, for
    accounts made before that rule whose names differ only in case."""
    name = username.strip()
    return db.scalar(select(User).where(User.username == name)) or db.scalar(
        select(User).where(func.lower(User.username) == name.lower()).order_by(User.id))


def _user_by_name(db: Session, username: str) -> User:
    other = user_named(db, username)
    if not other:
        raise HTTPException(404, "No user with that username")
    return other


@router.get("/friends", response_model=FriendsOut)
def list_friends(user: User = Depends(current_user), db: Session = Depends(get_db)):
    rows = db.scalars(select(Friendship).where(or_(Friendship.requester_id == user.id,
                                                   Friendship.addressee_id == user.id))).all()
    ids = {f.requester_id if f.addressee_id == user.id else f.addressee_id for f in rows}
    caught = caught_counts(db, [f.requester if f.addressee_id == user.id else f.addressee for f in rows])
    out = FriendsOut(friends=[], incoming=[], outgoing=[])
    for f in sorted(rows, key=lambda f: f.created_at):
        other = f.requester if f.addressee_id == user.id else f.addressee
        entry = FriendOut(username=other.username, caught=caught.get(other.id, 0) if f.accepted else 0,
                          since=f.created_at, is_bot=bool(other.is_bot))
        if f.accepted:
            out.friends.append(entry)
        elif f.addressee_id == user.id:
            out.incoming.append(entry)
        else:
            out.outgoing.append(entry)
    out.friends.sort(key=lambda e: e.username.lower())
    return out


@router.post("/friends/requests", status_code=201)
def send_friend_request(body: FriendRequestIn, user: User = Depends(current_user),
                        db: Session = Depends(get_db)):
    """Ask someone to be friends. If they already asked you, or they're a bot
    friend, you're friends now."""
    other = _user_by_name(db, body.username)
    if other.id == user.id:
        raise HTTPException(400, "You can't add yourself")
    f = db.scalar(select(Friendship).where(_between(user.id, other.id)))
    if f and f.accepted:
        raise HTTPException(409, "You're already friends")
    if f and f.requester_id == user.id:
        raise HTTPException(409, "Request already sent")
    if f:
        f.accepted = True
    else:
        db.add(Friendship(requester_id=user.id, addressee_id=other.id, accepted=bool(other.is_bot)))
    db.commit()
    return {"status": "friends" if f or other.is_bot else "requested"}


@router.get("/friends/suggestions", response_model=list[SuggestionOut])
def friend_suggestions(user: User = Depends(current_user), db: Session = Depends(get_db)):
    """Bot friends you haven't added or asked yet."""
    linked = {a if b == user.id else b for a, b in db.execute(
        select(Friendship.requester_id, Friendship.addressee_id).where(
            or_(Friendship.requester_id == user.id, Friendship.addressee_id == user.id)))}
    bots = db.scalars(select(User).where(User.is_bot, User.id != user.id,
                                         User.id.not_in(linked)).order_by(User.username)).all()
    caught = caught_counts(db, list(bots))
    return [SuggestionOut(username=b.username, caught=caught.get(b.id, 0), is_bot=True) for b in bots]


@router.post("/friends/requests/{username}/accept")
def accept_friend_request(username: str, user: User = Depends(current_user),
                          db: Session = Depends(get_db)):
    other = _user_by_name(db, username)
    f = db.scalar(select(Friendship).where(Friendship.requester_id == other.id,
                                           Friendship.addressee_id == user.id))
    if not f:
        raise HTTPException(404, "No friend request from that user")
    f.accepted = True
    db.commit()
    return {"status": "friends"}


@router.delete("/friends/{username}", status_code=204)
def remove_friend(username: str, user: User = Depends(current_user), db: Session = Depends(get_db)):
    """Unfriend, decline an incoming request, or cancel one you sent."""
    other = _user_by_name(db, username)
    db.execute(delete(Friendship).where(_between(user.id, other.id)))
    db.commit()
    return Response(status_code=204)
