package com.captureanimals.app

import android.graphics.Bitmap
import org.json.JSONObject
import java.io.File

data class Badge(val count: Int, val firstCaughtAt: Long, val photo: String?)

/**
 * Badges live on the phone: one JSON file per state plus a thumbnail of each first
 * catch. Captures count only in the state they were made in, as on the website.
 */
class CollectionStore(private val dir: File) {
    private val photos = File(dir, "badges").apply { mkdirs() }

    private fun file(state: String) = File(dir, "collection-$state.json")

    /** Catches from before they were kept per state belong to the player's [home] state. */
    fun migrate(home: String) {
        val legacy = File(dir, "collection.json")
        if (legacy.exists() && !file(home).exists()) legacy.renameTo(file(home))
    }

    fun load(state: String): Map<String, Badge> {
        val file = file(state)
        if (!file.exists()) return emptyMap()
        val o = JSONObject(file.readText())
        return o.keys().asSequence().associateWith { slug ->
            val b = o.getJSONObject(slug)
            Badge(b.getInt("count"), b.getLong("first_caught_at"), b.optString("photo").ifEmpty { null })
        }
    }

    /** Records a catch; returns the updated collection and whether it was a new badge. */
    fun addCatch(state: String, current: Map<String, Badge>, slug: String, photo: Bitmap): Pair<Map<String, Badge>, Boolean> {
        val existing = current[slug]
        val badge = if (existing == null) {
            Badge(1, System.currentTimeMillis(), savePhoto("$state-$slug", photo))
        } else {
            existing.copy(count = existing.count + 1)
        }
        val updated = current + (slug to badge)
        save(state, updated)
        return updated to (existing == null)
    }

    /** Saves the badge photo; returns its path, or null if the bitmap couldn't be encoded. */
    private fun savePhoto(name: String, photo: Bitmap): String? {
        // JPEG needs a plain 8-bit software bitmap; picker photos can arrive as
        // hardware or wide-color (F16) bitmaps, which compress() rejects.
        val bmp = if (photo.config == Bitmap.Config.ARGB_8888) photo else photo.copy(Bitmap.Config.ARGB_8888, false)
        val f = File(photos, "$name.jpg")
        val tmp = File(photos, "$name.jpg.tmp")
        val ok = bmp != null && tmp.outputStream().use { bmp.compress(Bitmap.CompressFormat.JPEG, 85, it) }
        if (!ok || tmp.length() == 0L) {
            android.util.Log.w("CollectionStore", "could not save photo for $name (config=${photo.config})")
            tmp.delete()
            return null
        }
        tmp.renameTo(f)
        return f.absolutePath
    }

    /** Takes back one catch, e.g. when the player says the model named the wrong animal. */
    fun removeCatch(state: String, current: Map<String, Badge>, slug: String): Map<String, Badge> {
        val existing = current[slug] ?: return current
        val updated = if (existing.count > 1) {
            current + (slug to existing.copy(count = existing.count - 1))
        } else {
            existing.photo?.let { File(it).delete() }
            current - slug
        }
        save(state, updated)
        return updated
    }

    /** Deletes the badge photo and un-catches the animal entirely. */
    fun forget(state: String, current: Map<String, Badge>, slug: String): Map<String, Badge> {
        val existing = current[slug] ?: return current
        existing.photo?.let { File(it).delete() }
        val updated = current - slug
        save(state, updated)
        return updated
    }

    private fun save(state: String, collection: Map<String, Badge>) {
        val o = JSONObject()
        for ((slug, b) in collection) {
            o.put(slug, JSONObject().put("count", b.count).put("first_caught_at", b.firstCaughtAt).put("photo", b.photo ?: ""))
        }
        val tmp = File(dir, "collection-$state.json.tmp")
        tmp.writeText(o.toString())
        tmp.renameTo(file(state))
    }
}
