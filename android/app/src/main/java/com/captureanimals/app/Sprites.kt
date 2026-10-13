package com.captureanimals.app

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
 * The species' 32×32 pixel art from species/sprites (packaged as assets): in colour once
 * caught, a silhouette until then. Scaled up without smoothing so the pixels stay crisp.
 */
@Composable
fun PixelSprite(slug: String, caught: Boolean, modifier: Modifier = Modifier) {
    val context = LocalContext.current
    val name = if (caught) "sprites/$slug.png" else "sprites/${slug}_silhouette.png"
    val bitmap = remember(name) {
        runCatching { context.assets.open(name).use { BitmapFactory.decodeStream(it) } }.getOrNull()
    } ?: return
    Image(bitmap.asImageBitmap(), contentDescription = null, modifier = modifier,
        contentScale = ContentScale.Fit, filterQuality = FilterQuality.None)
}
