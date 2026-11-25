#!/usr/bin/env python3
"""Semantic content and relationship coverage validation.

Checks that 100% of required nodes, sections, and approved copy from
Step 04 and Step 05 are present in the generated SVG.
"""

import json
import xml.etree.ElementTree as ET
from pathlib import Path


def validate_coverage(plan_or_svg, content, architecture, svg_path=None):
    """Check content coverage between upstream data and the visual artifact.

    Accepts plan_or_svg as either an SVG path or a plan dict, with optional svg_path.
    """
    actual_svg = None
    if svg_path and Path(svg_path).is_file():
        actual_svg = Path(svg_path)
    elif isinstance(plan_or_svg, (str, Path)) and Path(plan_or_svg).is_file():
        actual_svg = Path(plan_or_svg)

    errors = []
    covered = []
    missing = []

    # 1. Collect all required node IDs from architecture
    required_ids = set()
    for node in architecture.get("nodes", []):
        if isinstance(node, dict) and node.get("id"):
            required_ids.add(node["id"])

    # Also collect from visual_hierarchy if present
    if "visual_hierarchy" in architecture:
        _collect_hierarchy_ids(architecture["visual_hierarchy"], required_ids)

    # 2. Extract present IDs and text content
    present_ids = set()
    svg_text_content = set()

    # From SVG
    if actual_svg and actual_svg.is_file():
        try:
            tree = ET.parse(str(actual_svg))
            root = tree.getroot()
            for elem in root.iter():
                eid = elem.attrib.get("id")
                if eid:
                    present_ids.add(eid)
                txt = (elem.text or "").strip()
                if txt:
                    svg_text_content.add(txt)
                tail = (elem.tail or "").strip()
                if tail:
                    svg_text_content.add(tail)
        except Exception as e:
            errors.append(f"SVG parsing failed in coverage check: {e}")

    # From plan dict if passed
    if isinstance(plan_or_svg, dict):
        for c in plan_or_svg.get("components", []):
            if c.get("id"):
                present_ids.add(c["id"])
            if c.get("text"):
                svg_text_content.add(str(c["text"]).strip())
        for conn in plan_or_svg.get("connectors", []):
            if conn.get("id"):
                present_ids.add(conn["id"])
        for manifest_item in plan_or_svg.get("element_manifest", []):
            if manifest_item.get("id"):
                present_ids.add(manifest_item["id"])

    # 3. Check node ID coverage
    for rid in required_ids:
        # Match exact ID or compound prefix (e.g., node-step-1-header)
        if rid in present_ids or any(pid.startswith(rid) for pid in present_ids):
            covered.append(rid)
        else:
            missing.append(rid)

    # 4. Check copy items presence
    missing_copy = []
    copy_items = _extract_required_copy(content)
    full_svg_text = " ".join(svg_text_content).lower()

    for copy_id, copy_text in copy_items:
        if not copy_text:
            continue
        ct_clean = copy_text.strip().lower()
        # Direct match or multi-word substring match
        if ct_clean not in full_svg_text:
            # Check individual keywords for wrapped tspans
            words = [w for w in ct_clean.split() if len(w) > 3]
            if words and not any(w in full_svg_text for w in words):
                missing_copy.append({"id": copy_id, "text": copy_text})

    total = len(required_ids)
    ratio = len(covered) / total if total > 0 else 1.0

    return {
        "covered": covered,
        "missing": missing,
        "missing_copy": missing_copy,
        "coverage_ratio": round(ratio, 3),
        "total_required": total,
        "total_covered": len(covered),
        "errors": errors,
    }


def _collect_hierarchy_ids(hierarchy, id_set):
    """Recursively collect IDs from visual hierarchy."""
    if isinstance(hierarchy, dict):
        for k in ("sections", "nodes", "children"):
            if k in hierarchy:
                _collect_hierarchy_ids(hierarchy[k], id_set)
    elif isinstance(hierarchy, list):
        for item in hierarchy:
            if isinstance(item, dict):
                if item.get("id"):
                    id_set.add(item["id"])
                _collect_hierarchy_ids(item, id_set)


def _extract_required_copy(content):
    """Extract required copy from content_items or copy map."""
    items = []
    if not isinstance(content, dict):
        return items

    if "content_items" in content:
        for ci in content["content_items"]:
            if isinstance(ci, dict) and ci.get("required", True):
                txt = ci.get("preferred_text")
                if txt:
                    items.append((ci.get("id", "item"), txt))

    if "title" in content and content["title"]:
        items.append(("title", content["title"]))

    copy_data = content.get("copy", {})
    if isinstance(copy_data, dict):
        for k, v in copy_data.items():
            if isinstance(v, str):
                items.append((k, v))
            elif isinstance(v, dict) and "text" in v:
                items.append((k, v["text"]))

    return items
