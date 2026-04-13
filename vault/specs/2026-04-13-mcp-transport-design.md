# MCP Transport Design — Streamable HTTP

**Date**: 2026-04-13
**Status**: Draft
**Author**: Claude Code + ApprenticeGC

## Goal

Wire the existing Mastra MCPServer to a Streamable HTTP transport so Claude Code (and any MCP client) can call game tools (`move`, `interact`, `switch_era`, `get_state`) against a running game server with a live Godot connection. Add a `poll_events` tool so MCP clients can receive game state events (entity updates, era switches, battle starts) that would normally be pushed over WebSocket.

## Context

### Current Architecture

The game server (`project/server/packages/game-server/`) runs on port 3000 with:

- **HTTP health endpoint** — `GET /` returns server status JSON
- **WebSocket server** — Godot and agent clients connect, exchange game protocol messages
- **Mastra MCPServer object** — created with 4 tools, but **no transport wired** (never serves)
- **Mastra Agent (in-process)** — GLM/Qwen agents call tools directly via `Agent.generate()`, no MCP involved

### Why Streamable HTTP (not stdio)

The game tools depend on a live `ConnectionManager` with a Godot WebSocket connection. With stdio, Claude Code would spawn a separate server process that has no Godot connection — every tool call would fail with "no Godot client connected."

Streamable HTTP adds an `/mcp` endpoint to the **same running server** that Godot is connected to. Tool calls flow through the same `ConnectionManager` instance.

### Why Not WebSocket MCP Transport

Two blockers investigated during brainstorming:

1. **Protocol mismatch** — The existing WS speaks a custom game protocol (`command`, `state_event`, `state_snapshot`). MCP speaks JSON-RPC 2.0. They cannot share a connection.
2. **Client support** — Claude Code's MCP client supports stdio and HTTP/SSE, not raw WebSocket. The MCP spec chose Streamable HTTP over WebSocket.

### Future Upgrade Path

MCP protocol supports server-initiated notifications over Streamable HTTP's SSE channel. If Claude Code gains support for acting on these notifications, game events could be pushed directly instead of polled. The Streamable HTTP transport keeps this door open.

## Design

### Architecture

```
┌─────────────┐    WS (game protocol)    ┌──────────────────────────┐
│  Godot game  │◄────────────────────────►│                          │
│  (browser)   │                          │   game-server :3000      │
└─────────────┘                           │                          │
                                          │  ┌── ConnectionManager ──┤
┌─────────────┐    MCP Streamable HTTP    │  │                       │
│ Claude Code  │◄────────────────────────►│  │  ┌── EventQueue ──┐  │
│ (MCP client) │  POST/GET /mcp           │  │  │  per session   │  │
└─────────────┘                           │  │  └────────────────┘  │
                                          │  ├── GameStateStore ─────┤
┌─────────────┐    WS (game protocol)     │  ├── MCPServer ──────────┤
│ Other agents │◄────────────────────────►│  │  5 tools (+ poll)    │
│ (GLM, Qwen)  │                          │  │                       │
└─────────────┘                           └──┴───────────────────────┘
```

### Components

#### 1. HTTP Request Router (modify `src/index.js`)

The existing `createServer` handler currently serves only a health check JSON response. Change it to route based on URL path:

- `GET /` — health check (unchanged)
- `POST /mcp`, `GET /mcp`, `DELETE /mcp` — delegate to `mcpServer.startHTTP()`

Mastra's `startHTTP()` handles MCP session management, JSON-RPC parsing, and SSE streaming internally. We just pass `req`/`res` through.

#### 2. EventQueue (new file: `src/mcp/event-queue.js`)

A per-session buffer that captures game events from `ConnectionManager` broadcasts.

```
EventQueue
  - constructor(maxSize = 200)
  - push(event)          — add event, drop oldest if full
  - drain()              — return all events and clear buffer
  - size                 — current count
```

Events buffered: `state_event` and `state_snapshot` messages from Godot.

A registry maps MCP session IDs to EventQueue instances. Queues are created when an MCP session starts and cleaned up when the session ends or is garbage-collected after inactivity (5 min timeout).

#### 3. `poll_events` Tool (new file: `src/mastra/tools/poll-events.js`)

A new Mastra tool that drains the caller's event queue and returns buffered events.

- **Input**: none (session ID resolved from MCP context)
- **Output**: `{ events: Array<{type, event?, data, timestamp}>, count: number }`
- Returns an empty array if no events have occurred since last poll

The session-to-queue mapping needs to be accessible from the tool's execute function. Pass the event queue registry into the tool factory (same pattern as `createMoveTool(connMgr)`).

#### 4. MCP Session Lifecycle

When `mcpServer.startHTTP()` is called with session options:

- **`onsessioninitialized(sessionId)`** — create an `EventQueue` for this session, register it with `ConnectionManager.onEvent()` to receive broadcasts
- **Session cleanup** — when the MCP session ends or times out, remove the queue and unsubscribe from events

#### 5. Claude Code Configuration (new file: `.claude/settings.json`)

Register the MCP server so Claude Code auto-connects:

```json
{
  "mcpServers": {
    "legend-dad-game": {
      "url": "http://localhost:3000/mcp"
    }
  }
}
```

No auth required (localhost only).

### Tool Inventory (after change)

| Tool | Existing? | Description |
|------|-----------|-------------|
| `move` | Yes | Move active player one tile |
| `interact` | Yes | Interact with object in front |
| `switch_era` | Yes | Toggle Father/Son timeline |
| `get_state` | Yes | Return full game state snapshot |
| `poll_events` | **New** | Drain buffered game events since last poll |

### Files Changed

| File | Change |
|------|--------|
| `src/index.js` | Route `/mcp` to `mcpServer.startHTTP()`, pass session callbacks |
| `src/mastra/index.js` | Add `poll_events` tool to MCPServer, accept event queue registry |
| `src/mcp/event-queue.js` | **New** — EventQueue class + session registry |
| `src/mastra/tools/poll-events.js` | **New** — poll_events tool definition |
| `.claude/settings.json` | **New** — MCP server registration for Claude Code |

### What Does NOT Change

- WebSocket server, `ConnectionManager`, game protocol — untouched
- Existing 4 tools (move, interact, switch_era, get_state) — untouched
- Mastra Agent (`agent.js`) and test-agent — untouched
- Replay system — untouched
- Godot project — untouched

## Workflow

1. `task dev` — starts game server on :3000 (now with `/mcp` endpoint)
2. Open Godot game in browser — connects via WebSocket
3. Claude Code session starts — auto-connects to `http://localhost:3000/mcp`
4. Claude Code calls `get_state()` — gets game snapshot
5. Claude Code calls `move("right")` — character moves, Godot sends state_event
6. Claude Code calls `poll_events()` — gets the entity_updated event
7. Claude Code reasons about the new state and decides next action

## Error Handling

- **Godot not connected**: Tools return `{ success: false, error: "no Godot client connected" }` (existing behavior)
- **Server not running**: Claude Code gets connection refused — clear error, user runs `task dev`
- **Event queue overflow**: Oldest events dropped when buffer exceeds 200 (configurable)
- **Stale MCP session**: Queue garbage-collected after 5 min inactivity

## Known Issues

### Mastra `onsessioninitialized` callback silently overridden (`@mastra/mcp` v1.4.2)

**Problem:** The `startHTTP()` method accepts `options.onsessioninitialized` in its API, but the implementation overwrites it. In `dist/index.js` (line ~3632), Mastra spreads user options into the transport config then hardcodes its own `onsessioninitialized` after the spread:

```js
transport = new StreamableHTTPServerTransport({
  ...mergedOptions,                    // includes our callback
  onsessioninitialized: (id) => {      // overwrites it — last key wins
    this.streamableHTTPTransports.set(id, transport);
  }
});
```

In JavaScript object literals, duplicate keys resolve to the last one. Our callback is lost.

**Impact:** Per-MCP-session event queues cannot be created via the documented callback. The spec's Session Lifecycle design (create queue on session init, clean up on session end) does not work.

**Workaround:** Create a single "default" event queue eagerly at server startup (`eventRegistry.create("default")`). This is sufficient for the single-client case (one Claude Code session at a time). The `poll_events` tool uses `registry.getFirstQueue()` which returns this default queue.

**Fix on Mastra's side:** Compose both callbacks instead of overwriting:

```js
onsessioninitialized: (id) => {
  this.streamableHTTPTransports.set(id, transport);
  mergedOptions.onsessioninitialized?.(id);  // call user's callback too
}
```

**Action:** Consider filing a GitHub issue on [mastra-inc/mastra](https://github.com/mastra-inc/mastra). If fixed upstream, switch back to per-session queues for proper multi-client support.

## Testing

- Extend `test-agent.js` pattern: start server, connect mock Godot, then use `@modelcontextprotocol/sdk` client to connect via HTTP and call tools
- Verify: tool calls succeed, `poll_events` returns game events, session cleanup works
- Manual: `task dev`, open game, use Claude Code to call tools against live game
