"""Comprehensive tests for redesigned AI-driven Step 08 — Visual Generation.

Tests verify:
  - Upstream input validation (validate_input.py)
  - Design system rules and font discovery (design_system.py)
  - Text measurement utilities (text_measurement.py)
  - Safe asset embedding with security checks (embed_assets.py)
  - SVG structural validation (validate_svg.py)
  - Direct SVG geometry validation (validate_geometry.py)
  - Content coverage validation directly on SVG (validate_coverage.py)
  - Element manifest extraction and animation handoff (output_contract.py)
  - SVG rendering preview generation (render_preview.py)
  - End-to-end integration: reference-driven AI SVG workflow
"""

import importlib.util
import json
import os
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2] / "scripts" / "08-visual-generation"


def mod(name):
    spec = importlib.util.spec_from_file_location(name, ROOT / f"{name}.py")
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


# Load active Step 08 helper modules
val_input = mod("validate_input")
ds = mod("design_system")
tm = mod("text_measurement")
embed = mod("embed_assets")
val_svg = mod("validate_svg")
val_geo = mod("validate_geometry")
val_cov = mod("validate_coverage")
out_mod = mod("output_contract")
renderer = mod("render_preview")


# ---------------------------------------------------------------------------
# Test Fixtures
# ---------------------------------------------------------------------------

SAMPLE_AI_SVG = """<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="800" viewBox="0 0 1200 800">
  <defs>
    <marker id="arrow" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
      <path d="M 0 1 L 9 5 L 0 9 z" fill="#64748b" />
    </marker>
  </defs>
  <rect id="bg" width="1200" height="800" fill="#f8fafc" />
  <g id="section-header">
    <text id="node-title" x="40" y="60" font-family="sans-serif" font-size="28" font-weight="bold" fill="#0f172a">GTM Execution Blueprint</text>
  </g>
  <g id="section-step-1">
    <rect id="step-1-card" x="40" y="100" width="340" height="240" rx="12" fill="#ffffff" stroke="#e2e8f0" />
    <text id="node-step-1" x="60" y="140" font-family="sans-serif" font-size="18" font-weight="600" fill="#1e293b">Account Identification</text>
    <rect id="node-s1-tool-1" x="60" y="180" width="120" height="36" rx="6" fill="#f1f5f9" />
    <text x="70" y="202" font-family="sans-serif" font-size="12" fill="#334155">Salesforce</text>
  </g>
  <g id="section-step-2">
    <rect id="step-2-card" x="420" y="100" width="340" height="240" rx="12" fill="#ffffff" stroke="#e2e8f0" />
    <text id="node-step-2" x="440" y="140" font-family="sans-serif" font-size="18" font-weight="600" fill="#1e293b">Stakeholder Engagement</text>
    <rect id="node-s2-tool-1" x="440" y="180" width="120" height="36" rx="6" fill="#f1f5f9" />
    <text x="450" y="202" font-family="sans-serif" font-size="12" fill="#334155">HubSpot</text>
  </g>
  <path id="conn-1-to-2" d="M 380 220 L 420 220" fill="none" stroke="#64748b" stroke-width="2" marker-end="url(#arrow)" />
  <g id="section-outcome">
    <rect id="node-outcome" x="800" y="100" width="340" height="240" rx="12" fill="#fef9c3" stroke="#ca8a04" />
    <text x="830" y="140" font-family="sans-serif" font-size="18" font-weight="bold" fill="#854d0e">Closed-Won</text>
  </g>
</svg>"""


# ---------------------------------------------------------------------------
# Test Cases
# ---------------------------------------------------------------------------

class TestValidateInput(unittest.TestCase):
    def test_valid_upstream_artifacts(self):
        with tempfile.TemporaryDirectory() as t:
            p = Path(t)
            for name, step, version in val_input.EXPECTED:
                (p / name).write_text(json.dumps({
                    "step": step,
                    "version": version,
                    "status": "success",
                    "run_id": "test-run",
                    "errors": [],
                }))
            errors, run_id = val_input.validate(p)
            self.assertEqual(errors, [])
            self.assertEqual(run_id, "test-run")

    def test_missing_artifacts(self):
        with tempfile.TemporaryDirectory() as t:
            errors, run_id = val_input.validate(Path(t))
            self.assertTrue(len(errors) > 0)
            self.assertIsNone(run_id)


class TestDesignSystem(unittest.TestCase):
    def test_defaults_applied(self):
        res = ds.apply_defaults({})
        self.assertIn("palette", res)
        self.assertIn("type_scale", res)
        self.assertIn("borders", res)
        self.assertIn("fonts", res)

    def test_font_discovery(self):
        fonts = ds.discover_fonts()
        self.assertIn("resolved_fonts", fonts)
        self.assertIn("sans", fonts["resolved_fonts"])


class TestTextMeasurement(unittest.TestCase):
    def test_basic_metrics(self):
        m = tm.measure_text("Market Analysis and Selection", 16)
        self.assertGreater(m["width"], 0)
        self.assertEqual(m["line_count"], 1)

    def test_wrapping_computation(self):
        m = tm.measure_text("This is an extended label that should be split into multiple lines for cards", 14, max_width=150)
        self.assertGreater(m["line_count"], 1)
        self.assertLessEqual(m["width"], 150)


class TestAssetEmbedding(unittest.TestCase):
    def test_embed_png_success(self):
        with tempfile.TemporaryDirectory() as t:
            p = Path(t) / "logo.png"
            p.write_bytes(
                b"\x89PNG\r\n\x1a\n"
                b"\x00\x00\x00\rIHDR"
                b"\x00\x00\x00\x01\x00\x00\x00\x01\x08\x02"
                b"\x00\x00\x00\x90wS\xde"
            )
            res = embed.embed_asset(p, t)
            self.assertIsNotNone(res["data_uri"])
            self.assertTrue(res["data_uri"].startswith("data:image/png;base64,"))

    def test_embed_svg_clean_success(self):
        with tempfile.TemporaryDirectory() as t:
            p = Path(t) / "logo.svg"
            p.write_text('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100"><circle cx="50" cy="50" r="40" fill="#2563eb"/></svg>')
            res = embed.embed_asset(p, t)
            self.assertIsNotNone(res["data_uri"])
            self.assertTrue(res["data_uri"].startswith("data:image/svg+xml;base64,"))

    def test_reject_svg_script_injection(self):
        with tempfile.TemporaryDirectory() as t:
            p = Path(t) / "malicious.svg"
            p.write_text('<svg xmlns="http://www.w3.org/2000/svg"><script>alert(1)</script></svg>')
            res = embed.embed_asset(p, t)
            self.assertIsNone(res["data_uri"])
            self.assertIn("security rejection", res["error"])

    def test_reject_path_traversal(self):
        with tempfile.TemporaryDirectory() as t:
            valid, err, _ = embed.validate_asset_path("/etc/hosts", t)
            self.assertFalse(valid)
            self.assertIn("escapes allowed root", err)


class TestValidateSVG(unittest.TestCase):
    def test_valid_svg(self):
        with tempfile.TemporaryDirectory() as t:
            p = Path(t) / "test.svg"
            p.write_text(SAMPLE_AI_SVG)
            errors = val_svg.validate(p)
            self.assertEqual(errors, [])

    def test_detect_script(self):
        with tempfile.TemporaryDirectory() as t:
            p = Path(t) / "bad.svg"
            p.write_text('<svg width="100" height="100" viewBox="0 0 100 100"><script>alert("xss")</script></svg>')
            errors = val_svg.validate(p)
            self.assertTrue(any("script" in e for e in errors))

    def test_detect_missing_dimensions(self):
        with tempfile.TemporaryDirectory() as t:
            p = Path(t) / "no_dim.svg"
            p.write_text('<svg><rect/></svg>')
            errors = val_svg.validate(p)
            self.assertTrue(any("dimensions" in e for e in errors))


class TestValidateGeometry(unittest.TestCase):
    def test_svg_geometry_validation_pass(self):
        with tempfile.TemporaryDirectory() as t:
            p = Path(t) / "test.svg"
            p.write_text(SAMPLE_AI_SVG)
            errors = val_geo.validate_svg_geometry(p)
            self.assertEqual(errors, [])

    def test_svg_geometry_out_of_bounds_detected(self):
        with tempfile.TemporaryDirectory() as t:
            p = Path(t) / "overflow.svg"
            p.write_text('<svg width="200" height="100" viewBox="0 0 200 100"><rect id="r1" x="150" y="10" width="100" height="50" /></svg>')
            errors = val_geo.validate_svg_geometry(p)
            self.assertTrue(any("exceeds canvas width" in e for e in errors))

    def test_plan_dict_compatibility(self):
        plan = {
            "canvas": {"width": 500, "height": 300},
            "components": [{"id": "c1", "x": 10, "y": 10, "width": 100, "height": 40}],
        }
        self.assertEqual(val_geo.validate(plan), [])


class TestValidateCoverage(unittest.TestCase):
    def test_full_coverage(self):
        arch = {
            "nodes": [
                {"id": "node-title"},
                {"id": "node-step-1"},
                {"id": "node-s1-tool-1"},
                {"id": "node-step-2"},
                {"id": "node-s2-tool-1"},
                {"id": "node-outcome"},
            ]
        }
        content = {
            "title": "GTM Execution Blueprint",
            "copy": {
                "step1": "Account Identification",
                "step2": "Stakeholder Engagement",
                "outcome": "Closed-Won",
            }
        }
        with tempfile.TemporaryDirectory() as t:
            p = Path(t) / "sample.svg"
            p.write_text(SAMPLE_AI_SVG)
            cov = val_cov.validate_coverage(p, content, arch)
            self.assertEqual(cov["coverage_ratio"], 1.0)
            self.assertEqual(cov["missing"], [])
            self.assertEqual(len(cov["missing_copy"]), 0)


class TestOutputContract(unittest.TestCase):
    def test_manifest_extraction(self):
        with tempfile.TemporaryDirectory() as t:
            p = Path(t) / "test.svg"
            p.write_text(SAMPLE_AI_SVG)
            manifest = out_mod.extract_manifest_from_svg(p)
            self.assertGreater(len(manifest), 0)
            ids = [m["id"] for m in manifest]
            self.assertIn("node-title", ids)
            self.assertIn("conn-1-to-2", ids)
            self.assertIn("node-outcome", ids)

    def test_animation_handoff(self):
        manifest = [
            {"id": "conn-1-to-2", "role": "connector", "semantic": "flow", "animatable": True},
            {"id": "node-outcome", "role": "outcome", "semantic": "terminal", "animatable": True},
            {"id": "node-title", "role": "title", "semantic": "title", "animatable": False},
        ]
        handoff = out_mod.build_animation_handoff(manifest)
        self.assertEqual(handoff["animation_eligible_count"], 2)
        self.assertEqual(len(handoff["stationary_elements"]), 1)

    def test_output_contract_build(self):
        contract = out_mod.build_output_contract(
            run_id="test-run",
            sources={"arch": "04"},
            design_system_summary={"palette": {"bg": "#fff"}},
            element_manifest=[{"id": "node-1"}],
            asset_usage=[],
            coverage_assessment={"coverage_ratio": 1.0},
            animation_handoff={"eligible": 1},
            validation={"valid": True},
        )
        self.assertEqual(contract["step"], "08-visual-generation")
        self.assertEqual(contract["status"], "success")
        self.assertEqual(contract["run_id"], "test-run")


class TestRenderPreview(unittest.TestCase):
    def test_renderer_info(self):
        info = renderer.get_renderer_info()
        self.assertIn("available_renderers", info)

    def test_render_svg_to_png(self):
        info = renderer.get_renderer_info()
        if not info["available_renderers"]:
            self.skipTest("No local SVG renderer available")

        with tempfile.TemporaryDirectory() as t:
            svg_p = Path(t) / "test.svg"
            png_p = Path(t) / "test.png"
            svg_p.write_text(SAMPLE_AI_SVG)
            ok, msg = renderer.render(svg_p, png_p)
            self.assertTrue(ok, f"Render failed: {msg}")
            self.assertTrue(png_p.is_file())
            self.assertGreater(png_p.stat().st_size, 0)


# ---------------------------------------------------------------------------
# Synthetic Reference-Driven AI Workflow Integration
# ---------------------------------------------------------------------------

class TestSyntheticAIWorkflowIntegration(unittest.TestCase):
    def test_direct_ai_svg_pipeline(self):
        """Simulate the complete redesigned AI generation workflow:
        Upstream inputs -> Direct AI SVG authoring -> Geometry & SVG validation ->
        Coverage check -> PNG Preview rendering -> Manifest extraction -> Output contract
        """
        arch = {
            "nodes": [
                {"id": "node-title"},
                {"id": "node-step-1"},
                {"id": "node-s1-tool-1"},
                {"id": "node-step-2"},
                {"id": "node-s2-tool-1"},
                {"id": "node-outcome"},
            ]
        }
        content = {
            "title": "GTM Execution Blueprint",
            "copy": {
                "step1": "Account Identification",
                "step2": "Stakeholder Engagement",
                "outcome": "Closed-Won",
            }
        }

        with tempfile.TemporaryDirectory() as t:
            run_dir = Path(t)
            step08_dir = run_dir / "step-08"
            step08_dir.mkdir(parents=True)

            svg_file = step08_dir / "infographic.svg"
            png_file = step08_dir / "preview.png"

            # 1. AI writes the SVG directly
            svg_file.write_text(SAMPLE_AI_SVG)
            self.assertTrue(svg_file.is_file())

            # 2. Structural & Geometry validation
            svg_errs = val_svg.validate(svg_file)
            self.assertEqual(svg_errs, [])

            geo_errs = val_geo.validate_svg_geometry(svg_file)
            self.assertEqual(geo_errs, [])

            # 3. Content coverage verification
            cov = val_cov.validate_coverage(svg_file, content, arch)
            self.assertEqual(cov["coverage_ratio"], 1.0)
            self.assertEqual(cov["missing"], [])

            # 4. Preview rendering
            render_res = None
            info = renderer.get_renderer_info()
            if info["available_renderers"]:
                ok, msg = renderer.render(svg_file, png_file)
                render_res = (ok, msg)
                self.assertTrue(ok)
                self.assertTrue(png_file.is_file())

            # 5. Manifest extraction & animation handoff
            manifest = out_mod.extract_manifest_from_svg(svg_file)
            handoff = out_mod.build_animation_handoff(manifest)

            # 6. Validation report
            report = out_mod.build_validation_report(
                geometry_errors=geo_errs,
                svg_errors=svg_errs,
                coverage_result=cov,
                render_result=render_res,
            )
            self.assertTrue(report["overall"]["valid"])

            # 7. Output contract assembly
            contract = out_mod.build_output_contract(
                run_id="synth-ai-run",
                sources={"architecture": "04-workflow-architecture.json"},
                design_system_summary={"template_id": "T01-modular"},
                element_manifest=manifest,
                asset_usage=[],
                coverage_assessment=cov,
                animation_handoff=handoff,
                validation=report,
            )
            self.assertEqual(contract["status"], "success")
            self.assertEqual(contract["step"], "08-visual-generation")


if __name__ == "__main__":
    unittest.main()
