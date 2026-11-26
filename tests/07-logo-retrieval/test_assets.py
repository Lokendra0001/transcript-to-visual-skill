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

import json,sys,zlib
sys.path.insert(0,str(ROOT))
f=mod('free_logo_providers.py');e=mod('execute_step07.py')
def png(width,height):
 ihdr=width.to_bytes(4,'big')+height.to_bytes(4,'big')+b'\x08\x06\x00\x00\x00'
 return b'\x89PNG\r\n\x1a\n'+(13).to_bytes(4,'big')+b'IHDR'+ihdr+zlib.crc32(b'IHDR'+ihdr).to_bytes(4,'big')
SVG=b'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 10 10"><rect width="10" height="10"/></svg>'
class FakeLogoDev:
 def __init__(self,ok=True):self.calls=[];self.ok=ok
 def configured(self):return True
 def search(self,name):self.calls.append(('search',name));return {'ok':False,'state':'failed'}
 def brand(self,domain,kind):
  self.calls.append(('brand',domain))
  return {'ok':True,'data':{'data':{'domain':domain,'logo':{'url':'https://api.logo.dev/file/'+domain}}}} if self.ok else {'ok':False,'state':'insufficient_credits','http_status':402}
class LadderTests(unittest.TestCase):
 def setUp(self):
  self.dir=tempfile.TemporaryDirectory();self.t=Path(self.dir.name);self.files={};self.requested=[]
  registry=self.t/'registry.json';registry.write_text(json.dumps({'icons':[{'slug':'acme','title':'Acme','aliases':[],'url':'https://www.acme.com/','license':'CC0-1.0','variants':['default','mono']}]}))
  self.registry=f.TheSvgRegistry(registry)
  def fake_retrieve(url,destination,**_):
   self.requested.append(url);data=self.files.get(url)
   if data is None:return {'ok':False,'failure_category':'http_404','http_status':404}
   d=Path(destination).with_suffix('.svg' if data.startswith(b'<svg') else '.png');d.parent.mkdir(parents=True,exist_ok=True);d.write_bytes(data);return {'ok':True,'path':str(d)}
  self.original=e.retrieve;e.retrieve=fake_retrieve
 def tearDown(self):e.retrieve=self.original;self.dir.cleanup()
 def run_ladder(self,name,domain,logo_dev,hint_extra=None,taken=None):
  request={'id':'asset-request-1','entity_id':'ent','canonical_entity_name':name};attempts=[]
  for candidate in e.source_ladder(request,{'domain':domain,**(hint_extra or {})},logo_dev,attempts,self.registry):
   result=e.fetch_and_prepare(candidate,request['id'],{},self.t/'originals',self.t/'logos',taken or {})
   if result['outcome']=='selected':return candidate['provider'],attempts
  return None,attempts
 def test_domain_cleaning_and_slugs(self):
  self.assertEqual('clay.com',f.clean_domain('https://www.Clay.com/pricing'));self.assertIsNone(f.clean_domain('not a domain'))
  self.assertEqual(['frame-ai','frameai','frame'],f.slug_candidates('Frame AI','frame.ai'))
 def test_thesvg_matches_website_domain_before_name(self):
  self.assertEqual(['https://cdn.jsdelivr.net/gh/glincker/thesvg@main/public/icons/acme/default.svg'],self.registry.urls('Other Name','acme.com'))
  self.assertEqual('CC0-1.0',self.registry.licence('Acme',None))
 def test_hunter_first_and_logo_dev_untouched_when_free_source_succeeds(self):
  self.files['https://logos.hunter.io/acme.com']=png(256,256);logo_dev=FakeLogoDev()
  provider,_=self.run_ladder('Acme','acme.com',logo_dev);self.assertEqual('hunter',provider);self.assertEqual([],logo_dev.calls)
 def test_social_banner_is_rejected_and_ladder_continues(self):
  self.files['https://logos.hunter.io/acme.com']=png(1024,537)
  self.files['https://cdn.jsdelivr.net/gh/glincker/thesvg@main/public/icons/acme/default.svg']=SVG
  provider,_=self.run_ladder('Acme','acme.com',FakeLogoDev());self.assertEqual('thesvg',provider)
  self.assertIn('https://logos.lndev.me/logos/acme.svg',self.requested)
 def test_acquired_domain_duplicate_is_rejected(self):
  self.files['https://logos.hunter.io/acme.com']=png(256,256)
  first=e.fetch_and_prepare({'url':'https://logos.hunter.io/acme.com'},'asset-request-0',{},self.t/'originals',self.t/'logos',{})
  self.files['https://logos.hunter.io/oldacme.com']=png(256,256);self.files['https://api.logo.dev/file/oldacme.com']=SVG
  provider,_=self.run_ladder('Old Acme','oldacme.com',FakeLogoDev(),taken={first['verification']['fingerprint']:'asset-request-0'})
  self.assertEqual('logo_dev',provider)
 def test_logo_dev_is_last_and_uses_known_domain_without_search(self):
  self.files['https://api.logo.dev/file/clay.com']=SVG;logo_dev=FakeLogoDev()
  provider,_=self.run_ladder('Clay','clay.com',logo_dev);self.assertEqual('logo_dev',provider);self.assertEqual([('brand','clay.com')],logo_dev.calls)
  self.assertEqual(['https://logos.hunter.io/clay.com','https://logos.lndev.me/logos/clay.svg','https://api.logo.dev/file/clay.com'],self.requested)
 def test_logo_dev_error_leaves_request_for_generated_fallback(self):
  logo_dev=FakeLogoDev(ok=False);provider,attempts=self.run_ladder('Clay','clay.com',logo_dev)
  self.assertIsNone(provider);self.assertEqual('brand_lookup_failed',attempts[0]['outcome'])
 def test_reviewed_provider_rejection_skips_that_provider(self):
  self.files['https://logos.hunter.io/acme.com']=png(256,256);self.files['https://cdn.jsdelivr.net/gh/glincker/thesvg@main/public/icons/acme/default.svg']=SVG
  provider,_=self.run_ladder('Acme','acme.com',FakeLogoDev(),{'reject_providers':['hunter']});self.assertEqual('thesvg',provider)
  self.assertNotIn('https://logos.hunter.io/acme.com',self.requested)
 def test_avif_signature_is_recognised(self):
  data=b'\x00\x00\x00\x1cftypavif'+b'\x00'*20
  self.assertEqual('.avif',r.image_extension(data,'image/avif'))
  with tempfile.TemporaryDirectory() as t:
   p=Path(t)/'x.avif';p.write_bytes(data);self.assertTrue(v.verify(p)['valid'])
