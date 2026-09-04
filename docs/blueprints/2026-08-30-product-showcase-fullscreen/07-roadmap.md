# Development Roadmap

Every milestone ends in working, reversible software. Public marketing assets are not promoted until their evidence checks pass.

## Milestone 0 — Contracts and Regression Harness [MVP] (Day 1)

Goal: The repository can mechanically detect incomplete capability coverage and low-resolution/upscaled product evidence before publication.

Tasks:

- [ ] Add source-level and behavior tests for the bounded fullscreen bridge request and native state callback.
- [ ] Add a versioned evidence-manifest schema and validator.
- [ ] Inventory current site and film claims against the eight capability ids.
- [ ] Report source dimensions, target CSS/film dimensions, upscaling ratio, audio stream presence, poster luminance, privacy status, and shipping status.
- [ ] Keep the validator advisory until the current asset debt is recorded, then turn it into a release gate in Milestone 5.

Deliverable: A reproducible report that identifies every missing proof and every asset enlarged beyond its source pixels.

Testing: Unit tests for manifest parsing, missing asset references, low-resolution rejection, false shipping claims, silent video declarations, and black-poster detection.

Rollback: Remove the advisory script and manifest without affecting the product runtime.

## Milestone 1 — Newspaper Focus Reader [MVP] (Days 1–2)

Goal: A user can open a substantial edition in a calm, full-viewport reading layout inside the existing product window.

Tasks:

- [ ] Add the `Focus Reader` control to an actual rendered intelligence edition.
- [ ] Implement the `closed` / `organizer` / `newspaper-focus` state transitions.
- [ ] Preserve edition selection, scroll position, and keyboard focus across entry/exit.
- [ ] Remove non-reader chrome while keeping a compact edition toolbar.
- [ ] Implement wide, medium, and narrow editorial layouts without clipping text or stretching images.
- [ ] Add Escape handling, accessible labels, live status, and reduced-motion behavior.

Deliverable: The existing newspaper can be read edge-to-edge within the window and returns cleanly to the organizer.

Testing: DOM/unit tests for legal transitions and focus restoration; responsive browser screenshots at wide, medium, and narrow viewports; keyboard-only smoke test.

Rollback: Hide the focus-reader entry control; the existing organizer and edition rendering remain unchanged.

## Milestone 2 — Native macOS Fullscreen [MVP] (Days 2–3)

Goal: The MERRICK window enters and exits real macOS fullscreen from both the UI and the standard system shortcut.

Tasks:

- [ ] Add the whitelisted `setWindowFullscreen` bridge action with strict mode and UUID validation.
- [ ] Implement the AppKit fullscreen coordinator and delegate-driven state machine.
- [ ] Store and restore floating-window level and collection behavior.
- [ ] Mirror native transition state to the web UI using safely encoded callbacks.
- [ ] Make repeated or conflicting requests idempotent and keep focus reader available if native fullscreen fails.
- [ ] Expose a clear `Full Screen` / `Exit Full Screen` product control.

Deliverable: A real product newspaper shown in macOS fullscreen, with normal floating HUD behavior restored after exit.

Testing: Swift/source contract tests; manual Control-Command-F verification; entry/exit loop; Space change; Escape from focus reader; failure fallback.

Rollback: Remove the bridge action and button; web-only focus reader continues to work.

## Milestone 3 — Authentic 2× Product Evidence [V1] (Days 3–4)

Goal: The running product supplies privacy-approved, high-density evidence for every currently shipping campaign claim.

Tasks:

- [ ] Prepare deterministic demonstration data for conversation, voice identity, multi-page research, Mac actions, documents/memory, newspaper, and extension manager.
- [ ] Record the real listening/turning/speaking product state with the consented authentic MERRICK voice and no background music.
- [ ] Capture direct 1960×1400-or-larger stills and footage from the running 7:5 product window.
- [ ] Capture research with the synthesis and at least three source pages/cards visible.
- [ ] Capture the full newspaper in focus reader and plugin/skill manager with provenance, permissions, and export/import durability visible.
- [ ] Generate responsive WebP/AVIF derivatives while retaining lossless masters.
- [ ] Populate hashes, dimensions, privacy review, product revision, and shipping status in the evidence manifest.

Deliverable: A complete, auditable evidence set with no synthesized substitute for a claimed product screen.

Testing: Manifest validation, privacy review, visual inspection at 100% and 200%, audio identity review, and comparison with the running product revision.

Rollback: Continue serving the previous approved campaign assets; do not publish partial new evidence.

## Milestone 4 — Complete Marketing Story [V1] (Days 4–5)

Goal: The website visibly explains the whole system with coherent scroll order and correctly sized real product evidence.

Tasks:

- [ ] Rebuild the capability chapters in the specified mental-model order.
- [ ] Add full proof chapters for voice identity, multi-page research, and plugin/skill extensibility.
- [ ] Replace oversized empty frames with intrinsic-ratio media containers.
- [ ] Bind chapter copy to pinned evidence without continuous screenshot rotation.
- [ ] Use 1×/2× responsive sources and enforce manifest `maxCssWidth`.
- [ ] Preserve the dark visual system across every section.
- [ ] Add reduced-motion and non-JavaScript fallbacks.

Deliverable: A desktop and mobile campaign in which all eight capability areas are discoverable, readable, and backed by actual product evidence.

Testing: Automated proof-coverage check; browser screenshots at common desktop/mobile sizes and DPR 1/2; scroll-order QA; image completeness and crop audit; accessibility scan.

Rollback: Keep the current campaign route available behind a versioned asset reference until the replacement passes release review.

## Milestone 5 — High-Resolution System Film [V1] (Days 5–6)

Goal: A 1440p system walkthrough shows the actual product end to end with authentic voice, legible type, and no enlarged source pixels.

Tasks:

- [ ] Replace reconstructed or under-resolution proof scenes with approved Milestone 3 footage.
- [ ] Cover listening/speaking, voice identity, multi-page research, newspaper creation, scoped Mac action, and durable extensions.
- [ ] Remove background music and retain authentic product interaction audio.
- [ ] Normalize captions for fullscreen viewing and keep UI labels readable.
- [ ] Render the 2560×1440 master at CRF 15–16 plus a 1920×1080 web fallback.
- [ ] Generate a non-black poster from a meaningful real product frame.
- [ ] Validate every composition frame against source dimensions.

Deliverable: A complete high-resolution system film and web fallback with transcript/captions.

Testing: Automated metadata and scale audit; frame sampling for black/cropped frames; audio-stream and loudness inspection; full-duration visual and narrative review.

Rollback: Keep the current film addressable but do not set it as the campaign default until the new render passes.

## Milestone 6 — Cross-surface Release Gate [V1] (Days 6–7)

Goal: Product fullscreen, campaign, and film ship as one truthful, verified release.

Tasks:

- [ ] Turn evidence validation from advisory into a failing release check.
- [ ] Run desktop build/tests and repeated fullscreen entry/exit scenarios.
- [ ] Run browser visual QA against all capability chapters and breakpoints.
- [ ] Verify the campaign and film make no `shipping` claim for preview/planned Harness execution.
- [ ] Verify direct evidence matches the recorded product revision and all privacy approvals are current.
- [ ] Publish the new asset version and remove obsolete active references without destroying recoverable source masters.

Deliverable: A release candidate where the actual fullscreen product, the marketing narrative, and the film agree feature-for-feature.

Testing: Full product regression suite, evidence validator, campaign browser suite, film audit, keyboard/accessibility review, and a signed release checklist.

Rollback: Repoint the campaign manifest and film source to the previous approved release; product focus mode and native fullscreen can be independently disabled at their visible entry points.

## Dependency and Parallelism Notes

- Milestone 0 starts first and defines the release truth source.
- Milestone 1 can begin after the presentation-state tests exist.
- Milestone 3 depends on Milestones 1–2 because the full newspaper must be captured from the finished fullscreen product.
- Marketing layout work may proceed with dimension-preserving placeholders, but publication waits for Milestone 3 evidence.
- Film assembly may proceed after the shot list is fixed, but the final render waits for approved direct captures.
- No milestone requires a backend schema migration or a new cloud service.

## Definition of Done

- The newspaper works in both focus reader and native macOS fullscreen.
- Voice identity, multi-page research, and plugin/skill extensibility are visibly explained on the site and in the film at their truthful release status.
- All direct product visuals meet the 2× source requirement and are never enlarged.
- The film has authentic product audio, no background music, a visible first frame, and a 1440p master.
- Every public claim resolves to an approved evidence-manifest proof.
