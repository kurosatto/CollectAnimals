package com.captureanimals.app

import android.graphics.Bitmap
import android.net.Uri
import androidx.compose.foundation.Canvas
import androidx.compose.foundation.Image
import androidx.compose.foundation.gestures.detectDragGestures
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.aspectRatio
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.heightIn
import androidx.compose.foundation.layout.padding
import androidx.compose.material3.Button
import androidx.compose.material3.Card
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.FilterChip
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.rememberUpdatedState
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.geometry.Size
import androidx.compose.ui.graphics.ClipOp
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.asImageBitmap
import androidx.compose.ui.graphics.drawscope.Stroke
import androidx.compose.ui.graphics.drawscope.clipRect
import androidx.compose.ui.input.pointer.pointerInput
import androidx.compose.ui.layout.onSizeChanged
import androidx.compose.ui.layout.ContentScale
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.unit.dp
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import kotlin.math.abs
import kotlin.math.max
import kotlin.math.min
import kotlin.math.roundToInt

/** The part of the upright photo the player keeps, as fractions of its width and height. */
data class CropBox(val x: Float = 0f, val y: Float = 0f, val w: Float = 1f, val h: Float = 1f) {
    val isWhole get() = x <= 0.002f && y <= 0.002f && w >= 0.996f && h >= 0.996f

    /** The box in pixels of a [width] x [height] image: left, top, width, height. */
    fun pixels(width: Int, height: Int): IntArray {
        val left = (x * width).roundToInt().coerceIn(0, width - 1)
        val top = (y * height).roundToInt().coerceIn(0, height - 1)
        val right = ((x + w) * width).roundToInt().coerceIn(left + 1, width)
        val bottom = ((y + h) * height).roundToInt().coerceIn(top + 1, height)
        return intArrayOf(left, top, right - left, bottom - top)
    }

    companion object {
        /** The biggest square inside [box] of a [width] x [height] view, centred on it. */
        fun square(box: CropBox, width: Float, height: Float): CropBox {
            val side = min(box.w * width, box.h * height)
            return CropBox(box.x + (box.w * width - side) / 2 / width, box.y + (box.h * height - side) / 2 / height,
                side / width, side / height)
        }

        /** [start] slid by ([dx], [dy]) view pixels, kept inside the photo. */
        fun moved(start: CropBox, dx: Float, dy: Float, width: Float, height: Float) = start.copy(
            x = (start.x + dx / width).coerceIn(0f, 1f - start.w),
            y = (start.y + dy / height).coerceIn(0f, 1f - start.h))

        /**
         * [start] with one corner dragged to ([px], [py]) in view pixels; the opposite
         * corner stays put. [east]/[south] say which corner. At least [minSide] pixels.
         */
        fun resized(start: CropBox, east: Boolean, south: Boolean, px: Float, py: Float,
                    width: Float, height: Float, square: Boolean, minSide: Float): CropBox {
            val dx = if (east) 1f else -1f
            val dy = if (south) 1f else -1f
            val ax = (if (east) start.x else start.x + start.w) * width
            val ay = (if (south) start.y else start.y + start.h) * height
            val roomX = if (east) width - ax else ax
            val roomY = if (south) height - ay else ay
            var w = ((px - ax) * dx).coerceIn(min(minSide, roomX), roomX)
            var h = ((py - ay) * dy).coerceIn(min(minSide, roomY), roomY)
            if (square) { w = min(max(w, h), min(roomX, roomY)); h = w }
            return CropBox((if (east) ax else ax - w) / width, (if (south) ay else ay - h) / height, w / width, h / height)
        }
    }
}

/** Crops an upright bitmap to [box]; the whole photo comes back unchanged. */
fun Bitmap.cropTo(box: CropBox?): Bitmap {
    if (box == null || box.isWhole) return this
    val (left, top, w, h) = box.pixels(width, height).toList()
    return Bitmap.createBitmap(this, left, top, w, h)
}

/**
 * Before identifying, the player drags a box (or its corners) over the photo to crop
 * to the animal: free-form or square. The crop is applied to the full photo later,
 * and the photo's own time and place still count.
 */
@Composable
fun CropPanel(uri: Uri, onIdentify: (CropBox?) -> Unit, onCancel: () -> Unit) {
    val context = LocalContext.current
    var preview by remember(uri) { mutableStateOf<Bitmap?>(null) }
    var failed by remember(uri) { mutableStateOf(false) }
    var box by remember(uri) { mutableStateOf(CropBox()) }
    var square by remember(uri) { mutableStateOf(false) }
    var viewSize by remember { mutableStateOf(Size.Zero) }
    LaunchedEffect(uri) {
        preview = runCatching { withContext(Dispatchers.IO) { ImageLoader.load(context, uri, minShortSide = 720) } }
            .onFailure { failed = true }.getOrNull()
    }
    Card(Modifier.fillMaxWidth()) {
        Column(Modifier.padding(16.dp), verticalArrangement = Arrangement.spacedBy(8.dp),
            horizontalAlignment = Alignment.CenterHorizontally) {
            Text("Drag the box or its corners to crop to the animal.", style = MaterialTheme.typography.bodyMedium)
            val bmp = preview
            when {
                bmp != null -> Box(Modifier.fillMaxWidth().heightIn(max = 420.dp)
                    .aspectRatio(bmp.width / bmp.height.toFloat(), matchHeightConstraintsFirst = true)) {
                    Image(bmp.asImageBitmap(), contentDescription = "Your photo", Modifier.matchParentSize(),
                        contentScale = ContentScale.FillBounds)
                    CropOverlay(box, square, Modifier.matchParentSize(), onSize = { viewSize = it }) { box = it }
                }
                failed -> Text("Couldn't show this photo, but you can still identify it.")
                else -> CircularProgressIndicator()
            }
            Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                FilterChip(selected = !square, onClick = { square = false }, label = { Text("Free") })
                FilterChip(selected = square, onClick = {
                    square = true
                    if (viewSize.width > 0) box = CropBox.square(box, viewSize.width, viewSize.height)
                }, label = { Text("Square") })
                FilterChip(selected = false, onClick = { square = false; box = CropBox() }, label = { Text("Whole photo") })
            }
            Row(Modifier.align(Alignment.End), horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                TextButton(onClick = onCancel) { Text("Cancel") }
                Button(onClick = { onIdentify(box.takeUnless { it.isWhole }) }) { Text("Identify") }
            }
        }
    }
}

@Composable
private fun CropOverlay(box: CropBox, square: Boolean, modifier: Modifier, onSize: (Size) -> Unit,
                        onChange: (CropBox) -> Unit) {
    val current by rememberUpdatedState(box)
    val squareNow by rememberUpdatedState(square)
    Canvas(modifier.onSizeChanged { onSize(Size(it.width.toFloat(), it.height.toFloat())) }.pointerInput(Unit) {
        val grab = 28.dp.toPx()
        val minSide = 32.dp.toPx()
        var start = CropBox()
        var corner: Pair<Boolean, Boolean>? = null
        var origin = Offset.Zero
        var moved = Offset.Zero
        detectDragGestures(
            onDragStart = { at ->
                val w = size.width.toFloat()
                val h = size.height.toFloat()
                start = current
                origin = at
                moved = Offset.Zero
                // Near a corner resizes from it; anywhere else moves the box.
                corner = listOf(false to false, true to false, false to true, true to true).firstOrNull { (e, s) ->
                    abs(at.x - (if (e) start.x + start.w else start.x) * w) < grab &&
                        abs(at.y - (if (s) start.y + start.h else start.y) * h) < grab
                }
            },
            onDrag = { change, delta ->
                change.consume()
                moved += delta
                val w = size.width.toFloat()
                val h = size.height.toFloat()
                val c = corner
                onChange(if (c == null) CropBox.moved(start, moved.x, moved.y, w, h)
                else CropBox.resized(start, c.first, c.second, origin.x + moved.x, origin.y + moved.y, w, h,
                    squareNow, minSide))
            })
    }) {
        val left = box.x * size.width
        val top = box.y * size.height
        val right = (box.x + box.w) * size.width
        val bottom = (box.y + box.h) * size.height
        // Dim outside the box, then a thin frame, thirds, and thick corners.
        clipRect(left, top, right, bottom, clipOp = ClipOp.Difference) { drawRect(Color.Black.copy(alpha = 0.5f)) }
        drawRect(Color.White, Offset(left, top), Size(right - left, bottom - top), style = Stroke(2.dp.toPx()))
        val thin = Color.White.copy(alpha = 0.45f)
        for (i in 1..2) {
            val x = left + (right - left) * i / 3
            val y = top + (bottom - top) * i / 3
            drawLine(thin, Offset(x, top), Offset(x, bottom), 1.dp.toPx())
            drawLine(thin, Offset(left, y), Offset(right, y), 1.dp.toPx())
        }
        val arm = min(18.dp.toPx(), min(right - left, bottom - top) / 2)
        val thick = 4.dp.toPx()
        for ((cx, sx) in listOf(left to 1f, right to -1f)) for ((cy, sy) in listOf(top to 1f, bottom to -1f)) {
            drawLine(Color.White, Offset(cx, cy), Offset(cx + arm * sx, cy), thick)
            drawLine(Color.White, Offset(cx, cy), Offset(cx, cy + arm * sy), thick)
        }
    }
}
