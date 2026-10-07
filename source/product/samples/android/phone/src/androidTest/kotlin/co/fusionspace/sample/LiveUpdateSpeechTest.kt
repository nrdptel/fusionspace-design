// SPDX-License-Identifier: Apache-2.0 · Copyright 2026 Neer Patel
// What TalkBack is given for the Live Update in the notification shade: posts it, opens the shade, and reads the shade's
// accessibility nodes the way a screen reader gets them (text with any TtsSpans, content descriptions). uiautomator's dump can't do this: the shade never goes
// idle while the time since liftoff counts. Run: gradle :phone:connectedDebugAndroidTest (an emulator or phone attached).
package co.fusionspace.sample

import android.accessibilityservice.AccessibilityServiceInfo
import android.app.NotificationManager
import android.app.UiAutomation
import android.os.Build
import android.os.SystemClock
import android.text.Spanned
import android.text.style.TtsSpan
import android.util.Log
import android.view.accessibility.AccessibilityNodeInfo
import androidx.test.ext.junit.runners.AndroidJUnit4
import androidx.test.platform.app.InstrumentationRegistry
import org.junit.After
import org.junit.Assert.assertTrue
import org.junit.Test
import org.junit.runner.RunWith

@RunWith(AndroidJUnit4::class)
class LiveUpdateSpeechTest {
    private val instrumentation = InstrumentationRegistry.getInstrumentation()
    private val context = instrumentation.targetContext
    private val ui: UiAutomation = instrumentation.getUiAutomation(UiAutomation.FLAG_DONT_SUPPRESS_ACCESSIBILITY_SERVICES)

    /** Runs a shell command and waits for it to finish (closing the stream at once doesn't wait). */
    private fun shell(cmd: String) = android.os.ParcelFileDescriptor.AutoCloseInputStream(ui.executeShellCommand(cmd)).use { it.readBytes() }

    @After fun close() {
        shell("cmd statusbar collapse")
        context.getSystemService(NotificationManager::class.java).cancelAll()
    }

    /** A node's text as a screen reader speaks it: each TtsSpan's words in place of the characters it covers. */
    private fun spoken(text: CharSequence): String {
        if (text !is Spanned) return text.toString()
        val out = StringBuilder(); var at = 0
        text.getSpans(0, text.length, TtsSpan::class.java).sortedBy { text.getSpanStart(it) }.forEach { span ->
            val start = text.getSpanStart(span); val end = text.getSpanEnd(span)
            if (start < at) return@forEach
            out.append(text, at, start)
            out.append(span.args.getString(TtsSpan.ARG_TEXT) ?: text.subSequence(start, end))
            at = end
        }
        return out.append(text, at, text.length).toString()
    }

    private fun collect(node: AccessibilityNodeInfo?, into: MutableList<String>) {
        if (node == null) return
        node.contentDescription?.let { into += spoken(it) } ?: node.text?.let { into += spoken(it) }
        for (i in 0 until node.childCount) collect(node.getChild(i), into)
    }

    /** Posts with [post], opens the shade and returns what the card titled [title] says, line by line. */
    private fun shade(title: String, post: () -> Unit): List<String> {
        ui.serviceInfo = ui.serviceInfo.apply { flags = flags or AccessibilityServiceInfo.FLAG_RETRIEVE_INTERACTIVE_WINDOWS }
        shell("pm grant ${context.packageName} android.permission.POST_NOTIFICATIONS")
        // the screen may have gone off during earlier tests: the shade doesn't open on a sleeping phone
        shell("input keyevent KEYCODE_WAKEUP")
        shell("wm dismiss-keyguard")
        post()
        // The card's lines, found by its title; read from every window (the shade is SystemUI's). The shade is asked to
        // open again every few tries: it ignores the request while it's still closing from an earlier run.
        var lines = emptyList<String>()
        val until = SystemClock.uptimeMillis() + 20_000
        var tries = 0
        var last = emptyList<String>()
        while (SystemClock.uptimeMillis() < until) {
            if (tries++ % 6 == 0) shell("cmd statusbar expand-notifications")
            val all = mutableListOf<String>()
            ui.windows.forEach { collect(it.root, all) }
            last = all
            val card = all.indexOfFirst { it.startsWith(title) }
            if (card >= 0) { lines = all.drop(card).take(8); break }
            SystemClock.sleep(500)
        }
        if (lines.isEmpty()) Log.i("FsSpeech", "not found; windows ${ui.windows.map { it.title }}; read $last; " +
            "notifications ${context.getSystemService(NotificationManager::class.java).activeNotifications.map { it.id }}")
        lines.forEach { Log.i("FsSpeech", "$title: $it") }
        assertTrue("$title wasn't found in the shade", lines.isNotEmpty())
        return lines
    }

    /**
     * The Live Update as posted, promoted, read from the shade: the card is there, its title and values are each a line,
     * and nothing it says is cut ("…"). What TalkBack hears is logged under FsSpeech. Units: SystemUI passes the card's text
     * without spans, so a TtsSpan never reaches TalkBack here (tried October 2026 on Android 16 and 17, promoted and not);
     * the units are read as the speech engine reads "ft". Android 17's MetricStyle labels ("Altitude (ft)") are SystemUI's.
     */
    @Test fun cardIsRead() {
        val lines = shade("Flight 04") { postLiveUpdate(context) }
        assertTrue("Cut: $lines", lines.none { "…" in it })
        if (Build.VERSION.SDK_INT >= 37) assertTrue("$lines", lines.containsAll(listOf("Altitude (ft)", "612", "From you (ft)", "1,352", "Since liftoff")))
        else assertTrue("$lines", "612 ft AGL · −18 ft/s · 1,352 ft at 062° T" in lines.map { it.replace('\u00A0', ' ') })
    }
}
