// SVG.js integration: advanced vector construction (path arithmetic, transforms, gradients built
// programmatically) that still ends up as native SVG inside the composition.
import { useMemo } from 'react';
import { PathArray, SVG, type Svg } from '@svgdotjs/svg.js';
import { scopeIds, svgEl } from './layer';

/**
 * Draw with the SVG.js API into a nested <svg> placed at (x, y, w, h). `draw` receives an SVG.js
 * document whose user space is `viewBox` (default 0 0 w h). Output is inlined as plain SVG with ids
 * scoped under `id`; the group carries data-render="svgjs" for the render report.
 */
export function SvgJsLayer({ id, x, y, w, h, viewBox, draw }: { id: string; x: number; y: number; w: number; h: number; viewBox?: string; draw: (d: Svg) => void }) {
  const markup = useMemo(() => {
    const el = svgEl(w, h);
    draw(SVG(el));
    scopeIds(el, id);
    return el.innerHTML;
  }, []);
  return <svg id={id} data-render="svgjs" x={x} y={y} width={w} height={h} viewBox={viewBox ?? `0 0 ${w} ${h}`} overflow="visible" dangerouslySetInnerHTML={{ __html: markup }} />;
}

/** Fit any path (an icon or a traced shape) uniformly into a box, centred. Keeps proportions. */
export function fitPath(d: string, x: number, y: number, w: number, h: number): string {
  const p = new PathArray(d), b = p.bbox();
  if (!b.width && !b.height) throw new Error('fitPath: empty path');
  const s = Math.min(w / (b.width || 1), h / (b.height || 1)), bw = b.width * s, bh = b.height * s;
  return p.size(bw || 0.001, bh || 0.001).move(x + (w - bw) / 2, y + (h - bh) / 2).toString();
}
