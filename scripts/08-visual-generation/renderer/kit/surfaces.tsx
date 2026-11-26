// Reusable, parameterised SVG components for premium surfaces and pseudo-3D objects.
// Native SVG only (editable, animatable, export-safe). Colours, sizes, radii, depth and light come
// from props (i.e. from the composition's tokens); defaults are neutral, never template-specific.
//
// Part IDs: the main shape is `${id}-box` (use it as a data-fit container), extra layers get
// `${id}-depth`, `${id}-shade`, `${id}-gloss`, `${id}-top`, `${id}-side` … so motion can target them.
import type { ReactNode } from 'react';
import { darken, lighten, mix } from './color';
import { blob as blobPath, extrusion, polygon, ribbon as ribbonPaths, roundedRect, scallop, squircle, type Radii } from './shapes';

export type Finish = 'flat' | 'brutalist' | 'soft' | 'neumorphic' | 'inset' | 'glass' | 'glossy' | 'bevel';

type Box = { id: string; x: number; y: number; w: number; h: number };
export type SurfaceProps = Box & {
  /** Corner radius, or [tl, tr, br, bl]. */
  radius?: Radii;
  /** 0..1: switch to a continuous-curvature (squircle) outline with this smoothing. Needs a numeric radius. */
  smooth?: number;
  /** Custom outline path (overrides the rectangle); x/y/w/h still describe its bounds. */
  d?: string;
  fill: string;
  stroke?: string;
  strokeWidth?: number;
  opacity?: number;
  finish?: Finish;
  /** Offset (brutalist), shadow distance (neumorphic) or bevel height, in px. */
  depth?: number;
  /** Direction the light comes from, degrees in SVG space (0 = right, 90 = down). Default 225 = top-left. */
  light?: number;
  /** Shadow filter id for finish 'soft' / 'glass' (build it with <Shadow>). */
  shadow?: string;
  /** Colour of the brutalist offset or neumorphic dark side. */
  shadowColor?: string;
  /** Neumorphic light-side colour. */
  highlight?: string;
  /** Fill opacity for 'glass' (default 0.55). */
  tint?: number;
  children?: ReactNode;
};

export function outline({ x, y, w, h, radius = 0, smooth, d }: Pick<SurfaceProps, 'x' | 'y' | 'w' | 'h' | 'radius' | 'smooth' | 'd'>): string {
  if (d) return d;
  if (smooth !== undefined) {
    if (typeof radius !== 'number') throw new Error('smooth (squircle) outlines need a numeric radius');
    return squircle(x, y, w, h, radius, smooth);
  }
  return roundedRect(x, y, w, h, radius);
}

const need = (v: string | undefined, finish: Finish, prop: string) => {
  if (!v) throw new Error(`Surface finish '${finish}' needs the '${prop}' prop`);
  return v;
};

/** One container component, many finishes: flat, neo-brutalist offset, soft shadow, neumorphic,
 *  inset, glass, glossy and bevelled. Finishes other than flat/brutalist need <KitDefs/> in <defs>. */
export function Surface(p: SurfaceProps) {
  const { id, x, y, w, h, fill, stroke, strokeWidth = stroke ? 1.5 : 0, opacity, finish = 'flat', depth = 6, light = 225, children } = p;
  const d = outline(p);
  const away = ((light + 180) * Math.PI) / 180, ox = +(Math.cos(away) * depth).toFixed(2), oy = +(Math.sin(away) * depth).toFixed(2);
  const clip = `${id}-clip`;
  const main = (extra: object = {}) => <path id={`${id}-box`} d={d} fill={fill} stroke={stroke} strokeWidth={strokeWidth} {...extra} />;
  const gloss = (paint: string, share: number) => (
    <rect id={`${id}-gloss`} x={x} y={y} width={w} height={h * share} fill={`url(#${paint})`} clipPath={`url(#${clip})`} pointerEvents="none" />
  );
  let body: ReactNode;
  switch (finish) {
    case 'flat': body = main(); break;
    case 'brutalist':
      body = <>{<path id={`${id}-depth`} d={d} transform={`translate(${ox} ${oy})`} fill={p.shadowColor ?? stroke ?? '#000000'} />}{main()}</>;
      break;
    case 'soft': body = main({ filter: `url(#${need(p.shadow, finish, 'shadow')})` }); break;
    case 'neumorphic': {
      const dark = p.shadowColor ?? darken(fill, 0.16), lite = p.highlight ?? lighten(fill, 0.75);
      const blur = depth > 8 ? 'kit-blur-md' : 'kit-blur-sm';
      body = (
        <>
          <path id={`${id}-shade`} d={d} fill={dark} transform={`translate(${ox} ${oy})`} filter={`url(#${blur})`} />
          <path id={`${id}-light`} d={d} fill={lite} transform={`translate(${-ox} ${-oy})`} filter={`url(#${blur})`} />
          {main()}
        </>
      );
      break;
    }
    case 'inset': body = main({ filter: 'url(#kit-inner)' }); break;
    case 'glass':
      body = (
        <>
          <path id={`${id}-box`} d={d} fill={fill} fillOpacity={p.tint ?? 0.55} filter={p.shadow ? `url(#${p.shadow})` : undefined} />
          {gloss('kit-sheen', 0.6)}
          <path id={`${id}-edge`} d={d} fill="none" stroke={stroke ?? 'url(#kit-glass-edge)'} strokeWidth={strokeWidth || 1.5} />
        </>
      );
      break;
    case 'glossy': body = <>{main({ filter: p.shadow ? `url(#${p.shadow})` : undefined })}{gloss('kit-gloss', 1)}</>; break;
    case 'bevel': body = main({ filter: 'url(#kit-bevel)' }); break;
    default: throw new Error(`unknown Surface finish '${finish}'`);
  }
  return (
    <g id={id} opacity={opacity}>
      {finish === 'glass' || finish === 'glossy' ? <defs><clipPath id={clip}><path d={d} /></clipPath></defs> : null}
      {body}
      {children}
    </g>
  );
}

/** Extruded block (front face + top + side) in oblique or isometric projection: stair steps, podiums, stacked cards. */
export function Block3D({ id, x, y, w, h, depth, angle = 30, color, front, top, side, stroke, strokeWidth = 0, gloss = false, children }: Box & {
  depth: number; angle?: number; color: string; front?: string; top?: string; side?: string; stroke?: string; strokeWidth?: number; gloss?: boolean; children?: ReactNode;
}) {
  const f = extrusion(x, y, w, h, depth, angle);
  const s = { stroke, strokeWidth, strokeLinejoin: 'round' as const };
  return (
    <g id={id}>
      <path id={`${id}-side`} d={f.side} fill={side ?? darken(color, 0.22)} {...s} />
      <path id={`${id}-top`} d={f.top} fill={top ?? lighten(color, 0.28)} {...s} />
      <path id={`${id}-box`} d={f.front} fill={front ?? color} {...s} />
      {gloss ? <rect id={`${id}-gloss`} x={x} y={y} width={w} height={h * 0.5} fill="url(#kit-sheen)" /> : null}
      {children}
    </g>
  );
}

/** Database / storage cylinder with shaded body, lit top, optional band rings and gloss. */
export function Cylinder({ id, cx, y, rx, ry, h, color, bands = 0, stroke, strokeWidth = 0, gloss = true }: {
  id: string; cx: number; y: number; rx: number; ry: number; h: number; color: string; bands?: number; stroke?: string; strokeWidth?: number; gloss?: boolean;
}) {
  const g = `${id}-shade-grad`, l = cx - rx, r = cx + rx, b = y + h;
  const body = `M${l} ${y} V${b} A${rx} ${ry} 0 0 0 ${r} ${b} V${y} A${rx} ${ry} 0 0 1 ${l} ${y} Z`;
  return (
    <g id={id}>
      <defs>
        <linearGradient id={g} x1="0" x2="1" y1="0" y2="0">
          <stop offset="0" stopColor={darken(color, 0.18)} /><stop offset="0.35" stopColor={lighten(color, 0.12)} />
          <stop offset="0.7" stopColor={color} /><stop offset="1" stopColor={darken(color, 0.28)} />
        </linearGradient>
      </defs>
      <path id={`${id}-box`} d={body} fill={`url(#${g})`} stroke={stroke} strokeWidth={strokeWidth} />
      {Array.from({ length: bands }, (_, i) => {
        const by = y + (h * (i + 1)) / (bands + 1);
        return <path key={i} id={`${id}-band-${i + 1}`} d={`M${l} ${by} A${rx} ${ry} 0 0 0 ${r} ${by}`} fill="none" stroke={darken(color, 0.3)} strokeOpacity={0.55} strokeWidth={Math.max(1, rx / 30)} />;
      })}
      <ellipse id={`${id}-top`} cx={cx} cy={y} rx={rx} ry={ry} fill={lighten(color, 0.3)} stroke={stroke} strokeWidth={strokeWidth} />
      {gloss ? <ellipse id={`${id}-gloss`} cx={cx - rx * 0.25} cy={y - ry * 0.15} rx={rx * 0.45} ry={ry * 0.35} fill="#FFFFFF" fillOpacity={0.35} /> : null}
    </g>
  );
}

/** Glossy sphere / orb (floating decoration or node bullet). */
export function Orb({ id, cx, cy, r, color }: { id: string; cx: number; cy: number; r: number; color: string }) {
  const g = `${id}-grad`;
  return (
    <g id={id}>
      <defs>
        <radialGradient id={g} cx="0.38" cy="0.32" r="0.75">
          <stop offset="0" stopColor={lighten(color, 0.65)} /><stop offset="0.45" stopColor={color} /><stop offset="1" stopColor={darken(color, 0.35)} />
        </radialGradient>
      </defs>
      <circle id={`${id}-box`} cx={cx} cy={cy} r={r} fill={`url(#${g})`} />
      <ellipse id={`${id}-gloss`} cx={cx - r * 0.3} cy={cy - r * 0.38} rx={r * 0.38} ry={r * 0.22} fill="#FFFFFF" fillOpacity={0.55} />
    </g>
  );
}

/** Ribbon banner with forked tails and folds; content (text) goes in children over the band. */
export function Ribbon({ id, x, y, w, h, color, tail, notch, children }: Box & { color: string; tail?: number; notch?: number; children?: ReactNode }) {
  const r = ribbonPaths(x, y, w, h, tail, notch);
  return (
    <g id={id}>
      <path id={`${id}-tails`} d={r.tails} fill={darken(color, 0.18)} />
      <path id={`${id}-folds`} d={r.folds} fill={darken(color, 0.4)} />
      <path id={`${id}-box`} d={r.band} fill={color} />
      {children}
    </g>
  );
}

export type BadgeShape = 'circle' | 'star' | 'seal' | 'hexagon' | 'diamond';
/** Badge / seal: circle, star, scalloped seal, hexagon or diamond, optionally glossy and ringed. */
export function Badge({ id, cx, cy, r, shape = 'circle', fill, stroke, strokeWidth = 0, ring, gloss = false, points = 5, children }: {
  id: string; cx: number; cy: number; r: number; shape?: BadgeShape; fill: string; stroke?: string; strokeWidth?: number; ring?: string; gloss?: boolean; points?: number; children?: ReactNode;
}) {
  const d = shape === 'star' ? polygon(cx, cy, r, points, { inner: 0.5, round: r * 0.06 })
    : shape === 'seal' ? scallop(cx, cy, r * 0.88, 18)
    : shape === 'hexagon' ? polygon(cx, cy, r, 6, { rotate: 0, round: r * 0.12 })
    : shape === 'diamond' ? polygon(cx, cy, r, 4, { round: r * 0.12 })
    : `M${cx - r} ${cy} A${r} ${r} 0 1 0 ${cx + r} ${cy} A${r} ${r} 0 1 0 ${cx - r} ${cy} Z`;
  const clip = `${id}-clip`;
  return (
    <g id={id}>
      {gloss ? <defs><clipPath id={clip}><path d={d} /></clipPath></defs> : null}
      <path id={`${id}-box`} d={d} fill={fill} stroke={stroke} strokeWidth={strokeWidth} />
      {ring ? <circle id={`${id}-ring`} cx={cx} cy={cy} r={r * 0.72} fill="none" stroke={ring} strokeWidth={Math.max(1, r * 0.06)} strokeDasharray={`${r * 0.08} ${r * 0.06}`} /> : null}
      {gloss ? <rect id={`${id}-gloss`} x={cx - r * 1.1} y={cy - r * 1.1} width={r * 2.2} height={r * 1.1} fill="url(#kit-gloss)" clipPath={`url(#${clip})`} /> : null}
      {children}
    </g>
  );
}

/** Organic decorative blob (deterministic from seed). */
export function Blob({ id, cx, cy, rx, ry, seed, fill, opacity = 1, filter, points, wobble }: {
  id: string; cx: number; cy: number; rx: number; ry: number; seed: number; fill: string; opacity?: number; filter?: string; points?: number; wobble?: number;
}) {
  return <path id={id} d={blobPath(cx, cy, rx, ry, seed, { points, wobble })} fill={fill} opacity={opacity} filter={filter ? `url(#${filter})` : undefined} />;
}

/** Mesh-style gradient background: base fill plus blurred colour spots, clipped to the box. Needs <KitDefs/>. */
export function MeshBackground({ id, x, y, w, h, base, spots, radius = 0, blur = 'kit-blur-xl' }: Box & {
  base: string; spots: { cx: number; cy: number; r: number; color: string; opacity?: number }[]; radius?: Radii; blur?: string;
}) {
  const clip = `${id}-clip`, d = roundedRect(x, y, w, h, radius);
  return (
    <g id={id}>
      <defs><clipPath id={clip}><path d={d} /></clipPath></defs>
      <path id={`${id}-box`} d={d} fill={base} />
      <g clipPath={`url(#${clip})`}>
        <g filter={`url(#${blur})`}>
          {spots.map((s, i) => <circle key={i} cx={s.cx} cy={s.cy} r={s.r} fill={s.color} opacity={s.opacity ?? 0.8} />)}
        </g>
      </g>
    </g>
  );
}

/** Stacked "paper" layers behind a card (offset copies), e.g. folder back sheets. */
export function Stack({ id, x, y, w, h, radius = 0, layers, fill, stroke, strokeWidth = 1.5, dx = 6, dy = -6, children }: Box & {
  radius?: Radii; layers: number; fill: string; stroke?: string; strokeWidth?: number; dx?: number; dy?: number; children?: ReactNode;
}) {
  return (
    <g id={id}>
      {Array.from({ length: layers }, (_, i) => layers - i).map((k) => (
        <path key={k} id={`${id}-layer-${k}`} d={roundedRect(x + dx * k, y + dy * k, w, h, radius)} fill={mix(fill, '#FFFFFF', 0.08 * k)} stroke={stroke} strokeWidth={strokeWidth} />
      ))}
      {children}
    </g>
  );
}
