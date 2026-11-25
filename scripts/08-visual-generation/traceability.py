#!/usr/bin/env python3
"""Create deterministic upstream-to-visual traceability; no design inference."""
def build(architecture, writing, selection, assets, plan):
    plan_ids={x.get('id') for x in plan.get('components',[])}|{x.get('id') for x in plan.get('connectors',[])}
    entries=[]
    for node in architecture.get('nodes',[]):
        if isinstance(node,dict):
            nid=node.get('id');entries.append({'upstream':'04','id':nid,'represented':any(str(x).startswith(str(nid)) for x in plan_ids)})
    for item in writing.get('content_items',[]):
        if isinstance(item,dict) and item.get('required'):
            entries.append({'upstream':'05','id':item.get('id'),'represented':bool(item.get('target_refs'))})
    for mapping in assets.get('asset_mappings',[]):
        if isinstance(mapping,dict):entries.append({'upstream':'07','id':mapping.get('asset_requirement_id'),'represented':mapping.get('resolution_status') not in {'unresolved',None}})
    return {'entries':entries,'missing':[x for x in entries if not x['represented']]}
