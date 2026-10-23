from urllib.parse import parse_qs, urlparse

import pytest

from app import recovery
from test_api import client, signup  # noqa: F401  (fixtures)


class _Now:
    """Runs the email "thread" right away so the test can read the link."""
    def __init__(self, target, args, daemon):
        self.target, self.args = target, args

    def start(self):
        self.target(*self.args)


@pytest.fixture
def outbox(monkeypatch):
    sent = []
    monkeypatch.setattr(recovery.threading, "Thread", _Now)
    monkeypatch.setattr(recovery.settings, "smtp_host", "smtp.example.com")
    monkeypatch.setattr(recovery, "send_email", lambda to, subject, body: sent.append((to, body)))
    return sent


def token_in(body):
    link = next(w for w in body.split() if w.startswith("http"))
    return parse_qs(urlparse(link).query)["token"][0]


def test_reset_password_by_email(client, outbox):
    old = signup(client, "ana")
    r = client.post("/auth/forgot", json={"ident": "ana"})
    assert r.status_code == 200
    # Unknown accounts get the same answer and no email.
    assert client.post("/auth/forgot", json={"ident": "nobody@example.com"}).json() == r.json()
    assert len(outbox) == 1 and outbox[0][0] == "ana@example.com"
    token = token_in(outbox[0][1])

    # The reset token can't be used to log in.
    assert client.get("/me", headers={"Authorization": f"Bearer {token}"}).status_code == 401
    r = client.post("/auth/reset", json={"token": token, "password": "new-pass-123"})
    assert r.status_code == 200
    assert client.get("/me", headers={"Authorization": f"Bearer {r.json()['access_token']}"}).status_code == 200
    # Old logins end, the old password stops working, the new one works.
    assert client.get("/me", headers=old).status_code == 401
    assert client.post("/auth/login", data={"username": "ana", "password": "hunter22!"}).status_code == 401
    assert client.post("/auth/login", data={"username": "ana@example.com", "password": "new-pass-123"}).status_code == 200
    # The link works once.
    assert client.post("/auth/reset", json={"token": token, "password": "another-pass"}).status_code == 400


def test_reset_rejects_bad_tokens_and_limits_emails(client, outbox):
    h = signup(client, "ana")
    login_token = h["Authorization"].split()[1]
    assert client.post("/auth/reset", json={"token": login_token, "password": "new-pass-123"}).status_code == 400
    assert client.post("/auth/reset", json={"token": "junk", "password": "new-pass-123"}).status_code == 400
    for _ in range(5):
        assert client.post("/auth/forgot", json={"ident": "ana"}).status_code == 200
    assert len(outbox) == 3
    assert "Pick a new" in client.get("/reset-password").text


def test_signup_turns_away_under_13(client):
    from datetime import datetime
    body = {"email": "kid@example.com", "username": "kid", "password": "hunter22!"}
    r = client.post("/auth/register", json={**body, "birth_year": datetime.now().year - 10})
    assert r.status_code == 403 and "13" in r.json()["detail"]
    assert client.post("/auth/register", json={**body, "birth_year": datetime.now().year - 20}).status_code == 201
