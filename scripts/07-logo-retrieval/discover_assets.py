#!/usr/bin/env python3
"""Extract/deduplicate asset requirements; never infer brand identity."""
import argparse,json
from pathlib import Path
def load(p):return json.loads(p.read_text())
def discover(architecture,writing):
 names={x.get('entity_id'):x.get('canonical_name') or x.get('display_name') for x in writing.get('terminology_registry',[]) if isinstance(x,dict)}
 requests={}; mappings=[]
 for req in architecture.get('asset_requirements',[]):
  if not isinstance(req,dict) or not req.get('id'):continue
  key=(req.get('entity_id'),req.get('asset_type'),req.get('variant'),json.dumps(req.get('usage_constraints',{}),sort_keys=True),json.dumps(req.get('presentation_requirements',{}),sort_keys=True))
  rid='asset-request-'+str(len(requests)+1)
  if key not in requests: requests[key]={'id':rid,'entity_id':req.get('entity_id'),'canonical_entity_name':names.get(req.get('entity_id')) or req.get('subject'),'asset_type':req.get('asset_type'),'variant':req.get('variant'),'requirement_ids':[]}
  requests[key]['requirement_ids'].append(req['id']);mappings.append({'asset_requirement_id':req['id'],'unique_asset_request_id':requests[key]['id'],'target_scope':req.get('target_scope'),'target_id':req.get('target_id'),'required':req.get('required',False),'fallback':req.get('fallback')})
 return {'unique_asset_requests':list(requests.values()),'asset_mappings':mappings}
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--run-dir',type=Path,required=True);p.add_argument('--output',type=Path,required=True);x=p.parse_args();r=discover(load(x.run_dir/'04-workflow-architecture.json'),load(x.run_dir/'05-content-writing.json'));x.output.parent.mkdir(parents=True,exist_ok=True);x.output.write_text(json.dumps(r,indent=2)+'\n')
