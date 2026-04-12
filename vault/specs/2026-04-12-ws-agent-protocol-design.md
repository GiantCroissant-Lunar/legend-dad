---
date: 2026-04-12
status: draft
tags: [websocket, agent, protocol, mastra, ecs]
---

# WebSocket Agent Protocol — Design Spec

## Goal

Enable AI agents (Claude Code, Playwright, Mastra agents) to operate the game as a normal user would — sending semantic commands and receiving full game state — via a WebSocket protocol. The Node.js server becomes the agent runtime powered by Mastra, exposing game actions as both WS messages and MCP tools.

## Decisions Made

| Decision | Choice | Rationale |
|---|---|---|
| Primary consumer | Agent-only (testing/automation) | No multiplayer networking; Godot client stays self-contained |
| Input abstraction | Semantic commands | Agent sends `move(right)`, not raw key events; mirrors an internal action map |
| State delivery | Push-based + snapshot on demand | Agent gets real-time event stream; `get_state` for initial connect/resync |
| State detail | Full scene | All entities, positions, interactable states, battle state — enough for AI reasoning |
| Player control | One at a time (respects toggle) | Agent switches Father/Son the same way a human would |
| Server role | Mastra-powered with logic (Approach A) | Tools = protocol, MCP exposure for free, agent runtime in-process |

## Architecture

```
┌─────────────┐     MCP/HTTP      ┌──────────────────────┐      WS       ┌─────────────┐
│ Claude Code  │◄────────────────►│  Node.js Server       │◄────────────►│ Godot Web    │
│ Playwright   │                  │  ├─ Mastra Runtime     │              │ (browser)    │
│ Any MCP client│                  │  ├─ Game Tools         │              │              │
└─────────────┘                   │  ├─ WS Connection Mgr  │              └─────────────┘
                                  │  └─ State Store        │
                                  └──────────────────────┘
```

**Data flow:**

1. Agent invokes a Mastra tool (e.g. `move`) or sends a WS command
2. Server validates and forwards the command to Godot over WS
3. Godot's action bus processes the command identically to keyboard input
4. Godot pushes state changes back to the server over WS
5. Server stores latest state and forwards events to the agent

## Component 1: Godot Action Bus

An internal event-driven command system. Both keyboard input and WS commands feed into the same bus. All ECS systems subscribe to the bus instead of reading `Input` directly.

### Open Design Question: Singleton vs Alternatives

> **The action bus needs to be globally accessible.** The obvious GDScript pattern is an autoload singleton, but this may not be ideal for testability or ECS compatibility. Alternatives to evaluate:
>
> - **Autoload singleton** (`GameActions`) — standard Godot pattern, simple, globally accessible via `GameActions.move("right")`. Downside: implicit global state, harder to test in isolation.
> - **ECS component as command queue** — a `C_CommandQueue` component on a dedicated entity. Systems write commands to the queue, `S_ActionProcessor` drains it. Fits ECS philosophy but GECS may not support this pattern cleanly.
> - **Signal bus on a node in the scene tree** — similar to autoload but scoped to the scene. More explicit dependency but requires scene-tree access.
> - **Direct function calls on systems** — skip the bus; WS handler calls system methods directly. Simplest but couples WS to ECS internals.
>
> **Decision deferred.** Evaluate during implementation which pattern fits GECS best.

### Actions (regardless of bus pattern)

| Action | Payload | Description |
|---|---|---|
| `move` | `direction: String` (up, down, left, right) | Move active player one tile in direction |
| `interact` | none | Interact with tile in front of active player |
| `switch_era` | none | Toggle active player between Father and Son |

### Changes to Existing Code

- **`S_PlayerInput`** — stops reading `Input.is_action_pressed()` directly. Instead detects keyboard input and dispatches to the action bus.
- **New `S_ActionProcessor`** — subscribes to the action bus and executes grid movement / interaction logic (extracted from current `S_PlayerInput` and `S_Interaction`).
- **Movement cooldown** stays in `S_ActionProcessor` — rate-limits regardless of command source (keyboard or WS).

### WS Client (Godot-side)

- New `WSClient` node connects to `ws://localhost:3000` (configurable via export var or query param).
- On receiving a command message from the server, calls into the action bus — same path as keyboard.
- On game state changes, serializes and sends state to the server.
- Reconnection with backoff on disconnect.

## Component 2: WebSocket Message Protocol

JSON messages over WS between Godot and the Node.js server.

### Command Messages (Server → Godot)

```json
{
  "type": "command",
  "id": "cmd_001",
  "action": "move",
  "payload": {
    "direction": "right"
  }
}
```

```json
{
  "type": "command",
  "id": "cmd_002",
  "action": "interact",
  "payload": {}
}
```

```json
{
  "type": "command",
  "id": "cmd_003",
  "action": "switch_era",
  "payload": {}
}
```

```json
{
  "type": "command",
  "id": "cmd_004",
  "action": "get_state",
  "payload": {}
}
```

- `id` is a unique command identifier for correlating acknowledgements.
- `get_state` requests a full snapshot (used on initial connect or resync).

### Command Acknowledgement (Godot → Server)

```json
{
  "type": "command_ack",
  "id": "cmd_001",
  "success": true,
  "error": null
}
```

```json
{
  "type": "command_ack",
  "id": "cmd_002",
  "success": false,
  "error": "no_interactable_in_front"
}
```

### State Event Messages (Godot → Server)

Pushed automatically when game state changes.

**Entity update:**
```json
{
  "type": "state_event",
  "event": "entity_updated",
  "data": {
    "entity_id": "father",
    "components": {
      "grid_position": { "col": 3, "row": 2, "facing": "right" },
      "timeline_era": { "era": "FATHER" },
      "player_controlled": { "active": true }
    }
  }
}
```

**Interaction result:**
```json
{
  "type": "state_event",
  "event": "interaction_result",
  "data": {
    "entity_id": "boulder_01",
    "interactable_type": "BOULDER",
    "new_state": "ACTIVATED",
    "linked_entity_id": "boulder_01_son"
  }
}
```

**Battle started:**
```json
{
  "type": "state_event",
  "event": "battle_started",
  "data": {
    "enemy_type": "slime",
    "combatants": [
      { "name": "Father", "hp": 100, "max_hp": 100 },
      { "name": "Slime", "hp": 30, "max_hp": 30 }
    ]
  }
}
```

**Era switched:**
```json
{
  "type": "state_event",
  "event": "era_switched",
  "data": {
    "active_era": "SON",
    "active_entity_id": "son"
  }
}
```

### Full State Snapshot (Godot → Server)

Sent in response to `get_state` command or on initial connection.

```json
{
  "type": "state_snapshot",
  "data": {
    "active_era": "FATHER",
    "active_entity_id": "father",
    "entities": [
      {
        "entity_id": "father",
        "components": {
          "grid_position": { "col": 2, "row": 2, "facing": "down" },
          "timeline_era": { "era": "FATHER" },
          "player_controlled": { "active": true }
        }
      },
      {
        "entity_id": "son",
        "components": {
          "grid_position": { "col": 7, "row": 4, "facing": "down" },
          "timeline_era": { "era": "SON" },
          "player_controlled": { "active": false }
        }
      },
      {
        "entity_id": "slime_01",
        "components": {
          "grid_position": { "col": 4, "row": 4, "facing": "down" },
          "timeline_era": { "era": "FATHER" },
          "enemy": { "enemy_type": "slime" }
        }
      }
    ],
    "map": {
      "width": 10,
      "height": 8,
      "father_tiles": [[0,0,0,...], ...],
      "son_tiles": [[0,0,0,...], ...]
    },
    "battle": null
  }
}
```

## Component 3: Node.js Server (Mastra-Powered)

Replace the current echo server with a Mastra runtime that manages agent-game communication.

### Package Structure

```
project/server/packages/game-server/
├── src/
│   ├── index.js              # Server entry — HTTP + WS + Mastra init
│   ├── mastra/
│   │   ├── index.js          # Mastra instance configuration
│   │   ├── agent.js          # Game-playing agent definition
│   │   └── tools/
│   │       ├── move.js       # move tool
│   │       ├── interact.js   # interact tool
│   │       ├── switch-era.js # switch_era tool
│   │       └── get-state.js  # get_state tool (returns cached snapshot)
│   ├── ws/
│   │   ├── connection.js     # WS connection manager (Godot clients)
│   │   └── protocol.js       # Message serialization / validation
│   └── state/
│       └── store.js          # In-memory game state (updated from Godot events)
├── package.json
└── nodemon.json
```

### Mastra Tools

Each game action is a Mastra `createTool()` with a Zod input schema:

| Tool ID | Input Schema | Behavior |
|---|---|---|
| `move` | `{ direction: enum(up,down,left,right) }` | Sends command to Godot, waits for ack |
| `interact` | `{}` | Sends interact command, waits for ack |
| `switch_era` | `{}` | Sends switch command, waits for ack |
| `get_state` | `{}` | Returns cached state snapshot (no WS round-trip if fresh) |

Tools are async — they send the WS command, await the `command_ack`, and return the result to the agent.

### MCP Exposure

The Mastra instance exposes an MCP server, making all tools available to any MCP client:

```
Claude Code ──► MCP ──► Mastra Tools ──► WS ──► Godot
```

This means Claude Code can drive the game with tool calls like `move({ direction: "right" })` without any custom client code.

### State Store

- In-memory object updated by `state_event` and `state_snapshot` messages from Godot.
- `get_state` tool reads from the store (fast, no WS round-trip).
- On Godot connect, server sends `get_state` command to populate initial state.
- State is per-connection (one Godot client = one game state).

### Connection Management

- Server listens on port 3000 (configurable via `PORT` env var).
- On connect, client sends a handshake: `{ "type": "handshake", "client_type": "godot" | "agent", "name": "optional label" }`.
- Server responds with `{ "type": "handshake_ack", "session_id": "..." }`.
- Only one Godot client expected at a time. If a second connects, the first is disconnected.
- Multiple agent clients allowed (each gets its own session ID).
- If Godot disconnects, agents are notified with `{ "type": "state_event", "event": "game_disconnected" }`.

## Component 4: Agent Definition

A Mastra agent configured to play the game:

- **Instructions:** Describe the game world, available actions, how to interpret state.
- **Tools:** `move`, `interact`, `switch_era`, `get_state`.
- **Model:** Configurable (default: Claude via Anthropic API).
- **Memory:** Mastra's built-in memory for maintaining context across turns.

The agent is optional for the protocol to work — a Playwright script or manual WS client can use the same tools/protocol without the AI agent. The agent is a consumer of the protocol, not a prerequisite.

## Testing Strategy

1. **Protocol unit tests** — Validate message serialization/deserialization on both sides.
2. **Integration test** — Playwright launches the game in browser, connects a WS test client, sends commands, asserts state changes.
3. **MCP smoke test** — Claude Code connects to the MCP server, calls `get_state`, calls `move`, verifies state updated.

## Out of Scope

- Multiplayer / multiple Godot clients
- Battle system WS commands (observe only for now — battle actions deferred)
- Authentication / authorization on the WS connection
- Persistent state / save/load
- G.U.I.D.E integration (keyboard remapping stays as-is for now)
