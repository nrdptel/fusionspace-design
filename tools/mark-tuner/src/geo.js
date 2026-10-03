// ---- FusionSpace Rev C geometry: a line-for-line port of tools/build/geo.py and the lockup/icon
// ---- geometry in tools/build/build.py. Keep in step with those files.
const VK_SEGS = [[[0.0,0.0],[0.003444702564086392,0.0],[0.013518973238600625,0.00214641965292764],[0.020711354457486033,0.004]],[[0.020711354457486033,0.004],[0.045388484892322195,0.01035965233267237],[0.07272118207941179,0.02105737016132732],[0.09349567164037693,0.03]],[[0.09349567164037693,0.03],[0.1531509894464188,0.055679351758909215],[0.20870406080102846,0.08722664836372555],[0.26071522170854233,0.12]],[[0.26071522170854233,0.12],[0.3671616201383083,0.1870741661074845],[0.4657951196538054,0.2647472802029792],[0.5584969403591541,0.35]],[[0.5584969403591541,0.35],[0.8416531867690914,0.6104030854009941],[1.0,0.8908407745374308],[1.0,1.0]]];
// VK_SEGS is geo.VK_SEGS (the Nelder-Mead fit of the LD-Haack curve, max error 0.19%), normalised:
// (radius / R, distance from tip / L). It does not depend on any tunable parameter.
const ORDER = ["main", "west", "east", "south"];
const DRAW_ORDER = ["south", "west", "east", "main"];   // back to front: the ogive tail sits behind the Von Kármán
const NAMES = {main: "Main", west: "West", east: "East", south: "South"};
const PROFILE_NAMES = {vonkarman: "Von Kármán", conical: "conical", ogive: "tangent ogive", elliptical: "elliptical"};
const WM_W = 535.737;

function rot(p, c, deg) {
  const a = deg * Math.PI / 180, x = p[0] - c[0], y = p[1] - c[1];
  return [c[0] + x * Math.cos(a) - y * Math.sin(a), c[1] + x * Math.sin(a) + y * Math.cos(a)];
}

function fnum(v) {                     // geo.fnum: f"{v:.3f}".rstrip("0").rstrip(".")
  let s = v.toFixed(3);
  if (s.indexOf(".") >= 0) s = s.replace(/0+$/, "").replace(/\.$/, "");
  return (s === "-0" || s === "") ? "0" : s;
}

function bez1(P, u) {
  const m = 1 - u;
  return [m * m * m * P[0][0] + 3 * m * m * u * P[1][0] + 3 * m * u * u * P[2][0] + u * u * u * P[3][0],
          m * m * m * P[0][1] + 3 * m * m * u * P[1][1] + 3 * m * u * u * P[2][1] + u * u * u * P[3][1]];
}
function vkAt(tn) {                    // geo._vk_at
  let i = 0, P;
  for (i = 0; i < VK_SEGS.length; i++) { P = VK_SEGS[i]; if (P[3][1] >= tn || i === VK_SEGS.length - 1) break; }
  if (tn >= P[3][1]) return [i, 1.0, P[3][0]];
  let lo = 0, hi = 1;
  for (let k = 0; k < 60; k++) { const mid = (lo + hi) / 2; if (bez1(P, mid)[1] < tn) lo = mid; else hi = mid; }
  const u = (lo + hi) / 2;
  return [i, u, bez1(P, u)[0]];
}
function flankX(kind, W, L, h) {       // geo.flank_x
  if (kind === "conical") return W * (L - h) / L;
  if (kind === "ogive") { const rho = (W * W + L * L) / (2 * W); return Math.sqrt(Math.max(rho * rho - h * h, 0)) + W - rho; }
  if (kind === "elliptical") return W * Math.sqrt(Math.max(1 - h * h / (L * L), 0));
  return W * vkAt((L - h) / L)[2];
}
function splitBez(P, u) {              // geo._split
  if (u >= 1) return P.map(p => [p[0], p[1]]);
  const l = (a, b) => [a[0] + (b[0] - a[0]) * u, a[1] + (b[1] - a[1]) * u];
  const a = l(P[0], P[1]), b = l(P[1], P[2]), c = l(P[2], P[3]), d = l(a, b), e = l(b, c);
  return [[P[0][0], P[0][1]], a, d, l(d, e)];
}
const FOOT_STEPS = 400;

// P = {TILT, H_K, W_K, TIP_K, SAG_K, FOOT_K, SIZE:{}, KINDS:{}, GAP_W_R, GAP_E_R, WING_R, TAIL_R}
function makeGeo(P) {
  const {TILT, H_K, W_K, TIP_K, SAG_K, FOOT_K, SIZE, KINDS, GAP_W_R, GAP_E_R, WING_R, TAIL_R} = P;
  const footCache = new Map();
  function foot(kind, s, minWall = 0) { // geo.foot (minWall: production floor, units of a; 0 = brand foot)
    const key = kind + "|" + s + "|" + minWall;
    if (footCache.has(key)) return footCache.get(key);
    const W = W_K * s, L = H_K * s;
    const sag = SAG_K * W, Rn = (W * W + sag * sag) / (2 * sag), c = Rn - sag;
    const xa = h => Math.sqrt(Math.max(Rn * Rn - (h + c) * (h + c), 0));
    const wall = Math.max(FOOT_K * W, minWall);
    const d = h => flankX(kind, W, L, h) - xa(h) - wall;
    let lo = 0, found = false;
    for (let i = FOOT_STEPS - 1; i >= 0; i--) { const h = sag * i / FOOT_STEPS; if (d(h) < 0) { lo = h; found = true; break; } }
    let res;
    if (!found) res = [0, W, W];
    else {
      let hi = lo + sag / FOOT_STEPS;
      for (let k = 0; k < 60; k++) { const mid = (lo + hi) / 2; if (d(mid) < 0) lo = mid; else hi = mid; }
      res = [hi, flankX(kind, W, L, hi), xa(hi)];
    }
    footCache.set(key, res);
    return res;
  }

  function centroidY(kind, s) {         // geo.centroid_y: area centroid height from the cone centre (y down)
    const pts = sample(coneSegments(null, 1, [0, 0], {tilt: 0, kind, size: s, pos: [0, 0]}), 200);
    let a2 = 0, cy = 0;
    for (let i = 0; i < pts.length; i++) {
      const [x0, y0] = pts[i], [x1, y1] = pts[(i + 1) % pts.length];
      const c = x0 * y1 - x1 * y0;
      a2 += c; cy += (y0 + y1) * c;
    }
    return cy / (3 * a2);
  }
  function layout() {                  // geo.layout (diamond: VK north, ogive tail south, wings west/east on one centroid line)
    const r = W_K, B = (1 - TIP_K) * H_K;
    const F = {}, cf = {}, X = {};
    for (const n in SIZE) { F[n] = foot(KINDS[n], SIZE[n]); cf[n] = B * SIZE[n] - F[n][0]; X[n] = F[n][1]; }
    const yf = cf.main, wing = yf + WING_R * r;
    const up = {main: [0, 0]};
    up.west = [-X.main - GAP_W_R * r - X.west, wing - centroidY(KINDS.west, SIZE.west)];
    up.east = [X.main + GAP_E_R * r + X.east, wing - centroidY(KINDS.east, SIZE.east)];
    up.south = [0, yf + TAIL_R * r + TIP_K * H_K * SIZE.south];
    const pos = {}; for (const n in up) pos[n] = rot(up[n], [0, 0], TILT);
    return [pos, up];
  }
  const [POS, POS_UPRIGHT] = layout();

  function coneSegments(name, A = 1, origin = [0, 0], o = {}) {
    const tilt = o.tilt === undefined ? TILT : o.tilt;
    const s = o.size === undefined ? SIZE[name] : o.size;
    const [cx, cy] = o.pos === undefined ? POS[name] : o.pos;
    const kind = o.kind || KINDS[name];
    const H = H_K * s, W = W_K * s;
    const ytip = cy - TIP_K * H, yb = cy + (1 - TIP_K) * H, L = yb - ytip;
    const c = [cx, cy];
    const T = p => { const q = rot(p, c, tilt); return [origin[0] + A * q[0], origin[1] + A * q[1]]; };
    const [hf, xf, xa] = foot(kind, s, o.minWall || 0);
    const yf = yb - hf, tip = [cx, ytip];
    const fr = [cx + xf, yf], fl = [cx - xf, yf], nr = [cx + xa, yf], nl = [cx - xa, yf];
    let vk = null;
    if (kind === "vonkarman") { const [i, u] = vkAt((L - hf) / L); vk = VK_SEGS.slice(0, i).concat([splitBez(VK_SEGS[i], u)]); }
    const segs = [["M", T(tip)]];
    function flank(p_to, side) {
      if (kind === "conical") return [["L", T(p_to)]];
      if (kind === "ogive") { const rho = (W * W + L * L) / (2 * W); return [["A", A * rho, A * rho, 0, 0, 1, T(p_to)]]; }
      if (kind === "elliptical") return [["A", A * W, A * L, tilt, 0, 1, T(p_to)]];
      if (kind === "vonkarman") {
        const segsN = side > 0 ? vk : vk.slice().reverse().map(Q => Q.slice().reverse());
        return segsN.map(Q => {
          const pts = Q.map(q => [cx + side * q[0] * W, ytip + q[1] * L]);
          return ["C", T(pts[1]), T(pts[2]), T(pts[3])];
        });
      }
    }
    segs.push(...flank(fr, +1));
    if (hf > 0) segs.push(["L", T(nr)]);
    const sag = SAG_K * W, Rn = (W * W + sag * sag) / (2 * sag);
    segs.push(["A", A * Rn, A * Rn, 0, 0, 0, T(nl)]);
    if (hf > 0) segs.push(["L", T(fl)]);
    segs.push(...flank(tip, -1));
    segs.push(["Z"]);
    return segs;
  }

  function cluster(A = 1, origin = [0, 0]) {
    const o = {}; for (const n of ORDER) o[n] = coneSegments(n, A, origin); return o;
  }
  function bbox(cl) {
    let x0 = Infinity, y0 = Infinity, x1 = -Infinity, y1 = -Infinity;
    for (const n in cl) for (const p of sample(cl[n])) {
      if (p[0] < x0) x0 = p[0]; if (p[1] < y0) y0 = p[1]; if (p[0] > x1) x1 = p[0]; if (p[1] > y1) y1 = p[1];
    }
    return [x0, y0, x1, y1];
  }
  function fitCluster({height, width, x0 = 0, y0 = 0}) {
    const b = bbox(cluster());
    const w = b[2] - b[0], h = b[3] - b[1];
    const A = height ? height / h : width / w;
    const org = [x0 - A * b[0], y0 - A * b[1]];
    const cl = cluster(A, org);
    return {cl, A, org, bb: bbox(cl)};
  }
  return {P, POS, POS_UPRIGHT, foot, flankX, centroidY, coneSegments, cluster, bbox, fitCluster};
}

// ---------- SVG arc / segment sampling (geo._arc_center, seg_param, sample)
function arcCenter(p0, p1, rx, ry, phi, fa, fs) {
  const ph = phi * Math.PI / 180, cp = Math.cos(ph), sp = Math.sin(ph);
  const dx = (p0[0] - p1[0]) / 2, dy = (p0[1] - p1[1]) / 2;
  const x1 = cp * dx + sp * dy, y1 = -sp * dx + cp * dy;
  const lam = x1 * x1 / (rx * rx) + y1 * y1 / (ry * ry);
  if (lam > 1) { rx *= Math.sqrt(lam); ry *= Math.sqrt(lam); }
  const num = rx * rx * ry * ry - rx * rx * y1 * y1 - ry * ry * x1 * x1;
  const den = rx * rx * y1 * y1 + ry * ry * x1 * x1;
  const co = Math.sqrt(Math.max(0, num / den)) * (fa === fs ? -1 : 1);
  const cx1 = co * rx * y1 / ry, cy1 = -co * ry * x1 / rx;
  const cx = cp * cx1 - sp * cy1 + (p0[0] + p1[0]) / 2;
  const cy = sp * cx1 + cp * cy1 + (p0[1] + p1[1]) / 2;
  const ang = (u, v) => Math.atan2(u[0] * v[1] - u[1] * v[0], u[0] * v[0] + u[1] * v[1]);
  const t1 = ang([1, 0], [(x1 - cx1) / rx, (y1 - cy1) / ry]);
  let dt = ang([(x1 - cx1) / rx, (y1 - cy1) / ry], [(-x1 - cx1) / rx, (-y1 - cy1) / ry]);
  if (!fs && dt > 0) dt -= 2 * Math.PI;
  if (fs && dt < 0) dt += 2 * Math.PI;
  return [[cx, cy], rx, ry, t1, dt];
}
function segParam(p0, sg) {
  const k = sg[0];
  if (k === "L") { const p1 = sg[1]; return t => [p0[0] + (p1[0] - p0[0]) * t, p0[1] + (p1[1] - p0[1]) * t]; }
  if (k === "A") {
    const [c, rx, ry, t1, dt] = arcCenter(p0, sg[6], sg[1], sg[2], sg[3], sg[4], sg[5]);
    const ph = sg[3] * Math.PI / 180, cp = Math.cos(ph), sp = Math.sin(ph);
    return t => { const a = t1 + dt * t, x = rx * Math.cos(a), y = ry * Math.sin(a); return [c[0] + cp * x - sp * y, c[1] + sp * x + cp * y]; };
  }
  if (k === "C") {
    const c1 = sg[1], c2 = sg[2], p1 = sg[3];
    return t => { const m = 1 - t; return [m*m*m*p0[0] + 3*m*m*t*c1[0] + 3*m*t*t*c2[0] + t*t*t*p1[0], m*m*m*p0[1] + 3*m*m*t*c1[1] + 3*m*t*t*c2[1] + t*t*t*p1[1]]; };
  }
}
function sample(segs, n = 120) {
  const pts = []; let cur = null;
  for (const sg of segs) {
    if (sg[0] === "M") { cur = sg[1]; pts.push(cur); continue; }
    if (sg[0] === "Z") continue;
    const f = segParam(cur, sg);
    for (let i = 1; i <= n; i++) pts.push(f(i / n));
    cur = sg[sg.length - 1];
  }
  return pts;
}
function segToD(segs) {
  const out = [];
  for (const sg of segs) {
    const k = sg[0];
    if (k === "M" || k === "L") out.push(`${k}${fnum(sg[1][0])},${fnum(sg[1][1])}`);
    else if (k === "A") out.push(`A${fnum(sg[1])},${fnum(sg[2])} ${fnum(sg[3])} ${sg[4]} ${sg[5]} ${fnum(sg[6][0])},${fnum(sg[6][1])}`);
    else if (k === "C") out.push("C" + sg.slice(1).map(p => `${fnum(p[0])},${fnum(p[1])}`).join(" "));
    else if (k === "Z") out.push("Z");
  }
  return out.join(" ");
}

// ---------- build.py lockup + icon geometry
// Wordmark metrics are the constants build.py reads from the Rev B originals it uses as input.
const WM_H = {bbox: [262.699, 64.972, 807.516, 149.437], cap_top: 70, base: 130};   // horizontal file
const WM_S = {top: 223.056, cap_top: 228, bottom: 306.113};                                         // stacked file

function stackedGeometry(G, L) {           // build.stacked_geometry (L.STACK_POS: "above" | "below")
  const b = G.bbox(G.cluster());
  const A = L.STACK_H / (b[3] - b[1]), w = A * (b[2] - b[0]);
  const cx = WM_W / 2;
  const STACK_GAP = L.STACK_GAP_K * L.STACK_H;
  let f, dy, H;
  if (L.STACK_POS === "below") {           // wordmark on top, mark under the descenders
    dy = -WM_S.top;
    const y0 = WM_S.bottom + dy + STACK_GAP;
    f = G.fitCluster({height: L.STACK_H, x0: cx - w / 2, y0});
    H = y0 + L.STACK_H;
  } else {                                 // mark on top, gap to the cap line
    f = G.fitCluster({height: L.STACK_H, x0: cx - w / 2, y0: 0});
    dy = L.STACK_H + STACK_GAP - WM_S.cap_top;
    H = WM_S.bottom + dy;
  }
  return {cl: f.cl, bb: f.bb, A: f.A, org: f.org, dy, W: WM_W, H, capTop: WM_S.cap_top + dy, gap: STACK_GAP};
}
function horizontalGeometry(G, L) {        // build.horizontal_geometry (L.H_POS: "before" | "after")
  const mark_h = L.H_MARK, wb = WM_H.bbox;
  const capc = (WM_H.cap_top + WM_H.base) / 2;
  const b = G.bbox(G.cluster()); const A = mark_h / (b[3] - b[1]); const w = A * (b[2] - b[0]);
  const top = Math.min(capc - mark_h / 2, wb[1]);
  const bottom = Math.max(capc + mark_h / 2, wb[3]);
  let f, x_wm, W;
  if (L.H_POS === "after") {
    x_wm = 0;
    const x_mk = (wb[2] - wb[0]) + L.H_GAP_K * mark_h;
    f = G.fitCluster({height: mark_h, x0: x_mk, y0: capc - mark_h / 2 - top});
    W = x_mk + w;
  } else {
    f = G.fitCluster({height: mark_h, x0: 0, y0: capc - mark_h / 2 - top});
    x_wm = w + L.H_GAP_K * mark_h;
    W = wb[2] - wb[0] + x_wm;
  }
  const dx = x_wm - wb[0], dy = -top;
  return {cl: f.cl, bb: f.bb, A: f.A, org: f.org, dx, dy, W, H: bottom - top, x_wm, markW: w, gapW: L.H_GAP_K * mark_h,
          capTop: WM_H.cap_top + dy, baseline: WM_H.base + dy, wmX0: wb[0] + dx, wmX1: wb[2] + dx};
}
const FAV_FILL = 0.87, FAV_RX = 96, APP_SAFE_R = 0.40;   // build.FAV_FILL, build.FAV_RX, build.APP_SAFE_R
const FAV_SHIFT = [-10.72, 10.07];                        // build.FAV_SHIFT (of 512): evens the gap to the tile edge
const FAV_ARROWS = ["west", "east"];                      // build.FAV_ARROWS
function appFrac(G) {                      // build.app_frac
  const b = G.bbox(G.cluster()), w = b[2] - b[0], h = b[3] - b[1];
  const cx = (b[0] + b[2]) / 2, cy = (b[1] + b[3]) / 2;
  let r = 0;
  for (const n of ORDER) for (const p of sample(G.coneSegments(n), 400)) r = Math.max(r, Math.hypot(p[0] - cx, p[1] - cy));
  return APP_SAFE_R * Math.max(w, h) / r;
}
function dxfGeometry(G, heightMm, minWallMm) { // build.dxf_geometry: trimmed feet, scaled to heightMm tall, top-left at 0,0
  let A = G.fitCluster({height: heightMm}).A, b0;
  const trimmed = (A_, org) => { const o = {}; for (const n of ORDER) o[n] = G.coneSegments(n, A_, org, {minWall: minWallMm / A}); return o; };
  for (let k = 0; k < 4; k++) { b0 = G.bbox(trimmed(1, [0, 0])); A = heightMm / (b0[3] - b0[1]); }
  const org = [-A * b0[0], -A * b0[1]];
  const cl = trimmed(A, org);
  return {cl, A, org, bb: G.bbox(cl)};
}
function iconGeometry(G, kind) {           // build.icon_svg (geometry only)
  const S = 512;
  const [frac, rx] = kind === "favicon" ? [FAV_FILL, FAV_RX] : kind === "icon" ? [0.765, 112] : [appFrac(G), 0];
  const b = G.bbox(G.cluster()), w = b[2] - b[0], h = b[3] - b[1];
  const A = frac * S / Math.max(w, h);
  const sh = kind === "favicon" ? FAV_SHIFT : [0, 0];
  const org = [S / 2 - A * (b[0] + b[2]) / 2 + sh[0], S / 2 - A * (b[1] + b[3]) / 2 + sh[1]];
  const cl = G.cluster(A, org), bb = G.bbox(cl);
  return {rx, A, names: DRAW_ORDER, paths: DRAW_ORDER.map(n => segToD(cl[n])), gx0: bb[0], gx1: bb[2]};
}

if (typeof module !== "undefined") module.exports = {DRAW_ORDER, makeGeo, segToD, sample, stackedGeometry, horizontalGeometry, iconGeometry, dxfGeometry, ORDER, fnum, FAV_FILL, FAV_RX, FAV_SHIFT, APP_SAFE_R, FAV_ARROWS};
