package com.collectanimals.app

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
) {
    companion object {
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
            )
        }
    }
}

data class Prediction(val label: String, val probability: Float)

/** Runs the exported model with ONNX Runtime. The model already ends in softmax. */
class Classifier(modelBytes: ByteArray, val info: ModelInfo) : AutoCloseable {
    private val env = OrtEnvironment.getEnvironment()
    private val session: OrtSession = env.createSession(modelBytes, OrtSession.SessionOptions())

    fun predict(img: Preprocess.Rgb, k: Int = 3): List<Prediction> {
        val input = Preprocess.toTensor(img, info)
        val shape = longArrayOf(1, 3, info.imgSize.toLong(), info.imgSize.toLong())
        val probs = OnnxTensor.createTensor(env, FloatBuffer.wrap(input), shape).use { tensor ->
            session.run(mapOf("image" to tensor)).use { result ->
                @Suppress("UNCHECKED_CAST")
                (result[0].value as Array<FloatArray>)[0]
            }
        }
        return probs.indices.sortedByDescending { probs[it] }.take(k)
            .map { Prediction(info.classes[it], probs[it]) }
    }

    override fun close() = session.close()
}
