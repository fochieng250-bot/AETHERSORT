# AetherSort commercial roadmap

## Release 0.1 — Local MVP
- [x] Separate file engine from desktop UI
- [x] Preview before moving
- [x] Avoid recursive scanning and symlink following
- [x] Avoid overwrites; rename conflicting destinations
- [x] Skip byte-identical duplicates
- [x] SQLite run history and basic undo
- [x] Core unit tests
- [x] Manual user test of sorting and Undo reported successful
- [ ] Accessibility and keyboard-navigation review

## Release 0.2 — Reliability
- [x] Operation journal and startup recovery for interrupted runs
- [x] Tests simulating a crash after a move but before journal completion
- [x] Refuse execution when preview contains scan errors; revalidate stale destinations
- [ ] Interruption/recovery testing on Windows and across filesystem boundaries
- [ ] File metadata preservation checks, locked-file reporting, and permission diagnostics
- [ ] Settings UI for categories and exclusions
- [ ] Structured logs, diagnostics export, and Windows path edge-case tests
- [ ] Large-folder performance benchmarks and UI progress/cancellation

## Release 0.3.0-beta.1 — Windows beta packaging
- [x] PyInstaller onedir build configuration
- [x] Inno Setup installer definition
- [x] Product icon and Windows CI workflow
- [x] Draft privacy notice, EULA, release notes, and support guidance
- [x] Local build script runs tests before packaging and generates executable checksum
- [ ] Build and test the actual Windows executable on a clean Windows account
- [ ] Build and test installer/uninstaller with Inno Setup
- [ ] Code signing and signed release checksums
- [ ] Complete legal review and select official support contact
- [ ] Recruit 20–50 beta testers and track success/failure rates

## Release 1.0 — Monetization readiness
- Validate willingness to pay before choosing final prices.
- Keep useful core sorting free.
- Pro candidates: scheduled rules, advanced rule sets, duplicate reports, saved profiles, and richer history.
- Implement account/entitlement service only when product-market signal supports it.
- Use a reputable payment provider; keep secrets and subscription authority server-side.
- Publish clear renewal, cancellation, refund, data retention, and offline-use policies.

## Release gates
1. No known data-loss defect in supported test cases.
2. Preview and actual execution agree on destination and conflict handling.
3. Undo and interrupted-operation behavior are documented and tested.
4. Windows artifacts are tested on clean machines and signed before broad distribution.
5. Real user feedback demonstrates repeat use and willingness to pay.
