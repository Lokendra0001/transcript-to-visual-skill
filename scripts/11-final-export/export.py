#!/usr/bin/env python3
"""Export exact QA-approved image files; never infer preferences or create designs."""
import argparse
import hashlib
import importlib.util
import json
import os
import re
import shutil
import tempfile
import unicodedata
import zipfile
from datetime import datetime, timezone
from pathlib import Path

QA_PATH = Path(__file__).resolve().parents[1] / '10-quality-assurance' / 'qa.py'
spec = importlib.util.spec_from_file_location('step10qa', QA_PATH)
qa_module = importlib.util.module_from_spec(spec); spec.loader.exec_module(qa_module)
FORMATS = {'png':'PNG', 'jpg':'JPEG', 'jpeg':'JPEG', 'webp':'WEBP', 'gif':'GIF', 'svg':'SVG'}
ALLOWED_REQUIREMENTS = {'width','height','aspect_ratio','transparent','max_bytes'}


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def slug(title):
    text=unicodedata.normalize('NFKD', str(title)).encode('ascii','ignore').decode().lower()
    return re.sub(r'-+', '-', re.sub(r'[^a-z0-9]+','-',text)).strip('-')[:80].strip('-') or 'infographic'


def validated_approval(run, report):
    """Return exact run-scoped approved sources; reject stale or invalid QA handoff."""
    run=Path(run).resolve()
    if report.get('step')!='10-quality-assurance' or report.get('version')!='1.0' or report.get('run_id')!=run.name:
        raise ValueError('Step 10 identity or run ID does not match')
    if report.get('decision') not in ('approved','approved_with_warnings') or report.get('handoff',{}).get('approved') is not True:
        raise ValueError('Step 10 did not approve export')
    if report.get('errors') or report.get('failed_checks'):
        raise ValueError('Step 10 has unresolved errors or failed checks')
    checks=report.get('checks',{})
    if not isinstance(checks,dict) or any(not isinstance(checks.get(name),dict) for name in qa_module.CHECKS):
        raise ValueError('Step 10 mandatory QA checks missing')
    for name,check in checks.items():
        if check.get('status') not in ('passed','warning','not_applicable'):
            raise ValueError(f'Step 10 check {name} did not pass')
        if check.get('status')=='not_applicable' and not check.get('reason'):
            raise ValueError(f'Step 10 check {name} lacks non-applicability reason')
    for issue in report.get('issues',[]):
        if issue.get('severity') in ('critical','major') and issue.get('resolution')!='resolved':
            raise ValueError('Step 10 has unresolved critical or major issue')
    warnings=[]
    for check in report.get('checks',{}).values():
        if check.get('status')=='warning':
            if not check.get('non_blocking_reason'): raise ValueError('QA warning is not classified non-blocking')
            warnings.append(check['non_blocking_reason'])
    for issue in report.get('issues',[]):
        if issue.get('resolution')!='resolved' and issue.get('severity') in ('minor','recommendation'):
            warnings.append(issue.get('description','Non-blocking issue'))
    if report['decision']=='approved_with_warnings' and not warnings:
        raise ValueError('QA warnings missing or not identified as non-blocking')
    sources={}
    for kind in ('static','svg','animation'):
        entry=report['handoff'].get(kind)
        if not entry: continue
        if not isinstance(entry,dict) or not entry.get('path') or not entry.get('sha256'): raise ValueError('incomplete approved artifact entry')
        path=Path(entry['path']); path=(path if path.is_absolute() else run/path).resolve()
        if not path.is_relative_to(run) or not path.is_file(): raise ValueError('approved artifact outside run or missing')
        if sha(path)!=entry['sha256']: raise ValueError('approved artifact hash mismatch')
        info=qa_module.inspect_svg_master(path) if kind=='svg' else qa_module.inspect_artifact(path)
        if info.get('status')!='passed': raise ValueError(f'approved {kind} artifact did not decode or validate: {info.get("errors",info.get("limitations"))}')
        if kind=='animation' and info.get('format')!='GIF': raise ValueError('approved animation is not a supported animated GIF')
        if kind=='static' and info.get('format') not in ('PNG','JPEG','WEBP'): raise ValueError('approved static format unsupported')
        if kind=='svg' and info.get('format')!='SVG': raise ValueError('approved SVG format unsupported')
        sources[kind]={'path':path,'sha256':entry['sha256'],'info':info}
    if 'static' not in sources: raise ValueError('approved static artifact missing')
    if 'animation' in sources:
        animation_check=checks['animation']
        if animation_check.get('status')!='passed' or animation_check.get('method')!='playback_inspection':
            raise ValueError('approved animation requires a passed playback inspection')
    for ref in report.get('upstream_refs',[]):
        if not isinstance(ref,dict) or not ref.get('path') or not ref.get('sha256'): raise ValueError('incomplete upstream fingerprint')
        path=(run/ref['path']).resolve()
        if not path.is_relative_to(run) or not path.is_file() or sha(path)!=ref['sha256']: raise ValueError('upstream evidence changed since QA')
    return sources,warnings


def check_plan(plan):
    if set(plan)-{'mode','reason','title','formats','optional_formats','package_zip','requirements'}:
        raise ValueError('unsupported export-plan field; do not ignore explicit requirements')
    if plan.get('mode') not in ('user_directed','automatic') or not isinstance(plan.get('reason'),str) or not plan['reason'].strip():
        raise ValueError('plan requires mode and rationale')
    formats=plan.get('formats')
    if not isinstance(formats,list) or not formats or any(not isinstance(x,str) or not x.strip() for x in formats): raise ValueError('plan requires requested formats')
    formats=[x.lower().lstrip('.') for x in formats]
    if len(set(formats))!=len(formats): raise ValueError('duplicate format requests')
    optional=plan.get('optional_formats',[])
    if not isinstance(optional,list) or any(x not in formats for x in optional): raise ValueError('optional formats must be requested formats')
    if type(plan.get('package_zip',False)) is not bool: raise ValueError('package_zip must be boolean')
    requirements=plan.get('requirements',{})
    if not isinstance(requirements,dict) or set(requirements)-ALLOWED_REQUIREMENTS:
        raise ValueError('unsupported or invalid export requirement')
    for k in ('width','height','max_bytes'):
        if k in requirements and (type(requirements[k]) is not int or requirements[k]<=0): raise ValueError(f'invalid {k}')
    if 'aspect_ratio' in requirements and (type(requirements['aspect_ratio']) not in (float,int) or not 0 < requirements['aspect_ratio'] < 100): raise ValueError('invalid aspect ratio')
    if 'transparent' in requirements and type(requirements['transparent']) is not bool: raise ValueError('invalid transparency requirement')
    return formats,set(optional),requirements


def satisfies(source, constraints):
    info=source['info']; w,h=info['dimensions']
    if constraints.get('width',w)!=w or constraints.get('height',h)!=h: return 'requested dimensions require unsupported resize'
    if 'aspect_ratio' in constraints and abs(w/h-constraints['aspect_ratio'])>0.001: return 'requested aspect ratio conflicts with approved image'
    if constraints.get('transparent',False):
        if info['format']=='SVG': return 'SVG transparency cannot be verified by this exporter'
        from PIL import Image
        with Image.open(source['path']) as image:
            if image.convert('RGBA').getchannel('A').getextrema()[0] == 255: return 'requested transparency is unavailable'
    if constraints.get('max_bytes',info['bytes'])<info['bytes']: return 'requested file size requires unsupported optimization'
    return None


def export(run, report, plan):
    run=Path(run).resolve()
    sources,warnings=validated_approval(run,report)
    formats,optional,req=check_plan(plan)
    final=run/'final';summary=run/'11-final-export.json';validation=run/'11-validation-report.json'
    if any(x.exists() for x in (final,summary,validation)): raise ValueError('export output already exists; preserve it before rerunning')
    selected=[]; unavailable=[]
    for fmt in formats:
        canonical=FORMATS.get(fmt);kind='animation' if canonical=='GIF' else ('svg' if canonical=='SVG' else 'static')
        source=sources.get(kind); reason=None
        if not canonical: reason='format conversion is unsupported'
        elif not source: reason='approved artifact unavailable'
        elif source['info']['format']!=canonical: reason='conversion from approved source is unsupported'
        else: reason=satisfies(source,req)
        if reason: unavailable.append({'format':fmt,'reason':reason,'required':fmt not in optional})
        else: selected.append((fmt,kind,source))
    if not selected:
        return {'step':'11-final-export','version':'1.0','run_id':run.name,'status':'blocked','unavailable_formats':unavailable,'errors':['No requested approved deliverable can be exported.']}
    mandatory_missing=any(x['required'] for x in unavailable)
    status='partial_success' if mandatory_missing else ('success_with_warnings' if warnings or unavailable else 'success')
    # Stage only copies in the run. TemporaryDirectory removes only this scoped staging directory.
    with tempfile.TemporaryDirectory(prefix='.step11-',dir=run) as tmp:
        stage=Path(tmp)/'final'; stage.mkdir(); artifacts=[]; names=set()
        for fmt,kind,source in selected:
            directory=stage/('animated' if kind=='animation' else 'static');directory.mkdir(exist_ok=True)
            filename=f'{slug(plan.get("title","infographic"))}.{fmt}'
            if filename in names: raise ValueError('duplicate deliverable filename')
            names.add(filename);dest=directory/filename
            if sha(source['path'])!=source['sha256']: raise ValueError('approved artifact changed before copy')
            shutil.copyfile(source['path'],dest)
            if sha(dest)!=source['sha256'] or sha(source['path'])!=source['sha256']: raise ValueError('copy or source fingerprint mismatch')
            checked=qa_module.inspect_svg_master(dest) if kind=='svg' else qa_module.inspect_artifact(dest)
            if checked.get('status')!='passed': raise ValueError('exported file failed decoding')
            artifacts.append({'format':fmt,'kind':kind,'path':str(Path('final')/directory.name/filename),'sha256':sha(dest),'bytes':dest.stat().st_size,'dimensions':checked['dimensions'],'source_sha256':source['sha256'],'frame_count':checked.get('frame_count'),'duration_ms':sum(checked.get('durations_ms',[])) if kind=='animation' else None,'loop':checked.get('loop') if kind=='animation' else None})
        if plan.get('package_zip'):
            with zipfile.ZipFile(stage/'deliverables.zip','x',compression=zipfile.ZIP_DEFLATED) as bundle:
                for item in artifacts:
                    file=stage/Path(item['path']).relative_to('final');bundle.write(file,arcname=str(file.relative_to(stage)))
            with zipfile.ZipFile(stage/'deliverables.zip') as bundle:
                if bundle.testzip() is not None: raise ValueError('ZIP validation failed')
        manifest={'step':'11-final-export','version':'1.0','run_id':run.name,'timestamp':datetime.now(timezone.utc).isoformat(),'status':status,'decision_mode':plan['mode'],'rationale':plan['reason'],'requested_formats':formats,'requirements':req,'qa_decision':report['decision'],'artifacts':artifacts,'unavailable_formats':unavailable,'warnings':warnings,'package':'final/deliverables.zip' if plan.get('package_zip') else None,'limitations':['Lossless copies only; PDF, resizing and format conversions are not implemented.']}
        (stage/'export-manifest.json').write_text(json.dumps(manifest,indent=2,ensure_ascii=False)+'\n')
        (stage/'delivery-summary.md').write_text('# Delivery summary\n\nStatus: '+status.replace('_',' ')+'.\n\n'+''.join('- '+a['path']+'\n' for a in artifacts)+('' if not unavailable else '\nSome requested formats or constraints could not be fulfilled; see the export manifest.\n'))
        os.rename(stage,final)
    manifest['validation']={'status':'passed','method':'decoded byte-identical copies and matching source fingerprints'}
    with summary.open('x') as f: json.dump(manifest,f,indent=2);f.write('\n')
    with validation.open('x') as f: json.dump({'step':'11-final-export','run_id':run.name,'status':status,'checks':manifest['validation'],'unavailable_formats':unavailable},f,indent=2);f.write('\n')
    return manifest


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--run-dir',type=Path,required=True);p.add_argument('--plan',type=Path,required=True);args=p.parse_args()
    try:
        result=export(args.run_dir,json.loads((args.run_dir/'10-quality-assurance.json').read_text()),json.loads(args.plan.read_text()))
        print(json.dumps(result,indent=2,ensure_ascii=False));raise SystemExit(0 if result['status'] in ('success','success_with_warnings') else 2)
    except (OSError,ValueError,KeyError,TypeError) as exc:
        print(json.dumps({'step':'11-final-export','status':'blocked','errors':[str(exc)]},indent=2));raise SystemExit(2)
