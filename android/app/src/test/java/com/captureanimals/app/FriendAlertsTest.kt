package com.captureanimals.app

import org.junit.Assert.assertEquals
import org.junit.Assert.assertNull
import org.junit.Test

class FriendAlertsTest {
    @Test
    fun onlyUnseenRequestsAreNew() {
        assertEquals(listOf("bo"), FriendAlerts.newNames(setOf("ann"), listOf("ann", "bo")))
        assertEquals(emptyList<String>(), FriendAlerts.newNames(setOf("ann", "bo"), listOf("ann")))
    }

    @Test
    fun messages() {
        assertNull(FriendAlerts.message(emptyList(), emptyList()))
        assertEquals("ann sent you a friend request", FriendAlerts.message(listOf("ann"), emptyList()))
        assertEquals("2 new friend requests: ann, bo", FriendAlerts.message(listOf("ann", "bo"), emptyList()))
        assertEquals("ann sent you a friend request\ncy accepted your friend request",
            FriendAlerts.message(listOf("ann"), listOf("cy")))
    }
}
