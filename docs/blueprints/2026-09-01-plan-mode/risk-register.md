# Risk register

| Risk | Likelihood | Impact | Mitigation | Evidence |
|---|---:|---:|---|---|
| Plan state leaks into normal transcript/TTS | Medium | High | Typed Plan Mode events and isolated panel module; regression test verifies no assistant delta for plan state | Unit + browser check |
| Plan workflow breaks normal turn cancellation | Medium | High | Separate coordinator/task ownership; test ordinary `interrupt` after a plan event | Session integration test |
| Planner output is structurally unreliable | Medium | Medium | Strict JSON response contract, parser unit tests and retryable invalid-draft state | Unit test |
| Task Flow controller integration adds a gateway dependency | Medium | Medium | Port abstraction and fake adapter; direct old conversation remains unchanged | Adapter integration test |
| Panel crowds the HUD | Low | Medium | Modal/side panel with independent scrolling; desktop screenshot review | Visual QA |
| Flow cancellation leaves remote child task active | Medium | Medium | Use Task Flow cancel, surface final reported flow state and never claim a task stopped before it does | Adapter test/manual smoke |
| Auto router adds avoidable latency to chat | Medium | Medium | Restrict its eligibility to work-oriented turns; greetings/conversation retain direct streaming and a router failure falls through | Session test and latency trace |
| Organizer records duplicate an unaccepted plan | Low | Medium | Materialize only when the user selects an approach; a re-plan before selection has no work records | Coordinator/integration test |

No risk mitigation may introduce an additional per-action restriction or a new
fixed action vocabulary. Those would violate FR-007 and duplicate OpenClaw.
