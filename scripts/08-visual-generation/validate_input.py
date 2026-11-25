#!/usr/bin/env python3
import argparse,json,sys
from pathlib import Path
EXPECTED=[('03-content-classification.json','03-content-classification','1.0'),('04-workflow-architecture.json','04-workflow-architecture','1.1'),('05-content-writing.json','05-content-writing','1.0'),('06-template-selection.json','06-template-selection','1.0'),('07-logo-retrieval.json','07-logo-retrieval','1.0')]
def validate(run):
 errors=[];ids=[]
 for name,step,version in EXPECTED:
  try:a=json.loads((run/name).read_text())
  except Exception:errors.append(name+' missing or invalid');continue
  if a.get('step')!=step or a.get('version')!=version or a.get('status') not in {'success','warning'} or a.get('errors'):errors.append(name+' unusable')
  ids.append(a.get('run_id'))
 if not ids or None in ids or len(set(ids))!=1:errors.append('run IDs must match')
 return errors,ids[0] if ids and len(set(ids))==1 else None
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--run-dir',type=Path,required=True);x=p.parse_args();e,r=validate(x.run_dir);print(json.dumps({'valid':not e,'run_id':r,'errors':e},indent=2));sys.exit(0 if not e else 2)
