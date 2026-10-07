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
                    .init(1, "DROGUE", .ok, "Cont", spoken: "Continuity"), .init(2, "MAIN", .ok, "Cont", spoken: "Continuity"),
                    .init(3, "—", .off, "Not used"),
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

/// Follows the watch's own text size, unless `-typesize` names one to capture: xs, s, m, l, xl, xxl, xxxl, ax1 … ax5.
/// The watch's own largest Text Size (Settings › Display & Brightness, 100%) renders as ax1; see the README.
struct SampleTypeSize: ViewModifier {
    static let sizes: [String: DynamicTypeSize] = [
        "xs": .xSmall, "s": .small, "m": .medium, "l": .large, "xl": .xLarge, "xxl": .xxLarge, "xxxl": .xxxLarge,
        "ax1": .accessibility1, "ax2": .accessibility2, "ax3": .accessibility3, "ax4": .accessibility4, "ax5": .accessibility5,
    ]
    func body(content: Content) -> some View {
        if let s = UserDefaults.standard.string(forKey: "typesize").flatMap({ Self.sizes[$0] }) {
            content.dynamicTypeSize(s)
        } else {
            content
        }
    }
}
