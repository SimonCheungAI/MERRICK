# Risk Register

| Risk | Likelihood | Impact | Mitigation |
|---|---:|---:|---|
| OAuth connector output format changes | Medium | High | Parse conservatively, retain browser-device-code fallback and clear diagnostics. |
| Model follows untrusted document instructions | Medium | High | Root/operation capability is host-bound; document text cannot add roots or purge audit. |
| Snapshot storage grows indefinitely | Medium | Medium | Byte caps, retention policy, visible non-reversible status and paginated history. |
| User expects an operation to be reversible but file is large/binary | Medium | Medium | Show snapshot availability before restore; retain hashes/metadata for all changes. |
| macOS TCC blocks a chosen folder or GUI | High | Medium | Report exact missing native permission and keep unaffected operations usable. |
| New path breaks workspace documents | Low | High | Keep library fallback and add characterization tests before routing changes. |
| Gateway reload interrupts a spoken answer | Medium | Medium | Apply policy only between turns; emit a ready state after health check. |
| Credentials leak into a log/audit | Low | Critical | Keychain-only secret storage, secret redaction, zero secret fields in profile/audit schema and regression tests. |
