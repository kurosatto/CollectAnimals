package com.collectanimals.app

import android.graphics.BitmapFactory
import android.net.Uri
import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.rememberLauncherForActivityResult
import androidx.activity.compose.setContent
import androidx.activity.enableEdgeToEdge
import androidx.activity.result.PickVisualMediaRequest
import androidx.activity.result.contract.ActivityResultContracts
import androidx.compose.foundation.Image
import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.clickable
import androidx.compose.foundation.horizontalScroll
import androidx.compose.foundation.isSystemInDarkTheme
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.aspectRatio
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.lazy.grid.GridCells
import androidx.compose.foundation.lazy.grid.GridItemSpan
import androidx.compose.foundation.lazy.grid.LazyVerticalGrid
import androidx.compose.foundation.lazy.grid.items
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.AlertDialog
import androidx.compose.material3.Button
import androidx.compose.material3.Card
import androidx.compose.material3.CardDefaults
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.FilterChip
import androidx.compose.material3.LinearProgressIndicator
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Tab
import androidx.compose.material3.TabRow
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.material3.TopAppBar
import androidx.compose.material3.darkColorScheme
import androidx.compose.material3.lightColorScheme
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableIntStateOf
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.saveable.rememberSaveable
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.asImageBitmap
import androidx.compose.ui.layout.ContentScale
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.font.FontStyle
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.core.content.FileProvider
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import androidx.lifecycle.viewmodel.compose.viewModel
import java.io.File
import java.text.DateFormat
import java.util.Date

class MainActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        enableEdgeToEdge()
        setContent {
            MaterialTheme(colorScheme = if (isSystemInDarkTheme()) darkColorScheme(primary = Forest80)
                                        else lightColorScheme(primary = Forest40)) {
                App()
            }
        }
    }
}

private val Forest40 = Color(0xFF2E6B3F)
private val Forest80 = Color(0xFF8FD3A0)

fun rarityColor(rarity: String): Color = when (rarity) {
    "legendary" -> Color(0xFFE0A100)
    "rare" -> Color(0xFF7B4FD6)
    "uncommon" -> Color(0xFF2F80ED)
    else -> Color(0xFF6B7B6E)
}

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun App(vm: GameViewModel = viewModel()) {
    val state by vm.state.collectAsStateWithLifecycle()
    var tab by rememberSaveable { mutableIntStateOf(0) }
    val info = state.info
    val total = info?.species?.size ?: 0

    Scaffold(topBar = {
        Column {
            TopAppBar(title = { Text("CollectAnimals") })
            if (info != null) {
                Column(Modifier.padding(horizontal = 16.dp)) {
                    Text("${state.collection.size} / $total California species caught",
                        style = MaterialTheme.typography.bodyMedium)
                    Spacer(Modifier.height(4.dp))
                    LinearProgressIndicator(
                        progress = { if (total == 0) 0f else state.collection.size / total.toFloat() },
                        modifier = Modifier.fillMaxWidth())
                    Spacer(Modifier.height(8.dp))
                }
            }
            TabRow(selectedTabIndex = tab) {
                Tab(selected = tab == 0, onClick = { tab = 0 }, text = { Text("Catch") })
                Tab(selected = tab == 1, onClick = { tab = 1 }, text = { Text("Collection") })
            }
        }
    }) { padding ->
        Box(Modifier.padding(padding).fillMaxSize()) {
            when {
                info == null -> CircularProgressIndicator(Modifier.align(Alignment.Center))
                tab == 0 -> CatchScreen(state, vm::capture, vm::dismissResult)
                else -> CollectionScreen(info, state.collection)
            }
        }
    }
}

@Composable
fun CatchScreen(state: UiState, onPhoto: (Uri) -> Unit, onDismiss: () -> Unit) {
    val context = LocalContext.current
    var pendingCameraUri by rememberSaveable { mutableStateOf<Uri?>(null) }
    val takePicture = rememberLauncherForActivityResult(ActivityResultContracts.TakePicture()) { ok ->
        val uri = pendingCameraUri
        if (ok && uri != null) onPhoto(uri)
    }
    val pickPhoto = rememberLauncherForActivityResult(ActivityResultContracts.PickVisualMedia()) { uri ->
        if (uri != null) onPhoto(uri)
    }
    fun launchCamera() {
        val dir = File(context.cacheDir, "captures").apply { mkdirs() }
        val file = File(dir, "capture-${System.currentTimeMillis()}.jpg")
        val uri = FileProvider.getUriForFile(context, "${context.packageName}.files", file)
        pendingCameraUri = uri
        takePicture.launch(uri)
    }

    Column(
        Modifier.fillMaxSize().verticalScroll(rememberScrollState()).padding(16.dp),
        horizontalAlignment = Alignment.CenterHorizontally,
        verticalArrangement = Arrangement.spacedBy(12.dp),
    ) {
        Text("Photograph a wild animal. If it's one of the 100 California species, you earn its badge.",
            style = MaterialTheme.typography.bodyLarge, textAlign = TextAlign.Center)
        Row(horizontalArrangement = Arrangement.spacedBy(12.dp)) {
            Button(onClick = ::launchCamera, enabled = !state.busy) { Text("Take photo") }
            OutlinedButton(
                onClick = { pickPhoto.launch(PickVisualMediaRequest(ActivityResultContracts.PickVisualMedia.ImageOnly)) },
                enabled = !state.busy,
            ) { Text("Choose photo") }
        }
        if (state.busy) {
            CircularProgressIndicator()
            Text("Identifying…", style = MaterialTheme.typography.bodyMedium)
        }
        state.error?.let { Text(it, color = MaterialTheme.colorScheme.error) }
        state.result?.let { ResultCard(it, onDismiss) }
    }
}

@Composable
fun ResultCard(r: CaptureResult, onDismiss: () -> Unit) {
    Card(Modifier.fillMaxWidth()) {
        Column(Modifier.padding(16.dp), verticalArrangement = Arrangement.spacedBy(8.dp)) {
            Image(r.photo.asImageBitmap(), contentDescription = "Your photo",
                modifier = Modifier.fillMaxWidth().aspectRatio(r.photo.width / r.photo.height.toFloat())
                    .clip(RoundedCornerShape(12.dp)),
                contentScale = ContentScale.Crop)
            if (r.matched && r.species != null) {
                Text(if (r.newBadge) "New badge!" else "Caught again",
                    style = MaterialTheme.typography.labelLarge, color = rarityColor(r.species.rarity))
                Text(r.species.commonName, style = MaterialTheme.typography.headlineSmall, fontWeight = FontWeight.Bold)
                Text(r.species.scientificName, fontStyle = FontStyle.Italic)
                RarityTag(r.species.rarity)
            }
            Text(r.message, style = MaterialTheme.typography.bodyLarge)
            Text("Top guesses", style = MaterialTheme.typography.labelLarge)
            r.guesses.forEach { g ->
                Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.SpaceBetween) {
                    Text(g.name)
                    Text("${(g.probability * 100).toInt()}%")
                }
            }
            TextButton(onClick = onDismiss, modifier = Modifier.align(Alignment.End)) { Text("Done") }
        }
    }
}

@Composable
fun RarityTag(rarity: String) {
    Text(rarity.replaceFirstChar { it.uppercase() }, color = Color.White, fontSize = 12.sp,
        modifier = Modifier.clip(RoundedCornerShape(50)).background(rarityColor(rarity))
            .padding(horizontal = 10.dp, vertical = 2.dp))
}

@Composable
fun CollectionScreen(info: ModelInfo, collection: Map<String, Badge>) {
    val categories = remember(info) { listOf("all") + info.species.map { it.category }.distinct() }
    var category by rememberSaveable { mutableStateOf("all") }
    var selected by remember { mutableStateOf<Species?>(null) }
    val shown = info.species.filter { category == "all" || it.category == category }

    LazyVerticalGrid(columns = GridCells.Adaptive(104.dp), modifier = Modifier.fillMaxSize(),
        contentPadding = androidx.compose.foundation.layout.PaddingValues(12.dp),
        horizontalArrangement = Arrangement.spacedBy(8.dp), verticalArrangement = Arrangement.spacedBy(8.dp)) {
        item(span = { GridItemSpan(maxLineSpan) }) {
            Row(Modifier.horizontalScrollCompat(), horizontalArrangement = Arrangement.spacedBy(6.dp)) {
                categories.forEach { c ->
                    FilterChip(selected = category == c, onClick = { category = c },
                        label = { Text(c.replaceFirstChar { it.uppercase() }) })
                }
            }
        }
        items(shown, key = { it.slug }) { s -> SpeciesTile(s, collection[s.slug]) { selected = s } }
    }
    selected?.let { s -> SpeciesDialog(s, collection[s.slug]) { selected = null } }
}

@Composable
private fun Modifier.horizontalScrollCompat(): Modifier =
    this.then(Modifier.fillMaxWidth()).then(Modifier.horizontalScroll(rememberScrollState()))

@Composable
fun SpeciesTile(s: Species, badge: Badge?, onClick: () -> Unit) {
    val caught = badge != null
    Card(
        modifier = Modifier.clickable(onClick = onClick)
            .border(2.dp, if (caught) rarityColor(s.rarity) else Color.Transparent, RoundedCornerShape(12.dp)),
        shape = RoundedCornerShape(12.dp),
        colors = CardDefaults.cardColors(containerColor =
            if (caught) MaterialTheme.colorScheme.surfaceVariant else MaterialTheme.colorScheme.surface),
    ) {
        Column(Modifier.padding(6.dp), horizontalAlignment = Alignment.CenterHorizontally) {
            Box(Modifier.fillMaxWidth().aspectRatio(1f).clip(RoundedCornerShape(8.dp))
                .background(MaterialTheme.colorScheme.surfaceVariant), contentAlignment = Alignment.Center) {
                val thumb = remember(badge?.photo) { badge?.photo?.let { BitmapFactory.decodeFile(it) } }
                if (thumb != null) {
                    Image(thumb.asImageBitmap(), contentDescription = s.commonName,
                        modifier = Modifier.fillMaxSize(), contentScale = ContentScale.Crop)
                } else {
                    Text("?", fontSize = 32.sp, color = MaterialTheme.colorScheme.outline)
                }
            }
            Spacer(Modifier.height(4.dp))
            Text(s.commonName, style = MaterialTheme.typography.labelMedium, maxLines = 2,
                overflow = TextOverflow.Ellipsis, textAlign = TextAlign.Center,
                color = if (caught) MaterialTheme.colorScheme.onSurface else MaterialTheme.colorScheme.outline)
            Box(Modifier.padding(top = 2.dp).size(8.dp).clip(RoundedCornerShape(50)).background(rarityColor(s.rarity)))
        }
    }
}

@Composable
fun SpeciesDialog(s: Species, badge: Badge?, onClose: () -> Unit) {
    AlertDialog(
        onDismissRequest = onClose,
        confirmButton = { TextButton(onClick = onClose) { Text("Close") } },
        title = { Text(s.commonName) },
        text = {
            Column(verticalArrangement = Arrangement.spacedBy(6.dp)) {
                Text(s.scientificName, fontStyle = FontStyle.Italic)
                Row(horizontalArrangement = Arrangement.spacedBy(8.dp), verticalAlignment = Alignment.CenterVertically) {
                    RarityTag(s.rarity)
                    Text(s.category.replaceFirstChar { it.uppercase() })
                }
                if (badge != null) {
                    Text("Caught ${badge.count}× — first on " +
                        DateFormat.getDateInstance(DateFormat.MEDIUM).format(Date(badge.firstCaughtAt)))
                } else {
                    Text("Not caught yet.")
                }
            }
        },
    )
}
