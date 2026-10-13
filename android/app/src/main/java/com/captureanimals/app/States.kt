package com.captureanimals.app

import org.json.JSONObject

/** A playable state from species/states.json: its own 100 species and Field Guide. */
class StateInfo(val code: String, val name: String, val species: List<Species>, val fieldGuide: FieldGuide)

/**
 * Reads species/states.json (packaged as assets) the way the backend does
 * (backend/app/states.py, dex.py). A species on several lists keeps one slug, so
 * a badge counts in every state that lists it; rarity and name come from each
 * state's CSV, and the state's dex CSV replaces shared Field Guide text that
 * only fits another state.
 */
object States {
    /** [read] returns a packaged file's text, or null when it's missing. Returns (default code, states). */
    fun load(read: (String) -> String?): Pair<String, List<StateInfo>> {
        val o = JSONObject(read("states.json") ?: error("no states.json"))
        val details = read("details.csv") ?: error("no details.csv")
        val arr = o.getJSONArray("states")
        val states = List(arr.length()) { i ->
            val s = arr.getJSONObject(i)
            val name = s.getString("name")
            // Sighting maps are built on a PC with iNaturalist access; until then a state has an empty map.
            val ranges = read(s.getString("ranges"))
                ?: JSONObject().put("grid", s.getJSONObject("grid")).put("species", JSONObject()).toString()
            fun optional(key: String) = s.optString(key).takeIf { it.isNotEmpty() && it != "null" }?.let(read)
            var guide = FieldGuide.parse(details, ranges, read(s.getString("outline")) ?: error("no outline for $name"),
                optional("hotspots"), optional("seasons"), region = name)
            val dex = optional("dex")
            if (dex != null) guide = guide.withDetails(overlay(guide.details, dex))
            StateInfo(s.getString("code"), name, parseSpecies(read(s.getString("species")) ?: error("no list for $name")), guide)
        }
        return o.optString("default", states.first().code) to states
    }

    fun parseSpecies(csv: String): List<Species> {
        val rows = FieldGuide.parseCsv(csv)
        val h = rows.first()
        val col = { n: String -> h.indexOf(n).also { require(it >= 0) { "species CSV lacks $n" } } }
        val (slug, name, sci, cat) = listOf(col("slug"), col("common_name"), col("scientific_name"), col("category"))
        val rarity = col("rarity")
        return rows.drop(1).filter { it.size > rarity }.map { Species(it[slug], it[name], it[sci], it[cat], it[rarity]) }
    }

    /**
     * The state's dex CSV over the shared facts, like dex.details() on the backend.
     * where_to_find in details.csv is about the base state (California), so it's dropped.
     */
    fun overlay(base: Map<String, SpeciesDetails>, dexCsv: String): Map<String, SpeciesDetails> {
        val rows = FieldGuide.parseCsv(dexCsv)
        val h = rows.first()
        val bySlug = rows.drop(1).associateBy { it[h.indexOf("slug")] }
        return base.mapValues { (slug, d) ->
            val row = bySlug[slug]
            fun v(field: String, old: String) = row?.getOrNull(h.indexOf(field))?.ifEmpty { null } ?: old
            d.copy(whereToFind = v("where_to_find", ""), funFact = v("fun_fact", d.funFact),
                activeTime = v("active_time", d.activeTime), spottingTip = v("spotting_tip", d.spottingTip),
                safety = v("safety", d.safety), safeDistance = v("safe_distance", d.safeDistance),
                safetyNote = v("safety_note", d.safetyNote))
        }
    }
}
