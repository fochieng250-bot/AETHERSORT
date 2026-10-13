"""Safer local-first file sorting engine for AetherSort 0.3.0-beta.1."""
from __future__ import annotations

from contextlib import contextmanager
import hashlib
import os
import shutil
import sqlite3
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable, Iterator

APP_NAME = "AetherSort"
CATEGORIES: dict[str, set[str]] = {
    "Documents": {".pdf", ".doc", ".docx", ".odt", ".rtf", ".txt", ".md", ".csv", ".xls", ".xlsx", ".ppt", ".pptx"},
    "Images": {".png", ".jpg", ".jpeg", ".gif", ".bmp", ".webp", ".tif", ".tiff", ".svg", ".heic"},
    "Audio": {".mp3", ".wav", ".flac", ".aac", ".ogg", ".m4a", ".wma"},
    "Video": {".mp4", ".mov", ".avi", ".mkv", ".webm", ".wmv", ".mpeg", ".mpg"},
    "Archives": {".zip", ".7z", ".rar", ".tar", ".gz", ".bz2", ".xz"},
    "Code": {".py", ".js", ".ts", ".html", ".css", ".java", ".c", ".cpp", ".h", ".cs", ".go", ".rs", ".php", ".json", ".xml", ".yaml", ".yml", ".toml", ".sql", ".sh", ".ps1"},
}


@dataclass(frozen=True)
class PlannedAction:
    source: Path
    destination: Path | None
    category: str
    status: str  # move, identical, error
    note: str = ""


@dataclass
class RunResult:
    run_id: int | None
    moved: int
    skipped_identical: int
    errors: list[str]


def app_data_dir() -> Path:
    """Return a per-user data directory, never the selected folder or app install dir."""
    if os.name == "nt":
        base = Path(os.environ.get("LOCALAPPDATA", Path.home() / "AppData" / "Local"))
    elif os.name == "darwin":
        base = Path.home() / "Library" / "Application Support"
    else:
        base = Path(os.environ.get("XDG_DATA_HOME", Path.home() / ".local" / "share"))
    result = base / "AetherSort"
    result.mkdir(parents=True, exist_ok=True)
    return result


class AetherSortEngine:
    """Plans top-level file moves; never recursively reorganizes subfolders."""

    def __init__(self, database_path: Path | None = None):
        self.database_path = Path(database_path) if database_path else app_data_dir() / "history.sqlite3"
        self.database_path.parent.mkdir(parents=True, exist_ok=True)
        self.recovery_messages: list[str] = []
        self._initialize_db()
        self.recovery_messages = self.recover_interrupted_runs()

    def _connect(self) -> sqlite3.Connection:
        con = sqlite3.connect(self.database_path, timeout=10)
        con.row_factory = sqlite3.Row
        con.execute("PRAGMA foreign_keys = ON")
        # Use DELETE journal mode on Windows to prevent file-locking issues during test cleanups
        if os.name == "nt":
            con.execute("PRAGMA journal_mode = DELETE")
        else:
            con.execute("PRAGMA journal_mode = WAL")
        con.execute("PRAGMA synchronous = FULL")
        return con

    @contextmanager
    def _managed_connection(self) -> Iterator[sqlite3.Connection]:
        """Context manager to guarantee connection cleanup and prevent file locks."""
        con = self._connect()
        try:
            yield con
            con.commit()
        except Exception:
            con.rollback()
            raise
        finally:
            con.close()

    def _initialize_db(self) -> None:
        with self._managed_connection() as con:
            con.executescript("""
                CREATE TABLE IF NOT EXISTS runs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    target TEXT NOT NULL,
                    started_at TEXT NOT NULL,
                    moved INTEGER NOT NULL DEFAULT 0,
                    skipped_identical INTEGER NOT NULL DEFAULT 0,
                    status TEXT NOT NULL DEFAULT 'complete'
                );
                CREATE TABLE IF NOT EXISTS moves (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    run_id INTEGER NOT NULL REFERENCES runs(id) ON DELETE CASCADE,
                    source TEXT NOT NULL,
                    destination TEXT NOT NULL,
                    undone INTEGER NOT NULL DEFAULT 0
                );
                CREATE TABLE IF NOT EXISTS operation_journal (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    run_id INTEGER NOT NULL REFERENCES runs(id) ON DELETE CASCADE,
                    source TEXT NOT NULL,
                    destination TEXT NOT NULL,
                    state TEXT NOT NULL CHECK(state IN ('planned','moved','rolled_back'))
                );
            """)

    @staticmethod
    def _hash(path: Path) -> str:
        digest = hashlib.sha256()
        with path.open("rb") as stream:
            for chunk in iter(lambda: stream.read(1024 * 1024), b""):
                digest.update(chunk)
        return digest.hexdigest()

    @staticmethod
    def _category(path: Path) -> str:
        suffix = path.suffix.lower()
        for name, extensions in CATEGORIES.items():
            if suffix in extensions:
                return name
        return "Other"

    def plan(self, target: Path | str) -> list[PlannedAction]:
        root = Path(target).expanduser().resolve()
        if not root.exists() or not root.is_dir():
            raise ValueError("Choose an existing folder.")
        try:
            entries = sorted(root.iterdir(), key=lambda p: p.name.casefold())
        except OSError as exc:
            raise OSError(f"Cannot read selected folder: {exc}") from exc

        actions: list[PlannedAction] = []
        reserved: set[Path] = set()
        for source in entries:
            try:
                if source.is_symlink() or not source.is_file():
                    continue
                category = self._category(source)
                folder = root / category
                destination = folder / source.name
                if source.parent == folder:
                    continue
                if destination.exists() or destination in reserved:
                    if destination.exists() and destination.is_file() and self._hash(source) == self._hash(destination):
                        actions.append(PlannedAction(source, None, category, "identical", "Identical content already exists"))
                        continue
                    stem, suffix = destination.stem, destination.suffix
                    counter = 1
                    while True:
                        candidate = folder / f"{stem}_{counter}{suffix}"
                        if not candidate.exists() and candidate not in reserved:
                            destination = candidate
                            break
                        if candidate.exists() and candidate.is_file() and self._hash(source) == self._hash(candidate):
                            destination = None
                            break
                        counter += 1
                    if destination is None:
                        actions.append(PlannedAction(source, None, category, "identical", "Identical content already exists"))
                        continue
                reserved.add(destination)
                actions.append(PlannedAction(source, destination, category, "move"))
            except OSError as exc:
                actions.append(PlannedAction(source, None, "Other", "error", str(exc)))
        return actions

    def recover_interrupted_runs(self) -> list[str]:
        """Attempt to reverse journaled moves from runs interrupted by a crash."""
        messages: list[str] = []
        with self._managed_connection() as con:
            runs = con.execute("SELECT id FROM runs WHERE status='running' ORDER BY id").fetchall()
        for run_row in runs:
            run_id = int(run_row["id"])
            with self._managed_connection() as con:
                journal = con.execute(
                    "SELECT * FROM operation_journal WHERE run_id=? AND state IN ('planned','moved') ORDER BY id DESC",
                    (run_id,),
                ).fetchall()
            problems: list[str] = []
            recovered = 0
            for item in journal:
                source, destination = Path(item["source"]), Path(item["destination"])
                try:
                    if destination.exists() and not source.exists():
                        source.parent.mkdir(parents=True, exist_ok=True)
                        if source.exists():
                            raise FileExistsError(f"Original path is occupied: {source}")
                        shutil.move(str(destination), str(source))
                        recovered += 1
                        with self._managed_connection() as con:
                            con.execute("UPDATE operation_journal SET state='rolled_back' WHERE id=?", (item["id"],))
                    elif source.exists() and not destination.exists():
                        with self._managed_connection() as con:
                            con.execute("UPDATE operation_journal SET state='rolled_back' WHERE id=?", (item["id"],))
                    elif source.exists() and destination.exists():
                        raise FileExistsError(f"Both source and destination exist; left unchanged: {source} | {destination}")
                    else:
                        raise FileNotFoundError(f"Neither source nor destination exists; manual review needed: {source} | {destination}")
                except OSError as exc:
                    problems.append(str(exc))
            status = "needs_attention" if problems else "interrupted_rolled_back"
            with self._managed_connection() as con:
                con.execute("UPDATE runs SET status=?, moved=0 WHERE id=?", (status, run_id))
                con.execute("DELETE FROM moves WHERE run_id=?", (run_id,))
            if problems:
                messages.append(f"Run {run_id} needs attention. Recovered {recovered} file(s). " + " | ".join(problems))
            else:
                messages.append(f"Run {run_id} was interrupted; recovered {recovered} file(s) where needed.")
        return messages

    def execute(self, target: Path | str, actions: Iterable[PlannedAction]) -> RunResult:
        root = Path(target).expanduser().resolve()
        actions = list(actions)
        approved = [a for a in actions if a.status == "move" and a.destination is not None]
        identical = sum(a.status == "identical" for a in actions)
        plan_errors = [a.note for a in actions if a.status == "error"]
        if plan_errors:
            return RunResult(None, 0, identical, plan_errors)
        if not approved:
            return RunResult(None, 0, identical, [])

        with self._managed_connection() as con:
            cur = con.execute(
                "INSERT INTO runs(target, started_at, status) VALUES (?, ?, 'running')",
                (str(root), datetime.now(timezone.utc).isoformat()),
            )
            run_id = int(cur.lastrowid)

        errors: list[str] = []
        moved_pairs: list[tuple[Path, Path, int]] = []
        try:
            for action in approved:
                source, destination = action.source, action.destination
                assert destination is not None
                if not source.exists() or not source.is_file() or source.is_symlink():
                    raise FileNotFoundError(f"Source changed since preview: {source}")
                if destination.exists():
                    raise FileExistsError(f"Destination appeared since preview; nothing overwritten: {destination}")
                if source.parent != root or destination.parent.parent != root:
                    raise ValueError("Action is outside the selected folder; scan again before proceeding.")
                with self._managed_connection() as con:
                    cur = con.execute(
                        "INSERT INTO operation_journal(run_id, source, destination, state) VALUES (?, ?, ?, 'planned')",
                        (run_id, str(source), str(destination)),
                    )
                    journal_id = int(cur.lastrowid)
                destination.parent.mkdir(parents=True, exist_ok=True)
                shutil.move(str(source), str(destination))
                moved_pairs.append((source, destination, journal_id))
                with self._managed_connection() as con:
                    con.execute("UPDATE operation_journal SET state='moved' WHERE id=?", (journal_id,))
                    con.execute("INSERT INTO moves(run_id, source, destination) VALUES (?, ?, ?)",
                                 (run_id, str(source), str(destination)))
        except Exception as exc:
            errors.append(str(exc))
            for source, destination, journal_id in reversed(moved_pairs):
                try:
                    if destination.exists() and not source.exists():
                        source.parent.mkdir(parents=True, exist_ok=True)
                        shutil.move(str(destination), str(source))
                        with self._managed_connection() as con:
                            con.execute("UPDATE operation_journal SET state='rolled_back' WHERE id=?", (journal_id,))
                    elif destination.exists() and source.exists():
                        raise FileExistsError(f"Rollback conflict; both paths exist: {source} | {destination}")
                except OSError as rollback_exc:
                    errors.append(f"Rollback needs attention for {destination}: {rollback_exc}")
            needs_attention = len(errors) > 1
            with self._managed_connection() as con:
                con.execute("UPDATE runs SET moved=0, skipped_identical=?, status=? WHERE id=?",
                            (identical, "needs_attention" if needs_attention else "failed_rolled_back", run_id))
                con.execute("DELETE FROM moves WHERE run_id=?", (run_id,))
            return RunResult(run_id, 0, identical, errors)

        with self._managed_connection() as con:
            con.execute("UPDATE runs SET moved=?, skipped_identical=?, status='complete' WHERE id=?",
                        (len(moved_pairs), identical, run_id))
        return RunResult(run_id, len(moved_pairs), identical, [])

    def undo_last_run(self) -> RunResult:
        with self._managed_connection() as con:
            run = con.execute("SELECT * FROM runs WHERE status='complete' AND moved>0 ORDER BY id DESC LIMIT 1").fetchone()
            if run is None:
                return RunResult(None, 0, 0, ["No completed sorting run is available to undo."])
            moves = con.execute("SELECT * FROM moves WHERE run_id=? AND undone=0 ORDER BY id DESC", (run["id"],)).fetchall()

        undone: list[sqlite3.Row] = []
        errors: list[str] = []
        for move in moves:
            source, destination = Path(move["source"]), Path(move["destination"])
            try:
                if not destination.exists():
                    raise FileNotFoundError(f"Moved file is missing: {destination}")
                if source.exists():
                    raise FileExistsError(f"Original path is occupied; refusing to overwrite: {source}")
                source.parent.mkdir(parents=True, exist_ok=True)
                shutil.move(str(destination), str(source))
                undone.append(move)
            except OSError as exc:
                errors.append(str(exc))
                break

        if errors:
            for move in reversed(undone):
                source, destination = Path(move["source"]), Path(move["destination"])
                try:
                    if source.exists() and not destination.exists():
                        destination.parent.mkdir(parents=True, exist_ok=True)
                        shutil.move(str(source), str(destination))
                except OSError as exc:
                    errors.append(f"Undo recovery needs attention for {source}: {exc}")
            return RunResult(int(run["id"]), 0, 0, errors)

        with self._managed_connection() as con:
            con.executemany("UPDATE moves SET undone=1 WHERE id=?", [(m["id"],) for m in undone])
            con.execute("UPDATE runs SET status='undone' WHERE id=?", (run["id"],))
        return RunResult(int(run["id"]), len(undone), 0, [])

    def recent_runs(self, limit: int = 20) -> list[dict]:
        with self._managed_connection() as con:
            rows = con.execute("SELECT * FROM runs ORDER BY id DESC LIMIT ?", (max(1, min(limit, 100)),)).fetchall()
        return [dict(row) for row in rows]