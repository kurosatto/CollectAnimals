"""Minigame stats for every animal: Speed, Jump, Agility and Size, each 1 to 5.

They come from the real animal: its weight (species/details.csv), its kind (the
state lists, species/household.csv) and what it's known for (fast runners, great
jumpers, slow crawlers), with a few hand-tuned stars. Also how big each animal
is drawn on the field screen ("scale"). Writes
species/sprites/game_stats.json, which the website and the Android app both read.

    python tools/make_game_stats.py
"""
from __future__ import annotations

import csv
import json
import math
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
# Birds and bugs come in big families that the rules above lump together; these tell a
# dove from a wren and a bee from a butterfly: (pattern, speed, jump, agility), None keeps
# what the other rules said. First match wins.
FAMILY = [
    (r"heron|egret|bittern|crane|stork|ibis|spoonbill|limpkin|flamingo", 2, 2, 2),
    (r"vulture|condor", 2, 2, 1),
    (r"pelican|swan|goose|brant", 3, 2, 2),
    (r"eagle|osprey|owl", 3, 3, 3),
    (r"crow|raven|magpie|jay|nutcracker", 3, 3, 4),
    (r"dove|pigeon", 4, 2, 3),
    (r"swallow|martin|swift|nighthawk", 5, 2, 5),
    (r"grackle|blackbird|starling|cowbird|bobolink|meadowlark", 4, 3, 4),
    (r"woodpecker|flicker|sapsucker|nuthatch|creeper", 3, 4, 4),
    (r"robin|thrush|bluebird|thrasher|mockingbird|catbird|waxwing", 3, 3, 4),
    (r"warbler|kinglet|gnatcatcher|chickadee|titmouse|bushtit|wren|vireo|verdin", 3, 3, 5),
    (r"sparrow|junco|towhee|finch|goldfinch|siskin|grosbeak|bunting|cardinal|longspur", 3, 4, 4),
    (r"phoebe|flycatcher|kingbird|pewee", 4, 3, 5),
    (r"quail|grouse|bobwhite|turkey|pheasant|chachalaca|prairie_chicken", 2, 3, 2),
    (r"sandpiper|plover|killdeer|dunlin|sanderling|yellowlegs|dowitcher|turnstone|willet|curlew|godwit", 4, 3, 4),
    (r"gull|tern|skimmer", 4, 2, 3),
    (r"bee|bumble|wasp|hornet|yellowjacket", 3, 2, 5),
    (r"dragonfly|darner|skimmer|dasher|pennant|meadowhawk|pondhawk|whitetail|saddlebags|glider", 5, 2, 5),
    (r"damselfly|bluet|dancer|forktail|spreadwing|jewelwing", 3, 2, 4),
    (r"butterfly|swallowtail|monarch|skipper|fritillary|sulphur|admiral|hairstreak|painted_lady|buckeye|checkerspot|"
     r"crescent|longwing|mourning_cloak|queen|copper|blue|white|azure|satyr|wood_nymph|emperor|leafwing", 2, 2, 4),
    (r"moth|sphinx|hawkmoth|underwing|tiger_moth", 3, 2, 3),
    (r"fly|mosquito|midge|gnat", 4, 2, 5),
    (r"beetle|weevil|ladybug|lady_beetle|bug|stink|cicada|cockroach", 2, 2, 3),
    (r"ant|ants|termite", 2, 1, 3),
    (r"mantis", 2, 3, 3),
    (r"orbweaver|spider|widow|tarantula|recluse", 2, 2, 3),
    (r"fiddler_crab|ghost_crab|sand_crab|shore_crab|swimming_crab|blue_crab", 3, 2, 4),
    (r"hermit_crab|crab|crayfish|lobster", 2, 2, 3),
    (r"salamander|newt|ensatina|mudpuppy|hellbender", 2, 2, 3),
    (r"scorpion|centipede", 3, 2, 3),
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


UNIT_CM = {"cm": 1, "mm": .1, "m": 100, "in": 2.54, "ft": 30.48}


def length_cm(text: str) -> float | None:
    """The middle of a range like '16–21 in long (40–53 cm)', in centimetres."""
    best = None
    for lo, hi, unit in re.findall(r"([\d.,]+)(?:\s*[–-]\s*([\d.,]+))?\s*(cm|mm|m|in|ft)\b", text or ""):
        a = float(lo.replace(",", "")); b = float(hi.replace(",", "")) if hi else a
        cm = (a + b) / 2 * UNIT_CM[unit]
        if unit in ("cm", "mm", "m"):
            return cm
        best = best or cm
    return best


def bulk(kg: float | None, cm: float | None, category: str) -> float:
    """How big the animal is, from 1 to 5 in steps of a tenth: its weight and its length
    together, so a tall egret comes out bigger than a crow of about the same weight."""
    marks = []
    if kg is not None:
        # 5 g is a 1, 300 g a 2, 4 kg a 3, 60 kg a 4 and more is a 5, smoothly in between.
        marks.append(1 + math.log10(max(kg, 1e-4) / .005) / math.log10(.3 / .005) if kg < .3 else
                     2 + math.log10(kg / .3) / math.log10(4 / .3) if kg < 4 else
                     3 + math.log10(kg / 4) / math.log10(60 / 4) if kg < 60 else 4 + math.log10(kg / 60) / math.log10(10))
    if cm is not None:
        # 4 cm is a 1, 18 cm a 2, 55 cm a 3, 150 cm a 4 and more is a 5.
        marks.append(1 + math.log10(max(cm, .5) / 4) / math.log10(18 / 4) if cm < 18 else
                     2 + math.log10(cm / 18) / math.log10(55 / 18) if cm < 55 else
                     3 + math.log10(cm / 55) / math.log10(150 / 55) if cm < 150 else 4 + math.log10(cm / 150) / math.log10(3))
    if not marks:
        return {"invertebrate": 1, "amphibian": 2, "reptile": 2, "fish": 2, "marine": 2, "bird": 2}.get(category, 3)
    return max(1, min(5, sum(marks) / len(marks) + 1))


# Rough weight (kg) and length (cm) of the pets and pests that have no details row.
HOUSEHOLD_SIZE = {
    "american_cockroach": (.001, 4), "german_cockroach": (.0001, 1.3), "house_fly": (.00002, .7), "brown_rat": (.35, 40),
    "house_mouse": (.02, 16), "golden_hamster": (.13, 15), "domestic_rabbit": (2.5, 45), "domestic_cat": (4.5, 70),
    "domestic_dog": (20, 90), "horse": (500, 240), "domestic_chicken": (2.5, 45), "rock_pigeon": (.35, 32),
    "budgerigar": (.035, 18), "goldfish": (.1, 15),
}


def scale(kg: float | None, cm: float | None) -> float:
    """How big to draw the animal on the field screen, next to a 1.0 crow: from 0.4 for a
    bee to 1.5 for a bison or whale. Logarithmic, so a seal is clearly bigger than a
    banana slug without a bear being a hundred times the slug."""
    marks = []
    if kg is not None:
        marks.append((math.log10(max(kg, 1e-6)) + 3) / 6)        # 1 g is 0, 1 tonne is 1
    if cm is not None:
        marks.append(math.log10(max(cm, .5) / 2) / math.log10(150))  # 2 cm is 0, 3 m is 1
    if not marks:
        return 1.0
    return round(.4 + 1.1 * max(0, min(1, sum(marks) / len(marks))), 2)


def family(slug: str):
    for pattern, speed, jump, agility in FAMILY:
        if re.search(rf"(?:^|_)(?:{pattern})(?:_|$)", slug):
            return speed, jump, agility
    return None


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
    stats, places, scales = {}, {}, {}
    for slug, cat in sorted(category.items()):
        d = details.get(slug, {})
        kg, cm = weight_kg(d.get("weight", "")), length_cm(d.get("size", ""))
        scales[slug] = scale(*HOUSEHOLD_SIZE[slug]) if kg is None and cm is None and slug in HOUSEHOLD_SIZE else scale(kg, cm)
        if slug in STARS:
            stats[slug] = list(STARS[slug])
            continue
        big = bulk(kg, cm, cat)
        size = max(1, min(5, int(big)))
        speed = rule(SPEED, slug, CATEGORY_SPEED.get(cat, 3))
        jump = rule(JUMP, slug, CATEGORY_JUMP.get(cat, 3))
        # Small things and fliers turn on a dime; big heavy ones don't.
        agility = max(1, min(5, round(6.9 - big + (.8 if cat in ("bird", "invertebrate") else 0))))
        fam = family(slug) if cat != "mammal" else None
        if fam:
            # The family says how it moves; a tiny one is a bit nimbler, a big one less so.
            speed, jump = fam[0], fam[1]
            agility = max(1, min(5, fam[2] + (1 if big < 1.8 and fam[2] < 4 else 0) - (1 if big >= 4.1 else 0)))
        elif cat in ("mammal", "reptile", "amphibian") and speed == CATEGORY_SPEED.get(cat) and jump == CATEGORY_JUMP.get(cat):
            # No rule named it: big land animals cover ground faster, tiny ones dart about.
            speed = 2 if big < 2.3 else 4 if big >= 4.7 else speed
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
    out.write_text(json.dumps({"order": ["speed", "jump", "agility", "size"], "stats": stats, "speed": places,
                              "scale": scales},
                              separators=(",", ":")) + "\n", encoding="utf-8")
    from collections import Counter
    for i, name in enumerate(("speed", "jump", "agility", "size")):
        print(name, sorted(Counter(v[i] for v in stats.values()).items()))
    print(f"wrote {len(stats)} animals to {out.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
