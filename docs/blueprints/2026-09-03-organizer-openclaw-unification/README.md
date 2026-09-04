# Organizer–OpenClaw Task Unification

**Date:** 2026-09-03  
**Status:** validated design; implementation may begin  
**Scope:** make MERRICK tasks, reminders, and OpenClaw automations one coherent user-facing system.

## Decision in one sentence

MERRICK Organizer is the durable task ledger; OpenClaw is the linked automation executor and run-history provider. A task is never considered fully scheduled until a durable local receipt identifies the state of both systems.

## Package

1. [Feasibility](00-feasibility.md)
2. [Requirements](01-requirements.md)
3. [Architecture](02-architecture.md)
4. [Data model](03-data-model.md)
5. [API and tool contracts](04-api-contracts.md)
6. [Failure semantics](05-errors.md)
7. [Implementation roadmap](06-roadmap.md)
8. [Risk register](07-risk-register.md)
9. [Validation](08-validation.md)

## User-visible promise

“Save these for tomorrow” creates visible MERRICK tasks first. When reminders or recurring work are requested, the same task receives a linked OpenClaw automation. The spoken result distinguishes **saved locally**, **scheduled in OpenClaw**, and **delivered by macOS**, rather than collapsing them into an unverifiable “done.”
