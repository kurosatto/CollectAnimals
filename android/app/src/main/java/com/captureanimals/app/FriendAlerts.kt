package com.captureanimals.app

import android.Manifest
import android.app.NotificationChannel
import android.app.NotificationManager
import android.app.PendingIntent
import android.content.Context
import android.content.Intent
import android.content.pm.PackageManager
import android.os.Build
import androidx.core.app.NotificationCompat
import androidx.core.app.NotificationManagerCompat
import androidx.core.content.ContextCompat
import androidx.work.Constraints
import androidx.work.CoroutineWorker
import androidx.work.ExistingPeriodicWorkPolicy
import androidx.work.NetworkType
import androidx.work.PeriodicWorkRequestBuilder
import androidx.work.WorkManager
import androidx.work.WorkerParameters
import java.util.concurrent.TimeUnit

/**
 * Phone notifications for friend requests, likes and comments, without a push service:
 * every 15 minutes (Android's shortest repeat, and only with a network) the app asks
 * the game server for its friends list and for activity on your photos, and notifies
 * about requests it hasn't shown before, accepted requests, and new likes and comments.
 * Likes come grouped per photo, so a popular photo is one line, not one buzz per like.
 *
 * Requests the player has already seen in the app are remembered, so they don't pop
 * up again later. Nothing is stored on the server for this.
 */
object FriendAlerts {
    const val EXTRA_TAB = "open_tab"
    private const val CHANNEL = "friend_requests"
    private const val PHOTO_CHANNEL = "photo_activity"
    private const val WORK = "friend-alerts"

    fun schedule(context: Context) {
        val request = PeriodicWorkRequestBuilder<FriendCheckWorker>(15, TimeUnit.MINUTES)
            .setConstraints(Constraints.Builder().setRequiredNetworkType(NetworkType.CONNECTED).build())
            .build()
        WorkManager.getInstance(context).enqueueUniquePeriodicWork(WORK, ExistingPeriodicWorkPolicy.KEEP, request)
    }

    private fun prefs(context: Context) = context.getSharedPreferences("friend_alerts", Context.MODE_PRIVATE)

    /** What the player has already seen: their incoming requests and the requests they sent. */
    fun markSeen(context: Context, friends: Friends) {
        prefs(context).edit()
            .putStringSet("incoming", friends.incoming.map { it.username }.toSet())
            .putStringSet("outgoing", friends.outgoing.map { it.username }.toSet())
            .apply()
    }

    /** New requests since [markSeen], and people who accepted one of ours. */
    fun news(context: Context, friends: Friends): Pair<List<String>, List<String>> {
        val p = prefs(context)
        val seenIn = p.getStringSet("incoming", emptySet()).orEmpty()
        val seenOut = p.getStringSet("outgoing", emptySet()).orEmpty()
        val friendNames = friends.friends.map { it.username }.toSet()
        return newNames(seenIn, friends.incoming.map { it.username }) to
            seenOut.filter { it in friendNames }.sorted()
    }

    /** Names in [now] that weren't in [seen], in order. */
    fun newNames(seen: Set<String>, now: List<String>): List<String> = now.filter { it !in seen }

    /** Words for a notification about [requests] and [accepted], or null when there's nothing new. */
    fun message(requests: List<String>, accepted: List<String>): String? {
        val lines = buildList {
            when (requests.size) {
                0 -> {}
                1 -> add("${requests[0]} sent you a friend request")
                else -> add("${requests.size} new friend requests: ${requests.joinToString(", ")}")
            }
            when (accepted.size) {
                0 -> {}
                1 -> add("${accepted[0]} accepted your friend request")
                else -> add("${accepted.joinToString(", ")} accepted your friend requests")
            }
        }
        return lines.takeIf { it.isNotEmpty() }?.joinToString("\n")
    }

    /** Words for new likes and comments on your photos, or null when there are none. */
    fun activityMessage(a: Activity): String? {
        fun others(n: Int) = if (n > 0) " and $n other${if (n > 1) "s" else ""}" else ""
        val lines = a.likes.map { "${it.usernames.firstOrNull() ?: "Someone"}${others(it.count - 1)} liked your ${it.species} photo" } +
            a.comments.map { "${it.username} on your ${it.species}: ${it.body}" }
        return lines.takeIf { it.isNotEmpty() }?.joinToString("\n")
    }

    /** Server time of the last likes/comments check, sent back as `since`. */
    fun activitySince(context: Context): String? = prefs(context).getString("activity_since", null)
    fun setActivitySince(context: Context, now: String) = prefs(context).edit().putString("activity_since", now).apply()

    fun canNotify(context: Context) = Build.VERSION.SDK_INT < 33 ||
        ContextCompat.checkSelfPermission(context, Manifest.permission.POST_NOTIFICATIONS) == PackageManager.PERMISSION_GRANTED

    /** Shows [text]: a friends notification, or with [photos] one about likes and comments. */
    fun notify(context: Context, text: String, photos: Boolean = false) {
        if (!canNotify(context)) return
        val nm = context.getSystemService(NotificationManager::class.java)
        val channel = if (photos) PHOTO_CHANNEL else CHANNEL
        nm.createNotificationChannel(NotificationChannel(channel, if (photos) "Likes and comments" else "Friend requests",
            NotificationManager.IMPORTANCE_DEFAULT))
        val open = Intent(context, MainActivity::class.java)
            .putExtra(EXTRA_TAB, if (photos) "gallery" else "social")
            .addFlags(Intent.FLAG_ACTIVITY_NEW_TASK or Intent.FLAG_ACTIVITY_CLEAR_TOP)
        val tap = PendingIntent.getActivity(context, if (photos) 1 else 0, open,
            PendingIntent.FLAG_UPDATE_CURRENT or PendingIntent.FLAG_IMMUTABLE)
        val n = NotificationCompat.Builder(context, channel)
            .setSmallIcon(R.drawable.ic_notify)
            .setContentTitle("Capture Animals")
            .setContentText(text.lineSequence().first())
            .setStyle(NotificationCompat.BigTextStyle().bigText(text))
            .setContentIntent(tap)
            .setAutoCancel(true)
            .build()
        try { NotificationManagerCompat.from(context).notify(if (photos) 2 else 1, n) } catch (_: SecurityException) {}
    }
}

class FriendCheckWorker(context: Context, params: WorkerParameters) : CoroutineWorker(context, params) {
    override suspend fun doWork(): Result {
        Online.init(applicationContext)
        if (!Online.signedIn) return Result.success()
        // The server's address changes when the PC restarts, so look it up again if needed.
        val friends = runCatching { Online.friends() }.recoverCatching {
            Online.resolve()
            Online.friends()
        }.getOrNull() ?: return Result.success()
        val (requests, accepted) = FriendAlerts.news(applicationContext, friends)
        FriendAlerts.message(requests, accepted)?.let { FriendAlerts.notify(applicationContext, it) }
        FriendAlerts.markSeen(applicationContext, friends)
        // The first check only notes the server's time; later ones report what came after it.
        runCatching { Online.activity(FriendAlerts.activitySince(applicationContext)) }.onSuccess { a ->
            if (FriendAlerts.activitySince(applicationContext) != null) {
                FriendAlerts.activityMessage(a)?.let { FriendAlerts.notify(applicationContext, it, photos = true) }
            }
            FriendAlerts.setActivitySince(applicationContext, a.now)
        }
        return Result.success()
    }
}
