# Folder Ownership

```text
/Applications/MERRICK.app/             # one installed product bundle
~/Library/Application Support/JarvisStark/   # all mutable user state
jarvis-stark/dist/                           # developer build and optional DMG only
jarvis-stark/dist/MERRICK-installer/   # temporary DMG staging, deletable after packaging
```

The installer staging directory is never a supported launch target. Removing it cannot affect user state.
