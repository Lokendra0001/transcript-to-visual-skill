# 08c — React + SVG Composition

Write TypeScript React components that output plain SVG. The renderer bundles `step-08/src/Infographic.tsx` with esbuild, mounts it in headless Chrome after fonts load, and serializes the live `<svg>` element. Whatever the browser shows is exactly what ships.

## Structure

- **`src/tokens.ts`:** every visual constant from `reference-blueprint.json`, such as `colors`, `fonts`, `type`, `stroke`, `radius`, `space`, `shadow` and `pattern`. Components never hard-code a colour or size that belongs in tokens.
- **`src/content.ts`:** loads the approved inputs by importing the upstream JSON directly, for example `import writing from '../../05-content-writing.json'`. It exposes a lookup such as `text('cnt-…')` that returns `representation.visible_text` and throws when an ID is missing. Never retype copy into components.
- **`src/layout.ts`:** pure functions that turn content, tokens and the layout plan into positioned boxes.
  - Wrap text with `wrapText(text, font, maxWidth)` from `@kit`, which measures with the browser's real fonts.
  - Size every box from its content plus the blueprint padding.
  - Place modules on the blueprint grid and compute connector endpoints from the boxes they join.
  - Each module's height grows with its content. The canvas height is the sum.
- **`src/components/*.tsx`:** one component per catalogued reference component type, for example `HeaderBand`, `ModuleCard`, `ListBox`, `StepBox`, `LogoTile`, `CheckRow`, `TierLadder` and `Connector`. Props carry content and positions. Shape, colour and stroke come from tokens.
- **`src/Infographic.tsx`:** the default export. It renders `<svg id="infographic" xmlns="http://www.w3.org/2000/svg" width={W} height={H} viewBox={`0 0 ${W} ${H}`}>`. `defs` hold the patterns, markers, gradients, clip paths and font faces, followed by the components in reading order.

Import shared helpers from `@kit` and library layers from `@kit/svgjs`, `@kit/zdog`, `@kit/three` and `@kit/antv`. Import `react`, `gsap` and image or font files normally; the renderer resolves them from its own `node_modules`. Image and font imports become embedded data URIs.

## Composition kit

Build with the kit instead of re-implementing effects per run. Every component takes its colours, sizes, radii, depth and light from props, so feed it from `tokens.ts`; nothing in the kit is tied to one template. Use only what the blueprint's `rendering_plan` lists.

| Module | Provides |
| --- | --- |
| `@kit` shapes | `roundedRect` (per-corner radii), `squircle`, `tabbedPanel`, `ribbon`, `polygon`/`roundedPolygon` (stars, hexagons), `scallop`, `blob` and `smoothClosed` (seeded, deterministic), `wave`, `chevron`, `curve`, `orth`, `extrusion` |
| `@kit` effects (place in `<defs>`) | `LinearGradient` (angle, multi-stop), `RadialGradient`, `Shadow` with `shadowLayers.soft/ambient/lifted/hard`, `Glow`, `InnerShadow`, `Bevel`, `Blur`, `Noise`, `DotPattern`, `GridPattern`, `StripePattern`, `KitDefs` |
| `@kit` surfaces | `Surface` (finishes `flat`, `brutalist`, `soft`, `neumorphic`, `inset`, `glass`, `glossy`, `bevel`; radius or squircle `smooth`; `depth`, `light`, `shadow`, `tint`), `Block3D` (oblique or isometric extrusion), `Cylinder`, `Orb`, `Stack`, `Ribbon`, `Badge`, `Blob`, `MeshBackground` |
| `@kit` colour | `mix`, `lighten`, `darken`, `contrast`: derive faces, highlights and shadows from one token colour, and check text contrast |
| `@kit/svgjs` | `SvgJsLayer` (draw with the SVG.js API; inlined as native SVG), `fitPath` (fit any path into a box, proportions kept) |
| `@kit/zdog` | `ZdogLayer` (build a Zdog scene; `ISO` rotation for isometric), output as native `<path>` |
| `@kit/three` | `ThreeLayer` with `studioLights`, `environment` (reflections), `groundShadow`, `roundedBox`; renders a transparent PNG at the capture scale × `supersample` |
| `@kit/antv` | `AntvLayer` (AntV Infographic syntax in a box; text converted to native `<text>`; pass an installed `font`, no `icon` fields) |

Rules for the kit:

- Put `<KitDefs />` in `<defs>` whenever a `Surface` finish other than `flat` or `brutalist`, a `MeshBackground` or a kit blur is used. The renderer fails on any unresolved `url(#…)`.
- Library layers render into a nested `<svg id=… data-render="svgjs|zdog|antv">`, or an `<image data-render="three" data-raster="three">`. Ids they generate are prefixed with the layer id. Animate the layer by its id. Inner library elements have no stable ids.
- Text that must stay editable and checkable (`data-fit`) belongs in native `<text>`, not inside a Zdog or Three.js layer.
- **Brand logos:** only outer effects may wrap a logo: `Shadow` or `Glow`, which draw the element unchanged on top. Never put a logo under `InnerShadow`, `Bevel`, `Noise`, a mask, opacity below 1, a skew or a non-uniform scale. The renderer rejects all of these.
- Three.js is raster. Use it only for traits that need it (`realistic_3d`), never for text, logos or connectors. Keep its background transparent.
- AntV: use it for one structured region at a time inside the composition, never as the whole infographic. Map its colours to tokens with `options` (theme, palette) and check its text against Step 05 like any other text.

## Rules the renderer enforces

- **Root:** a single root `<svg id="infographic">` with numeric `width`, `height` and a `viewBox`.
- **IDs:**
  - Every `id` is unique, stable and meaningful.
  - Use Step 04 IDs for nodes, sections and connections, Step 07 asset requirement IDs for logos, and suffixes such as `-box`, `-label` and `-logo` for parts.
- **Data attributes:**
  - `data-node="<Step 04 node id>"` on each node's group.
  - `data-connection="<Step 04 connection id>"` on each connector.
  - `data-asset="<asset requirement id>"` on each logo `<image>`.
- **Text fit:** `data-fit="<box element id>"` on every text block that must stay inside a box. The renderer fails the run when the text's rendered bounds leave that box.
- **Canvas bounds:** every `data-node`, `data-connection` and `data-asset` element must sit inside the canvas.
- **Images:** embedded data URIs only. Never use `preserveAspectRatio="none"`.
- **Forbidden elements:** no `foreignObject`, no `<script>`, and no HTML inside the SVG.
- **References:** every `url(#…)` and `href="#…"` resolves to an element in the SVG.
- **Brand logos:** no filter other than an outer shadow or glow on the logo or any ancestor, no mask, no transparency, no skew, rotation or non-uniform scale.
- **Rasters:** every `data-raster` image (Three.js) has at least the PNG capture scale in pixel density.
- **No network:** Chrome resolves no hosts, so remote fonts, icons or images never load. Embed everything.

## Rules you are responsible for

- **Fidelity:** every component reproduces its reference counterpart's measured traits, including tabs, slants, offset paper layers, hard shadows, number blocks, dotted backgrounds and connector style. Build these from SVG primitives (`rect`, `path`, `circle`, `pattern`, `marker`), never from bitmaps of the reference.
- **Text:**
  - Use real `<text>` and `<tspan>`, so the result stays editable.
  - Use the blueprint type scale only.
  - Body text is never as heavy as headings.
- **Portable styling:**
  - Use SVG attributes or a `<style>` inside the SVG.
  - CSS files imported into the page don't travel with `infographic.svg`, so don't use them for visual styling.
  - For a custom font, import the font file and declare `@font-face` with that data URI inside the SVG `<style>`.
  - Otherwise use installed fonts, and record the font names from `render-report.json` in the review.
- **Relationships:** draw a connector only for a Step 04 connection. Use the user's requested line style first, then the reference's connector style; if neither specifies one, use a dashed stroke (for example `strokeDasharray` with spacing scaled to the line width). Draw an arrowhead only when Step 04 gives a direction, and point it from source to target. Show grouping with containers, not arrows.
- **People:** use a locally embedded, identity-verified and suitable real portrait from the 08b portrait manifest when available and appropriate; preserve its proportions and never substitute an unverified likeness. Otherwise use the documented neutral fallback or block if a portrait was mandatory.
- **Logos:** keep the original proportions. Size the logo box from the blueprint tile and keep the padding.
- **Footer:** import `Footer` and `footerHeight` from `@kit`; reserve `footerHeight(width)` at the bottom and render `<Footer width={width} y={footerY} />`. The default embeds the exact T01-derived raster strip. Override only requested fields, for example `<Footer width={width} y={footerY} content={{name: 'New Name'}} />`; optional fields are `name`, `portraitHref`, `brandHref`, `brandLabel` and `badgeHref` (set `badgeHref: null` to remove the badge). Unspecified fields retain T01 artwork; changed text is editable. Verify retained portrait, name, badge and branding remain appropriate together, and supply authorized, verified embedded replacement assets when needed. The customized version is an adaptation, not an exact T01 pixel match. An explicit no-footer instruction takes precedence.
- **Determinism:** no `Date`, unseeded randomness or network calls. Use the kit's seeded `rng`, `blob` and `Noise`. The same inputs must produce the same SVG.
- **Restraint:** apply effects, depth and decoration only where the reference has them. If a render looks flat, generic or repetitive compared with the reference, refine the components. Don't add effects the reference lacks.

## Motion layer (GSAP)

The static SVG is the master and the last frame of any animation. Write `src/motion.ts` only when the user asked for animation, or when Step 09 is planned and the user approved it. It exports:

```ts
export function buildTimeline(svg: SVGSVGElement, gsap: typeof import('gsap').gsap): gsap.core.Timeline
```

Rules:

- **End state:** use `from` and `fromTo` tweens that end exactly at the static state, or tweens that return to it.
  - The renderer runs `#check`: it jumps the timeline to its end and fails if any element's position, size, opacity, visibility or dash offset differs from the static render.
- **Targets:** select by element ID inside `svg` only. Every animated element must have an `id`.
- **What to animate:**
  - Opacity, translate and scale on groups.
  - `strokeDasharray` with `strokeDashoffset` to draw connectors.
  - Small emphasis pulses that return to rest.
- **What not to animate:**
  - Never change text content, logo colours or proportions, or layout.
  - Never animate anything into a state that hides required content at the end.
- **Reading order:** follow the Step 04 reading order. Move along a connector only in its Step 04 direction, and never move along non-directional groupings.

The renderer also writes `step-08/build/motion.html`:

- Opened plainly, it plays the timeline, so you can watch it.
- With `#t=<seconds>` it pauses at that time, so headless Chrome can capture exact frames.
- With `#check` it runs the final-frame test.

Step 09 decides whether the deliverable is animated and owns any exported animation format. Step 08 only guarantees that the master is ready for motion and that the timeline returns to it.
