# AetherSort 0.3.0-beta.1 Release Notes

## Focus: Windows beta packaging

- Added a Windows PyInstaller onedir build specification.
- Added a Windows PowerShell build script that runs the test suite before packaging.
- Added an Inno Setup installer definition for per-user installation without administrator privileges.
- Added a product icon and Windows CI workflow for tests and packaging.
- Added draft beta privacy notice, EULA, and support guidance.
- Added SHA-256 checksum generation for the main executable in local Windows builds.

## Existing behavior retained

- Preview before moving files.
- No recursive sorting of subfolders.
- Avoid intentional overwrites and rename conflicting destinations.
- Skip byte-identical duplicates.
- Local operation history, Undo, and best-effort interrupted-run recovery.

## Beta limitations

- Not code-signed; Windows SmartScreen may warn.
- Installer generation requires Inno Setup to be installed on the build machine.
- The GUI/package must be tested on a clean Windows installation before broad distribution.
- No subscription, payment, telemetry, or auto-update system is included.
