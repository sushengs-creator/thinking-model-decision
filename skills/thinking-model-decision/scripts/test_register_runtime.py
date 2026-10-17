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


if __name__ == "__main__":
    unittest.main()
