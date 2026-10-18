package com.captureanimals.app

import android.content.Context
import android.graphics.BitmapFactory
import androidx.compose.animation.core.Animatable
import androidx.compose.animation.core.LinearEasing
import androidx.compose.animation.core.tween
import androidx.compose.foundation.Image
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.remember
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.drawWithContent
import androidx.compose.ui.graphics.drawscope.clipRect
import androidx.compose.ui.graphics.graphicsLayer
import androidx.compose.ui.graphics.FilterQuality
import androidx.compose.ui.graphics.asImageBitmap
import androidx.compose.ui.layout.ContentScale
import androidx.compose.ui.platform.LocalContext
import kotlinx.coroutines.delay

/**
 * The species' 40×40 pixel art from species/sprites (packaged as assets): in colour once
 * caught, a silhouette until then. Scaled up without smoothing so the pixels stay crisp.
 * Animals without art yet (the newer states) get the "?" egg placeholder.
 */
@Composable
fun PixelSprite(slug: String, caught: Boolean, modifier: Modifier = Modifier) {
    val context = LocalContext.current
    val name = if (caught) "sprites/$slug.png" else "sprites/${slug}_silhouette.png"
    val bitmap = remember(name) {
        runCatching { context.assets.open(spriteAsset(name, spriteFiles(context)))
            .use { BitmapFactory.decodeStream(it) } }.getOrNull()
    } ?: return
    Image(bitmap.asImageBitmap(), contentDescription = null, modifier = modifier,
        contentScale = ContentScale.Fit, filterQuality = FilterQuality.None)
}

/** A 16x16 pixel-art tab icon, scaled up without smoothing and left in its own colors. */
@Composable
fun TabIcon(name: String, modifier: Modifier = Modifier) {
    val context = LocalContext.current
    val bitmap = remember(name) {
        runCatching { context.assets.open("sprites/$name.png").use { BitmapFactory.decodeStream(it) } }.getOrNull()
    } ?: return
    Image(bitmap.asImageBitmap(), contentDescription = null, modifier = modifier,
        contentScale = ContentScale.Fit, filterQuality = FilterQuality.None)
}

private var spriteFiles: Set<String>? = null

/** The files in the sprites/ assets, listed once. */
fun spriteFiles(context: Context): Set<String> =
    spriteFiles ?: context.assets.list("sprites").orEmpty().toSet().also { spriteFiles = it }

/**
 * The asset path to load for sprites/<name>.png: itself, or the placeholder egg
 * (placeholder.png / placeholder_silhouette.png) when that animal has no art yet.
 */
fun spriteAsset(path: String, files: Set<String>): String {
    val file = path.removePrefix("sprites/")
    if (file in files || "/" in file) return path
    return if (file.endsWith("_silhouette.png")) "sprites/placeholder_silhouette.png" else "sprites/placeholder.png"
}

/**
 * A new animal in the Field Guide: its silhouette, a little shake, then the colour pixel
 * art wipes in from the bottom a few pixel rows at a time, as on the website.
 */
@Composable
fun CaptureReveal(slug: String, modifier: Modifier = Modifier) {
    val shake = remember(slug) { Animatable(0f) }
    val shown = remember(slug) { Animatable(0f) }
    LaunchedEffect(slug) {
        delay(100)
        shake.animateTo(1f, tween(500, easing = LinearEasing))
        shown.animateTo(1f, tween(1200, delayMillis = 100, easing = LinearEasing))
    }
    // 20 steps, like the website's steps(20): whole rows of the 40x40 sprite at a time.
    val visible = kotlin.math.floor(shown.value * 20f) / 20f
    Box(modifier) {
        PixelSprite(slug, caught = false, Modifier.fillMaxSize()
            .graphicsLayer { rotationZ = 6f * kotlin.math.sin(shake.value * 2f * Math.PI.toFloat()) })
        PixelSprite(slug, caught = true, Modifier.fillMaxSize().drawWithContent {
            clipRect(top = size.height * (1f - visible)) { this@drawWithContent.drawContent() }
        })
    }
}
