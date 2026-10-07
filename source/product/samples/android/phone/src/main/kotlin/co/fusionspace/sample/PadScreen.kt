// SPDX-License-Identifier: Apache-2.0 · Copyright 2026 Neer Patel
// The pad screen (product/mobile.md#screens, product/mobile/screens/android-pad.png): field theme; checks and channels as
// sheets; at the bottom where a thumb reaches, the device's state above Hold to arm, with SAFE, one tap, to its right (or
// below it, when the text is too large for both side by side), and the accessible alternative under them.
package co.fusionspace.sample

import android.widget.Toast
import androidx.annotation.DrawableRes
import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.BoxWithConstraints
import androidx.compose.foundation.layout.ExperimentalLayoutApi
import androidx.compose.foundation.layout.FlowRow
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.IntrinsicSize
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.consumeWindowInsets
import androidx.compose.foundation.layout.fillMaxHeight
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.heightIn
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.layout.widthIn
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
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.platform.LocalDensity
import androidx.compose.ui.res.painterResource
import androidx.compose.ui.semantics.Role
import androidx.compose.ui.semantics.semantics
import androidx.compose.ui.text.TextStyle
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.em
import androidx.compose.ui.unit.sp
import co.fusionspace.design.FS_GLOVE_TARGET_DP
import co.fusionspace.design.FsArmConfirmation
import co.fusionspace.design.FsCommandedConfirmed
import co.fusionspace.design.FsFirstThatFits
import co.fusionspace.design.FsHoldToConfirm
import co.fusionspace.design.FsSheetHeader
import co.fusionspace.design.FsSignal
import co.fusionspace.design.FsStateBox
import co.fusionspace.design.FsStatus
import co.fusionspace.design.FsTag
import co.fusionspace.design.LocalFsColors
import co.fusionspace.design.LocalFsMono

@OptIn(ExperimentalMaterial3Api::class, ExperimentalLayoutApi::class)
@Composable
fun PadScreen(onBack: () -> Unit) {
    val c = LocalFsColors.current
    val context = LocalContext.current
    var armed by remember { mutableStateOf(false) }
    var confirming by remember { mutableStateOf(false) }
    val large = LocalDensity.current.fontScale >= 1.5f
    val arm = { armed = true; Toast.makeText(context, "Sample: ARM would be sent to FS-VEGA-004", Toast.LENGTH_SHORT).show() }
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
        // One scrolling column at least as tall as the screen, at every text size: the state and the controls sit at the
        // bottom where a thumb reaches, and when large text makes it all too tall, they scroll with everything else instead
        // of a fixed panel cutting rows off above them.
        BoxWithConstraints(Modifier.fillMaxSize().padding(padding).consumeWindowInsets(padding)) {
          Column(Modifier.fillMaxWidth().verticalScroll(rememberScrollState()).heightIn(min = maxHeight)) {
            Column(Modifier.padding(horizontal = 16.dp), verticalArrangement = Arrangement.spacedBy(4.dp)) {
                FlowRow(horizontalArrangement = Arrangement.spacedBy(8.dp), verticalArrangement = Arrangement.spacedBy(8.dp), itemVerticalAlignment = Alignment.CenterVertically) {
                    FsTag("FS-VEGA-004 rev B")
                    FsStatus("Link", FsSignal.Ok, detail = "0.3\u00A0s", icon = { StatusIcon(R.drawable.fs_link) })
                }
                Text("Pad 3 · Flight 04", style = MaterialTheme.typography.headlineMedium, color = c.ink)
                Text("K535W · dual deploy · screen stays on", style = mono(14), color = c.inkMuted)
                Spacer(Modifier.height(12.dp))
                FsSheetHeader("Checks", 1, 2)
                Line("Switch", "ON") { FsStatus("On", FsSignal.Ok, icon = { StatusIcon(R.drawable.fs_check) }) }
                Line("Battery", "8.1\u00A0V") { FsStatus("OK", FsSignal.Ok, icon = { StatusIcon(R.drawable.fs_battery) }) }
                Line("GPS", "3D · 11\u00A0sat") { FsStatus("Fix", FsSignal.Ok, icon = { StatusIcon(R.drawable.fs_gps_fix) }) }
                Spacer(Modifier.height(12.dp))
                FsSheetHeader("Channels", 2, 2)
                Line("1 · Drogue", "Apogee +\u00A00.4\u00A0s") { FsStatus("Cont", FsSignal.Ok, icon = { StatusIcon(R.drawable.fs_continuity) }) }
                Line("2 · Main", "700\u00A0ft desc.") { FsStatus("Cont", FsSignal.Ok, icon = { StatusIcon(R.drawable.fs_continuity) }) }
                Line("3 · —", "Not used") { FsStatus("Not used", FsSignal.Off, icon = { StatusIcon(R.drawable.fs_minus) }) }
                Spacer(Modifier.height(12.dp))
            }
            Spacer(Modifier.weight(1f))
            Column(Modifier.padding(horizontal = 16.dp), verticalArrangement = Arrangement.spacedBy(12.dp)) {
                Box(Modifier.fillMaxWidth().height(2.dp).background(c.ink))
                FlowRow(itemVerticalAlignment = Alignment.CenterVertically, horizontalArrangement = Arrangement.spacedBy(16.dp),
                    verticalArrangement = Arrangement.spacedBy(8.dp)) {
                    FsStateBox(armed)
                    FsCommandedConfirmed(commanded = if (armed) "ARM" else null, confirmed = "SAFE", age = "0.3\u00A0s ago")
                }
                // SAFE is right of Hold to arm, or below it from a large text size (150%) up, or whenever both don't fit
                // side by side (product/embedded.md: SAFE is right of or below ARM).
                val below = @Composable {
                    Column(verticalArrangement = Arrangement.spacedBy(12.dp)) {
                        FsHoldToConfirm("Hold to arm", "FS-VEGA-004", onConfirmed = arm)
                        SafeButton(onClick = { armed = false }, modifier = Modifier.fillMaxWidth())
                    }
                }
                if (large) below() else FsFirstThatFits {
                    Row(Modifier.height(IntrinsicSize.Min), horizontalArrangement = Arrangement.spacedBy(12.dp)) {
                        FsHoldToConfirm("Hold to arm", "FS-VEGA-004", onConfirmed = arm, modifier = Modifier.weight(1f))
                        SafeButton(onClick = { armed = false }, modifier = Modifier.width(128.dp).fillMaxHeight())
                    }
                    below()
                }
            }
            TextButton(onClick = { confirming = true }, modifier = Modifier.align(Alignment.CenterHorizontally).padding(vertical = 4.dp)) {
                Text("Arm with a confirmation instead", textAlign = TextAlign.Center)
            }
          }
        }
    }
    if (confirming) FsArmConfirmation("Arm", "FS-VEGA-004", onConfirmed = { confirming = false; arm() }, onDismiss = { confirming = false })
}

@Composable
private fun mono(size: Int, weight: FontWeight = FontWeight.Normal) =
    TextStyle(fontFamily = LocalFsMono.current, fontSize = size.sp, fontWeight = weight, letterSpacing = 0.02.em)

/** A FusionSpace icon from product/icons/android, in the status chip's own foreground color. */
@Composable
fun StatusIcon(@DrawableRes id: Int) = Icon(painterResource(id), null, Modifier.size(16.dp))

@Composable
private fun Line(label: String, value: String, status: @Composable () -> Unit) {
    val c = LocalFsColors.current
    val key = @Composable { m: Modifier -> Text(label.uppercase(), style = mono(12).copy(letterSpacing = 0.06.em), color = c.inkMuted, modifier = m) }
    Column {
        // One line while the label, the value and the state all fit; with larger text, the label above the value and the
        // state, so nothing wraps mid-phrase or breaks mid-word.
        FsFirstThatFits(Modifier.semantics(mergeDescendants = true) {}) {
            Row(Modifier.fillMaxWidth().heightIn(min = 40.dp), verticalAlignment = Alignment.CenterVertically) {
                key(Modifier.widthIn(min = 120.dp).padding(end = 8.dp))
                Text(value, style = mono(15), color = c.ink, modifier = Modifier.weight(1f).padding(vertical = 6.dp))
                status()
            }
            Column(Modifier.fillMaxWidth().padding(vertical = 8.dp), verticalArrangement = Arrangement.spacedBy(4.dp)) {
                key(Modifier)
                Text(value, style = mono(15), color = c.ink)
                status()
            }
        }
        Box(Modifier.fillMaxWidth().height(1.dp).background(c.rule))
    }
}

/** SAFE: one tap, as large as Hold to arm. A touchscreen is never the only way to safe a channel; the switch is. */
@Composable
private fun SafeButton(onClick: () -> Unit, modifier: Modifier = Modifier) {
    val c = LocalFsColors.current
    Column(
        modifier.heightIn(min = FS_GLOVE_TARGET_DP.dp).background(c.surface).border(2.dp, c.ink)
            .clickable(role = Role.Button, onClickLabel = "Safe FS-VEGA-004", onClick = onClick),
        horizontalAlignment = Alignment.CenterHorizontally, verticalArrangement = Arrangement.Center,
    ) {
        Icon(painterResource(R.drawable.fs_safe), null, Modifier.size(28.dp), tint = c.ink)
        Text("SAFE", style = mono(22, FontWeight.SemiBold), color = c.ink)
    }
}
