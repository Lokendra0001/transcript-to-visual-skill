# Profiling and requirement construction

For every readable candidate, inspect the visual itself. Profile layout/reading direction; sequence, hierarchy, branching, grouping, containment, comparison, timeline, feedback, and component arrangements; then observed background, color treatment, type hierarchy, cards, borders, shadows, spacing, icons/logos, connectors, numbering, and decoration. Record visible-region evidence and uncertainty. Keep source content isolated from the profile.

Assess observed capacity and adaptable versus fixed characteristics. Capacity is qualitative and not a hard limit. Store a profile in the run's `step-06/template-profiles/` directory. `manage_template_profiles.py` may reuse only a profile whose path, fingerprint, schema version, and successful visual-analysis status still match; otherwise regenerate it through visual inspection.

Build the visual requirement profile from Step 03 classifications, Step 04 units/sections/nodes/connections/layout/asset requirements, and Step 05 items/variants/density. Preserve relationship representation modes, mandatory reading order and arrangements, canonical names, optionality, ambiguity, and explicit constraints. Do not simplify the source to match a template.

Additionally observe text density, visual-to-text balance, component variety, whitespace and logo integration, with visible evidence. Treat the Step 05 representation plan and canonical fallback as distinct; neither a visual-only plan nor a reference style proves semantic clarity.

Separate observed structural, stylistic and component-level guidance. Note palette distribution, background texture and any localized halftone, type hierarchy, border/corner treatment, connector geometry, logo and label alignment, decorative placement and whitespace. Cite observed regions; do not infer exact specifications from appearance or import the reference's branding.

Record which content structures the reference suits and which it does not, as observed from its layout, in `suited_content_structures` and `unsuited_content_structures` (for example: "two-subject comparison", "dated milestones", "branching decisions", "dense logo grids", "long prose"). Describe capacity in concrete terms (rows, modules, logo slots, text length) rather than one line. A profile without these is incomplete and must be redone.
