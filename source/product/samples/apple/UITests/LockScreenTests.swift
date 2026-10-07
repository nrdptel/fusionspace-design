// SPDX-License-Identifier: Apache-2.0 · Copyright 2026 Neer Patel
// The flight's Live Activity on the Lock Screen, where only a locked device shows it. The simulator has no lock button
// without Simulator.app, so this presses it through XCUIDevice, keeps the device locked for a while (capture it with
// `xcrun simctl io <iphone> screenshot --mask=alpha`), and attaches its own screenshot to the test result.
// Run: xcodebuild test ... -only-testing:FusionSpaceSampleUITests/LockScreenTests
import XCTest

final class LockScreenTests: XCTestCase {
    private func lockScreen(_ activity: String) throws {
        let app = XCUIApplication()
        app.launchArguments += ["-screen", "pad", "-activity", activity]
        app.launch()
        sleep(4)                                                           // the activity starts in the app's first task
        let device = XCUIDevice.shared
        let lock = NSSelectorFromString("pressLockButton")
        try XCTSkipUnless(device.responds(to: lock), "this Xcode has no lock button for UI tests")
        device.perform(lock)
        sleep(2)
        device.perform(lock)                                               // wake the screen: the Lock Screen, still locked
        sleep(3)
        // iOS asks on the Lock Screen itself, first "Allow Live Activities from FusionSpace?", later "Do you want to
        // continue to allow…?": allow, and the card is left alone
        let springboard = XCUIApplication(bundleIdentifier: "com.apple.springboard")
        for _ in 0..<2 {
            guard let b = ["Always Allow", "Allow"].lazy.map({ springboard.buttons[$0] }).first(where: { $0.waitForExistence(timeout: 2) })
            else { break }
            b.tap(); sleep(3)
        }
        let shot = XCTAttachment(screenshot: XCUIScreen.main.screenshot())
        shot.name = "lock-screen-\(activity)"; shot.lifetime = .keepAlways
        add(shot)
        sleep(UInt32(ProcessInfo.processInfo.environment["FS_HOLD"].flatMap(UInt32.init) ?? 0))
    }

    func testFlight() throws { try lockScreen("flight") }
    func testPad() throws { try lockScreen("pad") }
}
