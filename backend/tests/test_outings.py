from datetime import date, datetime

from app import outings
from app.classifier import Prediction
from app.db import SessionLocal
from app.models import Capture
from test_api import client, fake, signup, upload  # noqa: F401  (fixtures)


def test_event_windows_wrap_the_new_year():
    members = {"mallard": "bird", "great_blue_heron": "bird", "coyote": "mammal", "ochre_sea_star": "marine"}
    jan = {e.id for e in outings.events_for("CA", members, date(2027, 1, 10))}
    assert {"winter_waterbirds", "low_tide"} <= jan
    nc = {e.id for e in outings.events_for("NC", members, date(2027, 1, 10))}
    assert "low_tide" not in nc
    ev = next(e for e in outings.events_for("CA", members, date(2026, 12, 20)) if e.id == "winter_waterbirds")
    assert ev.start == date(2026, 12, 1) and ev.end == date(2027, 2, 28) and "coyote" not in ev.slugs
    assert outings.event_progress(ev, [("mallard", date(2026, 12, 2)), ("mallard", date(2026, 12, 3)),
                                       ("great_blue_heron", date(2026, 11, 30))]) == 1


def test_events_leave_out_dangerous_animals():
    for d in (date(2026, 3, 1), date(2026, 7, 1), date(2026, 10, 1), date(2026, 12, 15)):
        for code in ("CA", "NC"):
            for e in outings.events_for(code, {"western_rattlesnake": "reptile", "american_alligator": "reptile",
                                               "western_black_widow": "invertebrate"}, d):
                assert not e.slugs


def test_outings_season_and_timeline(client, fake):
    h = signup(client)
    o = client.get("/me/outings", headers=h).json()
    assert o["days"] == [] and o["goal"] == 3 and len(o["recent_weeks"]) == 4
    fake.next = [Prediction("coyote", 0.95)]
    first = upload(client, h).json()["capture_id"]
    with SessionLocal() as db:
        db.get(Capture, first).taken_at = datetime(2026, 1, 3, 6)
        db.commit()
    fake.next = [Prediction("coyote", 0.95)]
    upload(client, h)
    o = client.get("/me/outings", headers=h).json()
    assert len(o["days"]) == 1 and o["recent_weeks"][-1] == 1

    s = client.get("/me/season", headers=h).json()
    assert s["state"] == "CA" and isinstance(s["arrivals"], list) and isinstance(s["events"], list)

    t = client.get("/me/captures?species=coyote", headers=h).json()
    assert len(t["photos"]) == 2
    assert t["photos"][-1]["notes"] == ["First meeting"] and "Early and late" in t["photos"][0]["notes"]
    assert client.get(f"/me/captures/{first}/photo", headers=h).status_code == 200
    assert client.get(f"/me/captures/{first}/photo", headers=signup(client, "bob")).status_code == 404
    assert client.get("/me/captures?species=raccoon", headers=h).status_code == 404
