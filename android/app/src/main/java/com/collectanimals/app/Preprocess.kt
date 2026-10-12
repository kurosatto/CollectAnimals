package com.collectanimals.app

import kotlin.math.abs
import kotlin.math.ceil
import kotlin.math.floor
import kotlin.math.max
import kotlin.math.min

/**
 * Image preprocessing that mirrors the training/eval pipeline in ml/train.py:
 *   Resize(shorter side = resize) -> CenterCrop(size) -> ToTensor -> Normalize(mean, std)
 *
 * Resizing follows PIL's bilinear filter (a triangle filter whose support widens
 * when shrinking), so a 4000 px phone photo is averaged down rather than
 * point-sampled. Pure Kotlin on ARGB int arrays, so it runs in JVM unit tests.
 */
object Preprocess {

    class Rgb(val width: Int, val height: Int, val pixels: IntArray)

    fun toTensor(img: Rgb, info: ModelInfo): FloatArray {
        val resized = resizeShorterSide(img, info.resize)
        val cropped = centerCrop(resized, info.imgSize)
        return normalize(cropped, info.mean, info.std)
    }

    fun resizeShorterSide(img: Rgb, target: Int): Rgb {
        // torchvision: the shorter side becomes `target`, the longer keeps the aspect ratio (truncated).
        val (w, h) = if (img.width <= img.height) {
            target to (target.toLong() * img.height / img.width).toInt()
        } else {
            (target.toLong() * img.width / img.height).toInt() to target
        }
        return resize(img, w, h)
    }

    fun centerCrop(img: Rgb, size: Int): Rgb {
        // Python round() is half-to-even, as torchvision uses for the crop offset.
        val left = Math.rint((img.width - size) / 2.0).toInt()
        val top = Math.rint((img.height - size) / 2.0).toInt()
        val out = IntArray(size * size)
        for (y in 0 until size) {
            System.arraycopy(img.pixels, (top + y) * img.width + left, out, y * size, size)
        }
        return Rgb(size, size, out)
    }

    fun normalize(img: Rgb, mean: FloatArray, std: FloatArray): FloatArray {
        val n = img.width * img.height
        val out = FloatArray(3 * n)
        for (i in 0 until n) {
            val p = img.pixels[i]
            out[i] = (((p shr 16) and 0xFF) / 255f - mean[0]) / std[0]
            out[n + i] = (((p shr 8) and 0xFF) / 255f - mean[1]) / std[1]
            out[2 * n + i] = ((p and 0xFF) / 255f - mean[2]) / std[2]
        }
        return out
    }

    /** Separable bilinear resample, horizontal pass then vertical (as PIL does), 8-bit between passes. */
    fun resize(img: Rgb, outW: Int, outH: Int): Rgb {
        val horiz = resamplePass(img.pixels, img.width, img.height, outW, horizontal = true)
        val vert = resamplePass(horiz, outW, img.height, outH, horizontal = false)
        return Rgb(outW, outH, vert)
    }

    private class Coeffs(val start: IntArray, val count: IntArray, val weights: Array<FloatArray>)

    private fun coefficients(inSize: Int, outSize: Int): Coeffs {
        val scale = inSize.toDouble() / outSize
        val filterScale = max(scale, 1.0)
        val support = 1.0 * filterScale
        val start = IntArray(outSize)
        val count = IntArray(outSize)
        val weights = Array(outSize) { FloatArray(0) }
        for (i in 0 until outSize) {
            val center = (i + 0.5) * scale
            val lo = max(0, floor(center - support).toInt())
            val hi = min(inSize, ceil(center + support).toInt())
            val w = DoubleArray(hi - lo)
            var total = 0.0
            for (j in lo until hi) {
                val t = abs((j - center + 0.5) / filterScale)
                val v = if (t < 1.0) 1.0 - t else 0.0
                w[j - lo] = v
                total += v
            }
            start[i] = lo
            count[i] = hi - lo
            weights[i] = FloatArray(w.size) { if (total > 0) (w[it] / total).toFloat() else 0f }
        }
        return Coeffs(start, count, weights)
    }

    private fun resamplePass(src: IntArray, w: Int, h: Int, outSize: Int, horizontal: Boolean): IntArray {
        val inSize = if (horizontal) w else h
        val c = coefficients(inSize, outSize)
        val outW = if (horizontal) outSize else w
        val outH = if (horizontal) h else outSize
        val out = IntArray(outW * outH)
        for (y in 0 until outH) {
            for (x in 0 until outW) {
                val i = if (horizontal) x else y
                var r = 0f
                var g = 0f
                var b = 0f
                val wts = c.weights[i]
                for (k in 0 until c.count[i]) {
                    val j = c.start[i] + k
                    val p = if (horizontal) src[y * w + j] else src[j * w + x]
                    val wk = wts[k]
                    r += ((p shr 16) and 0xFF) * wk
                    g += ((p shr 8) and 0xFF) * wk
                    b += (p and 0xFF) * wk
                }
                out[y * outW + x] = (0xFF shl 24) or (clamp8(r) shl 16) or (clamp8(g) shl 8) or clamp8(b)
            }
        }
        return out
    }

    private fun clamp8(v: Float): Int = min(255, max(0, (v + 0.5f).toInt()))
}
