"""Small in-memory rate limits (one server process, so no Redis needed).

Each limit counts events per key in a sliding window. Keys that go quiet are
dropped, so the tables can't grow without bound however many names or
addresses someone tries.
"""

from __future__ import annotations

import time

from fastapi import Request

_MAX_KEYS = 10_000


class Limit:
    def __init__(self, window_s: float, max_events: int):
        self.window, self.max = window_s, max_events
        self._events: dict[str, list[float]] = {}

    def _recent(self, key: str, now: float) -> list[float]:
        return [t for t in self._events.get(key, []) if now - t < self.window]

    def blocked(self, key: str) -> bool:
        return len(self._recent(key, time.monotonic())) >= self.max

    def hit(self, key: str) -> None:
        now = time.monotonic()
        if len(self._events) >= _MAX_KEYS:
            self._events = {k: r for k, v in self._events.items() if (r := self._recent(k, now))}
            if len(self._events) >= _MAX_KEYS:  # still full of live keys: forget the oldest half
                for k in sorted(self._events, key=lambda k: self._events[k][-1])[:_MAX_KEYS // 2]:
                    del self._events[k]
        self._events[key] = self._recent(key, now) + [now]

    def clear(self, key: str | None = None) -> None:
        if key is None:
            self._events.clear()
        else:
            self._events.pop(key, None)


# Failed logins per account, and per address (stops one address trying many accounts).
failed_logins_by_account = Limit(300, 10)
failed_logins_by_ip = Limit(300, 30)
# New accounts per address.
registrations_by_ip = Limit(3600, 10)

ALL = (failed_logins_by_account, failed_logins_by_ip, registrations_by_ip)


def client_ip(request: Request) -> str:
    """The player's address. Behind the Cloudflare tunnel every request comes from
    the local cloudflared process, so the address Cloudflare saw is in
    CF-Connecting-IP; that header is only trusted on connections from this machine."""
    host = request.client.host if request.client else ""
    if host in ("127.0.0.1", "::1") and request.headers.get("cf-connecting-ip"):
        return request.headers["cf-connecting-ip"].strip()
    return host
