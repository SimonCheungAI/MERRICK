# OpenClaw-native MERRICK Companion

## Decision

- Complexity: **Complex**
- Verdict: **PROCEED**
- Architecture: a supervised OpenClaw runtime, an official Gateway client
  adapter, and a bundled `jarvis-companion` OpenClaw plugin. MERRICK
  becomes the voice/native companion instead of a second tool-policy engine.
- Estimated delivery: six independently releasable milestones over roughly
  7-12 engineering days, with the existing path retained until native session
  dispatch has passed release verification.

## Outcome

OpenClaw owns sessions, tools, coding work, plugins, automations, browser work,
skills, subagents, approvals, questions and run state. MERRICK owns local
speech, the immediate acknowledgement, native presentation, macOS lifecycle
and a faithful projection of OpenClaw state. It does not keep a competing
capability allowlist.

The OpenClaw Control UI is a first-class advanced workspace. MERRICK can
open it through OpenClaw's short-lived dashboard handoff and can route the
current voice conversation into the same OpenClaw session.

## Blueprint package

1. `requirements.md`
2. `architecture.md`
3. `data-model.md`
4. `api-contracts.md`
5. `errors.md`
6. `risk-register.md`
7. `roadmap.md`
8. `validation.md`

## Architectural invariants

1. OpenClaw is the sole execution and tool-policy authority.
2. MERRICK never silently converts an OpenClaw denial into permission.
3. Removing the MERRICK allowlist does not remove OpenClaw approvals,
   device scopes, session permission modes or plugin trust checks.
4. The app and Gateway remain loopback-only by default.
5. One voice turn maps to one OpenClaw run and at most one final spoken answer.
6. Closing MERRICK terminates every app-owned child and leaves no Gateway,
   bridge or browser handoff process behind.
7. A failed native path falls back to the pinned legacy conversational path
   until the migration flag is promoted to general availability.

## Implementation status

Architecture validation: **PASS WITH WARNINGS**. Implementation may begin.
Warnings and their milestone owners are recorded in `validation.md`.
