package com.captureanimals.app

import androidx.activity.compose.BackHandler
import androidx.activity.compose.rememberLauncherForActivityResult
import androidx.activity.result.contract.ActivityResultContracts
import androidx.compose.foundation.BorderStroke
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.heightIn
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.grid.GridCells
import androidx.compose.foundation.lazy.grid.LazyVerticalGrid
import androidx.compose.foundation.lazy.grid.items
import androidx.compose.foundation.lazy.items
import androidx.compose.material3.AlertDialog
import androidx.compose.material3.CardDefaults
import androidx.compose.material3.HorizontalDivider
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedCard
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.background
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp

object StateList {
    /** The player's unlocked states, in states.json order (the state screen's tiles). */
    fun tiles(states: List<StateInfo>, unlocked: Set<String>): List<StateInfo> = states.filter { it.code in unlocked }

    /** Every US state A to Z, then the countries of Europe, then Asia, each A to Z, for the first-launch list. */
    fun alphabetical(states: List<StateInfo>): List<StateInfo> =
        states.sortedWith(compareBy({ REGIONS.indexOf(it.region).let { i -> if (i < 0) REGIONS.size else i } }, { it.name }))

    /** The picker's groups, in order. */
    val REGIONS = listOf("usa", "europe", "asia")
    private val LABELS = mapOf("usa" to "United States", "europe" to "Europe", "asia" to "Asia")

    /** One region of places, A to Z: tap "United States" to open its states. */
    data class Group<T>(val key: String, val label: String, val items: List<T>) {
        /** "50 states" / "42 countries". */
        val count get() = "${items.size} ${if (key == "usa") "states" else "countries"}"
    }

    /** Places by region (US, Europe, Asia, then any new region), each A to Z, empty regions left out. */
    fun <T> groups(items: List<T>, info: (T) -> StateInfo?): List<Group<T>> {
        val region = { t: T -> info(t)?.region ?: "usa" }
        val keys = REGIONS + items.map(region).distinct().filter { it !in REGIONS }
        return keys.map { k ->
            Group(k, LABELS[k] ?: k.replaceFirstChar { it.uppercase() },
                items.filter { region(it) == k }.sortedBy { info(it)?.name.orEmpty() })
        }.filter { it.items.isNotEmpty() }
    }

    fun groups(states: List<StateInfo>): List<Group<StateInfo>> = groups(states) { it }

    /** Open on the regions first only when there are several and the list is long. */
    fun <T> drills(groups: List<Group<T>>): Boolean = groups.size > 1 && groups.sumOf { it.items.size } > 8
}

/**
 * A place list that opens on its regions (United States, Europe, then Singapore on its
 * own row) and drills into one when tapped, with "All places" (or the back gesture) to
 * go back. [row] draws one place; a region holding one place shows that place directly.
 */
@Composable
fun <T> RegionDrill(groups: List<StateList.Group<T>>, current: String?, code: (T) -> String,
                    sub: (StateList.Group<T>, T?) -> String, modifier: Modifier = Modifier,
                    grid: Boolean = false, row: @Composable (T) -> Unit) {
    var open by remember(groups) { mutableStateOf<String?>(null) }
    val drill = StateList.drills(groups)
    BackHandler(enabled = drill && open != null) { open = null }
    val shown = if (!drill) groups else groups.filter { it.key == open }
    when {
        drill && open == null -> LazyColumn(modifier) {
            items(groups, key = { "region-" + it.key }) { g ->
                if (g.items.size == 1) row(g.items[0]) else RegionRow(g, sub(g, g.items.firstOrNull { code(it) == current }),
                    picked = g.items.any { code(it) == current }) { open = g.key }
            }
        }
        drill -> Column {
            Row(Modifier.fillMaxWidth().clickable { open = null }.padding(vertical = 10.dp, horizontal = 4.dp),
                verticalAlignment = Alignment.CenterVertically) {
                TabIcon("ui_ic_back", Modifier.size(18.dp))
                Spacer(Modifier.width(8.dp))
                Text("All places", color = MaterialTheme.colorScheme.primary, fontWeight = FontWeight.SemiBold)
            }
            shown.firstOrNull()?.let { g ->
                Text(g.label.uppercase(), style = MaterialTheme.typography.labelSmall,
                    color = MaterialTheme.colorScheme.onSurfaceVariant, modifier = Modifier.padding(4.dp))
                DrillItems(g.items, grid, modifier, code, row)
            }
        }
        else -> DrillItems(shown.flatMap { it.items }, grid, modifier, code, row)
    }
}

@Composable
private fun <T> DrillItems(items: List<T>, grid: Boolean, modifier: Modifier, code: (T) -> String, row: @Composable (T) -> Unit) {
    if (grid) LazyVerticalGrid(GridCells.Adaptive(120.dp), modifier,
        horizontalArrangement = Arrangement.spacedBy(8.dp), verticalArrangement = Arrangement.spacedBy(8.dp)) {
        items(items, key = code) { row(it) }
    } else LazyColumn(modifier) { items(items, key = code) { row(it) } }
}

/** "United States / 50 states  ›": opens that region's places. */
@Composable
private fun RegionRow(g: StateList.Group<*>, sub: String, picked: Boolean, onOpen: () -> Unit) {
    Row(Modifier.fillMaxWidth().clickable(onClick = onOpen).padding(vertical = 12.dp, horizontal = 4.dp),
        verticalAlignment = Alignment.CenterVertically) {
        Column(Modifier.weight(1f)) {
            Text(g.label, style = MaterialTheme.typography.titleMedium,
                color = if (picked) MaterialTheme.colorScheme.primary else Color.Unspecified)
            Text(sub, style = MaterialTheme.typography.bodySmall,
                color = if (picked) MaterialTheme.colorScheme.primary else MaterialTheme.colorScheme.onSurfaceVariant)
        }
        Text("›", style = MaterialTheme.typography.headlineSmall, color = MaterialTheme.colorScheme.onSurfaceVariant)
    }
    HorizontalDivider()
}

/** One place in a plain list, ✓ on the one already picked. */
@Composable
private fun PlaceRow(st: StateInfo, current: String?, hint: String = "", onPick: (String) -> Unit) {
    Row(Modifier.fillMaxWidth().clickable { onPick(st.code) }.padding(vertical = 12.dp, horizontal = 4.dp),
        verticalAlignment = Alignment.CenterVertically) {
        Text(st.name, Modifier.weight(1f), fontWeight = if (st.code == current) FontWeight.SemiBold else null,
            color = if (st.code == current) MaterialTheme.colorScheme.primary else Color.Unspecified)
        Text(if (st.code == current) "✓" else hint, style = MaterialTheme.typography.bodySmall,
            color = if (st.code == current) MaterialTheme.colorScheme.primary else MaterialTheme.colorScheme.onSurfaceVariant)
    }
}

/** Every place grouped by region, for the first-launch and "where was this taken?" lists. */
@Composable
private fun PlaceList(states: List<StateInfo>, current: String?, modifier: Modifier, onPick: (String) -> Unit) {
    val groups = remember(states) { StateList.groups(states) }
    // Singapore sits among the regions on its own row, with "Asia" beside it.
    val solo = remember(groups) {
        if (StateList.drills(groups)) groups.filter { it.items.size == 1 }.associate { it.items[0].code to it.label } else emptyMap()
    }
    RegionDrill(groups, current, code = { it.code }, modifier = modifier,
        sub = { g, cur -> cur?.let { "✓ ${it.name}" } ?: g.count }) { st ->
        PlaceRow(st, current, hint = solo[st.code].orEmpty(), onPick = onPick)
    }
}

/**
 * "📍 NC" in the top bar opens the player's states: one tile per unlocked state
 * (capturing an animal in a state unlocks it) with how much of its list they've
 * captured. Tapping a tile shows that state's Field Guide, habitat and parks
 * without changing the main state; a button makes the state on screen the main one.
 */
@Composable
fun StateMenu(states: List<StateInfo>, viewing: String, main: String, tiles: List<StateTile>?,
              onOpen: () -> Unit, onClose: () -> Unit, onView: (String) -> Unit, onMakeMain: (String) -> Unit) {
    val name = states.firstOrNull { it.code == viewing }?.name ?: viewing
    TextButton(onClick = onOpen, contentPadding = androidx.compose.foundation.layout.PaddingValues(horizontal = 6.dp),
        colors = androidx.compose.material3.ButtonDefaults.textButtonColors(contentColor = Journal.Cream)) {
        // Visiting another state: its code turns gold (no room for "(visiting)" next to the title).
        Row(verticalAlignment = androidx.compose.ui.Alignment.CenterVertically) {
            TabIcon("ui_ic_pin", Modifier.size(16.dp))
            Spacer(Modifier.width(5.dp))
            val visiting = viewing != main
            Text(viewing, style = MaterialTheme.typography.labelLarge,
                color = if (visiting) Color(0xFF2B1D0E) else Color.Unspecified,
                modifier = if (visiting) Modifier.background(Color(0xFFE0A100), RoundedCornerShape(4.dp)).padding(horizontal = 4.dp) else Modifier)
        }
    }
    if (tiles == null) return
    AlertDialog(onDismissRequest = onClose, confirmButton = {
        if (viewing != main) TextButton(onClick = { onClose(); onMakeMain(viewing) }) { Text("★ Make $name my main ${states.firstOrNull { it.code == viewing }?.word ?: "state"}") }
    },
        dismissButton = { TextButton(onClick = onClose) { Text("Close") } },
        title = { Text("Your places") },
        text = {
            Column(verticalArrangement = Arrangement.spacedBy(8.dp)) {
                Text("Tap one to look at its Field Guide, habitat and parks. Your main one (★) is where you start and what friends see first.",
                    style = MaterialTheme.typography.bodyMedium)
                val groups = remember(tiles, states) { StateList.groups(tiles) { t -> states.firstOrNull { it.code == t.code } } }
                RegionDrill(groups, viewing, code = { it.code }, grid = true,
                    modifier = Modifier.heightIn(max = dialogListMax()),
                    sub = { g, cur -> "${g.items.size} unlocked" + (cur?.let { c -> states.firstOrNull { it.code == c.code }?.name }?.let { " · $it" } ?: "") }) { t ->
                    states.firstOrNull { it.code == t.code }?.let { st ->
                        StateTile(st, main = t.code == viewing,
                            label = if (t.main) "★ Main ${st.word}" else if (t.code == viewing) "Looking now" else "",
                            sub = "${t.caught} of ${t.total} captured") {
                            onClose()
                            if (t.code != viewing) onView(t.code)
                        }
                    }
                }
                if (tiles.size < states.size) {
                    Text("Capture an animal somewhere else to unlock it (${tiles.size} of ${states.size} unlocked).",
                        style = MaterialTheme.typography.bodySmall, color = MaterialTheme.colorScheme.onSurfaceVariant)
                }
            }
        })
}

@Composable
private fun StateTile(st: StateInfo, main: Boolean, label: String, sub: String = "", onClick: () -> Unit) {
    OutlinedCard(onClick = onClick, modifier = Modifier.fillMaxWidth(),
        border = if (main) BorderStroke(2.dp, MaterialTheme.colorScheme.primary) else CardDefaults.outlinedCardBorder()) {
        Column(Modifier.padding(12.dp), verticalArrangement = Arrangement.spacedBy(2.dp)) {
            Text(st.code, style = MaterialTheme.typography.titleLarge, fontWeight = FontWeight.Bold)
            Text(st.name, style = MaterialTheme.typography.bodyMedium)
            if (sub.isNotEmpty()) Text(sub, style = MaterialTheme.typography.bodySmall)
            if (label.isNotEmpty()) Text(label, style = MaterialTheme.typography.labelSmall,
                color = if (main) MaterialTheme.colorScheme.primary else MaterialTheme.colorScheme.onSurfaceVariant,
                fontWeight = if (main) FontWeight.SemiBold else null)
        }
    }
}

/**
 * First launch: which state are you in? The phone's location suggests one; the
 * list below is there when location is off or the guess is wrong.
 */
@Composable
fun StatePicker(states: List<StateInfo>, onDismiss: () -> Unit, onPick: (String) -> Unit) {
    val context = LocalContext.current
    // null: not looked yet; "": looked and found nothing.
    var guess by remember { mutableStateOf<String?>(null) }
    var asked by remember { mutableStateOf(false) }
    fun locate() {
        guess = lastLocation(context)?.let { (lat, lon) -> States.stateAt(states, lat, lon)?.code }.orEmpty()
    }
    val askLocation = rememberLauncherForActivityResult(ActivityResultContracts.RequestMultiplePermissions()) { granted ->
        if (granted.values.any { it }) locate() else guess = ""
    }
    LaunchedEffect(Unit) { if (hasLocationPermission(context)) locate() }
    AlertDialog(onDismissRequest = onDismiss, confirmButton = {},
        dismissButton = { TextButton(onClick = onDismiss) { Text("Close") } },
        title = { Text("Where do you live?") },
        text = {
            Column(verticalArrangement = Arrangement.spacedBy(8.dp)) {
                Text("Your Field Guide and parks follow your main state or country. Photos you take in other places unlock them.",
                    style = MaterialTheme.typography.bodyMedium)
                val found = states.firstOrNull { it.code == guess }
                when {
                    found != null -> StateTile(found, main = true, label = "You're here") { onPick(found.code) }
                    guess == null && !asked -> TextButton(onClick = { asked = true; askLocation.launch(LOCATION_PERMISSIONS) }) {
                        IconText("pin", "Use my location")
                    }
                    guess != null -> Text("Couldn't tell where you are, so pick from the list.",
                        style = MaterialTheme.typography.bodySmall, color = MaterialTheme.colorScheme.onSurfaceVariant)
                }
                Text("OR PICK YOUR STATE OR COUNTRY", style = MaterialTheme.typography.labelSmall,
                    color = MaterialTheme.colorScheme.onSurfaceVariant, modifier = Modifier.padding(top = 4.dp))
                PlaceList(states, current = null, modifier = Modifier.heightIn(max = 300.dp), onPick = onPick)
            }
        })
}

/** Every place by region, to say where a photo was taken. */
@Composable
fun StateListDialog(states: List<StateInfo>, title: String, note: String, current: String? = null,
                    onDismiss: () -> Unit, onPick: (String) -> Unit) {
    AlertDialog(onDismissRequest = onDismiss, confirmButton = {},
        dismissButton = { TextButton(onClick = onDismiss) { Text("Close") } },
        title = { Text(title) },
        text = {
            Column(verticalArrangement = Arrangement.spacedBy(8.dp)) {
                Text(note, style = MaterialTheme.typography.bodyMedium)
                PlaceList(states, current, Modifier.heightIn(max = dialogListMax()), onPick)
            }
        })
}
