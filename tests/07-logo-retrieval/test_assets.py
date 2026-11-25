import importlib.util,tempfile,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]/'scripts/07-logo-retrieval'
def mod(n):
 s=importlib.util.spec_from_file_location(n,ROOT/n);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
d=mod('discover_assets.py');v=mod('verify_assets.py');r=mod('retrieve_assets.py');l=mod('logo_dev.py');g=mod('generate_fallback.py')
class Tests(unittest.TestCase):
 def test_deduplicates_occurrences_but_not_distinct_entities(self):
  a={'asset_requirements':[{'id':'a','entity_id':'one','asset_type':'brand_logo','target_id':'n1'},{'id':'b','entity_id':'one','asset_type':'brand_logo','target_id':'n2'},{'id':'c','entity_id':'two','asset_type':'brand_logo','target_id':'n3'}]};x=d.discover(a,{'terminology_registry':[]});self.assertEqual(2,len(x['unique_asset_requests']));self.assertEqual(3,len(x['asset_mappings']))
 def test_rejects_active_svg(self):
  with tempfile.TemporaryDirectory() as t:
   p=Path(t)/'bad.svg';p.write_text('<svg><script>x</script></svg>');self.assertFalse(v.verify(p)['valid'])
 def test_accepts_standard_svg_namespace_and_internal_defs(self):
  with tempfile.TemporaryDirectory() as t:
   p=Path(t)/'safe.svg';p.write_text('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 40 20"><defs><linearGradient id="g"/></defs><path fill="url(#g)"/></svg>');x=v.verify(p);self.assertTrue(x['valid']);self.assertEqual(2.0,x['aspect_ratio'])
 def test_rejects_external_svg_reference(self):
  with tempfile.TemporaryDirectory() as t:
   p=Path(t)/'bad.svg';p.write_text('<svg xmlns="http://www.w3.org/2000/svg"><image href="https://x/a"/></svg>');self.assertFalse(v.verify(p)['valid'])
 def test_blocks_private_downloads(self):self.assertFalse(r.retrieve('http://127.0.0.1/a','/tmp/nope')['ok'])
 def test_detects_extension_from_bytes_not_url(self):
  self.assertEqual('.svg',r.image_extension(b'<svg xmlns="http://www.w3.org/2000/svg"/>','image/svg+xml'))
  self.assertEqual('.png',r.image_extension(b'\x89PNG\r\n\x1a\nbytes','text/html'))
 def test_logo_dev_uses_documented_v2_parameters(self):
  captured=[]
  class Response:
   status=200
   def read(self):return b'{"data":[]}'
   def __enter__(self):return self
   def __exit__(self,*args):return False
  def transport(request,timeout):captured.append(request.full_url);return Response()
  client=l.LogoDev(key='sk_test',transport=transport);client.search('Slack');client.brand('slack.com','domain')
  self.assertIn('q=Slack',captured[0]);self.assertNotIn('query=',captured[0]);self.assertIn('domain=slack.com',captured[1]);self.assertNotIn('identifier=',captured[1])
 def test_generated_fallback_is_a_valid_non_official_svg(self):
  with tempfile.TemporaryDirectory() as t:
   result=g.create(Path(t)/'fallback.svg','Unknown Tool')
   self.assertEqual('generated_visual_fallback',result['representation_type'])
   self.assertTrue(v.verify(result['path'])['valid'])
