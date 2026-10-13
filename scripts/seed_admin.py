"""Demo only: a private test account with one capture of every animal.

Creates (or logs into) the account, turns off sharing, then uploads a training
photo of each species. If the model doesn't name it outright, the script picks
the right animal from the model's top guesses, like a player would with
"Not this animal?". Species it already has are skipped, so re-running is safe.

    ADMIN_PASSWORD=... python scripts/seed_admin.py --url http://127.0.0.1:8000
"""

import argparse
import csv
import os
import random
from pathlib import Path

import requests


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--url", default="http://127.0.0.1:8000")
    ap.add_argument("--username", default="admin")
    ap.add_argument("--images", default="data/images")
    ap.add_argument("--species", default=str(Path(__file__).resolve().parents[1] / "species" / "california_100.csv"))
    args = ap.parse_args()
    password = os.environ["ADMIN_PASSWORD"]
    u = args.url
    r = requests.post(f"{u}/auth/register", json={"email": f"{args.username}@example.com",
                                                  "username": args.username, "password": password})
    if r.status_code == 409:
        r = requests.post(f"{u}/auth/login", data={"username": args.username, "password": password})
    r.raise_for_status()
    h = {"Authorization": f"Bearer {r.json()['access_token']}"}
    requests.patch(f"{u}/me/settings", json={"show_in_feed": False, "is_private": True}, headers=h).raise_for_status()
    # New accounts start as friends with the example bots, and friends see
    # private photos; this account should be visible to nobody else.
    for f in requests.get(f"{u}/friends", headers=h).json()["friends"]:
        if f.get("is_bot"):
            requests.delete(f"{u}/friends/{f['username']}", headers=h)

    have = {p["species"]["slug"] for p in requests.get(f"{u}/me/album", headers=h).json()["photos"]}
    rng = random.Random(1)
    missing = []
    for row in csv.DictReader(open(args.species, encoding="utf-8")):
        slug = row["slug"]
        if slug in have:
            continue
        photos = sorted((Path(args.images) / slug).glob("*.jpg"))
        done = False
        for photo in rng.sample(photos, min(8, len(photos))):
            with open(photo, "rb") as fh:
                c = requests.post(f"{u}/captures", headers=h,
                                  files={"photo": (photo.name, fh, "image/jpeg")}).json()
            if c.get("matched") and c["species"]["slug"] == slug:
                done = True
            elif slug in [x["slug"] for x in c.get("choices", [])]:
                p = requests.post(f"{u}/captures/{c['capture_id']}/pick", headers=h, json={"label": slug})
                done = p.ok and p.json().get("matched")
            elif c.get("matched"):
                # Wrong animal and the right one isn't offered: undo it, try another photo.
                requests.post(f"{u}/captures/{c['capture_id']}/pick", headers=h, json={"label": "none"})
            if done:
                print(f"captured {slug}")
                break
        if not done:
            missing.append(slug)
    total = requests.get(f"{u}/me/collection", headers=h).json()
    print(f"{args.username}: {total['caught']}/{total['total']} captured"
          + (f"; couldn't get {', '.join(missing)}" if missing else ""))


if __name__ == "__main__":
    main()
