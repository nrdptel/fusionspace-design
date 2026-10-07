// SPDX-License-Identifier: Apache-2.0 · Copyright 2026 Neer Patel
// The track screen (product/mobile.md#screens): dark; the phase, the two numbers that matter under the main, the offline
// map, then distance, bearing and the coordinates.
import SwiftUI

struct TrackScreen: View {
    @Environment(\.dynamicTypeSize) private var typeSize
    var body: some View {
        FSPaletteReader { p in
            ScrollView {
                VStack(alignment: .leading, spacing: 14) {
                    ViewThatFits(in: .horizontal) {
                        HStack(spacing: 8) { FSTag("FLIGHT 04 · \(Sample.designation)"); FSStatus("Link", signal: .ok, detail: "0.4\u{00A0}s", symbol: "fs.telemetry") }
                        VStack(alignment: .leading, spacing: 6) { FSTag("FLIGHT 04 · \(Sample.designation)"); FSStatus("Link", signal: .ok, detail: "0.4\u{00A0}s", symbol: "fs.telemetry") }
                    }
                    FSPhaseStrip(current: 5)
                    VStack(spacing: 8) {
                        FSSheetHeader("Now", number: 1, of: 2)
                        pair {
                            FSReadout("Altitude", value: "612", unit: "ft AGL", qualifier: "Barometer · 0.4\u{00A0}s ago", spokenUnit: "feet above ground level")
                                .frame(maxWidth: .infinity, alignment: .leading)
                            FSReadout("Descent", value: "18", unit: "ft/s", qualifier: "Under the main", spokenUnit: "feet per second")
                                .frame(maxWidth: .infinity, alignment: .leading)
                        }
                    }
                    RecoveryMap().frame(height: 190)
                    VStack(spacing: 8) {
                        FSSheetHeader("Find it", number: 2, of: 2)
                        pair {
                            FSReadout("Distance", value: "1,352", unit: "ft", qualifier: "From you", size: 26, spokenUnit: "feet")
                                .frame(maxWidth: .infinity, alignment: .leading)
                            FSReadout("Bearing", value: "062°", unit: "T", qualifier: "Declination 13° E", size: 26, spokenUnit: "true")
                                .frame(maxWidth: .infinity, alignment: .leading)
                        }
                    }
                }
                .padding(.horizontal, 16)
                .padding(.bottom, 16)
            }
            .background(p.canvas)
            .navigationTitle("Track")
            // The large title is the platform's, set in Cascadia Mono through the toolbar (iOS 26+). The bar's appearance
            // fonts (UINavigationBarAppearance) aren't applied to large titles on iOS 27.
            .toolbar { ToolbarItem(placement: .largeTitle) {
                Text("Track").font(FS.title()).foregroundStyle(p.ink).frame(maxWidth: .infinity, alignment: .leading)
            } }
            .toolbarBackground(p.canvas, for: .navigationBar)
        }
        .fsKeepsScreenOn()          // follows the system appearance (captured in dark)
    }

    /// Two readouts side by side, or one above the other at accessibility text sizes.
    private func pair<C: View>(@ViewBuilder _ content: () -> C) -> some View {
        let layout = typeSize.isAccessibilitySize ? AnyLayout(VStackLayout(alignment: .leading, spacing: 12)) : AnyLayout(HStackLayout(alignment: .top))
        return layout { content() }
    }
}

/// The offline map (product/data.md#maps): muted base, north up, pad square, track, rocket diamond with its age, the
/// predicted landing as a dashed ellipse, the phone as the system's location dot, a scale bar and the tiles' date.
struct RecoveryMap: View {
    var body: some View {
        FSPaletteReader { p in
            Canvas { ctx, size in
                let w = size.width, h = size.height
                ctx.fill(Path(CGRect(origin: .zero, size: size)), with: .color(p.surface))
                var grid = Path()
                for x in stride(from: -40.0, through: w + 60, by: 64) { grid.move(to: CGPoint(x: x, y: 0)); grid.addLine(to: CGPoint(x: x + 40, y: h)) }
                for y in stride(from: 18.0, through: h, by: 64) { grid.move(to: CGPoint(x: 0, y: y)); grid.addLine(to: CGPoint(x: w, y: y - 25)) }
                ctx.stroke(grid, with: .color(p.rule), lineWidth: 1)
                let pad = CGPoint(x: w * 0.25, y: h * 0.72), rocket = CGPoint(x: w * 0.68, y: h * 0.38), you = CGPoint(x: w * 0.18, y: h * 0.84)
                let landing = CGRect(x: w * 0.56, y: h * 0.06, width: w * 0.24, height: h * 0.22)
                ctx.fill(Path(ellipseIn: landing), with: .color(p.predicted.opacity(0.08)))
                ctx.stroke(Path(ellipseIn: landing), with: .color(p.predicted), style: StrokeStyle(lineWidth: 2, dash: [8, 4]))
                var track = Path(); track.move(to: pad)
                track.addQuadCurve(to: rocket, control: CGPoint(x: w * 0.36, y: h * 0.36))
                ctx.stroke(track, with: .color(p.ink), lineWidth: 2)
                var ref = Path(); ref.move(to: you); ref.addLine(to: rocket)
                ctx.stroke(ref, with: .color(p.inkMuted), style: StrokeStyle(lineWidth: 1, dash: [24, 3, 1, 3]))
                ctx.fill(Path(CGRect(x: pad.x - 6, y: pad.y - 6, width: 12, height: 12)), with: .color(p.ink))
                var diamond = Path()
                diamond.move(to: CGPoint(x: rocket.x, y: rocket.y - 9)); diamond.addLine(to: CGPoint(x: rocket.x + 9, y: rocket.y))
                diamond.addLine(to: CGPoint(x: rocket.x, y: rocket.y + 9)); diamond.addLine(to: CGPoint(x: rocket.x - 9, y: rocket.y)); diamond.closeSubpath()
                ctx.fill(diamond, with: .color(p.ink))
                ctx.fill(Path(ellipseIn: CGRect(x: you.x - 11, y: you.y - 11, width: 22, height: 22)), with: .color(p.action.opacity(0.18)))
                ctx.fill(Path(ellipseIn: CGRect(x: you.x - 6, y: you.y - 6, width: 12, height: 12)), with: .color(p.action))
                let mono = Font.custom("CascadiaMono-Regular", fixedSize: 11)   // a drawing: its labels keep their size; the map has an accessibility label
                ctx.draw(Text("VEGA · 0.4\u{00A0}s").font(mono).foregroundStyle(p.ink), at: CGPoint(x: rocket.x, y: rocket.y + 22))
                ctx.draw(Text("PAD 3").font(mono).foregroundStyle(p.inkMuted), at: CGPoint(x: pad.x + 30, y: pad.y + 4))
                ctx.draw(Text("PREDICTED").font(mono).foregroundStyle(p.predicted), at: CGPoint(x: landing.minX - 6, y: landing.midY), anchor: .trailing)
                ctx.draw(Text("GPS 11 sat · HDOP 0.9").font(mono).foregroundStyle(p.inkMuted), at: CGPoint(x: 12, y: 14), anchor: .leading)
                ctx.draw(Text("TILES 2026-10-03").font(mono).foregroundStyle(p.inkMuted), at: CGPoint(x: w - 12, y: h - 12), anchor: .trailing)
                var scale = Path(); scale.move(to: CGPoint(x: 12, y: h - 18)); scale.addLine(to: CGPoint(x: 12, y: h - 12))
                scale.addLine(to: CGPoint(x: 92, y: h - 12)); scale.addLine(to: CGPoint(x: 92, y: h - 18))
                ctx.stroke(scale, with: .color(p.ink), lineWidth: 1.5)
                ctx.draw(Text("500\u{00A0}ft").font(mono).foregroundStyle(p.inkMuted), at: CGPoint(x: 100, y: h - 14), anchor: .leading)
                var north = Path(); north.move(to: CGPoint(x: w - 22, y: 10)); north.addLine(to: CGPoint(x: w - 16, y: 26))
                north.addLine(to: CGPoint(x: w - 22, y: 22)); north.addLine(to: CGPoint(x: w - 28, y: 26)); north.closeSubpath()
                ctx.fill(north, with: .color(p.ink))
                ctx.draw(Text("N").font(mono).foregroundStyle(p.ink), at: CGPoint(x: w - 22, y: 38))
            }
            .overlay(Rectangle().strokeBorder(p.ruleStrong, lineWidth: 1))
            .accessibilityLabel("Recovery map: rocket 1,352 feet from you, bearing 62 degrees true")
        }
    }
}
