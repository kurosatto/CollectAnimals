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
                       Pokedex.parse(text("details.csv"), text("ranges.json"), text("california_outline.json")),
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
        val preds = classifier(info).predict(ImageLoader.toRgb(bitmap), k = 3)
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
            matched && newBadge -> "You caught a ${species!!.commonName}! New badge unlocked."
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
            guesses = preds.map {
                RankedGuess(it.label, bySlug[it.label]?.commonName ?: "Something else", it.probability)
            },
        )
    }

    fun dismissResult() = _state.update { it.copy(result = null, error = null) }

    override fun onCleared() {
        classifier?.close()
    }
}
