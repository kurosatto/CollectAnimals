"""Friends, photo albums, the per-species gallery and likes.

Rules:
- A species' name is hidden until you or one of your friends has caught it.
- Each user shows one album photo per species; it starts as their first
  matching capture and they can swap in a later one.
- Album photos are visible to every logged-in user who has that species
  revealed, ranked by likes in the species gallery. How precisely others see
  where it was taken depends on the animal's rarity (see app/places.py).
- The news feed lists everyone's newest album photos, unless they opted out.
  Animals the viewer hasn't unlocked show as a mystery with no photo.
"""

from __future__ import annotations

import math
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy import and_, delete, func, or_, select
from sqlalchemy.orm import Session

from . import places
from .auth import current_user
from .db import get_db
from .models import AlbumPhoto, Badge, Capture, Friendship, PhotoLike, Species, User
from .schemas import (AlbumOut, AlbumPick, FeedOut, FriendOut, FriendRequestIn, FriendsOut,
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


def species_out(s: Species, revealed: bool) -> SpeciesOut:
    if revealed:
        return SpeciesOut(number=s.id, slug=s.slug, common_name=s.common_name,
                          scientific_name=s.scientific_name, category=s.category,
                          rarity=s.rarity, revealed=True)
    return SpeciesOut(number=s.id, slug=None, common_name=None, scientific_name=None,
                      category=s.category, rarity=s.rarity, revealed=False)


def find_species(db: Session, key: str) -> Species:
    """Look a species up by its number (works while hidden) or its slug."""
    s = db.get(Species, int(key)) if key.isdigit() else db.scalar(
        select(Species).where(Species.slug == key))
    if not s:
        raise HTTPException(404, "Unknown species")
    return s


def photo_out(p: AlbumPhoto, viewer: User, friends: set[int], likes: int, liked: bool,
              revealed: bool = True, rank: int | None = None, show_image: bool = True) -> PhotoOut:
    mine = p.user_id == viewer.id
    c = p.capture
    loc = places.for_viewer(c.latitude, c.longitude, p.species.rarity, mine, p.user_id in friends)
    return PhotoOut(
        id=p.id, url=get_storage().url(c.image_path) if show_image else None,
        username=p.user.username, species=species_out(p.species, revealed),
        taken_on=(c.taken_at or c.created_at).date(), caught_at=c.created_at,
        latitude=loc.latitude, longitude=loc.longitude, location_precise=loc.precise,
        place=loc.place, like_count=likes, liked_by_me=liked, is_mine=mine,
        by_friend=p.user_id in friends, rank=rank)


def _like_info(db: Session, photo_ids: list[int], viewer_id: int) -> tuple[dict[int, int], set[int]]:
    if not photo_ids:
        return {}, set()
    counts = dict(db.execute(select(PhotoLike.photo_id, func.count()).where(
        PhotoLike.photo_id.in_(photo_ids)).group_by(PhotoLike.photo_id)).all())
    mine = set(db.scalars(select(PhotoLike.photo_id).where(
        PhotoLike.photo_id.in_(photo_ids), PhotoLike.user_id == viewer_id)))
    return counts, mine


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


# --- albums -----------------------------------------------------------------

def _album(db: Session, owner: User, viewer: User) -> AlbumOut:
    friends = friend_ids(db, viewer.id)
    revealed = revealed_species_ids(db, viewer)
    photos = db.scalars(select(AlbumPhoto).where(AlbumPhoto.user_id == owner.id)
                        .order_by(AlbumPhoto.species_id)).all()
    counts, liked = _like_info(db, [p.id for p in photos], viewer.id)
    caught = db.scalar(select(func.count()).select_from(Badge).where(Badge.user_id == owner.id))
    total = db.scalar(select(func.count()).select_from(Species))
    return AlbumOut(username=owner.username, caught=caught, total=total, photos=[
        photo_out(p, viewer, friends, counts.get(p.id, 0), p.id in liked, p.species_id in revealed)
        for p in photos])


@router.get("/me/album", response_model=AlbumOut)
def my_album(user: User = Depends(current_user), db: Session = Depends(get_db)):
    return _album(db, user, user)


@router.get("/users/{username}/album", response_model=AlbumOut)
def user_album(username: str, user: User = Depends(current_user), db: Session = Depends(get_db)):
    owner = db.scalar(select(User).where(User.username == username))
    if not owner:
        raise HTTPException(404, "No such user")
    if owner.id != user.id and owner.id not in friend_ids(db, user.id):
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Only friends can see each other's albums")
    return _album(db, owner, user)


@router.put("/me/album/{species_key}", response_model=PhotoOut)
def set_album_photo(species_key: str, body: AlbumPick, user: User = Depends(current_user),
                    db: Session = Depends(get_db)):
    """Swap your album photo for a species to another of your captures of it.
    Likes belong to the old picture, so they are cleared."""
    s = find_species(db, species_key)
    capture = db.get(Capture, body.capture_id)
    if not capture or capture.user_id != user.id or capture.species_id != s.id:
        raise HTTPException(400, "That capture isn't one of your catches of this species")
    photo = db.scalar(select(AlbumPhoto).where(AlbumPhoto.user_id == user.id,
                                               AlbumPhoto.species_id == s.id))
    if photo is None:
        photo = AlbumPhoto(user_id=user.id, species_id=s.id, capture_id=capture.id)
        db.add(photo)
    elif photo.capture_id != capture.id:
        db.execute(delete(PhotoLike).where(PhotoLike.photo_id == photo.id))
        photo.capture_id = capture.id
    db.commit()
    db.refresh(photo)
    return photo_out(photo, user, friend_ids(db, user.id), 0, False)


@router.delete("/me/album/{species_key}", status_code=204)
def remove_album_photo(species_key: str, user: User = Depends(current_user),
                       db: Session = Depends(get_db)):
    """Take your photo out of your album and the gallery. You keep the badge."""
    s = find_species(db, species_key)
    photo = db.scalar(select(AlbumPhoto).where(AlbumPhoto.user_id == user.id,
                                               AlbumPhoto.species_id == s.id))
    if photo:
        db.execute(delete(PhotoLike).where(PhotoLike.photo_id == photo.id))
        db.delete(photo)
        db.commit()
    return Response(status_code=204)


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
                            "Catch this animal, or have a friend catch it, to see its photos")
    friends = friend_ids(db, user.id)
    likes = (select(PhotoLike.photo_id, func.count().label("n"))
             .group_by(PhotoLike.photo_id).subquery())
    n = func.coalesce(likes.c.n, 0)
    q = (select(AlbumPhoto, n).outerjoin(likes, likes.c.photo_id == AlbumPhoto.id)
         .where(AlbumPhoto.species_id == s.id))
    if scope == "friends":
        q = q.where(AlbumPhoto.user_id.in_(friends | {user.id}))
    total = db.scalar(select(func.count()).select_from(q.subquery()))
    order = ((n.desc(), AlbumPhoto.created_at, AlbumPhoto.id) if sort == "top"
             else (AlbumPhoto.created_at.desc(), AlbumPhoto.id.desc()))
    rows = db.execute(q.order_by(*order).limit(limit).offset(offset)).all()
    _, liked = _like_info(db, [p.id for p, _ in rows], user.id)
    return GalleryOut(species=species_out(s, True), scope=scope, sort=sort, total=total, photos=[
        photo_out(p, user, friends, count, p.id in liked,
                  rank=offset + i + 1 if sort == "top" else None)
        for i, (p, count) in enumerate(rows)])


@router.get("/feed", response_model=FeedOut)
def news_feed(scope: Literal["near", "all", "friends"] = "all",
              lat: float | None = Query(None, ge=-90, le=90),
              lon: float | None = Query(None, ge=-180, le=180),
              radius_km: float = Query(50, ge=places.MIN_RADIUS_KM, le=500),
              limit: int = Query(20, ge=1, le=50), before: int | None = Query(None, ge=1),
              user: User = Depends(current_user), db: Session = Depends(get_db)):
    """Newest catches first: each album photo, ordered by when it was caught.

    scope=near (needs lat/lon, the viewer's position) keeps catches within
    radius_km. Distances use each catch's blurred position, not its exact
    GPS, so the filter can't be used to pinpoint anyone (see places.py).
    Players who turned off show_in_feed are left out (except to themselves)."""
    if scope == "near" and (lat is None or lon is None):
        raise HTTPException(400, "scope=near needs lat and lon")
    friends = friend_ids(db, user.id)
    revealed = revealed_species_ids(db, user)
    q = (select(AlbumPhoto).join(Capture, Capture.id == AlbumPhoto.capture_id)
         .join(User, User.id == AlbumPhoto.user_id)
         .where(or_(User.show_in_feed.is_(None), User.show_in_feed, User.id == user.id)))
    if scope == "friends":
        q = q.where(AlbumPhoto.user_id.in_(friends | {user.id}))
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
    return FeedOut(scope=scope, next_before=rows[-1].capture_id if more else None, photos=[
        photo_out(p, user, friends, counts.get(p.id, 0), p.id in liked,
                  revealed=p.species_id in revealed, show_image=p.species_id in revealed)
        for p in rows])


@router.patch("/me/settings")
def update_settings(body: SettingsIn, user: User = Depends(current_user),
                    db: Session = Depends(get_db)):
    if body.show_in_feed is not None:
        user.show_in_feed = body.show_in_feed
    db.commit()
    return {"show_in_feed": user.show_in_feed is not False}


def _visible_photo(db: Session, photo_id: int, user: User) -> AlbumPhoto:
    photo = db.get(AlbumPhoto, photo_id)
    if not photo or photo.species_id not in revealed_species_ids(db, user):
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


def _user_by_name(db: Session, username: str) -> User:
    other = db.scalar(select(User).where(User.username == username.strip()))
    if not other:
        raise HTTPException(404, "No user with that username")
    return other


@router.get("/friends", response_model=FriendsOut)
def list_friends(user: User = Depends(current_user), db: Session = Depends(get_db)):
    rows = db.scalars(select(Friendship).where(or_(Friendship.requester_id == user.id,
                                                   Friendship.addressee_id == user.id))).all()
    ids = {f.requester_id if f.addressee_id == user.id else f.addressee_id for f in rows}
    caught = dict(db.execute(select(Badge.user_id, func.count()).where(Badge.user_id.in_(ids))
                             .group_by(Badge.user_id)).all()) if ids else {}
    out = FriendsOut(friends=[], incoming=[], outgoing=[])
    for f in sorted(rows, key=lambda f: f.created_at):
        other = f.requester if f.addressee_id == user.id else f.addressee
        entry = FriendOut(username=other.username, caught=caught.get(other.id, 0) if f.accepted else 0,
                          since=f.created_at)
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
    """Ask someone to be friends. If they already asked you, you're friends now."""
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
        db.add(Friendship(requester_id=user.id, addressee_id=other.id))
    db.commit()
    return {"status": "friends" if f else "requested"}


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
