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


def signup(client, name="ana"):
    r = client.post("/auth/register", json={"email": f"{name}@example.com", "username": name,
                                            "password": "hunter22!"})
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
    # Runner-up guesses don't reveal species the player hasn't unlocked.
    assert r["top_predictions"][0]["common_name"] == "Coyote"
    assert r["top_predictions"][1] == {"label": "hidden", "common_name": None, "probability": 0.04}

    r = upload(client, h).json()
    assert r["matched"] and not r["new_badge"]

    col = client.get("/me/collection", headers=h).json()
    assert col["caught"] == 1 and col["total"] == 100
    coyote = next(e for e in col["entries"] if e["species"]["slug"] == "coyote")
    assert coyote["caught"] and coyote["capture_count"] == 2

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
    from pathlib import Path
    dex.load(settings.details_csv, Path(ranges))

    # Before catching: size, weight and map are hints; name and fun fact are locked.
    r = client.get("/species/coyote/dex").json()
    assert r["species"]["common_name"] is None and r["fun_fact"] is None
    # Tips can name the animal, so they wait too; active time and parks are hints.
    assert r["where_to_find"] is None and r["spotting_tip"] is None
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
    dex.load(settings.details_csv, settings.ranges_json, None, tmp / "seasons.json")
    owl = client.get("/species/barn_owl/dex").json()["season"]
    assert owl["months"][3] == 9 and owl["night_ratio"] == 2.0
    assert client.get("/species/coyote/dex").json()["season"]["night_ratio"] == 0.0
    assert client.get("/species/bobcat/dex").json()["season"] is None
    dex.load(settings.details_csv, settings.ranges_json, settings.hotspots_json, settings.seasons_json)


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
    dex.load(settings.details_csv, settings.ranges_json, tmp / "hotspots.json")

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
    assert r["active_time"] and r["spotting_tip"] is None


def test_login_rate_limit(client):
    signup(client, "carol")
    for _ in range(10):
        assert client.post("/auth/login", data={"username": "carol", "password": "wrong-pass"}).status_code == 401
    r = client.post("/auth/login", data={"username": "carol", "password": "hunter2hunter2"})
    assert r.status_code == 429


def test_sprites(client):
    r = client.get("/sprites/coyote.png")
    assert r.status_code == 200 and r.headers["content-type"] == "image/png"
    assert client.get("/sprites/coyote_silhouette.png").status_code == 200
    assert client.get("/sprites/nope.png").status_code == 404
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
