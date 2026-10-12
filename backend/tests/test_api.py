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


def test_species_seeded(client):
    species = client.get("/species").json()
    assert len(species) == 100
    assert client.get("/species/coyote").json()["scientific_name"] == "Canis latrans"


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
    assert r["top_predictions"][1]["common_name"] == "Gray Fox"

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
    assert not r["matched"] and r["species"] is None and "Bobcat" in r["message"]

    fake.next = [Prediction("other", 0.97)]
    r = upload(client, h).json()
    assert not r["matched"] and r["top_predictions"][0]["common_name"] is None
    assert client.get("/me/collection", headers=h).json()["caught"] == 0


def test_rejects_non_image(client, fake):
    r = client.post("/captures", headers=signup(client),
                    files={"photo": ("x.jpg", b"not an image", "image/jpeg")})
    assert r.status_code == 400


def test_dex_entry(client):
    from app import dex
    from app.config import settings

    tmp = tempfile.mkdtemp()
    ranges = os.path.join(tmp, "ranges.json")
    with open(ranges, "w") as fh:
        fh.write('{"grid": {"lon0": -124.5, "lat0": 32.5, "step": 0.25, "cols": 42, "rows": 38},'
                 ' "species": {"coyote": [[10, 20, 5]]}}')
    from pathlib import Path
    dex.load(settings.details_csv, Path(ranges))

    r = client.get("/species/coyote/dex").json()
    assert r["species"]["common_name"] == "Coyote"
    assert r["size"] and r["weight"] and r["fun_fact"] and r["where_to_find"]
    assert r["range"]["cells"] == [[10, 20, 5]] and r["range"]["grid"]["step"] == 0.25

    r = client.get("/species/bobcat/dex").json()
    assert r["fun_fact"] and r["range"] is None
    assert client.get("/species/nope/dex").status_code == 404


def test_california_outline(client):
    r = client.get("/map/california")
    assert r.status_code == 200 and len(r.json()["rings"][0]) > 100


def test_hotspots(client):
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
    assert [s["slug"] for s in parks[0]["species"]] == ["california_condor", "coyote"]
    assert parks[0]["species"][0]["common_name"] == "California Condor"

    r = client.get("/species/coyote/dex").json()
    assert r["hotspots"] == ["Big Park", "Small Park"]
    assert r["active_time"] and r["spotting_tip"]


def test_login_rate_limit(client):
    signup(client, "carol")
    for _ in range(10):
        assert client.post("/auth/login", data={"username": "carol", "password": "wrong-pass"}).status_code == 401
    r = client.post("/auth/login", data={"username": "carol", "password": "hunter2hunter2"})
    assert r.status_code == 429
