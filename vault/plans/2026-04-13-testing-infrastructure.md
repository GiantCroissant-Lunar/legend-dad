# Testing Infrastructure Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Establish unified testing infrastructure across all project layers — Vitest for Node.js, Playwright for browser E2E, GUT scaffold for Godot, and Taskfile orchestration.

**Architecture:** Four independent test runners (pytest, Vitest, GUT, Playwright) each own their layer. Playwright lives in a new `@legend-dad/e2e` pnpm workspace package. Taskfile provides `task test` (all) plus `task test:{python,server,godot,e2e}` for granular runs.

**Tech Stack:** Vitest, Playwright, GUT v9.x (Godot), pytest (existing), go-task Taskfile

**Spec:** `vault/specs/2026-04-13-testing-infrastructure-design.md`

---

## File Map

### New files

| File | Responsibility |
|---|---|
| `project/server/packages/game-server/vitest.config.js` | Vitest configuration — ESM, 15s timeout |
| `project/server/packages/game-server/src/__tests__/helpers/mock-godot.js` | Reusable mock Godot WS client |
| `project/server/packages/game-server/src/__tests__/helpers/test-server.js` | Boots isolated HTTP+WS+MCP server on random port |
| `project/server/packages/game-server/src/__tests__/mcp-transport.test.js` | MCP transport tests (migrated from test-mcp.js) |
| `project/server/packages/game-server/src/__tests__/agent.test.js` | Agent integration test (migrated from test-agent.js) |
| `project/server/packages/e2e/package.json` | @legend-dad/e2e package definition |
| `project/server/packages/e2e/playwright.config.js` | Playwright config — Chromium, auto-start servers |
| `project/server/packages/e2e/tests/smoke.spec.js` | Godot loads in browser, WS connects |
| `project/server/packages/e2e/tests/mcp-roundtrip.spec.js` | MCP HTTP calls with live Godot in browser |
| `project/hosts/complete-app/tests/test_example.gd` | GUT scaffold test |
| `project/hosts/complete-app/.gutconfig.json` | GUT runner config |

### Modified files

| File | Change |
|---|---|
| `project/server/packages/game-server/package.json` | Add vitest devDep, test scripts |
| `Taskfile.yml` | Add test:* tasks |

### Deleted files (after migration verified)

| File | Reason |
|---|---|
| `project/server/packages/game-server/src/test-mcp.js` | Migrated to Vitest |
| `project/server/packages/game-server/src/test-agent.js` | Migrated to Vitest |

---

## Task 1: Add Vitest to game-server

**Files:**
- Create: `project/server/packages/game-server/vitest.config.js`
- Modify: `project/server/packages/game-server/package.json`

- [ ] **Step 1: Install vitest**

```bash
cd project/server/packages/game-server && pnpm add -D vitest
```

- [ ] **Step 2: Create vitest.config.js**

Create `project/server/packages/game-server/vitest.config.js`:

```js
import { defineConfig } from "vitest/config";

export default defineConfig({
	test: {
		testTimeout: 15_000,
		hookTimeout: 15_000,
	},
});
```

- [ ] **Step 3: Add test scripts to package.json**

In `project/server/packages/game-server/package.json`, add to `"scripts"`:

```json
"test": "vitest run",
"test:watch": "vitest"
```

- [ ] **Step 4: Verify vitest runs (no tests yet)**

```bash
cd project/server/packages/game-server && pnpm test
```

Expected: Vitest starts and reports "No test files found" (exit 0).

- [ ] **Step 5: Commit**

```bash
git add project/server/packages/game-server/vitest.config.js project/server/packages/game-server/package.json project/server/pnpm-lock.yaml
git commit -m "chore: add vitest to game-server package"
```

---

## Task 2: Extract mock-godot helper

**Files:**
- Create: `project/server/packages/game-server/src/__tests__/helpers/mock-godot.js`

The mock Godot WS client logic is duplicated in test-mcp.js (lines 147-198) and test-agent.js (lines 125-278). Extract a reusable version.

- [ ] **Step 1: Create the mock-godot helper**

Create `project/server/packages/game-server/src/__tests__/helpers/mock-godot.js`:

```js
import { WebSocket } from "ws";

/**
 * Default game state returned by mock Godot for get_state commands.
 */
export const MOCK_STATE = {
	active_era: "FATHER",
	active_entity_id: "father",
	entities: [
		{
			entity_id: "FatherPlayer",
			components: {
				grid_position: { col: 2, row: 2, facing: "down" },
				timeline_era: { era: "FATHER" },
				player_controlled: { active: true },
			},
		},
	],
	map: { width: 10, height: 8, father_tiles: [[0]], son_tiles: [[0]] },
	battle: null,
};

/**
 * Connect a mock Godot client to a WS server.
 * Responds to commands: get_state, move, interact, switch_era.
 *
 * @param {number} port - WS server port
 * @param {object} [opts]
 * @param {object} [opts.state] - Custom state to return (defaults to MOCK_STATE)
 * @returns {Promise<{ ws: WebSocket, close: () => void }>}
 */
export function connectMockGodot(port, opts = {}) {
	const state = structuredClone(opts.state ?? MOCK_STATE);

	return new Promise((resolve, reject) => {
		const ws = new WebSocket(`ws://localhost:${port}`);

		ws.on("error", reject);

		ws.on("open", () => {
			ws.send(
				JSON.stringify({
					type: "handshake",
					client_type: "godot",
					name: "mock-godot",
				}),
			);
		});

		ws.on("message", (raw) => {
			const msg = JSON.parse(raw.toString());

			if (msg.type === "handshake_ack") {
				resolve({ ws, close: () => ws.close() });
				return;
			}

			if (msg.type === "command") {
				handleCommand(ws, msg, state);
			}
		});
	});
}

function handleCommand(ws, msg, state) {
	const { id, action, payload } = msg;

	// Always ack first
	ws.send(
		JSON.stringify({ type: "command_ack", id, success: true, error: null }),
	);

	switch (action) {
		case "get_state":
			ws.send(JSON.stringify({ type: "state_snapshot", data: state }));
			break;

		case "move":
			ws.send(
				JSON.stringify({
					type: "state_event",
					event: "entity_updated",
					data: {
						entity_id: "FatherPlayer",
						components: {
							grid_position: {
								col: 3,
								row: 2,
								facing: payload?.direction || "right",
							},
						},
					},
				}),
			);
			break;

		case "interact":
			// Override ack with failure for interact (nothing in front)
			break;

		case "switch_era": {
			state.active_era = state.active_era === "FATHER" ? "SON" : "FATHER";
			state.active_entity_id =
				state.active_era === "FATHER" ? "father" : "son";
			ws.send(
				JSON.stringify({
					type: "state_event",
					event: "era_switched",
					data: {
						active_era: state.active_era,
						active_entity_id: state.active_entity_id,
					},
				}),
			);
			break;
		}
	}
}
```

- [ ] **Step 2: Commit**

```bash
git add project/server/packages/game-server/src/__tests__/helpers/mock-godot.js
git commit -m "test: extract reusable mock-godot WS client helper"
```

---

## Task 3: Extract test-server helper

**Files:**
- Create: `project/server/packages/game-server/src/__tests__/helpers/test-server.js`

Boots an isolated HTTP + WS + MCP server on a random port. Used by all Vitest tests.

- [ ] **Step 1: Create the test-server helper**

Create `project/server/packages/game-server/src/__tests__/helpers/test-server.js`:

```js
import { createServer } from "node:http";
import { WebSocketServer } from "ws";
import { createMastraServer } from "../../mastra/index.js";
import { EventQueueRegistry } from "../../mcp/event-queue.js";
import { GameStateStore } from "../../state/store.js";
import { ConnectionManager } from "../../ws/connection.js";

/**
 * Boot an isolated game server on a random available port.
 * Returns everything needed for testing + a cleanup function.
 *
 * @returns {Promise<{
 *   port: number,
 *   baseUrl: string,
 *   mcpUrl: string,
 *   stateStore: GameStateStore,
 *   connMgr: ConnectionManager,
 *   eventRegistry: EventQueueRegistry,
 *   cleanup: () => Promise<void>,
 * }>}
 */
export async function startTestServer() {
	const stateStore = new GameStateStore();
	const connMgr = new ConnectionManager(stateStore);
	const eventRegistry = new EventQueueRegistry();
	eventRegistry.create("default");

	connMgr.onEvent((direction, msg) => {
		if (
			direction === "from_godot" &&
			(msg.type === "state_event" || msg.type === "state_snapshot")
		) {
			eventRegistry.broadcast(msg);
		}
	});

	const { mcpServer } = createMastraServer(connMgr, stateStore, eventRegistry);

	const httpServer = createServer(async (req, res) => {
		const url = new URL(req.url || "", `http://localhost`);
		if (url.pathname === "/mcp") {
			await mcpServer.startHTTP({ url, httpPath: "/mcp", req, res });
			return;
		}
		res.writeHead(200, { "Content-Type": "application/json" });
		res.end(JSON.stringify({ status: "ok" }));
	});

	const wss = new WebSocketServer({ server: httpServer });
	wss.on("connection", (ws) => connMgr.handleConnection(ws));

	// Listen on port 0 = random available port
	await new Promise((resolve) => httpServer.listen(0, resolve));
	const port = httpServer.address().port;

	const cleanup = () =>
		new Promise((resolve) => {
			eventRegistry.dispose();
			wss.close();
			httpServer.close(resolve);
		});

	return {
		port,
		baseUrl: `http://localhost:${port}`,
		mcpUrl: `http://localhost:${port}/mcp`,
		stateStore,
		connMgr,
		eventRegistry,
		cleanup,
	};
}
```

- [ ] **Step 2: Commit**

```bash
git add project/server/packages/game-server/src/__tests__/helpers/test-server.js
git commit -m "test: extract test-server helper with random port allocation"
```

---

## Task 4: Migrate MCP transport tests to Vitest

**Files:**
- Create: `project/server/packages/game-server/src/__tests__/mcp-transport.test.js`

Migrates all 19 assertions from `src/test-mcp.js` into proper describe/it blocks.

- [ ] **Step 1: Write the MCP transport test file**

Create `project/server/packages/game-server/src/__tests__/mcp-transport.test.js`:

```js
import { afterAll, beforeAll, describe, expect, it } from "vitest";
import { connectMockGodot } from "./helpers/mock-godot.js";
import { startTestServer } from "./helpers/test-server.js";

const HEADERS = {
	"Content-Type": "application/json",
	Accept: "application/json, text/event-stream",
};

let server;
let mockGodot;
let sessionId = null;

/** Parse SSE response body into JSON-RPC result */
function parseSSE(body) {
	for (const line of body.split("\n")) {
		if (line.startsWith("data: ")) {
			return JSON.parse(line.slice(6));
		}
	}
	return JSON.parse(body);
}

async function mcpRequest(method, params = {}, id = 1) {
	const headers = { ...HEADERS };
	if (sessionId) headers["mcp-session-id"] = sessionId;

	const res = await fetch(server.mcpUrl, {
		method: "POST",
		headers,
		body: JSON.stringify({ jsonrpc: "2.0", id, method, params }),
	});

	const sid = res.headers.get("mcp-session-id");
	if (sid) sessionId = sid;

	const text = await res.text();
	return { status: res.status, body: parseSSE(text), raw: text };
}

function sleep(ms) {
	return new Promise((r) => setTimeout(r, ms));
}

beforeAll(async () => {
	server = await startTestServer();
	mockGodot = await connectMockGodot(server.port);
	await sleep(500); // Wait for handshake
});

afterAll(async () => {
	mockGodot?.close();
	await server?.cleanup();
});

describe("MCP Initialize", () => {
	it("returns server info and tools capability", async () => {
		const init = await mcpRequest("initialize", {
			protocolVersion: "2025-03-26",
			capabilities: {},
			clientInfo: { name: "test-mcp", version: "0.1.0" },
		});

		expect(init.status).toBe(200);
		expect(init.body.result.serverInfo.name).toBe("Legend Dad Game Server");
		expect(init.body.result.capabilities.tools).toBeDefined();

		// Send initialized notification
		await fetch(server.mcpUrl, {
			method: "POST",
			headers: { ...HEADERS, "mcp-session-id": sessionId },
			body: JSON.stringify({
				jsonrpc: "2.0",
				method: "notifications/initialized",
			}),
		});
		await sleep(200);
	});
});

describe("MCP tools/list", () => {
	it("returns all 5 tools", async () => {
		const tools = await mcpRequest("tools/list", {}, 2);

		expect(tools.status).toBe(200);
		const toolNames = tools.body.result.tools.map((t) => t.name).sort();
		expect(toolNames).toEqual([
			"get_state",
			"interact",
			"move",
			"poll_events",
			"switch_era",
		]);
	});
});

describe("MCP tool calls", () => {
	it("get_state returns game state with FATHER era", async () => {
		const state = await mcpRequest(
			"tools/call",
			{ name: "get_state", arguments: {} },
			3,
		);

		expect(state.status).toBe(200);
		const data = JSON.parse(state.body.result.content[0].text);
		expect(data.state).toBeDefined();
		expect(data.state.active_era).toBe("FATHER");
	});

	it("move returns success", async () => {
		const move = await mcpRequest(
			"tools/call",
			{ name: "move", arguments: { direction: "right" } },
			4,
		);

		expect(move.status).toBe(200);
		const data = JSON.parse(move.body.result.content[0].text);
		expect(data.success).toBe(true);
	});

	it("poll_events returns events after move", async () => {
		await sleep(300); // Wait for event propagation

		const poll = await mcpRequest(
			"tools/call",
			{ name: "poll_events", arguments: {} },
			5,
		);

		expect(poll.status).toBe(200);
		const data = JSON.parse(poll.body.result.content[0].text);
		expect(data.count).toBeGreaterThan(0);
		expect(data.events.some((e) => e.event === "entity_updated")).toBe(true);
	});

	it("poll_events drains queue (second call empty)", async () => {
		const poll = await mcpRequest(
			"tools/call",
			{ name: "poll_events", arguments: {} },
			6,
		);

		const data = JSON.parse(poll.body.result.content[0].text);
		expect(data.count).toBe(0);
	});
});
```

- [ ] **Step 2: Run the tests**

```bash
cd project/server/packages/game-server && pnpm test
```

Expected: All tests pass (6 test cases covering the 19 original assertions).

- [ ] **Step 3: Commit**

```bash
git add project/server/packages/game-server/src/__tests__/mcp-transport.test.js
git commit -m "test: migrate MCP transport tests to vitest"
```

---

## Task 5: Migrate agent test to Vitest

**Files:**
- Create: `project/server/packages/game-server/src/__tests__/agent.test.js`

The agent test requires API keys. It is skipped if neither `ZAI_API_KEY` nor `ALIBABA_API_KEY` is set.

- [ ] **Step 1: Write the agent test file**

Create `project/server/packages/game-server/src/__tests__/agent.test.js`:

```js
import { afterAll, beforeAll, describe, expect, it } from "vitest";
import { createGameAgent } from "../../mastra/agent.js";
import { createMastraServer } from "../../mastra/index.js";
import { connectMockGodot } from "./helpers/mock-godot.js";
import { startTestServer } from "./helpers/test-server.js";

const HAS_API_KEY = !!(process.env.ZAI_API_KEY || process.env.ALIBABA_API_KEY);

let server;
let mockGodot;

beforeAll(async () => {
	if (!HAS_API_KEY) return;
	server = await startTestServer();
	mockGodot = await connectMockGodot(server.port);
	// Wait for handshake + initial state
	await new Promise((r) => setTimeout(r, 1000));
});

afterAll(async () => {
	mockGodot?.close();
	await server?.cleanup();
});

describe.skipIf(!HAS_API_KEY)("Agent integration", () => {
	it("calls tools and receives game state", async () => {
		const providers = [
			{
				name: "zai",
				url: "https://api.z.ai/api/coding/paas/v4",
				apiKey: process.env.ZAI_API_KEY || "",
				model: process.env.ZAI_MODEL || "glm-5.1",
			},
			{
				name: "alibaba",
				url: "https://coding-intl.dashscope.aliyuncs.com/v1",
				apiKey: process.env.ALIBABA_API_KEY || "",
				model: process.env.ALIBABA_MODEL || "qwen3.5-plus",
			},
		];

		const { tools } = createMastraServer(
			server.connMgr,
			server.stateStore,
		);

		const agent = await createGameAgent(tools, {
			providers,
			stateStore: server.stateStore,
		});

		const result = await agent.generate(
			"Get the current game state and tell me where the player is.",
			{ maxSteps: 5 },
		);

		expect(result.text).toBeTruthy();
		// Agent should have called at least get_state
		const toolCalls = result.steps?.flatMap((s) => s.toolCalls || []) || [];
		expect(toolCalls.length).toBeGreaterThan(0);
		expect(toolCalls.some((tc) => tc.toolName === "get_state")).toBe(true);
	}, 30_000); // 30s timeout for LLM round-trip
});
```

- [ ] **Step 2: Run tests (will skip without API key)**

```bash
cd project/server/packages/game-server && pnpm test
```

Expected: MCP transport tests pass. Agent test shows "skipped" (unless API keys are set).

- [ ] **Step 3: Commit**

```bash
git add project/server/packages/game-server/src/__tests__/agent.test.js
git commit -m "test: migrate agent integration test to vitest (skip without API key)"
```

---

## Task 6: Delete old test scripts

**Files:**
- Delete: `project/server/packages/game-server/src/test-mcp.js`
- Delete: `project/server/packages/game-server/src/test-agent.js`

- [ ] **Step 1: Verify vitest tests pass before deleting**

```bash
cd project/server/packages/game-server && pnpm test
```

Expected: All non-skipped tests pass.

- [ ] **Step 2: Delete old scripts**

```bash
rm project/server/packages/game-server/src/test-mcp.js
rm project/server/packages/game-server/src/test-agent.js
```

- [ ] **Step 3: Commit**

```bash
git add -u project/server/packages/game-server/src/test-mcp.js project/server/packages/game-server/src/test-agent.js
git commit -m "chore: remove old test scripts (migrated to vitest)"
```

---

## Task 7: Create Playwright E2E package

**Files:**
- Create: `project/server/packages/e2e/package.json`
- Create: `project/server/packages/e2e/playwright.config.js`

- [ ] **Step 1: Create e2e package.json**

Create `project/server/packages/e2e/package.json`:

```json
{
	"name": "@legend-dad/e2e",
	"version": "0.0.1",
	"private": true,
	"type": "module",
	"scripts": {
		"test": "playwright test",
		"test:headed": "playwright test --headed"
	},
	"devDependencies": {
		"@playwright/test": "^1.52.0"
	}
}
```

- [ ] **Step 2: Install dependencies**

```bash
cd project/server && pnpm install
cd packages/e2e && pnpm exec playwright install chromium
```

- [ ] **Step 3: Create playwright.config.js**

Create `project/server/packages/e2e/playwright.config.js`:

```js
import { defineConfig } from "@playwright/test";

export default defineConfig({
	testDir: "./tests",
	timeout: 60_000,
	retries: 0,
	use: {
		baseURL: "http://localhost:8080",
		screenshot: "only-on-failure",
		trace: "retain-on-failure",
	},
	projects: [
		{
			name: "chromium",
			use: { browserName: "chromium" },
		},
	],
	outputDir: "../../../../build/_artifacts/latest/screenshots",
	webServer: [
		{
			command: "node src/index.js",
			cwd: "../game-server",
			port: 3000,
			reuseExistingServer: true,
			timeout: 10_000,
		},
		{
			command:
				"node ../../../../scripts/serve_web.js ../../../../build/_artifacts/latest/web",
			port: 8080,
			reuseExistingServer: true,
			timeout: 10_000,
		},
	],
});
```

- [ ] **Step 4: Commit**

```bash
git add project/server/packages/e2e/package.json project/server/packages/e2e/playwright.config.js project/server/pnpm-lock.yaml
git commit -m "chore: scaffold @legend-dad/e2e playwright package"
```

---

## Task 8: Write Playwright smoke test

**Files:**
- Create: `project/server/packages/e2e/tests/smoke.spec.js`

- [ ] **Step 1: Write smoke test**

Create `project/server/packages/e2e/tests/smoke.spec.js`:

```js
import { expect, test } from "@playwright/test";

test.describe("Godot web build smoke test", () => {
	test("page loads and Godot canvas renders", async ({ page }) => {
		await page.goto("/");

		// Godot creates a <canvas> element for rendering
		const canvas = page.locator("canvas");
		await expect(canvas).toBeVisible({ timeout: 30_000 });

		// Verify the canvas has non-zero dimensions (WASM loaded and rendering)
		const box = await canvas.boundingBox();
		expect(box.width).toBeGreaterThan(0);
		expect(box.height).toBeGreaterThan(0);
	});

	test("WebSocket connection is established", async ({ page }) => {
		// Listen for WebSocket connections
		const wsPromise = page.waitForEvent("websocket", {
			timeout: 30_000,
		});

		await page.goto("/");

		const ws = await wsPromise;
		expect(ws.url()).toContain("localhost:3000");

		// Wait for handshake to complete
		const framePromise = ws.waitForEvent("framesent", {
			predicate: (frame) => {
				try {
					const data = JSON.parse(frame.payload);
					return data.type === "handshake";
				} catch {
					return false;
				}
			},
			timeout: 10_000,
		});

		await framePromise;
	});
});
```

- [ ] **Step 2: Run the smoke test (requires a web build)**

This test needs `task build` to have been run and `build/_artifacts/latest/web/` to exist. If no build exists, the webServer will fail to start and the test will error.

```bash
cd project/server/packages/e2e && pnpm test
```

Expected: Both smoke tests pass (page loads, WS connects).

- [ ] **Step 3: Commit**

```bash
git add project/server/packages/e2e/tests/smoke.spec.js
git commit -m "test: add playwright smoke test for godot web build"
```

---

## Task 9: Write Playwright MCP round-trip test

**Files:**
- Create: `project/server/packages/e2e/tests/mcp-roundtrip.spec.js`

- [ ] **Step 1: Write MCP round-trip test**

Create `project/server/packages/e2e/tests/mcp-roundtrip.spec.js`:

```js
import { expect, test } from "@playwright/test";

const MCP_URL = "http://localhost:3000/mcp";
const MCP_HEADERS = {
	"Content-Type": "application/json",
	Accept: "application/json, text/event-stream",
};

/** Parse SSE response body into JSON-RPC result */
function parseSSE(body) {
	for (const line of body.split("\n")) {
		if (line.startsWith("data: ")) {
			return JSON.parse(line.slice(6));
		}
	}
	return JSON.parse(body);
}

test.describe("MCP round-trip with live Godot", () => {
	let sessionId = null;

	test.beforeAll(async ({ request }) => {
		// Initialize MCP session
		const res = await request.post(MCP_URL, {
			headers: MCP_HEADERS,
			data: {
				jsonrpc: "2.0",
				id: 1,
				method: "initialize",
				params: {
					protocolVersion: "2025-03-26",
					capabilities: {},
					clientInfo: { name: "e2e-test", version: "0.1.0" },
				},
			},
		});

		expect(res.status()).toBe(200);
		sessionId = res.headers()["mcp-session-id"];

		// Send initialized notification
		await request.post(MCP_URL, {
			headers: { ...MCP_HEADERS, "mcp-session-id": sessionId },
			data: {
				jsonrpc: "2.0",
				method: "notifications/initialized",
			},
		});
	});

	test("Godot is connected and MCP lists tools", async ({ page, request }) => {
		// First verify Godot is loaded in browser
		await page.goto("/");
		const canvas = page.locator("canvas");
		await expect(canvas).toBeVisible({ timeout: 30_000 });

		// List MCP tools
		const res = await request.post(MCP_URL, {
			headers: { ...MCP_HEADERS, "mcp-session-id": sessionId },
			data: { jsonrpc: "2.0", id: 2, method: "tools/list", params: {} },
		});

		expect(res.status()).toBe(200);
		const body = parseSSE(await res.text());
		const toolNames = body.result.tools.map((t) => t.name).sort();
		expect(toolNames).toContain("move");
		expect(toolNames).toContain("get_state");
	});

	test("MCP get_state reflects live game", async ({ page, request }) => {
		await page.goto("/");
		const canvas = page.locator("canvas");
		await expect(canvas).toBeVisible({ timeout: 30_000 });

		// Wait for WS connection + state sync
		await page.waitForTimeout(2000);

		const res = await request.post(MCP_URL, {
			headers: { ...MCP_HEADERS, "mcp-session-id": sessionId },
			data: {
				jsonrpc: "2.0",
				id: 3,
				method: "tools/call",
				params: { name: "get_state", arguments: {} },
			},
		});

		expect(res.status()).toBe(200);
		const body = parseSSE(await res.text());
		const data = JSON.parse(body.result.content[0].text);
		expect(data.state).toBeDefined();
		expect(data.state.active_era).toBeDefined();
	});
});
```

- [ ] **Step 2: Run the full E2E suite**

```bash
cd project/server/packages/e2e && pnpm test
```

Expected: All E2E tests pass (smoke + MCP round-trip).

- [ ] **Step 3: Commit**

```bash
git add project/server/packages/e2e/tests/mcp-roundtrip.spec.js
git commit -m "test: add playwright MCP round-trip e2e test"
```

---

## Task 10: Install GUT addon

**Files:**
- Create: `project/hosts/complete-app/addons/gut/` (downloaded from GitHub)
- Modify: `project/hosts/complete-app/project.godot` (enable plugin)

- [ ] **Step 1: Download GUT v9.x**

```bash
cd project/hosts/complete-app/addons && \
curl -L https://github.com/bitwes/Gut/archive/refs/tags/v9.3.0.tar.gz | tar xz && \
mv Gut-9.3.0/addons/gut . && \
rm -rf Gut-9.3.0
```

If v9.3.0 is not available, check the latest tag at https://github.com/bitwes/Gut/tags and adjust accordingly.

- [ ] **Step 2: Enable GUT plugin in project.godot**

In `project/hosts/complete-app/project.godot`, update the `enabled` line under `[editor_plugins]` to include GUT:

Change:
```
enabled=PackedStringArray("res://addons/beehave/plugin.cfg", "res://addons/dialogue_manager/plugin.cfg", "res://addons/gecs/plugin.cfg", "res://addons/guide/plugin.cfg", "res://addons/phantom_camera/plugin.cfg")
```

To:
```
enabled=PackedStringArray("res://addons/beehave/plugin.cfg", "res://addons/dialogue_manager/plugin.cfg", "res://addons/gecs/plugin.cfg", "res://addons/guide/plugin.cfg", "res://addons/gut/plugin.cfg", "res://addons/phantom_camera/plugin.cfg")
```

- [ ] **Step 3: Commit GUT addon**

```bash
git add project/hosts/complete-app/addons/gut/ project/hosts/complete-app/project.godot
git commit -m "chore: install GUT v9.3.0 test framework addon"
```

---

## Task 11: Create GUT scaffold test

**Files:**
- Create: `project/hosts/complete-app/.gutconfig.json`
- Create: `project/hosts/complete-app/tests/test_example.gd`

- [ ] **Step 1: Create .gutconfig.json**

Create `project/hosts/complete-app/.gutconfig.json`:

```json
{
	"dirs": ["res://tests/"],
	"prefix": "test_",
	"suffix": ".gd",
	"include_subdirs": true
}
```

- [ ] **Step 2: Create scaffold test**

Create `project/hosts/complete-app/tests/test_example.gd`:

```gdscript
extends GutTest

func test_scaffold_passes():
	assert_true(true, "GUT scaffold test works")
```

- [ ] **Step 3: Run GUT headless**

```bash
/Users/apprenticegc/Work/lunar-horse/tools/Godot.app/Contents/MacOS/Godot \
  --headless --path project/hosts/complete-app \
  -s addons/gut/gut_cmdln.gd -gexit
```

Expected: GUT runs, finds 1 test, reports 1 passed, exits with code 0.

Note: Godot may print warnings from ECS/Beehave autoloads in headless mode — these are harmless and expected.

- [ ] **Step 4: Commit**

```bash
git add project/hosts/complete-app/.gutconfig.json project/hosts/complete-app/tests/test_example.gd
git commit -m "test: add GUT scaffold test for godot"
```

---

## Task 12: Add Taskfile test commands

**Files:**
- Modify: `Taskfile.yml`

- [ ] **Step 1: Add test tasks to Taskfile.yml**

Add the following tasks after the existing `changelog` task in `Taskfile.yml`:

```yaml
  test:
    desc: Run all test suites (pytest, vitest, GUT, playwright)
    cmds:
      - task: test:python
      - task: test:server
      - task: test:godot
      - task: test:e2e

  test:python:
    desc: Run Python tests (pytest)
    cmds:
      - python3 -m pytest tests/ -v

  test:server:
    desc: Run game-server integration tests (vitest)
    dir: "{{.GAME_SERVER_DIR}}"
    cmds:
      - pnpm test

  test:godot:
    desc: Run Godot unit tests (GUT, headless)
    cmds:
      - >-
        {{.GODOT_PATH}} --headless
        --path {{.GODOT_PROJECT_DIR}}
        -s addons/gut/gut_cmdln.gd -gexit

  test:e2e:
    desc: Run browser E2E tests (Playwright, requires web build)
    dir: "project/server/packages/e2e"
    cmds:
      - pnpm exec playwright test
```

- [ ] **Step 2: Verify task test:python works**

```bash
task test:python
```

Expected: 32 pytest tests pass.

- [ ] **Step 3: Verify task test:server works**

```bash
task test:server
```

Expected: Vitest MCP transport tests pass (agent test skipped without API key).

- [ ] **Step 4: Verify task test:godot works**

```bash
task test:godot
```

Expected: GUT reports 1 test passed.

- [ ] **Step 5: Commit**

```bash
git add Taskfile.yml
git commit -m "feat: add unified test commands to taskfile"
```

---

## Task 13: Update AGENTS.md testing section

**Files:**
- Modify: `AGENTS.md`

- [ ] **Step 1: Update the Testing section in AGENTS.md**

Replace the existing `## Testing` section at the bottom of `AGENTS.md` with:

```markdown
## Testing

| Layer | Runner | Command | Location |
|---|---|---|---|
| All | Taskfile | `task test` | All suites sequentially |
| Python | pytest | `task test:python` | `tests/` |
| Node.js | Vitest | `task test:server` | `project/server/packages/game-server/src/__tests__/` |
| Godot | GUT | `task test:godot` | `project/hosts/complete-app/tests/` |
| Browser E2E | Playwright | `task test:e2e` | `project/server/packages/e2e/tests/` |

- `task test:server` runs Vitest tests against the game server (MCP transport, agent integration)
- `task test:e2e` auto-starts servers if not already running (requires web build from `task build`)
- Agent integration tests require API keys (`ZAI_API_KEY` or `ALIBABA_API_KEY`) — skipped otherwise
- Playwright uses Chromium only — game targets web browsers
- Screenshots stored in `build/_artifacts/latest/screenshots/`
```

- [ ] **Step 2: Also add `task test` to the Key Commands section**

In the `## Key Commands` section, add after `task changelog`:

```bash
task test            # Run all test suites (pytest, vitest, GUT, playwright)
task test:python     # Python tests only
task test:server     # Game server tests only
task test:godot      # Godot unit tests only (headless)
task test:e2e        # Browser E2E tests only (requires web build)
```

- [ ] **Step 3: Commit**

```bash
git add AGENTS.md
git commit -m "docs: update AGENTS.md with testing infrastructure"
```
