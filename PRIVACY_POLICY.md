# AetherSort Privacy Notice (Beta)

**Effective date:** 13 October 2026  
**Status:** Draft for the public beta; review before commercial distribution.

## What this beta does

AetherSort is designed to organize files locally on your computer. In this beta, the application does not include analytics, advertising, account sign-in, subscription processing, or an intentional telemetry upload feature.

## Files and local history

When you use AetherSort, it reads the names and file contents needed to categorize files and compare file hashes for duplicate detection. When you confirm an organization run, it moves selected files into category folders under the folder you selected. The app stores a local SQLite operation history in your operating system's per-user application-data directory so it can offer Undo and attempt recovery after an interrupted run.

AetherSort does not intentionally upload your files or operation history. Your operating system, security software, cloud-synced folders, or other software may separately process files according to their own settings.

## Your choices and responsibilities

- You choose the folder and confirm the proposed organization before files are moved.
- You can stop using the app at any time.
- Keep independent backups of important files. Undo and crash recovery are safeguards, not a replacement for backups.
- You can remove local history by closing AetherSort and deleting its `history.sqlite3` database and associated SQLite `-wal` / `-shm` files from the AetherSort folder inside your per-user application-data directory. Doing so removes Undo history and pending recovery records; do not delete these while a run is in progress.
