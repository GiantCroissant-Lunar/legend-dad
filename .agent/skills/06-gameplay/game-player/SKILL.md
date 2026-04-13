---
name: game-player
description: Play the Legend Dad game via MCP tools. Load this when you need to control the game as a player — move characters, interact with objects, switch timelines, observe state, and react to game events.
category: 06-gameplay
layer: gameplay
always_active: false
related_skills:
  - "@context-discovery"
  - "@dev-log"
---

# Game Player

Operate the Legend Dad game as a player through MCP tools. This skill is for AI coding agents (Claude Code, Copilot, etc.) that connect to the running game server via the MCP Streamable HTTP transport.

## Startup Checklist

Follow these steps in order before calling any game tools. Each step depends on the previous one.

### Step 1: Verify Web Build Exists

```bash
ls build/_artifacts/latest/web/complete-app.html
```

- **File exists** — proceed to step 2
- **File missing** — run `task build` first (requires Godot export templates, see `task setup`)

### Step 2: Start Servers

```bash
task dev
```

This starts two processes in parallel:
- **Static file server** on `:8080` — serves the Godot web build with COOP/COEP headers
- **WebSocket game server** on `:3000` — handles Godot and agent connections, exposes `/mcp`

Wait for both to be ready. Expected log output:

```
[server] listening on http://localhost:3000
[ws] WebSocket server ready on ws://localhost:3000
[mcp] Streamable HTTP endpoint at http://localhost:3000/mcp
[mcp] tools: move, interact, switch_era, get_state, poll_events
```

### Step 3: Verify Game Server Health

```bash
curl -s http://localhost:3000/ | python3 -m json.tool
```

Expected:

```json
{
    "name": "legend-dad-game-server",
    "status": "ok",
    "godot_connected": false,
    "agent_count": 0,
    "replay_enabled": true,
    "mcp_enabled": true
}
```

Check:
- `mcp_enabled: true` — MCP transport is wired
- `godot_connected: false` — expected, game not open yet

### Step 4: Verify MCP Endpoint Responds

```bash
curl -s -X POST http://localhost:3000/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -d '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2025-03-26","capabilities":{},"clientInfo":{"name":"test","version":"0.1.0"}}}'
```

Expected: SSE response with `serverInfo.name: "Legend Dad Game Server"` and `capabilities.tools`.

### Step 5: Open Game in Browser

Open `http://localhost:8080` in a browser. The Godot game loads and auto-connects to the WebSocket server.

Server logs should show:

```
[conn] godot registered: <session-id>
```

### Step 6: Verify Godot Connection

```bash
curl -s http://localhost:3000/ | python3 -m json.tool
```

Now `godot_connected` should be `true`.

Or call `get_state()` via MCP — should return game state instead of null.

### Step 7: Verify MCP Tools Work

Run the MCP verification test:

```bash
cd project/server/packages/game-server && node src/test-mcp.js
```

Expected: `19 passed, 0 failed`. Tests cover initialize, tools/list, get_state, move, poll_events, and queue drain.

### MCP Client Registration

Claude Code auto-connects via `.claude/settings.json`:

```json
{
  "mcpServers": {
    "legend-dad-game": {
      "url": "http://localhost:3000/mcp"
    }
  }
}
```

**Note:** Restart Claude Code after creating/modifying this file to pick up the change.

## Available MCP Tools

| Tool | Input | Output | Description |
|------|-------|--------|-------------|
| `move` | `{ direction: "up"\|"down"\|"left"\|"right" }` | `{ success, error }` | Move active player one tile |
| `interact` | `{}` | `{ success, error }` | Interact with object in front of active player |
| `switch_era` | `{}` | `{ success, error }` | Toggle between Father and Son timelines |
| `get_state` | `{}` | `{ state, error }` | Full game state snapshot |
| `poll_events` | `{}` | `{ events[], count }` | Drain buffered game events since last poll |

## Gameplay Loop

Follow this pattern for effective game operation:

```
1. get_state()          — understand current position and surroundings
2. Reason about goal    — what do you want to achieve?
3. Act                  — move(), interact(), or switch_era()
4. poll_events()        — see what changed (entity moves, battle starts, era switches)
5. Repeat from step 2
```

Always start with `get_state()` to establish context. Call `poll_events()` after each action to stay in sync with the game world.

## Game World Reference

### Timelines

Two parallel timelines on the same map:

- **FATHER** — present day, the father's era
- **SON** — future/ruined version, the son's era

You control one character at a time. `switch_era()` toggles which timeline and character is active.

### Map

- Grid size: 10 columns x 8 rows
- Coordinates: `{ col, row }` — col 0 is left, row 0 is top

### Tile Types

| Value | Father Era | Son Era | Walkable |
|-------|-----------|---------|----------|
| 0 | grass | dead_grass | yes |
| 1 | path | path | yes |
| 2 | building | ruin | no |
| 3 | water | blocked | no |

### Entities

The state snapshot includes an `entities` array. Each entity has:

```
{
  entity_id: "FatherPlayer",
  components: {
    grid_position: { col, row, facing },
    timeline_era: { era: "FATHER" | "SON" },
    player_controlled: { active: true | false },
    enemy: { enemy_type: "slime" }         // enemies only
  }
}
```

### State Snapshot Structure

```
{
  active_era: "FATHER" | "SON",
  active_entity_id: "father" | "son",
  entities: [ ... ],
  map: {
    width: 10, height: 8,
    father_tiles: [[...], ...],
    son_tiles: [[...], ...]
  },
  battle: null | { ... }
}
```

## Event Types

`poll_events()` returns these event types from Godot:

| Event | When | Data |
|-------|------|------|
| `entity_updated` | After movement or state change | Entity with updated components |
| `era_switched` | After `switch_era()` | `{ active_era, active_entity_id }` |
| `battle_started` | Encounter triggered | Battle state |
| `interaction_result` | After `interact()` | Interaction outcome |
| `state_snapshot` | Full state refresh | Complete game state |

## Strategy Tips

- Check tile walkability before moving — `map.father_tiles[row][col]` for Father era
- `move()` returns `{ success: false, error: "tile X,Y not walkable" }` if blocked
- `interact()` requires facing an interactable object — returns error otherwise
- Father's actions affect Son's timeline — plant a tree as Father, find a grown tree as Son
- Call `get_state()` periodically for a full refresh, not just `poll_events()`

## Troubleshooting

| Symptom | Cause | Fix |
|---------|-------|-----|
| No web build | Never built or build stale | `task build` |
| Port 8080 in use | Prior serve process still running | Kill it: `lsof -ti:8080 \| xargs kill` |
| Port 3000 in use | Prior game server still running | Kill it: `lsof -ti:3000 \| xargs kill` |
| Tools not available in Claude Code | MCP server not registered | Check `.claude/settings.json`, restart Claude Code |
| Connection refused on `:3000` | Server not running | Run `task dev` |
| `mcp_enabled: false` in health check | Old server code | Pull latest, rebuild |
| `state: null` from `get_state` | Godot not connected | Open game at `http://localhost:8080` |
| `poll_events` returns empty | No events since last poll | Normal — game is idle |
| Move returns `success: false` | Target tile not walkable | Check tile map, try different direction |
| MCP initialize returns 406 | Missing Accept header | Include `Accept: application/json, text/event-stream` |
| test-mcp.js fails on poll_events | Event queue not created | Verify `eventRegistry.create("default")` in `src/index.js` |
