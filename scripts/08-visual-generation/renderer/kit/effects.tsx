// SVG <defs> building blocks: gradients, filters and patterns. Place them inside the root <defs>
// (or a component's own <defs>) and reference them with url(#id). All values come from props:
// pass token colours and sizes; nothing here is tied to one template.
//
// Filter safety contract (checked by the renderer for brand logos): "outer" effects (Shadow, Glow)
// end with <feMergeNode in="SourceGraphic"/>, so the element itself is drawn unchanged on top.
// "Surface" effects (InnerShadow, Bevel, Noise) alter the element's pixels and must never sit on
// a logo image or any of its ancestors.

import { Fragment } from 'react';

export type Stop = [offset: number, color: string, opacity?: number];

const stops = (s: Stop[]) => s.map(([o, c, a = 1], i) => <stop key={i} offset={o} stopColor={c} stopOpacity={a} />);

/** Linear gradient at `angle` degrees (0 = left->right, 90 = top->bottom), multi-stop. */
export function LinearGradient({ id, stops: s, angle = 90, userSpace }: { id: string; stops: Stop[]; angle?: number; userSpace?: [number, number, number, number] }) {
  const a = (angle * Math.PI) / 180, dx = Math.cos(a) / 2, dy = Math.sin(a) / 2;
  const p = userSpace
    ? { x1: userSpace[0], y1: userSpace[1], x2: userSpace[2], y2: userSpace[3], gradientUnits: 'userSpaceOnUse' as const }
    : { x1: +(0.5 - dx).toFixed(4), y1: +(0.5 - dy).toFixed(4), x2: +(0.5 + dx).toFixed(4), y2: +(0.5 + dy).toFixed(4) };
  return <linearGradient id={id} {...p}>{stops(s)}</linearGradient>;
}

/** Radial gradient; centre, radius and focal point in bounding-box fractions. */
export function RadialGradient({ id, stops: s, cx = 0.5, cy = 0.5, r = 0.5, fx, fy }: { id: string; stops: Stop[]; cx?: number; cy?: number; r?: number; fx?: number; fy?: number }) {
  return <radialGradient id={id} cx={cx} cy={cy} r={r} fx={fx ?? cx} fy={fy ?? cy}>{stops(s)}</radialGradient>;
}

export type ShadowLayer = { dx?: number; dy?: number; blur?: number; color?: string; opacity?: number; spread?: number };

/**
 * Layered outer shadow: any number of offset/blur/colour layers (ambient + key light, or a hard
 * neo-brutalist offset with blur 0). Logo-safe: the element is merged unchanged on top.
 */
export function Shadow({ id, layers, pad = 0.4 }: { id: string; layers: ShadowLayer[]; pad?: number }) {
  return (
    <filter id={id} x={-pad} y={-pad} width={1 + pad * 2} height={1 + pad * 2} colorInterpolationFilters="sRGB">
      {layers.map(({ dx = 0, dy = 0, blur = 0, color = '#000000', opacity = 0.2, spread = 0 }, i) => (
        <Fragment key={i}>
          {spread ? <feMorphology in="SourceAlpha" operator={spread > 0 ? 'dilate' : 'erode'} radius={Math.abs(spread)} result={`s${i}m`} /> : null}
          <feGaussianBlur in={spread ? `s${i}m` : 'SourceAlpha'} stdDeviation={blur} result={`s${i}b`} />
          <feOffset in={`s${i}b`} dx={dx} dy={dy} result={`s${i}o`} />
          <feFlood floodColor={color} floodOpacity={opacity} result={`s${i}c`} />
          <feComposite in={`s${i}c`} in2={`s${i}o`} operator="in" result={`s${i}`} />
        </Fragment>
      ))}
      <feMerge>
        {layers.map((_, i) => <feMergeNode key={i} in={`s${i}`} />)}
        <feMergeNode in="SourceGraphic" />
      </feMerge>
    </filter>
  );
}

/** Ready-made shadow layer sets; `k` scales intensity (0.5 subtle .. 2 strong). */
export const shadowLayers = {
  soft: (k = 1, color = '#101828'): ShadowLayer[] => [
    { dy: 1 * k, blur: 1.5 * k, color, opacity: 0.06 * k },
    { dy: 6 * k, blur: 10 * k, color, opacity: 0.08 * k },
    { dy: 18 * k, blur: 28 * k, color, opacity: 0.06 * k },
  ],
  ambient: (k = 1, color = '#101828'): ShadowLayer[] => [{ dy: 2 * k, blur: 24 * k, spread: 2 * k, color, opacity: 0.1 * k }],
  hard: (dx = 6, dy = 6, color = '#000000'): ShadowLayer[] => [{ dx, dy, blur: 0, color, opacity: 1 }],
  lifted: (k = 1, color = '#101828'): ShadowLayer[] => [
    { dy: 2 * k, blur: 3 * k, color, opacity: 0.12 * k },
    { dy: 24 * k, blur: 32 * k, spread: -4 * k, color, opacity: 0.18 * k },
  ],
};

/** Outer glow in `color`; logo-safe. */
export function Glow({ id, color, blur = 8, opacity = 0.8, spread = 0 }: { id: string; color: string; blur?: number; opacity?: number; spread?: number }) {
  return <Shadow id={id} pad={0.6} layers={[{ blur, color, opacity, spread }, { blur: blur / 3, color, opacity: opacity * 0.6, spread }]} />;
}

/** Inner shadow (recessed / pressed surface). Changes the element's pixels: never on logos. */
export function InnerShadow({ id, dx = 0, dy = 2, blur = 4, color = '#000000', opacity = 0.25 }: { id: string; dx?: number; dy?: number; blur?: number; color?: string; opacity?: number }) {
  return (
    <filter id={id} x="-10%" y="-10%" width="120%" height="120%" colorInterpolationFilters="sRGB">
      <feComponentTransfer in="SourceAlpha" result="inv"><feFuncA type="table" tableValues="1 0" /></feComponentTransfer>
      <feGaussianBlur in="inv" stdDeviation={blur} result="b" />
      <feOffset in="b" dx={dx} dy={dy} result="o" />
      <feComposite in="o" in2="SourceAlpha" operator="in" result="clip" />
      <feFlood floodColor={color} floodOpacity={opacity} result="c" />
      <feComposite in="c" in2="clip" operator="in" result="shadow" />
      <feMerge><feMergeNode in="SourceGraphic" /><feMergeNode in="shadow" /></feMerge>
    </filter>
  );
}

/** Bevel / embossed edge lit from `azimuth` (deg) at `elevation` (deg). Changes pixels: never on logos. */
export function Bevel({ id, depth = 3, azimuth = 225, elevation = 45, specular = 0.6, shininess = 18 }: { id: string; depth?: number; azimuth?: number; elevation?: number; specular?: number; shininess?: number }) {
  return (
    <filter id={id} x="-5%" y="-5%" width="110%" height="110%" colorInterpolationFilters="sRGB">
      <feGaussianBlur in="SourceAlpha" stdDeviation={depth} result="b" />
      <feSpecularLighting in="b" surfaceScale={depth} specularConstant={specular} specularExponent={shininess} lightingColor="#FFFFFF" result="spec">
        <feDistantLight azimuth={azimuth} elevation={elevation} />
      </feSpecularLighting>
      <feComposite in="spec" in2="SourceAlpha" operator="in" result="lit" />
      <feComposite in="SourceGraphic" in2="lit" operator="arithmetic" k1={0} k2={1} k3={1} k4={0} />
    </filter>
  );
}

/** Blur filter for glows, mesh blobs and neumorphic shadow copies. */
export function Blur({ id, amount }: { id: string; amount: number }) {
  return <filter id={id} x="-50%" y="-50%" width="200%" height="200%"><feGaussianBlur stdDeviation={amount} /></filter>;
}

/** Film-grain / paper texture (deterministic feTurbulence). Apply to an overlay rect, not to content. */
export function Noise({ id, frequency = 0.9, opacity = 0.06, seed = 3, color = '#000000' }: { id: string; frequency?: number; opacity?: number; seed?: number; color?: string }) {
  return (
    <filter id={id} x="0" y="0" width="100%" height="100%" colorInterpolationFilters="sRGB">
      <feTurbulence type="fractalNoise" baseFrequency={frequency} numOctaves={2} seed={seed} stitchTiles="stitch" result="t" />
      <feColorMatrix in="t" type="matrix" values={`0 0 0 0 0  0 0 0 0 0  0 0 0 0 0  0 0 0 ${opacity * 3} 0`} result="a" />
      <feFlood floodColor={color} result="c" />
      <feComposite in="c" in2="a" operator="in" />
    </filter>
  );
}

/** Dot grid pattern. */
export function DotPattern({ id, pitch, dot, color, bg }: { id: string; pitch: number; dot: number; color: string; bg?: string }) {
  return (
    <pattern id={id} width={pitch} height={pitch} patternUnits="userSpaceOnUse">
      {bg ? <rect width={pitch} height={pitch} fill={bg} /> : null}
      <circle cx={pitch / 2} cy={pitch / 2} r={dot} fill={color} />
    </pattern>
  );
}

/** Square grid pattern (graph paper). */
export function GridPattern({ id, pitch, stroke, width = 1, bg }: { id: string; pitch: number; stroke: string; width?: number; bg?: string }) {
  return (
    <pattern id={id} width={pitch} height={pitch} patternUnits="userSpaceOnUse">
      {bg ? <rect width={pitch} height={pitch} fill={bg} /> : null}
      <path d={`M${pitch} 0 H0 V${pitch}`} fill="none" stroke={stroke} strokeWidth={width} />
    </pattern>
  );
}

/** Diagonal stripe pattern (hatching). */
export function StripePattern({ id, pitch, stroke, width = 1, angle = 45, bg }: { id: string; pitch: number; stroke: string; width?: number; angle?: number; bg?: string }) {
  return (
    <pattern id={id} width={pitch} height={pitch} patternUnits="userSpaceOnUse" patternTransform={`rotate(${angle})`}>
      {bg ? <rect width={pitch} height={pitch} fill={bg} /> : null}
      <line x1={0} y1={0} x2={0} y2={pitch} stroke={stroke} strokeWidth={width} />
    </pattern>
  );
}

/**
 * Shared defaults that Surface finishes reference: gloss and glass-edge gradients and blur filters.
 * Render once inside the root <defs> when any Surface finish other than flat/brutalist is used.
 */
export function KitDefs() {
  return (
    <>
      <LinearGradient id="kit-gloss" angle={90} stops={[[0, '#FFFFFF', 0.55], [0.45, '#FFFFFF', 0.12], [0.46, '#FFFFFF', 0], [1, '#FFFFFF', 0]]} />
      <LinearGradient id="kit-sheen" angle={90} stops={[[0, '#FFFFFF', 0.35], [1, '#FFFFFF', 0]]} />
      <LinearGradient id="kit-glass-edge" angle={60} stops={[[0, '#FFFFFF', 0.95], [0.5, '#FFFFFF', 0.25], [1, '#FFFFFF', 0.6]]} />
      <InnerShadow id="kit-inner" dy={3} blur={5} opacity={0.22} />
      <Bevel id="kit-bevel" depth={3} />
      <Blur id="kit-blur-sm" amount={4} />
      <Blur id="kit-blur-md" amount={9} />
      <Blur id="kit-blur-lg" amount={22} />
      <Blur id="kit-blur-xl" amount={60} />
    </>
  );
}
