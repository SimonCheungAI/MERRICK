# Requirements

## Phase 0 — Feasibility

Complexity: **Moderate**. The change crosses the macOS application lifecycle, Launch Services, the bundled loopback service, distribution packaging, code signing and user-facing recovery. Estimated effort: 1–2 small vertical slices. Verdict: **PROCEED**.

Evidence from the affected Mac: an installed-image copy was running with the backend on `127.0.0.1:8765`; launching a second build copy started a second native host, whose backend exited with status 3 because that port was occupied. The app was marked `LSUIElement=true` and set to the accessory activation policy, so the already-running copy was not discoverable through normal Dock behavior.

## Functional requirements

- FR-01: MERRICK appears as a normal macOS application in the Dock and Application Switcher while running.
- FR-02: Launching any second copy with the MERRICK bundle identifier focuses the already-running MERRICK window and exits the new host before it starts a backend. This redirect must run in native code rather than relying on silent Launch Services multiple-instance rejection.
- FR-03: The first instance alone owns port 8765 and all child processes.
- FR-04: A Finder, Dock, Spotlight, or `open` launch always makes the MERRICK window visible and active.
- FR-05: A startup failure remains visibly actionable, identifies the local category, and points to a local diagnostic log; it must never leave an invisible process.
- FR-06: The DMG continues to contain a drag-to-Applications flow and must not carry user state, credentials or memory.
- FR-07: Closing the MERRICK window still means a complete quit and child-process cleanup.

## Non-functional requirements

- NFR-01: Duplicate-instance detection completes before `buildWindow`, permission prompts, backend spawn or OpenClaw startup.
- NFR-02: Normal reopen/focus takes under 250 ms after Launch Services delivers the event.
- NFR-03: Lifecycle state/logging is local, contains no provider credential, transcript, document content or memory.
- NFR-04: Source and packaged builds retain their current first-run provider setup and private Application Support paths.

## Constraints and assumptions

- macOS is the only target in this slice; macOS Launch Services and `NSRunningApplication` are authoritative for local app discovery.
- A user may legitimately have a DMG/staging copy and an Applications copy. Same bundle identifier means one active MERRICK, not one instance per path.
- Developer-ID signing/notarization is a separate distribution release gate; this slice preserves ad-hoc local development signing.
- No background-helper process is introduced; one native host owns the lifecycle.

## Resolved decisions

- Q: Should the transparent HUD remain an accessory-only app? **No.** It should remain a transparent/floating window but participate normally in Dock/Command-Tab so it is findable and relaunchable.
- Q: Should a second copy select a random backend port? **No.** It should focus the first copy. Multiple isolated instances would share Application Support state and create unsafe duplicate audio/voice sessions.
