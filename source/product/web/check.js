// FusionSpace product system: the web rules a page check tests, and the code that measures them.
// Generated from source/product/web/check.js by tools/build/kit_product.py, which fills in RULES
// from its constants; edit there, not here. The design repository's build runs it on its own
// pages (tools/build/kit_clip.py), and a site built on the system runs the same file in its own
// page check, so both read one rule the same way. The line counter is ported from hpr-sim's page
// check (MIT OR Apache-2.0).
//
// Use: load it in the page, or in a harness page that measures pages in same-origin frames, then
//   FusionSpaceCheck.measure(win, root)   the prose under root, line by line, and the verdict
//   FusionSpaceCheck.scaleAt(widthPx)     the reading scale's factor at a window width
//   FusionSpaceCheck.RULES                the numbers: type scale, reading scale, measure, widths

'use strict';

(function (global) {
  const RULES = /*RULES*/;

  // The tags whose lines are held to the measure.
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

  // Whether a block is set at the full measure: its content box as wide as its own max-width,
  // not narrowed by the window or by what holds it. Only those lines say what the measure gives.
  function atMeasure(win, block) {
    const s = win.getComputedStyle(block);
    const most = parseFloat(s.maxWidth);
    if (!Number.isFinite(most)) return false;
    const inner = block.getBoundingClientRect().width - parseFloat(s.paddingLeft)
      - parseFloat(s.paddingRight) - parseFloat(s.borderLeftWidth) - parseFloat(s.borderRightWidth);
    const box = s.boxSizing === 'border-box' ? block.getBoundingClientRect().width : inner;
    return box >= most - 1;
  }

  // The measure under `root` (`foundations.md`, *Type*): no line of prose longer than
  // RULES.measure.max characters, and, where blocks are set at the full measure, the median of
  // their lines, last lines left out, from RULES.measure.median[0] to [1]. The median is judged
  // only on RULES.measure.min_lines such lines or more. Returns
  //   { blocks: [{ block, lines, longest, at_measure }], over: [{ block, chars, text }],
  //     median, counted, median_ok }
  // with `median` null when too few lines count.
  function measure(win, root) {
    const M = RULES.measure;
    const result = { blocks: [], over: [], median: null, counted: 0, median_ok: true };
    const full = [];
    for (const [block, nodes] of proseBlocks(win, root)) {
      const ls = lines(win, block, nodes);
      let longest = null;
      for (const l of ls) if (!longest || l.chars > longest.chars) longest = l;
      const at = atMeasure(win, block);
      result.blocks.push({ block: block, lines: ls, longest: longest, at_measure: at });
      if (longest && longest.chars > M.max) {
        result.over.push({ block: block, chars: longest.chars, text: longest.text });
      }
      if (at) for (const l of ls.slice(0, -1)) full.push(l.chars);
    }
    result.counted = full.length;
    if (full.length >= M.min_lines) {
      full.sort(function (a, b) { return a - b; });
      const mid = full.length >> 1;
      result.median = full.length % 2 ? full[mid] : (full[mid - 1] + full[mid]) / 2;
      result.median_ok = result.median >= M.median[0] && result.median <= M.median[1];
    }
    return result;
  }

  global.FusionSpaceCheck = {
    RULES: RULES, PROSE: PROSE, scaleAt: scaleAt, proseBlocks: proseBlocks, lines: lines,
    atMeasure: atMeasure, measure: measure,
  };
})(typeof window !== 'undefined' ? window : globalThis);
