package com.captureanimals.app

import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.heightIn
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.text.KeyboardActions
import androidx.compose.foundation.text.KeyboardOptions
import androidx.compose.material3.AlertDialog
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.saveable.rememberSaveable
import androidx.compose.runtime.setValue
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.input.ImeAction
import androidx.compose.ui.unit.dp

/** One row of the state list; [header] rows are the "Your states" / "Other states" labels. */
data class StateRow(val code: String, val name: String, val locked: Boolean = false, val header: Boolean = false)

object StateSearch {
    /**
     * The picker's rows for a search: the player's own states first, then the rest
     * A to Z (locked when the player has some states of their own). A query matches
     * any part of a name, or a code exactly ("nc").
     */
    fun rows(states: List<StateInfo>, query: String, mine: Set<String>): List<StateRow> {
        val q = query.trim().lowercase()
        val hits = states.filter { q.isEmpty() || q in it.name.lowercase() || it.code.lowercase() == q }
        val own = hits.filter { it.code in mine }.map { StateRow(it.code, it.name) }
        val rest = hits.filter { it.code !in mine }.sortedBy { it.name }.map { StateRow(it.code, it.name, locked = mine.isNotEmpty()) }
        return buildList {
            if (own.isNotEmpty()) { add(StateRow("", "Your states", header = true)); addAll(own) }
            if (own.isNotEmpty() && rest.isNotEmpty()) add(StateRow("", "Other states", header = true))
            addAll(rest)
        }
    }
}

/** "📍 NC" in the top bar; switching changes the Field Guide, parks and which animals count. */
@Composable
fun StateMenu(states: List<StateInfo>, current: String, unlocked: Set<String>, onPick: (String) -> Unit) {
    var open by remember { mutableStateOf(false) }
    // A locked state asks first: players unlock new states by choice.
    var unlocking by remember { mutableStateOf<StateInfo?>(null) }
    TextButton(onClick = { open = true }) { Text("📍 $current") }
    if (open) {
        StatePickerDialog(states, "Primary location", "Your Field Guide, parks and challenges follow it.",
            current = current, mine = unlocked, onDismiss = { open = false }) { code ->
            open = false
            when {
                code == current -> {}
                code !in unlocked -> unlocking = states.first { it.code == code }
                else -> onPick(code)
            }
        }
    }
    unlocking?.let { s ->
        AlertDialog(onDismissRequest = { unlocking = null },
            title = { Text("Unlock ${s.name}?") },
            text = { Text("Its Field Guide, parks and challenges will open, and your captures will count there while it's your state.") },
            confirmButton = { TextButton(onClick = { unlocking = null; onPick(s.code) }) { Text("Unlock") } },
            dismissButton = { TextButton(onClick = { unlocking = null }) { Text("Not now") } })
    }
}

/** First launch: which state are you in? Same question as the website's sign-up. */
@Composable
fun StatePicker(states: List<StateInfo>, onDismiss: () -> Unit, onPick: (String) -> Unit) {
    StatePickerDialog(states, "Which state are you in?",
        "Your Field Guide and parks follow your state. You can change it any time with 📍 at the top.",
        current = null, mine = emptySet(), onDismiss = onDismiss, onPick = onPick)
}

/** All 50 states in a searchable list. */
@Composable
fun StatePickerDialog(states: List<StateInfo>, title: String, note: String, current: String?, mine: Set<String>,
                      onDismiss: () -> Unit, onPick: (String) -> Unit) {
    var query by rememberSaveable { mutableStateOf("") }
    val rows = remember(states, query, mine) { StateSearch.rows(states, query, mine) }
    AlertDialog(onDismissRequest = onDismiss, confirmButton = {},
        dismissButton = { TextButton(onClick = onDismiss) { Text("Close") } },
        title = { Text(title) },
        text = {
            Column(verticalArrangement = Arrangement.spacedBy(8.dp)) {
                Text(note, style = MaterialTheme.typography.bodyMedium)
                OutlinedTextField(query, { query = it }, Modifier.fillMaxWidth(), singleLine = true,
                    placeholder = { Text("Search states") },
                    keyboardOptions = KeyboardOptions(imeAction = ImeAction.Done),
                    // Done picks the first match, so "ore" + Done is Oregon.
                    keyboardActions = KeyboardActions(onDone = { rows.firstOrNull { !it.header }?.let { onPick(it.code) } }))
                if (rows.isEmpty()) Text("No state matches.", color = MaterialTheme.colorScheme.onSurfaceVariant)
                LazyColumn(Modifier.heightIn(max = 360.dp)) {
                    items(rows, key = { it.code + it.name }) { r ->
                        if (r.header) {
                            Text(r.name.uppercase(), style = MaterialTheme.typography.labelSmall,
                                color = MaterialTheme.colorScheme.onSurfaceVariant,
                                modifier = Modifier.padding(top = 8.dp, bottom = 2.dp))
                        } else {
                            Row(Modifier.fillMaxWidth().clickable { onPick(r.code) }.padding(vertical = 10.dp, horizontal = 4.dp),
                                horizontalArrangement = Arrangement.SpaceBetween) {
                                Text((if (r.locked) "🔒 " else "") + r.name,
                                    fontWeight = if (r.code == current) FontWeight.SemiBold else null,
                                    color = if (r.code == current) MaterialTheme.colorScheme.primary else MaterialTheme.colorScheme.onSurface)
                                if (r.code == current) Text("✓", color = MaterialTheme.colorScheme.primary)
                            }
                        }
                    }
                }
            }
        })
}
