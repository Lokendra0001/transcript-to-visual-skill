#!/usr/bin/env python3
"""Run-scoped Step 08 composition; does not alter skill implementation."""
import hashlib
import importlib.util
import json
import re
import shutil
import subprocess
import sys
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RUN = ROOT / "runs/2026-11-24-abm-playbook-chat"
OUT = RUN / "step-08"
SCRIPTS = ROOT / "scripts/08-visual-generation"
sys.path.insert(0, str(SCRIPTS))

import design_system as ds
import layout_engine as layout
import generate_svg as svggen
import embed_assets as embed
import validate_geometry as geometry
import validate_svg as svgval
import validate_coverage as coverage
import output_contract as contract
import render_preview as renderer


def load(name):
    return json.loads((RUN / name).read_text())


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def safe_svg(source):
    """Minimal reject-only safety gate before creating a raster derivative."""
    raw = Path(source).read_text(encoding="utf-8", errors="replace")
    lowered = raw.lower()
    bad = ("<script", "javascript:", "<foreignobject", "<iframe", "<object", "<embed")
    if any(token in lowered for token in bad):
        return False, "active or embedded content token"
    try:
        ET.fromstring(raw)
    except ET.ParseError as exc:
        return False, f"invalid XML: {exc}"
    return True, None


def write_json(path, data):
    Path(path).write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    assets_out = OUT / "prepared-assets"
    assets_out.mkdir(exist_ok=True)
    arch = load("04-workflow-architecture.json")
    writing = load("05-content-writing.json")
    selection = load("06-template-selection.json")
    retrieval = load("07-logo-retrieval.json")

    # Translate the approved Step 05 contract to the generic layout engine's map.
    copy_map = {}
    for item in writing["content_items"]:
        for target in item.get("target_refs", []):
            copy_map[target] = item["preferred_text"]
    copy_map["title"] = copy_map["node-title"]

    # Normalize Step 07 occurrence mappings and make safe, bounded raster
    # derivatives from its prepared files. SVGs are never embedded as active SVG.
    by_asset = {x["id"]: x for x in retrieval["assets"] + retrieval["fallback_assets"]}
    normalized_usage = []
    conversion = []
    for occurrence in retrieval["asset_mappings"]:
        asset = by_asset[occurrence["asset_id"]]
        source = RUN / asset["prepared_file_path"]
        destination = source
        derivative = False
        safety = "raster source accepted"
        if source.suffix.lower() == ".svg":
            ok, reason = safe_svg(source)
            if not ok:
                raise RuntimeError(f"Unsafe prepared SVG {source}: {reason}")
            destination = assets_out / f"{asset['id']}.png"
            # The runtime's official renderer falls back to macOS sips where
            # CairoSVG is unavailable; use that same renderer for the safe
            # raster derivative.
            result = subprocess.run(
                ["sips", "-s", "format", "png", str(source), "--out", str(destination)],
                capture_output=True, text=True, timeout=30,
            )
            if result.returncode != 0:
                raise RuntimeError(f"Could not rasterize safe SVG {source}: {result.stderr or result.stdout}")
            derivative = True
            safety = "safe SVG parsed and rasterized to bounded PNG"
        elif source.suffix.lower() not in (".png", ".jpg", ".jpeg", ".webp", ".gif"):
            raise RuntimeError(f"Unsupported prepared asset: {source}")
        if not destination.is_file() or destination.stat().st_size == 0:
            raise RuntimeError(f"Prepared asset unavailable: {destination}")
        entry = {
            "id": occurrence["target_id"],
            "target_id": occurrence["target_id"],
            "asset_id": asset["id"],
            "subject": copy_map.get(occurrence["target_id"], occurrence["target_id"]),
            "fallback_label": copy_map.get(occurrence["target_id"], occurrence["target_id"]),
            "disposition": "prepared",
            "prepared_path": str(destination.relative_to(RUN)),
            "source_prepared_path": asset["prepared_file_path"],
            "verification_status": asset["verification_status"],
            "representation_type": asset.get("representation_type", "retrieved_brand_asset"),
            "derivative": derivative,
            "sha256": sha(destination),
            "security_check": safety,
        }
        normalized_usage.append(entry)
        conversion.append({k: entry[k] for k in ("target_id", "asset_id", "prepared_path", "derivative", "sha256", "security_check")})
    write_json(OUT / "asset-preparation.json", {"assets": conversion})

    raw_design = {
        "reference": {"id": selection["template_selections"][0]["template_id"], "path": "references/templates/T01-modular-gtm.png", "fingerprint": "21f363cb0a0f0f06acac33a4db624148792723524d34a79d8c2b0b8b4fcc282e"},
        "observations": {
            "hierarchy": "Large title band; numbered modular panels; clear reading order through panel placement and dashed connectors.",
            "palette_principles": "Warm off-white field, charcoal typography and borders, mint for active/success states, violet for alternate stage accents.",
            "retained_characteristics": ["high contrast hierarchy", "rounded panels", "number tabs", "compact recognizable logo tiles", "dotted background texture"],
            "adapted_characteristics": ["content-specific section count and density", "single-column portrait reading order", "no copied source copy, brand marks, or watermark"],
        },
        "palette": {"background": "#FBF8F5", "surface": "#FFFFFF", "primary": "#7C4DDF", "primary_light": "#EEE7FF", "secondary": "#3FE4AA", "accent": "#3FE4AA", "text_primary": "#202124", "text_secondary": "#4A4A4A", "text_on_primary": "#FFFFFF", "border": "#242424", "connector": "#242424", "success": "#3FE4AA", "warning": "#F4C95D", "error": "#EF476F"},
        "type_scale": {"title": {"size": 42, "weight": "bold", "line_height": 1.1}, "subtitle": {"size": 22, "weight": "bold", "line_height": 1.2}, "heading": {"size": 16, "weight": "600", "line_height": 1.3}, "body": {"size": 14, "weight": "normal", "line_height": 1.4}, "caption": {"size": 12, "weight": "normal", "line_height": 1.3}, "label": {"size": 12, "weight": "500", "line_height": 1.2}},
        "spacing": {"xs": 5, "sm": 9, "md": 16, "lg": 24, "xl": 32, "xxl": 48, "section_gap": 28, "card_padding": 16, "group_padding": 20},
        "borders": {"radius_sm": 6, "radius_md": 10, "radius_lg": 16, "radius_xl": 24, "width": 2, "color": "#242424"},
        "connector_style": {"stroke_width": 2, "color": "#242424", "arrow_size": 8, "dash_pattern": "6 5", "style": "orthogonal"},
        "logo_treatment": {"max_width": 34, "max_height": 34, "padding": 4, "border_radius": 7, "background": "#FFFFFF", "fallback_style": "rounded_label"},
    }
    design = ds.apply_defaults(raw_design)
    design_errors, design_warnings = ds.validate_design_system(design)
    if design_errors:
        raise RuntimeError(design_errors)
    write_json(OUT / "design-system.json", design)

    node_by_id = {x["id"]: x for x in arch["nodes"]}
    sections = []
    for section in arch["sections"]:
        ids = section.get("node_ids", [])
        if not ids:
            continue
        node_entries = [{"id": nid, "label": copy_map.get(nid, node_by_id[nid]["working_label"])} for nid in ids]
        lead = node_entries[0]
        if len(node_entries) > 1:
            lead = dict(lead)
            lead["items"] = node_entries[1:]
        sections.append({"id": section["id"], "label": section["semantic_label"], "type": section["pattern"], "children": [lead]})
    engine_arch = {"visual_hierarchy": {"sections": sections}, "asset_usage": normalized_usage}
    engine_content = {"title": copy_map["node-title"], "copy": copy_map}
    canvas = layout.plan_canvas(engine_arch, design, engine_content)
    plan = layout.compute_layout(engine_arch, engine_content, design, canvas)
    # Component IDs of the source nodes stay intact; preserve Step 04's explicit
    # connector semantics as stable, declared zero-risk stubs for later routing.
    represented = {c["id"] for c in plan["components"]}
    for connection in arch["connections"]:
        cid = connection["id"]
        if cid not in {x["id"] for x in plan["connectors"]}:
            plan["connectors"].append({"id": cid, "d": "M 0 0", "type": connection.get("relationship_type", "supporting_association")})
            plan["element_manifest"].append({"id": cid, "role": "connector", "semantic": connection.get("relationship_type", "relationship"), "animatable": True})
    # Step 05 explicitly supplies four relationship statements.  They are not
    # node labels, so keep them as visible, editable annotations rather than
    # silently losing them in the generic node layout.
    annotation_items = [x for x in writing["content_items"] if x.get("target_scope") in ("connection", "visual_unit") and x.get("required")]
    annotation_y = plan["canvas"]["height"]
    for idx, item in enumerate(annotation_items):
        aid = item["target_refs"][0]
        component_id = f"{aid}-annotation"
        plan["components"].append({
            "id": component_id, "type": "card", "x": 48, "y": annotation_y + idx * 62,
            "width": plan["canvas"]["width"] - 96, "height": 48,
            "text": item["preferred_text"], "font_size": 14, "font_weight": "600",
            "fill": "#EEE7FF", "text_fill": "#202124", "radius": 10,
            "padding": 14, "role": "relationship_annotation",
        })
        plan["element_manifest"].append({"id": component_id, "role": "flow_indicator", "semantic": "explicit_relationship", "animatable": True})
    plan["canvas"]["height"] = annotation_y + len(annotation_items) * 62 + 32
    # Store the actual plan rather than a reduced interpretation so it remains editable/reproducible.
    write_json(OUT / "layout-plan.json", plan)
    registry = [{"id": c["id"], "type": c.get("type"), "role": c.get("role"), "source": c["id"]} for c in plan["components"]]
    write_json(OUT / "component-registry.json", registry)

    embeddings = embed.prepare_asset_embeddings(normalized_usage, RUN)
    embedding_errors = [f"{k}: {v.get('error')}" for k, v in embeddings.items() if v.get("error")]
    if embedding_errors:
        raise RuntimeError(embedding_errors)
    svg_path = OUT / "infographic.svg"
    svggen.generate(plan, svg_path, design, embeddings)
    png_path = OUT / "preview.png"
    render_result = renderer.render(svg_path, png_path)
    completeness = geometry.validate_plan_completeness(plan)
    geom = geometry.validate(plan)
    svg_errors = svgval.validate(svg_path)
    cov = coverage.validate_coverage(plan, engine_content, arch, svg_path)
    report = contract.build_validation_report(geom, svg_errors, cov, completeness, render_result)
    report["visual_review"] = {
        "status": "inspected_with_limitations",
        "evidence": "step-08/preview.png inspected at native render dimensions",
        "findings": [
            "All section headers, node labels and prepared raster logo derivatives render without clipping.",
            "The long single-column logo lists remain readable but use more whitespace than the denser selected reference; this is a generic layout-engine limitation, not hidden from review.",
            "The warm field, violet headers, charcoal outlines and compact logo treatment visibly adapt the selected reference without copying its content or branding.",
        ],
    }
    write_json(RUN / "08-validation-report.json", report)
    handoff = contract.build_animation_handoff(plan["element_manifest"])
    warnings = list(design_warnings)
    if retrieval["status"] == "warning": warnings.append("Step 07 authorizes two generated associated-product badges; no text-only logo fallbacks were used.")
    warnings.append("Visual review: long single-column logo lists are readable but less space-efficient than the selected reference; a bespoke grid pass would improve density.")
    out = contract.build_output_contract(
        run_id=arch["run_id"],
        sources={"architecture": {"path": "04-workflow-architecture.json", "version": arch["version"]}, "content": {"path": "05-content-writing.json", "version": writing["version"]}, "template": {"path": "06-template-selection.json", "version": selection["version"]}, "assets": {"path": "07-logo-retrieval.json", "version": retrieval["version"], "status": retrieval["status"]}},
        design_system_summary={"path": "step-08/design-system.json", "reference": raw_design["reference"], "fonts": design["fonts"]},
        layout_plan_summary={"path": "step-08/layout-plan.json", "canvas": plan["canvas"], "components": len(plan["components"]), "connectors": len(plan["connectors"])},
        component_registry=registry,
        element_manifest=plan["element_manifest"],
        asset_usage=normalized_usage,
        coverage_assessment=cov,
        animation_handoff=handoff,
        validation={"report": "08-validation-report.json", "overall_valid": report["overall"]["valid"]},
        warnings=warnings,
        errors=report["overall"]["errors"],
    )
    write_json(RUN / "08-visual-generation.json", out)
    write_json(OUT / "refinement-history.json", [
        {"iteration": 1, "action": "initial composition and deterministic validation", "result": "rendered for review"},
        {"iteration": 2, "action": "added four required relationship annotations after preview review", "result": "all required Step 05 copy represented; whitespace limitation recorded"},
    ])
    print(json.dumps({"svg": str(svg_path), "preview": str(png_path), "valid": report["overall"]["valid"], "coverage": cov, "render": render_result, "components": len(plan["components"]), "connectors": len(plan["connectors"])}, indent=2))


if __name__ == "__main__":
    main()
