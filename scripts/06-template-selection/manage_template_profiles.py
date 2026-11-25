#!/usr/bin/env python3
"""Report profile-cache freshness; visual profiles remain Claude-authored."""
from __future__ import annotations
import argparse, json
from pathlib import Path
SCHEMA_VERSION = "1.0"
def load(path): return json.loads(path.read_text(encoding="utf-8"))
def valid_profile(profile, item):
    required = ("structural_characteristics", "design_characteristics", "content_capacity", "adaptability", "limitations", "uncertainties", "evidence")
    return (profile.get("template_id")==item["id"] and profile.get("reference_path")==item["reference_path"] and profile.get("reference_fingerprint")==item["fingerprint"] and profile.get("profile_schema_version")==SCHEMA_VERSION and profile.get("visual_analysis_status")=="success" and all(key in profile for key in required))
def main(argv=None):
    parser=argparse.ArgumentParser(); parser.add_argument("--discovery",type=Path,required=True); parser.add_argument("--profile-dir",type=Path,required=True); parser.add_argument("--output",type=Path,required=True); args=parser.parse_args(argv)
    discovery=load(args.discovery); args.profile_dir.mkdir(parents=True,exist_ok=True); states=[]
    for item in discovery.get("discovered_templates",[]):
        profile_path=args.profile_dir / f"{item['id']}.json"; state="needs_visual_analysis"; reason="profile is absent"
        if profile_path.is_file():
            try:
                profile=load(profile_path)
                matches=valid_profile(profile,item)
                state, reason=("valid_cached", None) if matches else ("stale", "profile identity, fingerprint, schema, analysis status, or required profile content differs")
            except Exception: state, reason="stale", "profile JSON is invalid"
        states.append({"template_id":item["id"],"profile_path":str(profile_path),"cache_state":state,"reason":reason})
    args.output.parent.mkdir(parents=True,exist_ok=True); args.output.write_text(json.dumps({"profile_schema_version":SCHEMA_VERSION,"profiles":states},indent=2)+"\n",encoding="utf-8")
    return 0
if __name__ == "__main__": raise SystemExit(main())
