package com.captureanimals.app

import org.junit.Assert.assertEquals
import org.junit.Assert.assertNull
import org.junit.Assert.assertTrue
import org.junit.Test

class HouseholdTest {
    private val base = """
        "classes": ["bobcat", "domestic_cat", "person", "other"], "img_size": 224, "resize": 256,
        "mean": [0.5, 0.5, 0.5], "std": [0.5, 0.5, 0.5], "match_threshold": 0.8, "other_label": "other",
        "species": [{"slug": "bobcat", "common_name": "Bobcat", "scientific_name": "Lynx rufus",
                     "category": "mammal", "rarity": "uncommon"}]
    """

    @Test
    fun parsesPetsExtrasAndPeople() {
        val info = ModelInfo.parse("""{$base,
            "household": [{"slug": "domestic_cat", "common_name": "Cat", "kind": "pet", "note": "Cats hide."}],
            "extras": {"CA": ["allens_hummingbird"]}, "person_label": "person"}""")
        assertEquals("domestic_cat", info.household.single().slug)
        assertEquals(setOf("allens_hummingbird"), info.extras["CA"])
        assertEquals("person", info.personLabel)
        // A state's own list keeps them.
        assertEquals("person", info.withSpecies(emptyList()).personLabel)
        assertTrue(info.household.single().message().startsWith("That's a cat! Pets aren't wild animals"))
    }

    @Test
    fun olderModelFilesHaveNone() {
        val info = ModelInfo.parse("{$base}")
        assertTrue(info.household.isEmpty() && info.extras.isEmpty())
        assertNull(info.personLabel)
    }

    @Test
    fun pestMessageKeepsProperWords() {
        val roach = HouseholdAnimal("german_cockroach", "German cockroach", "pest", "Common in kitchens.")
        assertEquals("That's a German cockroach. It's a pest, not one of the wild animals in the Field Guide. " +
            "Common in kitchens.", roach.message())
    }
}
