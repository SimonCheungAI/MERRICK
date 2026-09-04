import { describe, expect, it } from "vitest";
import { createHmac, randomBytes } from "node:crypto";
import { readFileSync } from "node:fs";
import type { LookupFn } from "openclaw/plugin-sdk/ssrf-runtime";
import entry, {
  extractReadablePage,
  renderSafeSnapshot,
  validatePublicWebUrl,
  verifyActionCapability,
} from "./index.js";
import { getToolPluginMetadata } from "openclaw/plugin-sdk/tool-plugin";

const TEST_SECRET = "a".repeat(64);
const POLICY_TEMPLATE = readFileSync(
  new URL("../../../openclaw.template.json5", import.meta.url),
  "utf8",
);

function agentPolicyBlock(agentId: string): string {
  const markers = [`"${agentId}": {`, `${agentId}: {`];
  const markerIndex = markers
    .map((marker) => POLICY_TEMPLATE.indexOf(marker))
    .find((index) => index >= 0) ?? -1;
  if (markerIndex < 0) throw new Error(`Missing ${agentId} agent policy.`);
  const start = POLICY_TEMPLATE.indexOf("{", markerIndex);
  if (start < 0) throw new Error(`Malformed ${agentId} agent policy.`);
  let depth = 0;
  let inString = false;
  let escaped = false;
  for (let index = start; index < POLICY_TEMPLATE.length; index += 1) {
    const char = POLICY_TEMPLATE[index];
    if (inString) {
      if (escaped) escaped = false;
      else if (char === "\\") escaped = true;
      else if (char === '"') inString = false;
      continue;
    }
    if (char === '"') inString = true;
    else if (char === "{") depth += 1;
    else if (char === "}" && --depth === 0) return POLICY_TEMPLATE.slice(start, index + 1);
  }
  throw new Error(`Unterminated ${agentId} agent policy.`);
}

function policyTools(agentId: string, policy: "allow" | "deny"): string[] {
  const block = agentPolicyBlock(agentId);
  const match = new RegExp(`${policy}:\\s*\\[([\\s\\S]*?)\\]`).exec(block);
  return match ? [...match[1].matchAll(/"([a-z0-9_*-]+)"/g)].map((item) => item[1]) : [];
}

function capability(payload: Record<string, unknown>): string {
  const body = Buffer.from(JSON.stringify({
    exp: Math.floor(Date.now() / 1000) + 120,
    jti: randomBytes(16).toString("hex"),
    ...payload,
  })).toString("base64url");
  const signed = `v1.${body}`;
  const signature = createHmac("sha256", Buffer.from(TEST_SECRET, "hex"))
    .update(signed)
    .digest("base64url");
  return `${signed}.${signature}`;
}

describe("jarvis-safe-tools", () => {
  it("declares the native companion and shared Organizer tools", () => {
    expect(getToolPluginMetadata(entry)?.tools.map((tool) => tool.name)).toEqual([
      "jarvis_tasks_create",
      "jarvis_tasks_list",
      "jarvis_tasks_complete",
      "jarvis_tasks_update",
      "jarvis_reminders_update",
      "jarvis_open_app",
      "jarvis_open_web_page",
      "jarvis_read_web_page",
      "jarvis_media_control",
      "jarvis_play_music",
    ]);
  });

  it("keeps every host action opt-in", () => {
    expect(getToolPluginMetadata(entry)?.tools.every((tool) => tool.optional)).toBe(true);
  });

  it.each([
    "http://localhost./",
    "http://foo.localhost/",
    "http://127.0.0.1/",
    "http://[::]/",
    "http://[::ffff:127.0.0.1]/",
    "http://[fc00::1]/",
    "http://[fe80::1]/",
    "file:///etc/passwd",
    "https://user:password@example.com/",
  ])("rejects non-public browser target %s", async (url) => {
    await expect(validatePublicWebUrl(url)).rejects.toThrow();
  });

  it("rejects a DNS name resolving to a private address", async () => {
    const privateLookup = (async () => [
      { address: "10.0.0.1", family: 4 },
    ]) as unknown as LookupFn;
    await expect(
      validatePublicWebUrl("https://example.test/", privateLookup),
    ).rejects.toThrow();
  });

  it("accepts a public HTTP URL after a public DNS result", async () => {
    const publicLookup = (async () => [
      { address: "93.184.216.34", family: 4 },
    ]) as unknown as LookupFn;
    await expect(
      validatePublicWebUrl("https://example.com/source", publicLookup),
    ).resolves.toMatchObject({ hostname: "example.com" });
  });

  it("renders fetched pages as inert escaped text", () => {
    const snapshot = renderSafeSnapshot(
      '<title>Safe &amp; sound</title><script>steal()</script><form action="https://evil.test"><input></form><p>Hello <a href="https://evil.test">world</a>.</p>',
      "https://example.com/source",
    );
    expect(snapshot).toContain("Safe &amp; sound");
    expect(snapshot).toContain("Hello world.");
    expect(snapshot).toContain("default-src 'none'");
    expect(snapshot).not.toContain("steal()");
    expect(snapshot).not.toContain("<form");
    expect(snapshot).not.toContain("href=");
    expect(snapshot).not.toContain("<script");
  });

  it("returns bounded readable page text without active markup", () => {
    const page = extractReadablePage(
      '<title>Result</title><script>steal()</script><article><h1>Heading</h1><p>Useful explanation.</p><a href="https://evil.test">Source link</a></article>',
      "https://example.com/result",
    );
    expect(page).toEqual({
      title: "Result",
      text: "Heading\nUseful explanation.\nSource link",
      url: "https://example.com/result",
    });
    expect(page.text).not.toContain("steal");
    expect(page.text).not.toContain("href");
  });

  it("binds a host capability to one exact action", () => {
    process.env.JARVIS_ACTION_SECRET = TEST_SECRET;
    const token = capability({ tool: "jarvis_open_app", app: "safari" });
    expect(() =>
      verifyActionCapability(token, "jarvis_open_app", { app: "safari" }),
    ).not.toThrow();
    expect(() =>
      verifyActionCapability(token, "jarvis_open_app", { app: "safari" }),
    ).toThrow(/reused/);
    const wrongScope = capability({ tool: "jarvis_open_app", app: "safari" });
    expect(() =>
      verifyActionCapability(wrongScope, "jarvis_open_app", { app: "notes" }),
    ).toThrow(/does not permit/);
    const parts = token.split(".");
    parts[1] = `${parts[1][0] === "A" ? "B" : "A"}${parts[1].slice(1)}`;
    expect(() =>
      verifyActionCapability(parts.join("."), "jarvis_open_app", { app: "safari" }),
    ).toThrow(/invalid/);
    expect(() =>
      verifyActionCapability(undefined as unknown as string, "jarvis_open_app", { app: "safari" }),
    ).toThrow(/invalid/);

    const webToken = capability({
      tool: "jarvis_open_web_page",
      scope: "public_web_page",
      url: "https://example.com/source",
    });
    expect(() =>
      verifyActionCapability(webToken, "jarvis_open_web_page", {
        url: "https://attacker.example/",
      }),
    ).toThrow(/does not permit/);

    const readToken = capability({
      tool: "jarvis_read_web_page",
      scope: "public_web_page",
      url: "https://example.com/source",
    });
    expect(() =>
      verifyActionCapability(readToken, "jarvis_read_web_page", {
        url: "https://example.com/source",
      }),
    ).not.toThrow();
  });

  it("binds music authorization to the exact validated query", () => {
    process.env.JARVIS_ACTION_SECRET = TEST_SECRET;
    const token = capability({
      tool: "jarvis_play_music",
      player: "music",
      query: "Heroes by David Bowie",
    });
    expect(() =>
      verifyActionCapability(token, "jarvis_play_music", {
        player: "music",
        query: "Heroes",
      }),
    ).toThrow(/does not permit/);

    const exactToken = capability({
      tool: "jarvis_play_music",
      player: "music",
      query: "Heroes by David Bowie",
    });
    expect(() =>
      verifyActionCapability(exactToken, "jarvis_play_music", {
        player: "music",
        query: "Heroes by David Bowie",
      }),
    ).not.toThrow();
  });

  it("does not place static tool filters in front of helper agents", () => {
    expect(policyTools("action-planner", "allow")).toEqual([]);
    expect(policyTools("action-planner", "deny")).toEqual([]);
    expect(policyTools("screen-reader", "allow")).toEqual([]);
    expect(policyTools("screen-reader", "deny")).toEqual([]);
    expect(policyTools("action-executor", "allow")).toEqual([]);
    expect(policyTools("action-executor", "deny")).toEqual([]);
    expect(policyTools("page-reader-executor", "allow")).toEqual([]);
    expect(policyTools("page-reader-executor", "deny")).toEqual([]);
  });

  it("lets research helpers inherit the full OpenClaw capability surface", () => {
    expect(policyTools("researcher", "allow")).toEqual([]);
    expect(policyTools("researcher", "deny")).toEqual([]);
    expect(policyTools("research-executor", "allow")).toEqual([]);
    expect(policyTools("research-executor", "deny")).toEqual([]);
    expect(policyTools("main", "allow")).toEqual([]);
    expect(policyTools("main", "deny")).toEqual([]);
  });
});
