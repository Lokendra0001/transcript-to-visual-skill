# Input validation and discovery

Validate the three upstream artifacts before reading any design reference. Require their expected step/version, a shared run ID, usable status, and no blocking error. Use `validate_input.py` for deterministic checks.

Run `discover_templates.py --templates-dir references/templates --output <run-dir>/step-06/template-discovery.json`. It recursively discovers supported reference formats, calculates a content fingerprint, and reports unsupported, unreadable, malformed, and byte-duplicate files. Its output is an inventory—not a visual profile. Do not call a file analyzed until it has actually been visually inspected.

Optional user constraints (selected references, canvas dimensions, orientation, brand rules, animation preference) must be recorded with their source and mandatory/preferred status. Missing guidelines are a disclosed absence, not permission to invent them.
