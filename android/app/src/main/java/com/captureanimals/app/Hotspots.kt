package com.captureanimals.app

import kotlin.math.asin
import kotlin.math.cos
import kotlin.math.roundToInt
import kotlin.math.sin
import kotlin.math.sqrt

/** A park in the Hotspots list: how many of its animals are still uncaptured and how far it is. */
data class RankedPark(val park: Park, val fresh: Int, val miles: Double?, val score: Double)

/** How many parks the Hotspots list shows before "Show all parks" (same as the web). */
const val HOTSPOTS_TOP = 8

/**
 * Parks most worth a trip, best first, matching the web's rankHotspots: the most
 * animals not captured yet, weighed against distance when [me] is known. A park
 * twice as far needs about twice as many new animals once past ~40 miles.
 */
fun rankParks(parks: List<Park>, captured: Set<String>, me: Pair<Double, Double>?): List<RankedPark> =
    parks.map { p ->
        val fresh = p.species.count { it.slug !in captured }
        val miles = me?.let { milesBetween(it.first, it.second, p.lat, p.lon) }
        RankedPark(p, fresh, miles, if (miles == null) fresh.toDouble() else fresh / (1 + miles / 40))
    }.sortedWith(compareByDescending<RankedPark> { it.score }.thenByDescending { it.park.species.size })

fun milesBetween(lat1: Double, lon1: Double, lat2: Double, lon2: Double): Double {
    val r = Math.PI / 180
    val dLat = (lat2 - lat1) * r
    val dLon = (lon2 - lon1) * r
    val h = sin(dLat / 2).let { it * it } + cos(lat1 * r) * cos(lat2 * r) * sin(dLon / 2).let { it * it }
    return 3958.8 * 2 * asin(sqrt(h))
}

fun formatMiles(m: Double): String = when {
    m < 1 -> "under 1 mi"
    m < 10 -> "${(m * 10).roundToInt() / 10.0} mi"
    else -> "${m.roundToInt()} mi"
}
