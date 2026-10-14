// SPDX-License-Identifier: Apache-2.0 · Copyright 2026 Neer Patel
// FusionSpace product system: the web rules a page check tests, and the code that measures them.
// Generated from source/product/web/check.js by tools/build/kit_product.py, which fills in RULES
// from its constants; edit there, not here. The design repository's build runs it on its own
// pages (tools/build/kit_clip.py), and a site built on the system runs the same file in its own
// page check, so both read one rule the same way. The line counter is ported from hpr-sim's page
// check (MIT OR Apache-2.0).
//
// Use: load it in the page, or in a harness page that measures pages in same-origin frames, then
//   FusionSpaceCheck.narrow(win, root)    prose under root held narrower than what holds it
//   FusionSpaceCheck.lineStats(win, root) the median and longest line of that prose, to report
//   FusionSpaceCheck.equations(win, root) math under root wider than the box that holds it
//   FusionSpaceCheck.scaleAt(widthPx)     the reading scale's factor at a window width
//   FusionSpaceCheck.RULES                the numbers: type scale, reading scale, widths

'use strict';

(function (global) {
  const RULES = {"rev": "E", "type": {"scale": [["label", 12, 16, "Cascadia Mono"], ["small", 14, 20, "Archivo"], ["body", 16, 24, "Archivo"], ["lead", 20, 28, "Archivo"], ["subtitle", 20, 24, "Cascadia Mono"], ["heading", 14, 20, "Cascadia Mono"], ["title", 28, 32, "Cascadia Mono"], ["display", 40, 44, "Cascadia Mono"], ["hero", 56, 60, "Cascadia Mono"], ["readout", 28, 32, "Cascadia Mono"], ["readout-l", 40, 44, "Cascadia Mono"], ["code", 14, 20, "Cascadia Mono"]], "capitals": [["label", 12, 16, "Cascadia Mono"], ["heading", 14, 20, "Cascadia Mono"]], "smallest_px": 12}, "fluid": {"from_px": 1024, "to_px": 1600, "max": 1.125, "scope": ".fs-read"}, "width": {"content_px": 1120, "gutter_px": 16, "gutter_wide_px": 32, "gutter_wide_from_px": 720}};

  // The tags of prose.
  const PROSE = ['P', 'LI', 'DD', 'DT', 'BLOCKQUOTE', 'FIGCAPTION'];

  // The reading scale's factor at a window `widthPx` wide (`foundations.md`, *Type*): 1 up to
  // RULES.fluid.from_px, RULES.fluid.max from RULES.fluid.to_px, and linear between. The CSS sets
  // it as a clamp() of rem and vw, so this is what that clamp gives at the browser's default size.
  function scaleAt(widthPx) {
    const f = RULES.fluid;
    const t = (widthPx - f.from_px) / (f.to_px - f.from_px);
    return 1 + (f.max - 1) * Math.min(1, Math.max(0, t));
  }

  // The prose blocks under `root`, each with its text nodes in order: every text node belongs to
  // its nearest box that isn't inline. Text in a table or a code block isn't prose. Whitespace
  // nodes are kept on their block, since they still part words.
  function proseBlocks(win, root) {
    const blockOf = function (node) {
      for (let e = node.parentElement; e && e !== root; e = e.parentElement) {
        const d = win.getComputedStyle(e).display;
        if (d !== 'inline' && d !== 'contents') return e;
      }
      return root;
    };
    const blocks = new Map();
    const walker = win.document.createTreeWalker(root, 4);
    for (let n = walker.nextNode(); n; n = walker.nextNode()) {
      if (!/\S/.test(n.data)) {
        const b = blocks.get(blockOf(n));
        if (b) b.push(n);
        continue;
      }
      const block = blockOf(n);
      if (PROSE.indexOf(block.tagName) < 0 || block.closest('table, pre')) continue;
      if (!blocks.has(block)) blocks.set(block, []);
      blocks.get(block).push(n);
    }
    return blocks;
  }

  // The lines of one prose block as drawn: [{ chars, text }], in order, the spaces between words
  // counted once. A character more than half a line below the line before starts a new one; a
  // word that wraps (at a hyphen) is split where it does.
  function lines(win, block, nodes) {
    const range = win.document.createRange();
    const midAt = function (node, k) {
      range.setStart(node, k);
      range.setEnd(node, k + 1);
      const r = range.getClientRects()[0];
      return r ? (r.top + r.bottom) / 2 : null;
    };
    const s = win.getComputedStyle(block);
    const half = (s.lineHeight === 'normal' ? 1.2 * parseFloat(s.fontSize)
      : parseFloat(s.lineHeight)) / 2;
    const out = [];
    let lineMid = null;
    let chars = 0;
    let text = '';
    let gap = false; // whitespace since the last word
    const piece = function (str, mid) {
      if (lineMid === null || mid > lineMid + half) {
        if (lineMid !== null) out.push({ chars: chars, text: text });
        lineMid = mid;
        chars = 0;
        text = '';
      } else if (gap) {
        chars += 1;
        text += ' ';
      }
      chars += Array.from(str).length;
      text += str;
      gap = false;
    };
    for (const node of nodes) {
      const data = node.data;
      const words = /\S+/g;
      let last = 0;
      for (let m = words.exec(data); m; m = words.exec(data)) {
        if (m.index > last) gap = true;
        last = m.index + m[0].length;
        let start = m.index;
        const end = last;
        while (start < end) {
          const mid = midAt(node, start);
          if (mid === null) break;
          const endMid = midAt(node, end - 1);
          if (endMid !== null && endMid <= mid + half) {
            piece(data.slice(start, end), mid);
            break;
          }
          // The word wraps: the last character still on this line.
          let lo = start;
          let hi = end - 1;
          while (hi - lo > 1) {
            const k = (lo + hi) >> 1;
            const km = midAt(node, k);
            if (km !== null && km <= mid + half) lo = k; else hi = k;
          }
          piece(data.slice(start, lo + 1), mid);
          start = lo + 1;
        }
      }
      if (last < data.length) gap = true;
    }
    if (lineMid !== null) out.push({ chars: chars, text: text });
    return out;
  }

  // What the lines of prose under `root` come to, as a report, not a rule (`foundations.md`,
  // *Type*: a line is as long as its column): the median line, each block's last left out, over
  // 20 such lines or more (null under that), and the longest line. Returns { median, counted,
  // longest } in characters.
  function lineStats(win, root) {
    const full = [];
    let longest = 0;
    for (const [block, nodes] of proseBlocks(win, root)) {
      const ls = lines(win, block, nodes);
      for (const l of ls) longest = Math.max(longest, l.chars);
      for (const l of ls.slice(0, -1)) full.push(l.chars);
    }
    let median = null;
    if (full.length >= 20) {
      full.sort(function (x, y) { return x - y; });
      const mid = full.length >> 1;
      median = full.length % 2 ? full[mid] : (full[mid - 1] + full[mid]) / 2;
    }
    return { median: median, counted: full.length, longest: longest };
  }

  // Prose held narrower than what holds it (`foundations.md`, *Type*: prose takes its column's
  // whole width). Each prose block under `root`, and each box around one up to `root`, must be as
  // wide as the box that holds it allows: one that is narrower is drawn again with no max-width
  // and no width of its own, and if it grows, something held it, a max-width, a width, or margins
  // set to auto. A box laid out by its parent (a flex or grid item, a table's part), a float, a
  // box taken out of the flow and one that isn't a block are sized on purpose, and one not drawn
  // has no width to read: each is skipped, but the boxes around it are still read. Returns [{ block, width, room }] in px, one per box
  // held, the innermost.
  function narrow(win, root) {
    const out = [];
    const seen = new Set();
    const num = function (v) { return parseFloat(v) || 0; };
    for (const block of proseBlocks(win, root).keys()) {
      for (let e = block; e && e !== root && !seen.has(e); e = e.parentElement) {
        seen.add(e);
        const p = e.parentElement;
        if (!p) break;
        const s = win.getComputedStyle(e);
        const ps = win.getComputedStyle(p);
        if (!/^(block|flow-root|list-item)$/.test(s.display) || s.float !== 'none'
          || /^(absolute|fixed)$/.test(s.position)
          || !/^(block|flow-root|list-item)$/.test(ps.display)) continue;
        // Not drawn now (in a closed <details>, say): nothing to read.
        if (!e.getClientRects().length) continue;
        const width = e.getBoundingClientRect().width;
        const room = p.clientWidth - num(ps.paddingLeft) - num(ps.paddingRight);
        if (width >= room - 1) continue;
        const was = e.getAttribute('style');
        e.style.setProperty('max-width', 'none', 'important');
        e.style.setProperty('width', 'auto', 'important');
        const free = e.getBoundingClientRect().width;
        if (was === null) e.removeAttribute('style'); else e.setAttribute('style', was);
        if (free > width + 1) {
          out.push({ block: e, width: width, room: room });
          break;
        }
      }
    }
    return out;
  }

  // Math wider than its room (`foundations.md`, *Type*, Math): MathML doesn't break a line, so
  // an equation too wide for a phone's column runs past its edge, or a box that scrolls hides
  // the rest. Each <math> under root whose drawn box leaves the content box of the block that
  // holds it, by more than a pixel either side, is one: the fix is a narrower equation, written
  // on more lines, never a scroll bar or a smaller size. Returns [{ math, width, room }] in px.
  function equations(win, root) {
    const out = [];
    const num = function (v) { return parseFloat(v) || 0; };
    for (const math of root.querySelectorAll('math')) {
      if (!math.getClientRects().length) continue;
      let p = math.parentElement;
      while (p && p !== root && !/^(block|flow-root|list-item|table-cell)$/.test(win.getComputedStyle(p).display)) {
        p = p.parentElement;
      }
      if (!p) continue;
      const ps = win.getComputedStyle(p);
      const box = p.getBoundingClientRect();
      const left = box.left + p.clientLeft + num(ps.paddingLeft);
      const right = left + p.clientWidth - num(ps.paddingLeft) - num(ps.paddingRight);
      // The formula's extent, not only its box: a too-wide display keeps its <math> box at the
      // column's width and lets its rows run past it.
      let x0 = Infinity;
      let x1 = -Infinity;
      for (const e of [math].concat(Array.from(math.querySelectorAll('*')))) {
        const r = e.getBoundingClientRect();
        if (r.width <= 0) continue;
        x0 = Math.min(x0, r.left);
        x1 = Math.max(x1, r.right);
      }
      if (x0 < left - 1 || x1 > right + 1) {
        out.push({ math: math, width: x1 - x0, room: right - left });
      }
    }
    return out;
  }

  global.FusionSpaceCheck = {
    RULES: RULES, PROSE: PROSE, scaleAt: scaleAt, proseBlocks: proseBlocks, lines: lines,
    lineStats: lineStats, narrow: narrow, equations: equations,
  };
})(typeof window !== 'undefined' ? window : globalThis);
