# Delivery Roadmap

## M1 — Reliable visible launch (MVP)

Goal: a Finder/Dock click reliably reveals one MERRICK instance.

- Change the app from accessory-only to regular application activation.
- Add an early same-bundle duplicate-instance redirect.
- Add source-characterization tests for both contracts.

Deliverable: clicking a second copy focuses the first and never starts a second backend.

Testing: unit/source contract tests; build bundle; launch application and verify only one listener exists.

## M2 — Installer and recovery clarity (V1)

Goal: a new user understands how to install and recover without Terminal.

- Improve DMG presentation with a drag-to-Applications instruction asset if needed.
- Make native startup errors identify port/runtime failures and point to diagnostics.
- Add post-build bundle validation for icon, executable, runtime, signature and plist lifecycle keys.

Deliverable: install can be completed solely through Finder; startup failures are visible and actionable.

Testing: clean-user account/VM test before broad distribution; Developer ID notarization as release gate.
