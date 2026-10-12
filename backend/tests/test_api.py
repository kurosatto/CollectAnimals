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
    assert r["size"] and r["weight"]
    assert r["range"]["cells"] == [[10, 20, 5]] and r["range"]["grid"]["step"] == 0.25

    h = signup(client)
    fake.next = [Prediction("coyote", 0.93)]
    upload(client, h)
    r = client.get("/species/coyote/dex", headers=h).json()
    assert r["species"]["common_name"] == "Coyote" and r["fun_fact"]

    r = client.get("/species/bobcat/dex", headers=h).json()
    assert r["fun_fact"] is None and r["range"] is None and r["size"]
    assert client.get("/species/nope/dex").status_code == 404


def test_california_outline(client):
    r = client.get("/map/california")
    assert r.status_code == 200 and len(r.json()["rings"][0]) > 100
