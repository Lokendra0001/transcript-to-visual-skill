#!/usr/bin/env python3
"""Check Step 06's three upstream handoffs without interpreting their content."""
from __future__ import annotations
import argparse, json, sys
from pathlib import Path

EXPECTED = (("03-content-classification.json", "03-content-classification", "1.0"), ("04-workflow-architecture.json", "04-workflow-architecture", "1.1"), ("05-content-writing.json", "05-content-writing", "1.0"))
def load(path): return json.loads(path.read_text(encoding="utf-8"))
def validate(run_dir):
    errors, run_ids = [], []
    for filename, step, version in EXPECTED:
        try: artifact = load(run_dir / filename)
        except Exception as exc: errors.append(f"{filename}: invalid_json_or_missing ({exc.__class__.__name__})"); continue
        if artifact.get("step") != step or artifact.get("version") != version: errors.append(f"{filename}: unexpected step or version")
        if artifact.get("status") not in {"success", "warning"}: errors.append(f"{filename}: unusable status")
        if artifact.get("errors"): errors.append(f"{filename}: contains reported errors")
        run_ids.append(artifact.get("run_id"))
    if not run_ids or None in run_ids or len(set(run_ids)) != 1: errors.append("upstream run IDs must be present and match")
    return errors, run_ids[0] if run_ids and len(set(run_ids)) == 1 else None
def main(argv=None):
    parser=argparse.ArgumentParser(); parser.add_argument("--run-dir",type=Path,required=True); args=parser.parse_args(argv)
    errors, run_id=validate(args.run_dir); json.dump({"valid":not errors,"run_id":run_id,"errors":errors},sys.stdout,indent=2); sys.stdout.write("\n"); return 0 if not errors else 2
if __name__ == "__main__": raise SystemExit(main())
