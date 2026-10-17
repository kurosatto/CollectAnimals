import csv
import io
import json
import time
import uuid
from contextlib import asynccontextmanager
from datetime import datetime, timedelta, timezone
from pathlib import Path

from fastapi import Depends, FastAPI, File, Form, HTTPException, Query, UploadFile, status
from fastapi.responses import FileResponse
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.staticfiles import StaticFiles
from PIL import Image, ImageOps, UnidentifiedImageError
from sqlalchemy import func, inspect, or_, select, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from . import classifier as clf
from . import dex
from . import bonds, goals, places, scoring, social
from . import states as st
from .auth import create_token, current_user, hash_password, optional_user, verify_password
from .classifier import OTHER_LABEL, Prediction
from .config import settings
from .db import Base, SessionLocal, add_missing_columns, engine, get_db
from .models import AlbumPhoto, Badge, Capture, Friendship, IdFeedback, PhotoLike, Species, StateSpecies, User
from .schemas import (BondNoteOut, BondOut, BondsOut, BuddyIn, BuddyOut, CaptureOut, ChallengeOut, ChallengesOut, ChoiceOut, ScoreOut, ScorePart, SetOut, SetSpecies, SetsOut, CollectionEntry, CollectionOut, DexOut, HotspotOut, HotspotSpecies,
                      PickIn, PredictionOut, RegisterIn, SpeciesMatch, SpeciesOut, StateOut, TokenOut, UserOut, UserUpdate)
from .social import find_species, friend_ids, revealed_species_ids, species_out, user_named
from .storage import get_storage

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


def add_state_column() -> None:
    """users.state is NOT NULL, which add_missing_columns() skips; add it with its default."""
    insp = inspect(engine)
    if "users" in insp.get_table_names() and "state" not in {c["name"] for c in insp.get_columns("users")}:
        with engine.begin() as conn:
            conn.execute(text("ALTER TABLE users ADD COLUMN state VARCHAR(2) NOT NULL DEFAULT 'CA'"))


def restar_scores() -> None:
    """Stars went from 1-3 to 1-5: work them out again from each saved score's parts."""
    with SessionLocal() as db:
        for c in db.scalars(select(Capture).where(Capture.score_parts.is_not(None))):
            stars = scoring.stars_for(json.loads(c.score_parts))
            if c.score_stars != stars:
                c.score_stars = stars
        db.commit()


def state_or_404(code: str | None) -> st.State:
    state = st.get(code)
    if state is None:
        raise HTTPException(404, f"Unknown state {code!r}")
    return state


def state_species(db: Session, code: str) -> list[StateSpecies]:
    return list(db.scalars(select(StateSpecies).where(StateSpecies.state == code)
                           .order_by(StateSpecies.position)))


def state_member(db: Session, code: str, species_id: int) -> StateSpecies | None:
    return db.scalar(select(StateSpecies).where(StateSpecies.state == code,
                                                StateSpecies.species_id == species_id))


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(engine)
    add_missing_columns()
    add_state_column()
    restar_scores()
    get_storage()
    st.load(settings.states_json)
    with SessionLocal() as db:
        seed_species(db, st.all_states())
    dex.load(settings.details_csv, st.all_states())
    places.load(settings.places_json)
    goals.load(settings.sets_json)
    if clf.get_classifier() is None:
        clf.load_classifier(settings.model_path)
    yield


app = FastAPI(title="Capture Animals", lifespan=lifespan,
              **({"docs_url": None, "redoc_url": None, "openapi_url": None} if settings.public else {}))

# Failed logins per account in the last LOGIN_WINDOW seconds; slows password guessing.
LOGIN_WINDOW, LOGIN_MAX_FAILURES = 300, 10
_failed_logins: dict[str, list[float]] = {}
app.include_router(social.router)
# Third-party browser libraries, served from here so the app works without a CDN.
app.mount("/vendor", StaticFiles(directory=STATIC_DIR / "vendor"), name="vendor")


@app.get("/", include_in_schema=False)
def index():
    return FileResponse(STATIC_DIR / "index.html")


@app.get("/habitat.js", include_in_schema=False)
def habitat_js():
    """The habitat scene, shared with the Android app."""
    return FileResponse(STATIC_DIR / "habitat.js", media_type="text/javascript")


@app.get("/sprites/silhouette/{number}.png", include_in_schema=False)
def silhouette_by_number(number: int, db: Session = Depends(get_db)):
    """The silhouette for a species that's still hidden, by Dex number, so the
    URL doesn't give away its name."""
    s = db.get(Species, number)
    path = settings.sprites_dir / f"{s.slug}_silhouette.png" if s else None
    if not path or not path.is_file():
        raise HTTPException(status.HTTP_404_NOT_FOUND, "No such sprite")
    return FileResponse(path, media_type="image/png", headers={"Cache-Control": "public, max-age=86400"})


@app.get("/sprites/anim/index.json", include_in_schema=False)
def sprite_anim_index():
    """Which poses (idle, walk, fly, swim, sleep) each species' animation sheet really draws."""
    path = settings.sprites_dir / "anim" / "index.json"
    if not path.is_file():
        raise HTTPException(status.HTTP_404_NOT_FOUND, "No animations")
    return FileResponse(path, media_type="application/json", headers={"Cache-Control": "public, max-age=3600"})


@app.get("/sprites/anim/{slug}.png", include_in_schema=False)
def sprite_anim(slug: str):
    """A species' animation sheet: a row of four 32x32 frames for each pose."""
    path = settings.sprites_dir / "anim" / f"{slug}.png"
    if not slug.replace("_", "").isalnum() or not path.is_file():
        raise HTTPException(status.HTTP_404_NOT_FOUND, "No such sprite")
    return FileResponse(path, media_type="image/png", headers={"Cache-Control": "public, max-age=3600"})


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
                                             func.lower(User.username) == body.username.lower())))
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
    # The example bot players (one set for every state, clearly labelled as
    # bots in the app) add them as a friend; players can remove them from the
    # Friends tab and add them back from the suggestions.
    for bot in db.scalars(select(User).where(User.is_bot.is_(True), User.id != user.id)):
        db.add(Friendship(requester_id=bot.id, addressee_id=user.id, accepted=True))
    db.commit()
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
    user = db.scalar(select(User).where(User.email == ident.lower())) or user_named(db, ident)
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

# Species are looked up by number or slug. Names stay hidden until the viewer
# or one of their friends has caught the species (see app/social.py).
# Endpoints that take ?state= default to the first state in states.json
# (California); names and rarity are that state's.

@app.get("/species", response_model=list[SpeciesOut])
def list_species(state: str | None = Query(None), user: User | None = Depends(optional_user),
                 db: Session = Depends(get_db)):
    """One state's list, in Field Guide order."""
    code = state_or_404(state).code
    revealed = revealed_species_ids(db, user)
    return [species_out(m.species, m.species_id in revealed, m) for m in state_species(db, code)]


def _species_in(key: str, code: str, db: Session) -> tuple[Species, StateSpecies | None]:
    """A species by number or slug, with its entry on `code`'s list if it has one."""
    s = find_species(db, key)
    lists = {m.state: m for m in db.scalars(select(StateSpecies).where(StateSpecies.species_id == s.id))}
    # A species dropped from every list is retired: old captures keep pointing at it,
    # but it's gone from the game.
    if not lists:
        raise HTTPException(404, "Unknown species")
    return s, lists.get(code)


@app.get("/species/{key}", response_model=SpeciesOut)
def get_species(key: str, state: str | None = Query(None), user: User | None = Depends(optional_user),
                db: Session = Depends(get_db)):
    s, m = _species_in(key, state_or_404(state).code, db)
    return species_out(s, s.id in revealed_species_ids(db, user), m)


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


@app.get("/species/{key}/dex", response_model=DexOut)
def get_dex_entry(key: str, state: str | None = Query(None), user: User | None = Depends(optional_user),
                  db: Session = Depends(get_db)):
    """Size, weight, active time, season, hotspot parks, the sighting map and
    safety advice show even while the name is hidden. The where-to-find and
    spotting tips can name the animal, so they wait until it's revealed, and so
    does the fun fact (your own capture or a friend's reveals it)."""
    code = state_or_404(state).code
    s, m = _species_in(key, code, db)
    d = dex.details(s.slug, code)
    revealed = s.id in revealed_species_ids(db, user)
    caught = user is not None and db.scalar(select(Badge.id).where(
        Badge.user_id == user.id, Badge.species_id == s.id)) is not None
    return DexOut(species=species_out(s, revealed, m), size=d.get("size"), weight=d.get("weight"),
                  fun_fact=d.get("fun_fact") if revealed else None,
                  where_to_find=d.get("where_to_find") if revealed else None,
                  active_time=d.get("active_time"),
                  spotting_tip=d.get("spotting_tip") if revealed else None,
                  safety=d.get("safety") or "none", safe_distance=d.get("safe_distance") or None,
                  safety_note=d.get("safety_note") or None,
                  hotspots=dex.hotspots_for(s.slug, code), range=dex.range_for(s.slug, code),
                  season=dex.season_for(s.slug, code), captured=caught)


@app.get("/hotspots", response_model=list[HotspotOut])
def list_hotspots(state: str | None = Query(None), user: User | None = Depends(optional_user),
                  db: Session = Depends(get_db)):
    """A state's parks and its listed species seen there, parks with the most
    species first. Species the viewer hasn't unlocked are listed without names."""
    code = state_or_404(state).code
    by_slug = {m.species.slug: m for m in state_species(db, code)}
    revealed = revealed_species_ids(db, user)
    out = []
    for p in dex.hotspots(code):
        species = []
        for sp in p["species"]:
            m = by_slug.get(sp["slug"])
            if m is None:
                continue
            shown = m.species_id in revealed
            species.append(HotspotSpecies(number=m.species_id, slug=sp["slug"] if shown else None,
                                          common_name=m.common_name if shown else None,
                                          rarity=m.rarity, observations=sp["observations"]))
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

    # Only the player's state counts: drop the other states' species and rescale,
    # so e.g. a bluebird photo in North Carolina isn't split between the eastern
    # and western bluebird. Five guesses: the first three are shown, all five are
    # offered if the player says the model got it wrong.
    state = st.get(user.state) or st.get(None)
    members = {m.species.slug: m for m in state_species(db, state.code)}
    preds = restrict(model.predict(image, k=1000), set(members) | {OTHER_LABEL})[:5]
    top = preds[0]
    species_by_slug = {p.label: members[p.label].species for p in preds if p.label in members}
    names = {p.label: members[p.label].common_name for p in preds if p.label in members}
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
    score = (_score_capture(model, capture, top.label, members[top.label].rarity, image, state.code,
                            set(members), new_badge, confidence=top.probability) if matched else None)
    db.commit()
    bond, bond_up = _bond_after(db, user, capture) if matched else (None, [])

    # Don't give away names the player hasn't unlocked yet.
    revealed = revealed_species_ids(db, user)
    if matched:
        message = (f"You captured a {names[top.label]}! New badge unlocked."
                   if new_badge else f"Another {names[top.label]} for your collection.")
        if album_photo:
            message += " It's now in your album."
        if bond_up:
            message += f" Bond with the {names[top.label]}: {bonds.title(bond)} ({', '.join(bond_up)} ✓)."
    elif species is not None and species.id in revealed:
        message = f"Might be a {names[top.label]}, but we're not sure. Try a clearer photo!"
    elif species is not None:
        message = "Might be an animal you haven't discovered yet, but we're not sure. Try a clearer photo!"
    else:
        message = f"We couldn't match this to any animal in the {state.name} collection."

    return CaptureOut(
        capture_id=capture.id,
        matched=matched,
        species=species_out(species, True, members[top.label]) if matched else None,
        confidence=round(top.probability, 4),
        new_badge=new_badge,
        message=message,
        top_predictions=[
            PredictionOut(label=p.label, probability=round(p.probability, 4),
                          common_name=names[p.label])
            if p.label in species_by_slug and species_by_slug[p.label].id in revealed
            else PredictionOut(label="other" if p.label not in species_by_slug else "hidden",
                               probability=round(p.probability, 4), common_name=None)
            for p in preds[:3]
        ],
        album_photo_id=album_photo.id if album_photo else None,
        choices=[ChoiceOut(slug=p.label, common_name=names[p.label],
                           probability=round(p.probability, 4))
                 for p in preds if p.label in species_by_slug],
        score=score,
        bond=bond,
        bond_up=bond_up,
    )


def _score_capture(model, capture: Capture, slug: str, rarity: str, image: Image.Image, state_code: str,
                   allowed: set[str], new_badge: bool, confidence: float | None = None) -> ScoreOut:
    """Score the photo for the species it counts as and keep the result on the capture."""
    safety = dex.details(slug, state_code).get("safety") or "none"
    sc = scoring.score_photo(model, image, slug, allowed, confidence=confidence, rarity=rarity,
                             safety=safety, new_species=new_badge,
                             activity=dex.activity(slug, state_code),
                             sun=_sun_at_capture(capture, state_code))
    capture.score, capture.score_stars, capture.score_parts = sc.total, sc.stars, sc.to_json()
    return score_out(capture)


def _sun_at_capture(capture: Capture, state_code: str) -> float | None:
    """The sun's elevation when and where the photo was taken: the photo's EXIF
    time (the phone's local time), else the upload time (UTC), at the photo's
    location, else the middle of the state."""
    state = st.get(state_code)
    if state is None:
        return None
    if capture.taken_at is not None:
        when = scoring.to_utc(capture.taken_at, state.utc_offset)
    else:
        when = capture.created_at or datetime.now(timezone.utc)
        if when.tzinfo is None:
            when = when.replace(tzinfo=timezone.utc)
    if capture.latitude is not None and capture.longitude is not None:
        lat, lon = capture.latitude, capture.longitude
    else:
        b = state.bounds
        lat, lon = (b["south"] + b["north"]) / 2, (b["west"] + b["east"]) / 2
    return scoring.sun_elevation(when, lat, lon)


def score_out(capture: Capture) -> ScoreOut | None:
    if capture.score is None:
        return None
    parts = json.loads(capture.score_parts or "[]")
    return ScoreOut(total=capture.score, stars=capture.score_stars or 1,
                    parts=[ScorePart(label=label, points=pts) for label, pts in parts])


def _unassign_capture(db: Session, capture: Capture) -> None:
    """Take back the badge and album photo a capture earned, e.g. when the
    player says the model named the wrong animal."""
    old = capture.species_id
    if old is None:
        return
    capture.species_id = None
    capture.score = capture.score_stars = capture.score_parts = None
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
        social.clear_reactions(db, photo.id)
        db.delete(photo)
        db.flush()
        # Re-point the album at the newest other catch that still has its photo.
        with_photo = [c for c in others if c.image_path]
        if with_photo:
            social.ensure_album_photo(db, with_photo[-1])


@app.post("/captures/{capture_id}/pick", response_model=CaptureOut)
def pick_capture_species(capture_id: int, body: PickIn, user: User = Depends(current_user),
                         db: Session = Depends(get_db)):
    """'Wrong animal?': the player names the animal themselves, from the model's
    top guesses or (after "None of these") any animal on their state's list, or
    skips with "none". We trust their pick and award the badge, and keep the
    correction so it can help retrain the model."""
    capture = db.get(Capture, capture_id)
    if capture is None or capture.user_id != user.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Capture not found")
    guesses = capture.top_labels.split(",") if capture.top_labels else []

    if body.label == "none":
        _unassign_capture(db, capture)
        capture.user_picked = True
        _record_feedback(db, capture, user, guesses, None)
        db.commit()
        return CaptureOut(capture_id=capture.id, matched=False, species=None, confidence=capture.confidence,
                          new_badge=False, message="Okay, this photo doesn't count for any animal.",
                          top_predictions=[])

    species = db.scalar(select(Species).where(Species.slug == body.label))
    m = state_member(db, user.state, species.id) if species else None
    # One of the model's guesses, or any animal on the player's state list.
    if species is None or (m is None and body.label not in guesses):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Pick an animal from your state's list")

    name = m.common_name if m else species.common_name
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
        _rescore_picked(db, capture, species, m, user, new_badge)
    _record_feedback(db, capture, user, guesses, species.slug)
    db.commit()
    bond, bond_up = _bond_after(db, user, capture)

    message = (f"Got it: a {name}! New badge unlocked." if new_badge
               else f"Got it: another {name} for your collection.")
    if album_photo:
        message += " It's now in your album."
    if bond_up:
        message += f" Bond with the {name}: {bonds.title(bond)} ({', '.join(bond_up)} ✓)."
    return CaptureOut(capture_id=capture.id, matched=True, species=species_out(species, True, m),
                      confidence=capture.confidence, new_badge=new_badge, message=message,
                      top_predictions=[], album_photo_id=album_photo.id if album_photo else None,
                      score=score_out(capture), bond=bond, bond_up=bond_up)


def _record_feedback(db: Session, capture: Capture, user: User, guesses: list[str], chosen: str | None) -> None:
    """Keep the player's correction (one row per capture). Picking the model's own
    best guess isn't a correction, so it clears any earlier one."""
    row = db.scalar(select(IdFeedback).where(IdFeedback.capture_id == capture.id))
    if chosen == capture.predicted_label:
        if row:
            db.delete(row)
        return
    source = "none" if chosen is None else "guesses" if chosen in guesses else "list"
    if row is None:
        row = IdFeedback(capture_id=capture.id, user_id=user.id)
        db.add(row)
    row.state = (st.get(user.state) or st.get(None)).code
    row.predicted_label = capture.predicted_label
    row.rejected_labels = ",".join(g for g in guesses if g != chosen) or capture.predicted_label
    row.chosen_label = chosen
    row.source = source


@app.get("/species-search", response_model=list[SpeciesMatch])
def search_species(q: str = Query(..., min_length=2, max_length=60), user: User = Depends(current_user),
                   db: Session = Depends(get_db)):
    """"None of these" > search: animals on the player's state list whose common or
    scientific name contains q. Only matches are named, so the Field Guide's
    undiscovered animals stay mostly a surprise."""
    needle = q.strip().lower()
    out = []
    for m in state_species(db, (st.get(user.state) or st.get(None)).code):
        if needle in m.common_name.lower() or needle in m.species.scientific_name.lower():
            out.append(SpeciesMatch(slug=m.species.slug, common_name=m.common_name,
                                    scientific_name=m.species.scientific_name, number=m.species.id))
    out.sort(key=lambda x: not x.common_name.lower().startswith(needle))
    return out[:10]


def _rescore_picked(db: Session, capture: Capture, species: Species, m: StateSpecies | None,
                    user: User, new_badge: bool) -> None:
    """Score a photo again for the animal the player picked (the saved copy)."""
    model = clf.get_classifier()
    data = get_storage().get(capture.image_path) if capture.image_path else None
    capture.score = capture.score_stars = capture.score_parts = None
    if model is None or data is None:
        return
    state = st.get(user.state) or st.get(None)
    allowed = {mm.species.slug for mm in state_species(db, state.code)}
    image = Image.open(io.BytesIO(data)).convert("RGB")
    _score_capture(model, capture, species.slug, m.rarity if m else species.rarity, image, state.code,
                   allowed, new_badge)


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
    """The player's Field Guide for their state (or ?state=). Badges are per
    species, so a coyote captured in California also counts in North Carolina."""
    return _collection(db, user, user, state_or_404(state or user.state))


@app.get("/users/{username}/collection", response_model=CollectionOut)
def user_collection(username: str, user: User = Depends(current_user), db: Session = Depends(get_db)):
    """A friend's Field Guide, for their own state. Friends only: anyone else sees
    just what the profile shows."""
    owner = user_named(db, username)
    if not owner:
        raise HTTPException(404, "No such user")
    if owner.id != user.id and owner.id not in friend_ids(db, user.id):
        raise HTTPException(403, "Only friends can see each other's Field Guide")
    return _collection(db, owner, user, state_or_404(owner.state))


def _collection(db: Session, owner: User, viewer: User, st_: st.State) -> CollectionOut:
    """`owner`'s Field Guide as `viewer` sees it. Names follow the viewer's own
    reveals (theirs and their friends' badges, which covers a friend's captures);
    friends_caught counts the viewer's friends, and you_caught the viewer."""
    code = st_.code
    month = (datetime.now(timezone.utc) + timedelta(hours=st_.utc_offset)).month
    badges = {b.species_id: b for b in db.scalars(select(Badge).where(Badge.user_id == owner.id))}
    mine = badges if owner.id == viewer.id else {
        b.species_id: b for b in db.scalars(select(Badge).where(Badge.user_id == viewer.id))}
    friends = friend_ids(db, viewer.id)
    friends_caught = dict(db.execute(
        select(Badge.species_id, func.count()).where(Badge.user_id.in_(friends))
        .group_by(Badge.species_id)).all()) if friends else {}
    photos = dict(db.execute(select(AlbumPhoto.species_id, Capture.image_path)
                             .join(Capture, Capture.id == AlbumPhoto.capture_id)
                             .where(AlbumPhoto.user_id == owner.id)).all())
    storage = get_storage()
    bond_levels = {sid: bonds.level(bonds.notes(sg)) for sid, sg in _sightings(db, owner.id, st_.utc_offset).items()}
    entries = []
    for m in state_species(db, code):
        b = badges.get(m.species_id)
        revealed = b is not None or m.species_id in mine or friends_caught.get(m.species_id, 0) > 0
        entries.append(CollectionEntry(
            species=species_out(m.species, revealed, m),
            caught=b is not None, capture_count=b.capture_count if b else 0,
            earned_at=b.earned_at if b else None, friends_caught=friends_caught.get(m.species_id, 0),
            you_caught=m.species_id in mine,
            photo_url=storage.url(photos[m.species_id]) if m.species_id in photos else None,
            in_season=dex.in_season(m.species.slug, code, month),
            activity=dex.activity(m.species.slug, code) if b else None,
            bond=bond_levels.get(m.species_id, 0) if b else 0))
    return CollectionOut(state=code, username=owner.username,
                         caught=sum(e.caught for e in entries), total=len(entries), entries=entries)


def _aware(d: datetime) -> datetime:
    return d if d.tzinfo else d.replace(tzinfo=timezone.utc)


@app.get("/me/sets", response_model=SetsOut)
def my_sets(state: str | None = Query(None), user: User = Depends(current_user), db: Session = Depends(get_db)):
    """Themed sets from the state's list (tide pools, state symbols, ...) and
    how many of each the player has captured. Hidden names stay hidden."""
    code = state_or_404(state or user.state).code
    members = {m.species.slug: m for m in state_species(db, code)}
    caught = set(db.scalars(select(Badge.species_id).where(Badge.user_id == user.id)))
    revealed = revealed_species_ids(db, user)
    out = []
    for s in goals.sets_for(code, set(members)):
        rows = [SetSpecies(species=species_out(members[x].species, members[x].species_id in revealed, members[x]),
                           caught=members[x].species_id in caught) for x in s.slugs]
        n = sum(r.caught for r in rows)
        out.append(SetOut(id=s.id, title=s.title, description=s.description, caught=n, total=len(rows),
                          complete=n == len(rows), species=rows))
    return SetsOut(state=code, sets=out)


@app.get("/me/challenges", response_model=ChallengesOut)
def my_challenges(user: User = Depends(current_user), db: Session = Depends(get_db)):
    """This week's three challenges for the player's state and their progress."""
    state = state_or_404(user.state)
    start, end = goals.week_bounds(state.utc_offset)
    members = {m.species_id: m for m in state_species(db, state.code)}
    categories: dict[str, int] = {}
    for m in members.values():
        categories[m.species.category] = categories.get(m.species.category, 0) + 1
    sets = goals.sets_for(state.code, {m.species.slug for m in members.values()})
    challenges = goals.challenges_for(state.code, start, categories, sets)

    new_ids = {b.species_id for b in db.scalars(select(Badge).where(Badge.user_id == user.id))
               if start <= _aware(b.earned_at) < end}
    week = []
    for c in db.scalars(select(Capture).where(Capture.user_id == user.id, Capture.species_id.is_not(None))):
        m = members.get(c.species_id)
        if m and start <= _aware(c.created_at) < end:
            week.append(goals.WeekCapture(m.species.slug, m.species.category, m.rarity,
                                          c.species_id in new_ids))
    likes = sum(start <= _aware(t) < end for t in db.scalars(
        select(PhotoLike.created_at).where(PhotoLike.user_id == user.id)))
    out = []
    for ch in challenges:
        p = goals.progress(ch, week, likes)
        out.append(ChallengeOut(id=ch.id, title=ch.title, progress=min(p, ch.goal), goal=ch.goal, done=p >= ch.goal))
    return ChallengesOut(state=state.code, week_start=start, week_end=end, challenges=out,
                         done=sum(c.done for c in out))


# --- bonds and buddy (app/bonds.py) ---------------------------------------------

def _sightings(db: Session, user_id: int, utc_offset: int, species_id: int | None = None,
               skip_capture: int | None = None) -> dict[int, list[bonds.Sighting]]:
    """The player's captures that count for an animal, per species, oldest first."""
    q = select(Capture).where(Capture.user_id == user_id, Capture.species_id.is_not(None)).order_by(Capture.id)
    if species_id is not None:
        q = q.where(Capture.species_id == species_id)
    out: dict[int, list[bonds.Sighting]] = {}
    for c in db.scalars(q):
        if c.id == skip_capture:
            continue
        out.setdefault(c.species_id, []).append(bonds.Sighting(
            bonds.local_time(c.taken_at, c.created_at, utc_offset), c.latitude, c.longitude, c.score_stars))
    return out


def _bond_after(db: Session, user: User, capture: Capture) -> tuple[int, list[str]]:
    """Bond hearts with the capture's animal now, and the field notes it ticked."""
    offset = (st.get(user.state) or st.get(None)).utc_offset
    after = _sightings(db, user.id, offset, capture.species_id).get(capture.species_id, [])
    before = _sightings(db, user.id, offset, capture.species_id, skip_capture=capture.id).get(capture.species_id, [])
    return bonds.level(bonds.notes(after)), bonds.newly_done(before, after)


def _bond_out(species: Species, m: StateSpecies | None, sightings: list[bonds.Sighting]) -> BondOut:
    ns = bonds.notes(sightings)
    lvl = bonds.level(ns)
    return BondOut(species=species_out(species, True, m), level=lvl, max_level=len(ns), title=bonds.title(lvl),
                   notes=[BondNoteOut(id=n.id, title=n.title, hint=n.hint, progress=n.progress, goal=n.goal,
                                      done=n.done) for n in ns])


@app.get("/me/bonds", response_model=BondsOut)
def my_bonds(species: str | None = Query(None), user: User = Depends(current_user),
             db: Session = Depends(get_db)):
    """Bond hearts and field notes for every animal the player has captured
    (or just ?species=, by number or slug), closest bonds first."""
    state = state_or_404(user.state)
    sid = find_species(db, species).id if species else None
    seen = _sightings(db, user.id, state.utc_offset, sid)
    members = {m.species_id: m for m in state_species(db, state.code)}
    out = []
    for species_id, sightings in seen.items():
        sp = db.get(Species, species_id)
        out.append(_bond_out(sp, members.get(species_id), sightings))
    out.sort(key=lambda b: (-b.level, b.species.common_name or ""))
    return BondsOut(state=state.code, bonds=out)


def _buddy_suggestion(db: Session, user: User, state: st.State, buddy: Species) -> str | None:
    """An animal around this month that the player hasn't captured, preferring
    the buddy's own kind. Hidden names stay hidden. Never a dangerous one."""
    month = (datetime.now(timezone.utc) + timedelta(hours=state.utc_offset)).month
    caught = set(db.scalars(select(Badge.species_id).where(Badge.user_id == user.id)))
    revealed = revealed_species_ids(db, user)
    options = [m for m in state_species(db, state.code)
               if m.species_id not in caught and dex.in_season(m.species.slug, state.code, month)
               and dex.details(m.species.slug, state.code).get("safety") != "danger"]
    if not options:
        return None
    same = [m for m in options if m.species.category == buddy.category] or options
    # Changes once a day, so the buddy doesn't say something new on every refresh.
    day = (datetime.now(timezone.utc) + timedelta(hours=state.utc_offset)).toordinal()
    m = same[(day + user.id) % len(same)]
    return f"the {m.common_name}" if m.species_id in revealed else f"a mystery {m.species.category}"


@app.get("/me/buddy", response_model=BuddyOut | None)
def my_buddy(user: User = Depends(current_user), db: Session = Depends(get_db)):
    """The player's buddy: the animal they picked (or, until they pick, their
    closest bond), its mood from the last week's outings and what it says.
    None before the first capture."""
    state = state_or_404(user.state)
    seen = _sightings(db, user.id, state.utc_offset)
    if not seen:
        return None
    chosen = user.buddy_species_id in seen
    if chosen:
        sid = user.buddy_species_id
    else:
        sid = max(seen, key=lambda k: (bonds.level(bonds.notes(seen[k])), len(seen[k]), -k))
    sp = db.get(Species, sid)
    bond = _bond_out(sp, state_member(db, state.code, sid), seen[sid])
    since = datetime.now(timezone.utc) - timedelta(days=7)
    days = {(_aware(c) + timedelta(hours=state.utc_offset)).date() for c in db.scalars(
        select(Capture.created_at).where(Capture.user_id == user.id, Capture.species_id.is_not(None)))
        if _aware(c) >= since}
    mood = bonds.mood(len(days))
    ns = bonds.notes(seen[sid])
    suggestion = _buddy_suggestion(db, user, state, sp) if bonds.level(ns) == len(ns) else None
    return BuddyOut(chosen=chosen, bond=bond, mood=mood, outing_days=len(days),
                    line=bonds.buddy_line(mood, ns, suggestion),
                    activity=dex.activity(sp.slug, state.code))


@app.put("/me/buddy", response_model=BuddyOut | None)
def set_buddy(body: BuddyIn, user: User = Depends(current_user), db: Session = Depends(get_db)):
    """Pick any animal you've captured as your buddy."""
    sp = find_species(db, body.species)
    if not db.scalar(select(Badge).where(Badge.user_id == user.id, Badge.species_id == sp.id)):
        raise HTTPException(400, "Capture this animal first to make it your buddy")
    user.buddy_species_id = sp.id
    db.commit()
    return my_buddy(user, db)
