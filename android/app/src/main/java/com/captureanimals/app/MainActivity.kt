package com.captureanimals.app

import androidx.activity.compose.BackHandler
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
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.WindowInsets
import androidx.compose.foundation.layout.statusBars
import androidx.compose.foundation.layout.windowInsetsPadding
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
import androidx.compose.foundation.layout.width
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
import androidx.compose.ui.draw.drawBehind
import androidx.compose.ui.draw.rotate
import androidx.compose.ui.draw.shadow
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.asImageBitmap
import androidx.compose.ui.layout.ContentScale
import androidx.compose.ui.platform.LocalContext
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
            JournalTheme {
                App(openTab = openTab)
            }
        }
    }
}


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
    // A minigame being played takes the whole screen, so the bars go away.
    var gameOn by remember { mutableStateOf(false) }
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
    val tab = tabChoice
    // Parks lives inside the Field Guide, behind a button (only for states with park data).
    var parksOpen by rememberSaveable { mutableStateOf(false) }
    val showParks = parksOpen && TABS[tab].key == "collection" && !dex?.parks.isNullOrEmpty()
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
                DexEntryScreen(info.dexNumber(entry.slug), entry, badge, entryDex) { dexSlug = null }
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
        if (!gameOn) Column {
            // One slim leather line (kuro, 2026-11-04): title, state, and your picture and name
            // (log out is in the account dialog it opens).
            Row(Modifier.fillMaxWidth().leather(top = false).windowInsetsPadding(WindowInsets.statusBars)
                .height(46.dp).padding(start = 12.dp, end = 4.dp), verticalAlignment = Alignment.CenterVertically) {
                Text(if (tab == 0) "Capture Animals" else if (showParks) "Parks" else TABS[tab].title,
                    style = MaterialTheme.typography.titleMedium, color = Journal.CreamBright, maxLines = 1,
                    overflow = TextOverflow.Ellipsis, modifier = Modifier.weight(1f))
                if (state.states.size > 1) StateMenu(state.states, state.stateCode, state.mainState(), state.stateTiles,
                    onOpen = vm::loadStateTiles, onClose = vm::closeStateTiles, onView = vm::viewState, onMakeMain = vm::chooseState)
                TextButton(onClick = { showAccount = true }, contentPadding = androidx.compose.foundation.layout.PaddingValues(horizontal = 8.dp),
                    colors = androidx.compose.material3.ButtonDefaults.textButtonColors(contentColor = Journal.Cream)) {
                    state.account?.let { Avatar(it.avatar, Modifier.size(22.dp)); Spacer(Modifier.width(5.dp)) }
                    Text(state.account?.username ?: "Log in", maxLines = 1, style = MaterialTheme.typography.labelLarge,
                        overflow = TextOverflow.Ellipsis, modifier = Modifier.widthIn(max = 110.dp))
                }
            }
            if (info != null) {
                // Progress on one short line instead of a sentence over a thick bar.
                Row(Modifier.padding(horizontal = 12.dp, vertical = 6.dp), verticalAlignment = Alignment.CenterVertically) {
                    Text("$captured/$total captured", style = handStyle(13))
                    Spacer(Modifier.width(8.dp))
                    LinearProgressIndicator(
                        progress = { if (total == 0) 0f else captured / total.toFloat() },
                        modifier = Modifier.weight(1f).height(6.dp), trackColor = MaterialTheme.colorScheme.outlineVariant,
                        drawStopIndicator = {})
                }
            }
        }
    }, bottomBar = {
        // One screen per job instead of one long page.
        if (!gameOn) NavigationBar(Modifier.leather(bottom = false), containerColor = Color.Transparent, tonalElevation = 0.dp) {
            TABS.forEachIndexed { i, t ->
                // Six tabs: one line of small text each, so "Field Guide" doesn't wrap.
                NavigationBarItem(selected = tab == i, onClick = { tabChoice = i; parksOpen = false },
                    colors = androidx.compose.material3.NavigationBarItemDefaults.colors(
                        indicatorColor = Journal.Cream, selectedTextColor = Journal.CreamBright,
                        unselectedTextColor = Journal.Cream.copy(alpha = .75f)),
                    icon = {
                        BadgedBox(badge = { if (t.key == "social" && requests > 0) Badge { Text("$requests") } }) {
                            TabIcon(t.icon, Modifier.size(28.dp).then(
                                if (tab == i) Modifier.border(2.dp, Journal.Brass, RoundedCornerShape(50)).padding(2.dp) else Modifier))
                        }
                    },
                    label = { Text(t.title, maxLines = 1, softWrap = false, fontSize = 11.sp) })
            }
        }
    }, containerColor = MaterialTheme.colorScheme.background) { padding ->
        val lines = MaterialTheme.colorScheme.outlineVariant.copy(alpha = .45f)
        Box(Modifier.padding(padding).fillMaxSize().paperLines(lines)) {
            when {
                info == null -> CircularProgressIndicator(Modifier.align(Alignment.Center))
                TABS[tab].key == "catch" -> {
                    val animals = remember(info, dex, state.collection) { habitatAnimals(info, dex, state.collection) }
                    CatchScreen(state, animals, vm::capture, vm::dismissResult, vm::pick, vm::saveWhereWhen, vm::chooseState,
                        vm::changeCaptureState, NameActions(vm::animalNames, vm::nameAnimal)) { dexSlug = it }
                }
                TABS[tab].key == "feed" ->
                    SocialScreen(state, social, "feed", onSignIn = { showAccount = true }) { dexSlug = it }
                TABS[tab].key == "social" ->
                    SocialScreen(state, social, "friends", onSignIn = { showAccount = true }) { dexSlug = it }
                TABS[tab].key == "gallery" && state.account != null ->
                    OnlinePhotosScreen(social, onOpenDex = { dexSlug = it }, onDeleted = vm::reloadCollection,
                        parks = state.fieldGuide?.parks.orEmpty())
                showParks && dex != null -> {
                    BackHandler { parksOpen = false }
                    Column(Modifier.fillMaxSize()) {
                        TextButton(onClick = { parksOpen = false }, modifier = Modifier.padding(horizontal = 8.dp)) {
                            Text("‹ Back to Field Guide")
                        }
                        Box(Modifier.weight(1f)) {
                            HotspotsScreen(info, dex, state.collection, onOpenDex = { dexSlug = it })
                        }
                    }
                }
                TABS[tab].key == "collection" -> {
                    val sets = remember(state.sets, info, dex, state.stateCode) {
                        state.sets.forState(state.stateCode, info.species.map { it.slug }.toSet()) { dex?.details?.get(it)?.safety }
                    }
                    CollectionScreen(info, dex, state.collection, sets,
                        onOpenParks = if (dex?.parks.isNullOrEmpty()) null else ({ parksOpen = true })) { dexSlug = it }
                }
                TABS[tab].key == "games" -> {
                    val animals = remember(info, dex, state.collection) { habitatAnimals(info, dex, state.collection) }
                    MinigamesScreen(animals) { gameOn = it }
                }
                TABS[tab].key == "gallery" -> GalleryScreen(state.allSpecies, state.collection, onOpenDex = { dexSlug = it },
                    onDelete = vm::deleteCatch)
            }
        }
    }
}

// Icons are the website's 16x16 pixel-art tab icons (species/sprites/ui_tab_*.png).
private class AppTab(val key: String, val title: String, val icon: String)

private val TABS = listOf(
    AppTab("catch", "Habitat", "ui_tab_capture"),
    AppTab("collection", "Field Guide", "ui_tab_guide"),
    AppTab("games", "Games", "ui_tab_games"),
    AppTab("gallery", "Photos", "ui_tab_photos"),
    AppTab("feed", "Feed", "ui_tab_feed"),
    AppTab("social", "Friends", "ui_tab_friends"),
)

@Composable
fun CatchScreen(state: UiState, animals: List<HabitatAnimal>, onCapture: (Uri, Pair<Double, Double>?, Boolean, CropBox?) -> Unit, onDismiss: () -> Unit,
                onPick: (String?) -> Unit, onSaveWhereWhen: SaveWhereWhen, onMakeMain: (String) -> Unit,
                onChangeState: (String) -> Unit, naming: NameActions? = null, onOpenDex: (String) -> Unit) {
    val context = LocalContext.current
    val habitat = rememberHabitatView()
    var saveLocation by rememberSaveable { mutableStateOf(true) }
    val askLocation = rememberLauncherForActivityResult(ActivityResultContracts.RequestMultiplePermissions()) { granted ->
        if (granted.values.none { it }) saveLocation = false
    }
    // A new photo goes to the crop step first; Identify sends it with the crop.
    var cropping by rememberSaveable { mutableStateOf<Uri?>(null) }
    val onPhoto: (Uri) -> Unit = { uri -> onDismiss(); cropping = uri }
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
        Modifier.fillMaxSize().verticalScroll(rememberScrollState()).padding(start = 12.dp, end = 12.dp, bottom = 12.dp),
        horizontalAlignment = Alignment.CenterHorizontally,
        verticalArrangement = Arrangement.spacedBy(8.dp),
    ) {
        // The habitat is the home page, edge to edge with no frame (kuro, 2026-11-04); while a
        // photo is being identified it moves below the result so the result shows first.
        val working = cropping != null || state.busy || state.result != null || state.error != null
        if (!working) Habitat(habitat, animals, state.stateCode, Modifier.bleed(12.dp), onOpen = onOpenDex)
        else Spacer(Modifier.height(4.dp))
        Text("Photograph a wild animal. If it's one of the ${state.info?.species?.size ?: 100} " +
            "${state.fieldGuide?.region ?: ""} species, it's captured in your Field Guide.",
            style = MaterialTheme.typography.bodySmall, textAlign = TextAlign.Center,
            color = MaterialTheme.colorScheme.onSurfaceVariant)
        val compact = androidx.compose.foundation.layout.PaddingValues(horizontal = 14.dp, vertical = 6.dp)
        Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
            Button(onClick = ::launchCamera, enabled = !state.busy, contentPadding = compact,
                elevation = androidx.compose.material3.ButtonDefaults.buttonElevation(defaultElevation = 3.dp)) {
                TabIcon("ui_tab_capture", Modifier.size(20.dp)); Spacer(Modifier.width(6.dp)); Text("Take photo")
            }
            OutlinedButton(
                onClick = { pickPhoto.launch(PickVisualMediaRequest(ActivityResultContracts.PickVisualMedia.ImageOnly)) },
                enabled = !state.busy, contentPadding = compact,
                border = androidx.compose.foundation.BorderStroke(1.5.dp, MaterialTheme.colorScheme.outline),
            ) { TabIcon("ui_tab_photos", Modifier.size(20.dp)); Spacer(Modifier.width(6.dp)); Text("Choose photo") }
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
        cropping?.let { uri ->
            CropPanel(uri, onIdentify = { box ->
                cropping = null
                onCapture(uri, if (saveLocation) lastLocation(context) else null, saveLocation, box)
            }, onCancel = { cropping = null })
        }
        if (state.busy) {
            CircularProgressIndicator()
            Text("Identifying…", style = MaterialTheme.typography.bodyMedium)
        }
        state.error?.let { Text(it, color = MaterialTheme.colorScheme.error) }
        state.result?.let { r ->
            ResultCard(r, onDismiss, onPick, onOpenDex, state.fieldGuide?.parks.orEmpty(), onSaveWhereWhen,
                safety = r.species?.let { state.fieldGuide?.details?.get(it.slug) }
                    ?.takeIf { it.safety == "caution" || it.safety == "danger" },
                // A photo that unlocked a state offers to make it the main one.
                makeMain = r.unlockedState?.takeIf { it != state.mainState() }
                    ?.let { code -> state.states.firstOrNull { it.code == code } }
                    ?.let { st -> st.name to { onMakeMain(st.code) } },
                changeState = if (r.canChangeState && state.states.size > 1) state.states to onChangeState else null,
                naming = naming, sharing = state.account?.shareTrainingPhotos == true, signedIn = state.account != null)
        }
        // Your live habitat: the animals you've captured, in your state's scenery.
        if (working) Habitat(habitat, animals, state.stateCode, Modifier.bleed(12.dp), onOpen = onOpenDex)
    }
}

@Composable
fun ResultCard(r: CaptureResult, onDismiss: () -> Unit, onPick: (String?) -> Unit, onOpenDex: (String) -> Unit,
               parks: List<Park> = emptyList(), onSaveWhereWhen: SaveWhereWhen? = null,
               safety: SpeciesDetails? = null, makeMain: Pair<String, () -> Unit>? = null,
               changeState: Pair<List<StateInfo>, (String) -> Unit>? = null,
               naming: NameActions? = null, sharing: Boolean = false, signedIn: Boolean = false) {
    Card(Modifier.fillMaxWidth()) {
        Column(Modifier.padding(16.dp), verticalArrangement = Arrangement.spacedBy(8.dp)) {
            Image(r.photo.asImageBitmap(), contentDescription = "Your photo",
                modifier = Modifier.fillMaxWidth().heightIn(max = 280.dp)
                    .aspectRatio(r.photo.width / r.photo.height.toFloat(), matchHeightConstraintsFirst = true)
                    .clip(RoundedCornerShape(12.dp)),
                contentScale = ContentScale.Crop)
            if (r.matched && r.species != null) {
                if (r.newBadge) CaptureReveal(r.species.slug, Modifier.size(120.dp).align(Alignment.CenterHorizontally))
                if (r.newBadge) InkStamp("Captured!") else Text("Captured again",
                    style = MaterialTheme.typography.labelLarge, color = rarityColor(r.species.rarity))
                Text(r.species.commonName, style = MaterialTheme.typography.headlineSmall, fontWeight = FontWeight.Bold)
                Text(r.species.scientificName, style = MaterialTheme.typography.bodySmall,
                    color = MaterialTheme.colorScheme.onSurfaceVariant)
                RarityTag(r.species.rarity)
            }
            Text(r.message, style = MaterialTheme.typography.bodyLarge)
            makeMain?.let { (name, go) -> OutlinedButton(onClick = go) { Text("★ Make $name my main state") } }
            changeState?.let { (states, go) ->
                // No place in a game state (no GPS in the photo, or taken elsewhere): say where it was taken.
                var picking by remember { mutableStateOf(false) }
                OutlinedButton(onClick = { picking = true }) { IconText("pin", "Taken in another state?") }
                if (picking) StateListDialog(states, "Where was this photo taken?",
                    "The photo has no location we can use, so it was checked against " +
                        "${states.firstOrNull { it.code == r.state }?.name ?: "your state"}'s animals.",
                    onDismiss = { picking = false }) { code -> picking = false; if (code != r.state) go(code) }
            }
            if (r.matched && safety != null) SafetyCard(safety)
            if (r.whereWhen != null && onSaveWhereWhen != null) WhereWhenRow(r.whereWhen, parks, onSaveWhereWhen)
            r.score?.let { ScoreBox(it) }
            Text("Top guesses", style = MaterialTheme.typography.labelLarge)
            r.guesses.forEach { g ->
                Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.SpaceBetween) {
                    Text(g.name)
                    Text("${(g.probability * 100).toInt()}%")
                }
            }
            if (!r.picked) PickPanel(r, onPick)
            // "What was it?" once the photo doesn't count: after "None of these", or nothing to pick from.
            if (naming != null && !r.matched && (r.picked || r.choices.isEmpty())) {
                r.named?.let { Text(it, style = MaterialTheme.typography.bodyMedium) }
                    ?: NamePanel(naming, sharing, signedIn, key = r.photo)
            }
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

/** Loads the bundled name list and sends the player's pick (GameViewModel). */
class NameActions(val load: suspend () -> AnimalNames?, val onName: (AnimalName) -> Unit)

/**
 * "What was it?": type to search the big name list (or tap a broad group) and pick
 * one. It helps train the identifier and never counts for a badge.
 */
@OptIn(androidx.compose.foundation.layout.ExperimentalLayoutApi::class)
@Composable
fun NamePanel(naming: NameActions, sharing: Boolean, signedIn: Boolean, key: Any) {
    var names by remember { mutableStateOf<AnimalNames?>(null) }
    LaunchedEffect(Unit) { names = naming.load() }
    var query by remember(key) { mutableStateOf("") }
    var skipped by remember(key) { mutableStateOf(false) }
    var sent by remember(key) { mutableStateOf(false) }
    if (skipped) return
    val list = names ?: return
    Column(verticalArrangement = Arrangement.spacedBy(6.dp)) {
        Text("What was it? Pick a name to help the game learn animals. It won't count for a badge.",
            style = MaterialTheme.typography.labelLarge)
        androidx.compose.material3.OutlinedTextField(query, { query = it }, singleLine = true,
            modifier = Modifier.fillMaxWidth(), placeholder = { Text("Type an animal, like robin or beetle") })
        val hits = remember(query, list) { if (query.isBlank()) list.groups.take(8) else list.search(query) }
        androidx.compose.foundation.layout.FlowRow(horizontalArrangement = Arrangement.spacedBy(6.dp)) {
            hits.forEach { e ->
                OutlinedButton(enabled = !sent, onClick = { sent = true; naming.onName(e) }) {
                    Text(e.name, fontWeight = if (e.isGroup) FontWeight.Bold else FontWeight.Normal)
                }
            }
        }
        if (query.isNotBlank() && hits.isEmpty()) {
            Text("No match. Try a shorter word, or pick a group like \u201csome kind of bird\u201d.",
                style = MaterialTheme.typography.bodySmall)
        }
        Text(when {
            sharing -> "Your photo is shared to help teach the game (you can turn this off in your account)."
            signedIn -> "Only the name is saved. To share photos too, turn on \u201cShare photos to teach the game\u201d in your account."
            else -> "It's saved on this phone and sent once you sign in. Photos are shared only if you turn that on in your account."
        }, style = MaterialTheme.typography.bodySmall, color = MaterialTheme.colorScheme.outline)
        Text(list.about, style = MaterialTheme.typography.labelSmall, color = MaterialTheme.colorScheme.outline)
        TextButton(onClick = { skipped = true }, contentPadding = androidx.compose.foundation.layout.PaddingValues(0.dp)) { Text("Skip") }
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
fun CollectionScreen(info: ModelInfo, dex: FieldGuide?, collection: Map<String, Badge>, sets: List<SetDef>,
                     onOpenParks: (() -> Unit)? = null, onOpen: (String) -> Unit) {
    val categories = remember(info) { listOf("all") + info.species.map { it.category }.distinct() }
    var category by rememberSaveable { mutableStateOf("all") }
    val month = remember { java.util.Calendar.getInstance().get(java.util.Calendar.MONTH) + 1 }
    val shown = info.dexOrder.filter { category == "all" || it.category == category }
    // dexOrder is already common to legendary, so each section keeps that order
    // and shows each rarity heading once.
    val sections = shown.groupBy { s -> if (s.slug in collection) 0 else 1 }

    LazyVerticalGrid(columns = GridCells.Adaptive(72.dp), modifier = Modifier.fillMaxSize(),
        contentPadding = androidx.compose.foundation.layout.PaddingValues(8.dp),
        horizontalArrangement = Arrangement.spacedBy(8.dp), verticalArrangement = Arrangement.spacedBy(10.dp)) {
        // Parks used to be its own tab; now it opens from here.
        if (onOpenParks != null) item(span = { GridItemSpan(maxLineSpan) }, key = "parks") {
            OutlinedButton(onClick = onOpenParks, modifier = Modifier.fillMaxWidth(), shape = RoundedCornerShape(12.dp),
                border = androidx.compose.foundation.BorderStroke(1.5.dp, MaterialTheme.colorScheme.outline)) {
                TabIcon("ui_tab_parks", Modifier.size(24.dp))
                Spacer(Modifier.width(8.dp))
                Text("Parks to find animals")
            }
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
                    Text(rarity.uppercase(), style = MaterialTheme.typography.labelMedium, letterSpacing = 2.sp,
                        color = rarityColor(rarity), modifier = Modifier.padding(top = 4.dp))
                }
                // Not captured yet: within a rarity, animals around this month come first.
                // Captured ones keep plain Field Guide order.
                items(if (i == 0) tier else tier.sortedBy { dex?.inSeason(it.slug, month) == false },
                      key = { it.slug }) { s ->
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
    // Field Journal: a captured animal is a specimen card pinned in at a slight angle;
    // one not captured yet is an empty dashed slot with its silhouette.
    val tilt = if (caught) listOf(-1.2f, 0.6f, 0f, 1f, -0.5f)[number % 5] else 0f
    val outline = MaterialTheme.colorScheme.outline
    val shape = RoundedCornerShape(3.dp)
    Column(
        Modifier.rotate(tilt).then(
            if (caught) Modifier.shadow(3.dp, shape).background(Journal.Card, shape)
            else Modifier.drawBehind {
                drawRoundRect(outline, cornerRadius = androidx.compose.ui.geometry.CornerRadius(3.dp.toPx()),
                    style = androidx.compose.ui.graphics.drawscope.Stroke(1.5.dp.toPx(),
                        pathEffect = androidx.compose.ui.graphics.PathEffect.dashPathEffect(floatArrayOf(10f, 8f))))
            }).clickable(onClick = onClick).padding(5.dp),
        horizontalAlignment = Alignment.CenterHorizontally,
    ) {
        Text("#%03d".format(number), fontSize = 10.sp, fontFamily = PixelFont, fontWeight = FontWeight.Bold,
            color = if (caught) Journal.CardMuted else outline, modifier = Modifier.fillMaxWidth())
        Box(Modifier.fillMaxWidth().aspectRatio(1f)
            .background(if (caught) Color(0xFFF1E7CF) else Color.Transparent), contentAlignment = Alignment.Center) {
            PixelSprite(s.slug, caught, Modifier.fillMaxSize(0.85f))
        }
        Text(if (caught) s.commonName else "???", fontFamily = PixelFont, fontSize = 11.sp, lineHeight = 13.sp, maxLines = 1,
            overflow = TextOverflow.Ellipsis, textAlign = TextAlign.Center, modifier = Modifier.padding(top = 2.dp),
            color = if (caught) Journal.CardInk else outline)
        // The rarity dot, so a slot still hints how hard it is to find.
        if (!caught) {
            Box(Modifier.padding(top = 2.dp).size(7.dp).clip(RoundedCornerShape(50)).background(rarityColor(s.rarity)))
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
