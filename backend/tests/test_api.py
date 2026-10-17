import io
import os
import tempfile

_tmp = tempfile.mkdtemp()
os.environ["DATABASE_URL"] = f"sqlite:///{_tmp}/test.db"
os.environ["UPLOAD_DIR"] = f"{_tmp}/uploads"
os.environ["MODEL_PATH"] = f"{_tmp}/missing.pt"
os.environ["SECRET_KEY"] = "test-secret-key-that-is-at-least-32-bytes"

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from PIL import Image  # noqa: E402

from app import classifier as clf  # noqa: E402
from app.classifier import Prediction  # noqa: E402
from app.db import Base, engine  # noqa: E402
from app.main import app  # noqa: E402


class FakeClassifier:
    """Returns whatever predictions the test queues up."""

    def __init__(self):
        self.next = [Prediction("other", 0.9)]

    def predict(self, image, k=3):
        return self.next[:k]


@pytest.fixture
def fake():
    f = FakeClassifier()
    clf._classifier = f
    yield f
    clf._classifier = None


@pytest.fixture
def client():
    Base.metadata.drop_all(engine)
    with TestClient(app) as c:
        yield c


def jpeg_bytes():
    buf = io.BytesIO()
    Image.new("RGB", (64, 48), "green").save(buf, "JPEG")
    return buf.getvalue()


def signup(client, name="ana", state=None):
    body = {"email": f"{name}@example.com", "username": name, "password": "hunter22!"}
    if state:
        body["state"] = state
    r = client.post("/auth/register", json=body)
    assert r.status_code == 201, r.text
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


def upload(client, headers):
    return client.post("/captures", headers=headers,
                       files={"photo": ("p.jpg", jpeg_bytes(), "image/jpeg")})


def test_species_seeded(client, fake):
    species = client.get("/species").json()
    assert len(species) == 100
    # Names stay hidden until caught.
    assert all(s["common_name"] is None and s["slug"] is None for s in species)
    hidden = client.get("/species/coyote").json()
    assert hidden["revealed"] is False and hidden["scientific_name"] is None
    assert hidden["rarity"] and hidden["category"]

    h = signup(client)
    fake.next = [Prediction("coyote", 0.93)]
    upload(client, h)
    r = client.get("/species/coyote", headers=h).json()
    assert r["revealed"] and r["scientific_name"] == "Canis latrans"
    assert client.get(f"/species/{r['number']}", headers=h).json()["slug"] == "coyote"


def test_safety_on_dex_entry(client):
    bear = client.get("/species/american_black_bear/dex").json()
    assert bear["safety"] == "danger" and bear["safe_distance"] and bear["safety_note"]
    assert client.get("/species/house_finch/dex").json()["safety"] == "none"


def test_dropped_species_are_retired(client, tmp_path):
    from app import states
    from app.db import SessionLocal
    from app.main import seed_species
    ca = states.get("CA")
    trimmed = tmp_path / "species.csv"
    lines = ca.species_csv.read_text(encoding="utf-8").splitlines()
    trimmed.write_text("\n".join(l for l in lines if not l.startswith(("garibaldi,", "coyote,")))
                       + "\n", encoding="utf-8")
    with SessionLocal() as db:
        seed_species(db, with_files("CA", species_csv=trimmed))
    assert client.get("/species/garibaldi").status_code == 404  # on no list any more
    assert len(client.get("/species").json()) == 98
    # The coyote left California's list but is still on North Carolina's.
    assert "coyote" not in {s["slug"] for s in client.get("/species").json()}
    assert client.get("/species/coyote", params={"state": "NC"}).status_code == 200
    with SessionLocal() as db:
        seed_species(db, states.all_states())
    assert client.get("/species/garibaldi").status_code == 200


def test_register_login_me(client):
    signup(client)
    assert client.post("/auth/register", json={"email": "ANA@example.com", "username": "other",
                                               "password": "hunter22!"}).status_code == 409
    for ident in ("ana", "ana@example.com"):
        r = client.post("/auth/login", data={"username": ident, "password": "hunter22!"})
        assert r.status_code == 200
    assert client.post("/auth/login", data={"username": "ana", "password": "nope"}).status_code == 401
    token = r.json()["access_token"]
    assert client.get("/me", headers={"Authorization": f"Bearer {token}"}).json()["username"] == "ana"
    assert client.get("/me", headers={"Authorization": "Bearer garbage"}).status_code == 401


def test_usernames_ignore_case(client):
    from app.db import SessionLocal
    from app.models import User

    h = signup(client, "Kuro")
    # Sign-up treats "kuro" as taken; login and lookups work in any case.
    assert client.post("/auth/register", json={"email": "k2@example.com", "username": "KURO",
                                               "password": "hunter22!"}).status_code == 409
    r = client.post("/auth/login", data={"username": "kURo", "password": "hunter22!"})
    assert r.status_code == 200
    assert client.get("/me", headers={"Authorization": f"Bearer {r.json()['access_token']}"}).json()["username"] == "Kuro"
    ana = signup(client, "ana")
    assert client.post("/friends/requests", json={"username": "KURO"}, headers=ana).status_code == 201
    assert client.post("/friends/requests/ANA/accept", headers=h).status_code == 200
    assert client.get("/users/kuro", headers=ana).json()["username"] == "Kuro"
    # Older accounts whose names differ only in case: an exact match wins.
    with SessionLocal() as db:
        db.add(User(email="old@example.com", username="kuro", password_hash="x", state="CA"))
        db.commit()
    assert client.get("/users/kuro", headers=ana).json()["username"] == "kuro"
    assert client.get("/users/Kuro", headers=ana).json()["username"] == "Kuro"


def with_files(code, **paths):
    """The real states, with one state's map files swapped for test files."""
    import dataclasses
    from pathlib import Path

    from app import states
    return [dataclasses.replace(s, **{k: Path(v) for k, v in paths.items()}) if s.code == code else s
            for s in states.all_states()]


def test_capture_requires_auth(client, fake):
    assert upload(client, {}).status_code == 401


def test_capture_without_model_is_503(client):
    assert upload(client, signup(client)).status_code == 503


def test_capture_awards_badge_once(client, fake):
    h = signup(client)
    fake.next = [Prediction("coyote", 0.93), Prediction("gray_fox", 0.04), Prediction("other", 0.02)]
    r = upload(client, h).json()
    assert r["matched"] and r["new_badge"]
    assert r["species"]["slug"] == "coyote"
    # Scored, with the new-species bonus the first time.
    assert r["score"]["stars"] in (1, 2, 3, 4, 5)
    assert {p["label"] for p in r["score"]["parts"]} >= {"Clarity", "Sharpness", "Framing", "New species"}
    album = client.get("/me/album", headers=h).json()["photos"]
    assert album[0]["score"] == r["score"]["total"]
    # Runner-up guesses don't reveal species the player hasn't unlocked.
    assert r["top_predictions"][0]["common_name"] == "Coyote"
    assert r["top_predictions"][1] == {"label": "hidden", "common_name": None, "probability": 0.0404}  # rescaled within the state

    r = upload(client, h).json()
    assert r["matched"] and not r["new_badge"]

    col = client.get("/me/collection", headers=h).json()
    assert col["caught"] == 1 and col["total"] == 100
    coyote = next(e for e in col["entries"] if e["species"]["slug"] == "coyote")
    assert coyote["caught"] and coyote["capture_count"] == 2
    # Habitat scene: coyotes are out at dawn and dusk; uncaught animals carry no hint.
    assert coyote["activity"] == "any"
    assert all(e["activity"] is None for e in col["entries"] if not e["caught"])

    # Badges are per user.
    assert client.get("/me/collection", headers=signup(client, "bob")).json()["caught"] == 0


def test_low_confidence_and_other_do_not_match(client, fake):
    h = signup(client)
    fake.next = [Prediction("bobcat", 0.41), Prediction("gray_fox", 0.3)]
    r = upload(client, h).json()
    assert not r["matched"] and r["species"] is None
    assert "Bobcat" not in r["message"] and "haven't discovered" in r["message"]

    fake.next = [Prediction("bobcat", 0.95)]
    upload(client, h)
    fake.next = [Prediction("bobcat", 0.41), Prediction("gray_fox", 0.3)]
    r = upload(client, h).json()
    assert not r["matched"] and "Bobcat" in r["message"]

    fake.next = [Prediction("other", 0.97)]
    r = upload(client, h).json()
    assert not r["matched"] and r["top_predictions"][0]["common_name"] is None
    assert client.get("/me/collection", headers=h).json()["caught"] == 1


def test_rejects_non_image(client, fake):
    r = client.post("/captures", headers=signup(client),
                    files={"photo": ("x.jpg", b"not an image", "image/jpeg")})
    assert r.status_code == 400


def test_dex_entry(client, fake):
    from app import dex
    from app.config import settings

    tmp = tempfile.mkdtemp()
    ranges = os.path.join(tmp, "ranges.json")
    with open(ranges, "w") as fh:
        fh.write('{"grid": {"lon0": -124.5, "lat0": 32.5, "step": 0.25, "cols": 42, "rows": 38},'
                 ' "species": {"coyote": [[10, 20, 5]]}}')
    dex.load(settings.details_csv, with_files("CA", ranges=ranges))

    # Before catching: size, weight and map are hints; name and fun fact are locked.
    r = client.get("/species/coyote/dex").json()
    assert r["species"]["common_name"] is None and r["fun_fact"] is None
    # Tips show before the capture, with the name masked out; active time and parks are hints.
    assert r["where_to_find"] and r["spotting_tip"]
    assert "coyote" not in (r["where_to_find"] + r["spotting_tip"]).lower()
    assert r["size"] and r["weight"] and r["active_time"]
    assert r["range"]["cells"] == [[10, 20, 5]] and r["range"]["grid"]["step"] == 0.25

    h = signup(client)
    fake.next = [Prediction("coyote", 0.93)]
    upload(client, h)
    r = client.get("/species/coyote/dex", headers=h).json()
    assert r["species"]["common_name"] == "Coyote" and r["fun_fact"] and r["where_to_find"]

    r = client.get("/species/bobcat/dex", headers=h).json()
    assert r["fun_fact"] is None and r["range"] is None and r["size"]
    assert client.get("/species/nope/dex").status_code == 404


def test_dex_season_compares_night_sightings_with_the_average(client):
    import json
    from pathlib import Path

    from app import dex
    from app.config import settings

    day = [0] * 6 + [10] * 14 + [0] * 4      # all daytime
    night = [10] * 6 + [0] * 14 + [10] * 4   # all night
    tmp = Path(tempfile.mkdtemp())
    (tmp / "seasons.json").write_text(json.dumps({"species": {
        "coyote": {"months": [1] * 12, "hours": day},
        "barn_owl": {"months": [0, 0, 5, 9, 9, 5, 0, 0, 0, 0, 0, 0], "hours": night}}}))
    from dataclasses import replace

    from app import states as st

    real = st.all_states()
    dex.load(settings.details_csv, [replace(s, seasons=tmp / "seasons.json") if s.code == "CA" else s
                                    for s in real])
    owl = client.get("/species/barn_owl/dex").json()["season"]
    assert owl["months"][3] == 9 and owl["night_ratio"] == 2.0
    assert client.get("/species/coyote/dex").json()["season"]["night_ratio"] == 0.0
    assert client.get("/species/bobcat/dex").json()["season"] is None
    dex.load(settings.details_csv, real)


def test_collection_marks_species_in_season(client):
    import json
    from dataclasses import replace
    from datetime import datetime, timedelta, timezone
    from pathlib import Path

    from app import dex
    from app import states as st
    from app.config import settings

    month = (datetime.now(timezone.utc) - timedelta(hours=8)).month
    now_only = [0] * 12
    now_only[month - 1] = 9
    never_now = [9] * 12
    never_now[month - 1] = 1
    tmp = Path(tempfile.mkdtemp())
    (tmp / "seasons.json").write_text(json.dumps({"species": {
        "coyote": {"months": now_only, "hours": [1] * 24},
        "ringtail": {"months": never_now, "hours": [1] * 24}}}))
    real = st.all_states()
    dex.load(settings.details_csv, [replace(s, seasons=tmp / "seasons.json") if s.code == "CA" else s
                                    for s in real])
    try:
        entries = client.get("/me/collection", headers=signup(client, "sky")).json()["entries"]
        by_num = {e["species"]["number"]: e["in_season"] for e in entries}
        from app.db import SessionLocal
        from app.models import Species
        with SessionLocal() as db:
            num = {s.slug: s.id for s in db.query(Species)}
        assert by_num[num["coyote"]] is True
        assert by_num[num["ringtail"]] is False
        assert by_num[num["bobcat"]] is True  # no data: can't rule it out
    finally:
        dex.load(settings.details_csv, real)


def test_california_outline(client):
    r = client.get("/map/california")
    assert r.status_code == 200 and len(r.json()["rings"][0]) > 100


def test_hotspots(client, fake):
    import json
    from pathlib import Path

    from app import dex
    from app.config import settings

    tmp = Path(tempfile.mkdtemp())
    (tmp / "hotspots.json").write_text(json.dumps({"parks": [
        {"id": "small", "name": "Small Park", "lat": 34.0, "lon": -118.0, "blurb": "b",
         "species": [{"slug": "coyote", "observations": 24}]},
        {"id": "big", "name": "Big Park", "lat": 36.5, "lon": -121.2, "blurb": "b",
         "species": [{"slug": "california_condor", "observations": 800},
                     {"slug": "coyote", "observations": 50}, {"slug": "not_listed", "observations": 9}]},
    ]}))
    dex.load(settings.details_csv, with_files("CA", hotspots=tmp / "hotspots.json"))

    parks = client.get("/hotspots").json()
    assert [p["name"] for p in parks] == ["Big Park", "Small Park"]
    # Names stay hidden until caught.
    assert [s["common_name"] for s in parks[0]["species"]] == [None, None]

    h = signup(client)
    fake.next = [Prediction("california_condor", 0.95)]
    upload(client, h)
    parks = client.get("/hotspots", headers=h).json()
    assert [s["slug"] for s in parks[0]["species"]] == ["california_condor", None]
    assert parks[0]["species"][0]["common_name"] == "California Condor"

    r = client.get("/species/coyote/dex").json()
    assert r["hotspots"] == ["Big Park", "Small Park"]
    assert r["active_time"] and r["spotting_tip"] and "coyote" not in r["spotting_tip"].lower()


def test_login_rate_limit(client):
    signup(client, "carol")
    for _ in range(10):
        assert client.post("/auth/login", data={"username": "carol", "password": "wrong-pass"}).status_code == 401
    r = client.post("/auth/login", data={"username": "carol", "password": "hunter2hunter2"})
    assert r.status_code == 429


def test_states_and_signup_state(client):
    states = {s["code"]: s for s in client.get("/states").json()}
    assert states["CA"]["species_count"] == 100 and states["NC"]["species_count"] == 100
    assert states["NC"]["name"] == "North Carolina" and states["NC"]["bounds"]["west"] < -84

    h = signup(client, "nina", state="nc")
    assert client.get("/me", headers=h).json()["state"] == "NC"
    assert client.get("/me", headers=signup(client)).json()["state"] == "CA"  # default
    r = client.post("/auth/register", json={"email": "x@example.com", "username": "xx",
                                            "password": "hunter22!", "state": "ZZ"})
    assert r.status_code == 422


def seen_everything(client):
    """Headers for a player who has captured every species, so names show."""
    from app.db import SessionLocal
    from app.models import Badge, Capture, Species, User

    h = signup(client, "seer")
    with SessionLocal() as db:
        uid = db.query(User).filter_by(username="seer").one().id
        for s in db.query(Species).all():
            c = Capture(user_id=uid, species_id=s.id, image_path="", predicted_label=s.slug, confidence=1.0)
            db.add(c)
            db.flush()
            db.add(Badge(user_id=uid, species_id=s.id, first_capture_id=c.id))
        db.commit()
    return h


def test_species_per_state(client):
    h = seen_everything(client)
    nc = client.get("/species", params={"state": "NC"}, headers=h).json()
    assert len(nc) == 100 and nc[0]["slug"] == "red_wolf"
    assert "northern_cardinal" in {s["slug"] for s in nc}
    assert "california_condor" not in {s["slug"] for s in nc}
    assert client.get("/species", headers=h).json()[0]["slug"] == "ringtail"  # California by default
    # Shared species: one identity, rarity and name per state.
    assert client.get("/species/american_black_bear").json()["rarity"] == "rare"
    assert client.get("/species/american_black_bear", params={"state": "NC"}).json()["rarity"] == "uncommon"
    assert client.get("/species/elk", params={"state": "NC"}, headers=h).json()["common_name"] == "Elk"
    assert client.get("/species", params={"state": "TX"}).status_code == 404


def test_change_state_and_shared_badges(client, fake):
    h = signup(client)
    fake.next = [Prediction("coyote", 0.95)]
    assert upload(client, h).json()["new_badge"]

    r = client.patch("/me", headers=h, json={"state": "NC"})
    assert r.status_code == 200 and r.json()["state"] == "NC"
    col = client.get("/me/collection", headers=h).json()
    assert col["state"] == "NC" and col["total"] == 100 and col["caught"] == 1  # coyote counts here too
    ca = client.get("/me/collection", headers=h, params={"state": "CA"}).json()
    assert ca["state"] == "CA" and ca["caught"] == 1
    assert client.patch("/me", headers=h, json={"state": "ZZ"}).status_code == 404


def test_capture_only_counts_the_players_state(client, fake):
    h = signup(client, "nina", state="NC")
    # The model splits a bluebird photo between the western (CA) and eastern (NC)
    # bluebird; in North Carolina only the eastern one is possible.
    fake.next = [Prediction("western_bluebird", 0.5), Prediction("eastern_bluebird", 0.4),
                 Prediction("other", 0.1)]
    r = upload(client, h).json()
    assert r["matched"] and r["species"]["slug"] == "eastern_bluebird"
    assert r["confidence"] == 0.8 and [p["label"] for p in r["top_predictions"]] == ["eastern_bluebird", "other"]

    fake.next = [Prediction("california_condor", 0.99), Prediction("other", 0.01)]
    r = upload(client, h).json()
    assert not r["matched"] and "North Carolina" in r["message"]


def test_dex_entry_per_state(client):
    h = seen_everything(client)
    r = client.get("/species/american_alligator/dex", params={"state": "NC"}, headers=h).json()
    assert "Greenfield Lake" in r["where_to_find"] and r["size"]
    assert r["safety"] == "danger" and r["safe_distance"] and r["safety_note"]
    # Shared species: North Carolina text replaces California-only text.
    ca = client.get("/species/elk/dex", headers=h).json()
    nc = client.get("/species/elk/dex", params={"state": "NC"}, headers=h).json()
    assert "Point Reyes" in ca["where_to_find"] and "Cataloochee" in nc["where_to_find"]
    assert "Tule" in ca["fun_fact"] and "Tule" not in nc["fun_fact"]
    assert nc["size"] == ca["size"] and nc["safety"] == ca["safety"] == "danger"
    assert "Smoky" in nc["safety_note"] and "Smoky" not in ca["safety_note"]
    assert client.get("/map/NC").json()["rings"]


def test_old_database_gets_state_column(client):
    from sqlalchemy import inspect, text

    from app.db import engine
    from app.main import add_state_column

    with engine.begin() as conn:
        conn.execute(text("DROP TABLE IF EXISTS users_old"))
        conn.execute(text("CREATE TABLE users_old (id INTEGER PRIMARY KEY, email VARCHAR(255))"))
    # Pretend users_old is the users table of an old install.
    with engine.begin() as conn:
        conn.execute(text("ALTER TABLE users RENAME TO users_new"))
        conn.execute(text("ALTER TABLE users_old RENAME TO users"))
        conn.execute(text("INSERT INTO users (id, email) VALUES (1, 'a@example.com')"))
    try:
        add_state_column()
        assert "state" in {c["name"] for c in inspect(engine).get_columns("users")}
        with engine.begin() as conn:
            assert conn.execute(text("SELECT state FROM users")).scalar() == "CA"
    finally:
        with engine.begin() as conn:
            conn.execute(text("DROP TABLE users"))
            conn.execute(text("ALTER TABLE users_new RENAME TO users"))


def test_sprites(client):
    r = client.get("/sprites/coyote.png")
    assert r.status_code == 200 and r.headers["content-type"] == "image/png"
    assert client.get("/sprites/coyote_silhouette.png").status_code == 200
    assert client.get("/sprites/red_wolf.png").status_code == 200  # North Carolina
    assert client.get("/sprites/nope.png").status_code == 404


def test_sprite_animations(client):
    idx = client.get("/sprites/anim/index.json").json()
    assert idx["rows"] == ["idle", "walk", "fly", "swim", "sleep"] and idx["frames"] == 4
    assert {"walk", "sleep"} <= set(idx["acts"]["mule_deer"])
    assert "fly" in idx["acts"]["american_robin"]
    r = client.get("/sprites/anim/mule_deer.png")
    assert r.status_code == 200 and r.headers["content-type"] == "image/png"
    assert client.get("/sprites/anim/nope.png").status_code == 404
    assert client.get("/sprites/anim/..%2Fcoyote.png").status_code == 404
    assert client.get("/sprites/..%2Fcalifornia_100.png").status_code == 404


def test_player_picks_the_animal_when_model_is_unsure(client, fake):
    h = signup(client)
    fake.next = [Prediction("bobcat", 0.41), Prediction("gray_fox", 0.3), Prediction("other", 0.1),
                 Prediction("coyote", 0.08), Prediction("raccoon", 0.05)]
    r = upload(client, h).json()
    assert not r["matched"]
    # The pick list names every suggested species, but never "other".
    assert [c["slug"] for c in r["choices"]] == ["bobcat", "gray_fox", "coyote", "raccoon"]
    assert r["choices"][1]["common_name"] == "Gray Fox"
    assert len(r["top_predictions"]) == 3

    p = client.post(f"/captures/{r['capture_id']}/pick", json={"label": "gray_fox"}, headers=h).json()
    assert p["matched"] and p["new_badge"] and p["species"]["slug"] == "gray_fox"
    assert p["album_photo_id"]
    col = client.get("/me/collection", headers=h).json()
    assert col["caught"] == 1
    assert next(e for e in col["entries"] if e["species"]["slug"] == "gray_fox")["caught"]

    # Only the model's suggestions can be picked, and only by the photo's owner.
    bad = client.post(f"/captures/{r['capture_id']}/pick", json={"label": "mountain_lion"}, headers=h)
    assert bad.status_code == 400
    other = client.post(f"/captures/{r['capture_id']}/pick", json={"label": "bobcat"},
                        headers=signup(client, "bob"))
    assert other.status_code == 404


def test_player_corrects_a_wrong_match(client, fake):
    h = signup(client)
    fake.next = [Prediction("coyote", 0.9), Prediction("gray_fox", 0.05)]
    r = upload(client, h).json()
    assert r["matched"] and r["species"]["slug"] == "coyote"

    # "Not this animal": the coyote badge and album photo move to the gray fox.
    p = client.post(f"/captures/{r['capture_id']}/pick", json={"label": "gray_fox"}, headers=h).json()
    assert p["species"]["slug"] == "gray_fox" and p["new_badge"]
    caught = [e["species"]["slug"] for e in client.get("/me/collection", headers=h).json()["entries"] if e["caught"]]
    assert caught == ["gray_fox"]  # the coyote is uncaught (and hidden) again
    album = client.get("/me/album", headers=h).json()
    assert [ph["species"]["slug"] for ph in album["photos"]] == ["gray_fox"]

    # "None of these" takes the badge back.
    n = client.post(f"/captures/{r['capture_id']}/pick", json={"label": "none"}, headers=h).json()
    assert not n["matched"]
    assert client.get("/me/collection", headers=h).json()["caught"] == 0


def test_corrections_are_kept_for_retraining(client, fake):
    from app.db import SessionLocal
    from app.models import IdFeedback

    h = signup(client)
    fake.next = [Prediction("coyote", 0.9), Prediction("gray_fox", 0.05)]
    r = upload(client, h).json()
    assert r["matched"]

    # There's no typed search: animals the model didn't suggest can't be picked.
    assert client.post(f"/captures/{r['capture_id']}/pick", json={"label": "bobcat"}, headers=h).status_code == 400
    assert client.get("/species-search?q=bobc", headers=h).status_code == 404

    client.post(f"/captures/{r['capture_id']}/pick", json={"label": "gray_fox"}, headers=h)
    with SessionLocal() as db:
        fb = db.query(IdFeedback).filter_by(capture_id=r["capture_id"]).one()
        assert (fb.predicted_label, fb.rejected_labels, fb.chosen_label, fb.source) == \
            ("coyote", "coyote", "gray_fox", "guesses")

    # "None of these" keeps one row per photo, now with no animal.
    n = client.post(f"/captures/{r['capture_id']}/pick", json={"label": "none"}, headers=h).json()
    assert not n["matched"]
    with SessionLocal() as db:
        fb = db.query(IdFeedback).filter_by(capture_id=r["capture_id"]).one()
        assert (fb.rejected_labels, fb.chosen_label, fb.source) == ("coyote,gray_fox", None, "none")

    # Going back to the model's own guess isn't a correction.
    client.post(f"/captures/{r['capture_id']}/pick", json={"label": "coyote"}, headers=h)
    with SessionLocal() as db:
        assert db.query(IdFeedback).filter_by(capture_id=r["capture_id"]).count() == 0


def test_bots_befriend_new_players(client):
    from app.db import SessionLocal
    from app.models import User

    signup(client, "birdnerd")
    with SessionLocal() as db:
        db.query(User).filter_by(username="birdnerd").update({"is_bot": True})
        db.commit()
    h = signup(client, "newbie")
    friends = client.get("/friends", headers=h).json()["friends"]
    assert [(f["username"], f["is_bot"]) for f in friends] == [("birdnerd", True)]
    # The same bots add players from every state.
    nina = signup(client, "nina", state="NC")
    assert [f["username"] for f in client.get("/friends", headers=nina).json()["friends"]] == ["birdnerd"]
    # Removing a bot works like removing anyone.
    assert client.delete("/friends/birdnerd", headers=h).status_code == 204
    assert client.get("/friends", headers=h).json()["friends"] == []


def test_activity_from_active_time():
    from app import dex
    assert dex.activity("raccoon", "CA") == "night"
    assert dex.activity("coyote", "CA") == "any"
    assert dex.activity("western_fence_lizard", "CA") == "day"


def test_dex_for_animal_from_another_state(client):
    # Red wolf is only on North Carolina's list; opened from California it gets NC's entry.
    nc = client.get("/species/red_wolf/dex?state=NC").json()
    ca = client.get("/species/red_wolf/dex?state=CA").json()
    assert nc["state"] == "NC" and ca["state"] == "NC"
    assert ca["range"] == nc["range"] and ca["season"] == nc["season"] and ca["species"]["number"] == nc["species"]["number"]
    assert client.get("/species/coyote/dex?state=CA").json()["state"] == "CA"


def test_mask_name():
    from app import dex
    m = dex.mask_name
    assert m("Look for a bobcat; bobcats sit still.", "Bobcat") == "Look for a ???; ??? sit still."
    assert m("Regular black bear sightings at Big Bear Lake", "American Black Bear") == \
        "Regular ??? sightings at Big ??? Lake"
    assert m("Take a whale-watching trip", "Humpback Whale") == "Take a ???-watching trip"
    assert m("Ursus americanus lives here", "American Black Bear", "Ursus americanus") == "??? lives here"
    assert m("", "Bobcat") == "" and m(None, "Bobcat") is None


def test_states_unlock_by_choice(client, fake):
    h = signup(client)
    me = client.get("/me", headers=h).json()
    assert me["state"] == "CA" and me["unlocked_states"] == ["CA"]
    r = client.patch("/me", json={"state": "NC"}, headers=h).json()
    assert r["state"] == "NC" and r["unlocked_states"] == ["CA", "NC"]
    r = client.patch("/me", json={"state": "CA"}, headers=h).json()
    assert r["state"] == "CA" and r["unlocked_states"] == ["CA", "NC"]   # stays unlocked
    # Players keep every state they've captured in (coyote is on both lists).
    old = signup(client, "bob")
    fake.next = [Prediction("coyote", 0.93)]
    upload(client, old)
    assert client.get("/me", headers=old).json()["unlocked_states"] == ["CA", "NC"]
