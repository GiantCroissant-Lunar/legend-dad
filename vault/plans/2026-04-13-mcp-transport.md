# MCP Streamable HTTP Transport Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Wire the Mastra MCPServer to a Streamable HTTP transport on `/mcp` so Claude Code can call game tools against a running game server with a live Godot connection, and poll for game state events.

**Architecture:** Add an `/mcp` route to the existing HTTP server on port 3000. Create an `EventQueue` class that buffers game events per MCP session. Add a `poll_events` tool that drains the queue. Register the server in `.claude/settings.json`.

**Tech Stack:** @mastra/mcp (MCPServer.startHTTP), @mastra/core/tools (createTool), zod, node:http

**Spec:** `vault/specs/2026-04-13-mcp-transport-design.md`

---

## File Map

| File | Action | Responsibility |
|------|--------|---------------|
| `src/mcp/event-queue.js` | Create | EventQueue class + EventQueueRegistry |
| `src/mastra/tools/poll-events.js` | Create | poll_events Mastra tool |
| `src/mastra/index.js` | Modify | Add poll_events tool to MCPServer |
| `src/index.js` | Modify | Route `/mcp` to mcpServer.startHTTP(), wire event queues |
| `.claude/settings.json` | Create | Register MCP server for Claude Code |

All paths relative to `project/server/packages/game-server/`.

---

### Task 1: EventQueue Class

**Files:**
- Create: `project/server/packages/game-server/src/mcp/event-queue.js`

- [ ] **Step 1: Create EventQueue class**

```js
// project/server/packages/game-server/src/mcp/event-queue.js

/**
 * Per-session ring buffer for game events.
 * MCP clients drain this via the poll_events tool.
 */
export class EventQueue {
	constructor(maxSize = 200) {
		this._maxSize = maxSize;
		/** @type {Array<{type: string, event?: string, data: object, timestamp: string}>} */
		this._buffer = [];
	}

	/**
	 * Push a game event into the buffer. Drops oldest if full.
	 * @param {object} msg — raw state_event or state_snapshot from Godot
	 */
	push(msg) {
		this._buffer.push({
			type: msg.type,
			event: msg.event ?? null,
			data: msg.data ?? {},
			timestamp: new Date().toISOString(),
		});
		if (this._buffer.length > this._maxSize) {
			this._buffer.shift();
		}
	}

	/**
	 * Return all buffered events and clear the buffer.
	 * @returns {Array<object>}
	 */
	drain() {
		const events = this._buffer;
		this._buffer = [];
		return events;
	}

	get size() {
		return this._buffer.length;
	}
}

/**
 * Registry of MCP session → EventQueue.
 * Handles creation, lookup, cleanup, and inactivity garbage collection.
 */
export class EventQueueRegistry {
	constructor({ inactivityMs = 5 * 60 * 1000 } = {}) {
		/** @type {Map<string, { queue: EventQueue, lastAccess: number }>} */
		this._sessions = new Map();
		this._inactivityMs = inactivityMs;

		// GC sweep every 60s
		this._gcInterval = setInterval(() => this._sweep(), 60_000);
		this._gcInterval.unref(); // don't keep process alive
	}

	/**
	 * Create a queue for a new MCP session.
	 * @param {string} sessionId
	 * @returns {EventQueue}
	 */
	create(sessionId) {
		const queue = new EventQueue();
		this._sessions.set(sessionId, { queue, lastAccess: Date.now() });
		console.log(`[mcp] event queue created for session ${sessionId}`);
		return queue;
	}

	/**
	 * Get the queue for a session, or null if not found.
	 * Updates last-access timestamp.
	 * @param {string} sessionId
	 * @returns {EventQueue|null}
	 */
	get(sessionId) {
		const entry = this._sessions.get(sessionId);
		if (!entry) return null;
		entry.lastAccess = Date.now();
		return entry.queue;
	}

	/**
	 * Remove a session's queue.
	 * @param {string} sessionId
	 */
	remove(sessionId) {
		if (this._sessions.delete(sessionId)) {
			console.log(`[mcp] event queue removed for session ${sessionId}`);
		}
	}

	/**
	 * Broadcast a game event to all active session queues.
	 * @param {object} msg
	 */
	broadcast(msg) {
		for (const { queue } of this._sessions.values()) {
			queue.push(msg);
		}
	}

	/** @private Sweep stale sessions */
	_sweep() {
		const now = Date.now();
		for (const [sessionId, entry] of this._sessions) {
			if (now - entry.lastAccess > this._inactivityMs) {
				this.remove(sessionId);
			}
		}
	}

	/** Stop the GC interval (for clean shutdown / tests). */
	dispose() {
		clearInterval(this._gcInterval);
	}
}
```

- [ ] **Step 2: Verify file parses cleanly**

Run: `cd project/server/packages/game-server && node -e "import('./src/mcp/event-queue.js').then(() => console.log('OK'))"`
Expected: `OK`

- [ ] **Step 3: Commit**

```bash
git add project/server/packages/game-server/src/mcp/event-queue.js
git commit -m "feat: add EventQueue and EventQueueRegistry for MCP sessions"
```

---

### Task 2: poll_events Tool

**Files:**
- Create: `project/server/packages/game-server/src/mastra/tools/poll-events.js`

- [ ] **Step 1: Create poll_events tool**

```js
// project/server/packages/game-server/src/mastra/tools/poll-events.js
import { createTool } from "@mastra/core/tools";
import { z } from "zod";

/**
 * Create a poll_events tool bound to an EventQueueRegistry.
 * MCP clients call this to drain buffered game events.
 *
 * NOTE: Mastra's startHTTP does not expose the MCP session ID to tool
 * execute functions. We use a single shared queue that broadcasts to
 * all MCP sessions via the registry. For poll_events, we use a
 * dedicated per-tool-invocation approach: the registry broadcasts to
 * all queues, and each MCP client drains its own queue.
 *
 * Since Claude Code is typically the only MCP client, we use a
 * default session key. If multi-session support is needed later,
 * the sessionId can be passed as an input parameter.
 *
 * @param {import('../mcp/event-queue.js').EventQueueRegistry} registry
 */
export function createPollEventsTool(registry) {
	return createTool({
		id: "poll_events",
		description:
			"Drain all game events buffered since your last poll. Returns state_event and state_snapshot messages from Godot. Call this between actions to see what changed in the game world (entity moves, era switches, battle starts, interactions).",
		inputSchema: z.object({
			sessionId: z
				.string()
				.optional()
				.describe(
					"MCP session ID. Omit to use the default session.",
				),
		}),
		outputSchema: z.object({
			events: z.array(
				z.object({
					type: z.string(),
					event: z.string().nullable(),
					data: z.any(),
					timestamp: z.string(),
				}),
			),
			count: z.number(),
		}),
		execute: async (input) => {
			// Try provided sessionId, fall back to first available queue
			let queue = null;
			if (input.sessionId) {
				queue = registry.get(input.sessionId);
			}
			if (!queue) {
				// Fall back: get the first session's queue (single-client case)
				for (const [id] of registry._sessions) {
					queue = registry.get(id);
					break;
				}
			}
			if (!queue) {
				return { events: [], count: 0 };
			}
			const events = queue.drain();
			return { events, count: events.length };
		},
	});
}
```

- [ ] **Step 2: Verify file parses cleanly**

Run: `cd project/server/packages/game-server && node -e "import('./src/mastra/tools/poll-events.js').then(() => console.log('OK'))"`
Expected: `OK`

- [ ] **Step 3: Commit**

```bash
git add project/server/packages/game-server/src/mastra/tools/poll-events.js
git commit -m "feat: add poll_events MCP tool for draining game event buffer"
```

---

### Task 3: Register poll_events in MCPServer

**Files:**
- Modify: `project/server/packages/game-server/src/mastra/index.js`

- [ ] **Step 1: Update createMastraServer to accept registry and add poll_events**

Replace the entire file content with:

```js
// project/server/packages/game-server/src/mastra/index.js
import { MCPServer } from "@mastra/mcp";
import { createGetStateTool } from "./tools/get-state.js";
import { createInteractTool } from "./tools/interact.js";
import { createMoveTool } from "./tools/move.js";
import { createPollEventsTool } from "./tools/poll-events.js";
import { createSwitchEraTool } from "./tools/switch-era.js";

/**
 * Initialize Mastra tools and MCP server, bound to live connection/state instances.
 *
 * @param {import('../ws/connection.js').ConnectionManager} connMgr
 * @param {import('../state/store.js').GameStateStore} stateStore
 * @param {import('../mcp/event-queue.js').EventQueueRegistry} [eventRegistry]
 */
export function createMastraServer(connMgr, stateStore, eventRegistry) {
	const moveTool = createMoveTool(connMgr);
	const interactTool = createInteractTool(connMgr);
	const switchEraTool = createSwitchEraTool(connMgr);
	const getStateTool = createGetStateTool(stateStore);

	const tools = {
		move: moveTool,
		interact: interactTool,
		switch_era: switchEraTool,
		get_state: getStateTool,
	};

	// Add poll_events only when an event registry is provided (MCP mode)
	if (eventRegistry) {
		tools.poll_events = createPollEventsTool(eventRegistry);
	}

	const mcpServer = new MCPServer({
		id: "legend-dad-game",
		name: "Legend Dad Game Server",
		version: "0.1.0",
		description:
			"Control the Legend Dad game — move characters, interact with objects, switch timelines, and observe game state.",
		tools,
	});

	return {
		mcpServer,
		tools: { moveTool, interactTool, switchEraTool, getStateTool },
	};
}
```

Key changes:
- Import `createPollEventsTool`
- Accept optional `eventRegistry` parameter (3rd arg)
- Conditionally add `poll_events` tool when registry is provided
- Existing callers (like `test-agent.js`) pass no 3rd arg and work unchanged

- [ ] **Step 2: Verify existing test-agent still parses**

Run: `cd project/server/packages/game-server && node -e "import('./src/mastra/index.js').then(() => console.log('OK'))"`
Expected: `OK`

- [ ] **Step 3: Commit**

```bash
git add project/server/packages/game-server/src/mastra/index.js
git commit -m "feat: register poll_events tool in MCPServer when event registry provided"
```

---

### Task 4: Wire HTTP Transport in Server Entry Point

**Files:**
- Modify: `project/server/packages/game-server/src/index.js`

- [ ] **Step 1: Update index.js to route /mcp and wire event queues**

Replace the entire file content with:

```js
// project/server/packages/game-server/src/index.js
import { createServer } from "node:http";
import { WebSocketServer } from "ws";
import { EventQueueRegistry } from "./mcp/event-queue.js";
import { createMastraServer } from "./mastra/index.js";
import { ContextBuilder } from "./replay/context-builder.js";
import { initReplayDB } from "./replay/db.js";
import { initEmbedder } from "./replay/embedder.js";
import { Recorder } from "./replay/recorder.js";
import { GameStateStore } from "./state/store.js";
import { ConnectionManager } from "./ws/connection.js";

const PORT = Number.parseInt(process.env.PORT || "3000", 10);

async function main() {
	// --- State & connections ---
	const stateStore = new GameStateStore();
	const connMgr = new ConnectionManager(stateStore);

	// --- MCP event queue registry ---
	const eventRegistry = new EventQueueRegistry();

	// Subscribe registry to all game events from Godot
	connMgr.onEvent((direction, msg) => {
		if (
			direction === "from_godot" &&
			(msg.type === "state_event" || msg.type === "state_snapshot")
		) {
			eventRegistry.broadcast(msg);
		}
	});

	// --- Replay system ---
	let recorder = null;
	let contextBuilder = null;
	try {
		const db = await initReplayDB();
		await initEmbedder();
		recorder = new Recorder(db);
		recorder.setStateStore(stateStore);
		contextBuilder = new ContextBuilder(db);

		// Hook recorder into connection manager
		connMgr.onEvent((direction, msg) => {
			recorder.recordEvent(direction, msg).catch((err) => {
				console.error("[replay] record error:", err.message);
			});
		});

		console.log("[replay] recording enabled");
	} catch (err) {
		console.warn("[replay] disabled —", err.message);
		console.warn("[replay] server will run without replay recording");
	}

	// --- Mastra MCP server (with event registry for poll_events) ---
	const { mcpServer } = createMastraServer(connMgr, stateStore, eventRegistry);

	// --- HTTP server (health check + MCP endpoint) ---
	const server = createServer(async (req, res) => {
		const url = new URL(req.url || "", `http://localhost:${PORT}`);

		// MCP Streamable HTTP endpoint
		if (url.pathname === "/mcp") {
			try {
				await mcpServer.startHTTP({
					url,
					httpPath: "/mcp",
					req,
					res,
					options: {
						onsessioninitialized: (sessionId) => {
							eventRegistry.create(sessionId);
							console.log(`[mcp] session initialized: ${sessionId}`);
						},
					},
				});
			} catch (err) {
				console.error("[mcp] error:", err.message);
				if (!res.headersSent) {
					res.writeHead(500, { "Content-Type": "application/json" });
					res.end(JSON.stringify({ error: "MCP error" }));
				}
			}
			return;
		}

		// Health check (default)
		res.writeHead(200, { "Content-Type": "application/json" });
		res.end(
			JSON.stringify({
				name: "legend-dad-game-server",
				status: "ok",
				godot_connected: connMgr.godotClient !== null,
				agent_count: connMgr.agentClients.size,
				replay_enabled: recorder !== null,
				mcp_enabled: true,
			}),
		);
	});

	// --- WebSocket server ---
	const wss = new WebSocketServer({ server });

	wss.on("connection", (ws, req) => {
		console.log(`[ws] new connection from ${req.socket.remoteAddress}`);
		connMgr.handleConnection(ws);

		// End recording session when WS disconnects
		if (recorder) {
			ws.on("close", () => {
				if (recorder._sessionId) {
					recorder.endSession("abandoned").catch((err) => {
						console.error("[replay] end session error:", err.message);
					});
				}
			});
		}
	});

	// --- Start replay session when Godot registers ---
	if (recorder) {
		connMgr.onEvent((direction, msg) => {
			// Detect initial get_state command (sent right after Godot registers)
			if (
				direction === "to_godot" &&
				msg.type === "command" &&
				msg.action === "get_state"
			) {
				if (!recorder._sessionId) {
					recorder
						.startSession("agent", process.env.ZAI_MODEL || "glm-5.1")
						.catch((err) => {
							console.error("[replay] start session error:", err.message);
						});
				}
			}
		});
	}

	// --- Start ---
	server.listen(PORT, () => {
		console.log(`[server] listening on http://localhost:${PORT}`);
		console.log(`[ws] WebSocket server ready on ws://localhost:${PORT}`);
		console.log(`[mcp] Streamable HTTP endpoint at http://localhost:${PORT}/mcp`);
		console.log(
			"[mcp] tools: move, interact, switch_era, get_state, poll_events",
		);
	});
}

main().catch((err) => {
	console.error("[server] fatal:", err);
	process.exit(1);
});
```

Key changes from original:
- Import `EventQueueRegistry`
- Create `eventRegistry` and subscribe it to `from_godot` state events
- Pass `eventRegistry` as 3rd arg to `createMastraServer`
- `createServer` handler routes `/mcp` to `mcpServer.startHTTP()` with `onsessioninitialized` callback
- Health check response includes `mcp_enabled: true`
- Startup logs show MCP endpoint URL and all 5 tools

- [ ] **Step 2: Verify server starts without errors**

Run: `cd project/server/packages/game-server && timeout 3 node src/index.js 2>&1 || true`
Expected output should include:
```
[server] listening on http://localhost:3000
[ws] WebSocket server ready on ws://localhost:3000
[mcp] Streamable HTTP endpoint at http://localhost:3000/mcp
[mcp] tools: move, interact, switch_era, get_state, poll_events
```

(Replay may warn as disabled if SurrealDB not running — that's fine.)

- [ ] **Step 3: Commit**

```bash
git add project/server/packages/game-server/src/index.js
git commit -m "feat: wire MCP Streamable HTTP transport on /mcp endpoint"
```

---

### Task 5: Claude Code MCP Configuration

**Files:**
- Create: `.claude/settings.json` (project root)

- [ ] **Step 1: Create .claude/settings.json**

```json
{
	"mcpServers": {
		"legend-dad-game": {
			"url": "http://localhost:3000/mcp"
		}
	}
}
```

- [ ] **Step 2: Commit**

```bash
git add .claude/settings.json
git commit -m "feat: register legend-dad-game MCP server for Claude Code"
```

---

### Task 6: Manual Smoke Test

This task verifies the full chain end-to-end.

- [ ] **Step 1: Start the server**

Run: `cd project/server/packages/game-server && node src/index.js`

Verify output includes the MCP endpoint line.

- [ ] **Step 2: Verify MCP endpoint responds**

In another terminal:

Run: `curl -s -X POST http://localhost:3000/mcp -H "Content-Type: application/json" -d '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2025-03-26","capabilities":{},"clientInfo":{"name":"test","version":"0.1.0"}}}' | head -c 500`

Expected: A JSON-RPC response with server info and capabilities (tools list including move, interact, switch_era, get_state, poll_events).

- [ ] **Step 3: Verify health check still works**

Run: `curl -s http://localhost:3000/ | python3 -m json.tool`

Expected: JSON with `"mcp_enabled": true` field.

- [ ] **Step 4: Stop the server**

Kill the server process from step 1.

- [ ] **Step 5: Final commit with docs update**

```bash
git add -A
git commit -m "docs: add MCP transport spec and implementation plan"
```
