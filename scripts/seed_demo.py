"""Fill a running server with the demo "bot friends" and their catches.

Each bot catches two animals by uploading real photos from the training set
(data/images/<slug>/) through the normal API, so the model really identifies
each one. New players can add the bots as friends; being friends reveals the
bots' animals, so each bot only has a couple.

Re-running trims any other catches the bots have (deleting a photo un-catches
the animal) and, with --db, marks the accounts as bots in the database.

    python scripts/seed_demo.py --url http://127.0.0.1:8000 --db backend/demo.db
"""

import argparse
import json
import os
import random
import secrets
import sqlite3
from pathlib import Path

import requests

PLAYERS = {
    "trailblazer": ["mule_deer", "sea_otter"],
    "tidepooler": ["ochre_sea_star", "harbor_seal"],
    "birdnerd": ["annas_hummingbird", "acorn_woodpecker"],
}
# Fallback spots for species without a hotspot park.
SPOTS = [(36.49, -121.18), (38.07, -122.88), (36.82, -121.76), (34.09, -118.83), (37.74, -119.59)]


def best_parks(hotspots_json: Path) -> dict[str, tuple[float, float]]:
    """Each species' most-observed park, so a harbor seal isn't 'caught' in Yosemite."""
    best: dict[str, tuple[int, float, float]] = {}
    if hotspots_json.exists():
        for park in json.loads(hotspots_json.read_text(encoding="utf-8"))["parks"]:
            for sp in park["species"]:
                if sp["observations"] > best.get(sp["slug"], (0,))[0]:
                    best[sp["slug"]] = (sp["observations"], park["lat"], park["lon"])
    return {slug: (lat, lon) for slug, (_, lat, lon) in best.items()}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--url", default="http://127.0.0.1:8000")
    ap.add_argument("--images", default="data/images")
    ap.add_argument("--db", help="SQLite file of the server, to mark the demo players as bots")
    ap.add_argument("--hotspots", default=str(Path(__file__).resolve().parents[1] / "species" / "hotspots.json"))
    args = ap.parse_args()
    rng = random.Random(7)
    parks = best_parks(Path(args.hotspots))
    # A random password unless DEMO_PASSWORD is set (e.g. to re-run against the
    # same database); a fixed one in a public repo would let anyone log in as them.
    password = os.getenv("DEMO_PASSWORD") or secrets.token_urlsafe(12)
    tokens = {}
    for name in PLAYERS:
        r = requests.post(f"{args.url}/auth/register",
                          json={"email": f"{name}@example.com", "username": name, "password": password})
        if r.status_code == 409:
            r = requests.post(f"{args.url}/auth/login", data={"username": name, "password": password})
        r.raise_for_status()
        tokens[name] = {"Authorization": f"Bearer {r.json()['access_token']}"}

    names = list(PLAYERS)
    for i, a in enumerate(names):
        for b in names[i + 1:]:
            requests.post(f"{args.url}/friends/requests", json={"username": b}, headers=tokens[a])
            requests.post(f"{args.url}/friends/requests/{a}/accept", headers=tokens[b])

    for name, slugs in PLAYERS.items():
        # Keep each bot small: drop catches from earlier, bigger seedings.
        album = requests.get(f"{args.url}/me/album", headers=tokens[name]).json()
        have = set()
        for p in album["photos"]:
            if p["species"]["slug"] in slugs:
                have.add(p["species"]["slug"])
            else:
                requests.delete(f"{args.url}/photos/{p['id']}", headers=tokens[name])
                print(f"{name}: removed {p['species']['slug']}")
        for slug in slugs:
            if slug in have:
                continue
            photos = sorted((Path(args.images) / slug).glob("*.jpg"))
            for photo in rng.sample(photos, min(4, len(photos))):  # try a few until one matches
                lat, lon = parks.get(slug) or rng.choice(SPOTS)
                with open(photo, "rb") as fh:
                    r = requests.post(f"{args.url}/captures", headers=tokens[name],
                                      files={"photo": (photo.name, fh, "image/jpeg")},
                                      data={"latitude": lat, "longitude": lon})
                if r.ok and r.json()["matched"]:
                    print(f"{name}: caught {slug}")
                    break
            else:
                print(f"{name}: no confident match for {slug}")
    if args.db:
        with sqlite3.connect(args.db) as con:
            cols = {r[1] for r in con.execute("PRAGMA table_info(users)")}
            if "is_bot" in cols:
                con.execute(f"UPDATE users SET is_bot = 1 WHERE username IN ({','.join('?' * len(names))})", names)
                print("marked as bots")
            else:
                print("this server has no is_bot column yet; restart it on the new code and re-run")
    print(f"demo players: {', '.join(names)} (password {password})")


if __name__ == "__main__":
    main()
