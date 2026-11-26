#!/usr/bin/env python3
"""Validate a Claude-authored Step 05 artifact; never generate copy."""
import argparse,json,sys
from pathlib import Path
def load(p): return json.loads(Path(p).read_text(encoding='utf-8'))
def metrics(t): return {'words':len(t.split()),'characters':len(t)}
def validate(a,r):
 e=[]
 if a.get('step')!='04-workflow-architecture' or a.get('version')!='1.1': return ['Invalid Step 04 artifact.']
 if r.get('step')!='05-content-writing' or r.get('version')!='1.0' or r.get('run_id')!=a.get('run_id'): e.append('Invalid Step 05 contract or run ID.')
 req={x.get('id'):x for x in a.get('content_requirements',[]) if isinstance(x,dict)}; valid={x.get('id') for k in ('visual_units','sections','nodes','connections') for x in a.get(k,[]) if isinstance(x,dict)}; seen=set()
 for x in r.get('content_items',[]):
  seen.add(x.get('content_requirement_id'))
  rep=x.get('representation')
  if rep is not None:
   if not isinstance(rep,dict): e.append('Invalid representation plan.'); continue
   kind=rep.get('type'); types={'text','concise_label','logo','icon','relationship','group','context_only'}
   if kind not in types or not isinstance(rep.get('meaning'),str) or not rep['meaning'].strip() or not isinstance(rep.get('reason'),str) or not rep['reason'].strip(): e.append('Invalid representation type, meaning or reason.')
   if kind=='context_only' and x.get('required'): e.append('Required meaning cannot be context only.')
   if kind in ('text','concise_label') and (not isinstance(rep.get('visible_text'),str) or not rep['visible_text'].strip()): e.append('Visible text required for text representation.')
   if kind in ('logo','icon') and (not isinstance(rep.get('asset_refs'),list) or not rep['asset_refs'] or not all(isinstance(v,str) and v.strip() for v in rep['asset_refs'])): e.append('Asset references required for visual representation.')
   if kind in ('relationship','group') and (not isinstance(rep.get('relationship_refs'),list) or not rep['relationship_refs'] or not all(isinstance(v,str) and v.strip() for v in rep['relationship_refs'])): e.append('Relationship references required for visual representation.')
  if x.get('content_requirement_id') not in req or any(t not in valid for t in x.get('target_refs',[]) if t is not None):e.append('Invalid requirement or target.')
  if x.get('status')=='generated' and (not isinstance(x.get('preferred_text'),str) or x.get('length_metrics')!=metrics(x['preferred_text'])):e.append('Invalid text metrics.')
  if x.get('status') not in {'generated','omitted_optional','blocked'}:e.append('Invalid item status.')
 for rid,x in req.items():
  if x.get('required') and rid not in seen:e.append('Unsatisfied required content requirement.')
 return e
def main(argv=None):
 p=argparse.ArgumentParser();p.add_argument('--run-dir',type=Path,required=True);x=p.parse_args(argv)
 try:e=validate(load(x.run_dir/'04-workflow-architecture.json'),load(x.run_dir/'05-content-writing.json'))
 except Exception as q:e=[f'invalid_json: {q}']
 json.dump({'valid':not e,'errors':e},sys.stdout,indent=2);sys.stdout.write('\n');return 0 if not e else 2
if __name__=='__main__':raise SystemExit(main())
