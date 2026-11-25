# 05 — Content Writing

## Objective

Turn valid Step 04 content requirements into concise, professional, source-faithful visual copy without changing architecture, relationships, targets, constraints, or scope. Claude performs writing and semantic review; scripts validate deterministic invariants only.

## Execute

Read `<run-dir>/04-workflow-architecture.json`, and consult Step 02/03 only for factual verification. Require matching run IDs, Step 04 v1.1 success/warning status, valid targets, and no blocking error. Process each requirement-target combination: required requirements receive usable copy; omitted optional requirements receive a reason.

Preserve canonical entity names, decisions, exclusions, numbers, information-flow meaning, and tool optionality. Do not make tools interchangeable or mandatory without source support. Preferred text is the default; compact/expanded variants are allowed only when meaning is unchanged. Do not research brands, select templates, create assets, or alter architecture.

## Output contract — v1.0

Write `<run-dir>/05-content-writing.json`:

```json
{"step":"05-content-writing","version":"1.0","status":"success","run_id":null,"sources":{"architecture":{"step":"04-workflow-architecture","version":"1.1","run_id":null}},"writing_strategy":{},"visual_units":[],"content_items":[],"terminology_registry":[],"relationship_communication":[],"omitted_optional_content":[],"preserved_constraints":[],"preserved_ambiguities":[],"content_density":[],"coverage_assessment":{},"validation":{},"warnings":[],"errors":[]}
```

Each item includes `id`, `content_requirement_id`, `target_scope`, `target_refs`, `content_type`, `required`, `priority`, `preferred_text`, optional `variants`, `source_refs`, `constraint_refs`, `status`, and actual `length_metrics` (`words`, `characters`). Status is `generated`, `omitted_optional`, or `blocked`. Content requirements must have valid visual-unit, section, node, connection, or global targets.

## Validation and handoff

Run `python3 scripts/05-content-writing/validate_content.py --run-dir <run-dir>`. Repair structural failures from existing architecture evidence only. Record only semantic checks actually performed. On pass, hand the artifact to Step 06; do not select a template.
