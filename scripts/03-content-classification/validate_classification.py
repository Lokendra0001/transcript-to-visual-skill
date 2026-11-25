#!/usr/bin/env python3
"""Validate a Claude-authored Step 03 artifact against Step 02; no semantic output is generated."""
from __future__ import annotations
import argparse, json, sys
from pathlib import Path
from typing import Any

TYPES = {"workflow","process_flow","playbook","framework","hierarchy","taxonomy","comparison","decision_tree","funnel","customer_journey","timeline","roadmap","system_architecture","ecosystem_map","network_diagram","cycle","lifecycle","matrix","checklist","concept_map","data_visualization","informational_infographic","composite_infographic","other"}
SCOPES = {"single_visual", "composite_visual", "multiple_visuals"}
COLLECTIONS = ("topics", "entities", "facts", "activities", "relationships", "decisions", "requirements", "ambiguities")

def load(path: Path) -> Any:
    try: return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc: raise ValueError(f"invalid_json: {path}") from exc

def validate(step02: Any, result: Any) -> list[str]:
    errors=[]
    if not isinstance(step02, dict) or step02.get("step") != "02-content-analysis" or step02.get("status") not in {"success","warning"}: return ["Step 02 is not eligible for classification."]
    if not isinstance(result, dict): return ["Step 03 artifact must be an object."]
    for key, value in (("step","03-content-classification"),("version","1.0")):
        if result.get(key)!=value: errors.append(f"{key} must equal {value}.")
    if result.get("status") not in {"success","warning","failed"}: errors.append("Invalid Step 03 status.")
    if result.get("run_id") != step02.get("run_id"): errors.append("run_id must match Step 02.")
    source=result.get("source",{})
    if source.get("step")!="02-content-analysis" or source.get("run_id")!=step02.get("run_id") or source.get("version")!=step02.get("version"): errors.append("source must identify the exact Step 02 artifact.")
    classification=result.get("classification",{})
    if classification.get("primary_type") not in TYPES: errors.append("Unsupported primary classification.")
    if any(value not in TYPES for value in classification.get("secondary_types",[])): errors.append("Unsupported secondary classification.")
    scope=result.get("visual_scope",{})
    if scope.get("type") not in SCOPES or not isinstance(scope.get("recommended_visual_count"),int) or scope["recommended_visual_count"] < 1: errors.append("Invalid visual scope.")
    units=result.get("visual_units",[])
    if len(units)!=scope.get("recommended_visual_count"): errors.append("Visual unit count must match recommended_visual_count.")
    ids={collection:{item.get("id") for item in step02.get(collection,[]) if isinstance(item,dict)} for collection in COLLECTIONS}
    all_refs=set().union(*ids.values())
    group_ids=set()
    for group in result.get("content_groups",[]):
        if not isinstance(group,dict) or not isinstance(group.get("id"),str): errors.append("Content group lacks an ID."); continue
        group_ids.add(group["id"])
        for field in ("topic_ids","entity_ids","fact_ids","activity_ids","relationship_ids","decision_ids","requirement_ids"):
            if any(ref not in all_refs for ref in group.get(field,[])): errors.append(f"content group {group['id']} has an unknown reference.")
    for unit in units:
        if any(ref not in group_ids for ref in unit.get("content_group_ids",[])): errors.append("Visual unit has an unknown content group.")
    coverage=result.get("coverage_assessment",{})
    if not isinstance(coverage,dict) or coverage.get("unassigned_relevant_refs"): errors.append("Material relevant references are unassigned.")
    return errors

def main(argv=None):
    p=argparse.ArgumentParser(); p.add_argument("--run-dir",type=Path,required=True); args=p.parse_args(argv)
    try: errors=validate(load(args.run_dir/"02-content-analysis.json"),load(args.run_dir/"03-content-classification.json"))
    except ValueError as exc: errors=[str(exc)]
    json.dump({"valid":not errors,"errors":errors},sys.stdout,indent=2); sys.stdout.write("\n"); return 0 if not errors else 2
if __name__=="__main__": raise SystemExit(main())
