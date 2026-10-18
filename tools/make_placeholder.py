"""Draw the stand-in sprite for animals that don't have pixel art yet (the
species added for the other 48 states), and write species/sprites/placeholder.png
and placeholder_silhouette.png. The server and the Android app show these
whenever a species has no sprite of its own.

    python tools/make_placeholder.py
"""
from pathlib import Path

from pixel import Sprite, silhouette

OUT = Path(__file__).resolve().parent.parent / "species" / "sprites"

# A "?" five pixels wide, drawn in the middle of the egg.
QUESTION = [
    ".###.",
    "#...#",
    "....#",
    "...#.",
    "..#..",
    "..#..",
    ".....",
    "..#..",
]


def draw() -> Sprite:
    """A speckled egg with a question mark: a new animal whose art is still to come."""
    s = Sprite()
    s.ellipse(16, 20, 10, 11.5, "#e8dcc2")
    s.px([(9, 15), (10, 15), (22, 23), (23, 22), (11, 26), (21, 12), (13, 10)], "#c9b48f", shade=False)
    pts = [(14 + x, 15 + y) for y, row in enumerate(QUESTION) for x, c in enumerate(row) if c == "#"]
    s.px(pts, "#7a6248", shade=False)
    return s


def main() -> None:
    img = draw().render()
    img.save(OUT / "placeholder.png")
    silhouette(img).save(OUT / "placeholder_silhouette.png")
    print("wrote", OUT / "placeholder.png", "and placeholder_silhouette.png")


if __name__ == "__main__":
    main()
