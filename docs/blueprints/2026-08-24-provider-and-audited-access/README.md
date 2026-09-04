# Provider Connection and Audited Access Blueprint

Status: validated for incremental implementation on 2026-08-24.

This package specifies two connected upgrades: application-owned model connection and user-configurable desktop/file access with an append-only local audit trail. It extends [ADR-0001](../../decisions/2026-08-23-adopt-modular-monolith-ports-and-contracts.md); it does not change the existing memory model or send private data to a new service.

| Document | Purpose |
|---|---|
| [requirements.md](requirements.md) | Functional and non-functional requirements |
| [architecture.md](architecture.md) | Components, trust boundaries and flows |
| [data-model.md](data-model.md) | Local policy and audit records |
| [bridge-contract.md](bridge-contract.md) | Native bridge and local service contracts |
| [errors.md](errors.md) | Stable errors and recovery behaviour |
| [folder-structure.md](folder-structure.md) | Target module ownership |
| [roadmap.md](roadmap.md) | Thin, reversible delivery slices |
| [risk-register.md](risk-register.md) | Risks and mitigations |
| [validation.md](validation.md) | Architecture quality review |
