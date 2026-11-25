"""Automated deterministic tests for Step 01 only.

Reasoning-dependent language identification and unusual-layout judgment are
documented acceptance checks; they are not asserted as automated NLP behavior.
"""

import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts" / "01-input-processing" / "process_input.py"
FIXTURES = Path(__file__).parent / "fixtures"
SPEC = importlib.util.spec_from_file_location("process_input", SCRIPT)
processor = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
SPEC.loader.exec_module(processor)


class ProcessInputTests(unittest.TestCase):
    def fixture(self, name):
        return (FIXTURES / name).read_text(encoding="utf-8")

    def test_granola_turns_are_ordered_and_source_is_verbatim(self):
        source = self.fixture("01-granola-transcript.txt")
        result = processor.process_text(source, input_source="granola")
        self.assertEqual("success", result["status"])
        self.assertEqual(source, result["original_text"])
        self.assertEqual("transcript", result["metadata"]["input_type"])
        self.assertEqual([1, 2, 3], [segment["sequence"] for segment in result["segments"]])
        self.assertEqual(["Alice", "Bob", "Alice"], [segment["speaker"] for segment in result["segments"]])
        self.assertEqual(3, result["segments"][-1]["source_location"]["end_line"])

    def test_markdown_bold_speaker_labels_are_turns(self):
        source = "# Transcript\n\n**Speaker 1:** Hello there.\n\n**Alice**: Hi.\n\n- **Note:** a list item stays content\n"
        result = processor.process_text(source)
        self.assertTrue(result["metadata"]["has_speakers"])
        self.assertEqual([s["speaker"] for s in result["segments"]], ["Speaker 1", "Alice"])
        self.assertEqual(result["segments"][0]["original_text"], "Hello there.")
        self.assertIn("- **Note:** a list item", result["segments"][1]["original_text"])

    def test_timestamps_are_preserved_and_normalized(self):
        result = processor.process_text(self.fixture("02-timestamped-transcript.txt"))
        self.assertTrue(result["metadata"]["has_timestamps"])
        self.assertEqual(["00:05", "01:12"], [segment["timestamp"] for segment in result["segments"]])

    def test_unlabeled_transcript_uses_null_metadata(self):
        result = processor.process_text(self.fixture("03-no-speakers.txt"))
        self.assertFalse(result["metadata"]["has_speakers"])
        self.assertTrue(all(segment["speaker"] is None for segment in result["segments"]))

    def test_normalization_is_limited_to_whitespace(self):
        source = self.fixture("04-inconsistent-formatting.txt")
        result = processor.process_text(source)
        self.assertEqual(source, result["original_text"])
        self.assertIn("Priya:   Keep the customer quote exactly.", result["normalized_text"])
        self.assertNotIn("\n\n\n", result["normalized_text"])

    def test_names_and_technical_terms_are_not_changed(self):
        source = self.fixture("05-company-technical.txt")
        result = processor.process_text(source)
        self.assertIn("AcmeCloud", result["normalized_text"])
        self.assertIn("OAuth 2.0", result["normalized_text"])

    def test_mixed_language_text_is_preserved_without_language_fabrication(self):
        source = self.fixture("06-multilingual.txt")
        result = processor.process_text(source)
        self.assertEqual(source, result["original_text"])
        self.assertIsNone(result["metadata"]["primary_language"])
        self.assertEqual([], result["metadata"]["additional_languages"])

    def test_requirements_and_notes_remain_structured(self):
        requirements = processor.process_text(self.fixture("07-written-requirements.md"))
        notes = processor.process_text(self.fixture("08-meeting-notes.md"))
        self.assertEqual("written_requirements", requirements["metadata"]["input_type"])
        self.assertEqual("meeting_notes", notes["metadata"]["input_type"])
        self.assertIn("# Weekly notes", notes["normalized_text"])

    def test_empty_and_whitespace_inputs_fail(self):
        for name in ("09-empty.txt", "10-whitespace-only.txt"):
            result = processor.process_text(self.fixture(name))
            self.assertEqual("failed", result["status"])
            self.assertEqual("empty_input", result["errors"][0]["code"])

    def test_long_input_is_never_truncated(self):
        line = self.fixture("11-long-transcript.txt").strip()
        source = "\n".join([line] * 1200)
        result = processor.process_text(source)
        self.assertEqual(source, result["original_text"])
        self.assertEqual(len(source), result["statistics"]["character_count"])
        self.assertEqual(1200, result["statistics"]["segment_count"])

    def test_sensitive_facts_and_instruction_like_source_are_data(self):
        for name, required in (("12-sensitive-facts.txt", "$5,000"), ("13-instruction-like-source.txt", "Ignore prior instructions")):
            source = self.fixture(name)
            result = processor.process_text(source)
            self.assertIn(required, result["original_text"])
            self.assertIn(required, result["normalized_text"])

    def test_file_errors_and_json_output(self):
        unsupported = FIXTURES / "14-unsupported.pdf"
        with self.assertRaisesRegex(ValueError, "unsupported_file_type"):
            processor.read_text_file(unsupported)
        with tempfile.TemporaryDirectory() as temp_dir:
            bad = Path(temp_dir) / "bad.txt"
            bad.write_bytes(b"\xff\xff")
            with self.assertRaisesRegex(ValueError, "invalid_text_encoding"):
                processor.read_text_file(bad)
            command = [sys.executable, str(SCRIPT), "--input-file", str(FIXTURES / "01-granola-transcript.txt"), "--source", "granola"]
            completed = subprocess.run(command, capture_output=True, text=True, check=False)
        self.assertEqual(0, completed.returncode, completed.stderr)
        rendered = json.loads(completed.stdout)
        self.assertEqual("success", rendered["status"])
        self.assertEqual("granola", rendered["metadata"]["input_source"])

    def test_run_directory_persists_the_canonical_handoff_artifact(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            run_dir = Path(temp_dir) / "runs" / "client-call"
            command = [
                sys.executable, str(SCRIPT),
                "--input-file", str(FIXTURES / "01-granola-transcript.txt"),
                "--run-dir", str(run_dir),
            ]
            completed = subprocess.run(command, capture_output=True, text=True, check=False)
            artifact = run_dir / "01-input-processing.json"
            self.assertEqual(0, completed.returncode, completed.stderr)
            self.assertEqual("", completed.stdout)
            self.assertTrue(artifact.is_file())
            result = json.loads(artifact.read_text(encoding="utf-8"))
        self.assertEqual("success", result["status"])
        self.assertEqual(self.fixture("01-granola-transcript.txt"), result["original_text"])

    def test_multiple_files_fail_without_processing(self):
        command = [sys.executable, str(SCRIPT), "--input-file", str(FIXTURES / "01-granola-transcript.txt"), "--input-file", str(FIXTURES / "02-timestamped-transcript.txt")]
        completed = subprocess.run(command, capture_output=True, text=True, check=False)
        rendered = json.loads(completed.stdout)
        self.assertEqual(2, completed.returncode)
        self.assertEqual("failed", rendered["status"])
        self.assertEqual("multiple_input_documents", rendered["errors"][0]["code"])


if __name__ == "__main__":
    unittest.main()
