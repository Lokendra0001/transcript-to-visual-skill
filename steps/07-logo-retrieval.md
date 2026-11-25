# 07 — Logo Retrieval and Asset Preparation

## Objective

Resolve, retrieve, verify, prepare, cache, and map authentic assets required by the approved architecture and Step 06 design direction. Claude resolves identity, provenance suitability, and visual appropriateness; Python performs bounded network/file handling and deterministic checks. Never copy unrelated reference-template branding, fabricate logos, or change prior artifacts.

## Preconditions and flow

Require matching successful/warning Step 02 v2.0, Step 04 v1.1, Step 05 v1.0, and Step 06 v1.0 artifacts. Run `validate_input.py`, then `discover_assets.py` to preserve every upstream asset requirement and deduplicate only by canonical entity identity, asset type, variant, and compatible usage constraints. Resolve product identities separately from parents; do not infer that related products share a logo.

For every unresolved brand or product identity, Claude must conduct bounded research and keep candidate records; search results only discover sources, never prove identity. Prefer, in order: authorized user assets, verified cache, official brand/press/media resources, official product sites/docs/repositories, trusted logo repositories, permitted external logo services, verified high-quality favicons, then an authorized fallback. Generate contextual queries from the entity/product identity and ambiguity; after a repository failure, research genuinely independent sources—not only alternate CDNs or delivery endpoints of that repository. Record 403, 404, rate-limit, and network failures distinctly. Stop only after a candidate satisfies identity, authority, quality, security, usage, and presentation requirements, or the configured research budget ends.

Generated fallback is enabled by default after the research ladder is exhausted, so a missing external logo cannot block an otherwise valid workflow. Prefer an associated verified parent-brand relationship when the research record establishes one; otherwise produce a neutral editable visual marker. Record each fallback as generated/non-official and retain the exact product label in the surrounding visual. Never imitate a trademark. Use `--no-generated-fallback` only for authentic-asset-only review runs; in that mode unresolved assets may block strict coverage.

Separate research, browser/image-search, HTTP-download, workspace-write, and visual-inspection capabilities. Record only capabilities actually available. Candidate records include identity evidence, source category/URLs, format/dimensions/transparency, quality assessment, usage information, retrieval/verification status, visual-inspection status, selection status, and rejection reason. A selected asset requires actual visual inspection before complete visual verification is reported. Product-specific assets require product-specific evidence; do not substitute a parent mark unless that use is established. Favicon use is a late fallback. Generic conceptual icons must come from an approved/licensed icon source and may never be represented by an unrelated brand.

Use `retrieve_assets.py` only for public HTTP(S) URLs. It blocks localhost/private destinations, bounds redirects/size/time, writes atomically, and does not execute downloads. Use `verify_assets.py` to check file signatures, paths, dimensions/viewBox, fingerprints, and XML-aware SVG safety; derive SVG aspect ratio from a valid viewBox when dimensions are absent. Standard namespaces, internal fragments, gradients, masks, and definitions are allowed; scripts, event handlers, external resources/CSS, foreign objects, and unsafe declarations are rejected. Suitable raster assets remain eligible when they meet the actual presentation need; SVG preference is not a raster rejection rule. Preserve original color/proportions and assess monochrome repository icons against Step 06 presentation requirements. Cache keys include entity, type, variant, usage constraints, and presentation compatibility.

Write `<run-dir>/07-logo-retrieval.json`, `<run-dir>/07-validation-report.json`, intermediate records beneath `<run-dir>/step-07/`, and prepared files under `<run-dir>/assets/{originals,logos,icons}/`. Paths are portable and relative to the run directory. Run `validate_asset_retrieval.py` before handoff.

## Output contract — v1.0

```json
{"step":"07-logo-retrieval","version":"1.0","status":"success","run_id":null,"sources":{},"network_capabilities":{},"retrieval_strategy":{},"asset_requirements":[],"entity_resolutions":[],"unique_asset_requests":[],"retrieval_attempts":[],"assets":[],"asset_mappings":[],"fallback_assets":[],"unavailable_assets":[],"cache_summary":{},"preserved_constraints":[],"preserved_ambiguities":[],"coverage_assessment":{},"validation":{},"warnings":[],"errors":[]}
```

Each mapping retains `asset_requirement_id`, entity/target references, approved display name, presentation requirements, required status, selected asset (if any), fallback, and resolution status. Each asset records its identity/variant, original/prepared relative paths, format/MIME/size/dimensions/aspect/transparency when known, fingerprint, provenance URLs/category, retrieval time, verification evidence/status, usage information, normalization, and cache status. Unknown fields remain unknown.

## Boundaries

Do not create final layouts, coordinates, SVG/PNG/GIF outputs, animation, or final QA. Generic conceptual icons are permitted only when required and must not imply unrelated brand affiliation. Record semantic/visual checks honestly; a successful download alone never verifies identity or license.

## Execution coordinator

Use `execute_step07.py --run-dir <run-dir> --candidates <candidate-records.json>` after Claude has completed research. Candidate records contain the resolved entity ID, public asset URL, source category, identity evidence, and intended variant. The coordinator checkpoints discovery, research records, download attempts, selected assets, and occurrence mappings; it may resume by supplying only unresolved candidates. It does not perform semantic research or claim visual inspection. Visual inspection and contact-sheet approval are explicit completion gates before final Step 07 success.

## Logo.dev primary provider

Configure `LOGO_DEV_SECRET_KEY` once in the execution environment (see `.env.example`); never place it in artifacts. The server-side adapter uses Logo.dev API v2 for search and brand resolution, then the coordinator downloads API-provided files for runtime-local preparation. For AI-assisted resolution, Logo.dev MCP can be connected with OAuth instead. CDN display URLs use a publishable key and must not be copied into a self-hosted asset cache. Logo.dev failures automatically require the documented official/repository/favicon sequence, followed by a recorded generated fallback. Asset availability therefore produces a warning for review rather than blocking downstream work; only `--no-generated-fallback` restores authentic-only blocking behavior.
