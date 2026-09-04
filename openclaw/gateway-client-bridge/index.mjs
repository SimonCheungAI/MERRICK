import readline from "node:readline";
import process from "node:process";

import { GatewayClient } from "@openclaw/gateway-client";
import { PROTOCOL_VERSION } from "@openclaw/gateway-protocol/version";

const OPERATOR_SCOPES = Object.freeze([
  "operator.read",
  "operator.write",
  "operator.admin",
  "operator.approvals",
  "operator.pairing",
  "operator.questions",
  "operator.talk",
]);

function emit(message) {
  process.stdout.write(`${JSON.stringify(message)}\n`);
}

function fatal(code, message) {
  emit({ type: "fatal", code, message });
  process.exitCode = 1;
}

function loopbackGatewayURL(raw) {
  let parsed;
  try {
    parsed = new URL(raw);
  } catch {
    return null;
  }
  const host = parsed.hostname.toLowerCase();
  if ((parsed.protocol !== "ws:" && parsed.protocol !== "wss:") ||
      (host !== "127.0.0.1" && host !== "localhost") ||
      !parsed.port || parsed.username || parsed.password) {
    return null;
  }
  return parsed;
}

const gatewayURL = loopbackGatewayURL(process.env.OPENCLAW_GATEWAY_URL || "");
if (!gatewayURL) {
  fatal("NON_LOOPBACK_GATEWAY", "The MERRICK Gateway bridge accepts only an explicit loopback WebSocket URL.");
} else if (!/^[0-9a-fA-F]{64}$/.test(process.env.OPENCLAW_GATEWAY_TOKEN || "")) {
  fatal("INVALID_GATEWAY_TOKEN", "The app-owned OpenClaw Gateway token is unavailable.");
} else {
  let connectedResolve;
  let connectedReject;
  let readySettled = false;
  let shuttingDown = false;
  let inputClosed = false;
  let pendingRequests = 0;
  const connected = new Promise((resolve, reject) => {
    connectedResolve = resolve;
    connectedReject = reject;
  });

  const client = new GatewayClient({
    url: gatewayURL.href,
    token: process.env.OPENCLAW_GATEWAY_TOKEN,
    minProtocol: PROTOCOL_VERSION,
    maxProtocol: PROTOCOL_VERSION,
    clientName: "gateway-client",
    clientDisplayName: "MERRICK Companion",
    clientVersion: "2026.8.1",
    platform: process.platform,
    mode: "backend",
    role: "operator",
    scopes: OPERATOR_SCOPES,
    caps: ["approvals", "exec-approvals", "session-scoped-events", "tool-events"],
    env: process.env,
    hostDeps: {
      logDebug: () => {},
      logError: () => {},
      redactForLog: () => "[redacted]",
    },
    onHelloOk: (hello) => {
      if (!readySettled) {
        readySettled = true;
        connectedResolve();
      }
      emit({
        type: "ready",
        protocol: hello.protocol,
        serverVersion: hello.server?.version || null,
        scopes: hello.auth?.scopes || [],
      });
    },
    onConnectError: (error) => {
      if (!readySettled) {
        readySettled = true;
        connectedReject(error);
      }
      emit({ type: "connection_error", message: "The OpenClaw Gateway connection was not accepted." });
    },
    onReconnectPaused: (info) => {
      emit({ type: "connection_paused", code: info.detailCode || "RECONNECT_PAUSED" });
    },
    onClose: (code) => {
      if (!shuttingDown) emit({ type: "disconnected", code });
    },
    onGap: ({ expected, received }) => {
      emit({ type: "event_gap", expected, received });
    },
    onEvent: (event) => {
      emit({ type: "event", event: event.event, payload: event.payload ?? null });
    },
  });

  async function shutdown() {
    if (shuttingDown) return;
    shuttingDown = true;
    await client.stopAndWait({ timeoutMs: 2_000 }).catch(() => {});
  }

  async function handle(message) {
    if (!message || typeof message !== "object" || Array.isArray(message)) {
      emit({ type: "protocol_error", code: "INVALID_MESSAGE" });
      return;
    }
    if (message.type === "shutdown") {
      await shutdown();
      return;
    }
    if (typeof message.id !== "string" || message.id.length < 1 || message.id.length > 128 ||
        typeof message.method !== "string" || !/^[a-z][a-z0-9._-]{0,127}$/i.test(message.method)) {
      emit({ type: "response", id: typeof message.id === "string" ? message.id : null, ok: false, error: { code: "INVALID_REQUEST", message: "A request id and OpenClaw method are required." } });
      return;
    }
    pendingRequests += 1;
    try {
      await connected;
      const result = await client.request(message.method, message.params ?? {});
      emit({ type: "response", id: message.id, ok: true, result });
    } catch (error) {
      const details = error?.details;
      emit({
        type: "response",
        id: message.id,
        ok: false,
        error: {
          code: typeof error?.gatewayCode === "string" ? error.gatewayCode : "GATEWAY_REQUEST_FAILED",
          message: typeof error?.message === "string" ? error.message : "The OpenClaw request failed.",
          ...(details !== undefined ? { details } : {}),
        },
      });
    } finally {
      pendingRequests -= 1;
      if (inputClosed && pendingRequests === 0) await shutdown();
    }
  }

  client.start();
  const lines = readline.createInterface({ input: process.stdin, crlfDelay: Infinity });
  lines.on("line", (line) => {
    let message;
    try {
      message = JSON.parse(line);
    } catch {
      emit({ type: "protocol_error", code: "INVALID_JSON" });
      return;
    }
    void handle(message);
  });
  lines.on("close", () => {
    inputClosed = true;
    if (pendingRequests === 0) void shutdown();
  });
  process.on("SIGTERM", () => void shutdown());
  process.on("SIGINT", () => void shutdown());
}
