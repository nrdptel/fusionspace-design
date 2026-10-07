// SPDX-License-Identifier: Apache-2.0 · Copyright 2026 Neer Patel
// The pad screen (product/mobile.md#screens): field theme; checks and channels as sheets; fixed at the bottom where a thumb
// reaches, the device's state above Hold to arm, with SAFE, one tap, to its right.
import SwiftUI

struct PadScreen: View {
    @Environment(\.dynamicTypeSize) private var typeSize
    /// From xxxLarge up the controls scroll with everything else, and SAFE goes under Hold to arm: a fixed panel that
    /// takes half the screen leaves too little for the checks above it.
    private var inline: Bool { typeSize >= .xxxLarge }
    @State private var commanded: String? = nil
    @State private var armed = false
    @State private var confirmedAt = Date.now.addingTimeInterval(-0.3)
    @State private var confirmingArm = false

    var body: some View {
        FSPaletteReader { p in
            ScrollView {
                VStack(alignment: .leading, spacing: 12) {
                    ViewThatFits(in: .horizontal) {
                        HStack(spacing: 8) { FSTag("\(Sample.designation) rev B"); FSStatus("Link", signal: .ok, detail: "0.3\u{00A0}s", symbol: "fs.link") }
                        VStack(alignment: .leading, spacing: 6) { FSTag("\(Sample.designation) rev B"); FSStatus("Link", signal: .ok, detail: "0.3\u{00A0}s", symbol: "fs.link") }
                    }
                    VStack(alignment: .leading, spacing: 4) {
                        Text("Pad 3 · Flight 04").font(FS.title()).foregroundStyle(p.ink).accessibilityAddTraits(.isHeader)
                        Text("K535W · dual deploy · screen stays on").font(FS.label()).foregroundStyle(p.inkMuted)
                    }
                    VStack(spacing: 8) {
                        FSSheetHeader("Checks", number: 1, of: 2)
                        PadRow(key: "SWITCH", value: "ON", status: FSStatus("On", signal: .ok))
                        PadRow(key: "BATTERY", value: "8.1\u{00A0}V", status: FSStatus("OK", signal: .ok, symbol: "fs.battery"))
                        PadRow(key: "GPS", value: "3D · 11 sat", status: FSStatus("Fix", signal: .ok, symbol: "fs.gps-fix"))
                    }
                    VStack(spacing: 8) {
                        FSSheetHeader("Channels", number: 2, of: 2)
                        PadRow(key: "1 · DROGUE", value: "Apogee + 0.4\u{00A0}s", status: FSStatus("Cont", signal: .ok, symbol: "fs.continuity", spoken: "Continuity"))
                        PadRow(key: "2 · MAIN", value: "700\u{00A0}ft desc.", status: FSStatus("Cont", signal: .ok, symbol: "fs.continuity", spoken: "Continuity"))
                        PadRow(key: "3 · —", value: "Not used", status: FSStatus("Not used", signal: .off), muted: true)
                    }
                    // Large text: the controls scroll with everything else instead of a fixed panel that would leave no room.
                    if inline { controls(p) }
                }
                .padding(.horizontal, 16)
                .padding(.bottom, 16)
            }
            .safeAreaInset(edge: .bottom, spacing: 0) {
                if !inline { controls(p).padding(.horizontal, 16).padding(.top, 12).background(p.canvas) }
            }
            .background(p.canvas)
            .toolbarBackground(p.canvas, for: .navigationBar)
        }
        .environment(\.fsTheme, .field)
        .fsKeepsScreenOn()
    }

    /// The device's state above the two controls that change it. SAFE sits right of Hold to arm, or below it when the
    /// text is too large for both side by side (product/embedded.md: SAFE is right of or below ARM).
    private func controls(_ p: FSPalette) -> some View {
                VStack(alignment: .leading, spacing: 12) {
                    Rectangle().fill(p.ink).frame(height: 2)
                    let stateLayout = inline ? AnyLayout(VStackLayout(alignment: .leading, spacing: 8)) : AnyLayout(HStackLayout(spacing: 16))
                    stateLayout {
                        FSStateBox(armed: armed)
                        FSCommandedConfirmed(commanded: commanded, confirmed: armed ? "ARMED" : "SAFE",
                                             age: FSFreshness.age(since: confirmedAt))
                        Spacer(minLength: 0)
                    }
                    let layout = inline ? AnyLayout(VStackLayout(spacing: 12)) : AnyLayout(HStackLayout(spacing: 12))
                    layout {
                        FSHoldToConfirm("Hold to arm", designation: Sample.designation) {
                            commanded = "ARM"; armed = true; confirmedAt = .now
                        }
                        Button { commanded = "SAFE"; armed = false; confirmedAt = .now } label: {
                            VStack(spacing: 6) {
                                Image(systemName: "shield.lefthalf.filled").font(.title2)
                                Text("SAFE").font(.custom("CascadiaMono-SemiBold", size: 22, relativeTo: .title2))
                            }
                            .frame(maxWidth: inline ? .infinity : 128, minHeight: FS.gloveTarget)
                            .frame(width: inline ? nil : 128)
                            .foregroundStyle(p.ink)
                            .background(p.surface)
                            .overlay(Rectangle().strokeBorder(p.ink, lineWidth: 2))
                        }
                        .buttonStyle(.plain)
                        .accessibilityLabel("Safe \(Sample.designation)")
                    }
                    // the two-step alternative to holding: the whole 44 pt row is the target, not just the words
                    Button { confirmingArm = true } label: {
                        Text("Arm with a confirmation instead").multilineTextAlignment(.center)
                            .frame(maxWidth: .infinity, minHeight: 44).contentShape(Rectangle())
                    }
                    .fsArmConfirmation(isPresented: $confirmingArm, designation: Sample.designation) {
                        commanded = "ARM"; armed = true; confirmedAt = .now
                    }
                }
    }
}

/// A label / value / state row in the content layer's own table.
struct PadRow: View {
    let key: String, value: String, status: FSStatus
    var muted = false
    var body: some View {
        FSPaletteReader { p in
            VStack(spacing: 0) {
                ViewThatFits(in: .horizontal) {
                    HStack(spacing: 8) {
                        // fixedSize: a label that doesn't fit makes this layout not fit, instead of breaking the word
                        Text(key).font(FS.label()).tracking(0.7).foregroundStyle(p.inkMuted).fixedSize().frame(minWidth: 104, alignment: .leading)
                        Text(value).font(FS.readout(15, relativeTo: .body)).foregroundStyle(muted ? p.inkMuted : p.ink).fixedSize()
                        Spacer(minLength: 4)
                        status
                    }
                    // large text: the label above, then the value and the state
                    VStack(alignment: .leading, spacing: 4) {
                        Text(key).font(FS.label()).tracking(0.7).foregroundStyle(p.inkMuted)
                        Text(value).font(FS.readout(15, relativeTo: .body)).foregroundStyle(muted ? p.inkMuted : p.ink)
                        status
                    }
                    .padding(.vertical, 6)
                    .frame(maxWidth: .infinity, alignment: .leading)
                }
                .frame(minHeight: 36)
                .accessibilityElement(children: .combine)       // one stop per row: label, value, state
                Rectangle().fill(p.rule).frame(height: 1)
            }
        }
    }
}
