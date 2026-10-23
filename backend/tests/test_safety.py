from app.config import settings
from test_api import client, fake, signup  # noqa: F401  (fixtures)
from test_social import befriend, catch


def photo_id(client, h):
    return client.get("/me/album", headers=h).json()["photos"][0]["id"]


def feed_names(client, h):
    return [p["username"] for p in client.get("/feed", headers=h).json()["photos"]]


def test_delete_account_removes_everything(client, fake):
    ana, ben = signup(client, "ana"), signup(client, "ben")
    befriend(client, ana, ben, "ben", "ana")
    catch(client, fake, ana, "coyote")
    catch(client, fake, ben, "coyote")
    ben_photo = photo_id(client, ben)
    client.post(f"/photos/{ben_photo}/like", headers=ana)
    client.post(f"/photos/{ben_photo}/comments", headers=ana, json={"body": "nice"})
    media = client.get("/me/album", headers=ana).json()["photos"][0]["url"]
    assert client.get(media).status_code == 200

    assert client.request("DELETE", "/me", headers=ana, json={"password": "wrong-pass"}).status_code == 403
    assert client.request("DELETE", "/me", headers=ana, json={"password": "hunter22!"}).status_code == 204

    assert client.get("/me", headers=ana).status_code == 401
    assert client.get(media).status_code == 404
    assert client.post("/auth/login", data={"username": "ana", "password": "hunter22!"}).status_code == 401
    assert client.get("/friends", headers=ben).json()["friends"] == []
    p = client.get("/me/album", headers=ben).json()["photos"][0]
    assert p["like_count"] == 0 and p["comment_count"] == 0
    assert "ana" not in feed_names(client, ben)
    # The name is free again.
    signup(client, "ana")


def test_delete_account_page_and_privacy_page(client, monkeypatch):
    assert "Delete my account" in client.get("/delete-account").text
    page = client.get("/privacy").text
    assert "privacy policy" in page.lower() and 'href="/delete-account"' in page
    monkeypatch.setattr(settings, "contact_email", "game@example.com")
    page = client.get("/privacy").text
    assert "mailto:game@example.com" in page and "Google Play listing" not in page
    assert 'href="/rules"' in page
    rules = client.get("/rules").text
    assert "community rules" in rules.lower() and 'href="/privacy"' in rules


def test_block_hides_both_ways(client, fake):
    ana, ben = signup(client, "ana"), signup(client, "ben")
    befriend(client, ana, ben, "ben", "ana")
    catch(client, fake, ana, "coyote")
    catch(client, fake, ben, "coyote")
    ana_photo, ben_photo = photo_id(client, ana), photo_id(client, ben)
    client.post(f"/photos/{ana_photo}/comments", headers=ben, json={"body": "hi"})
    assert "ben" in feed_names(client, ana)

    assert client.post("/blocks", headers=ana, json={"username": "ben"}).status_code == 204
    assert client.get("/blocks", headers=ana).json() == ["ben"]
    assert client.get("/friends", headers=ana).json()["friends"] == []
    assert "ben" not in feed_names(client, ana) and "ana" not in feed_names(client, ben)
    gallery = client.get("/species/coyote/photos", headers=ana).json()["photos"]
    assert [p["username"] for p in gallery] == ["ana"]
    assert client.get(f"/photos/{ana_photo}/comments", headers=ana).json() == []
    assert client.post(f"/photos/{ana_photo}/like", headers=ben).status_code == 404
    assert client.post(f"/photos/{ben_photo}/comments", headers=ana, json={"body": "x"}).status_code == 404
    assert client.post("/friends/requests", headers=ben, json={"username": "ana"}).status_code == 403
    assert client.get("/users/ben", headers=ana).json()["friendship"] == "blocked"
    assert client.get("/users/ben", headers=ana).json()["photos"] == []
    assert client.get("/users/ana", headers=ben).status_code == 404

    assert client.delete("/blocks/ben", headers=ana).status_code == 204
    assert "ben" in feed_names(client, ana)
    assert client.get("/users/ben", headers=ana).json()["friendship"] == "none"


def test_reports_hide_and_moderate(client, fake, monkeypatch):
    monkeypatch.setattr(settings, "admin_usernames", frozenset({"mod"}))
    owner = signup(client, "owner")
    catch(client, fake, owner, "coyote")
    pid = photo_id(client, owner)
    viewers = [signup(client, f"viewer{i}") for i in range(3)]
    mod = signup(client, "mod")
    for h in viewers + [mod]:
        catch(client, fake, h, "coyote")
    assert client.get("/me", headers=mod).json()["is_admin"] is True
    assert client.get("/admin/reports", headers=owner).status_code == 403
    assert client.post("/reports", headers=owner, json={"photo_id": pid, "reason": "spam"}).status_code == 400
    assert client.post("/reports", headers=viewers[0], json={"photo_id": pid, "reason": "nope"}).status_code == 422

    for i, h in enumerate(viewers):
        r = client.post("/reports", headers=h, json={"photo_id": pid, "reason": "inappropriate", "details": f"d{i}"})
        assert r.status_code == 201 and r.json()["hidden"] == (i == 2)
    # Hidden from everyone else, still there for its owner.
    assert "owner" not in feed_names(client, mod)
    assert client.get("/me/album", headers=owner).json()["photos"][0]["hidden"] is True

    reports = client.get("/admin/reports", headers=mod).json()
    assert len(reports) == 1 and reports[0]["reports"] == 3 and reports[0]["kind"] == "photo"
    assert reports[0]["photo_url"] and reports[0]["reasons"] == {"inappropriate": 3}
    assert client.post("/admin/reports/resolve", headers=mod,
                       json={"kind": "photo", "id": pid, "action": "keep"}).status_code == 204
    assert "owner" in feed_names(client, mod) and client.get("/admin/reports", headers=mod).json() == []

    # Comments and players can be reported too; a moderator can delete the account.
    c = client.post(f"/photos/{pid}/comments", headers=viewers[0], json={"body": "mean words"}).json()
    client.post("/reports", headers=owner, json={"comment_id": c["id"], "reason": "bullying"})
    client.post("/reports", headers=owner, json={"username": "viewer0", "reason": "bullying"})
    kinds = {r["kind"]: r for r in client.get("/admin/reports", headers=mod).json()}
    assert kinds["comment"]["comment"] == "mean words" and kinds["user"]["username"] == "viewer0"
    assert client.post("/admin/reports/resolve", headers=mod,
                       json={"kind": "comment", "id": c["id"], "action": "remove"}).status_code == 204
    assert client.get(f"/photos/{pid}/comments", headers=owner).json() == []
    v0 = client.get("/me", headers=viewers[0]).json()["id"]
    assert client.post("/admin/reports/resolve", headers=mod,
                       json={"kind": "user", "id": v0, "action": "delete_account"}).status_code == 204
    assert client.get("/me", headers=viewers[0]).status_code == 401
    assert client.get("/admin/reports", headers=mod).json() == []
