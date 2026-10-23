package com.captureanimals.app

import android.app.Application
import android.graphics.Bitmap
import androidx.compose.foundation.Image
import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.clickable
import androidx.compose.foundation.horizontalScroll
import androidx.compose.foundation.gestures.rememberTransformableState
import androidx.compose.foundation.gestures.transformable
import androidx.compose.foundation.layout.heightIn
import androidx.compose.foundation.layout.imePadding
import androidx.compose.runtime.mutableFloatStateOf
import androidx.compose.ui.draw.clipToBounds
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.graphicsLayer
import androidx.compose.ui.window.DialogProperties
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
import androidx.compose.material3.RadioButton
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
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.platform.LocalUriHandler
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
import org.json.JSONObject
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
    // The photo open full screen (its comments load into the fields above).
    val viewing: OnlinePhoto? = null,
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
        _state.update { it.copy(feed = swap(it.feed), album = it.album?.let(::swap),
            viewing = it.viewing?.let { v -> swap(listOf(v)).first() }) }
        viewModelScope.launch {
            runCatching { Online.like(p.id, on) }.onFailure { e -> _state.update { it.copy(message = e.message) } }
        }
    }

    private fun setCommentCount(photoId: Int, n: Int) {
        fun swap(list: List<OnlinePhoto>) = list.map { if (it.id == photoId) it.copy(commentCount = n) else it }
        _state.update { it.copy(feed = swap(it.feed), album = it.album?.let(::swap),
            viewing = it.viewing?.let { v -> swap(listOf(v)).first() }) }
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

    /** Full screen, with its likes and comments. */
    fun openPhoto(p: OnlinePhoto) {
        _state.update { it.copy(viewing = p) }
        openComments(p)
    }
    /** Fixes when and where one of your photos was taken; an error message, or null when saved. */
    suspend fun saveWhereWhen(p: OnlinePhoto, takenAt: java.time.LocalDateTime, place: Pair<Double, Double>?): String? {
        val ww = p.whereWhen ?: return null
        return try {
            val res = Online.whereWhen(ww.captureId, takenAt, place)
            val new = WhereWhen.parse(res.getJSONObject("where_when"))!!
            val score = PhotoScore.parse(res.optJSONObject("score"))
            fun swap(list: List<OnlinePhoto>) = list.map {
                if (it.id != p.id) it else it.copy(whereWhen = new, place = new.place,
                    takenOn = new.takenAt.toLocalDate().atTime(12, 0).atZone(java.time.ZoneId.systemDefault())
                        .toInstant().toEpochMilli(),
                    score = score?.total ?: it.score, stars = score?.stars ?: it.stars)
            }
            _state.update { it.copy(feed = swap(it.feed), album = it.album?.let(::swap),
                viewing = it.viewing?.let { v -> swap(listOf(v)).first() }) }
            null
        } catch (e: Exception) {
            e.message ?: "Couldn't save"
        }
    }

    fun closePhoto() {
        _state.update { it.copy(viewing = null) }
        closeComments()
    }

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

    fun loadFriends() = run { reloadFriends() }

    /** Refreshes friend requests for the Friends tab's badge, without a spinner or errors. */
    fun checkRequests() {
        if (!Online.signedIn) return
        viewModelScope.launch {
            runCatching { Online.friends() }.onSuccess { f -> _state.update { it.copy(friends = f) }; seen(f) }
        }
    }

    // Requests shown in the app don't need a phone notification later.
    private fun seen(f: Friends) = FriendAlerts.markSeen(getApplication<Application>(), f)

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
        seen(f)
        val s = runCatching { Online.suggestions() }.getOrDefault(emptyList())
        _state.update { it.copy(friends = f, suggestions = s) }
    }

    /** Opens [username]'s Field Guide on their primary state, or on [state] (one of their places). */
    fun openGuide(username: String, state: String? = null) {
        // Switching places keeps the open guide on screen until the new one arrives.
        _state.update { it.copy(guideFor = username, guide = if (state != null) it.guide else null, guideError = null) }
        viewModelScope.launch {
            runCatching { Online.friendGuide(username, state) }
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

    /** Report a photo, comment or player; [done] gets the line to show. */
    fun report(target: JSONObject, reason: String, details: String?, done: (String) -> Unit) {
        viewModelScope.launch {
            runCatching { Online.report(target, reason, details) }
                .onSuccess { hidden ->
                    done(if (hidden) "Thanks. It's hidden until a moderator looks at it." else "Thanks, we'll take a look.")
                    if (hidden) loadFeed()
                }
                .onFailure { done(it.message ?: "Couldn't send the report") }
        }
    }

    /** Block a player: their photos and comments disappear and they can't add you. */
    fun block(username: String) = run {
        Online.block(username)
        _state.update { it.copy(viewing = null, commentsFor = null, comments = null, message = "Blocked $username") }
        reloadFriends()
        val (photos, next) = Online.feed(_state.value.feedScope, _state.value.feedState, null)
        _state.update { it.copy(feed = photos, feedNext = next) }
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
    }, title = {
        Row(verticalAlignment = Alignment.CenterVertically) {
            acct?.let { Avatar(it.avatar, Modifier.size(40.dp)); Spacer(Modifier.size(10.dp)) }
            Text(acct?.let { "Signed in as ${it.username}" } ?: if (signUp) "Create an account" else "Log in")
        }
    },
    text = {
        Column(Modifier.verticalScroll(rememberScrollState()), verticalArrangement = Arrangement.spacedBy(8.dp)) {
            if (acct == null) {
                val here = state.states.find { it.code == state.stateCode } ?: state.states.firstOrNull()
                val place = here?.name ?: "your state"
                HabitatShowcase(rememberHabitatView(), here?.code ?: "", place)
                Text("How many of $place's ${here?.species?.size ?: 100} animals can you capture?", style = MaterialTheme.typography.titleMedium,
                    fontWeight = FontWeight.Bold)
                Text("Spot a wild animal, snap a great photo, and it's captured in your Field Guide. Then it moves " +
                    "into your own little pixel habitat, like the one here.", style = MaterialTheme.typography.bodyMedium)
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
                Text(if (signUp) "For players 13 and older. By signing up you agree to the community rules " +
                    "and privacy policy." else "For players 13 and older.", style = MaterialTheme.typography.bodySmall)
                PrivacyLink()
            } else {
                // Your profile picture: tap one of the ten to switch.
                Text("Your picture", style = MaterialTheme.typography.titleSmall)
                for (row in listOf(1..5, 6..10)) {
                    Row(horizontalArrangement = Arrangement.spacedBy(6.dp)) {
                        for (n in row) {
                            val on = n == acct.avatar
                            Avatar(n, Modifier.size(44.dp).clip(RoundedCornerShape(50))
                                .border(if (on) 3.dp else 0.dp, if (on) MaterialTheme.colorScheme.primary
                                    else Color.Transparent, RoundedCornerShape(50))
                                .clickable { vm.setAvatar(n) })
                        }
                    }
                }
                Row(verticalAlignment = Alignment.CenterVertically) {
                    Text("Show my captures in the news feed", Modifier.weight(1f))
                    Switch(acct.showInFeed, onCheckedChange = vm::setShowInFeed)
                }
                BlockedPlayers()
                PrivacyLink()
                DeleteAccount(vm, onDismiss)
            }
            HorizontalDivider()
            Text(if (state.server != null) "Game server: online" else "Game server: can't be found right now",
                style = MaterialTheme.typography.labelMedium, color = MaterialTheme.colorScheme.outline)
            Text("App version ${BuildConfigCompat.version(LocalContext.current)}",
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
/** The Feed tab ([section] "feed") or the Friends tab ("friends"), as on the website. */
fun SocialScreen(state: UiState, social: SocialViewModel, section: String, onSignIn: () -> Unit,
                 onOpenDex: (String) -> Unit) {
    if (state.account == null) {
        Column(Modifier.fillMaxSize().padding(24.dp), horizontalAlignment = Alignment.CenterHorizontally,
            verticalArrangement = Arrangement.spacedBy(12.dp, Alignment.CenterVertically)) {
            Text("Log in to see what other players are capturing, add friends, and like and comment on photos.",
                textAlign = TextAlign.Center, style = MaterialTheme.typography.bodyLarge)
            Button(onClick = onSignIn) { Text("Log in or sign up") }
        }
        return
    }
    val s by social.state.collectAsStateWithLifecycle()
    Column(Modifier.fillMaxSize()) {
        s.message?.let { Text(it, Modifier.padding(horizontal = 16.dp), color = MaterialTheme.colorScheme.outline,
            style = MaterialTheme.typography.bodySmall) }
        if (section == "feed") FeedSection(s, social, state, onOpenDex) else FriendsSection(s, social)
    }
    CommentsDialog(s, social)
    PhotoViewer(s, social, state.fieldGuide?.parks.orEmpty())
    FriendGuideDialog(s, social, state, onOpenDex)
}

/** Comments on one photo. Anyone who can see the photo can join in, friends or not. */
@Composable
fun CommentsDialog(s: SocialState, social: SocialViewModel) {
    val p = s.commentsFor ?: return
    if (s.viewing != null) return  // the full-screen photo shows them itself
    AlertDialog(onDismissRequest = social::closeComments,
        confirmButton = { TextButton(onClick = social::closeComments) { Text("Close") } },
        title = { Text("Comments · ${p.commonName ?: "photo"} by ${if (p.isMine) "you" else p.username}",
            maxLines = 2, overflow = TextOverflow.Ellipsis) },
        text = { Comments(s, social, p) })
}

@Composable
private fun Comments(s: SocialState, social: SocialViewModel, p: OnlinePhoto) {
    var text by rememberSaveable(p.id) { mutableStateOf("") }
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
                        if (!c.isMine) ReportButton("this comment", social, offerBlock = c.username) {
                            JSONObject().put("comment_id", c.id) }
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
}

/**
 * One photo full screen at the size the server keeps (up to 1600 px), pinch to zoom, with
 * its likes and comments underneath. Only photos the server sent a url for can open, so
 * private players and animals you haven't unlocked stay hidden as in the feed.
 */
@Composable
fun PhotoViewer(s: SocialState, social: SocialViewModel, parks: List<Park> = emptyList(),
                onDelete: ((OnlinePhoto) -> Unit)? = null) {
    val p = s.viewing ?: return
    Dialog(onDismissRequest = social::closePhoto, properties = DialogProperties(usePlatformDefaultWidth = false)) {
        Column(Modifier.fillMaxSize().background(Color.Black).imePadding()) {
            Box(Modifier.weight(1f).fillMaxWidth().clipToBounds(), Alignment.Center) {
                var scale by remember(p.id) { mutableFloatStateOf(1f) }
                var offset by remember(p.id) { mutableStateOf(Offset.Zero) }
                val zoom = rememberTransformableState { z, pan, _ ->
                    scale = (scale * z).coerceIn(1f, 5f)
                    offset = if (scale == 1f) Offset.Zero else offset + pan * scale
                }
                val bmp by produceState<Bitmap?>(null, p.url) { value = p.url?.let { Online.image(it, 1600) } }
                bmp?.let {
                    Image(it.asImageBitmap(), contentDescription = p.commonName, contentScale = ContentScale.Fit,
                        modifier = Modifier.fillMaxSize().transformable(zoom)
                            .graphicsLayer(scaleX = scale, scaleY = scale, translationX = offset.x, translationY = offset.y))
                } ?: CircularProgressIndicator()
                TextButton(onClick = social::closePhoto, modifier = Modifier.align(Alignment.TopEnd).padding(8.dp)
                    .background(Color.Black.copy(alpha = 0.5f), RoundedCornerShape(50))) {
                    Text("✕", color = Color.White, style = MaterialTheme.typography.titleLarge)
                }
            }
            Surface(Modifier.fillMaxWidth().heightIn(max = 360.dp)) {
                Column(Modifier.padding(16.dp), verticalArrangement = Arrangement.spacedBy(4.dp)) {
                    Row(verticalAlignment = Alignment.CenterVertically) {
                        Column(Modifier.weight(1f)) {
                            Text(p.commonName ?: "Photo", fontWeight = FontWeight.Bold, color = rarityColor(p.rarity),
                                style = MaterialTheme.typography.titleMedium, maxLines = 1, overflow = TextOverflow.Ellipsis)
                            p.stars?.let { Stars(it, points = p.score) }
                            if (p.whereWhen != null) {
                                WhereWhenRow(p.whereWhen, parks) { at, place -> social.saveWhereWhen(p, at, place) }
                            } else {
                                Text(listOfNotNull(if (p.isMine) "You" else p.username, p.place, dateOf(p.takenOn)).joinToString(" · "),
                                    style = MaterialTheme.typography.bodySmall, color = MaterialTheme.colorScheme.outline,
                                    maxLines = 2, overflow = TextOverflow.Ellipsis)
                            }
                        }
                        TextButton(onClick = { social.toggleLike(p) }, enabled = !p.isMine) {
                            Text((if (p.likedByMe) "♥ " else "♡ ") + p.likeCount)
                        }
                    }
                    if (p.isMine && onDelete != null) {
                        TextButton(onClick = { onDelete(p) }, contentPadding = PaddingValues(0.dp)) { Text("Delete photo") }
                    }
                    if (p.isMine && p.hidden) Text("Hidden from other players after reports",
                        color = MaterialTheme.colorScheme.error, style = MaterialTheme.typography.bodySmall)
                    if (!p.isMine) ReportButton("this photo", social, offerBlock = p.username) {
                        JSONObject().put("photo_id", p.id) }
                    HorizontalDivider()
                    Comments(s, social, p)
                }
            }
        }
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
                    .clickable { social.openPhoto(p) })
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
                    // The photo opens full screen; the name opens the Field Guide entry.
                    Text(p.commonName ?: "A ${p.rarity} ${p.category}", fontWeight = FontWeight.Bold,
                        color = rarityColor(p.rarity), maxLines = 1, overflow = TextOverflow.Ellipsis,
                        modifier = Modifier.clickable(enabled = p.slug != null) { p.slug?.let(onOpenDex) })
                    if (p.url != null) p.stars?.let { Stars(it, points = p.score) }
                    val who = (if (p.isMine) "You" else p.username) + (p.state?.let { " in $it" } ?: "")
                    Text(listOfNotNull(who, p.place, dateOf(p.takenOn)).joinToString(" · "),
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
        Avatar(u.avatar, Modifier.size(36.dp))
        Spacer(Modifier.size(10.dp))
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

/** The friend's Field Guide: the animals they've captured, on their primary state first,
 *  with a chip for each other state they've captured animals in. */
@Composable
fun FriendGuideDialog(s: SocialState, social: SocialViewModel, game: UiState, onOpenDex: (String) -> Unit) {
    val who = s.guideFor ?: return
    val g = s.guide
    // Their live habitat, in their state's scenery, as on the website's profile.
    val habitat = rememberHabitatView()
    // A plain Dialog, not AlertDialog: AlertDialog measures intrinsics, which lazy grids can't do.
    Dialog(onDismissRequest = social::closeGuide) {
        Surface(shape = RoundedCornerShape(20.dp), tonalElevation = 6.dp) {
            Column(Modifier.padding(16.dp)) {
                val stateName = g?.let { gd -> game.states.firstOrNull { it.code == gd.state }?.name ?: gd.state }
                Text(if (g == null) "$who's Field Guide" else "$who's Field Guide · $stateName · ${g.caught}/${g.total}",
                    style = MaterialTheme.typography.titleMedium, maxLines = 2, overflow = TextOverflow.Ellipsis)
                if (g != null && g.places.size > 1) Row(Modifier.horizontalScroll(rememberScrollState()).padding(top = 6.dp),
                    horizontalArrangement = Arrangement.spacedBy(6.dp)) {
                    for (p in g.places) FilterChip(p.state == g.state, { if (p.state != g.state) social.openGuide(who, p.state) },
                        label = { Text((if (p.state == g.primaryState) "📍 " else "") + "${p.name} · ${p.caught}") })
                }
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
                            // Only the animals they've captured; numbers follow the full Field Guide.
                            val captured = numbered.filter { it.second.caught }
                            val animals = captured.mapNotNull { (n, e) ->
                                e.slug?.let { HabitatAnimal(n, it, e.commonName ?: "", e.category, e.rarity, e.activity ?: "day") }
                            }
                            if (animals.isNotEmpty()) item(span = { GridItemSpan(maxLineSpan) }, key = "habitat") {
                                Habitat(habitat, animals, g.state, visitor = who) { slug ->
                                    social.closeGuide(); onOpenDex(slug)
                                }
                            }
                            if (captured.isEmpty()) item(span = { GridItemSpan(maxLineSpan) }) {
                                Text("$who hasn't captured any animals yet.", color = MaterialTheme.colorScheme.outline)
                            }
                            for ((title, list) in listOf("Captured" to captured)) {
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
        // Captured: their album photo's stars, once it's scored.
        val photoStars = e.photoStars?.takeIf { e.caught }
        Text(when { photoStars != null -> stars(photoStars); e.caught -> "✓"; e.youCaught -> "You have it"; else -> " " },
            style = MaterialTheme.typography.labelSmall, maxLines = 1,
            color = when { photoStars != null -> Gold; e.caught -> MaterialTheme.colorScheme.primary
                           else -> MaterialTheme.colorScheme.outline })
    }
}

// --- Photos tab when signed in: your album on the server -------------------------------------

@Composable
fun OnlinePhotosScreen(social: SocialViewModel, onOpenDex: (String) -> Unit, onDeleted: () -> Unit,
                       parks: List<Park> = emptyList()) {
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
    // Four to a row: the photo, its name and stars. Tap one for the full photo, its
    // likes and comments, and deleting it.
    LazyVerticalGrid(columns = GridCells.Fixed(4), modifier = Modifier.fillMaxSize(),
        contentPadding = PaddingValues(10.dp),
        horizontalArrangement = Arrangement.spacedBy(6.dp), verticalArrangement = Arrangement.spacedBy(6.dp)) {
        item(span = { GridItemSpan(maxLineSpan) }) {
            Text("${album.size} photo${if (album.size == 1) "" else "s"}",
                style = MaterialTheme.typography.labelLarge, color = MaterialTheme.colorScheme.outline)
        }
        items(album, key = { it.id }) { p ->
            Card(shape = RoundedCornerShape(8.dp), modifier = Modifier.clickable { social.openPhoto(p) }) {
                Column {
                    RemoteImage(p.url, p.commonName, Modifier.fillMaxWidth().aspectRatio(1f)
                        .clip(RoundedCornerShape(topStart = 8.dp, topEnd = 8.dp)), maxSide = 256)
                    Column(Modifier.padding(horizontal = 4.dp, vertical = 3.dp)) {
                        Text(p.commonName ?: "", style = MaterialTheme.typography.labelSmall, maxLines = 1,
                            overflow = TextOverflow.Ellipsis, color = rarityColor(p.rarity))
                        p.stars?.let { Text(stars(it), style = MaterialTheme.typography.labelSmall, color = Gold, maxLines = 1) }
                    }
                }
            }
        }
    }
    CommentsDialog(s, social)
    PhotoViewer(s, social, parks, onDelete = { confirm = it })
    confirm?.let { p ->
        AlertDialog(
            onDismissRequest = { confirm = null },
            title = { Text("Delete this photo?") },
            text = { Text("The ${p.commonName ?: "animal"} also leaves your collection. Capture it again to get it back.") },
            confirmButton = { TextButton(onClick = {
                social.deletePhoto(p, onDeleted); social.closePhoto(); confirm = null }) { Text("Delete") } },
            dismissButton = { TextButton(onClick = { confirm = null }) { Text("Cancel") } },
        )
    }
}


// --- Safety: privacy policy, blocking, reports, deleting the account ---------------------

// GitHub Pages copies of docs/, so the links work while the game server is off.
private const val DOCS = "https://kurosatto.github.io/CollectAnimals"

@Composable
private fun PrivacyLink() {
    val uri = LocalUriHandler.current
    Row(horizontalArrangement = Arrangement.spacedBy(16.dp)) {
        TextButton(onClick = { runCatching { uri.openUri("$DOCS/privacy.html") } }, contentPadding = PaddingValues(0.dp)) {
            Text("Privacy policy")
        }
        TextButton(onClick = { runCatching { uri.openUri("$DOCS/rules.html") } }, contentPadding = PaddingValues(0.dp)) {
            Text("Community rules")
        }
    }
}

/** Players you blocked, each with Unblock. */
@Composable
private fun BlockedPlayers() {
    var names by remember { mutableStateOf<List<String>>(emptyList()) }
    var reload by remember { mutableStateOf(0) }
    val scope = androidx.compose.runtime.rememberCoroutineScope()
    LaunchedEffect(reload) { names = runCatching { Online.blocks() }.getOrDefault(emptyList()) }
    if (names.isEmpty()) return
    Text("Players you blocked", style = MaterialTheme.typography.titleSmall)
    names.forEach { n ->
        Row(verticalAlignment = Alignment.CenterVertically) {
            Text(n, Modifier.weight(1f))
            TextButton(onClick = { scope.launch { runCatching { Online.unblock(n) }; reload++ } }) { Text("Unblock") }
        }
    }
}

/** Delete account: asks for the password, then deletes everything on the server. */
@Composable
private fun DeleteAccount(vm: GameViewModel, onDismiss: () -> Unit) {
    var asking by remember { mutableStateOf(false) }
    TextButton(onClick = { asking = true }, contentPadding = PaddingValues(0.dp)) {
        Text("Delete account", color = MaterialTheme.colorScheme.error)
    }
    if (!asking) return
    var password by remember { mutableStateOf("") }
    var busy by remember { mutableStateOf(false) }
    var error by remember { mutableStateOf<String?>(null) }
    AlertDialog(onDismissRequest = { if (!busy) asking = false },
        title = { Text("Delete your account?") },
        text = {
            Column(verticalArrangement = Arrangement.spacedBy(8.dp)) {
                Text("Your photos, Field Guide, friends, likes and comments on the server are all deleted for good. " +
                    "Captures saved on this phone stay here for offline play.")
                OutlinedTextField(password, { password = it }, label = { Text("Password") }, singleLine = true,
                    visualTransformation = PasswordVisualTransformation(), modifier = Modifier.fillMaxWidth(),
                    keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Password))
                error?.let { Text(it, color = MaterialTheme.colorScheme.error) }
            }
        },
        confirmButton = {
            Button(enabled = password.isNotEmpty() && !busy, onClick = {
                busy = true
                vm.deleteAccount(password) { err ->
                    busy = false
                    if (err == null) { asking = false; onDismiss() } else error = err
                }
            }) { Text("Delete for good") }
        },
        dismissButton = { TextButton(enabled = !busy, onClick = { asking = false }) { Text("Cancel") } })
}

private val REPORT_REASONS = listOf(
    "bullying" to "Bullying or mean",
    "inappropriate" to "Inappropriate (violence, nudity, gross)",
    "personal_info" to "Shows someone's personal info or face",
    "spam" to "Spam",
    "not_animal" to "Not an animal photo",
    "other" to "Something else",
)

/** "Report" (and, for another player's content, "Block"), each with its own dialog. */
@Composable
fun ReportButton(label: String, social: SocialViewModel, offerBlock: String? = null, target: () -> JSONObject) {
    var open by remember { mutableStateOf(false) }
    var confirmBlock by remember { mutableStateOf(false) }
    Row {
        TextButton(onClick = { open = true }, contentPadding = PaddingValues(horizontal = 4.dp)) { Text("Report") }
        if (offerBlock != null) TextButton(onClick = { confirmBlock = true },
            contentPadding = PaddingValues(horizontal = 4.dp)) { Text("Block") }
    }
    if (confirmBlock && offerBlock != null) AlertDialog(onDismissRequest = { confirmBlock = false },
        title = { Text("Block $offerBlock?") },
        text = { Text("You won't see each other's photos or comments, and they can't add you as a friend.") },
        confirmButton = { Button(onClick = { confirmBlock = false; social.block(offerBlock) }) { Text("Block") } },
        dismissButton = { TextButton(onClick = { confirmBlock = false }) { Text("Cancel") } })
    if (!open) return
    var reason by remember { mutableStateOf<String?>(null) }
    var details by remember { mutableStateOf("") }
    var result by remember { mutableStateOf<String?>(null) }
    var busy by remember { mutableStateOf(false) }
    AlertDialog(onDismissRequest = { open = false },
        title = { Text("Report $label") },
        text = {
            Column(Modifier.verticalScroll(rememberScrollState())) {
                Text("A moderator will look at it. The player isn't told who reported them.",
                    style = MaterialTheme.typography.bodySmall)
                REPORT_REASONS.forEach { (key, text) ->
                    Row(Modifier.fillMaxWidth().clickable { reason = key }, verticalAlignment = Alignment.CenterVertically) {
                        RadioButton(selected = reason == key, onClick = { reason = key })
                        Text(text, style = MaterialTheme.typography.bodyMedium)
                    }
                }
                OutlinedTextField(details, { if (it.length <= 500) details = it }, Modifier.fillMaxWidth(),
                    placeholder = { Text("Anything else? (optional)") }, maxLines = 3)
                result?.let { Text(it, Modifier.padding(top = 8.dp)) }
            }
        },
        confirmButton = {
            if (result == null) Button(enabled = reason != null && !busy, onClick = {
                busy = true
                social.report(target(), reason!!, details.trim()) { result = it; busy = false }
            }) { Text("Send report") }
            else TextButton(onClick = { open = false }) { Text("Close") }
        },
        dismissButton = { if (result == null) TextButton(onClick = { open = false }) { Text("Cancel") } })
}
