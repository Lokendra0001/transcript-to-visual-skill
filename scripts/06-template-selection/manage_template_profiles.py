#!/usr/bin/env python3
"""Report profile-cache freshness; visual profiles remain Claude-authored."""
from __future__ import annotations
import argparse, json
from pathlib import Path
# 1.1 adds the content structures a reference suits and does not suit, so selection
# starts from content fit instead of a default style. 1.0 profiles are stale.
SCHEMA_VERSION = "1.1"
REQUIRED = ("structural_characteristics", "design_characteristics", "content_capacity", "adaptability", "limitations", "uncertainties", "evidence")
FIT_LISTS = ("suited_content_structures", "unsuited_content_structures")
def load(path): return json.loads(path.read_text(encoding="utf-8"))
def valid_profile(profile, item, template_id=None):
    """A cached profile is reusable only for the same file, schema and a complete, successful analysis."""
    fit_ok = all(isinstance(profile.get(key), list) and any(isinstance(v, str) and v.strip() for v in profile[key]) for key in FIT_LISTS)
    return (profile.get("template_id")==(template_id or item.get("id")) and profile.get("reference_path")==item.get("reference_path") and profile.get("reference_fingerprint")==item.get("fingerprint") and profile.get("profile_schema_version")==SCHEMA_VERSION and profile.get("visual_analysis_status")=="success" and all(key in profile for key in REQUIRED) and fit_ok)
def main(argv=None):
    parser=argparse.ArgumentParser(); parser.add_argument("--discovery",type=Path,required=True); parser.add_argument("--profile-dir",type=Path,required=True); parser.add_argument("--output",type=Path,required=True); args=parser.parse_args(argv)
    discovery=load(args.discovery); args.profile_dir.mkdir(parents=True,exist_ok=True); states=[]
    for item in discovery.get("discovered_templates",[]):
        profile_path=args.profile_dir / f"{item['id']}.json"; state="needs_visual_analysis"; reason="profile is absent"
        if profile_path.is_file():
            try:
                profile=load(profile_path)
                matches=valid_profile(profile,item)
                state, reason=("valid_cached", None) if matches else ("stale", "profile identity, fingerprint, schema, analysis status, required content, or suited/unsuited content structures differ")
            except Exception: state, reason="stale", "profile JSON is invalid"
        states.append({"template_id":item["id"],"profile_path":str(profile_path),"cache_state":state,"reason":reason})
    args.output.parent.mkdir(parents=True,exist_ok=True); args.output.write_text(json.dumps({"profile_schema_version":SCHEMA_VERSION,"profiles":states},indent=2)+"\n",encoding="utf-8")
    return 0
if __name__ == "__main__": raise SystemExit(main())
