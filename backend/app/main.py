import csv
import io
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
from . import social
from .auth import create_token, current_user, hash_password, optional_user, verify_password
from .config import settings
from .db import Base, SessionLocal, add_missing_columns, engine, get_db
from .models import AlbumPhoto, Badge, Capture, Species, User
from .schemas import (CaptureOut, CollectionEntry, CollectionOut, DexOut, PredictionOut, RegisterIn,
                      SpeciesOut, TokenOut, UserOut)
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
    dex.load(settings.details_csv, settings.ranges_json)
    if clf.get_classifier() is None:
        clf.load_classifier(settings.model_path)
    yield


app = FastAPI(title="CollectAnimals", lifespan=lifespan)
app.include_router(social.router)


@app.get("/", include_in_schema=False)
def index():
    return FileResponse(STATIC_DIR / "index.html")


@app.get("/health")
def health():
    return {"ok": True, "model_loaded": clf.get_classifier() is not None,
            "model_error": clf.classifier_status()}


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
    user = db.scalar(select(User).where(or_(User.email == ident.lower(), User.username == ident)))
    if not user or not verify_password(form.password, user.password_hash):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Wrong email/username or password")
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
    """Size, weight and the sighting map are hints, so they show even while the
    name is hidden. The fun fact unlocks when you catch the species yourself."""
    s = find_species(db, key)
    d = dex.details(s.slug)
    caught = user is not None and db.scalar(select(Badge.id).where(
        Badge.user_id == user.id, Badge.species_id == s.id)) is not None
    return DexOut(species=species_out(s, s.id in revealed_species_ids(db, user)),
                  size=d.get("size"), weight=d.get("weight"),
                  fun_fact=d.get("fun_fact") if caught else None, range=dex.range_for(s.slug))


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

    preds = model.predict(image, k=3)
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
                      latitude=latitude, longitude=longitude, taken_at=taken_at)
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
            for p in preds
        ],
        album_photo_id=album_photo.id if album_photo else None,
    )


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
