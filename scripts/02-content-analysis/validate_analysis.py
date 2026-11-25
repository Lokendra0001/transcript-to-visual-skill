#!/usr/bin/env python3
"""Validate a Claude-authored Step 02 analysis against its Step 01 artifact.

This script deliberately does not extract semantics. It validates deterministic
contract invariants before Step 03 consumes 02-content-analysis.json.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

STEP01 = "01-input-processing.json"
STEP02 = "02-content-analysis.json"
PHASE_FILES = (
    "02a-context.json", "02b-relevance.json", "02c-information.json",
    "02d-relationships.json", "02e-decisions.json", "02f-consolidated.json",
    "02g-validation-report.json",
)
COLLECTIONS = ("topics", "entities", "facts", "activities", "relationships", "decisions", "requirements", "ambiguities", "relevance_assessment", "excluded_content")
TRACEABLE = ("topics", "entities", "facts", "activities", "relationships", "decisions", "requirements", "ambiguities", "relevance_assessment", "excluded_content")


def load_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ValueError(f"missing_file: {path}") from exc
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError(f"invalid_json: {path}") from exc


def validate_step01(record: Any) -> list[str]:
    errors: list[str] = []
    if not isinstance(record, dict):
        return ["Step 01 artifact must be a JSON object."]
    if record.get("step") != "01-input-processing":
        errors.append("Step 01 artifact has an invalid step value.")
    if record.get("status") != "success":
        errors.append("Step 01 must have status 'success' before analysis.")
    if not isinstance(record.get("metadata"), dict):
        errors.append("Step 01 metadata must be an object.")
    if not isinstance(record.get("segments"), list):
        errors.append("Step 01 segments must be an array.")
    elif len({item.get("id") for item in record["segments"] if isinstance(item, dict)}) != len(record["segments"]):
        errors.append("Step 01 segment IDs must be unique.")
    return errors


def as_list(value: Any, field: str, errors: list[str]) -> list[Any]:
    if not isinstance(value, list):
        errors.append(f"{field} must be an array.")
        return []
    return value


def validate_analysis(record: Any, step01: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if not isinstance(record, dict):
        return ["Step 02 artifact must be a JSON object."]
    for key, value in (("step", "02-content-analysis"), ("version", "2.0")):
        if record.get(key) != value:
            errors.append(f"{key} must equal '{value}'.")
    if record.get("status") not in {"success", "warning", "failed"}:
        errors.append("status must be success, warning, or failed.")
    if not isinstance(record.get("run_id"), str) or not record["run_id"]:
        errors.append("run_id must be a non-empty string.")
    source = record.get("source")
    if not isinstance(source, dict):
        errors.append("source must be an object.")
    else:
        if source.get("step") != "01-input-processing":
            errors.append("source.step must identify Step 01.")
        metadata = step01.get("metadata", {})
        for field in ("input_type", "input_source"):
            if source.get(field) != metadata.get(field):
                errors.append(f"source.{field} must match Step 01 metadata.")
    if not isinstance(record.get("context"), dict):
        errors.append("context must be an object.")
    coverage = record.get("coverage")
    if not isinstance(coverage, dict) or not isinstance(coverage.get("reviewed_segment_ids"), list) or not isinstance(coverage.get("unrepresented_details"), list):
        errors.append("coverage must contain reviewed_segment_ids and unrepresented_details arrays.")
    for field in (*COLLECTIONS, "warnings", "errors"):
        as_list(record.get(field), field, errors)

    segment_ids = {item.get("id") for item in step01.get("segments", []) if isinstance(item, dict)}
    context_refs = record.get("context", {}).get("source_segment_ids") if isinstance(record.get("context"), dict) else None
    if not isinstance(context_refs, list):
        errors.append("context.source_segment_ids must be an array.")
    elif any(ref not in segment_ids for ref in context_refs):
        errors.append("context references an unknown Step 01 segment.")
    all_ids: set[str] = set()
    entity_ids: set[str] = set()
    activity_ids: set[str] = set()
    for collection in COLLECTIONS:
        for index, item in enumerate(as_list(record.get(collection), collection, errors)):
            label = f"{collection}[{index}]"
            if not isinstance(item, dict):
                errors.append(f"{label} must be an object.")
                continue
            item_id = item.get("id")
            if not isinstance(item_id, str) or not item_id:
                errors.append(f"{label}.id must be a non-empty string.")
            elif item_id in all_ids:
                errors.append(f"Duplicate extracted ID: {item_id}.")
            else:
                all_ids.add(item_id)
                if collection == "entities":
                    entity_ids.add(item_id)
                if collection == "activities":
                    activity_ids.add(item_id)
            if collection in TRACEABLE:
                refs = item.get("source_segment_ids")
                if not isinstance(refs, list) or not refs:
                    errors.append(f"{label}.source_segment_ids must be a non-empty array.")
                elif any(ref not in segment_ids for ref in refs):
                    errors.append(f"{label} references an unknown Step 01 segment.")

    allowed_refs = entity_ids | activity_ids
    topic_ids = {item.get("id") for item in record.get("topics", []) if isinstance(item, dict)}
    fact_ids = {item.get("id") for item in record.get("facts", []) if isinstance(item, dict)}
    decision_ids = {item.get("id") for item in record.get("decisions", []) if isinstance(item, dict)}

    def validate_refs(collection: str, field: str, allowed: set[str]) -> None:
        for index, item in enumerate(record.get(collection, [])):
            if not isinstance(item, dict):
                continue
            refs = item.get(field, [])
            if not isinstance(refs, list):
                errors.append(f"{collection}[{index}].{field} must be an array.")
            elif any(ref not in allowed for ref in refs):
                errors.append(f"{collection}[{index}].{field} contains an unknown reference.")

    for collection in ("entities", "facts", "activities"):
        validate_refs(collection, "topic_ids", topic_ids)
    for collection in ("topics",):
        validate_refs(collection, "entity_ids", entity_ids)
        validate_refs(collection, "fact_ids", fact_ids)
        validate_refs(collection, "activity_ids", activity_ids)
    for collection in ("facts", "decisions", "requirements"):
        validate_refs(collection, "entity_ids" if collection == "facts" else "related_entity_ids", entity_ids)
    for collection in ("activities",):
        validate_refs(collection, "actor_entity_ids", entity_ids)
        validate_refs(collection, "input_refs", allowed_refs | fact_ids)
        validate_refs(collection, "output_refs", allowed_refs | fact_ids)
        validate_refs(collection, "dependency_refs", activity_ids)
        associations = record[collection]
        for index, item in enumerate(associations):
            if not isinstance(item, dict):
                continue
            for association in item.get("entity_associations", []):
                if not isinstance(association, dict) or association.get("entity_id") not in entity_ids:
                    errors.append(f"activities[{index}].entity_associations contains an unknown entity.")
                elif association.get("usage_status") not in {"confirmed", "optional", "proposed", "rejected", "excluded", "existing", "historical", "uncertain"}:
                    errors.append(f"activities[{index}].entity_associations has an invalid usage_status.")
    validate_refs("decisions", "supersedes_ids", decision_ids)

    relevance_refs: dict[str, str] = {}
    for item in record.get("relevance_assessment", []):
        if isinstance(item, dict):
            for ref in item.get("source_segment_ids", []):
                if ref in relevance_refs:
                    errors.append("A source segment must appear in only one relevance assessment.")
                relevance_refs[ref] = item.get("classification", "")
    if set(relevance_refs) != segment_ids:
        errors.append("relevance_assessment must cover every Step 01 segment exactly once.")
    elif isinstance(coverage, dict) and set(coverage.get("reviewed_segment_ids", [])) != segment_ids:
        errors.append("coverage.reviewed_segment_ids must cover every Step 01 segment.")
    excluded_refs = {ref for item in record.get("excluded_content", []) if isinstance(item, dict) for ref in item.get("source_segment_ids", [])}
    irrelevant_refs = {ref for ref, classification in relevance_refs.items() if classification == "irrelevant"}
    if excluded_refs != irrelevant_refs:
        errors.append("excluded_content must match fully irrelevant relevance references.")
    if record.get("status") == "success" and record.get("errors"):
        errors.append("success status cannot contain blocking errors.")
    if record.get("status") == "failed" and not record.get("errors"):
        errors.append("failed status must contain at least one error.")
    for index, item in enumerate(as_list(record.get("relationships"), "relationships", errors)):
        if not isinstance(item, dict):
            continue
        for field in ("source_ref", "target_ref", "relationship_type"):
            if not isinstance(item.get(field), str) or not item[field]:
                errors.append(f"relationships[{index}].{field} must be a non-empty string.")
        for field in ("source_ref", "target_ref"):
            if isinstance(item.get(field), str) and item[field] not in allowed_refs:
                errors.append(f"relationships[{index}].{field} must reference an entity or activity ID.")
    return errors


def validate_phase_artifacts(run_dir: Path, run_id: str) -> list[str]:
    errors: list[str] = []
    phase_dir = run_dir / "step-02"
    for filename in PHASE_FILES:
        try:
            artifact = load_json(phase_dir / filename)
        except ValueError as exc:
            errors.append(str(exc))
            continue
        if not isinstance(artifact, dict):
            errors.append(f"{filename} must be a JSON object.")
        elif artifact.get("run_id") != run_id or artifact.get("status") not in {"success", "warning"}:
            errors.append(f"{filename} has an invalid run_id or incomplete status.")
    return errors


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-dir", type=Path, required=True, help="Directory containing the Step 01 and Step 02 artifacts.")
    parser.add_argument("--analysis-file", type=Path, help=f"Analysis file to validate; defaults to <run-dir>/{STEP02}.")
    args = parser.parse_args(argv)
    step01_path = args.run_dir / STEP01
    analysis_path = args.analysis_file or args.run_dir / STEP02
    try:
        step01 = load_json(step01_path)
        errors = validate_step01(step01)
        if not errors:
            analysis = load_json(analysis_path)
            errors = validate_analysis(analysis, step01)
            if not errors:
                errors = validate_phase_artifacts(args.run_dir, analysis["run_id"])
    except ValueError as exc:
        errors = [str(exc)]
    if errors:
        json.dump({"valid": False, "errors": errors}, sys.stdout, indent=2)
        sys.stdout.write("\n")
        return 2
    json.dump({"valid": True, "step01": str(step01_path), "analysis": str(analysis_path)}, sys.stdout, indent=2)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
