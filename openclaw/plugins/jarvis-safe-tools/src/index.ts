import { execFile } from "node:child_process";
import { createHmac, timingSafeEqual } from "node:crypto";
import { mkdir, writeFile } from "node:fs/promises";
import { isAbsolute, join } from "node:path";
import { promisify } from "node:util";

import { Type } from "typebox";
import {
  fetchWithSsrFGuard,
  resolvePinnedHostnameWithPolicy,
  type LookupFn,
} from "openclaw/plugin-sdk/ssrf-runtime";
import { defineToolPlugin } from "openclaw/plugin-sdk/tool-plugin";

const execFileAsync = promisify(execFile);

type MediaPlayer = "music" | "spotify";
type MediaAction = "play" | "pause" | "toggle" | "next" | "previous";

type ActionCapability = {
  exp: number;
  jti: string;
  tool: "jarvis_open_app" | "jarvis_open_web_page" | "jarvis_read_web_page" | "jarvis_media_control" | "jarvis_play_music";
  app?: string;
  player?: MediaPlayer;
  action?: MediaAction;
  query?: string;
  scope?: "public_web_page";
  url?: string;
};

const ApplicationNameSchema = Type.String({
  minLength: 1,
  maxLength: 160,
  pattern: "^[^\\u0000-\\u001f\\u007f]+$",
  description: "Any installed macOS application name requested by the user.",
});
const MediaPlayerSchema = Type.Union([
  Type.Literal("music"),
  Type.Literal("spotify"),
]);
const MediaActionSchema = Type.Union([
  Type.Literal("play"),
  Type.Literal("pause"),
  Type.Literal("toggle"),
  Type.Literal("next"),
  Type.Literal("previous"),
]);

const AuthorizationSchema = Type.String({
  minLength: 80,
  maxLength: 1024,
  description:
    "A short-lived, single-use capability supplied by the trusted desktop host. Never invent, reuse, display, or request this value.",
});

const OrganizerTaskSchema = Type.Object({
  title: Type.String({ minLength: 1, maxLength: 300 }),
  projectTitle: Type.Optional(Type.String({ maxLength: 200 })),
  dueAt: Type.Optional(Type.String({ maxLength: 80 })),
});

const OrganizerTaskIdSchema = Type.String({
  minLength: 8,
  maxLength: 100,
  pattern: "^task-[a-z0-9]+$",
});

const OrganizerReminderIdSchema = Type.String({
  minLength: 8,
  maxLength: 100,
  pattern: "^reminder-[a-z0-9]+$",
});

const OrganizerOptionalDueAtSchema = Type.Optional(Type.Union([
  Type.String({ maxLength: 80 }),
  Type.Null(),
]));

const MEDIA_SCRIPTS: Record<MediaPlayer, Record<MediaAction, string>> = {
  music: {
    play: 'tell application "Music" to play',
    pause: 'tell application "Music" to pause',
    toggle: 'tell application "Music" to playpause',
    next: 'tell application "Music" to next track',
    previous: 'tell application "Music" to previous track',
  },
  spotify: {
    play: 'tell application "Spotify" to play',
    pause: 'tell application "Spotify" to pause',
    toggle: 'tell application "Spotify" to playpause',
    next: 'tell application "Spotify" to next track',
    previous: 'tell application "Spotify" to previous track',
  },
};

const PLAY_MUSIC_BY_NAME_SCRIPT = `
on run argv
  set requestedName to item 1 of argv
  tell application "Music"
    set matchingTracks to search library playlist 1 for requestedName only songs
    if (count of matchingTracks) is 0 then error "No matching song was found in the Music library."
    play item 1 of matchingTracks
  end tell
end run`;

const consumedCapabilities = new Map<string, number>();
const MAX_SOURCE_BYTES = 1_000_000;
const MAX_SNAPSHOT_CHARS = 60_000;

function base64UrlDecode(value: string): Buffer {
  if (!/^[A-Za-z0-9_-]+$/.test(value)) {
    throw new Error("The desktop action authorization is invalid.");
  }
  return Buffer.from(value, "base64url");
}

export function verifyActionCapability(
  token: string,
  tool: ActionCapability["tool"],
  args: { app?: string; player?: MediaPlayer; action?: MediaAction; query?: string; url?: string },
): string {
  if (typeof token !== "string" || token.length < 80 || token.length > 1024) {
    throw new Error("The desktop action authorization is invalid.");
  }
  const secret = process.env.JARVIS_ACTION_SECRET ?? "";
  if (!/^[0-9a-fA-F]{64}$/.test(secret)) {
    throw new Error("Desktop actions are locked because the host capability secret is unavailable.");
  }
  const parts = token.split(".");
  if (parts.length !== 3 || parts[0] !== "v1") {
    throw new Error("The desktop action authorization is invalid.");
  }
  const signed = `${parts[0]}.${parts[1]}`;
  const suppliedSignature = base64UrlDecode(parts[2]);
  const expectedSignature = createHmac("sha256", Buffer.from(secret, "hex"))
    .update(signed)
    .digest();
  if (
    suppliedSignature.length !== expectedSignature.length ||
    !timingSafeEqual(suppliedSignature, expectedSignature)
  ) {
    throw new Error("The desktop action authorization is invalid.");
  }

  let capability: ActionCapability;
  try {
    capability = JSON.parse(base64UrlDecode(parts[1]).toString("utf8")) as ActionCapability;
  } catch {
    throw new Error("The desktop action authorization is invalid.");
  }
  const now = Math.floor(Date.now() / 1000);
  for (const [jti, expiry] of consumedCapabilities) {
    if (expiry < now) consumedCapabilities.delete(jti);
  }
  if (
    !capability ||
    capability.tool !== tool ||
    !Number.isInteger(capability.exp) ||
    capability.exp < now ||
    capability.exp > now + 300 ||
    typeof capability.jti !== "string" ||
    !/^[a-f0-9]{32}$/.test(capability.jti) ||
    consumedCapabilities.has(capability.jti)
  ) {
    throw new Error("The desktop action authorization is expired, reused, or out of scope.");
  }
  if (
    (tool === "jarvis_open_app" && capability.app !== args.app) ||
    (tool === "jarvis_media_control" &&
      (capability.player !== args.player || capability.action !== args.action)) ||
    (tool === "jarvis_play_music" &&
      (capability.player !== args.player || capability.query !== args.query)) ||
    ((tool === "jarvis_open_web_page" || tool === "jarvis_read_web_page") &&
      (capability.scope !== "public_web_page" ||
        (capability.url !== undefined && capability.url !== args.url)))
  ) {
    throw new Error("The desktop action authorization does not permit this action.");
  }
  consumedCapabilities.set(capability.jti, capability.exp);
  return capability.jti;
}

export async function validatePublicWebUrl(raw: string, lookupFn?: LookupFn): Promise<URL> {
  if (raw.length > 2048) {
    throw new Error("The URL is too long.");
  }
  const url = new URL(raw);
  if (!['http:', 'https:'].includes(url.protocol)) {
    throw new Error("Only public HTTP and HTTPS pages may be opened.");
  }
  if (url.username || url.password) {
    throw new Error("URLs containing credentials are not allowed.");
  }
  await resolvePinnedHostnameWithPolicy(
    url.hostname,
    lookupFn ? { lookupFn } : undefined,
  );
  return url;
}

function decodeBasicHtmlEntities(value: string): string {
  const named: Record<string, string> = {
    amp: "&",
    apos: "'",
    gt: ">",
    lt: "<",
    nbsp: " ",
    quot: '"',
  };
  return value.replace(/&(#x[0-9a-f]+|#\d+|amp|apos|gt|lt|nbsp|quot);/gi, (_, entity: string) => {
    const lowered = entity.toLowerCase();
    if (lowered.startsWith("#x")) {
      const code = Number.parseInt(lowered.slice(2), 16);
      return Number.isInteger(code) && code >= 0 && code <= 0x10ffff && !(code >= 0xd800 && code <= 0xdfff)
        ? String.fromCodePoint(code)
        : " ";
    }
    if (lowered.startsWith("#")) {
      const code = Number.parseInt(lowered.slice(1), 10);
      return Number.isInteger(code) && code >= 0 && code <= 0x10ffff && !(code >= 0xd800 && code <= 0xdfff)
        ? String.fromCodePoint(code)
        : " ";
    }
    return named[lowered] ?? " ";
  });
}

function escapeHtml(value: string): string {
  return value
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#39;");
}

export function renderSafeSnapshot(source: string, finalUrl: string): string {
  const titleMatch = source.match(/<title\b[^>]*>([\s\S]*?)<\/title>/i);
  const title = decodeBasicHtmlEntities(
    (titleMatch?.[1] ?? "MERRICK research snapshot").replace(/<[^>]*>/g, " "),
  ).replace(/\s+/g, " ").trim().slice(0, 200);
  const readable = decodeBasicHtmlEntities(
    source
      .replace(/<head\b[^>]*>[\s\S]*?<\/head>/gi, " ")
      .replace(/<title\b[^>]*>[\s\S]*?<\/title>/gi, " ")
      .replace(/<(script|style|noscript|svg|template)\b[^>]*>[\s\S]*?<\/\1>/gi, " ")
      .replace(/<br\s*\/?\s*>/gi, "\n")
      .replace(/<\/(?:p|div|section|article|main|header|footer|li|h[1-6])\s*>/gi, "\n")
      .replace(/<[^>]*>/g, " "),
  )
    .replace(/[ \t]+/g, " ")
    .replace(/\s+([.,!?;:])/g, "$1")
    .replace(/\n\s*\n+/g, "\n\n")
    .trim()
    .slice(0, MAX_SNAPSHOT_CHARS);
  return `<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta http-equiv="Content-Security-Policy" content="default-src 'none'; style-src 'unsafe-inline'; base-uri 'none'; form-action 'none'; frame-ancestors 'none'">
<meta name="referrer" content="no-referrer">
<title>${escapeHtml(title || "MERRICK research snapshot")}</title>
<style>body{margin:0;background:#0b0d10;color:#e7b35a;font:16px/1.65 -apple-system,BlinkMacSystemFont,sans-serif}main{max-width:880px;margin:48px auto;padding:0 32px}h1{font-size:22px;color:#ffc96b}small{color:#a88b5b;overflow-wrap:anywhere}pre{white-space:pre-wrap;word-break:break-word;color:#e8dcc6}</style>
</head><body><main><h1>${escapeHtml(title || "Research snapshot")}</h1><small>${escapeHtml(finalUrl)}</small><pre>${escapeHtml(readable || "No readable text was returned by this page.")}</pre></main></body></html>`;
}

export function extractReadablePage(
  source: string,
  finalUrl: string,
): { title: string; text: string; url: string } {
  const rendered = renderSafeSnapshot(source, finalUrl);
  const title = decodeBasicHtmlEntities(
    rendered.match(/<h1>([\s\S]*?)<\/h1>/i)?.[1] ?? "Public web page",
  ).trim().slice(0, 200);
  const text = decodeBasicHtmlEntities(
    rendered.match(/<pre>([\s\S]*?)<\/pre>/i)?.[1] ?? "",
  )
    .split("\n")
    .map((line) => line.trim())
    .join("\n")
    .replace(/\n\s*\n+/g, "\n\n")
    .trim()
    .slice(0, MAX_SNAPSHOT_CHARS);
  return { title, text, url: finalUrl };
}

async function fetchSafeSource(
  url: URL,
  auditContext: "jarvis_open_web_page" | "jarvis_read_web_page",
): Promise<{ source: string; finalUrl: string }> {
  const guarded = await fetchWithSsrFGuard({
    url: url.href,
    init: {
      headers: {
        Accept: "text/html,application/xhtml+xml,text/plain;q=0.9",
        "User-Agent": "MERRICK-Research-Snapshot/1.0",
      },
    },
    maxRedirects: 3,
    timeoutMs: 20_000,
    mode: "strict",
    auditContext,
  });
  try {
    if (!guarded.response.ok) {
      throw new Error(`The source returned HTTP ${guarded.response.status}.`);
    }
    const contentType = (guarded.response.headers.get("content-type") ?? "").toLowerCase();
    if (!/^(?:text\/html|text\/plain|application\/xhtml\+xml)(?:;|$)/.test(contentType)) {
      throw new Error("Only readable HTML or plain-text sources can be opened.");
    }
    const reader = guarded.response.body?.getReader();
    if (!reader) throw new Error("The source returned no readable body.");
    const chunks: Uint8Array[] = [];
    let total = 0;
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      total += value.byteLength;
      if (total > MAX_SOURCE_BYTES) {
        await reader.cancel();
        throw new Error("The source is too large for a safe research snapshot.");
      }
      chunks.push(value);
    }
    const bytes = new Uint8Array(total);
    let offset = 0;
    for (const chunk of chunks) {
      bytes.set(chunk, offset);
      offset += chunk.byteLength;
    }
    const source = new TextDecoder("utf-8", { fatal: false }).decode(bytes);
    return { source, finalUrl: guarded.finalUrl };
  } finally {
    await guarded.release();
  }
}

export async function fetchSafeSnapshot(url: URL): Promise<{ html: string; finalUrl: string }> {
  const page = await fetchSafeSource(url, "jarvis_open_web_page");
  return {
    html: renderSafeSnapshot(page.source, page.finalUrl),
    finalUrl: page.finalUrl,
  };
}

export async function fetchSafeReadablePage(
  url: URL,
): Promise<{ title: string; text: string; url: string }> {
  const page = await fetchSafeSource(url, "jarvis_read_web_page");
  return extractReadablePage(page.source, page.finalUrl);
}

async function runFixedCommand(command: string, args: string[]): Promise<void> {
  await execFileAsync(command, args, {
    encoding: "utf8",
    shell: false,
    timeout: 10_000,
    windowsHide: true,
  });
}

async function organizerBridgeRequest(body: Record<string, unknown>): Promise<Record<string, unknown>> {
  const secret = process.env.JARVIS_ACTION_SECRET ?? "";
  const port = process.env.JARVIS_BACKEND_PORT ?? "8765";
  if (!/^[0-9a-f]{64}$/i.test(secret) || !/^\d{4,5}$/.test(port)) {
    throw new Error("MERRICK task bridge is unavailable.");
  }
  const response = await fetch(`http://127.0.0.1:${port}/internal/organizer/tasks`, {
    method: "POST",
    headers: {
      "content-type": "application/json",
      "x-jarvis-organizer-secret": secret,
    },
    body: JSON.stringify(body),
    signal: AbortSignal.timeout(10_000),
  });
  const payload = await response.json().catch(() => null);
  if (!response.ok || !payload || typeof payload !== "object") {
    const detail = payload && typeof payload === "object" && "detail" in payload
      ? String((payload as { detail: unknown }).detail)
      : "MERRICK task bridge did not accept the request.";
    throw new Error(detail);
  }
  return payload as Record<string, unknown>;
}

export default defineToolPlugin({
  id: "jarvis-safe-tools",
  name: "MERRICK Safe Tools",
  description:
    "Narrow macOS actions for MERRICK No paths, shell commands, file operations, or arbitrary scripts are accepted.",
  tools: (tool) => [
    tool({
      name: "jarvis_tasks_create",
      label: "Create MERRICK tasks",
      description:
        "Create one or more personal tasks in the visible MERRICK Assistant ledger. Use this for the owner's personal to-do list, work plan, or a list of tasks for a date. It returns a durable local receipt. It does not invent or create a generic OpenClaw automation.",
      optional: true,
      parameters: Type.Object({
        items: Type.Array(OrganizerTaskSchema, { minItems: 1, maxItems: 24 }),
      }),
      execute: async ({ items }) => organizerBridgeRequest({ action: "create", items }),
    }),
    tool({
      name: "jarvis_tasks_list",
      label: "List MERRICK tasks",
      description:
        "Read the owner's visible MERRICK personal tasks and reminders from the shared Organizer ledger. Use this before claiming that a personal task exists or is complete.",
      optional: true,
      parameters: Type.Object({}),
      execute: async () => organizerBridgeRequest({ action: "list" }),
    }),
    tool({
      name: "jarvis_tasks_complete",
      label: "Complete MERRICK task",
      description:
        "Mark one exact MERRICK personal task complete in the shared Organizer ledger. Use a task ID returned by jarvis_tasks_list or jarvis_tasks_create.",
      optional: true,
      parameters: Type.Object({ taskId: OrganizerTaskIdSchema }),
      execute: async ({ taskId }) => organizerBridgeRequest({ action: "complete", taskId }),
    }),
    tool({
      name: "jarvis_tasks_update",
      label: "Update MERRICK task",
      description:
        "Edit the title and/or due time of one open MERRICK task in the shared Organizer ledger. Use null for dueAt only when the owner asks to remove its due time.",
      optional: true,
      parameters: Type.Object({
        taskId: OrganizerTaskIdSchema,
        title: Type.Optional(Type.String({ minLength: 1, maxLength: 300 })),
        dueAt: OrganizerOptionalDueAtSchema,
      }),
      execute: async ({ taskId, title, dueAt }) => organizerBridgeRequest({
        action: "update_task",
        taskId,
        ...(title === undefined ? {} : { title }),
        ...(dueAt === undefined ? {} : { dueAt }),
      }),
    }),
    tool({
      name: "jarvis_reminders_update",
      label: "Update MERRICK reminder",
      description:
        "Move one pending MERRICK reminder to a new ISO-8601 date/time. The native notification is rescheduled through the shared Organizer ledger.",
      optional: true,
      parameters: Type.Object({
        reminderId: OrganizerReminderIdSchema,
        fireAt: Type.String({ minLength: 1, maxLength: 80 }),
      }),
      execute: async ({ reminderId, fireAt }) => organizerBridgeRequest({
        action: "update_reminder",
        reminderId,
        fireAt,
      }),
    }),
    tool({
      name: "jarvis_open_app",
      label: "Open application",
      description:
        "Open or focus any installed macOS application by name after user authorization.",
      optional: true,
      parameters: Type.Object({
        app: ApplicationNameSchema,
        authorization: AuthorizationSchema,
      }),
      execute: async ({ app, authorization }) => {
        const appName = String(app).trim();
        if (!appName || appName.length > 160 || /[\u0000-\u001f\u007f]/.test(appName)) {
          throw new Error("That application name is invalid.");
        }
        verifyActionCapability(
          authorization,
          "jarvis_open_app",
          { app: appName },
        );
        await runFixedCommand("/usr/bin/open", ["-a", appName]);
        return { ok: true, app: appName };
      },
    }),
    tool({
      name: "jarvis_open_web_page",
      label: "Open safe research snapshot",
      description:
        "Fetch a public HTTP(S) text source through pinned-DNS SSRF protection, remove scripts, links, forms, media, and active content, then open an inert local research snapshot. Use only when the user explicitly asks to see a page or source. Never place conversation text, secrets, or credentials in the URL.",
      optional: true,
      parameters: Type.Object({
        url: Type.String({ maxLength: 2048 }),
        authorization: AuthorizationSchema,
      }),
      execute: async ({ url, authorization }) => {
        verifyActionCapability(
          authorization,
          "jarvis_open_web_page",
          { url },
        );
        const safeUrl = await validatePublicWebUrl(url);
        const snapshot = await fetchSafeSnapshot(safeUrl);
        const stateDir = process.env.OPENCLAW_STATE_DIR ?? "";
        if (!stateDir || !isAbsolute(stateDir)) {
          throw new Error("OpenClaw's private state directory is unavailable.");
        }
        const snapshotDir = join(stateDir, "browser-snapshots");
        await mkdir(snapshotDir, { recursive: true, mode: 0o700 });
        const snapshotPath = join(snapshotDir, "research-snapshot.html");
        await writeFile(snapshotPath, snapshot.html, { encoding: "utf8", mode: 0o600 });
        await runFixedCommand("/usr/bin/open", [snapshotPath]);
        return { ok: true, url: snapshot.finalUrl, snapshot: true };
      },
    }),
    tool({
      name: "jarvis_read_web_page",
      label: "Read safe public web page",
      description:
        "Fetch one host-selected public HTTP(S) result through pinned-DNS SSRF protection and return only bounded readable text. It cannot use browser cookies, access local addresses, execute scripts, submit forms, or read files.",
      optional: true,
      parameters: Type.Object({
        url: Type.String({ maxLength: 2048 }),
        authorization: AuthorizationSchema,
      }),
      execute: async ({ url, authorization }) => {
        verifyActionCapability(
          authorization,
          "jarvis_read_web_page",
          { url },
        );
        const safeUrl = await validatePublicWebUrl(url);
        const page = await fetchSafeReadablePage(safeUrl);
        return { ok: true, ...page };
      },
    }),
    tool({
      name: "jarvis_media_control",
      label: "Control media app",
      description:
        "Play, pause, or change tracks in Apple Music or Spotify. It cannot execute arbitrary AppleScript and cannot modify files.",
      optional: true,
      parameters: Type.Object({
        player: MediaPlayerSchema,
        action: MediaActionSchema,
        authorization: AuthorizationSchema,
      }),
      execute: async ({ player, action, authorization }) => {
        const script = MEDIA_SCRIPTS[player as MediaPlayer]?.[action as MediaAction];
        if (!script) {
          throw new Error("That media operation is unsupported by this adapter.");
        }
        verifyActionCapability(
          authorization,
          "jarvis_media_control",
          { player: player as MediaPlayer, action: action as MediaAction },
        );
        await runFixedCommand("/usr/bin/osascript", ["-e", script]);
        return { ok: true, player, action };
      },
    }),
    tool({
      name: "jarvis_play_music",
      label: "Play a requested song",
      description:
        "Search the user's Apple Music library for a host-validated song or artist and play the first match. The query is passed as data to a fixed AppleScript and cannot execute code or modify files.",
      optional: true,
      parameters: Type.Object({
        player: Type.Literal("music"),
        query: Type.String({ minLength: 1, maxLength: 160 }),
        authorization: AuthorizationSchema,
      }),
      execute: async ({ player, query, authorization }) => {
        const safeQuery = (query as string).trim();
        if (!safeQuery || safeQuery.length > 160 || /[\u0000-\u001f]/.test(safeQuery)) {
          throw new Error("The music search query is invalid.");
        }
        verifyActionCapability(
          authorization,
          "jarvis_play_music",
          { player: player as MediaPlayer, query: safeQuery },
        );
        await runFixedCommand("/usr/bin/osascript", ["-e", PLAY_MUSIC_BY_NAME_SCRIPT, safeQuery]);
        return { ok: true, player, query: safeQuery };
      },
    }),
  ],
});
