# 04 — Workflow Architecture

## Objective

Transform valid Step 02 analysis and Step 03 classification into a complete, template-independent structural blueprint. Despite its name, this supports all Step 03 classifications—not only workflows. Determine logical units, sections, nodes, relationships, hierarchy, reading order, density, constraints, and traceability; do not determine pixels, style, templates, copy, assets, or rendered output.

## Preconditions

Read `<run-dir>/02-content-analysis.json` and `<run-dir>/03-content-classification.json`. Require matching run IDs, eligible statuses, valid Step 03 references into Step 02, supported visual scope, and no blocking upstream information loss. Stop on invalid or incomplete upstream data; do not silently repair semantic extraction.

## Execute

1. Select architecture strategies from actual Step 03 classifications, structures, groups, scope, constraints, and density: linear/branched sequence, parallel lanes, hierarchy, taxonomy, hub-and-spoke, network, layers, comparison, matrix, timeline, cycle, modular sections, or composite. Record why.
2. Create one architecture per Step 03 visual unit. Preserve scope unless a documented structural conflict makes it impossible.
3. Convert content groups into meaningful sections only. Establish parent-child containment separately from process relationships. Every non-root section has one valid parent; containment has no cycles.
4. Create nodes only for meaningful visual elements. A source entity can have multiple contextual visual instances. Keep optional tools, alternatives, and supporting associations distinct from process stages.
5. Create connections only for source-supported sequence, dependency, data/information flow, condition, feedback, association, alternative, comparison, or membership. Record `relationship_type`, `representation_mode`, and `visual_representation_required` separately. Important information flow can require visual communication while leaving its presentation flexible (connector, convergence, grouping, or annotation); it is not automatically an execution dependency. Use `explicit_connector`, `ordering`, `grouping`, `containment`, `supporting_association`, or `flexible` representation modes; avoid connector clutter.
6. Define reading order, priority (`primary`, `secondary`, `supporting`, `contextual`), qualitative density, conceptual arrangement requirements, content slots for Step 05, and potential asset requirements for Step 07. Every content requirement has an explicit target scope (`visual_unit`, `section`, `node`, `connection`, or `global`), target ID when scoped, `required`, priority, semantic purpose, source references, and optional advisory `max_words_hint`. Do not make meaningful semantic content optional merely for density. Do not write final copy or retrieve assets.
7. Map every required Step 03/02 record and association to a section, node, connection, grouping, constraint, context, or excluded disposition. Record unresolved ambiguity without inventing a relationship.

## Output contract — v1.1

Write `<run-dir>/04-workflow-architecture.json`:

```json
{
  "step":"04-workflow-architecture", "version":"1.1", "status":"success", "run_id":null,
  "sources":{"content_analysis":{"step":"02-content-analysis","version":null,"run_id":null},"content_classification":{"step":"03-content-classification","version":null,"run_id":null}},
  "architecture_strategy":{"primary_pattern":null,"secondary_patterns":[],"reasoning":null,"supporting_refs":[]},
  "visual_units":[],"sections":[],"nodes":[],"connections":[],"reading_order":[],"layout_requirements":[],"content_requirements":[],"asset_requirements":[],"density_assessment":[],"representation_constraints":[],"ambiguities":[],
  "coverage_assessment":{"record_mappings":[],"association_mappings":[],"unrepresented_required_refs":[],"unrepresented_required_associations":[]},"validation":{},"warnings":[],"errors":[]
}
```

Sections include `id`, `visual_unit_id`, `parent_section_id`, role, semantic label/purpose, group and upstream refs, child IDs, node IDs, pattern, ordering, priority, constraints, and source IDs. Nodes include `id`, unit/section ownership, semantic type, working label, source refs, priority/order, content and asset requirement IDs. Connections include typed endpoints, `relationship_type`, direction, upstream refs, `representation_mode`, and `visual_representation_required`. Content requirements include `target_scope`, `target_id`, `required`, `priority`, semantic purpose, source refs, and optional `max_words_hint`. Layout requirements state whether a conceptual arrangement is `mandatory`, `recommended`, or `flexible`; never encode template-specific styling. Use explicit namespaces where references could collide.

## Validation and handoff

Run `python3 scripts/04-workflow-architecture/validate_architecture.py --run-dir <run-dir>`. Its report contains individual deterministic checks with method, status, result, affected references, and failure detail. Claude separately records which semantic checks it actually reviewed; do not mark unexecuted semantic checks as passed. After a pass, preserve the architecture for Step 05 and stop in standalone execution.
