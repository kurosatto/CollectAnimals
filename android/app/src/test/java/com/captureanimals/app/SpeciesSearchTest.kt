package com.captureanimals.app

import org.junit.Assert.assertEquals
import org.junit.Test

class SpeciesSearchTest {
    private val list = listOf(
        Species("gray_fox", "Gray Fox", "Urocyon cinereoargenteus", "mammal", "common"),
        Species("bobcat", "Bobcat", "Lynx rufus", "mammal", "rare"),
        Species("red_fox", "Red Fox", "Vulpes vulpes", "mammal", "uncommon"),
        Species("fox_sparrow", "Fox Sparrow", "Passerella iliaca", "bird", "common"),
    )

    @Test fun needsTwoLetters() = assertEquals(emptyList<Species>(), searchSpecies(list, " f "))

    @Test fun matchesCommonOrScientificNameIgnoringCase() {
        assertEquals(listOf("bobcat"), searchSpecies(list, "LYNX").map { it.slug })
        assertEquals(listOf("bobcat"), searchSpecies(list, "bob").map { it.slug })
    }

    @Test fun prefixMatchesComeFirst() =
        assertEquals(listOf("fox_sparrow", "gray_fox", "red_fox"), searchSpecies(list, "fox").map { it.slug })
}
