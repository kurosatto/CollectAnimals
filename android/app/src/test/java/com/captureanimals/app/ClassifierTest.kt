package com.captureanimals.app

import org.junit.Assume.assumeTrue
import org.junit.Assert.assertTrue
import org.junit.Test
import java.io.File

/**
 * Runs the exported model (desktop ONNX Runtime) on downloaded photos, through the
 * same Kotlin preprocessing the app uses. Skipped unless ml/export_onnx.py has
 * been run and data/images exists (photos aren't kept in the repo).
 */
class ClassifierTest {

    // javax.imageio/java.awt exist at test runtime but aren't on the Android compile classpath.
    private fun readJpeg(f: File): Preprocess.Rgb {
        val img = Class.forName("javax.imageio.ImageIO").getMethod("read", File::class.java).invoke(null, f)
        val cls = img.javaClass
        val w = cls.getMethod("getWidth").invoke(img) as Int
        val h = cls.getMethod("getHeight").invoke(img) as Int
        val getRgb = cls.getMethod("getRGB", Int::class.java, Int::class.java, Int::class.java, Int::class.java,
            IntArray::class.java, Int::class.java, Int::class.java)
        return Preprocess.Rgb(w, h, getRgb.invoke(img, 0, 0, w, h, null, 0, w) as IntArray)
    }

    @Test
    fun classifiesDownloadedPhotos() {
        val model = File("src/main/assets/model.onnx")
        val data = File("../../data/images")
        assumeTrue(model.exists() && data.isDirectory)
        val info = ModelInfo.parse(File("src/main/assets/model.json").readText())
        val photos = data.listFiles()!!.filter { it.isDirectory }.sortedBy { it.name }
            .flatMap { dir -> dir.listFiles()!!.filter { it.extension == "jpg" }.sortedBy { it.name }.take(1) }

        Classifier(model.readBytes(), info).use { clf ->
            var correct = 0
            for (f in photos) {
                val top = clf.predict(readJpeg(f), k = 1).first()
                if (top.label == f.parentFile.name) correct++
            }
            val acc = correct / photos.size.toDouble()
            println("top-1 on ${photos.size} photos (one per class): ${"%.3f".format(acc)}")
            // Mostly training photos, so this is a wiring check, not an accuracy estimate.
            assertTrue("accuracy $acc", acc > 0.8)
        }
    }
}
