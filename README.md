# CollectAnimals

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
- `ml/` — dataset download from iNaturalist, fine-tuning, and a predict CLI
- `backend/` — FastAPI app: accounts, photo captures, badges, collection, and a minimal web page
- `android/` — offline Android app: runs the model on the phone, badges stored on the device

## Run the backend

```bash
pip install -r backend/requirements.txt
cd backend && uvicorn app.main:app --reload
# open http://127.0.0.1:8000
```

Without a trained model the API still runs; captures report that no model is loaded.

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
