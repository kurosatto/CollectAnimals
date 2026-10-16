from app import duels
from app.classifier import Prediction
from test_api import client, fake, signup, upload  # noqa: F401  (fixtures)
from test_social import befriend


def capture(client, fake, h, slug):
    fake.next = [Prediction(slug, 0.95)]
    assert upload(client, h).json()["matched"]


def test_card_stats_follow_field_guide_sizes():
    whale = duels.card_stats("humpback_whale", "legendary", "CA", None)
    bird = duels.card_stats("annas_hummingbird", "common", "CA", 900)
    assert whale["size"] > 90 and whale["weight"] > 90 and whale["rarity"] == 95
    assert bird["size"] < whale["size"] and bird["weight"] < 20
    assert bird["photo"] == 60 and whale["photo"] == 40  # 900 points / 15; no score yet = 40
    assert duels._first_amount("A few grams", duels.TO_G) == 3.0
    assert duels._first_amount("2.5–3.5 ft long", duels.TO_CM) == 3 * 30.48


def test_duel_five_rounds_against_a_friend(client, fake):
    ana, bob = signup(client, "ana"), signup(client, "bob")
    capture(client, fake, ana, "coyote")
    capture(client, fake, bob, "western_fence_lizard")
    # Strangers can't be challenged.
    assert client.post("/duels", headers=ana, json={"opponent": "bob"}).status_code == 400
    befriend(client, ana, bob, "bob", "ana")

    d = client.post("/duels", headers=ana, json={"opponent": "bob"}).json()
    assert d["round"] == 0 and d["next_card"]["species"]["slug"] == "coyote"
    # Only the challenger picks.
    assert client.post(f"/duels/{d['id']}/play", headers=bob, json={"stat": "size"}).status_code == 403
    for _ in range(5):
        d = client.post(f"/duels/{d['id']}/play", headers=ana, json={"stat": "weight"}).json()
    assert d["finished"] and d["outcome"] == "win" and d["your_points"] == 5
    assert d["rounds"][0]["theirs"]["species"]["slug"] == "western_fence_lizard"
    assert client.post(f"/duels/{d['id']}/play", headers=ana, json={"stat": "size"}).status_code == 400

    # Bob sees the same duel from his side.
    theirs = client.get(f"/duels/{d['id']}", headers=bob).json()
    assert theirs["outcome"] == "lose" and not theirs["you_started"] and theirs["next_card"] is None
    assert client.get("/duels", headers=ana).json()["wins"] == 1
    assert client.get("/duels", headers=bob).json()["played"] == 1


def test_duel_needs_cards(client, fake):
    ana, bob = signup(client, "ana"), signup(client, "bob")
    befriend(client, ana, bob, "bob", "ana")
    r = client.post("/duels", headers=ana, json={"opponent": "bob"})
    assert r.status_code == 400 and "Capture an animal first" in r.json()["detail"]
