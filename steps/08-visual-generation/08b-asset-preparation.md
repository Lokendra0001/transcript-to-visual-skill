# 08b — Content, Assets and Layout Plan

## Inventory

Run `python3 scripts/08-visual-generation/raster_workflow.py inventory --run-dir <run-dir>` and save the output as `step-08/content-asset-inventory.json`. Despite its older name, the tool is method-neutral. It extracts sections, nodes, connections, reading order, constraints, content items and asset mappings. It does not prove correctness or rendered coverage.

Check every required item against its authority:

- **Step 05 content:** `visible_text` must be used exactly as written. Keep qualifiers, values and optional notes.
- **Step 04:** nodes, connections (direction only when Step 04 states one), grouping and reading order.
- **Step 07:** asset occurrences.

## Assets

Check each logo file before use:

- It exists.
- Its SHA-256 matches Step 07.
- Its identity and warnings have been reviewed.
- Its transparency is suitable for the tile background.

Import logos straight from the run so the renderer embeds them as data URIs, for example `import hubspot from '../../assets/logos/asset-request-3.png'`. Never redraw, recolour, crop or swap a brand mark. Always keep its aspect ratio.

A missing required mark blocks success unless Step 07 recorded an authorised, verified fallback. Generic, non-brand icons may be drawn as plain SVG paths when the reference uses icons and no specific meaning is invented.

## People and portraits

When a named person is relevant to the approved visual, check whether the user supplied a suitable portrait. Otherwise, if external research is available and appropriate, search for an authentic photo, preferring the person's official profile or their organization's official website. Verify that the photo depicts the intended person using corroborating context such as their name, company and role; a name match or search-result thumbnail alone is not enough. Check the image's provenance and terms for the intended use. Do not infer an affiliation that the source does not establish or collect unnecessary personal information.

Record the person and target node, source page and asset URL, identity evidence, usage information, local file path, SHA-256 and visual-inspection result in a run-scoped portrait manifest. Download only through an available safe public-asset retrieval mechanism, inspect the actual file, and embed the local file in the SVG. Do not imply the existing logo pipeline automatically discovers or verifies portraits. If identity, use rights, access or a suitable image cannot be established, do not use a guessed image: record the reason and use a neutral labeled person icon or text where permitted; if a real photo is mandatory, mark the output incomplete and request usable material.

## Layout plan

Write `step-08/layout-plan.json` before writing components. It must contain:

- the canvas width (the height may grow to fit content) and the scale factor for the PNG
- the module order, each module's reference component type, and its grid position and size
- each Step 04 node, connection and asset occurrence, the module it sits in, and its planned stable element ID
- text style for each role, taken from the blueprint type scale, with the wrap width
- where adaptations from 08a apply

Expand the canvas or rebalance modules rather than shrinking text below the blueprint's smallest legible size. For a 1500 px-wide canvas, labels should stay at about 18 px or larger. Never drop content silently.

Reserve the full-width T01 footer using the asset and component in the main Step 08 instructions, unless explicitly overridden for this run. Record its bounds, footer asset and T01 reference paths and hashes, and spacing in `layout-plan.json`; expand the canvas to fit it. For requested replacements, record authorized content and verified replacement assets. Record assumptions and open questions in the plan.
