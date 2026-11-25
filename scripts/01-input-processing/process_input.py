#!/usr/bin/env python3
"""Create a loss-aware Step 01 JSON record from one text input.

Uses only the Python standard library. It reads UTF-8 (including BOM) and
UTF-16 text files, or text supplied with --text. It never truncates input.
Pass --run-dir to persist the handoff artifact as 01-input-processing.json.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

STEP = "01-input-processing"
VERSION = "1.0"
SUPPORTED_SUFFIXES = {".txt", ".md", ".markdown"}
ARTIFACT_FILENAME = "01-input-processing.json"
SPEAKER_RE = re.compile(
    r"^\s*(?:\[(?P<bracket_timestamp>\d{1,2}:\d{2}(?::\d{2})?)\]\s*)?"
    r"(?P<speaker>[A-Za-z][A-Za-z0-9 ._'-]{0,58})\s*:\s*(?P<text>.*)$"
)
SPEAKER_TIMESTAMP_RE = re.compile(
    r"^\s*(?P<speaker>[A-Za-z][A-Za-z0-9 ._'-]{0,58})\s*"
    r"\((?P<timestamp>\d{1,2}:\d{2}(?::\d{2})?)\)\s*:\s*(?P<text>.*)$"
)
# Markdown-bold labels such as "**Speaker 1:** text" or "**Alice**: text" (Granola markdown exports).
BOLD_SPEAKER_RE = re.compile(
    r"^\s*\*\*(?P<speaker>[A-Za-z][A-Za-z0-9 ._'-]{0,58}?)\s*(?::\s*\*\*|\*\*\s*:)\s*(?P<text>.*)$"
)
TIMESTAMP_RE = re.compile(r"^\[?(\d{1,2}:\d{2}(?::\d{2})?)\]?$")


def empty_result() -> dict[str, Any]:
    return {
        "step": STEP,
        "version": VERSION,
        "status": "failed",
        "metadata": {
            "input_type": "unknown",
            "input_source": None,
            "primary_language": None,
            "additional_languages": [],
            "has_speakers": False,
            "has_timestamps": False,
            "has_multiple_documents": False,
        },
        "original_text": None,
        "normalized_text": None,
        "segments": [],
        "statistics": {"character_count": 0, "word_count": 0, "segment_count": 0},
        "warnings": [],
        "errors": [],
    }


def issue(code: str, message: str) -> dict[str, str]:
    return {"code": code, "message": message}


def read_text_file(path: Path) -> str:
    """Read an approved text extension with strict, BOM-aware decoding."""
    if path.suffix.lower() not in SUPPORTED_SUFFIXES:
        raise ValueError("unsupported_file_type")
    try:
        raw = path.read_bytes()
    except OSError as exc:
        raise ValueError("unreadable_file") from exc
    if raw.startswith((b"\xff\xfe", b"\xfe\xff")):
        encodings = ("utf-16",)
    else:
        encodings = ("utf-8-sig",)
    try:
        return raw.decode(encodings[0], errors="strict")
    except UnicodeDecodeError as exc:
        raise ValueError("invalid_text_encoding") from exc


def normalize_text(text: str) -> str:
    """Make whitespace predictable without changing words, order, or punctuation."""
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    lines = [line.strip() for line in text.split("\n")]
    output: list[str] = []
    blank_run = 0
    for line in lines:
        if line:
            blank_run = 0
            output.append(line)
        else:
            blank_run += 1
            if blank_run <= 1:
                output.append("")
    return "\n".join(output).strip()


def normalize_timestamp(value: str | None) -> str | None:
    if not value:
        return None
    match = TIMESTAMP_RE.match(value.strip())
    if not match:
        return None
    parts = match.group(1).split(":")
    return ":".join(part.zfill(2) for part in parts)


def find_turn(line: str) -> tuple[str, str | None, str] | None:
    """Return a safely identifiable speaker turn; headings and lists are ignored."""
    match = BOLD_SPEAKER_RE.match(line)
    if not match:
        if line.lstrip().startswith(("#", "-", "*", "+")):
            return None
        match = SPEAKER_TIMESTAMP_RE.match(line) or SPEAKER_RE.match(line)
    if not match:
        return None
    speaker = match.group("speaker").strip()
    if speaker.lower() in {"agenda", "notes", "summary", "decision", "actions"}:
        return None
    timestamp = normalize_timestamp(match.groupdict().get("timestamp") or match.groupdict().get("bracket_timestamp"))
    return speaker, timestamp, match.group("text")


def detect_input_type(normalized: str, turns: list[tuple[int, str, str | None, str]]) -> str:
    if len(turns) >= 2:
        return "transcript"
    lowered = normalized.lower()
    if any(marker in lowered for marker in ("requirement", "must ", "should ", "objective", "acceptance criteria")):
        return "written_requirements"
    lines = normalized.splitlines()
    if any(line.lstrip().startswith(("#", "-", "*", "+")) for line in lines):
        return "meeting_notes"
    return "unknown"


def structure_segments(original: str, normalized: str) -> list[dict[str, Any]]:
    """Preserve source order as speaker turns, or as non-empty structural blocks."""
    original_lines = original.replace("\r\n", "\n").replace("\r", "\n").split("\n")
    turn_positions = [(index + 1, *turn) for index, line in enumerate(original_lines) if (turn := find_turn(line))]
    if len(turn_positions) >= 2:
        segments: list[dict[str, Any]] = []
        for sequence, (start_line, speaker, timestamp, first_text) in enumerate(turn_positions, 1):
            next_start = turn_positions[sequence][0] if sequence < len(turn_positions) else len(original_lines) + 1
            continuation = original_lines[start_line:next_start - 1]
            original_content = "\n".join([first_text, *continuation]).strip()
            end_line = next_start - 1
            while end_line > start_line and not original_lines[end_line - 1].strip():
                end_line -= 1
            segments.append({
                "id": f"segment-{sequence:03d}",
                "sequence": sequence,
                "speaker": speaker,
                "timestamp": timestamp,
                "original_text": original_content,
                "normalized_text": normalize_text(original_content),
                "source_location": {"start_line": start_line, "end_line": end_line},
            })
        return segments

    blocks = [block for block in re.split(r"\n\s*\n", original.replace("\r\n", "\n").replace("\r", "\n")) if block.strip()]
    segments = []
    line_cursor = 1
    for sequence, block in enumerate(blocks, 1):
        start_line = next((i + 1 for i, line in enumerate(original_lines[line_cursor - 1:], line_cursor - 1) if line == block.split("\n")[0]), line_cursor)
        end_line = start_line + len(block.split("\n")) - 1
        line_cursor = end_line + 1
        segments.append({
            "id": f"segment-{sequence:03d}",
            "sequence": sequence,
            "speaker": None,
            "timestamp": None,
            "original_text": block,
            "normalized_text": normalize_text(block),
            "source_location": {"start_line": start_line, "end_line": end_line},
        })
    return segments


def process_text(text: str, *, input_source: str | None = None, input_type: str = "auto") -> dict[str, Any]:
    """Return the Step 01 contract for one supplied text value."""
    result = empty_result()
    result["original_text"] = text
    if not text.strip():
        result["errors"].append(issue("empty_input", "Input is empty or whitespace-only."))
        return result
    normalized = normalize_text(text)
    meaningful_characters = re.sub(r"[^\w]", "", normalized, flags=re.UNICODE)
    if len(meaningful_characters) < 2:
        result["errors"].append(issue("insufficient_meaningful_content", "Input does not contain enough meaningful text."))
        return result
    segments = structure_segments(text, normalized)
    turns = [(item["sequence"], item["speaker"] or "", item["timestamp"], item["original_text"]) for item in segments if item["speaker"]]
    identified_type = detect_input_type(normalized, turns) if input_type == "auto" else input_type
    words = re.findall(r"\b\w+\b", normalized, flags=re.UNICODE)
    result.update({
        "status": "success",
        "metadata": {
            "input_type": identified_type,
            "input_source": input_source,
            "primary_language": None,
            "additional_languages": [],
            "has_speakers": bool(turns),
            "has_timestamps": any(item["timestamp"] is not None for item in segments),
            "has_multiple_documents": bool(re.search(r"^\s*(?:---+|===+)\s*(?:document\s+\d+)?\s*$", normalized, re.MULTILINE | re.IGNORECASE)),
        },
        "normalized_text": normalized,
        "segments": segments,
        "statistics": {"character_count": len(text), "word_count": len(words), "segment_count": len(segments)},
    })
    if len(words) < 5 and identified_type != "written_requirements":
        result["warnings"].append(issue("limited_content", "Input is usable but contains limited text."))
    if len(text) > 100_000:
        result["warnings"].append(issue("long_input", "Long input was processed without truncation; preserve all segments for downstream handling."))
    if result["metadata"]["has_multiple_documents"]:
        result["warnings"].append(issue("multiple_documents_detected", "Multiple document sections may be present; confirm their intended relationship."))
    if normalized and normalized[-1] not in ".!?…:;)]}\"'":
        result["warnings"].append(issue("possibly_incomplete", "Input ends without terminal punctuation and may be incomplete."))
    return result


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--text", help="Text supplied directly by the caller.")
    source.add_argument("--input-file", action="append", type=Path, help="One .txt, .md, or .markdown input file.")
    parser.add_argument("--source", default=None, help="Explicit input source, for example granola.")
    parser.add_argument("--input-type", choices=("auto", "transcript", "meeting_notes", "written_requirements", "unknown"), default="auto")
    destination = parser.add_mutually_exclusive_group()
    destination.add_argument(
        "--run-dir",
        type=Path,
        help=f"Workflow run directory. Writes {ARTIFACT_FILENAME} inside it.",
    )
    destination.add_argument("--output", type=Path, help="Explicit JSON output path for inspection or custom integration.")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])
    if args.input_file and len(args.input_file) != 1:
        result = empty_result()
        result["errors"].append(issue("multiple_input_documents", "Supply exactly one input document per invocation."))
    else:
        try:
            text = args.text if args.text is not None else read_text_file(args.input_file[0])
            result = process_text(text, input_source=args.source, input_type=args.input_type)
        except ValueError as exc:
            result = empty_result()
            result["errors"].append(issue(str(exc), "The supplied file could not be processed."))
    rendered = json.dumps(result, ensure_ascii=False, indent=2) + "\n"
    if args.run_dir:
        args.run_dir.mkdir(parents=True, exist_ok=True)
        (args.run_dir / ARTIFACT_FILENAME).write_text(rendered, encoding="utf-8")
    elif args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8")
    else:
        sys.stdout.write(rendered)
    return 0 if result["status"] == "success" else 2


if __name__ == "__main__":
    raise SystemExit(main())
