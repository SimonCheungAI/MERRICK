# API and Integration Contracts

## Contract 1: Web UI to macOS Fullscreen Bridge

The web UI uses the existing bounded `WKScriptMessageHandler` channel. It does not send arbitrary selectors, shell commands, or window properties.

### Request

```json
{
  "action": "setWindowFullscreen",
  "mode": "toggle",
  "requestId": "5796BC92-30DB-4306-BD39-0F845B313A6B"
}
```

### Validation

- `action` must exactly equal `setWindowFullscreen`.
- `mode` must be `enter`, `exit`, or `toggle`.
- `requestId` must parse as a UUID.
- Requests during an active transition return the current transition state and do not call `toggleFullScreen` again.
- `enter` while already fullscreen and `exit` while already normal are idempotent successes.

### Native behavior

1. Before entry, store the current level and collection behavior.
2. Use a normal window level and a fullscreen-capable collection behavior for the native transition.
3. Call AppKit's supported fullscreen API on the managed MERRICK window.
4. On exit, restore the previous floating-window level and collection behavior.
5. AppKit delegate callbacks, not optimistic JavaScript state, are authoritative.

### Response channel

The native shell invokes a fixed web callback:

```js
window.merrickNativeFullscreenState({
  mode: "fullscreen",
  requestId: "5796BC92-30DB-4306-BD39-0F845B313A6B",
  reason: "web",
  error: null
});
```

The argument is serialized with `JSONEncoder`; it is never interpolated from untrusted strings into executable JavaScript.

### Errors

| Code | Meaning | Web behavior |
|---|---|---|
| `invalid_request` | Message shape, mode, or UUID is invalid | Keep current state and announce failure |
| `transition_busy` | A transition is already running | Disable the control until the next native event |
| `fullscreen_unavailable` | AppKit rejected the transition | Return to normal state and retain the newspaper view |
| `window_unavailable` | Managed window no longer exists | Disable native fullscreen; keep web focus mode available |

## Contract 2: Web-only Newspaper Focus Controller

This is an internal UI contract, not a native or network API.

```ts
type ReaderMode = "closed" | "organizer" | "newspaper-focus";

interface ReaderFocusRequest {
  editionId: string;
  invokingControlId: string;
}
```

### Operations

- `enterNewspaperFocus(request)` validates that the edition exists, records scroll/focus state, hides non-reader chrome, and focuses the reader heading.
- `exitNewspaperFocus()` restores the organizer, scroll position, and invoking control.
- `Escape` exits newspaper focus first. If focus mode is already closed, native fullscreen is left to the system and its standard control.
- Closing the organizer while focused first exits focus mode so no hidden state survives.

## Contract 3: Native Fullscreen Keyboard Access

The visible control and macOS standard Control-Command-F behavior both converge on the same native fullscreen state machine. The web UI may request `toggle`; the native system menu/delegate path reports state through the same callback.

No global keyboard hook is introduced.

## Contract 4: Showcase Evidence Manifest

`marketing-site/assets/evidence/manifest.json` is validated before a site or film release.

### Required publication checks

1. Every published feature claim resolves to a `CapabilityProof`.
2. Every proof references at least one existing asset.
3. Direct captures meet their minimum dimensions and are not enlarged in site CSS or Remotion composition.
4. Video metadata contains the declared audio stream and a non-black poster/first frame.
5. Privacy review is `approved` for all public assets.
6. `shippingStatus` matches the product revision represented by the capture.

### Example

```json
{
  "schemaVersion": 1,
  "productRevision": "<git-revision>",
  "generatedAt": "2026-08-30T12:00:00Z",
  "assets": [
    {
      "id": "research-multi-page-2x",
      "kind": "image",
      "path": "../research-multi-page@2x.webp",
      "width": 1960,
      "height": 1400,
      "durationSeconds": null,
      "codec": null,
      "hasAudio": false,
      "origin": "direct-product-capture",
      "captureScale": 2,
      "maxCssWidth": 980,
      "maxFilmWidth": 980,
      "sha256": "<64-hex-digest>",
      "privacyReview": "approved",
      "productState": "Research view showing query synthesis and three source pages",
      "alt": "MERRICK research view comparing three cited web sources"
    }
  ],
  "proofs": [
    {
      "capabilityId": "multi-page-research",
      "shippingStatus": "shipping",
      "claim": "Search, open, and synthesize evidence across multiple pages.",
      "surface": ["site", "film", "product"],
      "assetIds": ["research-multi-page-2x"],
      "verifiedBy": "release-review",
      "verifiedAt": "2026-08-30T12:05:00Z"
    }
  ]
}
```

The example digest placeholder is not valid for publication; the validator requires the real digest.

## Compatibility

- Existing web-to-native actions remain unchanged.
- Browsers without the native bridge still support newspaper focus mode. The native fullscreen control is hidden or disabled with a clear explanation.
- No REST, WebSocket, model-provider, or storage contract changes.
- Older marketing assets may remain in the repository, but publication consumes only the current manifest.

## Observability

- Log fullscreen transition start, completion, failure, and duration without content or document identifiers.
- Build validation reports asset id, dimensions, publication width, audio presence, and proof coverage.
- Never log voiceprints, user utterances, newspaper content, URLs with private query parameters, or media frame contents.
