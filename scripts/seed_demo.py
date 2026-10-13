"""Fill a running server with the demo "bot friends" and their catches.

Each bot captures one animal in each state by uploading real photos from the
training set (data/images/<slug>/) through the normal API, so the model really
identifies each one (or, like a player, picks the right one from the model's
top guesses). One set of bots serves every state: every new player starts as
friends with all of them, and being friends reveals the bots' animals, so each
bot only has a couple. A bot's lists have spares, tried in order, for animals
the model can't name yet.

Re-running trims any other catches the bots have (deleting a photo un-catches
the animal) and, with --db, marks the accounts as bots in the database and adds
them as friends of existing players who aren't linked to them yet.

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

CATCHES = 1  # per state
PLAYERS = {  # name: {state: species to try in order}
    "trailblazer": {"CA": ["mule_deer", "elk", "bighorn_sheep"],
                    "NC": ["white_tailed_deer", "elk", "wild_turkey"]},
    "tidepooler": {"CA": ["ochre_sea_star", "harbor_seal", "sea_otter"],
                   "NC": ["atlantic_ghost_crab", "brown_pelican", "royal_tern"]},
    "birdnerd": {"CA": ["annas_hummingbird", "acorn_woodpecker", "california_quail"],
                 "NC": ["northern_cardinal", "carolina_wren", "eastern_bluebird"]},
    "blueridger": {"CA": ["american_black_bear", "yellow_bellied_marmot", "stellers_jay"],
                   "NC": ["eastern_box_turtle", "pileated_woodpecker", "groundhog"]},
    "outerbanker": {"CA": ["brown_pelican", "western_gull", "california_sea_lion"],
                    "NC": ["osprey", "great_egret", "royal_tern"]},
    "cardinalfan": {"CA": ["western_bluebird", "california_scrub_jay", "house_finch"],
                    "NC": ["northern_mockingbird", "eastern_bluebird", "red_tailed_hawk"]},
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


def capture(args, h, rng, state, slug, parks) -> bool:
    """Upload photos of slug until one is identified (or picked) as it."""
    photos = sorted((Path(args.images) / slug).glob("*.jpg"))
    for photo in rng.sample(photos, min(4, len(photos))):  # try a few until one works
        lat, lon = parks.get(slug) or rng.choice(NC_SPOTS if state == "NC" else SPOTS)
        with open(photo, "rb") as fh:
            c = requests.post(f"{args.url}/captures", headers=h,
                              files={"photo": (photo.name, fh, "image/jpeg")},
                              data={"latitude": lat, "longitude": lon}).json()
        if c.get("matched") and c["species"]["slug"] == slug:
            return True
        if slug in [x["slug"] for x in c.get("choices", [])]:
            p = requests.post(f"{args.url}/captures/{c['capture_id']}/pick", headers=h, json={"label": slug})
            if p.ok and p.json().get("matched"):
                return True
        elif c.get("capture_id"):  # wrong animal or no match: don't keep it
            requests.post(f"{args.url}/captures/{c['capture_id']}/pick", headers=h, json={"label": "none"})
    return False


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

    for name, lists in PLAYERS.items():
        h = tokens[name]
        # Keep each bot small: drop catches from earlier, bigger seedings.
        album = requests.get(f"{args.url}/me/album", headers=h).json()
        have = {state: [] for state in lists}
        for p in album["photos"]:
            slug = p["species"]["slug"]
            keep = next((st for st, slugs in lists.items() if slug in slugs and len(have[st]) < CATCHES), None)
            if keep:
                have[keep].append(slug)
            else:
                requests.delete(f"{args.url}/photos/{p['id']}", headers=h)
                print(f"{name}: removed {slug}")
        for state, slugs in lists.items():
            # Captures are matched against the bot's current state's list.
            requests.patch(f"{args.url}/me", json={"state": state}, headers=h)
            for slug in slugs:
                if len(have[state]) >= CATCHES:
                    break
                if capture(args, h, rng, state, slug, nc_parks if state == "NC" else parks):
                    have[state].append(slug)
                    print(f"{name}: caught {slug} ({state})")
                else:
                    print(f"{name}: couldn't get {slug}, trying the next one")
        requests.patch(f"{args.url}/me", json={"state": "CA"}, headers=h)
    if args.db:
        with sqlite3.connect(args.db) as con:
            cols = {r[1] for r in con.execute("PRAGMA table_info(users)")}
            if "is_bot" in cols:
                con.execute(f"UPDATE users SET is_bot = 1 WHERE username IN ({','.join('?' * len(names))})", names)
                print("marked as bots")
                # Every player is friends with every bot, whatever their state.
                bots = [r[0] for r in con.execute(
                    f"SELECT id FROM users WHERE username IN ({','.join('?' * len(names))})", names)]
                added = 0
                for (uid,) in con.execute("SELECT id FROM users WHERE NOT COALESCE(is_bot, 0)").fetchall():
                    for bid in bots:
                        linked = con.execute(
                            "SELECT 1 FROM friendships WHERE (requester_id=? AND addressee_id=?)"
                            " OR (requester_id=? AND addressee_id=?)", (bid, uid, uid, bid)).fetchone()
                        if not linked:
                            con.execute("INSERT INTO friendships (requester_id, addressee_id, accepted, created_at)"
                                        " VALUES (?, ?, 1, CURRENT_TIMESTAMP)", (bid, uid))
                            added += 1
                print(f"added {added} bot friendships")
            else:
                print("this server has no is_bot column yet; restart it on the new code and re-run")
    print(f"demo players: {', '.join(names)} (password {password})")


if __name__ == "__main__":
    main()
