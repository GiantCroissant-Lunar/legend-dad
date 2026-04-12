# WebSocket Agent Protocol — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Enable AI agents to operate the game via WebSocket using semantic commands, with a Mastra-powered Node.js server exposing game actions as MCP tools.

**Architecture:** Godot action bus decouples input sources from game logic. Node.js server (Mastra runtime) relays semantic commands to Godot and caches pushed game state. MCP server exposes tools to Claude Code and other clients.

**Tech Stack:** Godot 4.6 (GDScript, GECS), Node.js (ES modules, pnpm), Mastra (`@mastra/core`, `@mastra/mcp`), Zod, ws library.

**Spec:** `vault/specs/2026-04-12-ws-agent-protocol-design.md`

---

## File Map

### Godot (new files)

| File | Purpose |
|---|---|
| `project/hosts/complete-app/scripts/game_actions.gd` | Action bus — singleton autoload emitting semantic signals |
| `project/hosts/complete-app/scripts/ws_client.gd` | WebSocket client — connects to server, relays commands/state |

### Godot (modified files)

| File | Change |
|---|---|
| `project/hosts/complete-app/ecs/systems/s_player_input.gd` | Stop reading Input directly; dispatch to GameActions bus |
| `project/hosts/complete-app/ecs/systems/s_interaction.gd` | Stop reading Input directly; dispatch to GameActions bus |
| `project/hosts/complete-app/scripts/main.gd` | Add WSClient node, wire state push events, handle era switch via bus |
| `project/hosts/complete-app/project.godot` | Register GameActions autoload |

### Node.js (new files)

| File | Purpose |
|---|---|
| `project/server/packages/game-server/src/mastra/index.js` | Mastra instance + MCP server config |
| `project/server/packages/game-server/src/mastra/tools/move.js` | `move` tool |
| `project/server/packages/game-server/src/mastra/tools/interact.js` | `interact` tool |
| `project/server/packages/game-server/src/mastra/tools/switch-era.js` | `switch_era` tool |
| `project/server/packages/game-server/src/mastra/tools/get-state.js` | `get_state` tool |
| `project/server/packages/game-server/src/ws/connection.js` | WS connection manager (Godot + agent clients) |
| `project/server/packages/game-server/src/ws/protocol.js` | Message serialization, validation, ID generation |
| `project/server/packages/game-server/src/state/store.js` | In-memory game state store |

### Node.js (modified files)

| File | Change |
|---|---|
| `project/server/packages/game-server/src/index.js` | Replace echo server with Mastra-powered server |
| `project/server/packages/game-server/package.json` | Add `@mastra/core`, `@mastra/mcp`, `zod` deps |

---

## Task 1: Install Mastra Dependencies

**Files:**
- Modify: `project/server/packages/game-server/package.json`

- [ ] **Step 1: Add Mastra and Zod dependencies**

```bash
cd /Users/apprenticegc/Work/lunar-horse/yokan-projects/legend-dad/project/server
pnpm --filter @legend-dad/game-server add @mastra/core @mastra/mcp zod
```

- [ ] **Step 2: Verify installation**

```bash
cd /Users/apprenticegc/Work/lunar-horse/yokan-projects/legend-dad/project/server
pnpm --filter @legend-dad/game-server list
```

Expected: `@mastra/core`, `@mastra/mcp`, `zod` listed in dependencies.

- [ ] **Step 3: Verify server still starts**

```bash
cd /Users/apprenticegc/Work/lunar-horse/yokan-projects/legend-dad/project/server/packages/game-server
node src/index.js &
sleep 1
curl -s http://localhost:3000
kill %1
```

Expected: `legend-dad game server`

- [ ] **Step 4: Lint**

```bash
cd /Users/apprenticegc/Work/lunar-horse/yokan-projects/legend-dad
task lint
```

Expected: No errors.

- [ ] **Step 5: Commit**

```bash
git add project/server/packages/game-server/package.json project/server/pnpm-lock.yaml
git commit -m "chore: add mastra and zod dependencies to game-server"
```

---

## Task 2: WS Protocol Module

**Files:**
- Create: `project/server/packages/game-server/src/ws/protocol.js`

- [ ] **Step 1: Create protocol.js with message helpers**

```javascript
// project/server/packages/game-server/src/ws/protocol.js
import { randomUUID } from "node:crypto";

/**
 * Message types flowing server → Godot.
 */
export function createCommand(action, payload = {}) {
	return {
		type: "command",
		id: `cmd_${randomUUID().slice(0, 8)}`,
		action,
		payload,
	};
}

/**
 * Parse and validate incoming JSON message from any WS client.
 * Returns { ok: true, msg } or { ok: false, error }.
 */
export function parseMessage(raw) {
	try {
		const msg = JSON.parse(raw);
		if (!msg.type || typeof msg.type !== "string") {
			return { ok: false, error: "missing or invalid 'type' field" };
		}
		return { ok: true, msg };
	} catch {
		return { ok: false, error: "invalid JSON" };
	}
}

/**
 * Validate a handshake message.
 */
export function isValidHandshake(msg) {
	return (
		msg.type === "handshake" &&
		(msg.client_type === "godot" || msg.client_type === "agent")
	);
}

/**
 * Create handshake acknowledgement.
 */
export function createHandshakeAck(sessionId) {
	return {
		type: "handshake_ack",
		session_id: sessionId,
	};
}
```

- [ ] **Step 2: Verify with a quick Node REPL test**

```bash
cd /Users/apprenticegc/Work/lunar-horse/yokan-projects/legend-dad/project/server/packages/game-server
node -e "
import { createCommand, parseMessage, isValidHandshake } from './src/ws/protocol.js';
const cmd = createCommand('move', { direction: 'right' });
console.log('command:', JSON.stringify(cmd));
const parsed = parseMessage(JSON.stringify(cmd));
console.log('parsed ok:', parsed.ok);
const bad = parseMessage('not json');
console.log('bad ok:', bad.ok, 'error:', bad.error);
const hs = { type: 'handshake', client_type: 'godot' };
console.log('valid handshake:', isValidHandshake(hs));
"
```

Expected: command with type/id/action/payload, parsed ok: true, bad ok: false, valid handshake: true.

- [ ] **Step 3: Lint**

```bash
cd /Users/apprenticegc/Work/lunar-horse/yokan-projects/legend-dad
task lint
```

- [ ] **Step 4: Commit**

```bash
git add project/server/packages/game-server/src/ws/protocol.js
git commit -m "feat: add WS message protocol module with create/parse/validate helpers"
```

---

## Task 3: State Store

**Files:**
- Create: `project/server/packages/game-server/src/state/store.js`

- [ ] **Step 1: Create store.js**

```javascript
// project/server/packages/game-server/src/state/store.js

/**
 * In-memory game state store.
 * Updated by state_event and state_snapshot messages from Godot.
 */
export class GameStateStore {
	constructor() {
		/** @type {object|null} Full game state snapshot */
		this.snapshot = null;
		/** @type {Array<object>} Recent state events (ring buffer, max 100) */
		this.recentEvents = [];
		this._maxEvents = 100;
	}

	/**
	 * Replace entire state with a snapshot from Godot.
	 */
	setSnapshot(data) {
		this.snapshot = data;
	}

	/**
	 * Apply a state_event from Godot.
	 * Updates snapshot if possible, stores in recent events.
	 */
	pushEvent(event) {
		this.recentEvents.push(event);
		if (this.recentEvents.length > this._maxEvents) {
			this.recentEvents.shift();
		}

		// Apply entity updates to snapshot if we have one
		if (this.snapshot && event.event === "entity_updated" && event.data?.entity_id) {
			const entity = this.snapshot.entities?.find(
				(e) => e.entity_id === event.data.entity_id,
			);
			if (entity) {
				Object.assign(entity.components, event.data.components);
			}
		}

		if (this.snapshot && event.event === "era_switched" && event.data) {
			this.snapshot.active_era = event.data.active_era;
			this.snapshot.active_entity_id = event.data.active_entity_id;
		}
	}

	/**
	 * Get current state. Returns snapshot or null if not yet received.
	 */
	getState() {
		return this.snapshot;
	}

	/**
	 * Clear all state (on Godot disconnect).
	 */
	clear() {
		this.snapshot = null;
		this.recentEvents = [];
	}
}
```

- [ ] **Step 2: Verify with REPL test**

```bash
cd /Users/apprenticegc/Work/lunar-horse/yokan-projects/legend-dad/project/server/packages/game-server
node -e "
import { GameStateStore } from './src/state/store.js';
const store = new GameStateStore();
console.log('initial:', store.getState());
store.setSnapshot({ active_era: 'FATHER', active_entity_id: 'father', entities: [{ entity_id: 'father', components: { grid_position: { col: 2, row: 2 } } }] });
console.log('after snapshot:', JSON.stringify(store.getState()));
store.pushEvent({ event: 'entity_updated', data: { entity_id: 'father', components: { grid_position: { col: 3, row: 2 } } } });
console.log('after event:', JSON.stringify(store.getState().entities[0].components.grid_position));
store.clear();
console.log('after clear:', store.getState());
"
```

Expected: null, snapshot with father at col 2, updated to col 3, null after clear.

- [ ] **Step 3: Lint and commit**

```bash
cd /Users/apprenticegc/Work/lunar-horse/yokan-projects/legend-dad
task lint
git add project/server/packages/game-server/src/state/store.js
git commit -m "feat: add in-memory game state store"
```

---

## Task 4: WS Connection Manager

**Files:**
- Create: `project/server/packages/game-server/src/ws/connection.js`

- [ ] **Step 1: Create connection.js**

```javascript
// project/server/packages/game-server/src/ws/connection.js
import { randomUUID } from "node:crypto";
import { parseMessage, isValidHandshake, createHandshakeAck, createCommand } from "./protocol.js";

/**
 * Manages WS connections from Godot and agent clients.
 * Relays commands to Godot and state events to agents.
 */
export class ConnectionManager {
	/**
	 * @param {import('../state/store.js').GameStateStore} stateStore
	 */
	constructor(stateStore) {
		this.stateStore = stateStore;
		/** @type {{ ws: WebSocket, sessionId: string } | null} */
		this.godotClient = null;
		/** @type {Map<string, WebSocket>} sessionId → ws */
		this.agentClients = new Map();
		/** @type {Map<string, { resolve: Function, reject: Function, timer: ReturnType<typeof setTimeout> }>} */
		this._pendingAcks = new Map();
	}

	/**
	 * Handle a new WS connection. Waits for handshake message.
	 */
	handleConnection(ws) {
		let identified = false;

		ws.on("message", (raw) => {
			const { ok, msg, error } = parseMessage(raw.toString());
			if (!ok) {
				ws.send(JSON.stringify({ type: "error", error }));
				return;
			}

			if (!identified) {
				if (!isValidHandshake(msg)) {
					ws.send(JSON.stringify({ type: "error", error: "expected handshake" }));
					return;
				}
				identified = true;
				const sessionId = randomUUID().slice(0, 12);

				if (msg.client_type === "godot") {
					this._registerGodot(ws, sessionId);
				} else {
					this._registerAgent(ws, sessionId);
				}

				ws.send(JSON.stringify(createHandshakeAck(sessionId)));
				console.log(`[conn] ${msg.client_type} registered: ${sessionId}`);
				return;
			}

			this._routeMessage(ws, msg);
		});

		ws.on("close", () => {
			this._handleDisconnect(ws);
		});
	}

	/**
	 * Send a command to Godot and wait for ack.
	 * Returns a promise that resolves with the ack or rejects on timeout.
	 */
	sendCommandToGodot(action, payload = {}, timeoutMs = 5000) {
		return new Promise((resolve, reject) => {
			if (!this.godotClient) {
				reject(new Error("no Godot client connected"));
				return;
			}

			const cmd = createCommand(action, payload);
			const timer = setTimeout(() => {
				this._pendingAcks.delete(cmd.id);
				reject(new Error(`command ${cmd.id} timed out`));
			}, timeoutMs);

			this._pendingAcks.set(cmd.id, { resolve, reject, timer });
			this.godotClient.ws.send(JSON.stringify(cmd));
		});
	}

	_registerGodot(ws, sessionId) {
		if (this.godotClient) {
			console.log("[conn] replacing existing Godot client");
			this.godotClient.ws.close(1000, "replaced by new Godot client");
		}
		this.godotClient = { ws, sessionId };

		// Request initial state snapshot
		const cmd = createCommand("get_state");
		ws.send(JSON.stringify(cmd));
	}

	_registerAgent(ws, sessionId) {
		this.agentClients.set(sessionId, ws);
		ws.on("close", () => {
			this.agentClients.delete(sessionId);
		});
	}

	_routeMessage(_ws, msg) {
		switch (msg.type) {
			case "command_ack":
				this._handleCommandAck(msg);
				break;
			case "state_snapshot":
				this.stateStore.setSnapshot(msg.data);
				this._broadcastToAgents(msg);
				break;
			case "state_event":
				this.stateStore.pushEvent(msg);
				this._broadcastToAgents(msg);
				break;
			default:
				console.log(`[conn] unknown message type: ${msg.type}`);
		}
	}

	_handleCommandAck(msg) {
		const pending = this._pendingAcks.get(msg.id);
		if (pending) {
			clearTimeout(pending.timer);
			this._pendingAcks.delete(msg.id);
			pending.resolve(msg);
		}
	}

	_broadcastToAgents(msg) {
		const raw = JSON.stringify(msg);
		for (const [sessionId, ws] of this.agentClients) {
			if (ws.readyState === ws.OPEN) {
				ws.send(raw);
			}
		}
	}

	_handleDisconnect(ws) {
		if (this.godotClient?.ws === ws) {
			console.log("[conn] Godot client disconnected");
			this.godotClient = null;
			this.stateStore.clear();
			// Notify all agents
			this._broadcastToAgents({
				type: "state_event",
				event: "game_disconnected",
				data: {},
			});
			return;
		}

		for (const [sessionId, agentWs] of this.agentClients) {
			if (agentWs === ws) {
				console.log(`[conn] agent ${sessionId} disconnected`);
				this.agentClients.delete(sessionId);
				return;
			}
		}
	}
}
```

- [ ] **Step 2: Lint**

```bash
cd /Users/apprenticegc/Work/lunar-horse/yokan-projects/legend-dad
task lint
```

- [ ] **Step 3: Commit**

```bash
git add project/server/packages/game-server/src/ws/connection.js
git commit -m "feat: add WS connection manager with Godot/agent routing and command ack"
```

---

## Task 5: Mastra Game Tools

**Files:**
- Create: `project/server/packages/game-server/src/mastra/tools/move.js`
- Create: `project/server/packages/game-server/src/mastra/tools/interact.js`
- Create: `project/server/packages/game-server/src/mastra/tools/switch-era.js`
- Create: `project/server/packages/game-server/src/mastra/tools/get-state.js`

- [ ] **Step 1: Create move.js**

```javascript
// project/server/packages/game-server/src/mastra/tools/move.js
import { createTool } from "@mastra/core/tools";
import { z } from "zod";

/**
 * Factory: creates the move tool bound to a ConnectionManager.
 * @param {import('../../ws/connection.js').ConnectionManager} connMgr
 */
export function createMoveTool(connMgr) {
	return createTool({
		id: "move",
		description:
			"Move the active player character one tile in the given direction. Returns the command acknowledgement from the game.",
		inputSchema: z.object({
			direction: z
				.enum(["up", "down", "left", "right"])
				.describe("Direction to move the active player"),
		}),
		outputSchema: z.object({
			success: z.boolean(),
			error: z.string().nullable(),
		}),
		execute: async (input) => {
			const ack = await connMgr.sendCommandToGodot("move", {
				direction: input.direction,
			});
			return { success: ack.success, error: ack.error ?? null };
		},
	});
}
```

- [ ] **Step 2: Create interact.js**

```javascript
// project/server/packages/game-server/src/mastra/tools/interact.js
import { createTool } from "@mastra/core/tools";
import { z } from "zod";

/**
 * Factory: creates the interact tool bound to a ConnectionManager.
 * @param {import('../../ws/connection.js').ConnectionManager} connMgr
 */
export function createInteractTool(connMgr) {
	return createTool({
		id: "interact",
		description:
			"Interact with the object in front of the active player character. Returns the command acknowledgement from the game.",
		inputSchema: z.object({}),
		outputSchema: z.object({
			success: z.boolean(),
			error: z.string().nullable(),
		}),
		execute: async () => {
			const ack = await connMgr.sendCommandToGodot("interact");
			return { success: ack.success, error: ack.error ?? null };
		},
	});
}
```

- [ ] **Step 3: Create switch-era.js**

```javascript
// project/server/packages/game-server/src/mastra/tools/switch-era.js
import { createTool } from "@mastra/core/tools";
import { z } from "zod";

/**
 * Factory: creates the switch_era tool bound to a ConnectionManager.
 * @param {import('../../ws/connection.js').ConnectionManager} connMgr
 */
export function createSwitchEraTool(connMgr) {
	return createTool({
		id: "switch_era",
		description:
			"Switch the active player between Father and Son timelines. Returns the command acknowledgement from the game.",
		inputSchema: z.object({}),
		outputSchema: z.object({
			success: z.boolean(),
			error: z.string().nullable(),
		}),
		execute: async () => {
			const ack = await connMgr.sendCommandToGodot("switch_era");
			return { success: ack.success, error: ack.error ?? null };
		},
	});
}
```

- [ ] **Step 4: Create get-state.js**

```javascript
// project/server/packages/game-server/src/mastra/tools/get-state.js
import { createTool } from "@mastra/core/tools";
import { z } from "zod";

/**
 * Factory: creates the get_state tool bound to a GameStateStore.
 * @param {import('../../state/store.js').GameStateStore} stateStore
 */
export function createGetStateTool(stateStore) {
	return createTool({
		id: "get_state",
		description:
			"Get the current full game state snapshot including all entity positions, interactable states, map data, and battle state.",
		inputSchema: z.object({}),
		outputSchema: z.object({
			state: z.any().nullable(),
		}),
		execute: async () => {
			return { state: stateStore.getState() };
		},
	});
}
```

- [ ] **Step 5: Lint**

```bash
cd /Users/apprenticegc/Work/lunar-horse/yokan-projects/legend-dad
task lint
```

- [ ] **Step 6: Commit**

```bash
git add project/server/packages/game-server/src/mastra/tools/
git commit -m "feat: add Mastra game tools — move, interact, switch_era, get_state"
```

---

## Task 6: Mastra Instance + MCP Server

**Files:**
- Create: `project/server/packages/game-server/src/mastra/index.js`

- [ ] **Step 1: Create mastra/index.js**

```javascript
// project/server/packages/game-server/src/mastra/index.js
import { MCPServer } from "@mastra/mcp";
import { createMoveTool } from "./tools/move.js";
import { createInteractTool } from "./tools/interact.js";
import { createSwitchEraTool } from "./tools/switch-era.js";
import { createGetStateTool } from "./tools/get-state.js";

/**
 * Initialize Mastra tools and MCP server, bound to live connection/state instances.
 *
 * @param {import('../ws/connection.js').ConnectionManager} connMgr
 * @param {import('../state/store.js').GameStateStore} stateStore
 */
export function createMastraServer(connMgr, stateStore) {
	const moveTool = createMoveTool(connMgr);
	const interactTool = createInteractTool(connMgr);
	const switchEraTool = createSwitchEraTool(connMgr);
	const getStateTool = createGetStateTool(stateStore);

	const mcpServer = new MCPServer({
		id: "legend-dad-game",
		name: "Legend Dad Game Server",
		version: "0.1.0",
		description:
			"Control the Legend Dad game — move characters, interact with objects, switch timelines, and observe game state.",
		tools: {
			move: moveTool,
			interact: interactTool,
			switch_era: switchEraTool,
			get_state: getStateTool,
		},
	});

	return { mcpServer, tools: { moveTool, interactTool, switchEraTool, getStateTool } };
}
```

- [ ] **Step 2: Lint and commit**

```bash
cd /Users/apprenticegc/Work/lunar-horse/yokan-projects/legend-dad
task lint
git add project/server/packages/game-server/src/mastra/index.js
git commit -m "feat: add Mastra MCP server exposing game tools"
```

---

## Task 7: Rewrite Server Entry Point

**Files:**
- Modify: `project/server/packages/game-server/src/index.js`

- [ ] **Step 1: Replace index.js with Mastra-powered server**

Replace the entire contents of `project/server/packages/game-server/src/index.js`:

```javascript
// project/server/packages/game-server/src/index.js
import { createServer } from "node:http";
import { WebSocketServer } from "ws";
import { GameStateStore } from "./state/store.js";
import { ConnectionManager } from "./ws/connection.js";
import { createMastraServer } from "./mastra/index.js";

const PORT = Number.parseInt(process.env.PORT || "3000", 10);

// --- State & connections ---
const stateStore = new GameStateStore();
const connMgr = new ConnectionManager(stateStore);

// --- Mastra MCP server ---
const { mcpServer } = createMastraServer(connMgr, stateStore);

// --- HTTP server (health check) ---
const server = createServer((req, res) => {
	res.writeHead(200, { "Content-Type": "application/json" });
	res.end(
		JSON.stringify({
			name: "legend-dad-game-server",
			status: "ok",
			godot_connected: connMgr.godotClient !== null,
			agent_count: connMgr.agentClients.size,
		}),
	);
});

// --- WebSocket server ---
const wss = new WebSocketServer({ server });

wss.on("connection", (ws, req) => {
	console.log(`[ws] new connection from ${req.socket.remoteAddress}`);
	connMgr.handleConnection(ws);
});

// --- Start ---
server.listen(PORT, () => {
	console.log(`[server] listening on http://localhost:${PORT}`);
	console.log(`[ws] WebSocket server ready on ws://localhost:${PORT}`);
	console.log("[mcp] MCP server initialized — tools: move, interact, switch_era, get_state");
});
```

- [ ] **Step 2: Verify server starts without error**

```bash
cd /Users/apprenticegc/Work/lunar-horse/yokan-projects/legend-dad/project/server/packages/game-server
node src/index.js &
sleep 2
curl -s http://localhost:3000 | node -e "process.stdin.on('data',d=>console.log(JSON.parse(d)))"
kill %1
```

Expected: JSON with `name`, `status: "ok"`, `godot_connected: false`, `agent_count: 0`.

- [ ] **Step 3: Lint and commit**

```bash
cd /Users/apprenticegc/Work/lunar-horse/yokan-projects/legend-dad
task lint
git add project/server/packages/game-server/src/index.js
git commit -m "feat: replace echo server with Mastra-powered game server"
```

---

## Task 8: Godot Action Bus (GameActions Autoload)

**Files:**
- Create: `project/hosts/complete-app/scripts/game_actions.gd`
- Modify: `project/hosts/complete-app/project.godot` (add autoload)

- [ ] **Step 1: Create game_actions.gd**

```gdscript
# project/hosts/complete-app/scripts/game_actions.gd
# Autoload: GameActions
# Semantic action bus — decouples input sources from game logic.
# Both keyboard input and WS commands dispatch through this bus.
extends Node

signal action_move(direction: Vector2i)
signal action_interact
signal action_switch_era

## Dispatch a movement action.
func move(direction: Vector2i) -> void:
	action_move.emit(direction)

## Dispatch an interact action.
func interact() -> void:
	action_interact.emit()

## Dispatch a timeline switch action.
func switch_era() -> void:
	action_switch_era.emit()
```

- [ ] **Step 2: Register as autoload in project.godot**

Add the following line in the `[autoload]` section of `project/hosts/complete-app/project.godot`, after the existing ECS line:

```ini
GameActions="*res://scripts/game_actions.gd"
```

The `[autoload]` section should now read:

```ini
[autoload]

BeehaveGlobalMetrics="*uid://c3ktl6ontsdt7"
BeehaveGlobalDebugger="*uid://bl3ma400hpvsh"
ECS="*uid://dfqwl5njvdnmq"
GameActions="*res://scripts/game_actions.gd"
```

- [ ] **Step 3: Commit**

```bash
git add project/hosts/complete-app/scripts/game_actions.gd project/hosts/complete-app/project.godot
git commit -m "feat: add GameActions autoload — semantic action bus for input decoupling"
```

---

## Task 9: Refactor S_PlayerInput to Use Action Bus

**Files:**
- Modify: `project/hosts/complete-app/ecs/systems/s_player_input.gd`

- [ ] **Step 1: Replace Input reads with GameActions dispatch**

Replace the entire contents of `s_player_input.gd`:

```gdscript
class_name S_PlayerInput
extends System

## Reads hardware input and dispatches to the GameActions bus.
## No longer processes movement directly — S_ActionProcessor handles that.

func query() -> QueryBuilder:
	return q.with_all([C_PlayerControlled])

func process(_entities: Array[Entity], _components: Array, _delta: float) -> void:
	var direction := Vector2i.ZERO
	if Input.is_action_pressed("ui_right"):
		direction = Vector2i.RIGHT
	elif Input.is_action_pressed("ui_left"):
		direction = Vector2i.LEFT
	elif Input.is_action_pressed("ui_down"):
		direction = Vector2i.DOWN
	elif Input.is_action_pressed("ui_up"):
		direction = Vector2i.UP

	if direction != Vector2i.ZERO:
		GameActions.move(direction)

	if Input.is_action_just_pressed("ui_accept") or Input.is_action_just_pressed("interact"):
		GameActions.interact()
```

Note: This system now only reads hardware input and dispatches to the bus. The actual movement/interaction logic moves to `S_ActionProcessor` (created in the next task). The `toggle_map` (M key) and era-switch logic remain in `main.gd` which will subscribe to `GameActions.action_switch_era`.

- [ ] **Step 2: Commit**

```bash
git add project/hosts/complete-app/ecs/systems/s_player_input.gd
git commit -m "refactor: S_PlayerInput dispatches to GameActions bus instead of processing directly"
```

---

## Task 10: Create S_ActionProcessor

**Files:**
- Create: `project/hosts/complete-app/ecs/systems/s_action_processor.gd`

This system subscribes to the GameActions bus and executes the movement/interaction logic previously in `S_PlayerInput` and `S_Interaction`.

- [ ] **Step 1: Create s_action_processor.gd**

```gdscript
class_name S_ActionProcessor
extends System

## Processes semantic actions from the GameActions bus.
## Handles movement (with cooldown) and interactions.

const TILE_SIZE := 32
var move_cooldown := 0.15
var _cooldown_timer := 0.0
var _pending_move := Vector2i.ZERO
var _pending_interact := false

func _init() -> void:
	GameActions.action_move.connect(_on_move)
	GameActions.action_interact.connect(_on_interact)

func _on_move(direction: Vector2i) -> void:
	_pending_move = direction

func _on_interact() -> void:
	_pending_interact = true

func query() -> QueryBuilder:
	return q.with_all([C_PlayerControlled, C_GridPosition, C_TimelineEra])

func process(entities: Array[Entity], _components: Array, delta: float) -> void:
	_cooldown_timer -= delta

	if _pending_move != Vector2i.ZERO and _cooldown_timer <= 0.0:
		_process_move(entities, _pending_move)
		_pending_move = Vector2i.ZERO

	if _pending_interact:
		_process_interact(entities)
		_pending_interact = false

func _process_move(entities: Array[Entity], direction: Vector2i) -> void:
	for entity in entities:
		var pc = entity.get_component(C_PlayerControlled) as C_PlayerControlled
		if not pc or not pc.active:
			continue

		var grid_pos = entity.get_component(C_GridPosition) as C_GridPosition
		grid_pos.facing = direction

		var new_col = grid_pos.col + direction.x
		var new_row = grid_pos.row + direction.y

		var era_comp = entity.get_component(C_TimelineEra) as C_TimelineEra
		var tilemap = _get_tilemap_for_era(era_comp.era)
		if tilemap and _is_tile_walkable(tilemap, new_col, new_row):
			if not _is_tile_occupied(new_col, new_row, era_comp.era, entity):
				grid_pos.col = new_col
				grid_pos.row = new_row
				_cooldown_timer = move_cooldown

func _process_interact(entities: Array[Entity]) -> void:
	for entity in entities:
		var pc = entity.get_component(C_PlayerControlled) as C_PlayerControlled
		if not pc or not pc.active:
			continue

		var grid_pos = entity.get_component(C_GridPosition) as C_GridPosition
		var era_comp = entity.get_component(C_TimelineEra) as C_TimelineEra

		var target_col = grid_pos.col + grid_pos.facing.x
		var target_row = grid_pos.row + grid_pos.facing.y

		var interactables = ECS.world.query.with_all([
			C_Interactable, C_GridPosition, C_TimelineEra
		]).execute()

		for target_entity in interactables:
			var t_era = target_entity.get_component(C_TimelineEra) as C_TimelineEra
			if t_era.era != era_comp.era:
				continue
			var t_pos = target_entity.get_component(C_GridPosition) as C_GridPosition
			if t_pos.col != target_col or t_pos.row != target_row:
				continue

			var interactable = target_entity.get_component(C_Interactable) as C_Interactable
			if interactable.state == C_Interactable.InteractState.DEFAULT:
				_activate(target_entity, interactable)
			break

func _activate(_entity: Entity, interactable: C_Interactable) -> void:
	interactable.state = C_Interactable.InteractState.ACTIVATED

	var link = _entity.get_component(C_TimelineLinked) as C_TimelineLinked
	if not link or link.linked_entity_id.is_empty():
		return

	var all_linked = ECS.world.query.with_all([C_TimelineLinked, C_Interactable]).execute()
	for linked_entity in all_linked:
		if linked_entity.id == link.linked_entity_id:
			var linked_interact = linked_entity.get_component(C_Interactable) as C_Interactable
			linked_interact.state = C_Interactable.InteractState.ACTIVATED
			break

func _get_tilemap_for_era(era: C_TimelineEra.Era) -> TileMapLayer:
	var world_node = ECS.world as Node
	var meta_key = "father_tilemap" if era == C_TimelineEra.Era.FATHER else "son_tilemap"
	if world_node.has_meta(meta_key):
		return world_node.get_meta(meta_key) as TileMapLayer
	return null

func _is_tile_walkable(tilemap: TileMapLayer, col: int, row: int) -> bool:
	var cell_coords = Vector2i(col, row)
	var source_id = tilemap.get_cell_source_id(cell_coords)
	if source_id == -1:
		return false
	var tile_data = tilemap.get_cell_tile_data(cell_coords)
	if tile_data:
		return tile_data.get_custom_data("walkable") as bool
	return false

func _is_tile_occupied(col: int, row: int, era: C_TimelineEra.Era, exclude: Entity) -> bool:
	var all_entities = ECS.world.query.with_all([C_GridPosition, C_TimelineEra]).execute()
	for e in all_entities:
		if e == exclude:
			continue
		var e_era = e.get_component(C_TimelineEra) as C_TimelineEra
		if e_era.era != era:
			continue
		var e_pos = e.get_component(C_GridPosition) as C_GridPosition
		if e_pos.col == col and e_pos.row == row:
			return true
	return false
```

- [ ] **Step 2: Register S_ActionProcessor in main.gd**

In `main.gd`, the ECS systems are registered in `_ready()`. Find where `S_PlayerInput` and `S_Interaction` systems are added to the world and add `S_ActionProcessor` alongside them. The exact location depends on how systems are registered — look for `world.add_system()` or similar calls. Add:

```gdscript
world.add_system(S_ActionProcessor.new())
```

Note: `S_Interaction` can be removed from the world's system list since its logic is now in `S_ActionProcessor`. `S_PlayerInput` stays (it reads hardware input).

- [ ] **Step 3: Commit**

```bash
git add project/hosts/complete-app/ecs/systems/s_action_processor.gd project/hosts/complete-app/ecs/systems/s_interaction.gd project/hosts/complete-app/scripts/main.gd
git commit -m "feat: add S_ActionProcessor — processes GameActions bus, replaces S_Interaction"
```

---

## Task 11: Godot WS Client

**Files:**
- Create: `project/hosts/complete-app/scripts/ws_client.gd`

- [ ] **Step 1: Create ws_client.gd**

```gdscript
# project/hosts/complete-app/scripts/ws_client.gd
# WebSocket client — connects to the Node.js server, relays commands to
# GameActions bus, and pushes game state changes back to the server.
extends Node

const DIRECTION_MAP := {
	"up": Vector2i.UP,
	"down": Vector2i.DOWN,
	"left": Vector2i.LEFT,
	"right": Vector2i.RIGHT,
}

@export var server_url := "ws://localhost:3000"

var _socket := WebSocketPeer.new()
var _connected := false
var _reconnect_timer := 0.0
var _reconnect_delay := 2.0

func _ready() -> void:
	_connect_to_server()

func _connect_to_server() -> void:
	var err = _socket.connect_to_url(server_url)
	if err != OK:
		push_warning("[ws_client] failed to initiate connection: %s" % err)

func _process(delta: float) -> void:
	_socket.poll()

	var state = _socket.get_ready_state()

	match state:
		WebSocketPeer.STATE_OPEN:
			if not _connected:
				_connected = true
				_reconnect_timer = 0.0
				print("[ws_client] connected to %s" % server_url)
				_send_handshake()

			while _socket.get_available_packet_count() > 0:
				var raw = _socket.get_packet().get_string_from_utf8()
				_handle_message(raw)

		WebSocketPeer.STATE_CLOSED:
			if _connected:
				_connected = false
				print("[ws_client] disconnected (code=%s)" % _socket.get_close_code())

			_reconnect_timer -= delta
			if _reconnect_timer <= 0.0:
				_reconnect_timer = _reconnect_delay
				_socket = WebSocketPeer.new()
				_connect_to_server()

		WebSocketPeer.STATE_CONNECTING:
			pass # waiting

		WebSocketPeer.STATE_CLOSING:
			pass # closing

func _send_handshake() -> void:
	_send_json({ "type": "handshake", "client_type": "godot", "name": "legend-dad" })

func _handle_message(raw: String) -> void:
	var json = JSON.new()
	var err = json.parse(raw)
	if err != OK:
		push_warning("[ws_client] invalid JSON: %s" % raw)
		return

	var msg = json.data
	if not msg is Dictionary or not msg.has("type"):
		return

	match msg["type"]:
		"handshake_ack":
			print("[ws_client] handshake OK, session=%s" % msg.get("session_id", "?"))
		"command":
			_handle_command(msg)
		"error":
			push_warning("[ws_client] server error: %s" % msg.get("error", "unknown"))

func _handle_command(msg: Dictionary) -> void:
	var action = msg.get("action", "")
	var payload = msg.get("payload", {})
	var cmd_id = msg.get("id", "")

	match action:
		"move":
			var dir_str = payload.get("direction", "")
			if dir_str in DIRECTION_MAP:
				GameActions.move(DIRECTION_MAP[dir_str])
				_send_command_ack(cmd_id, true)
			else:
				_send_command_ack(cmd_id, false, "invalid direction: %s" % dir_str)

		"interact":
			GameActions.interact()
			_send_command_ack(cmd_id, true)

		"switch_era":
			GameActions.switch_era()
			_send_command_ack(cmd_id, true)

		"get_state":
			_send_state_snapshot()
			_send_command_ack(cmd_id, true)

		_:
			_send_command_ack(cmd_id, false, "unknown action: %s" % action)

func _send_command_ack(cmd_id: String, success: bool, error: String = "") -> void:
	var ack := { "type": "command_ack", "id": cmd_id, "success": success }
	if not error.is_empty():
		ack["error"] = error
	else:
		ack["error"] = null
	_send_json(ack)

## Serialize and send the full game state snapshot.
## Called on get_state command and on initial connect.
func _send_state_snapshot() -> void:
	var entities_data := []
	var all_entities = ECS.world.query.with_all([C_GridPosition, C_TimelineEra]).execute()

	for entity in all_entities:
		var entry := { "entity_id": entity.name, "components": {} }

		var gp = entity.get_component(C_GridPosition) as C_GridPosition
		if gp:
			entry["components"]["grid_position"] = {
				"col": gp.col, "row": gp.row,
				"facing": _vec2i_to_string(gp.facing),
			}

		var era = entity.get_component(C_TimelineEra) as C_TimelineEra
		if era:
			entry["components"]["timeline_era"] = {
				"era": "FATHER" if era.era == C_TimelineEra.Era.FATHER else "SON",
			}

		var pc = entity.get_component(C_PlayerControlled) as C_PlayerControlled
		if pc:
			entry["components"]["player_controlled"] = { "active": pc.active }

		var enemy = entity.get_component(C_Enemy) as C_Enemy
		if enemy:
			entry["components"]["enemy"] = { "enemy_type": enemy.enemy_type }

		var inter = entity.get_component(C_Interactable) as C_Interactable
		if inter:
			entry["components"]["interactable"] = {
				"type": "BOULDER" if inter.type == C_Interactable.InteractType.BOULDER else "SWITCH",
				"state": "ACTIVATED" if inter.state == C_Interactable.InteractState.ACTIVATED else "DEFAULT",
			}

		entities_data.append(entry)

	# Determine active era from main script (accessible via get_tree)
	var main_node = get_tree().root.get_node_or_null("Main")
	var active_era := "FATHER"
	var active_entity_id := "father"
	if main_node and "active_era" in main_node:
		active_era = "FATHER" if main_node.active_era == C_TimelineEra.Era.FATHER else "SON"
		active_entity_id = "son" if active_era == "SON" else "father"

	# Include map tile data for agent reasoning
	var map_data := {}
	if main_node and "FATHER_MAP" in main_node and "SON_MAP" in main_node:
		map_data = {
			"width": main_node.MAP_WIDTH,
			"height": main_node.MAP_HEIGHT,
			"father_tiles": main_node.FATHER_MAP,
			"son_tiles": main_node.SON_MAP,
		}

	_send_json({
		"type": "state_snapshot",
		"data": {
			"active_era": active_era,
			"active_entity_id": active_entity_id,
			"entities": entities_data,
			"map": map_data,
			"battle": null,
		},
	})

func send_state_event(event_name: String, data: Dictionary) -> void:
	if not _connected:
		return
	_send_json({
		"type": "state_event",
		"event": event_name,
		"data": data,
	})

func _send_json(data: Dictionary) -> void:
	if _connected:
		_socket.send_text(JSON.stringify(data))

func _vec2i_to_string(v: Vector2i) -> String:
	if v == Vector2i.UP: return "up"
	if v == Vector2i.DOWN: return "down"
	if v == Vector2i.LEFT: return "left"
	if v == Vector2i.RIGHT: return "right"
	return "down"
```

- [ ] **Step 2: Commit**

```bash
git add project/hosts/complete-app/scripts/ws_client.gd
git commit -m "feat: add Godot WSClient — connects to server, relays commands to GameActions, pushes state"
```

---

## Task 12: Wire WSClient and State Events into main.gd

**Files:**
- Modify: `project/hosts/complete-app/scripts/main.gd`

- [ ] **Step 1: Add WSClient node in _ready()**

In `main.gd`, after the ECS world setup (after the `_build_world_map()` / entity spawning section), add:

```gdscript
# --- WebSocket client ---
var ws_client := preload("res://scripts/ws_client.gd").new()
ws_client.name = "WSClient"
add_child(ws_client)
```

Store a reference as an instance var at the top of the script:

```gdscript
var _ws_client: Node = null
```

And assign it:

```gdscript
_ws_client = ws_client
```

- [ ] **Step 2: Connect GameActions.action_switch_era to existing era-switch logic**

Find the existing era-switch code in `main.gd` (triggered by `toggle_map` key press / M key) and refactor it into a callable method:

```gdscript
func _switch_active_era() -> void:
	if active_era == C_TimelineEra.Era.FATHER:
		active_era = C_TimelineEra.Era.SON
		father_player.get_component(C_PlayerControlled).active = false
		son_player.get_component(C_PlayerControlled).active = true
	else:
		active_era = C_TimelineEra.Era.FATHER
		father_player.get_component(C_PlayerControlled).active = true
		son_player.get_component(C_PlayerControlled).active = false
	_update_view_layout()
```

Then connect the signal in `_ready()`:

```gdscript
GameActions.action_switch_era.connect(_switch_active_era)
```

And update the keyboard handler for M key to use:

```gdscript
GameActions.switch_era()
```

- [ ] **Step 3: Emit state events on entity changes**

Add state push calls at the points where game state changes. There are three key locations:

**3a. After movement in S_ActionProcessor** — Add a signal to `S_ActionProcessor` that fires after a successful move. In `game_actions.gd`, add a new signal for state change notifications:

```gdscript
# Add to game_actions.gd
signal state_changed(event_name: String, data: Dictionary)
```

In `S_ActionProcessor._process_move()`, after `grid_pos.col = new_col` / `grid_pos.row = new_row`, emit:

```gdscript
GameActions.state_changed.emit("entity_updated", {
	"entity_id": entity.name,
	"components": {
		"grid_position": { "col": grid_pos.col, "row": grid_pos.row, "facing": _vec2i_to_string(grid_pos.facing) },
	},
})
```

(Add the `_vec2i_to_string` helper to `S_ActionProcessor` — same as in `ws_client.gd`.)

**3b. After interaction** — In `S_ActionProcessor._activate()`, after setting `interactable.state`, emit:

```gdscript
GameActions.state_changed.emit("interaction_result", {
	"entity_id": _entity.name,
	"interactable_type": "BOULDER" if interactable.type == C_Interactable.InteractType.BOULDER else "SWITCH",
	"new_state": "ACTIVATED",
})
```

**3c. After era switch** — In `main.gd._switch_active_era()`, after toggling, emit:

```gdscript
GameActions.state_changed.emit("era_switched", {
	"active_era": "FATHER" if active_era == C_TimelineEra.Era.FATHER else "SON",
	"active_entity_id": "father" if active_era == C_TimelineEra.Era.FATHER else "son",
})
```

**3d. Connect WSClient to the state_changed signal** — In `main.gd._ready()`, after creating the WSClient:

```gdscript
GameActions.state_changed.connect(func(event_name: String, data: Dictionary):
	_ws_client.send_state_event(event_name, data)
)
```

- [ ] **Step 4: Commit**

```bash
git add project/hosts/complete-app/scripts/main.gd
git commit -m "feat: wire WSClient into main scene, connect era switch to GameActions bus"
```

---

## Task 13: Remove S_Interaction (Logic Moved to S_ActionProcessor)

**Files:**
- Modify: `project/hosts/complete-app/ecs/systems/s_interaction.gd`
- Modify: `project/hosts/complete-app/scripts/main.gd` (remove system registration)

- [ ] **Step 1: Delete or empty S_Interaction**

Since all interaction logic is now in `S_ActionProcessor`, remove `S_Interaction` from the ECS world's system list in `main.gd`. The file can be deleted or left as an empty class if other code references it.

Find in `main.gd` where systems are registered and remove the `S_Interaction` registration:

```gdscript
# Remove this line:
# world.add_system(S_Interaction.new())
```

- [ ] **Step 2: Commit**

```bash
git add project/hosts/complete-app/ecs/systems/s_interaction.gd project/hosts/complete-app/scripts/main.gd
git commit -m "refactor: remove S_Interaction — logic consolidated in S_ActionProcessor"
```

---

## Task 14: Integration Smoke Test

Manual verification that the full pipeline works.

- [ ] **Step 1: Start the server**

```bash
cd /Users/apprenticegc/Work/lunar-horse/yokan-projects/legend-dad
task dev
```

- [ ] **Step 2: Open the game in browser**

```bash
task build && task serve
```

Open `http://localhost:8080` in Chrome. Verify keyboard controls still work (arrow keys to move, E to interact).

- [ ] **Step 3: Test WS handshake with a script**

```bash
cd /Users/apprenticegc/Work/lunar-horse/yokan-projects/legend-dad/project/server/packages/game-server
node -e "
import WebSocket from 'ws';
const ws = new WebSocket('ws://localhost:3000');
ws.on('open', () => {
  ws.send(JSON.stringify({ type: 'handshake', client_type: 'agent', name: 'test' }));
});
ws.on('message', (data) => {
  console.log('received:', data.toString());
  // After handshake ack, try get_state
  const msg = JSON.parse(data);
  if (msg.type === 'handshake_ack') {
    console.log('handshake OK, session:', msg.session_id);
    // State should come from Godot push
    setTimeout(() => {
      ws.close();
      process.exit(0);
    }, 3000);
  }
});
"
```

- [ ] **Step 4: Verify health endpoint shows Godot connected**

```bash
curl -s http://localhost:3000 | python3 -m json.tool
```

Expected: `godot_connected: true` (if the game is running in browser).

- [ ] **Step 5: Commit any fixes needed, then final commit**

```bash
git add -A
git commit -m "test: verify WS agent protocol integration works end-to-end"
```

---

## Summary

| Task | Component | Commits |
|---|---|---|
| 1 | Install Mastra deps | 1 |
| 2 | WS Protocol module | 1 |
| 3 | State Store | 1 |
| 4 | Connection Manager | 1 |
| 5 | Mastra Game Tools | 1 |
| 6 | Mastra MCP Server | 1 |
| 7 | Server Entry Point | 1 |
| 8 | GameActions Autoload | 1 |
| 9 | Refactor S_PlayerInput | 1 |
| 10 | S_ActionProcessor | 1 |
| 11 | Godot WS Client | 1 |
| 12 | Wire into main.gd | 1 |
| 13 | Remove S_Interaction | 1 |
| 14 | Integration Smoke Test | 1 |
| **Total** | | **14 commits** |
