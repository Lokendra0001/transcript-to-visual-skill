"""Deterministic contract tests; Claude semantic judgment is covered separately."""

import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts" / "02-content-analysis" / "validate_analysis.py"
STEP01_SCRIPT = ROOT / "scripts" / "01-input-processing" / "process_input.py"
SPEC = importlib.util.spec_from_file_location("validate_analysis", SCRIPT)
validator = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
SPEC.loader.exec_module(validator)


def step01(status="success"):
    return {
        "step": "01-input-processing", "status": status,
        "metadata": {"input_type": "transcript", "input_source": "granola"},
        "segments": [{"id": "segment-001"}, {"id": "segment-002"}],
    }


def analysis():
    result = {
        "step": "02-content-analysis", "version": "2.0", "status": "success", "run_id": "test-run",
        "source": {"step": "01-input-processing", "input_type": "transcript", "input_source": "granola"},
        "context": {"primary_subject": "CRM handoff", "source_segment_ids": ["segment-001"]},
        "topics": [{"id": "topic-001", "entity_ids": ["entity-001"], "fact_ids": ["fact-001"], "activity_ids": ["activity-001"], "source_segment_ids": ["segment-001"]}],
        "entities": [{"id": "entity-001", "topic_ids": ["topic-001"], "source_segment_ids": ["segment-001"]}],
        "facts": [{"id": "fact-001", "entity_ids": ["entity-001"], "topic_ids": ["topic-001"], "source_segment_ids": ["segment-001"]}],
        "activities": [{"id": "activity-001", "topic_ids": ["topic-001"], "actor_entity_ids": [], "entity_associations": [{"entity_id": "entity-001", "role": "CRM", "usage_status": "existing", "source_segment_ids": ["segment-002"]}], "input_refs": [], "output_refs": [], "dependency_refs": [], "source_segment_ids": ["segment-002"]}],
        "relationships": [{"id": "relationship-001", "source_ref": "entity-001", "target_ref": "activity-001", "relationship_type": "uses", "source_segment_ids": ["segment-002"]}],
        "decisions": [{"id": "decision-001", "related_entity_ids": ["entity-001"], "supersedes_ids": [], "source_segment_ids": ["segment-002"]}],
        "requirements": [], "ambiguities": [],
        "relevance_assessment": [{"id": "relevance-001", "classification": "core", "source_segment_ids": ["segment-001", "segment-002"]}],
        "excluded_content": [], "coverage": {"reviewed_segment_ids": ["segment-001", "segment-002"], "unrepresented_details": []}, "warnings": [], "errors": [],
    }
    return result


class ValidateAnalysisTests(unittest.TestCase):
    def test_valid_analysis_contract(self):
        self.assertEqual([], validator.validate_step01(step01()))
        self.assertEqual([], validator.validate_analysis(analysis(), step01()))

    def test_rejects_failed_step01(self):
        self.assertIn("Step 01 must have status 'success' before analysis.", validator.validate_step01(step01("failed")))

    def test_rejects_unknown_segment_reference(self):
        candidate = analysis()
        candidate["facts"][0]["source_segment_ids"] = ["segment-404"]
        self.assertTrue(any("unknown Step 01 segment" in error for error in validator.validate_analysis(candidate, step01())))

    def test_rejects_duplicate_ids_and_invalid_relationship_endpoint(self):
        candidate = analysis()
        candidate["facts"][0]["id"] = "entity-001"
        candidate["relationships"][0]["target_ref"] = "entity-404"
        errors = validator.validate_analysis(candidate, step01())
        self.assertTrue(any("Duplicate extracted ID" in error for error in errors))
        self.assertTrue(any("must reference an entity or activity ID" in error for error in errors))

    def test_rejects_inconsistent_exclusions_and_incomplete_relevance(self):
        candidate = analysis()
        candidate["relevance_assessment"][0]["classification"] = "irrelevant"
        self.assertTrue(any("excluded_content must match" in error for error in validator.validate_analysis(candidate, step01())))
        candidate = analysis()
        candidate["relevance_assessment"][0]["source_segment_ids"] = ["segment-001"]
        self.assertTrue(any("relevance_assessment must cover" in error for error in validator.validate_analysis(candidate, step01())))

    def test_rejects_unknown_contextual_entity_association(self):
        candidate = analysis()
        candidate["activities"][0]["entity_associations"][0]["entity_id"] = "entity-404"
        self.assertTrue(any("entity_associations contains an unknown entity" in error for error in validator.validate_analysis(candidate, step01())))

    def test_cli_reads_sibling_run_artifacts(self):
        with tempfile.TemporaryDirectory() as directory:
            run_dir = Path(directory)
            generated = subprocess.run([
                sys.executable, str(STEP01_SCRIPT),
                "--text", "Maya: Acme uses HubSpot.\nDev: Salesforce is the system of record.",
                "--source", "granola", "--run-dir", str(run_dir),
            ], capture_output=True, text=True, check=False)
            self.assertEqual(0, generated.returncode, generated.stderr)
            (run_dir / "02-content-analysis.json").write_text(json.dumps(analysis()), encoding="utf-8")
            phase_dir = run_dir / "step-02"
            phase_dir.mkdir()
            for filename in validator.PHASE_FILES:
                (phase_dir / filename).write_text(json.dumps({"run_id": "test-run", "status": "success"}), encoding="utf-8")
            self.assertEqual(0, validator.main(["--run-dir", str(run_dir)]))


if __name__ == "__main__":
    unittest.main()
