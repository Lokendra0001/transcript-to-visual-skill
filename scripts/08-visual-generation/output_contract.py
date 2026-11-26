#!/usr/bin/env python3
"""Assemble the Step 08 output contract, element manifest, and validation report.

Creates:
  - 08-visual-generation.json: the output contract for Step 09 Animation
  - 08-validation-report.json: deterministic verification summary
"""

import json
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path


def extract_manifest_from_svg(svg_path):
    """Extract an element manifest with animation roles directly from an SVG file."""
    svg_path = Path(svg_path)
    if not svg_path.is_file():
        return []

    manifest = []
    try:
        tree = ET.parse(str(svg_path))
        root = tree.getroot()
        for elem in root.iter():
            eid = elem.attrib.get("id")
            if not eid or eid.startswith("arrow-") or eid.startswith("filter-") or eid.endswith("-shadow"):
                continue

            tag = elem.tag.split("}")[-1]
            role = _infer_role(eid, tag, elem)
            animatable = role in {"connector", "flow_indicator", "stage_highlight", "outcome"}

            manifest.append({
                "id": eid,
                "tag": tag,
                "role": role,
                "semantic": eid,
                "animatable": animatable,
            })
    except Exception:
        pass

    return manifest


def _infer_role(eid, tag, elem):
    """Infer semantic animation role from element ID and tag."""
    eid_lower = eid.lower()
    if "conn" in eid_lower or "arrow" in eid_lower or tag == "path":
        return "connector"
    if "closed-won" in eid_lower or "terminal" in eid_lower or "outcome" in eid_lower:
        return "outcome"
    if "step" in eid_lower and ("header" in eid_lower or "badge" in eid_lower):
        return "stage_highlight"
    if "tool" in eid_lower or "logo" in eid_lower:
        return "tool_tile"
    if "title" in eid_lower:
        return "title"
    if "note" in eid_lower:
        return "note"
    if "sig" in eid_lower or "chip" in eid_lower:
        return "chip"
    if "lane" in eid_lower or "panel" in eid_lower:
        return "panel"
    if "card" in eid_lower:
        return "card"
    return "element"


def build_animation_handoff(element_manifest):
    """Build animation handoff metadata for Step 09."""
    animatable = []
    stationary = []

    for elem in element_manifest:
        entry = {
            "id": elem.get("id", ""),
            "role": elem.get("role", ""),
            "semantic": elem.get("semantic", ""),
        }
        if elem.get("animatable", False):
            animatable.append(entry)
        else:
            stationary.append(entry)

    return {
        "version": "1.0",
        "animatable_elements": animatable,
        "stationary_elements": stationary,
        "total_elements": len(element_manifest),
        "animation_eligible_count": len(animatable),
        "notes": [
            "Element IDs are stable across re-renders with the same input.",
            "Connectors support stroke-dashoffset animation.",
            "Text, logos, and informational cards remain stationary by default.",
        ],
    }


def build_output_contract(
    run_id,
    sources,
    design_system_summary,
    element_manifest,
    asset_usage,
    coverage_assessment,
    animation_handoff,
    validation,
    warnings=None,
    errors=None,
    layout_plan_summary=None,
    component_registry=None,
):
    """Build the Step 08 output contract dict conforming to downstream requirements."""
    overall = validation.get("overall", {}) if isinstance(validation, dict) else {}
    explicit_valid = validation.get("valid") if isinstance(validation, dict) else None
    visual = validation.get("visual_review", {}) if isinstance(validation, dict) else {}
    validated = (overall.get("valid") is True or explicit_valid is True) and visual.get("status") == "approved"
    contract = {
        "step": "08-visual-generation",
        "version": "1.0",
        "status": "error" if errors else ("incomplete" if not validated else ("warning" if warnings else "success")),
        "run_id": run_id,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "sources": sources,
        "design_system": design_system_summary,
        "element_manifest": element_manifest,
        "asset_usage": asset_usage,
        "coverage_assessment": coverage_assessment,
        "animation_handoff": animation_handoff,
        "validation": validation,
        "warnings": warnings or [],
        "errors": errors or [],
    }
    if layout_plan_summary:
        contract["layout_plan"] = layout_plan_summary
    if component_registry is not None:
        contract["component_registry"] = component_registry
    return contract


def build_validation_report(
    geometry_errors,
    svg_errors,
    coverage_result,
    render_result=None,
    plan_completeness_errors=None,
):
    """Build the separate validation report."""
    all_errors = []
    all_warnings = []

    all_errors.extend(geometry_errors or [])
    all_errors.extend(svg_errors or [])
    if plan_completeness_errors:
        all_errors.extend(plan_completeness_errors)
    all_errors.extend(coverage_result.get("errors", []))

    if coverage_result.get("missing"):
        all_warnings.append(
            f"{len(coverage_result['missing'])} content IDs not represented in visual"
        )
    if coverage_result.get("missing_copy"):
        all_warnings.append(
            f"{len(coverage_result['missing_copy'])} copy texts not found in visual"
        )

    render_status = "not_attempted"
    if render_result is not None:
        render_ok, render_msg = render_result
        render_status = "success" if render_ok else f"failed: {render_msg}"

    return {
        "step": "08-visual-generation",
        "validation_version": "1.0",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "geometry": {
            "valid": len(geometry_errors or []) == 0,
            "errors": geometry_errors or [],
        },
        "svg_structure": {
            "valid": len(svg_errors or []) == 0,
            "errors": svg_errors or [],
        },
        "content_coverage": {
            "coverage_ratio": coverage_result.get("coverage_ratio", 0),
            "total_required": coverage_result.get("total_required", 0),
            "total_covered": coverage_result.get("total_covered", 0),
            "missing": coverage_result.get("missing", []),
            "missing_copy": coverage_result.get("missing_copy", []),
        },
        "rendering": {
            "status": render_status,
        },
        "visual_review": {
            "status": "pending",
            "note": "Visual inspection must be performed and recorded against the actual output.",
        },
        "overall": {
            "valid": False,
            "errors": all_errors,
            "warnings": all_warnings,
        },
    }
