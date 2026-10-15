from datetime import datetime, timezone

from app import goals
from app.classifier import Prediction
from test_api import client, fake, signup, upload  # noqa: F401  (fixtures)


def test_sets_progress_and_hidden_names(client, fake):
    h = signup(client)
    fake.next = [Prediction("ochre_sea_star", 0.95)]
    upload(client, h)
    sets = {s["id"]: s for s in client.get("/me/sets", headers=h).json()["sets"]}
    assert "state_symbols" in sets and "tide_pools" in sets
    assert "beach" in sets and "state_symbols" in sets
    pools = sets["tide_pools"]
    assert pools["caught"] == 1 and not pools["complete"]
    star = next(r for r in pools["species"] if r["caught"])
    assert star["species"]["slug"] == "ochre_sea_star"
    # Animals nobody you know has captured keep their names hidden.
    assert all(r["species"]["slug"] is None for r in pools["species"] if not r["caught"])


def test_sets_leave_out_dangerous_animals():
    for code in ("CA", "NC"):
        for s in goals.sets_for(code, {"western_rattlesnake", "american_alligator", "raccoon", "red_fox",
                                       "striped_skunk", "virginia_opossum"}):
            assert "western_rattlesnake" not in s.slugs and "american_alligator" not in s.slugs


def test_weekly_challenges(client, fake):
    h = signup(client)
    r = client.get("/me/challenges", headers=h).json()
    assert len(r["challenges"]) == 3 and r["done"] == 0
    # Same challenges for everyone in the state this week.
    assert r["challenges"] == client.get("/me/challenges", headers=signup(client, "bob")).json()["challenges"]
    # The first challenge asks for a kind of animal: capture one of that kind.
    first = r["challenges"][0]
    assert first["id"].startswith("cat_")
    category = first["id"][4:]
    from app.db import SessionLocal
    from app.models import StateSpecies
    with SessionLocal() as db:
        slug = next(m.species.slug for m in db.query(StateSpecies).filter_by(state="CA")
                    if m.species.category == category)
    fake.next = [Prediction(slug, 0.95)]
    upload(client, h)
    after = client.get("/me/challenges", headers=h).json()["challenges"]
    assert after[0]["progress"] == 1


def test_week_bounds_start_monday_state_time():
    # Monday 03:00 UTC is still Sunday evening in California.
    start, end = goals.week_bounds(-8, datetime(2026, 10, 12, 3, 0, tzinfo=timezone.utc))
    assert start == datetime(2026, 10, 5, 8, 0, tzinfo=timezone.utc)
    assert (end - start).days == 7


def test_challenge_progress_counts():
    caps = [goals.WeekCapture("coyote", "mammal", "common", True),
            goals.WeekCapture("coyote", "mammal", "common", False),
            goals.WeekCapture("bobcat", "mammal", "rare", True)]
    assert goals.progress(goals.Challenge("c", "", "category", 2, category="mammal"), caps, 0) == 2
    assert goals.progress(goals.Challenge("d", "", "distinct", 5), caps, 0) == 2
    assert goals.progress(goals.Challenge("n", "", "new", 1), caps, 0) == 2
    assert goals.progress(goals.Challenge("r", "", "rarity", 1), caps, 0) == 1
    assert goals.progress(goals.Challenge("l", "", "likes", 3), caps, 4) == 4
