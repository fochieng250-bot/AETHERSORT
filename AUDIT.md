# Audit of the supplied `aether_sort.py`

## High-risk correctness issues identified

1. `sort()` iterates over `target_path.rglob("*")` while it creates category directories and moves files into them. The traversal is not a fixed plan, so newly created folders and moved files can be encountered during the same run.
2. The backup directory and logs are placed beside the source script rather than in per-user application data. The backup exclusion compares string prefixes, which can match unrelated paths and is not a safe path containment check.
3. `handle_duplicate(..., mode="overwrite")` returns the existing destination. `shutil.move()` may replace it, so unrelated data can be lost.
4. `restore_latest_snapshot()` copies files back but does not remove post-snapshot files, so it is not a true rollback. The snapshot is also created before sorting without robust completion verification.
5. The required `aether_config.json` is not included in the upload, so the script cannot start as provided.
6. The JSON log is read and rewritten as a whole. Invalid JSON or an interrupted write can prevent future operations or damage history.
7. `_hash_file()` exists but is not used to determine whether duplicate files have identical content.
8. The code does not provide a GUI, packaged build, automated tests, licensing, update mechanism, or subscription system.

## Changes in the 0.1 MVP

- Separated the engine from the GUI.
- Scans only direct files in the chosen folder; leaves nested folders untouched.
- Builds a preview before changes and asks for confirmation.
- Skips symbolic links and non-files.
- Detects identical content with SHA-256 and never intentionally overwrites a destination.
- Uses numbered names for conflicting, non-identical files.
- Stores run history in a per-user SQLite database.
- Includes a best-effort undo for the last completed run.
- Adds unit tests for core behavior.

## Known limitations before public release

- The GUI has not been run on Windows in this build environment; PySide6 is a runtime dependency.
- Undo is best-effort, not a guarantee against hardware failure or abrupt power loss.
- The operation journal needs stronger crash recovery before public beta.
- No code signing, installer, auto-updater, telemetry, payment integration, or license enforcement is included.
- Manual acceptance testing on supported Windows versions is still required.


## 0.2.0 reliability changes

- Added a SQLite operation journal that records intent before each move and marks completion afterward.
- Enabled SQLite WAL and FULL synchronous mode for stronger database durability (not a substitute for backups or a transactional filesystem).
- On startup, checks runs left in `running` state and attempts to restore files to their original paths without overwriting conflicts.
- Shows a startup recovery report if an interrupted run is detected.
- Refuses execution when the preview contains scan errors and rechecks source/destination state before each move.
- Added regression tests for interrupted-run recovery and stale-preview destination conflicts.

## Remaining 0.2.0 risks

- A crash between a filesystem move and journal completion is handled by inspecting source/destination paths, but external changes can make recovery ambiguous.
- Cross-volume moves can have different interruption characteristics; Windows acceptance tests are required.
- UI operations still need progress/cancellation work, and subscription/licensing/installer features are not included.

## 0.3.0-beta.1 packaging work

Added a Windows PyInstaller onedir specification, product icon, PowerShell build scripts, Inno Setup per-user installer definition, Windows CI workflow, beta privacy notice, draft EULA, support guidance, and release notes. The Windows build script runs the unit tests before creating a packaged application and writes a SHA-256 checksum for the main executable.

**Important validation boundary:** the source and engine tests were validated in this environment, but a Windows executable and installer have not been built or launched here. The user must build on Windows and test the app and installer on a clean Windows account. The beta is not code-signed, and the legal documents need review before commercial distribution.
