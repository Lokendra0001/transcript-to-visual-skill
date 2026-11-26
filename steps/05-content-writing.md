# 05 — Content Writing

## Objective

Turn valid Step 04 content requirements into concise, professional, source-faithful visual copy without changing architecture, relationships, targets, constraints, or scope. Claude performs writing and semantic review; scripts validate deterministic invariants only.

## Execute

Read `<run-dir>/04-workflow-architecture.json`, and consult Step 02/03 only for factual verification. Require matching run IDs, Step 04 v1.1 success/warning status, valid targets, and no blocking error. Process each requirement-target combination: required requirements receive usable canonical copy and a representation plan; omitted optional requirements receive a reason.

Preserve canonical entity names, decisions, exclusions, numbers, information-flow meaning, and tool optionality. Do not make tools interchangeable or mandatory without source support. Preferred text is the canonical fallback; compact/expanded variants and visual representation are allowed only when meaning is unchanged. Do not research brands, select templates, create assets, or alter architecture.

## Output contract — v1.0

Write `<run-dir>/05-content-writing.json`:

```json
{"step":"05-content-writing","version":"1.0","status":"success","run_id":null,"sources":{"architecture":{"step":"04-workflow-architecture","version":"1.1","run_id":null}},"writing_strategy":{},"visual_units":[],"content_items":[],"terminology_registry":[],"relationship_communication":[],"omitted_optional_content":[],"preserved_constraints":[],"preserved_ambiguities":[],"content_density":[],"coverage_assessment":{},"validation":{},"warnings":[],"errors":[]}
```

Each item includes `id`, `content_requirement_id`, `target_scope`, `target_refs`, `content_type`, `required`, `priority`, `preferred_text`, optional `variants`, `source_refs`, `constraint_refs`, `status`, and actual `length_metrics` (`words`, `characters`). Status is `generated`, `omitted_optional`, or `blocked`. Content requirements must have valid visual-unit, section, node, connection, or global targets.

## Validation and handoff

Run `python3 scripts/05-content-writing/validate_content.py --run-dir <run-dir>`. Repair structural failures from existing architecture evidence only. Record only semantic checks actually performed. On pass, hand the artifact to Step 06; do not select a template.

## Visual-first semantic preparation

Preserve 100% of intended meaning with the minimum necessary written information. For each requirement and target distinguish essential visible text, a concise label, verified logo, recognizable icon, directional relationship, meaningful group, or genuinely supporting context. Exact numbers, conditions, decisions, distinct names, exclusions and other material qualifiers remain visible whenever a visual alone would be ambiguous. Keep names for unfamiliar or unreadable marks; preserve tool optionality. Avoid repeated explanations, headings, counts, labels and internal process terms when the meaning is unmistakable without them. Do not apply fixed word limits. A proposed representation is not evidence of successful rendering.

Retain `preferred_text` and its metrics as canonical source/fallback for compatibility; it is not automatically a command to display that exact copy. Add optional `representation` on each item: `type` is `text`, `concise_label`, `logo`, `icon`, `relationship`, `group`, or `context_only`; `meaning` and `reason` explain the source-faithful meaning and choice; `visible_text` is the approved wording if text is needed; `asset_refs` or `relationship_refs` identify mapped resources where applicable. `context_only` is allowed only for nonrequired supporting information; required meaning must remain visibly represented. Require a nonempty approved `visible_text` for text/concise_label, asset refs for logo/icon, and relationship refs for relationship/group. Where needed a visual representation may also carry `visible_text` to preserve ambiguity-sensitive qualifiers. A visual-only choice must be unambiguous to its audience; otherwise retain the necessary label. If absent, legacy items retain their prior text behavior. Validate structure, but semantic correctness still requires independent review.

