"""Build species/animal_names.json: the text-only list players search when they
tell the game what an animal really was ("None of these" -> "What was it?").

The list is the North American animals people photograph most, plus every
species in the game and broad groups ("Some kind of beetle"). Names only, no
photos, so it's small enough to bundle in the web page and the Android app.

Sources (all usable commercially):
- How often each species is seen: research-grade observation counts inside a
  North America box, from the iNaturalist Open Dataset metadata on AWS
  (s3://inaturalist-open-data/observations.csv.gz and taxa.csv.gz). Only the
  counts and the taxonomy are used, to rank and group species.
- English common names: the "common-species" dataset by ecofactbook (npm
  package common-species), CC BY 4.0, built from GBIF and UniProt.
- The game's own names (species/*_100.csv, household.csv) win where they exist.

Usage (the counts take ~15 minutes to stream; see count_na below):
    python ml/build_animal_names.py --counts na_counts.tsv --taxa taxa.csv.gz \
        --common common.json [--limit 9000]

na_counts.tsv is "taxon_id<TAB>count", made with:
    curl -sS https://inaturalist-open-data.s3.amazonaws.com/observations.csv.gz | gzip -dc |
      awk -F'\\t' 'NR>1 && $7=="research" && $3!="" && $3>=14 && $3<=84 && $4>=-170 && $4<=-50
                   {c[$6]++} END {for (k in c) print k"\\t"c[k]}' > na_counts.tsv
common.json is the package's common_species_data.json.7z, which is plain LZMA:
    python -c "import lzma,json,sys; open('common.json','wb').write(lzma.decompress(
      open(sys.argv[1],'rb').read(), format=lzma.FORMAT_ALONE))" common_species_data.json.7z
"""

from __future__ import annotations

import argparse
import csv
import gzip
import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SPECIES = ROOT / "species"
ANIMALIA = "1"  # iNaturalist taxon id

# Broad groups: id, what the player sees, extra search words, and the taxa
# (iNaturalist names) that belong to it. The deepest matching taxon wins, so
# a hawk is "hawk", not "bird". Order here is the order shown before typing.
GROUPS = [
    ("bird", "Some kind of bird", "", ["Aves"]),
    ("insect", "Some kind of insect", "bug", ["Insecta"]),
    ("spider", "Some kind of spider", "", ["Araneae"]),
    ("mammal", "Some kind of mammal", "animal fur", ["Mammalia"]),
    ("butterfly", "Some kind of butterfly or moth", "caterpillar", ["Lepidoptera"]),
    ("beetle", "Some kind of beetle", "ladybug", ["Coleoptera"]),
    ("lizard", "Some kind of lizard", "", ["Squamata"]),
    ("snake", "Some kind of snake", "", ["Serpentes"]),
    ("fish", "Some kind of fish", "", ["Actinopterygii", "Holocephali", "Petromyzonti"]),
    ("frog", "Some kind of frog or toad", "tadpole", ["Anura"]),
    ("snail", "Some kind of snail or slug", "shell", ["Gastropoda"]),
    ("bee", "Some kind of bee or wasp", "hornet yellowjacket", ["Hymenoptera"]),
    ("ant", "Some kind of ant", "", ["Formicidae"]),
    ("fly", "Some kind of fly", "mosquito gnat", ["Diptera"]),
    ("dragonfly", "Some kind of dragonfly or damselfly", "", ["Odonata"]),
    ("grasshopper", "Some kind of grasshopper or cricket", "katydid", ["Orthoptera"]),
    ("true-bug", "Some kind of true bug (stink bug, cicada, aphid)", "", ["Hemiptera"]),
    ("mantis", "Some kind of mantis", "praying", ["Mantodea"]),
    ("turtle", "Some kind of turtle or tortoise", "", ["Testudines"]),
    ("salamander", "Some kind of salamander or newt", "", ["Caudata"]),
    ("reptile", "Some kind of reptile", "", ["Reptilia"]),
    ("amphibian", "Some kind of amphibian", "", ["Amphibia"]),
    ("rodent", "Some kind of rodent (mouse, rat, squirrel)", "chipmunk vole gopher", ["Rodentia"]),
    ("bat", "Some kind of bat", "", ["Chiroptera"]),
    ("rabbit", "Some kind of rabbit or hare", "bunny", ["Lagomorpha"]),
    ("deer", "Some kind of deer", "elk moose", ["Cervidae"]),
    ("duck", "Some kind of duck, goose or swan", "", ["Anatidae"]),
    ("hawk", "Some kind of hawk, eagle or falcon", "raptor kite vulture", ["Accipitridae", "Falconidae", "Cathartidae"]),
    ("owl", "Some kind of owl", "", ["Strigiformes"]),
    ("hummingbird", "Some kind of hummingbird", "", ["Trochilidae"]),
    ("gull", "Some kind of gull or tern", "seagull", ["Laridae"]),
    ("heron", "Some kind of heron or egret", "", ["Ardeidae"]),
    ("woodpecker", "Some kind of woodpecker", "flicker sapsucker", ["Picidae"]),
    ("songbird", "Some kind of songbird (sparrow, finch, warbler)", "", ["Passeriformes"]),
    ("shark", "Some kind of shark or ray", "skate", ["Elasmobranchii"]),
    ("crab", "Some kind of crab, shrimp or crayfish", "lobster crawdad", ["Decapoda"]),
    ("pill-bug", "Some kind of pill bug or sow bug", "roly poly woodlouse", ["Isopoda"]),
    ("crustacean", "Some other crustacean (barnacle, krill)", "", ["Crustacea"]),
    ("arachnid", "Some other arachnid (tick, scorpion, harvestman)", "mite daddy longlegs", ["Arachnida"]),
    ("centipede", "Some kind of centipede or millipede", "", ["Myriapoda"]),
    ("clam", "Some kind of clam, mussel or oyster", "scallop shell", ["Bivalvia"]),
    ("octopus", "Some kind of octopus or squid", "", ["Cephalopoda"]),
    ("mollusk", "Some other mollusk (chiton, sea slug)", "", ["Mollusca"]),
    ("sea-star", "Some kind of sea star", "starfish", ["Asteroidea"]),
    ("urchin", "Some kind of sea urchin or sand dollar", "", ["Echinoidea"]),
    ("echinoderm", "Some other echinoderm (sea cucumber, brittle star)", "", ["Echinodermata"]),
    ("jellyfish", "Some kind of jellyfish", "", ["Scyphozoa", "Hydrozoa", "Cubozoa"]),
    ("anemone", "Some kind of sea anemone or coral", "", ["Anthozoa"]),
    ("sponge", "Some kind of sponge", "", ["Porifera"]),
    ("sea-squirt", "Some kind of sea squirt (tunicate)", "", ["Ascidiacea"]),
    ("worm", "Some kind of worm", "earthworm leech", ["Annelida", "Nematoda", "Platyhelminthes"]),
    ("animal", "Some other animal", "", ["Animalia"]),
]
# Not animals: still useful training labels ("other").
EXTRA_GROUPS = [
    ("pet", "A pet (dog, cat, other pet)", "puppy kitten hamster"),
    ("person", "A person", "people human me selfie"),
    ("not-animal", "Not an animal (plant, mushroom, toy)", "flower tree rock nothing"),
    ("no-animal", "No animal in the photo", "empty blurry missed"),
]


def read_taxa(path: Path) -> tuple[dict[str, tuple[str, str, list[str]]], dict[str, str]]:
    """taxon_id -> (name, rank, ancestry ids) for animals, and name -> id of the
    active taxon with that name (old, inactive taxa keep their names too)."""
    out, by_name = {}, {}
    with gzip.open(path, "rt", encoding="utf-8", newline="") as f:
        for row in csv.DictReader(f, delimiter="\t"):
            anc = (row["ancestry"] or "").split("/")
            if len(anc) < 2 or anc[1] != ANIMALIA:
                continue
            out[row["taxon_id"]] = (row["name"], row["rank"], anc)
            if row["active"] == "true" or row["name"] not in by_name:
                by_name[row["name"]] = row["taxon_id"]
    return out, by_name


def game_species() -> dict[str, str]:
    """Scientific name -> the game's common name, for every state list and pets."""
    names = {}
    for p in sorted(SPECIES.glob("*_100.csv")) + [SPECIES / "household.csv"]:
        with p.open(encoding="utf-8", newline="") as f:
            for row in csv.DictReader(f):
                names.setdefault(row["scientific_name"].strip(), row["common_name"].strip())
    return names


def nice(name: str) -> str:
    name = " ".join(name.split())
    return name[:1].upper() + name[1:]


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--counts", type=Path, required=True)
    ap.add_argument("--taxa", type=Path, required=True)
    ap.add_argument("--common", type=Path, required=True)
    ap.add_argument("--limit", type=int, default=9000, help="most-seen species to keep")
    ap.add_argument("--min-count", type=int, default=20)
    ap.add_argument("--out", type=Path, default=SPECIES / "animal_names.json")
    args = ap.parse_args()

    taxa, by_name = read_taxa(args.taxa)
    group_of_taxon = {ANIMALIA: "animal"}
    for gid, _, _, names in GROUPS:
        for n in names:
            if n == "Animalia":
                continue
            if n in by_name:
                group_of_taxon[by_name[n]] = gid
            else:
                print(f"note: no iNaturalist taxon named {n}")

    # Observations of a subspecies count for its species.
    counts: Counter[str] = Counter()
    with args.counts.open(encoding="utf-8") as f:
        for line in f:
            tid, n = line.rstrip("\n").split("\t")
            t = taxa.get(tid)
            if t is None:
                continue
            name, rank, anc = t
            if rank in ("subspecies", "variety", "form"):
                tid = anc[-1]
                if tid not in taxa:
                    continue
            counts[tid] += int(n)

    common = {}
    for row in json.loads(args.common.read_text(encoding="utf-8")):
        if row["taxonomy"].get("kingdom") == "Animalia" and row["common_name"] not in ("", "_"):
            common.setdefault(row["taxonomy"]["species"], nice(row["common_name"]))
    game = game_species()

    def group(tid: str) -> str:
        for a in [tid] + taxa[tid][2][::-1]:
            if a in group_of_taxon:
                return group_of_taxon[a]
        return "animal"

    entries, seen_sci, seen_name = [], set(), set()

    def add(common_name: str, sci: str, gid: str, game_animal: bool = False) -> None:
        # Two species with one common name would look the same in the picker;
        # keep the more often seen one, unless both are in the game.
        key = common_name.lower()
        if sci in seen_sci or (key in seen_name and not game_animal):
            return
        seen_sci.add(sci)
        seen_name.add(key)
        entries.append([common_name, sci, gid])

    kept = 0
    for tid, n in counts.most_common():
        name, rank, _ = taxa[tid]
        if rank != "species" or n < args.min_count:
            continue
        cn = game.get(name) or common.get(name)
        if not cn:
            continue
        add(cn, name, group(tid))
        kept += 1
        if kept >= args.limit:
            break
    # Every animal in the game, even ones rarely photographed (pets have no taxon here).
    for sci, cn in game.items():
        tid = by_name.get(sci)
        add(cn, sci, group(tid) if tid else "animal", game_animal=True)

    groups = [[gid, label, words] for gid, label, words, _ in GROUPS] + [list(g) for g in EXTRA_GROUPS]
    out = {
        "about": "Names: common-species by ecofactbook (GBIF, UniProt), CC BY 4.0. "
                 "Ranked by iNaturalist Open Dataset sightings in North America.",
        "groups": groups,
        "names": entries,
    }
    args.out.write_text(json.dumps(out, ensure_ascii=False, separators=(",", ":")) + "\n", encoding="utf-8")
    print(f"{len(entries)} names ({kept} by sightings), {len(groups)} groups -> {args.out}")


if __name__ == "__main__":
    main()
