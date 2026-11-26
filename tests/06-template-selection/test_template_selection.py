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
            (run/'step-06/template-profiles'/f'{profile}.json').write_text(json.dumps({'template_id':tid,'reference_path':'reference.png','reference_fingerprint':fingerprint,'profile_schema_version':'1.1','visual_analysis_status':'success','structural_characteristics':{},'design_characteristics':{},'content_capacity':{},'adaptability':{},'limitations':[],'uncertainties':[],'evidence':[],'suited_content_structures':['comparison'],'unsuited_content_structures':['branching decisions']}))
            def write(name, value): (run/name).write_text(json.dumps(value))
            write('03-content-classification.json', {'step':'03-content-classification','version':'1.0','status':'success','run_id':'r','errors':[]})
            write('04-workflow-architecture.json', {'step':'04-workflow-architecture','version':'1.1','status':'success','run_id':'r','errors':[],'visual_units':[{'id':'u'}],'sections':[{'id':'s'}],'nodes':[{'id':'n'}],'connections':[{'id':'c','visual_representation_required':True}],'layout_requirements':[{'id':'l','level':'mandatory'}],'asset_requirements':[{'id':'a','required':True}]})
            write('05-content-writing.json', {'step':'05-content-writing','version':'1.0','status':'success','run_id':'r','errors':[],'content_items':[{'id':'i','required':True}]})
            sources = {key:{'step':step,'version':version,'run_id':'r'} for key,step,version in [('classification','03-content-classification','1.0'),('architecture','04-workflow-architecture','1.1'),('content_writing','05-content-writing','1.0')]}
            mappings = [{'target_type':kind,'target_id':item,'representation_strategy':'observed component'} for kind,item in [('section','s'),('node','n'),('connection','c'),('layout_requirement','l'),('asset_requirement','a'),('content_item','i')]]
            write('06-template-selection.json', {'step':'06-template-selection','version':'1.0','status':'success','run_id':'r','errors':[],'sources':sources,'template_library':{'discovered_templates':[{'id':tid,'reference_path':'reference.png','fingerprint':fingerprint}],'analyzed_templates':[{'template_id':tid,'profile_id':profile}]},'candidate_evaluations':[{'visual_unit_id':'u','template_id':tid,'assessment':'compatible','selection_eligible':True,'reasons':['Two-column layout fits the comparison']}],'template_selections':[{'visual_unit_id':'u','template_id':tid,'profile_id':profile,'reference_path':'reference.png','selection_rationale':'Fits','content_fit':'comparison -> two columns'}],'content_template_mapping':mappings})
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


def build_run(tmp, assessments, selected, schema='1.1', reasons=True, override=None):
    """Valid two-unit-free run with one visual unit and one template per entry in `assessments`."""
    run, templates = Path(tmp)/'run', Path(tmp)/'templates'; run.mkdir(); templates.mkdir()
    (run/'step-06/template-profiles').mkdir(parents=True)
    discovered, analyzed, evaluations = [], [], []
    for index, (tid, assessment) in enumerate(assessments.items()):
        path = templates/f'{tid}.png'; path.write_bytes(b'\x89PNG\r\n\x1a\n' + tid.encode() + bytes([index]))
        fingerprint = discover.fingerprint(path)
        (run/'step-06/template-profiles'/f'{tid}.json').write_text(json.dumps({'template_id':tid,'reference_path':path.name,'reference_fingerprint':fingerprint,'profile_schema_version':schema,'visual_analysis_status':'success','structural_characteristics':{},'design_characteristics':{},'content_capacity':{},'adaptability':{},'limitations':[],'uncertainties':[],'evidence':[],'suited_content_structures':['comparison'],'unsuited_content_structures':['branching decisions']}))
        discovered.append({'id':tid,'reference_path':path.name,'fingerprint':fingerprint}); analyzed.append({'template_id':tid,'profile_id':tid})
        evaluations.append({'visual_unit_id':'u','template_id':tid,'assessment':assessment,'selection_eligible':True,'reasons':['observed fit'] if reasons else []})
    def write(name, value): (run/name).write_text(json.dumps(value))
    write('03-content-classification.json', {'step':'03-content-classification','version':'1.0','status':'success','run_id':'r','errors':[]})
    write('04-workflow-architecture.json', {'step':'04-workflow-architecture','version':'1.1','status':'success','run_id':'r','errors':[],'visual_units':[{'id':'u'}],'sections':[],'nodes':[],'connections':[],'layout_requirements':[],'asset_requirements':[]})
    write('05-content-writing.json', {'step':'05-content-writing','version':'1.0','status':'success','run_id':'r','errors':[],'content_items':[]})
    sources = {key:{'step':step,'version':version,'run_id':'r'} for key,step,version in [('classification','03-content-classification','1.0'),('architecture','04-workflow-architecture','1.1'),('content_writing','05-content-writing','1.0')]}
    selection = {'visual_unit_id':'u','template_id':selected,'profile_id':selected,'reference_path':f'{selected}.png','selection_rationale':'Fits','content_fit':'comparison'}
    if override: selection['override_reason'] = override
    write('06-template-selection.json', {'step':'06-template-selection','version':'1.0','status':'warning','run_id':'r','errors':[],'sources':sources,'template_library':{'discovered_templates':discovered,'analyzed_templates':analyzed},'candidate_evaluations':evaluations,'template_selections':[selection],'content_template_mapping':[]})
    return run, templates


class ContentFitSelectionTests(unittest.TestCase):
    def test_best_ranked_selection_passes(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.assertEqual([], validator.validate(*build_run(tmp, {'t01':'compatible','t08':'highly_compatible'}, 't08')))

    def test_lower_ranked_selection_needs_override(self):
        with tempfile.TemporaryDirectory() as tmp:
            errors = validator.validate(*build_run(tmp, {'t01':'compatible','t08':'highly_compatible'}, 't01'))
            self.assertTrue(any('below eligible alternative' in e for e in errors))
        with tempfile.TemporaryDirectory() as tmp:
            self.assertEqual([], validator.validate(*build_run(tmp, {'t01':'compatible','t08':'highly_compatible'}, 't01', override='User explicitly requested T01')))

    def test_schema_1_0_profiles_are_stale(self):
        with tempfile.TemporaryDirectory() as tmp:
            errors = validator.validate(*build_run(tmp, {'t08':'highly_compatible'}, 't08', schema='1.0'))
            self.assertTrue(any('stale or incomplete profile' in e for e in errors))

    def test_evaluations_need_reasons(self):
        with tempfile.TemporaryDirectory() as tmp:
            errors = validator.validate(*build_run(tmp, {'t08':'highly_compatible'}, 't08', reasons=False))
            self.assertTrue(any('without reasons' in e for e in errors))
