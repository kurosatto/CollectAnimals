package com.captureanimals.app

import org.json.JSONObject
import org.junit.Assert.assertEquals
import org.junit.Assert.assertNull
import org.junit.Test
import java.io.File

class ProgressTest {
    private val dir = File("../../species")

    /** The app's sets match the website's (goals.sets_for): same sets and sizes per state. */
    @Test
    fun setsMatchTheWebsite() {
        val catalog = SetCatalog.parse(File(dir, "sets.json").readText())
        val (_, states) = States.load { name -> File(dir, name).takeIf { it.exists() }?.readText() }
        val sets = states.associate { st ->
            st.code to catalog.forState(st.code, st.species.map { it.slug }.toSet()) { st.fieldGuide.details[it]?.safety }
                .map { it.id to it.slugs.size }
        }
        assertEquals(listOf("state_symbols" to 3, "backyard" to 10, "tide_pools" to 13, "beach" to 4, "pond" to 9,
            "sky_hunters" to 10, "wings" to 5, "night_shift" to 8), sets["CA"])
        assertEquals(listOf("state_symbols" to 10, "backyard" to 11, "beach" to 9, "pond" to 10, "sky_hunters" to 7,
            "wings" to 5, "night_shift" to 11), sets["NC"])
    }

    @Test
    fun parsesScoreAndBond() {
        val score = PhotoScore.parse(JSONObject("""{"total": 1250, "stars": 4,
            "parts": [{"label": "Photo", "points": 1000}, {"label": "New animal", "points": 250}]}"""))!!
        assertEquals(PhotoScore(1250, 4, listOf("Photo" to 1000, "New animal" to 250)), score)
        assertNull(PhotoScore.parse(null))
        assertEquals("★★★★☆", stars(4))

        val bond = Bond.parse(JSONObject("""{"species": {"number": 3, "slug": "coyote", "common_name": "Coyote",
              "scientific_name": "Canis latrans", "category": "mammal", "rarity": "common"},
              "level": 2, "max_level": 6, "title": "Neighbor",
              "notes": [{"id": "met", "title": "First meeting", "hint": "Capture it", "progress": 1, "goal": 1, "done": true}]}"""))
        assertEquals("coyote", bond.slug)
        assertEquals(2, bond.level)
        assertEquals(BondNote("First meeting", "Capture it", 1, 1, true), bond.notes.single())
    }
}
