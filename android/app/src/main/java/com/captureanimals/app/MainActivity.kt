package com.captureanimals.app

import android.Manifest
import android.graphics.BitmapFactory
import android.content.Intent
import android.net.Uri
import android.os.Build
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
import androidx.compose.material3.Badge
import androidx.compose.material3.BadgedBox
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
import androidx.compose.runtime.LaunchedEffect
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
        FriendAlerts.schedule(this)
        // A friend request notification opens the Friends tab.
        val openTab = intent?.getStringExtra(FriendAlerts.EXTRA_TAB)
        setContent {
            MaterialTheme(colorScheme = if (isSystemInDarkTheme()) darkColorScheme(primary = Forest80)
                                        else lightColorScheme(primary = Forest40)) {
                App(openTab = openTab)
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
fun App(vm: GameViewModel = viewModel(), social: SocialViewModel = viewModel(), openTab: String? = null) {
    val state by vm.state.collectAsStateWithLifecycle()
    val socialState by social.state.collectAsStateWithLifecycle()
    var tabChoice by rememberSaveable { mutableIntStateOf(TABS.indexOfFirst { it.key == openTab }.coerceAtLeast(0)) }
    var showAccount by rememberSaveable { mutableStateOf(false) }
    // Android 13+ asks before showing notifications; ask once a player has signed in.
    val askNotify = rememberLauncherForActivityResult(ActivityResultContracts.RequestPermission()) {}
    val context = LocalContext.current
    // A different player (or none) sees nothing of the last one's feed and album. While
    // the app is open, friend requests are checked every minute for the tab's badge.
    LaunchedEffect(state.account?.username) {
        social.clear()
        if (state.account == null) return@LaunchedEffect
        if (Build.VERSION.SDK_INT >= 33 && !FriendAlerts.canNotify(context)) askNotify.launch(Manifest.permission.POST_NOTIFICATIONS)
        while (true) {
            social.checkRequests()
            kotlinx.coroutines.delay(60_000)
        }
    }
    // A newer app version (a major update) on the game server: offer it once per version.
    var update by remember { mutableStateOf<Updates.Available?>(null) }
    LaunchedEffect(state.server) { if (state.server != null) update = Updates.check(context) }
    update?.let { u ->
        AlertDialog(onDismissRequest = { update = null },
            title = { Text("A new version is available") },
            text = { Text("Capture Animals ${u.version} is out (you have ${BuildConfigCompat.version(context)}). " +
                "Download it, then open the file to install it over this one. Your captures stay.") },
            confirmButton = {
                Button(onClick = {
                    update = null
                    runCatching { context.startActivity(Intent(Intent.ACTION_VIEW, Uri.parse(u.url))) }
                }) { Text("Download") }
            },
            dismissButton = { TextButton(onClick = { Updates.skip(context, u.version); update = null }) { Text("Later") } })
    }
    val requests = socialState.friends?.incoming?.size ?: 0
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
                // Another state's animal gets that state's sighting map, tips and parks.
                val entryDex = if (info.species.any { it.slug == entry.slug }) dex
                    else state.states.firstOrNull { st -> st.species.any { it.slug == entry.slug } }?.fieldGuide ?: dex
                val badge = state.collection[entry.slug]
                DexEntryScreen(info.dexNumber(entry.slug), entry, badge, entryDex, bond = {
                    if (state.account != null && badge != null) {
                        BondPanel(entry.slug, state.buddy?.takeIf { it.chosen }?.bond?.slug, vm::setBuddy)
                    }
                }) { dexSlug = null }
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
                if (state.states.size > 1) StateMenu(state.states, state.stateCode, state.unlockedStates(), vm::chooseState)
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
                // Six tabs: one line of small text each, so "Field Guide" doesn't wrap.
                NavigationBarItem(selected = tab == i, onClick = { tabChoice = i },
                    icon = {
                        BadgedBox(badge = { if (t.key == "social" && requests > 0) Badge { Text("$requests") } }) {
                            TabIcon(t.icon, Modifier.size(28.dp))
                        }
                    },
                    label = { Text(t.title, maxLines = 1, softWrap = false, fontSize = 11.sp) })
            }
        }
    }) { padding ->
        Box(Modifier.padding(padding).fillMaxSize()) {
            when {
                info == null -> CircularProgressIndicator(Modifier.align(Alignment.Center))
                TABS[tab].key == "catch" -> CatchScreen(state, vm::capture, vm::dismissResult, vm::pick) { dexSlug = it }
                TABS[tab].key == "feed" ->
                    SocialScreen(state, social, "feed", onSignIn = { showAccount = true }) { dexSlug = it }
                TABS[tab].key == "social" ->
                    SocialScreen(state, social, "friends", onSignIn = { showAccount = true }) { dexSlug = it }
                TABS[tab].key == "gallery" && state.account != null ->
                    OnlinePhotosScreen(social, onOpenDex = { dexSlug = it }, onDeleted = vm::reloadCollection)
                TABS[tab].key == "collection" -> {
                    val sets = remember(state.sets, info, dex, state.stateCode) {
                        state.sets.forState(state.stateCode, info.species.map { it.slug }.toSet()) { dex?.details?.get(it)?.safety }
                    }
                    CollectionScreen(info, dex, state.stateCode, state.collection, state.buddy, sets) { dexSlug = it }
                }
                TABS[tab].key == "gallery" -> GalleryScreen(state.allSpecies, state.collection, onOpenDex = { dexSlug = it },
                    onDelete = vm::deleteCatch)
                dex != null -> HotspotsScreen(info, dex, state.collection, onOpenDex = { dexSlug = it })
            }
        }
    }
}

/** "📍 NC" in the top bar; switching changes the Field Guide, parks and which animals count. */
@Composable
private fun StateMenu(states: List<StateInfo>, current: String, unlocked: Set<String>, onPick: (String) -> Unit) {
    var open by remember { mutableStateOf(false) }
    // A locked state asks first: players unlock new states by choice.
    var unlocking by remember { mutableStateOf<StateInfo?>(null) }
    Box {
        TextButton(onClick = { open = true }) { Text("📍 $current") }
        DropdownMenu(expanded = open, onDismissRequest = { open = false }) {
            states.forEach { s ->
                val locked = s.code !in unlocked
                DropdownMenuItem(text = { Text((if (locked) "🔒 " else "") + s.name) }, onClick = {
                    open = false
                    if (locked) unlocking = s else onPick(s.code)
                })
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
    AppTab("feed", "Feed", "ui_tab_feed"),
    AppTab("hotspots", "Parks", "ui_tab_parks"),
    AppTab("social", "Friends", "ui_tab_friends"),
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
        if (state.account != null) state.week?.let { ChallengesCard(it) }
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
            r.score?.let { ScoreBox(it, r.bondUp) }
            Text("Top guesses", style = MaterialTheme.typography.labelLarge)
            r.guesses.forEach { g ->
                Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.SpaceBetween) {
                    Text(g.name)
                    Text("${(g.probability * 100).toInt()}%")
                }
            }
            if (!r.picked) PickPanel(r, onPick)
            Row(Modifier.align(Alignment.End)) {
                if (r.matched && r.species != null) {
                    TextButton(onClick = { onOpenDex(r.species.slug) }) { Text("Field Guide entry") }
                }
                TextButton(onClick = onDismiss) { Text("Done") }
            }
        }
    }
}

/**
 * "Wrong animal?": the player picks one of the model's other guesses, or says
 * "None of these" and the photo doesn't count for any animal. We trust them.
 */
@OptIn(androidx.compose.foundation.layout.ExperimentalLayoutApi::class)
@Composable
fun PickPanel(r: CaptureResult, onPick: (String?) -> Unit) {
    val guesses = r.choices.filter { !(r.matched && it.label == r.species?.slug) }
    if (!r.matched && guesses.isEmpty()) return
    Column(verticalArrangement = Arrangement.spacedBy(6.dp)) {
        Text(if (r.matched) "Wrong animal?" else "Know what it is?", style = MaterialTheme.typography.labelLarge)
        androidx.compose.foundation.layout.FlowRow(horizontalArrangement = Arrangement.spacedBy(6.dp)) {
            guesses.forEach { c ->
                OutlinedButton(onClick = { onPick(c.label) }) {
                    Text("${c.name} · ${(c.probability * 100).toInt()}%")
                }
            }
            TextButton(onClick = { onPick(null) }) { Text("None of these") }
        }
    }
}

@Composable
fun RarityTag(rarity: String) {
    Text(rarity.replaceFirstChar { it.uppercase() }, color = Color.White, fontSize = 12.sp,
        modifier = Modifier.clip(RoundedCornerShape(50)).background(rarityColor(rarity))
            .padding(horizontal = 10.dp, vertical = 2.dp))
}

/** Field Guide groups, like the website: captured, then the rest with animals seen this
 *  month before ones not around this time of year (split by a plain line, no label). */
private val SECTIONS = listOf("Captured", "Not captured yet")

@Composable
fun CollectionScreen(info: ModelInfo, dex: FieldGuide?, stateCode: String, collection: Map<String, Badge>,
                     buddy: Buddy?, sets: List<SetDef>, onOpen: (String) -> Unit) {
    // The live habitat sits above the list, as on the website; one WebView for the screen.
    val habitat = rememberHabitatView()
    val animals = remember(info, dex, collection) { habitatAnimals(info, dex, collection) }
    val categories = remember(info) { listOf("all") + info.species.map { it.category }.distinct() }
    var category by rememberSaveable { mutableStateOf("all") }
    val month = remember { java.util.Calendar.getInstance().get(java.util.Calendar.MONTH) + 1 }
    val shown = info.dexOrder.filter { category == "all" || it.category == category }
    // dexOrder is already common to legendary, so each section keeps that order
    // and shows each rarity heading once.
    val sections = shown.groupBy { s -> if (s.slug in collection) 0 else 1 }

    LazyVerticalGrid(columns = GridCells.Adaptive(72.dp), modifier = Modifier.fillMaxSize(),
        contentPadding = androidx.compose.foundation.layout.PaddingValues(8.dp),
        horizontalArrangement = Arrangement.spacedBy(6.dp), verticalArrangement = Arrangement.spacedBy(6.dp)) {
        if (buddy != null) item(span = { GridItemSpan(maxLineSpan) }, key = "buddy") { BuddyCard(buddy, onOpen) }
        item(span = { GridItemSpan(maxLineSpan) }, key = "habitat") {
            Habitat(habitat, animals, stateCode, Modifier.padding(bottom = 4.dp), onOpen = onOpen)
        }
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
                    Text(title, style = MaterialTheme.typography.titleMedium)
                    HorizontalDivider()
                }
            }
            list.groupBy { it.rarity }.forEach { (rarity, tier) ->
                item(span = { GridItemSpan(maxLineSpan) }, key = "tier-$i-$rarity") {
                    Text(rarity.replaceFirstChar { it.uppercase() }, style = MaterialTheme.typography.labelMedium,
                        color = rarityColor(rarity), modifier = Modifier.padding(top = 4.dp))
                }
                // Within a rarity, animals around this month come first.
                items(tier.sortedBy { dex?.inSeason(it.slug, month) == false }, key = { it.slug }) { s ->
                    SpeciesTile(info.dexNumber(s.slug), s, collection[s.slug]) { onOpen(s.slug) }
                }
            }
        }
        // Sets, as on the website: themed groups to complete, under the list.
        if (sets.isNotEmpty()) item(span = { GridItemSpan(maxLineSpan) }, key = "sets") {
            Column(Modifier.padding(top = 16.dp), verticalArrangement = Arrangement.spacedBy(8.dp)) {
                Text("Sets", style = MaterialTheme.typography.titleMedium)
                Text("Themed groups to complete. Each finished set is a badge on your profile.",
                    style = MaterialTheme.typography.bodySmall, color = MaterialTheme.colorScheme.outline)
                sets.forEach { SetCard(it, collection, onOpen) }
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

internal val LOCATION_PERMISSIONS = arrayOf(
    android.Manifest.permission.ACCESS_FINE_LOCATION, android.Manifest.permission.ACCESS_COARSE_LOCATION)

internal fun hasLocationPermission(context: android.content.Context) = LOCATION_PERMISSIONS.any {
    androidx.core.content.ContextCompat.checkSelfPermission(context, it) == android.content.pm.PackageManager.PERMISSION_GRANTED
}

/** The phone's last known position; the server blurs it before anyone else sees it. */
@android.annotation.SuppressLint("MissingPermission")
internal fun lastLocation(context: android.content.Context): Pair<Double, Double>? {
    if (!hasLocationPermission(context)) return null
    val lm = context.getSystemService(android.content.Context.LOCATION_SERVICE) as android.location.LocationManager
    return lm.getProviders(true).mapNotNull { runCatching { lm.getLastKnownLocation(it) }.getOrNull() }
        .maxByOrNull { it.time }?.let { it.latitude to it.longitude }
}
