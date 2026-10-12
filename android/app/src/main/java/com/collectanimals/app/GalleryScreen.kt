package com.collectanimals.app

import android.graphics.BitmapFactory
import androidx.compose.foundation.Image
import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
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
import java.text.DateFormat
import java.util.Date

/**
 * Your catches' photos, newest first. Tapping a photo opens its Pokédex page;
 * "Delete photo" removes the photo and un-catches the animal, as on the website.
 */
@Composable
fun GalleryScreen(info: ModelInfo, collection: Map<String, Badge>, onOpenDex: (String) -> Unit,
                  onDelete: (String) -> Unit) {
    val bySlug = remember(info) { info.species.associateBy { it.slug } }
    val entries = collection.entries.filter { it.key in bySlug }.sortedByDescending { it.value.firstCaughtAt }
    var confirm by remember { mutableStateOf<Species?>(null) }

    if (entries.isEmpty()) {
        Box(Modifier.fillMaxSize().padding(24.dp), contentAlignment = Alignment.Center) {
            Text("Your photos show up here once you catch your first animal.",
                style = MaterialTheme.typography.bodyLarge, color = MaterialTheme.colorScheme.outline)
        }
        return
    }

    LazyVerticalGrid(columns = GridCells.Adaptive(150.dp), modifier = Modifier.fillMaxSize(),
        contentPadding = PaddingValues(12.dp),
        horizontalArrangement = Arrangement.spacedBy(10.dp), verticalArrangement = Arrangement.spacedBy(10.dp)) {
        item(span = { GridItemSpan(maxLineSpan) }) {
            Text("${entries.size} photo${if (entries.size == 1) "" else "s"}",
                style = MaterialTheme.typography.labelLarge, color = MaterialTheme.colorScheme.outline)
        }
        items(entries, key = { it.key }) { (slug, badge) ->
            val s = bySlug.getValue(slug)
            Card(shape = RoundedCornerShape(12.dp)) {
                Column {
                    val photo = remember(badge.photo) { badge.photo?.let { BitmapFactory.decodeFile(it) } }
                    Box(Modifier.fillMaxWidth().aspectRatio(1f).clip(RoundedCornerShape(topStart = 12.dp, topEnd = 12.dp))
                        .background(MaterialTheme.colorScheme.surfaceVariant).clickable { onOpenDex(slug) }) {
                        if (photo != null) {
                            Image(photo.asImageBitmap(), contentDescription = s.commonName,
                                modifier = Modifier.fillMaxSize(), contentScale = ContentScale.Crop)
                        }
                    }
                    Column(Modifier.padding(horizontal = 10.dp, vertical = 8.dp)) {
                        Text(s.commonName, style = MaterialTheme.typography.titleSmall, maxLines = 1,
                            overflow = TextOverflow.Ellipsis, color = rarityColor(s.rarity))
                        Text(DateFormat.getDateInstance(DateFormat.MEDIUM).format(Date(badge.firstCaughtAt)) +
                            if (badge.count > 1) " · ${badge.count}×" else "",
                            style = MaterialTheme.typography.bodySmall, color = MaterialTheme.colorScheme.outline)
                        TextButton(onClick = { confirm = s }, contentPadding = PaddingValues(0.dp)) {
                            Text("Delete photo")
                        }
                    }
                }
            }
        }
    }

    confirm?.let { s ->
        AlertDialog(
            onDismissRequest = { confirm = null },
            title = { Text("Delete this photo?") },
            text = { Text("The ${s.commonName} also leaves your collection. Catch it again to get it back.") },
            confirmButton = { TextButton(onClick = { onDelete(s.slug); confirm = null }) { Text("Delete") } },
            dismissButton = { TextButton(onClick = { confirm = null }) { Text("Cancel") } },
        )
    }
}
