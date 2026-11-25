import importlib.util,unittest
from pathlib import Path
root=Path(__file__).resolve().parents[2]
spec=importlib.util.spec_from_file_location('v',root/'scripts/04-workflow-architecture/validate_architecture.py');v=importlib.util.module_from_spec(spec);spec.loader.exec_module(v)
def upstream(step):return {'step':step,'run_id':'run'}
def output():return {'step':'04-workflow-architecture','version':'1.1','run_id':'run','visual_units':[{'id':'unit'}],'sections':[{'id':'root','visual_unit_id':'unit','parent_section_id':None},{'id':'child','visual_unit_id':'unit','parent_section_id':'root'}],'nodes':[{'id':'a','visual_unit_id':'unit','section_id':'root'},{'id':'b','visual_unit_id':'unit','section_id':'child'}],'connections':[{'id':'connection-1','source_node_id':'a','target_node_id':'b','relationship_type':'information_flow','representation_mode':'flexible','visual_representation_required':True}],'content_requirements':[{'target_scope':'node','target_id':'a','required':True,'priority':'primary','semantic_purpose':'stage label'}],'asset_requirements':[],'coverage_assessment':{'unrepresented_required_refs':[],'unrepresented_required_associations':[]}}
class Tests(unittest.TestCase):
 def test_valid(self):self.assertEqual([],v.validate(upstream('02-content-analysis'),upstream('03-content-classification'),output()))
 def test_cycle(self):
  x=output();x['sections'][0]['parent_section_id']='child';self.assertTrue(v.validate(upstream('02-content-analysis'),upstream('03-content-classification'),x))
 def test_invalid_content_target(self):
  x=output();x['content_requirements'][0]['target_id']='missing';self.assertTrue(v.validate(upstream('02-content-analysis'),upstream('03-content-classification'),x))
