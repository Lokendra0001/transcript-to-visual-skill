import json
import base64
import os
import shutil
import subprocess
import tempfile
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RENDERER = ROOT / 'scripts/08-visual-generation/renderer'
FIXTURE = Path(__file__).parent / 'fixtures/render-smoke'
CHROME = os.environ.get('CHROME_PATH', '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome')


@unittest.skipUnless((RENDERER / 'node_modules').is_dir() and shutil.which('node') and Path(CHROME).exists(),
                     'renderer dependencies, node or Chrome unavailable')
class RendererTest(unittest.TestCase):
    def render(self, mutate=None):
        tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, tmp, True)
        run = tmp / 'run'
        shutil.copytree(FIXTURE, run)
        if mutate:
            mutate(run / 'step-08/src')
        proc = subprocess.run(['node', str(RENDERER / 'render.mjs'), '--run-dir', str(run)],
                              capture_output=True, text=True, timeout=180)
        report = json.loads((run / 'step-08/render-report.json').read_text())
        return proc.returncode, report, run

    def test_renders_svg_png_and_checks_motion(self):
        code, report, run = self.render()
        self.assertEqual(code, 0, report['errors'])
        self.assertEqual(report['status'], 'rendered')
        self.assertEqual(report['outputs']['png']['dimensions'], [1280, 520])
        self.assertEqual({n['id'] for n in report['nodes']}, {'node-1', 'node-2'})
        self.assertEqual([c['id'] for c in report['connections']], ['conn-1'])
        self.assertEqual({a['id'] for a in report['assets']}, {'ar-1', 'ar-2'})
        self.assertTrue(all(f['ok'] for f in report['text_fit']))
        self.assertTrue(report['motion']['final_frame_matches_static'])
        svg = (run / 'step-08/infographic.svg').read_text()
        self.assertIn('<tspan', svg)
        self.assertIn('href="data:image/png;base64,', svg)
        self.assertNotIn('foreignObject', svg)

    def test_reports_overflow_and_motion_that_changes_master(self):
        def mutate(src):
            comp = src / 'Infographic.tsx'
            comp.write_text(comp.read_text().replace('width={240} height={140}', 'width={120} height={140}'))
            (src / 'motion.ts').write_text(
                "export function buildTimeline(svg: SVGSVGElement, gsap: any) {\n"
                "  return gsap.timeline().to(svg.querySelector('#node-1'), { opacity: 0.5, duration: 0.2 });\n}\n")
        code, report, _ = self.render(mutate)
        self.assertEqual(code, 2)
        self.assertTrue(any('text overflows' in e for e in report['errors']))
        self.assertTrue(any('final frame differs' in e for e in report['errors']))

    def test_default_footer_embeds_exact_t01_crop(self):
        def mutate(src):
            (src / 'motion.ts').unlink()
            (src / 'Infographic.tsx').write_text('''import React from "react";
import { Footer, footerHeight } from "@kit";
export default function Infographic() {
  const width = 1398, y = 30;
  return <svg id="infographic" xmlns="http://www.w3.org/2000/svg" width={width} height={y + footerHeight(width)} viewBox={`0 0 ${width} ${y + footerHeight(width)}`}><rect width={width} height={y} fill="white"/><Footer width={width} y={y}/></svg>;
}''')
        code, report, run = self.render(mutate)
        self.assertEqual(code, 0, report['errors'])
        root=ET.parse(run / 'step-08/infographic.svg').getroot()
        footer=next(e for e in root.iter() if e.get('id')=='footer')
        self.assertEqual(footer.get('y'),'30')
        self.assertEqual(footer.get('height'),'117')
        uri=footer.get('href')
        self.assertTrue(uri.startswith('data:image/png;base64,'))
        self.assertEqual(base64.b64decode(uri.split(',',1)[1]), (ROOT/'references/assets/t01-footer.png').read_bytes())

    def test_footer_custom_content_is_editable(self):
        def mutate(src):
            (src / 'motion.ts').unlink()
            (src / 'Infographic.tsx').write_text('''import React from "react";
import { Footer, footerHeight } from "@kit";
import mark from "../../assets/mark.png";
export default function Infographic() {
  const width = 1398;
  return <svg id="infographic" xmlns="http://www.w3.org/2000/svg" width={width} height={footerHeight(width)} viewBox={`0 0 ${width} ${footerHeight(width)}`}><Footer width={width} y={0} content={{name:"New Name",portraitHref:mark,brandHref:mark,brandLabel:"New Brand"}}/></svg>;
}''')
        code, report, run = self.render(mutate)
        self.assertEqual(code, 0, report['errors'])
        svg=(run / 'step-08/infographic.svg').read_text()
        self.assertIn('New Name',svg)
        self.assertIn('New Brand',svg)

    def test_footer_name_only_retains_reference_artwork(self):
        def mutate(src):
            (src / 'motion.ts').unlink()
            (src / 'Infographic.tsx').write_text('''import React from "react";
import { Footer, footerHeight } from "@kit";
export default function Infographic() {
  const width = 1398;
  return <svg id="infographic" xmlns="http://www.w3.org/2000/svg" width={width} height={footerHeight(width)} viewBox={`0 0 ${width} ${footerHeight(width)}`}><Footer width={width} y={0} content={{name:"New Name"}}/></svg>;
}''')
        code, report, run = self.render(mutate)
        self.assertEqual(code, 0, report['errors'])
        root=ET.parse(run / 'step-08/infographic.svg').getroot()
        footer=next(e for e in root.iter() if e.get('id')=='footer')
        image=next(e for e in footer.iter() if e.tag.endswith('image'))
        self.assertEqual(base64.b64decode(image.get('href').split(',',1)[1]), (ROOT/'references/assets/t01-footer.png').read_bytes())
        self.assertTrue(any(e.tag.endswith('text') and e.text=='New Name' for e in footer.iter()))


if __name__ == '__main__':
    unittest.main()
