# MERRICK product name

The public product name is **MERRICK**. Use `Merrick` for PascalCase code
identifiers and `merrick` for new lowercase identifiers. The native application
is `MERRICK.app`, its executable is `Merrick`, and the installer is
`MERRICK-macOS-arm64.dmg`.

The September 2026 rename updates native titles and menus, permission copy,
the frontend in both languages, model identity prompts, generated provider
display names, source comments, owned class/function names, and documentation.
The old acronym expansion is no longer a product subtitle.

## Deliberate compatibility identifiers

These are storage or integration contracts, not public branding. Keep them
until a separate tested migration is approved:

- `ai.jarvis.desktop` and the matching designated signing requirement preserve
  macOS privacy grants and application identity across updates.
- `ai.jarvis.desktop.provider-credentials`, existing `Jarvis*` UserDefaults
  keys, and `Library/Application Support/JarvisStark` preserve credentials,
  preferences, memory, voice profiles, documents, and installed plugins.
- Existing `jarvis-*.db`, memory/archive names, plugin-vault formats and MIME
  types, gateway profile/session IDs, and schema/evidence identifiers keep
  saved data and prior exports readable.
- `JARVIS_*` environment variables, `jarvis_*` published OpenClaw/MCP tools,
  plugin/package IDs, the `jarvis-v1` WebSocket protocol, HTTP bridge headers,
  and the native message-handler name remain compatible with existing clients.
- The checkout/repository name, historical media filenames and binary footage,
  original voice-reference assets, and private backup history are unchanged.
  A source rename does not rewrite text baked into previously recorded media.
- The former spoken name remains an input alias. New speech hints and product
  copy use Merrick / 梅里克; old names never override the current system identity.

Do not globally replace these identifiers merely to make a text search empty.
The behavioral regression checks are in `tests/test_merrick_branding.py`.
