package com.collectanimals.app

import androidx.activity.compose.BackHandler
import androidx.compose.foundation.Canvas
import androidx.compose.foundation.background
import androidx.compose.foundation.gestures.detectTapGestures
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.ExperimentalLayoutApi
import androidx.compose.foundation.layout.FlowRow
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.aspectRatio
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.AssistChip
import androidx.compose.material3.AssistChipDefaults
import androidx.compose.material3.Card
import androidx.compose.material3.CardDefaults
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.saveable.rememberSaveable
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.graphics.drawscope.Stroke
import androidx.compose.ui.input.pointer.pointerInput
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import kotlin.math.hypot
import kotlin.math.min

/**
 * Parks where many of the 100 can be spotted (species/hotspots.json), matching the
 * web page's Hotspots card: a map with a pin per park, a list sorted by species count,
 * and a detail card whose species chips open their Pokédex pages.
 */
@OptIn(ExperimentalLayoutApi::class)
@Composable
fun HotspotsScreen(info: ModelInfo, dex: Pokedex, collection: Map<String, Badge>,
                   onOpenDex: (String) -> Unit, onBack: (() -> Unit)? = null) {
    if (onBack != null) BackHandler(onBack = onBack)
    val parks = remember(dex) { dex.parks.sortedByDescending { it.species.size } }
    var selectedId by rememberSaveable { mutableStateOf<String?>(null) }
    val selected = parks.firstOrNull { it.id == selectedId }
    val bySlug = remember(info) { info.species.associateBy { it.slug } }
    val scroll = rememberScrollState()

    Column(Modifier.fillMaxSize().verticalScroll(scroll).padding(16.dp), verticalArrangement = Arrangement.spacedBy(12.dp)) {
        if (onBack != null) {
            TextButton(onClick = onBack, contentPadding = androidx.compose.foundation.layout.PaddingValues(0.dp)) {
                Text("‹ Back")
            }
            Text("Hotspots", style = MaterialTheme.typography.headlineMedium, fontWeight = FontWeight.Bold)
        }
        Text("Parks where you can spot lots of the 100. Tap a park to see which ones.",
            style = MaterialTheme.typography.bodyMedium, color = MaterialTheme.colorScheme.outline)

        HotspotsMap(dex, parks, selectedId, Modifier.fillMaxWidth()) { selectedId = it }

        selected?.let { park ->
            val caught = park.species.count { it.slug in collection }
            Card(Modifier.fillMaxWidth(), colors = CardDefaults.cardColors(
                containerColor = MaterialTheme.colorScheme.primary.copy(alpha = 0.08f))) {
                Column(Modifier.padding(16.dp), verticalArrangement = Arrangement.spacedBy(8.dp)) {
                    Text(park.name, style = MaterialTheme.typography.titleLarge, fontWeight = FontWeight.Bold)
                    Text(park.blurb, style = MaterialTheme.typography.bodyMedium, color = MaterialTheme.colorScheme.outline)
                    Text("You can spot ${park.species.size} of the 100 here. You've captured $caught of them.",
                        style = MaterialTheme.typography.bodyLarge)
                    FlowRow(horizontalArrangement = Arrangement.spacedBy(6.dp)) {
                        park.species.forEach { ps ->
                            val s = bySlug[ps.slug] ?: return@forEach
                            val got = ps.slug in collection
                            AssistChip(
                                onClick = { onOpenDex(ps.slug) },
                                label = { Text((if (got) "✓ " else "") + s.commonName) },
                                colors = AssistChipDefaults.assistChipColors(labelColor = rarityColor(s.rarity)),
                            )
                        }
                    }
                }
            }
        }

        parks.forEach { park ->
            val on = park.id == selectedId
            Card(
                onClick = { selectedId = park.id },
                modifier = Modifier.fillMaxWidth(),
                colors = CardDefaults.cardColors(containerColor =
                    if (on) MaterialTheme.colorScheme.primaryContainer else MaterialTheme.colorScheme.surfaceVariant),
            ) {
                Row(Modifier.fillMaxWidth().padding(horizontal = 16.dp, vertical = 12.dp),
                    horizontalArrangement = Arrangement.SpaceBetween, verticalAlignment = Alignment.CenterVertically) {
                    Text(park.name, Modifier.weight(1f))
                    Text("${park.species.size}", fontWeight = FontWeight.Bold)
                }
            }
        }
    }
}

/** California outline with a pin per park; bigger pins have more species. Tap a pin to select it. */
@Composable
private fun HotspotsMap(dex: Pokedex, parks: List<Park>, selectedId: String?, modifier: Modifier,
                       onSelect: (String) -> Unit) {
    val frame = remember(dex) { CaliforniaFrame(dex.outline) }
    val land = MaterialTheme.colorScheme.surfaceVariant
    val sea = MaterialTheme.colorScheme.surface
    val border = MaterialTheme.colorScheme.outline
    val pin = MaterialTheme.colorScheme.primary
    val pinOn = MaterialTheme.colorScheme.tertiary

    // Same sizing as the web map: 5 + min(7, species / 6), in dp.
    fun radiusDp(p: Park) = 5f + min(7f, p.species.size / 6f)

    Canvas(
        modifier.aspectRatio(frame.aspect).clip(RoundedCornerShape(16.dp)).background(sea)
            .pointerInput(parks) {
                detectTapGestures { tap ->
                    val w = size.width.toFloat()
                    val h = size.height.toFloat()
                    val hit = parks.minByOrNull { p ->
                        hypot(frame.x(p.lon, w) - tap.x, frame.y(p.lat, h) - tap.y)
                    }
                    if (hit != null) {
                        val d = hypot(frame.x(hit.lon, w) - tap.x, frame.y(hit.lat, h) - tap.y)
                        // Generous touch target: pins are small, fingers aren't.
                        if (d <= (radiusDp(hit) + 14f) * density) onSelect(hit.id)
                    }
                }
            },
    ) {
        val path = frame.outlinePath(dex.outline, size)
        drawPath(path, land)
        drawPath(path, border, style = Stroke(width = 1.5.dp.toPx()))
        // Draw the selected pin last so it sits on top of its neighbors.
        for (p in parks.sortedBy { it.id == selectedId }) {
            val c = Offset(frame.x(p.lon, size.width), frame.y(p.lat, size.height))
            val r = radiusDp(p).dp.toPx()
            val on = p.id == selectedId
            drawCircle((if (on) pinOn else pin).copy(alpha = if (on) 1f else 0.75f), r, c)
            drawCircle(sea, r, c, style = Stroke(width = 1.5.dp.toPx()))
        }
    }
}
