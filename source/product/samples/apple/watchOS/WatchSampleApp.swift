// SPDX-License-Identifier: Apache-2.0 · Copyright 2026 Neer Patel
// FusionSpace sample app for Apple Watch: Find, Pad and Unfired from product/watch/swiftui/FSWatch.swift. Open a screen
// directly with `-screen find`, `-screen find-aod` (Always On, forced for the capture), `-screen pad` or `-screen unfired`.
import SwiftUI

@main
struct FusionSpaceWatchSampleApp: App {
    var body: some Scene {
        WindowGroup {
            // `-typesize ax3` renders at an accessibility text size (simctl can't set the watch's text size)
            WatchRoot().tint(FS.darkPalette.action).modifier(SampleTypeSize())
        }
    }
}

struct WatchRoot: View {
    var body: some View {
        switch Sample.screen {
        case "pad":
            NavigationStack {
                FSWatchState(designation: Sample.designation, armed: true, channels: [
                    .init(1, "DROGUE", .ok, "Cont"), .init(2, "MAIN", .ok, "Cont"), .init(3, "—", .off, "Not used"),
                ], linkAge: "0.3\u{00A0}s")
                .navigationTitle("Pad 3")
            }
        case "unfired":
            FSWatchUnfired(channel: "2 · MAIN") {}
        case "find-aod":
            find.environment(\.isLuminanceReduced, true)
        default:
            find
        }
    }

    private var find: some View {
        NavigationStack {
            FSWatchFind(distanceFt: Sample.distanceFt, bearingTrue: Sample.bearingTrue, headingTrue: Sample.headingTrue,
                        fixedAt: Sample.fixedAt) {}
        }
    }
}

/// Follows the watch's own text size, unless `-typesize ax3` (or `xxxl`) asks for one to capture.
struct SampleTypeSize: ViewModifier {
    func body(content: Content) -> some View {
        switch UserDefaults.standard.string(forKey: "typesize") {
        case "ax3": content.dynamicTypeSize(.accessibility3)
        case "xxxl": content.dynamicTypeSize(.xxxLarge)
        default: content
        }
    }
}
