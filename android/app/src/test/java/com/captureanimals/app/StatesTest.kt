package com.captureanimals.app

import org.junit.Assert.assertEquals
import org.junit.Assert.assertTrue
import org.junit.Test
import java.io.File

class StatesTest {
    private val dir = File("../../species")
    private fun load() = States.load { name -> File(dir, name).takeIf { it.exists() }?.readText() }

    /** Both states load from species/states.json, each with 100 species and Field Guide text for all of them. */
    @Test
    fun everyStateLoads() {
        val (default, states) = load()
        assertEquals("CA", default)
        assertEquals(listOf("CA", "NC"), states.map { it.code })
        for (st in states) {
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
}
