// SPDX-License-Identifier: Apache-2.0 · Copyright 2026 Neer Patel
// The watch screens under the Accessibility Test Framework (contrast, touch targets, labels, clipped text), at the default
// text size and the largest Wear OS offers (124%). Run: gradle :wear:connectedDebugAndroidTest (a watch emulator attached).
package co.fusionspace.sample.wear

import androidx.compose.runtime.Composable
import androidx.compose.runtime.CompositionLocalProvider
import androidx.compose.ui.platform.LocalDensity
import androidx.compose.ui.test.junit4.accessibility.enableAccessibilityChecks
import androidx.compose.ui.test.junit4.createComposeRule
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

    private val find = @Composable { FsWearFind(1352, 62f, 20f, "4\u00A0s ago", "9:41", onFound = {}) }
    private val unfired = @Composable { FsWearUnfired("2 · MAIN", onAcknowledge = {}) }

    @Test fun find() = check(screen = find)
    @Test fun findLargeText() = check(1.24f, find)
    @Test fun pad() = check { WearPad() }
    @Test fun padLargeText() = check(1.24f) { WearPad() }
    @Test fun unfired() = check(screen = unfired)
    @Test fun unfiredLargeText() = check(1.24f, unfired)
}
