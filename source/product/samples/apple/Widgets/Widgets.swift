// SPDX-License-Identifier: Apache-2.0 · Copyright 2026 Neer Patel
// The iPhone widget extension: the flight's Live Activity (FSFlightActivity.swift) and Window's wind widget (FSWindWidget.swift).
import SwiftUI
import WidgetKit

@main
struct FusionSpaceWidgets: WidgetBundle {
    init() { CaptureClock.apply() }

    var body: some Widget {
        FSWindWidget()
        FSFlightActivity()
    }
}
