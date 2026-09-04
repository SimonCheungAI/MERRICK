# Phase 0 — Feasibility

## Classification

- **Complexity:** Moderate
- **Surfaces:** static marketing site, Remotion system film, desktop Swift shell, embedded web product UI
- **Existing dependencies:** local HTTP/WebSocket application server, native desktop bridge, generated intelligence editions, capability inventory, voice identity, Remotion media pipeline
- **Estimated effort:** 4–7 focused engineering days for production-ready implementation and visual QA; 1–2 days for the first working vertical slice
- **Verdict:** PROCEED

## Why this is feasible

The requested capabilities already exist in the product and repository. Multi-page research, generated newspapers, Skills/plugins, and owner voiceprint flows have UI and server implementations. The marketing site and film currently under-represent them; they do not require speculative backend features. The desktop app already owns the native window and embeds the web UI, so native fullscreen and a newspaper-focused presentation state can be added without changing the assistant runtime.

## Principal risks

1. Reusing low-resolution `980 × 700` captures at large CSS sizes causes visible softness.
2. A marketing-only reconstruction can drift from the real product; direct product captures must remain the source of truth.
3. Browser fullscreen and native macOS fullscreen are different states and must not be conflated.
4. The newspaper reader must preserve escape, close, keyboard focus, scrolling, and reduced-motion behavior.
5. Capability copy must distinguish shipping functionality from blueprint-only Harness work.

## Working assumption

“Fullscreen” means both:

1. the MERRICK desktop window can enter and leave native macOS fullscreen; and
2. an open intelligence edition can enter a distraction-free newspaper presentation that uses the full available content area.

This does not grant any new filesystem, model, plugin, or external-action authority.
