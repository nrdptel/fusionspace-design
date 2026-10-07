// SPDX-License-Identifier: Apache-2.0 · Copyright 2026 Neer Patel
// The pad screen (product/mobile.md#screens): field theme; checks and channels as sheets; fixed at the bottom where a thumb
// reaches, the device's state above Hold to arm, with SAFE, one tap, to its right.
import SwiftUI

struct PadScreen: View {
    @State private var commanded: String? = nil
    @State private var armed = false
    @State private var confirmedAt = Date.now.addingTimeInterval(-0.3)

    var body: some View {
        FSPaletteReader { p in
            ScrollView {
                VStack(alignment: .leading, spacing: 12) {
                    HStack(spacing: 8) {
                        SampleTag("\(Sample.designation) rev B")
                        FSStatus("Link", signal: .ok, detail: "0.3 s", symbol: "link")
                    }
                    VStack(alignment: .leading, spacing: 4) {
                        Text("Pad 3 · Flight 04").font(FS.title()).foregroundStyle(p.ink)
                        Text("K535W · dual deploy · screen stays on").font(FS.label()).foregroundStyle(p.inkMuted)
                    }
                    VStack(spacing: 8) {
                        FSSheetHeader("Checks", number: 1, of: 2)
                        PadRow(key: "SWITCH", value: "ON", status: FSStatus("On", signal: .ok))
                        PadRow(key: "BATTERY", value: "8.1 V", status: FSStatus("OK", signal: .ok, symbol: "battery.100"))
                        PadRow(key: "GPS", value: "3D · 11 sat", status: FSStatus("Fix", signal: .ok, symbol: "location"))
                    }
                    VStack(spacing: 8) {
                        FSSheetHeader("Channels", number: 2, of: 2)
                        PadRow(key: "1 · DROGUE", value: "Apogee + 0.4 s", status: FSStatus("Cont", signal: .ok, symbol: "waveform.path"))
                        PadRow(key: "2 · MAIN", value: "700 ft desc.", status: FSStatus("Cont", signal: .ok, symbol: "waveform.path"))
                        PadRow(key: "3 · —", value: "Not used", status: FSStatus("Not used", signal: .off), muted: true)
                    }
                }
                .padding(.horizontal, 16)
                .padding(.bottom, 16)
            }
            .safeAreaInset(edge: .bottom, spacing: 0) {
                VStack(spacing: 12) {
                    Rectangle().fill(p.ink).frame(height: 2)
                    HStack(spacing: 16) {
                        FSStateBox(armed: armed)
                        FSCommandedConfirmed(commanded: commanded, confirmed: armed ? "ARMED" : "SAFE",
                                             age: FSFreshness.age(since: confirmedAt))
                        Spacer(minLength: 0)
                    }
                    HStack(spacing: 12) {
                        FSHoldToConfirm("Hold to arm", designation: Sample.designation) {
                            commanded = "ARM"; armed = true; confirmedAt = .now
                        }
                        Button { commanded = "SAFE"; armed = false; confirmedAt = .now } label: {
                            VStack(spacing: 6) {
                                Image(systemName: "shield.lefthalf.filled").font(.title2)
                                Text("SAFE").font(.custom("CascadiaMono-SemiBold", size: 22, relativeTo: .title2))
                            }
                            .frame(width: 128, height: FS.gloveTarget)
                            .foregroundStyle(p.ink)
                            .background(p.surface)
                            .overlay(Rectangle().strokeBorder(p.ink, lineWidth: 2))
                        }
                        .buttonStyle(.plain)
                        .accessibilityLabel("Safe \(Sample.designation)")
                    }
                    Button("Arm with a confirmation instead") {}
                        .frame(minHeight: 44)
                }
                .padding(.horizontal, 16)
                .padding(.top, 12)
                .background(p.canvas)
            }
            .background(p.canvas)
            .toolbarBackground(p.canvas, for: .navigationBar)
        }
        .environment(\.fsTheme, .field)
        .fsKeepsScreenOn()
    }
}

/// A label / value / state row in the content layer's own table.
struct PadRow: View {
    let key: String, value: String, status: FSStatus
    var muted = false
    var body: some View {
        FSPaletteReader { p in
            VStack(spacing: 0) {
                HStack(spacing: 8) {
                    Text(key).font(FS.label()).tracking(0.7).foregroundStyle(p.inkMuted).frame(width: 104, alignment: .leading)
                    Text(value).font(FS.readout(15, relativeTo: .body)).foregroundStyle(muted ? p.inkMuted : p.ink)
                        .lineLimit(1).minimumScaleFactor(0.8)
                    Spacer(minLength: 4)
                    status
                }
                .frame(minHeight: 36)
                Rectangle().fill(p.rule).frame(height: 1)
            }
        }
    }
}
