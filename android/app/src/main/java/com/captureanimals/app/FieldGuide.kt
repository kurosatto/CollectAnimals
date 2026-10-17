package com.captureanimals.app

import org.json.JSONObject

data class SpeciesDetails(
    val size: String,
    val weight: String,
    val funFact: String,
    val whereToFind: String = "",
    val activeTime: String = "",
    val spottingTip: String = "",
    // "caution" or "danger" for animals to watch from a distance (details.csv, as on the web).
    val safety: String = "",
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

    /** Could it turn up in this month (1-12)? Like the website: at least a quarter
     *  of its best month's sightings, or true with no data to rule it out. */
    fun likelyIn(month: Int): Boolean {
        val max = months.maxOrNull() ?: 0
        return max == 0 || months.getOrElse(month - 1) { 0 } >= IN_SEASON_SHARE * max
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
        const val IN_SEASON_SHARE = 0.25
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

/** A state outline's rings as [lon, lat] pairs (species/<state>_outline.json). */
class Outline(val rings: List<DoubleArray>) {
    val minLon = rings.minOf { r -> (r.indices step 2).minOf { r[it] } }
    val maxLon = rings.maxOf { r -> (r.indices step 2).maxOf { r[it] } }
    val minLat = rings.minOf { r -> (1 until r.size step 2).minOf { r[it] } }
    val maxLat = rings.maxOf { r -> (1 until r.size step 2).maxOf { r[it] } }
}

/** One state's Field Guide data; [region] is the state's name. */
class FieldGuide(val details: Map<String, SpeciesDetails>, val ranges: RangeGrid, val outline: Outline,
              val parks: List<Park> = emptyList(), val seasons: Map<String, Season> = emptyMap(),
              val region: String = "California") {

    fun withDetails(d: Map<String, SpeciesDetails>) = FieldGuide(d, ranges, outline, parks, seasons, region)

    // People mostly look by day, so compare each species with the average listed one.
    private val avgNightShare: Double? by lazy {
        seasons.values.mapNotNull { it.nightShare }.takeIf { it.isNotEmpty() }?.average()
    }

    /** Whether the species may be out this month (1-12); true without season data. */
    fun inSeason(slug: String, month: Int): Boolean = seasons[slug]?.likelyIn(month) ?: true

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

    /** When the animal is up and about for the habitat scene: "day", "night" or "any",
     *  as the website's dex.activity(): from active_time, else from night sightings. */
    fun activity(slug: String): String {
        val text = details[slug]?.activeTime.orEmpty().lowercase().split(";").first().trim()
        if (text.isNotEmpty()) {
            if (text.startsWith("night") || text.startsWith("dusk")) return "night"
            if (listOf("night", "dawn", "dusk", "all day", "any time").any { it in text }) return "any"
            return "day"
        }
        val share = seasons[slug]?.nightShare
        val avg = avgNightShare
        val ratio = if (share != null && avg != null && avg > 0) share / avg else null
        return if (ratio != null && ratio >= 3) "night" else "day"
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

        fun parse(detailsCsv: String, rangesJson: String, outlineJson: String, hotspotsJson: String? = null,
                  seasonsJson: String? = null, region: String = "California"): FieldGuide {
            val rows = parseCsv(detailsCsv)
            val header = rows.first()
            val idx = { name: String -> header.indexOf(name).also { require(it >= 0) { "details.csv lacks $name" } } }
            val (slug, size, weight, fact) = listOf(idx("slug"), idx("size"), idx("weight"), idx("fun_fact"))
            // Optional columns, so an older details.csv still loads.
            val where = header.indexOf("where_to_find")
            val active = header.indexOf("active_time")
            val tip = header.indexOf("spotting_tip")
            val safety = header.indexOf("safety")
            val distance = header.indexOf("safe_distance")
            val note = header.indexOf("safety_note")
            val details = rows.drop(1).filter { it.size > fact }.associate {
                it[slug] to SpeciesDetails(it[size], it[weight], it[fact], it.getOrElse(where) { "" },
                    it.getOrElse(active) { "" }, it.getOrElse(tip) { "" }, it.getOrElse(safety) { "" },
                    it.getOrElse(distance) { "" }, it.getOrElse(note) { "" })
            }

            val r = JSONObject(rangesJson)
            val g = r.getJSONObject("grid")
            val sp = r.getJSONObject("species")
            val cells = sp.keys().asSequence().associateWith { key ->
                val arr = sp.getJSONArray(key)
                List(arr.length()) { i -> arr.getJSONArray(i).let { c -> intArrayOf(c.getInt(0), c.getInt(1), c.getInt(2)) } }
            }
            val ranges = RangeGrid(g.getDouble("lon0"), g.getDouble("lat0"), g.getDouble("step"),
                g.getInt("cols"), g.getInt("rows"), cells)

            val ringsJson = JSONObject(outlineJson).getJSONArray("rings")
            val rings = List(ringsJson.length()) { i ->
                val ring = ringsJson.getJSONArray(i)
                DoubleArray(ring.length() * 2) { j -> ring.getJSONArray(j / 2).getDouble(j % 2) }
            }
            return FieldGuide(details, ranges, Outline(rings), hotspotsJson?.let(::parseParks).orEmpty(),
                seasonsJson?.let(::parseSeasons).orEmpty(), region)
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
