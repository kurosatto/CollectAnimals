# CollectAnimals

A Pokémon-style game for real wildlife: photograph animals around you, and if
the model recognizes one of the species on the list, you earn its badge.
Starting with 100 California species (`species/california_100.csv`).

## Layout

- `species/` — the species list (slug, names, category, rarity)
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
