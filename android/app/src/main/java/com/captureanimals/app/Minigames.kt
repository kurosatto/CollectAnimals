package com.captureanimals.app

import android.annotation.SuppressLint
import android.app.Activity
import android.content.Context
import android.content.ContextWrapper
import android.content.pm.ActivityInfo
import android.os.Handler
import android.os.Looper
import android.view.ViewGroup
import android.webkit.JavascriptInterface
import android.webkit.WebView
import androidx.activity.compose.BackHandler
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.runtime.Composable
import androidx.compose.runtime.DisposableEffect
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.viewinterop.AndroidView
import androidx.core.view.WindowCompat
import androidx.core.view.WindowInsetsCompat
import androidx.core.view.WindowInsetsControllerCompat
import kotlinx.coroutines.MainScope
import kotlinx.coroutines.cancel
import kotlinx.coroutines.launch
import org.json.JSONArray
import org.json.JSONObject

/**
 * The Games tab: the website's minigames (backend/app/static/minigames.js) in a
 * WebView from the app's assets, so they work offline. You play as one of your
 * captured [animals]; each game unlocks once you have an animal of its kind.
 */
@Composable
fun MinigamesScreen(animals: List<HabitatAnimal>, modifier: Modifier = Modifier, onPlaying: (Boolean) -> Unit = {}) {
    val context = LocalContext.current
    var playing by remember { mutableStateOf(false) }
    var picking by remember { mutableStateOf(false) }
    val view = remember { MinigamesWebView(context, { playing = it }, { picking = it }) }
    DisposableEffect(view) { onDispose { view.destroy() } }
    // While a game is on, it gets the whole screen: no app or system bars, and the
    // screen stays the way it's held (turning it would restart the page). Back quits the game.
    DisposableEffect(playing) {
        onPlaying(playing)
        val activity = context.findActivity()
        if (playing && activity != null) {
            activity.requestedOrientation = ActivityInfo.SCREEN_ORIENTATION_LOCKED
            WindowCompat.getInsetsController(activity.window, activity.window.decorView).apply {
                systemBarsBehavior = WindowInsetsControllerCompat.BEHAVIOR_SHOW_TRANSIENT_BARS_BY_SWIPE
                hide(WindowInsetsCompat.Type.systemBars())
            }
        }
        onDispose {
            if (playing && activity != null) {
                activity.requestedOrientation = ActivityInfo.SCREEN_ORIENTATION_UNSPECIFIED
                WindowCompat.getInsetsController(activity.window, activity.window.decorView)
                    .show(WindowInsetsCompat.Type.systemBars())
                onPlaying(false)
            }
        }
    }
    // On a game's page (picking an animal and a level), back goes to the grid of games.
    BackHandler(enabled = picking && !playing) { view.evaluateJavascript("mgCloseGame()", null) }
    BackHandler(enabled = playing) { view.evaluateJavascript("mgQuit()", null) }
    val json = remember(animals) {
        JSONArray(animals.map { a ->
            JSONObject().put("caught", true).put("species", JSONObject()
                .put("number", a.number).put("slug", a.slug).put("common_name", a.name).put("category", a.category))
        }).toString()
    }
    LaunchedEffect(json) { view.show(json) }
    AndroidView(
        factory = { view.also { (it.parent as? ViewGroup)?.removeView(it) } },
        modifier = modifier.fillMaxSize(),
    )
}

/** A WebView serving minigames.html, its scripts and the sprites from the APK's assets. */
@SuppressLint("SetJavaScriptEnabled", "ViewConstructor")
class MinigamesWebView(
    context: Context,
    private val onPlaying: (Boolean) -> Unit,
    private val onPicking: (Boolean) -> Unit = {},
) : WebView(context) {
    private var ready = false
    private var pending: String? = null
    private val main = Handler(Looper.getMainLooper())
    private val scope = MainScope()

    init {
        settings.javaScriptEnabled = true
        // Best scores and the last animal picked for each game.
        settings.domStorageEnabled = true
        settings.allowFileAccess = false
        setBackgroundColor(android.graphics.Color.TRANSPARENT)
        addJavascriptInterface(Bridge(), "AndroidMinigames")
        webViewClient = AssetClient(context)
        loadUrl("${HabitatWebView.ORIGIN}/minigames.html")
    }

    fun show(json: String) {
        val call = "setAnimals($json)"
        if (ready) evaluateJavascript(call, null) else pending = call
    }

    override fun destroy() {
        scope.cancel()
        super.destroy()
    }

    private inner class Bridge {
        /** A leaderboard call from minigames.js; the answer goes back to mgApiDone(). */
        @JavascriptInterface fun api(id: Int, method: String, path: String, body: String?) {
            scope.launch {
                val (ok, text) = try {
                    true to Online.games(method, path, body)
                } catch (e: Exception) {
                    false to (e.message ?: "error")
                }
                evaluateJavascript("mgApiDone($id, $ok, ${JSONObject.quote(text)})", null)
            }
        }


        /** A game started (true) or was left (false): minigames.js goes full screen. */
        @JavascriptInterface fun playing(on: Boolean) {
            main.post { onPlaying(on) }
        }

        /** A game's page was opened (true) or left for the grid of games (false). */
        @JavascriptInterface fun picking(on: Boolean) {
            main.post { onPicking(on) }
        }

        @JavascriptInterface fun ready() {
            main.post {
                ready = true
                pending?.let { evaluateJavascript(it, null) }
                pending = null
            }
        }
    }
}

private tailrec fun Context.findActivity(): Activity? = when (this) {
    is Activity -> this
    is ContextWrapper -> baseContext.findActivity()
    else -> null
}
