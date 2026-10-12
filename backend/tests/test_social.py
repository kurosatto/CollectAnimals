import io

from PIL import Image

from app.classifier import Prediction
from test_api import client, fake, signup, upload  # noqa: F401  (fixtures)


def catch(client, fake, h, slug, **form):
    fake.next = [Prediction(slug, 0.95)]
    r = client.post("/captures", headers=h, data={k: str(v) for k, v in form.items()},
                    files={"photo": ("p.jpg", _jpeg(), "image/jpeg")})
    assert r.status_code == 201, r.text
    return r.json()


def _jpeg(exif=None):
    buf = io.BytesIO()
    Image.new("RGB", (64, 48), "green").save(buf, "JPEG", **({"exif": exif} if exif is not None else {}))
    return buf.getvalue()


def befriend(client, a, b, b_name, a_name):
    assert client.post("/friends/requests", headers=a, json={"username": b_name}).json() == \
        {"status": "requested"}
    assert client.post(f"/friends/requests/{a_name}/accept", headers=b).json() == {"status": "friends"}


def names(client, h):
    return {e["species"]["slug"] for e in client.get("/me/collection", headers=h).json()["entries"]
            if e["species"]["revealed"]}


def test_friend_requests(client):
    ana, bob = signup(client, "ana"), signup(client, "bob")
    assert client.post("/friends/requests", headers=ana, json={"username": "ana"}).status_code == 400
    assert client.post("/friends/requests", headers=ana, json={"username": "zed"}).status_code == 404
    assert client.post("/friends/requests", headers=ana, json={"username": "bob"}).status_code == 201
    assert client.post("/friends/requests", headers=ana, json={"username": "bob"}).status_code == 409

    f = client.get("/friends", headers=bob).json()
    assert [x["username"] for x in f["incoming"]] == ["ana"] and not f["friends"]
    assert [x["username"] for x in client.get("/friends", headers=ana).json()["outgoing"]] == ["bob"]

    # Asking someone who already asked you makes you friends.
    assert client.post("/friends/requests", headers=bob, json={"username": "ana"}).json() == \
        {"status": "friends"}
    assert [x["username"] for x in client.get("/friends", headers=ana).json()["friends"]] == ["bob"]
    assert client.post("/friends/requests", headers=ana, json={"username": "bob"}).status_code == 409

    assert client.delete("/friends/bob", headers=ana).status_code == 204
    assert client.get("/friends", headers=bob).json() == {"friends": [], "incoming": [], "outgoing": []}
    assert client.post("/friends/requests/ana/accept", headers=bob).status_code == 404


def test_names_revealed_by_friends(client, fake):
    ana, bob = signup(client, "ana"), signup(client, "bob")
    catch(client, fake, bob, "bobcat")
    assert names(client, ana) == set()
    assert names(client, bob) == {"bobcat"}

    befriend(client, ana, bob, "bob", "ana")
    assert names(client, ana) == {"bobcat"}
    entry = next(e for e in client.get("/me/collection", headers=ana).json()["entries"]
                 if e["species"]["slug"] == "bobcat")
    assert not entry["caught"] and entry["friends_caught"] == 1
    # The fun fact still needs your own catch.
    assert client.get("/species/bobcat/dex", headers=ana).json()["fun_fact"] is None

    client.delete("/friends/ana", headers=bob)
    assert names(client, ana) == set()


def test_album_photo_location_and_date(client, fake):
    ana = signup(client, "ana")
    r = catch(client, fake, ana, "coyote", latitude=37.77493, longitude=-122.41942)
    assert r["album_photo_id"] and "album" in r["message"]
    # A second catch keeps the first photo unless you swap it.
    r2 = catch(client, fake, ana, "coyote", latitude=34.05, longitude=-118.24)
    assert r2["album_photo_id"] is None

    album = client.get("/me/album", headers=ana).json()
    assert album["caught"] == 1 and len(album["photos"]) == 1
    p = album["photos"][0]
    assert p["species"]["slug"] == "coyote" and p["is_mine"]
    assert (p["latitude"], p["longitude"], p["location_precise"]) == (37.775, -122.419, True)
    assert p["taken_on"]
    img = client.get(p["url"])
    assert img.status_code == 200 and img.headers["content-type"] == "image/jpeg"

    entry = next(e for e in client.get("/me/collection", headers=ana).json()["entries"]
                 if e["species"]["slug"] == "coyote")
    assert entry["photo_url"] == p["url"]

    swapped = client.put("/me/album/coyote", headers=ana, json={"capture_id": r2["capture_id"]})
    assert swapped.status_code == 200 and swapped.json()["latitude"] == 34.05
    # The old file is no longer served once it leaves the album.
    assert client.get(p["url"]).status_code == 404
    assert client.put("/me/album/bobcat", headers=ana,
                      json={"capture_id": r2["capture_id"]}).status_code == 400

    assert client.delete("/me/album/coyote", headers=ana).status_code == 204
    assert client.get("/me/album", headers=ana).json()["photos"] == []
    assert client.get("/me/collection", headers=ana).json()["caught"] == 0


def test_location_from_exif(client, fake):
    exif = Image.Exif()
    gps = exif.get_ifd(0x8825)
    gps.update({1: "N", 2: (37.0, 46.0, 30.0), 3: "W", 4: (122.0, 25.0, 0.0)})
    exif.get_ifd(0x8769)[36867] = "2026:05:04 10:11:12"
    ana = signup(client, "ana")
    fake.next = [Prediction("coyote", 0.95)]
    r = client.post("/captures", headers=ana, files={"photo": ("p.jpg", _jpeg(exif), "image/jpeg")})
    assert r.status_code == 201
    p = client.get("/me/album", headers=ana).json()["photos"][0]
    assert (p["latitude"], p["longitude"], p["taken_on"]) == (37.775, -122.417, "2026-05-04")


def test_albums_only_for_friends(client, fake):
    ana, bob, cyd = signup(client, "ana"), signup(client, "bob"), signup(client, "cyd")
    catch(client, fake, bob, "coyote")
    assert client.get("/users/bob/album", headers=ana).status_code == 403
    assert client.get("/users/nobody/album", headers=ana).status_code == 404
    befriend(client, ana, bob, "bob", "ana")
    album = client.get("/users/bob/album", headers=ana).json()
    assert album["username"] == "bob" and album["photos"][0]["by_friend"]
    assert client.get("/users/bob/album", headers=cyd).status_code == 403


def test_gallery_ranking_and_likes(client, fake):
    ana, bob, cyd, dee = (signup(client, n) for n in ("ana", "bob", "cyd", "dee"))
    for h in (ana, bob, cyd):
        catch(client, fake, h, "coyote", latitude=37.77493, longitude=-122.41942)

    # dee hasn't caught a coyote and has no friends who did.
    assert client.get("/species/coyote/photos", headers=dee).status_code == 403

    g = client.get("/species/coyote/photos", headers=ana).json()
    assert g["total"] == 3 and [p["rank"] for p in g["photos"]] == [1, 2, 3]
    by_user = {p["username"]: p for p in g["photos"]}
    # Strangers only see a rough location.
    assert by_user["bob"]["latitude"] == 37.8 and not by_user["bob"]["location_precise"]
    assert by_user["ana"]["location_precise"]

    cy_photo, bob_photo = by_user["cyd"]["id"], by_user["bob"]["id"]
    assert client.post(f"/photos/{cy_photo}/like", headers=ana).status_code == 204
    assert client.post(f"/photos/{cy_photo}/like", headers=ana).status_code == 204  # idempotent
    assert client.post(f"/photos/{cy_photo}/like", headers=bob).status_code == 204
    assert client.post(f"/photos/{bob_photo}/like", headers=ana).status_code == 204
    assert client.post(f"/photos/{cy_photo}/like", headers=cyd).status_code == 400  # own photo
    assert client.post(f"/photos/{cy_photo}/like", headers=dee).status_code == 404  # not revealed

    g = client.get("/species/coyote/photos", headers=ana).json()
    assert [(p["username"], p["like_count"], p["rank"]) for p in g["photos"]] == \
        [("cyd", 2, 1), ("bob", 1, 2), ("ana", 0, 3)]
    assert g["photos"][0]["liked_by_me"]

    assert client.delete(f"/photos/{cy_photo}/like", headers=ana).status_code == 204
    g = client.get("/species/coyote/photos?sort=new", headers=ana).json()
    assert [p["username"] for p in g["photos"]] == ["cyd", "bob", "ana"]
    assert g["photos"][0]["like_count"] == 1 and g["photos"][0]["rank"] is None

    page = client.get("/species/coyote/photos?limit=1&offset=1", headers=ana).json()
    assert page["total"] == 3 and page["photos"][0]["rank"] == 2

    befriend(client, ana, bob, "bob", "ana")
    g = client.get("/species/coyote/photos?scope=friends", headers=ana).json()
    assert {p["username"] for p in g["photos"]} == {"ana", "bob"}
    # dee can see the gallery once a friend has caught one.
    befriend(client, dee, cyd, "cyd", "dee")
    assert client.get("/species/coyote/photos", headers=dee).json()["total"] == 3


def test_unmatched_captures_are_private(client, fake):
    ana = signup(client, "ana")
    fake.next = [Prediction("other", 0.95)]
    r = client.post("/captures", headers=ana, files={"photo": ("p.jpg", _jpeg(), "image/jpeg")})
    assert r.json()["album_photo_id"] is None
    from app.models import Capture
    from app.db import SessionLocal
    with SessionLocal() as db:
        key = db.get(Capture, r.json()["capture_id"]).image_path
    assert client.get(f"/media/{key}").status_code == 404
    assert client.get("/media/..%2Fsecret").status_code == 404


def test_news_feed(client, fake):
    ana, bob, cyd = (signup(client, n) for n in ("ana", "bob", "cyd"))
    catch(client, fake, bob, "coyote", latitude=36.9741, longitude=-122.0308)       # Santa Cruz
    catch(client, fake, cyd, "bobcat", latitude=36.9741, longitude=-122.0308)       # rare
    catch(client, fake, cyd, "mountain_lion", latitude=34.10, longitude=-118.80)    # legendary
    catch(client, fake, ana, "coyote")                                              # no location

    feed = client.get("/feed", headers=ana).json()
    assert [(p["username"], p["species"]["number"]) for p in feed["photos"]][0][0] == "ana"
    items = {p["username"] + ":" + (p["species"]["slug"] or p["species"]["category"]): p
             for p in feed["photos"]}
    coyote = items["bob:coyote"]
    assert coyote["place"] == "near Santa Cruz" and coyote["latitude"] == 37.0
    assert coyote["url"] and coyote["caught_at"]
    # ana hasn't unlocked the bobcat or the mountain lion: no name, no photo.
    hidden = [p for p in feed["photos"] if p["username"] == "cyd"]
    assert all(p["url"] is None and p["species"]["common_name"] is None for p in hidden)
    rare, legendary = sorted(hidden, key=lambda p: p["species"]["rarity"] == "legendary")
    assert rare["place"] == "around Santa Cruz" and rare["latitude"] is None
    assert legendary["place"] == "somewhere in Southern California" and legendary["latitude"] is None
    assert items["ana:coyote"]["place"] is None

    # cyd sees their own catches exactly.
    mine = [p for p in client.get("/feed", headers=cyd).json()["photos"] if p["is_mine"]]
    assert all(p["location_precise"] and p["url"] for p in mine)

    # Paging.
    page1 = client.get("/feed?limit=3", headers=ana).json()
    assert len(page1["photos"]) == 3 and page1["next_before"]
    page2 = client.get(f"/feed?limit=3&before={page1['next_before']}", headers=ana).json()
    assert len(page2["photos"]) == 1 and page2["next_before"] is None

    # Opting out hides your catches from everyone else's feed, not your own.
    assert client.patch("/me/settings", headers=cyd, json={"show_in_feed": False}).json() == \
        {"show_in_feed": False}
    assert client.get("/me", headers=cyd).json()["show_in_feed"] is False
    assert {p["username"] for p in client.get("/feed", headers=ana).json()["photos"]} == {"ana", "bob"}
    assert len([p for p in client.get("/feed", headers=cyd).json()["photos"] if p["is_mine"]]) == 2

    befriend(client, ana, bob, "bob", "ana")
    friends_feed = client.get("/feed?scope=friends", headers=ana).json()["photos"]
    assert {p["username"] for p in friends_feed} == {"ana", "bob"}
    # Friends see common animals precisely.
    assert next(p for p in friends_feed if p["username"] == "bob")["location_precise"]


def test_place_names(client):
    from app import places
    assert places.place_name(37.7694, -122.4862) == "Golden Gate Park & Presidio"
    assert places.place_name(36.9741, -122.0308) == "near Santa Cruz"
    assert places.place_name(41.0, -121.0).startswith("in ")


def test_local_feed(client, fake):
    ana, bob, cyd = (signup(client, n) for n in ("ana", "bob", "cyd"))
    catch(client, fake, bob, "coyote", latitude=36.9741, longitude=-122.0308)   # Santa Cruz
    catch(client, fake, cyd, "coyote", latitude=32.7157, longitude=-117.1611)   # San Diego
    catch(client, fake, cyd, "bobcat", latitude=37.00, longitude=-122.06)       # rare, near Santa Cruz
    catch(client, fake, ana, "coyote")                                          # no location

    def near(**kw):
        r = client.get("/feed", headers=ana, params={"scope": "near", **kw})
        assert r.status_code == 200, r.text
        return [(p["username"], p["species"]["rarity"]) for p in r.json()["photos"]]

    # From San Jose: Santa Cruz is ~40 km away, San Diego ~650 km.
    assert near(lat=37.34, lon=-121.89) == [("cyd", "rare"), ("bob", "common")]
    assert near(lat=37.34, lon=-121.89, radius_km=20) == []
    assert near(lat=32.72, lon=-117.16, radius_km=25) == [("cyd", "common")]
    assert len(client.get("/feed", headers=ana).json()["photos"]) == 4

    assert client.get("/feed?scope=near", headers=ana).status_code == 400
    assert client.get("/feed?scope=near&lat=37&lon=-122&radius_km=1", headers=ana).status_code == 422

    # Paging works through the distance filter.
    page = client.get("/feed", headers=ana, params={"scope": "near", "lat": 37.34, "lon": -121.89,
                                                    "limit": 1}).json()
    assert page["next_before"]
    rest = client.get("/feed", headers=ana, params={"scope": "near", "lat": 37.34, "lon": -121.89,
                                                    "before": page["next_before"]}).json()
    assert [p["username"] for p in rest["photos"]] == ["bob"] and rest["next_before"] is None


def test_feed_uncaught_only(client, fake):
    ana, bob = signup(client, "ana"), signup(client, "bob")
    catch(client, fake, bob, "coyote")
    catch(client, fake, bob, "bobcat")
    catch(client, fake, ana, "coyote")

    def feed(**kw):
        return [p["species"]["number"] for p in
                client.get("/feed", headers=ana, params=kw).json()["photos"]]
    everything = feed()
    assert len(everything) == 3
    only = client.get("/feed?uncaught=true", headers=ana).json()["photos"]
    # Only bob's bobcat is left, still hidden from ana.
    assert len(only) == 1 and only[0]["species"]["common_name"] is None and only[0]["url"] is None
    assert len(client.get("/feed?uncaught=true", headers=bob).json()["photos"]) == 0


def test_delete_photo(client, fake):
    from app.config import settings

    ana, bob = signup(client, "ana"), signup(client, "bob")
    catch(client, fake, ana, "coyote", latitude=37.77, longitude=-122.42)
    catch(client, fake, ana, "coyote")
    catch(client, fake, ana, "bobcat")
    catch(client, fake, bob, "coyote")
    photo = next(p for p in client.get("/me/album", headers=ana).json()["photos"]
                 if p["species"]["slug"] == "coyote")
    assert client.post(f"/photos/{photo['id']}/like", headers=bob).status_code == 204
    files_before = len(list(settings.upload_dir.iterdir()))

    # Only the owner can delete it.
    assert client.delete(f"/photos/{photo['id']}", headers=bob).status_code == 404
    assert client.delete(f"/photos/{photo['id']}", headers=ana).status_code == 204

    # Gone from the album, gallery and feed; both coyote photo files are erased.
    assert [p["species"]["slug"] for p in client.get("/me/album", headers=ana).json()["photos"]] == ["bobcat"]
    assert [p["username"] for p in client.get("/species/coyote/photos", headers=bob).json()["photos"]] == ["bob"]
    assert "ana" not in {p["username"] for p in client.get("/feed?scope=all", headers=bob).json()["photos"]
                         if p["species"]["slug"] == "coyote"}
    assert client.get(photo["url"]).status_code == 404
    assert len(list(settings.upload_dir.iterdir())) == files_before - 2

    # The coyote is un-caught and locked again; the bobcat is untouched.
    col = client.get("/me/collection", headers=ana).json()
    assert col["caught"] == 1
    coyote = next(e for e in col["entries"] if e["species"]["number"] == photo["species"]["number"])
    assert not coyote["caught"] and not coyote["species"]["revealed"]
    assert client.get("/species/coyote/photos", headers=ana).status_code == 403

    # A friend's catch still reveals the name.
    befriend(client, ana, bob, "bob", "ana")
    assert client.get("/species/coyote", headers=ana).json()["revealed"]

    # Catching it again starts over with a new badge and album photo.
    r = catch(client, fake, ana, "coyote")
    assert r["new_badge"] and r["album_photo_id"]
    assert client.delete(f"/photos/{photo['id']}", headers=ana).status_code == 404
    assert client.delete("/me/album/coyote", headers=ana).status_code == 204
    assert client.get("/me/collection", headers=ana).json()["caught"] == 1


def test_profile(client, fake):
    ana, bob, cyd = (signup(client, n) for n in ("ana", "bob", "cyd"))
    catch(client, fake, bob, "coyote", latitude=36.9741, longitude=-122.0308)
    catch(client, fake, bob, "bobcat")
    catch(client, fake, bob, "mountain_lion", latitude=34.10, longitude=-118.80)
    catch(client, fake, ana, "coyote")
    catch(client, fake, cyd, "coyote")
    coyote_id = next(p["id"] for p in client.get("/species/coyote/photos", headers=ana).json()["photos"]
                     if p["username"] == "bob")
    client.post(f"/photos/{coyote_id}/like", headers=ana)
    client.post(f"/photos/{coyote_id}/like", headers=cyd)

    assert client.get("/users/nobody", headers=ana).status_code == 404
    p = client.get("/users/bob", headers=ana).json()
    assert p["username"] == "bob" and p["friendship"] == "none"
    assert p["caught"] == 3 and p["total"] == 100
    assert p["by_rarity"]["legendary"]["caught"] == 1 and p["by_rarity"]["rare"]["caught"] == 1
    assert p["by_category"]["mammal"]["caught"] == 3
    assert p["likes_received"] == 2
    ach = {a["id"]: a for a in p["achievements"]}
    assert ach["first_catch"]["earned"] and ach["first_legendary"]["earned"] and ach["first_rare"]["earned"]
    assert not ach["collector_10"]["earned"] and ach["collector_10"]["progress"] == 3
    assert not ach["all_legendaries"]["earned"]
    # A stranger sees only photos of animals they've unlocked, with blurred places,
    # and bob's legendary stays nameless for them.
    assert [x["species"]["slug"] for x in p["photos"]] == ["coyote"] and p["hidden_photos"] == 2
    assert not p["photos"][0]["location_precise"] and p["photos"][0]["liked_by_me"]
    assert p["legendaries"][0]["common_name"] is None

    # Add friend from the profile, then the friend sees everything.
    assert client.post("/friends/requests", headers=ana, json={"username": "bob"}).status_code == 201
    assert client.get("/users/bob", headers=ana).json()["friendship"] == "requested"
    assert client.get("/users/ana", headers=bob).json()["friendship"] == "incoming"
    client.post("/friends/requests/ana/accept", headers=bob)
    p = client.get("/users/bob", headers=ana).json()
    assert p["friendship"] == "friends" and len(p["photos"]) == 3 and p["hidden_photos"] == 0
    assert p["legendaries"][0]["common_name"] == "Mountain Lion"
    assert client.get("/users/ana", headers=ana).json()["friendship"] == "self"
