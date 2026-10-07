// SPDX-License-Identifier: Apache-2.0 · Copyright 2026 Neer Patel
// The sample phone app: a list of the reference screens, each built from product/mobile/compose. Debug: open one directly
// with `adb shell am start -n co.fusionspace.sample/.MainActivity --es screen pad|track|live` ("live" posts the Live Update).
package co.fusionspace.sample

import android.app.Activity
import android.content.Intent
import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.BackHandler
import androidx.activity.compose.setContent
import androidx.activity.enableEdgeToEdge
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.padding
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.ListItem
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Text
import androidx.compose.material3.TopAppBar
import androidx.compose.runtime.Composable
import androidx.compose.runtime.SideEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.setValue
import androidx.compose.foundation.clickable
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalView
import androidx.compose.ui.text.font.Font
import androidx.compose.ui.text.font.FontFamily
import androidx.compose.ui.text.font.FontWeight
import androidx.core.view.WindowCompat
import co.fusionspace.design.FsTheme
import co.fusionspace.design.FusionSpaceTheme

/** Cascadia Mono, bundled from type/fonts by the build (see the root build.gradle.kts). */
val CascadiaMono = FontFamily(
    Font(R.font.cascadia_mono_regular, FontWeight.Normal),
    Font(R.font.cascadia_mono_semibold, FontWeight.SemiBold),
)

enum class Screen { Home, Pad, Track }

class MainActivity : ComponentActivity() {
    private var screen by mutableStateOf(Screen.Home)

    override fun onCreate(savedInstanceState: Bundle?) {
        enableEdgeToEdge()
        super.onCreate(savedInstanceState)
        open(intent)
        setContent {
            when (screen) {
                Screen.Home -> FusionSpaceTheme(FsTheme.Light, mono = CascadiaMono) {
                    SystemBars(dark = false)
                    Home(onOpen = { screen = it }, onLive = { postLiveUpdate(this) })
                }
                Screen.Pad -> FusionSpaceTheme(FsTheme.Field, mono = CascadiaMono) {
                    SystemBars(dark = false)
                    BackHandler { screen = Screen.Home }
                    PadScreen(onBack = { screen = Screen.Home })
                }
                Screen.Track -> FusionSpaceTheme(FsTheme.Dark, mono = CascadiaMono) {
                    SystemBars(dark = true)
                    BackHandler { screen = Screen.Home }
                    TrackScreen(onBack = { screen = Screen.Home })
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
            "pad" -> screen = Screen.Pad
            "track" -> screen = Screen.Track
            "live" -> { postLiveUpdate(this); screen = Screen.Track }
        }
    }
}

/** Light or dark status- and navigation-bar icons for the screen's own theme (not the system's), drawn edge to edge. */
@Composable
private fun SystemBars(dark: Boolean) {
    val view = LocalView.current
    SideEffect {
        val window = (view.context as Activity).window
        WindowCompat.getInsetsController(window, view).apply {
            isAppearanceLightStatusBars = !dark
            isAppearanceLightNavigationBars = !dark
        }
    }
}

@OptIn(ExperimentalMaterial3Api::class)
@Composable
private fun Home(onOpen: (Screen) -> Unit, onLive: () -> Unit) {
    Scaffold(topBar = { TopAppBar(title = { Text("FusionSpace Sample") }) }) { padding ->
        Column(Modifier.padding(padding)) {
            ListItem(headlineContent = { Text("Pad") }, supportingContent = { Text("Field theme: checks, channels, hold to arm") },
                modifier = Modifier.clickable { onOpen(Screen.Pad) })
            ListItem(headlineContent = { Text("Track") }, supportingContent = { Text("Dark: phase, readouts, map, find it") },
                modifier = Modifier.clickable { onOpen(Screen.Track) })
            ListItem(headlineContent = { Text("Post the Live Update") }, supportingContent = { Text("FsLiveUpdate: Flight 04 under the main") },
                modifier = Modifier.clickable { onLive() })
        }
    }
}
