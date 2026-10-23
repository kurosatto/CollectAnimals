package com.captureanimals.app

import android.content.Context
import android.os.Build
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import org.json.JSONObject
import java.net.HttpURLConnection
import java.net.URL

/**
 * "A newer version is available": the game server's /app/version names the newest APK
 * it hands out (built after release.json is bumped for a major update). The phone
 * downloads it in the browser and installs it over this one.
 */
object Updates {
    data class Available(val version: String, val url: String)

    private fun prefs(context: Context) = context.getSharedPreferences("updates", Context.MODE_PRIVATE)

    /** The newer version on offer, unless this phone has it or already said "Later" to it. */
    suspend fun check(context: Context): Available? = withContext(Dispatchers.IO) {
        // Google Play updates its own installs, and its rules forbid offering APKs from elsewhere.
        if (installedFromPlay(context)) return@withContext null
        val base = Online.base ?: return@withContext null
        val offer = runCatching {
            val c = URL("$base/app/version").openConnection() as HttpURLConnection
            c.connectTimeout = 8000; c.readTimeout = 8000
            val android = c.inputStream.bufferedReader().use { JSONObject(it.readText()) }.optJSONObject("android")
            android?.let { Available(it.getString("version"), Online.absolute(it.getString("url"))) }
        }.getOrNull() ?: return@withContext null
        val skipped = prefs(context).getString("skipped", null)
        offer.takeIf { isNewer(it.version, BuildConfigCompat.version(context)) && it.version != skipped }
    }

    private fun installedFromPlay(context: Context): Boolean = runCatching {
        val pm = context.packageManager
        val installer = if (Build.VERSION.SDK_INT >= 30) pm.getInstallSourceInfo(context.packageName).installingPackageName
            else @Suppress("DEPRECATION") pm.getInstallerPackageName(context.packageName)
        installer == "com.android.vending"
    }.getOrDefault(false)

    fun skip(context: Context, version: String) = prefs(context).edit().putString("skipped", version).apply()

    /** "0.10.0" is newer than "0.9.2"; anything unreadable is not newer. */
    fun isNewer(offered: String, installed: String): Boolean {
        val a = offered.split(".").map { it.toIntOrNull() ?: return false }
        val b = installed.split(".").map { it.toIntOrNull() ?: return false }
        for (i in 0 until maxOf(a.size, b.size)) {
            val x = a.getOrElse(i) { 0 }
            val y = b.getOrElse(i) { 0 }
            if (x != y) return x > y
        }
        return false
    }
}
