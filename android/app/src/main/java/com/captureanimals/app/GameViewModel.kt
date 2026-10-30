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
    // True when the photo has no place in a game state, so the player may say
    // which state it was taken in ("Taken in another state?").
    val canChangeState: Boolean = false,
    // Offline: the photo and crop, to identify it again in another state.
    val uri: Uri? = null,
    val crop: CropBox? = null,
    // "What was it?": the thank-you once the player named an animal that didn't count.
    val named: String? = null,
)

/** The player's main state; [UiState.stateCode] is the one on screen, which can be any unlocked state. */
fun UiState.mainState(): String = account?.state ?: mainCode

/**
 * The states a player can look at or make their main state: their main state and
 * any state they've captured an animal in (deleting the last one locks it again).
 */
fun UiState.unlockedStates(): Set<String> =
    // Signed in, the server knows every capture, here or on the website.
    (account?.unlockedStates?.toSet() ?: unlocked) + mainState()

/** A tile on the "Your states" screen: how much of the state's list the player has captured. */
data class StateTile(val code: String, val name: String, val caught: Int, val total: Int, val main: Boolean)

data class UiState(
    // The model with the chosen state's species list, and that state's Field Guide.
    val info: ModelInfo? = null,
    val fieldGuide: FieldGuide? = null,
    val states: List<StateInfo> = emptyList(),
    // The state on screen (Field Guide, habitat, parks); mainState() is the player's main one.
    val stateCode: String = "",
    val mainCode: String = "",
    // Every state's species, so photos of animals from another state still show.
    val allSpecies: List<Species> = emptyList(),
    // First launch: ask which state the player is in, like the website's sign-up.
    val needsStatePick: Boolean = false,
    // States with a badge saved on this phone; see [unlockedStates].
    val unlocked: Set<String> = emptySet(),
    // "Your states", while it's open.
    val stateTiles: List<StateTile>? = null,
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
)

class GameViewModel(app: Application) : AndroidViewModel(app) {
    private val store = CollectionStore(app.filesDir)
    private val nameQueue = NameQueue(app.filesDir)
    private var names: AnimalNames? = null
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
            val unlocked = withContext(Dispatchers.IO) {
                store.migrate(saved ?: default)
                offlineUnlocked(list)
            }
            withContext(Dispatchers.IO) {
                // Read the starting state's Field Guide here rather than on the main thread.
                list.firstOrNull { it.code == (saved ?: default) }?.fieldGuide
            }
            _state.update {
                it.copy(states = list, needsStatePick = saved == null, sets = sets, unlocked = unlocked, mainCode = saved ?: default,
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
                sendQueuedNames()
            } catch (e: Online.ApiError) {
                // Signed out by the server (401): back to the badges saved on this phone.
                if (!Online.signedIn) _state.update { it.copy(account = null, collection = store.load(it.stateCode)) }
            }
        }
    }

    private suspend fun refreshCollection() {
        if (!Online.signedIn || _state.value.account == null) return
        val c = Online.collection(_state.value.stateCode)
        _state.update { it.copy(collection = c) }
    }

    fun signIn(ident: String, password: String) = account { Online.login(ident.trim(), password) }

    fun signUp(email: String, username: String, password: String, birthYear: Int) =
        account { Online.register(email.trim(), username.trim(), password, _state.value.stateCode, birthYear) }

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
                sendQueuedNames()
            } catch (e: Exception) {
                _state.update { it.copy(accountBusy = false, accountError = e.message ?: "Something went wrong") }
            }
        }
    }

    /** Back to playing offline, with the badges saved on this phone. */
    fun signOut() {
        Online.logout()
        _state.update { it.copy(account = null, collection = store.load(it.stateCode), result = null) }
    }

    /** Delete the account on the server (needs the password), then carry on offline. */
    fun deleteAccount(password: String, done: (String?) -> Unit) {
        viewModelScope.launch {
            val err = runCatching { Online.deleteAccount(password) }.exceptionOrNull()?.let { it.message ?: "Something went wrong" }
            if (err == null) signOut()
            done(err)
        }
    }

    fun setServer(url: String?) {
        Online.setManualUrl(url)
        _state.update { it.copy(server = Online.base) }
        connect()
    }

    fun setAvatar(n: Int) {
        val acct = _state.value.account ?: return
        _state.update { it.copy(account = acct.copy(avatar = n)) }
        viewModelScope.launch { runCatching { Online.setAvatar(n) } }
    }

    /** "Share photos to teach the game" (off by default). Turning it off deletes the server's copies. */
    fun setShareTraining(on: Boolean) {
        val acct = _state.value.account ?: return
        _state.update { it.copy(account = acct.copy(shareTrainingPhotos = on)) }
        viewModelScope.launch {
            runCatching { Online.setShareTraining(on) }.onFailure { e ->
                _state.update { it.copy(account = it.account?.copy(shareTrainingPhotos = !on), error = e.message) }
            }
        }
    }

    /** The bundled name list for "What was it?" (read once). */
    suspend fun animalNames(): AnimalNames? = names ?: withContext(Dispatchers.IO) {
        runCatching {
            AnimalNames.parse(getApplication<Application>().assets.open("animal_names.json").bufferedReader().use { it.readText() })
        }.getOrNull()
    }?.also { names = it }

    /**
     * The player names the animal in a photo that didn't count. Signed in, it goes
     * straight to the server; offline (or if that fails) it waits on the phone.
     */
    fun nameAnimal(entry: AnimalName) {
        val r = _state.value.result ?: return
        viewModelScope.launch {
            val sent = r.captureId?.let { id -> runCatching { Online.nameCapture(id, entry.label) }.getOrNull() }
            val message = sent ?: run {
                val predicted = r.guesses.firstOrNull()?.label
                withContext(Dispatchers.IO) { nameQueue.add(entry.label, predicted, r.state ?: _state.value.stateCode, r.photo) }
                if (Online.signedIn) sendQueuedNames()
                "Thanks! You said it's ${withArticle(entry.name)}. " +
                    if (Online.signedIn) "That helps the game learn." else "It's saved on this phone and helps the game learn once you sign in."
            }
            _state.update { s -> s.copy(result = s.result?.let { if (it.photo === r.photo) it.copy(named = message) else it }) }
        }
    }

    /** Sends names picked offline. Photos go only if the player shares photos to teach the game. */
    private suspend fun sendQueuedNames() {
        val acct = _state.value.account ?: return
        for (p in withContext(Dispatchers.IO) { nameQueue.all() }) {
            try {
                val photo = if (acct.shareTrainingPhotos) withContext(Dispatchers.IO) { nameQueue.photoBytes(p) } else null
                Online.sendNamed(p.label, p.predicted, p.state, photo)
            } catch (e: Online.ApiError) {
                // Offline, or the daily limit: try again later. Anything else can't be fixed by retrying.
                if (e.code == 0 || e.code == 429 || e.code >= 500) return
            }
            withContext(Dispatchers.IO) { nameQueue.remove(p.id) }
        }
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

    /** The player's main state: where photos without a place count, and what friends see first. */
    fun chooseState(code: String) {
        prefs.edit().putString("state", code).apply()
        _state.update { it.copy(needsStatePick = false, result = null, mainCode = code) }
        select(code)
        if (_state.value.account != null) viewModelScope.launch {
            runCatching {
                Online.setState(code)
                // The server may lock the old main state if it has no animals.
                val me = Online.me()
                _state.update { it.copy(account = me) }
                refreshCollection()
            }.onFailure { e -> _state.update { it.copy(error = e.message) } }
        }
    }

    /** Look at another unlocked state's Field Guide, habitat and parks without changing the main one. */
    fun viewState(code: String) {
        _state.update { it.copy(result = null) }
        select(code)
        viewModelScope.launch { runCatching { refreshCollection() } }
    }

    /** Fills "Your states": each unlocked state with how much of its list is captured. */
    fun loadStateTiles() {
        viewModelScope.launch {
            val ui = _state.value
            val tiles = if (ui.account != null) {
                runCatching { Online.myStates() }.getOrNull()?.also { tiles ->
                    _state.update { it.copy(account = it.account?.copy(unlockedStates = tiles.map { t -> t.code })) }
                }
            } else null
            _state.update { it.copy(stateTiles = tiles ?: withContext(Dispatchers.IO) { offlineTiles() }) }
        }
    }

    fun closeStateTiles() = _state.update { it.copy(stateTiles = null) }

    private fun offlineTiles(): List<StateTile> {
        val ui = _state.value
        val unlocked = ui.unlockedStates()
        return ui.states.filter { it.code in unlocked }.map { st ->
            val slugs = st.species.map { it.slug }.toSet()
            StateTile(st.code, st.name, collectionOf(st.code).keys.count { it in slugs }, slugs.size, st.code == ui.mainState())
        }
    }

    /** States with a badge saved on this phone. */
    private fun offlineUnlocked(states: List<StateInfo>): Set<String> {
        val unlocked = states.filter { st ->
            val slugs = st.species.map { it.slug }.toSet()
            store.load(st.code).keys.any { it in slugs }
        }.map { it.code }.toSet()
        prefs.edit().remove("unlocked").apply()
        return unlocked
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
            } catch (e: OutOfMemoryError) {
                _state.update { it.copy(busy = false, error = "That photo is too big to open. Try cropping less or another photo.") }
            }
        }
    }

    /** Signed in: the server identifies the photo and keeps the badge, as on the website. */
    private suspend fun captureOnline(uri: Uri, info: ModelInfo, location: Pair<Double, Double>?,
                                      savePlace: Boolean, crop: CropBox?): CaptureResult {
        val bitmap = withContext(Dispatchers.IO) { ImageLoader.load(getApplication(), uri, minShortSide = if (crop == null) 1200 else 1800).cropTo(crop) }
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
            canChangeState = if (prev != null) prev.canChangeState else r.optBoolean("can_change_state"),
        )
    }

    // Same rules as the backend's POST /captures, including counting the photo in
    // the state it was taken in (from its EXIF, or [location] if it's recent).
    private suspend fun classify(uri: Uri, mainInfo: ModelInfo, location: Pair<Double, Double>?,
                                 crop: CropBox? = null, chosenState: String? = null): CaptureResult {
        val app = getApplication<Application>()
        val ui = _state.value
        val meta = readPhotoMeta(app, uri)
        val place = if (chosenState != null) null else meta?.latitude?.let { lat -> meta.longitude?.let { lat to it } }
            ?: location?.takeIf { meta?.takenAt == null || java.time.Duration.between(meta.takenAt, java.time.LocalDateTime.now()).toHours() < 3 }
        // The player said where it was taken ("Taken in another state?"), or its place says.
        val here = ui.states.firstOrNull { it.code == chosenState }
            ?: place?.let { (lat, lon) -> States.stateAt(ui.states, lat, lon) }
        // Without a place, the main state (as on the website), whichever state is on screen.
        val code = here?.code ?: ui.mainState()
        val list = here?.species ?: ui.states.firstOrNull { it.code == code }?.species
        val info = if (code == ui.stateCode || list == null) mainInfo else (model ?: mainInfo).withSpecies(list)
        // Cropping keeps a part, so decode bigger to keep enough pixels for the model.
        val bitmap = ImageLoader.load(app, uri, minShortSide = if (crop == null) info.resize else info.resize * 3).cropTo(crop)
        // Five guesses: three are shown, all five are offered if the player corrects the model.
        // Only the chosen state's animals count, as on the website. Pets and pests, the
        // state's animals that aren't in its Field Guide yet, and people are recognised
        // too, so a photo of one isn't squeezed onto a look-alike, but none earns a badge.
        val bySlug = info.species.associateBy { it.slug }
        val pets = info.household.filter { it.slug !in bySlug }.associateBy { it.slug }
        val unlisted = info.extras[code].orEmpty() - bySlug.keys - pets.keys
        val allowed = bySlug.keys + pets.keys + unlisted + listOfNotNull(info.personLabel) + info.otherLabel
        val preds = classifier(info).predict(ImageLoader.toRgb(bitmap), k = 5, allowed = allowed)
        val top = preds.first()
        val species = bySlug[top.label]
        val sure = top.probability >= info.matchThreshold
        val matched = species != null && sure

        // A state unlocks with its first captured animal.
        val newlyUnlocked = matched && code !in ui.unlockedStates()
        if (newlyUnlocked) _state.update { it.copy(unlocked = it.unlocked + code) }
        var newBadge = false
        if (matched) {
            val thumb = ImageLoader.thumbnail(bitmap, 512)
            val (updated, isNew) = withContext(Dispatchers.IO) {
                store.addCatch(code, collectionOf(code), species!!.slug, thumb)
            }
            newBadge = isNew
            if (code == _state.value.stateCode) _state.update { it.copy(collection = updated) }
        }
        val stateName = ui.states.firstOrNull { it.code == code }?.name ?: regionName()
        var message = when {
            matched && newBadge -> "You captured a ${species!!.commonName}! New badge unlocked."
            matched -> "Another ${species!!.commonName} for your collection."
            species != null -> "Might be a ${species.commonName}, but we're not sure. Try a clearer photo!"
            sure && top.label in pets -> pets.getValue(top.label).message()
            sure && top.label == info.personLabel -> "That looks like a person! Only wild animals go in the Field Guide."
            sure && top.label in unlisted ->
                "That looks like a wild animal that isn't in the $stateName collection yet. It's coming soon!"
            else -> "We couldn't match this to any animal in the $stateName collection."
        }
        if (newlyUnlocked) message = "📍 You unlocked $stateName! $message"
        else if (code != ui.mainState() && matched) message += " It counts in your $stateName Field Guide."
        if (place != null && here == null) {
            message = "This photo was taken outside the states in the game, so it was checked against $stateName. $message"
        }
        return CaptureResult(
            photo = ImageLoader.thumbnail(bitmap, 1024),
            matched = matched,
            species = if (matched) species else null,
            confidence = top.probability,
            newBadge = newBadge,
            message = message,
            guesses = preds.take(3).map {
                RankedGuess(it.label, bySlug[it.label]?.commonName ?: pets[it.label]?.commonName ?: "Something else",
                    it.probability)
            },
            choices = preds.mapNotNull { p -> bySlug[p.label]?.let { RankedGuess(p.label, it.commonName, p.probability) } },
            state = code,
            unlockedState = code.takeIf { newlyUnlocked },
            // The phone's location only guesses where a saved picture was taken.
            canChangeState = here == null || chosenState != null || meta?.latitude == null,
            uri = uri,
            crop = crop,
        )
    }

    /** "Taken in another state?": identify the photo on the result card again against [code]'s animals. */
    fun changeCaptureState(code: String) {
        val r = _state.value.result ?: return
        val info = _state.value.info ?: return
        _state.update { it.copy(busy = true, error = null) }
        viewModelScope.launch {
            try {
                val id = r.captureId
                val result = if (id != null) {
                    onlineResult(Online.captureState(id, code), r.photo, info).also { res ->
                        res.unlockedState?.let { u ->
                            _state.update { it.copy(account = it.account?.let { a -> a.copy(unlockedStates = (a.unlockedStates + u).distinct()) }) }
                        }
                        runCatching { refreshCollection() }
                    }
                } else {
                    val uri = r.uri ?: run { _state.update { it.copy(busy = false) }; return@launch }
                    // Take back the badge it earned where it was counted before.
                    val old = r.state ?: _state.value.stateCode
                    if (r.matched && r.species != null) withContext(Dispatchers.IO) {
                        val updated = store.removeCatch(old, collectionOf(old), r.species.slug)
                        if (old == _state.value.stateCode) _state.update { it.copy(collection = updated) }
                    }
                    withContext(Dispatchers.Default) { classify(uri, info, null, r.crop, chosenState = code) }
                }
                _state.update { it.copy(busy = false, result = result) }
            } catch (e: Exception) {
                _state.update { it.copy(busy = false, error = e.message) }
            }
        }
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
            // Deleting the last animal from a state locks it again.
            val unlocked = withContext(Dispatchers.IO) { offlineUnlocked(_state.value.states) }
            _state.update { it.copy(unlocked = unlocked) }
        }
    }

    /** The phone's badges for a state: the ones on screen for the state on screen, else read from storage. */
    private fun collectionOf(code: String) =
        if (code == _state.value.stateCode) _state.value.collection else store.load(code)

    private fun regionName() = _state.value.fieldGuide?.region ?: "state"

    fun dismissResult() = _state.update { it.copy(result = null, error = null) }

    override fun onCleared() {
        classifier?.close()
    }
}
