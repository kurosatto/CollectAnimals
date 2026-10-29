package com.captureanimals.app

import android.graphics.Bitmap
import org.json.JSONArray
import org.json.JSONObject
import java.io.File
import java.text.Normalizer

/**
 * "What was it?": after "None of these" the player can name the animal from a big
 * text-only list (species/animal_names.json, bundled, so it works offline). The
 * answer helps train the identifier; it never counts for a badge. Same list and
 * search as the website.
 */
data class AnimalName(val label: String, val name: String, val scientific: String?, val words: List<String>) {
    val isGroup get() = scientific == null
    internal val folded = fold(name)
}

class AnimalNames(val groups: List<AnimalName>, val species: List<AnimalName>, val about: String) {
    /** Every typed word must start a word of the name; names that start with the whole text come first. */
    fun search(query: String, max: Int = 8): List<AnimalName> {
        val words = fold(query).split(' ').filter { it.isNotEmpty() }
        if (words.isEmpty()) return emptyList()
        val whole = fold(query)
        fun fits(e: AnimalName) = words.all { w -> e.words.any { it.startsWith(w) } }
        val starts = mutableListOf<AnimalName>()
        val others = mutableListOf<AnimalName>()
        for (e in species) {
            if (!fits(e)) continue
            if (e.folded.startsWith(whole)) starts += e else others += e
            if (starts.size >= max) break
        }
        return (starts + groups.filter(::fits).take(3) + others).take(max)
    }

    companion object {
        const val GROUP = "group:"

        fun parse(text: String): AnimalNames {
            val o = JSONObject(text)
            val g = o.getJSONArray("groups")
            val groups = List(g.length()) { i ->
                val a = g.getJSONArray(i)
                val name = a.getString(1)
                AnimalName(GROUP + a.getString(0), name, null, fold(name + " " + a.optString(2)).split(' '))
            }
            val n = o.getJSONArray("names")
            val species = List(n.length()) { i ->
                val a = n.getJSONArray(i)
                val name = a.getString(0)
                val sci = a.getString(1)
                AnimalName(sci, name, sci, fold("$name $sci").split(' '))
            }
            return AnimalNames(groups, species, o.optString("about"))
        }
    }
}

/** "a robin", "an owl", "some kind of beetle", as the server words it. */
fun withArticle(name: String): String {
    val lower = name.lowercase()
    if (listOf("some kind of", "some other", "not an", "no animal", "a ", "an ").any { lower.startsWith(it) }) {
        return name.replaceFirstChar { it.lowercase() }
    }
    return (if (lower.first() in "aeiou") "an " else "a ") + name
}

internal fun fold(s: String): String =
    Normalizer.normalize(s, Normalizer.Form.NFD).replace(Regex("\\p{M}+"), "").lowercase()
        .replace(Regex("[^a-z0-9]+"), " ").trim()

/** A name the player picked that hasn't reached the server yet. */
data class PendingName(val id: String, val label: String, val predicted: String?, val state: String?, val photo: File?)

/**
 * Names picked offline (or before signing in) wait here, each with a small copy of
 * the photo, until the player is signed in and online. The photo is sent only if
 * they share photos to teach the game. Capped so it can't fill the phone.
 */
class NameQueue(dir: File) {
    private val root = File(dir, "named").apply { mkdirs() }
    private val index = File(root, "queue.json")

    @Synchronized
    fun all(): List<PendingName> {
        if (!index.exists()) return emptyList()
        val a = runCatching { JSONArray(index.readText()) }.getOrElse { return emptyList() }
        return List(a.length()) { i ->
            val o = a.getJSONObject(i)
            val id = o.getString("id")
            PendingName(id, o.getString("label"), o.optString("predicted").ifEmpty { null },
                o.optString("state").ifEmpty { null }, File(root, "$id.jpg").takeIf { it.exists() })
        }
    }

    @Synchronized
    fun add(label: String, predicted: String?, state: String?, photo: Bitmap?) {
        val items = all().toMutableList()
        while (items.size >= MAX) items.removeAt(0).photo?.delete()
        val id = System.currentTimeMillis().toString(36) + (0..999).random()
        photo?.let { b -> File(root, "$id.jpg").outputStream().use { ImageLoader.thumbnail(b, 512).compress(Bitmap.CompressFormat.JPEG, 85, it) } }
        save(items + PendingName(id, label, predicted, state, null))
    }

    @Synchronized
    fun remove(id: String) {
        File(root, "$id.jpg").delete()
        save(all().filter { it.id != id })
    }

    fun photoBytes(p: PendingName): ByteArray? = p.photo?.takeIf { it.exists() }?.readBytes()

    private fun save(items: List<PendingName>) {
        val a = JSONArray()
        items.forEach { p ->
            a.put(JSONObject().put("id", p.id).put("label", p.label).put("predicted", p.predicted ?: "").put("state", p.state ?: ""))
        }
        index.writeText(a.toString())
    }

    companion object { const val MAX = 50 }
}
