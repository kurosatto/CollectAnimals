package com.captureanimals.app

import org.json.JSONObject

/** One entry of species/states.json: a state's list and the files describing it. */
data class StateInfo(
    val code: String,
    val name: String,
    val speciesCsv: String,
    /** Per-state text (where to find, fun fact, ...) laid over details.csv; null for the original list. */
    val dexCsv: String?,
    val outline: String,
    val ranges: String,
    val hotspots: String,
    val seasons: String?,
)

object States {
    fun parse(json: String): List<StateInfo> {
        val arr = JSONObject(json).getJSONArray("states")
        return List(arr.length()) { i ->
            val s = arr.getJSONObject(i)
            fun opt(key: String) = if (s.isNull(key)) null else s.optString(key).ifEmpty { null }
            StateInfo(s.getString("code"), s.getString("name"), s.getString("species"), opt("dex"),
                s.getString("outline"), s.getString("ranges"), s.getString("hotspots"), opt("seasons"))
        }
    }

    /** A state's species list (slug, common_name, scientific_name, category, rarity), in list order. */
    fun speciesList(csv: String): List<Species> {
        val rows = FieldGuide.parseCsv(csv)
        val h = rows.first()
        val (slug, name, sci, cat, rar) = listOf("slug", "common_name", "scientific_name", "category", "rarity")
            .map { h.indexOf(it).also { i -> require(i >= 0) { "species list lacks $it" } } }
        return rows.drop(1).filter { it.size > rar }.map { Species(it[slug], it[name], it[sci], it[cat], it[rar]) }
    }
}
