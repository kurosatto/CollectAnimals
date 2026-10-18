import csv
import io
import json
import logging
import re
import threading
import time
import uuid
from contextlib import asynccontextmanager
from datetime import datetime, timedelta, timezone
from pathlib import Path

from fastapi import Depends, FastAPI, File, Form, HTTPException, Query, Request, UploadFile, status
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.staticfiles import StaticFiles
from PIL import Image, ImageOps, UnidentifiedImageError
from sqlalchemy import func, inspect, or_, select, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from . import classifier as clf
from . import dex
from . import bonds, goals, limits, notices, places, scoring, social
from . import states as st
from .auth import DUMMY_HASH, create_token, current_user, hash_password, optional_user, verify_password
from .classifier import OTHER_LABEL, Prediction
from .config import settings
from .db import Base, SessionLocal, add_missing_columns, engine, get_db
from .models import AlbumPhoto, Badge, Capture, Friendship, IdFeedback, PhotoLike, Species, StateSpecies, User
from .schemas import (BondNoteOut, BondOut, BondsOut, CaptureOut, ChallengeOut, ChallengesOut, ChoiceOut, ScoreOut, ScorePart, SetOut, SetSpecies, SetsOut, CollectionEntry, CollectionOut, DexOut, PlaceOut, HotspotOut, HotspotSpecies,
                      PickIn, PredictionOut, RegisterIn, SpeciesOut, StateOut, TokenOut, UserOut, UserUpdate,
                      WhereWhenIn, WhereWhenResult)
from .social import catches_in, find_species, friend_ids, revealed_species_ids, species_out, user_named
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
    """Stars went from 1-3 to 1-5, and the golden-hour bonus was dropped (the time
    and place can be edited, so they don't count): work each saved score out again
    from its parts."""
    with SessionLocal() as db:
        for c in db.scalars(select(Capture).where(Capture.score_parts.is_not(None))):
            parts = json.loads(c.score_parts)
            kept = [p for p in parts if p[0] not in scoring.RETIRED_PARTS]
            if len(kept) != len(parts):
                c.score_parts, c.score = json.dumps(kept), sum(pts for _, pts in kept)
            stars = scoring.stars_for(kept)
            if c.score_stars != stars:
                c.score_stars = stars
        db.commit()


def fill_capture_states(db: Session) -> int:
    """Captures from before they recorded their state: put each in the state its
    location falls in (if that state lists the animal), else the player's home
    state, else the first state that lists it. Returns how many were filled."""
    lists: dict[int, list[str]] = {}
    for m in db.scalars(select(StateSpecies)):
        lists.setdefault(m.species_id, []).append(m.state)
    done = 0
    for c in db.scalars(select(Capture).where(Capture.state.is_(None), Capture.species_id.is_not(None))):
        options = lists.get(c.species_id, [])
        home = db.get(User, c.user_id).state
        where = [s.code for s in st.all_states() if c.latitude is not None and c.longitude is not None
                 and s.bounds["south"] <= c.latitude <= s.bounds["north"]
                 and s.bounds["west"] <= c.longitude <= s.bounds["east"]]
        c.state = next((code for code in where if code in options), None) or \
            (home if home in options else (options[0] if options else home))
        done += 1
    db.commit()
    return done


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
        fill_capture_states(db)
    dex.load(settings.details_csv, st.all_states())
    places.load(st.all_states())
    goals.load(settings.sets_json)
    if clf.get_classifier() is None:
        clf.load_classifier(settings.model_path)
    if settings.score_old_photos and clf.get_classifier() is not None:
        threading.Thread(target=_score_old_photos_in_background, daemon=True).start()
    yield


app = FastAPI(title="Capture Animals", lifespan=lifespan,
              **({"docs_url": None, "redoc_url": None, "openapi_url": None} if settings.public else {}))



@app.middleware("http")
async def security_headers(request: Request, call_next):
    response = await call_next(request)
    h = response.headers
    h.setdefault("X-Content-Type-Options", "nosniff")
    h.setdefault("Referrer-Policy", "same-origin")
    # Nobody else's site may show this one in a frame (stops click-jacking tricks).
    h.setdefault("X-Frame-Options", "DENY")
    h.setdefault("Content-Security-Policy", "frame-ancestors 'none'")
    if settings.public:
        h.setdefault("Strict-Transport-Security", "max-age=31536000")
    return response

app.include_router(social.router)
app.include_router(notices.router)
# Third-party browser libraries, served from here so the app works without a CDN.
app.mount("/vendor", StaticFiles(directory=STATIC_DIR / "vendor"), name="vendor")


def release_version() -> str:
    """The version in release.json, re-read so a bump shows without a restart."""
    try:
        return json.loads(settings.release_json.read_text(encoding="utf-8"))["version"]
    except (OSError, ValueError, KeyError):
        return "dev"


APK_NAME = re.compile(r"CaptureAnimals-(\d+(?:\.\d+)*)\.apk")


def _version_key(v: str) -> tuple[int, ...]:
    return tuple(int(p) for p in v.split("."))


def latest_apk() -> tuple[str, Path] | None:
    """The newest CaptureAnimals-<version>.apk in ANDROID_APK_DIR, if any."""
    d = settings.android_apk_dir
    if not d or not d.is_dir():
        return None
    found = [(m.group(1), p) for p in d.iterdir() if (m := APK_NAME.fullmatch(p.name)) and p.is_file()]
    return max(found, key=lambda f: _version_key(f[0])) if found else None


@app.get("/", include_in_schema=False)
def index():
    # The page carries the release it was served with, to notice when a newer one is out.
    html = (STATIC_DIR / "index.html").read_text(encoding="utf-8")
    return HTMLResponse(html.replace("__RELEASE_VERSION__", release_version()))


@app.get("/app/version")
def app_version():
    """The current release, and the Android APK to download if one is published here."""
    apk = latest_apk()
    return {"version": release_version(),
            "android": {"version": apk[0], "url": f"/app/android/{apk[1].name}"} if apk else None}


@app.get("/app/android/{name}", include_in_schema=False)
def android_apk(name: str):
    apk = latest_apk()
    if not apk or apk[1].name != name:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "No such app version")
    return FileResponse(apk[1], media_type="application/vnd.android.package-archive", filename=name)


app.mount("/icons", StaticFiles(directory=STATIC_DIR / "icons"), name="icons")


@app.get("/manifest.webmanifest", include_in_schema=False)
def manifest():
    """Web app manifest: lets phones install the web app to the home screen."""
    return FileResponse(STATIC_DIR / "manifest.webmanifest", media_type="application/manifest+json")


@app.get("/sw.js", include_in_schema=False)
def service_worker():
    """Offline support. Served from the root so it covers the whole app; never cached by
    the browser, so a new version is picked up on the next visit."""
    return FileResponse(STATIC_DIR / "sw.js", media_type="text/javascript",
                        headers={"Cache-Control": "no-cache"})


@app.get("/habitat.js", include_in_schema=False)
def habitat_js():
    """The habitat scene, shared with the Android app."""
    return FileResponse(STATIC_DIR / "habitat.js", media_type="text/javascript")


@app.get("/sprites/silhouette/{number}.png", include_in_schema=False)
def silhouette_by_number(number: int, db: Session = Depends(get_db)):
    """The silhouette for a species that's still hidden, by Dex number, so the
    URL doesn't give away its name."""
    s = db.get(Species, number)
    if s is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "No such sprite")
    path = _sprite_or_placeholder(f"{s.slug}_silhouette")
    age = 86400 if path.stem == f"{s.slug}_silhouette" else 3600
    return FileResponse(path, media_type="image/png", headers={"Cache-Control": f"public, max-age={age}"})


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
def sprite(name: str, db: Session = Depends(get_db)):
    """Pixel-art sprites: `{slug}.png` in colour, `{slug}_silhouette.png` until caught."""
    slug = name.removesuffix("_silhouette")
    if not slug.replace("_", "").isalnum():
        raise HTTPException(status.HTTP_404_NOT_FOUND, "No such sprite")
    path = settings.sprites_dir / f"{name}.png"
    if not path.is_file() and db.scalar(select(Species.id).where(Species.slug == slug)) is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "No such sprite")
    path = _sprite_or_placeholder(name)
    # A placeholder is cached briefly, so the real art shows up soon after it's drawn.
    age = 86400 if path.stem == name else 3600
    return FileResponse(path, media_type="image/png", headers={"Cache-Control": f"public, max-age={age}"})


def _sprite_or_placeholder(name: str) -> Path:
    """The sprite file, or the "?" egg (tools/make_placeholder.py) for an animal
    that has no pixel art yet, as in the states added before their art."""
    path = settings.sprites_dir / f"{name}.png"
    if path.is_file():
        return path
    path = settings.sprites_dir / ("placeholder_silhouette.png" if name.endswith("_silhouette") else "placeholder.png")
    if not path.is_file():
        raise HTTPException(status.HTTP_404_NOT_FOUND, "No such sprite")
    return path


@app.get("/health")
def health():
    return {"ok": True, "model_loaded": clf.get_classifier() is not None,
            "model_error": None if settings.public else clf.classifier_status()}


# --- auth -------------------------------------------------------------------

@app.post("/auth/register", response_model=TokenOut, status_code=201)
def register(body: RegisterIn, request: Request, db: Session = Depends(get_db)):
    ip = limits.client_ip(request)
    if limits.registrations_by_ip.blocked(ip):
        raise HTTPException(status.HTTP_429_TOO_MANY_REQUESTS,
                            "Too many new accounts from here. Try again later.")
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
    limits.registrations_by_ip.hit(ip)
    # The example bot players (one set for every state, clearly labelled as
    # bots in the app) add them as a friend; players can remove them from the
    # Friends tab and add them back from the suggestions.
    for bot in db.scalars(select(User).where(User.is_bot.is_(True), User.id != user.id)):
        db.add(Friendship(requester_id=bot.id, addressee_id=user.id, accepted=True))
    db.commit()
    return TokenOut(access_token=create_token(user.id))


@app.post("/auth/login", response_model=TokenOut)
def login(request: Request, form: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    """Log in with email or username (sent in the OAuth2 `username` field)."""
    ident = form.username.strip()
    ip = limits.client_ip(request)
    if limits.failed_logins_by_account.blocked(ident.lower()) or limits.failed_logins_by_ip.blocked(ip):
        raise HTTPException(status.HTTP_429_TOO_MANY_REQUESTS,
                            "Too many failed logins. Try again in a few minutes.")
    user = db.scalar(select(User).where(User.email == ident.lower())) or user_named(db, ident)
    # Check a password even for unknown names, so the reply takes as long either way
    # and doesn't give away which accounts exist.
    if not verify_password(form.password, user.password_hash if user else DUMMY_HASH) or not user:
        limits.failed_logins_by_account.hit(ident.lower())
        limits.failed_logins_by_ip.hit(ip)
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Wrong email/username or password")
    limits.failed_logins_by_account.clear(ident.lower())
    return TokenOut(access_token=create_token(user.id))


def unlocked_states(db: Session, user: User) -> list[str]:
    """A player starts with only their home state and unlocks others by choosing
    them. States they've already captured in stay unlocked (players from before
    unlocking existed keep what they had)."""
    have = {user.state, *filter(None, (user.extra_states or "").split(","))}
    have |= set(db.scalars(select(Capture.state).where(Capture.user_id == user.id, Capture.species_id.is_not(None),
                                                       Capture.state.is_not(None)).distinct()))
    return [s.code for s in st.all_states() if s.code in have]


def user_out(db: Session, user: User) -> UserOut:
    out = UserOut.model_validate(user)
    out.unlocked_states = unlocked_states(db, user)
    return out


@app.get("/me", response_model=UserOut)
def me(user: User = Depends(current_user), db: Session = Depends(get_db)):
    return user_out(db, user)


@app.patch("/me", response_model=UserOut)
def update_me(body: UserUpdate, user: User = Depends(current_user), db: Session = Depends(get_db)):
    """Change the player's state; their Dex, Hotspots and maps follow it. Moving
    to a state unlocks it (the apps ask first)."""
    code = state_or_404(body.state).code
    unlocked = unlocked_states(db, user)
    if code not in unlocked:
        user.extra_states = ",".join([*unlocked, code])
    user.state = code
    db.commit()
    return user_out(db, user)


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


@app.get("/map/{state}")
def state_outline(state: str):
    """A state's outline rings ([[lon, lat], ...]) for drawing range maps."""
    path = state_or_404(state).outline
    if not path or not path.exists():
        raise HTTPException(404, "No outline")
    return FileResponse(path, media_type="application/json")


@app.get("/species/{key}/dex", response_model=DexOut)
def get_dex_entry(key: str, state: str | None = Query(None), user: User | None = Depends(optional_user),
                  db: Session = Depends(get_db)):
    """Size, weight, active time, season, hotspot parks, the sighting map,
    safety advice and the where-to-find and spotting tips show even while the
    name is hidden (with the name masked out of the tips). The fun fact waits
    until the animal is revealed (your own capture or a friend's reveals it)."""
    code = state_or_404(state).code
    s, m = _species_in(key, code, db)
    # An animal that isn't on this state's list (one opened from the feed or a
    # friend's photo) gets the entry of a state that lists it; `state` says which.
    if m is None:
        m = db.scalars(select(StateSpecies).where(StateSpecies.species_id == s.id)
                       .order_by(StateSpecies.state)).first()
        code = m.state
    d = dex.details(s.slug, code)
    revealed = s.id in revealed_species_ids(db, user)
    caught = user is not None and db.scalar(select(Capture.id).where(
        Capture.user_id == user.id, Capture.species_id == s.id, Capture.state == code).limit(1)) is not None
    def tip(text: str | None) -> str | None:
        return text if revealed else dex.mask_name(text, s.common_name, s.scientific_name)
    return DexOut(species=species_out(s, revealed, m), state=code, size=d.get("size"), weight=d.get("weight"),
                  fun_fact=d.get("fun_fact") if revealed else None,
                  where_to_find=tip(d.get("where_to_find")),
                  active_time=d.get("active_time"),
                  spotting_tip=tip(d.get("spotting_tip")),
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
        # A tiny file can claim huge dimensions and take gigabytes to decode;
        # check the size from the header before decoding anything.
        if im.width * im.height > MAX_IMAGE_PIXELS:
            raise HTTPException(status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, "Photo has too many pixels")
        im.load()
    except Image.DecompressionBombError:  # Pillow's own check, for sizes far past ours
        raise HTTPException(status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, "Photo has too many pixels")
    except (UnidentifiedImageError, OSError):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Not a valid image")
    return im


# 108 MP, the biggest common phone camera (200 MP modes make files over the upload limit anyway).
MAX_IMAGE_PIXELS = 12032 * 9024


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


# A phone's location only says where a photo was taken if it was taken just now;
# an older photo from the gallery gets no place rather than the wrong one.
DEVICE_PLACE_MAX_AGE = timedelta(hours=3)


def _local_now(state: st.State) -> datetime:
    """The state's wall clock now (no zone), with US daylight saving."""
    return _local(datetime.now(timezone.utc), state)


def _local(when: datetime, state: st.State) -> datetime:
    return scoring.to_local(when, state.utc_offset)


def _parse_local_time(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.strip()).replace(tzinfo=None)
    except ValueError:
        return None


@app.post("/captures", response_model=CaptureOut, status_code=201)
async def create_capture(photo: UploadFile = File(...),
                         latitude: float | None = Form(None, ge=-90, le=90),
                         longitude: float | None = Form(None, ge=-180, le=180),
                         photo_latitude: float | None = Form(None, ge=-90, le=90),
                         photo_longitude: float | None = Form(None, ge=-180, le=180),
                         photo_taken_at: str | None = Form(None),
                         save_place: bool = Form(True),
                         user: User = Depends(current_user), db: Session = Depends(get_db)):
    """Identify a photo. When and where it was taken come from the photo's own
    metadata (EXIF) first. Apps that shrink the photo before uploading (which
    drops EXIF) send what they read as photo_latitude/photo_longitude/photo_taken_at
    (local time). Without metadata, latitude/longitude (the phone's location now)
    are used if the photo is recent, and the upload time stands in for the time.
    save_place=false (the player turned off saving where) keeps no place at all."""
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
    state = st.get(user.state) or st.get(None)
    exif_lat, exif_lon, taken_at = _exif_meta(raw)
    if exif_lat is None and photo_latitude is not None and photo_longitude is not None:
        exif_lat, exif_lon = photo_latitude, photo_longitude
    taken_at = taken_at or _parse_local_time(photo_taken_at)
    now = _local_now(state)
    if taken_at is not None and not (datetime(1990, 1, 1) <= taken_at <= now + timedelta(days=1)):
        taken_at = None  # the camera's clock was wrong
    time_source = "photo" if taken_at is not None else None
    if not save_place:
        latitude = longitude = place_source = None
    elif exif_lat is not None:
        latitude, longitude, place_source = exif_lat, exif_lon, "photo"
    elif latitude is not None and longitude is not None and (taken_at is None or now - taken_at <= DEVICE_PLACE_MAX_AGE):
        place_source = "device"
    else:
        latitude = longitude = place_source = None
    # Phone photos are often rotated via EXIF; apply it before classifying.
    image = ImageOps.exif_transpose(raw).convert("RGB")

    # Only the player's state counts: drop the other states' species and rescale,
    # so e.g. a bluebird photo in North Carolina isn't split between the eastern
    # and western bluebird. Five guesses: the first three are shown, all five are
    # offered if the player says the model got it wrong.
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
                      latitude=latitude, longitude=longitude, taken_at=taken_at, state=state.code,
                      time_source=time_source, place_source=place_source,
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
        # New for this state's Field Guide: captures elsewhere don't count here.
        new_badge = _first_in_state(db, capture)
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
        where_when=social.where_when_out(capture, state.utc_offset),
        **(_safety_out(species.slug, state.code) if matched else {}),
    )


def _safety_out(slug: str, state_code: str | None) -> dict:
    """The capture screen's safety fields for an animal with a safety rating."""
    d = dex.details(slug, state_code)
    if not bonds.careful(d.get("safety")):
        return {}
    return {"safety": d["safety"], "safe_distance": d.get("safe_distance") or None,
            "safety_note": d.get("safety_note") or None, "safety_tip": bonds.SAFE_TIP}


def _score_capture(model, capture: Capture, slug: str, rarity: str, image: Image.Image, state_code: str,
                   allowed: set[str], new_badge: bool, confidence: float | None = None) -> ScoreOut:
    """Score the photo for the species it counts as and keep the result on the capture."""
    safety = dex.details(slug, state_code).get("safety") or "none"
    sc = scoring.score_photo(model, image, slug, allowed, confidence=confidence, rarity=rarity,
                             safety=safety, new_species=new_badge,
                             activity=dex.activity(slug, state_code))
    capture.score, capture.score_stars, capture.score_parts = sc.total, sc.stars, sc.to_json()
    return score_out(capture)



def score_old_photos(db: Session, model, pause: float = 0.0) -> int:
    """Score photos taken before scoring existed, and re-score ones scored
    before the lighting part was added. Returns how many were scored. `pause`
    (seconds) between photos keeps the machine responsive."""
    stale = [c for c in db.scalars(select(Capture).where(Capture.species_id.is_not(None)).order_by(Capture.id))
             if c.score_parts is None or "Lighting" not in c.score_parts]
    done = 0
    for c in stale:
        if not _rescore(db, model, c):
            continue
        db.commit()
        done += 1
        if pause:
            time.sleep(pause)
    return done


def _rescore(db: Session, model, c: Capture) -> bool:
    """Score a saved capture again for the species it counts as. False if the
    photo is gone."""
    data = get_storage().get(c.image_path) if c.image_path else None
    if data is None or model is None or c.species_id is None:
        return False
    user = db.get(User, c.user_id)
    state = st.get(c.state or user.state) or st.get(None)
    members = {m.species.slug: m for m in state_species(db, state.code)}
    species = db.get(Species, c.species_id)
    m = members.get(species.slug)
    first = db.scalar(select(Badge.first_capture_id).where(Badge.user_id == c.user_id,
                                                           Badge.species_id == c.species_id))
    image = Image.open(io.BytesIO(data)).convert("RGB")
    # The model's own pick on the whole photo already has its confidence;
    # a player's pick is scored from scratch.
    confidence = c.confidence if not c.user_picked and c.predicted_label == species.slug else None
    _score_capture(model, c, species.slug, m.rarity if m else species.rarity, image, state.code,
                   set(members), first == c.id, confidence=confidence)
    return True


def _score_old_photos_in_background() -> None:
    """Once per startup, at a gentle pace; a no-op when everything is scored."""
    try:
        with SessionLocal() as db:
            n = score_old_photos(db, clf.get_classifier(), pause=0.5)
        if n:
            logging.getLogger(__name__).info("Scored %d older photos", n)
    except Exception:
        logging.getLogger(__name__).exception("Scoring older photos failed")


def score_out(capture: Capture) -> ScoreOut | None:
    if capture.score is None:
        return None
    parts = json.loads(capture.score_parts or "[]")
    return ScoreOut(total=capture.score, stars=capture.score_stars or 1,
                    parts=[ScorePart(label=label, points=pts) for label, pts in parts])


def _first_in_state(db: Session, capture: Capture) -> bool:
    """Whether this is the player's first capture of its animal in its state."""
    return db.scalar(select(Capture.id).where(
        Capture.user_id == capture.user_id, Capture.species_id == capture.species_id,
        Capture.state == capture.state, Capture.id != capture.id).limit(1)) is None


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
    """'Wrong animal?': the player names the animal themselves from the model's
    top guesses, or says "none" of them. We trust their pick and award the badge,
    and keep the correction so it can help retrain the model."""
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

    if capture.top_labels is not None and body.label not in guesses:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Pick one of the suggested animals")
    species = db.scalar(select(Species).where(Species.slug == body.label))
    if species is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Unknown species")
    m = state_member(db, user.state, species.id)

    name = m.common_name if m else species.common_name
    new_badge = False
    album_photo = None
    if capture.species_id != species.id:
        _unassign_capture(db, capture)
        capture.species_id = species.id
        capture.user_picked = True
        capture.state = capture.state or user.state
        badge = db.scalar(select(Badge).where(Badge.user_id == user.id, Badge.species_id == species.id))
        if badge:
            badge.capture_count += 1
        else:
            db.add(Badge(user_id=user.id, species_id=species.id, first_capture_id=capture.id))
        new_badge = _first_in_state(db, capture)
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
                      score=score_out(capture), bond=bond, bond_up=bond_up,
                      where_when=social.where_when_out(capture, (st.get(user.state) or st.get(None)).utc_offset),
                      **_safety_out(species.slug, capture.state or user.state))


@app.put("/captures/{capture_id}/where-when", response_model=WhereWhenResult)
def set_where_when(capture_id: int, body: WhereWhenIn, user: User = Depends(current_user),
                   db: Session = Depends(get_db)):
    """The player fixes when and where they took a photo (the photo's metadata
    can be missing or wrong). The place must be in the state the capture counts
    in and the time no later than the upload. Field notes and the place name
    follow; the photo score doesn't depend on either."""
    capture = db.get(Capture, capture_id)
    if capture is None or capture.user_id != user.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Capture not found")
    state = st.get(capture.state or user.state) or st.get(None)
    taken = (_local(body.taken_at, state) if body.taken_at.tzinfo else body.taken_at).replace(microsecond=0)
    uploaded = _local(capture.created_at or datetime.now(timezone.utc), state)
    # A few minutes' slack for clocks that disagree.
    if taken > max(uploaded, _local_now(state)) + timedelta(minutes=5):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "That's after the photo was uploaded")
    if taken < datetime(1990, 1, 1):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "That's too long ago")
    if (body.latitude is None) != (body.longitude is None):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Give both latitude and longitude, or neither")
    if body.latitude is not None and not places.in_state(state, body.latitude, body.longitude):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, f"Pick a place in {state.name}")

    before_bond = _sightings(db, user.id, state.utc_offset, capture.species_id).get(capture.species_id, []) \
        if capture.species_id else []
    old_time = capture.taken_at.replace(tzinfo=None) if capture.taken_at else uploaded
    if taken != old_time.replace(microsecond=0):
        capture.taken_at, capture.time_source = taken, "edited"
    old_place = (capture.latitude, capture.longitude)
    new_place = (body.latitude, body.longitude)
    if old_place != new_place and not (old_place[0] is not None and new_place[0] is not None
                                       and abs(old_place[0] - new_place[0]) < 1e-5
                                       and abs(old_place[1] - new_place[1]) < 1e-5):
        capture.latitude, capture.longitude = new_place
        capture.place_source = "edited" if new_place[0] is not None else None
    db.commit()

    bond, bond_up = None, []
    if capture.species_id is not None:
        after = _sightings(db, user.id, state.utc_offset, capture.species_id).get(capture.species_id, [])
        safety = _safety(db, capture.species_id, state.code)
        bond = bonds.level(bonds.notes(after, safety))
        bond_up = bonds.newly_done(before_bond, after, safety)
    return WhereWhenResult(where_when=social.where_when_out(capture, state.utc_offset), score=score_out(capture),
                           bond=bond, bond_up=bond_up)


def _record_feedback(db: Session, capture: Capture, user: User, guesses: list[str], chosen: str | None) -> None:
    """Keep the player's correction (one row per capture). Picking the model's own
    best guess isn't a correction, so it clears any earlier one."""
    row = db.scalar(select(IdFeedback).where(IdFeedback.capture_id == capture.id))
    if chosen == capture.predicted_label:
        if row:
            db.delete(row)
        return
    source = "none" if chosen is None else "guesses"
    if row is None:
        row = IdFeedback(capture_id=capture.id, user_id=user.id)
        db.add(row)
    row.state = (st.get(user.state) or st.get(None)).code
    row.predicted_label = capture.predicted_label
    row.rejected_labels = ",".join(g for g in guesses if g != chosen) or capture.predicted_label
    row.chosen_label = chosen
    row.source = source


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
    """The player's Field Guide for their state (or ?state=). Captures count only
    in the state they were made in: a coyote captured in California has to be
    captured again to count in North Carolina."""
    return _collection(db, user, user, state_or_404(state or user.state))


@app.get("/users/{username}/collection", response_model=CollectionOut)
def user_collection(username: str, state: str | None = Query(None), user: User = Depends(current_user),
                    db: Session = Depends(get_db)):
    """A friend's Field Guide: their primary state (the one they play in) unless
    ?state= picks another. `places` lists their primary state plus every state
    where they've captured something on that state's list. Friends only: anyone
    else sees just what the profile shows."""
    owner = user_named(db, username)
    if not owner:
        raise HTTPException(404, "No such user")
    if owner.id != user.id and owner.id not in friend_ids(db, user.id):
        raise HTTPException(403, "Only friends can see each other's Field Guide")
    out = _collection(db, owner, user, state_or_404(state or owner.state))
    caught = dict(db.execute(
        select(Capture.state, func.count(func.distinct(Capture.species_id)))
        .where(Capture.user_id == owner.id, Capture.species_id.is_not(None)).group_by(Capture.state)).all())
    out.primary_state = owner.state
    out.places = [PlaceOut(state=s.code, name=s.name, caught=caught.get(s.code, 0))
                  for s in st.all_states() if s.code == owner.state or caught.get(s.code)]
    return out


def _collection(db: Session, owner: User, viewer: User, st_: st.State) -> CollectionOut:
    """`owner`'s Field Guide as `viewer` sees it. Names follow the viewer's own
    reveals (theirs and their friends' badges, which covers a friend's captures);
    friends_caught counts the viewer's friends, and you_caught the viewer."""
    code = st_.code
    month = (datetime.now(timezone.utc) + timedelta(hours=st_.utc_offset)).month
    # Captured here (counts and dates) vs. anywhere (which reveals names).
    here = catches_in(db, owner.id, code)
    mine_here = here if owner.id == viewer.id else catches_in(db, viewer.id, code)
    owner_any = set(db.scalars(select(Badge.species_id).where(Badge.user_id == owner.id)))
    mine = owner_any if owner.id == viewer.id else set(
        db.scalars(select(Badge.species_id).where(Badge.user_id == viewer.id)))
    friends = friend_ids(db, viewer.id)
    friends_caught = dict(db.execute(
        select(Badge.species_id, func.count()).where(Badge.user_id.in_(friends))
        .group_by(Badge.species_id)).all()) if friends else {}
    photos = {sid: (path, score, stars) for sid, path, score, stars in db.execute(
        select(AlbumPhoto.species_id, Capture.image_path, Capture.score, Capture.score_stars)
        .join(Capture, Capture.id == AlbumPhoto.capture_id).where(AlbumPhoto.user_id == owner.id))}
    storage = get_storage()
    bond_levels = {sid: bonds.level(bonds.notes(sg, _safety(db, sid, code)))
                   for sid, sg in _sightings(db, owner.id, st_.utc_offset).items()}
    entries = []
    for m in state_species(db, code):
        b = here.get(m.species_id)
        revealed = m.species_id in owner_any or m.species_id in mine or friends_caught.get(m.species_id, 0) > 0
        entries.append(CollectionEntry(
            species=species_out(m.species, revealed, m),
            caught=b is not None, capture_count=b[0] if b else 0,
            earned_at=b[1] if b else None, friends_caught=friends_caught.get(m.species_id, 0),
            you_caught=m.species_id in mine_here,
            photo_url=storage.url(photos[m.species_id][0]) if m.species_id in photos else None,
            photo_score=photos[m.species_id][1] if m.species_id in photos else None,
            photo_stars=photos[m.species_id][2] if m.species_id in photos else None,
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
    caught = set(catches_in(db, user.id, code))
    revealed = revealed_species_ids(db, user)
    out = []
    for s in goals.sets_for(code, set(members)):
        rows = [SetSpecies(species=species_out(members[x].species, members[x].species_id in revealed, members[x]),
                           caught=members[x].species_id in caught) for x in s.slugs]
        n = sum(r.caught for r in rows)
        careful = any(bonds.careful(dex.details(x, code).get("safety")) for x in s.slugs)
        out.append(SetOut(id=s.id, title=s.title, description=s.description, caught=n, total=len(rows),
                          complete=n == len(rows), species=rows, safety_tip=bonds.SAFE_TIP if careful else None))
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

    new_ids = {sid for sid, (_, first) in catches_in(db, user.id, state.code).items()
               if start <= _aware(first) < end}
    week = []
    for c in db.scalars(select(Capture).where(Capture.user_id == user.id, Capture.species_id.is_not(None),
                                              Capture.state == state.code)):
        m = members.get(c.species_id)
        if m and start <= _aware(c.created_at) < end:
            week.append(goals.WeekCapture(m.species.slug, m.species.category, m.rarity,
                                          c.species_id in new_ids))
    likes = sum(start <= _aware(t) < end for t in db.scalars(
        select(PhotoLike.created_at).where(PhotoLike.user_id == user.id)))
    out = []
    for ch in challenges:
        p = goals.progress(ch, week, likes)
        pool = ([m.species.slug for m in members.values() if m.species.category == ch.category]
                if ch.kind == "category" else list(ch.slugs))
        careful = any(bonds.careful(dex.details(x, state.code).get("safety")) for x in pool)
        out.append(ChallengeOut(id=ch.id, title=ch.title, progress=min(p, ch.goal), goal=ch.goal, done=p >= ch.goal,
                                safety_tip=bonds.SAFE_TIP if careful else None))
    return ChallengesOut(state=state.code, week_start=start, week_end=end, challenges=out,
                         done=sum(c.done for c in out))


# --- bonds (app/bonds.py) ---------------------------------------------------

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


def _safety(db: Session, species_id: int, state_code: str | None) -> str:
    """The animal's safety rating ("none", "caution" or "danger") in the state."""
    sp = db.get(Species, species_id)
    return (dex.details(sp.slug, state_code).get("safety") or "none") if sp else "none"


def _bond_after(db: Session, user: User, capture: Capture) -> tuple[int, list[str]]:
    """Bond hearts with the capture's animal now, and the field notes it ticked."""
    offset = (st.get(user.state) or st.get(None)).utc_offset
    safety = _safety(db, capture.species_id, capture.state or user.state)
    after = _sightings(db, user.id, offset, capture.species_id).get(capture.species_id, [])
    before = _sightings(db, user.id, offset, capture.species_id, skip_capture=capture.id).get(capture.species_id, [])
    return bonds.level(bonds.notes(after, safety)), bonds.newly_done(before, after, safety)


def _bond_out(species: Species, m: StateSpecies | None, sightings: list[bonds.Sighting],
              state_code: str | None = None) -> BondOut:
    ns = bonds.notes(sightings, dex.details(species.slug, state_code or (m.state if m else None)).get("safety"))
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
        out.append(_bond_out(sp, members.get(species_id), sightings, state.code))
    out.sort(key=lambda b: (-b.level, b.species.common_name or ""))
    return BondsOut(state=state.code, bonds=out)
