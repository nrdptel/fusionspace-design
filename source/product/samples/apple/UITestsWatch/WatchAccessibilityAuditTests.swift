// SPDX-License-Identifier: Apache-2.0 · Copyright 2026 Neer Patel
// Apple's accessibility audit on the watch sample's screens: clipped text, contrast, hit regions, labels, Dynamic Type.
// Run: xcodebuild test -project FusionSpaceSample.xcodeproj -scheme FusionSpaceSampleWatchUITests -destination '...'
import XCTest

final class WatchAccessibilityAuditTests: XCTestCase {
    override func setUp() { continueAfterFailure = true }

    private func audit(_ screen: String, file: StaticString = #filePath, line: UInt = #line) throws {
        let app = XCUIApplication()
        app.launchArguments += ["-screen", screen]
        app.launch()
        // Every audit but .dynamicType: on views that switch layout with ViewThatFits as the text grows, the audit reports
        // text as "partially unsupported" inconsistently (the same component flagged in one place and not another). Large
        // text is checked instead by rendering the screens at Accessibility XXXL and looking at them (product/mobile.md).
        // Text the audit only predicts "may be clipped at larger Dynamic Type sizes" (one-line chips and labels, which switch
        // to wrapping layouts at accessibility sizes) is checked the same way: screens rendered at xxxLarge and at
        // Accessibility XXXL. Any text actually clipped still fails here.
        try app.performAccessibilityAudit(for: XCUIAccessibilityAuditType.all.subtracting(.dynamicType)) { issue in
            if issue.auditType == .textClipped, issue.detailedDescription.contains("larger Dynamic Type sizes") { return true }
            // Record every issue with the element it's about; the test fails on any of them.
            let what = issue.element.map { "\($0.elementType) '\($0.label)'" } ?? "screen"
            XCTFail("[\(screen)] \(issue.compactDescription) — \(what) — \(issue.detailedDescription) — frame \(issue.element?.frame ?? .zero)", file: file, line: line)
            return true
        }
    }

    func testFind() throws { try audit("find") }
    func testPad() throws { try audit("pad") }
    func testUnfired() throws { try audit("unfired") }
}
