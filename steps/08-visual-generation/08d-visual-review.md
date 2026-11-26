# 08d — Visual Review Against the Reference

The render report only proves technical soundness. Whether the image matches the template and carries the right content is a visual judgment, made by looking at the actual PNG.

## Each iteration

1. Copy `src/`, `infographic.svg`, `infographic.png` and `render-report.json` into `history/vN/`.
2. Make a side-by-side sheet at the same height:
   ```bash
   uv run --quiet --with pillow python scripts/08-visual-generation/reference_tools.py side-by-side --left <reference> --right step-08/infographic.png --out step-08/review/vN-side-by-side.png
   ```
3. Crop matching regions from the reference and the render at native size, for example the header, one module of each component type, logo tiles, connectors and the bottom edge. Compare them in pairs.
4. Write down every observed defect. Fix it in tokens, layout or components, never by editing the output SVG by hand. Re-render and review the whole image again, because a local change can move everything below it.

The default is at most four iterations. Stop early once nothing is left to fix, and say what remains if the limit is reached.

## What to compare

**Reference fidelity.** For each locked trait in the blueprint, check:

- canvas proportion and margins
- the background pattern
- header construction
- module anatomy: tabs, number blocks, slants and paper layers
- palette roles and sampled colours (use `sample` on the render too)
- type sizes, weights and case
- stroke widths, radii and shadows
- connector style
- logo tile style
- surface finish, depth and lighting: gradient smoothness and direction, shadow softness and consistency between components, highlight placement, corner smoothness
- 3D and decorative elements: projection, proportions, placement, and whether each one appears in the reference
- overall density and whitespace

Crop every library layer (SVG.js, Zdog, Three.js, AntV) at native size. Check Three.js edges against the background for halos, and AntV text against Step 05.

A viewer should see the same template. Record each approved adaptation from the blueprint and confirm that it keeps the reference's visual language.

**Content.** Check every required Step 05 item character by character, including qualifiers, values, order and grouping. Look for any text that isn't in Step 05.

**Relationships.** For every Step 04 connection, trace the path from its source to its target. Check that it is attached at both ends, that dashed segments remain visibly continuous as a path, and that any arrowhead points the stated way. Verify the requested or reference line style, or the dashed default when neither specifies one. Check that no connector suggests a relationship Step 04 doesn't contain.

**Assets.** For every occurrence, check:

- it is the correct Step 07 file and identity, in the right context
- its proportions, padding and size within the tile
- it has no halo or wrong background

For each person photo, compare the actual placement with the 08b portrait manifest and inspect identity evidence, image provenance, permitted use and appearance. Record unverified or mismatched identity as a defect; do not treat a search result or planned image as proof.

**Quality.**

- No clipping, overlap or cramped padding.
- Text is readable at native size and at the intended viewing size. Check a 50% downscale for social feeds.
- Alignment and spacing are consistent between neighbouring modules.
- Inspect the complete bottom edge against T01: footer band and divider, portrait, name, badge, Pipelin.ai mark and wordmark, alignment, spacing, legibility and cropping. Confirm the default asset and T01 fingerprints; do not claim independent verification of the extracted identities. For explicit replacements compare authorized content and verified assets. Record missing or incorrect required items as blocking defects.
- No empty region sits next to compressed content.

**Motion** (when `motion.ts` exists):

- Capture frames from `build/motion.html#t=<seconds>` at the start, at key beats and at the end.
- Confirm the order matches Step 04 and that required content is readable when the animation finishes.
- Confirm the render report shows `final_frame_matches_static: true`.

## Record

Write `step-08/visual-review.json` with these fields:

- `image_sha256` and `dimensions` of the final PNG
- `reference`: path and sha256
- `checks`: one entry for each of `design_quality`, `reference_fit`, `readability`, `content_accuracy`, `relationship_accuracy`, `asset_identity`, `asset_placement` and `unauthorized_content`, each with a `status` and specific `evidence`
- `content`, `assets` and `relationships`: one row per required ID, with a `status` and observed `evidence` that names the region where it was seen
- `iterations`: each version's hashes, the defects found and the fixes made
- `remaining_issues`

Then run:

```bash
python3 scripts/08-visual-generation/raster_workflow.py check-review --image <run-dir>/step-08/infographic.png --review <run-dir>/step-08/visual-review.json --inventory <run-dir>/step-08/content-asset-inventory.json
```

It checks that the review is complete and up to date, not whether its judgments are true. Never mark an item as passed unless you actually inspected it.
