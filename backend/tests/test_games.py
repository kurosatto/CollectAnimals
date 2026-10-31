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
    best = lambda r: {k: r.json()[k] for k in ("points", "animal_best")}  # noqa: E731
    assert best(score(client, ana, "bobcat", 20)) == {"points": 230, "animal_best": True}
    assert best(score(client, ana, "raccoon", 20)) == {"points": 200, "animal_best": True}
    assert best(score(client, ana, "raccoon", 10)) == {"points": 100, "animal_best": False}
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


def test_coins_buy_skins_and_decorations(client, fake):
    ana = signup(client, "ana")
    catch(client, fake, ana, "bobcat")  # speed 4 on land
    r = score(client, ana, "bobcat", 20).json()  # 230 points
    assert (r["coins_earned"], r["coins"]) == (23, 23)
    assert client.post("/games/shop/buy", headers=ana, json={"item": "decor.flowers"}).status_code == 400
    for _ in range(6):
        score(client, ana, "bobcat", 60)  # 69 coins a run, but only 300 a day
    shop = client.get("/games/shop", headers=ana).json()
    assert shop["coins"] == 300
    shop = client.post("/games/shop/buy", headers=ana, json={"item": "skin.frosty"}).json()
    assert shop["coins"] == 150 and next(i for i in shop["items"] if i["key"] == "skin.frosty")["owned"]
    assert client.post("/games/shop/buy", headers=ana, json={"item": "skin.frosty"}).status_code == 409
    assert client.post("/games/shop/skin", headers=ana, json={"species": "bobcat", "skin": "golden"}).status_code == 400
    assert client.post("/games/shop/skin", headers=ana, json={"species": "bobcat", "skin": "frosty"}).json()["skins"] == \
        {"bobcat": "frosty"}
    # A best score remembers the skin the animal wore, and the board shows it.
    assert board(client, ana)["you"]["skin"] is None
    score(client, ana, "bobcat", 61)
    assert board(client, ana)["you"]["skin"] == "frosty"
    shop = client.post("/games/shop/buy", headers=ana, json={"item": "decor.flowers"}).json()
    assert shop["decor"] == ["flowers"] and shop["coins"] == 50
    assert client.post("/games/shop/decor", headers=ana, json={"item": "decor.flowers", "on": False}).json()["decor"] == []


def test_newer_games_take_scores(client, fake):
    ana = signup(client, "ana")
    catch(client, fake, ana, "harbor_seal")
    # Big Splash is in the water, where a seal is fast; Mud Slide is on land.
    assert score(client, ana, "harbor_seal", 20, level="splash.1").json()["points"] == 260
    assert score(client, ana, "harbor_seal", 20, level="slide.0").json()["points"] == 150
    assert score(client, ana, "harbor_seal", 20, level="school.1").status_code == 200
    assert score(client, ana, "harbor_seal", 20, level="nope.0").status_code == 422


def test_place_table_matches_the_game():
    js = (Path(__file__).parents[1] / "app/static/minigames.js").read_text()
    for game, place in games.PLACE.items():
        assert f'{game}: "{place}"' in js


def test_decorations_need_room(client, fake):
    from app.db import SessionLocal
    from app.models import User
    ana = signup(client, "ana")
    with SessionLocal() as db:
        db.query(User).filter(User.username == "ana").update({"coins": 2000})
        db.commit()
    shop = client.get("/games/shop", headers=ana).json()
    decor = [i for i in shop["items"] if i["kind"] == "decor"]
    assert len(decor) == 103 and all(i["note"] and i["area"] in games.ROOM for i in decor)
    # The pond holds three; a fourth waits in your shop until you hide one.
    for k in ("rubber_duck", "lily_pads", "basking_rock", "rowboat"):
        shop = client.post("/games/shop/buy", headers=ana, json={"item": f"decor.{k}"}).json()
    assert shop["decor"] == ["rubber_duck", "lily_pads", "basking_rock"]
    r = client.post("/games/shop/decor", headers=ana, json={"item": "decor.rowboat", "on": True})
    assert r.status_code == 409 and "pond" in r.json()["detail"]
    client.post("/games/shop/decor", headers=ana, json={"item": "decor.lily_pads", "on": False})
    shop = client.post("/games/shop/decor", headers=ana, json={"item": "decor.rowboat", "on": True}).json()
    assert shop["decor"] == ["rubber_duck", "basking_rock", "rowboat"]


def test_decor_catalog_matches_the_sprites():
    import json
    root = Path(__file__).resolve().parents[2] / "species"
    for d in json.loads((root / "decor.json").read_text()):
        assert (root / "sprites" / "decor" / f"{d['key']}.png").is_file(), d["key"]
        assert len(f"decor.{d['key']}") <= 32


def test_admin_owns_everything(client, fake, monkeypatch):
    from app.config import settings
    monkeypatch.setattr(settings, "admin_usernames", frozenset({"admin"}))
    admin = signup(client, "admin")
    shop = client.get("/games/shop", headers=admin).json()
    assert all(i["owned"] for i in shop["items"]) and shop["decor"] == []
    shop = client.post("/games/shop/decor", headers=admin, json={"item": "decor.tent", "on": True}).json()
    assert shop["decor"] == ["tent"]
    assert not any(i["owned"] for i in client.get("/games/shop", headers=signup(client, "bob")).json()["items"])
