#!/usr/bin/env python3
"""Safe embedding of verified raster and vector assets into SVG as base64 data URIs.

Security rules:
  - Only embeds files from the run's assets directory.
  - Supports PNG, JPEG, WebP, GIF, and clean SVG assets.
  - Rejects paths that traverse outside the allowed directory.
  - Validates file headers/magic bytes before embedding.
  - Size-limits individual assets (max 2 MB).
  - Sanitizes SVG assets (rejects scripts, external entities, and event handlers).
"""

import base64
import mimetypes
import os
import re
from pathlib import Path

MAX_ASSET_SIZE = 2 * 1024 * 1024

ALLOWED_MIMES = {
    "image/png",
    "image/jpeg",
    "image/webp",
    "image/gif",
    "image/svg+xml",
}

MAGIC_BYTES = {
    b"\x89PNG": "image/png",
    b"\xff\xd8\xff": "image/jpeg",
    b"RIFF": "image/webp",
    b"GIF8": "image/gif",
    b"<svg": "image/svg+xml",
    b"<?xm": "image/svg+xml",
}


def validate_asset_path(asset_path, allowed_root):
    """Validate that asset_path is safe and within allowed_root.

    Returns (is_valid: bool, error: str|None, resolved_path: Path|None).
    """
    try:
        resolved = Path(asset_path).resolve()
        root = Path(allowed_root).resolve()
    except (ValueError, OSError) as e:
        return False, f"invalid path: {e}", None

    # Path traversal check
    try:
        resolved.relative_to(root)
    except ValueError:
        return False, f"path escapes allowed root: {resolved}", None

    if not resolved.is_file():
        return False, f"file not found: {resolved}", None

    # Size check
    size = resolved.stat().st_size
    if size > MAX_ASSET_SIZE:
        return False, f"file too large: {size} bytes (max {MAX_ASSET_SIZE})", None

    # Extension / MIME check
    mime, _ = mimetypes.guess_type(str(resolved))
    if mime not in ALLOWED_MIMES and resolved.suffix.lower() not in {".png", ".jpg", ".jpeg", ".webp", ".gif", ".svg"}:
        return False, f"unsupported format: {mime}", None

    return True, None, resolved


def detect_mime(file_path):
    """Detect MIME type from file magic bytes or extension."""
    try:
        with open(file_path, "rb") as f:
            header = f.read(64)
    except (IOError, OSError):
        return None

    # Check magic bytes
    for magic, mime in MAGIC_BYTES.items():
        if header.startswith(magic):
            if magic == b"RIFF" and header[8:12] != b"WEBP":
                continue
            return mime

    # SVG text search in initial chunk
    try:
        header_text = header.decode("utf-8", errors="ignore").lower()
        if "<svg" in header_text or "xmlns=\"http://www.w3.org/2000/svg\"" in header_text:
            return "image/svg+xml"
    except Exception:
        pass

    mime, _ = mimetypes.guess_type(str(file_path))
    return mime if mime in ALLOWED_MIMES else None


def sanitize_svg_content(data_bytes):
    """Ensure SVG contains no executable scripts or dangerous attributes."""
    try:
        text = data_bytes.decode("utf-8", errors="ignore")
    except Exception:
        return False, "cannot decode SVG as UTF-8"

    # Reject <script> tags
    if re.search(r"<\s*script", text, re.IGNORECASE):
        return False, "script element detected in SVG asset"

    # Reject onload, onclick etc.
    if re.search(r"on[a-z]+\s*=", text, re.IGNORECASE):
        return False, "inline event handler detected in SVG asset"

    # Reject DOCTYPE / entity expansions (XXE prevention)
    if "<!DOCTYPE" in text or "<!ENTITY" in text:
        return False, "DOCTYPE/ENTITY declaration detected in SVG asset"

    return True, None


def embed_asset(asset_path, allowed_root):
    """Embed an asset file as a base64 data URI.

    Returns dict with data_uri, mime, size, path, or error.
    """
    valid, error, resolved = validate_asset_path(asset_path, allowed_root)
    if not valid:
        return {"data_uri": None, "error": error}

    mime = detect_mime(resolved)
    if not mime:
        return {"data_uri": None, "error": f"cannot determine MIME type for {resolved}"}

    try:
        data = resolved.read_bytes()
    except (IOError, OSError) as e:
        return {"data_uri": None, "error": f"read error: {e}"}

    if mime == "image/svg+xml":
        is_safe, sec_err = sanitize_svg_content(data)
        if not is_safe:
            return {"data_uri": None, "error": f"security rejection: {sec_err}"}

    b64 = base64.b64encode(data).decode("ascii")
    return {
        "data_uri": f"data:{mime};base64,{b64}",
        "mime": mime,
        "size": len(data),
        "path": str(resolved),
    }


def prepare_asset_embeddings(asset_mappings, run_dir):
    """Prepare all asset embeddings for a run from Step 07 asset mappings.

    Returns dict mapping target_id / asset_id to embedding data.
    """
    allowed_root = Path(run_dir).resolve()
    results = {}

    for mapping in asset_mappings:
        if not isinstance(mapping, dict):
            continue

        target_id = mapping.get("target_id") or mapping.get("id", "")
        status = mapping.get("resolution_status") or mapping.get("disposition", "")
        fallback_label = mapping.get("approved_display_name") or mapping.get("fallback_label", mapping.get("subject", ""))

        if status not in ("resolved_with_asset", "retrieved", "cached", "user_supplied", "prepared"):
            results[target_id] = {
                "data_uri": None,
                "status": status,
                "fallback_label": fallback_label,
            }
            continue

        path = mapping.get("prepared_path") or mapping.get("path", "")
        if not path:
            results[target_id] = {
                "data_uri": None,
                "error": "no path specified",
                "fallback_label": fallback_label,
            }
            continue

        full_path = Path(path)
        if not full_path.is_absolute():
            full_path = allowed_root / path

        result = embed_asset(full_path, allowed_root)
        result["fallback_label"] = fallback_label
        result["status"] = status
        results[target_id] = result

    return results
