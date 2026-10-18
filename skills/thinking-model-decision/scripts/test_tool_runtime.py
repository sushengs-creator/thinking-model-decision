import copy
import json
import tempfile
import unittest
from pathlib import Path
import tool_runtime as runtime


class RuntimeTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name) / "skill"
        self.root.mkdir()
        refs = self.root / "references"
        (refs / "tools").mkdir(parents=True)
        self.row = {"id": "TM-001", "name": "sample", "runtime_status": "authored", "trial_records": [], "task": "改变合作方式", "roles": ["参与者"], "signals": ["共同合作"], "output": "合作安排"}
        for kind, rel in (("source", "references/source.md"), ("card", "references/card.md"), ("runtime", "references/tools/TM-001.md")):
            (self.root / rel).write_text(kind, encoding="utf-8")
            self.row[kind + "_path"] = rel
            self.row[kind + "_sha256"] = runtime.digest(self.root / rel)
        self.index = {"schema_version": 2, "version": "2.0.0", "tools": [self.row]}
        self.users = [{"id": "TM-001", "short_name": "sample", "path": self.row["source_path"], "card_path": self.row["card_path"]},
                      {"id": "TM-002", "short_name": "legacy", "path": "references/source.md", "card_path": "references/card.md"}]
        for user in self.users:
            user.update(source_sha256=self.row["source_sha256"], content_sha256=self.row["source_sha256"],
                        card_sha256=self.row["card_sha256"], card_source_sha256=self.row["source_sha256"],
                        card_status="source_reviewed")
        self.state = {"version": self.index["version"], "wan_tools": 1, "tool_migration": {"migrated_ids": ["TM-001"], "migrated_count": 1, "total_user_models": 2, "remaining_not_migrated": 1}}
        (refs / "wan.md").write_text("WW peer body", encoding="utf-8")
        self.wan = [{"id": "WW-1.1", "short_name": "合作", "trigger": "共同合作", "path": "references/wan.md", "content_sha256": runtime.digest(refs / "wan.md")}]
        self.save()

    def save(self):
        for name, data in (("tool-index", self.index), ("user-index", self.users), ("library-state", self.state), ("wan-index", self.wan)):
            (self.root / "references" / (name + ".json")).write_text(json.dumps(data), encoding="utf-8")

    def test_valid_and_legacy_fallback(self):
        self.assertTrue(runtime.validate(self.root)["ok"])
        self.assertEqual(runtime.show(self.root, "TM-002")["runtime_status"], "not_migrated")
        with self.assertRaises(ValueError):
            runtime.show(self.root, "TM-999")

    def test_changed_source_invalidates_fingerprint(self):
        (self.root / self.row["source_path"]).write_text("changed")
        self.assertIn("TM-001: stale source fingerprint", runtime.validate(self.root)["errors"])
        self.assertFalse(runtime.show(self.root, "TM-001")["fingerprints_current"])

    def test_stale_card_association_cannot_be_hidden_by_current_runtime_hashes(self):
        self.users[0]["card_source_sha256"] = "0" * 64
        self.save()
        self.assertFalse(runtime.validate(self.root)["ok"])
        shown = runtime.show(self.root, "TM-001")
        self.assertFalse(shown["card_source_is_current"])
        self.assertEqual(shown["invocation_status"], "review_required")
        self.users[0]["card_source_sha256"] = self.users[0]["source_sha256"]
        self.users[0]["card_status"] = "needs_review"
        self.save()
        self.assertFalse(runtime.validate(self.root)["ok"])
        self.assertFalse(runtime.show(self.root, "TM-001")["fingerprints_current"])

    def test_search_marks_stale_tm_and_ww_without_hiding_candidates(self):
        (self.root / self.row["source_path"]).write_text("changed source")
        (self.root / "references/wan.md").write_text("changed WW")
        hits = runtime.search(self.root, "共同合作")["results"]
        self.assertEqual({r["family"] for r in hits}, {"TM", "WW"})
        for hit in hits:
            self.assertFalse(hit["fingerprints_current"])
            self.assertEqual(hit["invocation_status"], "review_required")
            self.assertTrue(hit["freshness_issues"])

    def test_unregistered_source_or_card_edits_are_not_current(self):
        for kind, hash_key in (("source", "content_sha256"), ("card", "card_sha256")):
            with self.subTest(kind=kind):
                old = self.users[0].pop(hash_key)
                self.save()
                self.assertFalse(runtime.validate(self.root)["ok"])
                self.users[0][hash_key] = old
        self.save()
        self.assertTrue(runtime.validate(self.root)["ok"])

    def test_duplicate_or_count_drift(self):
        self.index["tools"].append(copy.deepcopy(self.row))
        self.save()
        self.assertFalse(runtime.validate(self.root)["ok"])

    def test_path_escape(self):
        for path in ("../outside", "/tmp/outside"):
            with self.assertRaises(ValueError):
                runtime.checked_path(self.root, path)

    def test_symlink_escape(self):
        outside = Path(self.temp.name) / "outside.md"
        outside.write_text("outside")
        (self.root / "escape.md").symlink_to(outside)
        with self.assertRaises(ValueError):
            runtime.checked_path(self.root, "escape.md")

    def test_trial_claim_needs_existing_record(self):
        self.row["runtime_status"] = "sample_trials_reviewed"
        self.save()
        self.assertFalse(runtime.validate(self.root)["ok"])
        self.row["trial_records"] = ["references/not-there.md"]
        self.save()
        self.assertFalse(runtime.validate(self.root)["ok"])
        (self.root / "references/not-there.md").write_text("actual response")
        self.assertFalse(runtime.validate(self.root)["ok"])
        self.row["review_records"] = ["references/review.md"]
        (self.root / "references/review.md").write_text("scope-limited review")
        self.save()
        self.assertTrue(runtime.validate(self.root)["ok"])

    def test_source_association_mismatch(self):
        self.row["card_path"] = self.row["source_path"]
        self.row["card_sha256"] = self.row["source_sha256"]
        self.save()
        self.assertFalse(runtime.validate(self.root)["ok"])

    def test_ww_is_searchable_peer_and_readback_detects_changes(self):
        hits = runtime.search(self.root, "共同合作")["results"]
        self.assertEqual({r["family"] for r in hits}, {"TM", "WW"})
        self.assertTrue(runtime.show(self.root, "WW-1.1")["fingerprints_current"])
        (self.root / "references/wan.md").write_text("changed")
        self.assertFalse(runtime.show(self.root, "WW-1.1")["fingerprints_current"])
        self.assertFalse(runtime.validate(self.root)["ok"])

    def test_exact_id_and_role_filter_are_explicit(self):
        self.assertEqual(runtime.search(self.root, "TM-001")["results"][0]["id"], "TM-001")
        filtered = runtime.search(self.root, "共同合作", role="参与者")
        self.assertEqual(filtered["role_scope"], "TM only")
        self.assertEqual([r["id"] for r in filtered["results"]], ["TM-001"])
        self.assertFalse(runtime.contains("icapping", "icap"))

    def test_additional_runtime_must_be_registered(self):
        (self.root / "references/tools/TM-002.md").write_text("local addition")
        self.assertIn("Runtime file/index mismatch", runtime.validate(self.root)["errors"])
        self.assertEqual(runtime.show(self.root, "TM-002")["runtime_status"], "not_migrated")

    def test_unknown_role_and_invalid_input(self):
        self.row["roles"] = ["not a role"]
        self.save()
        self.assertFalse(runtime.validate(self.root)["ok"])
        with self.assertRaises(ValueError):
            runtime.search(self.root, "!!!")
        with self.assertRaises(ValueError):
            runtime.show(self.root, "WW-9.99")


if __name__ == "__main__":
    unittest.main()
