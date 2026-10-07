// SPDX-License-Identifier: Apache-2.0 · Copyright 2026 Neer Patel
// Example values shared by the sample apps, the same as the mock-ups in product/mobile/ and product/watch/.
import SwiftUI

enum Sample {
    static let designation = "FS-VEGA-004"
    static let distanceFt = 1352
    static let bearingTrue = 62.0
    static let headingTrue = 20.0
    static var fixedAt: Date { .now.addingTimeInterval(-4) }

    /// Which screen to open, from the launch arguments (`-screen pad`), so each one can be captured directly.
    static var screen: String { UserDefaults.standard.string(forKey: "screen") ?? "" }
}
