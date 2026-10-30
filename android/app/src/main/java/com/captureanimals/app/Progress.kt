package com.captureanimals.app

import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.ExperimentalLayoutApi
import androidx.compose.foundation.layout.FlowRow
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.material3.Card
import androidx.compose.material3.CardDefaults
import androidx.compose.material3.LinearProgressIndicator
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import org.json.JSONArray
import org.json.JSONObject

// Photo stars and sets: the website's versions
// (backend/app/goals.py, static/index.html), shown the same way in the app.

// --- Data --------------------------------------------------------------------------------

/** Points and stars for one photo (ScoreOut). */
data class PhotoScore(val total: Int, val stars: Int, val parts: List<Pair<String, Int>>) {
    companion object {
        fun parse(o: JSONObject?): PhotoScore? = o?.let {
            val a = it.optJSONArray("parts") ?: JSONArray()
            PhotoScore(it.getInt("total"), it.getInt("stars"),
                List(a.length()) { i -> a.getJSONObject(i).let { p -> p.getString("label") to p.getInt("points") } })
        }
    }
}

/** A themed set from species/sets.json, resolved for one state. */
data class SetDef(val id: String, val title: String, val description: String, val slugs: List<String>)

/**
 * species/sets.json, read the way goals.sets_for() does: a state shows the sets with at
 * least [MIN_SET_SIZE] of its animals, leaving out ones with a danger safety rating.
 * The app works the sets out itself, so they show offline too.
 */
class SetCatalog(private val sets: List<JSONObject>) {
    fun forState(code: String, members: Set<String>, safety: (String) -> String?): List<SetDef> = sets.mapNotNull { s ->
        val list = s.optJSONObject("species_by_state")?.optJSONArray(code) ?: s.optJSONArray("species") ?: JSONArray()
        val slugs = List(list.length()) { list.getString(it) }.filter { it in members && safety(it) != "danger" }
        if (slugs.size < MIN_SET_SIZE) null
        else SetDef(s.getString("id"), s.getString("title"), s.optString("description"), slugs)
    }

    companion object {
        const val MIN_SET_SIZE = 3
        fun parse(json: String?): SetCatalog {
            val a = json?.let { JSONObject(it).optJSONArray("sets") } ?: JSONArray()
            return SetCatalog(List(a.length()) { a.getJSONObject(it) })
        }
    }
}

// --- UI ----------------------------------------------------------------------------------

val Gold = Color(0xFFE0A100)

fun stars(n: Int) = "★".repeat(n.coerceIn(0, 5)) + "☆".repeat(5 - n.coerceIn(0, 5))

@Composable
fun Stars(n: Int, modifier: Modifier = Modifier, points: Int? = null) {
    Text(stars(n) + (points?.let { "  %,d pts".format(it) } ?: ""), color = Gold, modifier = modifier,
        style = MaterialTheme.typography.bodyMedium)
}

/** Stars for the photo itself, then the points with each bonus, as on the website. */
@Composable
fun ScoreBox(score: PhotoScore) {
    Card(colors = CardDefaults.cardColors(containerColor = Gold.copy(alpha = 0.12f)), modifier = Modifier.fillMaxWidth()) {
        Column(Modifier.padding(12.dp), verticalArrangement = Arrangement.spacedBy(2.dp)) {
            Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.SpaceBetween,
                verticalAlignment = Alignment.CenterVertically) {
                Text(stars(score.stars), color = Gold, style = MaterialTheme.typography.titleLarge)
                Text("%,d pts".format(score.total), style = MaterialTheme.typography.titleMedium, fontWeight = FontWeight.Bold)
            }
            score.parts.forEach { (label, points) ->
                Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.SpaceBetween) {
                    Text(label, style = MaterialTheme.typography.bodyMedium)
                    Text("+$points", style = MaterialTheme.typography.bodyMedium)
                }
            }
        }
    }
}

/** One set: progress and its animals (in colour once captured). */
@OptIn(ExperimentalLayoutApi::class)
@Composable
fun SetCard(set: SetDef, collection: Map<String, Badge>, onOpen: (String) -> Unit) {
    val caught = set.slugs.count { it in collection }
    val complete = caught == set.slugs.size
    Card(Modifier.fillMaxWidth(), colors = CardDefaults.cardColors(containerColor =
        if (complete) Gold.copy(alpha = 0.15f) else MaterialTheme.colorScheme.surface)) {
        Column(Modifier.padding(12.dp), verticalArrangement = Arrangement.spacedBy(6.dp)) {
            Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.SpaceBetween) {
                Text((if (complete) "🏅 " else "") + set.title, fontWeight = FontWeight.Bold)
                Text("$caught / ${set.slugs.size}", color = MaterialTheme.colorScheme.outline)
            }
            LinearProgressIndicator(progress = { caught / set.slugs.size.toFloat() }, modifier = Modifier.fillMaxWidth())
            FlowRow(horizontalArrangement = Arrangement.spacedBy(4.dp), verticalArrangement = Arrangement.spacedBy(4.dp)) {
                set.slugs.forEach { slug ->
                    PixelSprite(slug, caught = slug in collection, Modifier.size(36.dp).clickable { onOpen(slug) })
                }
            }
            Text(set.description, style = MaterialTheme.typography.bodySmall, color = MaterialTheme.colorScheme.outline)
        }
    }
}

