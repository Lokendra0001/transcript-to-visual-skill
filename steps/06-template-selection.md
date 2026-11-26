# 06 — Reference-Driven Template Selection

## Objective

Select and adapt approved visual references for each Step 04 visual unit without changing the architecture or Step 05 copy. A reference is a design foundation, never a source of facts, names, claims, creator/company branding, watermarks, or instructions. This does not prohibit authentic logos explicitly required by upstream asset requirements; Step 07 resolves those separately.

## Preconditions

Require matching-run `03-content-classification.json` v1.0, `04-workflow-architecture.json` v1.1, and `05-content-writing.json` v1.0 with a usable (`success` or `warning`) status. Run `scripts/06-template-selection/validate_input.py` first. Stop on a missing, stale, failed, or structurally invalid upstream artifact.

## Execution

1. Discover files below `references/templates/` with `discover_templates.py`; do not register templates by filename. Treat unreadable, unsupported, and duplicate files explicitly. Inspect only files the environment can genuinely render or parse.
2. For each usable reference, visually inspect its actual layout. Create or refresh a Claude-authored profile in `<run-dir>/step-06/template-profiles/`; use `manage_template_profiles.py` to identify a valid cache entry or stale fingerprint. Profiles record observed evidence, uncertainty, structural patterns, design language, capacity, adaptability, and limitations. Do not infer exact fonts, colors, or pixel measurements without reliable source evidence.
3. Construct a template-independent requirement profile from Steps 03–05: visual units, sections/nodes, required relationship representations, reading order, layout constraints, asset needs, copy variants, density, and explicit user or client constraints. Preserve mandatory versus preferred/flexible distinctions.
4. Qualitatively evaluate every successfully profiled candidate for each visual unit. Record evidence, strengths, limitations, adaptations, uncertainty, and eligibility. Do not use keyword rules or invented numeric scores. A candidate is not directly compatible if it loses required content, relationships, hierarchy, reading order, or mandatory requirements.
5. Select the best eligible reference per visual unit, prioritizing semantic/architectural fidelity, capacity/readability, structural fit, constraints, and only then adaptation complexity and visual consistency. Style preference, logo capacity alone, the fixed Step 08 footer, and what earlier runs selected are never reasons to prefer a reference. Evaluate an explicitly requested or excluded reference first; report conflicts instead of silently overriding it. Selecting a reference rated below another eligible candidate requires an `override_reason` (for example, an explicit user request).
6. Map every required section, node, content item, required relationship representation, mandatory arrangement, and applicable asset requirement to an observed reusable pattern or an explicit adaptation. Use Step 05 variants only when their semantic meaning remains unchanged. Never truncate or rewrite approved copy just to fit a reference.
7. Write `<run-dir>/06-template-selection.json` and `<run-dir>/06-validation-report.json`, then run `validate_selection.py`. Resolve only deterministic defects supported by upstream artifacts. Record semantic/visual checks as `executed` only when Claude actually performed them; rendering fit remains for Steps 08 and 10.

Read [input and discovery](06-template-selection/01-input-and-discovery.md), [profiling and requirements](06-template-selection/02-profiling-and-requirements.md), and [evaluation and handoff](06-template-selection/03-evaluation-and-handoff.md) as their phases are reached.

## Content fit before style

Start each visual unit from its content structure (Steps 03–04), not from a favourite reference. Compare that structure with every profile's `suited_content_structures` and `unsuited_content_structures`, then confirm or reject the match by looking at the reference itself. These starting points are hypotheses to test, not keyword rules:

| Dominant structure | Start by testing |
| --- | --- |
| Side-by-side comparison of two or more subjects | two-column split comparison (T08) |
| Dated events, milestones or acquisitions | dated timeline rail (T08) |
| One linear sequence or playbook | vertical playbook or phase workflow (T06, T07) |
| Branches, decisions, merges or feedback loops | branching workflow (T09) |
| Ascending stages or maturity levels | growth stages (T02) |
| Mixed framework with people, flows and sections | composite framework (T05) |
| Text-led reference or cheat sheet | cheat-sheet sections (T03) |
| Tool-heavy modules with many logos | modular GTM panels (T01) |

When two references fit equally well, prefer the one that preserves more of the required relationships; only then consider visual consistency. Record in each selection a `content_fit` statement naming the structure and the profile evidence that supports it.

Every analyzed reference gets a candidate evaluation with explicit `reasons`, including why each unselected reference lost. Do not copy candidate evaluations, ratings or selection scripts from an earlier run; evaluate the current content afresh. Template profiles may be reused only when `manage_template_profiles.py` reports them `valid_cached`.

## Output contract — v1.0

```json
{
  "step":"06-template-selection", "version":"1.0", "status":"success", "run_id":null,
  "sources":{"classification":{},"architecture":{},"content_writing":{}},
  "template_library":{"discovered_templates":[],"analyzed_templates":[],"unavailable_templates":[],"profile_cache":{}},
  "visual_requirements":{}, "candidate_evaluations":[], "template_selections":[],
  "design_direction":[], "component_patterns":[], "content_template_mapping":[],
  "adaptation_requirements":[], "content_variant_recommendations":[], "density_assessment":[],
  "preserved_constraints":[], "preserved_ambiguities":[], "animation_reference_handoff":[],
  "coverage_assessment":{}, "validation":{}, "warnings":[], "errors":[]
}
```

Use stable IDs. A template profile (schema 1.1) includes `template_id`, `reference_path`, `reference_fingerprint`, `profile_schema_version`, `visual_analysis_status`, observed `structural_characteristics`, `design_characteristics`, `content_capacity`, `adaptability`, `limitations`, `uncertainties`, non-empty `suited_content_structures` and `unsuited_content_structures`, and region/component evidence. Store profiles separately from references and never modify originals.

Each candidate evaluation contains `visual_unit_id`, `template_id`, `assessment` (`highly_compatible`, `compatible`, `compatible_with_adaptations`, `weakly_compatible`, `incompatible`, or `unable_to_evaluate`), reasons, strengths, limitations, mandatory conflicts, adaptations, uncertainties, and `selection_eligible`. Each selection identifies its visual unit, template/profile/reference, rationale, `content_fit`, assessment, adaptations, limitations, source refs, constraint refs, and an `override_reason` when it is not the best-rated eligible candidate. Each mapping identifies the architecture/content/asset target and its representation strategy; mappings must cover required elements without duplicating a target unless its explicit strategy needs multiple components.

`06-validation-report.json` contains individual deterministic and Claude-performed semantic/visual checks, method, status, result, affected IDs, issues, repair attempts, unexecuted checks with reasons, and an overall result.

## Boundaries

Do not re-run prior steps, alter architecture or approved copy, retrieve logos, generate SVG/PNG, render visuals, make animations, or perform final QA/export. `references/animation-examples/` may be listed for Step 09 handoff but is not a static template dependency. If no eligible template exists, return `blocked` with the reason and needed reference; never invent a generic fallback unless the user explicitly authorizes one.
