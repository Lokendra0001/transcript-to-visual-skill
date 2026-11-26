# 07 — Logo Retrieval and Asset Preparation

## Objective

Resolve, retrieve, verify, prepare, cache, and map authentic assets required by the approved architecture and Step 06 design direction. Claude resolves identity, provenance suitability, and visual appropriateness; Python performs bounded network/file handling and deterministic checks. Never copy unrelated reference-template branding, fabricate logos, or change prior artifacts.

## Preconditions and flow

Require matching successful/warning Step 02 v2.0, Step 04 v1.1, Step 05 v1.0, and Step 06 v1.0 artifacts. Run `validate_input.py`, then `discover_assets.py` to preserve every upstream asset requirement and deduplicate only by canonical entity identity, asset type, variant, and compatible usage constraints. Resolve product identities separately from parents; do not infer that related products share a logo.

## Source ladder (fixed order)

Every brand goes through the same ladder. The coordinator stops at the first source that passes the checks:

1. **Official domain (Claude).** For each entity, Claude writes the company's official domain into the candidate record (`"domain": "clay.com"`). Use what you already know. Confirm it is the right company (for example the GTM tool, not a namesake), and note product/parent relationships. Search results only help find the domain; they never prove identity.
2. **Hunter Logos:** `https://logos.hunter.io/{domain}`. Free and keyless. It returns PNG/AVIF/WebP rasters; AVIF and WebP are re-encoded losslessly to PNG.
3. **lndev Logos:** `https://logos.lndev.me/logos/{slug}.svg`, trying slugs from the name and the domain stem.
4. **theSVG:** the registry (`https://thesvg.org/api/registry.json`, cached per run in `step-07/thesvg-registry.json`) is matched by website domain first, then by exact name, slug or alias. Files come from jsDelivr, and each icon's licence is recorded.
5. **Logo.dev (paid, last authentic source):** a direct `/v2/brands` domain lookup when the domain is known, and a name search only when it is not. It is contacted only after steps 2–4 have failed, so credits are spent only on brands the free providers lack.
6. **Generated fallback:** when Logo.dev is unconfigured, out of credits, errors, or has no logo, the coordinator generates a labelled, non-official marker from the company name.

**Automatic rejections inside the ladder.** A 200 response is not proof of a logo. The coordinator rejects a source and moves to the next provider when:
- the prepared raster is a social-preview banner (at least 500 px wide with a 1.6–2.1 aspect ratio). Domain-keyed providers return these for sites with no stored mark, and for acquired domains that redirect to the parent's page;
- its bytes match an asset already selected for another entity. An acquired domain (Performable → HubSpot) returns the acquirer's exact file.

**Review-driven rejection.** After visual inspection, if a selected file is wrong, add `"reject_providers": ["hunter"]` (or `lndev`, `thesvg`, `logo_dev`) to that entity's candidate record and re-run. The ladder continues from the next provider. A `url` in a candidate record pins a source ahead of the ladder. Use it only for a user-supplied or user-approved asset, or a reviewed official-site or Wikimedia file for an acquired or retired brand.

Every attempt is recorded per request in `source_attempts` (provider, URL, outcome, HTTP status). 403, 404, rate-limit, network, invalid-file, banner and duplicate outcomes stay distinct.

Generated fallback is enabled by default after the research ladder is exhausted, so a missing external logo cannot block an otherwise valid workflow. Prefer an associated verified parent-brand relationship when the research record establishes one; otherwise produce a neutral editable visual marker. Record each fallback as generated/non-official and retain the exact product label in the surrounding visual. Never imitate a trademark. Use `--no-generated-fallback` only for authentic-asset-only review runs; in that mode unresolved assets may block strict coverage.

Separate research, browser/image-search, HTTP-download, workspace-write, and visual-inspection capabilities. Record only capabilities actually available. Candidate records include identity evidence, source category/URLs, format/dimensions/transparency, quality assessment, usage information, retrieval/verification status, visual-inspection status, selection status, and rejection reason. A selected asset requires actual visual inspection before complete visual verification is reported. Product-specific assets require product-specific evidence; do not substitute a parent mark unless that use is established. Favicon use is a late fallback. Generic conceptual icons must come from an approved/licensed icon source and may never be represented by an unrelated brand.

Prepare each logo or icon with a genuinely transparent outer background for placement over the infographic. Prefer an authentic transparent official SVG or raster. Inspect actual alpha/transparent regions rather than trusting an extension or a white preview; an alpha channel alone is not proof that the outside background is transparent. Preserve legitimate white details, integral colored logo shapes and official surrounding shapes; never erase brand artwork or recolor a mark to manufacture transparency. If a safe, accurate transparent version cannot be obtained or prepared, keep the original intact, record the issue and authorized fallback, and mark the asset unverified/incomplete rather than asserting transparency or fabricating an altered logo. Record source and prepared fingerprints and visual inspection evidence for each occurrence mapping. An explicit user-approved exception must be documented.

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

Use `execute_step07.py --run-dir <run-dir> --candidates <candidate-records.json>` once Claude has resolved the domains. A candidate record looks like this:

```json
{"entity_id": "ent-tool-clay", "name": "Clay", "domain": "clay.com", "reject_providers": [], "fallback": {"parent_entity_id": null}}
```

`domain` is required for Hunter and strongly recommended for the other providers. `name` defaults to the canonical entity name. The coordinator checkpoints discovery, research records, every source attempt, selected assets and occurrence mappings. On a re-run it first retries the source a previous run selected, unless that provider is now rejected. It does not perform semantic research or claim visual inspection. Visual inspection and contact-sheet approval are explicit completion gates before final Step 07 success.

## Logo.dev configuration

Configure `LOGO_DEV_SECRET_KEY` once in the execution environment (see `.env.example`); never place it in artifacts. Without a key, the ladder goes straight from theSVG to the generated fallback. The adapter uses Logo.dev API v2 and downloads the API-provided file. CDN display URLs (publishable key) must not be fetched by script or copied into a self-hosted cache. Asset availability produces a warning for review rather than blocking downstream work; only `--no-generated-fallback` restores authentic-only blocking behavior.
