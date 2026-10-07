// SPDX-License-Identifier: Apache-2.0 · Copyright 2026 Neer Patel
// FusionSpace sample app for Apple Watch: Find, Pad and Unfired from product/watch/swiftui/FSWatch.swift. Open a screen
// directly with `-screen find`, `-screen find-aod` (Always On, forced for the capture), `-screen pad` or `-screen unfired`.
import SwiftUI

@main
struct FusionSpaceWatchSampleApp: App {
    var body: some Scene {
        WindowGroup { WatchRoot().tint(FS.darkPalette.action) }
    }
}

struct WatchRoot: View {
    var body: some View {
        switch Sample.screen {
        case "pad":
            NavigationStack {
                FSWatchState(designation: Sample.designation, armed: true, channels: [
                    .init(1, "DROGUE", .ok, "Cont"), .init(2, "MAIN", .ok, "Cont"), .init(3, "—", .off, "Not used"),
                ], linkAge: "0.3 s")
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
