from app.words import a_or_an


def test_a_or_an():
    assert a_or_an("American Robin") == "an American Robin"
    assert a_or_an("Osprey") == "an Osprey"
    assert a_or_an("Eurasian Collared-Dove") == "a Eurasian Collared-Dove"
    assert a_or_an("Utah Prairie Dog") == "a Utah Prairie Dog"
    assert a_or_an("Upland Sandpiper") == "an Upland Sandpiper"
    assert a_or_an("Coyote") == "a Coyote"


def test_friendly_error():
    from app.words import friendly_error
    e = friendly_error({"type": "string_pattern_mismatch", "loc": ("body", "username"),
                        "msg": "String should match pattern", "input": "ana b"})
    assert e == {"type": "string_pattern_mismatch", "loc": ["body", "username"],
                 "msg": "Usernames can only use letters, numbers, _ . and -"}
    assert friendly_error({"type": "value_error", "loc": ("body", "x"), "msg": "Value error, too big"})["msg"] == "too big"
