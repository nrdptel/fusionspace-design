// SPDX-License-Identifier: Apache-2.0 · Copyright 2026 Neer Patel
// Apple's accessibility audit on the watch sample's screens: clipped text, contrast, hit regions, labels, Dynamic Type.
// Run: xcodebuild test -project FusionSpaceSample.xcodeproj -scheme FusionSpaceSampleWatchUITests -destination '...'
import XCTest

final class WatchAccessibilityAuditTests: XCTestCase {
    override func setUp() { continueAfterFailure = true }

    private func audit(_ screen: String, typesize: String? = nil, file: StaticString = #filePath, line: UInt = #line) throws {
        let app = XCUIApplication()
        app.launchArguments += ["-screen", screen] + (typesize.map { ["-typesize", $0] } ?? [])
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
            XCTFail("[\(screen)\(typesize.map { " @\($0)" } ?? "")] \(issue.compactDescription) — \(what) — \(issue.detailedDescription) — frame \(issue.element?.frame ?? .zero)", file: file, line: line)
            return true
        }
    }

    func testFind() throws { try audit("find") }
    func testPad() throws { try audit("pad") }
    func testUnfired() throws { try audit("unfired") }

    /// The same audit at the sizes a watch really reaches: the largest standard size, and the watch's own largest Text Size,
    /// which is ax1 on a 40 mm case and ax3 on the 49 mm Ultra (measured in Settings › Display & Brightness › Text Size).
    /// The audit does not see a line cut short with "…" (it passed with Unfired's title cut to "UNFIRED 2 ·…"): the
    /// captures are read back with text recognition for that (tools/build/kit_clip.py, check_captures).
    func testLargeText() throws {
        for size in ["xxxl", "ax1", "ax3"] {
            for screen in ["find", "pad", "unfired"] { try audit(screen, typesize: size) }
        }
    }
}
