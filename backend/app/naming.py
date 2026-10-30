"""'What was it?': after "None of these" the player can name the animal themselves.

They type and pick from a big text-only list of North American animals plus
broad groups ("Some kind of beetle"), species/animal_names.json, which the web
page and the Android app both bundle so it works offline. The answer is a label
for retraining the identifier, never a badge: a typed name can't be checked,
so it doesn't count in the Field Guide.

If the player turned on "Share photos to teach the game" (off by default), a
small copy of the photo is kept with the label. Turning it off deletes those
copies; the labels (text only) stay.
"""

from __future__ import annotations

import io
import json
import uuid
from datetime import datetime, timedelta, timezone
from functools import lru_cache

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from fastapi.responses import FileResponse
from PIL import Image, ImageOps, UnidentifiedImageError
from pydantic import BaseModel, Field
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from .auth import current_user
from .config import settings
from .db import get_db
from .models import Capture, NamedPhoto, User
from .storage import get_storage

router = APIRouter()

GROUP_PREFIX = "group:"
# Training copies are small: enough to train on, little storage.
TRAINING_SIDE = 512
# Answers per player per day (the offline queue sends several at once).
DAILY_LIMIT = 60
MAX_PHOTO_BYTES = 4 * 1024 * 1024


def names_path():
    return settings.states_json.parent / "animal_names.json"


@lru_cache
def _names() -> dict[str, str]:
    """Every label a player can pick -> its display name."""
    path = names_path()
    if not path.is_file():
        return {}
    data = json.loads(path.read_text(encoding="utf-8"))
    out = {GROUP_PREFIX + g[0]: g[1] for g in data["groups"]}
    for common, sci, _group in data["names"]:
        out.setdefault(sci, common)
    return out


def display_name(label: str) -> str | None:
    return _names().get(label)


@router.get("/species/names")
def animal_names():
    """The name list the pickers search (also bundled in the Android app)."""
    path = names_path()
    if not path.is_file():
        raise HTTPException(status.HTTP_404_NOT_FOUND, "No name list")
    return FileResponse(path, media_type="application/json", headers={"Cache-Control": "public, max-age=86400"})


class NameIn(BaseModel):
    label: str = Field(max_length=96)


class NamedOut(BaseModel):
    label: str
    name: str
    photo_shared: bool
    message: str


def _check(db: Session, user: User, label: str) -> str:
    name = display_name(label)
    if name is None:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Pick a name from the list")
    since = datetime.now(timezone.utc) - timedelta(days=1)
    today = db.scalar(select(func.count()).select_from(NamedPhoto)
                      .where(NamedPhoto.user_id == user.id, NamedPhoto.created_at >= since))
    if today >= DAILY_LIMIT:
        raise HTTPException(status.HTTP_429_TOO_MANY_REQUESTS, "That's plenty for today. Thank you!")
    return name


def _training_copy(data: bytes) -> str | None:
    """Save a small re-encoded copy (no EXIF, so no GPS) and return its storage key."""
    try:
        im = Image.open(io.BytesIO(data))
        if im.width * im.height > 108_000_000:
            return None
        im = ImageOps.exif_transpose(im).convert("RGB")
    except (UnidentifiedImageError, OSError, Image.DecompressionBombError):
        return None
    im.thumbnail((TRAINING_SIDE, TRAINING_SIDE))
    buf = io.BytesIO()
    im.save(buf, "JPEG", quality=85)
    key = f"train_{uuid.uuid4().hex}.jpg"
    get_storage().put(key, buf.getvalue())
    return key


def _message(name: str, shared: bool) -> str:
    return (f"Thanks! You said it's {_a(name)}. " +
            ("Your photo will help teach the game." if shared else "That helps the game learn."))


def _a(name: str) -> str:
    if name.lower().startswith(("some kind of", "some other", "not an", "no animal", "a ", "an ")):
        return name[0].lower() + name[1:]
    return ("an " if name[0].lower() in "aeiou" else "a ") + name


@router.post("/captures/{capture_id}/name", response_model=NamedOut)
def name_capture(capture_id: int, body: NameIn, user: User = Depends(current_user), db: Session = Depends(get_db)):
    """The player names an animal that doesn't count for any badge (after "None
    of these", or a photo the game didn't recognise). One answer per photo; a new
    one replaces it."""
    capture = db.get(Capture, capture_id)
    if capture is None or capture.user_id != user.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Capture not found")
    if capture.species_id is not None:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "This photo already counts for an animal")
    row = db.scalar(select(NamedPhoto).where(NamedPhoto.capture_id == capture.id))
    name = display_name(body.label) if row else _check(db, user, body.label)
    if name is None:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Pick a name from the list")
    if row is None:
        row = NamedPhoto(user_id=user.id, capture_id=capture.id)
        db.add(row)
    row.label = body.label
    row.predicted_label = capture.predicted_label
    row.state = capture.state or user.state
    if user.share_training_photos and row.image_path is None and capture.image_path:
        data = get_storage().get(capture.image_path)
        row.image_path = _training_copy(data) if data else None
    db.commit()
    shared = row.image_path is not None
    return NamedOut(label=row.label, name=name, photo_shared=shared, message=_message(name, shared))


@router.post("/me/named-photos", response_model=NamedOut, status_code=201)
async def name_offline_photo(label: str = Form(..., max_length=96), predicted_label: str | None = Form(None, max_length=64),
                             state: str | None = Form(None, max_length=2), photo: UploadFile | None = File(None),
                             user: User = Depends(current_user), db: Session = Depends(get_db)):
    """An answer the phone saved while offline (the photo never reached the
    server). The photo is kept only if the player shares photos to teach the game."""
    name = _check(db, user, label)
    row = NamedPhoto(user_id=user.id, label=label, predicted_label=predicted_label,
                     state=(state or "").upper() or None)
    if photo is not None and user.share_training_photos:
        data = await photo.read(MAX_PHOTO_BYTES + 1)
        if len(data) <= MAX_PHOTO_BYTES:
            row.image_path = _training_copy(data)
    db.add(row)
    db.commit()
    shared = row.image_path is not None
    return NamedOut(label=label, name=name, photo_shared=shared, message=_message(name, shared))


def forget_photos(db: Session, user_id: int, delete_rows: bool = False) -> None:
    """Delete a player's training copies (when they stop sharing, or delete their
    account). The text labels stay unless delete_rows."""
    storage = get_storage()
    for row in db.scalars(select(NamedPhoto).where(NamedPhoto.user_id == user_id)).all():
        if row.image_path:
            try:
                storage.delete(row.image_path)
            except ValueError:
                pass
            row.image_path = None
        if delete_rows:
            db.delete(row)
    db.flush()
