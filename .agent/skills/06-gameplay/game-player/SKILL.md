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

## Prerequisites

Before using game tools, ensure:

1. **Server is running** — `task dev` (or `node project/server/packages/game-server/src/index.js`)
2. **Game is open in browser** — Godot web build at `http://localhost:8080`
3. **MCP server is registered** — `.claude/settings.json` points to `http://localhost:3000/mcp`

### Verify Server State

Call the health endpoint or use `get_state()`:

- `get_state()` returns `{ state: <data>, error: null }` — Godot is connected, ready to play
- `get_state()` returns `{ state: null, error: "no game state available..." }` — server is up but Godot hasn't connected yet. Wait for the player to open the game in browser.

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

- Check tile walkability before moving �� `map.father_tiles[row][col]` for Father era
- `move()` returns `{ success: false, error: "tile X,Y not walkable" }` if blocked
- `interact()` requires facing an interactable object — returns error otherwise
- Father's actions affect Son's timeline — plant a tree as Father, find a grown tree as Son
- Call `get_state()` periodically for a full refresh, not just `poll_events()`

## Troubleshooting

| Symptom | Cause | Fix |
|---------|-------|-----|
| Tools not available | MCP server not registered | Check `.claude/settings.json`, restart Claude Code |
| Connection refused | Server not running | Run `task dev` |
| `state: null` from `get_state` | Godot not connected | Open game at `http://localhost:8080` |
| `poll_events` returns empty | No events since last poll | Normal — game is idle |
| Move returns `success: false` | Target tile not walkable | Check tile map, try different direction |
