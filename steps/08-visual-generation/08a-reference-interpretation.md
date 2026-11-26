# 08a — Reference Blueprint

The goal is a render a viewer would recognise as the reference template filled with new content. That takes measurement, not impressions. Work from the reference file chosen in Step 06; use its original SVG, Figma export or written spec when one exists, and the PNG otherwise.

## Measure

Record the reference path and SHA-256, then measure with `reference_tools.py`. Use `info` for size and aspect ratio, and `palette` for dominant colours. Use `sample --points x,y …` for the exact fill of each surface, stroke, accent and text colour. Use `crop --scale 2` to study details. Save crops in `step-08/review/ref-*.png`.

Measure these in reference pixels, then convert to the output canvas scale:

- **Canvas:** width, height, aspect ratio, outer margins and background (flat, dotted, gridded, gradient), including pattern pitch and dot size.
- **Grid:** columns, gutters, module widths, vertical rhythm and how modules stack, snake or branch.
- **Typography:**
  - Title, section heading, label and body sizes; weights, case, letter-spacing and line height.
  - Name the closest installed font, and say whether the exact font is known or estimated.
- **Colour roles:** page, sheet, card, header band, accent 1 and 2, text, muted text, borders and connectors. Give each role a sampled hex value.
- **Shapes:**
  - Corner radii (and whether corners are plain arcs or smooth squircles), border widths and colours.
  - Stacked or offset "paper" layers, folder tabs, slanted edges, ribbons, badges, number blocks, organic or irregular shapes.
- **Surface and depth:**
  - Surface finish: flat, hard-offset (neo-brutalist), soft-shadowed, neumorphic, inset, glass, glossy or bevelled.
  - Shadows as layers: offset, blur, spread, colour and opacity of each (ambient vs key light), inner shadows and glows.
  - Light direction, highlights and gloss; gradients (type, angle, stops).
  - 3D elements and how they are drawn: flat-faced extrusions or isometric blocks, cylinders, rounded 3D objects, or realistic materials (metal, glass, reflections, soft contact shadows).
- **Connectors:** stroke width, colour, line style (solid, dashed, dotted), arrowheads, junction dots and elbow or curve style. When no line style is specified by the user or visible in the reference, record dashed as the default.
- **Logos and icons:** tile size, inner padding, logo box size, tile style and label position.
- **Decoration:** badges, breadcrumbs, icons, dividers, floating objects, background treatment (flat, dotted, grid, texture, mesh gradient) and footer.

Record only what the reference shows. A flat, minimal reference stays flat: no gradients, shadows, glass or 3D that it doesn't use.

Separate measured values from estimated ones. Note anything you can't resolve.

## Catalogue components

List every distinct component type in the reference, for example header band, numbered module card, list box, step box, logo tile, checklist row, tier ladder, connector and footer. For each one, record:

- anatomy and part sizes
- which traits are locked: shape, colours, strokes, radii, type
- which parts take dynamic content: the title, the number of rows or tiles, and the body
- how it grows when content is longer: wraps, gets taller, adds rows

Each catalogued type becomes one React component in 08c.

## Decide adaptations

Compare the catalogue with Steps 03–05 and the Step 06 adaptation notes. Keep the reference's composition unless the content can't fit legibly or a mandatory Step 04 layout requires a change. For example, a required side-by-side comparison may replace a snake flow.

Record every departure from the reference with:

- what changed
- why it changed
- which upstream requirement forces it
- how the reference's visual language is kept

Never add arrows, numbering, rankings or groupings that the reference shows but the content doesn't support. Do not carry over the reference's facts, names or branding except for the fixed T01 footer specified in the main Step 08 instructions.

## Choose rendering technology

For each catalogued component, list the visual traits it needs and let the selector pick the simplest capable technology:

```bash
python3 scripts/08-visual-generation/rendering_plan.py traits                     # trait vocabulary and kit building blocks
python3 scripts/08-visual-generation/rendering_plan.py select --traits extruded_blocks,gradients
```

Native SVG (`@kit`) covers shapes, gradients, shadows, glow, glass, neumorphism, neo-brutalism, patterns, textures, mesh backgrounds, flat-faced 3D blocks and cylinders. Escalate only when a trait requires it: SVG.js for programmatic path construction, Zdog for isometric or rounded pseudo-3D illustration, AntV for a structured component generated from data, Three.js for genuine materials and lighting (the only raster output). A component whose traits need two non-SVG libraries must be split. Choosing a heavier technology than the selector returns requires a written `reason`.

## Output

Write `step-08/reference-blueprint.json` with these fields:

- `reference`: path and sha256
- `canvas`
- `grid`
- `colors`: role → hex, plus `measured` or `estimated`
- `typography`
- `shapes`
- `connectors`
- `decoration`
- `components`: the catalogue
- `rendering_plan`: one entry per component, `{"component", "traits", "technology", "reason"?}`
- `adaptations`
- `uncertainties`

`tokens.ts` must be derivable from this file alone.
