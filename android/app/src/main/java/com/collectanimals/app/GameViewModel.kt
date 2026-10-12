package com.collectanimals.app

import android.app.Application
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
)

data class UiState(
    val info: ModelInfo? = null,
    val pokedex: Pokedex? = null,
    val collection: Map<String, Badge> = emptyMap(),
    val busy: Boolean = false,
    val result: CaptureResult? = null,
    val error: String? = null,
)

class GameViewModel(app: Application) : AndroidViewModel(app) {
    private val store = CollectionStore(app.filesDir)
    private val _state = MutableStateFlow(UiState())
    val state: StateFlow<UiState> = _state

    private var classifier: Classifier? = null
    private val classifierLock = Mutex()

    init {
        viewModelScope.launch {
            val assets = getApplication<Application>().assets
            fun text(name: String) = assets.open(name).bufferedReader().use { it.readText() }
            val loaded = withContext(Dispatchers.IO) {
                Triple(ModelInfo.parse(text("model.json")),
                       Pokedex.parse(text("details.csv"), text("ranges.json"), text("california_outline.json"),
                           runCatching { text("hotspots.json") }.getOrNull()),
                       store.load())
            }
            _state.update { it.copy(info = loaded.first, pokedex = loaded.second, collection = loaded.third) }
        }
    }

    private suspend fun classifier(info: ModelInfo): Classifier = classifierLock.withLock {
        classifier ?: withContext(Dispatchers.IO) {
            val bytes = getApplication<Application>().assets.open("model.onnx").use { it.readBytes() }
            Classifier(bytes, info)
        }.also { classifier = it }
    }

    fun capture(uri: Uri) {
        val info = _state.value.info ?: return
        _state.update { it.copy(busy = true, error = null) }
        viewModelScope.launch {
            try {
                val result = withContext(Dispatchers.Default) { classify(uri, info) }
                _state.update { it.copy(busy = false, result = result) }
            } catch (e: Exception) {
                _state.update { it.copy(busy = false, error = "Couldn't read that photo (${e.message})") }
            }
        }
    }

    // Same rules as the backend's POST /captures.
    private suspend fun classify(uri: Uri, info: ModelInfo): CaptureResult {
        val app = getApplication<Application>()
        val bitmap = ImageLoader.load(app, uri, minShortSide = info.resize)
        // Five guesses: three are shown, all five are offered if the player corrects the model.
        val preds = classifier(info).predict(ImageLoader.toRgb(bitmap), k = 5)
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
            else -> "We couldn't match this to any animal in the California collection."
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

    fun dismissResult() = _state.update { it.copy(result = null, error = null) }

    override fun onCleared() {
        classifier?.close()
    }
}
