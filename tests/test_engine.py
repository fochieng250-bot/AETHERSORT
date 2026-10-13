import tempfile
import unittest
from pathlib import Path
from aethersort.engine import AetherSortEngine


class EngineTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.base = Path(self.tmp.name)
        self.target = self.base / "target"
        self.target.mkdir()
        self.engine = AetherSortEngine(self.base / "history.sqlite3")

    def tearDown(self):
        # Explicitly clear engine references to release SQLite file handles on Windows
        if hasattr(self, "engine"):
            del self.engine
        
        # Clean up the temporary directory safely
        try:
            self.tmp.cleanup()
        except PermissionError:
            pass  # Fallback in case OS is still releasing the file handle

    def test_plan_only_root_files_and_categories(self):
        (self.target / "notes.txt").write_text("hello")
        nested = self.target / "nested"
        nested.mkdir()
        (nested / "inside.pdf").write_text("untouched")
        actions = self.engine.plan(self.target)
        self.assertEqual([(a.source.name, a.category, a.status) for a in actions], [("notes.txt", "Documents", "move")])

    def test_identical_duplicate_is_skipped(self):
        (self.target / "photo.jpg").write_bytes(b"same")
        (self.target / "Images").mkdir()
        (self.target / "Images" / "photo.jpg").write_bytes(b"same")
        actions = self.engine.plan(self.target)
        self.assertEqual(len(actions), 1)
        self.assertEqual(actions[0].status, "identical")

    def test_conflicting_destination_is_renamed_not_overwritten(self):
        (self.target / "report.pdf").write_text("new")
        folder = self.target / "Documents"
        folder.mkdir()
        (folder / "report.pdf").write_text("old")
        actions = self.engine.plan(self.target)
        self.assertEqual(actions[0].destination.name, "report_1.pdf")
        result = self.engine.execute(self.target, actions)
        self.assertEqual(result.moved, 1)
        self.assertEqual((folder / "report.pdf").read_text(), "old")
        self.assertEqual((folder / "report_1.pdf").read_text(), "new")

    def test_execute_and_undo(self):
        file = self.target / "notes.txt"
        file.write_text("safe")
        actions = self.engine.plan(self.target)
        result = self.engine.execute(self.target, actions)
        self.assertEqual(result.moved, 1)
        self.assertFalse(file.exists())
        self.assertTrue((self.target / "Documents" / "notes.txt").exists())
        undo = self.engine.undo_last_run()
        self.assertEqual(undo.moved, 1)
        self.assertTrue(file.exists())
        self.assertEqual(file.read_text(), "safe")

    def test_recovery_reverses_interrupted_journaled_move(self):
        source = self.target / "interrupted.txt"
        destination = self.target / "Documents" / "interrupted.txt"
        source.write_text("recover me")
        with self.engine._managed_connection() as con:
            cur = con.execute(
                "INSERT INTO runs(target, started_at, status) VALUES (?, ?, 'running')",
                (str(self.target), "2026-01-01T00:00:00+00:00"),
            )
            run_id = int(cur.lastrowid)
            con.execute(
                "INSERT INTO operation_journal(run_id, source, destination, state) VALUES (?, ?, ?, 'planned')",
                (run_id, str(source), str(destination)),
            )
        destination.parent.mkdir(parents=True, exist_ok=True)
        source.rename(destination)  # simulate a crash after moving but before journal update

        # Explicitly delete the original engine first to free the database lock
        del self.engine

        restarted = AetherSortEngine(self.base / "history.sqlite3")
        self.assertTrue(source.exists())
        self.assertFalse(destination.exists())
        self.assertTrue(any("interrupted" in message for message in restarted.recovery_messages))
        run = restarted.recent_runs(1)[0]
        self.assertEqual(run["status"], "interrupted_rolled_back")
        
        # Clean up the restarted engine instance as well
        del restarted

    def test_stale_preview_refuses_to_overwrite_new_destination(self):
        source = self.target / "notes.txt"
        source.write_text("original")
        actions = self.engine.plan(self.target)
        destination = actions[0].destination
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text("someone else's file")
        result = self.engine.execute(self.target, actions)
        self.assertEqual(result.moved, 0)
        self.assertTrue(source.exists())
        self.assertEqual(destination.read_text(), "someone else's file")
        self.assertTrue(result.errors)

    def test_invalid_target_rejected(self):
        with self.assertRaises(ValueError):
            self.engine.plan(self.base / "missing")


if __name__ == "__main__":
    unittest.main()