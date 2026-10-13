package com.captureanimals.app

import org.json.JSONObject

data class SpeciesDetails(
    val size: String,
    val weight: String,
    val funFact: String,
    val whereToFind: String = "",
    val activeTime: String = "",
    val spottingTip: String = "",
    /** "none", "caution" or "danger", with how far to stay back and why. */
    val safety: String = "none",
    val safeDistance: String = "",
    val safetyNote: String = "",
)

data class ParkSpecies(val slug: String, val observations: Int)

/** Sightings per month (Jan..Dec) and per local hour (0..23), from species/seasons.json. */
class Season(val months: IntArray, val hours: IntArray) {
    /** Share of timed sightings at night (20:00–05:59), or null with too few to tell. */
    val nightShare: Double? get() {
        val total = hours.sum()
        if (total < 30) return null
        return NIGHT_HOURS.sumOf { hours.getOrElse(it) { 0 } }.toDouble() / total
    }

    /** "Apr–Jun, Sep" style runs of months with at least 60% of the peak, like the website. */
    fun bestMonths(): String {
        val max = months.maxOrNull() ?: 0
        if (max == 0) return ""
        val good = BooleanArray(12) { months[it] >= 0.6 * max }
        if (good.all { it }) return "All year"
        val start = (0 until 12).first { good[it] && !good[(it + 11) % 12] }
        val runs = mutableListOf<IntArray>()
        for (k in 0 until 12) {
            val i = (start + k) % 12
            if (good[i] && !good[(i + 11) % 12]) runs.add(intArrayOf(i, i)) else if (good[i]) runs.last()[1] = i
        }
        return runs.joinToString(", ") { (a, b) -> if (a == b) MONTH_NAMES[a] else "${MONTH_NAMES[a]}–${MONTH_NAMES[b]}" }
    }

    companion object {
        val NIGHT_HOURS = (0..5) + (20..23)
        val MONTH_NAMES = listOf("Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec")
    }
}

/** A park from species/hotspots.json (ml/build_hotspots.py). */
data class Park(val id: String, val name: String, val lat: Double, val lon: Double, val blurb: String,
                val species: List<ParkSpecies>)

/** Sighting counts on a lon/lat grid (species/ranges.json, built by ml/build_ranges.py). */
class RangeGrid(val lon0: Double, val lat0: Double, val step: Double, val cols: Int, val rows: Int,
                val cells: Map<String, List<IntArray>>) {
    fun sightings(slug: String) = cells[slug].orEmpty().sumOf { it[2] }
}

/** A state's outline rings as [lon, lat] pairs (e.g. species/california_outline.json). */
class Outline(val rings: List<DoubleArray>) {
    val minLon = rings.minOf { r -> (r.indices step 2).minOf { r[it] } }
    val maxLon = rings.maxOf { r -> (r.indices step 2).maxOf { r[it] } }
    val minLat = rings.minOf { r -> (1 until r.size step 2).minOf { r[it] } }
    val maxLat = rings.maxOf { r -> (1 until r.size step 2).maxOf { r[it] } }
}

/** One state's Field Guide data. [ranges] is null until that state's sighting map is built. */
class FieldGuide(val details: Map<String, SpeciesDetails>, val ranges: RangeGrid?, val outline: Outline,
              val parks: List<Park> = emptyList(), val seasons: Map<String, Season> = emptyMap()) {

    // People mostly look by day, so compare each species with the average listed one.
    private val avgNightShare: Double? by lazy {
        seasons.values.mapNotNull { it.nightShare }.takeIf { it.isNotEmpty() }?.average()
    }

    /** The website's day/night hint, or null when there isn't enough data. */
    fun dayNight(slug: String): String? {
        val share = seasons[slug]?.nightShare ?: return null
        val r = share / (avgNightShare ?: return null)
        return when {
            r >= 1.8 -> "🌙 Often out at night"
            r >= 1.2 -> "🌗 Day and night"
            r <= 0.5 -> "☀️ Daytime"
            else -> "☀️ Mostly daytime"
        }
    }

    /** Names of the parks with the most sightings of this species (as the web's hotspots_for). */
    fun hotspotsFor(slug: String, limit: Int = 3): List<String> =
        parks.mapNotNull { p -> p.species.firstOrNull { it.slug == slug }?.let { it.observations to p.name } }
            .sortedByDescending { it.first }.take(limit).map { it.second }

    companion object {
        /** Same cutoff as the web (backend/app/dex.py): hotspots.json keeps species with >= 3. */
        const val MIN_HOTSPOT_OBSERVATIONS = 20

        fun parseParks(json: String): List<Park> {
            val arr = JSONObject(json).getJSONArray("parks")
            return List(arr.length()) { i ->
                val p = arr.getJSONObject(i)
                val sp = p.getJSONArray("species")
                Park(p.getString("id"), p.getString("name"), p.getDouble("lat"), p.getDouble("lon"),
                    p.optString("blurb"),
                    List(sp.length()) { j -> sp.getJSONObject(j).let { ParkSpecies(it.getString("slug"), it.getInt("observations")) } }
                        .filter { it.observations >= MIN_HOTSPOT_OBSERVATIONS })
            }
        }

        fun parseSeasons(json: String): Map<String, Season> {
            val sp = JSONObject(json).getJSONObject("species")
            return sp.keys().asSequence().associateWith { k ->
                val e = sp.getJSONObject(k)
                fun ints(key: String) = e.optJSONArray(key)?.let { a -> IntArray(a.length()) { a.getInt(it) } } ?: IntArray(0)
                Season(ints("months"), ints("hours"))
            }
        }

        /**
         * [stateDexCsv] is a state's own text (where to find, fun fact, safety...) laid
         * over details.csv, as the web's dex.details(); details.csv's where-to-find is
         * about California, so it's dropped for a state with its own file.
         */
        fun parse(detailsCsv: String, rangesJson: String?, outlineJson: String, hotspotsJson: String? = null,
                  seasonsJson: String? = null, stateDexCsv: String? = null): FieldGuide {
            fun table(csv: String): Map<String, Map<String, String>> {
                val rows = parseCsv(csv)
                val header = rows.first()
                return rows.drop(1).associate { r -> r[0] to header.indices.associate { header[it] to r.getOrElse(it) { "" } } }
            }
            val base = table(detailsCsv)
            require(base.values.firstOrNull()?.keys?.containsAll(listOf("slug", "size", "weight", "fun_fact")) != false) {
                "details.csv lacks a required column"
            }
            val overlay = stateDexCsv?.let(::table).orEmpty()
            val details = base.mapValues { (slug, row) ->
                val own = overlay[slug].orEmpty()
                // Optional columns, so an older details.csv still loads.
                fun f(key: String) = own[key]?.takeIf { it.isNotBlank() }
                    ?: (if (key == "where_to_find" && stateDexCsv != null) "" else row[key].orEmpty())
                SpeciesDetails(row["size"].orEmpty(), row["weight"].orEmpty(), f("fun_fact"), f("where_to_find"),
                    f("active_time"), f("spotting_tip"), f("safety").ifBlank { "none" }, f("safe_distance"),
                    f("safety_note"))
            }

            val ranges = rangesJson?.let { json ->
                val r = JSONObject(json)
                val g = r.getJSONObject("grid")
                val sp = r.getJSONObject("species")
                val cells = sp.keys().asSequence().associateWith { key ->
                    val arr = sp.getJSONArray(key)
                    List(arr.length()) { i -> arr.getJSONArray(i).let { c -> intArrayOf(c.getInt(0), c.getInt(1), c.getInt(2)) } }
                }
                RangeGrid(g.getDouble("lon0"), g.getDouble("lat0"), g.getDouble("step"),
                    g.getInt("cols"), g.getInt("rows"), cells)
            }

            val ringsJson = JSONObject(outlineJson).getJSONArray("rings")
            val rings = List(ringsJson.length()) { i ->
                val ring = ringsJson.getJSONArray(i)
                DoubleArray(ring.length() * 2) { j -> ring.getJSONArray(j / 2).getDouble(j % 2) }
            }
            return FieldGuide(details, ranges, Outline(rings), hotspotsJson?.let(::parseParks).orEmpty(),
                seasonsJson?.let(::parseSeasons).orEmpty())
        }

        /** Minimal RFC 4180 CSV: quoted fields, doubled quotes, commas/newlines inside quotes. */
        fun parseCsv(text: String): List<List<String>> {
            val rows = mutableListOf<List<String>>()
            var row = mutableListOf<String>()
            val field = StringBuilder()
            var quoted = false
            var i = 0
            val s = text.removePrefix("﻿")
            while (i < s.length) {
                val c = s[i]
                when {
                    quoted && c == '"' && i + 1 < s.length && s[i + 1] == '"' -> { field.append('"'); i++ }
                    c == '"' -> quoted = !quoted
                    !quoted && c == ',' -> { row.add(field.toString()); field.clear() }
                    !quoted && (c == '\n' || c == '\r') -> {
                        if (c == '\r' && i + 1 < s.length && s[i + 1] == '\n') i++
                        row.add(field.toString()); field.clear()
                        if (row.any { it.isNotEmpty() }) rows.add(row)
                        row = mutableListOf()
                    }
                    else -> field.append(c)
                }
                i++
            }
            if (field.isNotEmpty() || row.isNotEmpty()) { row.add(field.toString()); rows.add(row) }
            return rows
        }
    }
}
