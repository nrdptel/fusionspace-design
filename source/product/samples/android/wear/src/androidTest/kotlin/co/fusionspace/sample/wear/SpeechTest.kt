// SPDX-License-Identifier: Apache-2.0 · Copyright 2026 Neer Patel
// What TalkBack is given on the watch's glanceable surfaces: the Find complication's one sentence (with its age counting
// up), and the Find tile read from its window the way a screen reader gets it. Fails on units read as letters ("ft", "° T").
// The screens' own labels are in AccessibilityTest. Run: gradle :wear:connectedDebugAndroidTest (a watch emulator attached).
package co.fusionspace.sample.wear

import android.accessibilityservice.AccessibilityServiceInfo
import android.app.UiAutomation
import android.os.SystemClock
import android.util.Log
import android.view.accessibility.AccessibilityNodeInfo
import androidx.test.ext.junit.runners.AndroidJUnit4
import androidx.test.platform.app.InstrumentationRegistry
import androidx.wear.watchface.complications.data.ComplicationType
import androidx.wear.watchface.complications.data.LongTextComplicationData
import androidx.wear.watchface.complications.data.ShortTextComplicationData
import org.junit.Assert.assertEquals
import org.junit.Assert.assertTrue
import org.junit.Test
import org.junit.runner.RunWith
import java.time.Instant

@RunWith(AndroidJUnit4::class)
class SpeechTest {
    private val instrumentation = InstrumentationRegistry.getInstrumentation()
    private val context = instrumentation.targetContext
    private val ui: UiAutomation = instrumentation.getUiAutomation(UiAutomation.FLAG_DONT_SUPPRESS_ACCESSIBILITY_SERVICES)
    private val letters = Regex("""\bft\b|\bAGL\b|°|\bT\b""")

    @Test fun complicationIsOneSentence() {
        val service = FindComplicationService()
        val now = Instant.now()
        for (type in listOf(ComplicationType.SHORT_TEXT, ComplicationType.LONG_TEXT)) {
            val data = service.getPreviewData(type)
            val spoken = when (data) {
                is ShortTextComplicationData -> data.contentDescription
                is LongTextComplicationData -> data.contentDescription
                else -> null
            }!!.getTextAt(context.resources, now).toString()
            Log.i("FsSpeech", "$type: $spoken")
            assertTrue("Not one sentence: $spoken", spoken.startsWith("Vega, landed, 1,352 feet, bearing 62 degrees true, fix "))
            assertTrue("Read as letters: $spoken", !letters.containsMatchIn(spoken))
            // the age counts up on the watch: a minute later it says so, without a new complication update
            val later = (data as? ShortTextComplicationData)?.contentDescription?.getTextAt(context.resources, now.plusSeconds(180))
                ?: (data as LongTextComplicationData).contentDescription!!.getTextAt(context.resources, now.plusSeconds(180))
            Log.i("FsSpeech", "$type, 3 min later: $later")
            assertTrue("The age didn't count: $later", Regex("""fix less than 4 min""").containsMatchIn(later.toString()))
        }
    }

    /** Runs a shell command and waits for it to finish (closing the stream at once doesn't wait). */
    private fun shell(cmd: String) = android.os.ParcelFileDescriptor.AutoCloseInputStream(ui.executeShellCommand(cmd)).use { it.readBytes() }

    private fun focusable(n: AccessibilityNodeInfo) = n.isFocusable || n.isClickable || n.isScreenReaderFocusable

    /** Everything a node says: its content description, else its text and the text of what it contains (not of other stops). */
    private fun says(n: AccessibilityNodeInfo, top: Boolean = true): List<String> {
        if (!top && focusable(n)) return emptyList()
        n.contentDescription?.takeIf { it.isNotBlank() }?.let { return listOf(it.toString()) }
        return listOfNotNull(n.text?.toString()?.takeIf { it.isNotBlank() }) + (0 until n.childCount).flatMap { i -> n.getChild(i)?.let { says(it, false) } ?: emptyList() }
    }

    /**
     * The screen as TalkBack's stops, in order (its rules, simplified): a focusable or clickable node is one stop and says
     * what it contains; text outside any such node is a stop of its own. Each stop is what would be spoken.
     */
    private fun collect(node: AccessibilityNodeInfo?, into: MutableList<String>, covered: Boolean = false) {
        if (node == null || !node.isVisibleToUser) return
        val stop = focusable(node)
        if (stop || (!covered && (node.contentDescription?.isNotBlank() == true || node.text?.isNotBlank() == true))) {
            val words = (says(node) + listOfNotNull(node.stateDescription?.toString())).joinToString(" ")
            if (words.isNotBlank()) into += words
        }
        for (i in 0 until node.childCount) collect(node.getChild(i), into, covered || stop || node.contentDescription?.isNotBlank() == true)
    }

    @Test fun tileReadsAsSentences() {
        ui.serviceInfo = ui.serviceInfo.apply { flags = flags or AccessibilityServiceInfo.FLAG_RETRIEVE_INTERACTIVE_WINDOWS }
        shell("input keyevent KEYCODE_WAKEUP")
        shell("am broadcast -a com.google.android.wearable.app.DEBUG_SURFACE --es operation add-tile --ecn component ${context.packageName}/.FindTileService")
        var lines = emptyList<String>()
        val until = SystemClock.uptimeMillis() + 20_000
        var tries = 0
        while (SystemClock.uptimeMillis() < until) {
            if (tries++ % 6 == 0) shell("am broadcast -a com.google.android.wearable.app.DEBUG_SYSUI --es operation show-tile --ei index 0")
            val all = mutableListOf<String>()
            ui.windows.forEach { collect(it.root, all) }
            if (all.any { "feet" in it }) { lines = all; break }
            SystemClock.sleep(500)
        }
        lines.forEach { Log.i("FsSpeech", "tile: $it") }
        shell("input keyevent KEYCODE_BACK")
        assertTrue("The tile wasn't found", lines.isNotEmpty())
        assertTrue("No title: $lines", lines.any { it == "Vega, landed" })
        val sentence = lines.first { it.startsWith("1,352 feet") }
        assertTrue("Not one sentence: $sentence", Regex("""1,352 feet, bearing 62 degrees true, fix \d+ seconds? old""").matches(sentence))
        // the readout's own texts aren't read again after the sentence
        val read = lines.filter { letters.containsMatchIn(it) }
        assertEquals("Read as letters: $read", emptyList<String>(), read)
    }
}
