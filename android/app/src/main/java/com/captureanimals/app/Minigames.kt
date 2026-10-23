package com.captureanimals.app

import android.annotation.SuppressLint
import android.content.Context
import android.os.Handler
import android.os.Looper
import android.view.ViewGroup
import android.webkit.JavascriptInterface
import android.webkit.WebView
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.runtime.Composable
import androidx.compose.runtime.DisposableEffect
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.remember
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.viewinterop.AndroidView
import org.json.JSONArray
import org.json.JSONObject

/**
 * The Games tab: the website's minigames (backend/app/static/minigames.js) in a
 * WebView from the app's assets, so they work offline. You play as one of your
 * captured [animals]; each game unlocks once you have an animal of its kind.
 */
@Composable
fun MinigamesScreen(animals: List<HabitatAnimal>, modifier: Modifier = Modifier) {
    val context = LocalContext.current
    val view = remember { MinigamesWebView(context) }
    DisposableEffect(view) { onDispose { view.destroy() } }
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
class MinigamesWebView(context: Context) : WebView(context) {
    private var ready = false
    private var pending: String? = null
    private val main = Handler(Looper.getMainLooper())

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

    private inner class Bridge {
        @JavascriptInterface fun ready() {
            main.post {
                ready = true
                pending?.let { evaluateJavascript(it, null) }
                pending = null
            }
        }
    }
}
