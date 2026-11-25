#!/usr/bin/env python3
"""Text measurement utilities for AI visual spatial budgeting.

Assists the AI visual designer in calculating character metrics, estimated
text widths, and wrapping line counts so cards and panels are appropriately sized.
"""

_CHAR_WIDTH_RATIOS = {
    "sans": 0.52,
    "mono": 0.60,
    "serif": 0.50,
}


def measure_text(text, font_size, font_stack="sans", max_width=None):
    """Approximate text metrics.

    Returns dict with estimated width, height, lines, and line_count.
    """
    ratio = _CHAR_WIDTH_RATIOS.get(font_stack, 0.52)
    char_width = font_size * ratio
    line_height = font_size * 1.4

    if not text:
        return {
            "width": 0,
            "height": line_height,
            "lines": [""],
            "line_count": 1,
        }

    if max_width is None:
        width = len(text) * char_width
        return {
            "width": width,
            "height": line_height,
            "lines": [text],
            "line_count": 1,
        }

    words = str(text).split()
    lines = []
    current_line = ""
    for word in words:
        test = f"{current_line} {word}".strip() if current_line else word
        if len(test) * char_width <= max_width:
            current_line = test
        else:
            if current_line:
                lines.append(current_line)
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
