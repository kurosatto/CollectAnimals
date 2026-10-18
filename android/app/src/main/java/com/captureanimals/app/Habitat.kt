package com.captureanimals.app

import android.annotation.SuppressLint
import android.content.Context
import android.os.Handler
import android.os.Looper
import android.view.ViewGroup
import android.webkit.JavascriptInterface
import android.webkit.WebResourceRequest
import android.webkit.WebResourceResponse
import android.webkit.WebView
import android.webkit.WebViewClient
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.runtime.Composable
import androidx.compose.runtime.DisposableEffect
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableIntStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.rememberUpdatedState
import androidx.compose.runtime.setValue
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.unit.dp
import androidx.compose.ui.viewinterop.AndroidView
import org.json.JSONArray
import org.json.JSONObject

/** One animal for the habitat scene. */
data class HabitatAnimal(val number: Int, val slug: String, val name: String, val category: String,
                         val rarity: String, val activity: String)

/** Your captured animals, in the habitat's JSON shape. */
fun habitatAnimals(info: ModelInfo, dex: FieldGuide?, collection: Map<String, Badge>): List<HabitatAnimal> =
    info.dexOrder.filter { it.slug in collection }.map { s ->
        HabitatAnimal(info.dexNumber(s.slug), s.slug, s.commonName, s.category, s.rarity, dex?.activity(s.slug) ?: "day")
    }

/**
 * The live habitat: the same pixel scene as the website (backend/app/static/habitat.js),
 * shown in a WebView from the app's own assets, so it works offline. [visitor] shows a
 * friend's animals in their state's scenery. Tapping an animal twice calls [onOpen].
 *
 * Keep one per screen with [rememberHabitatView] so scrolling it away and back doesn't
 * restart the scene.
 */
@Composable
fun Habitat(view: HabitatWebView, animals: List<HabitatAnimal>, state: String, modifier: Modifier = Modifier,
            visitor: String? = null, onOpen: (String) -> Unit) {
    val open by rememberUpdatedState(onOpen)
    view.onOpen = { open(it) }
    val json = remember(animals) {
        JSONArray(animals.map { a ->
            JSONObject().put("caught", true).put("activity", a.activity).put("species", JSONObject()
                .put("number", a.number).put("slug", a.slug).put("common_name", a.name)
                .put("category", a.category).put("rarity", a.rarity))
        }).toString()
    }
    LaunchedEffect(json, state, visitor) { view.show(json, state, visitor) }
    AndroidView(
        factory = { view.also { (it.parent as? ViewGroup)?.removeView(it) } },
        modifier = modifier.fillMaxWidth().height(view.heightDp.dp),
    )
}

/** Before you log in: [state]'s scenery with one featured animal, as a taste of the game. */
@Composable
fun HabitatShowcase(view: HabitatWebView, state: String, placeName: String, modifier: Modifier = Modifier) {
    LaunchedEffect(state, placeName) { view.showcase(state, placeName) }
    AndroidView(
        factory = { view.also { (it.parent as? ViewGroup)?.removeView(it) } },
        modifier = modifier.fillMaxWidth().height(view.heightDp.dp),
    )
}

@Composable
fun rememberHabitatView(): HabitatWebView {
    val context = LocalContext.current
    val view = remember { HabitatWebView(context) }
    DisposableEffect(view) { onDispose { view.destroy() } }
    return view
}

/** A WebView serving habitat.html, habitat.js and the sprites from the APK's assets. */
@SuppressLint("SetJavaScriptEnabled", "ViewConstructor")
class HabitatWebView(context: Context) : WebView(context) {
    var onOpen: (String) -> Unit = {}
    // Starts at the canvas's shape on a phone (320 x 270 plus the note line), then
    // follows what the page reports.
    var heightDp by mutableIntStateOf(330)
    private var ready = false
    private var pending: String? = null
    private val main = Handler(Looper.getMainLooper())

    init {
        settings.javaScriptEnabled = true
        settings.allowFileAccess = false
        setBackgroundColor(android.graphics.Color.TRANSPARENT)
        isVerticalScrollBarEnabled = false
        addJavascriptInterface(Bridge(), "AndroidHabitat")
        webViewClient = AssetClient(context)
        loadUrl("$ORIGIN/habitat.html")
    }

    fun show(json: String, state: String, visitor: String?) {
        val call = "setAnimals($json, ${JSONObject.quote(state)}, ${visitor?.let(JSONObject::quote) ?: "null"})"
        runJs(call)
    }

    fun showcase(state: String, placeName: String) = runJs("showcase(${JSONObject.quote(state)}, ${JSONObject.quote(placeName)})")

    private fun runJs(call: String) {
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
        @JavascriptInterface fun open(slug: String) { main.post { onOpen(slug) } }
        @JavascriptInterface fun height(px: Int) { main.post { if (px > 0) heightDp = px } }
    }

    companion object {
        const val ORIGIN = "https://appassets.androidplatform.net"
    }
}

/** Serves https://appassets.androidplatform.net/<path> from the APK's assets
 *  (species/ and backend/app/static/ are both packaged at the asset root). */
class AssetClient(private val context: Context) : WebViewClient() {
    override fun shouldInterceptRequest(view: WebView, request: WebResourceRequest): WebResourceResponse? {
        val url = request.url
        if (url.host != "appassets.androidplatform.net") return null
        val path = url.path.orEmpty().trimStart('/')
        return runCatching {
            WebResourceResponse(mimeType(path), if (mimeType(path).startsWith("text") ||
                path.endsWith(".js") || path.endsWith(".json")) "utf-8" else null, context.assets.open(path))
        }.getOrElse { WebResourceResponse("text/plain", "utf-8", 404, "Not found", emptyMap(), null) }
    }

    private fun mimeType(path: String) = when (path.substringAfterLast('.').lowercase()) {
        "html" -> "text/html"
        "js" -> "text/javascript"
        "json" -> "application/json"
        "css" -> "text/css"
        "png" -> "image/png"
        "svg" -> "image/svg+xml"
        else -> "application/octet-stream"
    }
}
