package com.captureanimals.app

import org.junit.Assert.assertEquals
import org.junit.Assert.assertTrue
import org.junit.Test
import java.io.File

class StatesTest {
    private val dir = File("../../species")
    private fun load() = States.load { name -> File(dir, name).takeIf { it.exists() }?.readText() }

    /** Every state in species/states.json loads; California and North Carolina have 100 species with Field Guide text for all. */
    @Test
    fun everyStateLoads() {
        val (default, states) = load()
        assertEquals("CA", default)
        assertTrue(states.map { it.code }.containsAll(listOf("CA", "NC")))
        for (st in states) assertTrue(st.code, st.species.isNotEmpty() && st.fieldGuide.region == st.name)
        for (st in states.filter { it.code in setOf("CA", "NC") }) {
            assertEquals(st.name, 100, st.species.size)
            assertEquals(st.name, st.fieldGuide.region)
            for (s in st.species) {
                val d = st.fieldGuide.details[s.slug]
                assertTrue("${st.code}: no details for ${s.slug}", d != null && d.size.isNotBlank() && d.funFact.isNotBlank())
                assertTrue("${st.code}: no where_to_find for ${s.slug}", d!!.whereToFind.isNotBlank())
            }
        }
    }

    /** NC text replaces the California facts, as on the website. */
    @Test
    fun stateTextOverridesSharedFacts() {
        val (_, states) = load()
        val ca = states.first { it.code == "CA" }.fieldGuide.details.getValue("elk")
        val nc = states.first { it.code == "NC" }.fieldGuide.details.getValue("elk")
        assertTrue("Tule" in ca.funFact)
        assertTrue("Cataloochee" in nc.whereToFind && "Cataloochee" in nc.funFact)
        assertTrue(nc.safety == "caution" || nc.safety == "danger")
    }

    @Test
    fun restrictKeepsOnlyTheStatesAnimals() {
        val preds = listOf(Prediction("sea_otter", 0.6f), Prediction("raccoon", 0.3f), Prediction("other", 0.1f))
        val out = Prediction.restrict(preds, setOf("raccoon", "other"), "other")
        assertEquals(listOf("raccoon", "other"), out.map { it.label })
        assertEquals(0.75f, out[0].probability, 1e-6f)
        assertEquals(listOf(Prediction("other", 1f)), Prediction.restrict(preds, setOf("elk"), "other"))
    }

    /** A state added with only its species list and bounds (no maps yet) still loads. */
    @Test
    fun stateWithoutMapFilesLoads() {
        val files = mapOf(
            "states.json" to """{"default":"TL","states":[{"code":"TL","name":"Testland","species":"tl.csv",
                "bounds":{"west":-100.0,"east":-95.0,"south":40.0,"north":43.0}}]}""",
            "details.csv" to File(dir, "details.csv").readText(),
            "tl.csv" to "slug,common_name,scientific_name,category,rarity\ncoyote,Coyote,Canis latrans,mammal,common\n")
        val (default, states) = States.load { files[it] }
        assertEquals("TL", default)
        val tl = states.single()
        assertEquals(listOf("coyote"), tl.species.map { it.slug })
        assertEquals(-100.0, tl.fieldGuide.outline.minLon, 1e-9)
        assertEquals(43.0, tl.fieldGuide.outline.maxLat, 1e-9)
        assertEquals(20, tl.fieldGuide.ranges.cols)
        assertTrue(tl.fieldGuide.parks.isEmpty())
    }

    @Test
    fun stateTilesAndList() {
        val names = mapOf("CA" to "California", "NC" to "North Carolina", "SC" to "South Carolina", "OR" to "Oregon")
        val states = names.map { (c, n) -> StateInfo(c, n, emptyList()) { error("not needed") } }
        // First launch: every state A to Z.
        assertEquals(listOf("CA", "NC", "OR", "SC"), StateList.alphabetical(states).map { it.code })
        // The state screen: only unlocked states, in states.json order.
        assertEquals(listOf("NC", "OR"), StateList.tiles(states, setOf("OR", "NC")).map { it.code })
    }

    @Test
    fun stateAtAPoint() {
        // A real outline (a triangle) beats an overlapping bounding box; of two boxes the smaller wins.
        val tri = listOf(doubleArrayOf(-120.0, 35.0, -110.0, 35.0, -115.0, 45.0))
        val states = listOf(
            StateInfo("AA", "Outlined", emptyList(), Box(-120.0, -110.0, 35.0, 45.0), { tri }) { error("not needed") },
            StateInfo("BB", "Big box", emptyList(), Box(-125.0, -100.0, 30.0, 50.0)) { error("not needed") },
            StateInfo("CC", "Small box", emptyList(), Box(-105.0, -100.0, 40.0, 45.0)) { error("not needed") })
        assertEquals("AA", States.stateAt(states, 38.0, -115.0)?.code)     // inside the triangle
        assertEquals("BB", States.stateAt(states, 44.0, -119.0)?.code)     // in AA's box but not its outline
        assertEquals("CC", States.stateAt(states, 42.0, -102.0)?.code)
        assertEquals(null, States.stateAt(states, 10.0, 0.0))
    }

    @Test
    fun spritesWithoutArtUseThePlaceholder() {
        val files = setOf("coyote.png", "coyote_silhouette.png", "placeholder.png", "placeholder_silhouette.png")
        assertEquals("sprites/coyote.png", spriteAsset("sprites/coyote.png", files))
        assertEquals("sprites/placeholder.png", spriteAsset("sprites/plains_vole.png", files))
        assertEquals("sprites/placeholder_silhouette.png", spriteAsset("sprites/plains_vole_silhouette.png", files))
        assertEquals("sprites/anim/plains_vole.png", spriteAsset("sprites/anim/plains_vole.png", files))
    }
}
