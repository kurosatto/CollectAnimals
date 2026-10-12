import csv
import io
import time
import uuid
from contextlib import asynccontextmanager
from datetime import datetime
from pathlib import Path

from fastapi import Depends, FastAPI, File, Form, HTTPException, UploadFile, status
from fastapi.responses import FileResponse
from fastapi.security import OAuth2PasswordRequestForm
from PIL import Image, ImageOps, UnidentifiedImageError
from sqlalchemy import func, or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from . import classifier as clf
from . import dex
from . import places, social
from .auth import create_token, current_user, hash_password, optional_user, verify_password
from .config import settings
from .db import Base, SessionLocal, add_missing_columns, engine, get_db
from .models import AlbumPhoto, Badge, Capture, PhotoLike, Species, User
from .schemas import (CaptureOut, ChoiceOut, CollectionEntry, CollectionOut, DexOut, HotspotOut, HotspotSpecies,
                      PickIn, PredictionOut, RegisterIn, SpeciesOut, TokenOut, UserOut)
from .social import find_species, friend_ids, revealed_species_ids, species_out
from .storage import get_storage

STATIC_DIR = Path(__file__).parent / "static"


def seed_species(db: Session, csv_path: Path) -> None:
    """Upsert species from the CSV so editing the list doesn't need a migration."""
    existing = {s.slug: s for s in db.scalars(select(Species))}
    with open(csv_path, newline="", encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            s = existing.get(row["slug"]) or Species(slug=row["slug"])
            s.common_name = row["common_name"]
            s.scientific_name = row["scientific_name"]
            s.category = row["category"]
            s.rarity = row["rarity"]
            db.add(s)
    db.commit()


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(engine)
    add_missing_columns()
    get_storage()
    with SessionLocal() as db:
        seed_species(db, settings.species_csv)
    dex.load(settings.details_csv, settings.ranges_json, settings.hotspots_json)
    places.load(settings.places_json)
    if clf.get_classifier() is None:
        clf.load_classifier(settings.model_path)
    yield


app = FastAPI(title="CollectAnimals", lifespan=lifespan,
              **({"docs_url": None, "redoc_url": None, "openapi_url": None} if settings.public else {}))

# Failed logins per account in the last LOGIN_WINDOW seconds; slows password guessing.
LOGIN_WINDOW, LOGIN_MAX_FAILURES = 300, 10
_failed_logins: dict[str, list[float]] = {}
app.include_router(social.router)


@app.get("/", include_in_schema=False)
def index():
    return FileResponse(STATIC_DIR / "index.html")


@app.get("/sprites/{name}.png", include_in_schema=False)
def sprite(name: str):
    """Pixel-art sprites: `{slug}.png` in colour, `{slug}_silhouette.png` until caught."""
    slug = name.removesuffix("_silhouette")
    path = settings.sprites_dir / f"{name}.png"
    if not slug.replace("_", "").isalnum() or not path.is_file():
        raise HTTPException(status.HTTP_404_NOT_FOUND, "No such sprite")
    return FileResponse(path, media_type="image/png", headers={"Cache-Control": "public, max-age=86400"})


@app.get("/health")
def health():
    return {"ok": True, "model_loaded": clf.get_classifier() is not None,
            "model_error": None if settings.public else clf.classifier_status()}


# --- auth -------------------------------------------------------------------

@app.post("/auth/register", response_model=TokenOut, status_code=201)
def register(body: RegisterIn, db: Session = Depends(get_db)):
    taken = db.scalar(select(User).where(or_(User.email == body.email.lower(),
                                             User.username == body.username)))
    if taken:
        raise HTTPException(status.HTTP_409_CONFLICT, "Email or username already registered")
    user = User(email=body.email.lower(), username=body.username,
                password_hash=hash_password(body.password))
    db.add(user)
    try:
        db.commit()
    except IntegrityError:
        raise HTTPException(status.HTTP_409_CONFLICT, "Email or username already registered")
    return TokenOut(access_token=create_token(user.id))


@app.post("/auth/login", response_model=TokenOut)
def login(form: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    """Log in with email or username (sent in the OAuth2 `username` field)."""
    ident = form.username.strip()
    now = time.monotonic()
    recent = [t for t in _failed_logins.get(ident.lower(), []) if now - t < LOGIN_WINDOW]
    if len(recent) >= LOGIN_MAX_FAILURES:
        raise HTTPException(status.HTTP_429_TOO_MANY_REQUESTS,
                            "Too many failed logins. Try again in a few minutes.")
    user = db.scalar(select(User).where(or_(User.email == ident.lower(), User.username == ident)))
    if not user or not verify_password(form.password, user.password_hash):
        _failed_logins[ident.lower()] = recent + [now]
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Wrong email/username or password")
    _failed_logins.pop(ident.lower(), None)
    return TokenOut(access_token=create_token(user.id))


@app.get("/me", response_model=UserOut)
def me(user: User = Depends(current_user)):
    return user


# --- species ----------------------------------------------------------------

# Species are looked up by number or slug. Names stay hidden until the viewer
# or one of their friends has caught the species (see app/social.py).

@app.get("/species", response_model=list[SpeciesOut])
def list_species(user: User | None = Depends(optional_user), db: Session = Depends(get_db)):
    revealed = revealed_species_ids(db, user)
    return [species_out(s, s.id in revealed) for s in db.scalars(select(Species).order_by(Species.id))]


@app.get("/species/{key}", response_model=SpeciesOut)
def get_species(key: str, user: User | None = Depends(optional_user), db: Session = Depends(get_db)):
    s = find_species(db, key)
    return species_out(s, s.id in revealed_species_ids(db, user))


@app.get("/map/california")
def california_outline():
    """Outline rings ([[lon, lat], ...]) for drawing range maps."""
    path = settings.species_csv.parent / "california_outline.json"
    if not path.exists():
        raise HTTPException(404, "No outline")
    return FileResponse(path, media_type="application/json")


@app.get("/species/{key}/dex", response_model=DexOut)
def get_dex_entry(key: str, user: User | None = Depends(optional_user), db: Session = Depends(get_db)):
    """Size, weight, active time, hotspot parks and the sighting map are hints,
    so they show even while the name is hidden. The where-to-find and spotting
    tips can name the animal, so they wait until it's revealed. The fun fact
    unlocks when you catch the species yourself."""
    s = find_species(db, key)
    d = dex.details(s.slug)
    revealed = s.id in revealed_species_ids(db, user)
    caught = user is not None and db.scalar(select(Badge.id).where(
        Badge.user_id == user.id, Badge.species_id == s.id)) is not None
    return DexOut(species=species_out(s, revealed), size=d.get("size"), weight=d.get("weight"),
                  fun_fact=d.get("fun_fact") if caught else None,
                  where_to_find=d.get("where_to_find") if revealed else None,
                  active_time=d.get("active_time"),
                  spotting_tip=d.get("spotting_tip") if revealed else None,
                  hotspots=dex.hotspots_for(s.slug), range=dex.range_for(s.slug))


@app.get("/hotspots", response_model=list[HotspotOut])
def list_hotspots(user: User | None = Depends(optional_user), db: Session = Depends(get_db)):
    """Parks and the listed species seen there, parks with the most species first.
    Species the viewer hasn't unlocked are listed without their names."""
    by_slug = {s.slug: s for s in db.scalars(select(Species))}
    revealed = revealed_species_ids(db, user)
    out = []
    for p in dex.hotspots():
        species = []
        for sp in p["species"]:
            s = by_slug.get(sp["slug"])
            if s is None:
                continue
            shown = s.id in revealed
            species.append(HotspotSpecies(number=s.id, slug=s.slug if shown else None,
                                          common_name=s.common_name if shown else None,
                                          rarity=s.rarity, observations=sp["observations"]))
        out.append(HotspotOut(id=p["id"], name=p["name"], lat=p["lat"], lon=p["lon"],
                              blurb=p.get("blurb", ""), species=species))
    return sorted(out, key=lambda h: -len(h.species))


# --- captures & collection --------------------------------------------------

def _read_image(data: bytes) -> Image.Image:
    try:
        im = Image.open(io.BytesIO(data))
        im.load()
    except (UnidentifiedImageError, OSError):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Not a valid image")
    return im


def _exif_meta(im: Image.Image) -> tuple[float | None, float | None, datetime | None]:
    """GPS position and capture time from the photo's EXIF, if the phone kept them."""
    lat = lon = taken = None
    try:
        exif = im.getexif()
        gps = exif.get_ifd(0x8825)
        if 2 in gps and 4 in gps:
            def deg(v):
                return float(v[0]) + float(v[1]) / 60 + float(v[2]) / 3600
            lat = deg(gps[2]) * (-1 if gps.get(1) == "S" else 1)
            lon = deg(gps[4]) * (-1 if gps.get(3) == "W" else 1)
        stamp = exif.get_ifd(0x8769).get(36867) or exif.get(306)
        if stamp:
            taken = datetime.strptime(str(stamp).strip("\x00 ")[:19], "%Y:%m:%d %H:%M:%S")
    except (ValueError, TypeError, ZeroDivisionError, KeyError, IndexError):
        pass
    if lat is not None and not (-90 <= lat <= 90 and -180 <= lon <= 180):
        lat = lon = None
    return lat, lon, taken


@app.post("/captures", response_model=CaptureOut, status_code=201)
async def create_capture(photo: UploadFile = File(...),
                         latitude: float | None = Form(None, ge=-90, le=90),
                         longitude: float | None = Form(None, ge=-180, le=180),
                         user: User = Depends(current_user), db: Session = Depends(get_db)):
    """Identify a photo. latitude/longitude are where it was taken (the web page
    sends the phone's location); without them we fall back to the photo's EXIF GPS."""
    model = clf.get_classifier()
    if model is None:
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE,
                            clf.classifier_status() or "Model not loaded")

    max_bytes = settings.max_upload_mb * 1024 * 1024
    data = await photo.read(max_bytes + 1)
    if len(data) > max_bytes:
        raise HTTPException(status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                            f"Photo larger than {settings.max_upload_mb} MB")
    raw = _read_image(data)
    exif_lat, exif_lon, taken_at = _exif_meta(raw)
    if latitude is None or longitude is None:
        latitude, longitude = exif_lat, exif_lon
    # Phone photos are often rotated via EXIF; apply it before classifying.
    image = ImageOps.exif_transpose(raw).convert("RGB")

    # Five guesses: the first three are shown, all five are offered if the
    # player says the model got it wrong.
    preds = model.predict(image, k=5)
    top = preds[0]
    species_by_slug = {s.slug: s for s in db.scalars(
        select(Species).where(Species.slug.in_([p.label for p in preds])))}
    species = species_by_slug.get(top.label)
    matched = species is not None and top.probability >= settings.match_threshold

    # Re-encode before saving: normalizes the format and strips EXIF (incl. GPS).
    name = f"{uuid.uuid4().hex}.jpg"
    image.thumbnail((1600, 1600))
    buf = io.BytesIO()
    image.save(buf, "JPEG", quality=88)
    get_storage().put(name, buf.getvalue(), "image/jpeg")

    capture = Capture(user_id=user.id, species_id=species.id if matched else None,
                      image_path=name, predicted_label=top.label, confidence=top.probability,
                      latitude=latitude, longitude=longitude, taken_at=taken_at,
                      top_labels=",".join(p.label for p in preds if p.label in species_by_slug))
    db.add(capture)
    db.flush()

    new_badge = False
    if matched:
        badge = db.scalar(select(Badge).where(Badge.user_id == user.id,
                                              Badge.species_id == species.id))
        if badge:
            badge.capture_count += 1
        else:
            db.add(Badge(user_id=user.id, species_id=species.id, first_capture_id=capture.id))
            new_badge = True
    album_photo = social.ensure_album_photo(db, capture) if matched else None
    db.commit()

    # Don't give away names the player hasn't unlocked yet.
    revealed = revealed_species_ids(db, user)
    if matched:
        message = (f"You caught a {species.common_name}! New badge unlocked."
                   if new_badge else f"Another {species.common_name} for your collection.")
        if album_photo:
            message += " It's now in your album."
    elif species is not None and species.id in revealed:
        message = f"Might be a {species.common_name}, but we're not sure. Try a clearer photo!"
    elif species is not None:
        message = "Might be an animal you haven't discovered yet, but we're not sure. Try a clearer photo!"
    else:
        message = "We couldn't match this to any animal in the California collection."

    return CaptureOut(
        capture_id=capture.id,
        matched=matched,
        species=species_out(species, True) if matched else None,
        confidence=round(top.probability, 4),
        new_badge=new_badge,
        message=message,
        top_predictions=[
            PredictionOut(label=p.label, probability=round(p.probability, 4),
                          common_name=species_by_slug[p.label].common_name)
            if p.label in species_by_slug and species_by_slug[p.label].id in revealed
            else PredictionOut(label="other" if p.label not in species_by_slug else "hidden",
                               probability=round(p.probability, 4), common_name=None)
            for p in preds[:3]
        ],
        album_photo_id=album_photo.id if album_photo else None,
        choices=[ChoiceOut(slug=p.label, common_name=species_by_slug[p.label].common_name,
                           probability=round(p.probability, 4))
                 for p in preds if p.label in species_by_slug],
    )


def _unassign_capture(db: Session, capture: Capture) -> None:
    """Take back the badge and album photo a capture earned, e.g. when the
    player says the model named the wrong animal."""
    old = capture.species_id
    if old is None:
        return
    capture.species_id = None
    db.flush()
    others = db.scalars(select(Capture).where(Capture.user_id == capture.user_id,
                                              Capture.species_id == old).order_by(Capture.id)).all()
    badge = db.scalar(select(Badge).where(Badge.user_id == capture.user_id, Badge.species_id == old))
    if badge:
        if not others:
            db.delete(badge)
        else:
            badge.capture_count = max(1, badge.capture_count - 1)
            if badge.first_capture_id == capture.id:
                badge.first_capture_id = others[0].id
    photo = db.scalar(select(AlbumPhoto).where(AlbumPhoto.capture_id == capture.id))
    if photo:
        for like in db.scalars(select(PhotoLike).where(PhotoLike.photo_id == photo.id)):
            db.delete(like)
        db.delete(photo)
        db.flush()
        if others:
            social.ensure_album_photo(db, others[-1])


@app.post("/captures/{capture_id}/pick", response_model=CaptureOut)
def pick_capture_species(capture_id: int, body: PickIn, user: User = Depends(current_user),
                         db: Session = Depends(get_db)):
    """'Not this animal?': the player names the animal themselves, from the
    model's top guesses (or "none"). We trust their pick and award the badge."""
    capture = db.get(Capture, capture_id)
    if capture is None or capture.user_id != user.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Capture not found")

    if body.label == "none":
        _unassign_capture(db, capture)
        capture.user_picked = True
        db.commit()
        return CaptureOut(capture_id=capture.id, matched=False, species=None, confidence=capture.confidence,
                          new_badge=False, message="Okay, this photo doesn't count for any animal.",
                          top_predictions=[])

    allowed = capture.top_labels.split(",") if capture.top_labels else None
    if allowed is not None and body.label not in allowed:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Pick one of the suggested animals")
    species = db.scalar(select(Species).where(Species.slug == body.label))
    if species is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Unknown species")

    new_badge = False
    album_photo = None
    if capture.species_id != species.id:
        _unassign_capture(db, capture)
        capture.species_id = species.id
        capture.user_picked = True
        badge = db.scalar(select(Badge).where(Badge.user_id == user.id, Badge.species_id == species.id))
        if badge:
            badge.capture_count += 1
        else:
            db.add(Badge(user_id=user.id, species_id=species.id, first_capture_id=capture.id))
            new_badge = True
        album_photo = social.ensure_album_photo(db, capture)
    db.commit()

    message = (f"Got it: a {species.common_name}! New badge unlocked." if new_badge
               else f"Got it: another {species.common_name} for your collection.")
    if album_photo:
        message += " It's now in your album."
    return CaptureOut(capture_id=capture.id, matched=True, species=species_out(species, True),
                      confidence=capture.confidence, new_badge=new_badge, message=message,
                      top_predictions=[], album_photo_id=album_photo.id if album_photo else None)


@app.get("/me/collection", response_model=CollectionOut)
def my_collection(user: User = Depends(current_user), db: Session = Depends(get_db)):
    badges = {b.species_id: b for b in db.scalars(select(Badge).where(Badge.user_id == user.id))}
    friends = friend_ids(db, user.id)
    friends_caught = dict(db.execute(
        select(Badge.species_id, func.count()).where(Badge.user_id.in_(friends))
        .group_by(Badge.species_id)).all()) if friends else {}
    photos = dict(db.execute(select(AlbumPhoto.species_id, Capture.image_path)
                             .join(Capture, Capture.id == AlbumPhoto.capture_id)
                             .where(AlbumPhoto.user_id == user.id)).all())
    storage = get_storage()
    entries = []
    for s in db.scalars(select(Species).order_by(Species.id)):
        b = badges.get(s.id)
        entries.append(CollectionEntry(
            species=species_out(s, b is not None or friends_caught.get(s.id, 0) > 0),
            caught=b is not None, capture_count=b.capture_count if b else 0,
            earned_at=b.earned_at if b else None, friends_caught=friends_caught.get(s.id, 0),
            photo_url=storage.url(photos[s.id]) if s.id in photos else None))
    return CollectionOut(caught=len(badges), total=len(entries), entries=entries)
