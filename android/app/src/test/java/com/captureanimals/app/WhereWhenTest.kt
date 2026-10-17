package com.captureanimals.app

import org.json.JSONObject
import org.junit.Assert.assertEquals
import org.junit.Assert.assertNull
import org.junit.Test
import java.time.LocalDateTime

class WhereWhenTest {
    @Test
    fun parsesTheOwnersTimeAndPlace() {
        val ww = WhereWhen.parse(JSONObject("""{"capture_id": 7, "taken_at": "2026-05-04T18:41:12",
            "time_source": "photo", "latitude": 36.97, "longitude": -122.03, "place": "near Santa Cruz",
            "place_source": "edited"}"""))!!
        assertEquals(7, ww.captureId)
        assertEquals(LocalDateTime.of(2026, 5, 4, 18, 41, 12), ww.takenAt)
        assertEquals(36.97, ww.latitude!!, 1e-9)
        assertEquals("near Santa Cruz" to "edited", ww.place to ww.placeSource)
    }

    @Test
    fun noPlace() {
        val ww = WhereWhen.parse(JSONObject("""{"capture_id": 7, "taken_at": "2026-05-04T18:41:00",
            "time_source": "upload", "latitude": null, "longitude": null, "place": null, "place_source": null}"""))!!
        assertNull(ww.latitude)
        assertNull(ww.place)
        assertNull(WhereWhen.parse(null))
    }

    @Test
    fun albumPhotoShowsTheDayItWasTaken() {
        val o = JSONObject("""{"taken_on": "2026-01-10", "caught_at": "2026-10-17T22:00:00Z"}""")
        val day = java.time.Instant.ofEpochMilli(OnlinePhoto.takenOn(o)).atZone(java.time.ZoneId.systemDefault()).toLocalDate()
        assertEquals(java.time.LocalDate.of(2026, 1, 10), day)
    }
}
