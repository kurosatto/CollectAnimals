"""Small helpers for the sentences the game shows players."""

# Names that start with a vowel letter but a "you" sound take "a" (a Eurasian Collared-Dove,
# a Utah Prairie Dog, a Uinta Chipmunk).
_YOU_SOUND = ("eu", "uin", "uni", "uta", "use", "usu")


def a_or_an(name: str) -> str:
    """The name with "a" or "an" in front: "an American Robin", "a Eurasian Wren"."""
    low = name.lower()
    vowel = low[:1] in ("a", "e", "i", "o", "u") and not low.startswith(_YOU_SOUND)
    return f"{'an' if vowel else 'a'} {name}"


# Plain words for the form mistakes players actually make (FastAPI's own
# messages read like "String should match pattern '^[A-Za-z0-9_.-]+$'").
_FIELD_WORDS = {
    ("username", "string_pattern_mismatch"): "Usernames can only use letters, numbers, _ . and -",
    ("username", "string_too_short"): "Usernames need at least 3 characters",
    ("username", "string_too_long"): "Usernames can be at most 40 characters",
    ("password", "string_too_short"): "Passwords need at least 8 characters",
    ("password", "value_error"): "That password is too long",
    ("email", "value_error"): "That email address doesn't look right",
    ("birth_year", None): "Enter the year you were born",
}


def friendly_error(err: dict) -> dict:
    """One validation error with a readable msg, and without the input echoed back
    (the default reply repeats what was sent, passwords included)."""
    loc = err.get("loc") or ()
    field, kind = (loc[-1] if loc else None), err.get("type")
    msg = _FIELD_WORDS.get((field, kind)) or _FIELD_WORDS.get((field, None)) or str(err.get("msg", ""))
    if msg.startswith("Value error, "):
        msg = msg[len("Value error, "):]
    return {"type": kind, "loc": list(loc), "msg": msg}
