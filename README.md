# CollectAnimals

A real-world animal collecting game, "Pokémon, but the animals are real." You photograph animals around
you, a vision model identifies them, and each new species unlocks a badge in your collection.

The first region is **California, with 100 species**. More regions and species come later.

```
species/california_100.csv   the 100 collectible species (slug, names, category, rarity)
ml/fetch_inat.py             download training photos from iNaturalist (CA, research grade, open licenses)
ml/train.py                  fine-tune an ImageNet-pretrained backbone (timm) → models/ca100.pt
ml/predict.py                classify local images with a checkpoint
backend/app/                 FastAPI app: auth, species, photo capture → classify → badge, collection
backend/app/static/          minimal web UI (log in, upload a photo, see your collection)
backend/tests/               API tests (use a fake classifier; no torch needed)
```

## How it works

1. **Species list.** `species/california_100.csv` holds 25 mammals, 35 birds, 12 reptiles, 6 amphibians,
   14 insects and other invertebrates, and 8 tidepool/marine species. Each has a game rarity
   (`common` 50, `uncommon` 27, `rare` 18, `legendary` 5). The list favors animals people can actually
   find, with enough iNaturalist photos to train on. Edit the CSV freely: the backend re-syncs it at
   startup.
2. **Data.** `fetch_inat.py` resolves each scientific name to an iNaturalist taxon. It then downloads
   up to N photos per species from research-grade California observations, using only
   CC0/CC-BY/CC-BY-NC photos and one photo per observation. It also builds an **`other` class** from
   CA animal observations *not* in the list. Without that class, a 100-way classifier would force a
   pigeon or a pet dog into one of the 100 species. Photo credits go to `data/images/attribution.csv`,
   which the licenses require you to keep.
3. **Model.** `train.py` fine-tunes any timm model. The default is
   `convnext_tiny.fb_in22k_ft_in1k`, pretrained on ImageNet. The backbone trains at a lower learning
   rate than the new head. Training uses class-balanced loss and label smoothing, and the script saves
   the checkpoint with the best validation score plus per-class accuracy
   (`models/ca100.metrics.json`).
4. **Game logic.** The upload flow is `POST /captures` → classifier top-3. A capture **matches** when
   the top label is one of the 100 species *and* its confidence is ≥ `MATCH_THRESHOLD` (default 0.6).
   The first match for a species awards a badge, and later matches increment its count. Every upload
   is stored as a `Capture`, matched or not. These are useful later as new training data and for
   tuning the threshold.

## Quickstart

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r backend/requirements.txt -r ml/requirements.txt

# 1. Data. Start small to try the pipeline, then scale up.
#    This is roughly 1 API call/sec: ~100 species × 1000 photos takes a few hours.
python ml/fetch_inat.py --per-species 200 --negatives 2000
#    (later) python ml/fetch_inat.py --per-species 1000 --negatives 10000   # resumes, skips existing files

# 2. Train. A GPU is strongly recommended; for a CPU/Mac test run, use efficientnet_b0 with a few epochs.
python ml/train.py --data data/images --out models/ca100.pt
python ml/predict.py models/ca100.pt some_photo.jpg

# 3. Run the app.
cd backend && SECRET_KEY=$(openssl rand -hex 32) uvicorn app.main:app --reload
# open http://localhost:8000  (API docs at /docs)

# Tests
cd backend && pytest
```

Configuration is set through environment variables; see `backend/app/config.py`. The main ones are
`DATABASE_URL` (default: SQLite), `SECRET_KEY`, `MODEL_PATH`, `MATCH_THRESHOLD` and `UPLOAD_DIR`.

## API

| Method | Path | Notes |
|---|---|---|
| POST | `/auth/register` | `{email, username, password}` → bearer token |
| POST | `/auth/login` | form `username` (email or username) + `password` → bearer token |
| GET | `/me` | current user |
| GET | `/species`, `/species/{slug}` | the collectible species |
| POST | `/captures` | multipart `photo` → `{matched, species, confidence, new_badge, message, top_predictions}` |
| GET | `/me/collection` | all species, with `caught`, `capture_count` and `earned_at` |
| GET | `/health` | whether the model is loaded |

## Roadmap ideas

- **Better backbone.** ImageNet works, but backbones pretrained on iNaturalist or nature imagery
  (e.g. BioCLIP, or timm's `*_inat21` weights) are much stronger for fine-grained species ID. They
  are worth trying once the pipeline is running.
- **More negatives.** Add plants, people, pets, and empty landscapes to `other`, and calibrate
  `MATCH_THRESHOLD` on held-out data.
- **Anti-cheat.** Require camera capture or recent EXIF time and location, and reject screenshots
  and duplicate images (perceptual hash). Location could also unlock region-specific collections.
  Note: uploads are currently re-encoded, which strips EXIF, so read it before re-encoding if you
  want to use it.
- **Data flywheel.** Send low-confidence captures to a review queue, and add confirmed ones to the
  training set.
- **Regions.** Add a `region` column to the CSV (the DB already has one) and per-region collections.
- **Mobile app.** Build a React Native or Flutter client on the same API, possibly with an on-device
  model export (ONNX / Core ML).
- **Production.** Postgres, object storage for uploads, Alembic migrations, and rate limiting.
