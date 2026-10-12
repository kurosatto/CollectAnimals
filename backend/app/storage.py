"""Where photo files live.

Everything goes through `get_storage()`, so moving photos to S3, Cloudflare R2
or similar later means adding one class here and pointing STORAGE_BACKEND at
it; the database only ever stores the key.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Protocol

from .config import settings

_KEY = re.compile(r"^[A-Za-z0-9_.-]{1,128}$")


class Storage(Protocol):
    def put(self, key: str, data: bytes, content_type: str = "image/jpeg") -> None: ...
    def get(self, key: str) -> bytes | None: ...
    def delete(self, key: str) -> None: ...
    def url(self, key: str) -> str:
        """URL a browser can load the photo from (a presigned URL for cloud stores)."""
        ...


class LocalStorage:
    """Files in a directory on this server, served by the app at /media/{key}."""

    def __init__(self, root: Path):
        self.root = root
        root.mkdir(parents=True, exist_ok=True)

    def _path(self, key: str) -> Path:
        if not _KEY.match(key) or key.startswith("."):
            raise ValueError(f"bad storage key: {key!r}")
        return self.root / key

    def put(self, key: str, data: bytes, content_type: str = "image/jpeg") -> None:
        self._path(key).write_bytes(data)

    def get(self, key: str) -> bytes | None:
        p = self._path(key)
        return p.read_bytes() if p.exists() else None

    def delete(self, key: str) -> None:
        self._path(key).unlink(missing_ok=True)

    def url(self, key: str) -> str:
        return f"/media/{key}"


_storage: Storage | None = None


def get_storage() -> Storage:
    global _storage
    if _storage is None:
        if settings.storage_backend != "local":
            raise RuntimeError(f"Unknown STORAGE_BACKEND {settings.storage_backend!r}")
        _storage = LocalStorage(settings.upload_dir)
    return _storage


def reset_storage() -> None:
    global _storage
    _storage = None
