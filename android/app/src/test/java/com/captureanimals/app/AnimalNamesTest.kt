package com.captureanimals.app

import org.junit.Assert.assertEquals
import org.junit.Assert.assertTrue
import org.junit.Test
import java.io.File

class AnimalNamesTest {
    private val names = AnimalNames.parse("""{"about": "Names: test",
        "groups": [["bird", "Some kind of bird", ""], ["beetle", "Some kind of beetle", "ladybug"]],
        "names": [["American Robin", "Turdus migratorius", "songbird"],
                  ["European Starling", "Sturnus vulgaris", "songbird"],
                  ["Convergent Lady Beetle", "Hippodamia convergens", "beetle"],
                  ["Rufous Hummingbird", "Selasphorus rufus", "hummingbird"],
                  ["Mule Deer", "Odocoileus hemionus", "deer"]]}""")

    @Test
    fun everyWordMustStartAWord() {
        assertEquals(listOf("Turdus migratorius"), names.search("amer rob").map { it.label })
        assertEquals(listOf("Turdus migratorius"), names.search("turdus").map { it.label })
        assertTrue(names.search("obin").isEmpty())
    }

    @Test
    fun namesStartingWithTheTextComeFirstThenGroups() {
        // "Rufous Hummingbird" starts with "ru"; nothing else does.
        assertEquals("Selasphorus rufus", names.search("ru").first().label)
        // A group's extra words find it too, ahead of names that only match a later word.
        assertEquals(listOf("group:beetle", "Hippodamia convergens"), names.search("lady").map { it.label })
    }

    @Test
    fun foldsAccentsAndPunctuation() {
        assertEquals("cafe s bird", fold("Café's  Bird!"))
        assertEquals(listOf("Odocoileus hemionus"), names.search("MULE-deer").map { it.label })
    }

    @Test
    fun articles() {
        assertEquals("an American Robin", withArticle("American Robin"))
        assertEquals("a Mule Deer", withArticle("Mule Deer"))
        assertEquals("some kind of beetle", withArticle("Some kind of beetle"))
        assertEquals("a person", withArticle("A person"))
    }

    @Test
    fun queueKeepsNamesUntilSent() {
        val dir = createTempDirectory()
        val q = NameQueue(dir)
        q.add("Turdus migratorius", "american_crow", "CA", null)
        q.add("group:beetle", null, null, null)
        val items = q.all()
        assertEquals(listOf("Turdus migratorius", "group:beetle"), items.map { it.label })
        assertEquals("american_crow", items[0].predicted)
        q.remove(items[0].id)
        assertEquals(listOf("group:beetle"), NameQueue(dir).all().map { it.label })
        dir.deleteRecursively()
    }

    private fun createTempDirectory(): File = kotlin.io.path.createTempDirectory("names").toFile()
}
