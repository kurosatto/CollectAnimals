package com.captureanimals.app

import android.app.Application
import android.graphics.Bitmap
import androidx.compose.foundation.Image
import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.PaddingValues
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.aspectRatio
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.grid.GridCells
import androidx.compose.foundation.lazy.grid.GridItemSpan
import androidx.compose.foundation.lazy.grid.LazyVerticalGrid
import androidx.compose.foundation.lazy.grid.items
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.text.KeyboardOptions
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.AlertDialog
import androidx.compose.material3.Button
import androidx.compose.material3.Card
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.FilterChip
import androidx.compose.material3.HorizontalDivider
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Switch
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.produceState
import androidx.compose.runtime.remember
import androidx.compose.runtime.saveable.rememberSaveable
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.asImageBitmap
import androidx.compose.ui.layout.ContentScale
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.input.KeyboardType
import androidx.compose.ui.text.input.PasswordVisualTransformation
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.dp
import androidx.lifecycle.AndroidViewModel
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import androidx.lifecycle.viewModelScope
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.update
import kotlinx.coroutines.launch
import java.text.DateFormat
import java.util.Date

data class SocialState(
    val feedScope: String = "state",
    val feedState: String = "",
    val feed: List<OnlinePhoto> = emptyList(),
    val feedNext: Int? = null,
    val friends: Friends? = null,
    val suggestions: List<FriendEntry> = emptyList(),
    val album: List<OnlinePhoto>? = null,
    val loading: Boolean = false,
    val message: String? = null,
)

/** The website's feed, friends and album, for signed-in players. */
class SocialViewModel(app: Application) : AndroidViewModel(app) {
    private val _state = MutableStateFlow(SocialState())
    val state: StateFlow<SocialState> = _state

    private fun run(block: suspend () -> Unit) {
        _state.update { it.copy(loading = true, message = null) }
        viewModelScope.launch {
            try { block() } catch (e: Exception) { _state.update { it.copy(message = e.message) } }
            _state.update { it.copy(loading = false) }
        }
    }

    fun loadFeed(scope: String = _state.value.feedScope, stateCode: String = _state.value.feedState) = run {
        _state.update { it.copy(feedScope = scope, feedState = stateCode) }
        val (photos, next) = Online.feed(scope, stateCode, null)
        _state.update { it.copy(feed = photos, feedNext = next) }
    }

    fun moreFeed() {
        val before = _state.value.feedNext ?: return
        run {
            val (photos, next) = Online.feed(_state.value.feedScope, _state.value.feedState, before)
            _state.update { it.copy(feed = it.feed + photos, feedNext = next) }
        }
    }

    fun toggleLike(p: OnlinePhoto) {
        val on = !p.likedByMe
        fun swap(list: List<OnlinePhoto>) = list.map {
            if (it.id == p.id) it.copy(likedByMe = on, likeCount = it.likeCount + if (on) 1 else -1) else it
        }
        _state.update { it.copy(feed = swap(it.feed), album = it.album?.let(::swap)) }
        viewModelScope.launch {
            runCatching { Online.like(p.id, on) }.onFailure { e -> _state.update { it.copy(message = e.message) } }
        }
    }

    fun loadFriends() = run {
        val f = Online.friends()
        val s = runCatching { Online.suggestions() }.getOrDefault(emptyList())
        _state.update { it.copy(friends = f, suggestions = s) }
    }

    fun addFriend(username: String) = run {
        val status = Online.addFriend(username.trim())
        _state.update {
            it.copy(message = if (status == "friends") "You and $username are friends now." else "Request sent to $username.")
        }
        reloadFriends()
    }

    fun accept(username: String) = run { Online.acceptFriend(username); reloadFriends() }
    fun remove(username: String) = run { Online.removeFriend(username); reloadFriends() }

    private suspend fun reloadFriends() {
        val f = Online.friends()
        val s = runCatching { Online.suggestions() }.getOrDefault(emptyList())
        _state.update { it.copy(friends = f, suggestions = s) }
    }

    fun loadAlbum() = run {
        val a = Online.album()
        _state.update { it.copy(album = a) }
    }

    fun deletePhoto(p: OnlinePhoto, then: () -> Unit) = run {
        Online.deletePhoto(p.id)
        _state.update { it.copy(album = it.album?.filter { x -> x.id != p.id }) }
        then()
    }

    fun clear() = _state.update { SocialState() }
}

/** A photo from the server, loaded once and cached. */
@Composable
fun RemoteImage(path: String?, description: String?, modifier: Modifier, maxSide: Int = 800) {
    val bmp by produceState<Bitmap?>(null, path) { value = path?.let { Online.image(it, maxSide) } }
    Box(modifier.background(MaterialTheme.colorScheme.surfaceVariant), contentAlignment = Alignment.Center) {
        bmp?.let {
            Image(it.asImageBitmap(), contentDescription = description, modifier = Modifier.fillMaxSize(),
                contentScale = ContentScale.Crop)
        }
    }
}

private fun dateOf(ms: Long) = DateFormat.getDateInstance(DateFormat.MEDIUM).format(Date(ms))

// --- Account ------------------------------------------------------------------------------

/** Sign in, sign up, or (signed in) feed sharing and sign out. Also where the server lives. */
@Composable
fun AccountDialog(state: UiState, vm: GameViewModel, onDismiss: () -> Unit) {
    val acct = state.account
    var signUp by rememberSaveable { mutableStateOf(false) }
    var email by rememberSaveable { mutableStateOf("") }
    var ident by rememberSaveable { mutableStateOf("") }
    var password by rememberSaveable { mutableStateOf("") }
    var editServer by rememberSaveable { mutableStateOf(false) }
    var serverText by rememberSaveable { mutableStateOf(Online.manualUrl ?: "") }
    // Close once signed in.
    LaunchedEffect(acct?.username) { if (acct != null && password.isNotEmpty()) onDismiss() }

    AlertDialog(onDismissRequest = onDismiss, confirmButton = {
        if (acct == null) {
            Button(enabled = !state.accountBusy && ident.isNotBlank() && password.length >= 8 &&
                    (!signUp || email.isNotBlank()),
                onClick = { if (signUp) vm.signUp(email, ident, password) else vm.signIn(ident, password) }) {
                Text(if (signUp) "Sign up" else "Log in")
            }
        } else {
            TextButton(onClick = onDismiss) { Text("Done") }
        }
    }, dismissButton = {
        if (acct == null) TextButton(onClick = onDismiss) { Text("Cancel") }
        else TextButton(onClick = { vm.signOut(); onDismiss() }) { Text("Log out") }
    }, title = { Text(acct?.let { "Signed in as ${it.username}" } ?: if (signUp) "Create an account" else "Log in") },
    text = {
        Column(Modifier.verticalScroll(rememberScrollState()), verticalArrangement = Arrangement.spacedBy(8.dp)) {
            if (acct == null) {
                Text("An account adds friends, the news feed and likes, and keeps your badges on the game " +
                    "server, the same as the website. Without one you play offline on this phone.",
                    style = MaterialTheme.typography.bodySmall)
                if (signUp) OutlinedTextField(email, { email = it }, label = { Text("Email") }, singleLine = true,
                    keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Email), modifier = Modifier.fillMaxWidth())
                OutlinedTextField(ident, { ident = it }, singleLine = true, modifier = Modifier.fillMaxWidth(),
                    label = { Text(if (signUp) "Username" else "Email or username") })
                OutlinedTextField(password, { password = it }, label = { Text("Password (8+ characters)") },
                    singleLine = true, visualTransformation = PasswordVisualTransformation(),
                    keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Password), modifier = Modifier.fillMaxWidth())
                if (state.accountBusy) CircularProgressIndicator(Modifier.size(24.dp))
                state.accountError?.let { Text(it, color = MaterialTheme.colorScheme.error) }
                TextButton(onClick = { signUp = !signUp }, contentPadding = PaddingValues(0.dp)) {
                    Text(if (signUp) "Have an account? Log in" else "Need an account? Sign up")
                }
            } else {
                Row(verticalAlignment = Alignment.CenterVertically) {
                    Text("Show my captures in the news feed", Modifier.weight(1f))
                    Switch(acct.showInFeed, onCheckedChange = vm::setShowInFeed)
                }
            }
            HorizontalDivider()
            Text(if (state.server != null) "Game server: online" else "Game server: can't be found right now",
                style = MaterialTheme.typography.labelMedium, color = MaterialTheme.colorScheme.outline)
            if (editServer) {
                OutlinedTextField(serverText, { serverText = it }, singleLine = true, modifier = Modifier.fillMaxWidth(),
                    label = { Text("Server address (blank = automatic)") })
                TextButton(onClick = { vm.setServer(serverText); editServer = false }) { Text("Save address") }
            } else {
                TextButton(onClick = { editServer = true }, contentPadding = PaddingValues(0.dp)) {
                    Text("Change server address")
                }
            }
        }
    })
}

// --- Friends tab: news feed + friends -------------------------------------------------------

@Composable
fun SocialScreen(state: UiState, social: SocialViewModel, onSignIn: () -> Unit, onOpenDex: (String) -> Unit) {
    if (state.account == null) {
        Column(Modifier.fillMaxSize().padding(24.dp), horizontalAlignment = Alignment.CenterHorizontally,
            verticalArrangement = Arrangement.spacedBy(12.dp, Alignment.CenterVertically)) {
            Text("Log in to see what other players are catching, add friends and like photos.",
                textAlign = TextAlign.Center, style = MaterialTheme.typography.bodyLarge)
            Button(onClick = onSignIn) { Text("Log in or sign up") }
        }
        return
    }
    var section by rememberSaveable { mutableStateOf("feed") }
    val s by social.state.collectAsStateWithLifecycle()
    Column(Modifier.fillMaxSize()) {
        Row(Modifier.padding(horizontal = 12.dp, vertical = 4.dp), horizontalArrangement = Arrangement.spacedBy(6.dp)) {
            FilterChip(section == "feed", { section = "feed" }, label = { Text("News feed") })
            FilterChip(section == "friends", { section = "friends" }, label = { Text("Friends") })
        }
        s.message?.let { Text(it, Modifier.padding(horizontal = 16.dp), color = MaterialTheme.colorScheme.outline,
            style = MaterialTheme.typography.bodySmall) }
        if (section == "feed") FeedSection(s, social, state, onOpenDex) else FriendsSection(s, social)
    }
}

@Composable
private fun FeedSection(s: SocialState, social: SocialViewModel, game: UiState, onOpenDex: (String) -> Unit) {
    val stateName = game.states.firstOrNull { it.code == game.stateCode }?.name ?: game.stateCode
    LaunchedEffect(game.stateCode) { social.loadFeed(stateCode = game.stateCode) }
    LazyColumn(Modifier.fillMaxSize(), contentPadding = PaddingValues(12.dp),
        verticalArrangement = Arrangement.spacedBy(10.dp)) {
        item {
            // Your state, or Global: everyone in every state, for when you travel.
            Row(horizontalArrangement = Arrangement.spacedBy(6.dp)) {
                FilterChip(s.feedScope == "state", { social.loadFeed("state") }, label = { Text("📍 $stateName") })
                FilterChip(s.feedScope == "all", { social.loadFeed("all") }, label = { Text("🌎 Global") })
                FilterChip(s.feedScope == "friends", { social.loadFeed("friends") }, label = { Text("Friends") })
            }
        }
        if (s.feed.isEmpty() && !s.loading) item {
            Text("No catches here yet.", color = MaterialTheme.colorScheme.outline)
        }
        items(s.feed, key = { it.id }) { p -> FeedCard(p, social, onOpenDex) }
        if (s.loading) item { Box(Modifier.fillMaxWidth(), Alignment.Center) { CircularProgressIndicator() } }
        else if (s.feedNext != null) item {
            OutlinedButton(onClick = social::moreFeed, modifier = Modifier.fillMaxWidth()) { Text("Show more") }
        }
    }
}

@Composable
private fun FeedCard(p: OnlinePhoto, social: SocialViewModel, onOpenDex: (String) -> Unit) {
    Card(shape = RoundedCornerShape(12.dp)) {
        Column {
            if (p.url != null) {
                RemoteImage(p.url, p.commonName, Modifier.fillMaxWidth().aspectRatio(4f / 3f)
                    .clip(RoundedCornerShape(topStart = 12.dp, topEnd = 12.dp))
                    .clickable(enabled = p.slug != null) { p.slug?.let(onOpenDex) })
            } else {
                // Animals you haven't unlocked stay hidden, as on the website.
                Box(Modifier.fillMaxWidth().height(120.dp).background(MaterialTheme.colorScheme.surfaceVariant),
                    contentAlignment = Alignment.Center) {
                    Text("❓ Catch or befriend someone who has caught it to see this one",
                        Modifier.padding(16.dp), textAlign = TextAlign.Center, color = MaterialTheme.colorScheme.outline)
                }
            }
            Row(Modifier.padding(horizontal = 12.dp, vertical = 8.dp), verticalAlignment = Alignment.CenterVertically) {
                Column(Modifier.weight(1f)) {
                    Text(p.commonName ?: "A ${p.rarity} ${p.category}", fontWeight = FontWeight.Bold,
                        color = rarityColor(p.rarity), maxLines = 1, overflow = TextOverflow.Ellipsis)
                    Text(listOfNotNull(if (p.isMine) "You" else p.username, p.place, dateOf(p.caughtAt)).joinToString(" · "),
                        style = MaterialTheme.typography.bodySmall, color = MaterialTheme.colorScheme.outline,
                        maxLines = 1, overflow = TextOverflow.Ellipsis)
                }
                TextButton(onClick = { social.toggleLike(p) }, enabled = !p.isMine) {
                    Text((if (p.likedByMe) "♥ " else "♡ ") + p.likeCount)
                }
            }
        }
    }
}

@Composable
private fun FriendsSection(s: SocialState, social: SocialViewModel) {
    LaunchedEffect(Unit) { social.loadFriends() }
    var name by rememberSaveable { mutableStateOf("") }
    val f = s.friends
    LazyColumn(Modifier.fillMaxSize(), contentPadding = PaddingValues(12.dp)) {
        item {
            Row(verticalAlignment = Alignment.CenterVertically, horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                OutlinedTextField(name, { name = it }, label = { Text("Friend's username") }, singleLine = true,
                    modifier = Modifier.weight(1f))
                Button(enabled = name.isNotBlank(), onClick = { social.addFriend(name); name = "" }) { Text("Add") }
            }
            Spacer(Modifier.height(8.dp))
        }
        if (f == null) {
            if (s.loading) item { CircularProgressIndicator() }
            return@LazyColumn
        }
        section("Friend requests", f.incoming) { u ->
            TextButton(onClick = { social.accept(u.username) }) { Text("Accept") }
            TextButton(onClick = { social.remove(u.username) }) { Text("Decline") }
        }
        section("Friends (${f.friends.size})", f.friends, empty = "No friends yet. Add one above, or a bot below.") { u ->
            TextButton(onClick = { social.remove(u.username) }) { Text("Remove") }
        }
        section("Waiting for them to accept", f.outgoing) { u ->
            TextButton(onClick = { social.remove(u.username) }) { Text("Cancel") }
        }
        section("Bot friends to add 🤖", s.suggestions) { u ->
            TextButton(onClick = { social.addFriend(u.username) }) { Text("Add") }
        }
    }
}

private fun androidx.compose.foundation.lazy.LazyListScope.section(
    title: String, people: List<FriendEntry>, empty: String? = null,
    actions: @Composable (FriendEntry) -> Unit,
) {
    if (people.isEmpty() && empty == null) return
    item(key = "h-$title") {
        Text(title, style = MaterialTheme.typography.titleSmall, modifier = Modifier.padding(top = 12.dp, bottom = 4.dp))
    }
    if (people.isEmpty()) item(key = "e-$title") { Text(empty!!, color = MaterialTheme.colorScheme.outline) }
    items(people, key = { "$title-${it.username}" }) { u -> FriendRow(u) { actions(u) } }
}

/** One line per person, bots included, so every row is the same height. */
@Composable
private fun FriendRow(u: FriendEntry, actions: @Composable () -> Unit) {
    Row(Modifier.fillMaxWidth().height(48.dp), verticalAlignment = Alignment.CenterVertically) {
        Text((if (u.isBot) "🤖 " else "") + u.username, Modifier.weight(1f), maxLines = 1,
            overflow = TextOverflow.Ellipsis, style = MaterialTheme.typography.bodyLarge)
        if (u.caught > 0) Text("${u.caught} caught", style = MaterialTheme.typography.bodySmall,
            color = MaterialTheme.colorScheme.outline, maxLines = 1, modifier = Modifier.padding(end = 4.dp))
        actions()
    }
    HorizontalDivider()
}

// --- Photos tab when signed in: your album on the server -------------------------------------

@Composable
fun OnlinePhotosScreen(social: SocialViewModel, onOpenDex: (String) -> Unit, onDeleted: () -> Unit) {
    val s by social.state.collectAsStateWithLifecycle()
    LaunchedEffect(Unit) { social.loadAlbum() }
    var confirm by remember { mutableStateOf<OnlinePhoto?>(null) }
    val album = s.album
    if (album == null) {
        Box(Modifier.fillMaxSize(), Alignment.Center) { if (s.loading) CircularProgressIndicator() else s.message?.let { Text(it) } }
        return
    }
    if (album.isEmpty()) {
        Box(Modifier.fillMaxSize().padding(24.dp), Alignment.Center) {
            Text("Your photos show up here once you capture your first animal.",
                style = MaterialTheme.typography.bodyLarge, color = MaterialTheme.colorScheme.outline)
        }
        return
    }
    LazyVerticalGrid(columns = GridCells.Adaptive(150.dp), modifier = Modifier.fillMaxSize(),
        contentPadding = PaddingValues(12.dp),
        horizontalArrangement = Arrangement.spacedBy(10.dp), verticalArrangement = Arrangement.spacedBy(10.dp)) {
        item(span = { GridItemSpan(maxLineSpan) }) {
            Text("${album.size} photo${if (album.size == 1) "" else "s"}",
                style = MaterialTheme.typography.labelLarge, color = MaterialTheme.colorScheme.outline)
        }
        items(album, key = { it.id }) { p ->
            Card(shape = RoundedCornerShape(12.dp)) {
                Column {
                    RemoteImage(p.url, p.commonName, Modifier.fillMaxWidth().aspectRatio(1f)
                        .clip(RoundedCornerShape(topStart = 12.dp, topEnd = 12.dp))
                        .clickable { p.slug?.let(onOpenDex) }, maxSide = 512)
                    Column(Modifier.padding(horizontal = 10.dp, vertical = 8.dp)) {
                        Text(p.commonName ?: "", style = MaterialTheme.typography.titleSmall, maxLines = 1,
                            overflow = TextOverflow.Ellipsis, color = rarityColor(p.rarity))
                        Text(dateOf(p.caughtAt) + if (p.likeCount > 0) " · ♥ ${p.likeCount}" else "",
                            style = MaterialTheme.typography.bodySmall, color = MaterialTheme.colorScheme.outline)
                        TextButton(onClick = { confirm = p }, contentPadding = PaddingValues(0.dp)) { Text("Delete photo") }
                    }
                }
            }
        }
    }
    confirm?.let { p ->
        AlertDialog(
            onDismissRequest = { confirm = null },
            title = { Text("Delete this photo?") },
            text = { Text("The ${p.commonName ?: "animal"} also leaves your collection. Capture it again to get it back.") },
            confirmButton = { TextButton(onClick = { social.deletePhoto(p, onDeleted); confirm = null }) { Text("Delete") } },
            dismissButton = { TextButton(onClick = { confirm = null }) { Text("Cancel") } },
        )
    }
}
