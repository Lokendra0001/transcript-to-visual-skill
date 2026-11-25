import importlib.util,unittest
from pathlib import Path
p=Path(__file__).resolve().parents[2]/'scripts/05-content-writing/validate_content.py';s=importlib.util.spec_from_file_location('v',p);v=importlib.util.module_from_spec(s);s.loader.exec_module(v)
def architecture():return {'step':'04-workflow-architecture','version':'1.1','run_id':'r','content_requirements':[{'id':'req','required':True}],'visual_units':[{'id':'unit'}],'sections':[],'nodes':[{'id':'node'}],'connections':[]}
def result():return {'step':'05-content-writing','version':'1.0','run_id':'r','content_items':[{'content_requirement_id':'req','target_refs':['node'],'status':'generated','preferred_text':'Hello world','length_metrics':{'words':2,'characters':11}}]}
class Tests(unittest.TestCase):
 def test_valid(self):self.assertEqual([],v.validate(architecture(),result()))
 def test_required_missing(self):x=result();x['content_items']=[];self.assertTrue(v.validate(architecture(),x))
