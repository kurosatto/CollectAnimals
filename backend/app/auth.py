import hashlib
from datetime import datetime, timedelta, timezone

import bcrypt
import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from .config import settings
from .db import get_db
from .models import User

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")
optional_oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login", auto_error=False)


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def verify_password(password: str, hashed: str) -> bool:
    try:
        return bcrypt.checkpw(password.encode(), hashed.encode())
    except ValueError:  # over bcrypt's 72-byte limit, so it can't be anyone's password
        return False


# Checked against when the account doesn't exist, so failed logins take the same time.
DUMMY_HASH = hash_password("not-a-real-password")


def password_stamp(user: User) -> str:
    """Changes whenever the password does, so tokens made before a change stop working."""
    return hashlib.sha256(user.password_hash.encode()).hexdigest()[:16]


def create_token(user: User) -> str:
    exp = datetime.now(timezone.utc) + timedelta(minutes=settings.token_ttl_minutes)
    return jwt.encode({"sub": str(user.id), "pw": password_stamp(user), "exp": exp},
                      settings.secret_key, algorithm="HS256")


def current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> User:
    unauthorized = HTTPException(
        status.HTTP_401_UNAUTHORIZED, "Invalid or expired token",
        headers={"WWW-Authenticate": "Bearer"})
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=["HS256"])
        if payload.get("purpose"):  # a password reset link, not a login
            raise unauthorized
        user = db.get(User, int(payload["sub"]))
    except (jwt.PyJWTError, KeyError, ValueError):
        raise unauthorized
    # Tokens from before stamps existed have no "pw" and stay valid until they expire.
    if user is None or payload.get("pw", password_stamp(user)) != password_stamp(user):
        raise unauthorized
    return user


def optional_user(token: str | None = Depends(optional_oauth2_scheme),
                  db: Session = Depends(get_db)) -> User | None:
    """The logged-in user, or None for anonymous requests. A bad token is still a 401."""
    return current_user(token, db) if token else None
