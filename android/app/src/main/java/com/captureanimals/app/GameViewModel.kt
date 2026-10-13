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
)

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
            val (base, states, collection) = withContext(Dispatchers.IO) {
                Triple(ModelInfo.parse(text("model.json")),
                       States.load { name -> runCatching { text(name) }.getOrNull() },
                       store.load())
            }
            model = base
            val (default, list) = states
            val saved = prefs.getString("state", null)?.takeIf { code -> list.any { it.code == code } }
            _state.update {
                it.copy(states = list, collection = collection, needsStatePick = saved == null,
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
                if (!Online.signedIn) _state.update { it.copy(account = null, collection = store.load()) }
            }
        }
    }

    private suspend fun refreshCollection() {
        if (!Online.signedIn || _state.value.account == null) return
        val c = Online.collection(_state.value.stateCode)
        _state.update { it.copy(collection = c) }
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
        _state.update { it.copy(account = null, collection = store.load(), result = null) }
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
        _state.update { it.copy(stateCode = st.code, info = base.withSpecies(st.species), fieldGuide = st.fieldGuide) }
    }

    /** The player's state: its 100 species, Field Guide and parks. Badges carry over. */
    fun chooseState(code: String) {
        prefs.edit().putString("state", code).apply()
        _state.update { it.copy(needsStatePick = false, result = null) }
        select(code)
        if (_state.value.account != null) viewModelScope.launch {
            runCatching {
                Online.setState(code)
                _state.update { it.copy(account = it.account?.copy(state = code)) }
                refreshCollection()
            }
        }
    }

    private suspend fun classifier(info: ModelInfo): Classifier = classifierLock.withLock {
        classifier ?: withContext(Dispatchers.IO) {
            val bytes = getApplication<Application>().assets.open("model.onnx").use { it.readBytes() }
            Classifier(bytes, info)
        }.also { classifier = it }
    }

    /** [location] is (lat, lon) when the player lets us save where they captured it. */
    fun capture(uri: Uri, location: Pair<Double, Double>? = null) {
        val info = _state.value.info ?: return
        _state.update { it.copy(busy = true, error = null) }
        viewModelScope.launch {
            try {
                val result = if (_state.value.account != null) {
                    captureOnline(uri, info, location)
                } else {
                    withContext(Dispatchers.Default) { classify(uri, info) }
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
    private suspend fun captureOnline(uri: Uri, info: ModelInfo, location: Pair<Double, Double>?): CaptureResult {
        val bitmap = withContext(Dispatchers.IO) { ImageLoader.load(getApplication(), uri, minShortSide = 1200) }
        val r = Online.capture(bitmap, location?.first, location?.second)
        val result = onlineResult(r, ImageLoader.thumbnail(bitmap, 1024), info)
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
        )
    }

    // Same rules as the backend's POST /captures.
    private suspend fun classify(uri: Uri, info: ModelInfo): CaptureResult {
        val app = getApplication<Application>()
        val bitmap = ImageLoader.load(app, uri, minShortSide = info.resize)
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
                store.addCatch(_state.value.collection, species!!.slug, thumb)
            }
            newBadge = isNew
            _state.update { it.copy(collection = updated) }
        }
        val message = when {
            matched && newBadge -> "You captured a ${species!!.commonName}! New badge unlocked."
            matched -> "Another ${species!!.commonName} for your collection."
            species != null -> "Might be a ${species.commonName}, but we're not sure. Try a clearer photo!"
            else -> "We couldn't match this to any animal in the ${regionName()} collection."
        }
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
        )
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
        val species = slug?.let { s -> info.species.firstOrNull { it.slug == s } }
        viewModelScope.launch {
            var collection = _state.value.collection
            var newBadge = false
            withContext(Dispatchers.IO) {
                if (r.matched && r.species != null && r.species.slug != slug) {
                    collection = store.removeCatch(collection, r.species.slug)
                }
                if (species != null && r.species?.slug != species.slug) {
                    val (updated, isNew) = store.addCatch(collection, species.slug, ImageLoader.thumbnail(r.photo, 512))
                    collection = updated
                    newBadge = isNew
                }
            }
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
            val updated = withContext(Dispatchers.IO) { store.forget(_state.value.collection, slug) }
            _state.update { it.copy(collection = updated) }
        }
    }

    private fun regionName() = _state.value.fieldGuide?.region ?: "state"

    fun dismissResult() = _state.update { it.copy(result = null, error = null) }

    override fun onCleared() {
        classifier?.close()
    }
}
