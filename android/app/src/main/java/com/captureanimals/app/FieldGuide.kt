package com.captureanimals.app

import org.json.JSONObject

data class SpeciesDetails(
    val size: String,
    val weight: String,
    val funFact: String,
    val whereToFind: String = "",
    val activeTime: String = "",
    val spottingTip: String = "",
)

data class ParkSpecies(val slug: String, val observations: Int)

/** A park from species/hotspots.json (ml/build_hotspots.py). */
data class Park(val id: String, val name: String, val lat: Double, val lon: Double, val blurb: String,
                val species: List<ParkSpecies>)

/** Sighting counts on a lon/lat grid (species/ranges.json, built by ml/build_ranges.py). */
class RangeGrid(val lon0: Double, val lat0: Double, val step: Double, val cols: Int, val rows: Int,
                val cells: Map<String, List<IntArray>>) {
    fun sightings(slug: String) = cells[slug].orEmpty().sumOf { it[2] }
}

/** California outline rings as [lon, lat] pairs (species/california_outline.json). */
class Outline(val rings: List<DoubleArray>) {
    val minLon = rings.minOf { r -> (r.indices step 2).minOf { r[it] } }
    val maxLon = rings.maxOf { r -> (r.indices step 2).maxOf { r[it] } }
    val minLat = rings.minOf { r -> (1 until r.size step 2).minOf { r[it] } }
    val maxLat = rings.maxOf { r -> (1 until r.size step 2).maxOf { r[it] } }
}

class FieldGuide(val details: Map<String, SpeciesDetails>, val ranges: RangeGrid, val outline: Outline,
              val parks: List<Park> = emptyList()) {

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

        fun parse(detailsCsv: String, rangesJson: String, outlineJson: String, hotspotsJson: String? = null): FieldGuide {
            val rows = parseCsv(detailsCsv)
            val header = rows.first()
            val idx = { name: String -> header.indexOf(name).also { require(it >= 0) { "details.csv lacks $name" } } }
            val (slug, size, weight, fact) = listOf(idx("slug"), idx("size"), idx("weight"), idx("fun_fact"))
            // Optional columns, so an older details.csv still loads.
            val where = header.indexOf("where_to_find")
            val active = header.indexOf("active_time")
            val tip = header.indexOf("spotting_tip")
            val details = rows.drop(1).filter { it.size > fact }.associate {
                it[slug] to SpeciesDetails(it[size], it[weight], it[fact], it.getOrElse(where) { "" },
                    it.getOrElse(active) { "" }, it.getOrElse(tip) { "" })
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
            return FieldGuide(details, ranges, Outline(rings), hotspotsJson?.let(::parseParks).orEmpty())
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
