from datetime import datetime, timezone

from app import bonds
from app.classifier import Prediction
from app.db import SessionLocal
from app.models import Capture
from test_api import client, fake, jpeg_bytes, signup, upload  # noqa: F401  (fixtures)


def S(y, mo, d, h, lat=None, lon=None, stars=None):
    return bonds.Sighting(datetime(y, mo, d, h), lat, lon, stars)


def done(ns):
    return {n.id for n in ns if n.done}


def test_burst_in_one_sitting_ticks_nothing_new():
    one = [S(2026, 10, 16, 9, 37.0, -122.0)] * 20
    assert done(bonds.notes(one)) == {"first"}


def test_each_note():
    base = S(2026, 10, 16, 9, 37.0, -122.0)
    assert "days" in done(bonds.notes([base, S(2026, 10, 17, 9), S(2026, 10, 20, 9)]))
    assert "times" in done(bonds.notes([base, S(2026, 10, 16, 18)]))
    # 1 km apart counts as a new place; next door does not.
    assert "places" not in done(bonds.notes([base, S(2026, 10, 16, 9, 37.001, -122.0)]))
    assert "places" in done(bonds.notes([base, S(2026, 10, 16, 9, 37.02, -122.0)]))
    assert "seasons" in done(bonds.notes([base, S(2027, 1, 5, 9)]))
    assert "star" in done(bonds.notes([S(2026, 10, 16, 9, stars=4)]))
    assert "star" not in done(bonds.notes([S(2026, 10, 16, 9, stars=3)]))
    all_six = [base, S(2026, 10, 17, 18, 37.05, -122.0, 4), S(2027, 1, 5, 9)]
    assert bonds.level(bonds.notes(all_six)) == 6 and bonds.title(6) == "Lifelong friend"


def test_newly_done_and_buddy_lines():
    before = [S(2026, 10, 16, 9)]
    assert bonds.newly_done(before, before + [S(2026, 10, 16, 19)]) == ["Early and late"]
    assert bonds.mood(0) == "napping" and bonds.mood(2) == "happy" and bonds.mood(5) == "excited"
    assert "outside" in bonds.buddy_line("napping", bonds.notes(before))


def test_local_time_uses_exif_or_state_time():
    assert bonds.local_time(datetime(2026, 10, 16, 7), datetime(2026, 10, 16, 20, tzinfo=timezone.utc), -8).hour == 7
    assert bonds.local_time(None, datetime(2026, 10, 16, 20, tzinfo=timezone.utc), -8).hour == 12


def test_bonds_buddy_api(client, fake):
    h = signup(client)
    assert client.get("/me/buddy", headers=h).json() is None
    fake.next = [Prediction("coyote", 0.95)]
    r = upload(client, h).json()
    assert r["bond"] == 1 and r["bond_up"] == []
    # A second photo "taken" on another day and time of day.
    with SessionLocal() as db:
        c = db.get(Capture, r["capture_id"])
        c.taken_at = datetime(2026, 1, 3, 6)
        db.commit()
    fake.next = [Prediction("coyote", 0.95)]
    r2 = upload(client, h).json()
    assert r2["bond"] >= 3 and "Early and late" in r2["bond_up"] and "Bond with the" in r2["message"]

    b = client.get("/me/bonds", headers=h).json()["bonds"]
    assert b[0]["species"]["slug"] == "coyote" and b[0]["level"] == r2["bond"]
    entry = next(e for e in client.get("/me/collection", headers=h).json()["entries"]
                 if e["species"]["slug"] == "coyote")
    assert entry["bond"] == r2["bond"]

    buddy = client.get("/me/buddy", headers=h).json()
    assert buddy["chosen"] is False and buddy["bond"]["species"]["slug"] == "coyote"
    assert buddy["mood"] == "happy" and buddy["line"]
    assert client.put("/me/buddy", headers=h, json={"species": "raccoon"}).status_code == 400
    assert client.put("/me/buddy", headers=h, json={"species": "coyote"}).json()["chosen"] is True
