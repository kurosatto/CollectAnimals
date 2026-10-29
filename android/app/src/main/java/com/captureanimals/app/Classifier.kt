package com.captureanimals.app

import ai.onnxruntime.OnnxTensor
import ai.onnxruntime.OrtEnvironment
import ai.onnxruntime.OrtSession
import org.json.JSONObject
import java.nio.FloatBuffer

data class Species(
    val slug: String,
    val commonName: String,
    val scientificName: String,
    val category: String,
    val rarity: String,
)

/** A pet or pest the model knows (species/household.csv): named, but not a Field Guide animal. */
data class HouseholdAnimal(val slug: String, val commonName: String, val kind: String, val note: String) {
    /** What the capture screen says, as the backend's household.message(). */
    fun message(): String {
        val name = commonName.split(" ").joinToString(" ") { w ->
            if (w.lowercase() in setOf("european", "german", "american")) w else w.lowercase()
        }
        return if (kind == "pet") "That's a $name! Pets aren't wild animals, so they don't go in the Field Guide. $note"
        else "That's a $name. It's a pest, not one of the wild animals in the Field Guide. $note"
    }
}

/** Contents of assets/model.json, written by ml/export_onnx.py. */
class ModelInfo(
    val classes: List<String>,
    val imgSize: Int,
    val resize: Int,
    val mean: FloatArray,
    val std: FloatArray,
    val matchThreshold: Float,
    val otherLabel: String,
    val species: List<Species>,
    val household: List<HouseholdAnimal> = emptyList(),
    // Each state's animals the model knows that aren't in its Field Guide yet.
    val extras: Map<String, Set<String>> = emptyMap(),
    val personLabel: String? = null,
) {
    /** Dex order, as on the website: common to legendary, then by kind, then list order. */
    val dexOrder: List<Species> by lazy {
        species.withIndex().sortedWith(compareBy(
            { RARITY_ORDER.indexOf(it.value.rarity).let { r -> if (r < 0) RARITY_ORDER.size else r } },
            { CATEGORY_ORDER.indexOf(it.value.category).let { c -> if (c < 0) CATEGORY_ORDER.size else c } },
            { it.index },
        )).map { it.value }
    }
    private val dexNumbers by lazy { dexOrder.withIndex().associate { it.value.slug to it.index + 1 } }

    /** The species' display number (#001…), following [dexOrder]. */
    fun dexNumber(slug: String): Int = dexNumbers[slug] ?: 0

    /** The same model with one state's species list (its Field Guide order and numbers). */
    fun withSpecies(list: List<Species>) =
        ModelInfo(classes, imgSize, resize, mean, std, matchThreshold, otherLabel, list, household, extras, personLabel)

    companion object {
        val RARITY_ORDER = listOf("common", "uncommon", "rare", "legendary")
        val CATEGORY_ORDER = listOf("mammal", "bird", "reptile", "amphibian", "invertebrate", "marine")

        fun parse(json: String): ModelInfo {
            val o = JSONObject(json)
            fun floats(key: String) = o.getJSONArray(key).let { a -> FloatArray(a.length()) { a.getDouble(it).toFloat() } }
            val cls = o.getJSONArray("classes")
            val sp = o.getJSONArray("species")
            return ModelInfo(
                classes = List(cls.length()) { cls.getString(it) },
                imgSize = o.getInt("img_size"),
                resize = o.getInt("resize"),
                mean = floats("mean"),
                std = floats("std"),
                matchThreshold = o.getDouble("match_threshold").toFloat(),
                otherLabel = o.getString("other_label"),
                species = List(sp.length()) {
                    val s = sp.getJSONObject(it)
                    Species(s.getString("slug"), s.getString("common_name"), s.getString("scientific_name"),
                        s.getString("category"), s.getString("rarity"))
                },
                household = o.optJSONArray("household")?.let { a ->
                    List(a.length()) { i ->
                        a.getJSONObject(i).let { h ->
                            HouseholdAnimal(h.getString("slug"), h.getString("common_name"), h.getString("kind"),
                                h.optString("note"))
                        }
                    }
                }.orEmpty(),
                extras = o.optJSONObject("extras")?.let { e ->
                    e.keys().asSequence().associateWith { k ->
                        e.getJSONArray(k).let { a -> List(a.length()) { a.getString(it) }.toSet() }
                    }
                }.orEmpty(),
                personLabel = o.optString("person_label").ifEmpty { null },
            )
        }
    }
}

data class Prediction(val label: String, val probability: Float) {
    companion object {
        /**
         * Keep only the allowed labels, rescaled so they sum to 1, like the backend's
         * restrict(): a capture only counts for the player's state.
         */
        fun restrict(preds: List<Prediction>, allowed: Set<String>, otherLabel: String): List<Prediction> {
            val kept = preds.filter { it.label in allowed }
            val total = kept.sumOf { it.probability.toDouble() }
            if (kept.isEmpty() || total <= 0) return listOf(Prediction(otherLabel, 1f))
            return kept.map { Prediction(it.label, (it.probability / total).toFloat()) }
        }
    }
}

/** Runs the exported model with ONNX Runtime. The model already ends in softmax. */
class Classifier(modelBytes: ByteArray, val info: ModelInfo) : AutoCloseable {
    private val env = OrtEnvironment.getEnvironment()
    private val session: OrtSession = env.createSession(modelBytes, OrtSession.SessionOptions())

    /** Top [k] guesses; with [allowed], only those labels, rescaled (see [Prediction.restrict]). */
    fun predict(img: Preprocess.Rgb, k: Int = 3, allowed: Set<String>? = null): List<Prediction> {
        val input = Preprocess.toTensor(img, info)
        val shape = longArrayOf(1, 3, info.imgSize.toLong(), info.imgSize.toLong())
        val probs = OnnxTensor.createTensor(env, FloatBuffer.wrap(input), shape).use { tensor ->
            session.run(mapOf("image" to tensor)).use { result ->
                @Suppress("UNCHECKED_CAST")
                (result[0].value as Array<FloatArray>)[0]
            }
        }
        val all = probs.indices.sortedByDescending { probs[it] }.map { Prediction(info.classes[it], probs[it]) }
        return (if (allowed == null) all else Prediction.restrict(all, allowed, info.otherLabel)).take(k)
    }

    override fun close() = session.close()
}
