# Capture Animals: handover for a new agent

Read this first, then `README.md` (setup, API behaviour, Android build). Where
they disagree, this file is newer. Written 2026-10-19; sections 3, 4, 7 and 8
brought up to date on 2026-11-11 (release 0.63).

## 1. What the product is

A real-world creature collection game. Players photograph wild animals; a
classifier names the species, and if it's on the player's state list they
earn its badge in their **Field Guide**. Each of the 50 US states has its own
list of ~100 animals (~930 distinct species overall), each with a 40×40
pixel-art sprite that lives in an animated **habitat** scene.

Around that core: photo scores (1–5 stars), 16 minigames with coins, a shop of
skins and habitat decorations, sets, friends and their Field Guides, galleries with
likes and comments, a news feed, parks ("hotspots") maps, live weather and
seasons in the habitat, states unlocked by where your photos were taken.

- Owner: **kuro** (GitHub `kurosatto`). Solo hobby project that may be
  monetized later. Kid-friendly audience.
- Name in the app: **Capture Animals**. Repo name stays `CollectAnimals`.
- Release version: `release.json`. Android package
  `com.captureanimals.app`, US-only release planned.

## 2. Repository map

| Path | What's there |
|---|---|
| `backend/app/main.py` | FastAPI app: auth, states, species/dex, captures (upload → identify → badge), collection, sets, challenges, weather, app version, static files |
| `backend/app/social.py` | Albums, galleries, likes, comments, feed, friends, profiles, `/media` |
| `backend/app/notices.py` | Web Push (own RFC 8291 + VAPID implementation) and `/me/activity` polling |
| `backend/app/classifier.py` | Loads the torch checkpoint lazily; API and tests run without torch |
| `backend/app/{scoring,goals,places,states,weather,household,limits,storage}.py` | Photo scores, sets/challenges, location blurring and place names, state lookup, api.weather.gov, pets-and-pests, rate limits, photo storage |
| `backend/app/config.py` | Every setting, read from env vars (see §5) |
| `backend/app/static/index.html` | The whole web client (~2.3k lines, vanilla JS, no build step) |
| `backend/app/static/habitat.js` | Habitat engine (scenes per state: per-state terrain backdrops in `habFarScene`, water kinds in `HAB_WATER_KIND`, landmarks; perches, motion, weather, seasons, real sun and moon). **Shared with Android** |
| `backend/app/static/decor.js`, `species/decor.json`, `tools/make_decor.py` | The ~100 shop decorations for your own habitat: catalog, sprites (`species/sprites/decor/`), placement (12 meadow spots, pond, beach, sea, sky) and the animal visits (perch, hide, ride, slide...). Admin accounts own every shop item |
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
| `tools/` | Sprite drawing in code: `pixel.py` (canvas), `archetypes.py` (body plans), `make_sprites.py`, `species_<st>.py` per state; tab icons (`make_tab_icons.py`) and the app logo, Anna's Hummingbird, at every size (`make_app_icons.py`) |
| `scripts/` | `seed_demo.py` (bot friends), `seed_admin.py`, `publish_server_url.py` (tells the app the new tunnel URL) |
| `.github/workflows/tests.yml` | CI: backend pytest + Android unit tests, debug APK, unsigned release bundle, 16 KB page-alignment check |

## 3. How it all runs today

- **Game server**: an Oracle Cloud Always Free VM (Ampere ARM, no GPU, Ubuntu 24.04)
  at `https://captureanimals.duckdns.org`, Caddy HTTPS. Setup and operations:
  `deploy/server/README.md`. Nightly server backups; kuro's PC copies them to
  `D:\AnimalCollect\releases\server-backups`. The APK is served from the server.
- **kuro's Windows PC** (RTX 4080 Laptop, 12 GB) does what the cloud sandbox can't:
  iNaturalist/Hugging Face downloads, training, Android builds (APK + signed AAB),
  and deploying to the server. It's reached through the Remote Control thread
  "Better animal identification". It often sleeps or goes offline; PC work waits.
- **Keep PC load light** (kuro killed jobs over lag): lowest priority; on "pause"
  stop GPU jobs completely, restart on "resume". C: is nearly full: everything lives
  under `D:\AnimalCollect`.
- **Release flow**: a cloud thread merges to `main`, the coordinator relays it to the
  PC thread, which redeploys the server and publishes the APK/AAB. Play Store uploads
  use the newest `D:\AnimalCollect\releases\CaptureAnimals-<version>.aab`; the
  upload key never goes in the repo.

## 4. The identification model

- **Server (live since 2026-11-03)**: v7, `convnext_base.fb_in22k_ft_in1k` (MIT),
  val top-1 83.0%, ~80% correct badges. v6 is kept on the server as a one-minute
  fallback. Swapping the server model needs kuro's own OK in the PC thread.
- **Phone (offline)**: v6, `convnext_nano.in12k_ft_in1k` (Apache-2.0), last stage
  fine-tuned (`ml/finetune.py`), 1,696 classes (200 per state + pets/pests + human),
  ONNX float32. `species/model_extras.json` lists model-only animals that answer
  "coming soon" with no badge.
- At ID time the backend drops classes outside the photo's state and rescales; a
  capture counts above `MATCH_THRESHOLD`. "Not this animal?" offers the top 5.
- **Licensing**: ~91% of iNaturalist photos are CC-BY-NC, so the shipped model isn't
  cleared for commercial use. A commercial-photos-only model exists (badges 74% -> 52%);
  kuro keeps it as an option, not shipped.
- The cloud sandbox can't reach `api.inaturalist.org` or `huggingface.co`: model work
  goes through the PC.

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

Web previews: `?weather=rain,windy`, `?season=winter` and
`?at=2026-10-26T05:00:00Z` force the habitat's weather, season and sky time.

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
- **Look (0.37.0, phone fit)**: Field Journal colours and leather bars, but no italic
  or handwritten fonts: Pixelify Sans (headings, buttons, labels) + Space Grotesk (text),
  both OFL, in `static/vendor/fonts` and `res/font`. The habitat is the first thing on the
  Habitat tab, edge to edge on phones, with no photo frame or tape. One-line top bar.
  **No generic emojis in the UI**: use the 16 px pixel icons from `tools/make_ui_icons.py`
  (`ui_ic_<name>.png`: pin, coin, shop, lock, bell, sun, moon, warn, chat, trophy, palette,
  sound, logout) via `ico()`/`icoText()` (web), `mgIco()` (minigames.js), `IconText` (Android).
  Check layouts at 360 px wide.
- Change habitat and map behaviour in `habitat.js` and the web first;
  Android packages `backend/app/static` and `species/` as assets, so it picks
  them up on its next build. Keep web and Android at feature parity.
- Sprites have 12 frames per pose (`pixel.FRAMES`); body plans animate from `s.t`
  (0..1) via `s.wave()` / `s.cyc(...)`, and still poses breathe, blink and swish
  tails. They stay at the original 1:1 pixels (`pixel.SS = 1`): kuro tried 2x
  (0.35.0 preview) and preferred the old look. The apps always draw an animal 40
  units square (`HAB_UNIT`) and pick frames with `habCyc()` / `habIdleFrame()`.
- Sheet rows are `pixel.ACTS` (idle, walk, fly, swim, sleep, sit, look, back, eat,
  dive, hide, run, groom); append new rows at the end so the apps' row indices stay
  valid. `run` is the gallop / bound (habitat: fleeing or chasing; Trail Run) and
  `groom` the animal's own idle behaviour (dog scratches, cat/squirrel washes, bird
  and duck preen, lizard push-ups, frog calls, snake raises its head).
- 0.47.0 remake: four-legged mammals are `tools/mammal.py` (`quad`): a skeleton per
  build with two-bone legs placed by inverse kinematics from the gait, chest/barrel/
  haunch torso, detailed head, every pose drawn (no warp, breathing swells the chest).
  `lizard`, `turtle` and `fish` were redrawn too. Species that paint markings in the
  old fixed coordinates are carried along: these body plans set a translation
  (`s.fwd`/`s.xs`/`s.ys`) after drawing so later species calls follow the head.
  `eat` is grazing (quad, critter) or pecking (bird, wader, gull, raptor), also
  used for drinking. `dive` (plunge divers, leaping dolphins and whales) is drawn
  pitched from 55 degrees nose up to 75 nose down (`make_sprites.DIVE_DEG`,
  `habPitchFrame()`), `hide` is reef animals and jellies pulling in.
- kuro doesn't want pictures stretched, squashed or turned to fake motion: every
  movement in the habitat is a drawn frame. Bends of a whole drawing are done in
  the sprite generator (`Sprite.pitch` / `Sprite.bend`), drawn pixel by pixel.
  Birds of prey use the `raptor()` body plan.
- A big collection takes turns in the habitat (0.51): up to 32 animals out on a phone
  (44 on wide screens), a new mix every 20 minutes (`habOutNow`, `HAB_ROOM`).
- Habitat interactions live in habitat.js (`habReact` on tap, `habSocial` for
  animals noticing each other, `habTimers`): bolting, looking at you (`?`),
  swooping, pulling in, drinking at the pond, pecking, singing, freezing under a
  hawk, play chase, gulls following a pelican's fish.
- A new species needs a drawing function in `tools/species_<st>.py` (else it
  shows the "?" egg). A state's habitat should feature a **signature landmark**
  for that state (TX mesas and windmill, FL mangroves and a launch pad, NY
  Statue of Liberty, VA Assateague lighthouse and ponies), one state at a
  time, biggest first.
- New offline-capable game-data endpoints go in `isGameData` in `sw.js`.
  Photos, feeds and POSTs are never cached.
- Map tiles: USGS National Map topo only (public domain). Never OpenStreetMap
  tiles (their usage policy forbids this).
- Field Guide sighting maps sit on a drawn atlas plate per state,
  `backend/app/static/maps/<CODE>.webp`, made by `tools/make_state_maps.py`
  (Natural Earth 1:10m + AWS Terrain Tiles relief, both free for commercial use).
  The same script rewrites `species/<state>_outline.json` (Great Lakes cut out)
  with the `frame` the image covers; web and Android place sightings with it.
- Each release that merges bumps `release.json` (minor version) and `VERSION` in `sw.js`
  (plus `ASSETS` when sprites change), so phones pick up the update.

**Safety and privacy (kid-friendly)**
- Danger/caution animals (`safety` column in `details.csv`) get full framing
  in photo scores and no quests that push close-ups, night
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
- **Merging** (kuro, 2026-10-31): "from now on just merge things, don't ask me."
  Merge your own PRs and version bumps once CI is green, then say which release
  merged so the PC thread deploys it. Still show previews before building a big
  batch of new content (kuro picks), and server model swaps need kuro's OK.
- Don't do irreversible or outward-facing things without asking: deleting
  data or branches, spending money, creating cloud accounts, publishing.
- Reply in short, plain language with screenshots when UI changes. Shared
  screenshots and notes live in the project's files folder.
- **Features kuro rejected; don't re-propose**: seasonal events that need
  upkeep, weekly outing-day goals or streaks, keeping every photo per animal,
  card duels, "first in state" badges, the buddy system (removed in #65),
  typed species search that *awards a badge* in "None of these" (removed in
  #47). Typed naming came back on 2026-10-29 as **training labels only**
  (see "What was it?" below). kuro prefers features that **run
  themselves** and **cost little storage**.
- Hosting: stay on the PC ($0) until there are users. If moving, the
  recommendation on record is FastAPI on a cheap host + Postgres + Cloudflare
  R2 (via `storage.py`), optionally Firebase Auth only. Not a full Firebase
  rewrite.

## 8. State of play (2026-11-11)

- Release 0.63.0 (whole-game review rounds 1-15, 0.49-0.63). Recent work: Field Journal look (0.34), phone fit
  and pixel icons instead of emojis (0.37), all animals redrawn with drawn-frame
  animations at 40 px (0.38-0.47), per-state painted habitat scenery (0.43-0.48),
  one long hard level per minigame with `tools/levelcheck` (0.46; check.js per game, leap.js for Branch Leap, claw.js for Claw Catch).
  Practice mode (0.55): a "Practice" button per game; flags every 2 s, a bump goes back to one at least 1.5 s earlier; no points, coins or bests (mgFlag/mgBackToFlag in minigames.js).
- Review rounds 1-9 (0.49-0.57), in short: phone layout fixes, a/an grammar
  (`app/words.py`), plain-word validation errors (`friendly_error`, no input echo),
  account privacy switches, habitat turn-taking, Field Guide order and "First
  captured" date, policy pages in the Field Journal look (privacy policy now names
  Oracle Cloud), photos under 32 px refused, Practice mode, `mgToast` instead of
  `alert()` in shared JS (alert() does nothing in the Android WebView), and the
  app's WebView pages (assets/*.html) in Field Journal colours and fonts.
- Google Play: developer account verified; listing doc and reviewer account exist;
  closed test needs 12+ testers for 14 days.
- **kuro's taste** (keep to it): kid-friendly; realistic field-guide pixel art,
  animals in profile, no stretched/squashed/rotated sprites; no generic emojis;
  Geometry-Dash-hard minigames; features that run themselves with little storage.
  Rejected: seasonal events, weekly streaks/challenges, card duels, buddy system,
  "first in state" badges, keeping every photo per animal, colour variants on main pages.
- Android 0.34+ hasn't been checked on a real phone; check layouts at 360 px.
- Testing the web app without the model: run the backend with a fake classifier
  (see `backend/tests/test_api.py` `FakeClassifier`) and drive it with Playwright at
  360x740; that is how the review rounds found the phone layout bugs.

## 8b. "What was it?" (player labels for retraining)

After "None of these" (or a photo with nothing to pick) the player can type and
pick what the animal really was from `species/animal_names.json`: ~8,800 North
American animals plus ~55 broad groups ("Some kind of beetle", "No animal in the
photo"). It never awards a badge. Answers land in the `named_photos` table
(`label` = scientific name or `group:<id>`, plus the model's guess and state).
A 512 px training copy of the photo is kept only while the player has "Share
photos to teach the game" on (off by default); turning it off or deleting the
account deletes the copies. Android bundles the list and queues answers on the
phone (`NameQueue`) until signed in and online (`POST /me/named-photos`).
Rebuild the list with `ml/build_animal_names.py` (iNaturalist Open Dataset
counts for ranking, common names from the CC BY 4.0 common-species dataset).

## 9. Gotchas

- GitHub's **default branch is `claude/ecstatic-noether-82qfta`** (the initial
  scaffold), not `main`. A plain `git clone` checks out that stale branch.
  Always work from and target **`main`**.
- Several Claude threads work in parallel. The PC thread sometimes builds the
  same feature on its own branch; compare and keep the fuller one.
- The cloud sandbox can't delete remote branches (the git proxy blocks ref
  deletes); the PC session can.
- Android can't be compiled in the cloud. Push and let CI build it.
- The Android WebViews (Habitat.kt, Minigames.kt, ParksMap.kt) have no
  WebChromeClient: `alert()`, `confirm()` and `prompt()` silently do nothing there.
  Shared JS (habitat.js, minigames.js, decor.js) must show messages in the page.
- The Android photo picker strips GPS, so gallery picks usually have no place
  unless the player sets one.
- Deleting your album photo un-catches the animal (badge, captures and files
  go). Intentional.
- `restar_scores()` and `score_old_photos()` run at startup and touch the DB.
