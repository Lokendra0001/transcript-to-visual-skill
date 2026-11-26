// Pure path generators for advanced shapes. Every function returns an SVG path `d` string in
// user units, so the result stays native, editable SVG. Deterministic: no randomness without a seed.

export type Pt = [number, number];
export type Radii = number | [number, number, number, number]; // tl, tr, br, bl
const n = (v: number) => +v.toFixed(2);

function corners(r: Radii, w: number, h: number): [number, number, number, number] {
  const max = Math.min(w, h) / 2;
  return (typeof r === 'number' ? [r, r, r, r] : r).map((v) => Math.max(0, Math.min(v, max))) as any;
}

/** Rectangle with an independent radius per corner. */
export function roundedRect(x: number, y: number, w: number, h: number, r: Radii = 0): string {
  const [tl, tr, br, bl] = corners(r, w, h);
  return `M${n(x + tl)} ${n(y)} H${n(x + w - tr)} A${tr} ${tr} 0 0 1 ${n(x + w)} ${n(y + tr)} V${n(y + h - br)} `
    + `A${br} ${br} 0 0 1 ${n(x + w - br)} ${n(y + h)} H${n(x + bl)} A${bl} ${bl} 0 0 1 ${n(x)} ${n(y + h - bl)} `
    + `V${n(y + tl)} A${tl} ${tl} 0 0 1 ${n(x + tl)} ${n(y)} Z`;
}

/**
 * Continuous-curvature ("squircle", iOS/Figma smooth corner) rectangle. `smoothing` 0 gives a
 * plain rounded rect, 1 the fully smoothed corner that starts `r * 2` from the edge.
 */
export function squircle(x: number, y: number, w: number, h: number, r: number, smoothing = 0.6): string {
  const p = Math.min(r * (1 + smoothing), w / 2, h / 2);   // tangent distance from the corner
  const t = Math.min(0.5523 + 0.3 * smoothing, 0.95);      // handle reach toward the corner, as a share of p
  const corner = (s: Pt, c: Pt, e: Pt) => `L${n(s[0])} ${n(s[1])} C${n(s[0] + (c[0] - s[0]) * t)} ${n(s[1] + (c[1] - s[1]) * t)} `
    + `${n(e[0] + (c[0] - e[0]) * t)} ${n(e[1] + (c[1] - e[1]) * t)} ${n(e[0])} ${n(e[1])}`;
  return `M${n(x + p)} ${n(y)} `
    + corner([x + w - p, y], [x + w, y], [x + w, y + p]) + ' '
    + corner([x + w, y + h - p], [x + w, y + h], [x + w - p, y + h]) + ' '
    + corner([x + p, y + h], [x, y + h], [x, y + h - p]) + ' '
    + corner([x, y + p], [x, y], [x + p, y]) + ' Z';
}

/** Panel with a folder tab on its top edge (tab at `tabX` from the left, `tabW` wide, `tabH` tall). */
export function tabbedPanel(x: number, y: number, w: number, h: number, r: number, tabX: number, tabW: number, tabH: number, slant = 0): string {
  const top = y + tabH, tr = Math.min(r, tabH / 2);
  return `M${n(x + r)} ${n(top)} H${n(x + tabX)} L${n(x + tabX + slant)} ${n(y + tr)} Q${n(x + tabX + slant)} ${n(y)} ${n(x + tabX + slant + tr)} ${n(y)} `
    + `H${n(x + tabX + tabW - slant - tr)} Q${n(x + tabX + tabW - slant)} ${n(y)} ${n(x + tabX + tabW - slant)} ${n(y + tr)} L${n(x + tabX + tabW)} ${n(top)} `
    + `H${n(x + w - r)} A${r} ${r} 0 0 1 ${n(x + w)} ${n(top + r)} V${n(y + h - r)} A${r} ${r} 0 0 1 ${n(x + w - r)} ${n(y + h)} `
    + `H${n(x + r)} A${r} ${r} 0 0 1 ${n(x)} ${n(y + h - r)} V${n(top + r)} A${r} ${r} 0 0 1 ${n(x + r)} ${n(top)} Z`;
}

/** Ribbon banner: main band plus forked tails `tail` wide on both ends, notched `notch` deep. */
export function ribbon(x: number, y: number, w: number, h: number, tail = h * 0.8, notch = h * 0.3): { band: string; tails: string; folds: string } {
  const fold = h * 0.25;
  return {
    band: `M${n(x)} ${n(y)} H${n(x + w)} V${n(y + h)} H${n(x)} Z`,
    tails: `M${n(x - tail)} ${n(y + fold)} H${n(x)} V${n(y + h + fold)} H${n(x - tail)} L${n(x - tail + notch)} ${n(y + fold + h / 2)} Z `
      + `M${n(x + w + tail)} ${n(y + fold)} H${n(x + w)} V${n(y + h + fold)} H${n(x + w + tail)} L${n(x + w + tail - notch)} ${n(y + fold + h / 2)} Z`,
    folds: `M${n(x)} ${n(y + h)} L${n(x + fold * 0.9)} ${n(y + h)} L${n(x)} ${n(y + h + fold)} Z M${n(x + w)} ${n(y + h)} L${n(x + w - fold * 0.9)} ${n(y + h)} L${n(x + w)} ${n(y + h + fold)} Z`,
  };
}

/** Regular polygon or star centred at (cx, cy). `inner` < 1 makes a star; `round` rounds the vertices. */
export function polygon(cx: number, cy: number, r: number, sides: number, { inner = 1, rotate = -90, round = 0 } = {}): string {
  const pts: Pt[] = [];
  const count = inner < 1 ? sides * 2 : sides;
  for (let i = 0; i < count; i++) {
    const a = ((rotate + (360 / count) * i) * Math.PI) / 180, rad = inner < 1 && i % 2 ? r * inner : r;
    pts.push([cx + rad * Math.cos(a), cy + rad * Math.sin(a)]);
  }
  return roundedPolygon(pts, round);
}

/** Closed polygon through `pts` with each vertex rounded by radius `r`. */
export function roundedPolygon(pts: Pt[], r = 0): string {
  if (!r) return `M${pts.map((p) => `${n(p[0])} ${n(p[1])}`).join(' L')} Z`;
  let d = '';
  pts.forEach((p, i) => {
    const a = pts[(i - 1 + pts.length) % pts.length], b = pts[(i + 1) % pts.length];
    const la = Math.hypot(a[0] - p[0], a[1] - p[1]), lb = Math.hypot(b[0] - p[0], b[1] - p[1]);
    const rr = Math.min(r, la / 2, lb / 2);
    const s: Pt = [p[0] + ((a[0] - p[0]) / la) * rr, p[1] + ((a[1] - p[1]) / la) * rr];
    const e: Pt = [p[0] + ((b[0] - p[0]) / lb) * rr, p[1] + ((b[1] - p[1]) / lb) * rr];
    d += `${i ? 'L' : 'M'}${n(s[0])} ${n(s[1])} Q${n(p[0])} ${n(p[1])} ${n(e[0])} ${n(e[1])} `;
  });
  return d + 'Z';
}

/** Scalloped seal (rosette) badge outline. */
export function scallop(cx: number, cy: number, r: number, bumps = 16, depth = 0.08): string {
  let d = '';
  for (let i = 0; i <= bumps; i++) {
    const a = (i / bumps) * Math.PI * 2, mid = ((i - 0.5) / bumps) * Math.PI * 2;
    const p: Pt = [cx + r * Math.cos(a), cy + r * Math.sin(a)];
    const c: Pt = [cx + r * (1 + depth * 2) * Math.cos(mid), cy + r * (1 + depth * 2) * Math.sin(mid)];
    d += i === 0 ? `M${n(p[0])} ${n(p[1])} ` : `Q${n(c[0])} ${n(c[1])} ${n(p[0])} ${n(p[1])} `;
  }
  return d + 'Z';
}

/** Deterministic pseudo-random generator (mulberry32). */
export function rng(seed: number) {
  let a = seed >>> 0;
  return () => { a = (a + 0x6d2b79f5) >>> 0; let t = a; t = Math.imul(t ^ (t >>> 15), t | 1); t ^= t + Math.imul(t ^ (t >>> 7), t | 61); return ((t ^ (t >>> 14)) >>> 0) / 4294967296; };
}

/** Smooth closed curve through points (Catmull-Rom converted to cubic Béziers). */
export function smoothClosed(pts: Pt[], tension = 1): string {
  const m = pts.length;
  let d = `M${n(pts[0][0])} ${n(pts[0][1])}`;
  for (let i = 0; i < m; i++) {
    const p0 = pts[(i - 1 + m) % m], p1 = pts[i], p2 = pts[(i + 1) % m], p3 = pts[(i + 2) % m];
    const c1: Pt = [p1[0] + ((p2[0] - p0[0]) / 6) * tension, p1[1] + ((p2[1] - p0[1]) / 6) * tension];
    const c2: Pt = [p2[0] - ((p3[0] - p1[0]) / 6) * tension, p2[1] - ((p3[1] - p1[1]) / 6) * tension];
    d += ` C${n(c1[0])} ${n(c1[1])} ${n(c2[0])} ${n(c2[1])} ${n(p2[0])} ${n(p2[1])}`;
  }
  return d + ' Z';
}

/** Organic blob in the ellipse (cx, cy, rx, ry); same seed, same shape. */
export function blob(cx: number, cy: number, rx: number, ry: number, seed: number, { points = 7, wobble = 0.22 } = {}): string {
  const rand = rng(seed), pts: Pt[] = [];
  for (let i = 0; i < points; i++) {
    const a = (i / points) * Math.PI * 2, k = 1 - wobble / 2 + rand() * wobble;
    pts.push([cx + Math.cos(a) * rx * k, cy + Math.sin(a) * ry * k]);
  }
  return smoothClosed(pts);
}

/** Horizontal wave across [x, x + w] at baseline y: a decorative section boundary. Close it to fill below. */
export function wave(x: number, y: number, w: number, amp: number, periods = 2, closeTo?: number): string {
  const seg = w / (periods * 2);
  let d = `M${n(x)} ${n(y)}`;
  for (let i = 0; i < periods * 2; i++) d += ` q${n(seg / 2)} ${n(i % 2 ? amp : -amp)} ${n(seg)} 0`;
  return closeTo === undefined ? d : `${d} V${n(closeTo)} H${n(x)} Z`;
}

/** Chevron / arrow step shape (process ribbons). `point` is the arrow depth; `notch` the tail cut. */
export function chevron(x: number, y: number, w: number, h: number, point = h / 3, notch = point): string {
  return `M${n(x)} ${n(y)} H${n(x + w - point)} L${n(x + w)} ${n(y + h / 2)} L${n(x + w - point)} ${n(y + h)} H${n(x)} L${n(x + notch)} ${n(y + h / 2)} Z`;
}

/** Smooth S-curve connector between two points; `axis` picks the tangent direction at both ends. */
export function curve(a: Pt, b: Pt, axis: 'x' | 'y' = 'x', bend = 0.5): string {
  const dx = (b[0] - a[0]) * bend, dy = (b[1] - a[1]) * bend;
  const c1: Pt = axis === 'x' ? [a[0] + dx, a[1]] : [a[0], a[1] + dy];
  const c2: Pt = axis === 'x' ? [b[0] - dx, b[1]] : [b[0], b[1] - dy];
  return `M${n(a[0])} ${n(a[1])} C${n(c1[0])} ${n(c1[1])} ${n(c2[0])} ${n(c2[1])} ${n(b[0])} ${n(b[1])}`;
}

/** Orthogonal polyline with rounded elbows. Repeated and collinear points are dropped (no zero-length legs). */
export function orth(raw: Pt[], r = 10): string {
  const pts = raw.filter((p, i) => i === 0 || p[0] !== raw[i - 1][0] || p[1] !== raw[i - 1][1])
    .filter((p, i, a) => i === 0 || i === a.length - 1
      || (a[i + 1][0] - p[0]) * (p[1] - a[i - 1][1]) !== (a[i + 1][1] - p[1]) * (p[0] - a[i - 1][0]));
  let d = `M${n(pts[0][0])} ${n(pts[0][1])}`;
  for (let i = 1; i < pts.length - 1; i++) {
    const [x0, y0] = pts[i - 1], [x1, y1] = pts[i], [x2, y2] = pts[i + 1];
    const l1 = Math.hypot(x1 - x0, y1 - y0), l2 = Math.hypot(x2 - x1, y2 - y1), rr = Math.min(r, l1 / 2, l2 / 2);
    d += ` L${n(x1 - ((x1 - x0) / l1) * rr)} ${n(y1 - ((y1 - y0) / l1) * rr)} Q${n(x1)} ${n(y1)} ${n(x1 + ((x2 - x1) / l2) * rr)} ${n(y1 + ((y2 - y1) / l2) * rr)}`;
  }
  const e = pts[pts.length - 1];
  return `${d} L${n(e[0])} ${n(e[1])}`;
}

/** Corner points of an extruded block. `oblique` recedes up-right by `depth` at `angle` degrees; `isometric` uses 30°. */
export function extrusion(x: number, y: number, w: number, h: number, depth: number, angle = 30) {
  const dx = depth * Math.cos((angle * Math.PI) / 180), dy = -depth * Math.sin((angle * Math.PI) / 180);
  const front = `M${n(x)} ${n(y)} H${n(x + w)} V${n(y + h)} H${n(x)} Z`;
  const top = `M${n(x)} ${n(y)} L${n(x + dx)} ${n(y + dy)} H${n(x + w + dx)} L${n(x + w)} ${n(y)} Z`;
  const side = `M${n(x + w)} ${n(y)} L${n(x + w + dx)} ${n(y + dy)} V${n(y + h + dy)} L${n(x + w)} ${n(y + h)} Z`;
  return { front, top, side, dx, dy };
}
