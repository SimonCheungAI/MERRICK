# Risk Register

| ID | Risk | Likelihood | Impact | Mitigation | Owner / milestone |
|---|---|---:|---:|---|---|
| R-01 | Generated/imported code escapes its declared permission scope | High | Critical | Out-of-process worker, OS sandbox, brokered capabilities, empty env, adversarial escape tests | Security / M1–M3 |
| R-02 | A native OpenClaw plugin runs in-process and bypasses fine-grained policy | High | Critical | Separate `native_full_trust` profile, explicit native warning/click, never auto-enable, Safe Mode and rollback | Runtime / M2–M4 |
| R-03 | Prompt injection inside requirements, README, source, tests or webpage tells the agent to self-authorize/exfiltrate | High | Critical | Treat all project/package content as untrusted; model lacks grant/activation APIs; host-only assertions | Security / M0–M2 |
| R-04 | Existing broad `exec: full`, elevated and destructive OpenClaw settings let the main agent bypass Harness | High | Critical | Route plugin lifecycle mutations through host service; deny direct PluginVault/config access; conformance tests and policy update before activation | Architecture / M0 |
| R-05 | Full Access is mistaken for “no boundary” and exposes secrets or other plugins | High | Critical | Define product maximum; exclude policy kernel, vault internals, app bundle and Keychain plaintext; exact effective-scope UI | Product/security / M0–M3 |
| R-06 | Dependency install hooks or compromised package dependencies execute during build | Medium | Critical | Frozen lockfiles, lifecycle scripts disabled, allowlisted registry/cache, checksums, SBOM and vulnerability scan | Build / M1–M2 |
| R-07 | Malicious archive performs traversal, link escape or decompression bomb | Medium | Critical | Randomized non-executable intake, canonical path validation, reject links/special files/duplicates, strict size/count/depth limits | Package / M2 |
| R-08 | Export leaks credentials, documents, logs or absolute local paths | Medium | Critical | Server-owned include schema, immutable source/artifact allowlist, secret scanner, golden export tests | Package / M2 |
| R-09 | Imported package smuggles grants or inherits publisher Full Access | Medium | Critical | Package schema excludes authority; receiver creates all grants locally; activation always re-previews | Policy / M2–M3 |
| R-10 | App update overwrites or deletes user-generated plugins | Medium | Critical | Vault under Application Support, installer conformance test, pre-migration snapshots, explicit uninstall retention choice | Lifecycle / M0–M4 |
| R-11 | Schema migration corrupts registry or immutable revision references | Low | Critical | Disk/integrity preflight, checkpoint/snapshot, forward-only migrations, fixtures from every version, read-only recovery | Data / M0, M4 |
| R-12 | OpenClaw/Harness ABI change leaves incompatible code active | Medium | Critical | Version ranges, tool schema/artifact hashes, startup revalidation, candidate active set, quarantine on drift | Runtime / M1–M4 |
| R-13 | Plugin ID collision shadows a core or different-origin plugin | Medium | High | Origin-qualified identity, core IDs reserved, one public ID per active generation, explicit replacement UI | Registry / M0–M3 |
| R-14 | Gateway restart during activation leaves half-installed plugin/config | Medium | Critical | Staged config validation, atomic swap, monotonic active sets, exact health receipt, rollback transaction | Runtime / M3 |
| R-15 | Revoked permission remains usable by a live worker | Medium | Critical | Broker checks grant on every capability call, revoke closes session/socket and terminates worker, revocation E2E test | Policy/runtime / M1–M3 |
| R-16 | Agent silently modifies the currently active revision | Medium | High | Active source read-only; edits create child revision in isolated worktree; filesystem ACL/conformance tests | Harness / M1 |
| R-17 | User approves an opaque or misleading Full Access sheet | Medium | High | Host-computed normalized scope, observed-vs-declared diff, plain-language examples, keyboard/native control, no plugin-supplied HTML | UX/security / M2–M3 |
| R-18 | Voice spoof/misrecognition grants persistent authority | Medium | Critical | Voice may request but not submit; persistent/FULL requires trusted native click or biometric assertion | Native / M2 |
| R-19 | Worker process consumes CPU, memory, disk or spawns children indefinitely | High | High | Per-worker process group, resource/time/output quotas, sandbox process policy, supervisor kill and breaker | Runtime / M1 |
| R-20 | Network access becomes SSRF or local-network discovery | High | Critical | Normalized destination allowlist, DNS rebinding checks, private/link-local denial, method/port limits, broker proxy | Security / M1 |
| R-21 | Plugin runtime writes an external effect twice after timeout | Medium | High | Tool-level effect declaration, idempotency contract, no generic write retry, plugin-specific reconciliation requirement | SDK/runtime / M1–M3 |
| R-22 | Audit/evidence files leak source prompts or personal test fixtures | Medium | High | Metadata-only audit, bounded redacted evidence, synthetic preview fixtures, retention and export exclusions | Privacy / M1–M2 |
| R-23 | Optional local signing creates false marketplace trust | Medium | Medium | Label signature as identity/integrity only; no automatic trust/grants; future publisher trust is separate | Product/package / M2 |
| R-24 | Sandboxing differs across macOS versions or disappears | Medium | Critical | Startup feature detection, fail closed, versioned profiles, no fallback to unsandboxed; compatibility fixtures | Runtime / M1–M4 |
| R-25 | Safe Mode or rollback cannot start because the core bridge is damaged | Low | Critical | Bridge bundled/signed and excluded from Harness edits; core-only config fixture; packaged release recovery E2E | Release / M0–M4 |
| R-26 | Disk fills during build/export/migration | Medium | High | Preflight estimates, quotas, streamed hashing, atomic cleanup, never prune referenced revisions/backups | Storage / M1–M4 |
| R-27 | Concurrent jobs edit/activate the same project or generation | Medium | High | Project leases, optimistic revisions, serialized config/restart lock, idempotency keys | Application / M1–M3 |
| R-28 | User assumes portable package includes connected accounts or secrets | Medium | Medium | Export summary explicitly lists exclusions; imported plugin starts disconnected/ungranted | UX / M2 |
| R-29 | Uninstall or “clean install” semantics surprise the owner | Medium | High | Separate app removal from vault deletion, retain by default, explicit owner-confirmed data removal tool | Lifecycle / M4 |
| R-30 | Generated plugin quality is poor despite passing unit tests | High | Medium | Disposable real Gateway preview, contract fixtures, observed permission evidence, owner acceptance and easy rollback | Quality / M1–M3 |

## Release-blocking controls

Before any generated plugin can activate in production, M0–M3 must prove:

1. The main model cannot write the production OpenClaw config, PluginVault
   registry, grants or signed bridge outside typed Harness services.
2. Revocation terminates the exact worker and blocks the next broker call.
3. Candidate activation failure restores a core-only or last-known-good Gateway.
4. Archive inspection and export-exclusion adversarial test suites pass.
5. A packaged app upgrade preserves the vault and quarantines incompatible
   revisions without deleting them.
