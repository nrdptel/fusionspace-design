// SPDX-License-Identifier: Apache-2.0 · Copyright 2026 Neer Patel
// For screenshots only. simctl draws 9:41 in the status bar and on the Lock Screen, but the widgets and the Live Activity
// format times from the real clock ("measured 6:03 AM", "your pad time, 11:15 PM"), which then disagree with it. Built with
// FS_CAPTURE_CLOCK=9:41 (an Info.plist key), a process moves its own time zone so that now reads 9:41 when it starts.
// Only the time zone changes: ages, countdowns and durations are untouched. Without the setting this does nothing.
// iPhone only: watchOS has no status bar override, so a watch keeps its real clock and the app and complications agree with it.
import Foundation

enum CaptureClock {
    static func apply() {
        guard let s = Bundle.main.object(forInfoDictionaryKey: "FSCaptureClock") as? String,
              case let hm = s.split(separator: ":").compactMap({ Int($0) }), hm.count == 2 else { return }
        var utc = Calendar(identifier: .gregorian); utc.timeZone = TimeZone(identifier: "UTC")!
        let now = utc.dateComponents([.hour, .minute], from: .now)
        var offset = hm[0] * 60 + hm[1] - (now.hour! * 60 + now.minute!)
        if offset > 720 { offset -= 1440 } else if offset < -720 { offset += 1440 }
        setenv("TZ", String(format: "GMT%@%02d%02d", offset < 0 ? "-" : "+", abs(offset) / 60, abs(offset) % 60), 1)
        NSTimeZone.resetSystemTimeZone()
    }
}
