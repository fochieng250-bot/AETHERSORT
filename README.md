# AetherSort 0.3.0-beta.1 — Windows Beta Packaging Preview

A local-first desktop file organizer. This is a public-beta packaging preview, not a production-certified commercial product. Please test it with disposable files before using it on important folders.

## Included

- Native desktop UI built with PySide6, with a product icon.
- Select a folder, scan it, and preview actions before moving anything.
- Categorize common document, image, audio, video, archive, and code formats.
- Only scans regular files directly inside the selected folder. Subfolders are intentionally left untouched.
- Never intentionally overwrites a destination. Conflicting names are assigned a numbered filename; byte-identical files are skipped.
- Local SQLite operation history and an Undo Last Run action.
- SQLite write-ahead logging and a recovery journal that attempts to reverse moves interrupted by an application/process crash.
- Core tests for preview scope, duplicate handling, no-overwrite behavior, Undo, and interrupted-run recovery.
- Windows PyInstaller build configuration, Inno Setup installer definition, and Windows CI workflow.

## Run from source on Windows

1. Install Python 3.11 or newer.
2. Open PowerShell in this directory.
3. Run `setup_windows.bat` or use these commands:

   ```powershell
   py -3.11 -m venv .venv
   .\.venv\Scripts\Activate.ps1
   python -m pip install --upgrade pip
   pip install -e .
   python run_aethersort.py
   ```

## Run tests

```powershell
py -3.11 -m unittest discover -s tests -v
```

## Build the Windows application

Build on Windows; PyInstaller is not a cross-compiler. From PowerShell:

```powershell
Set-ExecutionPolicy -Scope Process Bypass
.\build_windows.ps1
```

The script installs build dependencies, runs tests, creates the onedir application in `dist\AetherSort`, copies the beta documents, and generates a SHA-256 checksum for `AetherSort.exe`.

To create a Windows installer:

1. Install [Inno Setup](https://jrsoftware.org/isinfo.php) on the Windows build machine.
2. Run `installer\AetherSort.iss` in Inno Setup Compiler, or run `installer\build_installer.ps1`.
3. Test install, launch, upgrade-over-previous-version, and uninstall on a clean Windows account before sharing the installer.

The installer is configured for per-user installation. The beta is not code-signed; Windows SmartScreen may show a reputation warning. The checksum detects accidental changes but does not establish publisher identity.

## Safety boundaries

- Test with a disposable sample folder first. Keep independent backups of important files.
- Preview is required before every organize operation.
- The app does not recurse into subfolders, delete files, or intentionally overwrite conflicting files.
- Undo is best-effort and refuses to overwrite an occupied original path. If a filesystem or process failure occurs, inspect the selected folder and the error message before retrying.
- SQLite history is stored in the user's application-data directory, not beside the selected files.
- Recovery cannot guarantee safety after disk failure, sudden power loss, filesystem corruption, or external changes. Backups remain necessary.

## Privacy and legal documents

See `PRIVACY_POLICY.md`, `EULA.md`, and `SUPPORT.md`. These are beta drafts, not a substitute for legal review. This build contains no accounts, subscription/payment code, analytics, intentional telemetry upload, or automatic updater.
