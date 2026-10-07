// SPDX-License-Identifier: Apache-2.0 · Copyright 2026 Neer Patel
// FusionSpace sample app for iPhone: the Pad and Track reference screens built from product/mobile/swiftui/FSComponents.swift,
// inside the system's own navigation and tab bar. Open a screen directly with `-screen pad` or `-screen track`.
import SwiftUI

@main
struct FusionSpaceSampleApp: App {
    var body: some Scene {
        WindowGroup { SampleRoot().task { await SampleActivity.startIfAsked() } }
    }
}

struct SampleRoot: View {
    enum TabID: Hashable { case pad, track, flights, devices }
    @State private var tab: TabID = Sample.screen == "track" ? .track : .pad
    @State private var padPath: [String] = Sample.screen == "pad" ? ["pad"] : []

    var body: some View {
        TabView(selection: $tab) {
            Tab("Pad", systemImage: "flag.pattern.checkered", value: .pad) {
                NavigationStack(path: $padPath) {
                    FlightsList(open: { padPath.append("pad") })
                        .navigationDestination(for: String.self) { _ in PadScreen().toolbar(.hidden, for: .tabBar) }
                }
            }
            Tab("Track", systemImage: "scope", value: .track) {
                NavigationStack { TrackScreen() }
            }
            Tab("Flights", systemImage: "chart.xyaxis.line", value: .flights) {
                NavigationStack { Text("Flights").navigationTitle("Flights") }
            }
            Tab("Devices", systemImage: "cpu", value: .devices) {
                NavigationStack { Text("Devices").navigationTitle("Devices") }
            }
        }
        .tint(FS.action)
    }
}

/// The list the pad screen is pushed from, so the pad screen has the system's back button.
struct FlightsList: View {
    let open: () -> Void
    var body: some View {
        List {
            Button(action: open) { LabeledContent("Pad 3 · Flight 04", value: "K535W") }
        }
        .navigationTitle("Flights")
    }
}
