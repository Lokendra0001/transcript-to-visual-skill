#!/usr/bin/env python3
"""Discover reference files and deterministic metadata; never classify design."""
from __future__ import annotations
import argparse, hashlib, json
from pathlib import Path

SUPPORTED = {".png", ".jpg", ".jpeg", ".webp", ".svg", ".pdf"}

def fingerprint(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()

def readable(path: Path) -> tuple[bool, str | None]:
    try:
        start = path.read_bytes()[:8192]
    except OSError as exc:
        return False, f"unreadable: {exc.__class__.__name__}"
    suffix = path.suffix.lower()
    valid = {
        ".png": start.startswith(b"\x89PNG\r\n\x1a\n"),
        ".jpg": start.startswith(b"\xff\xd8"), ".jpeg": start.startswith(b"\xff\xd8"),
        ".webp": start.startswith(b"RIFF") and start[8:12] == b"WEBP",
        ".pdf": start.startswith(b"%PDF-"),
        ".svg": b"<svg" in start.lower(),
    }
    return (True, None) if valid.get(suffix) else (False, "format signature is missing or malformed")

def discover(templates_dir: Path) -> dict:
    templates, unavailable, fingerprints = [], [], {}
    if not templates_dir.is_dir():
        return {"templates_dir": str(templates_dir), "discovered_templates": [], "unavailable_templates": [{"path": str(templates_dir), "reason": "templates directory does not exist"}], "duplicates": []}
    for path in sorted(item for item in templates_dir.rglob("*") if item.is_file()):
        relative = path.relative_to(templates_dir).as_posix()
        if path.suffix.lower() not in SUPPORTED:
            unavailable.append({"path": relative, "reason": "unsupported format"}); continue
        ok, reason = readable(path)
        if not ok:
            unavailable.append({"path": relative, "reason": reason}); continue
        value = fingerprint(path)
        record = {"id": "template-" + hashlib.sha256(relative.encode()).hexdigest()[:12], "reference_path": relative, "format": path.suffix.lower()[1:], "fingerprint": value, "byte_size": path.stat().st_size}
        if value in fingerprints:
            record["duplicate_of"] = fingerprints[value]
        else:
            fingerprints[value] = record["id"]
        templates.append(record)
    return {"templates_dir": str(templates_dir), "discovered_templates": templates, "unavailable_templates": unavailable, "duplicates": [x for x in templates if x.get("duplicate_of")]}

def main(argv=None):
    parser = argparse.ArgumentParser(); parser.add_argument("--templates-dir", type=Path, required=True); parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv); args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(discover(args.templates_dir), indent=2) + "\n", encoding="utf-8")
    return 0
if __name__ == "__main__": raise SystemExit(main())
