from app.classifier import Prediction
from test_api import client, fake, jpeg_bytes, signup, upload  # noqa: F401  (fixtures)


def _none_of_these(client, fake, h):
    fake.next = [Prediction("coyote", 0.9), Prediction("gray_fox", 0.05)]
    r = upload(client, h).json()
    client.post(f"/captures/{r['capture_id']}/pick", json={"label": "none"}, headers=h)
    return r["capture_id"]


def _rows():
    from app.db import SessionLocal
    from app.models import NamedPhoto
    with SessionLocal() as db:
        return db.query(NamedPhoto).order_by(NamedPhoto.id).all()


def test_name_list_is_served_and_big(client):
    d = client.get("/species/names").json()
    assert len(d["names"]) > 3000 and "CC BY" in d["about"]
    labels = {sci for _, sci, _ in d["names"]}
    assert "Canis latrans" in labels  # every game animal is on it
    assert ["beetle", "Some kind of beetle", "ladybug"] in d["groups"]


def test_player_names_the_animal_after_none_of_these(client, fake):
    h = signup(client)
    cid = _none_of_these(client, fake, h)
    r = client.post(f"/captures/{cid}/name", json={"label": "Turdus migratorius"}, headers=h)
    assert r.status_code == 200, r.text
    assert r.json()["name"] == "American Robin" and not r.json()["photo_shared"]
    assert "an American Robin" in r.json()["message"]
    # A name never counts for a badge.
    assert client.get("/me/collection", headers=h).json()["caught"] == 0
    # One answer per photo: a new pick replaces it.
    client.post(f"/captures/{cid}/name", json={"label": "group:beetle"}, headers=h)
    rows = _rows()
    assert [(x.capture_id, x.label, x.predicted_label, x.state, x.image_path) for x in rows] == \
        [(cid, "group:beetle", "coyote", "CA", None)]


def test_names_must_come_from_the_list_and_the_photo_must_not_count(client, fake):
    h = signup(client)
    cid = _none_of_these(client, fake, h)
    assert client.post(f"/captures/{cid}/name", json={"label": "Dragon"}, headers=h).status_code == 400
    assert client.post(f"/captures/{cid}/name", json={"label": "group:bird"}, headers=signup(client, "bob")).status_code == 404
    fake.next = [Prediction("coyote", 0.95)]
    matched = upload(client, h).json()
    assert matched["matched"]
    assert client.post(f"/captures/{matched['capture_id']}/name", json={"label": "group:bird"},
                       headers=h).status_code == 400


def test_photos_are_kept_only_when_the_player_shares_them(client, fake):
    from app.storage import get_storage
    h = signup(client)
    assert client.get("/me", headers=h).json()["share_training_photos"] is False
    s = client.patch("/me/settings", json={"share_training_photos": True}, headers=h).json()
    assert s["share_training_photos"] is True
    cid = _none_of_these(client, fake, h)
    r = client.post(f"/captures/{cid}/name", json={"label": "group:beetle"}, headers=h).json()
    assert r["photo_shared"] and "teach the game" in r["message"]
    key = _rows()[0].image_path
    assert key.startswith("train_") and get_storage().get(key)

    # Turning sharing off deletes the copies but keeps the names.
    client.patch("/me/settings", json={"share_training_photos": False}, headers=h)
    assert _rows()[0].image_path is None and _rows()[0].label == "group:beetle"
    assert get_storage().get(key) is None


def test_names_saved_offline_arrive_later(client):
    h = signup(client)
    files = {"photo": ("p.jpg", jpeg_bytes(), "image/jpeg")}
    r = client.post("/me/named-photos", data={"label": "Canis latrans", "predicted_label": "gray_fox", "state": "ca"},
                    files=files, headers=h)
    assert r.status_code == 201, r.text
    assert not r.json()["photo_shared"]  # not sharing: the photo is dropped
    client.patch("/me/settings", json={"share_training_photos": True}, headers=h)
    r = client.post("/me/named-photos", data={"label": "group:no-animal"}, files=files, headers=h).json()
    assert r["photo_shared"]
    rows = _rows()
    assert [(x.capture_id, x.label, x.predicted_label, x.state, bool(x.image_path)) for x in rows] == \
        [(None, "Canis latrans", "gray_fox", "CA", False), (None, "group:no-animal", None, None, True)]
    assert client.post("/me/named-photos", data={"label": "Nope"}, headers=h).status_code == 400


def test_daily_limit(client, monkeypatch):
    from app import naming
    monkeypatch.setattr(naming, "DAILY_LIMIT", 2)
    h = signup(client)
    for _ in range(2):
        assert client.post("/me/named-photos", data={"label": "group:bird"}, headers=h).status_code == 201
    assert client.post("/me/named-photos", data={"label": "group:bird"}, headers=h).status_code == 429


def test_deleting_the_account_deletes_names_and_photos(client, fake):
    from app.storage import get_storage
    h = signup(client)
    client.patch("/me/settings", json={"share_training_photos": True}, headers=h)
    cid = _none_of_these(client, fake, h)
    client.post(f"/captures/{cid}/name", json={"label": "group:bird"}, headers=h)
    key = _rows()[0].image_path
    assert client.request("DELETE", "/me", json={"password": "hunter22!"}, headers=h).status_code == 204
    assert _rows() == [] and get_storage().get(key) is None
