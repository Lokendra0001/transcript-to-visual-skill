import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / 'scripts/08-visual-generation'
RENDERER = SCRIPTS / 'renderer'
FIXTURE = Path(__file__).parent / 'fixtures/render-effects'
CHROME = os.environ.get('CHROME_PATH', '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome')
sys.path.insert(0, str(SCRIPTS))
import rendering_plan  # noqa: E402


class SelectionTest(unittest.TestCase):
    def test_simplest_capable_technology_wins(self):
        self.assertEqual(rendering_plan.select(['soft_shadow', 'gradients', 'glassmorphism'])['technology'], 'svg')
        self.assertEqual(rendering_plan.select(['extruded_blocks'])['technology'], 'svg')
        self.assertEqual(rendering_plan.select(['isometric_illustration', 'gradients'])['technology'], 'zdog')
        self.assertEqual(rendering_plan.select(['path_construction'])['technology'], 'svgjs')
        self.assertEqual(rendering_plan.select(['realistic_3d', 'soft_shadow'])['technology'], 'three')
        self.assertEqual(rendering_plan.select(['structured_component'])['technology'], 'antv')

    def test_incompatible_traits_must_be_split(self):
        with self.assertRaisesRegex(ValueError, 'split the component'):
            rendering_plan.select(['realistic_3d', 'structured_component'])
        with self.assertRaisesRegex(ValueError, 'unknown traits'):
            rendering_plan.select(['sparkles'])


@unittest.skipUnless((RENDERER / 'node_modules').is_dir() and shutil.which('node') and Path(CHROME).exists(),
                     'renderer dependencies, node or Chrome unavailable')
class EngineRenderTest(unittest.TestCase):
    def render(self, mutate=None, plan=None):
        tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, tmp, True)
        run = tmp / 'run'
        shutil.copytree(FIXTURE, run)
        if mutate:
            comp = run / 'step-08/src/Infographic.tsx'
            comp.write_text(mutate(comp.read_text()))
        if plan:
            bp = run / 'step-08/reference-blueprint.json'
            data = json.loads(bp.read_text())
            data['rendering_plan'] = plan(data['rendering_plan'])
            bp.write_text(json.dumps(data))
        proc = subprocess.run(['node', str(RENDERER / 'render.mjs'), '--run-dir', str(run), '--scale', '2'],
                              capture_output=True, text=True, timeout=240)
        return proc.returncode, json.loads((run / 'step-08/render-report.json').read_text()), run

    def test_every_technology_renders_natively_and_matches_the_plan(self):
        code, report, run = self.render()
        self.assertEqual(code, 0, report['errors'])
        self.assertEqual({l['technology'] for l in report['render_layers']}, {'svgjs', 'zdog', 'three', 'antv'})
        raster = [i for i in report['images'] if i['kind'] == 'raster']
        self.assertEqual([(i['element_id'], i['technology']) for i in raster], [('hero-3d', 'three')])
        self.assertGreaterEqual(raster[0]['density'], 2)
        self.assertGreater(report['effects']['filters'], 5)
        svg = (run / 'step-08/infographic.svg').read_text()
        self.assertNotIn('foreignObject', svg)              # AntV text converted to native <text>
        self.assertIn('>Capture</text>', svg)
        self.assertNotIn('svgjs:data', svg)
        self.assertIn('id="servers-', svg)                   # library ids are scoped under the layer id
        self.assertIn('blocked', report['environment']['network'])
        self.assertEqual(rendering_plan.check(run)['errors'], [])

    def test_effects_that_alter_logos_and_broken_references_fail(self):
        def mutate(src):
            src = src.replace('<g id="node-logo" data-node="node-logo" filter="url(#fx-soft)">',
                              '<g id="node-logo" data-node="node-logo" filter="url(#kit-bevel)">')
            return src.replace('fill="url(#p-dots)"', 'fill="url(#p-missing)"')
        code, report, _ = self.render(mutate)
        self.assertEqual(code, 2)
        self.assertTrue(any('alters brand logo ar-mark' in e for e in report['errors']), report['errors'])
        self.assertTrue(any('unresolved reference url(#p-missing)' in e for e in report['errors']), report['errors'])

    def test_low_resolution_raster_fails(self):
        code, report, _ = self.render(lambda s: s.replace(
            '<Label id="logo-label"',
            '<image id="bad-raster" data-raster="three" href={mark} x={20} y={20} width={300} height={300} />\n      <Label id="logo-label"'))
        self.assertEqual(code, 2)
        self.assertTrue(any('raster bad-raster' in e and 'below the 2x' in e for e in report['errors']), report['errors'])

    def test_plan_must_match_rendered_layers(self):
        _, _, run = self.render(plan=lambda p: [c for c in p if c['technology'] != 'three']
                                + [{'component': 'Extra', 'traits': ['soft_shadow'], 'technology': 'zdog'}])
        errors = rendering_plan.check(run)['errors']
        self.assertTrue(any('three layers rendered but not in rendering_plan' in e for e in errors), errors)
        self.assertTrue(any('heavier than the selected svg' in e for e in errors), errors)


if __name__ == '__main__':
    unittest.main()
