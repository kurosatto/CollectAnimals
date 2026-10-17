package com.captureanimals.app

import android.graphics.BitmapFactory
import androidx.activity.compose.BackHandler
import androidx.compose.foundation.Canvas
import androidx.compose.foundation.Image
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.aspectRatio
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.Card
import androidx.compose.material3.CardDefaults
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.runtime.Composable
import androidx.compose.runtime.remember
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.geometry.Size
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.Path
import androidx.compose.ui.graphics.asImageBitmap
import androidx.compose.ui.graphics.drawscope.Stroke
import androidx.compose.ui.layout.ContentScale
import androidx.compose.ui.text.font.FontStyle
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import java.text.DateFormat
import java.util.Date
import kotlin.math.cos
import kotlin.math.ln
import kotlin.math.roundToInt

/** Full-page Field Guide entry for one species. */
@Composable
fun DexEntryScreen(number: Int, s: Species, badge: Badge?, dex: FieldGuide,
                   bond: @Composable () -> Unit = {}, onBack: () -> Unit) {
    BackHandler(onBack = onBack)
    val details = dex.details[s.slug]
    Column(Modifier.fillMaxSize().verticalScroll(rememberScrollState()).padding(16.dp),
        verticalArrangement = Arrangement.spacedBy(12.dp)) {
        TextButton(onClick = onBack, contentPadding = androidx.compose.foundation.layout.PaddingValues(0.dp)) {
            Text("‹ Field Guide")
        }
        // Another state's species (opened from Photos) has no number in this state's guide.
        val kind = s.category.replaceFirstChar { it.uppercase() }
        Text(if (number > 0) "#%03d · %s".format(number, kind) else kind,
            style = MaterialTheme.typography.labelLarge, color = MaterialTheme.colorScheme.outline)
        Text(s.commonName, style = MaterialTheme.typography.headlineMedium, fontWeight = FontWeight.Bold)
        Row(horizontalArrangement = Arrangement.spacedBy(10.dp), verticalAlignment = Alignment.CenterVertically) {
            Text(s.scientificName, fontStyle = FontStyle.Italic)
            RarityTag(s.rarity)
        }

        Box(Modifier.fillMaxWidth().aspectRatio(4f / 3f).clip(RoundedCornerShape(16.dp))
            .background(MaterialTheme.colorScheme.surfaceVariant), contentAlignment = Alignment.Center) {
            // Signed in, the photo is on the game server; offline it's a file on the phone.
            val remote = badge?.photo?.takeIf { it.startsWith("/") && !java.io.File(it).exists() }
            val photo = remember(badge?.photo) { badge?.photo?.takeIf { remote == null }?.let { BitmapFactory.decodeFile(it) } }
            if (remote != null) {
                RemoteImage(remote, "Your ${s.commonName}", Modifier.fillMaxSize())
            } else if (photo != null) {
                Image(photo.asImageBitmap(), contentDescription = "Your ${s.commonName}",
                    modifier = Modifier.fillMaxSize(), contentScale = ContentScale.Crop)
            } else {
                Column(horizontalAlignment = Alignment.CenterHorizontally) {
                    PixelSprite(s.slug, caught = false, Modifier.size(128.dp))
                    Text("Not captured yet", color = MaterialTheme.colorScheme.outline)
                }
            }
        }
        details?.takeIf { it.safety == "caution" || it.safety == "danger" }?.let { SafetyCard(it) }
        if (badge != null) {
            Text("Captured ${badge.count}× — first on " +
                DateFormat.getDateInstance(DateFormat.MEDIUM).format(Date(badge.firstCaughtAt)),
                style = MaterialTheme.typography.bodyMedium)
        }
        bond()

        if (details != null) {
            Row(horizontalArrangement = Arrangement.spacedBy(12.dp)) {
                StatCard("Size", details.size, Modifier.weight(1f))
                StatCard("Weight", details.weight, Modifier.weight(1f))
            }
            Card(Modifier.fillMaxWidth(), colors = CardDefaults.cardColors(
                containerColor = rarityColor(s.rarity).copy(alpha = 0.12f))) {
                Column(Modifier.padding(16.dp)) {
                    Text("Fun fact", style = MaterialTheme.typography.labelLarge, color = rarityColor(s.rarity))
                    // Same as the web page: the fact is the reward for catching it.
                    Text(if (badge != null) details.funFact else "🔒 Capture one to unlock its fun fact.",
                        style = MaterialTheme.typography.bodyLarge)
                }
            }
        }

        dex.seasons[s.slug]?.takeIf { it.months.any { n -> n > 0 } }?.let { season ->
            WhenToLook(season, dex.dayNight(s.slug), rarityColor(s.rarity))
        }

        Text("Where to find it", style = MaterialTheme.typography.titleMedium)
        RangeMap(dex, s.slug, rarityColor(s.rarity), Modifier.fillMaxWidth())
        details?.whereToFind?.takeIf { it.isNotBlank() }?.let {
            Text("📍 $it", style = MaterialTheme.typography.bodyMedium)
        }
        details?.activeTime?.takeIf { it.isNotBlank() }?.let { LabeledLine("Most active", it) }
        details?.spottingTip?.takeIf { it.isNotBlank() }?.let { LabeledLine("Spotting tip", it) }
        if (dex.parks.isNotEmpty()) {
            LabeledLine("Hotspots", dex.hotspotsFor(s.slug).joinToString(", ").ifEmpty { "—" })
        }
        // A grid step of 0.25° is about 25 km; NC's finer 0.125° grid is about 12 km.
        val km = (dex.ranges.step * 100).roundToInt()
        Text("Each square is about $km km (${(km * 0.62).roundToInt()} mi) across; darker means more of the " +
            "${dex.ranges.sightings(s.slug)} recent iNaturalist sightings in ${dex.region}.",
            style = MaterialTheme.typography.bodySmall, color = MaterialTheme.colorScheme.outline)
    }
}

/** Same wording as the web page: watch from a distance, never approach. */
@Composable
private fun SafetyCard(d: SpeciesDetails) {
    val danger = d.safety == "danger"
    Card(Modifier.fillMaxWidth(), colors = CardDefaults.cardColors(
        containerColor = (if (danger) Color(0xFFD64545) else Color(0xFFE0A100)).copy(alpha = 0.15f))) {
        Text((if (danger) "⚠️ Dangerous: " else "✋ ") + d.safetyNote +
            (if (d.safeDistance.isNotBlank()) " Stay at least ${d.safeDistance} away." else ""),
            Modifier.padding(16.dp), style = MaterialTheme.typography.bodyMedium)
    }
}

/** "When to look": best months, a day/night hint and a bar per month, as on the website. */
@Composable
private fun WhenToLook(season: Season, dayNight: String?, color: Color) {
    Column(verticalArrangement = Arrangement.spacedBy(6.dp)) {
        Text("When to look", style = MaterialTheme.typography.titleMedium)
        Text("📅 Best months: ${season.bestMonths()}", style = MaterialTheme.typography.bodyMedium)
        dayNight?.let { Text(it, style = MaterialTheme.typography.bodyMedium) }
        val max = season.months.maxOrNull()?.coerceAtLeast(1) ?: 1
        Row(Modifier.fillMaxWidth().height(56.dp), horizontalArrangement = Arrangement.spacedBy(3.dp),
            verticalAlignment = Alignment.Bottom) {
            season.months.forEachIndexed { i, n ->
                Column(Modifier.weight(1f), horizontalAlignment = Alignment.CenterHorizontally) {
                    val frac = (n.toFloat() / max).coerceAtLeast(0.05f)
                    Box(Modifier.fillMaxWidth().height((40 * frac).dp).clip(RoundedCornerShape(2.dp))
                        .background(if (n >= 0.6 * max) color else color.copy(alpha = 0.3f)))
                    Text("JFMAMJJASOND"[i].toString(), style = MaterialTheme.typography.labelSmall,
                        color = MaterialTheme.colorScheme.outline)
                }
            }
        }
    }
}

@Composable
private fun LabeledLine(label: String, value: String) {
    Column {
        Text(label, style = MaterialTheme.typography.labelMedium, color = MaterialTheme.colorScheme.outline)
        Text(value, style = MaterialTheme.typography.bodyMedium)
    }
}

@Composable
private fun StatCard(label: String, value: String, modifier: Modifier) {
    Card(modifier) {
        Column(Modifier.padding(12.dp)) {
            Text(label, style = MaterialTheme.typography.labelMedium, color = MaterialTheme.colorScheme.outline)
            Text(value, style = MaterialTheme.typography.bodyMedium)
        }
    }
}

/**
 * Equirectangular frame around a state outline, with longitudes squeezed by the cosine
 * of its middle latitude, which is close enough at state scale. Widened a little to the
 * west so offshore sightings (whales, seals) stay on the California map.
 */
class StateFrame(o: Outline) {
    private val kx = cos(Math.toRadians((o.minLat + o.maxLat) / 2))
    val minLon = o.minLon - 0.6
    val maxLon = o.maxLon + 0.2
    val minLat = o.minLat - 0.2
    val maxLat = o.maxLat + 0.2
    val aspect = ((maxLon - minLon) * kx / (maxLat - minLat)).toFloat()

    fun x(lon: Double, width: Float) = ((lon - minLon) / (maxLon - minLon) * width).toFloat()
    fun y(lat: Double, height: Float) = ((maxLat - lat) / (maxLat - minLat) * height).toFloat()

    fun outlinePath(o: Outline, size: Size): Path = Path().apply {
        for (ring in o.rings) {
            moveTo(x(ring[0], size.width), y(ring[1], size.height))
            for (i in 2 until ring.size step 2) lineTo(x(ring[i], size.width), y(ring[i + 1], size.height))
            close()
        }
    }
}

/** State outline with the species' sighting cells shaded on top. */
@Composable
fun RangeMap(dex: FieldGuide, slug: String, color: Color, modifier: Modifier = Modifier) {
    val g = dex.ranges
    val frame = remember(dex) { StateFrame(dex.outline) }
    val land = MaterialTheme.colorScheme.surfaceVariant
    val sea = MaterialTheme.colorScheme.surface
    val border = MaterialTheme.colorScheme.outline
    val cells = g.cells[slug].orEmpty()
    val maxCount = cells.maxOfOrNull { it[2] } ?: 1

    Canvas(modifier.aspectRatio(frame.aspect).clip(RoundedCornerShape(16.dp)).background(sea)) {
        val path = frame.outlinePath(dex.outline, size)
        drawPath(path, land)
        val cw = frame.x(frame.minLon + g.step, size.width)
        val ch = size.height - frame.y(frame.minLat + g.step, size.height)
        for ((col, row, n) in cells) {
            val lon = g.lon0 + col * g.step
            val lat = g.lat0 + row * g.step
            // Log scale so a few sightings still show next to city hotspots.
            val t = (0.25 + 0.75 * ln(1.0 + n) / ln(1.0 + maxCount)).toFloat()
            drawRect(color.copy(alpha = t), topLeft = Offset(frame.x(lon, size.width), frame.y(lat + g.step, size.height)),
                size = Size(cw, ch))
        }
        drawPath(path, border, style = Stroke(width = 1.5.dp.toPx()))
    }
}
