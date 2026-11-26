// Zdog integration: stylised pseudo-3D vector illustrations (isometric objects, rounded 3D icons,
// stacked cards, servers, databases) rendered by Zdog's SVG renderer into native <path>s.
import { useMemo } from 'react';
import Zdog from 'zdog';
import { scopeIds, svgEl } from './layer';

export type ZdogApi = typeof Zdog;
/** Isometric camera rotation (Zdog convention). */
export const ISO = { x: -Math.atan(1 / Math.SQRT2), y: Math.PI / 4 };

/**
 * Build a Zdog scene with `build(illo, Zdog)` and inline the result at (x, y, w, h). Zdog draws in a
 * centred coordinate space: (0, 0) is the middle of the box. Static (one render), deterministic.
 */
export function ZdogLayer({ id, x, y, w, h, zoom = 1, rotate = ISO, build }: {
  id: string; x: number; y: number; w: number; h: number; zoom?: number; rotate?: { x?: number; y?: number; z?: number };
  build: (illo: any, Z: ZdogApi) => void;
}) {
  const { markup, viewBox } = useMemo(() => {
    const el = svgEl(w, h);
    const illo = new Zdog.Illustration({ element: el, zoom, rotate, resize: false, dragRotate: false });
    build(illo, Zdog);
    illo.updateRenderGraph();
    scopeIds(el, id);
    return { markup: el.innerHTML, viewBox: el.getAttribute('viewBox') ?? `${-w / 2} ${-h / 2} ${w} ${h}` };
  }, []);
  return <svg id={id} data-render="zdog" x={x} y={y} width={w} height={h} viewBox={viewBox} overflow="visible" dangerouslySetInnerHTML={{ __html: markup }} />;
}
