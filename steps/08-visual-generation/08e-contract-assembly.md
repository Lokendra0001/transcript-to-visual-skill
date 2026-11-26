# 08e — Validation and Handoff

## Deterministic checks

Run all of these against the final outputs and record the results:

- **Renderer:** `render-report.json` shows status `rendered` with no errors, and its output hashes match the files on disk.
- **Rendering plan:** `python3 scripts/08-visual-generation/rendering_plan.py check --run-dir <run-dir>` exits 0. Every rendered library layer and raster is planned, and every planned library was rendered. Record its warnings (effects rendered without a matching planned trait).
- **SVG:** `python3 -c "import sys; sys.path.insert(0, 'scripts/08-visual-generation'); import validate_svg; print(validate_svg.validate('<run-dir>/step-08/infographic.svg'))"` prints `[]`.
- **Coverage:** every required Step 04 node and visual connection appears in `render-report.json` `nodes` or `connections`, and every Step 07 asset mapping appears in `assets`. Missing or unexpected IDs are errors.
- **Review:** `raster_workflow.py check-review` passes for the final PNG.
- **Footer:** the actual output and visual review satisfy the T01-derived asset rule and record its source fingerprint, or document the user's explicit per-run override and any verified replacement assets. A missing or incorrect required footer is not a pass.

These checks do not prove visual fidelity, logo identity or semantic accuracy; the 08d review covers those.

## Contract

Build the outputs with `output_contract.py` (`build_output_contract`, `build_validation_report`, `build_animation_handoff`).

Write `08-visual-generation.json` in the existing v1.0 shape with these fields:

- **`generation_method`:** `code_render_react_svg`, plus the renderer versions from `render-report.json`, the technologies used (`render_layers`) and every embedded raster from `images`, with its density.
- **`sources`:** paths and SHA-256 of Steps 03–07, the reference and every file in `step-08/src/`.
- **`design_system`:** a summary of `reference-blueprint.json` and `tokens.ts`, including the recorded adaptations.
- **`element_manifest`:** built from `render-report.json`. List each Step 04 node, connection and asset ID with its element ID and bounds. Do not infer roles or direction from ID names.
- **`asset_usage`:** each asset occurrence with its file, SHA-256 and element ID.
- **Portrait evidence:** reference the run-scoped portrait manifest and record each used photo's person, target, source, file hash and verification status; document neutral fallbacks or missing mandatory portraits.
- **`coverage_assessment`:** the coverage results.
- **`animation_handoff`:**
  - The element IDs that can be animated on their own.
  - The Step 04 reading order, and the direction of each connection that has one.
  - When `motion.ts` exists, its path, duration, target IDs and the final-frame check result.
- **`validation`:** the deterministic results and the visual review status.
- **Output paths and hashes:** for the SVG and PNG.

Write `08-validation-report.json` with these sections kept separate:

- deterministic results
- the visual review outcome, with its review hash
- warnings, such as estimated fonts or logo identity notes carried over from Step 07
- unresolved failures

## Status

| Status | When |
| --- | --- |
| `success` | Every check passes, the review approves the current hashes, and there are no warnings |
| `warning` | As for success, but with non-blocking warnings recorded |
| `incomplete` | Rendered, but a mandatory review item failed or wasn't checked |
| `blocked` | A tool or upstream input is missing |
| `error` | The run failed unexpectedly |

Steps 09–11 may use only the hashes recorded here.

Never overwrite an approved output silently; keep earlier versions under `history/`.
