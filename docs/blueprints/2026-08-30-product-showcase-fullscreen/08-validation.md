# Architecture Validation

## Verdict

**PASS WITH WARNINGS**

The architecture is safe to implement. The warnings are delivery evidence gaps, not unresolved design decisions: the current 980×700 assets are too small for the intended presentation, and production Harness plugin execution is not yet a shipping capability. Both are explicitly gated in the roadmap.

## 25-Point Check

### Scalability

| Check | Result | Evidence |
|---|---|---|
| S1 — Frequently queried columns indexed | Pass — not applicable | No persisted entity or query is added. Existing edition/query models are unchanged. |
| S2 — No N+1 query pattern | Pass — not applicable | Focus/fullscreen state is local presentation state; the evidence manifest is read once at build time. |
| S3 — Cache strategy for high-read data | Pass | Static media uses versioned filenames/cache keys; the high-quality master is outside the critical path and web derivatives are cacheable. |
| S4 — Application tier stateless | Pass | No server state is added. Window/reader state is process-local UI state and evidence metadata is version-controlled. |
| S5 — Horizontal scaling path | Pass — not applicable | This is a single-owner local desktop product and static campaign; no shared service tier is introduced. Static derivatives may be placed behind the existing host/CDN. |
| S6 — Long-running work asynchronous | Pass | Capturing and rendering are offline build/release work. Runtime focus/fullscreen operations are non-blocking UI transitions. |

### Security

| Check | Result | Evidence |
|---|---|---|
| SEC1 — Authentication on non-public endpoints | Pass — not applicable | No endpoint is added. The native bridge remains restricted to the trusted bundled WebView. |
| SEC2 — Authorization enforced | Pass | Window authority remains in the Swift host; web content receives only an enum request port and cannot choose selectors, screens, levels, or windows. |
| SEC3 — Boundary input validation | Pass | Action literal, enum mode, and UUID are validated at the bridge boundary; malformed requests are rejected. |
| SEC4 — Sensitive data identified/encrypted | Pass | Voiceprints, raw audio, credentials, private documents, paths, and private URLs are prohibited from public evidence. Existing product encryption/storage is unchanged. |
| SEC5 — Secrets management | Pass | No secret or new credential is introduced. The manifest forbids local paths and diagnostics containing secrets. |
| SEC6 — Auth rate limiting | Pass — not applicable | No authentication endpoint or network request is added. Bridge transition de-duplication prevents rapid conflicting native calls. |

### Maintainability

| Check | Result | Evidence |
|---|---|---|
| M1 — Conventional folder structure | Pass | Changes remain within existing `desktop/`, `web/`, `marketing-site/`, `marketing-video/`, tests, and blueprint locations. |
| M2 — Separation of concerns | Pass | Web owns reader state, Swift owns AppKit window state, backend owns content, and build tooling owns evidence validation. |
| M3 — No circular dependencies | Pass | Product emits direct evidence to the publication pipeline; campaign/film never call back into the product runtime. Swift reports state to web without owning reader content. |
| M4 — Configuration externalized | Pass | Capture dimensions, publication ceilings, revision, and claim status live in the versioned evidence manifest; render commands remain in package configuration. |
| M5 — Logging strategy | Pass | Fullscreen transition timing/failure and build evidence checks are logged without content, biometric, document, or private URL data. |
| M6 — Actionable errors | Pass | The four fullscreen error codes specify recovery behavior; manifest errors name the asset, failed field, and expected constraint. |

### Performance

| Check | Result | Evidence |
|---|---|---|
| P1 — Critical latency targets | Pass | Reader state settles within 100 ms, native requests acknowledge within 100 ms before system animation, and campaign p75 LCP target is below 2.5 s. |
| P2 — DB connection pooling | Pass — not applicable | No database or server request is added. |
| P3 — Pagination on list endpoints | Pass — not applicable | No list endpoint is added; existing intelligence archive/capability pagination contracts remain unchanged. |
| P4 — Static delivery strategy | Pass | Responsive 1×/2× WebP/AVIF, explicit dimensions, metadata preload for offscreen clips, click-to-play film, cache keys, and 1440p/1080p variants are specified. |

### Consistency

| Check | Result | Evidence |
|---|---|---|
| C1 — Naming conventions | Pass | Runtime and manifest fields use camelCase; enum values and action names are fixed and consistent with the existing JavaScript bridge. |
| C2 — Uniform error response | Pass | All fullscreen failures use the same native state-event shape with `mode`, `requestId`, `reason`, and sanitized `error`; build errors use one manifest validator format. |
| C3 — Timestamp consistency | Pass | Manifest and runtime contracts specify UTC ISO-8601 timestamps. |

## Warnings and Resolutions

### W1 — Current evidence is under-resolution

- Evidence: existing direct captures are approximately 980×700 and are currently shown at up to 1110–1160 film pixels; this creates visible softness before encoding.
- Risk: publishing layout/film changes without new captures would preserve or worsen the user's reported blur.
- Resolution: Milestone 3 records direct 1960×1400-or-larger product masters; Milestones 4–5 enforce no-upscale ceilings; Milestone 6 makes the validator blocking.

### W2 — Harness production plugin execution is not yet shipping

- Evidence: the current Harness blueprint exposes readiness but keeps generated/imported production execution disabled.
- Risk: a generic “MERRICK writes and runs its own plugins” claim would overstate current behavior.
- Resolution: show the shipping extension inventory, diagnostics, provenance, permissions, and durable management as direct proof. Label generated/imported execution `preview` or `planned` until that separate milestone passes. The manifest validator rejects a false `shipping` status.

### W3 — Authentic voice and biometric demo require human privacy approval

- Evidence: the final public media must use the actual product voice while excluding a real user's biometric template and private utterances.
- Risk: a technically correct capture can still expose sensitive or unapproved identity material.
- Resolution: Milestone 3 uses a consented demonstration identity and requires `privacyReview=approved`; Milestone 6 blocks publication without the review.

## Quality Gate

All 25 architecture checks pass or are explicitly non-applicable to this no-database, no-new-endpoint change. The three warnings have owners, blocking controls, and assigned milestones.

**Implementation may begin.** Public promotion of the replacement assets may not begin until W1–W3 are resolved by Milestones 3 and 6.
