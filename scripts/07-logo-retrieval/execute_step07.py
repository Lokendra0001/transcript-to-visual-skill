#!/usr/bin/env python3
"""Checkpointed Step 07 executor. Candidates are supplied by an AI research phase."""
import argparse,json,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parent))
from discover_assets import discover
from normalize_assets import normalize
from retrieve_assets import retrieve
from validate_input import validate as validate_input
from verify_assets import verify
from contact_sheet import generate as contact_sheet
from inspection import validate as validate_inspections
from logo_dev import LogoDev
from generate_fallback import create as create_fallback

def dump(path,data): path.parent.mkdir(parents=True,exist_ok=True);path.write_text(json.dumps(data,indent=2)+'\n')
def load(path,default):
 try:return json.loads(path.read_text())
 except FileNotFoundError:return default
def normalized(value):return ''.join(character for character in (value or '').lower() if character.isalnum())
def logo_dev_candidate(request,provider,attempts):
 """Resolve only an exact brand-name match, then use the API's signed file URL."""
 name=request.get('canonical_entity_name') or ''
 if not name or not provider.configured():
  attempts.append({'asset_request_id':request['id'],'name':name,'outcome':'not_configured' if not provider.configured() else 'not_attempted'})
  return None
 # A source name that is itself a domain should use the provider's direct
 # domain resolver; search is a name-matching endpoint and can rank it away.
 if '.' in name and ' ' not in name:
  brand=provider.brand(name.lower(),'domain')
  if not brand.get('ok'):
   attempts.append({'asset_request_id':request['id'],'name':name,'outcome':'brand_lookup_failed',**{key:value for key,value in brand.items() if key!='data'}})
   return None
  profile=brand.get('data',{}).get('data',{});logo=profile.get('logo') or {}
  if not logo.get('url'):
   attempts.append({'asset_request_id':request['id'],'name':name,'outcome':'no_logo_in_brand_profile','domain':name.lower()})
   return None
  attempts.append({'asset_request_id':request['id'],'name':name,'outcome':'resolved','domain':profile.get('domain'),'brand_id':profile.get('id'),'source_format':(logo.get('source') or {}).get('format')})
  return {'entity_id':request.get('entity_id'),'name':name,'url':logo['url'],'source_category':'logo_dev_api','identity_evidence':'Direct Logo.dev domain lookup for '+name.lower()+'.','provider_brand_id':profile.get('id'),'provider_domain':profile.get('domain')}
 search=provider.search(name)
 if not search.get('ok'):
  attempts.append({'asset_request_id':request['id'],'name':name,'outcome':'failed',**{key:value for key,value in search.items() if key!='data'}})
  return None
 matches=search.get('data',{}).get('data',[])
 match=next((item for item in matches if normalized(item.get('name'))==normalized(name)),None)
 if not match:
  attempts.append({'asset_request_id':request['id'],'name':name,'outcome':'no_exact_match','candidate_count':len(matches)})
  return None
 brand=provider.brand(match['domain'],'domain')
 if not brand.get('ok'):
  attempts.append({'asset_request_id':request['id'],'name':name,'outcome':'brand_lookup_failed',**{key:value for key,value in brand.items() if key!='data'}})
  return None
 profile=brand.get('data',{}).get('data',{});logo=profile.get('logo') or {}
 if not logo.get('url'):
  attempts.append({'asset_request_id':request['id'],'name':name,'outcome':'no_logo_in_brand_profile','domain':match.get('domain')})
  return None
 attempts.append({'asset_request_id':request['id'],'name':name,'outcome':'resolved','domain':match.get('domain'),'brand_id':profile.get('id'),'source_format':(logo.get('source') or {}).get('format')})
 return {'entity_id':request.get('entity_id'),'name':name,'url':logo['url'],'source_category':'logo_dev_api','identity_evidence':'Exact Logo.dev search match followed by a Logo.dev brand lookup for '+match['domain']+'.','provider_brand_id':profile.get('id'),'provider_domain':match.get('domain')}
def reusable_original(record,candidate):
 download=record.get('download') or {}
 prior_candidate=record.get('candidate') or {}
 path=download.get('path')
 if path and prior_candidate.get('url')==candidate.get('url') and Path(path).is_file():return Path(path)
 return None
def execute(run,candidates,inspections=None,strict=False,allow_generated_fallback=True):
 errors,run_id=validate_input(run)
 if errors:return {'status':'blocked','errors':errors}
 step=run/'step-07'; assets=run/'assets'; originals=assets/'originals'; prepared=assets/'logos'
 arch=load(run/'04-workflow-architecture.json',{});writing=load(run/'05-content-writing.json',{})
 discovery=discover(arch,writing);dump(step/'asset-discovery.json',discovery)
 previous=load(step/'retrieval-attempts.json',[]); prior={x.get('asset_request_id'):x for x in previous}; by_entity={c.get('entity_id'):c for c in candidates}; records=[]; selected=[]; mappings=[]; provider=LogoDev();provider_attempts=[];fallback_assets=[]
 for request in discovery['unique_asset_requests']:
  record=prior.get(request['id'],{'asset_request_id':request['id'],'entity_id':request.get('entity_id'),'selection_status':'unresolved'});prior_candidate=record.get('candidate') or {};candidate=by_entity.get(request.get('entity_id')) or logo_dev_candidate(request,provider,provider_attempts) or prior_candidate;record['candidate']=candidate
  if candidate and candidate.get('url'):
   original=reusable_original({**record,'candidate':prior_candidate},candidate)
   if original:
    got={'ok':True,'path':str(original),'reused_after_revalidation':True};record['download']=got
   else:
    got=retrieve(candidate['url'],originals/request['id']);record['download']=got
    original=Path(got['path']) if got.get('ok') else None
   if got.get('ok') and original:
    checked=verify(original);record['verification']=checked
    # A stale file from an older URL-based suffix scheme is not reusable.
    if not checked.get('valid') and got.get('reused_after_revalidation'):
     got=retrieve(candidate['url'],originals/request['id']);record['download']=got
     original=Path(got['path']) if got.get('ok') else None
     checked=verify(original) if original else {'valid':False,'reason':'redownload failed'};record['verification']=checked
    if checked.get('valid'):
     destination=prepared/(request['id']+original.suffix.lower());result=normalize(original,destination);record['normalization']=result
     if result.get('valid'):
      record['selection_status']='selected';selected.append({'id':request['id'],'entity_id':request.get('entity_id'),'prepared_file_path':str(destination.relative_to(run)),'verification_status':'verified','visual_verification_status':'pending','visually_inspected':False,'source_url':candidate['url']})
  records.append(record)
 # A fallback is produced after the normal source ladder is exhausted. It is
 # explicitly recorded as non-official, never as an exact logo.
 if allow_generated_fallback:
  selected_entities={asset['entity_id']:asset for asset in selected}
  for request,record in zip(discovery['unique_asset_requests'],records):
   candidate=by_entity.get(request.get('entity_id')) or {};fallback=candidate.get('fallback') or {'type':'generated_visual_fallback','reason':'No usable authentic asset was available after the configured source ladder.'}
   if record.get('selection_status')=='selected':continue
   parent=selected_entities.get(fallback.get('parent_entity_id'));parent_path=run/parent['prepared_file_path'] if parent else None
   generated=create_fallback(prepared/(request['id']+'.svg'),request.get('canonical_entity_name') or request['id'],parent_path,fallback.get('parent_display_name'))
   checked=verify(generated['path'])
   if not checked.get('valid'):continue
   representation=generated['representation_type'];record['selection_status']=representation;record['fallback']={'type':representation,'parent_asset_id':parent['id'] if parent else None,'reason':fallback.get('reason','authorised generated visual fallback')};record['verification']=checked
   asset={'id':request['id'],'entity_id':request.get('entity_id'),'prepared_file_path':str(Path(generated['path']).relative_to(run)),'verification_status':'verified','visual_verification_status':'pending','visually_inspected':False,'source_url':None,'representation_type':representation,'fallback_reason':record['fallback']['reason']};selected.append(asset);selected_entities[asset['entity_id']]=asset;fallback_assets.append(asset)
 for occurrence in discovery['asset_mappings']:
  asset=next((x for x in selected if x['id']==occurrence['unique_asset_request_id']),None)
  mappings.append({**occurrence,'asset_id':asset['id'] if asset else None,'resolution_status':'selected_pending_visual_verification' if asset else ('unresolved_strict' if strict else 'text_label_fallback')})
 inspections=inspections or [];inspection_errors=validate_inspections(inspections,selected) if selected else [];sheet=contact_sheet(run,selected,discovery['unique_asset_requests']);dump(step/'retrieval-attempts.json',records);dump(step/'research-records.json',candidates);dump(step/'logo-dev-attempts.json',{'provider':'Logo.dev API v2 adapter','credential_configured':provider.configured(),'attempts':provider_attempts,'fallback_required':any(item.get('outcome')!='resolved' for item in provider_attempts)});dump(step/'visual-inspections.json',inspections)
 unresolved=len(discovery['unique_asset_requests'])-len(selected);blocked=strict and unresolved>0
 output={'step':'07-logo-retrieval','version':'1.0','status':'blocked' if blocked else ('warning' if inspection_errors or unresolved else 'success'),'run_id':run_id,'sources':{},'strict_asset_coverage':strict,'generated_fallbacks_authorized':allow_generated_fallback,'asset_requirements':arch.get('asset_requirements',[]),'unique_asset_requests':discovery['unique_asset_requests'],'retrieval_attempts':records,'assets':selected,'asset_mappings':mappings,'candidate_records':records,'fallback_assets':fallback_assets,'visual_inspections':inspections,'contact_sheet':sheet,'warnings':['Selected assets require actual visual inspection before complete verification.'] if inspection_errors else [],'errors':['strict coverage unmet'] if blocked else [],'coverage_assessment':{'total_occurrences':len(mappings),'unique_requests':len(discovery['unique_asset_requests']),'retrieved':len(selected),'unresolved_unique_assets':unresolved,'unresolved_occurrences':len(mappings)-sum(bool(x['asset_id']) for x in mappings),'text_fallbacks':0 if strict else len(mappings)-sum(bool(x['asset_id']) for x in mappings),'generated_fallbacks':len(fallback_assets)}}
 dump(run/'07-logo-retrieval.json',output);dump(run/'07-validation-report.json',{'deterministic':'pending post-inspection','selected_assets':len(selected)});return output
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--run-dir',type=Path,required=True);p.add_argument('--candidates',type=Path,required=True);p.add_argument('--inspections',type=Path);p.add_argument('--strict-coverage',action='store_true');p.set_defaults(allow_generated_fallback=True);p.add_argument('--no-generated-fallback',dest='allow_generated_fallback',action='store_false');p.add_argument('--allow-generated-fallback',dest='allow_generated_fallback',action='store_true',help=argparse.SUPPRESS);x=p.parse_args();print(json.dumps(execute(x.run_dir,load(x.candidates,[]),load(x.inspections,[]) if x.inspections else [],x.strict_coverage,x.allow_generated_fallback),indent=2))
