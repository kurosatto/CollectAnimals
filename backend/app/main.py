import csv
import io
import time
import uuid
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import Depends, FastAPI, File, HTTPException, Query, UploadFile, status
from fastapi.responses import FileResponse
from fastapi.security import OAuth2PasswordRequestForm
from PIL import Image, ImageOps, UnidentifiedImageError
from sqlalchemy import inspect, or_, select, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from . import classifier as clf
from . import dex
from . import states as st
from .auth import create_token, current_user, hash_password, verify_password
from .config import settings
from .db import Base, SessionLocal, engine, get_db
from .classifier import OTHER_LABEL, Prediction
from .models import Badge, Capture, Species, StateSpecies, User
from .schemas import (CaptureOut, CollectionEntry, CollectionOut, DexOut, HotspotOut, HotspotSpecies,
                      PredictionOut, RegisterIn, SpeciesOut, StateOut, TokenOut, UserOut, UserUpdate)

STATIC_DIR = Path(__file__).parent / "static"


def seed_species(db: Session, state_list: list[st.State]) -> None:
    """Upsert species and each state's list from the CSVs, so editing a list doesn't
    need a migration. Species dropped from a list leave that state's Dex, Hotspots
    and matching; their rows stay because old captures point at them. A species on several lists is one row; its shared fields
    come from the first state that lists it, rarity and name are kept per state."""
    existing = {s.slug: s for s in db.scalars(select(Species))}
    members = {(m.state, m.species_id): m for m in db.scalars(select(StateSpecies))}
    seen: set[str] = set()
    for state in state_list:
        with open(state.species_csv, newline="", encoding="utf-8") as fh:
            rows = list(csv.DictReader(fh))
        for row in rows:
            s = existing.get(row["slug"])
            if s is None:
                s = existing[row["slug"]] = Species(slug=row["slug"])
            if row["slug"] not in seen:
                seen.add(row["slug"])
                s.common_name = row["common_name"]
                s.scientific_name = row["scientific_name"]
                s.category = row["category"]
                s.rarity = row["rarity"]
                s.region = state.name.lower().replace(" ", "_")
                db.add(s)
        db.flush()
        keep = set()
        for pos, row in enumerate(rows, 1):
            sid = existing[row["slug"]].id
            m = members.get((state.code, sid)) or StateSpecies(state=state.code, species_id=sid)
            m.position, m.common_name, m.rarity = pos, row["common_name"], row["rarity"]
            db.add(m)
            keep.add(sid)
        for (code, sid), m in members.items():
            if code == state.code and sid not in keep:
                db.delete(m)
    db.commit()


def add_missing_columns() -> None:
    """create_all() doesn't add columns to existing tables; add the few added since."""
    insp = inspect(engine)
    if "users" in insp.get_table_names() and "state" not in {c["name"] for c in insp.get_columns("users")}:
        with engine.begin() as conn:
            conn.execute(text("ALTER TABLE users ADD COLUMN state VARCHAR(2) NOT NULL DEFAULT 'CA'"))


def state_or_404(code: str | None) -> st.State:
    state = st.get(code)
    if state is None:
        raise HTTPException(404, f"Unknown state {code!r}")
    return state


def state_species(db: Session, code: str) -> list[StateSpecies]:
    return list(db.scalars(select(StateSpecies).where(StateSpecies.state == code)
                           .order_by(StateSpecies.position)))


def species_out(s: Species, m: StateSpecies | None) -> SpeciesOut:
    """The species as one state shows it (that state's name and rarity)."""
    out = SpeciesOut.model_validate(s)
    if m is not None:
        out = out.model_copy(update={"common_name": m.common_name, "rarity": m.rarity})
    return out


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(engine)
    add_missing_columns()
    settings.upload_dir.mkdir(parents=True, exist_ok=True)
    st.load(settings.states_json)
    with SessionLocal() as db:
        seed_species(db, st.all_states())
    dex.load(settings.details_csv, st.all_states())
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
    state = st.get(body.state)
    if state is None:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, f"Unknown state {body.state!r}")
    user = User(email=body.email.lower(), username=body.username,
                password_hash=hash_password(body.password), state=state.code)
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


@app.patch("/me", response_model=UserOut)
def update_me(body: UserUpdate, user: User = Depends(current_user), db: Session = Depends(get_db)):
    """Change the player's state; their Dex, Hotspots and maps follow it."""
    user.state = state_or_404(body.state).code
    db.commit()
    return user


@app.get("/states", response_model=list[StateOut])
def list_states(db: Session = Depends(get_db)):
    return [StateOut(code=s.code, name=s.name, species_count=len(state_species(db, s.code)),
                     bounds=s.bounds) for s in st.all_states()]


# --- species ----------------------------------------------------------------

# Endpoints that take ?state= default to the first state in states.json (California).

@app.get("/species", response_model=list[SpeciesOut])
def list_species(state: str | None = Query(None), db: Session = Depends(get_db)):
    """One state's list, in Dex order."""
    code = state_or_404(state).code
    return [species_out(m.species, m) for m in state_species(db, code)]


def _species_in(slug: str, code: str, db: Session) -> tuple[Species, StateSpecies | None]:
    s = db.scalar(select(Species).where(Species.slug == slug))
    lists = {m.state: m for m in db.scalars(select(StateSpecies).where(StateSpecies.species_id == s.id))} if s else {}
    # A species dropped from every list is retired: old captures keep pointing at it,
    # but it's gone from the game.
    if not lists:
        raise HTTPException(404, "Unknown species")
    return s, lists.get(code)


@app.get("/species/{slug}", response_model=SpeciesOut)
def get_species(slug: str, state: str | None = Query(None), db: Session = Depends(get_db)):
    return species_out(*_species_in(slug, state_or_404(state).code, db))


@app.get("/map/california")
def california_outline():
    """Outline rings ([[lon, lat], ...]) for drawing range maps."""
    return state_outline("CA")


@app.get("/map/{state}")
def state_outline(state: str):
    """A state's outline rings ([[lon, lat], ...]) for drawing range maps."""
    path = state_or_404(state).outline
    if not path.exists():
        raise HTTPException(404, "No outline")
    return FileResponse(path, media_type="application/json")


@app.get("/species/{slug}/dex", response_model=DexOut)
def get_dex_entry(slug: str, state: str | None = Query(None), db: Session = Depends(get_db)):
    code = state_or_404(state).code
    s, m = _species_in(slug, code, db)
    d = dex.details(slug, code)
    return DexOut(species=species_out(s, m), size=d.get("size"), weight=d.get("weight"),
                  fun_fact=d.get("fun_fact"), where_to_find=d.get("where_to_find"),
                  active_time=d.get("active_time"), spotting_tip=d.get("spotting_tip"),
                  safety=d.get("safety") or "none", safe_distance=d.get("safe_distance") or None,
                  safety_note=d.get("safety_note") or None,
                  hotspots=dex.hotspots_for(slug, code), range=dex.range_for(slug, code))


@app.get("/hotspots", response_model=list[HotspotOut])
def list_hotspots(state: str | None = Query(None), db: Session = Depends(get_db)):
    """A state's parks and its listed species seen there, parks with the most species first."""
    code = state_or_404(state).code
    by_slug = {m.species.slug: m for m in state_species(db, code)}
    out = []
    for p in dex.hotspots(code):
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

    # Only the player's state counts: drop the other states' species and rescale,
    # so e.g. a bluebird photo in North Carolina isn't split between the eastern
    # and western bluebird.
    state = st.get(user.state) or st.get(None)
    members = {m.species.slug: m for m in state_species(db, state.code)}
    preds = restrict(model.predict(image, k=1000), set(members) | {OTHER_LABEL})[:3]
    top = preds[0]
    species = members[top.label].species if top.label in members else None
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

    name = members[top.label].common_name if species is not None else None
    if matched:
        message = (f"You caught a {name}! New badge unlocked."
                   if new_badge else f"Another {name} for your collection.")
    elif species is not None:
        message = f"Might be a {name}, but we're not sure. Try a clearer photo!"
    else:
        message = f"We couldn't match this to any animal in the {state.name} collection."

    return CaptureOut(
        capture_id=capture.id,
        matched=matched,
        species=species_out(species, members[top.label]) if matched else None,
        confidence=round(top.probability, 4),
        new_badge=new_badge,
        message=message,
        top_predictions=[
            PredictionOut(label=p.label, probability=round(p.probability, 4),
                          common_name=members[p.label].common_name
                          if p.label in members else None)
            for p in preds
        ],
    )


def restrict(preds: list[Prediction], allowed: set[str]) -> list[Prediction]:
    """Keep only the allowed labels, rescaled so their probabilities sum to 1."""
    kept = [p for p in preds if p.label in allowed]
    total = sum(p.probability for p in kept)
    if not kept or total <= 0:
        return [Prediction(OTHER_LABEL, 1.0)]
    return [Prediction(p.label, p.probability / total) for p in kept]


@app.get("/me/collection", response_model=CollectionOut)
def my_collection(state: str | None = Query(None), user: User = Depends(current_user),
                  db: Session = Depends(get_db)):
    """The player's Dex for their state (or ?state=). Badges are per species, so a
    coyote caught in California is also caught in North Carolina's Dex."""
    code = state_or_404(state or user.state).code
    badges = {b.species_id: b for b in db.scalars(select(Badge).where(Badge.user_id == user.id))}
    entries = []
    for m in state_species(db, code):
        b = badges.get(m.species_id)
        entries.append(CollectionEntry(
            species=species_out(m.species, m), caught=b is not None,
            capture_count=b.capture_count if b else 0, earned_at=b.earned_at if b else None))
    return CollectionOut(state=code, caught=sum(e.caught for e in entries), total=len(entries),
                         entries=entries)
