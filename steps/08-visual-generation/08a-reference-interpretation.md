# 08a — Reference Interpretation & Design System Extraction

## Objective

The executing AI visually inspects the selected reference image and extracts its visual design language into a reusable design specification.

## Input

- Selected reference image path from Step 06: `<run-dir>/06-template-selection.json` -> `template_selections[0].reference_path`.
- Reference design direction from Step 06: `design_direction`.

## Execution

1. **Multimodal Visual Inspection**:
   - Inspect the actual reference image (`references/templates/<reference_path>`).
   - Analyze:
     * **Composition & Spatial Structure**: Canvas orientation (portrait/landscape/square), column grid, modular cards, sequence flow, gutter width, margins.
     * **Palette & Contrast**: Background color/texture, primary surfaces, secondary surfaces, accent colors (header tabs, badges, terminal highlight), text contrast.
     * **Typography Hierarchy**: Display title size/weight, step header typography, section labels, item body copy, chip/badge labels, letter spacing.
     * **Containers & Cards**: Corner radii, borders, drop shadows, header tab styling, nested panel styling.
     * **Connectors & Flow Indicators**: Stroke style (solid, dashed, dotted), color, thickness, arrowhead shapes, routing patterns (direct, orthogonal, curved).
     * **Logo & Icon Treatments**: Tile dimensions, aspect ratio, background fill, border/shadow, placement relative to labels.

2. **Author `<run-dir>/step-08/design-system.json`**:
   - Record the extracted tokens and design rules.
   - Record the reference canvas proportions and a region-by-region map with normalized bounds, reading order, panel relationships, component patterns, and dominant visual anchors. Record reference-derived type, spacing, colors, texture, border, shadow, and logo treatment with evidence from the image.
   - Map approved content to reference regions and identify repeated slots and any content that cannot fit. Record each necessary deviation and its reason. A different grid or wholesale single-column layout is a material deviation, not a routine adaptation.
   - Do NOT copy the reference template's original factual content, authors, watermarks, or personal branding.

## Completion Criteria

- `<run-dir>/step-08/design-system.json` authored with complete palette, typography, spacing, border, and connector rules.
- Design choices faithfully reflect the selected reference template.
