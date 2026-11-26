import importlib.util
import json
import tempfile
import unittest
import zipfile
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
spec=importlib.util.spec_from_file_location('export',ROOT/'scripts/11-final-export/export.py')
exp=importlib.util.module_from_spec(spec);spec.loader.exec_module(exp)
try:
 from PIL import Image
except ImportError:
 Image=None


@unittest.skipIf(Image is None,'Pillow required for actual decoding')
class ExportTests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
  self.run=Path(self.tmp.name)/'run';self.run.mkdir();self.png=self.run/'approved.png';Image.new('RGB',(30,20),'white').save(self.png)
  self.checks={k:{'status':'passed'} for k in exp.qa_module.CHECKS};self.checks['animation']={'status':'not_applicable','reason':'static'}
  self.report={'step':'10-quality-assurance','version':'1.0','run_id':'run','decision':'approved','errors':[],'failed_checks':[],'checks':self.checks,'issues':[],'handoff':{'approved':True,'static':{'path':str(self.png),'sha256':exp.sha(self.png)},'animation':None}}
  self.plan={'mode':'user_directed','reason':'requested PNG','title':'Market / Growth','formats':['png'],'package_zip':False,'requirements':{}}
 def test_png_copy_is_identical_and_manifest(self):
  result=exp.export(self.run,self.report,self.plan);self.assertEqual(result['status'],'success')
  output=self.run/result['artifacts'][0]['path'];self.assertEqual(exp.sha(output),exp.sha(self.png));self.assertTrue((self.run/'11-validation-report.json').is_file())
  with self.assertRaises(ValueError):exp.export(self.run,self.report,self.plan)
 def test_zip_contains_only_deliverables(self):
  self.plan['package_zip']=True;result=exp.export(self.run,self.report,self.plan)
  with zipfile.ZipFile(self.run/result['package']) as bundle:self.assertEqual(bundle.namelist(),['static/market-growth.png'])
 def test_approval_gate_stale_wrong_run_and_missing_checks(self):
  for key,value in [('decision','blocked'),('run_id','other')]:
   report=dict(self.report);report[key]=value
   with self.assertRaises(ValueError):exp.export(self.run,report,self.plan)
  report=dict(self.report);report['checks']={}
  with self.assertRaises(ValueError):exp.export(self.run,report,self.plan)
  Image.new('RGB',(30,20),'red').save(self.png)
  with self.assertRaises(ValueError):exp.export(self.run,self.report,self.plan)
 def test_unsupported_format_and_constraints_block(self):
  self.plan['formats']=['svg'];self.assertEqual(exp.export(self.run,self.report,self.plan)['status'],'blocked');self.assertFalse((self.run/'final').exists())
  self.plan['formats']=['png'];self.plan['requirements']={'width':100};self.assertEqual(exp.export(self.run,self.report,self.plan)['status'],'blocked')
  self.plan['requirements']={'transparent':True};self.assertEqual(exp.export(self.run,self.report,self.plan)['status'],'blocked')
  self.plan['requirements']={'max_bytes':1};self.assertEqual(exp.export(self.run,self.report,self.plan)['status'],'blocked')
 def test_partial_mandatory_and_optional(self):
  self.plan['formats']=['png','pdf'];result=exp.export(self.run,self.report,self.plan);self.assertEqual(result['status'],'partial_success');self.assertTrue(result['unavailable_formats'][0]['required'])
 def test_actual_approved_gif(self):
  gif=self.run/'approved.gif';Image.new('RGB',(30,20),'red').save(gif,save_all=True,append_images=[Image.new('RGB',(30,20),'blue')],duration=100,loop=0)
  self.report['handoff']['animation']={'path':str(gif),'sha256':exp.sha(gif)};self.plan['formats']=['gif'];self.report['checks']['animation']={'status':'passed','method':'playback_inspection'}
  result=exp.export(self.run,self.report,self.plan);self.assertEqual(result['artifacts'][0]['frame_count'],2);self.assertEqual(result['artifacts'][0]['duration_ms'],200)
 def test_export_separately_approved_svg_with_png(self):
  svg=self.run/'master.svg';svg.write_text('<svg xmlns="http://www.w3.org/2000/svg" width="30" height="20" viewBox="0 0 30 20"><text x="1" y="10">Hello</text></svg>')
  self.report['handoff']['svg']={'path':str(svg),'sha256':exp.sha(svg)};self.plan['formats']=['svg','png']
  result=exp.export(self.run,self.report,self.plan);self.assertEqual(result['status'],'success')
  self.assertEqual(exp.sha(self.run/result['artifacts'][0]['path']),exp.sha(svg))
 def test_outside_run_and_corrupt_source_rejected(self):
  external=Path(self.tmp.name)/'outside.png';Image.new('RGB',(2,2),'black').save(external)
  self.report['handoff']['static']={'path':str(external),'sha256':exp.sha(external)}
  with self.assertRaises(ValueError):exp.export(self.run,self.report,self.plan)
  self.png.write_bytes(b'broken');self.report['handoff']['static']={'path':str(self.png),'sha256':exp.sha(self.png)}
  with self.assertRaises(ValueError):exp.export(self.run,self.report,self.plan)
 def test_safe_names_and_unrecognized_requirements(self):
  self.assertEqual(exp.slug('%%%'),'infographic');self.assertEqual(exp.slug('../Custom & Price'),'custom-price')
  self.plan['requirements']={'editable':True}
  with self.assertRaises(ValueError):exp.export(self.run,self.report,self.plan)
 def test_qa_warning_requires_non_blocking_rationale(self):
  self.report['decision']='approved_with_warnings'
  with self.assertRaises(ValueError):exp.export(self.run,self.report,self.plan)
  self.report['checks']['design']={'status':'warning','non_blocking_reason':'Minor alignment'}
  self.assertEqual(exp.export(self.run,self.report,self.plan)['status'],'success_with_warnings')
 def test_actual_png_transparency_satisfies_requirement(self):
  Image.new('RGBA',(30,20),(0,0,0,0)).save(self.png);self.report['handoff']['static']['sha256']=exp.sha(self.png)
  self.plan['requirements']={'transparent':True};self.assertEqual(exp.export(self.run,self.report,self.plan)['status'],'success')
 def test_animation_without_playback_approval_rejected(self):
  gif=self.run/'approved.gif';Image.new('RGB',(30,20),'red').save(gif,save_all=True,append_images=[Image.new('RGB',(30,20),'blue')],duration=100,loop=0)
  self.report['handoff']['animation']={'path':str(gif),'sha256':exp.sha(gif)};self.plan['formats']=['gif']
  with self.assertRaises(ValueError):exp.export(self.run,self.report,self.plan)
 def test_unsupported_delivery_field_is_not_ignored(self):
  self.plan['external_destination']='https://example.invalid'
  with self.assertRaises(ValueError):exp.export(self.run,self.report,self.plan)


if __name__=='__main__':unittest.main()
