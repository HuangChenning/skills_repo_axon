#!/usr/bin/env python3
"""Focused tests for README content and editorial-static verification."""

import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import verify_readme


SVG_TEMPLATE = """\
<svg viewBox="0 0 {width} {height}" data-diagram-engine="editorial-static"
     data-readme-preset="{preset}" role="img"
     aria-labelledby="request-title request-desc">
  <title id="request-title">Request flow</title>
  <desc id="request-desc">Source-backed request decision flow.</desc>
  <rect width="100%" height="100%" fill="#f5f5f5"/>
</svg>
"""


class ContentVerificationTests(unittest.TestCase):
    def test_outcome_heading_is_classified_as_proof(self):
        self.assertEqual(
            verify_readme.classify_heading("See the outcome first"),
            "Proof",
        )
        self.assertEqual(
            verify_readme.classify_heading("先看成果"),
            "Proof",
        )

    def test_html_image_alt_text_is_checked(self):
        readme = (
            '<img src="assets/readme/hero.svg" '
            'alt="Project\'s workflow and generated outputs">'
        )
        results = verify_readme.check_alt_text(readme)
        self.assertEqual(len(results), 1)
        self.assertTrue(results[0].passed)
        self.assertNotIn("No images found", results[0].detail)

    def test_html_image_without_alt_fails(self):
        results = verify_readme.check_alt_text(
            '<img src="assets/readme/hero.svg">'
        )
        self.assertTrue(any(not result.passed for result in results))

    def test_complex_mechanism_without_visual_fails(self):
        readme = """\
## How it works

Request → inspect → build → verify → publish
"""
        results = verify_readme.check_mechanism_visualization(readme)
        self.assertTrue(any(not result.passed for result in results))

    def test_complex_mechanism_with_visual_passes(self):
        readme = """\
## How it works

1. Inspect
2. Choose
3. Build
4. Verify

![Verified workflow](assets/readme/diagrams/workflow.svg)
"""
        results = verify_readme.check_mechanism_visualization(readme)
        self.assertTrue(all(result.passed for result in results))

    def test_concrete_prose_only_decision_passes(self):
        readme = """\
## How it works

Request → inspect → build → verify

<!-- diagram-decision: prose-only | reason: The four labels already fit in one readable sentence. -->
"""
        results = verify_readme.check_mechanism_visualization(readme)
        self.assertTrue(all(result.passed for result in results))


class EditorialStaticVerificationTests(unittest.TestCase):
    def setUp(self):
        self.tempdir = tempfile.TemporaryDirectory()
        self.root = Path(self.tempdir.name)
        self.diagram_dir = self.root / "assets" / "readme" / "diagrams"
        self.source_dir = self.root / "assets" / "readme" / "source"
        self.diagram_dir.mkdir(parents=True)
        self.source_dir.mkdir(parents=True)
        (self.root / "src").mkdir()
        (self.root / "src" / "router.py").write_text(
            "def route(request):\n    return request\n", encoding="utf-8"
        )
        self.readme = self.root / "README.md"
        self.readme.write_text(
            "![Request routing decisions](assets/readme/diagrams/request-flow.svg)\n",
            encoding="utf-8",
        )

    def tearDown(self):
        self.tempdir.cleanup()

    def write_svg(self, preset="doc-inline", width=960, height=600):
        path = self.diagram_dir / "request-flow.svg"
        path.write_text(
            SVG_TEMPLATE.format(preset=preset, width=width, height=height),
            encoding="utf-8",
        )
        return path

    def write_manifest(self, **overrides):
        manifest = {
            "schema_version": 1,
            "engine": "editorial-static",
            "type": "flowchart",
            "format": "svg",
            "size": "doc-inline",
            "detail": "balanced",
            "audience": "mixed",
            "source_backed": True,
            "evidence": [{"path": "src/router.py", "lines": "1-2"}],
            "counts": {"nodes": 2, "connectors": 1, "focal": 1, "zones": 0},
            "fidelity": {"merged": [], "collapsed": [], "dropped": []},
        }
        manifest.update(overrides)
        (self.source_dir / "request-flow.diagram.json").write_text(
            json.dumps(manifest), encoding="utf-8"
        )

    def editorial_results(self):
        return verify_readme.check_editorial_static_diagrams(
            self.readme.read_text(encoding="utf-8"), self.readme
        )

    def test_valid_source_backed_diagram_passes(self):
        self.write_svg()
        self.write_manifest()
        self.assertTrue(all(result.passed for result in self.editorial_results()))

    def test_missing_manifest_fails(self):
        self.write_svg()
        results = self.editorial_results()
        self.assertTrue(any(
            not result.passed and "manifest exists" in result.name
            for result in results
        ))

    def test_preset_mismatch_fails(self):
        self.write_svg(preset="doc-wide", width=1200, height=675)
        self.write_manifest(size="doc-inline")
        results = self.editorial_results()
        self.assertTrue(any(
            not result.passed and "markers/preset" in result.name
            for result in results
        ))

    def test_source_backed_evidence_must_resolve(self):
        self.write_svg()
        self.write_manifest(evidence=[{"path": "../secret.py", "lines": "1"}])
        results = self.editorial_results()
        self.assertTrue(any(
            not result.passed and "evidence resolves" in result.name
            for result in results
        ))

    def test_evidence_line_range_must_exist(self):
        self.write_svg()
        self.write_manifest(evidence=[{"path": "src/router.py", "lines": "1-99"}])
        results = self.editorial_results()
        self.assertTrue(any(
            not result.passed
            and "evidence resolves" in result.name
            and "outside" in result.detail
            for result in results
        ))

    def test_manifest_root_must_be_object(self):
        self.write_svg()
        (self.source_dir / "request-flow.diagram.json").write_text(
            "[]", encoding="utf-8"
        )
        results = self.editorial_results()
        self.assertTrue(any(
            not result.passed
            and "manifest contract" in result.name
            and "root" in result.detail
            for result in results
        ))

    def test_complexity_budget_is_enforced(self):
        self.write_svg()
        self.write_manifest(
            counts={"nodes": 10, "connectors": 13, "focal": 3, "zones": 0}
        )
        results = self.editorial_results()
        self.assertTrue(any(
            not result.passed
            and "manifest contract" in result.name
            and "node budget" in result.detail
            and "connector budget" in result.detail
            and "focal budget" in result.detail
            for result in results
        ))

    def test_unmarked_960_svg_fails_general_width_check(self):
        svg = self.diagram_dir / "plain.svg"
        svg.write_text(
            '<svg viewBox="0 0 960 600"><title>x</title><desc>y</desc></svg>',
            encoding="utf-8",
        )
        results = verify_readme.check_svg_files([str(svg)], self.readme)
        width_result = next(result for result in results if "2.3" in result.name)
        self.assertFalse(width_result.passed)


ARCHIFY_SVG_TEMPLATE = """\
<svg viewBox="0 0 795 652" data-layout-contract="readable-v2" role="img"
     aria-labelledby="archify-diagram-title archify-diagram-description">
  <style>@font-face {{ font-family: 'JetBrains Mono'; src: url({font_src}) format('woff2'); }}</style>
  <title id="archify-diagram-title">Flow</title>
  <desc id="archify-diagram-description">Workflow export.</desc>
</svg>
"""


class ArchifyExportVerificationTests(unittest.TestCase):
    def setUp(self):
        self.tempdir = tempfile.TemporaryDirectory()
        self.root = Path(self.tempdir.name)
        self.readme = self.root / "README.md"
        self.readme.write_text("", encoding="utf-8")

    def tearDown(self):
        self.tempdir.cleanup()

    def svg_results(self, font_src, template=ARCHIFY_SVG_TEMPLATE):
        svg = self.root / "flow.svg"
        svg.write_text(template.format(font_src=font_src), encoding="utf-8")
        results = verify_readme.check_svg_files([str(svg)], self.readme)
        return {result.name.split(":")[0]: result for result in results}

    def test_archify_export_with_embedded_font_passes(self):
        results = self.svg_results("data:font/woff2;base64,AAAA")
        self.assertTrue(results["2.3 Approved viewBox width"].passed)
        self.assertTrue(results["2.6 No fragile SVG features"].passed)

    def test_archify_export_with_remote_font_fails(self):
        results = self.svg_results("https://example.com/font.woff2")
        self.assertFalse(results["2.6 No fragile SVG features"].passed)

    def test_embedded_font_without_archify_markers_fails(self):
        template = ARCHIFY_SVG_TEMPLATE.replace(
            'data-layout-contract="readable-v2" ', ""
        )
        results = self.svg_results("data:font/woff2;base64,AAAA", template)
        self.assertFalse(results["2.3 Approved viewBox width"].passed)
        self.assertFalse(results["2.6 No fragile SVG features"].passed)

    def write_published_export(self):
        diagram_dir = self.root / "assets" / "readme" / "diagrams"
        source_dir = self.root / "assets" / "readme" / "source"
        diagram_dir.mkdir(parents=True)
        source_dir.mkdir(parents=True)
        (diagram_dir / "flow.svg").write_text(
            ARCHIFY_SVG_TEMPLATE.format(font_src="data:font/woff2;base64,AAAA"),
            encoding="utf-8",
        )
        readme = "![Flow](assets/readme/diagrams/flow.svg)\n"
        self.readme.write_text(readme, encoding="utf-8")
        return source_dir, readme

    def test_archify_export_skips_editorial_manifest_and_requires_ir(self):
        source_dir, readme = self.write_published_export()
        editorial = verify_readme.check_editorial_static_diagrams(readme, self.readme)
        self.assertTrue(all(result.passed for result in editorial))
        archify = verify_readme.check_archify_diagrams(readme, self.readme)
        self.assertFalse(archify[0].passed)

        (source_dir / "flow.archify.json").write_text(
            json.dumps({"schema_version": 2, "diagram_type": "workflow"}),
            encoding="utf-8",
        )
        archify = verify_readme.check_archify_diagrams(readme, self.readme)
        self.assertTrue(all(result.passed for result in archify))


if __name__ == "__main__":
    unittest.main()
