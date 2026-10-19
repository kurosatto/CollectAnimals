package com.captureanimals.app

import android.content.Context
import org.json.JSONObject

/** The extra fun facts per species (species/facts.json, packaged as an asset), told
 *  after the main one in the Field Guide and by animals tapped in the habitat. */
object FunFacts {
    @Volatile private var all: Map<String, List<String>>? = null

    fun of(context: Context, slug: String): List<String> = load(context)[slug].orEmpty()

    private fun load(context: Context): Map<String, List<String>> = all ?: synchronized(this) {
        all ?: runCatching {
            val o = JSONObject(context.assets.open("facts.json").bufferedReader().use { it.readText() })
            o.keys().asSequence().associateWith { k -> o.getJSONArray(k).let { a -> List(a.length()) { a.getString(it) } } }
        }.getOrDefault(emptyMap()).also { all = it }
    }
}
