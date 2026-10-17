package com.captureanimals.app

import android.annotation.SuppressLint
import android.content.Context
import android.os.Handler
import android.os.Looper
import android.view.MotionEvent
import android.webkit.JavascriptInterface
import android.webkit.WebView
import androidx.compose.foundation.layout.BoxWithConstraints
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.runtime.Composable
import androidx.compose.runtime.DisposableEffect
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.remember
import androidx.compose.runtime.rememberUpdatedState
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalConfiguration
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.unit.dp
import androidx.compose.ui.viewinterop.AndroidView
import org.json.JSONArray
import org.json.JSONObject
import kotlin.math.PI
import kotlin.math.ln
import kotlin.math.tan

/**
 * The parks map, the same as the website's: a zoomable street map (OpenStreetMap,
 * when online) framed to the state, with everything outside it dimmed and a pin per
 * park. The box takes the state's shape so the whole state fits. 📍 calls [onLocate];
 * pass the result back as [me].
 */
@Composable
fun ParksMap(dex: FieldGuide, parks: List<Park>, selectedId: String?, me: Pair<Double, Double>?,
             modifier: Modifier = Modifier, onLocate: () -> Unit, onSelect: (String) -> Unit) {
    val context = LocalContext.current
    val view = remember { ParksWebView(context) }
    DisposableEffect(view) { onDispose { view.destroy() } }
    val select by rememberUpdatedState(onSelect)
    val locate by rememberUpdatedState(onLocate)
    view.onSelect = { select(it) }
    view.onLocate = { locate() }
    val o = dex.outline
    val data = remember(dex, parks, selectedId) {
        JSONObject()
            .put("key", dex.region)
            .put("rings", JSONArray(o.rings.map { JSONArray(it.toList()) }))
            .put("bounds", JSONObject().put("west", o.minLon).put("east", o.maxLon)
                .put("south", o.minLat).put("north", o.maxLat))
            .put("parks", JSONArray(parks.map { p ->
                JSONObject().put("id", p.id).put("name", p.name).put("lat", p.lat).put("lon", p.lon)
                    .put("n", p.species.size)
            }))
            .put("selected", selectedId ?: JSONObject.NULL)
            .toString()
    }
    LaunchedEffect(data) { view.call("setMap($data)") }
    LaunchedEffect(me) { me?.let { (lat, lon) -> view.call("setMe($lat, $lon, true)") } }
    // Height from the state's shape (tall California, wide North Carolina), as on the website.
    val screenH = LocalConfiguration.current.screenHeightDp
    BoxWithConstraints(modifier.fillMaxWidth()) {
        val h = (maxWidth.value * stateAspect(o)).coerceIn(220f, screenH * 0.7f)
        AndroidView(factory = { view }, modifier = Modifier.fillMaxWidth().height(h.dp))
    }
}

/** Height / width of the state's bounding box on a web (Mercator) map. */
fun stateAspect(o: Outline): Float {
    fun merc(lat: Double) = ln(tan(PI / 4 + lat * PI / 360))
    return ((merc(o.maxLat) - merc(o.minLat)) / ((o.maxLon - o.minLon) * PI / 180)).toFloat()
}

@SuppressLint("SetJavaScriptEnabled", "ViewConstructor", "ClickableViewAccessibility")
class ParksWebView(context: Context) : WebView(context) {
    var onSelect: (String) -> Unit = {}
    var onLocate: () -> Unit = {}
    private var ready = false
    private val pending = mutableListOf<String>()
    private val main = Handler(Looper.getMainLooper())

    init {
        settings.javaScriptEnabled = true
        settings.allowFileAccess = false
        // OpenStreetMap asks apps to identify themselves.
        settings.userAgentString = settings.userAgentString + " CaptureAnimals/" + BuildConfigCompat.version(context)
        isVerticalScrollBarEnabled = false
        addJavascriptInterface(Bridge(), "AndroidParks")
        webViewClient = AssetClient(context)
        // Drags pan the map instead of scrolling the page around it.
        setOnTouchListener { v, e ->
            if (e.actionMasked == MotionEvent.ACTION_DOWN) v.parent?.requestDisallowInterceptTouchEvent(true)
            false
        }
        loadUrl("${HabitatWebView.ORIGIN}/parks.html")
    }

    fun call(js: String) {
        if (ready) evaluateJavascript(js, null) else pending += js
    }

    private inner class Bridge {
        @JavascriptInterface fun ready() {
            main.post {
                ready = true
                pending.forEach { evaluateJavascript(it, null) }
                pending.clear()
            }
        }
        @JavascriptInterface fun select(id: String) { main.post { onSelect(id) } }
        @JavascriptInterface fun locate() { main.post { onLocate() } }
    }
}

/** The app's version name, for the map's user agent. */
object BuildConfigCompat {
    fun version(context: Context): String = runCatching {
        context.packageManager.getPackageInfo(context.packageName, 0).versionName
    }.getOrNull() ?: "dev"
}
