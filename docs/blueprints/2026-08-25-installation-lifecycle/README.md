# Installation and Lifecycle Blueprint

Status: validated on 2026-08-25. This repair closes the launch failure caused by two copies of the app competing for the fixed loopback backend port, and makes the application discoverable through normal macOS application surfaces.

| Document | Purpose |
|---|---|
| [requirements.md](requirements.md) | Feasibility, requirements and constraints |
| [architecture.md](architecture.md) | Components, authority and launch/reopen flows |
| [data-model.md](data-model.md) | Small local lifecycle state |
| [bridge-contract.md](bridge-contract.md) | Native lifecycle/diagnostic contracts |
| [errors.md](errors.md) | User-visible startup errors and recovery |
| [folder-structure.md](folder-structure.md) | Ownership and packaging layout |
| [roadmap.md](roadmap.md) | Thin delivery slices |
| [risk-register.md](risk-register.md) | Launch/distribution risks |
| [validation.md](validation.md) | Architecture quality gate |
