package com.captureanimals.app

import org.json.JSONObject

/**
 * A playable state from species/states.json: its own 100 species and Field Guide.
 * The Field Guide (sighting map, parks, seasons) is read the first time it's needed,
 * so 50 states don't all load at start-up.
 */
class StateInfo(val code: String, val name: String, val species: List<Species>, val bounds: Box? = null,
                outline: () -> List<DoubleArray> = { emptyList() }, guide: () -> FieldGuide) {
    val fieldGuide: FieldGuide by lazy(guide)
    // The real outline's rings ([lon, lat, lon, lat, ...]); empty until the state has one.
    val outlineRings: List<DoubleArray> by lazy(outline)
}

/** A state's bounding box in degrees. */
class Box(val west: Double, val east: Double, val south: Double, val north: Double) {
    fun contains(lat: Double, lon: Double, margin: Double = 0.0) =
        lat in south - margin..north + margin && lon in west - margin..east + margin
    val area get() = (north - south) * (east - west)
}

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
            fun optional(key: String) = s.optString(key).takeIf { it.isNotEmpty() && it != "null" }?.let(read)
            val box = s.getJSONObject("bounds").let { b ->
                Box(b.getDouble("west"), b.getDouble("east"), b.getDouble("south"), b.getDouble("north"))
            }
            StateInfo(s.getString("code"), name, parseSpecies(read(s.getString("species")) ?: error("no list for $name")),
                box, { optional("outline")?.let { parseRings(it) }.orEmpty() }) {
                // Sighting maps and outlines are built on a PC with iNaturalist access; until then
                // a state has an empty sighting map and its bounding box as the outline.
                val bounds = s.getJSONObject("bounds")
                val ranges = optional("ranges")
                    ?: JSONObject().put("grid", s.optJSONObject("grid") ?: gridFor(bounds)).put("species", JSONObject()).toString()
                var guide = FieldGuide.parse(details, ranges, optional("outline") ?: boxOutline(bounds),
                    optional("hotspots"), optional("seasons"), region = name)
                val dex = optional("dex")
                if (dex != null) guide = guide.withDetails(overlay(guide.details, dex))
                guide
            }
        }
        return o.optString("default", states.first().code) to states
    }

    fun parseRings(outlineJson: String): List<DoubleArray> {
        val ringsJson = JSONObject(outlineJson).getJSONArray("rings")
        return List(ringsJson.length()) { i ->
            val ring = ringsJson.getJSONArray(i)
            DoubleArray(ring.length() * 2) { j -> ring.getJSONArray(j / 2).getDouble(j % 2) }
        }
    }

    // Same as the backend's places.state_at: how far outside a box still counts
    // (degrees), and how far off a coarse outline a beach or island still counts (km).
    private const val MARGIN = 0.3
    private const val COAST_KM = 5.0

    /**
     * The state a point is in, or null. A real outline beats a bounding box (boxes
     * of neighbouring states overlap), and of two boxes the smaller wins.
     */
    fun stateAt(states: List<StateInfo>, lat: Double, lon: Double): StateInfo? =
        states.mapNotNull { st -> fit(st, lat, lon)?.let { Triple(it, st.bounds?.area ?: 0.0, st) } }
            .minWithOrNull(compareBy({ it.first }, { it.second }))?.third

    /** 0 inside the outline, 1 just off its edge, 2 inside the box of a state with no outline, 3 just outside it. */
    private fun fit(st: StateInfo, lat: Double, lon: Double): Int? {
        val b = st.bounds ?: return null
        if (!b.contains(lat, lon, MARGIN)) return null
        val rings = st.outlineRings
        if (rings.isEmpty()) return if (b.contains(lat, lon)) 2 else 3
        var inside = false
        for (r in rings) {
            val n = r.size / 2
            for (i in 0 until n) {
                val (x1, y1) = r[2 * i] to r[2 * i + 1]
                val (x2, y2) = r[2 * ((i + 1) % n)] to r[2 * ((i + 1) % n) + 1]
                if ((y1 > lat) != (y2 > lat) && lon < x1 + (lat - y1) * (x2 - x1) / (y2 - y1)) inside = !inside
            }
        }
        if (inside) return 0
        val kx = 111.32 * Math.cos(Math.toRadians(lat))
        for (r in rings) {
            val n = r.size / 2
            for (i in 0 until n) {
                val ax = (r[2 * i] - lon) * kx; val ay = (r[2 * i + 1] - lat) * 110.57
                val bx = (r[2 * ((i + 1) % n)] - lon) * kx; val by = (r[2 * ((i + 1) % n) + 1] - lat) * 110.57
                val dx = bx - ax; val dy = by - ay
                val t = if (dx != 0.0 || dy != 0.0) (-(ax * dx + ay * dy) / (dx * dx + dy * dy)).coerceIn(0.0, 1.0) else 0.0
                if (Math.hypot(ax + t * dx, ay + t * dy) <= COAST_KM) return 1
            }
        }
        return null
    }

    /** A quarter-degree sighting grid over the state's bounds, for a state with no ranges file yet. */
    fun gridFor(b: JSONObject): JSONObject {
        val step = 0.25
        return JSONObject().put("lon0", b.getDouble("west")).put("lat0", b.getDouble("south")).put("step", step)
            .put("cols", Math.ceil((b.getDouble("east") - b.getDouble("west")) / step).toInt())
            .put("rows", Math.ceil((b.getDouble("north") - b.getDouble("south")) / step).toInt())
    }

    /** The state's bounding box as its outline, until the real outline is added. */
    fun boxOutline(b: JSONObject): String {
        val (w, e, so, n) = listOf("west", "east", "south", "north").map { b.getDouble(it) }
        return """{"rings":[[[$w,$so],[$e,$so],[$e,$n],[$w,$n],[$w,$so]]]}"""
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
