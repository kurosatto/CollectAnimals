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
    # A friend's capture unlocks the full entry, but it isn't yours.
    d = client.get("/species/bobcat/dex", headers=ana).json()
    assert d["fun_fact"] and not d["captured"]

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
    catch(client, fake, cyd, "ringtail", latitude=34.10, longitude=-118.80)    # legendary
    catch(client, fake, ana, "coyote")                                              # no location

    feed = client.get("/feed", headers=ana).json()
    assert [(p["username"], p["species"]["number"]) for p in feed["photos"]][0][0] == "ana"
    items = {p["username"] + ":" + (p["species"]["slug"] or p["species"]["category"]): p
             for p in feed["photos"]}
    coyote = items["bob:coyote"]
    assert coyote["place"] == "near Santa Cruz" and coyote["latitude"] == 37.0
    assert coyote["url"] and coyote["caught_at"]
    # ana hasn't unlocked the bobcat or the ringtail: no name, no photo.
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
        {"show_in_feed": False, "is_private": False}
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
    # Each state names its own towns and regions; none fall back to California's.
    assert places.place_name(35.73, -81.34) == "near Hickory"
    assert places.place_name(35.25, -76.2) == "in the Outer Banks"
    assert places.region(34.8, -116.0) == "the California deserts"
    assert places.region(35.6, -82.5) == "the Blue Ridge Mountains"
    assert places.region(40.7, -74.0) == "New York"  # every state is on the map now
    assert places.region(51.5, -0.1) == "another state"  # London


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
    catch(client, fake, bob, "ringtail", latitude=34.10, longitude=-118.80)
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
    assert p["legendaries"][0]["common_name"] == "Ringtail"
    assert client.get("/users/ana", headers=ana).json()["friendship"] == "self"


def test_bot_friends(client, fake):
    from app.db import SessionLocal
    from app.models import User

    ana, bot = signup(client, "ana"), signup(client, "birdnerd")
    signup(client, "trailblazer")
    signup(client, "human")
    with SessionLocal() as db:
        for u in db.query(User).filter(User.username.in_(["birdnerd", "trailblazer"])):
            u.is_bot = True
        db.commit()
    catch(client, fake, bot, "coyote")

    s = client.get("/friends/suggestions", headers=ana).json()
    assert s == [{"username": "birdnerd", "caught": 1, "is_bot": True},
                 {"username": "trailblazer", "caught": 0, "is_bot": True}]
    # Bots accept right away, and their catches reveal names.
    assert client.post("/friends/requests", headers=ana, json={"username": "birdnerd"}).json() == \
        {"status": "friends"}
    f = client.get("/friends", headers=ana).json()
    assert f["friends"][0] == {**f["friends"][0], "username": "birdnerd", "is_bot": True, "caught": 1}
    assert client.get("/species/coyote", headers=ana).json()["revealed"]
    assert [x["username"] for x in client.get("/friends/suggestions", headers=ana).json()] == ["trailblazer"]
    assert client.get("/users/birdnerd", headers=ana).json()["is_bot"] is True
    assert client.get("/users/human", headers=ana).json()["is_bot"] is False
    assert client.post("/friends/requests", headers=ana, json={"username": "human"}).json() == \
        {"status": "requested"}


def test_private_player(client, fake):
    admin, ana, bob = signup(client, "admin"), signup(client, "ana"), signup(client, "bob")
    catch(client, fake, admin, "coyote")
    catch(client, fake, admin, "bobcat")
    catch(client, fake, ana, "coyote")
    catch(client, fake, bob, "coyote")
    assert client.patch("/me/settings", headers=admin, json={"is_private": True}).json() == \
        {"show_in_feed": True, "is_private": True}
    assert client.get("/me", headers=admin).json()["is_private"] is True
    befriend(client, admin, bob, "bob", "admin")
    admin_photo = client.get("/me/album", headers=admin).json()["photos"][0]["id"]

    def users(path, h):
        return {p["username"] for p in client.get(path, headers=h).json()["photos"]}

    # Strangers don't see a private player's photos anywhere.
    assert users("/species/coyote/photos", ana) == {"ana", "bob"}
    assert users("/feed", ana) == {"ana", "bob"}
    prof = client.get("/users/admin", headers=ana).json()
    assert prof["is_private"] and prof["photos"] == [] and prof["hidden_photos"] == 2
    assert client.post(f"/photos/{admin_photo}/like", headers=ana).status_code == 404
    # Friends and the player themself still do.
    assert users("/species/coyote/photos", bob) == {"admin", "ana", "bob"}
    assert "admin" in users("/feed", bob)
    assert len(client.get("/users/admin", headers=bob).json()["photos"]) == 2
    assert client.post(f"/photos/{admin_photo}/like", headers=bob).status_code == 204
    assert users("/species/coyote/photos", admin) == {"admin", "ana", "bob"}
    # Captures only reveal names to friends, as for everyone.
    assert not client.get("/species/bobcat", headers=ana).json()["revealed"]

    client.patch("/me/settings", headers=admin, json={"is_private": False})
    assert "admin" in users("/species/coyote/photos", ana)


def test_feed_by_state_and_global(client, fake):
    ana, nina = signup(client, "ana"), signup(client, "nina", state="NC")
    catch(client, fake, ana, "coyote", latitude=36.97, longitude=-122.03)    # Santa Cruz, CA
    catch(client, fake, ana, "raccoon", latitude=35.78, longitude=-78.64)    # Raleigh, NC (on a trip)
    catch(client, fake, nina, "coyote")                                      # no location, NC player

    def slugs(h, **params):
        return sorted(p["username"] + ":" + str(p["species"]["number"])
                      for p in client.get("/feed", headers=h, params=params).json()["photos"])

    everyone = slugs(ana, scope="all")
    assert len(everyone) == 3                                   # global: every capture
    assert len(slugs(ana, scope="state")) == 1                  # ana's state (CA): Santa Cruz only
    nc = slugs(ana, scope="state", state="NC")
    assert len(nc) == 2 and any(s.startswith("nina:") for s in nc)
    assert slugs(nina, scope="state") == nc                     # defaults to the viewer's state
    assert client.get("/feed", headers=ana, params={"scope": "state", "state": "ZZ"}).status_code == 404


def test_comments_from_strangers(client, fake):
    ana, bob, cyd, dee = (signup(client, n) for n in ("ana", "bob", "cyd", "dee"))
    catch(client, fake, ana, "coyote")
    catch(client, fake, bob, "coyote")  # bob isn't ana's friend but has the coyote revealed
    photo = client.get("/me/album", headers=ana).json()["photos"][0]["id"]

    # Strangers can like and comment; whitespace is tidied.
    assert client.post(f"/photos/{photo}/like", headers=bob).status_code == 204
    r = client.post(f"/photos/{photo}/comments", headers=bob, json={"body": "  Great   shot! "})
    assert r.status_code == 201 and r.json()["body"] == "Great shot!" and r.json()["is_mine"]
    assert client.post(f"/photos/{photo}/comments", headers=ana, json={"body": "Thanks"}).status_code == 201
    assert client.post(f"/photos/{photo}/comments", headers=bob, json={"body": "   "}).status_code == 422
    assert client.post(f"/photos/{photo}/comments", headers=bob, json={"body": "x" * 301}).status_code == 422
    # Players who can't see the photo can't read or write comments.
    assert client.get(f"/photos/{photo}/comments", headers=dee).status_code == 404
    assert client.post(f"/photos/{photo}/comments", headers=dee, json={"body": "hi"}).status_code == 404

    comments = client.get(f"/photos/{photo}/comments", headers=ana).json()
    assert [(c["username"], c["body"], c["can_delete"]) for c in comments] == \
        [("bob", "Great shot!", True), ("ana", "Thanks", True)]
    p = client.get("/species/coyote/photos", headers=bob).json()["photos"]
    assert {x["username"]: x["comment_count"] for x in p} == {"ana": 2, "bob": 0}
    feed = client.get("/feed?scope=all", headers=bob).json()["photos"]
    assert next(x for x in feed if x["id"] == photo)["comment_count"] == 2

    # Only the commenter or the photo's owner can delete a comment.
    bobs, anas = comments[0]["id"], comments[1]["id"]
    assert client.get(f"/photos/{photo}/comments", headers=bob).json()[1]["can_delete"] is False
    assert client.delete(f"/comments/{anas}", headers=bob).status_code == 404
    catch(client, fake, cyd, "coyote")
    assert client.delete(f"/comments/{bobs}", headers=cyd).status_code == 404
    assert client.delete(f"/comments/{bobs}", headers=ana).status_code == 204
    assert [c["id"] for c in client.get(f"/photos/{photo}/comments", headers=cyd).json()] == [anas]

    # A private player's photos only take comments from friends.
    assert client.patch("/me/settings", headers=ana, json={"is_private": True}).status_code == 200
    assert client.post(f"/photos/{photo}/comments", headers=cyd, json={"body": "hi"}).status_code == 404
    client.patch("/me/settings", headers=ana, json={"is_private": False})

    # Spam guard.
    for i in range(4):
        assert client.post(f"/photos/{photo}/comments", headers=cyd, json={"body": f"{i}"}).status_code == 201
    assert client.post(f"/photos/{photo}/comments", headers=cyd, json={"body": "5"}).status_code == 201
    assert client.post(f"/photos/{photo}/comments", headers=cyd, json={"body": "6"}).status_code == 429

    # Deleting the photo takes its comments with it.
    assert client.delete(f"/photos/{photo}", headers=ana).status_code == 204
    from app.db import SessionLocal
    from app.models import PhotoComment
    with SessionLocal() as db:
        assert not db.query(PhotoComment).filter_by(photo_id=photo).count()


def test_friend_field_guide_uses_their_state(client, fake):
    ana, nina, zed = signup(client, "ana"), signup(client, "nina", state="NC"), signup(client, "zed")
    catch(client, fake, nina, "american_black_bear")
    catch(client, fake, ana, "coyote")
    catch(client, fake, zed, "bobcat")
    assert client.get("/users/nina/collection", headers=ana).status_code == 403   # not friends yet
    befriend(client, ana, nina, "nina", "ana")
    assert client.get("/users/nobody/collection", headers=ana).status_code == 404

    g = client.get("/users/nina/collection", headers=ana).json()
    assert g["state"] == "NC" and g["username"] == "nina" and g["caught"] == 1
    assert g["total"] == client.get("/me/collection", headers=nina).json()["total"]
    by = {e["species"]["slug"]: e for e in g["entries"] if e["species"]["revealed"]}
    bear = by["american_black_bear"]
    assert bear["caught"] and not bear["you_caught"] and bear["photo_url"]
    coyote = by["coyote"]                  # ana's California capture: named, but not caught here
    assert not coyote["caught"] and not coyote["you_caught"]
    assert "bobcat" not in by              # zed is nobody's friend, so it stays "???"
    assert sum(not e["species"]["revealed"] for e in g["entries"]) == g["total"] - 2
    # Friendship works both ways, in the viewer's own state.
    back = client.get("/users/ana/collection", headers=nina).json()
    assert back["state"] == "CA" and back["caught"] == 1


def test_friend_field_guide_places(client, fake):
    ana, nina = signup(client, "ana"), signup(client, "nina", state="NC")
    befriend(client, ana, nina, "nina", "ana")
    g = client.get("/users/nina/collection", headers=ana).json()
    assert g["primary_state"] == "NC"
    assert [p["state"] for p in g["places"]] == ["NC"]      # primary state is always a place
    catch(client, fake, nina, "american_black_bear")         # on both state lists
    g = client.get("/users/nina/collection", headers=ana).json()
    assert [(p["state"], p["caught"]) for p in g["places"]] == [("NC", 1)]   # counts only where captured
    catch(client, fake, nina, "american_black_bear", latitude=36.97, longitude=-122.03)   # on a trip to CA
    g = client.get("/users/nina/collection", headers=ana).json()
    places = {p["state"]: p for p in g["places"]}
    assert places["NC"]["caught"] == 1 and places["CA"]["caught"] == 1 and places["CA"]["name"]
    ca = client.get("/users/nina/collection?state=CA", headers=ana).json()
    assert client.get("/users/nina", headers=ana).json()["state"] == "NC"
    assert ca["state"] == "CA" and ca["primary_state"] == "NC" and ca["caught"] == 1
    assert client.get("/users/nina/collection?state=ZZ", headers=ana).status_code == 404
