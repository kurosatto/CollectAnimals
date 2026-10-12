# CollectAnimals

A Pokémon-style game for real wildlife: photograph animals around you, and if
the model recognizes one of the species on the list, you earn its badge.
Starting with 100 California species (`species/california_100.csv`).

## Layout

- `species/` — the species list (slug, names, category, rarity) and `sprites/`, a 32×32
  pixel-art sprite and silhouette per species (drawn by `tools/make_sprites.py`; a new
  species needs a drawing added there, then rerun it)
- `ml/` — dataset download from iNaturalist, fine-tuning, and a predict CLI
- `backend/` — FastAPI app: accounts, photo captures, badges, collection, friends, photo albums and galleries, and a minimal web page
- `android/` — offline Android app: runs the model on the phone, badges stored on the device

## Run the backend

```bash
pip install -r backend/requirements.txt
cd backend && uvicorn app.main:app --reload
# open http://127.0.0.1:8000
```

Without a trained model the API still runs; captures report that no model is loaded.

## Friends, albums and the gallery

- **Hidden names.** A species shows as "???" (with its category, rarity, size,
  weight and sighting map as hints) until you or one of your friends has
  caught it. The fun fact unlocks only with your own catch.
- **Album.** Each player keeps one photo per species, with where and when it
  was taken. The first matching capture goes in automatically; a later one can
  replace it (`PUT /me/album/{species}`), which resets that photo's likes.
  Location comes from the phone (the web page asks for it; "Save where I
  caught it" can be unticked) or the photo's EXIF GPS. Saved files have EXIF
  stripped.
- **Friends.** Send a request by username; when accepted you see each other's
  albums and each other's catches unlock names for you.
- **Gallery.** `GET /species/{species}/photos?scope=all|friends&sort=top|new`
  lists everyone's album photos for a species, ranked by likes. You need the
  species unlocked to see it. Photos that never made it into an album are
  never served.
- **Deleting.** "Delete photo" on your own photo (`DELETE /photos/{id}` or
  `DELETE /me/album/{species}`) removes it from your album, the gallery and
  the feed, drops its likes and deletes the file. You keep the badge, and
  your next catch of that animal becomes the new album photo.
- **News feed.** `GET /feed?scope=near|friends|all` lists the newest catches
  with the place and time. The page defaults to "Near me" (`lat`, `lon`,
  `radius_km`, 50 km by default, 10 km minimum) and falls back to all of
  California without location permission. Distances use each catch's blurred
  position (a ~10 km grid, ~50 km for rare and legendary animals), so the
  radius can't be used to pinpoint anyone.
  `uncaught=true` ("Only animals I haven't caught") hides species you already have. Animals you haven't unlocked show as "a mystery
  mammal" with no photo. Players can turn off "Show my catches in this feed"
  (`PATCH /me/settings`).
- **Locations others see** (`backend/app/places.py`): a hotspot park name,
  "near <town>" (`species/ca_places.json`) or a region, never exact GPS.
  Common and uncommon animals also get coordinates rounded to about 10 km
  (about 100 m for friends). Rare animals get only a park or "around <town>",
  and legendary ones only a region, for everyone but you.
- **Hidden tips.** While a species is hidden its where-to-find and spotting
  tips are held back (some name the animal); active time, hotspot parks, size,
  weight and the map stay visible as hints.

## Storage and hosting

Right now everything is free and local: SQLite (`backend/collectanimals.db`)
and photo files in `backend/uploads/`. Photo access goes through
`backend/app/storage.py`, so moving photos to a cloud bucket later means one
new class there (`STORAGE_BACKEND`), and `DATABASE_URL` can point at Postgres.
Saved photos are at most 1600 px JPEG, roughly 200–400 KB each, so 10,000
album photos is about 3 GB.

Options for when it goes online (rough prices; check before choosing):

| Setup | Rough cost | Notes |
|---|---|---|
| One small VPS (Hetzner, DigitalOcean, Lightsail) running this app with SQLite + disk | ~$4–6/month | Simplest. Back up the disk. Fine for the first thousands of players. |
| Free tiers (Render, Fly.io, Railway) | $0 to a few $/month | Many sleep when idle or wipe local disk, so photos need object storage. |
| Photos in object storage | Cloudflare R2: 10 GB free, then ~$0.015/GB-month, no download fees. AWS S3: ~$0.023/GB-month plus download fees. Backblaze B2: ~$0.006/GB-month | R2 is the cheapest for a photo gallery because people view photos far more than they upload them. |
| Managed Postgres (Neon, Supabase) | Free tier, then ~$19–25/month | Only needed once one server isn't enough. |

No paid service is needed until the app is public.

## Build the model

```bash
pip install -r ml/requirements.txt
python ml/fetch_inat.py --per-species 1000 --negatives 5000 --out data/images
python ml/train.py --data data/images --out models/ca100.pt   # frozen backbone, trains the head only
python ml/predict.py models/ca100.pt some_photo.jpg
```

The backend loads `models/ca100.pt` by default (override with `MODEL_PATH`).
A capture only counts above `MATCH_THRESHOLD` (default 0.7; see the table below).

## Current model

Frozen `convnext_nano.in12k_ft_in1k` backbone with a trained linear head (v2,
2026-10-12). Trained on ~110k small iNaturalist photos: 100 species with
779–1,000 each, plus ~10,000 "other" animals spread over 8 groups and 12 months.

On held-out photos: 80% top-1 on the 100 species. Weakest: bobcat, crow vs.
raven, the hawks. Animals not on the list are the hard part: they are labelled
"other" only ~25% of the time, so the confidence threshold does most of the
work of preventing wrong badges:

| Threshold | Correct badge | Wrong species | Non-list animal gets a badge |
|---|---|---|---|
| 0.5 | 68.9% | 5.0% | 22.3% |
| 0.6 | 64.4% | 2.8% | 17.7% |
| **0.7** (default) | 57.7% | 1.7% | 13.4% |
| 0.8 | 48.1% | 0.7% | 8.5% |
| 0.9 | 31.3% | 0.2% | 3.1% |

About 91% of the photos are CC-BY-NC (non-commercial only); credits are in
`data/images/attribution.csv`.

## Android app

The app runs the classifier on the phone (no server, works offline in the
field) and keeps badges on the device. Same rules as the backend: a capture
counts when the top guess is one of the 100 species at >= 0.7 confidence.

```bash
python ml/export_onnx.py models/ca100.pt          # writes android/app/src/main/assets/model.{onnx,json}
cd android && ./gradlew assembleDebug testDebugUnitTest
# APK: android/app/build/outputs/apk/debug/app-debug.apk
```

Needs JDK 17 and the Android SDK (platform 35; set `sdk.dir` in
`android/local.properties` or `ANDROID_HOME`). The APK is ~88 MB, mostly the
60 MB model; int8 quantization shrank it to 15 MB but changed the top-1
answer on 11% of photos, so it ships in float32. `PreprocessTest` checks the
Kotlin resize/crop against PIL/torchvision; `ClassifierTest` runs the real
model through it when `data/images` is present.

## Tests

```bash
cd backend && python -m pytest -q
```
