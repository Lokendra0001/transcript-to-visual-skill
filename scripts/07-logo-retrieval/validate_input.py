#!/usr/bin/env python3
import argparse,json,sys
from pathlib import Path
EXPECTED=[('02-content-analysis.json','02-content-analysis','2.0'),('04-workflow-architecture.json','04-workflow-architecture','1.1'),('05-content-writing.json','05-content-writing','1.0'),('06-template-selection.json','06-template-selection','1.0')]
def load(p): return json.loads(p.read_text())
def validate(run):
 e=[]; ids=[]
 for n,s,v in EXPECTED:
  try:a=load(run/n)
  except Exception as x:e.append(f'{n}: missing or invalid JSON');continue
  if a.get('step')!=s or a.get('version')!=v or a.get('status') not in {'success','warning'} or a.get('errors'):e.append(f'{n}: unusable contract')
  ids.append(a.get('run_id'))
 if not ids or None in ids or len(set(ids))!=1:e.append('upstream run IDs must match')
 return e,ids[0] if ids and len(set(ids))==1 else None
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--run-dir',type=Path,required=True);x=p.parse_args();e,r=validate(x.run_dir);print(json.dumps({'valid':not e,'run_id':r,'errors':e},indent=2));raise SystemExit(0 if not e else 2)
