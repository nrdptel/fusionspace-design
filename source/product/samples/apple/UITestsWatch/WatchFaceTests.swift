// SPDX-License-Identifier: Apache-2.0 · Copyright 2026 Neer Patel
// The watch face in Always On, for a capture: Device Hub has no wrist-down, so this presses the lock button through
// XCUIDevice (as LockScreenTests does on the iPhone), which dims the watch, and holds it there for FS_HOLD seconds while
// `xcrun simctl io <watch> screenshot --mask=alpha` captures the face and its complications.
// Run: TEST_RUNNER_FS_HOLD=40 xcodebuild test ... -only-testing:FusionSpaceSampleWatchUITests/WatchFaceTests
import XCTest

final class WatchFaceTests: XCTestCase {
    func testAlwaysOn() throws {
        let device = XCUIDevice.shared
        let lock = NSSelectorFromString("pressLockButton")
        try XCTSkipUnless(device.responds(to: lock), "this Xcode has no lock button for UI tests")
        sleep(2)
        device.perform(lock)
        sleep(UInt32(ProcessInfo.processInfo.environment["FS_HOLD"].flatMap(UInt32.init) ?? 0))
    }

    /// The watch stays dimmed after testAlwaysOn until something raises it: the lock button again.
    func testWake() throws {
        let lock = NSSelectorFromString("pressLockButton")
        try XCTSkipUnless(XCUIDevice.shared.responds(to: lock), "this Xcode has no lock button for UI tests")
        XCUIDevice.shared.perform(lock)
        sleep(2)
    }
}
