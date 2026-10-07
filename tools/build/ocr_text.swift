// SPDX-License-Identifier: Apache-2.0 · Copyright 2026 Neer Patel
// Reads the text in images with macOS's Vision framework and prints one JSON line per image: {"file", "lines": [{"text",
// "box": [x0, y0, x1, y1] in pixels from the top left]}]}. Used by kit_clip.check_captures to find text cut short with "…".
// Run: xcrun swift tools/build/ocr_text.swift <image> [<image> …]
import AppKit
import Foundation
import Vision

for path in CommandLine.arguments.dropFirst() {
    guard let img = NSImage(contentsOfFile: path), let cg = img.cgImage(forProposedRect: nil, context: nil, hints: nil) else {
        print("{\"file\": \"\(path)\", \"error\": \"unreadable\"}"); continue
    }
    let req = VNRecognizeTextRequest()
    req.recognitionLevel = .accurate
    req.usesLanguageCorrection = false
    try? VNImageRequestHandler(cgImage: cg).perform([req])
    let w = Double(cg.width), h = Double(cg.height)
    let lines: [[String: Any]] = (req.results ?? []).compactMap { o in
        guard let t = o.topCandidates(1).first?.string else { return nil }
        let b = o.boundingBox
        return ["text": t, "box": [b.minX * w, (1 - b.maxY) * h, b.maxX * w, (1 - b.minY) * h]]
    }
    let data = try! JSONSerialization.data(withJSONObject: ["file": path, "lines": lines], options: [.sortedKeys])
    print(String(data: data, encoding: .utf8)!)
}
