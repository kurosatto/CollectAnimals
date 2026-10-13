package com.captureanimals.app

import org.junit.Assert.assertTrue
import org.junit.Test

/** Kotlin resize + crop vs PIL/torchvision (references from tools/make_preprocess_reference.py). */
class PreprocessTest {

    private fun pattern(w: Int, h: Int): Preprocess.Rgb {
        val px = IntArray(w * h)
        for (y in 0 until h) for (x in 0 until w) {
            val r = (x * 7 + y * 3) % 256
            val g = ((x.toLong() * x / 13 + y) % 256).toInt()
            val b = ((x / 4) xor (y / 4)) % 256
            px[y * w + x] = (0xFF shl 24) or (r shl 16) or (g shl 8) or b
        }
        return Preprocess.Rgb(w, h, px)
    }

    private fun check(w: Int, h: Int) {
        val expected = javaClass.getResourceAsStream("/preprocess_${w}x$h.rgb")!!.readBytes()
        val crop = Preprocess.centerCrop(Preprocess.resizeShorterSide(pattern(w, h), 256), 224)
        var maxDiff = 0
        var exact = 0
        for (i in 0 until 224 * 224) {
            val p = crop.pixels[i]
            val got = intArrayOf((p shr 16) and 0xFF, (p shr 8) and 0xFF, p and 0xFF)
            for (c in 0..2) {
                val d = kotlin.math.abs(got[c] - (expected[i * 3 + c].toInt() and 0xFF))
                maxDiff = maxOf(maxDiff, d)
                if (d == 0) exact++
            }
        }
        val exactFrac = exact / (224.0 * 224 * 3)
        println("${w}x$h: max diff $maxDiff, exact ${"%.4f".format(exactFrac)}")
        // PIL uses fixed-point math; allow off-by-one rounding, nothing more.
        assertTrue("${w}x$h max diff $maxDiff", maxDiff <= 1)
        assertTrue("${w}x$h exact $exactFrac", exactFrac > 0.95)
    }

    @Test fun upscale() = check(200, 150)
    @Test fun mildDownscale() = check(640, 480)
    @Test fun phonePhotoDownscale() = check(3000, 2000)
    @Test fun portrait() = check(1080, 1920)
}
