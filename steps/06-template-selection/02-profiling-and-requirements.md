# Profiling and requirement construction

For every readable candidate, inspect the visual itself. Profile layout/reading direction; sequence, hierarchy, branching, grouping, containment, comparison, timeline, feedback, and component arrangements; then observed background, color treatment, type hierarchy, cards, borders, shadows, spacing, icons/logos, connectors, numbering, and decoration. Record visible-region evidence and uncertainty. Keep source content isolated from the profile.

Assess observed capacity and adaptable versus fixed characteristics. Capacity is qualitative and not a hard limit. Store a profile in the run's `step-06/template-profiles/` directory. `manage_template_profiles.py` may reuse only a profile whose path, fingerprint, schema version, and successful visual-analysis status still match; otherwise regenerate it through visual inspection.

Build the visual requirement profile from Step 03 classifications, Step 04 units/sections/nodes/connections/layout/asset requirements, and Step 05 items/variants/density. Preserve relationship representation modes, mandatory reading order and arrangements, canonical names, optionality, ambiguity, and explicit constraints. Do not simplify the source to match a template.
