"""Forgotten passwords: an emailed link that lets the player pick a new one.

Rules:
- Asking for a reset always gets the same answer, so it doesn't reveal which
  emails or usernames have accounts.
- The link holds a signed token that lasts RESET_MINUTES and works once:
  it carries the password's stamp, so setting a new password ends it (and
  logs out every device signed in with the old one).
- Without SMTP settings the link is written to the server log instead, so a
  server without email still works for whoever runs it.
"""

from __future__ import annotations

import logging
import smtplib
import threading
from datetime import datetime, timedelta, timezone
from email.message import EmailMessage
from urllib.parse import quote

import jwt
from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field, field_validator
from sqlalchemy import select
from sqlalchemy.orm import Session

from . import limits
from .auth import create_token, hash_password, password_stamp
from .config import settings
from .db import get_db
from .models import User
from .schemas import TokenOut
from .social import user_named

router = APIRouter()
log = logging.getLogger(__name__)

RESET_MINUTES = 30

SENT = {"ok": True, "detail": "If that account exists, we sent it an email with a link to pick a new password."}


class ForgotIn(BaseModel):
    ident: str = Field(min_length=1, max_length=255)  # email or username


class ResetIn(BaseModel):
    token: str = Field(max_length=1000)
    password: str = Field(min_length=8)

    @field_validator("password")
    @classmethod
    def bcrypt_limit(cls, v: str) -> str:
        if len(v.encode()) > 72:
            raise ValueError("password must be at most 72 bytes")
        return v


def reset_token(user: User) -> str:
    exp = datetime.now(timezone.utc) + timedelta(minutes=RESET_MINUTES)
    return jwt.encode({"sub": str(user.id), "purpose": "reset", "pw": password_stamp(user), "exp": exp},
                      settings.secret_key, algorithm="HS256")


def send_email(to: str, subject: str, body: str) -> None:
    msg = EmailMessage()
    msg["From"], msg["To"], msg["Subject"] = settings.mail_from, to, subject
    msg.set_content(body)
    with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=20) as smtp:
        smtp.starttls()
        if settings.smtp_user:
            smtp.login(settings.smtp_user, settings.smtp_password)
        smtp.send_message(msg)


def _send_reset(user: User, link: str) -> None:
    if not settings.smtp_host:
        log.warning("No SMTP_HOST set, so no email was sent. Password reset link for %s: %s", user.username, link)
        return
    body = (f"Hi {user.username},\n\nSomeone asked to reset your Capture Animals password. To pick a new "
            f"one, open this link within {RESET_MINUTES} minutes:\n\n{link}\n\n"
            "If it wasn't you, ignore this email. Your password stays the same.\n")
    try:
        send_email(user.email, "Reset your Capture Animals password", body)
    except Exception:  # noqa: BLE001  (a mail outage shouldn't show up as a different answer)
        log.exception("Couldn't send the password reset email to user %s", user.id)


@router.post("/auth/forgot")
def forgot_password(body: ForgotIn, request: Request, db: Session = Depends(get_db)):
    ident, ip = body.ident.strip(), limits.client_ip(request)
    if limits.resets_by_ip.blocked(ip):
        raise HTTPException(status.HTTP_429_TOO_MANY_REQUESTS, "Too many reset requests. Try again later.")
    limits.resets_by_ip.hit(ip)
    user = db.scalar(select(User).where(User.email == ident.lower())) or user_named(db, ident)
    if user is None or user.is_bot or limits.resets_by_account.blocked(str(user.id)):
        return SENT
    limits.resets_by_account.hit(str(user.id))
    link = f"{settings.reset_page_url}?token={quote(reset_token(user))}"
    # Sent in the background, so the answer takes as long whether or not the account exists.
    threading.Thread(target=_send_reset, args=(user, link), daemon=True).start()
    return SENT


@router.post("/auth/reset", response_model=TokenOut)
def reset_password(body: ResetIn, db: Session = Depends(get_db)):
    expired = HTTPException(status.HTTP_400_BAD_REQUEST,
                            "This reset link has expired or was already used. Ask for a new one.")
    try:
        payload = jwt.decode(body.token, settings.secret_key, algorithms=["HS256"])
        user = db.get(User, int(payload["sub"])) if payload.get("purpose") == "reset" else None
    except (jwt.PyJWTError, KeyError, ValueError):
        raise expired
    if user is None or payload.get("pw") != password_stamp(user):
        raise expired
    user.password_hash = hash_password(body.password)
    db.commit()
    limits.failed_logins_by_account.clear(user.username.lower())
    limits.failed_logins_by_account.clear(user.email)
    return TokenOut(access_token=create_token(user))


@router.get("/reset-password", include_in_schema=False)
def reset_password_page():
    from .safety import _page
    return _page("Pick a new password", RESET_HTML)


RESET_HTML = """
<h1>Pick a new Capture Animals password</h1>
<form id="f">
<input id="pw" type="password" placeholder="New password (8+ characters)" minlength="8" required
  autocomplete="new-password">
<button style="background:#2e7d32">Save new password</button>
</form>
<p id="msg" role="status"></p>
<script>
const token = new URLSearchParams(location.search).get("token") || "";
const msg = document.getElementById("msg");
if (!token) msg.textContent = "This page needs the link from your reset email.";
document.getElementById("f").onsubmit = async (e) => {
  e.preventDefault();
  msg.textContent = "Saving…";
  try {
    const r = await fetch("/auth/reset", { method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ token, password: document.getElementById("pw").value }) });
    const t = await r.json().catch(() => ({}));
    if (!r.ok) throw new Error(Array.isArray(t.detail) ? t.detail.map((d) => d.msg).join("; ")
                               : t.detail || "Couldn't save the password");
    try { localStorage.setItem("token", t.access_token); } catch {}
    e.target.remove();
    msg.innerHTML = 'Your new password is saved. <a href="/">Open the game</a> or log in on the app.';
  } catch (err) { msg.textContent = err.message; }
};
</script>
"""
