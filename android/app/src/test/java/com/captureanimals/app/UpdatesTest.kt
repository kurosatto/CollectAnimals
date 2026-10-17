package com.captureanimals.app

import org.junit.Assert.assertFalse
import org.junit.Assert.assertTrue
import org.junit.Test

class UpdatesTest {
    @Test fun comparesVersionsByNumber() {
        assertTrue(Updates.isNewer("0.9.0", "0.8.2"))
        assertTrue(Updates.isNewer("0.10.0", "0.9.2"))
        assertTrue(Updates.isNewer("1.0", "0.9.9"))
        assertFalse(Updates.isNewer("0.9.0", "0.9.0"))
        assertFalse(Updates.isNewer("0.9", "0.9.0"))
        assertFalse(Updates.isNewer("0.8.2", "0.9.0"))
        assertFalse(Updates.isNewer("0.9.0", "dev"))
    }
}
