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
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.width
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
import androidx.compose.ui.layout.Layout
import androidx.compose.ui.platform.LocalConfiguration
import androidx.compose.ui.platform.LocalDensity
import androidx.compose.ui.unit.Constraints
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
import co.fusionspace.design.wear.fsClearOfTime

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
                    Screen.Find -> FsWearFind(distanceFt = 1352, bearingTrue = 62f, headingTrue = 20f, fixAge = "4\u00A0s ago", asOf = "9:41",
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

/** What the Find tile's edge button opens. */
class FindActivity : MainActivity()

class FindTileService : FsFindTileService() {
    override val findActivityClass: String get() = FindActivity::class.java.name
}
class FindComplicationService : FsFindComplicationService()

/** Pad, read only (product/watch.md#screens): the state in its box, the designation and link age, the channels in order. */
@Composable
internal fun WearPad() {
    val c = FsWearColors
    val state = rememberTransformingLazyColumnState()
    AppScaffold(timeText = { TimeText() }) {
        ScreenScaffold(scrollState = state) { padding ->
            // ScreenScaffold's padding is vertical only; on a round screen the rows need their own side margins, wide enough
            // that the last row, low on the circle, clears the bezel.
            // Larger text pushes the rows lower on the circle, where it's narrower: the margins grow with it.
            val side = (LocalConfiguration.current.screenWidthDp * 0.14f + (LocalDensity.current.fontScale - 1f).coerceAtLeast(0f) * 56).dp
            val clear = fsClearOfTime(padding)  // the top grows with the time at large text sizes
            val inset = PaddingValues(start = side, end = side, top = clear.calculateTopPadding(), bottom = clear.calculateBottomPadding())
            TransformingLazyColumn(state = state, contentPadding = inset, verticalArrangement = Arrangement.spacedBy(6.dp)) {
                item { FsWearStateBox(armed = true) }
                item { Text("FS-VEGA-004 · 0.3\u00A0s", style = mono(13), color = c.inkMuted) }
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
private fun Channel(name: String, word: String, ok: Boolean, modifier: Modifier = Modifier) {
    val c = FsWearColors
    val filled = ok && LocalAmbientModeManager.current?.currentAmbientMode !is AmbientMode.Ambient  // no fills in ambient
    val nameText = @Composable { Text(name, style = mono(15), color = c.ink, maxLines = 1, softWrap = false) }
    val state = @Composable {
        Text(
            word, style = mono(13, FontWeight.SemiBold), color = if (filled) c.onOkFill else if (ok) c.ok else c.inkMuted, maxLines = 1, softWrap = false,
            modifier = (if (filled) Modifier.background(c.okFill) else Modifier.border(1.dp, if (ok) c.ok else c.ruleStrong))
                .heightIn(min = 24.dp).padding(horizontal = 8.dp, vertical = 3.dp),
        )
    }
    // The name and its state on one line, or the state under the name when the text is too large for both.
    FirstThatFits(modifier.fillMaxWidth().clearAndSetSemantics { contentDescription = "$name, $word" }) {
        Row(Modifier.fillMaxWidth(), verticalAlignment = Alignment.CenterVertically) {
            nameText(); Spacer(Modifier.width(8.dp)); Spacer(Modifier.weight(1f)); state()
        }
        Column(verticalArrangement = Arrangement.spacedBy(4.dp)) { nameText(); state() }
    }
}

/** The first child that fits the width at its own size, every text on one line; the last one otherwise (FsFirstThatFits on the phone). */
@Composable
private fun FirstThatFits(modifier: Modifier = Modifier, content: @Composable () -> Unit) {
    Layout(content, modifier) { measurables, constraints ->
        val chosen = measurables.dropLast(1).firstOrNull {
            !constraints.hasBoundedWidth || it.maxIntrinsicWidth(Constraints.Infinity) <= constraints.maxWidth
        } ?: measurables.last()
        val p = chosen.measure(constraints)
        layout(p.width, p.height) { p.place(0, 0) }
    }
}
