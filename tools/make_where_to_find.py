"""Write each state's "Where to find it" text (species/<state>_dex.csv, where_to_find column).

Every line is the animal's habitat (species/habitats.csv, hand-written, one line per
animal, the same in every state) followed by the state's parks where it is seen most
(species/<state>_hotspots.json, iNaturalist sightings). California and North Carolina
have their own hand-written text and are skipped. Re-run after the hotspots or species
lists change:

    python tools/make_where_to_find.py
"""
import csv
import json
from pathlib import Path

SPECIES = Path(__file__).resolve().parent.parent / "species"
SKIP = {"CA", "NC"}                # hand-written text already
MIN_OBSERVATIONS = 20              # same cut as dex.MIN_HOTSPOT_OBSERVATIONS
FIELDS = ["slug", "where_to_find", "fun_fact", "active_time", "spotting_tip",
          "safety", "safe_distance", "safety_note"]


def parks_for(slug: str, parks: list[dict]) -> list[str]:
    hits = [(sp["observations"], p["name"]) for p in parks for sp in p["species"]
            if sp["slug"] == slug and sp["observations"] >= MIN_OBSERVATIONS]
    return [name for _, name in sorted(hits, reverse=True)[:2]]


def line(habitat: str, parks: list[str]) -> str:
    if not parks:
        return habitat + "."
    if len(parks) == 1:
        tail = f"{parks[0]} is a good bet."
    elif any(" and " in p for p in parks):
        # "Central Park and Heart Lake and Adirondack Loj" would read as three places.
        tail = f"{parks[0]} is a good bet, and so is {parks[1]}."
    else:
        tail = f"{parks[0]} and {parks[1]} are good bets."
    # A habitat that already has a "; ..." clause gets a new sentence instead.
    return f"{habitat}. {tail}" if ";" in habitat else f"{habitat}; {tail}"


def main() -> None:
    with open(SPECIES / "habitats.csv", newline="", encoding="utf-8") as fh:
        habitats = {r["slug"]: r["habitat"] for r in csv.DictReader(fh)}
    sj_path = SPECIES / "states.json"
    sj = json.loads(sj_path.read_text(encoding="utf-8"))
    missing = set()
    for st in sj["states"]:
        if st["code"] in SKIP:
            continue
        stem = st["species"].removesuffix("_100.csv")
        with open(SPECIES / st["species"], newline="", encoding="utf-8") as fh:
            slugs = [r["slug"] for r in csv.DictReader(fh)]
        parks = json.loads((SPECIES / st["hotspots"]).read_text(encoding="utf-8"))["parks"] if st.get("hotspots") else []
        out = SPECIES / f"{stem}_dex.csv"
        with open(out, "w", newline="", encoding="utf-8") as fh:
            w = csv.DictWriter(fh, FIELDS)
            w.writeheader()
            for slug in slugs:
                if slug not in habitats:
                    missing.add(slug)
                    continue
                w.writerow({"slug": slug, "where_to_find": line(habitats[slug], parks_for(slug, parks))})
        st["dex"] = out.name
    sj_path.write_text(json.dumps(sj, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    if missing:
        print("No habitat line yet (add to species/habitats.csv):", ", ".join(sorted(missing)))


if __name__ == "__main__":
    main()
