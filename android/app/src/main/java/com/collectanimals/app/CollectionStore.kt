package com.collectanimals.app

import android.graphics.Bitmap
import org.json.JSONObject
import java.io.File

data class Badge(val count: Int, val firstCaughtAt: Long, val photo: String?)

/** Badges live on the phone: one JSON file plus a thumbnail of each first catch. */
class CollectionStore(private val dir: File) {
    private val file = File(dir, "collection.json")
    private val photos = File(dir, "badges").apply { mkdirs() }

    fun load(): Map<String, Badge> {
        if (!file.exists()) return emptyMap()
        val o = JSONObject(file.readText())
        return o.keys().asSequence().associateWith { slug ->
            val b = o.getJSONObject(slug)
            Badge(b.getInt("count"), b.getLong("first_caught_at"), b.optString("photo").ifEmpty { null })
        }
    }

    /** Records a catch; returns the updated collection and whether it was a new badge. */
    fun addCatch(current: Map<String, Badge>, slug: String, photo: Bitmap): Pair<Map<String, Badge>, Boolean> {
        val existing = current[slug]
        val badge = if (existing == null) {
            val f = File(photos, "$slug.jpg")
            f.outputStream().use { photo.compress(Bitmap.CompressFormat.JPEG, 85, it) }
            Badge(1, System.currentTimeMillis(), f.absolutePath)
        } else {
            existing.copy(count = existing.count + 1)
        }
        val updated = current + (slug to badge)
        save(updated)
        return updated to (existing == null)
    }

    /** Takes back one catch, e.g. when the player says the model named the wrong animal. */
    fun removeCatch(current: Map<String, Badge>, slug: String): Map<String, Badge> {
        val existing = current[slug] ?: return current
        val updated = if (existing.count > 1) {
            current + (slug to existing.copy(count = existing.count - 1))
        } else {
            existing.photo?.let { File(it).delete() }
            current - slug
        }
        save(updated)
        return updated
    }

    private fun save(collection: Map<String, Badge>) {
        val o = JSONObject()
        for ((slug, b) in collection) {
            o.put(slug, JSONObject().put("count", b.count).put("first_caught_at", b.firstCaughtAt).put("photo", b.photo ?: ""))
        }
        val tmp = File(dir, "collection.json.tmp")
        tmp.writeText(o.toString())
        tmp.renameTo(file)
    }
}
