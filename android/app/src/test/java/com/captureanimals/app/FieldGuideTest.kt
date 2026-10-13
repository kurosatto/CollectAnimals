package com.captureanimals.app

import org.junit.Assert.assertEquals
import org.junit.Assert.assertTrue
import org.junit.Test
import java.io.File

class FieldGuideTest {

    @Test
    fun csvHandlesQuotesAndCommas() {
        val rows = FieldGuide.parseCsv("a,b\r\n\"x, y\",\"say \"\"hi\"\"\"\n")
        assertEquals(listOf(listOf("a", "b"), listOf("x, y", "say \"hi\"")), rows)
    }

    /** The shared species/ files cover every species and parse the way the app reads them. */
    @Test
    fun everySpeciesHasDetailsAndARange() {
        val dir = File("../../species")
        val dex = FieldGuide.parse(File(dir, "details.csv").readText(), File(dir, "ranges.json").readText(),
            File(dir, "california_outline.json").readText())
        val slugs = FieldGuide.parseCsv(File(dir, "california_100.csv").readText()).drop(1).map { it[0] }
        assertEquals(100, slugs.size)
        val ranges = dex.ranges!!
        for (slug in slugs) {
            val d = dex.details[slug]
            assertTrue("no details for $slug", d != null && d.size.isNotBlank() && d.weight.isNotBlank() &&
                d.funFact.isNotBlank() && d.whereToFind.isNotBlank())
            assertTrue("no range cells for $slug", ranges.sightings(slug) > 0)
            for (c in ranges.cells.getValue(slug)) {
                assertTrue("$slug cell off grid", c[0] in 0 until ranges.cols && c[1] in 0 until ranges.rows)
            }
        }
        // California spans roughly 124.4°W–114.1°W and 32.5°N–42°N.
        val o = dex.outline
        assertTrue(o.minLon in -124.6..-124.2 && o.maxLon in -114.3..-113.9)
        assertTrue(o.minLat in 32.4..32.7 && o.maxLat in 41.9..42.1)
    }

    /** Hotspots use the web's cutoff and give the expected top parks. */
    @Test
    fun hotspotsMatchTheWeb() {
        val dir = File("../../species")
        val dex = FieldGuide.parse(File(dir, "details.csv").readText(), File(dir, "ranges.json").readText(),
            File(dir, "california_outline.json").readText(), File(dir, "hotspots.json").readText())
        assertTrue(dex.parks.size >= 20)
        assertTrue(dex.parks.all { p -> p.species.all { it.observations >= FieldGuide.MIN_HOTSPOT_OBSERVATIONS } })
        assertEquals("Pinnacles National Park", dex.hotspotsFor("california_condor").first())
        assertTrue("Elkhorn Slough & Moss Landing" in dex.hotspotsFor("sea_otter"))
        val d = dex.details.getValue("california_condor")
        assertTrue(d.activeTime.isNotBlank() && d.spottingTip.isNotBlank())
    }

    @Test
    fun seasonsMatchTheWeb() {
        val dir = File("../../species")
        val dex = FieldGuide.parse(File(dir, "details.csv").readText(), File(dir, "ranges.json").readText(),
            File(dir, "california_outline.json").readText(), null, File(dir, "seasons.json").readText())
        assertEquals(100, dex.seasons.size)
        assertEquals("🌙 Often out at night", dex.dayNight("barn_owl"))
        assertEquals("🌙 Often out at night", dex.dayNight("great_horned_owl"))
        assertTrue(dex.dayNight("western_fence_lizard")!!.startsWith("☀️"))
        // A spring-and-summer animal, and the wrap from December into January.
        assertEquals("Apr–Jun", Season(intArrayOf(1, 1, 1, 9, 10, 8, 2, 1, 1, 1, 1, 1), IntArray(0)).bestMonths())
        assertEquals("Dec–Jan", Season(intArrayOf(10, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 9), IntArray(0)).bestMonths())
        assertEquals("All year", Season(IntArray(12) { 5 }, IntArray(0)).bestMonths())
    }

    @Test
    fun fieldGuideOrderIsRarityThenKind() {
        val species = listOf(
            Species("condor", "Condor", "", "bird", "legendary"),
            Species("quail", "Quail", "", "bird", "common"),
            Species("coyote", "Coyote", "", "mammal", "common"),
            Species("skunk", "Skunk", "", "mammal", "uncommon"))
        val info = ModelInfo(emptyList(), 224, 256, FloatArray(3), FloatArray(3), 0.7f, "other", species)
        assertEquals(listOf("coyote", "quail", "skunk", "condor"), info.dexOrder.map { it.slug })
        assertEquals(4, info.dexNumber("condor"))
    }

    /** Every state in states.json has a full list with details and sprites, and its own text wins. */
    @Test
    fun everyStateListIsComplete() {
        val dir = File("../../species")
        val states = States.parse(File(dir, "states.json").readText())
        assertEquals(listOf("CA", "NC"), states.map { it.code })
        for (st in states) {
            val list = States.speciesList(File(dir, st.speciesCsv).readText())
            assertEquals(st.code, 100, list.size)
            val guide = FieldGuide.parse(File(dir, "details.csv").readText(), null, File(dir, st.outline).readText(),
                stateDexCsv = st.dexCsv?.let { File(dir, it).readText() })
            for (s in list) {
                val d = guide.details[s.slug]
                assertTrue("${st.code}: no details for ${s.slug}", d != null && d.size.isNotBlank() && d.funFact.isNotBlank())
                assertTrue("${st.code}: no sprite for ${s.slug}", File(dir, "sprites/${s.slug}.png").exists() &&
                    File(dir, "sprites/${s.slug}_silhouette.png").exists())
            }
        }
        val nc = states.single { it.code == "NC" }
        val ncGuide = FieldGuide.parse(File(dir, "details.csv").readText(), null, File(dir, nc.outline).readText(),
            stateDexCsv = File(dir, nc.dexCsv!!).readText())
        assertTrue("Cataloochee" in ncGuide.details.getValue("elk").whereToFind)
        assertEquals("danger", ncGuide.details.getValue("american_alligator").safety)
        assertTrue(ncGuide.outline.minLon in -84.4..-84.2)
    }

    /** As the backend: a North Carolina photo can't be split with a California-only species. */
    @Test
    fun restrictKeepsOnlyTheStatesSpecies() {
        val preds = listOf(Prediction("western_bluebird", 0.5f), Prediction("eastern_bluebird", 0.4f),
            Prediction("other", 0.1f))
        val r = restrict(preds, setOf("eastern_bluebird", "other"))
        assertEquals(listOf("eastern_bluebird", "other"), r.map { it.label })
        assertEquals(0.8f, r[0].probability, 1e-4f)
        assertEquals(listOf(Prediction("other", 1f)), restrict(preds, setOf("coyote")))
    }
}
