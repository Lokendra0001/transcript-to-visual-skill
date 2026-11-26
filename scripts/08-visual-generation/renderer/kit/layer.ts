// Plumbing shared by the library layers (SVG.js, Zdog, Three.js, AntV).

const NS = 'http://www.w3.org/2000/svg';
export const svgEl = (w?: number, h?: number) => {
  const el = document.createElementNS(NS, 'svg');
  if (w !== undefined) el.setAttribute('width', String(w));
  if (h !== undefined) el.setAttribute('height', String(h));
  return el;
};

/** Pixel density the renderer captures the PNG at (from --scale); rasters are rendered at least this dense. */
export const renderScale = (): number => (globalThis as any).__kitScale ?? 2;

/** Register async layer work; the renderer waits for all of it before checking and serialising. */
export function defer(work: Promise<unknown>) {
  const g = globalThis as any;
  (g.__kitPending ??= []).push(work);
}

/**
 * Prefix every id inside `root` with `${prefix}-` and rewrite url(#…) / href="#…" references, so
 * library-generated ids never collide with Step 04 ids or with another layer. Also drops
 * library-private attributes (svgjs:data, editor data-*) that have no meaning in the output.
 */
export function scopeIds(root: Element, prefix: string) {
  const map = new Map<string, string>();
  root.querySelectorAll('[id]').forEach((e) => { const n = `${prefix}-${e.id}`; map.set(e.id, n); e.id = n; });
  const fix = (v: string) => v.replace(/url\(\s*['"]?#([^'")\s]+)['"]?\s*\)/g, (m, id) => (map.has(id) ? `url(#${map.get(id)})` : m))
    .replace(/^#(.+)$/, (m, id) => (map.has(id) ? `#${map.get(id)}` : m));
  root.querySelectorAll('*').forEach((e) => {
    for (const a of [...e.attributes]) {
      if (a.name.startsWith('svgjs:') || a.name.startsWith('xmlns:svgjs') || /^data-(element-type|indexes|x|y|horizontal-align|vertical-align|word-wrap)$/.test(a.name)) { e.removeAttribute(a.name); continue; }
      if (a.value.includes('#')) { const v = fix(a.value); if (v !== a.value) e.setAttribute(a.name, v); }
    }
  });
}
