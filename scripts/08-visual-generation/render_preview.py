#!/usr/bin/env python3
"""Render the generated SVG to PNG preview.

Rendering adapter priority:
  1. cairosvg (Python, cross-platform, best SVG support)
  2. rsvg-convert (Linux/macOS, fast, good SVG support)
  3. sips (macOS built-in, limited SVG support)

Never substitutes a different design for the actual generated SVG.
Reports capability failures accurately without claiming success.
"""

import argparse
import shutil
import subprocess
import sys
from pathlib import Path


def render(svg, png):
    """Render SVG file to PNG.

    Args:
        svg: Path to input SVG file
        png: Path to output PNG file

    Returns:
        (success: bool, message: str)
    """
    svg = Path(svg)
    png = Path(png)

    if not svg.is_file():
        return False, f"SVG file not found: {svg}"

    # Ensure parent directory exists
    png.parent.mkdir(parents=True, exist_ok=True)

    # Try cairosvg first (best cross-platform option)
    try:
        import cairosvg
        cairosvg.svg2png(url=str(svg), write_to=str(png))
        if png.is_file() and png.stat().st_size > 0:
            return True, f"rendered with cairosvg ({png.stat().st_size} bytes)"
        return False, "cairosvg produced empty output"
    except ImportError:
        pass
    except Exception as e:
        return False, f"cairosvg error: {e}"

    # Try rsvg-convert
    if shutil.which("rsvg-convert"):
        try:
            result = subprocess.run(
                ["rsvg-convert", "-o", str(png), str(svg)],
                capture_output=True,
                text=True,
                timeout=30,
            )
            if result.returncode == 0 and png.is_file() and png.stat().st_size > 0:
                return True, f"rendered with rsvg-convert ({png.stat().st_size} bytes)"
            return False, f"rsvg-convert failed: {result.stderr}"
        except subprocess.TimeoutExpired:
            return False, "rsvg-convert timed out"
        except Exception as e:
            return False, f"rsvg-convert error: {e}"

    # Try sips (macOS)
    if shutil.which("sips"):
        try:
            result = subprocess.run(
                ["sips", "-s", "format", "png", str(svg), "--out", str(png)],
                capture_output=True,
                text=True,
                timeout=30,
            )
            if result.returncode == 0 and png.is_file() and png.stat().st_size > 0:
                return True, f"rendered with sips ({png.stat().st_size} bytes)"
            msg = result.stderr.strip() or result.stdout.strip() or "unknown error"
            return False, f"sips failed: {msg}"
        except subprocess.TimeoutExpired:
            return False, "sips timed out"
        except Exception as e:
            return False, f"sips error: {e}"

    return False, (
        "no supported SVG renderer found. "
        "Install one of: pip install cairosvg | "
        "apt-get install librsvg2-bin | "
        "brew install librsvg"
    )


def get_renderer_info():
    """Return information about available renderers.

    Returns dict with renderer name and availability.
    """
    info = {
        "available_renderers": [],
        "preferred": None,
        "limitations": [],
    }

    try:
        import cairosvg
        info["available_renderers"].append("cairosvg")
        if not info["preferred"]:
            info["preferred"] = "cairosvg"
    except ImportError:
        pass

    if shutil.which("rsvg-convert"):
        info["available_renderers"].append("rsvg-convert")
        if not info["preferred"]:
            info["preferred"] = "rsvg-convert"

    if shutil.which("sips"):
        info["available_renderers"].append("sips")
        if not info["preferred"]:
            info["preferred"] = "sips"
        info["limitations"].append(
            "sips has limited SVG support; "
            "complex gradients, filters, and some text features may not render correctly"
        )

    if not info["available_renderers"]:
        info["limitations"].append("no SVG renderer available; PNG preview cannot be generated")

    return info


if __name__ == "__main__":
    p = argparse.ArgumentParser(description="Render SVG to PNG preview")
    p.add_argument("--svg", type=Path, required=True, help="Input SVG file")
    p.add_argument("--png", type=Path, required=True, help="Output PNG file")
    p.add_argument("--info", action="store_true", help="Print renderer info and exit")

    args = p.parse_args()

    if args.info:
        import json
        print(json.dumps(get_renderer_info(), indent=2))
        sys.exit(0)

    ok, msg = render(args.svg, args.png)
    print(msg)
    sys.exit(0 if ok else 2)
