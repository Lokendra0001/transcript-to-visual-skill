import importlib.util
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location("validator", ROOT / "scripts/03-content-classification/validate_classification.py")
validator = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(validator)

def upstream():
    return {"step":"02-content-analysis","version":"2.0","status":"success","run_id":"run-1","topics":[{"id":"topic-1"}],"entities":[{"id":"entity-1"}],"facts":[],"activities":[{"id":"activity-1"}],"relationships":[],"decisions":[],"requirements":[],"ambiguities":[]}
def result():
    return {"step":"03-content-classification","version":"1.0","status":"success","run_id":"run-1","source":{"step":"02-content-analysis","version":"2.0","run_id":"run-1"},"classification":{"primary_type":"playbook","secondary_types":["workflow"]},"visual_scope":{"type":"single_visual","recommended_visual_count":1},"visual_units":[{"id":"unit-1","content_group_ids":["group-1"]}],"content_groups":[{"id":"group-1","topic_ids":["topic-1"],"entity_ids":["entity-1"],"fact_ids":[],"activity_ids":["activity-1"],"relationship_ids":[],"decision_ids":[],"requirement_ids":[]}],"coverage_assessment":{"represented_refs":["topic-1","entity-1","activity-1"],"supporting_context_refs":[],"constraint_refs":[],"excluded_refs":[],"unassigned_relevant_refs":[]}}
class Tests(unittest.TestCase):
    def test_valid(self): self.assertEqual([], validator.validate(upstream(), result()))
    def test_rejects_unknown_group_reference(self):
        item = result(); item["visual_units"][0]["content_group_ids"] = ["missing"]
        self.assertTrue(validator.validate(upstream(), item))
    def test_rejects_scope_count_mismatch(self):
        item = result(); item["visual_scope"]["recommended_visual_count"] = 2
        self.assertTrue(validator.validate(upstream(), item))
