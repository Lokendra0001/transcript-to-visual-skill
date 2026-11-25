#!/usr/bin/env python3
"""Deterministic geometry and layout bounds validation.

Validates either:
  1. An SVG file directly (parsing bounds, coordinates, viewBox)
  2. A layout plan / component bounds dict if provided

Checks:
  - Canvas width and height are positive
  - Elements and coordinates stay within canvas dimensions
  - No negative positions or dimensions on primary elements
  - Path coordinate sanity checks
"""

import re
import xml.etree.ElementTree as ET
from pathlib import Path


def validate_svg_geometry(svg_path):
    """Validate geometry directly from an SVG file.

    Returns list of error strings. Empty list means valid geometry.
    """
    svg_path = Path(svg_path)
    if not svg_path.is_file():
        return [f"SVG file not found: {svg_path}"]

    try:
        tree = ET.parse(str(svg_path))
        root = tree.getroot()
    except Exception as e:
        return [f"XML parse error in SVG: {e}"]

    # Parse dimensions
    w_str = root.attrib.get("width", "0")
    h_str = root.attrib.get("height", "0")
    viewbox = root.attrib.get("viewBox", "")

    try:
        w = float(re.sub(r"[^\d.]", "", w_str))
        h = float(re.sub(r"[^\d.]", "", h_str))
    except ValueError:
        w, h = 0, 0

    if (w <= 0 or h <= 0) and viewbox:
        vb_parts = viewbox.strip().split()
        if len(vb_parts) == 4:
            try:
                w = float(vb_parts[2])
                h = float(vb_parts[3])
            except ValueError:
                pass

    if w <= 0 or h <= 0:
        return [f"canvas has invalid dimensions: width={w_str}, height={h_str}, viewBox={viewbox}"]

    errors = []

    # Inspect visible rect, circle, image, text elements
    for elem in root.iter():
        tag = elem.tag.split("}")[-1]
        eid = elem.attrib.get("id", f"<{tag}>")

        if tag in ("rect", "image"):
            try:
                x = float(elem.attrib.get("x", 0))
                y = float(elem.attrib.get("y", 0))
                ew = float(elem.attrib.get("width", 0))
                eh = float(elem.attrib.get("height", 0))

                if ew < 0 or eh < 0:
                    errors.append(f"negative dimensions on {eid}: {ew}x{eh}")
                if x < 0 or y < 0:
                    errors.append(f"negative position on {eid}: ({x}, {y})")
                if x + ew > w + 10:  # allow 10px subpixel margin
                    errors.append(f"element {eid} exceeds canvas width: {x + ew} > {w}")
                if y + eh > h + 10:
                    errors.append(f"element {eid} exceeds canvas height: {y + eh} > {h}")
            except (ValueError, TypeError):
                pass

        elif tag == "circle":
            try:
                cx = float(elem.attrib.get("cx", 0))
                cy = float(elem.attrib.get("cy", 0))
                r = float(elem.attrib.get("r", 0))
                if r < 0:
                    errors.append(f"negative radius on {eid}: {r}")
                if cx - r < -10 or cy - r < -10 or cx + r > w + 10 or cy + r > h + 10:
                    errors.append(f"circle {eid} outside canvas bounds")
            except (ValueError, TypeError):
                pass

        elif tag == "path":
            d = elem.attrib.get("d", "")
            if d:
                # Basic check for wildly out-of-bound coords
                coords = re.findall(r"[-+]?\d*\.?\d+", d)
                try:
                    nums = [float(c) for c in coords]
                    margin = max(w, h) * 0.25
                    for i, num in enumerate(nums):
                        if i % 2 == 0 and (num < -margin or num > w + margin):
                            errors.append(f"path {eid} x-coord wildly out of bounds: {num}")
                            break
                        elif i % 2 == 1 and (num < -margin or num > h + margin):
                            errors.append(f"path {eid} y-coord wildly out of bounds: {num}")
                            break
                except (ValueError, TypeError):
                    pass

    return errors


def validate(plan_or_svg):
    """Validate geometry from either a plan dict or an SVG path.

    Maintains backward compatibility with tests expecting a plan dict.
    """
    if isinstance(plan_or_svg, (str, Path)):
        return validate_svg_geometry(plan_or_svg)

    if not isinstance(plan_or_svg, dict):
        return ["invalid geometry input"]

    # Plan dict validation
    canvas = plan_or_svg.get("canvas", {})
    w = canvas.get("width", 0)
    h = canvas.get("height", 0)
    errors = []

    if w <= 0 or h <= 0:
        errors.append("canvas has non-positive dimensions")
        return errors

    for comp in plan_or_svg.get("components", []):
        cid = comp.get("id", "unknown")
        cx = comp.get("x", 0)
        cy = comp.get("y", 0)
        cw = comp.get("width", 0)
        ch = comp.get("height", 0)

        if cw <= 0 or ch <= 0:
            errors.append(f"non-positive dimensions: {cid} ({cw}x{ch})")
        if cx < 0 or cy < 0:
            errors.append(f"negative position: {cid} ({cx},{cy})")
        if cx + cw > w:
            errors.append(f"exceeds canvas width: {cid} (x={cx} + w={cw} = {cx + cw} > {w})")
        if cy + ch > h:
            errors.append(f"exceeds canvas height: {cid} (y={cy} + h={ch} = {cy + ch} > {h})")

    return errors


def validate_plan_completeness(plan):
    """Check structural completeness of plan or element manifest."""
    errors = []
    if "canvas" not in plan:
        errors.append("missing canvas definition")

    components = plan.get("components", [])
    if not components and "element_manifest" not in plan:
        errors.append("no components in layout plan")

    seen = set()
    for comp in components:
        cid = comp.get("id")
        if not cid:
            errors.append("component missing 'id'")
        elif cid in seen:
            errors.append(f"duplicate element ID: {cid}")
        seen.add(cid)

    return errors
