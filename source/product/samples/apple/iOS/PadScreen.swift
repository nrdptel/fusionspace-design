// SPDX-License-Identifier: Apache-2.0 · Copyright 2026 Neer Patel
// The pad screen (product/mobile.md#screens), a tool: field theme; the title, then the designation as a data line; checks
// and channels as sections under a 2 pt rule; fixed at the bottom where a thumb reaches, the device's state above Hold to
// arm, with SAFE, one tap, to its right.
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
                    // the title first, then the designation as a plain data line (no tag over the title)
                    VStack(alignment: .leading, spacing: 4) {
                        Text("Pad 3 · Flight 04").font(FS.title()).foregroundStyle(p.ink).accessibilityAddTraits(.isHeader)
                            .fixedSize(horizontal: false, vertical: true)
                        Text("\(FS.unbroken(Sample.designation)) rev B · K535W · dual deploy").font(FS.data()).foregroundStyle(p.inkMuted)
                            .fixedSize(horizontal: false, vertical: true)
                    }
                    ViewThatFits(in: .horizontal) {
                        HStack(spacing: 12) { link; awake(p) }
                        VStack(alignment: .leading, spacing: 6) { link; awake(p) }
                    }
                    VStack(spacing: 8) {
                        FSSheetHeader("Checks")
                        PadRow(key: "Switch", value: "ON", status: FSStatus("On", signal: .ok, caps: true))
                        PadRow(key: "Battery", value: "8.1\u{00A0}V", status: FSStatus("OK", signal: .ok, symbol: "fs.battery", caps: true))
                        PadRow(key: "GPS", value: "3D · 11 sat", status: FSStatus("Fix", signal: .ok, symbol: "fs.gps-fix", caps: true))
                    }
                    VStack(spacing: 8) {
                        FSSheetHeader("Channels")
                        PadRow(key: "1 · Drogue", value: "Apogee + 0.4\u{00A0}s", status: FSStatus("Cont", signal: .ok, symbol: "fs.continuity", caps: true, spoken: "Continuity"))
                        PadRow(key: "2 · Main", value: "700\u{00A0}ft desc.", status: FSStatus("Cont", signal: .ok, symbol: "fs.continuity", caps: true, spoken: "Continuity"))
                        PadRow(key: "3 · —", value: "Not used", status: FSStatus("Not used", signal: .off, caps: true), muted: true)
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
        // The field theme is a light theme: the system's tint and the navigation bar follow it too. In dark appearance the
        // tint stayed dark-mode blue on the white canvas (about 3 : 1), and Apple's audit failed the confirmation link.
        .environment(\.colorScheme, .light)
        .toolbarColorScheme(.light, for: .navigationBar)
        .fsKeepsScreenOn()
    }

    private var link: FSStatus { FSStatus("Link", signal: .ok, detail: "0.3\u{00A0}s", symbol: "fs.link") }
    private func awake(_ p: FSPalette) -> some View {
        Text("Screen stays on").font(FS.label()).foregroundStyle(p.inkMuted).fixedSize(horizontal: false, vertical: true)
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
                                Text("SAFE").font(FS.button(22, relativeTo: .title2)).tracking(0.9)
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
                        Text("Arm with a confirmation instead").font(FS.button()).multilineTextAlignment(.center)
                            .frame(maxWidth: .infinity, minHeight: 44).contentShape(Rectangle())
                    }
                    .fsArmConfirmation(isPresented: $confirmingArm, designation: Sample.designation) {
                        commanded = "ARM"; armed = true; confirmedAt = .now
                    }
                }
    }
}

/// A label / value / state row in the content layer's own table: the label in Archivo, the value in Cascadia Mono (a word
/// such as "Not used", `muted`, in the label's font), the state as a chip.
struct PadRow: View {
    let key: String, value: String, status: FSStatus
    var muted = false
    var body: some View {
        FSPaletteReader { p in
            VStack(spacing: 0) {
                ViewThatFits(in: .horizontal) {
                    HStack(spacing: 8) {
                        // fixedSize: a label that doesn't fit makes this layout not fit, instead of breaking the word
                        Text(key).font(FS.label()).foregroundStyle(p.inkMuted).fixedSize().frame(minWidth: 104, alignment: .leading)
                        valueText(p).fixedSize()
                        Spacer(minLength: 4)
                        status
                    }
                    // large text: the label above, then the value and the state
                    VStack(alignment: .leading, spacing: 4) {
                        Text(key).font(FS.label()).foregroundStyle(p.inkMuted)
                        valueText(p)
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
    private func valueText(_ p: FSPalette) -> Text {
        Text(value).font(muted ? FS.label() : FS.data(15, relativeTo: .body)).foregroundStyle(muted ? p.inkMuted : p.ink)
    }
}
