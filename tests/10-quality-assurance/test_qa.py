import importlib.util
import tempfile
import json
import os
import subprocess
import sys
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
spec=importlib.util.spec_from_file_location('qa',ROOT/'scripts/10-quality-assurance/qa.py')
qa=importlib.util.module_from_spec(spec);spec.loader.exec_module(qa)
try:
 from PIL import Image
except ImportError:
 Image=None


@unittest.skipIf(Image is None, 'Pillow is required for actual image decoding tests')
class TestQualityAssurance(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.dir=Path(self.tmp.name)
  self.png=self.dir/'visual.png';Image.new('RGB',(24,24),'white').save(self.png)
  self.arch={'connections':[{'id':'r1','relationship_type':'sequence','visual_representation_required':True}]}
  self.content={'content_items':[{'id':'c1','required':True,'preferred_text':'Approved'},{'id':'optional','required':False}]}
  self.assets={'asset_mappings':[{'asset_requirement_id':'a1','required':True}]}
 def review(self):
  checks={k:{'status':'passed','method':'visual_inspection','evidence':'inspected actual artifact'} for k in qa.CHECKS}
  checks['technical']['method']='deterministic';checks['animation']={'status':'not_applicable','method':'semantic_comparison','evidence':'static only','reason':'static request'}
  return {'run_id':'run','artifact_sha256':qa.digest(self.png),'animation_preference':'static','checks':checks,
          'content_items':[{'id':'c1','status':'passed','evidence':'visible'}],
          'relationships':[{'id':'r1','status':'passed','evidence':'direction checked'}],
          'assets':[{'id':'a1','status':'passed','evidence':'compared with source'}],'issues':[]}
 def evaluate(self, review, **kw):
  return qa.evaluate('run',self.png,review,self.arch,self.content,self.assets,**kw)
 def test_actual_png_decode_and_valid_mock_review(self):
  self.assertEqual(qa.inspect_artifact(self.png)['dimensions'],[24,24]); self.assertEqual(self.evaluate(self.review())['decision'],'approved')
 def test_missing_required_content_and_duplicates_fail(self):
  r=self.review();r['content_items']=[];self.assertEqual(self.evaluate(r)['decision'],'blocked')
  r=self.review();r['assets'].append(r['assets'][0]);self.assertEqual(self.evaluate(r)['decision'],'blocked')
 def test_missing_visual_and_stale_hash_block(self):
  r=self.review();r['checks']['design']['status']='not_executed';self.assertEqual(self.evaluate(r)['decision'],'blocked')
  r=self.review();Image.new('RGB',(24,24),'red').save(self.png);self.assertEqual(self.evaluate(r)['decision'],'blocked')
 def test_export_handoff_rejects_changed_artifact(self):
  result=self.evaluate(self.review());self.assertTrue(qa.verify_handoff(result))
  Image.new('RGB',(24,24),'red').save(self.png);self.assertFalse(qa.verify_handoff(result))
 def test_unresolved_wrong_content_or_relationship_blocks(self):
  for category in ('content','text','relationships','assets','readability','reference'):
   r=self.review();r['checks'][category]['status']='failed';self.assertEqual(self.evaluate(r)['decision'],'blocked')
 def test_issue_severity_and_planned_routing(self):
  r=self.review();issue={'id':'i','category':'visual','severity':'major','description':'bad','artifact':'v','region':'x','expected':'a','observed':'b','upstream_refs':[],'method':'visual','confidence':'high','recommended_correction':'fix','owner':'08','resolution':'open'}
  r['issues']=[issue];self.assertEqual(self.evaluate(r,attempts_remaining=1)['decision'],'correction_required');self.assertEqual(self.evaluate(r)['decision'],'blocked')
  self.assertEqual(qa.route_issue(issue)['status'],'planned_not_executed')
  issue['severity']='minor';self.assertEqual(self.evaluate(r)['decision'],'approved_with_warnings')
 def test_explicit_animation_cannot_skip(self):
  self.assertEqual(self.evaluate(self.review(),animation_requested=True)['decision'],'blocked')
 def test_actual_gif_decode_and_corruption(self):
  gif=self.dir/'motion.gif';Image.new('RGB',(24,24),'red').save(gif,save_all=True,append_images=[Image.new('RGB',(24,24),'blue')],duration=100,loop=0)
  info=qa.inspect_artifact(gif);self.assertEqual(info['status'],'passed');self.assertEqual(info['frame_count'],2)
  gif.write_bytes(b'GIF89a broken');self.assertEqual(qa.inspect_artifact(gif)['status'],'failed')
 def test_invalid_png_and_no_motion_gif_rejected(self):
  self.png.write_bytes(b'not a PNG');self.assertEqual(qa.inspect_artifact(self.png)['status'],'failed')
  gif=self.dir/'still.gif';Image.new('RGB',(24,24),'red').save(gif,format='GIF')
  self.assertEqual(qa.inspect_artifact(gif)['status'],'failed')
 def test_warning_on_required_check_and_unverified_fix_block(self):
  r=self.review();r['checks']['content']={'status':'warning','method':'semantic_comparison','evidence':'unclear','non_blocking_reason':'unclear'}
  self.assertEqual(self.evaluate(r)['decision'],'blocked')
  r=self.review();r['issues']=[{'id':'i','category':'visual','severity':'major','description':'bad','artifact':'v','region':'x','expected':'a','observed':'b','upstream_refs':[],'method':'visual','confidence':'high','recommended_correction':'fix','owner':'08','resolution':'resolved','resolution_evidence':'rechecked','verified_artifact_sha256':'old'}]
  self.assertEqual(self.evaluate(r)['decision'],'blocked')
 def test_svg_raster_wrapper_not_vector(self):
  svg=self.dir/'wrapped.svg';svg.write_text('<svg xmlns="http://www.w3.org/2000/svg"><image href="data:image/png;base64,AA"/></svg>')
  self.assertEqual(qa.inspect_artifact(svg)['classification'],'raster_wrapped')
 def test_diverse_structures_do_not_override_review(self):
  for kind in ('sequence','branch','comparison','hierarchy','architecture','timeline','framework','composite','dense','minimal'):
   self.arch['connections'][0]['relationship_type']=kind
   self.assertEqual(self.evaluate(self.review())['decision'],'approved')
 def test_cli_writes_isolated_reports_without_overwrite(self):
  run=self.dir/'run';run.mkdir();visual=run/'visual.png';Image.new('RGB',(24,24),'white').save(visual)
  for name,step,version in qa.UPSTREAM:
   doc={'step':step,'version':version,'run_id':'run','status':'success'}
   if name.startswith('04-'):doc.update(self.arch)
   if name.startswith('05-'):doc.update(self.content)
   if name.startswith('07-'):doc.update(self.assets)
   if name.startswith('09-'):doc['status']='skipped'
   (run/name).write_text(json.dumps(doc))
  r=self.review();r['artifact_sha256']=qa.digest(visual);review_path=self.dir/'input-review.json';review_path.write_text(json.dumps(r))
  cmd=[sys.executable,str(ROOT/'scripts/10-quality-assurance/qa.py'),'evaluate','--run-dir',str(run),'--artifact',str(visual),'--review',str(review_path),'--write']
  first=subprocess.run(cmd,capture_output=True,text=True,env=os.environ.copy());self.assertEqual(first.returncode,0,first.stdout+first.stderr)
  self.assertTrue((run/'10-quality-assurance.json').is_file());self.assertEqual(json.loads((run/'10-quality-assurance.json').read_text())['decision'],'approved')
  second=subprocess.run(cmd,capture_output=True,text=True,env=os.environ.copy());self.assertNotEqual(second.returncode,0)


if __name__=='__main__':unittest.main()
