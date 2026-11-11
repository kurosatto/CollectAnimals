"""Draw the small 16x16 pixel-art UI icons (coin, shop, lock, pin, bell, sun, moon,
music, log out, palette, flag, heart) that replace generic emojis in the apps, in the same palette
and ink outline as the tab icons and animal sprites. Writes species/sprites/ui_ic_<name>.png
(the web app serves them from /sprites/, the Android app bundles the same files).

Each icon is painted as fills only; the dark outline is added around them automatically.

    python tools/make_ui_icons.py
"""
from pathlib import Path

from PIL import Image

from make_tab_icons import PALETTE as TAB

PALETTE = dict(TAB)
PALETTE.update({
    "Y": (196, 138, 44),    # dark gold
    "h": (255, 238, 170),   # highlight
    "R": (150, 44, 44),     # dark red
    "m": (238, 230, 196),   # moon
    "M": (196, 186, 150),   # moon shadow
})
INK = PALETTE["o"]


def circle(r2, cx=7.5, cy=7.5):
    return lambda x, y: (x - cx) ** 2 + (y - cy) ** 2 <= r2


def coin():
    rows = []
    for y in range(16):
        row = ""
        for x in range(16):
            d = (x - 7.5) ** 2 + (y - 7.5) ** 2
            if d > 42:
                row += "."
            elif d > 30:
                row += "Y" if x + y > 15 else "y"   # rim, darker bottom right
            elif d > 20:
                row += "h" if x + y < 12 else "y"
            elif d > 12:
                row += "Y" if x + y > 15 else "y"   # a raised inner ring
            else:
                row += "h" if x + y < 14 else "y"
        rows.append(row)
    return rows


def sun():
    rows = []
    for y in range(16):
        row = ""
        for x in range(16):
            d = (x - 7.5) ** 2 + (y - 7.5) ** 2
            ray = (x in (7, 8) and (y <= 1 or y >= 14)) or (y in (7, 8) and (x <= 1 or x >= 14)) \
                or (abs(x - y) == 0 and (x <= 2 or x >= 13)) or (x + y == 15 and (x <= 2 or x >= 13))
            if d <= 17:
                row += "h" if (x - 6) ** 2 + (y - 6) ** 2 <= 3 else ("Y" if x + y > 18 else "y")
            elif ray:
                row += "y"
            else:
                row += "."
        rows.append(row)
    return rows


def moon():
    rows = []
    for y in range(16):
        row = ""
        for x in range(16):
            inside = (x - 7.5) ** 2 + (y - 7.5) ** 2 <= 36
            bite = (x - 10.5) ** 2 + (y - 5) ** 2 <= 22
            if inside and not bite:
                row += "M" if (x - 4) ** 2 + (y - 9) ** 2 <= 2 or (x - 6) ** 2 + (y - 12) ** 2 <= 1 else "m"
            else:
                row += "."
        rows.append(row)
    return rows


GRIDS = {
    # A market stall: striped awning over a wooden counter with jars.
    "shop": [
        "................",
        "..............  ",
        ".rrwwrrwwrrwwrr.",
        ".rrwwrrwwrrwwrr.",
        ".rrwwrrwwrrwwrr.",
        "..r..r..r..r..r.",
        "..B..........B..",
        "..B..........B..",
        "..B..yy..gg..B..",
        "..B..yy..gg..B..",
        "bbbbbbbbbbbbbbbb",
        "bBBBBBBBBBBBBBBb",
        "bbbbbbbbbbbbbbbb",
        "bBBBBBBBBBBBBBBb",
        "................",
        "................",
    ],
    # A brass padlock with a keyhole.
    "lock": [
        "................",
        "................",
        ".....kkkkkk.....",
        "....kk....kk....",
        "....k......k....",
        "....k......k....",
        "....k......k....",
        "...yyyyyyyyyy...",
        "...yhhhhhhhhy...",
        "...yhyyyyyyyY...",
        "...yyyyRRyyyY...",
        "...yyyyRRyyyY...",
        "...yyyyyRyyyY...",
        "...YYYYYYYYYY...",
        "................",
        "................",
    ],
    # A red map pin.
    "pin": [
        "................",
        "......rrrr......",
        ".....rrrrrr.....",
        "....rrhrrrrR....",
        "....rhrwwrrR....",
        "....rrwwwwrR....",
        "....rrwwwwrR....",
        "....rrrwwrrR....",
        ".....rrrrrR.....",
        ".....rrrrRR.....",
        "......rrRR......",
        "......rrR.......",
        ".......R........",
        "................",
        "................",
        "................",
    ],
    # A brass bell.
    "bell": [
        "................",
        ".......yy.......",
        "......yyyy......",
        ".....yhyyyY.....",
        ".....yhyyyY.....",
        ".....yhyyyY.....",
        "....yhyyyyyY....",
        "....yhyyyyyY....",
        "...yyyyyyyyyY...",
        "..yyyyyyyyyyyY..",
        "..YYYYYYYYYYYY..",
        "......yYY.......",
        "................",
        "................",
        "................",
        "................",
    ],
    # A painter's palette with dabs of paint.
    "palette": [
        "................",
        "....wwwwwww.....",
        "..wwwwwwwwwww...",
        ".wwrrwwwyywwww..",
        ".wwrrwwwyywwwww.",
        "wwwwwwwwwwwwwww.",
        "wwggwww..wwSSww.",
        "wwggww....wSSww.",
        "wwwwww....wwwww.",
        "wwwwwww..wwwww..",
        ".wwPPwwwwwwwww..",
        ".wwPPwwwwwwww...",
        "..wwwwwwwww.....",
        "....wwww........",
        "................",
        "................",
    ],
    # A speaker with sound waves.
    "sound_on": [
        "................",
        "................",
        "......k.....S...",
        ".....kk...S..S..",
        "....kkk....S.S..",
        "..kkkkk..S..S.S.",
        "..kkkkk..S..S.S.",
        "..kkkkk..S..S.S.",
        "..kkkkk..S..S.S.",
        "....kkk....S.S..",
        ".....kk...S..S..",
        "......k.....S...",
        "................",
        "................",
        "................",
        "................",
    ],
    # The same speaker, crossed out.
    "sound_off": [
        "................",
        "................",
        "......k.........",
        ".....kk.........",
        "....kkk.........",
        "..kkkkk..r...r..",
        "..kkkkk...r.r...",
        "..kkkkk....r....",
        "..kkkkk...r.r...",
        "....kkk..r...r..",
        ".....kk.........",
        "......k.........",
        "................",
        "................",
        "................",
        "................",
    ],
    # A yellow warning sign.
    "warn": [
        "................",
        ".......yy.......",
        "......yyyy......",
        "......yyyy......",
        ".....yyRRyy.....",
        ".....yyRRyy.....",
        "....yyyRRyyy....",
        "....yyyRRyyy....",
        "...yyyyRRyyyy...",
        "...yyyyyyyyyy...",
        "..yyyyyRRyyyyy..",
        "..yyyyyRRyyyyy..",
        ".YYYYYYYYYYYYYY.",
        "................",
        "................",
        "................",
    ],
    # A speech bubble: comments.
    "chat": [
        "................",
        "................",
        "..wwwwwwwwwwww..",
        ".wwwwwwwwwwwwww.",
        ".wwkkkkkkkkkkww.",
        ".wwwwwwwwwwwwww.",
        ".wwkkkkkkkkwwww.",
        ".wwwwwwwwwwwwww.",
        "..wwwwwwwwwwww..",
        "....www.........",
        "....ww..........",
        "....w...........",
        "................",
        "................",
        "................",
        "................",
    ],
    # A gold trophy cup.
    "trophy": [
        "................",
        "...yyyyyyyyyy...",
        ".yyyhhyyyyyyYyy.",
        ".y.yhyyyyyyyY.y.",
        ".y.yhyyyyyyyY.y.",
        "..yyhyyyyyyyYy..",
        "....yyyyyyyY....",
        ".....yyyyyY.....",
        ".......yY.......",
        ".......yY.......",
        "......yyYY......",
        ".....BBBBBB.....",
        ".....BbbbbB.....",
        ".....BBBBBB.....",
        "................",
        "................",
    ],
    # A wooden door with a green arrow walking out of it.
    "logout": [
        "................",
        ".BBBBBBBB.......",
        ".BbbbbbbB.......",
        ".BbBBBBbB.......",
        ".BbBbbBbB.......",
        ".BbBbbBbB...G...",
        ".BbBBBBbB...GG..",
        ".BbbbbyGGGGGGGG.",
        ".BbbbbyGGGGGGGG.",
        ".BbBBBBbB...GG..",
        ".BbBbbBbB...G...",
        ".BbBbbBbB.......",
        ".BbBBBBbB.......",
        ".BbbbbbbB.......",
        ".BBBBBBBB.......",
        "................",
    ],
    # A red flag on a pole: report something.
    "flag": [
        "................",
        "..B.............",
        "..BrrrrrrrRr....",
        "..BrrrrrrrrRr...",
        "..BrrrrrrrrrR...",
        "..BrrrrrrrrRr...",
        "..BrrrrrrrRr....",
        "..BRRRRRRRR.....",
        "..B.............",
        "..B.............",
        "..B.............",
        "..B.............",
        "..B.............",
        ".BBB............",
        "................",
        "................",
    ],
    # A red heart: likes.
    "heart": [
        "................",
        "................",
        "..rrrr....rrrr..",
        ".rrhhrr..rrrrRr.",
        ".rhhrrrrrrrrrRr.",
        ".rhrrrrrrrrrrRr.",
        ".rrrrrrrrrrrRRr.",
        "..rrrrrrrrrrRr..",
        "...rrrrrrrrRr...",
        "....rrrrrrRr....",
        ".....rrrrRr.....",
        "......rrRr......",
        ".......rr.......",
        "................",
        "................",
        "................",
    ],
}


# Thin details (sound waves, the cross) that look better without an outline.
NO_OUTLINE = {"sound_on": "S", "sound_off": "r"}


def outline(rows, skip=""):
    """Paint the ink outline around every filled pixel (4-neighbours)."""
    grid = [list(r.ljust(16, ".")[:16].replace(" ", ".")) for r in rows]
    out = [row[:] for row in grid]
    for y in range(16):
        for x in range(16):
            if grid[y][x] != ".":
                continue
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                nx, ny = x + dx, y + dy
                if 0 <= nx < 16 and 0 <= ny < 16 and grid[ny][nx] not in "." + skip:
                    out[y][x] = "o"
                    break
    return out


def main():
    out = Path(__file__).resolve().parents[1] / "species" / "sprites"
    icons = dict(GRIDS, coin=coin(), sun=sun(), moon=moon())
    for name, rows in icons.items():
        assert len(rows) == 16 and all(len(r) <= 16 for r in rows), name
        im = Image.new("RGBA", (16, 16), (0, 0, 0, 0))
        for y, row in enumerate(outline(rows, NO_OUTLINE.get(name, ""))):
            for x, ch in enumerate(row):
                if ch != ".":
                    im.putpixel((x, y), (INK if ch == "o" else PALETTE[ch]) + (255,))
        im.save(out / f"ui_ic_{name}.png")
        print(f"wrote ui_ic_{name}.png")


if __name__ == "__main__":
    main()
