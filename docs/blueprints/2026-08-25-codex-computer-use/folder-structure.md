# Ownership and Packaging Layout

```text
app bundle/Contents/Resources/runtime/
  codex-computer-use/                 # immutable, signed official resources
  server/openclaw_client.py            # bootstrap + private environment owner
  openclaw/openclaw.template.json5     # capability configuration only

~/Library/Application Support/JarvisStark/OpenClaw/
  native-home/.codex/                  # MERRICK-only Codex home
    computer-use/                      # seeded native client
    marketplaces/jarvis-bundled/       # seeded local marketplace
    plugins/                           # Codex-managed install state
    jarvis-computer-use-state.json     # redacted status record
```

The package build never copies `~/.codex/auth.json`, user plugins, conversations, Skills, or global OpenClaw state. The bootstrap never writes to the app bundle.
