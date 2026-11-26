import base64
import importlib.util
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2] / 'scripts/08-visual-generation/raster_workflow.py'
spec = importlib.util.spec_from_file_location('raster_workflow', ROOT)
workflow = importlib.util.module_from_spec(spec)
spec.loader.exec_module(workflow)
place_spec = importlib.util.spec_from_file_location('place_assets', ROOT.parent / 'place_assets.py')
placement = importlib.util.module_from_spec(place_spec); place_spec.loader.exec_module(placement)
PNG = base64.b64decode('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+/aWQAAAAASUVORK5CYII=')


def passing_review(path, content=(), assets=(), relationships=()):
    info = workflow.inspect_png(path)
    checks = {key: {'status': 'pass', 'evidence': 'inspected'} for key in workflow.CHECKS}
    return {'image_sha256': info['sha256'], 'dimensions': [info['width'], info['height']],
            'checks': checks,
            'content': [{'id': x, 'status': 'pass', 'evidence': 'visible'} for x in content],
            'assets': [{'id': x, 'status': 'pass', 'evidence': 'compared'} for x in assets],
            'relationships': [{'id': x, 'status': 'pass', 'evidence': 'direction inspected'} for x in relationships]}


class TestRasterWorkflow(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(); self.addCleanup(self.tmp.cleanup)
        self.png = Path(self.tmp.name) / 'image.png'; self.png.write_bytes(PNG)

    def test_varied_structures_preserved_without_inference(self):
        for pattern in ('sequence', 'branching', 'comparison', 'hierarchy', 'architecture', 'timeline', 'framework', 'composite', 'dense', 'minimal'):
            data = workflow.inventory({'classification': {'primary_type': pattern}}, {'nodes': [{'id':'n'}], 'connections': [{'id':'r','relationship_type':pattern}]}, {'content_items': [{'id':'c','preferred_text':'exact'}]}, {}, {})
            self.assertEqual(data['classification']['primary_type'], pattern)
            self.assertEqual(data['connections'][0]['relationship_type'], pattern)
            self.assertEqual(data['content_items'][0]['preferred_text'], 'exact')

    def test_evidence_gate_and_repeated_asset_occurrences(self):
        review = passing_review(self.png, ['c1'], ['occ1','occ2'], ['r1'])
        self.assertTrue(workflow.validate_review(self.png, review, ['c1'], ['occ1','occ2'], ['r1'])['valid'])
        review['assets'].append(review['assets'][0])
        self.assertFalse(workflow.validate_review(self.png, review, ['c1'], ['occ1','occ2'], ['r1'])['valid'])

    def test_unreviewed_missing_invented_and_failed_checks_fail(self):
        review = passing_review(self.png, ['c1'], [], ['r1'])
        for key in ('content_accuracy','relationship_accuracy','readability','reference_fit'):
            altered = passing_review(self.png, ['c1'], [], ['r1']); altered['checks'][key]['status'] = 'fail'
            self.assertFalse(workflow.validate_review(self.png, altered, ['c1'], [], ['r1'])['valid'])
        review['content'].append({'id':'invented','status':'pass','evidence':'visible'})
        self.assertFalse(workflow.validate_review(self.png, review, ['c1'], [], ['r1'])['valid'])
        self.assertFalse(workflow.validate_review(self.png, passing_review(self.png), ['missing'], [], [])['valid'])

    def test_wrong_hash_dimensions_and_bad_image_fail(self):
        review = passing_review(self.png); review['image_sha256'] = 'stale'
        self.assertFalse(workflow.validate_review(self.png, review)['valid'])
        review = passing_review(self.png); review['dimensions'] = [20,20]
        self.assertFalse(workflow.validate_review(self.png, review)['valid'])
        self.png.write_bytes(b'not a png')
        self.assertFalse(workflow.validate_review(self.png, review)['valid'])

    def test_reference_record_requires_attachment_and_matching_hash(self):
        import hashlib
        record = {'reference_sha256': hashlib.sha256(self.png.read_bytes()).hexdigest(),
                  'attached_to_generation': True, 'tool': 'image tool',
                  'call_evidence': 'reference included in recorded call'}
        self.assertTrue(workflow.validate_reference_input(self.png, record)['valid'])
        for field, invalid in [('reference_sha256', 'stale'), ('attached_to_generation', False),
                               ('tool', ''), ('call_evidence', '')]:
            broken = dict(record, **{field: invalid})
            self.assertFalse(workflow.validate_reference_input(self.png, broken)['valid'])
        self.assertFalse(workflow.validate_reference_input(self.png.parent / 'missing.png', record)['valid'])

    def test_no_asset_or_relationship_checks_can_be_not_applicable(self):
        review = passing_review(self.png)
        for key in ('asset_identity','asset_placement','relationship_accuracy'):
            review['checks'][key] = {'status':'not_applicable','evidence':'none required'}
        self.assertTrue(workflow.validate_review(self.png, review)['valid'])
        self.assertFalse(workflow.validate_review(self.png, review, required_assets=['a'])['valid'])

    def test_real_asset_placement_preserves_master_and_checks_hash(self):
        try:
            from PIL import Image
        except ImportError:
            self.skipTest('Pillow unavailable')
        folder = Path(self.tmp.name); master = folder/'master.png'; asset = folder/'mark.png'; out = folder/'out.png'
        Image.new('RGBA', (40,40), 'white').save(master)
        Image.new('RGBA', (6,3), 'red').save(asset)
        before = placement.sha(master)
        entry = {'occurrence_id':'one', 'source':'mark.png', 'sha256':placement.sha(asset), 'bounds':[10,10,12,12]}
        result = placement.place(master, folder, [entry], out)
        self.assertEqual(placement.sha(master), before)
        self.assertEqual(result['placements'][0]['actual_bounds'], [10,13,12,6])
        with Image.open(out) as image:
            self.assertEqual(image.getpixel((11,14))[:3], (255,0,0))
        entry['sha256'] = 'wrong'
        with self.assertRaises(ValueError): placement.place(master, folder, [entry], folder/'bad.png')
        entry['sha256'] = placement.sha(asset)
        with self.assertRaises(ValueError): placement.place(master, folder, [entry,entry], folder/'dup.png')
        overlap = dict(entry, occurrence_id='two', bounds=[11,11,12,12])
        with self.assertRaises(ValueError): placement.place(master, folder, [entry,overlap], folder/'overlap.png')
        with self.assertRaises(ValueError): placement.place(master, folder, [entry], master)


if __name__ == '__main__': unittest.main()
