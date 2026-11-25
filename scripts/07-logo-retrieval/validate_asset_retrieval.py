#!/usr/bin/env python3
import argparse,json
from pathlib import Path
def load(p):return json.loads(p.read_text())
def validate(run):
 try:a=load(run/'04-workflow-architecture.json');r=load(run/'07-logo-retrieval.json')
 except Exception as e:return ['missing or invalid JSON']
 e=[];req={x.get('id'):x for x in a.get('asset_requirements',[]) if isinstance(x,dict)};maps={x.get('asset_requirement_id'):x for x in r.get('asset_mappings',[]) if isinstance(x,dict)}
 if r.get('step')!='07-logo-retrieval' or r.get('version')!='1.0' or r.get('run_id')!=a.get('run_id'):e.append('invalid Step 07 contract')
 for rid,x in req.items():
  m=maps.get(rid)
  if not m:e.append('missing mapping: '+str(rid));continue
  if m.get('target_id')!=x.get('target_id') or m.get('target_scope')!=x.get('target_scope'):e.append('invalid target mapping: '+str(rid))
  if x.get('required') and m.get('resolution_status') in {'unresolved','text_label_fallback','optional_omitted',None}:e.append('required asset unresolved: '+str(rid))
 candidates={x.get('id'):x for x in r.get('candidate_records',[]) if isinstance(x,dict)}
 for candidate in candidates.values():
  if candidate.get('selection_status')=='selected' and candidate.get('verification_status')=='rejected':e.append('rejected candidate selected: '+str(candidate.get('id')))
  if candidate.get('selection_status')=='selected' and candidate.get('visual_verification_status')=='complete' and not candidate.get('visually_inspected'):e.append('uninspected candidate reported visually complete: '+str(candidate.get('id')))
 return e
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--run-dir',type=Path,required=True);x=p.parse_args();e=validate(x.run_dir);print(json.dumps({'valid':not e,'errors':e},indent=2));raise SystemExit(0 if not e else 2)
