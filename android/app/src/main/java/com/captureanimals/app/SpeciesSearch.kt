package com.captureanimals.app

/**
 * "None of these" > search: the state's animals whose common or scientific name
 * contains [query] (at least 2 letters), common-name prefix matches first, as on the website.
 */
fun searchSpecies(species: List<Species>, query: String, limit: Int = 10): List<Species> {
    val q = query.trim().lowercase()
    if (q.length < 2) return emptyList()
    return species
        .filter { q in it.commonName.lowercase() || q in it.scientificName.lowercase() }
        .sortedBy { if (it.commonName.lowercase().startsWith(q)) 0 else 1 }
        .take(limit)
}
