# 08e — Verification and Output Contract

Verify the generated PNG exists, decodes and has adequate dimensions. Review the actual image against the complete required content, relationship and asset inventory, including readable copy and logo identity. OCR or automated image checks can assist but do not alone prove semantic or visual correctness. Document missing or unverified items, the final visual review and the reference-fidelity gate in `<run-dir>/08-validation-report.json`.

Write `<run-dir>/08-visual-generation.json` using the Step 08 contract. Record the real generation tool, prompt and inputs, preview path, content and asset coverage, review outcome, warnings and errors. Since the output is a flat image, set `element_manifest` to an empty list and explicitly set the animation handoff to unavailable: do not claim SVG editability, stable IDs, layers, or downstream readiness. The existing SVG validators do not validate the contents of a generated PNG and must not be represented as doing so.

Mark the output successful only when the final PNG passes the visual, fidelity, completeness and accuracy reviews. Otherwise mark it incomplete and explain the failed checks. Stop after Step 08.
