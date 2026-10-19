package com.captureanimals.app

import android.graphics.BitmapFactory
import androidx.compose.foundation.Image
import androidx.compose.foundation.background
import androidx.compose.foundation.combinedClickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.PaddingValues
import androidx.compose.foundation.layout.aspectRatio
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.lazy.grid.GridCells
import androidx.compose.foundation.lazy.grid.GridItemSpan
import androidx.compose.foundation.lazy.grid.LazyVerticalGrid
import androidx.compose.foundation.lazy.grid.items
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.AlertDialog
import androidx.compose.material3.Card
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.asImageBitmap
import androidx.compose.ui.layout.ContentScale
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.dp

/**
 * Your captures' photos, newest first, four to a row. Tapping a photo opens its Field
 * Guide page; holding it offers to delete it, which un-captures the animal, as on the website.
 */
@Composable
fun GalleryScreen(species: List<Species>, collection: Map<String, Badge>, onOpenDex: (String) -> Unit,
                  onDelete: (String) -> Unit) {
    // Every state's species: photos stay when the player switches state.
    val bySlug = remember(species) { species.associateBy { it.slug } }
    val entries = collection.entries.filter { it.key in bySlug }.sortedByDescending { it.value.firstCaughtAt }
    var confirm by remember { mutableStateOf<Species?>(null) }

    if (entries.isEmpty()) {
        Box(Modifier.fillMaxSize().padding(24.dp), contentAlignment = Alignment.Center) {
            Text("Your photos show up here once you capture your first animal.",
                style = MaterialTheme.typography.bodyLarge, color = MaterialTheme.colorScheme.outline)
        }
        return
    }

    LazyVerticalGrid(columns = GridCells.Fixed(4), modifier = Modifier.fillMaxSize(),
        contentPadding = PaddingValues(10.dp),
        horizontalArrangement = Arrangement.spacedBy(6.dp), verticalArrangement = Arrangement.spacedBy(6.dp)) {
        item(span = { GridItemSpan(maxLineSpan) }) {
            Text("${entries.size} photo${if (entries.size == 1) "" else "s"} · hold one to delete it",
                style = MaterialTheme.typography.labelLarge, color = MaterialTheme.colorScheme.outline)
        }
        items(entries, key = { it.key }) { (slug, badge) ->
            val s = bySlug.getValue(slug)
            Card(shape = RoundedCornerShape(8.dp),
                modifier = Modifier.combinedClickable(onLongClick = { confirm = s }) { onOpenDex(slug) }) {
                Column {
                    // Decoded small: a quarter of the screen wide is all it needs.
                    val photo = remember(badge.photo) {
                        badge.photo?.let { BitmapFactory.decodeFile(it, BitmapFactory.Options().apply { inSampleSize = 4 }) }
                    }
                    Box(Modifier.fillMaxWidth().aspectRatio(1f).clip(RoundedCornerShape(topStart = 8.dp, topEnd = 8.dp))
                        .background(MaterialTheme.colorScheme.surfaceVariant)) {
                        if (photo != null) {
                            Image(photo.asImageBitmap(), contentDescription = s.commonName,
                                modifier = Modifier.fillMaxSize(), contentScale = ContentScale.Crop)
                        }
                    }
                    Text(s.commonName, style = MaterialTheme.typography.labelSmall, maxLines = 1,
                        overflow = TextOverflow.Ellipsis, color = rarityColor(s.rarity),
                        modifier = Modifier.padding(horizontal = 4.dp, vertical = 3.dp))
                }
            }
        }
    }

    confirm?.let { s ->
        AlertDialog(
            onDismissRequest = { confirm = null },
            title = { Text("Delete this photo?") },
            text = { Text("The ${s.commonName} also leaves your collection. Capture it again to get it back.") },
            confirmButton = { TextButton(onClick = { onDelete(s.slug); confirm = null }) { Text("Delete") } },
            dismissButton = { TextButton(onClick = { confirm = null }) { Text("Cancel") } },
        )
    }
}
