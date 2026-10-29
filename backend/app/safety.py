"""Deleting your account, blocking players, and reporting photos, comments and
players for a moderator (what Google Play asks of apps with accounts and posts).

Rules:
- Deleting an account removes everything of the player's at once: photos and
  their files, captures, badges, likes, comments, friends, blocks and reports.
- Blocking works both ways: neither player sees the other's photos or comments
  in the feed, galleries or profiles, and they can't friend, like or comment on
  each other. Blocking also ends a friendship or pending request.
- A report goes to the moderators (ADMIN_USERNAMES). A photo or comment that
  HIDE_AFTER different players reported is hidden from everyone but its owner
  until a moderator keeps it. Moderators can remove the content or delete the
  player's account.
"""

from __future__ import annotations

import re
from datetime import datetime, timedelta, timezone
from html import escape
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Response, status
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field
from sqlalchemy import delete, func, or_, select
from sqlalchemy.orm import Session

from . import naming, notices
from .auth import current_user, verify_password
from .config import ROOT, settings
from .db import get_db
from .models import (AlbumPhoto, Badge, Block, Capture, Friendship, GameItem, GameScore, AnimalSkin, IdFeedback, PhotoComment, PhotoLike,
                     PushSubscription, Report, User)
from .social import _between, _user_by_name, _visible_photo, blocked_ids, clear_reactions
from .storage import get_storage

router = APIRouter()

# Different players reporting one photo or comment before it's hidden for review.
HIDE_AFTER = 3
# Reports one player can send per day.
REPORTS_PER_DAY = 20
REASONS = ("spam", "bullying", "inappropriate", "personal_info", "not_animal", "other")


def is_admin(user: User) -> bool:
    return user.username.lower() in settings.admin_usernames


def admin_user(user: User = Depends(current_user)) -> User:
    if not is_admin(user):
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Moderators only")
    return user


# --- deleting an account ------------------------------------------------------

class DeleteAccountIn(BaseModel):
    password: str = Field(max_length=200)


def delete_account(db: Session, user: User) -> None:
    """Remove the player and everything that belongs to them, photo files included."""
    uid = user.id
    photo_ids = list(db.scalars(select(AlbumPhoto.id).where(AlbumPhoto.user_id == uid)))
    # Their comments, and everyone's comments on their photos (those go with the photos).
    comment_ids = list(db.scalars(select(PhotoComment.id).where(
        or_(PhotoComment.user_id == uid, PhotoComment.photo_id.in_(photo_ids)))))
    db.execute(delete(Report).where(or_(Report.reporter_id == uid, Report.reported_user_id == uid,
                                        Report.photo_id.in_(photo_ids), Report.comment_id.in_(comment_ids))))
    for pid in photo_ids:
        clear_reactions(db, pid)
    db.execute(delete(PhotoLike).where(PhotoLike.user_id == uid))
    db.execute(delete(PhotoComment).where(PhotoComment.user_id == uid))
    db.execute(delete(AlbumPhoto).where(AlbumPhoto.user_id == uid))
    db.execute(delete(Badge).where(Badge.user_id == uid))
    db.execute(delete(IdFeedback).where(IdFeedback.user_id == uid))
    naming.forget_photos(db, uid, delete_rows=True)
    storage = get_storage()
    for path in db.scalars(select(Capture.image_path).where(Capture.user_id == uid)):
        if path:
            try:
                storage.delete(path)
            except ValueError:
                pass
    db.execute(delete(Capture).where(Capture.user_id == uid))
    db.execute(delete(Friendship).where(or_(Friendship.requester_id == uid, Friendship.addressee_id == uid)))
    db.execute(delete(Block).where(or_(Block.blocker_id == uid, Block.blocked_id == uid)))
    db.execute(delete(PushSubscription).where(PushSubscription.user_id == uid))
    db.execute(delete(GameScore).where(GameScore.user_id == uid))
    db.execute(delete(GameItem).where(GameItem.user_id == uid))
    db.execute(delete(AnimalSkin).where(AnimalSkin.user_id == uid))
    db.delete(user)
    db.commit()


@router.delete("/me", status_code=204)
@router.post("/me/delete", status_code=204)  # for clients that can't send a body with DELETE
def delete_me(body: DeleteAccountIn, user: User = Depends(current_user), db: Session = Depends(get_db)):
    """Delete your account for good. Needs your password, so a borrowed phone can't do it."""
    if not verify_password(body.password, user.password_hash):
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Wrong password")
    delete_account(db, user)
    return Response(status_code=204)


# --- blocking -----------------------------------------------------------------

class BlockIn(BaseModel):
    username: str


@router.get("/blocks")
def list_blocks(user: User = Depends(current_user), db: Session = Depends(get_db)) -> list[str]:
    """Players you blocked (not the ones who blocked you)."""
    rows = db.scalars(select(Block).where(Block.blocker_id == user.id).order_by(Block.created_at))
    return [b.blocked.username for b in rows]


@router.post("/blocks", status_code=204)
def block(body: BlockIn, user: User = Depends(current_user), db: Session = Depends(get_db)):
    other = _user_by_name(db, body.username)
    if other.id == user.id:
        raise HTTPException(400, "You can't block yourself")
    if not db.scalar(select(Block.id).where(Block.blocker_id == user.id, Block.blocked_id == other.id)):
        db.add(Block(blocker_id=user.id, blocked_id=other.id))
    db.execute(delete(Friendship).where(_between(user.id, other.id)))
    db.commit()
    return Response(status_code=204)


@router.delete("/blocks/{username}", status_code=204)
def unblock(username: str, user: User = Depends(current_user), db: Session = Depends(get_db)):
    other = _user_by_name(db, username)
    db.execute(delete(Block).where(Block.blocker_id == user.id, Block.blocked_id == other.id))
    db.commit()
    return Response(status_code=204)


# --- reports --------------------------------------------------------------------

class ReportIn(BaseModel):
    photo_id: int | None = None
    comment_id: int | None = None
    username: str | None = None
    reason: Literal[REASONS]
    details: str | None = Field(None, max_length=500)


def _open_reporters(db: Session, **target) -> int:
    col, value = next(iter(target.items()))
    return db.scalar(select(func.count(func.distinct(Report.reporter_id))).where(
        getattr(Report, col) == value, Report.status == "open")) or 0


@router.post("/reports", status_code=201)
def report(body: ReportIn, user: User = Depends(current_user), db: Session = Depends(get_db)):
    """Flag a photo, a comment or a player. The same player reporting the same
    thing again just updates their report."""
    if sum(x is not None for x in (body.photo_id, body.comment_id, body.username)) != 1:
        raise HTTPException(422, "Report one photo, comment or player")
    since = datetime.now(timezone.utc) - timedelta(days=1)
    if (db.scalar(select(func.count()).select_from(Report).where(
            Report.reporter_id == user.id, Report.created_at >= since)) or 0) >= REPORTS_PER_DAY:
        raise HTTPException(429, "You've sent a lot of reports today. Try again tomorrow.")
    photo = comment = None
    if body.photo_id is not None:
        photo = _visible_photo(db, body.photo_id, user)
        target, owner = {"photo_id": photo.id}, photo.user_id
    elif body.comment_id is not None:
        comment = db.get(PhotoComment, body.comment_id)
        if comment is None or comment.user_id in blocked_ids(db, user.id):
            raise HTTPException(404, "No such comment")
        _visible_photo(db, comment.photo_id, user)
        target, owner = {"comment_id": comment.id}, comment.user_id
    else:
        other = _user_by_name(db, body.username)
        target, owner = {"reported_user_id": other.id, "photo_id": None, "comment_id": None}, other.id
    if owner == user.id:
        raise HTTPException(400, "You can't report yourself")

    existing = db.scalar(select(Report).where(Report.reporter_id == user.id, Report.status == "open",
                                              *(getattr(Report, k) == v if v is not None else getattr(Report, k).is_(None)
                                                for k, v in target.items())))
    if existing:
        existing.reason, existing.details = body.reason, body.details
    else:
        db.add(Report(reporter_id=user.id, reported_user_id=owner, photo_id=target.get("photo_id"),
                      comment_id=target.get("comment_id"), reason=body.reason, details=body.details))
    db.flush()
    hidden = False
    if photo is not None and _open_reporters(db, photo_id=photo.id) >= HIDE_AFTER:
        photo.hidden = hidden = True
    if comment is not None and _open_reporters(db, comment_id=comment.id) >= HIDE_AFTER:
        comment.hidden = hidden = True
    db.commit()
    if not existing:
        for name in settings.admin_usernames:
            admin = db.scalar(select(User).where(func.lower(User.username) == name))
            if admin and admin.id != user.id:
                notices.notify(admin.id, "New report", "A player reported something. Have a look.",
                               "report", "/#reports")
    return {"status": "received", "hidden": hidden}


# --- moderators -----------------------------------------------------------------

def _kind(r: Report) -> tuple[str, int]:
    if r.photo_id is not None:
        return "photo", r.photo_id
    if r.comment_id is not None:
        return "comment", r.comment_id
    return "user", r.reported_user_id


@router.get("/admin/reports")
def open_reports(admin: User = Depends(admin_user), db: Session = Depends(get_db)) -> list[dict]:
    """Open reports, one entry per reported photo, comment or player, newest first."""
    groups: dict[tuple[str, int], dict] = {}
    for r in db.scalars(select(Report).where(Report.status == "open").order_by(Report.created_at.desc())):
        kind, tid = _kind(r)
        g = groups.get((kind, tid))
        if g is None:
            owner = db.get(User, r.reported_user_id)
            g = groups[(kind, tid)] = {"kind": kind, "id": tid, "username": owner.username if owner else None,
                                       "reports": 0, "reasons": {}, "details": [], "latest": r.created_at,
                                       "hidden": False, "photo_url": None, "comment": None}
            if kind == "photo" and (p := db.get(AlbumPhoto, tid)):
                g["photo_url"] = get_storage().url(p.capture.image_path)
                g["species"] = p.species.common_name
                g["hidden"] = bool(p.hidden)
            if kind == "comment" and (c := db.get(PhotoComment, tid)):
                g["comment"] = c.body
                g["hidden"] = bool(c.hidden)
        g["reports"] += 1
        g["reasons"][r.reason] = g["reasons"].get(r.reason, 0) + 1
        if r.details:
            g["details"].append(r.details)
    return list(groups.values())


class ResolveIn(BaseModel):
    kind: Literal["photo", "comment", "user"]
    id: int
    # remove: take the photo or comment down; keep: it's fine (shown again if it
    # was hidden); delete_account: remove the player and everything of theirs.
    action: Literal["remove", "keep", "delete_account"]


@router.post("/admin/reports/resolve", status_code=204)
def resolve(body: ResolveIn, admin: User = Depends(admin_user), db: Session = Depends(get_db)):
    col = {"photo": Report.photo_id, "comment": Report.comment_id}.get(body.kind)
    where = [Report.status == "open"]
    where += [col == body.id] if col is not None else [Report.reported_user_id == body.id,
                                                       Report.photo_id.is_(None), Report.comment_id.is_(None)]
    owner_id = {"photo": lambda: (p := db.get(AlbumPhoto, body.id)) and p.user_id,
                "comment": lambda: (c := db.get(PhotoComment, body.id)) and c.user_id,
                "user": lambda: body.id}[body.kind]()
    if not owner_id:
        db.execute(delete(Report).where(*where))  # the content is already gone
        db.commit()
        return Response(status_code=204)
    if body.action == "delete_account":
        owner = db.get(User, owner_id)
        if owner.id == admin.id:
            raise HTTPException(400, "That's your own account")
        delete_account(db, owner)
        return Response(status_code=204)
    if body.kind == "photo":
        db.get(AlbumPhoto, body.id).hidden = body.action == "remove"
    elif body.kind == "comment":
        c = db.get(PhotoComment, body.id)
        if body.action == "remove":
            db.execute(delete(Report).where(Report.comment_id == c.id))
            db.delete(c)
        else:
            c.hidden = False
    if not (body.kind == "comment" and body.action == "remove"):
        for r in db.scalars(select(Report).where(*where)):
            r.status = "removed" if body.action == "remove" else "kept"
            r.resolved_at = datetime.now(timezone.utc)
    db.commit()
    return Response(status_code=204)


# --- pages for the store listing --------------------------------------------------

def _page(title: str, body: str) -> HTMLResponse:
    return HTMLResponse(f"""<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><title>{title} · Capture Animals</title>
<style>body{{font:16px/1.55 system-ui,sans-serif;max-width:720px;margin:0 auto;padding:16px;color:#1d2a1f;background:#f6f8f3}}
h1{{font-size:1.5rem}}h2{{font-size:1.1rem;margin-top:1.6em}}input,button{{font:inherit;padding:8px 10px;margin:4px 0;
width:100%;box-sizing:border-box}}button{{background:#b33;color:#fff;border:0;border-radius:6px;cursor:pointer}}
a{{color:#2e7d32}}@media (prefers-color-scheme:dark){{body{{background:#141a15;color:#e3ebe2}}a{{color:#8fd694}}}}</style>
</head><body>{body}</body></html>""")


# The policy itself is docs/privacy.html, so the same page can also live on GitHub Pages,
# which stays up while the game server is off.
PRIVACY_FILE = ROOT / "docs" / "privacy.html"


@router.get("/privacy", include_in_schema=False)
def privacy_page():
    html = _docs_links(PRIVACY_FILE.read_text(encoding="utf-8"))
    if settings.contact_email:
        e = escape(settings.contact_email)
        html = re.sub(r"<!--CONTACT-->.*?<!--/CONTACT-->",
                      f'<p>Questions or requests: <a href="mailto:{e}">{e}</a>.</p>', html, flags=re.S)
    return HTMLResponse(html)


RULES_FILE = ROOT / "docs" / "rules.html"


def _docs_links(html: str) -> str:
    """The docs pages link each other by file name (GitHub Pages); on the server they're paths."""
    for page in ("privacy", "rules", "delete-account"):
        html = html.replace(f'href="{page}.html"', f'href="/{page}"')
    return html


@router.get("/rules", include_in_schema=False)
def rules_page():
    return HTMLResponse(_docs_links(RULES_FILE.read_text(encoding="utf-8")))


@router.get("/delete-account", include_in_schema=False)
def delete_account_page():
    return _page("Delete your account", DELETE_HTML)




DELETE_HTML = """
<h1>Delete your Capture Animals account</h1>
<p>This deletes your account and everything in it right away: your photos, captures, Field Guide, likes,
comments, friends, blocks and reports. It can't be undone. You can also do this in the app: open your
account and choose <b>Delete account</b>.</p>
<form id="f">
<input id="ident" placeholder="Email or username" required autocomplete="username">
<input id="pw" type="password" placeholder="Password" required autocomplete="current-password">
<button>Delete my account</button>
</form>
<p id="msg" role="status"></p>
<p><a href="/privacy">Privacy policy</a></p>
<script>
document.getElementById("f").onsubmit = async (e) => {
  e.preventDefault();
  const msg = document.getElementById("msg"), pw = document.getElementById("pw").value;
  if (!confirm("Delete your account and all your photos for good?")) return;
  msg.textContent = "Deleting…";
  try {
    const r = await fetch("/auth/login", { method: "POST", body: new URLSearchParams({
      username: document.getElementById("ident").value, password: pw }) });
    const t = await r.json();
    if (!r.ok) throw new Error(t.detail || "Couldn't log in");
    const d = await fetch("/me", { method: "DELETE", headers: { Authorization: "Bearer " + t.access_token,
      "Content-Type": "application/json" }, body: JSON.stringify({ password: pw }) });
    if (!d.ok) throw new Error((await d.json().catch(() => ({}))).detail || "Couldn't delete the account");
    try { localStorage.removeItem("token"); } catch {}
    e.target.remove();
    msg.textContent = "Your account and everything in it is deleted.";
  } catch (err) { msg.textContent = err.message; }
};
</script>
"""
