import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
def load(name, path):
    spec = importlib.util.spec_from_file_location(name, ROOT / path)
    module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    return module

writing = load('writing_visual_first', 'scripts/05-content-writing/validate_content.py')
raster = load('raster_visual_first', 'scripts/08-visual-generation/raster_workflow.py')

class VisualFirst(unittest.TestCase):
    def docs(self, representation=None, required=True):
        arch = {'step':'04-workflow-architecture','version':'1.1','run_id':'synthetic',
                'content_requirements':[{'id':'r','required':required}], 'nodes':[{'id':'n'}]}
        item = {'id':'c','content_requirement_id':'r','target_refs':['n'],'required':required,
                'status':'generated','preferred_text':'Long approved wording',
                'length_metrics':writing.metrics('Long approved wording')}
        if representation is not None: item['representation'] = representation
        return arch, {'step':'05-content-writing','version':'1.0','run_id':'synthetic','content_items':[item]}

    def test_legacy_and_varied_semantic_representation(self):
        for kind, extra in [('text',{'visible_text':'Long approved wording'}),
                            ('concise_label',{'visible_text':'Label'}),
                            ('logo',{'asset_refs':['asset-1']}), ('icon',{'asset_refs':['icon-1']}),
                            ('relationship',{'relationship_refs':['edge-1']}), ('group',{'relationship_refs':['group-1']})]:
            with self.subTest(kind=kind):
                rep = {'type':kind,'meaning':'Approved meaning','reason':'Clear for this audience',**extra}
                arch, doc = self.docs(rep)
                self.assertEqual(writing.validate(arch,doc), [])
                brief = raster.generation_brief({'content_items':doc['content_items']})
                self.assertEqual(brief['requirements'][0]['representation'], rep)
                self.assertEqual(doc['content_items'][0]['preferred_text'], 'Long approved wording')
        arch, doc = self.docs()
        self.assertEqual(writing.validate(arch,doc), [])
        self.assertEqual(raster.generation_brief({'content_items':doc['content_items']})['requirements'][0]['representation']['visible_text'], 'Long approved wording')

    def test_no_required_context_and_missing_evidence_references(self):
        for rep in ({'type':'context_only','meaning':'essential','reason':'hidden'},
                    {'type':'icon','meaning':'essential','reason':'visual'},
                    {'type':'relationship','meaning':'essential','reason':'visual'},
                    {'type':'text','meaning':'essential','reason':'visible'}):
            arch, doc = self.docs(rep)
            self.assertTrue(writing.validate(arch,doc))
        with self.assertRaises(ValueError):
            raster.generation_brief({'content_items':[self.docs({'type':'context_only','meaning':'x','reason':'x'})[1]['content_items'][0]]})
        arch, doc = self.docs({'type':'context_only','meaning':'context','reason':'not needed'}, required=False)
        self.assertEqual(writing.validate(arch,doc), [])

    def test_varied_structures_and_repeated_asset_mappings_preserved(self):
        for pattern in ('text-heavy','branching','comparison','customer journey','hierarchy','tool-heavy','data-rich','minimal'):
            source = {'communication_objective':{'audience':'test','type':pattern},
                      'content_items':self.docs()[1]['content_items'],
                      'connections':[{'id':'edge','relationship_type':pattern}],
                      'asset_mappings':[{'asset_requirement_id':'one'},{'asset_requirement_id':'two'}],
                      'design_direction':[{'user_preference':'explicit'},{'reference':'different'}]}
            brief = raster.generation_brief(source)
            self.assertEqual(brief['relationships'], source['connections'])
            self.assertEqual(brief['asset_mappings'], source['asset_mappings'])
            self.assertEqual(brief['reference_direction'], source['design_direction'])
            self.assertIn('no image', brief['limitation'])

    def test_agent_direction_passes_through_actual_brief_cli(self):
        # Distinct directions are agent decisions, not palettes selected by code.
        directions = [
            {'palette': {'background': 'cream', 'accent': 'sage'}, 'source': 'explicit user',
             'background': 'localized halftone', 'logos': 'transparent, aligned',
             'connectors': 'branch and converge', 'animation': 'stable logos'},
            {'palette': {'background': 'black', 'accent': 'gold'}, 'source': 'brand guideline',
             'background': 'clean', 'logos': 'preserve intentional official surfaces',
             'connectors': 'feedback loop'},
        ]
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp); inventory = folder / 'inventory.json'; design = folder / 'design.json'
            inventory.write_text(json.dumps({'content_items':self.docs()[1]['content_items']}))
            for direction in directions:
                design.write_text(json.dumps(direction))
                result = subprocess.run([sys.executable, str(ROOT / 'scripts/08-visual-generation/raster_workflow.py'),
                                         'brief', '--inventory', str(inventory), '--design-system', str(design)],
                                        check=True, capture_output=True, text=True)
                brief = json.loads(result.stdout)
                self.assertEqual(brief['creative_direction'], direction)
                self.assertIn('no image', brief['limitation'])
        with self.assertRaises(ValueError):
            raster.generation_brief({}, ['invalid'])

if __name__ == '__main__': unittest.main()
