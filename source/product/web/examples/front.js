// SPDX-License-Identifier: Apache-2.0 · Copyright 2026 Neer Patel
// The landing page's two figures, drawn at the width they're shown so their words stay 13 px at every size.
// The flight is HPR Sim 0.1.0's own recording of Loft Demo 54mm on an H54 (`hpr sim ... --export`), one sample
// every 0.1 s plus its events, in feet and feet per second.
(() => {
  const NS = "http://www.w3.org/2000/svg";
  const STILL = new URLSearchParams(location.search).has("still") || matchMedia("(prefers-reduced-motion: reduce)").matches;
  const fmt = (n) => Math.round(n).toLocaleString("en-US");
  const esc = (s) => s.replace(/&/g, "&amp;").replace(/</g, "&lt;");

  /* ------------------------------------------------------------------ the flight */
  const D = __DATA__.filter(([t]) => ![3.5, 9.1, 22.4].includes(t));
  // The events, with the numbers `hpr sim` prints for them.
  const EV = [[3.5, 535, 196, "Burnout"], [9.12, 1063, 0, "Apogee"], [22.41, 492, 46, "Main opens"], [53.94, 0, 15, "Landing"]];
  for (const e of EV) D.push([e[0], e[1], e[2]]);
  D.sort((a, b) => a[0] - b[0]);
  const T_END = 53.94;
  const phase = (t) => {
    const at = EV.find((e) => Math.abs(e[0] - t) < 0.001);
    if (at) return { Burnout: "Burnout: the motor is spent", Apogee: "Apogee: the drogue fires", "Main opens": "The main opens", Landing: "On the ground" }[at[3]];
    if (t < 0.27) return "On the rail";
    if (t < 3.5) return "Motor burning";
    if (t < 9.12) return "Coasting up";
    if (t < 22.41) return "Falling under the drogue";
    return "Falling under the main";
  };

  const fig = document.querySelector(".flight");
  const hero = document.querySelector(".hero");
  const copy = document.querySelector(".hero-copy");
  if (fig) {
    const plot = fig.querySelector(".plot");
    const out = {}; for (const k of ["t", "h", "v", "p"]) out[k] = fig.querySelector(`[data-r="${k}"]`);
    let S = null, cur = D.findIndex((d) => d[0] === 9.12), played = STILL, anim = 0;

    const show = (i) => {
      cur = Math.max(0, Math.min(D.length - 1, i));
      const [t, h, v] = D[cur];
      out.t.innerHTML = `${t.toFixed(t % 0.1 > 0.001 && 0.1 - (t % 0.1) > 0.001 ? 2 : 1)}<small>s</small>`;
      out.h.innerHTML = `${fmt(h)}<small>ft</small>`;
      out.v.innerHTML = `${fmt(v)}<small>ft/s</small>`;
      out.p.textContent = phase(t);
      plot.setAttribute("aria-valuenow", t.toFixed(2));
      plot.setAttribute("aria-valuetext", `${t.toFixed(1)} seconds: ${fmt(h)} feet, ${fmt(v)} feet per second. ${phase(t)}.`);
      if (S) {
        const x = S.X(t), y = S.Y(h);
        S.line.setAttribute("x1", x); S.line.setAttribute("x2", x); S.line.setAttribute("y1", S.Y(0)); S.line.setAttribute("y2", y);
        S.dot.setAttribute("cx", x); S.dot.setAttribute("cy", y);
      }
    };

    const draw = () => {
      const W = Math.round(plot.clientWidth);
      if (!W) return;
      const overlay = matchMedia("(min-width: 1080px)").matches;
      hero.classList.toggle("overlay", overlay);
      const narrow = W < 560;
      const ml = 66, mr = 8, mt = 30, mb = 34, xmax = 55;
      const pw = W - ml - mr;
      const X = (t) => ml + (t / xmax) * pw;
      let H = Math.round(Math.max(250, Math.min(440, W * 0.58))), ymax = 1200;
      if (overlay) {
        // The words sit in the sky above the descent: grow the chart until the flight passes under them, with room.
        const pr = plot.getBoundingClientRect(), cr = copy.getBoundingClientRect();
        const left = cr.left - pr.left - 32, bottom = cr.bottom - pr.top + 40;
        let hi = 0; for (const [t, h] of D) if (X(t) >= left) hi = Math.max(hi, h);
        for (H = 520; H < 1000; H += 10) {
          const ph = H - mt - mb, frac = (bottom - mt) / ph;
          if (frac < 0.85) { ymax = Math.max(1200, hi / (1 - frac)); if (ymax <= 1500) break; }
        }
      }
      ymax = Math.ceil(ymax / 50) * 50;
      const ph = H - mt - mb;
      const Y = (h) => mt + ph * (1 - h / ymax);
      const yt = [0, 500, 1000, 1500].filter((v) => v <= ymax);
      const xt = narrow ? [0, 20, 40] : [0, 10, 20, 30, 40, 50];
      const path = D.map(([t, h], i) => `${i ? "L" : "M"}${X(t).toFixed(1)} ${Y(h).toFixed(1)}`).join(" ");
      const area = `${path} L${X(T_END).toFixed(1)} ${Y(0)} L${X(0)} ${Y(0)} Z`;
      const labels = narrow
        ? [[9.12, 1063, "Apogee", "1,063 ft", "top"], [22.41, 492, "Main", "", "right"]]
        : [[3.5, 535, "Burnout", "535 ft", "upleft"], [9.12, 1063, "Apogee", "1,063 ft at 9.1 s", "top"], [22.41, 492, "Main opens", "492 ft", "left"]];
      const lab = ([t, h, name, val, side]) => {
        const x = X(t), y = Y(h);
        const [lx, ly, anchor] = side === "top" ? [x - 6, y - 14, "start"] : side === "right" ? [x + 12, y + 5, "start"]
          : side === "upleft" ? [x - 10, y - 10, "end"] : [x - 12, y + 22, "end"];
        return `<g class="late${played ? "" : " wait"}" data-t="${t}"${side === "upleft" ? ' data-fit="left"' : ""}><circle class="ev-dot" cx="${x.toFixed(1)}" cy="${y.toFixed(1)}" r="4.5"/>` +
          `<text class="ev" x="${lx.toFixed(1)}" y="${ly.toFixed(1)}" text-anchor="${anchor}">${esc(name)}${val ? ` <tspan class="ev-v">${esc(val)}</tspan>` : ""}</text></g>`;
      };
      const reveal = played ? W : 0;
      plot.innerHTML = `<svg viewBox="0 0 ${W} ${H}" width="${W}" height="${H}" aria-hidden="true" focusable="false">
<defs><linearGradient id="fl-g" gradientUnits="userSpaceOnUse" x1="${X(0)}" y1="0" x2="${X(T_END).toFixed(1)}" y2="0"><stop offset="0" stop-color="#DA7C30"/><stop offset=".35" stop-color="#D07D7A"/><stop offset=".65" stop-color="#A188CB"/><stop offset="1" stop-color="#768DF5"/></linearGradient>
<linearGradient id="fl-f" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#fff" stop-opacity=".26"/><stop offset="1" stop-color="#fff" stop-opacity="0"/></linearGradient>
<mask id="fl-m"><rect x="0" y="${mt}" width="${W}" height="${ph}" fill="url(#fl-f)"/></mask>
</defs>
${yt.map((v, i) => `<line class="tick" x1="${ml - 6}" x2="${ml}" y1="${Y(v)}" y2="${Y(v)}"/><text x="${ml - 10}" y="${Y(v) + 4.5}" text-anchor="end">${fmt(v)}${i === yt.length - 1 ? " ft" : ""}</text>`).join("")}
<line class="axis" x1="${ml}" x2="${ml + pw}" y1="${Y(0)}" y2="${Y(0)}"/>
${xt.map((v, i) => `<text x="${X(v)}" y="${Y(0) + 22}" text-anchor="${i ? "middle" : "start"}">${v}${i === xt.length - 1 ? " s" : ""}</text>`).join("")}
<g class="rv"><path d="${area}" fill="url(#fl-g)" mask="url(#fl-m)"/><path class="under" d="${path}"/>
<path d="${path}" fill="none" stroke="url(#fl-g)" stroke-width="3" stroke-linejoin="round" stroke-linecap="round"/></g>
<line class="scrub-line" x1="0" x2="0" y1="0" y2="0"/>
${labels.map(lab).join("")}
<circle class="scrub-dot" r="5"/>
</svg>`;
      const svg = plot.firstElementChild;
      // A label set to the left of its point keeps its value only while the whole label clears the chart's left edge.
      for (const g of svg.querySelectorAll('[data-fit="left"]')) {
        const text = g.querySelector("text"), v = text.querySelector(".ev-v");
        if (v && +text.getAttribute("x") - text.getComputedTextLength() < 2) v.remove();
      }
      S = { X, Y, ml, pw, xmax, line: svg.querySelector(".scrub-line"), dot: svg.querySelector(".scrub-dot"), rv: svg.querySelector(".rv"), W };
      S.rv.style.clipPath = `inset(0 ${W - reveal}px 0 0)`; // through the CSSOM: a strict security policy refuses style attributes
      show(cur);
      if (!played) play();
    };

    // One moment on arrival: the flight draws itself, each event appearing as the line reaches it.
    const play = () => {
      played = true;
      cancelAnimationFrame(anim);
      const start = performance.now(), dur = 2400;
      const step = (now) => {
        const k = Math.min(1, (now - start) / dur), e = 1 - Math.pow(1 - k, 2.2);
        const x = S.X(e * T_END) + 6;
        S.rv.style.clipPath = `inset(0 ${k < 1 ? Math.max(0, S.W - x) : 0}px 0 0)`;
        for (const g of plot.querySelectorAll(".late.wait")) if (S.X(+g.dataset.t) <= x) g.classList.remove("wait");
        if (k < 1) anim = requestAnimationFrame(step);
      };
      anim = requestAnimationFrame(step);
    };
    const finish = () => {
      if (!S) return;
      cancelAnimationFrame(anim); S.rv.style.clipPath = "inset(0 0px 0 0)";
      for (const g of plot.querySelectorAll(".late.wait")) g.classList.remove("wait");
    };

    const nearest = (t) => { let b = 0; for (let i = 1; i < D.length; i++) if (Math.abs(D[i][0] - t) < Math.abs(D[b][0] - t)) b = i; return b; };
    const at = (e) => {
      const r = plot.getBoundingClientRect();
      const t = ((e.clientX - r.left - S.ml) / S.pw) * S.xmax;
      finish(); show(nearest(Math.max(0, Math.min(T_END, t))));
    };
    plot.addEventListener("pointermove", (e) => { if (S) at(e); });
    plot.addEventListener("pointerdown", (e) => { if (S) at(e); });
    plot.addEventListener("keydown", (e) => {
      const t = D[cur][0], big = e.shiftKey ? 5 : 0.5;
      const go = { ArrowRight: t + big, ArrowUp: t + big, ArrowLeft: t - big, ArrowDown: t - big, PageUp: t + 5, PageDown: t - 5, Home: 0, End: T_END }[e.key];
      if (go === undefined) return;
      e.preventDefault(); finish(); show(nearest(Math.max(0, Math.min(T_END, go))));
    });

    // Redraw on the next frame, and only for a new width: drawing changes the figure's height, and a redraw run while
    // the browser delivers resize notifications (as a promise's callback can be) is a ResizeObserver loop.
    let queued = 0, lastW = -1;
    const redraw = () => { cancelAnimationFrame(queued); queued = requestAnimationFrame(() => { lastW = plot.clientWidth; const p = played; draw(); if (p) finish(); }); };
    new ResizeObserver(() => { if (plot.clientWidth !== lastW) redraw(); }).observe(plot);
    if (document.fonts) document.fonts.ready.then(redraw);
  }

  /* ------------------------------------------------------------------ the 60-flight check */
  // Misses in steps of 5%, from -35% to +35%; the end steps hold every flight past 30%.
  const HIST = [[-35, 0], [-30, 0], [-25, 0], [-20, 1], [-15, 4], [-10, 6], [-5, 4], [0, 10], [5, 12], [10, 10], [15, 2], [20, 5], [25, 4], [30, 2]];
  const MEAN = 7.76;
  const hf = document.querySelector(".hist-plot");
  if (hf) {
    const drawHist = (above = false) => {
      const W = Math.round(hf.clientWidth); if (!W) return;
      const narrow = W < 520;
      const ml = 30, mr = 6, mb = 52, mt = above ? 58 : 34;   // the band's label gets a line above the band when it can't fit inside
      const H = Math.round(Math.max(250, Math.min(340, W * 0.4)));
      const pw = W - ml - mr, ph = H - mt - mb, lo = -35, hi = 35, cmax = 16;
      const X = (v) => ml + ((v - lo) / (hi - lo)) * pw;
      const Y = (c) => mt + ph - (c / cmax) * ph;
      const xt = narrow ? [-30, -10, 10, 30] : [-30, -20, -10, 0, 10, 20, 30];
      const sign = (v) => (v > 0 ? "+" : v < 0 ? "−" : "") + Math.abs(v) + "%";
      const gap = narrow ? 2 : 3;
      const mx = X(MEAN), meanRight = mx + 6 + 104 < W;
      const bin = HIST.find(([b]) => MEAN >= b && MEAN < b + 5), cnt = Y(bin[1]) - 6;   // the count over the bar the average falls in
      const parted = Math.abs(mx - X(bin[0] + 2.5)) < 14;                             // its digits are about 16 px wide
      const meanLine = parted
        ? `<line class="mean" x1="${mx}" x2="${mx}" y1="${mt + 2}" y2="${cnt - 15}"/><line class="mean" x1="${mx}" x2="${mx}" y1="${cnt + 4}" y2="${Y(0)}"/>`
        : `<line class="mean" x1="${mx}" x2="${mx}" y1="${mt + 2}" y2="${Y(0)}"/>`;
      hf.innerHTML = `<svg class="fs-chart hist" viewBox="0 0 ${W} ${H}" width="${W}" height="${H}" aria-hidden="true" focusable="false">
<rect class="within" x="${X(-10)}" y="${mt - 26}" width="${X(10) - X(-10)}" height="${ph + 26}"/>
<text class="t-ink band-label" x="${X(-10) + 8}" y="${mt - 9}">32 within 10%</text>
${[0, 5, 10].map((c) => `<line class="grid" x1="${ml}" x2="${ml + pw}" y1="${Y(c)}" y2="${Y(c)}"/><text x="${ml - 8}" y="${Y(c) + 4.5}" text-anchor="end">${c}</text>`).join("")}
${HIST.filter(([, c]) => c).map(([b, c]) => `<rect class="bar${b >= -10 && b < 10 ? " in" : ""}" x="${X(b) + gap / 2}" y="${Y(c)}" width="${X(b + 5) - X(b) - gap}" height="${Y(0) - Y(c)}"/>`).join("")}
<line class="axis" x1="${ml}" x2="${ml + pw}" y1="${Y(0)}" y2="${Y(0)}"/>
${meanLine}
${HIST.filter(([, c]) => c).map(([b, c]) => `<text class="t-ink${b >= -10 && b < 10 ? " in" : ""}" x="${X(b + 2.5)}" y="${Y(c) - 6}" text-anchor="middle">${c}</text>`).join("")}
<text class="t-mean" x="${meanRight ? mx + 6 : mx - 6}" y="${mt + 12}" text-anchor="${meanRight ? "start" : "end"}">average +7.8%</text>
${xt.map((v) => `<text x="${X(v)}" y="${Y(0) + 20}" text-anchor="middle">${sign(v)}</text>`).join("")}
<text x="${ml}" y="${Y(0) + 42}">read low</text><text x="${ml + pw}" y="${Y(0) + 42}" text-anchor="end">read high</text>
</svg>`;
      const band = hf.querySelector(".band-label");
      if (!above && band.getComputedTextLength() + 16 > X(10) - X(-10)) return drawHist(true);
      if (above) { band.setAttribute("x", X(-10)); band.setAttribute("y", mt - 34); }
    };
    let hq = 0, hw = -1;
    new ResizeObserver(() => { if (hf.clientWidth === hw) return; cancelAnimationFrame(hq); hq = requestAnimationFrame(() => { hw = hf.clientWidth; drawHist(); }); }).observe(hf);
    if (document.fonts) document.fonts.ready.then(() => { cancelAnimationFrame(hq); hq = requestAnimationFrame(() => drawHist()); });   // it measures its words
  }
})();
