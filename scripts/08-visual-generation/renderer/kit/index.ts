// Step 08 composition kit. Import as `@kit` (text, colour, shapes, effects, surfaces).
// Library layers are separate entry points so they are bundled only when a composition uses them:
//   `@kit/svgjs` (SVG.js), `@kit/zdog` (Zdog), `@kit/three` (Three.js), `@kit/antv` (AntV Infographic).
// Choose between them with `scripts/08-visual-generation/rendering_plan.py select` (simplest first).
export * from './text';
export * from './color';
export * from './shapes';
export * from './effects';
export * from './surfaces';
export * from './footer';
export { defer, renderScale } from './layer';
