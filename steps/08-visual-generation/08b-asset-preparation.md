# 08b — Asset Preparation & Text Measurement

## Objective

Prepare a traceable content and asset inventory for direct AI image generation and later visual verification.

## Input

- Verified assets and mappings from Step 07 (`<run-dir>/07-logo-retrieval.json`).
- Approved copy and terminology from Step 05 (`<run-dir>/05-content-writing.json`).

## Execution

1. **Asset references**:
   - List verified Step 07 files and their occurrence-level mappings. Supply compatible files to the image tool when possible and note any that cannot be supplied.
   - Record approved fallback labels and verify generated marks visually; a generated approximation is not proof of an authentic logo.
   - Plan an icon-forward tile for every mapped tool occurrence: the verified mark is the visual focus and the exact tool name is a smaller readable label. Record which actual files can be provided to the image tool and any marks that are missing, unverified or illegible. Avoid silently substituting text for a suitable available logo.

2. **Content inventory**:
   - Record exact required Step 05 copy, Step 04 grouping and relationships, and Step 07 mapping for every occurrence. Use this checklist to prepare the prompt and inspect the resulting image.

3. **Canvas and typography plan**:
   - AI selects an appropriate width and height in pixels based on the number of content items, label lengths, grouping, reference style, required footer, and intended viewing or sharing size. Increase height or width where needed; avoid squeezing dense content into a preset aspect ratio. Choose a readable font style and a hierarchy for title, panel headings, body text and labels, with estimated size ranges in pixels and sufficient line spacing, padding and contrast.
   - Discover the available image generator's actual dimension and aspect-ratio controls. Record planned dimensions, supported options, requested settings where available, and expected constraints in `step-08/design-system.json`. If the user has not stated display size, choose a reasonable assumption and record it. A requested font or pixel size is a design target, not proof that a generative model rendered it exactly.

## Output

- `<run-dir>/step-08/content-asset-inventory.json` with target IDs, exact copy, relationships, asset references and fallback dispositions.
