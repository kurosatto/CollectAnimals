package com.captureanimals.app

import android.app.Application
import android.content.Context
import android.graphics.Bitmap
import android.net.Uri
import androidx.lifecycle.AndroidViewModel
import androidx.lifecycle.viewModelScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.update
import kotlinx.coroutines.launch
import kotlinx.coroutines.sync.Mutex
import kotlinx.coroutines.sync.withLock
import kotlinx.coroutines.withContext

data class RankedGuess(val label: String, val name: String, val probability: Float)

data class CaptureResult(
    val photo: Bitmap,
    val matched: Boolean,
    val species: Species?,
    val confidence: Float,
    val newBadge: Boolean,
    val message: String,
    val guesses: List<RankedGuess>,
    // The model's top species guesses, offered under "Not this animal? Pick the right one".
    val choices: List<RankedGuess> = emptyList(),
    // Set once the player has picked, so the panel isn't offered again.
    val picked: Boolean = false,
    // The server's capture id when signed in (picks go to the server too).
    val captureId: Int? = null,
    // Signed in: the photo's stars and points, and the field notes it ticked for the bond.
    val score: PhotoScore? = null,
    val bondUp: List<String> = emptyList(),
    // Signed in: when and where it was taken, which the player can fix.
    val whereWhen: WhereWhen? = null,
    // The state the photo counts in (where it was taken), and set when it was the
    // player's first photo from there, which unlocks that state.
    val state: String? = null,
    val unlockedState: String? = null,
)

/**
 * The states a player can make their main state: their main state, any state
 * they have a photo from (here or on the website), and states they unlocked
 * before photos did that.
 */
fun UiState.unlockedStates(): Set<String> =
    // Signed in, the server knows every photo, here or on the website.
    (account?.unlockedStates?.toSet() ?: unlocked) + stateCode

data class UiState(
    // The model with the chosen state's species list, and that state's Field Guide.
    val info: ModelInfo? = null,
    val fieldGuide: FieldGuide? = null,
    val states: List<StateInfo> = emptyList(),
    val stateCode: String = "",
    // Every state's species, so photos of animals from another state still show.
    val allSpecies: List<Species> = emptyList(),
    // First launch: ask which state the player is in, like the website's sign-up.
    val needsStatePick: Boolean = false,
    // States unlocked on this phone (photos taken there, past main states); see [unlockedStates].
    val unlocked: Set<String> = emptySet(),
    val collection: Map<String, Badge> = emptyMap(),
    val busy: Boolean = false,
    val result: CaptureResult? = null,
    val error: String? = null,
    // Signed in to the game server: captures, badges and photos live there, as on the website.
    val account: Account? = null,
    // The server address in use, or null while it can't be found.
    val server: String? = null,
    val accountBusy: Boolean = false,
    val accountError: String? = null,
    // species/sets.json; each state shows its own sets (works offline too).
    val sets: SetCatalog = SetCatalog(emptyList()),
    // Signed in: this week's challenges (they live on the server).
    val week: Week? = null,
)

class GameViewModel(app: Application) : AndroidViewModel(app) {
    private val store = CollectionStore(app.filesDir)
    private val _state = MutableStateFlow(UiState())
    val state: StateFlow<UiState> = _state

    private val prefs = app.getSharedPreferences("settings", Context.MODE_PRIVATE)
    private var classifier: Classifier? = null
    private val classifierLock = Mutex()
    private var model: ModelInfo? = null

    init {
        Online.init(app)
        _state.update { it.copy(server = Online.base) }
        viewModelScope.launch {
            val assets = getApplication<Application>().assets
            fun text(name: String) = assets.open(name).bufferedReader().use { it.readText() }
            val (base, states) = withContext(Dispatchers.IO) {
                ModelInfo.parse(text("model.json")) to States.load { name -> runCatching { text(name) }.getOrNull() }
            }
            val sets = withContext(Dispatchers.IO) { SetCatalog.parse(runCatching { text("sets.json") }.getOrNull()) }
            model = base
            val (default, list) = states
            val saved = prefs.getString("state", null)?.takeIf { code -> list.any { it.code == code } }
            val unlocked = prefs.getStringSet("unlocked", emptySet()).orEmpty()
            withContext(Dispatchers.IO) {
                store.migrate(saved ?: default)
                // Read the starting state's Field Guide here rather than on the main thread.
                list.firstOrNull { it.code == (saved ?: default) }?.fieldGuide
            }
            _state.update {
                it.copy(states = list, needsStatePick = saved == null, sets = sets, unlocked = unlocked,
                    allSpecies = list.flatMap { s -> s.species }.distinctBy { s -> s.slug })
            }
            select(saved ?: default)
            connect()
        }
    }

    /** Finds the server and, if signed in, loads the account and its badges. */
    fun connect() {
        viewModelScope.launch {
            val server = Online.resolve()
            _state.update { it.copy(server = server) }
            if (server == null || !Online.signedIn) return@launch
            try {
                val me = Online.me()
                _state.update { it.copy(account = me) }
                if (me.state != _state.value.stateCode && _state.value.states.any { it.code == me.state }) {
                    prefs.edit().putString("state", me.state).apply()
                    _state.update { it.copy(needsStatePick = false) }
                    select(me.state)
                }
                refreshCollection()
            } catch (e: Online.ApiError) {
                // Signed out by the server (401): back to the badges saved on this phone.
                if (!Online.signedIn) _state.update { it.copy(account = null, collection = store.load(it.stateCode), week = null) }
            }
        }
    }

    private suspend fun refreshCollection() {
        if (!Online.signedIn || _state.value.account == null) return
        val c = Online.collection(_state.value.stateCode)
        _state.update { it.copy(collection = c) }
        // Extras: the game works without them if the server can't send them.
        val week = runCatching { Online.challenges() }.getOrNull()
        _state.update { it.copy(week = week) }
    }

    fun signIn(ident: String, password: String) = account { Online.login(ident.trim(), password) }

    fun signUp(email: String, username: String, password: String) =
        account { Online.register(email.trim(), username.trim(), password, _state.value.stateCode) }

    private fun account(block: suspend () -> Unit) {
        _state.update { it.copy(accountBusy = true, accountError = null) }
        viewModelScope.launch {
            try {
                if (Online.resolve() == null) throw Online.ApiError(0, "Can't find the game server. Is the PC on?")
                _state.update { it.copy(server = Online.base) }
                block()
                val me = Online.me()
                _state.update { it.copy(account = me, accountBusy = false, result = null) }
                if (me.state != _state.value.stateCode && _state.value.states.any { it.code == me.state }) {
                    chooseState(me.state)
                } else {
                    refreshCollection()
                }
            } catch (e: Exception) {
                _state.update { it.copy(accountBusy = false, accountError = e.message ?: "Something went wrong") }
            }
        }
    }

    /** Back to playing offline, with the badges saved on this phone. */
    fun signOut() {
        Online.logout()
        _state.update { it.copy(account = null, collection = store.load(it.stateCode), result = null, week = null) }
    }

    fun setServer(url: String?) {
        Online.setManualUrl(url)
        _state.update { it.copy(server = Online.base) }
        connect()
    }

    fun setShowInFeed(on: Boolean) {
        val acct = _state.value.account ?: return
        _state.update { it.copy(account = acct.copy(showInFeed = on)) }
        viewModelScope.launch { runCatching { Online.setShowInFeed(on) } }
    }

    /** After the Photos tab deletes an album photo, the badge may be gone too. */
    fun reloadCollection() {
        viewModelScope.launch { runCatching { refreshCollection() } }
    }

    private fun select(code: String) {
        val base = model ?: return
        val st = _state.value.states.firstOrNull { it.code == code } ?: return
        // Offline, the phone keeps each state's catches apart; signed in, they come from the server.
        _state.update { it.copy(stateCode = st.code, info = base.withSpecies(st.species), fieldGuide = st.fieldGuide,
            collection = if (it.account == null) store.load(st.code) else it.collection) }
    }

    /** The player's state: its 100 species, Field Guide and parks. Captures count only in the state they were made in. */
    fun chooseState(code: String) {
        val unlocked = _state.value.unlocked + code
        prefs.edit().putString("state", code).putStringSet("unlocked", unlocked).apply()
        _state.update { it.copy(needsStatePick = false, result = null, unlocked = unlocked) }
        select(code)
        if (_state.value.account != null) viewModelScope.launch {
            runCatching {
                Online.setState(code)
                _state.update { it.copy(account = it.account?.let { a -> a.copy(state = code,
                    unlockedStates = (a.unlockedStates + code).distinct()) }) }
                refreshCollection()
            }.onFailure { e -> _state.update { it.copy(error = e.message) } }
        }
    }

    private suspend fun classifier(info: ModelInfo): Classifier = classifierLock.withLock {
        classifier ?: withContext(Dispatchers.IO) {
            val bytes = getApplication<Application>().assets.open("model.onnx").use { it.readBytes() }
            Classifier(bytes, info)
        }.also { classifier = it }
    }

    /**
     * [location] is where the phone is now, (lat, lon), when the player lets us save where
     * they captured it ([savePlace]); the photo's own time and place come first.
     */
    fun capture(uri: Uri, location: Pair<Double, Double>? = null, savePlace: Boolean = true, crop: CropBox? = null) {
        val info = _state.value.info ?: return
        _state.update { it.copy(busy = true, error = null) }
        viewModelScope.launch {
            try {
                val result = if (_state.value.account != null) {
                    captureOnline(uri, info, location, savePlace, crop)
                } else {
                    withContext(Dispatchers.Default) { classify(uri, info, if (savePlace) location else null, crop) }
                }
                _state.update { it.copy(busy = false, result = result) }
            } catch (e: Online.ApiError) {
                _state.update { it.copy(busy = false, error = e.message) }
            } catch (e: Exception) {
                _state.update { it.copy(busy = false, error = "Couldn't read that photo (${e.message})") }
            }
        }
    }

    /** Signed in: the server identifies the photo and keeps the badge, as on the website. */
    private suspend fun captureOnline(uri: Uri, info: ModelInfo, location: Pair<Double, Double>?,
                                      savePlace: Boolean, crop: CropBox?): CaptureResult {
        val bitmap = withContext(Dispatchers.IO) { ImageLoader.load(getApplication(), uri, minShortSide = if (crop == null) 1200 else 2400).cropTo(crop) }
        val meta = withContext(Dispatchers.IO) { readPhotoMeta(getApplication(), uri) }
        val r = Online.capture(bitmap, location?.first, location?.second, meta, savePlace)
        val result = onlineResult(r, ImageLoader.thumbnail(bitmap, 1024), info)
        result.unlockedState?.let { code ->
            _state.update { it.copy(account = it.account?.let { a -> a.copy(unlockedStates = (a.unlockedStates + code).distinct()) }) }
        }
        runCatching { refreshCollection() }
        return result
    }

    private fun onlineResult(r: org.json.JSONObject, photo: Bitmap, info: ModelInfo,
                             prev: CaptureResult? = null): CaptureResult {
        val bySlug = (_state.value.allSpecies + info.species).associateBy { it.slug }
        val species = r.optJSONObject("species")?.optStringOrNull("slug")?.let { bySlug[it] }
        val matched = r.getBoolean("matched") && species != null
        val preds = r.optJSONArray("top_predictions")
        val choices = r.optJSONArray("choices")
        return CaptureResult(
            photo = photo,
            matched = matched,
            species = if (matched) species else null,
            confidence = r.optDouble("confidence", 0.0).toFloat(),
            newBadge = r.optBoolean("new_badge"),
            message = r.optString("message"),
            guesses = prev?.guesses ?: List(preds?.length() ?: 0) { i ->
                preds!!.getJSONObject(i).let { p ->
                    RankedGuess(p.getString("label"), p.optStringOrNull("common_name") ?: "Something else",
                        p.getDouble("probability").toFloat())
                }
            }.take(3),
            choices = prev?.choices ?: List(choices?.length() ?: 0) { i ->
                choices!!.getJSONObject(i).let { c ->
                    RankedGuess(c.getString("slug"), c.getString("common_name"), c.getDouble("probability").toFloat())
                }
            },
            picked = prev != null,
            captureId = r.getInt("capture_id"),
            score = PhotoScore.parse(r.optJSONObject("score")),
            bondUp = r.optJSONArray("bond_up")?.let { a -> List(a.length()) { a.getString(it) } }.orEmpty(),
            whereWhen = WhereWhen.parse(r.optJSONObject("where_when")) ?: prev?.whereWhen,
            state = r.optStringOrNull("state") ?: prev?.state,
            unlockedState = prev?.unlockedState ?: r.optStringOrNull("unlocked_state"),
        )
    }

    // Same rules as the backend's POST /captures, including counting the photo in
    // the state it was taken in (from its EXIF, or [location] if it's recent).
    private suspend fun classify(uri: Uri, mainInfo: ModelInfo, location: Pair<Double, Double>?,
                                 crop: CropBox? = null): CaptureResult {
        val app = getApplication<Application>()
        val ui = _state.value
        val meta = readPhotoMeta(app, uri)
        val place = meta?.latitude?.let { lat -> meta.longitude?.let { lat to it } }
            ?: location?.takeIf { meta?.takenAt == null || java.time.Duration.between(meta.takenAt, java.time.LocalDateTime.now()).toHours() < 3 }
        val here = place?.let { (lat, lon) -> States.stateAt(ui.states, lat, lon) }
        val code = here?.code ?: ui.stateCode
        val info = if (here == null || code == ui.stateCode) mainInfo else (model ?: mainInfo).withSpecies(here.species)
        val newlyUnlocked = code !in ui.unlockedStates()
        if (newlyUnlocked) {
            val unlocked = ui.unlocked + code
            prefs.edit().putStringSet("unlocked", unlocked).apply()
            _state.update { it.copy(unlocked = unlocked) }
        }
        // Cropping keeps a part, so decode bigger to keep enough pixels for the model.
        val bitmap = ImageLoader.load(app, uri, minShortSide = if (crop == null) info.resize else info.resize * 3).cropTo(crop)
        // Five guesses: three are shown, all five are offered if the player corrects the model.
        // Only the chosen state's animals count, as on the website.
        val allowed = info.species.map { it.slug }.toSet() + info.otherLabel
        val preds = classifier(info).predict(ImageLoader.toRgb(bitmap), k = 5, allowed = allowed)
        val bySlug = info.species.associateBy { it.slug }
        val top = preds.first()
        val species = bySlug[top.label]
        val matched = species != null && top.probability >= info.matchThreshold

        var newBadge = false
        if (matched) {
            val thumb = ImageLoader.thumbnail(bitmap, 512)
            val (updated, isNew) = withContext(Dispatchers.IO) {
                store.addCatch(code, collectionOf(code), species!!.slug, thumb)
            }
            newBadge = isNew
            if (code == _state.value.stateCode) _state.update { it.copy(collection = updated) }
        }
        val stateName = here?.name ?: regionName()
        var message = when {
            matched && newBadge -> "You captured a ${species!!.commonName}! New badge unlocked."
            matched -> "Another ${species!!.commonName} for your collection."
            species != null -> "Might be a ${species.commonName}, but we're not sure. Try a clearer photo!"
            else -> "We couldn't match this to any animal in the $stateName collection."
        }
        if (newlyUnlocked) message = "📍 You unlocked $stateName! $message"
        else if (code != ui.stateCode && matched) message += " It counts in your $stateName Field Guide."
        return CaptureResult(
            photo = ImageLoader.thumbnail(bitmap, 1024),
            matched = matched,
            species = if (matched) species else null,
            confidence = top.probability,
            newBadge = newBadge,
            message = message,
            guesses = preds.take(3).map {
                RankedGuess(it.label, bySlug[it.label]?.commonName ?: "Something else", it.probability)
            },
            choices = preds.mapNotNull { p -> bySlug[p.label]?.let { RankedGuess(p.label, it.commonName, p.probability) } },
            state = code,
            unlockedState = code.takeIf { newlyUnlocked },
        )
    }

    /** Fixes when and where the photo on the result card was taken; an error message, or null. */
    suspend fun saveWhereWhen(takenAt: java.time.LocalDateTime, place: Pair<Double, Double>?): String? {
        val r = _state.value.result ?: return null
        val id = r.captureId ?: return null
        return try {
            val res = Online.whereWhen(id, takenAt, place)
            _state.update { s ->
                s.copy(result = s.result?.let { cur ->
                    if (cur.captureId != id) cur else cur.copy(
                        whereWhen = WhereWhen.parse(res.getJSONObject("where_when")),
                        score = PhotoScore.parse(res.optJSONObject("score")) ?: cur.score,
                        bondUp = res.optJSONArray("bond_up")?.let { a -> List(a.length()) { a.getString(it) } }.orEmpty(),
                    )
                })
            }
            runCatching { refreshCollection() }
            null
        } catch (e: Exception) {
            e.message ?: "Couldn't save"
        }
    }

    /**
     * The player names the animal themselves (slug), or says "none of these" (null).
     * We trust them: the badge moves to their pick, as on the website.
     */
    fun pick(slug: String?) {
        val r = _state.value.result ?: return
        val info = _state.value.info ?: return
        r.captureId?.let { id ->
            viewModelScope.launch {
                try {
                    val res = onlineResult(Online.pick(id, slug ?: "none"), r.photo, info, prev = r)
                    _state.update { it.copy(result = res) }
                    refreshCollection()
                } catch (e: Exception) {
                    _state.update { it.copy(error = e.message) }
                }
            }
            return
        }
        // The photo counts in the state it was taken in, which may not be the main one.
        val code = r.state ?: _state.value.stateCode
        val list = _state.value.states.firstOrNull { it.code == code }?.species ?: info.species
        val species = slug?.let { s -> list.firstOrNull { it.slug == s } }
        viewModelScope.launch {
            var collection = _state.value.collection
            var newBadge = false
            withContext(Dispatchers.IO) {
                if (code != _state.value.stateCode) collection = store.load(code)
                if (r.matched && r.species != null && r.species.slug != slug) {
                    collection = store.removeCatch(code, collection, r.species.slug)
                }
                if (species != null && r.species?.slug != species.slug) {
                    val (updated, isNew) = store.addCatch(code, collection, species.slug, ImageLoader.thumbnail(r.photo, 512))
                    collection = updated
                    newBadge = isNew
                }
            }
            if (code != _state.value.stateCode) collection = _state.value.collection
            val result = if (species == null) {
                r.copy(matched = false, species = null, newBadge = false, picked = true,
                    message = "Okay, this photo doesn't count for any animal.")
            } else {
                r.copy(matched = true, species = species, newBadge = newBadge, picked = true,
                    message = if (newBadge) "Got it: a ${species.commonName}! New badge unlocked."
                              else "Got it: another ${species.commonName} for your collection.")
            }
            _state.update { it.copy(collection = collection, result = result) }
        }
    }

    /** "Delete photo": removes the photo and the catch, as on the website. */
    fun deleteCatch(slug: String) {
        viewModelScope.launch {
            val updated = withContext(Dispatchers.IO) { store.forget(_state.value.stateCode, _state.value.collection, slug) }
            _state.update { it.copy(collection = updated) }
        }
    }

    /** The phone's badges for a state: the ones on screen for the main state, else read from storage. */
    private fun collectionOf(code: String) =
        if (code == _state.value.stateCode) _state.value.collection else store.load(code)

    private fun regionName() = _state.value.fieldGuide?.region ?: "state"

    fun dismissResult() = _state.update { it.copy(result = null, error = null) }

    override fun onCleared() {
        classifier?.close()
    }
}
