# Transcript to Visual

Modular Claude Skill scaffold for turning Granola transcripts and written requirements into designed workflows and infographics.

- `SKILL.md` orchestrates the sequential workflow.
- `steps/` contains one instruction module per stage. Steps 01–08 are implemented; Steps 09–11 are pending.
- `scripts/` contains deterministic processing and validation helpers. Claude performs semantic extraction, visual analysis, writing, and design selection; scripts do not replace those judgments.
- `references/templates/` contains client-approved visual references. They are inspected as designs and are never modified or used as factual source content.
- `tests/` is reserved for sample transcripts and generated outputs.

## Current workflow status

Step 01 validates and safely normalizes one pasted-text or supported text-file input, preserves its verbatim source, structures segments, and persists JSON for Step 02. Each workflow chooses its own run directory; the artifact is always named `01-input-processing.json`. Runtime artifacts do not belong in `tests/outputs/`.

Run it with:

```sh
python3 scripts/01-input-processing/process_input.py \
  --input-file sample.txt --run-dir runs/2026-11-24-client-call
```

The Step 01 handoff file is `runs/2026-11-24-client-call/01-input-processing.json`. Step 02 writes seven internal phase artifacts under `runs/2026-11-24-client-call/step-02/`, then writes and validates the authoritative `02-content-analysis.json` in the same directory:

```sh
python3 scripts/02-content-analysis/validate_analysis.py \
  --run-dir runs/2026-11-24-client-call
```

It supports UTF-8 (including BOM) and UTF-16 `.txt`, `.md`, and `.markdown` files, has no network or third-party dependency, and does not perform audio transcription. Step 02 semantic reasoning is performed by Claude; the companion script checks only deterministic contract invariants.

Step 06 discovers supported reference files recursively, fingerprints them, detects malformed/duplicate candidates, verifies profile-cache freshness, and validates a Claude-authored selection/mapping artifact. Its templates are reference designs, not preclassified or editable layouts:

```sh
python3 scripts/06-template-selection/discover_templates.py \
  --templates-dir references/templates \
  --output runs/2026-11-24-client-call/step-06/template-discovery.json
python3 scripts/06-template-selection/validate_selection.py \
  --run-dir runs/2026-11-24-client-call \
  --templates-dir references/templates
```

Step 07 validates the Step 02/04/05/06 handoffs, discovers and deduplicates asset requirements, uses bounded public-URL retrieval, rejects unsafe active SVG content, and maps each requirement to a verified asset or authorized fallback. Live network retrieval is only performed during a real authorized run.

The automated tests require only Python 3; run them from the skill directory with:

```sh
python3 -m unittest discover -s tests/01-input-processing && \
python3 -m unittest discover -s tests/02-content-analysis && \
python3 -m unittest discover -s tests/03-content-classification && \
python3 -m unittest discover -s tests/04-workflow-architecture && \
python3 -m unittest discover -s tests/05-content-writing && \
python3 -m unittest discover -s tests/06-template-selection && \
python3 -m unittest discover -s tests/07-logo-retrieval && \
python3 -m unittest discover -s tests/08-visual-generation
```

Step 08 executes reference-driven visual generation: the executing AI model acts directly as the infographic designer, visually inspecting the selected reference image and authoring the editable SVG while Python provides deterministic helper utilities:

| Script | Responsibility |
|--------|---------------|
| `validate_input.py` | Upstream artifact presence and version check |
| `design_system.py` | Design token defaults, font discovery, and palette fallback rules |
| `text_measurement.py` | Character width ratios and text-wrapping estimates for spatial planning |
| `embed_assets.py` | Safe base64 asset embedding (PNG, WebP, JPEG, sanitized SVG) with security validation |
| `render_preview.py` | Multi-renderer SVG→PNG adapter (cairosvg, rsvg-convert, sips) |
| `validate_svg.py` | SVG structural validation (XML well-formedness, no scripts, IDs, dimensions) |
| `validate_geometry.py` | Deterministic bounds and non-negative dimension checks on SVG |
| `validate_coverage.py` | Semantic content coverage validation against upstream contracts directly from SVG |
| `output_contract.py` | Element manifest extraction, animation handoff, and output contract assembly |

Rendering dependencies (at least one required for PNG preview):
- `pip install cairosvg` (recommended, cross-platform)
- `apt-get install librsvg2-bin` / `brew install librsvg` (rsvg-convert)
- `sips` (macOS built-in, limited SVG support)
# transcript-to-visual-skill
