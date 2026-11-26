---
name: transcript-to-visual
description: Convert Granola call transcripts and written requirements into professionally designed workflows and infographics using approved resources. Use when creating or planning a transcript-driven visual deliverable.
---

# Transcript to Visual

The visual style comes from the reference template that Step 06 selects for the content's structure, not from a fixed house style. Whatever the reference, aim for strong hierarchy, crisp forms, intentional contrast and restrained graphic accents. Favor visual communication and recognizable authentic logos with small readable labels, while retaining essential meaning. Follow any explicit user direction for a particular output.

For every workflow input, choose a unique caller-controlled run directory. Step 07 records asset retrieval outcomes and fallbacks; review their authorization and warnings before publishing. Step 08 builds the visual as code: a React + SVG composition that reproduces the selected reference template's design system with the approved architecture, copy and verified logos, rendered locally by `scripts/08-visual-generation/renderer/` (headless Chrome) into an editable SVG and PNG. Premium surfaces, depth and 3D come from a reference-driven, code-only kit (native SVG first; SVG.js, Zdog, Three.js or AntV only where a reference trait requires them), with an optional GSAP motion layer whose final frame must equal the static master. No AI image generation is used. Continue only when each artifact meets its completion criteria. In standalone operation, stop after Step 08. Steps 09–11 remain implementation pending.

1. [Input processing](steps/01-input-processing.md)
2. [Content analysis](steps/02-content-analysis.md)
3. [Content classification](steps/03-content-classification.md)
4. [Workflow architecture](steps/04-workflow-architecture.md)
5. [Content writing](steps/05-content-writing.md)
6. [Template selection](steps/06-template-selection.md)
7. [Logo retrieval](steps/07-logo-retrieval.md)
8. [Visual generation](steps/08-visual-generation.md)
9. [Animation](steps/09-animation.md)
10. [Quality assurance](steps/10-quality-assurance.md)
11. [Final export](steps/11-final-export.md)

