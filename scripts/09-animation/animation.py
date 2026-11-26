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
    if data.get('08-visual-generation.json',{}).get('generation_method') == 'code_render_react_svg':
        try:
            render_report=json.loads((run/'step-08/render-report.json').read_text())
            for kind in ('svg','png'):
                entry=render_report['outputs'][kind]; path=(run/entry['path']).resolve()
                if not path.is_relative_to(run.resolve()) or digest(path)!=entry['sha256']: errors.append(f'Step 08 {kind} master missing or changed')
        except (OSError,ValueError,KeyError,TypeError): errors.append('Step 08 render report or master fingerprints missing')
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

def render_gsap(run, fps, final_hold, loop, chrome):
    """Capture Step 08's seekable GSAP page; never approve the result automatically."""
    run=Path(run).resolve(); data,errors=read_inputs(run)
    if errors: raise ValueError('; '.join(errors))
    if not (1 <= fps <= 60 and 0 <= final_hold <= 60): raise ValueError('invalid fps or final hold')
    report=json.loads((run/'step-08/render-report.json').read_text()); motion=report.get('motion',{})
    if report.get('status')!='rendered' or motion.get('errors') or motion.get('final_frame_matches_static') is not True: raise ValueError('Step 08 motion final-state check did not pass')
    duration=float(motion.get('duration',0))
    if not math.isfinite(duration) or not 0<duration<=120: raise ValueError('invalid motion duration')
    page=(run/motion['page']).resolve()
    if not page.is_relative_to(run/'step-08/build') or not page.is_file(): raise ValueError('invalid motion page')
    masters=[run/'step-08/infographic.svg',run/'step-08/infographic.png',page]
    before=[digest(p) for p in masters]
    width=int(report['width']); height=int(report['height'])
    if not 0<width<=8192 or not 0<height<=8192: raise ValueError('invalid frame dimensions')
    if not shutil.which('ffmpeg') or not shutil.which('ffprobe'): raise ValueError('ffmpeg and ffprobe required')
    out=run/'step-09'; gif=out/'animated.gif'; record=out/'animation-report.json'; frames=out/'frames'
    if gif.exists() or record.exists() or frames.exists(): raise ValueError('animation artifacts already exist; preserve them before rerunning')
    out.mkdir(exist_ok=True)
    capture=Path(__file__).with_name('capture.mjs')
    command=['node',str(capture),str(page),str(frames),str(width),str(height),str(fps),str(duration),str(final_hold),str(chrome)]
    result=subprocess.run(command,capture_output=True,text=True,timeout=3600)
    if result.returncode: raise RuntimeError('frame capture failed: '+result.stderr[-3000:])
    count=math.ceil((duration+final_hold)*fps)
    files=sorted(frames.glob('frame-*.png'))
    if len(files)!=count or len({digest(p) for p in files})<2: raise RuntimeError('wrong frame count or no detectable motion')
    palette=out/'palette.png'
    result=subprocess.run(['ffmpeg','-v','error','-framerate',str(fps),'-i',str(frames/'frame-%05d.png'),'-vf','palettegen=stats_mode=diff','-y',str(palette)],capture_output=True,text=True)
    if result.returncode: raise RuntimeError('palette generation failed: '+result.stderr)
    result=subprocess.run(['ffmpeg','-v','error','-framerate',str(fps),'-i',str(frames/'frame-%05d.png'),'-i',str(palette),'-lavfi','paletteuse=dither=sierra2_4a','-loop','0' if loop else '-1','-y',str(gif)],capture_output=True,text=True)
    if result.returncode: raise RuntimeError('GIF encoding failed: '+result.stderr)
    probe=subprocess.run(['ffprobe','-v','error','-select_streams','v:0','-count_frames','-show_entries','stream=width,height,nb_read_frames','-of','json',str(gif)],capture_output=True,text=True)
    if probe.returncode: raise RuntimeError('GIF decode failed: '+probe.stderr)
    info=json.loads(probe.stdout)['streams'][0]
    if int(info.get('nb_read_frames',0))!=count or [info['width'],info['height']]!=[width,height]: raise RuntimeError('GIF frame count or dimensions mismatch')
    if [digest(p) for p in masters]!=before: raise RuntimeError('Step 08 master or motion page changed')
    result={'method':'gsap_playwright','frame_count':count,'fps':fps,'duration':duration,'final_hold':final_hold,'loop':loop,'dimensions':[width,height],'gif_sha256':digest(gif),'svg_sha256':before[0],'png_sha256':before[1],'motion_page_sha256':before[2],'visual_review':'pending'}
    record.write_text(json.dumps(result,indent=2)+'\n'); return result

def finalize_gsap(run, review_path):
    """Record a reviewed GIF, binding approval to the actual files and masters."""
    run=Path(run).resolve(); _,errors=read_inputs(run)
    if errors: raise ValueError('; '.join(errors))
    report=json.loads((run/'step-09/animation-report.json').read_text())
    review=json.loads(Path(review_path).read_text()); gif=run/'step-09/animated.gif'
    if report.get('method')!='gsap_playwright' or digest(gif)!=report.get('gif_sha256'): raise ValueError('GIF is missing or changed')
    for key,path in [('svg_sha256',run/'step-08/infographic.svg'),('png_sha256',run/'step-08/infographic.png'),('motion_page_sha256',run/'step-08/build/motion.html')]:
        if digest(path)!=report.get(key): raise ValueError('animation source changed since capture')
    if review.get('gif_sha256')!=digest(gif) or review.get('status')!='approved' or review.get('method')!='playback_inspection' or not str(review.get('evidence','')).strip(): raise ValueError('current GIF requires recorded playback inspection')
    out=run/'step-09'; paths=[out/'visual-review.json',run/'09-animation.json',run/'09-validation-report.json']
    if any(p.exists() for p in paths): raise ValueError('animation review artifacts exist; preserve them before rerunning')
    outcome={'step':'09-animation','version':'1.0','run_id':run.name,'status':'success','method':'gsap_playwright','artifacts':{'gif':'step-09/animated.gif','sha256':digest(gif),'report':'step-09/animation-report.json'},'warnings':[],'errors':[]}
    validation={'step':'09-animation','run_id':run.name,'overall':{'valid':True,'errors':[]},'visual_review':{'status':'approved','sha256':digest(gif)}}
    for path,obj in zip(paths,[review,outcome,validation]):
        with path.open('x') as f: json.dump(obj,f,indent=2);f.write('\n')
    return outcome

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__); sub=p.add_subparsers(dest='action',required=True)
    inp=sub.add_parser('validate-input'); inp.add_argument('--run-dir',type=Path,required=True)
    v=sub.add_parser('validate-plan'); v.add_argument('--svg',type=Path,required=True);v.add_argument('--plan',type=Path,required=True)
    r=sub.add_parser('render');r.add_argument('--run-dir',type=Path,required=True);r.add_argument('--svg',type=Path,required=True);r.add_argument('--plan',type=Path,required=True);r.add_argument('--output',type=Path,required=True)
    g=sub.add_parser('render-gsap');g.add_argument('--run-dir',type=Path,required=True);g.add_argument('--fps',type=int,default=20);g.add_argument('--final-hold',type=float,default=2);g.add_argument('--loop',action='store_true');g.add_argument('--chrome',default='/Applications/Google Chrome.app/Contents/MacOS/Google Chrome')
    f=sub.add_parser('finalize-gsap');f.add_argument('--run-dir',type=Path,required=True);f.add_argument('--review',type=Path,required=True)
    args=p.parse_args()
    try:
        if args.action=='validate-input': _,errors=read_inputs(args.run_dir); result={'valid':not errors,'errors':errors}
        elif args.action=='validate-plan': errors=validate_plan(json.loads(args.plan.read_text()),args.svg);result={'valid':not errors,'errors':errors}
        elif args.action=='render-gsap': result=render_gsap(args.run_dir,args.fps,args.final_hold,args.loop,args.chrome);errors=[]
        elif args.action=='finalize-gsap': result=finalize_gsap(args.run_dir,args.review);errors=[]
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
