# MERRICK Companion Bridge

This bundled OpenClaw plugin adds the few native macOS surfaces that belong to
the MERRICK host: focusing an app, handing a public page to the visible
display, and fixed media controls. Its historical plugin id remains
`jarvis-safe-tools` so existing installations migrate without duplicate plugin
records.

It is additive. The OpenClaw `main` agent inherits the complete configured
OpenClaw capability surface, including files, exec, browser, computer, coding,
skills, sessions, subagents, automations, and connected integrations. This
plugin does not filter, proxy, or approve those native OpenClaw capabilities.
OpenClaw's own permission modes, scopes, and approval system remain
authoritative.

The companion-specific tools continue to validate their own arguments because
they cross into native macOS APIs. Their short-lived host capabilities protect
that bridge from replay and do not form an allowlist for OpenClaw itself.

## Build

```bash
pnpm --filter openclaw-plugin-jarvis-safe-tools run build
pnpm --filter openclaw-plugin-jarvis-safe-tools test
```
