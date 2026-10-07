// SPDX-License-Identifier: Apache-2.0 · Copyright 2026 Neer Patel
// The track screen (product/mobile.md#screens, product/mobile/screens/android-track.png): dark; the phase strip, the two
// numbers that matter under the main, a drawn stand-in for the offline map, then distance, bearing and the coordinates.
package co.fusionspace.sample

import android.content.ClipData
import androidx.compose.foundation.Canvas
import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.ExperimentalLayoutApi
import androidx.compose.foundation.layout.FlowRow
import androidx.compose.foundation.layout.IntrinsicSize
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.aspectRatio
import androidx.compose.foundation.layout.consumeWindowInsets
import androidx.compose.foundation.layout.fillMaxHeight
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.heightIn
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.filled.ArrowBack
import androidx.compose.material.icons.filled.MoreVert
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.material3.TopAppBar
import androidx.compose.material3.TopAppBarDefaults
import androidx.compose.runtime.Composable
import androidx.compose.runtime.rememberCoroutineScope
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.geometry.Size
import androidx.compose.ui.graphics.Path
import androidx.compose.ui.graphics.PathEffect
import androidx.compose.ui.graphics.drawscope.Stroke
import androidx.compose.ui.platform.ClipEntry
import androidx.compose.ui.platform.LocalClipboard
import androidx.compose.ui.platform.LocalDensity
import androidx.compose.ui.res.painterResource
import androidx.compose.ui.semantics.contentDescription
import androidx.compose.ui.semantics.semantics
import androidx.compose.ui.text.TextStyle
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.em
import androidx.compose.ui.unit.sp
import co.fusionspace.design.FsReadout
import co.fusionspace.design.FsSheetHeader
import co.fusionspace.design.FsSignal
import co.fusionspace.design.FsStatus
import co.fusionspace.design.LocalFsColors
import co.fusionspace.design.LocalFsMono
import kotlinx.coroutines.launch

private val PHASES = listOf("Pad", "Boost", "Coast", "Apogee", "Drogue", "Main", "Landed")

@OptIn(ExperimentalMaterial3Api::class, ExperimentalLayoutApi::class)
@Composable
fun TrackScreen(onBack: () -> Unit) {
    val c = LocalFsColors.current
    Scaffold(
        containerColor = c.canvas,
        topBar = {
            TopAppBar(
                title = {},
                navigationIcon = { IconButton(onClick = onBack) { Icon(Icons.AutoMirrored.Filled.ArrowBack, "Back") } },
                actions = { IconButton(onClick = {}) { Icon(Icons.Filled.MoreVert, "More") } },
                colors = TopAppBarDefaults.topAppBarColors(containerColor = c.canvas, scrolledContainerColor = c.canvas),
            )
        },
    ) { padding ->
        Column(
            Modifier.fillMaxSize().padding(padding).consumeWindowInsets(padding).verticalScroll(rememberScrollState())
                .padding(horizontal = 16.dp).padding(bottom = 16.dp),
            verticalArrangement = Arrangement.spacedBy(12.dp),
        ) {
            FlowRow(horizontalArrangement = Arrangement.spacedBy(8.dp), verticalArrangement = Arrangement.spacedBy(8.dp)) {
                Tag("FLIGHT 04 · FS-VEGA-004")
                FsStatus("Link", FsSignal.Ok, detail = "0.4 s", icon = { StatusIcon(R.drawable.fs_telemetry) })
            }
            Text("Track", style = MaterialTheme.typography.headlineMedium, color = c.ink)
            PhaseStrip(now = 5)
            FsSheetHeader("Now", 1, 2)
            Row(Modifier.fillMaxWidth()) {
                FsReadout("Altitude", "612", "ft AGL", Modifier.weight(1f), qualifier = "Barometer · 0.4 s ago", spokenUnit = "feet above ground level")
                FsReadout("Descent", "18", "ft/s", Modifier.weight(1f), qualifier = "Under the main", spokenUnit = "feet per second")
            }
            MapStandIn()
            FsSheetHeader("Find it", 2, 2)
            Row(Modifier.fillMaxWidth()) {
                FsReadout("Distance", "1,352", "ft", Modifier.weight(1f), qualifier = "From you", spokenUnit = "feet")
                FsReadout("Bearing", "062°", "T", Modifier.weight(1f), qualifier = "Declination 13° E", spokenUnit = "true")
            }
            Coordinates("40.86512, -119.06274")
        }
    }
}

@Composable
private fun mono(size: Int, weight: FontWeight = FontWeight.Normal) =
    TextStyle(fontFamily = LocalFsMono.current, fontSize = size.sp, fontWeight = weight, letterSpacing = 0.02.em)

/**
 * Done in ink, now inverted, next faint (product/mobile.md#screens). Seven cells in a row; with large text, as many as
 * fit per row (whole words, never cut).
 */
@OptIn(ExperimentalLayoutApi::class)
@Composable
private fun PhaseStrip(now: Int) {
    val c = LocalFsColors.current
    val perRow = when { LocalDensity.current.fontScale <= 1.15f -> 7; LocalDensity.current.fontScale <= 1.6f -> 4; else -> 3 }
    FlowRow(
        Modifier.fillMaxWidth().border(0.5.dp, c.ruleStrong)
            .semantics { contentDescription = "Phase: ${PHASES[now]}, ${now} of ${PHASES.size - 1} done" },
        maxItemsInEachRow = perRow,
    ) {
        PHASES.forEachIndexed { i, p ->
            Text(
                p.uppercase(), style = mono(11).copy(letterSpacing = 0.em), textAlign = TextAlign.Center, maxLines = 1, softWrap = false,
                color = when { i < now -> c.ink; i == now -> c.canvas; else -> c.inkFaint },
                modifier = Modifier.weight(1f).border(0.5.dp, c.ruleStrong).background(if (i == now) c.ink else c.canvas)
                    .heightIn(min = 32.dp).padding(vertical = 8.dp),
            )
        }
    }
}

/** A drawn stand-in for the offline map: the flight path, the pad, the rocket and the predicted landing (dashed, Nebula). */
@Composable
private fun MapStandIn() {
    val c = LocalFsColors.current
    Box(Modifier.fillMaxWidth().aspectRatio(1.6f).border(1.dp, c.ruleStrong).background(c.surface)
        .semantics { contentDescription = "Map: Vega 1,352 feet from you at 62 degrees true, predicted landing to the north-east" }) {
        Canvas(Modifier.fillMaxSize()) {
            val w = size.width; val h = size.height
            for (i in 1..5) drawLine(c.rule, Offset(w * i / 6f, 0f), Offset(w * i / 6f - 40f, h), 1.dp.toPx())
            for (i in 1..3) drawLine(c.rule, Offset(0f, h * i / 4f), Offset(w, h * i / 4f - 30f), 1.dp.toPx())
            val pts = listOf(0.25f to 0.74f, 0.30f to 0.62f, 0.38f to 0.53f, 0.46f to 0.47f, 0.55f to 0.43f, 0.66f to 0.40f, 0.70f to 0.39f)
                .map { (x, y) -> Offset(w * x, h * y) }
            val path = Path().apply { moveTo(pts[0].x, pts[0].y); pts.drop(1).forEach { lineTo(it.x, it.y) } }
            drawPath(path, c.ink, style = Stroke(2.dp.toPx()))
            pts.drop(1).dropLast(1).forEach { drawCircle(c.ink, 3.dp.toPx(), it) }
            drawRect(c.ink, Offset(pts[0].x - 6.dp.toPx(), pts[0].y - 6.dp.toPx()), Size(12.dp.toPx(), 12.dp.toPx()))
            val me = Offset(w * 0.19f, h * 0.84f)
            drawCircle(c.action.copy(alpha = 0.3f), 11.dp.toPx(), me)
            drawCircle(c.action, 6.dp.toPx(), me)
            drawLine(c.inkMuted, me, pts.last(), 1.dp.toPx(), pathEffect = PathEffect.dashPathEffect(floatArrayOf(8f, 6f)))
            drawOval(c.predicted.copy(alpha = 0.12f), Offset(w * 0.69f, h * 0.15f), Size(w * 0.24f, h * 0.27f))
            drawOval(c.predicted, Offset(w * 0.69f, h * 0.15f), Size(w * 0.24f, h * 0.27f),
                style = Stroke(2.dp.toPx(), pathEffect = PathEffect.dashPathEffect(floatArrayOf(14f, 8f))))
            drawRect(c.ink, Offset(pts.last().x - 7.dp.toPx(), pts.last().y - 7.dp.toPx()), Size(14.dp.toPx(), 14.dp.toPx()))
        }
        Row(Modifier.fillMaxWidth().padding(10.dp), horizontalArrangement = Arrangement.spacedBy(12.dp)) {
            Text("GPS 11 sat · HDOP 0.9", style = mono(11), color = c.inkMuted, modifier = Modifier.weight(1f))
            Text("PREDICTED LANDING", style = mono(11), color = c.predicted, textAlign = TextAlign.End, modifier = Modifier.weight(1f))
        }
        Text("VEGA · 0.4 s", style = mono(11), color = c.ink, modifier = Modifier.align(Alignment.CenterEnd).padding(end = 64.dp, top = 40.dp))
        Text("TILES 2026-10-03", style = mono(11), color = c.inkMuted, modifier = Modifier.align(Alignment.BottomEnd).padding(10.dp))
    }
}

@Composable
private fun Coordinates(text: String) {
    val c = LocalFsColors.current
    val clipboard = LocalClipboard.current
    val scope = rememberCoroutineScope()
    Column {
        Box(Modifier.fillMaxWidth().height(1.dp).background(c.rule))
        Row(Modifier.fillMaxWidth().heightIn(min = 48.dp), verticalAlignment = Alignment.CenterVertically) {
            Text(text, style = mono(16), color = c.ink, modifier = Modifier.weight(1f))
            TextButton(onClick = { scope.launch { clipboard.setClipEntry(ClipEntry(ClipData.newPlainText("Coordinates", text))) } }) {
                Icon(painterResource(R.drawable.fs_copy), null, Modifier.size(20.dp))
                Spacer(Modifier.width(8.dp))
                Text("Copy")
            }
        }
    }
}
