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
python ml/train.py --data data/images --out models/ca100.pt
python ml/predict.py models/ca100.pt some_photo.jpg
```

The backend loads `models/ca100.pt` by default (override with `MODEL_PATH`).
A capture only counts above `MATCH_THRESHOLD` (default 0.6).

## Tests

```bash
cd backend && python -m pytest -q
```
