// Colour helpers so surfaces can derive faces, highlights and shadows from one token colour.

type RGB = [number, number, number];

function parse(c: string): RGB {
  const m = c.trim().match(/^#([0-9a-f]{3}|[0-9a-f]{6})$/i);
  if (!m) throw new Error(`colour helpers need #rgb or #rrggbb, got "${c}"`);
  const h = m[1].length === 3 ? [...m[1]].map((x) => x + x).join('') : m[1];
  return [0, 2, 4].map((i) => parseInt(h.slice(i, i + 2), 16)) as RGB;
}
const hex = (rgb: RGB) => '#' + rgb.map((v) => Math.round(Math.max(0, Math.min(255, v))).toString(16).padStart(2, '0')).join('').toUpperCase();

/** Linear mix of two colours; t=0 gives a, t=1 gives b. */
export function mix(a: string, b: string, t: number): string {
  const x = parse(a), y = parse(b);
  return hex(x.map((v, i) => v + (y[i] - v) * t) as RGB);
}
export const lighten = (c: string, t: number) => mix(c, '#FFFFFF', t);
export const darken = (c: string, t: number) => mix(c, '#000000', t);

/** Relative luminance (WCAG), 0..1. */
export function luminance(c: string): number {
  const [r, g, b] = parse(c).map((v) => { const s = v / 255; return s <= 0.03928 ? s / 12.92 : ((s + 0.055) / 1.055) ** 2.4; });
  return 0.2126 * r + 0.7152 * g + 0.0722 * b;
}
/** WCAG contrast ratio between two colours. */
export function contrast(a: string, b: string): number {
  const [x, y] = [luminance(a), luminance(b)].sort((p, q) => q - p);
  return (x + 0.05) / (y + 0.05);
}
