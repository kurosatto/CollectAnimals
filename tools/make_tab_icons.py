"""Draw the 16x16 pixel-art tab icons in the same palette and outline as the
animal sprites, and write them to species/sprites/ui_tab_<name>.png (the web
app serves them from /sprites/, the Android app bundles the same files).

    python tools/make_tab_icons.py
"""
from pathlib import Path

from PIL import Image

PALETTE = {
    "o": (38, 26, 46),      # outline ink, as on the sprites
    "g": (88, 166, 98),     # leaf green
    "G": (47, 125, 79),     # app green
    "d": (31, 84, 54),      # deep green
    "l": (160, 214, 140),   # light green
    "w": (246, 242, 230),   # paper
    "k": (150, 156, 170),   # stone
    "K": (96, 100, 120),    # dark stone
    "b": (150, 98, 60),     # bark
    "B": (98, 62, 38),      # dark bark
    "y": (242, 193, 78),    # sun
    "s": (124, 196, 232),   # sky
    "S": (70, 140, 196),    # deep sky
    "r": (217, 83, 79),     # red
    "p": (232, 180, 130),   # fur / skin
    "P": (190, 132, 90),    # darker fur
}

ICONS = {
    # A chunky green camera with a lens.
    "capture": [
        "................",
        "................",
        "....oooo........",
        "...okkkko...oo..",
        ".oooooooooooyyo.",
        ".oGGGGGGGGGGooo.",
        ".oGGGGoooGGGGGo.",
        ".oGGGoSSSoGGGGo.",
        ".oGGoSswSSoGGGo.",
        ".oGGoSSSSSoGGGo.",
        ".oGGoSSSSSoGGGo.",
        ".oGGGoSSSoGGGGo.",
        ".odddGoooGddddo.",
        ".oooooooooooooo.",
        "................",
        "................",
    ],
    # An open field guide with a leaf on the page.
    "guide": [
        "................",
        "................",
        "..oooo....oooo..",
        ".owwwwoooowwwwo.",
        ".owwwwwoowwwwwo.",
        ".owggwwoowwkkwo.",
        ".owgggwoowwwwwo.",
        ".owwgGwoowkkkwo.",
        ".owwwGwoowwwwwo.",
        ".owwwwwoowkkwwo.",
        ".owwwwwoowwwwwo.",
        ".obbbbwoowbbbbo.",
        ".oBBBBBooBBBBBo.",
        "..oooooooooooo..",
        "................",
        "................",
    ],
    # A framed photo of hills under the sun.
    "photos": [
        "................",
        "................",
        ".oooooooooooooo.",
        ".obbbbbbbbbbbbo.",
        ".obsssssssssybo.",
        ".obssssssssyybo.",
        ".obsssssssssssbo"[:16],
        ".obsssgsssssssbo"[:16],
        ".obssgggssgssbo.",
        ".obsgggggggggbo.",
        ".obgggllgggggbo.",
        ".obGGGGGGGGGGbo.",
        ".obbbbbbbbbbbbo.",
        ".oooooooooooooo.",
        "................",
        "................",
    ],
    # A speech bubble with a paw print: news from other players.
    "feed": [
        "................",
        "................",
        "..oooooooooooo..",
        ".owwwwwwwwwwwwo.",
        ".owwwPwwwwPwwwo.",
        ".owwPPwPPwPPwwo.",
        ".owwwwPPPPwwwwo.",
        ".owwwPPPPPPwwwo.",
        ".owwwPPPPPPwwwo.",
        ".owwwwPPPPwwwwo.",
        ".owwwwwwwwwwwwo.",
        "..oooowwoooooo..",
        ".....owo........",
        "....oo..........",
        "................",
        "................",
    ],
    # A pine tree on a hill: parks to visit.
    "parks": [
        "................",
        ".......oo.......",
        "......oGGo......",
        ".....oGGgGo.....",
        "....oGGGGgGo....",
        "......oGGo......",
        ".....oGGGgGo....",
        "....oGGGGGgGo...",
        "...oGGGGGGGgGo..",
        "......oGGo......",
        "....ooGddGoo....",
        "..oo.oGddGo.oo..",
        ".oggggobbogggggo"[:16],
        ".ogggggbbgggllgo",
        ".oooooooooooooo.",
        "................",
    ],
    # Two friendly faces.
    "friends": [
        "................",
        "................",
        "..ooooo.........",
        ".oBBBBBo..ooooo.",
        ".opppppo.oBBBBBo",
        ".opopopo.opppppo",
        ".oppPppo.opopopo",
        "..ooooo..oppPppo",
        ".oGGGGGo..ooooo.",
        "oGGGGGGGooyyyyyo",
        "oGGGGGGGoyyyyyyo",
        "oGGGGGGGoyyyyyyo",
        "oooooooooooooooo",
        "................",
        "................",
        "................",
    ],
    # A little green game pad with a red and a yellow button.
    "games": [
        "................",
        "................",
        "................",
        "................",
        "..oooooooooooo..",
        ".oGGGGGGGGGGGGo.",
        "oGGGoGGGGGGGGyGo",
        "oGGoooGGGGGrGGGo",
        "oGGGoGGGGGGGGGGo",
        "oGGGGGGddGGGGGGo",
        "oGGGGGdoodGGGGGo",
        ".oGGGdo..odGGGo.",
        "..oooo....oooo..",
        "................",
        "................",
        "................",
    ],
}


def main():
    out = Path(__file__).resolve().parents[1] / "species" / "sprites"
    for name, rows in ICONS.items():
        assert len(rows) == 16 and all(len(r) == 16 for r in rows), name
        im = Image.new("RGBA", (16, 16), (0, 0, 0, 0))
        for y, row in enumerate(rows):
            for x, ch in enumerate(row):
                if ch != ".":
                    im.putpixel((x, y), PALETTE[ch] + (255,))
        im.save(out / f"ui_tab_{name}.png")
        print(f"wrote ui_tab_{name}.png")


if __name__ == "__main__":
    main()
