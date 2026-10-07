// SPDX-License-Identifier: Apache-2.0 · Copyright 2026 Neer Patel
// Starts the example flight's Live Activity (`-activity flight` or `-activity pad`), so the Dynamic Island and the Lock
// Screen can be captured; `-activity end` ends it (a Home Screen capture without the island).
import ActivityKit
import Foundation

enum SampleActivity {
    @MainActor static func startIfAsked() async {
        guard let kind = UserDefaults.standard.string(forKey: "activity") else { return }
        if kind == "end" {
            for a in Activity<FSFlightAttributes>.activities { await a.end(nil, dismissalPolicy: .immediate) }
            return
        }
        let attributes = FSFlightAttributes(flight: "FLIGHT 04", designation: Sample.designation, motor: "K535W")
        let state: FSFlightAttributes.ContentState
        if kind == "pad" {
            state = .init(phase: .pad, armed: false, altitudeFt: nil, verticalFtS: nil, distanceFt: nil, bearingTrue: nil,
                          padTime: .now.addingTimeInterval(285), liftoff: nil, sampledAt: .now)
        } else {
            state = .init(phase: .main, armed: false, altitudeFt: 612, verticalFtS: -18, distanceFt: 1352, bearingTrue: 62,
                          padTime: nil, liftoff: .now.addingTimeInterval(-62), sampledAt: .now)
        }
        for a in Activity<FSFlightAttributes>.activities { await a.end(nil, dismissalPolicy: .immediate) }
        _ = try? Activity.request(attributes: attributes, content: .init(state: state, staleDate: .now.addingTimeInterval(120)))
    }
}
