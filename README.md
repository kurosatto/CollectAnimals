# Capture Animals

A Pokémon-style game for real wildlife: photograph animals around you, and if
the model recognizes one of the species on the list, you earn its badge.
Each state has its own 100 species: California (`species/california_100.csv`)
and North Carolina (`species/north_carolina_100.csv`), listed in
`species/states.json`. Players pick a state at sign-up and can change it later;
the Dex, Hotspots and maps follow it. A species on several lists keeps one
slug, so a badge counts in every state that lists it.

## Layout

- `species/` — `states.json`, each state's species list (slug, names, category, rarity) and map
  data, the shared Dex facts (`details.csv`), and per-state Dex text (`<state>_dex.csv`)
- `species/sprites/` — a 32×32 pixel-art sprite and silhouette per species, shared by all
  states (drawn by `tools/make_sprites.py`; a new species needs a drawing added there, then rerun it)
- `HANDOVER.md` — start here if you are new to the project (current state, how it runs, conventions)
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
  Time and place come from the photo's EXIF first (the Android app reads it
  before shrinking the photo and sends it along). Without EXIF GPS, the phone's
  location is used only for recent photos; without an EXIF time, the upload
  time. Unticking "Save where I captured it" keeps no place at all. Owners can
  fix both (`PUT /captures/{id}/where-when`: no later than the upload, inside
  their state); the place name follows. Photo scores never
  depend on time or place. Saved files have EXIF stripped.
- **Friends.** Send a request by username; when accepted you see each other's
  albums and each other's catches unlock names for you.
- **Gallery.** `GET /species/{species}/photos?scope=all|friends&sort=top|new`
  lists everyone's album photos for a species, ranked by likes. You need the
  species unlocked to see it. Photos that never made it into an album are
  never served.
- **Likes and comments.** Anyone who can see a photo can like it and comment
  on it, friends or not (`POST /photos/{id}/like`, `GET|POST
  /photos/{id}/comments`). Comments are up to 300 characters, at most 5 a
  minute and 100 a day per player. The commenter and the photo's owner can
  delete a comment (`DELETE /comments/{id}`). Swapping or deleting a photo
  drops its likes and comments.
- **Private players.** `PATCH /me/settings {"is_private": true}` hides your
  photos from everyone but you and your friends: they leave the species
  galleries, the feed and your profile for strangers (strangers can't like
  or comment on them either).
- **Player pages.** `GET /users/{username}` returns a player's achievements
  (milestones, rare and legendary finds, completing a group, likes), catches
  by rarity and group, and their photos, plus whether you're friends. Friends
  see every photo; others see only animals they've unlocked themselves, with
  the usual blurred places.
- **Deleting.** "Delete photo" on your own photo (`DELETE /photos/{id}` or
  `DELETE /me/album/{species}`) removes it from your album, the gallery and
  the feed, drops its likes and deletes the file. It also un-catches the
  animal: the badge and your other captures of it are deleted, so it is
  locked again (unless a friend has caught it) until you catch it again.
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
  "near <town>" (each state's places file in `species/states.json`) or a
  region of the state the photo was taken in, never exact GPS.
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

### Adding a state

Add its CSV, `<state>_dex.csv` and an entry in `species/states.json`, then:

```bash
python ml/fetch_inat.py --states NC --size small --out data/images   # only the new species + NC "other"
python ml/build_ranges.py --state NC      # sighting maps + state outline
python ml/build_hotspots.py --state NC    # parks (add the state's parks to PARKS first)
python ml/train.py --data data/images --out models/ca_nc.pt
MODEL_PATH=models/ca_nc.pt uvicorn app.main:app   # or copy it over models/ca100.pt
```

The model has one class per species across all states; the backend only
counts the player's state (other states' classes are dropped and the rest
rescaled).

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

Needs JDK 17 and the Android SDK (platform 36; set `sdk.dir` in
`android/local.properties` or `ANDROID_HOME`). The APK is ~88 MB, mostly the
60 MB model; int8 quantization shrank it to 15 MB but changed the top-1
answer on 11% of photos, so it ships in float32. `PreprocessTest` checks the
Kotlin resize/crop against PIL/torchvision; `ClassifierTest` runs the real
model through it when `data/images` is present.

### New versions

`release.json` holds the release version for the web app and the Android app. Bump it only
for a major update; smaller changes reach the website silently on the next page load.

- Website: open pages notice the new version and show "Capture Animals X is here. Tap to update".
- Android: the next APK build takes the version from `release.json` (versionCode is
  major×10000 + minor×100 + patch). Copy it to the folder in `ANDROID_APK_DIR` as
  `CaptureAnimals-<version>.apk`; phones on an older version are offered the download from
  `/app/android/...`, once per version.

### Release build for Google Play

Play takes a signed app bundle (`.aab`). Make an upload key once and keep it
and its passwords backed up in two places outside the repo (losing it means
asking Google support to reset it):

```bash
keytool -genkeypair -v -keystore ~/capture-animals-upload.jks -alias upload \
  -keyalg RSA -keysize 2048 -validity 10000
```

Then create `android/keystore.properties` (git-ignored, never commit it):

```properties
storeFile=/full/path/to/capture-animals-upload.jks
storePassword=...
keyAlias=upload
keyPassword=...
```

```bash
cd android && ./gradlew bundleRelease
# AAB: android/app/build/outputs/bundle/release/app-release.aab
```

On CI the same values can come from `UPLOAD_STORE_FILE`, `UPLOAD_STORE_PASSWORD`,
`UPLOAD_KEY_ALIAS` and `UPLOAD_KEY_PASSWORD`. Without any of them the bundle is
built unsigned. The package name `com.captureanimals.app` is permanent once
uploaded. CI also checks that the native libraries are 16 KB page-aligned,
which Play requires.

## Tests

```bash
cd backend && python -m pytest -q
```
