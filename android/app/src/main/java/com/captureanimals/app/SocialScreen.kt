package com.captureanimals.app

import android.app.Application
import android.graphics.Bitmap
import androidx.compose.foundation.Image
import androidx.compose.foundation.background
import androidx.compose.foundation.border
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
import androidx.compose.material3.Surface
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
import androidx.compose.ui.draw.alpha
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.asImageBitmap
import androidx.compose.ui.layout.ContentScale
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.input.KeyboardType
import androidx.compose.ui.text.input.PasswordVisualTransformation
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.dp
import androidx.compose.ui.window.Dialog
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
    // The photo whose comments are open, and its comments once loaded.
    val commentsFor: OnlinePhoto? = null,
    val comments: List<PhotoComment>? = null,
    val commentError: String? = null,
    // The friend whose Field Guide is open, and the guide once loaded.
    val guideFor: String? = null,
    val guide: FriendGuide? = null,
    val guideError: String? = null,
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

    private fun setCommentCount(photoId: Int, n: Int) {
        fun swap(list: List<OnlinePhoto>) = list.map { if (it.id == photoId) it.copy(commentCount = n) else it }
        _state.update { it.copy(feed = swap(it.feed), album = it.album?.let(::swap)) }
    }

    fun openComments(p: OnlinePhoto) {
        _state.update { it.copy(commentsFor = p, comments = null, commentError = null) }
        viewModelScope.launch {
            runCatching { Online.comments(p.id) }
                .onSuccess { cs -> _state.update { it.copy(comments = cs) }; setCommentCount(p.id, cs.size) }
                .onFailure { e -> _state.update { it.copy(comments = emptyList(), commentError = e.message) } }
        }
    }

    fun closeComments() = _state.update { it.copy(commentsFor = null, comments = null, commentError = null) }

    fun postComment(text: String, done: () -> Unit) {
        val p = _state.value.commentsFor ?: return
        viewModelScope.launch {
            runCatching { Online.addComment(p.id, text) }
                .onSuccess { c ->
                    val list = (_state.value.comments ?: emptyList()) + c
                    _state.update { it.copy(comments = list, commentError = null) }
                    setCommentCount(p.id, list.size)
                    done()
                }
                .onFailure { e -> _state.update { it.copy(commentError = e.message) } }
        }
    }

    fun deleteComment(c: PhotoComment) {
        val p = _state.value.commentsFor ?: return
        viewModelScope.launch {
            runCatching { Online.deleteComment(c.id) }
                .onSuccess {
                    val list = _state.value.comments.orEmpty().filter { it.id != c.id }
                    _state.update { it.copy(comments = list) }
                    setCommentCount(p.id, list.size)
                }
                .onFailure { e -> _state.update { it.copy(commentError = e.message) } }
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

    fun openGuide(username: String) {
        _state.update { it.copy(guideFor = username, guide = null, guideError = null) }
        viewModelScope.launch {
            runCatching { Online.friendGuide(username) }
                .onSuccess { g -> _state.update { if (it.guideFor == username) it.copy(guide = g) else it } }
                .onFailure { e -> _state.update { it.copy(guideError = e.message) } }
        }
    }

    fun closeGuide() = _state.update { it.copy(guideFor = null, guide = null, guideError = null) }

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
            Text("Log in to see what other players are capturing, add friends, and like and comment on photos.",
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
    CommentsDialog(s, social)
    FriendGuideDialog(s, social, state)
}

/** Comments on one photo. Anyone who can see the photo can join in, friends or not. */
@Composable
fun CommentsDialog(s: SocialState, social: SocialViewModel) {
    val p = s.commentsFor ?: return
    var text by rememberSaveable(p.id) { mutableStateOf("") }
    AlertDialog(onDismissRequest = social::closeComments,
        confirmButton = { TextButton(onClick = social::closeComments) { Text("Close") } },
        title = { Text("Comments · ${p.commonName ?: "photo"} by ${if (p.isMine) "you" else p.username}",
            maxLines = 2, overflow = TextOverflow.Ellipsis) },
        text = {
            Column(verticalArrangement = Arrangement.spacedBy(8.dp)) {
                val cs = s.comments
                Column(Modifier.weight(1f, fill = false).verticalScroll(rememberScrollState()),
                    verticalArrangement = Arrangement.spacedBy(6.dp)) {
                    when {
                        cs == null -> CircularProgressIndicator(Modifier.size(24.dp))
                        cs.isEmpty() -> Text("No comments yet. Say something nice!", color = MaterialTheme.colorScheme.outline)
                        else -> cs.forEach { c ->
                            Row(verticalAlignment = Alignment.Top) {
                                Column(Modifier.weight(1f)) {
                                    Text(if (c.isMine) "You" else c.username, fontWeight = FontWeight.Bold,
                                        style = MaterialTheme.typography.bodySmall)
                                    Text(c.body, style = MaterialTheme.typography.bodyMedium)
                                }
                                if (c.canDelete) TextButton(onClick = { social.deleteComment(c) },
                                    contentPadding = PaddingValues(0.dp)) { Text("Delete") }
                            }
                        }
                    }
                }
                s.commentError?.let { Text(it, color = MaterialTheme.colorScheme.error, style = MaterialTheme.typography.bodySmall) }
                Row(verticalAlignment = Alignment.CenterVertically, horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                    OutlinedTextField(text, { if (it.length <= 300) text = it }, Modifier.weight(1f),
                        placeholder = { Text("Add a comment") }, maxLines = 3)
                    Button(enabled = text.isNotBlank(), onClick = { social.postComment(text.trim()) { text = "" } }) {
                        Text("Post")
                    }
                }
            }
        })
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
            Text("No captures here yet.", color = MaterialTheme.colorScheme.outline)
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
                    Text("❓ Capture this animal, or befriend someone who has, to see this one",
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
                // Anyone can like or comment, friends or not; animals you haven't unlocked stay hidden.
                if (p.url != null) {
                    TextButton(onClick = { social.toggleLike(p) }, enabled = !p.isMine) {
                        Text((if (p.likedByMe) "♥ " else "♡ ") + p.likeCount)
                    }
                    TextButton(onClick = { social.openComments(p) }) { Text("💬 ${p.commentCount}") }
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
        section("Friends (${f.friends.size})", f.friends, empty = "No friends yet. Add one above, or a bot below.",
            onOpen = social::openGuide) { u ->
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
    onOpen: ((String) -> Unit)? = null,
    actions: @Composable (FriendEntry) -> Unit,
) {
    if (people.isEmpty() && empty == null) return
    item(key = "h-$title") {
        Text(title, style = MaterialTheme.typography.titleSmall, modifier = Modifier.padding(top = 12.dp, bottom = 4.dp))
    }
    if (people.isEmpty()) item(key = "e-$title") { Text(empty!!, color = MaterialTheme.colorScheme.outline) }
    items(people, key = { "$title-${it.username}" }) { u -> FriendRow(u, onOpen) { actions(u) } }
}

/** One line per person, bots included, so every row is the same height. Tapping a
 *  friend opens their Field Guide. */
@Composable
private fun FriendRow(u: FriendEntry, onOpen: ((String) -> Unit)?, actions: @Composable () -> Unit) {
    Row(Modifier.fillMaxWidth().height(48.dp).let { m -> onOpen?.let { m.clickable { it(u.username) } } ?: m },
        verticalAlignment = Alignment.CenterVertically) {
        Text((if (u.isBot) "🤖 " else "") + u.username, Modifier.weight(1f), maxLines = 1,
            overflow = TextOverflow.Ellipsis, style = MaterialTheme.typography.bodyLarge)
        if (u.caught > 0) Text("${u.caught} captured", style = MaterialTheme.typography.bodySmall,
            color = MaterialTheme.colorScheme.outline, maxLines = 1, modifier = Modifier.padding(end = 4.dp))
        actions()
    }
    HorizontalDivider()
}

// --- A friend's Field Guide ---------------------------------------------------------------

private val RARITY_ORDER = listOf("common", "uncommon", "rare", "legendary")

/** The friend's Field Guide in their own state: Captured, then Not captured yet. */
@Composable
fun FriendGuideDialog(s: SocialState, social: SocialViewModel, game: UiState) {
    val who = s.guideFor ?: return
    val g = s.guide
    // A plain Dialog, not AlertDialog: AlertDialog measures intrinsics, which lazy grids can't do.
    Dialog(onDismissRequest = social::closeGuide) {
        Surface(shape = RoundedCornerShape(20.dp), tonalElevation = 6.dp) {
            Column(Modifier.padding(16.dp)) {
                val stateName = g?.let { gd -> game.states.firstOrNull { it.code == gd.state }?.name ?: gd.state }
                Text(if (g == null) "$who's Field Guide" else "$who's Field Guide · $stateName · ${g.caught}/${g.total}",
                    style = MaterialTheme.typography.titleMedium, maxLines = 2, overflow = TextOverflow.Ellipsis)
                Spacer(Modifier.height(8.dp))
                when {
                    s.guideError != null -> Text(s.guideError, color = MaterialTheme.colorScheme.error)
                    g == null -> Box(Modifier.fillMaxWidth().height(120.dp), Alignment.Center) { CircularProgressIndicator() }
                    else -> {
                        // Numbered in Field Guide order (common to legendary), as on the website.
                        val numbered = g.entries.withIndex()
                            .sortedBy { (i, e) -> RARITY_ORDER.indexOf(e.rarity) * 1000 + i }
                            .mapIndexed { i, e -> i + 1 to e.value }
                        LazyVerticalGrid(columns = GridCells.Adaptive(72.dp), modifier = Modifier.weight(1f, fill = false),
                            horizontalArrangement = Arrangement.spacedBy(6.dp), verticalArrangement = Arrangement.spacedBy(6.dp)) {
                            for ((title, list) in listOf("Captured" to numbered.filter { it.second.caught },
                                                         "Not captured yet" to numbered.filter { !it.second.caught })) {
                                if (list.isEmpty()) continue
                                item(key = "h-$title", span = { GridItemSpan(maxLineSpan) }) {
                                    Text(title, style = MaterialTheme.typography.titleSmall,
                                        modifier = Modifier.padding(top = 8.dp, bottom = 2.dp))
                                }
                                items(list, key = { "$title-${it.second.number}" }) { (n, e) -> GuideTile(n, e) }
                            }
                        }
                    }
                }
                TextButton(onClick = social::closeGuide, modifier = Modifier.align(Alignment.End)) { Text("Close") }
            }
        }
    }
}

@Composable
private fun GuideTile(n: Int, e: GuideEntry) {
    val border = if (e.caught) MaterialTheme.colorScheme.primary else MaterialTheme.colorScheme.outlineVariant
    Column(Modifier.clip(RoundedCornerShape(8.dp)).background(MaterialTheme.colorScheme.surface)
        .border(if (e.caught) 2.dp else 1.dp, border, RoundedCornerShape(8.dp)).padding(4.dp),
        horizontalAlignment = Alignment.CenterHorizontally) {
        Text("#%03d".format(n), style = MaterialTheme.typography.labelSmall, color = MaterialTheme.colorScheme.outline)
        Box(Modifier.size(48.dp), Alignment.Center) {
            if (e.slug != null) PixelSprite(e.slug, caught = true, modifier = Modifier.fillMaxSize()
                .let { if (e.caught) it else it.alpha(0.6f) })
            else Text("?", style = MaterialTheme.typography.titleLarge, color = MaterialTheme.colorScheme.outline)
        }
        Text(e.commonName ?: "???", style = MaterialTheme.typography.labelSmall, maxLines = 1,
            overflow = TextOverflow.Ellipsis, color = if (e.caught) rarityColor(e.rarity) else MaterialTheme.colorScheme.outline)
        Text(when { e.caught -> "✓"; e.youCaught -> "You have it"; else -> " " },
            style = MaterialTheme.typography.labelSmall, maxLines = 1,
            color = if (e.caught) MaterialTheme.colorScheme.primary else MaterialTheme.colorScheme.outline)
    }
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
                        Row {
                            TextButton(onClick = { social.openComments(p) }, contentPadding = PaddingValues(0.dp)) {
                                Text("💬 ${p.commentCount}")
                            }
                            Spacer(Modifier.size(8.dp))
                            TextButton(onClick = { confirm = p }, contentPadding = PaddingValues(0.dp)) { Text("Delete photo") }
                        }
                    }
                }
            }
        }
    }
    CommentsDialog(s, social)
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
