# 03 — Content Classification

## Objective and activation

Activate only after a valid `<run-dir>/02-content-analysis.json` exists. Classify its communication objective, semantic structures, visual representation candidates, scope, and conceptual content groups. Do not re-extract source content, write visual copy, choose templates, create layouts, or generate assets.

## Input validation

1. Read Step 02 unchanged and require `step: "02-content-analysis"`, status `success` or `warning`, a matching `run_id`, valid source references, and no known blocking information loss.
2. Treat Step 02 warnings and ambiguities as classification context. Stop on invalid JSON, failed upstream status, unresolved references, or material unrepresented details.
3. Inspect Step 01 only to resolve a documented classification ambiguity; do not silently reimplement semantic extraction.

## Execute

1. Identify the primary and secondary communication objectives from Step 02 context, topics, activities, relationships, facts, decisions, requirements, and constraints. Never invent an audience.
2. Identify source-supported information structures: sequential, hierarchical, parallel, conditional, comparative, temporal, cyclic, network, quantitative, associative, or independent groups. A discussion order is not automatically logical order.
3. Evaluate only plausible conceptual types: `workflow`, `process_flow`, `playbook`, `framework`, `hierarchy`, `taxonomy`, `comparison`, `decision_tree`, `funnel`, `customer_journey`, `timeline`, `roadmap`, `system_architecture`, `ecosystem_map`, `network_diagram`, `cycle`, `lifecycle`, `matrix`, `checklist`, `concept_map`, `data_visualization`, `informational_infographic`, `composite_infographic`, or `other`.
4. For each candidate, assess objective alignment, supported structures, hierarchy/relationship preservation, alternatives versus sequence, information loss, and limitations. Use qualitative reasoning, not keyword rules or numerical scores.
5. Select primary and secondary classifications, then choose `single_visual`, `composite_visual`, or `multiple_visuals`. Multiple visuals require genuinely independent objectives; a long transcript alone is insufficient.
6. Create semantic content groups with source-backed topic/entity/fact/activity/relationship/decision/requirement IDs. These are not layout sections, nodes, or coordinates.
7. Categorize every relevant Step 02 record as represented content, supporting context, representation constraint, excluded/superseded context, or unresolved ambiguity. If a chosen classification cannot accommodate a material group, revise the classification or scope.
8. Write `<run-dir>/03-content-classification.json`, then run the validator below. On a deterministic error, repair only the classification artifact and revalidate once.

## Output contract — v1.0

```json
{
  "step": "03-content-classification",
  "version": "1.0",
  "status": "success",
  "run_id": "same Step 02 run id",
  "source": {"step": "02-content-analysis", "version": "2.0", "run_id": null},
  "communication_objective": {"primary": null, "secondary": [], "intended_audience": null, "supporting_refs": []},
  "information_structures": [],
  "classification": {"primary_type": null, "secondary_types": [], "reasoning": null, "supporting_refs": []},
  "candidate_evaluations": [],
  "visual_scope": {"type": null, "recommended_visual_count": null, "reasoning": null},
  "visual_units": [], "content_groups": [], "representation_constraints": [],
  "coverage_assessment": {"represented_refs": [], "supporting_context_refs": [], "constraint_refs": [], "excluded_refs": [], "unassigned_relevant_refs": []},
  "ambiguities": [], "validation": {}, "warnings": [], "errors": []
}
```

Each structure has `id`, `type`, `description`, `supporting_refs`; each candidate has `id`, `type`, `assessment`, `limitations`, `supporting_refs`; each group has `id`, `name`, `semantic_purpose`, `structures`, related Step 02 IDs, source IDs, and inclusion rationale. Each visual unit has `id`, objective, primary/secondary types, group IDs, constraint IDs, and reasoning.

`success` means classification is usable with no blocking error; `warning` means usable with disclosed non-blocking uncertainty; `failed` means no reliable classification. Preserve excluded alternatives as constraints, not active content. Confirmed tool inclusion remains distinct from mandatory use.

## Validation and handoff

Run:

```sh
python3 scripts/03-content-classification/validate_classification.py --run-dir <run-dir>
```

The script validates structure and references only. Claude must review semantic suitability, candidate rationale, coverage, hierarchy, alternatives, and scope. On pass, preserve the artifact for Step 04; in standalone operation return it and stop.
