#!/usr/bin/env python3
"""Exercise the audit CLI with a synthetic 100-tool library in temporary storage.

Run: python3 <skill>/scripts/test_audit_wan_source.py
Uses only the standard library. Does not read private source attachments or
modify the installed library. The generated source is deliberately fictional.
"""
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


SCRIPT = Path(__file__).resolve().with_name("audit_wan_source.py")


def sha(blob):
    return hashlib.sha256(blob).hexdigest()


class AuditTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="source-audit-")
        self.addCleanup(self.temp.cleanup)
        self.home = Path(self.temp.name)
        self.root = self.home / "skill with spaces"
        self.out = self.home / "reports"
        refs = self.root / "references"
        (refs / "wan-tools").mkdir(parents=True)
        head = "# Fictional framework\n\nFixture only.\n\n".encode()
        category = "## Tools\n\n".encode()
        tail = "## Fictional final checklist\n\nCheck the fixture.\n".encode()
        chunks = [f"### 1.{i} Tool {i}\n\n**何时调用**：Fixture trigger {i}.\n\nMechanism {i}.\n\n".encode()
                  for i in range(1, 101)]
        source = head + category + b"".join(chunks) + tail
        self.source = self.home / "source.md"
        self.source.write_bytes(source)
        fingerprint = sha(source)
        rows, catalog = [], []
        for i, chunk in enumerate(chunks, 1):
            identifier = f"WW-1.{i}"
            relative = f"references/wan-tools/{identifier}.md"
            body = (f"Source: `{fingerprint}`\n\n".encode()
                    + b"<!-- source-excerpt-begin -->\n" + chunk
                    + b"<!-- source-excerpt-end -->\n")
            (self.root / relative).write_bytes(body)
            rows.append({"id": identifier, "title": f"Tool {i}", "short_name": f"Tool {i}",
                         "source_section": f"1.{i}", "trigger": f"Fixture trigger {i}.",
                         "path": relative, "source_sha256": fingerprint, "content_sha256": sha(body)})
            catalog.append(f"| [{identifier} · Tool {i}](wan-tools/{identifier}.md) | Fixture trigger {i}. |")
        self.index = refs / "wan-index.json"
        self.index.write_text(json.dumps(rows), encoding="utf-8")
        (refs / "wan-catalog.md").write_text("\n".join(catalog) + "\n", encoding="utf-8")
        (refs / "source-notes.md").write_text(
            f"| 原文件 SHA-256 | `{fingerprint}` |\n| 原文件字节数 | {len(source)} |\n", encoding="utf-8")
        (refs / "wan-framework.md").write_bytes(
            fingerprint.encode() + b"\n<!-- source-framework-head-begin -->\n" + head
            + b"<!-- source-framework-head-end -->\n<!-- source-framework-tail-begin -->\n"
            + tail + b"<!-- source-framework-tail-end -->\n")

    def run_cli(self, *extra, source=None, root=None):
        command = [sys.executable, str(SCRIPT), "--source-file", str(source or self.source),
                   "--skill-root", str(root or self.root), *map(str, extra)]
        result = subprocess.run(command, cwd=self.home, capture_output=True, text=True)
        self.assertNotIn("Traceback", result.stderr)
        return result, json.loads(result.stdout)

    def assert_error(self, result, report):
        self.assertEqual(result.returncode, 2, (result.stdout, result.stderr))
        self.assertFalse(report["pass"])
        self.assertEqual(report["status"], "error")
        self.assertTrue(report["error"]["message"])

    def test_complete_synthetic_source_matches(self):
        result, report = self.run_cli()
        self.assertEqual(result.returncode, 0)
        self.assertTrue(report["pass"])
        self.assertEqual(report["numeric_h3_count"], 100)
        self.assertTrue(all(report["aggregate_checks"].values()))

    def test_content_difference_keeps_exit_one(self):
        card = self.root / "references/wan-tools/WW-1.50.md"
        card.write_bytes(card.read_bytes().replace(b"Mechanism 50.", b"Changed mechanism."))
        result, report = self.run_cli()
        self.assertEqual(result.returncode, 1)
        self.assertFalse(report["pass"])
        difference = next(row for row in report["differences"] if row.get("id") == "WW-1.50")
        self.assertIn("excerpt_byte_identical", difference["failed_checks"])

    def test_framework_difference_keeps_exit_one(self):
        framework = self.root / "references/wan-framework.md"
        framework.write_bytes(framework.read_bytes().replace(b"Fixture only.", b"Changed."))
        result, report = self.run_cli()
        self.assertEqual(result.returncode, 1)
        self.assertFalse(report["aggregate_checks"]["global_framework_excerpts_match"])

    def test_failed_invocation_replaces_both_prior_success_reports(self):
        result, _ = self.run_cli("--out", self.out)
        self.assertEqual(result.returncode, 0)
        report_file = self.out / "wan-source-audit.json"
        prior = json.loads(report_file.read_text(encoding="utf-8"))
        result, report = self.run_cli("--out", self.out, source=self.home / "missing.md")
        self.assert_error(result, report)
        current = json.loads(report_file.read_text(encoding="utf-8"))
        self.assertFalse(current["pass"])
        self.assertEqual(current["status"], "error")
        self.assertNotEqual(prior["audit_generated_at"], current["audit_generated_at"])
        markdown = (self.out / "wan-source-audit.md").read_text(encoding="utf-8")
        self.assertIn("审计未完成", markdown)
        self.assertNotIn("结论：通过", markdown)

    def test_invalid_encoding_is_explicit_error(self):
        self.source.write_bytes(b"\xff")
        result, report = self.run_cli()
        self.assert_error(result, report)
        self.assertEqual(report["error"]["kind"], "encoding_error")

    def test_missing_skill_root_is_explicit_error(self):
        result, report = self.run_cli(root=self.home / "missing-root")
        self.assert_error(result, report)
        self.assertIn("wan-index.json", report["error"]["message"])

    def test_malformed_json_is_explicit_error(self):
        self.index.write_text("[", encoding="utf-8")
        result, report = self.run_cli()
        self.assert_error(result, report)
        self.assertEqual(report["error"]["kind"], "input_error")

    def test_invalid_index_shapes_are_explicit_errors(self):
        for value in ({}, [None], [{"id": [], "source_sha256": "test"}], [{"id": "WW-1.1"}]):
            with self.subTest(value=value):
                self.index.write_text(json.dumps(value), encoding="utf-8")
                result, report = self.run_cli()
                self.assert_error(result, report)
                self.assertIn("wan-index.json", report["error"]["message"])

    def test_unwritable_report_target_is_not_success(self):
        self.out.write_text("This is a file, not a directory.", encoding="utf-8")
        result, report = self.run_cli("--out", self.out)
        self.assert_error(result, report)
        self.assertTrue(report["report_write_errors"])

    def test_argument_errors_are_json_and_help_remains_help(self):
        result = subprocess.run([sys.executable, str(SCRIPT)], capture_output=True, text=True)
        self.assert_error(result, json.loads(result.stdout))
        self.assertNotIn("Traceback", result.stderr)
        help_result = subprocess.run([sys.executable, str(SCRIPT), "--help"], capture_output=True, text=True)
        self.assertEqual(help_result.returncode, 0)
        self.assertIn("--source-file", help_result.stdout)


if __name__ == "__main__":
    unittest.main(verbosity=2)
