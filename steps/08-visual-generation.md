# 08 — Code-Based Visual Generation (React + SVG, GSAP-ready)

Build the infographic as code. The executing agent studies the Step 06 reference, writes a React + SVG composition that reproduces that reference's design system with this run's approved content, and renders it locally into an editable `infographic.svg` and a high-resolution `infographic.png`. The result must look like it belongs to the reference template: same component types, proportions, palette, type scale, line weights, radii, background treatment and decoration. Only the content, module count and arrangement adapt to Steps 04–05.

Never use AI image-generation models or services, remote rendering services, invented or redrawn brand marks, or a raster picture wrapped in SVG. All rendering happens on this machine.

## Toolchain

Everything lives in the repository:

- **Renderer:** `scripts/08-visual-generation/renderer/` contains React 19, ReactDOM, GSAP 3, esbuild and the rendering libraries below, pinned in its `package.json`. `render.mjs` bundles the run's composition, renders it in headless Google Chrome (network blocked, WebGL via SwiftShader), writes `infographic.svg` from the live DOM, screenshots that SVG to `infographic.png`, and runs layout, reference, raster-resolution and logo-safety checks in the browser.
- **Composition kit (`@kit`):** reusable, parameterised components for premium visuals: shapes (squircles, per-corner radii, tabbed panels, ribbons, badges, chevrons, seeded blobs, waves, curves), effects (multi-stop gradients, layered/ambient/hard shadows, inner shadow, glow, bevel, grain, dot/grid/stripe patterns), surfaces (`Surface` with flat, brutalist, soft, neumorphic, inset, glass, glossy and bevel finishes; `Block3D`, `Cylinder`, `Orb`, `Stack`, `Ribbon`, `Badge`, `Blob`, `MeshBackground`). All native SVG. Catalogue and rules: [08c](08-visual-generation/08c-svg-composition.md#composition-kit).
- **Library layers:** `@kit/svgjs` (SVG.js: programmatic path construction, `fitPath`), `@kit/zdog` (Zdog: isometric and rounded pseudo-3D, output as native paths), `@kit/three` (Three.js: realistic materials, lighting, reflections and glass, embedded as a transparent PNG at ≥ the capture scale) and `@kit/antv` (AntV Infographic: structured process, timeline, hierarchy and comparison components, with its HTML text converted to native `<text>`). Each is bundled only when imported.
- **Technology selection:** `scripts/08-visual-generation/rendering_plan.py` maps each reference trait to the technologies that can produce it, simplest first (`traits`, `select --traits …`), and `check --run-dir` verifies the blueprint's `rendering_plan` against what the renderer actually produced.
- **Reference tools:** `scripts/08-visual-generation/reference_tools.py` measures and crops the reference (`info`, `palette`, `sample`, `crop`, `side-by-side`). It needs Pillow; run it as `uv run --quiet --with pillow python …`.
- **Existing validators:** `validate_input.py`, `validate_svg.py`, `raster_workflow.py` (`inventory` and `check-review`) and `output_contract.py`.

One-time setup, and again after `package.json` changes:

```bash
npm --prefix scripts/08-visual-generation/renderer ci
```

The renderer requires Node.js 20 or newer and Google Chrome; pass `--chrome <path>` or set `CHROME_PATH` if Chrome isn't in its default macOS location. If a tool is missing and can't be installed, stop with status `blocked`. Name the missing tool. Never substitute another rendering method without telling the user.

GSAP is free to use under its Standard License, including commercial use; record the version in the render report.

## Inputs and authority

Require matching, usable Steps 03 v1.0, 04 v1.1, 05 v1.0, 06 v1.0 and 07 v1.0. Run:

```bash
python3 scripts/08-visual-generation/validate_input.py --run-dir <run-dir>
```

It checks metadata only. You still check content, relationships, reference fingerprint, asset identity and provenance yourself.

Each upstream step is the authority for one thing:

- **Step 04:** structure, nodes, relationships and mandatory layout.
- **Step 05:** visual content copy. Use `representation.visible_text` exactly as written; the fixed T01 footer below is an authorized separate branding element.
- **Step 06:** which reference to reproduce, and the adaptations it approved.
- **Step 07:** which logo files may appear, and authorised fallbacks.

The user's explicit instructions override reference styling. Never invent facts, flows, rankings or logos. Never silently drop content or import reference text or branding, except for the fixed T01 footer required below.

For connections between nodes, follow an explicitly requested line style or the selected reference's visible connector style. If neither specifies a style, use dashed lines by default; add arrowheads only where Step 04 establishes direction. Dashed styling is a visual default and must not imply an unsupported relationship.

When an identifiable person is relevant to the approved visual, consider a verified real photo instead of a generic person icon. Research and prepare photos as described in [08b](08-visual-generation/08b-asset-preparation.md); a name appearing incidentally in a transcript does not by itself require a portrait. Never guess an identity or fabricate a likeness.

## Fixed footer

Include a footer in every Step 08 output by default, regardless of the selected template. Reproduce the footer of `references/templates/T01-modular-gtm.png`: a full-width white band at the bottom, separated from the content by a thin grey horizontal rule; a left-aligned circular portrait, **Sumeru Chatterjee** and blue verification badge; and a right-aligned green Pipelin.ai mark and black wordmark. Match T01's spacing, alignment, proportions and visual treatment, scaling to the canvas. Keep the full footer visible with adequate padding; expand the canvas rather than cropping or compressing content.

Use the exact reference-derived strip `references/assets/t01-footer.png` through the reusable `Footer` component from `@kit`. This explicitly authorized default is a raster footer embedded in the SVG; the rest of the infographic must remain genuinely editable vector content. Record the T01 reference and footer asset hashes and reserve `footerHeight(width)` at the bottom of the canvas. Do not misrepresent the extracted portrait or branding as independently verified original assets. An explicit user instruction for a particular run to change or omit the footer overrides this default. For changes, supply authorized replacement content and verified embedded assets to the component, or use an explicitly requested alternative; never invent a replacement identity. Record the choice in the layout plan and inspect the entire bottom edge.

## Run layout

Everything below lives in `<run-dir>/step-08/`. Files are written by the agent unless marked (renderer).

| Path | Content |
| --- | --- |
| `reference-blueprint.json` | Measured design system of the reference, including its `rendering_plan` ([08a](08-visual-generation/08a-reference-interpretation.md)) |
| `content-asset-inventory.json` | Content, relationship and asset inventory ([08b](08-visual-generation/08b-asset-preparation.md)) |
| `layout-plan.json` | Module order, sizes, grid and placement of every node, connection and asset |
| `src/tokens.ts` | Colours, fonts, type scale, strokes, radii, spacing, all taken from the blueprint |
| `src/components/*.tsx` | One component for each reference component type |
| `src/Infographic.tsx` | Root composition. Default export, renders `<svg id="infographic">` |
| `src/motion.ts` | Optional GSAP timeline ([08c](08-visual-generation/08c-svg-composition.md#motion-layer-gsap)) |
| `infographic.svg`, `infographic.png`, `render-report.json` | Outputs (renderer) |
| `build/` | Bundled pages, including `motion.html` for playback (renderer) |
| `review/` | Reference crops, render crops and side-by-side sheets |
| `history/vN/` | Each iteration's `src/`, SVG, PNG and render report, kept for comparison |
| `visual-review.json` | Visual review record ([08d](08-visual-generation/08d-visual-review.md)) |

## Execution

1. **Blueprint the reference** per [08a](08-visual-generation/08a-reference-interpretation.md). Measure it: canvas, grid, palette (sampled hex values), type scale, strokes, radii, surface finish, depth, lighting, shadows, connectors and decoration. Catalogue every component type, decide which traits are locked and which regions take dynamic content, and choose each component's rendering technology with `rendering_plan.py select`.
2. **Inventory content and assets** and plan the layout per [08b](08-visual-generation/08b-asset-preparation.md).
3. **Compose in React + SVG** per [08c](08-visual-generation/08c-svg-composition.md). Write `tokens.ts` first, then one component per reference component type, then `Infographic.tsx`. Add `motion.ts` only when animation is requested or approved.
4. **Render:**
   ```bash
   node scripts/08-visual-generation/renderer/render.mjs --run-dir <run-dir> --scale 2
   ```
   Exit code 0 means every check in the render report passed. Exit code 2 means the report lists errors such as text overflow, out-of-canvas elements, unembedded images or a motion final frame that doesn't match the static image. Fix every error before reviewing.
5. **Review against the reference** per [08d](08-visual-generation/08d-visual-review.md). Make side-by-side sheets and crops at native size, fix the code, re-render and repeat. Keep each iteration in `history/`. The default is at most four iterations; the user may allow more when the goal is a close match.
6. **Validate and hand off** per [08e](08-visual-generation/08e-contract-assembly.md).

## Gate

Report `success` only when all of these hold:

- The renderer exits 0.
- `rendering_plan.py check --run-dir <run-dir>` exits 0.
- `validate_svg.py` reports no errors.
- Every required content item, relationship and asset occurrence is present and correct in the actual PNG.
- The default footer uses the recorded T01-derived asset, is complete, legible, uncropped and visually checked against T01; any explicit replacement uses authorized content and verified assets.
- `raster_workflow.py check-review` passes for the final PNG hash.
- The visual review approves the match to the reference for the current output hashes.

Report `incomplete` when the render works but the review finds unresolved mandatory defects. Report `blocked` when tools or inputs are missing. Never describe a planned or partly built composition as rendered. Keep earlier run artifacts; never silently overwrite an approved output.
