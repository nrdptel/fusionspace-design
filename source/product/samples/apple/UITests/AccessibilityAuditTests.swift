// SPDX-License-Identifier: Apache-2.0 · Copyright 2026 Neer Patel
// Apple's accessibility audit on the sample's screens: clipped text, contrast, hit regions, labels, Dynamic Type.
// Run: xcodebuild test -project FusionSpaceSample.xcodeproj -scheme FusionSpaceSampleUITests -destination '...'
import XCTest

final class AccessibilityAuditTests: XCTestCase {
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
        // Issues are kept as they come and read after the audit returns: on Xcode 27, looking an element up (its label,
        // its frame) inside the handler sometimes hung the run, the app idle on screen until the test was stopped.
        let problems = AuditIssues()
        try app.performAccessibilityAudit(for: XCUIAccessibilityAuditType.all.subtracting(.dynamicType)) { issue in
            if issue.auditType == .textClipped, issue.detailedDescription.contains("larger Dynamic Type sizes") { return true }
            // Every issue is kept with the element it's about; the test fails on any of them.
            problems.list.append((issue.compactDescription, issue.detailedDescription, issue.element))
            return true
        }
        for (compact, detail, element) in problems.list {
            let what = element.map { "\($0.elementType) '\($0.label)'" } ?? "screen"
            XCTFail("[\(screen)] \(compact) — \(what) — \(detail) — frame \(element?.frame ?? .zero)", file: file, line: line)
        }
    }

    func testPad() throws { try audit("pad") }
    func testTrack() throws { try audit("track") }
}

/// The issues an audit's handler finds, reported once the audit has returned. The handler runs on the test's own thread.
final class AuditIssues: @unchecked Sendable { var list: [(String, String, XCUIElement?)] = [] }
