#!/usr/bin/env python3
"""Small deterministic SVG opacity animator. Creative decisions belong to the agent."""
import argparse
import copy
import hashlib
import importlib.util
import json
import math
import shutil
import subprocess
import tempfile
import xml.etree.ElementTree as ET
from pathlib import Path

SUPPORTED = {'opacity_reveal', 'opacity_pulse'}
EXPECTED = {'03-content-classification.json':('03-content-classification','1.0'),
            '04-workflow-architecture.json':('04-workflow-architecture','1.1'),
            '06-template-selection.json':('06-template-selection','1.0'),
            '08-visual-generation.json':('08-visual-generation','1.0')}

def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def read_inputs(run):
    run=Path(run); data={}; errors=[]; ids=set()
    for name,(step,version) in EXPECTED.items():
        try: obj=json.loads((run/name).read_text())
        except (OSError,ValueError): errors.append(f'{name}: missing or invalid'); continue
        data[name]=obj; ids.add(obj.get('run_id'))
        if obj.get('step')!=step or obj.get('version')!=version or obj.get('status') not in ('success','warning') or obj.get('errors'): errors.append(f'{name}: unusable')
    if len(ids)!=1 or None in ids or (ids and next(iter(ids))!=run.name): errors.append('run IDs do not match directory')
    try:
        report=json.loads((run/'08-validation-report.json').read_text())
        if report.get('overall',{}).get('valid') is not True: errors.append('Step 08 validation did not pass')
        if report.get('visual_review',{}).get('status') not in ('approved','pass','passed'): errors.append('Step 08 visual review is not approved')
        if report.get('visual_review',{}).get('reference_fidelity_gate') in ('fail','failed'): errors.append('Step 08 reference fidelity failed')
    except (OSError,ValueError): errors.append('Step 08 validation report missing or invalid')
    return data,errors

def decide(mode, reason, auto_animate=None):
    if mode not in ('auto','static','animated'): raise ValueError('invalid preference mode')
    if not isinstance(reason,str) or not reason.strip(): raise ValueError('reason is required')
    if mode=='auto' and not isinstance(auto_animate,bool): raise ValueError('auto requires the executing AI contextual decision')
    return {'preference':mode,'source':'automatic_ai_assessment' if mode=='auto' else 'explicit_user_preference',
            'animate':auto_animate if mode=='auto' else mode=='animated','reason':reason}

def record_skip(run, decision):
    """Record an intentionally static outcome after validating upstream state."""
    run=Path(run); data,errors=read_inputs(run)
    if errors: raise ValueError('; '.join(errors))
    if decision.get('animate') is not False: raise ValueError('skip requires a static decision')
    out=run/'step-09'; out.mkdir(exist_ok=True)
    outcome={'step':'09-animation','version':'1.0','run_id':run.name,'status':'skipped',
             'decision':decision,'sources':list(EXPECTED),'artifacts':{'decision':'step-09/animation-decision.json'},
             'animation_handoff':{'animated':False,'reason':'intentionally static'},'warnings':[],'errors':[]}
    report={'step':'09-animation','run_id':run.name,'overall':{'valid':True,'errors':[]},'outcome':'skipped'}
    for path,obj in [(out/'animation-decision.json',decision),(run/'09-animation.json',outcome),(run/'09-validation-report.json',report)]:
        if path.exists(): raise ValueError(f'refusing to overwrite existing artifact: {path}')
    for path,obj in [(out/'animation-decision.json',decision),(run/'09-animation.json',outcome),(run/'09-validation-report.json',report)]:
        path.write_text(json.dumps(obj,indent=2)+'\n')
    return outcome

def svg_elements(svg):
    tree=ET.parse(svg); root=tree.getroot(); elements={}
    for el in root.iter():
        key=el.get('id')
        if key:
            if key in elements: raise ValueError(f'duplicate SVG ID: {key}')
            elements[key]=el
    return tree,elements

def validate_plan(plan, svg):
    errors=[]
    try: _,elems=svg_elements(svg)
    except (ET.ParseError,OSError,ValueError) as e: return [str(e)]
    try:
        duration=float(plan['duration']); fps=float(plan['fps']); hold=float(plan.get('final_hold',0))
        if not all(math.isfinite(x) for x in (duration,fps,hold)) or not (0<duration<=120 and 0<fps<=60 and 0<=hold<duration): raise ValueError()
    except (KeyError,TypeError,ValueError): return ['invalid duration, fps or final hold']
    effects=plan.get('effects'); seen=set()
    if not isinstance(effects,list) or not effects: return ['plan needs effects']
    for effect in effects:
        if not isinstance(effect,dict): errors.append('invalid effect'); continue
        target=effect.get('target_id'); technique=effect.get('technique')
        if technique not in SUPPORTED: errors.append(f'unsupported technique: {technique}')
        if target not in elems: errors.append(f'missing SVG element: {target}')
        if target in seen: errors.append(f'conflicting effects for {target}')
        seen.add(target)
        try:
            start=float(effect['start']); span=float(effect['duration'])
            if not math.isfinite(start) or not math.isfinite(span) or start<0 or span<=0 or start+span>duration-hold: raise ValueError()
        except (KeyError,TypeError,ValueError): errors.append(f'invalid timing for {target}')
        if not effect.get('purpose'): errors.append(f'missing purpose for {target}')
        if effect.get('relationship_id'): errors.append('directional connector motion is not supported')
    return errors

def frame_svg(svg, plan, t, out):
    tree, elements=svg_elements(svg)
    for effect in plan['effects']:
        el=elements[effect['target_id']]; original=float(el.get('opacity','1'))
        start=float(effect['start']); duration=float(effect['duration']); p=max(0,min(1,(t-start)/duration))
        if effect['technique']=='opacity_reveal': factor=p
        elif 0<p<1: factor=1-0.3*math.sin(math.pi*p)**2
        else: factor=1
        el.set('opacity',str(round(original*factor,5)))
    tree.write(out,encoding='utf-8',xml_declaration=True)

def render(svg, plan, output):
    errors=validate_plan(plan,svg)
    if errors: raise ValueError('; '.join(errors))
    renderer_path=Path(__file__).resolve().parents[1]/'08-visual-generation'/'render_preview.py'
    spec=importlib.util.spec_from_file_location('preview_adapter',renderer_path); adapter=importlib.util.module_from_spec(spec); spec.loader.exec_module(adapter)
    if not shutil.which('ffmpeg') or not shutil.which('ffprobe'): raise RuntimeError('ffmpeg and ffprobe are required')
    before=digest(svg); fps=float(plan['fps']); count=math.ceil(float(plan['duration'])*fps)
    if count<2: raise ValueError('at least two frames required')
    output=Path(output)
    if output.resolve()==Path(svg).resolve(): raise ValueError('output cannot overwrite static master')
    with tempfile.TemporaryDirectory(prefix='step09-') as td:
        td=Path(td); hashes=[]
        for i in range(count):
            f=td/f'frame-{i:05}.svg'; p=td/f'frame-{i:05}.png'; frame_svg(svg,plan,i/fps,f)
            ok,msg=adapter.render(f,p)
            if not ok: raise RuntimeError(f'frame {i} render failed: {msg}')
            hashes.append(digest(p))
        if len(set(hashes))<2: raise RuntimeError('rendered frames contain no detectable motion')
        loop='0' if plan.get('loop',False) else '-1'
        result=subprocess.run(['ffmpeg','-v','error','-framerate',str(fps),'-i',str(td/'frame-%05d.png'),'-loop',loop,'-y',str(td/'out.gif')],capture_output=True,text=True)
        if result.returncode: raise RuntimeError('GIF encoding failed: '+result.stderr)
        probe=subprocess.run(['ffprobe','-v','error','-select_streams','v:0','-count_frames','-show_entries','stream=width,height,nb_read_frames,duration','-of','json',str(td/'out.gif')],capture_output=True,text=True)
        if probe.returncode: raise RuntimeError('GIF decode check failed: '+probe.stderr)
        info=json.loads(probe.stdout)['streams'][0]
        if int(info.get('nb_read_frames',0))!=count: raise RuntimeError('GIF frame count mismatch')
        output.parent.mkdir(parents=True,exist_ok=True); shutil.copyfile(td/'out.gif',output)
    if digest(svg)!=before: raise RuntimeError('static master changed')
    return {'frame_count':count,'distinct_rendered_frames':len(set(hashes)),'fps':fps,'duration':count/fps,'loop':bool(plan.get('loop',False)),'width':info['width'],'height':info['height'],'bytes':output.stat().st_size,'sha256':digest(output),'static_master_sha256':before,'visual_review':'pending'}

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__); sub=p.add_subparsers(dest='action',required=True)
    inp=sub.add_parser('validate-input'); inp.add_argument('--run-dir',type=Path,required=True)
    v=sub.add_parser('validate-plan'); v.add_argument('--svg',type=Path,required=True);v.add_argument('--plan',type=Path,required=True)
    r=sub.add_parser('render');r.add_argument('--run-dir',type=Path,required=True);r.add_argument('--svg',type=Path,required=True);r.add_argument('--plan',type=Path,required=True);r.add_argument('--output',type=Path,required=True)
    args=p.parse_args()
    try:
        if args.action=='validate-input': _,errors=read_inputs(args.run_dir); result={'valid':not errors,'errors':errors}
        elif args.action=='validate-plan': errors=validate_plan(json.loads(args.plan.read_text()),args.svg);result={'valid':not errors,'errors':errors}
        else:
            data,errors=read_inputs(args.run_dir)
            if errors: raise ValueError('; '.join(errors))
            if args.svg.resolve() != (args.run_dir/'step-08/infographic.svg').resolve(): raise ValueError('SVG must be the approved Step 08 master')
            handoff=data['08-visual-generation.json'].get('animation_handoff',{})
            if handoff.get('eligible') is False or handoff.get('available') is False: raise ValueError('Step 08 has no eligible animation handoff')
            if not data['08-visual-generation.json'].get('element_manifest'): raise ValueError('Step 08 element mappings unavailable')
            if args.output.resolve() != (args.run_dir/'step-09/animated.gif').resolve(): raise ValueError('output must be the Step 09 GIF')
            result=render(args.svg,json.loads(args.plan.read_text()),args.output); errors=[]
        print(json.dumps(result,indent=2)); raise SystemExit(2 if errors else 0)
    except (ValueError,RuntimeError,OSError,KeyError) as e:
        print(json.dumps({'valid':False,'error':str(e)},indent=2));raise SystemExit(2)
