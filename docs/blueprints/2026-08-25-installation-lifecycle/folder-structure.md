# Ownership and Packaging Layout

```text
desktop/
  Info.plist                  # Dock/Launch Services identity and privacy usage text
  MerrickApp.swift             # lifecycle gate, native window and backend owner
scripts/
  build-macos-app.sh          # signed self-contained bundle
  package-macos-app.sh        # DMG drag-to-Applications image
tests/
  test_desktop_lifecycle.py   # source-level lifecycle contracts
docs/blueprints/2026-08-25-installation-lifecycle/
                              # decision and verification record
```

Application Support remains the sole location for mutable user state. The `.app` bundle is read-only after signing; the DMG/staging directory is never treated as runtime data.
