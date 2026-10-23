# Capture Animals: handover for a new agent

Read this first, then `README.md` (setup, API behaviour, Android build). Where
they disagree, this file is newer: the README's "Current model" section and
its "CA and NC only" intro predate the all-states work. Written 2026-10-19
against `main` at b03a48d.

## 1. What the product is

A real-world creature collection game. Players photograph wild animals; a
classifier names the species, and if it's on the player's state list they
earn its badge in their **Field Guide**. Each of the 50 US states has its own
list of ~100 animals (~930 distinct species overall), each with a 40×40
pixel-art sprite that lives in an animated **habitat** scene.

Around that core: photo scores (1–5 stars), field notes / bonds per animal,
sets and weekly challenges, friends and their Field Guides, galleries with
likes and comments, a news feed, parks ("hotspots") maps, live weather and
seasons in the habitat, states unlocked by where your photos were taken.

- Owner: **kuro** (GitHub `kurosatto`). Solo hobby project that may be
  monetized later. Kid-friendly audience.
- Name in the app: **Capture Animals**. Repo name stays `CollectAnimals`.
- Release version: `release.json` (0.10.0). Android package
  `com.captureanimals.app`, US-only release planned.

## 2. Repository map

| Path | What's there |
|---|---|
| `backend/app/main.py` | FastAPI app: auth, states, species/dex, captures (upload → identify → badge), collection, sets, challenges, bonds, weather, app version, static files |
| `backend/app/social.py` | Albums, galleries, likes, comments, feed, friends, profiles, `/media` |
| `backend/app/notices.py` | Web Push (own RFC 8291 + VAPID implementation) and `/me/activity` polling |
| `backend/app/classifier.py` | Loads the torch checkpoint lazily; API and tests run without torch |
| `backend/app/{scoring,bonds,goals,places,states,weather,household,limits,storage}.py` | Photo scores, field notes, sets/challenges, location blurring and place names, state lookup, api.weather.gov, pets-and-pests, rate limits, photo storage |
| `backend/app/config.py` | Every setting, read from env vars (see §5) |
| `backend/app/static/index.html` | The whole web client (~2.3k lines, vanilla JS, no build step) |
| `backend/app/static/habitat.js` | Habitat engine (scenes per state, perches, motion, weather, seasons). **Shared with Android** |
| `backend/app/static/sw.js`, `manifest.webmanifest`, `icons/` | PWA (install, offline Field Guide) |
| `backend/tests/` | pytest, ~105 tests, ~2 min |
| `android/` | Kotlin + Jetpack Compose app. Runs the ONNX model on the phone offline; talks to the server when signed in |
| `android/app/src/main/assets/{habitat,parks}.html` | WebView wrappers around `habitat.js` and the Leaflet parks map |
| `ml/` | `fetch_inat.py` (iNaturalist photos), `train.py`, `predict.py`, `export_onnx.py` (Android), `build_ranges/hotspots/seasons/states.py` (map data) |
| `species/states.json` | The 50 states: code, name, species CSV, optional outline/ranges/hotspots/places/seasons/dex, bounds, grid, `utc_offset`, `inat_place_id` |
| `species/<state>_100.csv`, `details.csv`, `<state>_dex.csv` | Lists (slug, names, category, rarity), shared facts and safety columns, per-state text |
| `species/household.csv` | Pets and pests (dog, cat, rats...): recognized by name only, no badge |
| `species/sets.json`, `events.json` | Sets/challenges data |
| `species/sprites/` | Generated sprites, silhouettes, `anim/` frame sheets, `placeholder*.png` ("?" egg) |
| `tools/` | Sprite drawing in code: `pixel.py` (canvas), `archetypes.py` (body plans), `make_sprites.py`, `species_<st>.py` per state; tab and PWA icon makers |
| `scripts/` | `seed_demo.py` (bot friends), `seed_admin.py`, `publish_server_url.py` (tells the app the new tunnel URL) |
| `.github/workflows/tests.yml` | CI: backend pytest + Android unit tests, debug APK, unsigned release bundle, 16 KB page-alignment check |

## 3. How it all runs today

**Everything runs on kuro's Windows laptop** (RTX 4080 Laptop, 12 GB VRAM).
kuro: "use my pc until we scale" and won't pay for hosting until real people
use it.

- **Demo server**: a separate worktree `C:\Users\mesta\Desktop\AnimalCollect-demo`
  with its own `demo.db` and uploads, `PUBLIC=1`, on 127.0.0.1:8000, exposed
  with a Cloudflare **quick tunnel** (random `*.trycloudflare.com` URL that
  changes on every restart). After a restart, `scripts/publish_server_url.py`
  writes `server.json` to the **`server-url` branch**, which the Android app
  reads to find the server. Never delete that branch.
- **APKs**: built on the PC, copied to `ANDROID_APK_DIR=D:\CaptureAnimals` as
  `CaptureAnimals-<version>.apk`, downloadable from `<demo>/app/android/`.
- **Training and data downloads** also run on the PC.
- The PC is reached through a **Remote Control** Claude session (project thread
  "Better animal identification", folder `~\Desktop\AnimalCollect`). It often
  sleeps, goes offline or hits usage limits; PC work waits until it's back.
- **C: is nearly full.** Put datasets, caches, models and backups on **D:**
  (kuro: "you can use the other drive"). Back up `demo.db` to D: before any
  demo update.
- **Keep PC load light.** kuro killed jobs once because the laptop lagged. Run
  downloads/training at low priority and ask before a big retrain.

**Moving off the PC (planned, $0):** `deploy/server/` sets the server up on an Oracle
Cloud Always Free VM with a fixed DuckDNS address and Caddy HTTPS; see its README for
the sign-ups only kuro can do. kuro (2026-10-23): no spending until 100+ daily players.

Updating the demo after a merge: back up `demo.db` → pull `main` in the demo
worktree → restart server + tunnel → `publish_server_url.py` → rebuild the APK
if Android changed → post the new link. Cloud threads can't message the PC
thread directly; they tell the project coordinator, which relays.

## 4. The identification model

- Shipping: `convnext_nano.in12k_ft_in1k` (timm, Apache-2.0), **last stage
  fine-tuned** plus a ~925-class head: every state's species + pets/pests +
  `other`. Trained on small-size iNaturalist photos.
- Accuracy (2026-10-18): 77.7% top-1 overall; on CA/NC 74% correct badges vs
  88% for the older CA/NC-only model (kept on the PC as a backup). kuro chose
  to ship the all-states model.
- At ID time the backend drops classes outside the player's state and
  rescales; a capture counts above `MATCH_THRESHOLD`. If the top guess is
  wrong the player can pick from the top 5 ("Not this animal?").
- Android runs the same model as ONNX float32 (~60 MB; int8 changed 11% of
  answers so it isn't used).
- `ml/train.py` on `main` trains the **head only** on a frozen backbone (the
  original recipe). The last-stage fine-tune that produced the shipping model
  was run on the PC; its script may not be on `main` (inferred from `main`'s
  `train.py`). Check the PC checkout before retraining.
- The cloud sandbox can't reach `api.inaturalist.org`, `huggingface.co` or
  `dl.google.com`, so downloads, pretrained weights, training and Android
  builds happen on the PC; CI is the Android compile check from the cloud.
- **Pets not recognized yet**: the iNat pet download got throttled; it resumes
  on the PC into `D:\data\household`, then retrain.
- **List size**: kuro (2026-10-19): keep 100 per state for now; target ~200 at
  some future retrain, but it isn't a priority. Small gap fixes (e.g. CA
  missing Double-crested Cormorant and Wild Turkey) are fine.
- Ideas if accuracy needs work: full end-to-end fine-tune, or a bigger
  backbone server-side. BioCLIP-family models scored higher but are
  research-licensed or likely trained on iNat, so can't ship.

## 5. Running and testing locally

```bash
pip install -r backend/requirements.txt pytest httpx
cd backend && python -m pytest -q          # 104 passed, 1 skipped on 2026-10-19
uvicorn app.main:app --reload              # http://127.0.0.1:8000, works without a model
```

Useful env vars (`backend/app/config.py`): `MODEL_PATH` (default
`models/ca100.pt`), `MATCH_THRESHOLD`, `DATABASE_URL` (SQLite by default),
`UPLOAD_DIR`, `STORAGE_BACKEND`, `PUBLIC=1` (hides docs and error details),
`ANDROID_APK_DIR`, `SCORE_OLD_PHOTOS=0`, `SECRET_KEY` (else generated once in
`backend/.secret_key`). The Web Push key lives in `backend/.vapid_private.pem`;
losing it breaks every push subscription.

Web previews: `?weather=rain,windy` and `?season=winter` force the habitat's
weather and season.

## 6. Conventions and design rules

**Wording**
- Players **capture** animals ("captured", "Not captured yet"), never
  catch/caught in UI text. API paths and field names keep their old names
  (`caught`, `/captures` etc.).
- The collection is the **Field Guide**. No "Dex", "Pokédex", "Pokémon",
  "Pokémon Snap" or other trademarks anywhere a player can see.
- Never show "Watch from far away with zoom, and stay with an adult." (kuro
  had it removed everywhere.) No "maybe out" / "out of season" wording.

**Code**
- Change habitat and map behaviour in `habitat.js` and the web first;
  Android packages `backend/app/static` and `species/` as assets, so it picks
  them up on its next build. Keep web and Android at feature parity.
- A new species needs a drawing function in `tools/species_<st>.py` (else it
  shows the "?" egg). A state's habitat should feature a **signature landmark**
  for that state (TX mesas and windmill, FL mangroves and a launch pad, NY
  Statue of Liberty, VA Assateague lighthouse and ponies), one state at a
  time, biggest first.
- New offline-capable game-data endpoints go in `isGameData` in `sw.js`.
  Photos, feeds and POSTs are never cached.
- Map tiles: USGS National Map topo only (public domain). Never OpenStreetMap
  tiles (their usage policy forbids this).
- Bump `release.json` only when kuro asks (major updates).

**Safety and privacy (kid-friendly)**
- Danger/caution animals (`safety` column in `details.csv`) get full framing
  in photo scores and no field notes or quests that push close-ups, night
  visits or revisits. No exact locations for danger/protected species.
- Locations others see are blurred: ~10 km for common animals, park/town only
  for rare, region only for legendary. Friends get ~100 m.
- Photo scores never depend on time or place (players can edit those).

**Licensing (the game may be monetized)**
- Experiments can use anything. What **ships** must be commercially licensed:
  model weights, their pretraining data, and training photos. ~91% of the
  iNaturalist photos are CC-BY-NC, so the current model is **not** cleared to
  ship commercially; the plan is to retrain on CC0/CC-BY photos only with a
  license manifest.
- Sprites are original (drawn in code), CC0.
- Player uploads will need clear terms: consent for display and training
  (training opt-in, off by default), retention, deletion, location privacy.

## 7. Working with kuro

- **Work autonomously.** kuro checks in rarely. Pick sensible defaults, do the
  reversible work (branches, PRs, scratch analysis), and report results with
  what you decided. Don't park work on questions.
- **Merging**: open a PR and wait. kuro approves with "merge" (or "merge all
  the changes"); then merge it. Don't merge without that word.
- Don't do irreversible or outward-facing things without asking: deleting
  data or branches, spending money, creating cloud accounts, publishing.
- Reply in short, plain language with screenshots when UI changes. Shared
  screenshots and notes live in the project's files folder.
- **Features kuro rejected; don't re-propose**: seasonal events that need
  upkeep, weekly outing-day goals or streaks, keeping every photo per animal,
  card duels, "first in state" badges, the buddy system (removed in #65),
  typed species search in "None of these" (removed in #47). kuro prefers features that **run
  themselves** and **cost little storage**.
- Hosting: stay on the PC ($0) until there are users. If moving, the
  recommendation on record is FastAPI on a cheap host + Postgres + Cloudflare
  R2 (via `storage.py`), optionally Firebase Auth only. Not a full Firebase
  rewrite.

## 8. State of play (2026-10-19)

**Recently merged**: all 50 states (data #64 + `all-states-data`), state art
for TX, FL, NY, VA, weather and seasons in the habitat, local weather, unlock
states by photo location (#80), photo crop before identify (#81), security
hardening (#68: login limits, image size cap, headers).

**Open / in flight**
- PR #82: show an error instead of endless "Identifying…" when the server is
  offline. Awaiting "merge".
- Project threads working now: fun facts when tapping animals in the habitat,
  4-across "My photos" grid, random nature-lover avatars on the friends list;
  removing a leftover buddy mention.
- PC: sighting maps/seasons for the remaining states (GBIF), pet photo
  download, then retrain with pets. The demo still runs pre-50-state code
  until the PC thread updates it.

**Known gaps / likely next work**
- 577 new-state animals have no sprite yet (show the "?" egg); art goes one
  state at a time.
- Sighting maps (ranges/hotspots) exist for only some states.
- No account deletion (required by Google Play), no password reset, 7-day
  JWTs can't be revoked, no backups beyond manual copies to D:.
- Play Store: needs release signing set up on the PC, a closed test with 12+
  testers for 14 days, and a commercially licensed model.
- The quick-tunnel URL changes on every restart, which breaks installed PWAs;
  a named tunnel on a custom domain (~$10/yr via Cloudflare) fixes it, but
  kuro postponed that.

## 9. Gotchas

- GitHub's **default branch is `claude/ecstatic-noether-82qfta`** (the initial
  scaffold), not `main`. A plain `git clone` checks out that stale branch.
  Always work from and target **`main`**.
- Several Claude threads work in parallel. The PC thread sometimes builds the
  same feature on its own branch; compare and keep the fuller one.
- The cloud sandbox can't delete remote branches (the git proxy blocks ref
  deletes); the PC session can.
- Android can't be compiled in the cloud. Push and let CI build it.
- The Android photo picker strips GPS, so gallery picks usually have no place
  unless the player sets one.
- Deleting your album photo un-catches the animal (badge, captures and files
  go). Intentional.
- `restar_scores()` and `score_old_photos()` run at startup and touch the DB.
