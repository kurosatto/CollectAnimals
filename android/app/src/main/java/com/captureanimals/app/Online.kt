package com.captureanimals.app

import android.content.Context
import android.content.SharedPreferences
import android.graphics.Bitmap
import android.graphics.BitmapFactory
import android.util.LruCache
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import org.json.JSONArray
import org.json.JSONObject
import java.io.ByteArrayOutputStream
import java.net.HttpURLConnection
import java.net.URL
import java.net.URLEncoder
import java.time.OffsetDateTime
import java.time.LocalDateTime
import java.time.ZoneOffset

/**
 * The game server (backend/) for accounts, friends, the news feed and likes: the
 * same API the website uses. Playing offline needs none of this.
 *
 * The server runs on the developer's PC behind a tunnel whose address changes on
 * every restart, so the app looks up the current one in server.json on the repo's
 * `server-url` branch (scripts/publish_server_url.py updates it). A typed-in address
 * wins over the lookup.
 */
object Online {
    const val SERVER_JSON = "https://raw.githubusercontent.com/kurosatto/CollectAnimals/server-url/server.json"

    private lateinit var prefs: SharedPreferences
    var base: String? = null
        private set
    var token: String? = null
        private set
    val signedIn get() = token != null && base != null

    fun init(context: Context) {
        if (::prefs.isInitialized) return
        prefs = context.getSharedPreferences("online", Context.MODE_PRIVATE)
        base = prefs.getString("manual_url", null) ?: prefs.getString("looked_up_url", null)
        token = prefs.getString("token", null)
    }

    val manualUrl: String? get() = prefs.getString("manual_url", null)

    /** Finds the server: a typed-in address, else the published one. Returns it, or null. */
    suspend fun resolve(): String? = withContext(Dispatchers.IO) {
        manualUrl?.let { return@withContext it.also { base = it } }
        runCatching {
            val c = URL("$SERVER_JSON?t=${System.currentTimeMillis() / 60_000}").openConnection() as HttpURLConnection
            c.connectTimeout = 8000; c.readTimeout = 8000
            c.inputStream.bufferedReader().use { JSONObject(it.readText()).getString("url") }.trimEnd('/')
        }.getOrNull()?.let { url ->
            prefs.edit().putString("looked_up_url", url).apply()
            base = url
        }
        base
    }

    /** A typed-in server address (blank goes back to the published one). */
    fun setManualUrl(url: String?) {
        val clean = url?.trim()?.trimEnd('/')?.takeIf { it.isNotEmpty() }
            ?.let { if (it.startsWith("http")) it else "https://$it" }
        prefs.edit().apply { if (clean == null) remove("manual_url") else putString("manual_url", clean) }.apply()
        base = clean ?: prefs.getString("looked_up_url", null)
    }

    fun setToken(t: String?) {
        token = t
        prefs.edit().apply { if (t == null) remove("token") else putString("token", t) }.apply()
    }

    fun absolute(path: String) = if (path.startsWith("http")) path else "${base ?: ""}$path"

    // --- HTTP -------------------------------------------------------------------------

    class ApiError(val code: Int, message: String) : Exception(message)

    private fun request(method: String, path: String, body: ByteArray? = null, contentType: String? = null,
                        auth: Boolean = true): String {
        val server = base ?: throw ApiError(0, "Can't find the game server")
        val c = URL(server + path).openConnection() as HttpURLConnection
        c.requestMethod = method
        c.connectTimeout = 15_000
        c.readTimeout = 60_000
        if (auth) token?.let { c.setRequestProperty("Authorization", "Bearer $it") }
        val code = try {
            if (body != null) {
                c.doOutput = true
                contentType?.let { c.setRequestProperty("Content-Type", it) }
                c.outputStream.use { it.write(body) }
            }
            c.responseCode
        } catch (e: java.io.IOException) {
            throw ApiError(0, "Can't reach the game server. Is the PC on?")
        }
        val text = (if (code < 400) c.inputStream else c.errorStream)?.bufferedReader()?.use { it.readText() }.orEmpty()
        if (code == 401 && auth && token != null) setToken(null)
        if (code >= 400) throw ApiError(code, errorMessage(code, text))
        return text
    }

    /** FastAPI errors: {"detail": "..."} or {"detail": [{"msg": ...}]} for validation. */
    private fun errorMessage(code: Int, text: String): String = runCatching {
        when (val d = JSONObject(text).get("detail")) {
            is JSONArray -> (0 until d.length()).joinToString("; ") { d.getJSONObject(it).getString("msg") }
            else -> d.toString()
        }
    }.getOrElse { if (code == 502 || code == 530) "The game server is offline right now" else "Server error ($code)" }

    private suspend fun call(method: String, path: String, json: JSONObject? = null): String =
        withContext(Dispatchers.IO) {
            request(method, path, json?.toString()?.toByteArray(), json?.let { "application/json" })
        }

    private fun q(s: String) = URLEncoder.encode(s, "UTF-8")

    // --- Accounts ---------------------------------------------------------------------

    suspend fun register(email: String, username: String, password: String, state: String) {
        val r = call("POST", "/auth/register", JSONObject().put("email", email).put("username", username)
            .put("password", password).put("state", state))
        setToken(JSONObject(r).getString("access_token"))
    }

    suspend fun login(ident: String, password: String) = withContext(Dispatchers.IO) {
        val form = "username=${q(ident)}&password=${q(password)}".toByteArray()
        val r = request("POST", "/auth/login", form, "application/x-www-form-urlencoded", auth = false)
        setToken(JSONObject(r).getString("access_token"))
    }

    fun logout() = setToken(null)

    suspend fun me(): Account = Account.parse(JSONObject(call("GET", "/me")))
    suspend fun setState(code: String) { call("PATCH", "/me", JSONObject().put("state", code)) }
    suspend fun setShowInFeed(on: Boolean) { call("PATCH", "/me/settings", JSONObject().put("show_in_feed", on)) }
    suspend fun setAvatar(n: Int) { call("PATCH", "/me/settings", JSONObject().put("avatar", n)) }

    // --- Captures ---------------------------------------------------------------------

    /**
     * Uploads a photo for the server to identify, as the website's capture form does.
     * The shrunk photo has no EXIF, so what the original said ([meta]) goes along;
     * [lat]/[lon] is where the phone is now, used only if the photo has no place and is
     * recent. [savePlace] false keeps no place at all.
     */
    suspend fun capture(photo: Bitmap, lat: Double?, lon: Double?, meta: PhotoMeta? = null,
                        savePlace: Boolean = true): JSONObject = withContext(Dispatchers.IO) {
        val boundary = "----captureanimals${System.nanoTime()}"
        val out = ByteArrayOutputStream()
        fun part(name: String, value: String) = out.write(
            "--$boundary\r\nContent-Disposition: form-data; name=\"$name\"\r\n\r\n$value\r\n".toByteArray())
        if (lat != null && lon != null) { part("latitude", lat.toString()); part("longitude", lon.toString()) }
        if (meta?.latitude != null && meta.longitude != null) {
            part("photo_latitude", meta.latitude.toString()); part("photo_longitude", meta.longitude.toString())
        }
        meta?.takenAt?.let { part("photo_taken_at", it.toString()) }
        if (!savePlace) part("save_place", "false")
        out.write(("--$boundary\r\nContent-Disposition: form-data; name=\"photo\"; filename=\"photo.jpg\"\r\n" +
            "Content-Type: image/jpeg\r\n\r\n").toByteArray())
        jpeg(ImageLoader.thumbnail(photo, 1600), out)
        out.write("\r\n--$boundary--\r\n".toByteArray())
        JSONObject(request("POST", "/captures", out.toByteArray(), "multipart/form-data; boundary=$boundary"))
    }

    /** Fixes when ([takenAt], local time) and where ([place], or null for none) a photo was taken. */
    suspend fun whereWhen(captureId: Int, takenAt: java.time.LocalDateTime, place: Pair<Double, Double>?): JSONObject {
        val body = JSONObject().put("taken_at", takenAt.withNano(0).toString())
        place?.let { body.put("latitude", it.first).put("longitude", it.second) }
        return JSONObject(call("PUT", "/captures/$captureId/where-when", body))
    }

    suspend fun pick(captureId: Int, label: String): JSONObject =
        JSONObject(call("POST", "/captures/$captureId/pick", JSONObject().put("label", label)))

    /** Identifies a photo with no usable place again against another state's animals. */
    suspend fun captureState(captureId: Int, state: String): JSONObject =
        JSONObject(call("POST", "/captures/$captureId/state", JSONObject().put("state", state)))

    /** Badges for the given state, keyed by slug (caught animals are always named). */
    suspend fun collection(state: String): Map<String, Badge> {
        val o = JSONObject(call("GET", "/me/collection?state=${q(state)}"))
        val entries = o.getJSONArray("entries")
        return buildMap {
            for (i in 0 until entries.length()) {
                val e = entries.getJSONObject(i)
                val slug = e.getJSONObject("species").optStringOrNull("slug") ?: continue
                if (!e.getBoolean("caught")) continue
                put(slug, Badge(e.optInt("capture_count", 1), parseTime(e.optStringOrNull("earned_at")),
                    e.optStringOrNull("photo_url")))
            }
        }
    }

    /** A friend's Field Guide: their primary state, or [state] when given. */
    suspend fun friendGuide(username: String, state: String? = null): FriendGuide =
        FriendGuide.parse(username, JSONObject(call("GET", "/users/${q(username)}/collection" +
            (state?.let { "?state=${q(it)}" } ?: ""))))

    // --- Challenges and bonds ------------------------------------------------------------

    suspend fun challenges(state: String): Week = Week.parse(JSONObject(call("GET", "/me/challenges?state=${q(state)}")))

    /** The player's unlocked states and how much of each they've captured ("Your states"). */
    suspend fun myStates(): List<StateTile> {
        val a = JSONArray(call("GET", "/me/states"))
        return List(a.length()) { i ->
            val o = a.getJSONObject(i)
            StateTile(o.getString("state"), o.getString("name"), o.getInt("caught"), o.getInt("total"), o.getBoolean("main"))
        }
    }

    /** Bond and field notes for one captured animal, or null when it isn't captured. */
    suspend fun bond(slug: String): Bond? =
        JSONObject(call("GET", "/me/bonds?species=${q(slug)}")).getJSONArray("bonds").optJSONObject(0)?.let { Bond.parse(it) }

    // --- Photos, feed, likes -----------------------------------------------------------

    suspend fun album(): List<OnlinePhoto> = OnlinePhoto.list(JSONObject(call("GET", "/me/album")).getJSONArray("photos"))

    /** scope: "state" (needs [state]), "all" (every state) or "friends". */
    suspend fun feed(scope: String, state: String, before: Int?): Pair<List<OnlinePhoto>, Int?> {
        val o = JSONObject(call("GET", "/feed?scope=$scope&limit=20&state=${q(state)}" +
            (before?.let { "&before=$it" } ?: "")))
        return OnlinePhoto.list(o.getJSONArray("photos")) to o.optIntOrNull("next_before")
    }

    suspend fun like(photoId: Int, on: Boolean) { call(if (on) "POST" else "DELETE", "/photos/$photoId/like") }

    /** Anyone who can see a photo can read and write its comments, friends or not. */
    suspend fun comments(photoId: Int): List<PhotoComment> {
        val a = JSONArray(call("GET", "/photos/$photoId/comments"))
        return List(a.length()) { PhotoComment.parse(a.getJSONObject(it)) }
    }
    suspend fun addComment(photoId: Int, body: String): PhotoComment =
        PhotoComment.parse(JSONObject(call("POST", "/photos/$photoId/comments", JSONObject().put("body", body))))
    suspend fun deleteComment(commentId: Int) { call("DELETE", "/comments/$commentId") }
    suspend fun deletePhoto(photoId: Int) { call("DELETE", "/photos/$photoId") }

    // --- Friends ----------------------------------------------------------------------

    suspend fun friends(): Friends = Friends.parse(JSONObject(call("GET", "/friends")))

    /** Likes and comments on your photos after [since] (the last answer's `now`); null gets just `now`. */
    suspend fun activity(since: String?): Activity =
        Activity.parse(JSONObject(call("GET", "/me/activity" + (since?.let { "?since=${q(it)}" } ?: ""))))
    suspend fun suggestions(): List<FriendEntry> {
        val a = JSONArray(call("GET", "/friends/suggestions"))
        return List(a.length()) { FriendEntry.parse(a.getJSONObject(it)) }
    }
    /** Returns "friends" or "requested". */
    suspend fun addFriend(username: String): String =
        JSONObject(call("POST", "/friends/requests", JSONObject().put("username", username))).getString("status")
    suspend fun acceptFriend(username: String) { call("POST", "/friends/requests/${q(username)}/accept") }
    suspend fun removeFriend(username: String) { call("DELETE", "/friends/${q(username)}") }

    // --- Safety: blocking, reports, deleting the account --------------------------------

    suspend fun blocks(): List<String> {
        val a = JSONArray(call("GET", "/blocks"))
        return List(a.length()) { a.getString(it) }
    }
    suspend fun block(username: String) { call("POST", "/blocks", JSONObject().put("username", username)) }
    suspend fun unblock(username: String) { call("DELETE", "/blocks/${q(username)}") }

    /** target is {"photo_id": n}, {"comment_id": n} or {"username": "..."}. True if it's now hidden. */
    suspend fun report(target: JSONObject, reason: String, details: String?): Boolean {
        target.put("reason", reason)
        if (!details.isNullOrBlank()) target.put("details", details)
        return JSONObject(call("POST", "/reports", target)).optBoolean("hidden")
    }

    /** Deletes the account and everything in it on the server, then signs out here. */
    suspend fun deleteAccount(password: String) {
        call("POST", "/me/delete", JSONObject().put("password", password))
        setToken(null)
    }

    // --- Images -----------------------------------------------------------------------

    private val images = object : LruCache<String, Bitmap>(24 * 1024 * 1024) {
        override fun sizeOf(key: String, value: Bitmap) = value.byteCount
    }

    /** Cached per size, so the full-screen copy doesn't replace the thumbnail or vice versa. */
    suspend fun image(path: String, maxSide: Int = 800): Bitmap? = images.get("$maxSide $path") ?: withContext(Dispatchers.IO) {
        runCatching {
            val c = URL(absolute(path)).openConnection() as HttpURLConnection
            token?.let { c.setRequestProperty("Authorization", "Bearer $it") }
            c.connectTimeout = 15_000; c.readTimeout = 30_000
            val bytes = c.inputStream.use { it.readBytes() }
            val b = BitmapFactory.decodeByteArray(bytes, 0, bytes.size) ?: return@runCatching null
            ImageLoader.thumbnail(b, maxSide).also { images.put("$maxSide $path", it) }
        }.getOrNull()
    }

    private fun jpeg(b: Bitmap, out: ByteArrayOutputStream) {
        val bmp = if (b.config == Bitmap.Config.ARGB_8888) b else b.copy(Bitmap.Config.ARGB_8888, false)
        bmp.compress(Bitmap.CompressFormat.JPEG, 88, out)
    }

    /** Server times are UTC, with or without an offset. */
    fun parseTime(s: String?): Long = s?.let { t ->
        runCatching { OffsetDateTime.parse(t).toInstant().toEpochMilli() }
            .recoverCatching { LocalDateTime.parse(t).toInstant(ZoneOffset.UTC).toEpochMilli() }.getOrNull()
    } ?: 0L
}

fun JSONObject.optStringOrNull(key: String): String? = if (isNull(key) || !has(key)) null else getString(key)
fun JSONObject.optIntOrNull(key: String): Int? = if (isNull(key) || !has(key)) null else getInt(key)

data class Account(val username: String, val email: String, val state: String, val showInFeed: Boolean,
                   val unlockedStates: List<String> = emptyList(), val avatar: Int = 1) {
    companion object {
        fun parse(o: JSONObject) = Account(o.getString("username"), o.getString("email"), o.getString("state"),
            o.isNull("show_in_feed") || o.optBoolean("show_in_feed", true),
            o.optJSONArray("unlocked_states")?.let { a -> List(a.length()) { a.getString(it) } } ?: emptyList(),
            o.optInt("avatar", 1))
    }
}

/** An album photo as the server shows it to this player (PhotoOut). */
data class OnlinePhoto(
    val id: Int,
    val url: String?,
    val username: String,
    val slug: String?,
    val commonName: String?,
    val rarity: String,
    val category: String,
    // When the photo was taken (its date), shown under it.
    val takenOn: Long,
    val place: String?,
    // Name of the state it was captured in.
    val state: String?,
    val likeCount: Int,
    val likedByMe: Boolean,
    val commentCount: Int,
    val isMine: Boolean,
    val byFriend: Boolean,
    // The photo's own 1-5 stars and points (null until it's scored).
    val stars: Int? = null,
    val score: Int? = null,
    // Only on your own photos: the exact time and place, to show and fix.
    val whereWhen: WhereWhen? = null,
    // Your own photo is hidden from other players (reported, or removed by a moderator).
    val hidden: Boolean = false,
) {
    companion object {
        fun parse(o: JSONObject): OnlinePhoto {
            val s = o.getJSONObject("species")
            return OnlinePhoto(o.getInt("id"), o.optStringOrNull("url"), o.getString("username"),
                s.optStringOrNull("slug"), s.optStringOrNull("common_name"), s.getString("rarity"),
                s.getString("category"), takenOn(o), o.optStringOrNull("place"), o.optStringOrNull("state"),
                o.optInt("like_count"), o.optBoolean("liked_by_me"), o.optInt("comment_count"),
                o.optBoolean("is_mine"), o.optBoolean("by_friend"), o.optIntOrNull("stars"),
                o.optIntOrNull("score"), WhereWhen.parse(o.optJSONObject("where_when")), o.optBoolean("hidden"))
        }

        /** Midday on the photo's date (so it shows the same day in any zone), else the upload time. */
        fun takenOn(o: JSONObject): Long = o.optStringOrNull("taken_on")?.let {
            runCatching { java.time.LocalDate.parse(it).atTime(12, 0).atZone(java.time.ZoneId.systemDefault())
                .toInstant().toEpochMilli() }.getOrNull()
        } ?: Online.parseTime(o.optStringOrNull("caught_at"))

        fun list(a: JSONArray) = List(a.length()) { parse(a.getJSONObject(it)) }
    }
}

data class PhotoComment(val id: Int, val username: String, val body: String, val at: Long,
                        val isMine: Boolean, val canDelete: Boolean) {
    companion object {
        fun parse(o: JSONObject) = PhotoComment(o.getInt("id"), o.getString("username"), o.getString("body"),
            Online.parseTime(o.optStringOrNull("created_at")), o.optBoolean("is_mine"), o.optBoolean("can_delete"))
    }
}

data class FriendEntry(val username: String, val caught: Int, val isBot: Boolean, val avatar: Int = 1) {
    companion object {
        fun parse(o: JSONObject) = FriendEntry(o.getString("username"), o.optInt("caught"), o.optBoolean("is_bot"),
            o.optInt("avatar", 1))
    }
}

data class Friends(val friends: List<FriendEntry>, val incoming: List<FriendEntry>, val outgoing: List<FriendEntry>) {
    companion object {
        fun parse(o: JSONObject): Friends {
            fun l(k: String) = o.getJSONArray(k).let { a -> List(a.length()) { FriendEntry.parse(a.getJSONObject(it)) } }
            return Friends(l("friends"), l("incoming"), l("outgoing"))
        }
    }
}

/** One animal on a friend's Field Guide. Names stay "???" until you or a friend captured it. */
data class GuideEntry(val number: Int, val slug: String?, val commonName: String?, val rarity: String,
                      val category: String, val caught: Boolean, val youCaught: Boolean,
                      val activity: String? = null, val photoStars: Int? = null) {
    companion object {
        fun parse(o: JSONObject): GuideEntry {
            val s = o.getJSONObject("species")
            return GuideEntry(s.getInt("number"), s.optStringOrNull("slug"), s.optStringOrNull("common_name"),
                s.getString("rarity"), s.getString("category"), o.getBoolean("caught"), o.optBoolean("you_caught"),
                o.optStringOrNull("activity"), o.optIntOrNull("photo_stars"))
        }
    }
}

/** A state a friend has captured animals in; their primary location is always one. */
data class GuidePlace(val state: String, val name: String, val caught: Int)

data class FriendGuide(val username: String, val state: String, val caught: Int, val total: Int,
                       val entries: List<GuideEntry>, val primaryState: String, val places: List<GuidePlace>) {
    companion object {
        fun parse(username: String, o: JSONObject): FriendGuide {
            val a = o.getJSONArray("entries")
            val p = o.optJSONArray("places") ?: JSONArray()
            val state = o.getString("state")
            val primary = o.optStringOrNull("primary_state") ?: state
            val places = List(p.length()) { p.getJSONObject(it) }
                .map { GuidePlace(it.getString("state"), it.getString("name"), it.getInt("caught")) }
                .sortedByDescending { it.state == primary }
            return FriendGuide(o.optString("username").ifEmpty { username }, state,
                o.getInt("caught"), o.getInt("total"), List(a.length()) { GuideEntry.parse(a.getJSONObject(it)) },
                primary, places)
        }
    }
}

/** GET /me/activity: likes grouped by photo, and the newest comments. */
data class Activity(val now: String, val likes: List<Like>, val comments: List<Comment>) {
    data class Like(val species: String, val count: Int, val usernames: List<String>)
    data class Comment(val species: String, val username: String, val body: String)

    companion object {
        fun parse(o: JSONObject): Activity {
            val likes = o.optJSONArray("likes") ?: JSONArray()
            val comments = o.optJSONArray("comments") ?: JSONArray()
            return Activity(o.getString("now"),
                List(likes.length()) { i ->
                    likes.getJSONObject(i).let { l ->
                        val names = l.getJSONArray("usernames")
                        Like(l.getString("species"), l.getInt("count"), List(names.length()) { names.getString(it) })
                    }
                },
                List(comments.length()) { i ->
                    comments.getJSONObject(i).let { Comment(it.getString("species"), it.getString("username"), it.getString("body")) }
                })
        }
    }
}
