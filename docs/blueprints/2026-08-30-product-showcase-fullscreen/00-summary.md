# MERRICK Complete Product Showcase and Fullscreen Reader

| Field | Decision |
|---|---|
| Complexity | Moderate |
| Feasibility verdict | PROCEED |
| Validation | PASS WITH WARNINGS |
| Estimated effort | 4–7 working days for the complete cross-surface release; 1–2 days for the first working fullscreen slice |
| Architecture | Extend the existing local modular monolith with a bounded native fullscreen contract, a web newspaper focus controller, and a versioned direct-evidence publication pipeline |

## Outcome

The product will support both real macOS fullscreen and a distraction-free newspaper focus reader. The campaign and film will demonstrate the complete system in a coherent order, including voice identity, multi-page web research, a substantial intelligence newspaper, and plugin/skill extensibility.

The low-resolution issue is not treated as a CSS-only problem. Existing 980×700 captures are being enlarged beyond their source pixels. The approved path records the running product at 1960×1400 or greater, prohibits enlargement in the website and Remotion composition, and produces a 2560×1440 film master plus a 1080p fallback.

## Architecture Package

1. `01-feasibility.md` — complexity, effort, verdict, and principal risks.
2. `02-requirements.md` — complete feature, media, fullscreen, accessibility, privacy, and performance requirements.
3. `03-architecture.md` — component ownership, native/web boundaries, key flows, security, scaling, and failure containment.
4. `04-data-model.md` — runtime presentation state and versioned evidence manifest.
5. `05-api-contracts.md` — bounded fullscreen bridge, native callback, reader controller, validation, and errors.
6. `06-experience-spec.md` — product interaction, complete campaign sequence, film narrative, media standards, and accessibility.
7. `07-roadmap.md` — seven independently verifiable MVP/V1 milestones with tests and rollback.
8. `08-validation.md` — all 25 architecture checks and warning-resolution gates.

## Critical Product Decisions

- Native fullscreen and newspaper focus mode are independent and may be combined.
- AppKit remains the sole window authority; JavaScript may request only `enter`, `exit`, or `toggle`.
- The existing complete edition is re-laid out for reading; no duplicate newspaper format or backend schema is introduced.
- Public claims require direct evidence from a pinned product revision.
- The website and film must visibly show all eight capability areas, not merely list them.
- Shipping extension management is shown as real product behavior. Future Harness-generated/imported execution remains clearly labelled until it ships.
- Product audio is authentic and there is no background music.

## Validation Warnings

- New 2× direct captures are still required before the replacement campaign can publish.
- Harness execution status must remain truthful throughout the implementation.
- Voice and identity demonstration assets require explicit privacy approval.

These warnings are release gates with milestone assignments, not architecture blockers.

**Implementation may begin.**
