import importlib.util
import json
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
spec=importlib.util.spec_from_file_location('animation',ROOT/'scripts/09-animation/animation.py')
animation=importlib.util.module_from_spec(spec);spec.loader.exec_module(animation)
SVG='<svg xmlns="http://www.w3.org/2000/svg" width="200" height="100" viewBox="0 0 200 100"><rect width="200" height="100" fill="white"/><rect id="stage" x="10" y="10" width="80" height="60" fill="red"/><text id="title" x="100" y="50">Hello</text></svg>'

def plan(technique='opacity_reveal',target='stage'):
 return {'duration':2,'fps':4,'final_hold':0.5,'loop':False,'effects':[{'target_id':target,'technique':technique,'start':0,'duration':1,'purpose':'emphasize stage'}]}

class AnimationTests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.path=Path(self.tmp.name);self.svg=self.path/'master.svg';self.svg.write_text(SVG)
 def test_explicit_and_automatic_decisions(self):
  self.assertTrue(animation.decide('animated','GIF requested')['animate'])
  self.assertFalse(animation.decide('static','static only')['animate'])
  self.assertFalse(animation.decide('auto','dense reference',False)['animate'])
  with self.assertRaises(ValueError):animation.decide('auto','needs judgment')
 def test_validation_failures(self):
  self.assertTrue(animation.validate_plan(plan('typewriter'),self.svg))
  self.assertTrue(animation.validate_plan(plan(target='missing'),self.svg))
  p=plan();p['effects'][0]['duration']=9;self.assertTrue(animation.validate_plan(p,self.svg))
  p=plan();p['effects'].append(p['effects'][0]);self.assertTrue(animation.validate_plan(p,self.svg))
  p=plan();p['effects'][0]['relationship_id']='rel';self.assertTrue(animation.validate_plan(p,self.svg))
 def test_frame_reveal_preserves_text_and_position(self):
  out=self.path/'frame.svg';animation.frame_svg(self.svg,plan(target='title'),0.5,out)
  _,elements=animation.svg_elements(out);self.assertEqual(elements['title'].text,'Hello');self.assertEqual(elements['title'].get('x'),'100');self.assertEqual(elements['title'].get('opacity'),'0.5')
 def test_missing_inputs(self):
  _,errors=animation.read_inputs(self.path);self.assertTrue(errors)
 def test_code_render_handoff_rejects_changed_master(self):
  run=self.path/'run';run.mkdir();step=run/'step-08';step.mkdir()
  for name,(kind,version) in animation.EXPECTED.items():
   doc={'step':kind,'version':version,'run_id':'run','status':'success'}
   if name.startswith('08-'):doc['generation_method']='code_render_react_svg'
   (run/name).write_text(json.dumps(doc))
  (run/'08-validation-report.json').write_text(json.dumps({'overall':{'valid':True},'visual_review':{'status':'approved'}}))
  svg=step/'infographic.svg';svg.write_text(SVG);png=step/'infographic.png';png.write_bytes(b'png')
  (step/'render-report.json').write_text(json.dumps({'outputs':{'svg':{'path':'step-08/infographic.svg','sha256':animation.digest(svg)},'png':{'path':'step-08/infographic.png','sha256':animation.digest(png)}}}))
  self.assertEqual(animation.read_inputs(run)[1],[])
  svg.write_text(SVG+' ');self.assertTrue(any('svg master' in e for e in animation.read_inputs(run)[1]))
 def test_actual_gif_reveal_and_pulse(self):
  if not shutil.which('ffmpeg') or not shutil.which('ffprobe'):self.skipTest('ffmpeg unavailable')
  original=animation.digest(self.svg)
  for effect in ('opacity_reveal','opacity_pulse'):
   out=self.path/(effect+'.gif');result=animation.render(self.svg,plan(effect),out)
   self.assertTrue(out.is_file());self.assertEqual(result['frame_count'],8);self.assertGreater(result['distinct_rendered_frames'],1);self.assertEqual(animation.digest(self.svg),original)
 def test_gsap_capture_from_step08_fixture(self):
  chrome='/Applications/Google Chrome.app/Contents/MacOS/Google Chrome'
  if not Path(chrome).exists() or not shutil.which('ffmpeg'): self.skipTest('Chrome or ffmpeg unavailable')
  run=self.path/'run';shutil.copytree(ROOT/'tests/08-visual-generation/fixtures/render-smoke',run)
  cmd=['node',str(ROOT/'scripts/08-visual-generation/renderer/render.mjs'),'--run-dir',str(run),'--scale','1']
  proc=subprocess.run(cmd,capture_output=True,text=True,timeout=180);self.assertEqual(proc.returncode,0,proc.stdout+proc.stderr)
  for name,(kind,version) in animation.EXPECTED.items():
   doc={'step':kind,'version':version,'run_id':'run','status':'success'}
   if name.startswith('08-'):doc['generation_method']='code_render_react_svg'
   (run/name).write_text(json.dumps(doc))
  (run/'08-validation-report.json').write_text(json.dumps({'overall':{'valid':True},'visual_review':{'status':'approved'}}))
  result=animation.render_gsap(run,4,0.5,False,chrome)
  self.assertEqual(result['frame_count'],7);self.assertTrue((run/'step-09/animated.gif').is_file())
  self.assertEqual(result['visual_review'],'pending')
  review=self.path/'review.json';review.write_text(json.dumps({'gif_sha256':result['gif_sha256'],'status':'approved','method':'playback_inspection','evidence':'test fixture review'}))
  outcome=animation.finalize_gsap(run,review);self.assertEqual(outcome['status'],'success')
  self.assertEqual(outcome['artifacts']['sha256'],result['gif_sha256'])

if __name__=='__main__':unittest.main()
