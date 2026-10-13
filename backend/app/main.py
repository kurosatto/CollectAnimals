import csv
import io
import time
import uuid
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import Depends, FastAPI, File, HTTPException, UploadFile, status
from fastapi.responses import FileResponse
from fastapi.security import OAuth2PasswordRequestForm
from PIL import Image, ImageOps, UnidentifiedImageError
from sqlalchemy import or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from . import classifier as clf
from . import dex
from .auth import create_token, current_user, hash_password, verify_password
from .config import settings
from .db import Base, SessionLocal, engine, get_db
from .models import Badge, Capture, Species, User
from .schemas import (CaptureOut, CollectionEntry, CollectionOut, DexOut, HotspotOut, HotspotSpecies,
                      PredictionOut, RegisterIn, SpeciesOut, TokenOut, UserOut)

STATIC_DIR = Path(__file__).parent / "static"


RETIRED = "retired"


def seed_species(db: Session, csv_path: Path) -> None:
    """Upsert species from the CSV so editing the list doesn't need a migration.

    Species dropped from the CSV are kept (old captures point at them) but
    marked retired, which hides them from the list, the collection and matching.
    """
    existing = {s.slug: s for s in db.scalars(select(Species))}
    listed = set()
    with open(csv_path, newline="", encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            listed.add(row["slug"])
            s = existing.get(row["slug"]) or Species(slug=row["slug"])
            s.common_name = row["common_name"]
            s.scientific_name = row["scientific_name"]
            s.category = row["category"]
            s.rarity = row["rarity"]
            if s.region == RETIRED:
                s.region = "california"
            db.add(s)
    for slug, s in existing.items():
        if slug not in listed:
            s.region = RETIRED
    db.commit()


def active_species():
    return select(Species).where(Species.region != RETIRED)


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(engine)
    settings.upload_dir.mkdir(parents=True, exist_ok=True)
    with SessionLocal() as db:
        seed_species(db, settings.species_csv)
    dex.load(settings.details_csv, settings.ranges_json, settings.hotspots_json)
    if clf.get_classifier() is None:
        clf.load_classifier(settings.model_path)
    yield


app = FastAPI(title="CollectAnimals", lifespan=lifespan,
              **({"docs_url": None, "redoc_url": None, "openapi_url": None} if settings.public else {}))

# Failed logins per account in the last LOGIN_WINDOW seconds; slows password guessing.
LOGIN_WINDOW, LOGIN_MAX_FAILURES = 300, 10
_failed_logins: dict[str, list[float]] = {}


@app.get("/", include_in_schema=False)
def index():
    return FileResponse(STATIC_DIR / "index.html")


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

@app.get("/species", response_model=list[SpeciesOut])
def list_species(db: Session = Depends(get_db)):
    return db.scalars(active_species().order_by(Species.id)).all()


@app.get("/species/{slug}", response_model=SpeciesOut)
def get_species(slug: str, db: Session = Depends(get_db)):
    s = db.scalar(active_species().where(Species.slug == slug))
    if not s:
        raise HTTPException(404, "Unknown species")
    return s


@app.get("/map/california")
def california_outline():
    """Outline rings ([[lon, lat], ...]) for drawing range maps."""
    path = settings.species_csv.parent / "california_outline.json"
    if not path.exists():
        raise HTTPException(404, "No outline")
    return FileResponse(path, media_type="application/json")


@app.get("/species/{slug}/dex", response_model=DexOut)
def get_dex_entry(slug: str, db: Session = Depends(get_db)):
    s = get_species(slug, db)
    d = dex.details(slug)
    return DexOut(species=SpeciesOut.model_validate(s), size=d.get("size"), weight=d.get("weight"),
                  fun_fact=d.get("fun_fact"), where_to_find=d.get("where_to_find"),
                  active_time=d.get("active_time"), spotting_tip=d.get("spotting_tip"),
                  safety=d.get("safety") or "none", safe_distance=d.get("safe_distance") or None,
                  safety_note=d.get("safety_note") or None,
                  hotspots=dex.hotspots_for(slug), range=dex.range_for(slug))


@app.get("/hotspots", response_model=list[HotspotOut])
def list_hotspots(db: Session = Depends(get_db)):
    """Parks and the listed species seen there, parks with the most species first."""
    by_slug = {s.slug: s for s in db.scalars(active_species())}
    out = []
    for p in dex.hotspots():
        species = [HotspotSpecies(slug=sp["slug"], common_name=by_slug[sp["slug"]].common_name,
                                  rarity=by_slug[sp["slug"]].rarity, observations=sp["observations"])
                   for sp in p["species"] if sp["slug"] in by_slug]
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
    # Phone photos are often rotated via EXIF; apply it before classifying.
    return ImageOps.exif_transpose(im).convert("RGB")


@app.post("/captures", response_model=CaptureOut, status_code=201)
async def create_capture(photo: UploadFile = File(...), user: User = Depends(current_user),
                         db: Session = Depends(get_db)):
    model = clf.get_classifier()
    if model is None:
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE,
                            clf.classifier_status() or "Model not loaded")

    max_bytes = settings.max_upload_mb * 1024 * 1024
    data = await photo.read(max_bytes + 1)
    if len(data) > max_bytes:
        raise HTTPException(status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                            f"Photo larger than {settings.max_upload_mb} MB")
    image = _read_image(data)

    preds = model.predict(image, k=3)
    top = preds[0]
    species_by_slug = {s.slug: s for s in db.scalars(
        active_species().where(Species.slug.in_([p.label for p in preds])))}
    species = species_by_slug.get(top.label)
    matched = species is not None and top.probability >= settings.match_threshold

    # Re-encode before saving: normalizes the format and strips EXIF (incl. GPS).
    name = f"{uuid.uuid4().hex}.jpg"
    image.thumbnail((1600, 1600))
    image.save(settings.upload_dir / name, "JPEG", quality=88)

    capture = Capture(user_id=user.id, species_id=species.id if matched else None,
                      image_path=name, predicted_label=top.label, confidence=top.probability)
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
    db.commit()

    if matched:
        message = (f"You caught a {species.common_name}! New badge unlocked."
                   if new_badge else f"Another {species.common_name} for your collection.")
    elif species is not None:
        message = f"Might be a {species.common_name}, but we're not sure. Try a clearer photo!"
    else:
        message = "We couldn't match this to any animal in the California collection."

    return CaptureOut(
        capture_id=capture.id,
        matched=matched,
        species=SpeciesOut.model_validate(species) if matched else None,
        confidence=round(top.probability, 4),
        new_badge=new_badge,
        message=message,
        top_predictions=[
            PredictionOut(label=p.label, probability=round(p.probability, 4),
                          common_name=species_by_slug[p.label].common_name
                          if p.label in species_by_slug else None)
            for p in preds
        ],
    )


@app.get("/me/collection", response_model=CollectionOut)
def my_collection(user: User = Depends(current_user), db: Session = Depends(get_db)):
    badges = {b.species_id: b for b in db.scalars(select(Badge).where(Badge.user_id == user.id))}
    entries = []
    for s in db.scalars(active_species().order_by(Species.id)):
        b = badges.get(s.id)
        entries.append(CollectionEntry(
            species=SpeciesOut.model_validate(s), caught=b is not None,
            capture_count=b.capture_count if b else 0, earned_at=b.earned_at if b else None))
    return CollectionOut(caught=sum(e.caught for e in entries), total=len(entries), entries=entries)
