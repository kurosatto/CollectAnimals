from app.words import a_or_an


def test_a_or_an():
    assert a_or_an("American Robin") == "an American Robin"
    assert a_or_an("Osprey") == "an Osprey"
    assert a_or_an("Eurasian Collared-Dove") == "a Eurasian Collared-Dove"
    assert a_or_an("Utah Prairie Dog") == "a Utah Prairie Dog"
    assert a_or_an("Upland Sandpiper") == "an Upland Sandpiper"
    assert a_or_an("Coyote") == "a Coyote"
