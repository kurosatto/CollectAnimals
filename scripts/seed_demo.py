"""Fill a running server with the demo "bot friends" and their catches.

Each bot catches two animals by uploading real photos from the training set
(data/images/<slug>/) through the normal API, so the model really identifies
each one (or, like a player, picks the right one from the model's top guesses).
Bots belong to a state: new players start as friends with their own state's
bots, and being friends reveals the bots' animals, so each bot only has a couple.
A bot's list has spares, tried in order, for animals the model can't name yet.

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

CATCHES = 2
PLAYERS = {  # name: (state, species to try in order)
    "trailblazer": ("CA", ["mule_deer", "sea_otter"]),
    "tidepooler": ("CA", ["ochre_sea_star", "harbor_seal"]),
    "birdnerd": ("CA", ["annas_hummingbird", "acorn_woodpecker"]),
    "blueridger": ("NC", ["white_tailed_deer", "american_black_bear", "eastern_box_turtle", "elk", "wild_turkey"]),
    "outerbanker": ("NC", ["atlantic_ghost_crab", "brown_pelican", "royal_tern", "osprey", "great_egret"]),
    "cardinalfan": ("NC", ["northern_cardinal", "carolina_wren", "eastern_bluebird", "northern_mockingbird",
                           "red_tailed_hawk"]),
}
# Fallback spots for species without a hotspot park.
SPOTS = [(36.49, -121.18), (38.07, -122.88), (36.82, -121.76), (34.09, -118.83), (37.74, -119.59)]
NC_SPOTS = [(35.63, -83.09), (35.85, -78.75), (35.91, -75.60), (34.21, -77.89)]


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
    args = ap.parse_args()
    rng = random.Random(7)
    species_dir = Path(__file__).resolve().parents[1] / "species"
    parks = best_parks(species_dir / "hotspots.json")
    nc_parks = best_parks(species_dir / "north_carolina_hotspots.json")
    # A random password unless DEMO_PASSWORD is set (e.g. to re-run against the
    # same database); a fixed one in a public repo would let anyone log in as them.
    password = os.getenv("DEMO_PASSWORD") or secrets.token_urlsafe(12)
    tokens = {}
    for name, (state, _) in PLAYERS.items():
        r = requests.post(f"{args.url}/auth/register",
                          json={"email": f"{name}@example.com", "username": name, "password": password,
                                "state": state})
        if r.status_code == 409:
            r = requests.post(f"{args.url}/auth/login", data={"username": name, "password": password})
        r.raise_for_status()
        tokens[name] = {"Authorization": f"Bearer {r.json()['access_token']}"}
        requests.patch(f"{args.url}/me", json={"state": state}, headers=tokens[name])

    names = list(PLAYERS)
    for i, a in enumerate(names):
        for b in names[i + 1:]:
            if PLAYERS[a][0] != PLAYERS[b][0]:
                continue
            requests.post(f"{args.url}/friends/requests", json={"username": b}, headers=tokens[a])
            requests.post(f"{args.url}/friends/requests/{a}/accept", headers=tokens[b])

    for name, (state, slugs) in PLAYERS.items():
        h = tokens[name]
        # Keep each bot small: drop catches from earlier, bigger seedings.
        album = requests.get(f"{args.url}/me/album", headers=h).json()
        have = []
        for p in album["photos"]:
            slug = p["species"]["slug"]
            if slug in slugs and len(have) < CATCHES:
                have.append(slug)
            else:
                requests.delete(f"{args.url}/photos/{p['id']}", headers=h)
                print(f"{name}: removed {slug}")
        for slug in slugs:
            if len(have) >= CATCHES:
                break
            if slug in have:
                continue
            photos = sorted((Path(args.images) / slug).glob("*.jpg"))
            for photo in rng.sample(photos, min(4, len(photos))):  # try a few until one works
                lat, lon = (nc_parks if state == "NC" else parks).get(slug) or (
                    rng.choice(NC_SPOTS) if state == "NC" else rng.choice(SPOTS))
                with open(photo, "rb") as fh:
                    c = requests.post(f"{args.url}/captures", headers=h,
                                      files={"photo": (photo.name, fh, "image/jpeg")},
                                      data={"latitude": lat, "longitude": lon}).json()
                if c.get("matched") and c["species"]["slug"] == slug:
                    done = True
                elif slug in [x["slug"] for x in c.get("choices", [])]:
                    p = requests.post(f"{args.url}/captures/{c['capture_id']}/pick", headers=h, json={"label": slug})
                    done = p.ok and p.json().get("matched")
                else:
                    done = False
                    if c.get("capture_id"):  # wrong animal or no match: don't keep it
                        requests.post(f"{args.url}/captures/{c['capture_id']}/pick", headers=h,
                                      json={"label": "none"})
                if done:
                    have.append(slug)
                    print(f"{name}: caught {slug}")
                    break
            else:
                print(f"{name}: couldn't get {slug}, trying the next one")
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
