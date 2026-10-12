# CollectAnimals

A Pokémon-style game for real wildlife: photograph animals around you, and if
the model recognizes one of the species on the list, you earn its badge.
Starting with 100 California species (`species/california_100.csv`).

## Layout

- `species/` — the species list (slug, names, category, rarity)
- `ml/` — dataset download from iNaturalist, fine-tuning, and a predict CLI
- `backend/` — FastAPI app: accounts, photo captures, badges, collection, and a minimal web page

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

## Tests

```bash
cd backend && python -m pytest -q
```
