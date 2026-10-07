// SPDX-License-Identifier: Apache-2.0 · Copyright 2026 Neer Patel
// The watch screens under the Accessibility Test Framework (contrast, touch targets, labels, clipped text), at the default
// text size and the largest Wear OS offers (124%). Run: gradle :wear:connectedDebugAndroidTest (a watch emulator attached).
package co.fusionspace.sample.wear

import androidx.compose.runtime.Composable
import androidx.compose.runtime.CompositionLocalProvider
import androidx.compose.ui.platform.LocalDensity
import androidx.compose.ui.test.junit4.accessibility.enableAccessibilityChecks
import androidx.compose.ui.test.junit4.createComposeRule
import androidx.compose.ui.semantics.SemanticsProperties
import androidx.compose.ui.test.SemanticsMatcher
import androidx.compose.ui.test.assert
import androidx.compose.ui.test.assertCountEquals
import androidx.compose.ui.test.onAllNodesWithText
import androidx.compose.ui.test.onNodeWithContentDescription
import androidx.compose.ui.test.onRoot
import androidx.compose.ui.test.tryPerformAccessibilityChecks
import androidx.compose.ui.unit.Density
import androidx.test.ext.junit.runners.AndroidJUnit4
import com.google.android.apps.common.testing.accessibility.framework.AccessibilityCheckPreset
import com.google.android.apps.common.testing.accessibility.framework.AccessibilityCheckResult.AccessibilityCheckResultType
import com.google.android.apps.common.testing.accessibility.framework.integrations.espresso.AccessibilityValidator
import co.fusionspace.design.wear.FsWearFind
import co.fusionspace.design.wear.FsWearUnfired
import co.fusionspace.design.wear.FusionSpaceWearTheme
import org.junit.Before
import org.junit.Rule
import org.junit.Test
import org.junit.runner.RunWith

@RunWith(AndroidJUnit4::class)
class AccessibilityTest {
    @get:Rule val rule = createComposeRule()

    // Every check in the latest preset, from the root, with a screenshot (contrast needs one); warnings fail too.
    @Before fun checks() = rule.enableAccessibilityChecks(
        AccessibilityValidator().setRunChecksFromRootView(true).setCaptureScreenshots(true)
            .setCheckPreset(AccessibilityCheckPreset.LATEST).setThrowExceptionFor(AccessibilityCheckResultType.WARNING)
    )

    private fun check(fontScale: Float = 1f, screen: @Composable () -> Unit) {
        rule.setContent {
            val d = LocalDensity.current
            CompositionLocalProvider(LocalDensity provides Density(d.density, fontScale)) {
                FusionSpaceWearTheme(mono = CascadiaMono, content = screen)
            }
        }
        rule.onRoot().tryPerformAccessibilityChecks()
    }

    private val find = @Composable { FsWearFind(1352, 62f, 20f, System.currentTimeMillis() - 4_000, onFound = {}) }
    private val unfired = @Composable { FsWearUnfired("2 · MAIN", onAcknowledge = {}) }

    @Test fun find() = check(screen = find)
    @Test fun findLargeText() = check(1.24f, find)
    @Test fun pad() = check { WearPad() }
    @Test fun padLargeText() = check(1.24f) { WearPad() }
    @Test fun unfired() = check(screen = unfired)
    @Test fun unfiredLargeText() = check(1.24f, unfired)

    // What TalkBack says: the words VoiceOver says on Apple Watch (product/watch/swiftui), one stop per thing.
    private fun says(description: String, state: Regex? = null) {
        val node = rule.onNodeWithContentDescription(description).assertExists()
        if (state != null) node.assert(SemanticsMatcher("state matches $state") {
            it.config.getOrElseNullable(SemanticsProperties.StateDescription) { null }?.let { d -> state.matches(d) } == true
        })
    }

    @Test fun findSpeech() {
        check(screen = find)
        says("Rocket 1,352 feet away, 42 degrees to your right, bearing 62 degrees true", Regex("""fix \d+ seconds old"""))
    }
    @Test fun padSpeech() {
        check { WearPad() }
        says("Device state, armed"); says("FS-VEGA-004, link 0.3 seconds")
        says("Channel 1, drogue, continuity"); says("Channel 2, main, continuity"); says("Channel 3, not used")
    }
    @Test fun unfiredSpeech() {
        check(screen = unfired)
        says("Unfired charge, 2, main. Approach as live. Disarm before handling.")
        rule.onAllNodesWithText("UNFIRED").assertCountEquals(0)  // read once: the parts aren't stops of their own
        rule.onNode(SemanticsMatcher.keyIsDefined(SemanticsProperties.Heading)).assertExists()
    }
}
