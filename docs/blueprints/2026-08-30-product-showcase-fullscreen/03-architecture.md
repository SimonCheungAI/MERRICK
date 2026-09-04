# Phase 2 — Architecture

## Selected pattern

Extend the accepted **local modular monolith with typed native contracts**. Do not add a service, database, frontend framework, or cloud dependency.

The desktop WebView owns presentation state, the Swift host owns macOS window authority, the Python backend continues to own intelligence content, and the marketing/media pipeline consumes redacted direct-capture artifacts. This preserves current trust boundaries while giving each fullscreen state one owner.

## Component map

```text
Shipping MERRICK product

  Existing Python intelligence / voice / capability services
                 │ existing versioned WebSocket snapshots
                 ▼
  web/index.html + web/app.js + web/style.css
  ├─ Organizer / complete intelligence edition
  ├─ Newspaper Focus Controller (new, presentation-only)
  ├─ Research / sources / voiceprint / capability surfaces
  └─ Native Window Request Port (new, 3-command allowlist)
                 │ trusted WKScriptMessage: enter | exit | toggle
                 ▼
  desktop/MerrickApp.swift
  └─ Native Fullscreen Coordinator (new)
     ├─ owns NSWindow transition
     ├─ emits fullscreen state back to WebView
     └─ preserves HUD frame/level/collection behavior

Direct-capture / publication pipeline

  Running shipping product in deterministic showcase state
                 │ redacted 2× capture (1960×1400 minimum)
                 ▼
  High-DPI evidence masters + evidence manifest
        ├───────────────┬────────────────────┐
        ▼               ▼                    ▼
  marketing-site/   marketing-video/   automated media audit
  responsive proofs Remotion scenes    size/DPR/no-upscale checks
        │               │
        └──── public 1440p film + 1080p fallback/poster
```

## Responsibility boundaries

| Component | Owns | Must not own |
|---|---|---|
| Web Newspaper Focus Controller | Focus-mode DOM state, focus trap, Escape precedence, scroll/focus restoration | Native window geometry, model/backend state |
| Native Fullscreen Coordinator | AppKit fullscreen transition, window collection behavior, state notification | Newspaper selection, article content, arbitrary JavaScript |
| Intelligence backend | Complete edition data and source references | Window/fullscreen state |
| Marketing site | Accessible capability narrative and responsive direct-product proofs | Product authority or invented capability output |
| Remotion film | Timed presentation of evidence masters and authentic voice | Reconstructed substitutes labelled as direct captures |
| Evidence manifest/audit | Capability-to-proof mapping, source dimensions, privacy review, display-size ceiling | Runtime UI behavior |

## Technology decisions

| Layer | Choice | Rationale |
|---|---|---|
| Native window | Existing Swift/AppKit `NSWindow` | Only the native host can reliably own macOS fullscreen behavior |
| Product UI | Existing semantic HTML/CSS/vanilla JavaScript | Avoid a frontend migration and preserve bundled offline HUD |
| Backend | Existing Python/FastAPI/WebSocket | No new content contract is required |
| Marketing | Existing static HTML/CSS/JavaScript | Keeps local/file hosting and simple public deployment |
| Film | Existing React + Remotion 4.0.518 | Current composition and voice pipeline already work |
| Master media | High-DPI PNG/JPEG and high-resolution H.264/ProRes master | Keeps fine UI text legible before web encoding |
| Web film | 2560 × 1440 H.264, CRF 15–16, yuv420p, AAC voice | Retina-friendly delivery while remaining browser compatible |
| Validation | Existing Node/Python tooling plus metadata/DOM assertions | No production dependency added |

## Fullscreen state model

The states are orthogonal:

```text
windowMode: normal | entering | fullscreen | exiting
readerMode: closed | organizer | newspaper-focus
```

Valid combinations include `normal + newspaper-focus` and `fullscreen + organizer`. A native transition failure changes only `windowMode`; the reader remains usable. Escape is handled in this order:

1. close an active subordinate dialog/editor;
2. exit newspaper focus mode;
3. allow macOS to exit native fullscreen;
4. otherwise preserve existing HUD behavior.

## Key flow A — read a newspaper fullscreen

1. The owner opens Personal Assistant → Intelligence and selects an edition.
2. `renderIntelligenceEdition` renders the complete existing edition and a labelled “Focus reader” control.
3. The Focus Controller stores the invoking element and current edition scroll position, sets `readerMode=newspaper-focus`, and focuses the edition heading.
4. The owner may independently press the native fullscreen control. JavaScript posts `{action: "setWindowFullscreen", mode: "toggle"}` through the existing signed/validated bridge.
5. Swift accepts only the three enumerated modes, updates collection behavior, calls AppKit fullscreen APIs on the main thread, and reports the resulting state.
6. CSS gives the edition the full WebView: one readable page column at smaller widths; editorial columns and source desk expand at wide widths.
7. Escape exits focus mode first and restores focus/scroll. A later Escape or `Control–Command–F` leaves native fullscreen without discarding the selected edition.

## Key flow B — produce truthful high-resolution marketing proof

1. Run the shipping product with a privacy-safe fixture/demo profile and open a real target surface: multi-page Research Display, Voiceprint Vault status sequence, Skills/plugins manager, or complete newspaper.
2. Capture at `1960 × 1400` or greater with a documented backing scale. Redact or replace private identifiers before capture; do not blur them after publication if the source can be made safe.
3. Record dimensions, product revision, capture state, privacy review, and intended maximum CSS/film size in an evidence manifest.
4. The marketing site uses 2× image/video sources and never renders beyond the manifest ceiling.
5. Remotion scenes use `contain` or exact aspect-ratio layouts and never enlarge the evidence master. Explicit callouts show multiple sources, plugin readiness, and owner verification without covering essential product content.
6. Render a high-quality master, then a 1440p browser-compatible film and matching poster. Media audit rejects missing posters, wrong ratios, low-DPI sources, and accidental soundtrack tracks.

## Marketing information architecture

The capability story is ordered by the user's mental model, not backend module order:

1. **Presence and conversation** — actual listening/speaking motion and voice.
2. **Identity and privacy** — voiceprint enrolment, owner verification, private-memory gate.
3. **Research** — query → returned pages → page reading → synthesis → inspectable sources.
4. **Native production** — safe Mac actions and bounded workspace work.
5. **Knowledge and operations** — documents, memory, meetings, projects, reminders.
6. **Intelligence publication** — complete newspaper and fullscreen reader.
7. **Extensibility** — models, Skills, plugins, diagnostics, and current Harness readiness.
8. **Control boundary** — explicit authority and safe refusal behavior.

Every visual chapter links to the corresponding capability-atlas entries. Text remains useful when autoplay or video decoding is unavailable.

## Security architecture

- The existing trusted bridge token/origin validation remains mandatory.
- The fullscreen message accepts one action name and an enum; it carries no code, selector, URL, path, or window identifier.
- Web content cannot choose a screen, elevate window level, or create another window.
- Voiceprint marketing proof uses synthetic/demo status only; no template, embedding, raw waveform, or private audio is published.
- Capability marketing proof shows redacted names/versions and readiness; it never publishes local paths, grants, diagnostics containing secrets, or user plugin source.
- The marketing site remains static and cannot call the local product backend.

## Scalability and performance

- This is a single-owner local product; no multi-user scaling change is required.
- Focus mode is a CSS/DOM state change and adds no backend load.
- Only one high-resolution loop should autoplay in the viewport at a time; IntersectionObserver pauses offscreen proof clips.
- The system film uses an explicit poster and click-to-play. Short chapter clips use metadata preload and efficient H.264 delivery variants.
- Keep one high-quality master outside the critical website path; serve an optimized web derivative with a stable cache key.

## Failure containment

- If native fullscreen fails, restore the normal window and report state; do not close or reload the WebView.
- If a 2× capture is absent, the associated website proof renders at a smaller safe size with a labelled text fallback; it is never upscaled.
- If a clip fails to decode, its poster and full capability text remain available.
- If an edition is missing or malformed, focus mode is not offered and the existing empty/error state remains.
- If Harness capabilities are not production-ready, the marketing panel says “readiness” and does not imply code generation/activation is shipping.

## Target change locations

```text
desktop/MerrickApp.swift                  native fullscreen coordinator + bridge case
web/index.html                           fullscreen/focus controls and live regions
web/style.css                            native-state affordance + newspaper focus layout
web/app.js                               reader state machine, focus/escape, bridge request
marketing-site/index.html                complete capability chapters/proofs
marketing-site/styles.css                high-DPI no-upscale presentation
marketing-site/script.js                 offscreen media lifecycle and proof interactions
marketing-video/src/scenes/              voiceprint/research/extension/newspaper scenes
marketing-video/package.json             master + 1440p web render commands
marketing-site/media/                    reviewed 2× direct captures and film derivatives
docs/blueprints/.../                      contracts, evidence rules, roadmap, validation
```
