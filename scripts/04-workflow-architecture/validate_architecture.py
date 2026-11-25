#!/usr/bin/env python3
"""Structural validator for a Claude-authored Step 04 architecture."""
from __future__ import annotations
import argparse,json,sys
from pathlib import Path

def load(p):
    try:return json.loads(Path(p).read_text(encoding='utf-8'))
    except Exception as e:raise ValueError(f'invalid_json: {p}') from e
def validate(a,c,r):
    e=[]
    if a.get('step')!='02-content-analysis' or c.get('step')!='03-content-classification':return ['Invalid upstream artifacts.']
    if a.get('run_id')!=c.get('run_id') or r.get('run_id')!=a.get('run_id'):e.append('Run IDs must match.')
    if r.get('step')!='04-workflow-architecture' or r.get('version')!='1.1':e.append('Invalid Step 04 contract.')
    units={x.get('id') for x in r.get('visual_units',[]) if isinstance(x,dict)}; sections={x.get('id'):x for x in r.get('sections',[]) if isinstance(x,dict)}; nodes={x.get('id'):x for x in r.get('nodes',[]) if isinstance(x,dict)}
    if len(units)!=len(r.get('visual_units',[])) or len(sections)!=len(r.get('sections',[])) or len(nodes)!=len(r.get('nodes',[])):e.append('Duplicate or missing IDs.')
    for sid,s in sections.items():
        if s.get('visual_unit_id') not in units:e.append(f'{sid} has unknown unit.')
        p=s.get('parent_section_id')
        if p is not None and p not in sections:e.append(f'{sid} has unknown parent.')
        seen={sid}
        while p is not None:
            if p in seen:e.append(f'Containment cycle at {sid}.');break
            seen.add(p); p=sections.get(p,{}).get('parent_section_id')
    for nid,n in nodes.items():
        if n.get('visual_unit_id') not in units or n.get('section_id') not in sections:e.append(f'{nid} has invalid ownership.')
    for x in r.get('connections',[]):
        if x.get('source_node_id') not in nodes or x.get('target_node_id') not in nodes:e.append('Connection endpoint missing.')
        elif nodes[x['source_node_id']].get('visual_unit_id')!=nodes[x['target_node_id']].get('visual_unit_id'):e.append('Cross-unit connection.')
        if x.get('relationship_type') is None or x.get('representation_mode') is None or not isinstance(x.get('visual_representation_required'),bool):e.append('Connection lacks relationship communication fields.')
    valid_targets={'visual_unit':units,'section':set(sections),'node':set(nodes),'connection':{x.get('id') for x in r.get('connections',[]) if isinstance(x,dict)},'global':{None}}
    for item in r.get('content_requirements',[]):
        scope=item.get('target_scope'); target=item.get('target_id')
        if scope not in valid_targets or target not in valid_targets.get(scope,set()):e.append('Content requirement has an invalid target.')
        if not isinstance(item.get('required'),bool) or item.get('priority') not in {'primary','secondary','supporting','contextual'} or not item.get('semantic_purpose'):e.append('Content requirement lacks required semantics.')
    for item in r.get('asset_requirements',[]):
        target=item.get('target_id')
        if target not in nodes and target not in sections:e.append('Asset requirement has an invalid target.')
    coverage=r.get('coverage_assessment',{})
    if coverage.get('unrepresented_required_refs') or coverage.get('unrepresented_required_associations'):e.append('Required content is unrepresented.')
    return e
def main(argv=None):
    p=argparse.ArgumentParser();p.add_argument('--run-dir',type=Path,required=True);x=p.parse_args(argv)
    try:e=validate(load(x.run_dir/'02-content-analysis.json'),load(x.run_dir/'03-content-classification.json'),load(x.run_dir/'04-workflow-architecture.json'))
    except ValueError as q:e=[str(q)]
    checks=[{'id':'deterministic-structural','method':'validator','execution_status':'executed','result':'pass' if not e else 'fail','affected_references':[],'failure_explanation':None if not e else '; '.join(e)}]
    json.dump({'valid':not e,'errors':e,'checks':checks},sys.stdout,indent=2);sys.stdout.write('\n');return 0 if not e else 2
if __name__=='__main__':raise SystemExit(main())
