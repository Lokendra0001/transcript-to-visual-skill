import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
def module(filename):
    path = ROOT / 'scripts/06-template-selection' / filename
    spec = importlib.util.spec_from_file_location(filename.stem, path)
    value = importlib.util.module_from_spec(spec); spec.loader.exec_module(value)
    return value
discover = module(Path('discover_templates.py'))
validator = module(Path('validate_selection.py'))

class TemplateSelectionTests(unittest.TestCase):
    def test_discovery_handles_nested_duplicate_and_malformed_files(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); (root/'nested').mkdir(); png = b'\x89PNG\r\n\x1a\ncontent'
            (root/'one.png').write_bytes(png); (root/'nested'/'two.png').write_bytes(png)
            (root/'bad.png').write_bytes(b'nope'); (root/'note.txt').write_text('x')
            found = discover.discover(root)
            self.assertEqual(2, len(found['discovered_templates']))
            self.assertEqual(1, len(found['duplicates']))
            self.assertEqual(2, len(found['unavailable_templates']))

    def test_valid_selection_covers_required_elements(self):
        with tempfile.TemporaryDirectory() as tmp:
            run, templates = Path(tmp)/'run', Path(tmp)/'templates'; run.mkdir(); templates.mkdir()
            template = templates/'reference.png'; template.write_bytes(b'\x89PNG\r\n\x1a\ncontent')
            fingerprint, tid, profile = discover.fingerprint(template), 'template-a', 'profile-a'
            (run/'step-06/template-profiles').mkdir(parents=True)
            (run/'step-06/template-profiles'/f'{profile}.json').write_text(json.dumps({'template_id':tid,'reference_path':'reference.png','reference_fingerprint':fingerprint,'profile_schema_version':'1.0','visual_analysis_status':'success','structural_characteristics':{},'design_characteristics':{},'content_capacity':{},'adaptability':{},'limitations':[],'uncertainties':[],'evidence':[]}))
            def write(name, value): (run/name).write_text(json.dumps(value))
            write('03-content-classification.json', {'step':'03-content-classification','version':'1.0','status':'success','run_id':'r','errors':[]})
            write('04-workflow-architecture.json', {'step':'04-workflow-architecture','version':'1.1','status':'success','run_id':'r','errors':[],'visual_units':[{'id':'u'}],'sections':[{'id':'s'}],'nodes':[{'id':'n'}],'connections':[{'id':'c','visual_representation_required':True}],'layout_requirements':[{'id':'l','level':'mandatory'}],'asset_requirements':[{'id':'a','required':True}]})
            write('05-content-writing.json', {'step':'05-content-writing','version':'1.0','status':'success','run_id':'r','errors':[],'content_items':[{'id':'i','required':True}]})
            sources = {key:{'step':step,'version':version,'run_id':'r'} for key,step,version in [('classification','03-content-classification','1.0'),('architecture','04-workflow-architecture','1.1'),('content_writing','05-content-writing','1.0')]}
            mappings = [{'target_type':kind,'target_id':item,'representation_strategy':'observed component'} for kind,item in [('section','s'),('node','n'),('connection','c'),('layout_requirement','l'),('asset_requirement','a'),('content_item','i')]]
            write('06-template-selection.json', {'step':'06-template-selection','version':'1.0','status':'success','run_id':'r','errors':[],'sources':sources,'template_library':{'discovered_templates':[{'id':tid,'reference_path':'reference.png','fingerprint':fingerprint}],'analyzed_templates':[{'template_id':tid,'profile_id':profile}]},'candidate_evaluations':[{'visual_unit_id':'u','template_id':tid,'assessment':'compatible','selection_eligible':True}],'template_selections':[{'visual_unit_id':'u','template_id':tid,'profile_id':profile,'reference_path':'reference.png','selection_rationale':'Fits'}],'content_template_mapping':mappings})
            self.assertEqual([], validator.validate(run, templates))

    def test_rejects_missing_required_mapping(self):
        with tempfile.TemporaryDirectory() as tmp:
            run, templates = Path(tmp), Path(tmp)/'templates'; templates.mkdir()
            for name,step,version in [('03-content-classification.json','03-content-classification','1.0'),('04-workflow-architecture.json','04-workflow-architecture','1.1'),('05-content-writing.json','05-content-writing','1.0')]:
                (run/name).write_text(json.dumps({'step':step,'version':version,'status':'success','run_id':'r','errors':[],'visual_units':[],'sections':[],'nodes':[],'connections':[],'layout_requirements':[],'asset_requirements':[],'content_items':[]}))
            (run/'04-workflow-architecture.json').write_text(json.dumps({'step':'04-workflow-architecture','version':'1.1','status':'success','run_id':'r','errors':[],'visual_units':[{'id':'u'}],'sections':[{'id':'s'}],'nodes':[],'connections':[],'layout_requirements':[],'asset_requirements':[]}))
            sources = {key:{'step':step,'version':version,'run_id':'r'} for key,step,version in [('classification','03-content-classification','1.0'),('architecture','04-workflow-architecture','1.1'),('content_writing','05-content-writing','1.0')]}
            (run/'06-template-selection.json').write_text(json.dumps({'step':'06-template-selection','version':'1.0','status':'success','run_id':'r','errors':[],'sources':sources,'template_library':{'discovered_templates':[],'analyzed_templates':[]},'candidate_evaluations':[],'template_selections':[],'content_template_mapping':[]}))
            self.assertTrue(validator.validate(run, templates))
