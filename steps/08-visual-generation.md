# 08 — Reference-Driven Visual Generation

## Objective

Use an available AI image-generation tool to create a publication-grade raster infographic directly from the selected visual reference and approved workflow data. The primary deliverable is a generated PNG, not a code-drawn SVG.

The selected reference is a template, not merely inspiration. Recreate its recognizable composition, proportions, spatial arrangement, typography, palette, background, panels, badges, connectors, and logo treatment as closely as possible, replacing its factual content with approved Step 04/05 content and Step 07 assets. Preserve the template's structure and visual identity while excluding its unrelated factual text, personal branding, and watermarks, except for the user-requested T01 footer below.

For T01, include the reference footer at the bottom: the left-side portrait, creator name and verification badge, and the right-side Pipelin.ai mark and wordmark, arranged and styled like the original. This is a specific user-requested exception to excluding reference branding. Use the actual reference or verified source assets when supported; do not claim a generated approximation is exact or verified.

The user-approved [ABM concept](../references/visual-quality/abm-playbook-concept.png) illustrates the expected finish for the T01 reference: a portrait infographic with a prominent title, numbered modular panels, multi-column groupings, readable nested content, compact tool tiles and clear flow. Inspect it when T01 is selected. It is a visual quality example, not an authoritative source of copy, relationships, or logos: it contains AI-generated details and may omit or misrepresent approved data. Other selected templates retain their own reference-specific design. The user permits a taller image: increase vertical space as needed for legible text, generous spacing, complete content and the footer, while retaining the recognizable reference design.

Use the image generator for composition and targeted image edits. Scripts may support input checks and record keeping, but must not substitute a coded SVG layout for image generation. A raster image is flat: do not claim editable text, vector components, stable element IDs, or animation-ready layers. If editable output is explicitly required, discuss a separate conversion or reconstruction after the image is approved.

## Preconditions

Require matching usable Step 03 v1.0, Step 04 v1.1, Step 05 v1.0, Step 06 v1.0, and Step 07 v1.0 artifacts. Accept `warning` only when its recorded limitation is non-blocking and every required asset mapping has an authorized disposition. Validate selected-reference fingerprints, prepared asset paths/fingerprints, required copy, targets, and run IDs using `scripts/08-visual-generation/validate_input.py`.

## Execution

1. **Reference Visual Inspection & Design System Extraction** ([08a](08-visual-generation/08a-reference-interpretation.md)):
   - Inspect the selected reference image (`reference_path` from Step 06).
   - Analyze composition, aspect ratio, typography hierarchy, palettes, card shapes, borders, shadows, connector styles, and asset badge presentation.
   - Record the design rules in `<run-dir>/step-08/design-system.json`.
   - Never copy factual text, author marks, or unrelated branding from the reference, except the specifically requested T01 footer.

2. **Asset and content preparation** ([08b](08-visual-generation/08b-asset-preparation.md)):
   - Prepare an exact inventory of required copy, relationships and approved asset mappings. Supply the reference image and relevant verified assets to the image tool when supported; otherwise record that accurate logo reproduction requires verification.
   - The executing AI chooses a pixel-based canvas and typography plan suited to the actual content and intended viewing size, without requiring the user to specify dimensions or fonts. Record the planned width and height in pixels, intended display size, font style and hierarchy, target approximate text sizes, content density, and rationale in `step-08/design-system.json`.

3. **Direct AI image generation** ([08c](08-visual-generation/08c-svg-composition.md)):
   - Use the available image-generation tool with the selected template, approved concept where applicable, exact approved content and prepared asset references. Save the generated image as `<run-dir>/step-08/preview.png` and retain the actual prompt and input references.
   - Reconstruct the reference's actual layout and component patterns; map approved content to corresponding template slots. When the user approves a particular layout, preserve its arrangement, title treatment, panel hierarchy, color, connectors and footer in subsequent refinements; edit the approved image rather than regenerating the whole layout. Resize or extend the canvas only where needed for legibility, keeping the recognizable arrangement. Approved content and correct relationships remain mandatory; do not restore placeholder bars or unapproved claims from a visual reference.
   - Request accurate content, relationships and logo appearance. Do not assert that generated logos are authentic or identical to prepared assets without inspecting them.
   - Prioritize the verified Step 07 logo or icon visually in each tool tile, with its exact name as a smaller readable supporting label. The final logo must come from the actual mapped source file, not an AI-redrawn interpretation of a contact sheet. Keep repeated occurrences identical. Use an explicitly authorized fallback only where the asset is unavailable or unsuitable; never invent a logo.
   - Give every box, tile and nested panel a continuous, crisp border that remains clearly visible against adjacent surfaces at the intended viewing size. Preserve the selected reference's border style and ensure contrast, corners and visual hierarchy are consistent.

4. **Visual Inspection & Iterative Refinement** ([08d](08-visual-generation/08d-visual-review.md)):
   - Visually inspect the actual generated PNG beside the reference at comparable size, including detailed crops, and explicitly compare composition, relative positions, proportions, components, typography, colors, connectors, and logo tiles.
   - Verify actual image width and height in pixels, logo identity and prominence, text clarity and readability at native and intended viewing sizes, box-border visibility, adequate spacing, hierarchy, sparse-section handling, and the complete reference footer. Check the bottom edge explicitly so the footer cannot be omitted or cropped.
   - If flaws exist, use targeted AI image edits or regeneration (maximum 3 bounded cycles) and document review in `<run-dir>/step-08/visual-review.json`. Bind each final review and report to the final PNG's SHA-256 and pixel dimensions; after any edit or replacement, all visual checks must be performed again. Never carry forward an earlier candidate's pass.

5. **Verification & Output Contract Assembly** ([08e](08-visual-generation/08e-contract-assembly.md)):
   - Verify the PNG file and review every required content item, relationship, logo occurrence and readability against the upstream inventory. Record actual visual evidence and unresolved discrepancies; do not treat OCR or generated metadata alone as proof.
   - Record that the image is flat and animation-ready layers are unavailable; never invent an element manifest.
   - Write `<run-dir>/08-validation-report.json` and `<run-dir>/08-visual-generation.json`.

## Output Contract — v1.0

```json
{
  "step": "08-visual-generation",
  "version": "1.0",
  "status": "success",
  "run_id": "<run-id>",
  "timestamp": "<iso-timestamp>",
  "sources": {},
  "design_system": {},
  "element_manifest": [],
  "asset_usage": [],
  "coverage_assessment": {},
  "animation_handoff": {},
  "validation": {},
  "warnings": [],
  "errors": []
}
```

Visual fidelity, visual quality, and semantic accuracy are mandatory acceptance gates. A valid image file, automated text detection, or matching colors alone cannot establish fidelity. If the reference structure cannot accommodate the required content without materially changing its design or distorting its meaning, record the conflict, mark the output incomplete, and request a decision; never report successful completion or a non-blocking warning for a materially different layout.

If an image-generation tool is unavailable, report that blocker and stop; do not silently replace the requested method with SVG code or claim an image was generated. When a visually good image contains missing, incorrect, unreadable or invented material, deliver it only as a clearly identified draft and mark verification incomplete.

Image-generation reference inputs do not guarantee exact preservation or placement of logo files. If the available image tool cannot insert original verified assets unchanged, do not certify generated approximations as authentic; mark the result incomplete and explain that a supported asset-placement workflow is needed. Respect the user's preference for direct image generation; do not silently switch to a coded layout or image-editing method.

For the current ABM run, a CRM card containing any gray horizontal placeholder or skeleton rows is a failed output even if the approved relationship appears elsewhere. A footer alone does not make a cramped image acceptable. Never mark readability or copy review as passed without inspecting the actual final PNG and its dense-section and footer crops and recording file hashes and findings.
