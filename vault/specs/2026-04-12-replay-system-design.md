---
date: 2026-04-12
status: draft
tags: [replay, agent, surrealdb, embeddings, fastembed]
---

# Replay System — Design Spec

## Goal

Record agent and human play sessions as structured replay data in SurrealDB, with per-turn vector embeddings for similarity search. Agents use past replay data as runtime context ("memory of past runs"), and replay data is available for offline evaluation.

## Decisions Made

| Decision | Choice | Rationale |
|---|---|---|
| Replay purpose | Runtime context + offline evaluation | Agent learns from past play; devs analyze agent behavior |
| What to capture | Full WS event stream | Commands, acks, state events, snapshots — nothing discarded |
| Agent context method | Hybrid — summary + key moments | Summaries for narrative, verbatim for critical decision points |
| Storage | SurrealDB (existing instance, port 6480) | Already running for other agents; multi-model (document + vector) |
| Embedding model | fastembed (Node.js, BGE-small-en-v1.5, 384 dims) | Local, fast (~5ms/embed), no API dependency |
| Embedding granularity | Per-turn (action + surrounding state) | Natural decision unit; balanced between noise and detail |
| Recording location | Node.js server only | Server sees all WS traffic; Godot unchanged |
| Type generation | quicktype from JSON Schema | Consistent types across Node.js server and documentation |

## Architecture

```
During play:
  Godot ◄──WS──► Node.js Server
                      │
                 ConnectionManager ──► Recorder ──► SurrealDB (port 6480)
                                          │
                                     fastembed (local)

Before agent plays:
  Current state ──► fastembed ──► SurrealDB vector search ──► similar turns
                                                                    │
  Past session summaries ──────────────────────────────────────────┤
                                                                    ▼
                                                          Context Builder
                                                                    │
                                                            Agent instructions
```

**Key principle:** Godot is unaware of replay. The Node.js server passively records all WS traffic and builds the replay store. The agent's Context Builder queries the store before play begins and can also query mid-session.

## Component 1: SurrealDB Schema

### Tables

**`replay_session`** — One record per play session.

| Field | Type | Description |
|---|---|---|
| `id` | record | Auto-generated |
| `started_at` | datetime | Session start |
| `ended_at` | datetime | Session end (null if active) |
| `player_type` | string | `"agent"` or `"human"` |
| `agent_model` | string | e.g. `"glm-5.1"` (null for human) |
| `initial_state` | object | First state snapshot received |
| `summary` | string | Natural-language session summary (generated at session end) |
| `total_actions` | int | Count of actions taken |
| `outcome` | string | `"completed"`, `"abandoned"`, `"stuck"` |

**`replay_event`** — Every WS message, raw. Linked to session.

| Field | Type | Description |
|---|---|---|
| `id` | record | Auto-generated |
| `session` | record(replay_session) | Parent session |
| `timestamp` | datetime | When it occurred |
| `direction` | string | `"to_godot"` or `"from_godot"` |
| `message` | object | Raw WS JSON message |
| `sequence` | int | Monotonic order within session |

**`replay_turn`** — Per-turn decision point. Embedded for vector search.

| Field | Type | Description |
|---|---|---|
| `id` | record | Auto-generated |
| `session` | record(replay_session) | Parent session |
| `sequence` | int | Turn order within session |
| `state_before` | object | Game state snapshot at decision time |
| `action` | string | `"move"`, `"interact"`, `"switch_era"` |
| `payload` | object | Action payload (e.g. `{ direction: "right" }`) |
| `result` | object | Ack result (`{ success, error }`) |
| `state_after` | object | State after action (from next state event) |
| `text` | string | Human-readable turn description for embedding input |
| `embedding` | array\<float\> | 384-dim fastembed vector |

### Indexes

```surql
DEFINE INDEX replay_turn_vec ON replay_turn FIELDS embedding HNSW DIMENSION 384 DIST COSINE;
DEFINE INDEX replay_event_session ON replay_event FIELDS session;
DEFINE INDEX replay_turn_session ON replay_turn FIELDS session;
```

### Graph Relations

```surql
-- Sessions contain turns and events
replay_session -> has_turn -> replay_turn
replay_turn -> has_events -> replay_event
```

### SurrealDB Connection

- Endpoint: `ws://localhost:6480` (existing instance)
- Namespace: `legend_dad`
- Database: `replay`
- Auth: root/root (local dev) or env vars `SURREAL_USER`/`SURREAL_PASS`

## Component 2: Recording Pipeline

### Recorder Module

**File:** `project/server/packages/game-server/src/replay/recorder.js`

The Recorder is instantiated at server startup and receives all WS messages from the ConnectionManager. It is a passive observer — it does not modify or delay message flow.

### Recording Flow

1. **Session lifecycle:**
   - `startSession(playerType, agentModel)` — Creates `replay_session` record, returns session ID
   - `endSession(outcome)` — Sets `ended_at`, `total_actions`, generates summary, updates record
   - Session starts when Godot connects; ends when Godot disconnects or server shuts down

2. **Event recording:**
   - `recordEvent(direction, message)` — Writes `replay_event` with auto-incrementing sequence
   - Called by ConnectionManager for every WS message in both directions

3. **Turn detection and embedding:**
   - Turn starts when a `command` is sent to Godot (direction: `"to_godot"`, type: `"command"`)
   - Turn ends when matching `command_ack` arrives (matched by `id`)
   - At turn end, Recorder:
     a. Captures `state_before` (cached state at command send time)
     b. Captures `state_after` (state after any resulting `state_event`s, with short delay)
     c. Builds turn text string
     d. Computes embedding via fastembed
     e. Writes `replay_turn` record

### Turn Text Format

Input to fastembed for embedding:

```
era:FATHER pos:(4,2) facing:right nearby:[slime@(4,4)] | move right | success -> pos:(5,2)
```

Format: `{context} | {action} {payload} | {result} -> {outcome}`

- **Context:** active era, player position, facing direction, nearby entities (within 2 tiles)
- **Action:** action name and payload
- **Result:** success/failure and resulting position or error

### Session Summary Generation

At session end, generate a natural-language summary from the recorded turns. Initial implementation: template-based (not LLM-generated).

```
Session #12 (agent/glm-5.1): 23 actions over 45s.
Path: (2,2) → (6,2) → (6,6) via path tiles.
3 blocked moves (water at col 8-9). 1 interaction (boulder activated).
Switched era once. Outcome: completed.
```

This summary is stored in `replay_session.summary` and used in the agent's context.

## Component 3: Context Builder

**File:** `project/server/packages/game-server/src/replay/context-builder.js`

Queries SurrealDB to build replay context for the agent before or during play.

### Context Building Flow

1. **On agent session start:**
   a. Get current game state (from state store)
   b. Query `replay_session` for past session summaries (last N sessions)
   c. Embed current state as a turn text
   d. Vector search `replay_turn` for similar past situations (top K results)
   e. Assemble context string

2. **Mid-session queries (optional):**
   - Agent's `get_state` tool can optionally include "have I been here before?" context
   - Same vector search, triggered by the tool

### Context Format (injected into agent instructions)

```
## Past Experience

### Session History
- Session #10 (agent/glm-5.1, 2 hours ago): Explored north path, got blocked by water. 15 actions. Outcome: stuck.
- Session #11 (agent/glm-5.1, 1 hour ago): Went south, activated boulder, cleared path. 23 actions. Outcome: completed.

### Similar Situations
- [Session #10, turn 8]: At (4,2) facing right, moved right → blocked (building at 5,2). Tried down instead → success.
- [Session #11, turn 3]: At (3,2) facing right, moved right → success. Continued to (5,2) via path.

Use this experience to make better decisions. Avoid repeating past failures.
```

### Query Parameters

| Parameter | Default | Description |
|---|---|---|
| `maxSessions` | 5 | Number of past session summaries to include |
| `maxSimilarTurns` | 10 | Number of similar turns from vector search |
| `similarityThreshold` | 0.7 | Minimum cosine similarity for turn matches |
| `sessionRecency` | 24h | Only include sessions from the last N hours |

## Component 4: JSON Schemas + quicktype

### Schema Files

**Location:** `project/server/packages/game-server/schemas/`

| File | Defines |
|---|---|
| `ws-messages.schema.json` | All WS message types (command, ack, state_event, state_snapshot, handshake) |
| `replay-records.schema.json` | SurrealDB record types (replay_session, replay_event, replay_turn) |
| `game-state.schema.json` | Game state structures (entity, components, map) |

### quicktype Generation

```bash
# Generate JS types from schemas
npx quicktype --src-lang schema --lang javascript \
  --out src/types/ws-messages.js \
  schemas/ws-messages.schema.json

npx quicktype --src-lang schema --lang javascript \
  --out src/types/replay-records.js \
  schemas/replay-records.schema.json
```

Add to package.json scripts:
```json
"generate:types": "quicktype ..."
```

### Note on GDScript

quicktype does not support GDScript output. The JSON schemas serve as documentation for the Godot side. GDScript types are maintained manually based on the schemas.

## Component 5: Server Integration

### New Dependencies

| Package | Purpose |
|---|---|
| `surrealdb` | SurrealDB JS SDK |
| `@surrealdb/node` | Node.js engine (if embedded fallback needed) |
| `fastembed` | Local embedding model |
| `quicktype` | JSON schema → type generation (devDependency) |

### Package Structure (additions)

```
project/server/packages/game-server/
├── schemas/
│   ├── ws-messages.schema.json
│   ├── replay-records.schema.json
│   └── game-state.schema.json
├── src/
│   ├── replay/
│   │   ├── recorder.js         # Records WS events + turns to SurrealDB
│   │   ├── context-builder.js  # Queries SurrealDB to build agent context
│   │   ├── embedder.js         # fastembed wrapper (init model, compute vectors)
│   │   └── db.js               # SurrealDB connection + schema initialization
│   ├── types/
│   │   ├── ws-messages.js      # Generated from schema
│   │   └── replay-records.js   # Generated from schema
│   └── mastra/
│       └── agent.js            # Updated: Context Builder injects replay context
```

### Startup Flow

```javascript
// In index.js, after creating connMgr and stateStore:
const db = await initReplayDB();          // Connect to SurrealDB, ensure schema
const embedder = await initEmbedder();    // Load fastembed model
const recorder = new Recorder(db, embedder);
const contextBuilder = new ContextBuilder(db, embedder);

// Hook recorder into connection manager (requires adding onEvent callback to ConnectionManager)
// ConnectionManager._routeMessage and sendCommandToGodot need to call this callback
connMgr.onEvent((direction, msg) => recorder.recordEvent(direction, msg));

// Pass context builder to agent creation
const agent = createGameAgent(tools, { contextBuilder, ...opts });
```

## Testing Strategy

1. **Recorder unit test** — Mock SurrealDB, verify events and turns are written correctly
2. **Embedder unit test** — Verify fastembed produces 384-dim vectors, similar texts produce similar vectors
3. **Context Builder unit test** — Mock SurrealDB query results, verify context string format
4. **Integration test** — Run the agent test (test-agent.js) with recording enabled, verify SurrealDB contains session/events/turns after run
5. **Vector search test** — Record two sessions, query for similar turns, verify relevant results

## Out of Scope

- **Godot-side gameplay replay** — Father's recorded actions replaying during Son's adventure is a core game mechanic that needs its own design spec. The replay data captured here can serve as input for that feature, but the playback logic in Godot is separate work. *(See: Future Spec — Gameplay Replay)*
- **LLM-generated session summaries** — Start with template-based summaries. LLM summarization can be added later.
- **Replay file export/import** — SurrealDB is the primary store. JSON export for portability is deferred.
- **Visual replay viewer** — No UI for watching replays. Evaluation is via queries and scripts.
- **Multi-agent concurrent recording** — One agent per session for now.

## Future: Godot-Side Gameplay Replay

> **Note for future design:** The father/son timeline mechanic requires Father's actions to replay and affect Son's world. This is a gameplay feature, not an agent feature. The data model here (replay_session → replay_turn with ordered actions and state) provides the raw material. A future spec should address:
> - How Father's replay_turns drive automated movement in Son's timeline
> - Whether replay is deterministic (exact repeat) or adaptive
> - Visual representation of the "ghost" father during Son's play
> - How interactable state changes from Father's replay propagate to Son's world
> - Integration with the ECS (new system: `S_ReplayPlayback`)
