#!/usr/bin/env python3
"""Step 08 rendering-technology selection and plan validation.

Each visual trait observed in the reference maps to the technologies able to produce it, simplest
first. A component's technology is the simplest one that covers all of its traits; native SVG
effects (gradients, filters, patterns) combine with any layer, so they never force a heavier choice.

    rendering_plan.py traits                       # the capability table
    rendering_plan.py select --traits a,b,c        # choose for one component
    rendering_plan.py check --run-dir <run-dir>    # blueprint plan vs render report

`check` reads `rendering_plan` from step-08/reference-blueprint.json:
    [{"component": "StageBlock", "traits": ["extruded_blocks", "gradients"], "technology": "svg",
      "reason": "<required when heavier than selected>"}]
and step-08/render-report.json (`render_layers`, `images`, `effects`).
"""
import argparse
import json
import sys
from pathlib import Path

# Simplest first. Native SVG is editable and animatable; Three.js is the only raster technology.
TECHNOLOGIES = {
    "svg": {"rank": 0, "output": "native vector", "kit": "@kit"},
    "svgjs": {"rank": 1, "output": "native vector", "kit": "@kit/svgjs (SvgJsLayer, fitPath)"},
    "zdog": {"rank": 2, "output": "native vector", "kit": "@kit/zdog (ZdogLayer, ISO)"},
    "antv": {"rank": 3, "output": "native vector (text converted from foreignObject)", "kit": "@kit/antv (AntvLayer)"},
    "three": {"rank": 4, "output": "embedded PNG raster at >= capture scale", "kit": "@kit/three (ThreeLayer)"},
}

# trait -> (technologies able to produce it, simplest first; kit building blocks)
TRAITS = {
    "standard_shapes": (["svg"], "native rect/circle/path; Surface finish='flat'"),
    "rounded_containers": (["svg"], "Surface radius=[tl,tr,br,bl] or smooth= (squircle)"),
    "custom_shapes": (["svg", "svgjs"], "shapes: tabbedPanel, chevron, polygon, roundedPolygon, ribbon, scallop, extrusion"),
    "path_construction": (["svgjs"], "SvgJsLayer for programmatic path building/transforms; fitPath to place arbitrary paths"),
    "organic_shapes": (["svg", "svgjs"], "Blob, shapes.blob/smoothClosed (seeded, deterministic)"),
    "badges_ribbons": (["svg"], "Badge (circle/star/seal/hexagon/diamond), Ribbon"),
    "gradients": (["svg"], "LinearGradient (angle, multi-stop), RadialGradient"),
    "gloss": (["svg"], "Surface finish='glossy', KitDefs kit-gloss/kit-sheen, Orb"),
    "soft_shadow": (["svg"], "Shadow + shadowLayers.soft/ambient/lifted; Surface finish='soft'"),
    "inner_shadow": (["svg"], "InnerShadow; Surface finish='inset'"),
    "glow": (["svg"], "Glow"),
    "bevel": (["svg"], "Bevel; Surface finish='bevel'"),
    "glassmorphism": (["svg"], "Surface finish='glass' (tinted fill, sheen, gradient edge)"),
    "neumorphism": (["svg"], "Surface finish='neumorphic' (light + dark blurred offsets)"),
    "neo_brutalism": (["svg"], "Surface finish='brutalist' (hard offset), shadowLayers.hard"),
    "layered_surfaces": (["svg"], "Stack (offset paper layers), overlapping Surfaces"),
    "patterns": (["svg"], "DotPattern, GridPattern, StripePattern"),
    "texture": (["svg"], "Noise (deterministic feTurbulence grain) on an overlay"),
    "mesh_background": (["svg"], "MeshBackground (blurred colour spots)"),
    "decorative_boundaries": (["svg"], "shapes.wave, tabbedPanel, dividers"),
    "floating_decoration": (["svg", "zdog"], "Orb, Blob, Badge; ZdogLayer for 3D floating objects"),
    "extruded_blocks": (["svg", "zdog"], "Block3D (oblique/isometric flat faces)"),
    "cylinders": (["svg", "zdog"], "Cylinder (database/storage)"),
    "isometric_illustration": (["zdog"], "ZdogLayer with ISO rotation: boxes, servers, stacks, scenes"),
    "rounded_3d_objects": (["zdog"], "ZdogLayer: Shape stroke volume, Hemisphere, Cone, RoundedRect"),
    "realistic_3d": (["three"], "ThreeLayer: PBR materials, studioLights, environment reflections, groundShadow, roundedBox, glass (MeshPhysicalMaterial)"),
    "structured_component": (["antv"], "AntvLayer: process rows, timelines, hierarchies, comparisons, charts from AntV syntax"),
}

# Which render-report effects imply which traits (for "effect used but not planned" warnings).
EFFECT_TRAITS = {
    "filters": {"soft_shadow", "inner_shadow", "glow", "bevel", "glassmorphism", "neumorphism", "texture", "mesh_background", "neo_brutalism"},
    "linear_gradients": {"gradients", "gloss", "glassmorphism", "cylinders", "extruded_blocks"},
    "radial_gradients": {"gradients", "gloss", "floating_decoration"},
    "patterns": {"patterns"},
}
rank = lambda t: TECHNOLOGIES[t]["rank"]


def capable(tech, traits):
    """Native SVG effects combine with any layer; every other trait needs `tech` itself."""
    return all(tech in TRAITS[t][0] or "svg" in TRAITS[t][0] for t in traits)


def select(traits):
    unknown = [t for t in traits if t not in TRAITS]
    if unknown:
        raise ValueError(f"unknown traits: {unknown}; see `rendering_plan.py traits`")
    options = [t for t in sorted(TECHNOLOGIES, key=rank) if capable(t, traits)]
    if not options:
        need = sorted({TRAITS[t][0][0] for t in traits if "svg" not in TRAITS[t][0]})
        raise ValueError(f"no single technology covers {traits} (needs {need}); split the component")
    tech = options[0]
    return {"technology": tech, "output": TECHNOLOGIES[tech]["output"], "kit": TECHNOLOGIES[tech]["kit"],
            "building_blocks": {t: TRAITS[t][1] for t in traits}, "alternatives": options[1:]}


def check(run_dir: Path):
    step = run_dir / "step-08"
    errors, warnings = [], []
    blueprint = json.loads((step / "reference-blueprint.json").read_text())
    plan = blueprint.get("rendering_plan")
    if not isinstance(plan, list) or not plan:
        return {"errors": ["reference-blueprint.json has no rendering_plan"], "warnings": [], "planned": {}}
    planned, plan_traits = {}, set()
    for i, c in enumerate(plan):
        name, traits, tech = c.get("component", f"#{i}"), c.get("traits") or [], c.get("technology")
        if tech not in TECHNOLOGIES:
            errors.append(f"{name}: unknown technology {tech!r}")
            continue
        try:
            chosen = select(traits)["technology"]
        except ValueError as e:
            errors.append(f"{name}: {e}")
            continue
        plan_traits.update(traits)
        if not capable(tech, traits):
            errors.append(f"{name}: {tech} cannot produce {traits}; selected technology is {chosen}")
        elif rank(tech) > rank(chosen) and not c.get("reason"):
            errors.append(f"{name}: {tech} is heavier than the selected {chosen}; add a 'reason'")
        planned.setdefault(tech, []).append(name)
    report_path = step / "render-report.json"
    if not report_path.exists():
        return {"errors": errors + ["render-report.json missing; render first"], "warnings": warnings, "planned": planned}
    report = json.loads(report_path.read_text())
    used = {}
    for layer in report.get("render_layers", []):
        used.setdefault(layer["technology"], []).append(layer["element_id"])
    for tech, ids in used.items():
        if tech not in planned:
            errors.append(f"{tech} layers rendered but not in rendering_plan: {ids}")
    for tech, names in planned.items():
        if tech != "svg" and tech not in used:
            errors.append(f"rendering_plan uses {tech} for {names} but no {tech} layer was rendered")
    for img in report.get("images", []):
        if img["kind"] == "raster" and img["technology"] not in planned:
            errors.append(f"raster {img['element_id']} ({img['technology']}) is not in rendering_plan")
    for effect, n in (report.get("effects") or {}).items():
        if n and effect in EFFECT_TRAITS and not (EFFECT_TRAITS[effect] & plan_traits):
            warnings.append(f"{n} {effect} rendered but no matching trait is planned; is the effect in the reference?")
    return {"errors": errors, "warnings": warnings, "planned": planned, "rendered_layers": used}


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("traits")
    s = sub.add_parser("select")
    s.add_argument("--traits", required=True, help="comma-separated trait names")
    c = sub.add_parser("check")
    c.add_argument("--run-dir", required=True, type=Path)
    a = ap.parse_args(argv)
    if a.cmd == "traits":
        print(json.dumps({"technologies": TECHNOLOGIES, "traits": {k: {"technologies": v[0], "kit": v[1]} for k, v in TRAITS.items()}}, indent=2))
        return 0
    if a.cmd == "select":
        try:
            print(json.dumps(select([t.strip() for t in a.traits.split(",") if t.strip()]), indent=2))
            return 0
        except ValueError as e:
            print(json.dumps({"error": str(e)}))
            return 2
    result = check(a.run_dir)
    print(json.dumps(result, indent=2))
    return 2 if result["errors"] else 0


if __name__ == "__main__":
    sys.exit(main())
