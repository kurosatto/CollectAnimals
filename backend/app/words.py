"""Small helpers for the sentences the game shows players."""

# Names that start with a vowel letter but a "you" sound take "a" (a Eurasian Collared-Dove,
# a Utah Prairie Dog, a Uinta Chipmunk).
_YOU_SOUND = ("eu", "uin", "uni", "uta", "use", "usu")


def a_or_an(name: str) -> str:
    """The name with "a" or "an" in front: "an American Robin", "a Eurasian Wren"."""
    low = name.lower()
    vowel = low[:1] in ("a", "e", "i", "o", "u") and not low.startswith(_YOU_SOUND)
    return f"{'an' if vowel else 'a'} {name}"
