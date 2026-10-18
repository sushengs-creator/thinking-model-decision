import copy
import json
import unittest
from pathlib import Path
import register_runtime
import tool_runtime
import test_tool_runtime as fixtures


class RegistrationTests(unittest.TestCase):
    setUp = fixtures.RuntimeTests.setUp
    save = fixtures.RuntimeTests.save

    def test_future_model_preview_preserves_unrelated_rows(self):
        (self.root / "references/tools/TM-002.md").write_text("new local tool")
        metadata = {"id": "TM-002", "name": "new", "task": "new task", "roles": ["澄清"], "signals": ["new"], "output": "new output"}
        before = (self.root / "references/tool-index.json").read_bytes()
        index, state, row = register_runtime.prepare(self.root, metadata)
        self.assertEqual((self.root / "references/tool-index.json").read_bytes(), before)
        self.assertEqual(index["tools"][0], self.row)
        self.assertEqual(state["tool_migration"]["remaining_not_migrated"], 0)
        self.assertEqual(row["runtime_status"], "authored")
        self.assertFalse(state["release_validation"]["valid_for_current_revision"])
        (self.root / "references/tool-catalog.md").write_text("old catalog")
        backup = register_runtime.apply(self.root, index, state, Path(self.temp.name) / "backups")
        self.assertEqual((backup / "tool-index.json").read_bytes(), before)
        self.assertTrue(tool_runtime.validate(self.root)["ok"])

    def test_revised_runtime_does_not_inherit_old_trial_claim(self):
        self.row["runtime_status"] = "sample_trials_reviewed"
        self.save()
        metadata = {k: copy.deepcopy(self.row[k]) for k in ("id", "name", "task", "roles", "signals", "output")}
        _, _, row = register_runtime.prepare(self.root, metadata)
        self.assertEqual(row["runtime_status"], "authored")
        self.assertEqual(row["trial_records"], [])

    def test_backup_inside_skill_is_rejected_before_mutation(self):
        before = (self.root / "references/tool-index.json").read_bytes()
        with self.assertRaises(ValueError):
            register_runtime.apply(self.root, self.index, self.state, self.root / "backup")
        self.assertEqual((self.root / "references/tool-index.json").read_bytes(), before)

    def test_stale_source_card_is_rejected_without_writing(self):
        metadata = {k: copy.deepcopy(self.row[k]) for k in ("id", "name", "task", "roles", "signals", "output")}
        for field, value in (("card_status", "needs_review"), ("card_source_sha256", "0" * 64)):
            with self.subTest(field=field):
                original = self.users[0][field]
                self.users[0][field] = value
                self.save()
                before = (self.root / "references/tool-index.json").read_bytes()
                with self.assertRaises(ValueError):
                    register_runtime.prepare(self.root, metadata)
                self.assertEqual((self.root / "references/tool-index.json").read_bytes(), before)
                self.users[0][field] = original

    def test_unregistered_source_and_card_edits_cannot_be_rehashed_as_current(self):
        metadata = {k: copy.deepcopy(self.row[k]) for k in ("id", "name", "task", "roles", "signals", "output")}
        for kind in ("source", "card"):
            with self.subTest(kind=kind):
                path = self.root / self.row[kind + "_path"]
                before = path.read_bytes()
                path.write_text("unregistered edit")
                with self.assertRaises(ValueError):
                    register_runtime.prepare(self.root, metadata)
                path.write_bytes(before)

    def test_only_recognized_reviewed_cards_can_back_registered_runtimes(self):
        metadata = {k: copy.deepcopy(self.row[k]) for k in ("id", "name", "task", "roles", "signals", "output")}
        metadata["runtime_status"] = "source_checked"
        for status in ("draft", "unsupported", None):
            with self.subTest(rejected_status=status):
                if status is None:
                    self.users[0].pop("card_status", None)
                else:
                    self.users[0]["card_status"] = status
                self.save()
                before = (self.root / "references/tool-index.json").read_bytes()
                with self.assertRaises(ValueError):
                    register_runtime.prepare(self.root, metadata)
                self.assertEqual((self.root / "references/tool-index.json").read_bytes(), before)
                self.assertFalse(tool_runtime.validate(self.root)["ok"])
                self.assertEqual(tool_runtime.show(self.root, "TM-001")["invocation_status"], "review_required")
                hit = tool_runtime.search(self.root, "TM-001")["results"][0]
                self.assertEqual(hit["invocation_status"], "review_required")
        for status in ("source_reviewed", "sample_reviewed", "behavior_checked"):
            with self.subTest(accepted_status=status):
                self.users[0]["card_status"] = status
                self.save()
                metadata.pop("runtime_status", None)
                _, _, row = register_runtime.prepare(self.root, metadata)
                self.assertEqual(row["runtime_status"], "authored")
                self.assertTrue(tool_runtime.validate(self.root)["ok"])


if __name__ == "__main__":
    unittest.main()
