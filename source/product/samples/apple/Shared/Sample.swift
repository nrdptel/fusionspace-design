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

/// A designation tag: a mono label in a 1 pt box with its top-right corner cut at 45°, like a drawing's tag.
struct SampleTag: View {
    let text: String
    init(_ text: String) { self.text = text }
    var body: some View {
        FSPaletteReader { p in
            Text(text)
                .font(.custom("CascadiaMono-Regular", size: 12, relativeTo: .caption))
                .padding(.leading, 8).padding(.trailing, 10).padding(.vertical, 3)
                .foregroundStyle(p.ink)
                .overlay(ChamferedRect(cut: 4).stroke(p.ruleStrong, lineWidth: 1))
        }
    }
}

struct ChamferedRect: Shape {
    let cut: CGFloat
    func path(in r: CGRect) -> Path {
        var p = Path()
        p.move(to: CGPoint(x: r.minX, y: r.minY)); p.addLine(to: CGPoint(x: r.maxX - cut, y: r.minY))
        p.addLine(to: CGPoint(x: r.maxX, y: r.minY + cut)); p.addLine(to: CGPoint(x: r.maxX, y: r.maxY))
        p.addLine(to: CGPoint(x: r.minX, y: r.maxY)); p.closeSubpath()
        return p
    }
}
