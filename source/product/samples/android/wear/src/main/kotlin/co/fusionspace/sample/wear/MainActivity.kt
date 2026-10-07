// SPDX-License-Identifier: Apache-2.0 · Copyright 2026 Neer Patel
// The sample Wear OS app: Find, Pad and Unfired from product/watch/compose. Debug: open one directly with
// `adb shell am start -n co.fusionspace.sample.wear/.MainActivity --es screen find|pad|unfired`.
package co.fusionspace.sample.wear

import android.content.Intent
import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.PaddingValues
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.heightIn
import androidx.compose.foundation.layout.padding
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalConfiguration
import androidx.compose.ui.semantics.contentDescription
import androidx.compose.ui.semantics.clearAndSetSemantics
import androidx.compose.ui.text.TextStyle
import androidx.wear.compose.foundation.AmbientMode
import androidx.wear.compose.foundation.LocalAmbientModeManager
import androidx.compose.ui.text.font.Font
import androidx.compose.ui.text.font.FontFamily
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.em
import androidx.compose.ui.unit.sp
import androidx.wear.compose.foundation.lazy.TransformingLazyColumn
import androidx.wear.compose.foundation.lazy.rememberTransformingLazyColumnState
import androidx.wear.compose.material3.AppScaffold
import androidx.wear.compose.material3.ScreenScaffold
import androidx.wear.compose.material3.Text
import androidx.wear.compose.material3.TimeText
import co.fusionspace.design.wear.FsFindComplicationService
import co.fusionspace.design.wear.FsFindTileService
import co.fusionspace.design.wear.FsWearColors
import co.fusionspace.design.wear.FsWearFind
import co.fusionspace.design.wear.FsWearStateBox
import co.fusionspace.design.wear.FsWearUnfired
import co.fusionspace.design.wear.FusionSpaceWearTheme

/** Cascadia Mono, bundled from type/fonts by the build (see the root build.gradle.kts). */
val CascadiaMono = FontFamily(
    Font(R.font.cascadia_mono_regular, FontWeight.Normal),
    Font(R.font.cascadia_mono_semibold, FontWeight.SemiBold),
)

enum class Screen { Find, Pad, Unfired }

open class MainActivity : ComponentActivity() {
    private var screen by mutableStateOf(Screen.Find)

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        open(intent)
        setContent {
            // The theme provides LocalAmbientModeManager, so the screens follow ambient mode.
            FusionSpaceWearTheme(mono = CascadiaMono) {
                when (screen) {
                    // The example from product/watch.md: 1,352 ft at 062° T, the wrist pointing 020°.
                    Screen.Find -> FsWearFind(distanceFt = 1352, bearingTrue = 62f, headingTrue = 20f, fixAge = "4 s ago", asOf = "9:41",
                        onFound = { finish() })
                    Screen.Pad -> WearPad()
                    Screen.Unfired -> FsWearUnfired("2 · MAIN", onAcknowledge = { screen = Screen.Find })
                }
            }
        }
    }

    override fun onNewIntent(intent: Intent) {
        super.onNewIntent(intent)
        open(intent)
    }

    private fun open(intent: Intent) {
        when (intent.getStringExtra("screen")) {
            "find" -> screen = Screen.Find
            "pad" -> screen = Screen.Pad
            "unfired" -> screen = Screen.Unfired
        }
    }
}

/** What the Find tile's edge button opens (FsFindTileService launches "<package>.FindActivity"). */
class FindActivity : MainActivity()

class FindTileService : FsFindTileService()
class FindComplicationService : FsFindComplicationService()

/** Pad, read only (product/watch.md#screens): the state in its box, the designation and link age, the channels in order. */
@Composable
private fun WearPad() {
    val c = FsWearColors
    val state = rememberTransformingLazyColumnState()
    AppScaffold(timeText = { TimeText() }) {
        ScreenScaffold(scrollState = state) { padding ->
            // ScreenScaffold's padding is vertical only; on a round screen the rows need their own side margins, wide enough
            // that the last row, low on the circle, clears the bezel.
            val side = (LocalConfiguration.current.screenWidthDp * 0.14f).dp
            val inset = PaddingValues(start = side, end = side, top = padding.calculateTopPadding(), bottom = padding.calculateBottomPadding())
            TransformingLazyColumn(state = state, contentPadding = inset, verticalArrangement = Arrangement.spacedBy(6.dp)) {
                item { FsWearStateBox(armed = true) }
                item { Text("FS-VEGA-004 · 0.3 s", style = mono(13), color = c.inkMuted) }
                item { Channel("1 DROGUE", "CONT", ok = true) }
                item { Channel("2 MAIN", "CONT", ok = true) }
                item { Channel("3 —", "NOT USED", ok = false) }
                item {
                    Text("Safe it with the switch or the phone.", color = c.inkMuted, fontSize = 14.sp, textAlign = TextAlign.Center,
                        modifier = Modifier.fillMaxWidth())
                }
            }
        }
    }
}

private fun mono(size: Int, weight: FontWeight = FontWeight.Normal) =
    TextStyle(fontFamily = CascadiaMono, fontSize = size.sp, fontWeight = weight, letterSpacing = 0.04.em)

/** A channel and its continuity: CONT filled in Aurora, NOT USED outlined and gray (product/watch.md#what-fusionspace-owns). */
@Composable
private fun Channel(name: String, word: String, ok: Boolean) {
    val c = FsWearColors
    val filled = ok && LocalAmbientModeManager.current?.currentAmbientMode !is AmbientMode.Ambient  // no fills in ambient
    Row(Modifier.fillMaxWidth().clearAndSetSemantics { contentDescription = "$name, $word" }, verticalAlignment = Alignment.CenterVertically) {
        Text(name, style = mono(15), color = c.ink)
        Spacer(Modifier.weight(1f))
        Text(
            word, style = mono(13, FontWeight.SemiBold), color = if (filled) c.onOkFill else if (ok) c.ok else c.inkMuted,
            modifier = (if (filled) Modifier.background(c.okFill) else Modifier.border(1.dp, if (ok) c.ok else c.ruleStrong))
                .heightIn(min = 24.dp).padding(horizontal = 8.dp, vertical = 3.dp),
        )
    }
}
