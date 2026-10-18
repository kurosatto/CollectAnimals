from datetime import datetime, timedelta

from PIL import Image

from app.classifier import Prediction
from test_api import client, fake, signup  # noqa: F401  (fixtures)
from test_social import _jpeg


def _exif(lat=None, lon=None, taken=None):
    exif = Image.Exif()
    if lat is not None:
        exif.get_ifd(0x8825).update({1: "N", 2: (float(int(lat)), (lat % 1) * 60, 0.0),
                                     3: "W", 4: (float(int(-lon)), (-lon % 1) * 60, 0.0)})
    if taken is not None:
        exif.get_ifd(0x8769)[36867] = taken.strftime("%Y:%m:%d %H:%M:%S")
    return exif


def post(client, fake, h, exif=None, slug="coyote", **form):
    fake.next = [Prediction(slug, 0.95)]
    r = client.post("/captures", headers=h, data={k: str(v) for k, v in form.items()},
                    files={"photo": ("p.jpg", _jpeg(exif), "image/jpeg")})
    assert r.status_code == 201, r.text
    return r.json()


def test_photo_metadata_beats_the_phones_location(client, fake):
    h = signup(client)
    r = post(client, fake, h, _exif(37.5, -122.5, datetime(2026, 5, 4, 10, 11, 12)),
             latitude=34.05, longitude=-118.24)
    ww = r["where_when"]
    assert (ww["latitude"], ww["longitude"], ww["place_source"]) == (37.5, -122.5, "photo")
    assert (ww["taken_at"], ww["time_source"]) == ("2026-05-04T10:11:12", "photo")


def test_apps_can_send_the_metadata_they_read(client, fake):
    h = signup(client)
    ww = post(client, fake, h, photo_latitude=36.97, photo_longitude=-122.03,
              photo_taken_at="2026-05-04T07:30:00", latitude=34.05, longitude=-118.24)["where_when"]
    assert (ww["latitude"], ww["place_source"], ww["taken_at"]) == (36.97, "photo", "2026-05-04T07:30:00")


def test_phone_location_only_for_recent_photos(client, fake):
    h = signup(client)
    # No metadata at all: the phone's location and the upload time.
    ww = post(client, fake, h, latitude=34.05, longitude=-118.24)["where_when"]
    assert (ww["place_source"], ww["time_source"]) == ("device", "upload") and ww["taken_at"]
    # An old gallery photo with no GPS: no place rather than where the phone is today.
    ww = post(client, fake, h, _exif(taken=datetime(2025, 8, 1, 9)), latitude=34.05, longitude=-118.24)["where_when"]
    assert ww["latitude"] is None and ww["place_source"] is None and ww["time_source"] == "photo"
    # A camera clock in the future is ignored.
    ww = post(client, fake, h, _exif(taken=datetime.now() + timedelta(days=30)))["where_when"]
    assert ww["time_source"] == "upload"


def test_owner_edits_time_and_place(client, fake):
    h = signup(client)
    r = post(client, fake, h, slug="western_gray_squirrel", latitude=34.05, longitude=-118.24)
    cid = r["capture_id"]
    body = {"taken_at": "2026-01-10T07:15:00", "latitude": 36.9741, "longitude": -122.0308}
    e = client.put(f"/captures/{cid}/where-when", headers=h, json=body)
    assert e.status_code == 200, e.text
    ww = e.json()["where_when"]
    assert (ww["taken_at"], ww["time_source"], ww["place_source"]) == ("2026-01-10T07:15:00", "edited", "edited")
    assert ww["place"] == "near Santa Cruz"
    assert e.json()["score"] == r["score"] and e.json()["bond"] >= 1
    # The album photo shows the new date and place, and the owner sees the details.
    p = client.get("/me/album", headers=h).json()["photos"][0]
    assert p["taken_on"] == "2026-01-10" and p["place"] == "near Santa Cruz"
    assert p["where_when"]["capture_id"] == cid
    # Field notes count the edited day.
    post(client, fake, h, slug="western_gray_squirrel")
    bond = client.get("/me/bonds?species=western_gray_squirrel", headers=h).json()
    days = next(n for n in bond["bonds"][0]["notes"] if n["id"] == "days")
    assert days["progress"] == 2

    # Clearing the place.
    e = client.put(f"/captures/{cid}/where-when", headers=h, json={"taken_at": "2026-01-10T07:15:00"}).json()
    assert e["where_when"]["latitude"] is None and e["where_when"]["place"] is None


def test_edit_rules(client, fake):
    h = signup(client)
    cid = post(client, fake, h)["capture_id"]
    url = f"/captures/{cid}/where-when"
    future = (datetime.now() + timedelta(days=2)).isoformat(timespec="seconds")
    assert client.put(url, headers=h, json={"taken_at": future}).status_code == 400
    assert client.put(url, headers=h, json={"taken_at": "1980-01-01T00:00:00"}).status_code == 400
    # Outside the player's state (Reno, Nevada; Raleigh, North Carolina), or half a place.
    for lat, lon in ((39.53, -119.81), (35.78, -78.64)):
        r = client.put(url, headers=h, json={"taken_at": "2026-01-10T07:15:00", "latitude": lat, "longitude": lon})
        assert r.status_code == 400 and "California" in r.json()["detail"]
    assert client.put(url, headers=h, json={"taken_at": "2026-01-10T07:15:00", "latitude": 37.0}).status_code == 400
    # A beach just off the coarse outline still counts (Point Reyes lighthouse).
    assert client.put(url, headers=h, json={"taken_at": "2026-01-10T07:15:00",
                                            "latitude": 37.9955, "longitude": -123.0228}).status_code == 200
    # Only the owner.
    other = signup(client, "bob")
    assert client.put(url, headers=other, json={"taken_at": "2026-01-10T07:15:00"}).status_code == 404
    # Others never get the exact details.
    assert client.get("/feed", headers=other).json()["photos"][0].get("where_when") is None


def test_editing_time_and_place_leaves_the_score_alone(client, fake):
    h = signup(client)
    r = post(client, fake, h)
    cid = r["capture_id"]
    place = {"latitude": 36.9741, "longitude": -122.0308}
    for at in ("2026-01-10T12:30:00", "2026-01-10T07:30:00"):
        e = client.put(f"/captures/{cid}/where-when", headers=h, json={"taken_at": at, **place}).json()
        assert e["score"] == r["score"]


def test_turning_off_saving_the_place_drops_the_photos_gps_too(client, fake):
    h = signup(client)
    ww = post(client, fake, h, _exif(37.5, -122.5), save_place="false")["where_when"]
    assert ww["latitude"] is None and ww["place_source"] is None


def test_saved_golden_hour_bonuses_are_taken_back(client, fake):
    import json
    from app.db import SessionLocal
    from app.main import restar_scores
    from app.models import Capture
    h = signup(client)
    cid = post(client, fake, h)["capture_id"]
    with SessionLocal() as db:
        c = db.get(Capture, cid)
        before = c.score
        c.score_parts = json.dumps(json.loads(c.score_parts) + [["Golden hour", 100]])
        c.score += 100
        db.commit()
    restar_scores()
    with SessionLocal() as db:
        c = db.get(Capture, cid)
        assert c.score == before and "Golden hour" not in c.score_parts
