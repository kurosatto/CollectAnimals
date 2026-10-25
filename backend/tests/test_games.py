from pathlib import Path

from app import games
from test_api import client, fake, signup  # noqa: F401  (fixtures)
from test_social import befriend, catch


def score(client, h, species, treats, level="trail.0"):
    return client.post("/games/scores", headers=h, json={"level": level, "species": species, "treats": treats})


def board(client, h, scope="all", level="trail.0"):
    return client.get(f"/games/scores/{level}?scope={scope}", headers=h).json()


def test_points_come_from_the_animals_speed(client, fake):
    ana = signup(client, "ana")
    catch(client, fake, ana, "bobcat")  # speed 4
    catch(client, fake, ana, "raccoon")  # speed 3
    assert score(client, ana, "bobcat", 20).json() == {"points": 230, "animal_best": True}
    assert score(client, ana, "raccoon", 20).json() == {"points": 200, "animal_best": True}
    assert score(client, ana, "raccoon", 10).json() == {"points": 100, "animal_best": False}
    # Only animals you've captured, sane treat counts and real levels.
    assert score(client, ana, "coyote", 5).status_code == 400
    assert score(client, ana, "bobcat", 100000).status_code == 422
    assert score(client, ana, "bobcat", 5, level="moon.0").status_code == 422
    me = board(client, ana)["you"]
    assert (me["rank"], me["points"], me["species"]["slug"]) == (1, 230, "bobcat")


def test_top_ten_and_friends(client, fake):
    ana, ben, cal = signup(client, "ana"), signup(client, "ben"), signup(client, "cal")
    for h, n in ((ana, 10), (ben, 30), (cal, 20)):
        catch(client, fake, h, "raccoon")
        score(client, h, "raccoon", n)
    befriend(client, ana, cal, "cal", "ana")
    assert [r["username"] for r in board(client, ana)["top"]] == ["ben", "cal", "ana"]
    assert [r["username"] for r in board(client, ana, "friends")["top"]] == ["cal", "ana"]
    assert board(client, ana)["you"]["rank"] == 3
    # Private players only show to their friends.
    client.patch("/me/settings", headers=ben, json={"is_private": True})
    assert [r["username"] for r in board(client, ana)["top"]] == ["cal", "ana"]


def test_unrevealed_animals_stay_a_mystery(client, fake):
    ana, ben = signup(client, "ana"), signup(client, "ben")
    catch(client, fake, ben, "bobcat")
    score(client, ben, "bobcat", 10)
    top = board(client, ana)["top"][0]
    assert top["species"] == {"slug": None, "common_name": "a mystery mammal"}
    assert board(client, ana)["you"] is None


def test_speed_table_matches_the_game():
    js = (Path(__file__).parents[1] / "app/static/minigames.js").read_text()
    assert "tempo: [" + ", ".join(f"{x:g}".lstrip("0") for x in games.TEMPO) + "]" in js


def test_speed_depends_on_the_game(client, fake):
    ana = signup(client, "ana")
    catch(client, fake, ana, "harbor_seal")  # slow on land, fast in the water
    assert score(client, ana, "harbor_seal", 20, level="trail.0").json()["points"] == 150
    assert score(client, ana, "harbor_seal", 20, level="river.0").json()["points"] == 260
