#!/usr/bin/env python3
"""Deterministic QA support. Visual and semantic judgments require the executing AI."""
import argparse
import hashlib
import json
import math
import xml.etree.ElementTree as ET
from pathlib import Path

CHECKS = ('content', 'text', 'relationships', 'assets', 'design', 'readability', 'reference', 'technical', 'animation')
STATUSES = {'passed', 'failed', 'warning', 'not_applicable', 'not_executed', 'uncertain'}
SEVERITIES = {'critical', 'major', 'minor', 'recommendation'}
UPSTREAM = [('01-input-processing.json','01-input-processing','1.0'),
            ('02-content-analysis.json','02-content-analysis','2.0'),
            ('03-content-classification.json','03-content-classification','1.0'),
            ('04-workflow-architecture.json','04-workflow-architecture','1.1'),
            ('05-content-writing.json','05-content-writing','1.0'),
            ('06-template-selection.json','06-template-selection','1.0'),
            ('07-logo-retrieval.json','07-logo-retrieval','1.0'),
            ('08-visual-generation.json','08-visual-generation','1.0'),
            ('09-animation.json','09-animation','1.0')]


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def inspect_artifact(path):
    """Decode image frames using Pillow; SVG inspection is structural only."""
    path = Path(path)
    try:
        raw = path.read_bytes()
    except OSError as exc:
        return {'status': 'failed', 'errors': [str(exc)]}
    info = {'path': str(path), 'sha256': hashlib.sha256(raw).hexdigest(), 'bytes': len(raw)}
    if path.suffix.lower() == '.svg':
        try:
            if b'<!doctype' in raw.lower() or b'<!entity' in raw.lower():
                raise ValueError('unsafe XML declaration')
            root = ET.fromstring(raw)
            if root.tag.split('}')[-1] != 'svg': raise ValueError('not an SVG root')
            kinds = [element.tag.split('}')[-1] for element in root.iter()]
            if any(tag in ('script','foreignObject') for tag in kinds): raise ValueError('active SVG element')
            raster = 'image' in kinds
            vector = any(tag in ('path','rect','circle','polygon','polyline','line','text','ellipse') for tag in kinds)
            info.update({'status':'not_executed','format':'SVG','classification':'hybrid' if raster and vector else ('raster_wrapped' if raster else ('vector' if vector else 'unknown')),
                         'limitations':['XML structure only; full SVG security and rendering were not validated.']})
        except (ET.ParseError, ValueError) as exc: info.update({'status':'failed','errors':[str(exc)]})
        return info
    try:
        from PIL import Image, ImageSequence
    except ImportError:
        info.update({'status':'not_executed','errors':['Pillow unavailable: cannot decode image'], 'limitations':['Header inspection is not full decoding.']}); return info
    try:
        with Image.open(path) as image:
            fmt=image.format
            if fmt not in ('PNG','JPEG','WEBP','GIF'): raise ValueError('unsupported image format')
            expected={'.png':'PNG','.jpg':'JPEG','.jpeg':'JPEG','.webp':'WEBP','.gif':'GIF'}.get(path.suffix.lower())
            if expected != fmt: raise ValueError('file extension does not match detected image format')
            size=image.size; frames=[]; durations=[]; frame_hashes=[]; loop=image.info.get('loop')
            for frame in ImageSequence.Iterator(image):
                frame.load()
                if frame.size != size: raise ValueError('inconsistent frame dimensions')
                rgba=frame.convert('RGBA'); frame_hashes.append(hashlib.sha256(rgba.tobytes()).hexdigest())
                frames.append(frame.size); durations.append(frame.info.get('duration',0))
            if not frames: raise ValueError('no decodable frames')
            info.update({'status':'passed','format':fmt,'dimensions':list(size),'frame_count':len(frames),
                         'durations_ms':durations,'loop':loop,'distinct_frames':len(set(frame_hashes)),
                         'has_transparency':image.info.get('transparency') is not None or 'A' in image.getbands(),
                         'limitations':['Pixel decoding does not establish content accuracy, logo identity, semantic direction or playback quality.']})
            if fmt == 'GIF' and (len(frames)<2 or len(set(frame_hashes))<2 or any(not isinstance(d,(int,float)) or d<=0 for d in durations)):
                info['status']='failed'; info['errors']=['GIF requires multiple distinct frames with positive durations']
    except (OSError,ValueError,EOFError) as exc:
        info.update({'status':'failed','errors':[str(exc)]})
    return info


def expected_ids(architecture, writing, assets):
    return {
        'content_items': [x['id'] for x in writing.get('content_items',[]) if x.get('required') and x.get('status') != 'omitted_optional'],
        'relationships': [x['id'] for x in architecture.get('connections',[]) if x.get('visual_representation_required')],
        'assets': [x['asset_requirement_id'] for x in assets.get('asset_mappings',[]) if x.get('asset_requirement_id')],
    }


def route_issue(issue):
    """Only classify explicit evidence, never execute corrections."""
    owner=str(issue.get('owner',''))
    if owner not in {f'{n:02}' for n in range(1,10)}: raise ValueError('issue needs an explicit responsible step 01–09')
    return {'issue_id':issue.get('id'), 'owner':owner, 'region':issue.get('region'),
            'observed':issue.get('observed'), 'expected':issue.get('expected'),
            'correction':issue.get('recommended_correction'), 'preserve':'all unrelated approved content and artifacts',
            'status':'planned_not_executed'}


def evaluate(run_id, artifact, review, architecture, writing, assets, animation=None, animation_requested=False, attempts_remaining=0):
    """Validate review completeness and policy; does not verify the review's assertions."""
    errors=[]; failed_checks=[]; issues=review.get('issues',[]); technical=inspect_artifact(artifact)
    if technical.get('status') != 'passed': errors.append('actual static artifact technical inspection did not pass')
    if technical.get('format') not in ('PNG','JPEG','WEBP','SVG'): errors.append('unsupported static visual format')
    if review.get('run_id') != run_id: errors.append('review run ID mismatch')
    if review.get('artifact_sha256') != technical.get('sha256'): errors.append('stale or mismatched review hash')
    preference=review.get('animation_preference')
    if preference not in ('static','animated','auto'): errors.append('animation preference missing or invalid')
    if preference == 'animated': animation_requested=True
    if preference == 'auto' and animation is None and review.get('animation_skip_reason') in (None,''):
        errors.append('automatic animation skip reason missing')
    checks=review.get('checks',{})
    for name in CHECKS:
        check=checks.get(name,{})
        if not isinstance(check,dict) or check.get('status') not in STATUSES:
            errors.append(f'{name}: missing or invalid status'); continue
        status=check['status']; evidence=check.get('evidence'); method=check.get('method')
        if not isinstance(method,str) or not method.strip() or not isinstance(evidence,str) or not evidence.strip(): errors.append(f'{name}: missing method/evidence')
        if status == 'failed': failed_checks.append(name)
        if status == 'warning' and not check.get('non_blocking_reason'): errors.append(f'{name}: warning lacks non-blocking justification')
        if status == 'warning' and name in ('content','text','relationships','assets','technical','animation'): errors.append(f'{name}: mandatory check must pass')
        if status in ('not_executed','uncertain'): errors.append(f'{name}: {status}')
        if status == 'not_applicable':
            allowed = ((name == 'animation' and animation is None and not animation_requested)
                       or (name == 'assets' and not expected_ids(architecture, writing, assets)['assets'])
                       or (name == 'relationships' and not expected_ids(architecture, writing, assets)['relationships']))
            if not allowed or not check.get('reason'): errors.append(f'{name}: invalid not_applicable')
        if name != 'technical' and status in ('passed','warning') and method not in ('visual_inspection','semantic_comparison','playback_inspection'):
            errors.append(f'{name}: direct inspection required')
    for category,expected in expected_ids(architecture,writing,assets).items():
        rows=review.get(category,[])
        if not isinstance(rows,list): errors.append(f'{category}: invalid observations'); continue
        ids=[x.get('id') for x in rows if isinstance(x,dict)]
        if len(ids)!=len(rows) or len(ids)!=len(set(ids)): errors.append(f'{category}: malformed or duplicate IDs')
        if set(ids)!=set(expected): errors.append(f'{category}: missing or unexpected required IDs')
        for row in rows:
            if not isinstance(row,dict) or row.get('status')!='passed' or not str(row.get('evidence','')).strip(): errors.append(f'{category}: incomplete item review')
    if not isinstance(issues,list): issues=[]; errors.append('invalid issue list')
    required_issue_fields=('id','category','severity','description','artifact','region','expected','observed','upstream_refs','method','confidence','recommended_correction','owner','resolution')
    seen=set()
    for issue in issues:
        if not isinstance(issue,dict): errors.append('malformed issue'); continue
        if any(k not in issue or issue[k] in ('',None) for k in required_issue_fields): errors.append('issue missing required fields')
        if issue.get('severity') not in SEVERITIES: errors.append('invalid issue severity')
        if issue.get('id') in seen: errors.append('duplicate issue ID')
        seen.add(issue.get('id'))
        if issue.get('resolution') not in ('open','resolved'): errors.append('invalid issue resolution')
        if issue.get('resolution') == 'resolved' and (not issue.get('resolution_evidence') or issue.get('verified_artifact_sha256') != technical.get('sha256')): errors.append('resolved issue requires regression evidence bound to current artifact')
    open_issues=[i for i in issues if isinstance(i,dict) and i.get('resolution')!='resolved']
    severe=[i for i in open_issues if i.get('severity') in ('critical','major')]
    if animation_requested and animation is None: errors.append('explicitly requested animation missing')
    animation_info=None
    if animation is not None:
        animation_info=inspect_artifact(animation)
        if animation_info.get('status')!='passed' or animation_info.get('format')!='GIF': errors.append('animation technical inspection failed')
        if review.get('animation_sha256') != animation_info.get('sha256'): errors.append('stale or mismatched animation review')
        check=checks.get('animation',{})
        if check.get('status') not in ('passed','warning') or check.get('method') != 'playback_inspection': errors.append('actual animation playback not verified')
    if failed_checks and not severe: errors.append('failed checks require documented critical or major issues')
    if errors: decision='blocked'
    elif severe or failed_checks: decision='correction_required' if attempts_remaining>0 else 'blocked'
    elif open_issues or any(isinstance(c,dict) and c.get('status')=='warning' for c in checks.values()): decision='approved_with_warnings'
    else: decision='approved'
    return {'step':'10-quality-assurance','version':'1.0','run_id':run_id,'decision':decision,
            'reviewed_artifacts':{'static':technical,'animation':animation_info},'checks':checks,'issues':issues,
            'errors':errors,'failed_checks':failed_checks,'method':'deterministic technical and evidence-completeness checks; agent observations are not independently verified',
            'handoff':{'approved':decision in ('approved','approved_with_warnings'),
                       'static': {'path':str(artifact),'sha256':technical.get('sha256')} if decision in ('approved','approved_with_warnings') else None,
                       'animation': {'path':str(animation),'sha256':animation_info.get('sha256')} if animation_info and decision in ('approved','approved_with_warnings') else None,
                       'step_11':'implementation_pending'},
            'limitations':['No automatic visual, semantic, brand identity or playback judgments.', 'Correction routes are plans, not automatic invocations.']}


def load(path): return json.loads(Path(path).read_text())


def validate_upstream(run):
    """Check artifact identity and run linkage; do not trust status as QA proof."""
    run=Path(run); data={}; errors=[]
    for name,step,version in UPSTREAM:
        try: doc=load(run/name)
        except (OSError,ValueError): errors.append(f'{name}: missing or invalid'); continue
        if not isinstance(doc,dict): errors.append(f'{name}: invalid document'); continue
        if doc.get('step') != step or doc.get('version') != version: errors.append(f'{name}: step/version mismatch')
        if name != '01-input-processing.json' and doc.get('run_id') != run.name: errors.append(f'{name}: run ID mismatch')
        if name[:2] in ('01','02','03','04','05','06','07') and (doc.get('status') not in ('success','warning') or doc.get('errors')):
            errors.append(f'{name}: upstream authority unusable')
        data[name]=doc
    return data,errors


def verify_handoff(report):
    """Recheck approved artifact hashes immediately before a future export."""
    handoff=report.get('handoff',{})
    if not handoff.get('approved') or report.get('decision') not in ('approved','approved_with_warnings'):
        return False
    for name in ('static','animation'):
        entry=handoff.get(name)
        if entry:
            try:
                if digest(entry['path']) != entry['sha256']: return False
            except (OSError,KeyError,TypeError): return False
    return bool(handoff.get('static'))


if __name__ == '__main__':
    p=argparse.ArgumentParser(description=__doc__); sub=p.add_subparsers(dest='action',required=True)
    i=sub.add_parser('inspect');i.add_argument('--artifact',type=Path,required=True)
    e=sub.add_parser('evaluate');e.add_argument('--run-dir',type=Path,required=True);e.add_argument('--artifact',type=Path,required=True);e.add_argument('--review',type=Path,required=True);e.add_argument('--animation',type=Path);e.add_argument('--animation-requested',action='store_true');e.add_argument('--attempts-remaining',type=int,default=0);e.add_argument('--write',action='store_true',help='write new Step 10 output files without overwriting existing artifacts')
    args=p.parse_args()
    try:
        if args.action=='inspect': result=inspect_artifact(args.artifact); ok=result['status']=='passed'
        else:
            run=args.run_dir.resolve(); artifact=args.artifact.resolve(); anim=args.animation.resolve() if args.animation else None
            if not artifact.is_relative_to(run) or (anim and not anim.is_relative_to(run)): raise ValueError('reviewed artifacts must be inside the run directory')
            upstream, upstream_errors=validate_upstream(run)
            if upstream_errors: raise ValueError('; '.join(upstream_errors))
            docs=[upstream[f] for f in ('04-workflow-architecture.json','05-content-writing.json','07-logo-retrieval.json')]
            if args.attempts_remaining < 0: raise ValueError('attempts remaining cannot be negative')
            result=evaluate(run.name,artifact,load(args.review),*docs,animation=anim,animation_requested=args.animation_requested,attempts_remaining=args.attempts_remaining)
            result['upstream_refs']=[{'path':name,'sha256':digest(run/name),'status':upstream[name].get('status')} for name,_,_ in UPSTREAM]
            animation_status=upstream['09-animation.json'].get('status')
            if animation_status not in ('success','skipped') or (animation_status == 'success' and anim is None):
                result['errors'].append('Step 09 has no usable animation outcome or its animated artifact is missing')
                result['decision']='blocked'; result['handoff']={'approved':False,'static':None,'animation':None,'step_11':'implementation_pending'}
            if args.write:
                review=load(args.review)
                output=run/'step-10'
                paths=[run/'10-quality-assurance.json',run/'10-validation-report.json',output/'review.json',output/'issues.json',output/'refinement-history.json']
                if any(path.exists() for path in paths): raise ValueError('Step 10 artifacts exist; preserve them before writing a new review')
                output.mkdir(exist_ok=True)
                objects=[result,{'step':'10-quality-assurance','run_id':run.name,'decision':result['decision'],'errors':result['errors'],'method':result['method']},review,review.get('issues',[]),review.get('refinement_history',[])]
                for path,obj in zip(paths,objects):
                    with path.open('x',encoding='utf-8') as stream: json.dump(obj,stream,indent=2,ensure_ascii=False);stream.write('\n')
            ok=result['decision'] in ('approved','approved_with_warnings')
        print(json.dumps(result,indent=2,ensure_ascii=False));raise SystemExit(0 if ok else 2)
    except (OSError,ValueError,KeyError,TypeError) as exc:
        print(json.dumps({'decision':'failed','errors':[str(exc)]}));raise SystemExit(2)
