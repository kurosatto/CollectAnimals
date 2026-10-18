package com.captureanimals.app

import android.content.Context
import android.graphics.BitmapFactory
import androidx.compose.foundation.Image
import androidx.compose.runtime.Composable
import androidx.compose.runtime.remember
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.FilterQuality
import androidx.compose.ui.graphics.asImageBitmap
import androidx.compose.ui.layout.ContentScale
import androidx.compose.ui.platform.LocalContext

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
