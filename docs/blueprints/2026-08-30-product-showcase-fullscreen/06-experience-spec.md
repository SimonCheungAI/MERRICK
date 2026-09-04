# Experience Specification

## Design Intent

The product and its campaign should feel like the same intelligence seen at different scales. Product evidence stays visually literal: real MERRICK chrome, real states, readable content, and restrained framing. Motion explains state changes; it does not decorate screenshots.

## Product: Native Fullscreen

### Entry points

- A labeled `Full Screen` control sits in the organizer's persistent top bar.
- The control uses the existing icon language, includes an accessible name, and displays the current state.
- Control-Command-F continues to behave as a normal macOS fullscreen command.
- A failed native transition leaves the organizer usable and explains that focus reading remains available.

### Transition

- The button enters a pending state until the AppKit delegate confirms fullscreen.
- The UI does not scale, rotate, or fake a zoom while macOS animates the window.
- The floating HUD level is temporarily removed for native fullscreen and restored on exit.
- The control changes to `Exit Full Screen` only after confirmation.

## Product: Newspaper Focus Reader

### Entry and exit

- An edition-level `Focus Reader` control is visible beside the newspaper date/actions.
- Entry preserves the selected edition and scroll position, then focuses the newspaper heading.
- `Escape`, `Close Reader`, or returning to the organizer exits focus mode.
- On exit, keyboard focus returns to the invoking control and the previous scroll position is restored.

### Layout

- Remove organizer navigation, composer, archive rail, and unrelated status panels.
- Keep a slim, quiet toolbar with edition identity, native fullscreen state, and exit control.
- Use the full viewport, but constrain readable story lines to approximately 58–76 characters.
- On wide displays, the newspaper may use a lead-story column plus supporting stories and source rail. The content itself grows into available space; a raster screenshot is never stretched.
- Images and charts use intrinsic proportions and `object-fit: contain` unless an explicitly art-directed crop is supplied.
- The full edition remains vertically scrollable; no story text is clipped to make the screen look full.

### Responsive behavior

- `>= 1280px`: lead story, supporting story column, and source rail may appear together.
- `800–1279px`: two-column editorial layout with sources below or in a compact rail.
- `< 800px`: single reading column; controls remain reachable and horizontally scroll-free.
- Safe-area insets and reduced-motion preferences are respected.

## Marketing Site: Complete Capability Story

The scrolling sequence follows the product's mental model, not a pile of isolated screenshots:

1. **Presence** — the authentic MERRICK listening and speaking states with actual product audio.
2. **Voice identity** — enrollment, recognition result, and the privacy boundary around stored voiceprints.
3. **Conversation** — a complete user request and useful response, shown at a readable native proportion.
4. **Research across the web** — query, simultaneous page/source cards, synthesis, and citations; at least three distinct pages remain visible in the proof state.
5. **Action on the Mac** — a confirmed app-owned action with visible permission scope.
6. **Documents and memory** — user-authorized sources and the bounded library experience.
7. **Daily newspaper** — a full, content-rich edition in the new focus reader, not a sparse mock front page.
8. **Extensibility** — actual skills/plugins manager, provenance, permissions, export/import durability, and honest `preview` labels for capabilities not yet released.

### Scrolling mechanics

- Each chapter has one visual focal state and one concise explanatory idea.
- Pinned media changes only when its paired copy becomes active; it does not continuously rotate.
- Visual frames preserve the product's 7:5 ratio unless the source itself uses another ratio.
- Small product views do not sit in oversized empty frames. The outer frame adapts to the intrinsic media size.
- At mobile widths, pinned sequences become normal document flow with captions immediately following their media.
- All critical information remains available when motion is reduced or JavaScript observation is unavailable.

## Film: System Walkthrough

### Narrative coverage

The system film must show, in order:

1. MERRICK wakes, turns/listens in the real product, and the user hears the real interaction voice.
2. Voice identity recognizes the enrolled speaker.
3. A natural request becomes multi-page research with multiple pages and citations visible.
4. The result is turned into a substantial daily newspaper edition.
5. The product performs a scoped Mac action after permission.
6. The extensions surface shows installed skills/plugins, permission boundaries, and durable export/import.
7. The film ends on the real product state, not a fabricated UI recreation.

No background music is added. Product speech, interaction sounds, and silence provide the sound design. Captions are sized for television and fullscreen viewing, not scaled from oversized web typography.

### Media quality rules

- Direct visual masters are captured from the running product at 2× scale, minimum 1960×1400 for the 7:5 window.
- Product footage is never enlarged above its source pixels in the Remotion composition.
- The delivery master is 2560×1440 H.264 at CRF 15–16 with AAC product audio; a 1920×1080 web fallback may be derived from the master.
- Marketing stills use lossless PNG masters and WebP/AVIF derivatives with explicit intrinsic dimensions and 1×/2× sources.
- Posters use a meaningful visible product frame. A luma check rejects black or near-black poster/first frames.
- CSS and film composition use `contain` for evidence whose full interface must remain visible. Cropping is permitted only for a labeled detail shot.
- Existing 980×700 captures are fallback references only; they cannot fill 980 CSS pixels on a 2× display and cannot be enlarged to 1110–1160 film pixels.

## Capability Proof Treatments

### Multi-page research

- Show the query, synthesis, citation mapping, and at least three source cards/page previews simultaneously.
- Source titles and domains must be readable at the published size.
- If a page cannot be captured for privacy or licensing reasons, show its product-generated source card rather than recreating the page.

### Plugin and skill extensibility

- Use the actual manager surface: installed state, provenance, permission summary, version, and export/import affordances.
- Distinguish built-in, user-installed, and generated/imported items.
- Never show unrestricted execution as already available when it remains a Harness milestone.

### Voice identity

- Show listening, match result/confidence state where the product exposes it, enrollment management, and the deletion/privacy control.
- Do not publish a real user's biometric template, raw voiceprint data, or private utterance.
- Use a consented demonstration identity and approved product audio.

## Accessibility and Interaction QA

- All controls are keyboard reachable with a visible focus indicator.
- State changes are announced through an `aria-live` status region without repeating newspaper content.
- Contrast meets WCAG AA; the redesign remains dark throughout and avoids abrupt white sections.
- Reduced-motion mode removes pinned interpolation and crossfades while retaining chapter order.
- Captions and transcript accompany the film; audio is not the only carrier of meaning.
- Decorative device framing is ignored by assistive technology; product captures have precise alt text.

## Acceptance Scenarios

1. A keyboard-only user opens an edition, enters focus reader, enters native fullscreen, reads the complete edition, exits both modes, and returns to the original control.
2. A visitor scrolls the campaign with reduced motion and can still inspect voice identity, multi-page research, newspaper, and extension proofs in the correct order.
3. On a 2× display, no direct product asset is rendered beyond half its source width.
4. A film reviewer can hear only authentic product interaction audio and see no black first frame.
5. A release reviewer can trace every public feature claim to an approved manifest asset and truthful shipping status.
