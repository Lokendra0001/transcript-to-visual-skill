// AntV Infographic integration: structured components (process rows, timelines, hierarchies,
// comparisons, charts) from AntV's declarative syntax, embedded as one region of the composition.
//
// AntV lays text out as HTML inside <foreignObject>, which is not portable SVG (it vanishes in
// most SVG tools and is forbidden by the renderer). This layer re-creates every laid-out line as
// a native <text> at the exact position, font, size, weight and colour the browser computed, then
// removes the foreignObject. Remote fonts and icon services are never used: the renderer blocks
// the network, so pass `font` (an installed font) and avoid AntV `icon` fields.
import { useLayoutEffect, useRef } from 'react';
import { Infographic } from '@antv/infographic';
import { defer, scopeIds } from './layer';

const NS = 'http://www.w3.org/2000/svg';

/** Replace each <foreignObject> text block with native <text> lines measured from the live layout. */
export function foreignTextToSvg(svg: SVGSVGElement): number {
  const inv = svg.getScreenCTM()!.inverse();
  const toSvg = (x: number, y: number) => new DOMPoint(x, y).matrixTransform(inv);
  const out = document.createElementNS(NS, 'g');
  out.setAttribute('data-converted-text', '');
  let lines = 0;
  for (const fo of [...svg.querySelectorAll('foreignObject')]) {
    const unit = (fo as SVGGraphicsElement).getScreenCTM()!.a / svg.getScreenCTM()!.a; // FO css px -> root user units
    const walker = document.createTreeWalker(fo, NodeFilter.SHOW_TEXT);
    type Word = { text: string; left: number; right: number; top: number; bottom: number; el: Element };
    const words: Word[] = [];
    for (let t = walker.nextNode() as Text | null; t; t = walker.nextNode() as Text | null) {
      const re = /\S+/g;
      for (let m = re.exec(t.data); m; m = re.exec(t.data)) {
        const r = document.createRange();
        r.setStart(t, m.index); r.setEnd(t, m.index + m[0].length);
        const rects = [...r.getClientRects()].filter((q) => q.width > 0);
        if (!rects.length) continue;
        const q = rects[0];
        words.push({ text: m[0], left: q.left, right: rects[rects.length - 1].right, top: q.top, bottom: q.bottom, el: t.parentElement! });
      }
    }
    const groups: Word[][] = [];
    for (const w of words) {
      const g = groups[groups.length - 1];
      if (g && Math.abs(g[0].top - w.top) < 2 && g[0].el === w.el) g.push(w); else groups.push([w]);
    }
    for (const g of groups) {
      const cs = getComputedStyle(g[0].el), a = toSvg(g[0].left, (g[0].top + g[0].bottom) / 2);
      const t = document.createElementNS(NS, 'text');
      t.setAttribute('x', a.x.toFixed(2));
      t.setAttribute('y', a.y.toFixed(2));
      t.setAttribute('dominant-baseline', 'central');
      t.setAttribute('font-family', cs.fontFamily);
      t.setAttribute('font-size', (parseFloat(cs.fontSize) * unit).toFixed(2));
      t.setAttribute('font-weight', cs.fontWeight);
      if (cs.fontStyle !== 'normal') t.setAttribute('font-style', cs.fontStyle);
      if (cs.letterSpacing !== 'normal') t.setAttribute('letter-spacing', cs.letterSpacing);
      t.setAttribute('fill', cs.color);
      // Keep the measured line width: same words, same spacing as the browser laid them out.
      t.setAttribute('textLength', ((g[g.length - 1].right - g[0].left) / svg.getScreenCTM()!.a).toFixed(2));
      t.setAttribute('lengthAdjust', 'spacing');
      t.textContent = g.map((w) => w.text).join(' ');
      out.appendChild(t);
      lines++;
    }
    fo.remove();
  }
  svg.appendChild(out);
  return lines;
}

async function renderAntv(host: SVGSVGElement, id: string, w: number, h: number, syntax: string, font: string, options: object) {
  const box = document.createElement('div');
  Object.assign(box.style, { position: 'absolute', left: '-20000px', top: '0', width: `${w}px`, height: `${h}px` });
  document.body.appendChild(box);
  const errors: string[] = [];
  const ig = new Infographic({ container: box, width: w, height: h, editable: false, ...options,
    themeConfig: { ...(options as any).themeConfig, base: { ...(options as any).themeConfig?.base, text: { 'font-family': font } } } } as any);
  ig.on('error', (e: any) => errors.push(String(e?.message ?? e)));
  const loaded = new Promise((ok) => { ig.on('loaded', ok); setTimeout(ok, 4000); });
  ig.render(syntax);
  await loaded;
  if (errors.length) throw new Error(`AntvLayer ${id}: ${errors.join('; ')}`);
  const svg = box.querySelector('svg');
  if (!svg) throw new Error(`AntvLayer ${id}: AntV produced no <svg>`);
  if (svg.querySelector('image[href^="http"], use[href^="http"]')) throw new Error(`AntvLayer ${id}: remote resource in AntV output (remove icon fields)`);
  foreignTextToSvg(svg);
  scopeIds(svg, id);
  host.setAttribute('viewBox', svg.getAttribute('viewBox') ?? `0 0 ${w} ${h}`);
  host.replaceChildren(...[...svg.childNodes]);
  box.remove();
}

/**
 * Render AntV Infographic `syntax` (e.g. "infographic list-row-simple-horizontal-arrow\ndata …")
 * into the box (x, y, w, h). `options` passes extra AntV options (theme, palette …). The result is
 * native SVG under <svg id={id} data-render="antv">, scaled to fit with preserved aspect ratio.
 */
export function AntvLayer({ id, x, y, w, h, syntax, font, options = {} }: { id: string; x: number; y: number; w: number; h: number; syntax: string; font: string; options?: object }) {
  const ref = useRef<SVGSVGElement>(null);
  useLayoutEffect(() => { defer(renderAntv(ref.current!, id, w, h, syntax, font, options)); }, []);
  return <svg ref={ref} id={id} data-render="antv" x={x} y={y} width={w} height={h} viewBox={`0 0 ${w} ${h}`} />;
}
