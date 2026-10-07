// SPDX-License-Identifier: Apache-2.0 · Copyright 2026 Neer Patel
// The phone screens under the Accessibility Test Framework (contrast, touch targets, labels, clipped text), at the
// default text size and at 200%. Run: gradle :phone:connectedDebugAndroidTest (an emulator or phone attached).
package co.fusionspace.sample

import androidx.compose.runtime.Composable
import androidx.compose.runtime.CompositionLocalProvider
import androidx.compose.ui.platform.LocalDensity
import androidx.compose.ui.test.junit4.accessibility.enableAccessibilityChecks
import androidx.compose.ui.test.junit4.createComposeRule
import androidx.compose.ui.semantics.SemanticsProperties
import androidx.compose.ui.test.SemanticsMatcher
import androidx.compose.ui.test.hasText
import androidx.compose.ui.test.onAllNodesWithContentDescription
import androidx.compose.ui.test.onFirst
import androidx.compose.ui.test.onNodeWithContentDescription
import androidx.compose.ui.test.onRoot
import androidx.compose.ui.test.tryPerformAccessibilityChecks
import androidx.compose.ui.unit.Density
import androidx.test.ext.junit.runners.AndroidJUnit4
import com.google.android.apps.common.testing.accessibility.framework.AccessibilityCheckPreset
import com.google.android.apps.common.testing.accessibility.framework.AccessibilityCheckResult.AccessibilityCheckResultType
import com.google.android.apps.common.testing.accessibility.framework.integrations.espresso.AccessibilityValidator
import co.fusionspace.design.FsTheme
import co.fusionspace.design.FusionSpaceTheme
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

    private fun check(theme: FsTheme, fontScale: Float = 1f, screen: @Composable () -> Unit) {
        rule.setContent {
            val d = LocalDensity.current
            CompositionLocalProvider(LocalDensity provides Density(d.density, fontScale)) {
                FusionSpaceTheme(theme, mono = CascadiaMono, content = screen)
            }
        }
        rule.onRoot().tryPerformAccessibilityChecks()
    }

    @Test fun pad() = check(FsTheme.Field) { PadScreen(onBack = {}) }
    @Test fun padLargeText() = check(FsTheme.Field, 2f) { PadScreen(onBack = {}) }
    @Test fun track() = check(FsTheme.Dark) { TrackScreen(onBack = {}) }
    @Test fun trackLargeText() = check(FsTheme.Dark, 2f) { TrackScreen(onBack = {}) }

    // What TalkBack says: the words VoiceOver says on the iPhone (product/mobile/swiftui).
    @Test fun padSpeech() {
        check(FsTheme.Field) { PadScreen(onBack = {}) }
        rule.onNodeWithContentDescription("Device state, safe").assertExists()
        rule.onNode(hasText("Pad 3 · Flight 04") and SemanticsMatcher.keyIsDefined(SemanticsProperties.Heading)).assertExists()
        // the chip says the word in full (both of FsFirstThatFits's layouts carry it)
        rule.onAllNodesWithContentDescription("Continuity", useUnmergedTree = true).onFirst().assertExists()
    }
}
