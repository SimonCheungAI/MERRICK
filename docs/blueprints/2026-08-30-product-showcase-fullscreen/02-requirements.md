# Phase 1 — Requirements

## Goal

Make the public website and system film accurately demonstrate the complete shipping MERRICK product, and add a real fullscreen reading experience to the desktop application so generated intelligence newspapers can be comfortably presented and read.

## Functional requirements

### Marketing site

- **FR-01 Complete capability narrative:** The site must visibly demonstrate conversation, owner voiceprint, multi-page research, source inspection, native Mac action, private documents/memory, personal operations, intelligence newspapers, model selection, and Skills/plugin management.
- **FR-02 Multi-page research proof:** A dedicated product sequence must show the query, at least three independently returned pages/source cards, reading/progress states, synthesis, and the inspectable URLs. It must not reduce the feature to one static answer screenshot.
- **FR-03 Extensibility proof:** A dedicated sequence must show the real Skills/plugins inventory, status/readiness, enable/disable controls, diagnostics, source/version information, and the boundary between immutable core capabilities and user-managed extensions.
- **FR-04 Voice identity proof:** A dedicated sequence must show Mac-authenticated vault unlock, four-second enrolment, owner verification, private-memory gate, and Watch Mode owner-only behavior. It must explain that raw enrolment audio is not retained.
- **FR-05 Newspaper proof:** The site must show an actual complete generated edition, including front page, metrics/data desk, stories, analysis, watchlist, citations, source desk, and archive context.
- **FR-06 Truthfulness:** Demonstrations must use direct captures of shipping product surfaces. Planned Harness generation/import features must be labelled as planned until their production milestone is complete.
- **FR-07 Capability index:** The complete capability atlas remains available as scannable text and mirrors the visible demonstrations.

### System film and media

- **FR-08 Complete film coverage:** The film must include explicit scenes for multi-page research, owner voiceprint, extension management, and full newspaper reading; no scene may imply a capability using only decorative UI.
- **FR-09 Authentic voice:** Product voice audio must use the real production voice. The film has no background music.
- **FR-10 High-DPI source capture:** New direct product captures must be recorded at a minimum of `1960 × 1400` for 7:5 product panels, or an equivalent 2× backing resolution. The 1920 × 1080 system film must never enlarge a source beyond its effective captured resolution.
- **FR-11 Web delivery variants:** Preserve a high-quality master and generate a web delivery asset. Posters must match film resolution and must not be derived from a low-resolution screenshot.
- **FR-12 Media fallback:** Autoplay clips remain muted and looped; every video has a meaningful poster/fallback image and accessible label.

### Desktop fullscreen

- **FR-13 Native fullscreen:** The desktop app exposes an explicit fullscreen toggle and the standard `Control–Command–F` behavior through the native window owner.
- **FR-14 Newspaper focus mode:** An open intelligence edition can enter a distraction-free reader that fills the available WebView. Composer, archive navigation, HUD controls, and unrelated organizer panels are hidden while reading.
- **FR-15 Exit paths:** Escape exits newspaper focus mode first. A visible close/restore control and an accessible button label are always present. Leaving native fullscreen does not lose the selected edition or scroll position.
- **FR-16 State separation:** Native window fullscreen and newspaper focus mode are independent states. Either may be used alone or together.
- **FR-17 Keyboard and focus:** Entering focus mode moves focus to the edition heading; leaving returns focus to the invoking control. Tab order remains bounded to the active modal surface.
- **FR-18 Edition navigation:** Focus mode preserves scrolling, citations/source-card actions, and the full generated edition structure.
- **FR-19 Safe native bridge:** JavaScript may request only `enter`, `exit`, or `toggle` fullscreen. The Swift host validates the command and never accepts arbitrary window selectors or scripts.

## Non-functional requirements

- **NFR-01 Fidelity:** Product media is captured from the running product. No reconstructed orb, fake search result, or invented plugin state is presented as direct product output.
- **NFR-02 Visual quality:** At target display size, raster/video sources provide at least 1.5 physical source pixels per device pixel; 2.0 is preferred for Retina screenshots.
- **NFR-03 Performance:** The marketing page keeps below-the-fold clips at `preload="metadata"`; a single system film may use `preload="auto"` only when the user initiates playback. Desktop focus mode adds no network request. Focus-reader DOM state must settle within 100 ms on supported Macs; the native control must acknowledge a request state within 100 ms before the system-owned animation; the campaign must keep 75th-percentile LCP below 2.5 s on the agreed production profile.
- **NFR-04 Accessibility:** WCAG AA contrast, visible focus, reduced-motion support, semantic headings, labelled media, and keyboard-only entry/exit are required.
- **NFR-05 Responsive behavior:** Marketing demonstrations remain readable from 390px mobile width through wide desktop. No capture is cropped unless the crop is an explicitly labelled detail view.
- **NFR-06 Reliability:** Fullscreen transitions are idempotent. Repeated requests and Escape during animation do not corrupt organizer or edition state.
- **NFR-07 Privacy:** Voiceprint status may be demonstrated, but biometric templates, raw audio, credentials, private documents, and personal source URLs never enter marketing assets.
- **NFR-08 Compatibility:** Existing WebSocket events and backend intelligence schemas remain backward compatible.

## Implicit requirements review

| Concern | Decision |
|---|---|
| Pagination | Existing intelligence archive behavior remains; no new server pagination is required for fullscreen. Capability inventory pagination stays governed by the Harness blueprint. |
| Error states | Missing/failed media shows a poster and text fallback. Fullscreen bridge failures leave the normal window usable and report a non-blocking status. |
| Email notifications | Out of scope. |
| Mobile | Marketing site supported; desktop fullscreen is macOS-only. |
| Admin panel | Out of scope; this is a single-owner product. |
| File uploads | Out of scope for this slice; future plugin package import remains in the Harness blueprint. |
| Audit logs | No new audit event for display-only fullscreen. Plugin mutations retain existing audit/readiness behavior. |
| Soft delete | Out of scope. Existing newspaper deletion semantics are unchanged. |

## Dependencies

- `desktop/MerrickApp.swift` owns native window state and bridge validation.
- `web/index.html`, `web/style.css`, and `web/app.js` own organizer, intelligence edition, focus state, keyboard behavior, and the fullscreen request.
- Existing organizer/intelligence snapshot events provide newspaper content; no new backend entity is required.
- Existing voice identity and capability inventory surfaces provide authentic website/film captures.
- `marketing-video/` owns the 1920 × 1080 Remotion composition and web film render.
- `marketing-site/` owns the public capability story and direct media delivery.

## Constraints and resolved conflicts

- The current HUD window is borderless and marked `.fullScreenAuxiliary`. Native fullscreen requires a host-owned transition to a primary fullscreen window behavior; JavaScript alone is insufficient.
- Existing `980 × 700` captures remain valid as low-resolution fallbacks but cannot be enlarged for the new film or wide website proofs.
- “Plugin extensibility” means real installed Skills/plugin management today. Generated/imported Harness plugins remain future-facing until implemented and validated under their separate blueprint.

## Open questions

No critical question blocks architecture. The working assumption is that both native fullscreen and an in-app newspaper focus mode are required.
