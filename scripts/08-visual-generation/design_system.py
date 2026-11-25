#!/usr/bin/env python3
"""Build a dynamic design system from Claude-authored design decisions.

The execution agent (Claude) inspects the selected reference image and authors
a design-system.json that captures observed hierarchy, palette, type scale,
spacing, borders, shadows, connector treatment, and logo treatment.

This module provides:
  - Schema validation of a Claude-authored design system.
  - Sensible defaults for any missing properties.
  - Font availability discovery.
  - Text-measurement helpers (approximation when no renderer is available).

It does NOT perform visual analysis of reference images — that is a semantic
task performed by the execution agent.
"""

import json
import os
import shutil
import subprocess
from pathlib import Path

# ---------------------------------------------------------------------------
# Default design tokens — used when the execution agent omits a property
# ---------------------------------------------------------------------------

DEFAULT_PALETTE = {
    "background": "#ffffff",
    "surface": "#f5f7fa",
    "primary": "#2563eb",
    "primary_light": "#dbeafe",
    "secondary": "#64748b",
    "accent": "#f59e0b",
    "text_primary": "#1e293b",
    "text_secondary": "#64748b",
    "text_on_primary": "#ffffff",
    "border": "#e2e8f0",
    "connector": "#94a3b8",
    "success": "#22c55e",
    "warning": "#f59e0b",
    "error": "#ef4444",
}

DEFAULT_TYPE_SCALE = {
    "title": {"size": 32, "weight": "bold", "line_height": 1.2},
    "subtitle": {"size": 20, "weight": "600", "line_height": 1.3},
    "heading": {"size": 16, "weight": "600", "line_height": 1.4},
    "body": {"size": 14, "weight": "normal", "line_height": 1.5},
    "caption": {"size": 12, "weight": "normal", "line_height": 1.4},
    "label": {"size": 11, "weight": "500", "line_height": 1.3},
}

DEFAULT_SPACING = {
    "xs": 4,
    "sm": 8,
    "md": 16,
    "lg": 24,
    "xl": 32,
    "xxl": 48,
    "section_gap": 24,
    "card_padding": 16,
    "group_padding": 20,
}

DEFAULT_BORDERS = {
    "radius_sm": 4,
    "radius_md": 8,
    "radius_lg": 16,
    "radius_xl": 24,
    "width": 1,
    "color": "#e2e8f0",
}

DEFAULT_SHADOWS = {
    "card": "0 1px 3px rgba(0,0,0,0.1)",
    "elevated": "0 4px 6px rgba(0,0,0,0.1)",
    "none": "none",
}

DEFAULT_CONNECTOR_STYLE = {
    "stroke_width": 2,
    "color": "#94a3b8",
    "arrow_size": 8,
    "dash_pattern": None,
    "style": "straight",  # straight | curved | orthogonal
}

DEFAULT_LOGO_TREATMENT = {
    "max_width": 48,
    "max_height": 48,
    "padding": 4,
    "border_radius": 8,
    "background": "#ffffff",
    "fallback_style": "rounded_label",  # rounded_label | circle_initial | plain_text
}


# ---------------------------------------------------------------------------
# Font discovery
# ---------------------------------------------------------------------------

# Portable font stacks ordered by preference
FONT_STACKS = {
    "sans": ["Inter", "Helvetica Neue", "Helvetica", "Arial", "sans-serif"],
    "mono": ["JetBrains Mono", "SF Mono", "Menlo", "Consolas", "monospace"],
    "serif": ["Georgia", "Times New Roman", "serif"],
}


def discover_fonts():
    """Return dict mapping stack names to the best available font family string.

    Uses fc-list when available, otherwise falls back to safe cross-platform
    defaults.  Never fails — always returns at least generic family names.
    """
    available = set()
    if shutil.which("fc-list"):
        try:
            result = subprocess.run(
                ["fc-list", "--format", "%{family}\n"],
                capture_output=True,
                text=True,
                timeout=5,
            )
            for line in result.stdout.splitlines():
                for name in line.split(","):
                    available.add(name.strip())
        except Exception:
            pass

    resolved = {}
    for stack_name, candidates in FONT_STACKS.items():
        chosen = candidates[-1]  # generic fallback
        for font in candidates:
            if font in available or font.lower() in {"sans-serif", "monospace", "serif"}:
                chosen = font
                break
        resolved[stack_name] = chosen

    return {
        "resolved_fonts": resolved,
        "discovery_method": "fc-list" if available else "generic-fallback",
        "available_count": len(available),
    }


# ---------------------------------------------------------------------------
# Text measurement (approximation)
# ---------------------------------------------------------------------------

# Average character width ratios relative to font size for common faces
_CHAR_WIDTH_RATIOS = {
    "sans": 0.52,
    "mono": 0.60,
    "serif": 0.50,
}


def measure_text(text, font_size, font_stack="sans", max_width=None):
    """Approximate text metrics.

    Returns dict with estimated width, height, and wrapped lines if max_width
    is given.  This is a deterministic approximation; actual rendering may
    differ by ±15%.
    """
    ratio = _CHAR_WIDTH_RATIOS.get(font_stack, 0.52)
    char_width = font_size * ratio
    line_height = font_size * 1.5

    if max_width is None:
        width = len(text) * char_width
        return {
            "width": width,
            "height": line_height,
            "lines": [text],
            "line_count": 1,
        }

    # Word-wrap
    words = text.split()
    lines = []
    current_line = ""
    for word in words:
        test = f"{current_line} {word}".strip() if current_line else word
        if len(test) * char_width <= max_width:
            current_line = test
        else:
            if current_line:
                lines.append(current_line)
            # Handle single words wider than max_width
            if len(word) * char_width > max_width:
                lines.append(word)
                current_line = ""
            else:
                current_line = word
    if current_line:
        lines.append(current_line)

    if not lines:
        lines = [""]

    return {
        "width": min(max(len(l) * char_width for l in lines), max_width),
        "height": len(lines) * line_height,
        "lines": lines,
        "line_count": len(lines),
    }


# ---------------------------------------------------------------------------
# Design system validation and defaults
# ---------------------------------------------------------------------------

REQUIRED_SECTIONS = [
    "palette",
    "type_scale",
    "spacing",
    "borders",
    "connector_style",
    "logo_treatment",
]


def validate_design_system(ds):
    """Validate a Claude-authored design system dict.

    Returns (errors: list[str], warnings: list[str]).
    """
    errors = []
    warnings = []

    if not isinstance(ds, dict):
        return ["design system must be a JSON object"], []

    for section in REQUIRED_SECTIONS:
        if section not in ds:
            warnings.append(f"missing section '{section}'; defaults will be used")

    palette = ds.get("palette", {})
    if isinstance(palette, dict):
        for key in ["background", "primary", "text_primary"]:
            if key not in palette:
                warnings.append(f"palette missing '{key}'; default will be used")

    type_scale = ds.get("type_scale", {})
    if isinstance(type_scale, dict):
        for role in ["title", "heading", "body"]:
            if role not in type_scale:
                warnings.append(f"type_scale missing '{role}'; default will be used")

    return errors, warnings


def apply_defaults(ds):
    """Return a complete design system with defaults applied for missing values."""
    result = dict(ds) if isinstance(ds, dict) else {}

    defaults = {
        "palette": DEFAULT_PALETTE,
        "type_scale": DEFAULT_TYPE_SCALE,
        "spacing": DEFAULT_SPACING,
        "borders": DEFAULT_BORDERS,
        "shadows": DEFAULT_SHADOWS,
        "connector_style": DEFAULT_CONNECTOR_STYLE,
        "logo_treatment": DEFAULT_LOGO_TREATMENT,
    }

    for section, default_val in defaults.items():
        if section not in result:
            result[section] = dict(default_val)
        elif isinstance(result[section], dict) and isinstance(default_val, dict):
            merged = dict(default_val)
            merged.update(result[section])
            result[section] = merged

    # Attach font discovery
    if "fonts" not in result:
        result["fonts"] = discover_fonts()

    return result
