package com.collectanimals.app

import org.junit.Assert.assertEquals
import org.junit.Assert.assertTrue
import org.junit.Test
import java.io.File

class PokedexTest {

    @Test
    fun csvHandlesQuotesAndCommas() {
        val rows = Pokedex.parseCsv("a,b\r\n\"x, y\",\"say \"\"hi\"\"\"\n")
        assertEquals(listOf(listOf("a", "b"), listOf("x, y", "say \"hi\"")), rows)
    }

    /** The shared species/ files cover every species and parse the way the app reads them. */
    @Test
    fun everySpeciesHasDetailsAndARange() {
        val dir = File("../../species")
        val dex = Pokedex.parse(File(dir, "details.csv").readText(), File(dir, "ranges.json").readText(),
            File(dir, "california_outline.json").readText())
        val slugs = Pokedex.parseCsv(File(dir, "california_100.csv").readText()).drop(1).map { it[0] }
        assertEquals(100, slugs.size)
        for (slug in slugs) {
            val d = dex.details[slug]
            assertTrue("no details for $slug", d != null && d.size.isNotBlank() && d.weight.isNotBlank() && d.funFact.isNotBlank())
            assertTrue("no range cells for $slug", dex.ranges.sightings(slug) > 0)
            for (c in dex.ranges.cells.getValue(slug)) {
                assertTrue("$slug cell off grid", c[0] in 0 until dex.ranges.cols && c[1] in 0 until dex.ranges.rows)
            }
        }
        // California spans roughly 124.4°W–114.1°W and 32.5°N–42°N.
        val o = dex.outline
        assertTrue(o.minLon in -124.6..-124.2 && o.maxLon in -114.3..-113.9)
        assertTrue(o.minLat in 32.4..32.7 && o.maxLat in 41.9..42.1)
    }
}
