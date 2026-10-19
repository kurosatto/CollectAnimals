package com.captureanimals.app

import org.junit.Assert.assertArrayEquals
import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertTrue
import org.junit.Test

class CropTest {
    private fun assertBox(expected: CropBox, actual: CropBox) {
        assertEquals(expected.x, actual.x, 1e-4f); assertEquals(expected.y, actual.y, 1e-4f)
        assertEquals(expected.w, actual.w, 1e-4f); assertEquals(expected.h, actual.h, 1e-4f)
    }

    @Test
    fun wholePhotoIsNoCrop() {
        assertTrue(CropBox().isWhole)
        assertFalse(CropBox(0.5f, 0f, 0.5f, 1f).isWhole)
        assertArrayEquals(intArrayOf(100, 0, 100, 100), CropBox(0.5f, 0f, 0.5f, 1f).pixels(200, 100))
    }

    @Test
    fun squareFitsInTheBox() {
        // 400x200 view, whole photo: a 200 px square in the middle.
        assertBox(CropBox(0.25f, 0f, 0.5f, 1f), CropBox.square(CropBox(), 400f, 200f))
    }

    @Test
    fun movingStaysInsideThePhoto() {
        val box = CropBox(0.25f, 0.25f, 0.5f, 0.5f)
        assertBox(CropBox(0.5f, 0.5f, 0.5f, 0.5f), CropBox.moved(box, 1000f, 1000f, 100f, 100f))
        assertBox(CropBox(0.35f, 0.15f, 0.5f, 0.5f), CropBox.moved(box, 10f, -10f, 100f, 100f))
    }

    @Test
    fun resizingKeepsTheOppositeCorner() {
        val box = CropBox(0.25f, 0.25f, 0.5f, 0.5f)
        // Drag the bottom-right corner to (50, 90) in a 100x100 view.
        assertBox(CropBox(0.25f, 0.25f, 0.25f, 0.65f), CropBox.resized(box, true, true, 50f, 90f, 100f, 100f, false, 10f))
        // Square: the bigger side wins, limited by the room left.
        assertBox(CropBox(0.25f, 0.25f, 0.65f, 0.65f), CropBox.resized(box, true, true, 50f, 90f, 100f, 100f, true, 10f))
        assertBox(CropBox(0.25f, 0.25f, 0.75f, 0.75f), CropBox.resized(box, true, true, 500f, 500f, 100f, 100f, true, 10f))
        // Top-left past the other corner stops at the minimum size.
        assertBox(CropBox(0.65f, 0.65f, 0.1f, 0.1f), CropBox.resized(box, false, false, 90f, 90f, 100f, 100f, false, 10f))
    }
}
