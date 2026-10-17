package com.captureanimals.app

import org.junit.Assert.assertEquals
import org.junit.Assert.assertNull
import org.junit.Test

class HotspotsTest {
    private fun park(id: String, lat: Double, lon: Double, vararg slugs: String) =
        Park(id, id, lat, lon, "", slugs.map { ParkSpecies(it, 50) })

    private val near = park("near", 37.80, -122.40, "a", "b", "c")
    private val far = park("far", 34.05, -118.25, "a", "b", "c", "d", "e", "f")

    @Test fun withoutLocationMostNewAnimalsFirst() {
        val ranked = rankParks(listOf(near, far), captured = setOf("d"), me = null)
        assertEquals(listOf("far", "near"), ranked.map { it.park.id })
        assertEquals(5, ranked[0].fresh)
        assertNull(ranked[0].miles)
    }

    @Test fun nearbyParkBeatsFarOneWithAFewMore() {
        val ranked = rankParks(listOf(far, near), captured = emptySet(), me = 37.78 to -122.42)
        assertEquals(listOf("near", "far"), ranked.map { it.park.id })
        assertEquals(3, ranked[0].fresh)
    }

    @Test fun capturedAnimalsDontCount() {
        val ranked = rankParks(listOf(near), captured = setOf("a", "b", "c"), me = null)
        assertEquals(0, ranked[0].fresh)
    }

    @Test fun distances() {
        // San Francisco to Los Angeles is about 347 miles as the crow flies.
        assertEquals(347.0, milesBetween(37.7749, -122.4194, 34.0522, -118.2437), 3.0)
        assertEquals("under 1 mi", formatMiles(0.4))
        assertEquals("3.2 mi", formatMiles(3.24))
        assertEquals("27 mi", formatMiles(26.6))
    }
}
