"""Fill a running server with a few demo players, friendships and catches.

Uploads real photos from the training set (data/images/<slug>/) through the
normal API, so the model really identifies each one. Only catches the model
accepts count, which is what a visitor would see too.

    python scripts/seed_demo.py --url http://127.0.0.1:8000
"""

import argparse
import json
import random
from pathlib import Path

import requests

PLAYERS = {
    "trailblazer": ["california_condor", "sea_otter", "elk", "brown_pelican", "california_quail",
                    "western_fence_lizard", "monarch", "mule_deer"],
    "tidepooler": ["ochre_sea_star", "giant_green_anemone", "harbor_seal", "california_sea_lion",
                   "western_gull", "brown_pelican"],
    "birdnerd": ["annas_hummingbird", "acorn_woodpecker", "red_tailed_hawk", "great_blue_heron",
                 "california_scrub_jay", "bald_eagle", "california_quail"],
}
PASSWORD = "demo-password-123"
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
    ap.add_argument("--hotspots", default=str(Path(__file__).resolve().parents[1] / "species" / "hotspots.json"))
    args = ap.parse_args()
    rng = random.Random(7)
    parks = best_parks(Path(args.hotspots))
    tokens = {}
    for name in PLAYERS:
        r = requests.post(f"{args.url}/auth/register",
                          json={"email": f"{name}@example.com", "username": name, "password": PASSWORD})
        if r.status_code == 409:
            r = requests.post(f"{args.url}/auth/login", data={"username": name, "password": PASSWORD})
        r.raise_for_status()
        tokens[name] = {"Authorization": f"Bearer {r.json()['access_token']}"}

    names = list(PLAYERS)
    for i, a in enumerate(names):
        for b in names[i + 1:]:
            requests.post(f"{args.url}/friends/requests", json={"username": b}, headers=tokens[a])
            requests.post(f"{args.url}/friends/requests/{a}/accept", headers=tokens[b])

    for name, slugs in PLAYERS.items():
        for slug in slugs:
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
    print(f"demo players: {', '.join(names)} (password {PASSWORD})")


if __name__ == "__main__":
    main()
