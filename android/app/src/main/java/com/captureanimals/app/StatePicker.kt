package com.captureanimals.app

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
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp

object StateList {
    /** The player's unlocked states, in states.json order (the state screen's tiles). */
    fun tiles(states: List<StateInfo>, unlocked: Set<String>): List<StateInfo> = states.filter { it.code in unlocked }

    /** Every state A to Z, for the first-launch list. */
    fun alphabetical(states: List<StateInfo>): List<StateInfo> = states.sortedBy { it.name }
}

/**
 * "📍 NC" in the top bar opens the player's states: one tile per unlocked state
 * (a photo taken in a state unlocks it). Tapping a tile makes it the main state,
 * which the Field Guide, parks and challenges follow.
 */
@Composable
fun StateMenu(states: List<StateInfo>, current: String, unlocked: Set<String>, onPick: (String) -> Unit) {
    var open by remember { mutableStateOf(false) }
    TextButton(onClick = { open = true }) { Text("📍 $current") }
    if (!open) return
    val tiles = remember(states, unlocked) { StateList.tiles(states, unlocked) }
    AlertDialog(onDismissRequest = { open = false }, confirmButton = {},
        dismissButton = { TextButton(onClick = { open = false }) { Text("Close") } },
        title = { Text("Your states") },
        text = {
            Column(verticalArrangement = Arrangement.spacedBy(8.dp)) {
                Text("Your Field Guide, parks and challenges follow your main state. Tap a state to make it your main one.",
                    style = MaterialTheme.typography.bodyMedium)
                LazyVerticalGrid(GridCells.Adaptive(120.dp), Modifier.heightIn(max = 360.dp),
                    horizontalArrangement = Arrangement.spacedBy(8.dp), verticalArrangement = Arrangement.spacedBy(8.dp)) {
                    items(tiles, key = { it.code }) { st ->
                        StateTile(st, main = st.code == current, label = if (st.code == current) "★ Main state" else "Make main") {
                            open = false
                            if (st.code != current) onPick(st.code)
                        }
                    }
                }
                if (tiles.size < states.size) {
                    Text("📷 Take a photo in another state to unlock it (${tiles.size} of ${states.size} unlocked).",
                        style = MaterialTheme.typography.bodySmall, color = MaterialTheme.colorScheme.onSurfaceVariant)
                }
            }
        })
}

@Composable
private fun StateTile(st: StateInfo, main: Boolean, label: String, onClick: () -> Unit) {
    OutlinedCard(onClick = onClick, modifier = Modifier.fillMaxWidth(),
        border = if (main) BorderStroke(2.dp, MaterialTheme.colorScheme.primary) else CardDefaults.outlinedCardBorder()) {
        Column(Modifier.padding(12.dp), verticalArrangement = Arrangement.spacedBy(2.dp)) {
            Text(st.code, style = MaterialTheme.typography.titleLarge, fontWeight = FontWeight.Bold)
            Text(st.name, style = MaterialTheme.typography.bodyMedium)
            Text(label, style = MaterialTheme.typography.labelSmall,
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
    val rows = remember(states) { StateList.alphabetical(states) }
    AlertDialog(onDismissRequest = onDismiss, confirmButton = {},
        dismissButton = { TextButton(onClick = onDismiss) { Text("Close") } },
        title = { Text("Which state are you in?") },
        text = {
            Column(verticalArrangement = Arrangement.spacedBy(8.dp)) {
                Text("Your Field Guide and parks follow your main state. Photos you take in other states unlock them.",
                    style = MaterialTheme.typography.bodyMedium)
                val found = states.firstOrNull { it.code == guess }
                when {
                    found != null -> StateTile(found, main = true, label = "📍 You're here") { onPick(found.code) }
                    guess == null && !asked -> TextButton(onClick = { asked = true; askLocation.launch(LOCATION_PERMISSIONS) }) {
                        Text("📍 Use my location")
                    }
                    guess != null -> Text("Couldn't tell where you are, so pick from the list.",
                        style = MaterialTheme.typography.bodySmall, color = MaterialTheme.colorScheme.onSurfaceVariant)
                }
                Text("OR PICK YOUR STATE", style = MaterialTheme.typography.labelSmall,
                    color = MaterialTheme.colorScheme.onSurfaceVariant, modifier = Modifier.padding(top = 4.dp))
                LazyColumn(Modifier.heightIn(max = 300.dp)) {
                    items(rows, key = { it.code }) { st ->
                        Row(Modifier.fillMaxWidth().clickable { onPick(st.code) }.padding(vertical = 10.dp, horizontal = 4.dp)) {
                            Text(st.name)
                        }
                    }
                }
            }
        })
}

/** Every state A to Z, to say where a photo was taken. */
@Composable
fun StateListDialog(states: List<StateInfo>, title: String, note: String, onDismiss: () -> Unit, onPick: (String) -> Unit) {
    val rows = remember(states) { StateList.alphabetical(states) }
    AlertDialog(onDismissRequest = onDismiss, confirmButton = {},
        dismissButton = { TextButton(onClick = onDismiss) { Text("Close") } },
        title = { Text(title) },
        text = {
            Column(verticalArrangement = Arrangement.spacedBy(8.dp)) {
                Text(note, style = MaterialTheme.typography.bodyMedium)
                LazyColumn(Modifier.heightIn(max = 360.dp)) {
                    items(rows, key = { it.code }) { st ->
                        Row(Modifier.fillMaxWidth().clickable { onPick(st.code) }.padding(vertical = 10.dp, horizontal = 4.dp)) {
                            Text(st.name)
                        }
                    }
                }
            }
        })
}
