package com.captureanimals.app

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
import androidx.compose.foundation.layout.heightIn
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.widthIn
import androidx.compose.foundation.lazy.grid.GridCells
import androidx.compose.foundation.lazy.grid.GridItemSpan
import androidx.compose.foundation.lazy.grid.LazyVerticalGrid
import androidx.compose.foundation.lazy.grid.items
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.AlertDialog
import androidx.compose.material3.Button
import androidx.compose.material3.DropdownMenu
import androidx.compose.material3.DropdownMenuItem
import androidx.compose.material3.Card
import androidx.compose.material3.CardDefaults
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.FilterChip
import androidx.compose.material3.HorizontalDivider
import androidx.compose.material3.LinearProgressIndicator
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.NavigationBar
import androidx.compose.material3.NavigationBarItem
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.Scaffold
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
fun App(vm: GameViewModel = viewModel(), social: SocialViewModel = viewModel()) {
    val state by vm.state.collectAsStateWithLifecycle()
    var tabChoice by rememberSaveable { mutableIntStateOf(0) }
    var showAccount by rememberSaveable { mutableStateOf(false) }
    // A different player (or none) sees nothing of the last one's feed and album.
    androidx.compose.runtime.LaunchedEffect(state.account?.username) { social.clear() }
    if (showAccount) AccountDialog(state, vm) { showAccount = false }
    var dexSlug by rememberSaveable { mutableStateOf<String?>(null) }
    val info = state.info
    val dex = state.fieldGuide
    // A state without park data yet has no Parks tab, so fall back to Capture.
    val tab = if (TABS[tabChoice].key == "hotspots" && dex?.parks.isNullOrEmpty()) 0 else tabChoice
    // The state's own entry, or another state's species from the Photos tab.
    val entry = dexSlug?.let { slug ->
        info?.species?.firstOrNull { it.slug == slug } ?: state.allSpecies.firstOrNull { it.slug == slug }
    }
    if (info != null && dex != null && entry != null) {
        Scaffold { padding ->
            Box(Modifier.padding(padding)) {
                DexEntryScreen(info.dexNumber(entry.slug), entry, state.collection[entry.slug], dex) { dexSlug = null }
            }
        }
        return
    }
    if (state.needsStatePick && state.states.size > 1) {
        StatePicker(state.states, onDismiss = { vm.chooseState(state.stateCode) }, onPick = vm::chooseState)
    }
    val total = info?.species?.size ?: 0
    // Badges are per species, so a coyote captured in one state counts in every state that lists it.
    val captured = info?.species?.count { it.slug in state.collection } ?: 0

    Scaffold(topBar = {
        Column {
            TopAppBar(title = { Text(if (tab == 0) "Capture Animals" else TABS[tab].title) }, actions = {
                if (state.states.size > 1) StateMenu(state.states, state.stateCode, vm::chooseState)
                TextButton(onClick = { showAccount = true }) {
                    Text(state.account?.let { "👤 ${it.username}" } ?: "Log in", maxLines = 1,
                        overflow = TextOverflow.Ellipsis, modifier = Modifier.widthIn(max = 120.dp))
                }
            })
            if (info != null) {
                Column(Modifier.padding(horizontal = 16.dp)) {
                    Text("$captured / $total ${dex?.region ?: ""} species captured",
                        style = MaterialTheme.typography.bodyMedium)
                    Spacer(Modifier.height(4.dp))
                    LinearProgressIndicator(
                        progress = { if (total == 0) 0f else captured / total.toFloat() },
                        modifier = Modifier.fillMaxWidth())
                    Spacer(Modifier.height(8.dp))
                }
            }
        }
    }, bottomBar = {
        // One screen per job instead of one long page; Hotspots only once its data is there.
        NavigationBar {
            TABS.forEachIndexed { i, t ->
                if (t.key == "hotspots" && dex?.parks.isNullOrEmpty()) return@forEachIndexed
                NavigationBarItem(selected = tab == i, onClick = { tabChoice = i },
                    icon = { TabIcon(t.icon, Modifier.size(28.dp)) }, label = { Text(t.title) })
            }
        }
    }) { padding ->
        Box(Modifier.padding(padding).fillMaxSize()) {
            when {
                info == null -> CircularProgressIndicator(Modifier.align(Alignment.Center))
                TABS[tab].key == "catch" -> CatchScreen(state, vm::capture, vm::dismissResult, vm::pick) { dexSlug = it }
                TABS[tab].key == "social" -> SocialScreen(state, social, onSignIn = { showAccount = true }) { dexSlug = it }
                TABS[tab].key == "gallery" && state.account != null ->
                    OnlinePhotosScreen(social, onOpenDex = { dexSlug = it }, onDeleted = vm::reloadCollection)
                TABS[tab].key == "collection" -> CollectionScreen(info, dex, state.collection) { dexSlug = it }
                TABS[tab].key == "gallery" -> GalleryScreen(state.allSpecies, state.collection, onOpenDex = { dexSlug = it },
                    onDelete = vm::deleteCatch)
                dex != null -> HotspotsScreen(info, dex, state.collection, onOpenDex = { dexSlug = it })
            }
        }
    }
}

/** "📍 NC" in the top bar; switching changes the Field Guide, parks and which animals count. */
@Composable
private fun StateMenu(states: List<StateInfo>, current: String, onPick: (String) -> Unit) {
    var open by remember { mutableStateOf(false) }
    Box {
        TextButton(onClick = { open = true }) { Text("📍 $current") }
        DropdownMenu(expanded = open, onDismissRequest = { open = false }) {
            states.forEach { s ->
                DropdownMenuItem(text = { Text(s.name) }, onClick = { open = false; onPick(s.code) })
            }
        }
    }
}

/** First launch: which state are you in? Same question as the website's sign-up. */
@Composable
private fun StatePicker(states: List<StateInfo>, onDismiss: () -> Unit, onPick: (String) -> Unit) {
    AlertDialog(onDismissRequest = onDismiss, confirmButton = {},
        title = { Text("Which state are you in?") },
        text = {
            Column(verticalArrangement = Arrangement.spacedBy(8.dp)) {
                Text("Your Field Guide and parks follow your state. You can change it any time with 📍 at the top.")
                states.forEach { s ->
                    OutlinedButton(onClick = { onPick(s.code) }, modifier = Modifier.fillMaxWidth()) { Text(s.name) }
                }
            }
        })
}

// Icons are the website's 16x16 pixel-art tab icons (species/sprites/ui_tab_*.png).
private class AppTab(val key: String, val title: String, val icon: String)

private val TABS = listOf(
    AppTab("catch", "Capture", "ui_tab_capture"),
    AppTab("collection", "Field Guide", "ui_tab_guide"),
    AppTab("gallery", "Photos", "ui_tab_photos"),
    AppTab("social", "Friends", "ui_tab_friends"),
    AppTab("hotspots", "Parks", "ui_tab_parks"),
)

@Composable
fun CatchScreen(state: UiState, onCapture: (Uri, Pair<Double, Double>?) -> Unit, onDismiss: () -> Unit,
                onPick: (String?) -> Unit, onOpenDex: (String) -> Unit) {
    val context = LocalContext.current
    var saveLocation by rememberSaveable { mutableStateOf(true) }
    val askLocation = rememberLauncherForActivityResult(ActivityResultContracts.RequestMultiplePermissions()) { granted ->
        if (granted.values.none { it }) saveLocation = false
    }
    val onPhoto: (Uri) -> Unit = { uri ->
        onCapture(uri, if (state.account != null && saveLocation) lastLocation(context) else null)
    }
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
        Text("Photograph a wild animal. If it's one of the ${state.info?.species?.size ?: 100} " +
            "${state.fieldGuide?.region ?: ""} species, you earn its badge.",
            style = MaterialTheme.typography.bodyLarge, textAlign = TextAlign.Center)
        Row(horizontalArrangement = Arrangement.spacedBy(12.dp)) {
            Button(onClick = ::launchCamera, enabled = !state.busy) { Text("Take photo") }
            OutlinedButton(
                onClick = { pickPhoto.launch(PickVisualMediaRequest(ActivityResultContracts.PickVisualMedia.ImageOnly)) },
                enabled = !state.busy,
            ) { Text("Choose photo") }
        }
        if (state.account != null) {
            Row(verticalAlignment = Alignment.CenterVertically) {
                androidx.compose.material3.Checkbox(saveLocation, onCheckedChange = { on ->
                    saveLocation = on
                    if (on && !hasLocationPermission(context)) askLocation.launch(LOCATION_PERMISSIONS)
                })
                Text("Save where I captured it")
            }
            androidx.compose.runtime.LaunchedEffect(Unit) {
                if (saveLocation && !hasLocationPermission(context)) askLocation.launch(LOCATION_PERMISSIONS)
            }
        }
        if (state.busy) {
            CircularProgressIndicator()
            Text("Identifying…", style = MaterialTheme.typography.bodyMedium)
        }
        state.error?.let { Text(it, color = MaterialTheme.colorScheme.error) }
        state.result?.let { ResultCard(it, onDismiss, onPick, onOpenDex) }
    }
}

@Composable
fun ResultCard(r: CaptureResult, onDismiss: () -> Unit, onPick: (String?) -> Unit, onOpenDex: (String) -> Unit) {
    Card(Modifier.fillMaxWidth()) {
        Column(Modifier.padding(16.dp), verticalArrangement = Arrangement.spacedBy(8.dp)) {
            Image(r.photo.asImageBitmap(), contentDescription = "Your photo",
                modifier = Modifier.fillMaxWidth().heightIn(max = 280.dp)
                    .aspectRatio(r.photo.width / r.photo.height.toFloat(), matchHeightConstraintsFirst = true)
                    .clip(RoundedCornerShape(12.dp)),
                contentScale = ContentScale.Crop)
            if (r.matched && r.species != null) {
                Text(if (r.newBadge) "New badge!" else "Captured again",
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
            if (!r.picked && r.choices.isNotEmpty()) PickPanel(r, onPick)
            Row(Modifier.align(Alignment.End)) {
                if (r.matched && r.species != null) {
                    TextButton(onClick = { onOpenDex(r.species.slug) }) { Text("Field Guide entry") }
                }
                TextButton(onClick = onDismiss) { Text("Done") }
            }
        }
    }
}

/** "Not this animal?": the player picks from the model's top guesses. We trust them. */
@OptIn(androidx.compose.foundation.layout.ExperimentalLayoutApi::class)
@Composable
fun PickPanel(r: CaptureResult, onPick: (String?) -> Unit) {
    var open by remember(r) { mutableStateOf(false) }
    Column(verticalArrangement = Arrangement.spacedBy(6.dp)) {
        OutlinedButton(onClick = { open = !open }) {
            Text(if (r.matched) "Not this animal? Pick the right one" else "Know what it is? Pick it")
        }
        if (open) {
            androidx.compose.foundation.layout.FlowRow(horizontalArrangement = Arrangement.spacedBy(6.dp)) {
                r.choices.filter { !(r.matched && it.label == r.species?.slug) }.forEach { c ->
                    OutlinedButton(onClick = { onPick(c.label) }) {
                        Text("${c.name} · ${(c.probability * 100).toInt()}%")
                    }
                }
                TextButton(onClick = { onPick(null) }) { Text("None of these") }
            }
        }
    }
}

@Composable
fun RarityTag(rarity: String) {
    Text(rarity.replaceFirstChar { it.uppercase() }, color = Color.White, fontSize = 12.sp,
        modifier = Modifier.clip(RoundedCornerShape(50)).background(rarityColor(rarity))
            .padding(horizontal = 10.dp, vertical = 2.dp))
}

/** Field Guide sections, like the website: captured, maybe out this month, not this time of year. */
private val SECTIONS = listOf("Captured", "Maybe out now", "Not out this time of year")

@Composable
fun CollectionScreen(info: ModelInfo, dex: FieldGuide?, collection: Map<String, Badge>, onOpen: (String) -> Unit) {
    val categories = remember(info) { listOf("all") + info.species.map { it.category }.distinct() }
    var category by rememberSaveable { mutableStateOf("all") }
    val month = remember { java.util.Calendar.getInstance().get(java.util.Calendar.MONTH) + 1 }
    val shown = info.dexOrder.filter { category == "all" || it.category == category }
    // dexOrder is already common to legendary, so each section keeps that order.
    val sections = shown.groupBy { s ->
        when {
            s.slug in collection -> 0
            dex?.inSeason(s.slug, month) != false -> 1
            else -> 2
        }
    }

    LazyVerticalGrid(columns = GridCells.Adaptive(72.dp), modifier = Modifier.fillMaxSize(),
        contentPadding = androidx.compose.foundation.layout.PaddingValues(8.dp),
        horizontalArrangement = Arrangement.spacedBy(6.dp), verticalArrangement = Arrangement.spacedBy(6.dp)) {
        item(span = { GridItemSpan(maxLineSpan) }) {
            Row(Modifier.horizontalScrollCompat(), horizontalArrangement = Arrangement.spacedBy(6.dp)) {
                categories.forEach { c ->
                    FilterChip(selected = category == c, onClick = { category = c },
                        label = { Text(c.replaceFirstChar { it.uppercase() }) })
                }
            }
        }
        SECTIONS.forEachIndexed { i, title ->
            val list = sections[i] ?: return@forEachIndexed
            item(span = { GridItemSpan(maxLineSpan) }, key = "section-$i") {
                Column(Modifier.padding(top = 12.dp)) {
                    Text("$title · ${list.size}", style = MaterialTheme.typography.titleMedium)
                    HorizontalDivider()
                }
            }
            list.groupBy { it.rarity }.forEach { (rarity, tier) ->
                item(span = { GridItemSpan(maxLineSpan) }, key = "tier-$i-$rarity") {
                    Text(rarity.replaceFirstChar { it.uppercase() }, style = MaterialTheme.typography.labelMedium,
                        color = rarityColor(rarity), modifier = Modifier.padding(top = 4.dp))
                }
                items(tier, key = { it.slug }) { s ->
                    SpeciesTile(info.dexNumber(s.slug), s, collection[s.slug]) { onOpen(s.slug) }
                }
            }
        }
    }
}

@Composable
private fun Modifier.horizontalScrollCompat(): Modifier =
    this.then(Modifier.fillMaxWidth()).then(Modifier.horizontalScroll(rememberScrollState()))

@Composable
fun SpeciesTile(number: Int, s: Species, badge: Badge?, onClick: () -> Unit) {
    val caught = badge != null
    Card(
        modifier = Modifier.clickable(onClick = onClick)
            .border(2.dp, if (caught) rarityColor(s.rarity) else Color.Transparent, RoundedCornerShape(12.dp)),
        shape = RoundedCornerShape(12.dp),
        colors = CardDefaults.cardColors(containerColor =
            if (caught) MaterialTheme.colorScheme.primaryContainer else MaterialTheme.colorScheme.surface),
    ) {
        Column(Modifier.padding(4.dp), horizontalAlignment = Alignment.CenterHorizontally) {
            Box(Modifier.fillMaxWidth().aspectRatio(1f).clip(RoundedCornerShape(8.dp))
                .background(MaterialTheme.colorScheme.surfaceVariant), contentAlignment = Alignment.Center) {
                PixelSprite(s.slug, caught, Modifier.fillMaxSize(0.85f))
            }
            Spacer(Modifier.height(4.dp))
            Text("#%03d".format(number), style = MaterialTheme.typography.labelSmall, fontSize = 10.sp,
                color = MaterialTheme.colorScheme.outline)
            Text(s.commonName, style = MaterialTheme.typography.labelSmall, maxLines = 1,
                overflow = TextOverflow.Ellipsis, textAlign = TextAlign.Center,
                color = if (caught) MaterialTheme.colorScheme.onSurface else MaterialTheme.colorScheme.outline)
            // Small tiles, so many fit on a phone; the border and fill mark a captured one.
            if (!caught) {
                Box(Modifier.padding(top = 2.dp).size(8.dp).clip(RoundedCornerShape(50)).background(rarityColor(s.rarity)))
            }
        }
    }
}

private val LOCATION_PERMISSIONS = arrayOf(
    android.Manifest.permission.ACCESS_FINE_LOCATION, android.Manifest.permission.ACCESS_COARSE_LOCATION)

private fun hasLocationPermission(context: android.content.Context) = LOCATION_PERMISSIONS.any {
    androidx.core.content.ContextCompat.checkSelfPermission(context, it) == android.content.pm.PackageManager.PERMISSION_GRANTED
}

/** The phone's last known position; the server blurs it before anyone else sees it. */
@android.annotation.SuppressLint("MissingPermission")
private fun lastLocation(context: android.content.Context): Pair<Double, Double>? {
    if (!hasLocationPermission(context)) return null
    val lm = context.getSystemService(android.content.Context.LOCATION_SERVICE) as android.location.LocationManager
    return lm.getProviders(true).mapNotNull { runCatching { lm.getLastKnownLocation(it) }.getOrNull() }
        .maxByOrNull { it.time }?.let { it.latitude to it.longitude }
}
