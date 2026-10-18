import struct
from datetime import datetime, timedelta, timezone

import jwt
import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from app import notices
from test_api import client, fake, signup  # noqa: F401  (fixtures)
from test_social import catch


def browser_keys():
    """A pretend browser: its key pair and auth secret, as a push subscription carries them."""
    key = ec.generate_private_key(ec.SECP256R1())
    pub = key.public_key().public_bytes(serialization.Encoding.X962, serialization.PublicFormat.UncompressedPoint)
    return key, notices.b64url(pub), notices.b64url(b"0123456789abcdef")


def decrypt(body: bytes, key, p256dh: str, auth: str) -> bytes:
    """What the browser does with an aes128gcm push (RFC 8291), to check our side."""
    salt, (rs, idlen) = body[:16], struct.unpack("!IB", body[16:21])
    as_public, cipher = body[21:21 + idlen], body[21 + idlen:]
    shared = key.exchange(ec.ECDH(), ec.EllipticCurvePublicKey.from_encoded_point(ec.SECP256R1(), as_public))
    ikm = notices._hmac(notices._hmac(notices.unb64url(auth), shared),
                        b"WebPush: info\x00" + notices.unb64url(p256dh) + as_public + b"\x01")
    prk = notices._hmac(salt, ikm)
    cek = notices._hmac(prk, b"Content-Encoding: aes128gcm\x00\x01")[:16]
    nonce = notices._hmac(prk, b"Content-Encoding: nonce\x00\x01")[:12]
    plain = AESGCM(cek).decrypt(nonce, cipher, None)
    assert rs == 4096 and plain.endswith(b"\x02")
    return plain[:-1]


@pytest.fixture
def pushes(monkeypatch, tmp_path):
    monkeypatch.setenv("VAPID_PRIVATE_KEY_FILE", str(tmp_path / "vapid.pem"))
    monkeypatch.setattr(notices, "_key", None)
    monkeypatch.setattr(notices, "_last_like_push", {})
    monkeypatch.setattr(notices, "run", lambda job: job())
    sent = []

    def post(sub, payload):
        sent.append((sub.endpoint, payload))
        return 410 if "gone" in sub.endpoint else 201
    monkeypatch.setattr(notices, "post", post)
    return sent


def subscribe(client, h, endpoint):
    _, p256dh, auth = browser_keys()
    r = client.post("/push/subscribe", headers=h, json={"endpoint": endpoint, "p256dh": p256dh, "auth": auth})
    assert r.status_code == 204, r.text


def test_encryption_round_trip():
    key, p256dh, auth = browser_keys()
    body = notices.encrypt(b'{"title": "hi"}', p256dh, auth)
    assert decrypt(body, key, p256dh, auth) == b'{"title": "hi"}'


def test_encryption_matches_rfc_8291_example():
    """The worked example in RFC 8291 section 5, byte for byte."""
    k = ec.derive_private_key(int.from_bytes(notices.unb64url("yfWPiYE-n46HLnH0KqZOF1fJJU3MYrct3AELtAQ-oRw"),
                                             "big"), ec.SECP256R1())
    body = notices.encrypt(
        b"When I grow up, I want to be a watermelon",
        "BCVxsr7N_eNgVRqvHtD0zTZsEc6-VV-JvLexhqUzORcxaOzi6-AYWXvTBHm4bjyPjs7Vd8pZGH6SRpkNtoIAiw4",
        "BTBZMqHH6r4Tts7J_aSIgg", salt=notices.unb64url("DGv6ra1nlYgDCS1FRnbzlw"), server_key=k)
    assert notices.b64url(body) == (
        "DGv6ra1nlYgDCS1FRnbzlwAAEABBBP4z9KsN6nGRTbVYI_c7VJSPQTBtkgcy27mlmlMoZIIgDll6e3vCYLocInmYWAmS6TlzAC8wEqKK"
        "6PBru3jl7A_yl95bQpu6cVPTpK4Mqgkf1CXztLVBSt2Ks3oZwbuwXPXLWyouBWLVWGNWQexSgSxsj_Qulcy4a-fN")


def test_vapid_header_is_signed_with_the_served_key(client, pushes):
    k = notices.unb64url(client.get("/push/key").json()["key"])
    header = notices._vapid_header("https://fcm.googleapis.com/fcm/send/abc")
    token = header.split("t=")[1].split(",")[0]
    claims = jwt.decode(token, ec.EllipticCurvePublicKey.from_encoded_point(ec.SECP256R1(), k),
                        algorithms=["ES256"], audience="https://fcm.googleapis.com")
    assert claims["sub"].startswith("mailto:") and header.endswith("k=" + notices.b64url(k))


def test_pushes_for_friend_requests_likes_and_comments(client, fake, pushes):
    ana, bob, cyd = signup(client, "ana"), signup(client, "bob"), signup(client, "cyd")
    assert client.post("/push/subscribe", headers=ana, json={
        "endpoint": "https://push.example/x", "p256dh": "bad", "auth": "bad"}).status_code == 422
    subscribe(client, ana, "https://push.example/ana")

    client.post("/friends/requests", headers=bob, json={"username": "ana"})
    assert pushes[-1] == ("https://push.example/ana", {"title": "Friend request", "tag": "friends",
                          "body": "bob sent you a friend request", "url": "/#friends"})
    subscribe(client, bob, "https://push.example/bob")
    client.post("/friends/requests/bob/accept", headers=ana)
    assert pushes[-1][0] == "https://push.example/bob" and pushes[-1][1]["body"] == \
        "ana accepted your friend request"

    catch(client, fake, ana, "coyote")
    catch(client, fake, bob, "coyote")
    catch(client, fake, cyd, "coyote")
    photo = client.get("/me/album", headers=ana).json()["photos"][0]["id"]
    before = len(pushes)
    client.post(f"/photos/{photo}/like", headers=bob)
    assert pushes[-1][1]["body"] == "bob liked your Coyote photo" and pushes[-1][1]["tag"] == f"like-{photo}"
    # More likes soon after don't buzz again; the next notification will count them.
    client.post(f"/photos/{photo}/like", headers=cyd)
    assert len(pushes) == before + 1
    notices._last_like_push.clear()
    client.post(f"/photos/{photo}/like", headers=cyd)  # already liked: nothing new
    assert len(pushes) == before + 1

    client.post(f"/photos/{photo}/comments", headers=cyd, json={"body": "Nice!"})
    assert pushes[-1][1]["body"] == "cyd on your Coyote: Nice!"
    client.post(f"/photos/{photo}/comments", headers=ana, json={"body": "Thanks"})  # own photo
    assert pushes[-1][1]["body"] == "cyd on your Coyote: Nice!"

    # Logging out in a browser stops its notifications there.
    client.post("/push/unsubscribe", headers=ana, json={"endpoint": "https://push.example/ana"})
    client.post(f"/photos/{photo}/comments", headers=bob, json={"body": "wow"})
    assert pushes[-1][1]["body"] == "cyd on your Coyote: Nice!"


def test_expired_subscriptions_are_dropped(client, pushes):
    ana, bob = signup(client, "ana"), signup(client, "bob")
    subscribe(client, ana, "https://push.example/gone")
    client.post("/friends/requests", headers=bob, json={"username": "ana"})
    client.delete("/friends/ana", headers=bob)
    client.post("/friends/requests", headers=bob, json={"username": "ana"})
    assert len(pushes) == 1


def test_activity(client, fake):
    ana, bob, cyd = signup(client, "ana"), signup(client, "bob"), signup(client, "cyd")
    first = client.get("/me/activity", headers=ana).json()
    assert first["likes"] == [] and first["comments"] == []
    catch(client, fake, ana, "coyote")
    catch(client, fake, bob, "coyote")
    catch(client, fake, cyd, "coyote")
    photo = client.get("/me/album", headers=ana).json()["photos"][0]["id"]
    client.post(f"/photos/{photo}/like", headers=bob)
    client.post(f"/photos/{photo}/like", headers=cyd)
    client.post(f"/photos/{photo}/comments", headers=bob, json={"body": "Cool"})
    client.post(f"/photos/{photo}/comments", headers=ana, json={"body": "Thanks"})

    a = client.get("/me/activity", headers=ana, params={"since": first["now"]}).json()
    assert a["likes"] == [{"photo_id": photo, "species": "Coyote", "count": 2, "usernames": ["cyd", "bob"]}]
    assert [(c["username"], c["body"]) for c in a["comments"]] == [("bob", "Cool")]
    again = client.get("/me/activity", headers=ana, params={"since": a["now"]}).json()
    assert again["likes"] == [] and again["comments"] == []
    later = (datetime.now(timezone.utc) - timedelta(hours=1)).isoformat()
    assert client.get("/me/activity", headers=bob, params={"since": later}).json()["likes"] == []
