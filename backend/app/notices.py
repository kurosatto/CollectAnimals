"""Notifications: friend requests, likes and comments on your photos.

Two ways to hear about them, neither needing a paid service:

- Web Push, for the website and the installed web app. The browser's own push
  service (Google's for Chrome, Mozilla's, Apple's) carries an encrypted message
  from this server to the phone, even when the site is closed. The server signs
  them with its own VAPID key, made on first start and kept in
  backend/.vapid_private.pem, so subscriptions survive restarts.
- GET /me/activity, which the Android app and open web pages poll for likes and
  comments since their last check.

Likes are batched: a photo sends at most one like notification every
LIKE_PUSH_GAP, and each one replaces the last on the phone (same tag), so a
popular photo doesn't buzz for every like.
"""
from __future__ import annotations

import base64
import json
import logging
import os
import struct
import threading
import time
import urllib.error
import urllib.request
from datetime import datetime, timedelta, timezone
from urllib.parse import urlparse

import jwt
from cryptography.hazmat.primitives import hashes, hmac, serialization
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from fastapi import APIRouter, Depends, HTTPException, Query, Response
from pydantic import BaseModel, Field
from sqlalchemy import delete, func, select
from sqlalchemy.orm import Session

from .auth import current_user
from .config import ROOT
from .db import SessionLocal, get_db
from .models import AlbumPhoto, PhotoComment, PhotoLike, PushSubscription, Species, User

log = logging.getLogger(__name__)
router = APIRouter()

LIKE_PUSH_GAP = 600  # seconds between like notifications for one photo
SUBJECT = os.getenv("VAPID_SUBJECT", "mailto:hello@captureanimals.app")


# --- VAPID key -----------------------------------------------------------------

_key: ec.EllipticCurvePrivateKey | None = None


def vapid_key() -> ec.EllipticCurvePrivateKey:
    """This server's push signing key: VAPID_PRIVATE_KEY_FILE, else backend/.vapid_private.pem,
    made the first time it's needed."""
    global _key
    if _key is None:
        path = os.getenv("VAPID_PRIVATE_KEY_FILE") or str(ROOT / "backend" / ".vapid_private.pem")
        if not os.path.exists(path):
            pem = ec.generate_private_key(ec.SECP256R1()).private_bytes(
                serialization.Encoding.PEM, serialization.PrivateFormat.PKCS8, serialization.NoEncryption())
            with open(path, "wb") as f:
                f.write(pem)
        with open(path, "rb") as f:
            _key = serialization.load_pem_private_key(f.read(), password=None)
    return _key


def _raw_public(key) -> bytes:
    return key.public_key().public_bytes(serialization.Encoding.X962, serialization.PublicFormat.UncompressedPoint)


def b64url(b: bytes) -> str:
    return base64.urlsafe_b64encode(b).rstrip(b"=").decode()


def unb64url(s: str) -> bytes:
    return base64.urlsafe_b64decode(s + "=" * (-len(s) % 4))


# --- Web Push encryption (RFC 8291, aes128gcm) -----------------------------------

def _hmac(key: bytes, data: bytes) -> bytes:
    h = hmac.HMAC(key, hashes.SHA256())
    h.update(data)
    return h.finalize()


def encrypt(payload: bytes, p256dh: str, auth: str, salt: bytes | None = None,
            server_key: ec.EllipticCurvePrivateKey | None = None) -> bytes:
    """Encrypts payload for one browser subscription; returns the request body."""
    ua_public = unb64url(p256dh)
    ua_key = ec.EllipticCurvePublicKey.from_encoded_point(ec.SECP256R1(), ua_public)
    server_key = server_key or ec.generate_private_key(ec.SECP256R1())
    as_public = _raw_public(server_key)
    shared = server_key.exchange(ec.ECDH(), ua_key)
    ikm = _hmac(_hmac(unb64url(auth), shared), b"WebPush: info\x00" + ua_public + as_public + b"\x01")
    salt = salt or os.urandom(16)
    prk = _hmac(salt, ikm)
    cek = _hmac(prk, b"Content-Encoding: aes128gcm\x00\x01")[:16]
    nonce = _hmac(prk, b"Content-Encoding: nonce\x00\x01")[:12]
    body = AESGCM(cek).encrypt(nonce, payload + b"\x02", None)
    return salt + struct.pack("!IB", 4096, len(as_public)) + as_public + body


def _vapid_header(endpoint: str) -> str:
    u = urlparse(endpoint)
    token = jwt.encode({"aud": f"{u.scheme}://{u.netloc}", "exp": int(time.time()) + 12 * 3600, "sub": SUBJECT},
                       vapid_key(), algorithm="ES256")
    return f"vapid t={token}, k={b64url(_raw_public(vapid_key()))}"


def post(sub: PushSubscription, payload: dict) -> int:
    """Sends one push; returns the push service's HTTP status (0 if unreachable)."""
    req = urllib.request.Request(sub.endpoint, method="POST",
                                 data=encrypt(json.dumps(payload).encode(), sub.p256dh, sub.auth), headers={
        "Content-Encoding": "aes128gcm", "Content-Type": "application/octet-stream",
        "TTL": "86400", "Urgency": "normal", "Authorization": _vapid_header(sub.endpoint)})
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            return r.status
    except urllib.error.HTTPError as e:
        return e.code
    except OSError:
        return 0


def run(job) -> None:
    """Sends in the background so a like or comment never waits on a push service.
    (Tests swap this for a direct call.)"""
    threading.Thread(target=job, daemon=True).start()


def notify(user_id: int, title: str, body: str, tag: str, url: str) -> None:
    """Pushes to every browser the player turned notifications on in."""
    with SessionLocal() as db:
        subs = db.scalars(select(PushSubscription).where(PushSubscription.user_id == user_id)).all()
    if not subs:
        return
    payload = {"title": title, "body": body, "tag": tag, "url": url}

    def job():
        gone = [s.id for s in subs if post(s, payload) in (404, 410)]
        if gone:  # the browser unsubscribed or the subscription expired
            with SessionLocal() as db:
                db.execute(delete(PushSubscription).where(PushSubscription.id.in_(gone)))
                db.commit()
    run(job)


# --- what triggers a notification ------------------------------------------------

_last_like_push: dict[int, float] = {}


def _species_name(db: Session, photo: AlbumPhoto) -> str:
    return db.get(Species, photo.species_id).common_name


def friend_request(other: User, sender: User) -> None:
    notify(other.id, "Friend request", f"{sender.username} sent you a friend request",
           "friends", "/#friends")


def friend_accepted(requester: User, accepter: User) -> None:
    notify(requester.id, "New friend", f"{accepter.username} accepted your friend request",
           "friends", "/#friends")


def liked(db: Session, photo: AlbumPhoto, liker: User) -> None:
    now = time.monotonic()
    if now - _last_like_push.get(photo.id, -LIKE_PUSH_GAP) < LIKE_PUSH_GAP:
        return
    _last_like_push[photo.id] = now
    since = datetime.now(timezone.utc) - timedelta(seconds=LIKE_PUSH_GAP)
    others = (db.scalar(select(func.count()).select_from(PhotoLike).where(
        PhotoLike.photo_id == photo.id, PhotoLike.created_at >= since)) or 1) - 1
    who = liker.username + (f" and {others} other{'s' if others > 1 else ''}" if others > 0 else "")
    notify(photo.user_id, "New like", f"{who} liked your {_species_name(db, photo)} photo",
           f"like-{photo.id}", "/#photos")


def commented(db: Session, photo: AlbumPhoto, commenter: User, text: str) -> None:
    if commenter.id == photo.user_id:
        return
    short = text if len(text) <= 80 else text[:79] + "…"
    notify(photo.user_id, "New comment", f"{commenter.username} on your {_species_name(db, photo)}: {short}",
           f"comment-{photo.id}", "/#photos")


# --- endpoints -----------------------------------------------------------------------

class SubscriptionIn(BaseModel):
    endpoint: str = Field(max_length=1000, pattern=r"^https://")
    p256dh: str = Field(max_length=200)
    auth: str = Field(max_length=100)


class EndpointIn(BaseModel):
    endpoint: str = Field(max_length=1000)


@router.get("/push/key")
def push_key():
    """The public key browsers need to subscribe (applicationServerKey)."""
    return {"key": b64url(_raw_public(vapid_key()))}


@router.post("/push/subscribe", status_code=204)
def subscribe(body: SubscriptionIn, user: User = Depends(current_user), db: Session = Depends(get_db)):
    try:
        ec.EllipticCurvePublicKey.from_encoded_point(ec.SECP256R1(), unb64url(body.p256dh))
        if len(unb64url(body.auth)) != 16:
            raise ValueError
    except ValueError:
        raise HTTPException(422, "That isn't a push subscription")
    sub = db.scalar(select(PushSubscription).where(PushSubscription.endpoint == body.endpoint))
    if sub is None:
        sub = PushSubscription(endpoint=body.endpoint)
        db.add(sub)
    # A browser follows whoever logged in on it last.
    sub.user_id, sub.p256dh, sub.auth = user.id, body.p256dh, body.auth
    db.commit()
    return Response(status_code=204)


@router.post("/push/unsubscribe", status_code=204)
def unsubscribe(body: EndpointIn, user: User = Depends(current_user), db: Session = Depends(get_db)):
    db.execute(delete(PushSubscription).where(PushSubscription.endpoint == body.endpoint,
                                              PushSubscription.user_id == user.id))
    db.commit()
    return Response(status_code=204)


@router.get("/me/activity")
def activity(since: datetime | None = Query(None), user: User = Depends(current_user),
             db: Session = Depends(get_db)):
    """Likes and comments on your photos after `since` (likes grouped by photo).
    Pass back `now` as the next `since`; without one you just get `now`."""
    now = datetime.now(timezone.utc)
    out = {"now": now.isoformat(), "likes": [], "comments": []}
    if since is None:
        return out
    since = since.astimezone(timezone.utc) if since.tzinfo else since.replace(tzinfo=timezone.utc)
    from .social import blocked_ids
    blocked = blocked_ids(db, user.id)
    likes = db.execute(
        select(PhotoLike.photo_id, Species.common_name, User.username)
        .join(AlbumPhoto, AlbumPhoto.id == PhotoLike.photo_id).join(Species, Species.id == AlbumPhoto.species_id)
        .join(User, User.id == PhotoLike.user_id)
        .where(AlbumPhoto.user_id == user.id, PhotoLike.created_at > since, PhotoLike.created_at <= now,
               PhotoLike.user_id.not_in(blocked))
        .order_by(PhotoLike.created_at.desc())).all()
    by_photo: dict[int, dict] = {}
    for photo_id, name, who in likes:
        e = by_photo.setdefault(photo_id, {"photo_id": photo_id, "species": name, "count": 0, "usernames": []})
        e["count"] += 1
        if len(e["usernames"]) < 3:
            e["usernames"].append(who)
    out["likes"] = list(by_photo.values())
    comments = db.execute(
        select(PhotoComment, Species.common_name)
        .join(AlbumPhoto, AlbumPhoto.id == PhotoComment.photo_id).join(Species, Species.id == AlbumPhoto.species_id)
        .where(AlbumPhoto.user_id == user.id, PhotoComment.user_id != user.id, PhotoComment.user_id.not_in(blocked),
               PhotoComment.created_at > since, PhotoComment.created_at <= now)
        .order_by(PhotoComment.created_at.desc()).limit(20)).all()
    out["comments"] = [{"photo_id": c.photo_id, "species": name, "username": c.user.username, "body": c.body,
                        "created_at": c.created_at.isoformat()} for c, name in comments]
    return out
