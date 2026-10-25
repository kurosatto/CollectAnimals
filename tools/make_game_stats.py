"""Minigame stats for every animal: Speed, Jump, Agility and Size, each 1 to 5.

They come from the real animal: its weight (species/details.csv), its kind (the
state lists, species/household.csv) and what it's known for (fast runners, great
jumpers, slow crawlers), with a few hand-tuned stars. Writes
species/sprites/game_stats.json, which the website and the Android app both read.

    python tools/make_game_stats.py
"""
from __future__ import annotations

import csv
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SPECIES = ROOT / "species"

# Words in a slug that say how fast it is (first match wins, most specific first).
SPEED = [
    (5, r"pronghorn|peregrine|swifts?|merlin|sailfish|tuna|mako|dolphin|porpoise"),
    (4, r"deer|elk|horse|pony|coyote|fox|wolf|jackrabbit|hare|roadrunner|hummingbird|swallow|martin|falcon|kestrel|hawk|"
        r"sea_lion|seal|trout|salmon|bass|mackerel|barracuda|darner|dragonfly|skimmer|antelope|bighorn|cougar|bobcat|lynx|"
        r"greyhound|dog|sandpiper|plover|tern|gull|duck|mallard|teal|merganser|cormorant|squid|tiger_beetle"),
    (1, r"slug|snail|whelk|periwinkle|nerite|tortoise|box_turtle|sea_star|star|starfish|chiton|mussel|clam|oyster|scallop|anemone|"
        r"urchin|sea_cucumber|barnacle|sponge|bryozoan|woodlouse|pill_bug|millipede|sloth|limpet|dogwinkle|slippersnail|"
        r"caterpillar|tussock|webworm|blindsnake|manatee|jelly|nettle"),
    (2, r"turtle|cooter|slider|terrapin|softshell|salamander|newt|mudpuppy|hellbender|siren|amphiuma|toad|porcupine|skunk|"
        r"opossum|armadillo|beetle|ladybug|lady_beetle|firefly|crab|crayfish|lobster|mole|vole|shrew|woodchuck|groundhog|"
        r"beaver|muskrat|bear|bison|moose|manatee|tortoise|spider|tarantula|scorpion|centipede|mantis|stick|walkingstick|"
        r"grub|ants?|termite|goby|sculpin|catfish|bullhead|sucker|carp|blenny|eel|moray|boxfish|toby|puffer|gar"),
]
JUMP = [
    (5, r"frog|bullfrog|peeper|treefrog|coqui|rabbit|cottontail|hare|jackrabbit|kangaroo|grasshopper|cricket|katydid|flea|"
        r"jumping_spider|springtail|mountain_lion|cougar|impala|klipspringer|leaping"),
    (4, r"deer|pronghorn|bighorn|mountain_goat|cat|bobcat|lynx|squirrel|chipmunk|fox|toad|spadefoot|lizard|anole|gecko|"
        r"monkey|lemur|flying|salmon|dolphin|mullet|tarpon"),
    (1, r"slug|snail|tortoise|turtle|cooter|slider|terrapin|softshell|snake|boa|python|rattlesnake|kingsnake|garter|"
        r"ratsnake|racer|whipsnake|hognose|watersnake|cottonmouth|copperhead|blindsnake|worm|sea_star|star|chiton|mussel|clam|"
        r"anemone|urchin|sea_cucumber|barnacle|sponge|bryozoan|woodlouse|millipede|centipede|caterpillar|bison|bear|moose|"
        r"manatee|walrus|limpet|periwinkle|nerite|whelk|dogwinkle|slippersnail|jelly|nettle|caecilian|amphiuma|siren"),
    (2, r"salamander|newt|mudpuppy|hellbender|beetle|crab|crayfish|lobster|skunk|opossum|porcupine|armadillo|beaver|"
        r"woodchuck|groundhog|mole|shrew|vole|duck|goose|swan|heron|egret|crane|pelican"),
]
CATEGORY_SPEED = {"mammal": 3, "bird": 3, "reptile": 2, "amphibian": 2, "fish": 3, "marine": 3, "invertebrate": 2}
CATEGORY_JUMP = {"mammal": 3, "bird": 3, "reptile": 3, "amphibian": 3, "fish": 3, "marine": 3, "invertebrate": 2}
# Hand-tuned stars, where the rules above don't say enough: (speed, jump, agility, size).
STARS = {
    "pacific_banana_slug": (1, 1, 1, 2),
    "pronghorn": (5, 4, 3, 4),
    "greater_roadrunner": (4, 3, 5, 2),
    "peregrine_falcon": (5, 3, 5, 2),
    "western_gray_squirrel": (3, 5, 5, 2),
    "eastern_gray_squirrel": (3, 5, 5, 2),
    "american_bullfrog": (2, 5, 3, 2),
    "desert_tortoise": (1, 1, 1, 3),
    "american_black_bear": (3, 2, 2, 5),
    "american_bison": (4, 2, 1, 5),
    "ruby_throated_hummingbird": (4, 3, 5, 1),
    "annas_hummingbird": (4, 3, 5, 1),
    # Names that fool the word rules: a swift woodlouse isn't a swift, a prairie dog or a
    # fox squirrel isn't a dog or a fox.
    "swift_woodlouse": (1, 1, 2, 1),
    "black_tailed_prairie_dog": (3, 3, 4, 2),
    "fox_squirrel": (3, 5, 5, 2),
    "house_mouse": (3, 3, 5, 1),
}

# Each game uses the animal's speed in its own place: Trail Run on land, River Swim in
# the water, Sky Glide in the air. A seal is slow on land and fast in the water; a duck
# waddles, paddles and flies fast. The shared Speed above is where it's at home.
LAND = [
    (1, r"seal|walrus|penguin|loon|grebe|sea_otter|manatee|sea_turtle|loggerhead|dolphin|porpoise|orca|whale|turtle|cooter|"
        r"slider|terrapin|softshell"),
    (2, r"sea_lion|beaver|muskrat|alligator|crocodile|duck|teal|merganser|goose|brant|swan|gull|tern|cormorant|pelican|coot|mallard|"
        r"wigeon|gadwall|pintail|shoveler|scaup|bufflehead|goldeneye|eider|scoter|gallinule|anhinga|otter"),
]
WATER = [
    (5, r"dolphin|porpoise|orca|seal|sea_lion|penguin|sailfish|tuna|mako"),
    (4, r"otter|loon|grebe|merganser|cormorant|anhinga|goldeneye|bufflehead|eider|scoter|scaup|sea_turtle|loggerhead|"
        r"alligator|crocodile|trout|salmon|bass|barracuda|mackerel|squid|whale|swimming_crab"),
    (3, r"beaver|muskrat|softshell|snapping|cooter|slider|map|pond_turtle|painted_turtle|frog|bullfrog|duck|teal|wigeon|gadwall|pintail|shoveler|goose|"
        r"brant|swan|coot|gallinule|watersnake|cottonmouth|pelican|newt|manatee|octopus|mallard"),
    (2, r"turtle|terrapin|toad|spadefoot|salamander|hellbender|mudpuppy|crayfish|crab"),
    (1, r"jelly|man_o_war|sea_hare|by_the_wind|nettle"),
]
# Land and air animals that can paddle a bit, when no rule above names them.
WATER_DEFAULT = {"mammal": 2, "bird": 2, "reptile": 2, "amphibian": 2}

UNIT_KG = {"kg": 1, "g": .001, "mg": 1e-6, "lb": .4536, "lbs": .4536, "oz": .02835, "ton": 907.2, "tons": 907.2, "t": 1000}


def weight_kg(text: str) -> float | None:
    """The middle of a range like '1.5–2.5 lb (0.7–1.1 kg)', in kilograms."""
    best = None
    for lo, hi, unit in re.findall(r"([\d.,]+)(?:\s*[–-]\s*([\d.,]+))?\s*(kg|mg|g|lbs?|oz|tons?|t)\b", text or ""):
        a = float(lo.replace(",", "")); b = float(hi.replace(",", "")) if hi else a
        kg = (a + b) / 2 * UNIT_KG[unit]
        if unit in ("kg", "g", "mg", "t"):
            return kg  # the metric figure is the most exact
        best = best or kg
    return best


def rule(table, slug, default):
    """The first pattern that names a whole word of the slug ("tern" isn't in "western")."""
    for value, pattern in table:
        if re.search(rf"(?:^|_)(?:{pattern})(?:_|$)", slug):
            return value
    return default


def size_of(kg: float | None, category: str) -> int:
    if kg is None:
        return {"invertebrate": 1, "amphibian": 2, "reptile": 2, "fish": 2, "marine": 2, "bird": 2}.get(category, 3)
    for limit, size in ((.005, 1), (.3, 2), (4, 3), (60, 4)):
        if kg < limit:
            return size
    return 5


def main() -> None:
    category, details = {}, {}
    for path in sorted(SPECIES.glob("*_100.csv")):
        with path.open(encoding="utf-8") as f:
            for row in csv.DictReader(f):
                category.setdefault(row["slug"], row["category"])
    household = SPECIES / "household.csv"
    if household.is_file():
        with household.open(encoding="utf-8") as f:
            for row in csv.DictReader(f):
                category.setdefault(row["slug"], "mammal")
    with (SPECIES / "details.csv").open(encoding="utf-8") as f:
        for row in csv.DictReader(f):
            details[row["slug"]] = row
    stats, places = {}, {}
    for slug, cat in sorted(category.items()):
        if slug in STARS:
            stats[slug] = list(STARS[slug])
            continue
        d = details.get(slug, {})
        size = size_of(weight_kg(d.get("weight", "")), cat)
        speed = rule(SPEED, slug, CATEGORY_SPEED.get(cat, 3))
        jump = rule(JUMP, slug, CATEGORY_JUMP.get(cat, 3))
        # Small things and fliers turn on a dime; big heavy ones don't.
        agility = max(1, min(5, 6 - size + (1 if cat in ("bird", "invertebrate") else 0)))
        if speed == 1:
            agility = min(agility, 2)  # crawlers can't dodge
        elif speed >= 4 or jump >= 4:
            agility = max(agility, 3)  # quick, springy animals can
        stats[slug] = [speed, jump, agility, size]
    for slug, cat in sorted(category.items()):
        base = stats[slug][0]
        p = {"trail": rule(LAND, slug, base), "river": rule(WATER, slug, WATER_DEFAULT.get(cat, base)), "sky": base}
        p = {k: v for k, v in p.items() if v != base}
        if p:
            places[slug] = p
    out = SPECIES / "sprites" / "game_stats.json"
    out.write_text(json.dumps({"order": ["speed", "jump", "agility", "size"], "stats": stats, "speed": places},
                              separators=(",", ":")) + "\n", encoding="utf-8")
    from collections import Counter
    for i, name in enumerate(("speed", "jump", "agility", "size")):
        print(name, sorted(Counter(v[i] for v in stats.values()).items()))
    print(f"wrote {len(stats)} animals to {out.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
