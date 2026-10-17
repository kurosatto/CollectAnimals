package com.captureanimals.app

import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.ExperimentalLayoutApi
import androidx.compose.foundation.layout.FlowRow
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.Card
import androidx.compose.material3.CardDefaults
import androidx.compose.material3.LinearProgressIndicator
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.alpha
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.SpanStyle
import androidx.compose.ui.text.buildAnnotatedString
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.withStyle
import androidx.compose.ui.unit.dp
import org.json.JSONArray
import org.json.JSONObject

// Photo stars, sets, weekly challenges, bonds and the buddy: the website's versions
// (backend/app/goals.py, bonds.py, static/index.html), shown the same way in the app.

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

data class Challenge(val title: String, val progress: Int, val goal: Int, val done: Boolean)

/** This week's challenges for the player's state (ChallengesOut). */
data class Week(val endsAt: Long, val challenges: List<Challenge>, val done: Int) {
    companion object {
        fun parse(o: JSONObject): Week {
            val a = o.getJSONArray("challenges")
            return Week(Online.parseTime(o.optStringOrNull("week_end")), List(a.length()) { i ->
                a.getJSONObject(i).let { Challenge(it.getString("title"), it.getInt("progress"), it.getInt("goal"),
                    it.getBoolean("done")) }
            }, o.getInt("done"))
        }
    }
}

data class BondNote(val title: String, val hint: String, val progress: Int, val goal: Int, val done: Boolean)

/** Bond hearts and field notes for one captured animal (BondOut). */
data class Bond(val slug: String, val name: String, val level: Int, val maxLevel: Int, val title: String,
                val notes: List<BondNote>) {
    companion object {
        fun parse(o: JSONObject): Bond {
            val s = o.getJSONObject("species")
            val a = o.optJSONArray("notes") ?: JSONArray()
            return Bond(s.optString("slug"), s.optString("common_name"), o.getInt("level"), o.getInt("max_level"),
                o.optStringOrNull("title") ?: BOND_TITLES.first(), List(a.length()) { i ->
                    a.getJSONObject(i).let { BondNote(it.getString("title"), it.optString("hint"), it.getInt("progress"),
                        it.getInt("goal"), it.getBoolean("done")) }
                })
        }
    }
}

/** The animal the player keeps closest; its mood follows recent outings (BuddyOut). */
data class Buddy(val chosen: Boolean, val bond: Bond, val mood: String, val line: String) {
    companion object {
        fun parse(o: JSONObject) = Buddy(o.getBoolean("chosen"), Bond.parse(o.getJSONObject("bond")),
            o.optString("mood"), o.optString("line"))
    }
}

val BOND_TITLES = listOf("Met", "Familiar", "Regular", "Friend", "Good friend", "Lifelong friend")
private val MOODS = mapOf("napping" to "napping 💤", "happy" to "happy", "excited" to "excited!")

// --- UI ----------------------------------------------------------------------------------

val Gold = Color(0xFFE0A100)
private val Heart = Color(0xFFE0457B)

fun stars(n: Int) = "★".repeat(n.coerceIn(0, 5)) + "☆".repeat(5 - n.coerceIn(0, 5))

@Composable
fun Stars(n: Int, modifier: Modifier = Modifier, points: Int? = null) {
    Text(stars(n) + (points?.let { "  %,d pts".format(it) } ?: ""), color = Gold, modifier = modifier,
        style = MaterialTheme.typography.bodyMedium)
}

@Composable
fun Hearts(n: Int, max: Int = 6) {
    Text(buildAnnotatedString {
        withStyle(SpanStyle(color = Heart)) { append("♥".repeat(n)) }
        withStyle(SpanStyle(color = Heart.copy(alpha = 0.25f))) { append("♥".repeat((max - n).coerceAtLeast(0))) }
    }, style = MaterialTheme.typography.bodyMedium)
}

/** Stars for the photo itself, then the points with each bonus, as on the website. */
@Composable
fun ScoreBox(score: PhotoScore, bondUp: List<String>) {
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
            bondUp.forEach { Text("♥ Field note: $it", color = Heart, style = MaterialTheme.typography.bodyMedium) }
        }
    }
}

/** "This week's challenges" on the Capture tab (signed in). */
@Composable
fun ChallengesCard(week: Week) {
    Card(Modifier.fillMaxWidth()) {
        Column(Modifier.padding(16.dp), verticalArrangement = Arrangement.spacedBy(8.dp)) {
            Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.SpaceBetween) {
                Text("This week's challenges", style = MaterialTheme.typography.titleMedium)
                Text("${week.done} / ${week.challenges.size}", color = MaterialTheme.colorScheme.outline)
            }
            val days = ((week.endsAt - System.currentTimeMillis()) / 86_400_000.0).let { kotlin.math.ceil(it).toInt() }
                .coerceAtLeast(1)
            Text(if (week.done == week.challenges.size) "All done this week. New challenges on Monday!"
                 else "New challenges in $days day${if (days > 1) "s" else ""}.",
                style = MaterialTheme.typography.bodySmall, color = MaterialTheme.colorScheme.outline)
            week.challenges.forEach { c ->
                Column {
                    Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.spacedBy(6.dp)) {
                        Text(if (c.done) "✓" else "•", color = MaterialTheme.colorScheme.primary)
                        Text(c.title, Modifier.weight(1f), style = MaterialTheme.typography.bodyMedium)
                        Text("${c.progress} / ${c.goal}", color = MaterialTheme.colorScheme.outline,
                            style = MaterialTheme.typography.bodySmall)
                    }
                    LinearProgressIndicator(progress = { c.progress / c.goal.coerceAtLeast(1).toFloat() },
                        modifier = Modifier.fillMaxWidth().padding(top = 2.dp))
                }
            }
        }
    }
}

/** The buddy above the habitat: its sprite, hearts, mood and what it says. */
@Composable
fun BuddyCard(b: Buddy, onOpen: (String) -> Unit) {
    Card(Modifier.fillMaxWidth()) {
        Row(Modifier.padding(12.dp), horizontalArrangement = Arrangement.spacedBy(12.dp),
            verticalAlignment = Alignment.CenterVertically) {
            Box(Modifier.size(56.dp).clip(RoundedCornerShape(8.dp)).background(MaterialTheme.colorScheme.surfaceVariant)
                .clickable { onOpen(b.bond.slug) }, contentAlignment = Alignment.Center) {
                PixelSprite(b.bond.slug, caught = true, Modifier.size(48.dp)
                    .let { if (b.mood == "napping") it.alpha(0.7f) else it })
            }
            Column(Modifier.weight(1f)) {
                Text((if (b.chosen) "Your buddy: " else "") + b.bond.name, fontWeight = FontWeight.Bold)
                Row(horizontalArrangement = Arrangement.spacedBy(6.dp), verticalAlignment = Alignment.CenterVertically) {
                    Hearts(b.bond.level, b.bond.maxLevel)
                    Text("${b.bond.title} · ${MOODS[b.mood] ?: b.mood}", style = MaterialTheme.typography.bodySmall,
                        color = MaterialTheme.colorScheme.outline)
                }
                Text(b.line, style = MaterialTheme.typography.bodyMedium)
                if (!b.chosen) Text("Pick any animal you've captured as your buddy from its page.",
                    style = MaterialTheme.typography.bodySmall, color = MaterialTheme.colorScheme.outline)
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

/**
 * Bond hearts and field notes on a captured animal's page, with "Make my buddy".
 * Signed in only: bonds live on the server.
 */
@Composable
fun BondPanel(slug: String, buddySlug: String?, onMakeBuddy: (String) -> Unit) {
    var bond by remember(slug) { mutableStateOf<Bond?>(null) }
    LaunchedEffect(slug) { bond = runCatching { Online.bond(slug) }.getOrNull() }
    val b = bond ?: return
    Card(Modifier.fillMaxWidth()) {
        Column(Modifier.padding(16.dp), verticalArrangement = Arrangement.spacedBy(6.dp)) {
            Row(Modifier.fillMaxWidth(), verticalAlignment = Alignment.CenterVertically) {
                Column(Modifier.weight(1f)) {
                    Text("Bond: ${b.title}", fontWeight = FontWeight.Bold)
                    Hearts(b.level, b.maxLevel)
                }
                OutlinedButton(onClick = { onMakeBuddy(slug) }, enabled = buddySlug != slug) {
                    Text(if (buddySlug == slug) "Your buddy ✓" else "Make my buddy")
                }
            }
            b.notes.forEach { n ->
                Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                    Text(if (n.done) "♥" else "♡", color = Heart)
                    Column(Modifier.weight(1f)) {
                        Text(n.title, style = MaterialTheme.typography.bodyMedium)
                        if (n.hint.isNotBlank()) Text(n.hint, style = MaterialTheme.typography.bodySmall,
                            color = MaterialTheme.colorScheme.outline)
                    }
                    if (!n.done) Text("${n.progress} / ${n.goal}", Modifier.width(48.dp),
                        style = MaterialTheme.typography.bodySmall, color = MaterialTheme.colorScheme.outline)
                }
            }
        }
    }
}
