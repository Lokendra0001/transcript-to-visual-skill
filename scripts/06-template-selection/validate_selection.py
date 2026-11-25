#!/usr/bin/env python3
"""Deterministically validate a Claude-authored Step 06 selection artifact."""
from __future__ import annotations
import argparse, hashlib, json, sys
from pathlib import Path

ASSESSMENTS = {"highly_compatible", "compatible", "compatible_with_adaptations", "weakly_compatible", "incompatible", "unable_to_evaluate"}
def load(path): return json.loads(path.read_text(encoding="utf-8"))
def ids(items): return {x.get("id") for x in items if isinstance(x, dict) and x.get("id")}
def digest(path):
    h=hashlib.sha256()
    with path.open("rb") as f:
        for b in iter(lambda:f.read(1024*1024),b""): h.update(b)
    return h.hexdigest()
def source_error(artifact, step, version, run_id):
    return artifact.get("step") != step or artifact.get("version") != version or artifact.get("run_id") != run_id or artifact.get("status") not in {"success","warning"} or bool(artifact.get("errors"))
def valid_profile(profile, item, template_id):
    required=("structural_characteristics","design_characteristics","content_capacity","adaptability","limitations","uncertainties","evidence")
    return (profile.get("template_id")==template_id and profile.get("reference_path")==item.get("reference_path") and profile.get("reference_fingerprint")==item.get("fingerprint") and profile.get("profile_schema_version")=="1.0" and profile.get("visual_analysis_status")=="success" and all(key in profile for key in required))

def validate(run_dir: Path, templates_dir: Path):
    errors=[]
    try:
        classification, architecture, writing, result = (load(run_dir/n) for n in ("03-content-classification.json","04-workflow-architecture.json","05-content-writing.json","06-template-selection.json"))
    except Exception as exc: return [f"invalid_json_or_missing: {exc.__class__.__name__}"]
    run_id=result.get("run_id")
    if result.get("step") != "06-template-selection" or result.get("version") != "1.0" or result.get("status") not in {"success","warning","blocked"}: errors.append("invalid Step 06 contract")
    if source_error(classification,"03-content-classification","1.0",run_id) or source_error(architecture,"04-workflow-architecture","1.1",run_id) or source_error(writing,"05-content-writing","1.0",run_id): errors.append("invalid or mismatched upstream artifact")
    expected_sources={"classification":("03-content-classification","1.0"),"architecture":("04-workflow-architecture","1.1"),"content_writing":("05-content-writing","1.0")}
    for key,(step,version) in expected_sources.items():
        source=result.get("sources",{}).get(key,{})
        if source.get("step")!=step or source.get("version")!=version or source.get("run_id")!=run_id: errors.append(f"invalid source reference: {key}")
    library=result.get("template_library",{}); discovered={x.get("id"):x for x in library.get("discovered_templates",[]) if isinstance(x,dict)}
    if len(discovered)!=len(library.get("discovered_templates",[])): errors.append("duplicate or missing discovered template IDs")
    for tid,item in discovered.items():
        path=templates_dir/item.get("reference_path","")
        if not path.is_file(): errors.append(f"template file missing: {tid}")
        elif item.get("fingerprint") != digest(path): errors.append(f"template fingerprint changed: {tid}")
    analyzed={x.get("template_id"):x for x in library.get("analyzed_templates",[]) if isinstance(x,dict)}
    profiles_dir=run_dir/"step-06"/"template-profiles"
    for tid,item in analyzed.items():
        if tid not in discovered: errors.append(f"analyzed unknown template: {tid}"); continue
        profile_path=profiles_dir/f"{item.get('profile_id', tid)}.json"
        try: profile=load(profile_path)
        except Exception: errors.append(f"missing or invalid profile: {tid}"); continue
        if not valid_profile(profile,discovered[tid],tid): errors.append(f"stale or incomplete profile: {tid}")
    unit_ids=ids(architecture.get("visual_units",[])); selection_by_unit={x.get("visual_unit_id"):x for x in result.get("template_selections",[]) if isinstance(x,dict)}
    if len(selection_by_unit)!=len(result.get("template_selections",[])): errors.append("duplicate or missing template selections")
    for unit in unit_ids:
        if result.get("status") != "blocked" and unit not in selection_by_unit: errors.append(f"unselected visual unit: {unit}")
    evaluations={(x.get("visual_unit_id"),x.get("template_id")):x for x in result.get("candidate_evaluations",[]) if isinstance(x,dict)}
    for unit in unit_ids:
        for tid in analyzed:
            if (unit,tid) not in evaluations: errors.append(f"candidate evaluation missing: {unit}/{tid}")
    for key,evaluation in evaluations.items():
        if key[0] not in unit_ids or key[1] not in analyzed or evaluation.get("assessment") not in ASSESSMENTS or not isinstance(evaluation.get("selection_eligible"),bool): errors.append("invalid candidate evaluation")
    for unit,selection in selection_by_unit.items():
        tid=selection.get("template_id"); evaluation=evaluations.get((unit,tid))
        if unit not in unit_ids or tid not in analyzed or not evaluation or not evaluation.get("selection_eligible"): errors.append(f"ineligible selection: {unit}")
        if selection.get("reference_path") != discovered.get(tid,{}).get("reference_path") or not selection.get("profile_id") or not selection.get("selection_rationale"): errors.append(f"incomplete selection: {unit}")
    required={
        *( ("section",x.get("id")) for x in architecture.get("sections",[]) if isinstance(x,dict)),
        *( ("node",x.get("id")) for x in architecture.get("nodes",[]) if isinstance(x,dict)),
        *( ("connection",x.get("id")) for x in architecture.get("connections",[]) if isinstance(x,dict) and x.get("visual_representation_required")),
        *( ("content_item",x.get("id")) for x in writing.get("content_items",[]) if isinstance(x,dict) and x.get("required")),
        *( ("layout_requirement",x.get("id")) for x in architecture.get("layout_requirements",[]) if isinstance(x,dict) and x.get("level")=="mandatory"),
        *( ("asset_requirement",x.get("id")) for x in architecture.get("asset_requirements",[]) if isinstance(x,dict) and x.get("required")),
    }
    mapped={(x.get("target_type"),x.get("target_id")) for x in result.get("content_template_mapping",[]) if isinstance(x,dict) and x.get("representation_strategy")}
    missing=required-mapped
    if missing: errors.append("required mapping missing: "+", ".join(f"{t}:{i}" for t,i in sorted(missing)))
    if result.get("status")=="success" and (result.get("errors") or errors): errors.append("success artifact contains errors")
    return errors

def main(argv=None):
    p=argparse.ArgumentParser(); p.add_argument("--run-dir",type=Path,required=True); p.add_argument("--templates-dir",type=Path,default=Path("references/templates")); args=p.parse_args(argv)
    errors=validate(args.run_dir,args.templates_dir)
    checks=[{"id":"deterministic-template-selection","method":"python structural validator","execution_status":"executed","result":"pass" if not errors else "fail","affected_references":[],"failure_explanation":None if not errors else "; ".join(errors)}]
    print(json.dumps({"valid":not errors,"errors":errors,"checks":checks},indent=2)); return 0 if not errors else 2
if __name__=="__main__": raise SystemExit(main())
