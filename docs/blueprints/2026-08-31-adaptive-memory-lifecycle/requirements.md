# Requirements

## Phase 1 — Scope

MERRICK shall adapt to its verified owner through a four-level local
memory lifecycle while speaking naturally and applying only the latest
effective preference.

## Functional requirements

- **FR-001 Episode evidence:** completed verified-owner turns remain Level 1
  evidence in the existing episode store.
- **FR-002 Candidate observation:** an incidental preference expression may
  become a Level 2 candidate but must not change assistant behaviour.
- **FR-003 Confirmation proposal:** repeated or deliberately reviewed evidence
  may become a Level 3 proposal; it remains inactive until owner confirmation.
- **FR-004 Active preference:** an explicit owner directive or confirmed
  proposal becomes the unique Level 4 active value for its preference key.
- **FR-005 Latest-only projection:** ordinary prompts, preference questions,
  summaries and OpenClaw wiki projection receive only the current active value
  for each key.
- **FR-006 Supersession:** activating a new value for a key makes every older
  active/proposed value for that key non-serving before the next turn.
- **FR-007 Natural behaviour:** normal replies demonstrate a preference instead
  of announcing, listing or contrasting stored preferences.
- **FR-008 Compact acknowledgement:** a preference change may receive one
  concise forward-looking acknowledgement, without reciting the old value.
- **FR-009 Explicit history boundary:** superseded values are unavailable to
  ordinary recall. A future owner-only history request may use the audit path.
- **FR-010 Forget semantics:** forgetting a preference revokes the active card
  and removes related candidate/proposal lifecycle rows so retrieval cannot
  resurrect it.
- **FR-011 Owner gate:** guest and presentation-only voice matches cannot read,
  propose, confirm, revise or forget private preferences.
- **FR-012 OpenClaw boundary:** OpenClaw remains a derived corroboration/index
  layer and never becomes authoritative for lifecycle state.
- **FR-013 Legacy compatibility:** existing cards and preference snapshots load
  as active values without requiring destructive migration.
- **FR-014 Failure isolation:** lifecycle migration or bookkeeping failure must
  not block conversation or erase the last valid active projection.

## Non-functional requirements

- **NFR-001 Privacy:** all lifecycle state remains under the private local
  OpenClaw state directory with mode 0600 files and 0700 directories.
- **NFR-002 Latency:** latest-only filtering adds less than 20 ms to a local
  recall on a personal-scale database.
- **NFR-003 Determinism:** the same set of active cards produces the same prompt
  projection and wiki projection.
- **NFR-004 Auditability:** lifecycle rows identify stage, key, timestamps,
  confidence, evidence count and the active revision when applicable.
- **NFR-005 Data minimization:** serving projections omit raw evidence,
  confidence commentary and superseded text.
- **NFR-006 Reliability:** schema upgrades are additive and idempotent.
- **NFR-007 Testability:** the store is verifiable using a temporary real SQLite
  database; OpenClaw is mocked only at its gateway boundary.

## Implicit-requirement review

| Concern | Resolution |
|---|---|
| Pagination | Not required for the bounded serving projection; any future history UI must paginate |
| Error states | Corrupt/missing lifecycle data falls back to current cards, never history |
| Notifications | No notification or unsolicited preference prompt in this slice |
| Mobile | Out of scope; lifecycle contract is host-neutral |
| Admin panel | Future memory-review panel may expose proposals and history |
| File uploads | Not applicable |
| Audit logs | Local structured lifecycle rows and redacted trace events |
| Soft delete | Supersession is retained; explicit forget deletes candidate/proposal evidence and revokes serving state |

## Constraints and assumptions

- The existing Python process, SQLite memory database and JSON materialized
  cards remain in place.
- No cloud model training, external vector service or new daemon is introduced.
- Explicit directives may skip candidate/proposal stages and become active
  immediately because they are direct owner authority.
- A candidate may be promoted to proposed without becoming active. Proposal UI
  is a later independently deployable slice.

## Resolved conflicts

- Four-level history versus latest-only answers: keep lifecycle history on the
  write/audit path and expose only materialized active state on the serving path.
- Adaptation versus accidental personality drift: implicit evidence stops at
  candidate/proposed; only explicit owner authority activates it.
- Auditability versus forgetting: ordinary supersession retains history, while
  an explicit forget request removes related lifecycle evidence.

## Open questions

None block the core implementation. A later product decision may choose where
Level 3 proposals appear: in conversation, the memory dashboard, or both.
