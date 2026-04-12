# Replay System Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Record agent play sessions to SurrealDB with per-turn vector embeddings, and build a context builder that injects relevant past experience into the agent's instructions.

**Architecture:** Passive recorder taps ConnectionManager events, writes raw events and per-turn embeddings to SurrealDB. Context builder queries SurrealDB (session summaries + vector-searched similar turns) and injects results into agent instructions before play.

**Tech Stack:** SurrealDB (existing instance, port 6480), surrealdb JS SDK, fastembed (BGE-small-en-v1.5, 384 dims), quicktype for JSON schema codegen.

**Spec:** `vault/specs/2026-04-12-replay-system-design.md`

---

## File Map

### New Files

| File | Purpose |
|---|---|
| `project/server/packages/game-server/src/replay/db.js` | SurrealDB connection + schema initialization |
| `project/server/packages/game-server/src/replay/embedder.js` | fastembed wrapper — init model, compute vectors |
| `project/server/packages/game-server/src/replay/recorder.js` | Records WS events + turns to SurrealDB |
| `project/server/packages/game-server/src/replay/context-builder.js` | Queries SurrealDB to build agent context string |
| `project/server/packages/game-server/schemas/ws-messages.schema.json` | JSON schema for all WS message types |
| `project/server/packages/game-server/schemas/replay-records.schema.json` | JSON schema for SurrealDB replay records |
| `project/server/packages/game-server/schemas/game-state.schema.json` | JSON schema for game state structures |

### Modified Files

| File | Change |
|---|---|
| `project/server/packages/game-server/package.json` | Add surrealdb, fastembed, quicktype deps |
| `project/server/packages/game-server/src/ws/connection.js` | Add `onEvent` callback hook |
| `project/server/packages/game-server/src/index.js` | Wire recorder + context builder into startup |
| `project/server/packages/game-server/src/mastra/agent.js` | Accept context builder, inject replay context |
| `project/server/packages/game-server/src/test-agent.js` | Add replay recording to the integration test |

---

## Task 1: Install Dependencies

**Files:**
- Modify: `project/server/packages/game-server/package.json`

- [ ] **Step 1: Install SurrealDB and fastembed**

```bash
cd /Users/apprenticegc/Work/lunar-horse/yokan-projects/legend-dad/project/server
pnpm --filter @legend-dad/game-server add surrealdb fastembed
```

- [ ] **Step 2: Install quicktype as devDependency**

```bash
cd /Users/apprenticegc/Work/lunar-horse/yokan-projects/legend-dad/project/server
pnpm --filter @legend-dad/game-server add -D quicktype
```

- [ ] **Step 3: Verify imports work**

```bash
cd /Users/apprenticegc/Work/lunar-horse/yokan-projects/legend-dad/project/server/packages/game-server
node -e "
import { Surreal } from 'surrealdb';
console.log('surrealdb OK');
import { EmbeddingModel, FlagEmbedding } from 'fastembed';
console.log('fastembed OK');
"
```

Expected: Both imports succeed.

- [ ] **Step 4: Lint and commit**

```bash
cd /Users/apprenticegc/Work/lunar-horse/yokan-projects/legend-dad
task lint
git add project/server/packages/game-server/package.json project/server/pnpm-lock.yaml
git commit -m "chore: add surrealdb, fastembed, and quicktype dependencies

Co-Authored-By: Claude Opus 4.6 (1M context) <noreply@anthropic.com>"
```

---

## Task 2: SurrealDB Connection + Schema

**Files:**
- Create: `project/server/packages/game-server/src/replay/db.js`

- [ ] **Step 1: Create db.js**

```javascript
// project/server/packages/game-server/src/replay/db.js
import { Surreal } from "surrealdb";

const SURREAL_URL = process.env.SURREAL_URL || "ws://localhost:6480";
const SURREAL_NS = process.env.SURREAL_NS || "legend_dad";
const SURREAL_DB = process.env.SURREAL_DB || "replay";
const SURREAL_USER = process.env.SURREAL_USER || "root";
const SURREAL_PASS = process.env.SURREAL_PASS || "root";

const SCHEMA = `
DEFINE TABLE IF NOT EXISTS replay_session SCHEMALESS;
DEFINE FIELD IF NOT EXISTS started_at ON replay_session TYPE datetime;
DEFINE FIELD IF NOT EXISTS ended_at ON replay_session TYPE option<datetime>;
DEFINE FIELD IF NOT EXISTS player_type ON replay_session TYPE string;
DEFINE FIELD IF NOT EXISTS agent_model ON replay_session TYPE option<string>;
DEFINE FIELD IF NOT EXISTS initial_state ON replay_session TYPE option<object>;
DEFINE FIELD IF NOT EXISTS summary ON replay_session TYPE option<string>;
DEFINE FIELD IF NOT EXISTS total_actions ON replay_session TYPE int DEFAULT 0;
DEFINE FIELD IF NOT EXISTS outcome ON replay_session TYPE option<string>;

DEFINE TABLE IF NOT EXISTS replay_event SCHEMALESS;
DEFINE FIELD IF NOT EXISTS session ON replay_event TYPE record<replay_session>;
DEFINE FIELD IF NOT EXISTS timestamp ON replay_event TYPE datetime;
DEFINE FIELD IF NOT EXISTS direction ON replay_event TYPE string;
DEFINE FIELD IF NOT EXISTS message ON replay_event TYPE object;
DEFINE FIELD IF NOT EXISTS sequence ON replay_event TYPE int;
DEFINE INDEX IF NOT EXISTS replay_event_session ON replay_event FIELDS session;

DEFINE TABLE IF NOT EXISTS replay_turn SCHEMALESS;
DEFINE FIELD IF NOT EXISTS session ON replay_turn TYPE record<replay_session>;
DEFINE FIELD IF NOT EXISTS sequence ON replay_turn TYPE int;
DEFINE FIELD IF NOT EXISTS state_before ON replay_turn TYPE option<object>;
DEFINE FIELD IF NOT EXISTS action ON replay_turn TYPE string;
DEFINE FIELD IF NOT EXISTS payload ON replay_turn TYPE object;
DEFINE FIELD IF NOT EXISTS result ON replay_turn TYPE object;
DEFINE FIELD IF NOT EXISTS state_after ON replay_turn TYPE option<object>;
DEFINE FIELD IF NOT EXISTS text ON replay_turn TYPE string;
DEFINE FIELD IF NOT EXISTS embedding ON replay_turn TYPE option<array>;
DEFINE INDEX IF NOT EXISTS replay_turn_session ON replay_turn FIELDS session;
DEFINE INDEX IF NOT EXISTS replay_turn_vec ON replay_turn FIELDS embedding HNSW DIMENSION 384 DIST COSINE;
`;

/**
 * Connect to SurrealDB and ensure replay schema exists.
 * @returns {Promise<Surreal>}
 */
export async function initReplayDB() {
  const db = new Surreal();

  await db.connect(SURREAL_URL);
  await db.signin({ username: SURREAL_USER, password: SURREAL_PASS });
  await db.use({ namespace: SURREAL_NS, database: SURREAL_DB });

  // Apply schema (idempotent — IF NOT EXISTS)
  await db.query(SCHEMA);
  console.log(`[replay-db] connected to ${SURREAL_URL} ns=${SURREAL_NS} db=${SURREAL_DB}`);

  return db;
}
```

- [ ] **Step 2: Verify connection to running SurrealDB**

```bash
cd /Users/apprenticegc/Work/lunar-horse/yokan-projects/legend-dad/project/server/packages/game-server
node -e "
import { initReplayDB } from './src/replay/db.js';
const db = await initReplayDB();
const result = await db.query('INFO FOR DB');
console.log('tables:', Object.keys(result[0] || {}));
await db.close();
console.log('OK');
"
```

Expected: Connects, shows tables including `replay_session`, `replay_event`, `replay_turn`, then closes.

- [ ] **Step 3: Lint and commit**

```bash
cd /Users/apprenticegc/Work/lunar-horse/yokan-projects/legend-dad
task lint
git add project/server/packages/game-server/src/replay/db.js
git commit -m "feat: add SurrealDB connection and replay schema initialization

Co-Authored-By: Claude Opus 4.6 (1M context) <noreply@anthropic.com>"
```

---

## Task 3: Embedder Module

**Files:**
- Create: `project/server/packages/game-server/src/replay/embedder.js`

- [ ] **Step 1: Create embedder.js**

```javascript
// project/server/packages/game-server/src/replay/embedder.js
import { EmbeddingModel, FlagEmbedding } from "fastembed";

let _model = null;

/**
 * Initialize the fastembed model. Call once at startup.
 * @returns {Promise<void>}
 */
export async function initEmbedder() {
  if (_model) return;
  _model = await FlagEmbedding.init({
    model: EmbeddingModel.BGESmallENV15,
  });
  console.log("[embedder] BGE-small-en-v1.5 model loaded (384 dims)");
}

/**
 * Compute embedding for a single text string.
 * @param {string} text
 * @returns {Promise<number[]>} 384-dimensional float array
 */
export async function embed(text) {
  if (!_model) {
    throw new Error("embedder not initialized — call initEmbedder() first");
  }
  const batches = _model.embed([text], 1);
  for await (const batch of batches) {
    // batch is Float32Array[], we want the first (and only) item
    return Array.from(batch);
  }
  throw new Error("embed returned no results");
}

/**
 * Compute embeddings for multiple texts.
 * @param {string[]} texts
 * @returns {Promise<number[][]>}
 */
export async function embedBatch(texts) {
  if (!_model) {
    throw new Error("embedder not initialized — call initEmbedder() first");
  }
  const results = [];
  const batches = _model.embed(texts, 32);
  for await (const batch of batches) {
    results.push(Array.from(batch));
  }
  return results;
}
```

- [ ] **Step 2: Verify embedding works**

```bash
cd /Users/apprenticegc/Work/lunar-horse/yokan-projects/legend-dad/project/server/packages/game-server
node -e "
import { initEmbedder, embed } from './src/replay/embedder.js';
await initEmbedder();
const vec = await embed('era:FATHER pos:(4,2) facing:right | move right | success');
console.log('dims:', vec.length);
console.log('first 5:', vec.slice(0, 5));
console.log('type:', typeof vec[0]);
"
```

Expected: `dims: 384`, array of floats, type: `number`.

- [ ] **Step 3: Lint and commit**

```bash
cd /Users/apprenticegc/Work/lunar-horse/yokan-projects/legend-dad
task lint
git add project/server/packages/game-server/src/replay/embedder.js
git commit -m "feat: add fastembed wrapper for turn embeddings (BGE-small-en-v1.5, 384d)

Co-Authored-By: Claude Opus 4.6 (1M context) <noreply@anthropic.com>"
```

---

## Task 4: Add onEvent Callback to ConnectionManager

**Files:**
- Modify: `project/server/packages/game-server/src/ws/connection.js`

- [ ] **Step 1: Add event listeners array and onEvent method**

In the `ConnectionManager` constructor (after `this._pendingAcks = new Map();` on line 24), add:

```javascript
    /** @type {Array<(direction: string, msg: object) => void>} */
    this._eventListeners = [];
```

Add a new public method after `sendCommandToGodot`:

```javascript
  /**
   * Register a callback for all WS messages (both directions).
   * @param {(direction: string, msg: object) => void} callback
   */
  onEvent(callback) {
    this._eventListeners.push(callback);
  }

  /** @private */
  _emitEvent(direction, msg) {
    for (const cb of this._eventListeners) {
      try {
        cb(direction, msg);
      } catch (err) {
        console.error("[conn] event listener error:", err.message);
      }
    }
  }
```

- [ ] **Step 2: Call _emitEvent in sendCommandToGodot**

In `sendCommandToGodot`, after `this.godotClient.ws.send(JSON.stringify(cmd));` (line 87), add:

```javascript
      this._emitEvent("to_godot", cmd);
```

- [ ] **Step 3: Call _emitEvent in _routeMessage**

In `_routeMessage`, at the top of each case (before existing logic), add emit calls. Replace the entire `_routeMessage` method:

```javascript
  _routeMessage(_ws, msg) {
    switch (msg.type) {
      case "command_ack":
        this._emitEvent("from_godot", msg);
        this._handleCommandAck(msg);
        break;
      case "state_snapshot":
        this._emitEvent("from_godot", msg);
        this.stateStore.setSnapshot(msg.data);
        this._broadcastToAgents(msg);
        break;
      case "state_event":
        this._emitEvent("from_godot", msg);
        this.stateStore.pushEvent(msg);
        this._broadcastToAgents(msg);
        break;
      default:
        console.log(`[conn] unknown message type: ${msg.type}`);
    }
  }
```

- [ ] **Step 4: Also emit the initial get_state command in _registerGodot**

In `_registerGodot`, after `ws.send(JSON.stringify(cmd));` (line 100), add:

```javascript
    this._emitEvent("to_godot", cmd);
```

- [ ] **Step 5: Verify server still starts**

```bash
cd /Users/apprenticegc/Work/lunar-horse/yokan-projects/legend-dad/project/server/packages/game-server
node -e "
import { GameStateStore } from './src/state/store.js';
import { ConnectionManager } from './src/ws/connection.js';
const store = new GameStateStore();
const cm = new ConnectionManager(store);
let events = [];
cm.onEvent((dir, msg) => events.push({ dir, type: msg.type }));
console.log('listeners:', cm._eventListeners.length);
console.log('OK');
"
```

Expected: `listeners: 1`, `OK`.

- [ ] **Step 6: Lint and commit**

```bash
cd /Users/apprenticegc/Work/lunar-horse/yokan-projects/legend-dad
task lint
git add project/server/packages/game-server/src/ws/connection.js
git commit -m "feat: add onEvent callback to ConnectionManager for replay recording

Co-Authored-By: Claude Opus 4.6 (1M context) <noreply@anthropic.com>"
```

---

## Task 5: Recorder Module

**Files:**
- Create: `project/server/packages/game-server/src/replay/recorder.js`

- [ ] **Step 1: Create recorder.js**

```javascript
// project/server/packages/game-server/src/replay/recorder.js
import { RecordId, Table } from "surrealdb";
import { embed } from "./embedder.js";

/**
 * Records WS events and per-turn decision points to SurrealDB.
 * Passive observer — does not modify or delay message flow.
 */
export class Recorder {
  /**
   * @param {import('surrealdb').Surreal} db
   */
  constructor(db) {
    this._db = db;
    this._sessionId = null;
    this._sequence = 0;
    this._turnSequence = 0;
    this._pendingTurn = null; // { cmdId, action, payload, stateBefore, sentAt }
    this._stateStore = null;
  }

  /**
   * Bind the state store so recorder can capture state_before/state_after.
   * @param {import('../state/store.js').GameStateStore} stateStore
   */
  setStateStore(stateStore) {
    this._stateStore = stateStore;
  }

  /**
   * Start a new recording session.
   * @param {string} playerType — "agent" or "human"
   * @param {string|null} agentModel — e.g. "glm-5.1"
   * @returns {Promise<string>} session record ID
   */
  async startSession(playerType, agentModel = null) {
    const [session] = await this._db.create(new Table("replay_session"), {
      started_at: new Date().toISOString(),
      ended_at: null,
      player_type: playerType,
      agent_model: agentModel,
      initial_state: this._stateStore?.getState() ?? null,
      summary: null,
      total_actions: 0,
      outcome: null,
    });
    this._sessionId = session.id;
    this._sequence = 0;
    this._turnSequence = 0;
    this._pendingTurn = null;
    console.log(`[recorder] session started: ${this._sessionId}`);
    return this._sessionId;
  }

  /**
   * End the current session.
   * @param {string} outcome — "completed", "abandoned", "stuck"
   */
  async endSession(outcome = "completed") {
    if (!this._sessionId) return;

    // Flush any pending turn
    if (this._pendingTurn) {
      await this._flushPendingTurn({ success: false, error: "session_ended" });
    }

    const summary = this._buildSessionSummary(outcome);

    await this._db.merge(this._sessionId, {
      ended_at: new Date().toISOString(),
      total_actions: this._turnSequence,
      outcome,
      summary,
    });

    console.log(`[recorder] session ended: ${this._sessionId} (${outcome}, ${this._turnSequence} actions)`);
    this._sessionId = null;
  }

  /**
   * Record a WS event. Called by ConnectionManager.onEvent.
   * @param {string} direction — "to_godot" or "from_godot"
   * @param {object} msg — raw WS message
   */
  async recordEvent(direction, msg) {
    if (!this._sessionId) return;

    // Write raw event
    this._sequence++;
    await this._db.create(new Table("replay_event"), {
      session: this._sessionId,
      timestamp: new Date().toISOString(),
      direction,
      message: msg,
      sequence: this._sequence,
    });

    // Turn detection
    if (direction === "to_godot" && msg.type === "command" && msg.action !== "get_state") {
      // New turn starts — capture state before
      this._pendingTurn = {
        cmdId: msg.id,
        action: msg.action,
        payload: msg.payload || {},
        stateBefore: structuredClone(this._stateStore?.getState()),
        sentAt: Date.now(),
      };
    }

    if (direction === "from_godot" && msg.type === "command_ack" && this._pendingTurn) {
      if (msg.id === this._pendingTurn.cmdId) {
        // Turn ends — capture result and state after
        // Small delay to let state_events propagate
        await new Promise((r) => setTimeout(r, 50));
        await this._flushPendingTurn({ success: msg.success, error: msg.error ?? null });
      }
    }
  }

  /** @private */
  async _flushPendingTurn(result) {
    if (!this._pendingTurn || !this._sessionId) return;

    const turn = this._pendingTurn;
    this._pendingTurn = null;
    this._turnSequence++;

    const stateAfter = structuredClone(this._stateStore?.getState());
    const text = this._buildTurnText(turn, result, stateAfter);

    let embedding = null;
    try {
      embedding = await embed(text);
    } catch (err) {
      console.error("[recorder] embedding failed:", err.message);
    }

    await this._db.create(new Table("replay_turn"), {
      session: this._sessionId,
      sequence: this._turnSequence,
      state_before: turn.stateBefore,
      action: turn.action,
      payload: turn.payload,
      result,
      state_after: stateAfter,
      text,
      embedding,
    });
  }

  /** @private */
  _buildTurnText(turn, result, stateAfter) {
    const parts = [];

    // Context from state_before
    if (turn.stateBefore) {
      const activeId = turn.stateBefore.active_entity_id || "?";
      const entity = turn.stateBefore.entities?.find(
        (e) => e.entity_id === activeId || e.components?.player_controlled?.active,
      );
      if (entity?.components?.grid_position) {
        const gp = entity.components.grid_position;
        parts.push(`era:${turn.stateBefore.active_era || "?"} pos:(${gp.col},${gp.row}) facing:${gp.facing}`);

        // Nearby entities
        const nearby = (turn.stateBefore.entities || [])
          .filter((e) => {
            if (e.entity_id === entity.entity_id) return false;
            const egp = e.components?.grid_position;
            if (!egp) return false;
            return Math.abs(egp.col - gp.col) <= 2 && Math.abs(egp.row - gp.row) <= 2;
          })
          .map((e) => {
            const egp = e.components.grid_position;
            const type = e.components?.enemy?.enemy_type || e.components?.interactable?.type || "entity";
            return `${type}@(${egp.col},${egp.row})`;
          });

        if (nearby.length > 0) {
          parts.push(`nearby:[${nearby.join(",")}]`);
        }
      }
    }

    // Action
    const payloadStr = Object.keys(turn.payload).length > 0
      ? " " + Object.entries(turn.payload).map(([k, v]) => v).join(" ")
      : "";
    parts.push(`| ${turn.action}${payloadStr}`);

    // Result
    if (result.success) {
      const afterEntity = stateAfter?.entities?.find(
        (e) => e.entity_id === (turn.stateBefore?.active_entity_id || ""),
      );
      if (afterEntity?.components?.grid_position) {
        const agp = afterEntity.components.grid_position;
        parts.push(`| success -> pos:(${agp.col},${agp.row})`);
      } else {
        parts.push("| success");
      }
    } else {
      parts.push(`| failed: ${result.error || "unknown"}`);
    }

    return parts.join(" ");
  }

  /** @private */
  _buildSessionSummary(outcome) {
    return `Session (${this._turnSequence} actions). Outcome: ${outcome}.`;
  }
}
```

- [ ] **Step 2: Lint and commit**

```bash
cd /Users/apprenticegc/Work/lunar-horse/yokan-projects/legend-dad
task lint
git add project/server/packages/game-server/src/replay/recorder.js
git commit -m "feat: add replay Recorder — writes events + embedded turns to SurrealDB

Co-Authored-By: Claude Opus 4.6 (1M context) <noreply@anthropic.com>"
```

---

## Task 6: Context Builder

**Files:**
- Create: `project/server/packages/game-server/src/replay/context-builder.js`

- [ ] **Step 1: Create context-builder.js**

```javascript
// project/server/packages/game-server/src/replay/context-builder.js
import { embed } from "./embedder.js";

/**
 * Queries SurrealDB to build replay context for the agent.
 * Returns a string to inject into the agent's instructions.
 */
export class ContextBuilder {
  /**
   * @param {import('surrealdb').Surreal} db
   */
  constructor(db) {
    this._db = db;
  }

  /**
   * Build context string from past replay data.
   * @param {object|null} currentState — current game state snapshot
   * @param {object} opts
   * @param {number} opts.maxSessions — max past session summaries (default 5)
   * @param {number} opts.maxSimilarTurns — max similar turns from vector search (default 10)
   * @param {number} opts.sessionRecencyHours — only sessions from last N hours (default 24)
   * @returns {Promise<string>} context string for agent instructions
   */
  async buildContext(currentState, opts = {}) {
    const maxSessions = opts.maxSessions ?? 5;
    const maxSimilarTurns = opts.maxSimilarTurns ?? 10;
    const recencyHours = opts.sessionRecencyHours ?? 24;

    const sections = [];

    // 1. Past session summaries
    const summaries = await this._getSessionSummaries(maxSessions, recencyHours);
    if (summaries.length > 0) {
      sections.push("### Session History");
      for (const s of summaries) {
        const ago = this._timeAgo(s.ended_at || s.started_at);
        const model = s.agent_model ? `${s.player_type}/${s.agent_model}` : s.player_type;
        sections.push(`- ${ago}: ${s.summary || "No summary"} (${model})`);
      }
    }

    // 2. Similar past turns (vector search)
    if (currentState) {
      const similarTurns = await this._findSimilarTurns(currentState, maxSimilarTurns);
      if (similarTurns.length > 0) {
        sections.push("");
        sections.push("### Similar Past Situations");
        for (const t of similarTurns) {
          sections.push(`- [turn ${t.sequence}]: ${t.text}`);
        }
      }
    }

    if (sections.length === 0) {
      return ""; // No replay history yet
    }

    return [
      "",
      "## Past Experience",
      "",
      ...sections,
      "",
      "Use this experience to make better decisions. Avoid repeating past failures.",
    ].join("\n");
  }

  /** @private */
  async _getSessionSummaries(maxSessions, recencyHours) {
    const cutoff = new Date(Date.now() - recencyHours * 60 * 60 * 1000).toISOString();
    const [results] = await this._db.query(
      `SELECT started_at, ended_at, player_type, agent_model, summary, total_actions, outcome
       FROM replay_session
       WHERE started_at > $cutoff
       ORDER BY started_at DESC
       LIMIT $limit`,
      { cutoff, limit: maxSessions },
    );
    return results || [];
  }

  /** @private */
  async _findSimilarTurns(currentState, maxTurns) {
    // Build a query text from current state
    const activeId = currentState.active_entity_id || "";
    const entity = (currentState.entities || []).find(
      (e) => e.entity_id === activeId || e.components?.player_controlled?.active,
    );

    if (!entity?.components?.grid_position) {
      return [];
    }

    const gp = entity.components.grid_position;
    const queryText = `era:${currentState.active_era || "?"} pos:(${gp.col},${gp.row}) facing:${gp.facing}`;

    let queryEmbedding;
    try {
      queryEmbedding = await embed(queryText);
    } catch {
      return [];
    }

    const [results] = await this._db.query(
      `SELECT text, sequence, action, payload, result,
              vector::similarity::cosine(embedding, $vec) AS similarity
       FROM replay_turn
       WHERE embedding <~$limit:COSINE:> $vec
       ORDER BY similarity DESC`,
      { vec: queryEmbedding, limit: maxTurns },
    );

    return results || [];
  }

  /** @private */
  _timeAgo(isoString) {
    if (!isoString) return "unknown time";
    const diffMs = Date.now() - new Date(isoString).getTime();
    const mins = Math.floor(diffMs / 60000);
    if (mins < 60) return `${mins}m ago`;
    const hours = Math.floor(mins / 60);
    if (hours < 24) return `${hours}h ago`;
    return `${Math.floor(hours / 24)}d ago`;
  }
}
```

- [ ] **Step 2: Lint and commit**

```bash
cd /Users/apprenticegc/Work/lunar-horse/yokan-projects/legend-dad
task lint
git add project/server/packages/game-server/src/replay/context-builder.js
git commit -m "feat: add replay ContextBuilder — session summaries + vector-searched similar turns

Co-Authored-By: Claude Opus 4.6 (1M context) <noreply@anthropic.com>"
```

---

## Task 7: Update Agent to Accept Replay Context

**Files:**
- Modify: `project/server/packages/game-server/src/mastra/agent.js`

- [ ] **Step 1: Add contextBuilder parameter and inject replay context**

Read the current `agent.js`. Modify `createGameAgent` to accept an optional `contextBuilder` and use it to build replay context. Replace the full file:

```javascript
// project/server/packages/game-server/src/mastra/agent.js
import { Agent } from "@mastra/core/agent";

const BASE_INSTRUCTIONS = `You are an AI agent playing the game "Legend Dad". You control a character on a 10x8 tile grid.

## Game World
- Two timelines: FATHER (present) and SON (future/ruined)
- You control one character at a time (Father or Son)
- Movement is grid-based: up, down, left, right (one tile per move)
- You can interact with objects in front of you (boulders, switches)
- You can switch between Father and Son timelines

## Available Actions
- move(direction) — Move one tile. direction: "up", "down", "left", "right"
- interact() — Interact with the object in the tile you're facing
- switch_era() — Toggle between Father and Son
- get_state() — Get the full game state snapshot

## Tile Types
- 0 = grass/dead_grass (walkable)
- 1 = path (walkable)
- 2 = building/ruin (not walkable)
- 3 = water/blocked (not walkable)

## Strategy
1. Always call get_state() first to understand your position and surroundings
2. Plan your movement path considering walkable tiles
3. Interact with objects when you're adjacent and facing them
4. Use switch_era when you need to affect the other timeline

When asked to explore or play, start by getting the state, then move around the map systematically.`;

/**
 * Create a game-playing agent bound to the Mastra tools.
 *
 * @param {object} tools — { moveTool, interactTool, switchEraTool, getStateTool }
 * @param {object} opts — { modelUrl, apiKey, modelId, contextBuilder, stateStore }
 */
export async function createGameAgent(tools, opts = {}) {
  const modelUrl =
    opts.modelUrl ||
    process.env.ZAI_BASE_URL ||
    "https://api.z.ai/api/coding/paas/v4";
  const apiKey = opts.apiKey || process.env.ZAI_API_KEY || "";
  const modelId = opts.modelId || process.env.ZAI_MODEL || "glm-5.1";

  // Build replay context if context builder is available
  let replayContext = "";
  if (opts.contextBuilder && opts.stateStore) {
    const currentState = opts.stateStore.getState();
    replayContext = await opts.contextBuilder.buildContext(currentState);
    if (replayContext) {
      console.log("[agent] injected replay context (%d chars)", replayContext.length);
    }
  }

  const instructions = replayContext
    ? `${BASE_INSTRUCTIONS}\n${replayContext}`
    : BASE_INSTRUCTIONS;

  return new Agent({
    id: "legend-dad-player",
    name: "Legend Dad Player Agent",
    instructions,
    model: {
      id: `custom/${modelId}`,
      url: modelUrl,
      apiKey: apiKey,
    },
    tools: {
      move: tools.moveTool,
      interact: tools.interactTool,
      switch_era: tools.switchEraTool,
      get_state: tools.getStateTool,
    },
  });
}
```

Note: `createGameAgent` is now `async` because it awaits the context builder. Callers need to be updated.

- [ ] **Step 2: Lint and commit**

```bash
cd /Users/apprenticegc/Work/lunar-horse/yokan-projects/legend-dad
task lint
git add project/server/packages/game-server/src/mastra/agent.js
git commit -m "feat: agent accepts contextBuilder, injects replay context into instructions

Co-Authored-By: Claude Opus 4.6 (1M context) <noreply@anthropic.com>"
```

---

## Task 8: Wire Replay into Server Entry Point

**Files:**
- Modify: `project/server/packages/game-server/src/index.js`

- [ ] **Step 1: Add replay imports and initialization**

Replace the entire `index.js`:

```javascript
// project/server/packages/game-server/src/index.js
import { createServer } from "node:http";
import { WebSocketServer } from "ws";
import { createMastraServer } from "./mastra/index.js";
import { initReplayDB } from "./replay/db.js";
import { initEmbedder } from "./replay/embedder.js";
import { Recorder } from "./replay/recorder.js";
import { ContextBuilder } from "./replay/context-builder.js";
import { GameStateStore } from "./state/store.js";
import { ConnectionManager } from "./ws/connection.js";

const PORT = Number.parseInt(process.env.PORT || "3000", 10);

async function main() {
  // --- State & connections ---
  const stateStore = new GameStateStore();
  const connMgr = new ConnectionManager(stateStore);

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
        replay_enabled: recorder !== null,
      }),
    );
  });

  // --- WebSocket server ---
  const wss = new WebSocketServer({ server });

  wss.on("connection", (ws, req) => {
    console.log(`[ws] new connection from ${req.socket.remoteAddress}`);
    connMgr.handleConnection(ws);

    // Start recording session when Godot connects
    if (recorder) {
      // Detect Godot connection by listening for the first handshake
      const origHandler = connMgr.handleConnection;
      // Session management via connection events
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
      // Detect Godot handshake ack (means Godot just connected)
      if (direction === "to_godot" && msg.type === "command" && msg.action === "get_state") {
        // Initial get_state is sent right after Godot registers
        if (!recorder._sessionId) {
          recorder.startSession("agent", process.env.ZAI_MODEL || "glm-5.1").catch((err) => {
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
    console.log("[mcp] MCP server initialized — tools: move, interact, switch_era, get_state");
  });
}

main().catch((err) => {
  console.error("[server] fatal:", err);
  process.exit(1);
});
```

- [ ] **Step 2: Verify server starts with replay**

```bash
cd /Users/apprenticegc/Work/lunar-horse/yokan-projects/legend-dad/project/server/packages/game-server
node src/index.js &
SERVER_PID=$!
sleep 3
curl -s http://localhost:3000
kill $SERVER_PID 2>/dev/null
wait $SERVER_PID 2>/dev/null
```

Expected: JSON with `replay_enabled: true` (if SurrealDB is running) or `replay_enabled: false` with a warning.

- [ ] **Step 3: Lint and commit**

```bash
cd /Users/apprenticegc/Work/lunar-horse/yokan-projects/legend-dad
task lint
git add project/server/packages/game-server/src/index.js
git commit -m "feat: wire replay recorder + context builder into server startup

Co-Authored-By: Claude Opus 4.6 (1M context) <noreply@anthropic.com>"
```

---

## Task 9: JSON Schemas

**Files:**
- Create: `project/server/packages/game-server/schemas/ws-messages.schema.json`
- Create: `project/server/packages/game-server/schemas/replay-records.schema.json`
- Create: `project/server/packages/game-server/schemas/game-state.schema.json`

- [ ] **Step 1: Create ws-messages.schema.json**

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "WSMessages",
  "description": "All WebSocket message types between Node.js server and Godot",
  "oneOf": [
    { "$ref": "#/definitions/Command" },
    { "$ref": "#/definitions/CommandAck" },
    { "$ref": "#/definitions/StateEvent" },
    { "$ref": "#/definitions/StateSnapshot" },
    { "$ref": "#/definitions/Handshake" },
    { "$ref": "#/definitions/HandshakeAck" }
  ],
  "definitions": {
    "Command": {
      "type": "object",
      "required": ["type", "id", "action", "payload"],
      "properties": {
        "type": { "const": "command" },
        "id": { "type": "string" },
        "action": { "type": "string", "enum": ["move", "interact", "switch_era", "get_state"] },
        "payload": { "type": "object" }
      }
    },
    "CommandAck": {
      "type": "object",
      "required": ["type", "id", "success"],
      "properties": {
        "type": { "const": "command_ack" },
        "id": { "type": "string" },
        "success": { "type": "boolean" },
        "error": { "type": ["string", "null"] }
      }
    },
    "StateEvent": {
      "type": "object",
      "required": ["type", "event", "data"],
      "properties": {
        "type": { "const": "state_event" },
        "event": { "type": "string", "enum": ["entity_updated", "interaction_result", "era_switched", "game_disconnected", "battle_started"] },
        "data": { "type": "object" }
      }
    },
    "StateSnapshot": {
      "type": "object",
      "required": ["type", "data"],
      "properties": {
        "type": { "const": "state_snapshot" },
        "data": { "$ref": "game-state.schema.json" }
      }
    },
    "Handshake": {
      "type": "object",
      "required": ["type", "client_type"],
      "properties": {
        "type": { "const": "handshake" },
        "client_type": { "type": "string", "enum": ["godot", "agent"] },
        "name": { "type": "string" }
      }
    },
    "HandshakeAck": {
      "type": "object",
      "required": ["type", "session_id"],
      "properties": {
        "type": { "const": "handshake_ack" },
        "session_id": { "type": "string" }
      }
    }
  }
}
```

- [ ] **Step 2: Create game-state.schema.json**

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "GameState",
  "description": "Full game state snapshot",
  "type": "object",
  "required": ["active_era", "active_entity_id", "entities"],
  "properties": {
    "active_era": { "type": "string", "enum": ["FATHER", "SON"] },
    "active_entity_id": { "type": "string" },
    "entities": {
      "type": "array",
      "items": {
        "type": "object",
        "required": ["entity_id", "components"],
        "properties": {
          "entity_id": { "type": "string" },
          "components": {
            "type": "object",
            "properties": {
              "grid_position": {
                "type": "object",
                "properties": {
                  "col": { "type": "integer" },
                  "row": { "type": "integer" },
                  "facing": { "type": "string", "enum": ["up", "down", "left", "right"] }
                }
              },
              "timeline_era": {
                "type": "object",
                "properties": {
                  "era": { "type": "string", "enum": ["FATHER", "SON"] }
                }
              },
              "player_controlled": {
                "type": "object",
                "properties": {
                  "active": { "type": "boolean" }
                }
              },
              "enemy": {
                "type": "object",
                "properties": {
                  "enemy_type": { "type": "string" }
                }
              },
              "interactable": {
                "type": "object",
                "properties": {
                  "type": { "type": "string", "enum": ["BOULDER", "SWITCH"] },
                  "state": { "type": "string", "enum": ["DEFAULT", "ACTIVATED"] }
                }
              }
            }
          }
        }
      }
    },
    "map": {
      "type": "object",
      "properties": {
        "width": { "type": "integer" },
        "height": { "type": "integer" },
        "father_tiles": { "type": "array", "items": { "type": "array", "items": { "type": "integer" } } },
        "son_tiles": { "type": "array", "items": { "type": "array", "items": { "type": "integer" } } }
      }
    },
    "battle": { "type": ["object", "null"] }
  }
}
```

- [ ] **Step 3: Create replay-records.schema.json**

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "ReplayRecords",
  "description": "SurrealDB replay record types",
  "definitions": {
    "ReplaySession": {
      "type": "object",
      "required": ["started_at", "player_type"],
      "properties": {
        "id": { "type": "string" },
        "started_at": { "type": "string", "format": "date-time" },
        "ended_at": { "type": ["string", "null"], "format": "date-time" },
        "player_type": { "type": "string", "enum": ["agent", "human"] },
        "agent_model": { "type": ["string", "null"] },
        "initial_state": { "type": ["object", "null"] },
        "summary": { "type": ["string", "null"] },
        "total_actions": { "type": "integer" },
        "outcome": { "type": ["string", "null"], "enum": ["completed", "abandoned", "stuck", null] }
      }
    },
    "ReplayEvent": {
      "type": "object",
      "required": ["session", "timestamp", "direction", "message", "sequence"],
      "properties": {
        "id": { "type": "string" },
        "session": { "type": "string" },
        "timestamp": { "type": "string", "format": "date-time" },
        "direction": { "type": "string", "enum": ["to_godot", "from_godot"] },
        "message": { "type": "object" },
        "sequence": { "type": "integer" }
      }
    },
    "ReplayTurn": {
      "type": "object",
      "required": ["session", "sequence", "action", "payload", "result", "text"],
      "properties": {
        "id": { "type": "string" },
        "session": { "type": "string" },
        "sequence": { "type": "integer" },
        "state_before": { "type": ["object", "null"] },
        "action": { "type": "string" },
        "payload": { "type": "object" },
        "result": {
          "type": "object",
          "properties": {
            "success": { "type": "boolean" },
            "error": { "type": ["string", "null"] }
          }
        },
        "state_after": { "type": ["object", "null"] },
        "text": { "type": "string" },
        "embedding": { "type": ["array", "null"], "items": { "type": "number" } }
      }
    }
  }
}
```

- [ ] **Step 4: Lint and commit**

```bash
cd /Users/apprenticegc/Work/lunar-horse/yokan-projects/legend-dad
task lint
git add project/server/packages/game-server/schemas/
git commit -m "feat: add JSON schemas for WS messages, game state, and replay records

Co-Authored-By: Claude Opus 4.6 (1M context) <noreply@anthropic.com>"
```

---

## Task 10: Integration Test — Agent with Replay

**Files:**
- Modify: `project/server/packages/game-server/src/test-agent.js`

- [ ] **Step 1: Update test-agent.js to enable replay recording**

This is a significant update to the test. Read the current `test-agent.js`, then add replay support. The key changes:

1. Import and initialize replay (db, embedder, recorder, context builder)
2. Start a recording session before the agent runs
3. After the agent runs, query SurrealDB to verify replay data was written
4. Run the agent a second time to verify context builder injects past experience

Add these sections to the `runAgent` function, after the existing agent test:

```javascript
// At top of file, add imports:
import { initReplayDB } from "./replay/db.js";
import { initEmbedder } from "./replay/embedder.js";
import { Recorder } from "./replay/recorder.js";
import { ContextBuilder } from "./replay/context-builder.js";

// In runAgent(), before creating the agent:
let recorder = null;
let contextBuilder = null;
try {
  const db = await initReplayDB();
  await initEmbedder();
  recorder = new Recorder(db);
  recorder.setStateStore(stateStore);
  contextBuilder = new ContextBuilder(db);
  connMgr.onEvent((direction, msg) => {
    recorder.recordEvent(direction, msg).catch(console.error);
  });
  await recorder.startSession("agent", "glm-5.1");
  console.log("[test] replay recording enabled");
} catch (err) {
  console.warn("[test] replay disabled:", err.message);
}

// After agent.generate() completes, end session and verify:
if (recorder) {
  await recorder.endSession("completed");

  // Query SurrealDB to verify data
  const db = await initReplayDB();
  const [sessions] = await db.query("SELECT * FROM replay_session");
  const [events] = await db.query("SELECT count() FROM replay_event GROUP ALL");
  const [turns] = await db.query("SELECT text, sequence FROM replay_turn ORDER BY sequence");

  console.log("\n=== REPLAY VERIFICATION ===");
  console.log(`Sessions: ${sessions?.length || 0}`);
  console.log(`Events: ${events?.[0]?.count || 0}`);
  console.log(`Turns: ${turns?.length || 0}`);
  if (turns?.length > 0) {
    console.log("Turn texts:");
    for (const t of turns) {
      console.log(`  [${t.sequence}] ${t.text}`);
    }
  }

  // Test context builder
  const context = await contextBuilder.buildContext(stateStore.getState());
  console.log("\n=== CONTEXT BUILDER OUTPUT ===");
  console.log(context || "(empty — no past sessions yet, this is the first run)");

  await db.close();
}
```

- [ ] **Step 2: Run the full test**

```bash
cd /Users/apprenticegc/Work/lunar-horse/yokan-projects/legend-dad/project/server/packages/game-server
ZAI_API_KEY="<key>" node src/test-agent.js
```

Expected:
- Agent plays (moves right, right, down) as before
- Replay verification shows: 1 session, multiple events, 3+ turns with text descriptions
- Context builder output shows session history (from the current session that just ended)

- [ ] **Step 3: Lint and commit**

```bash
cd /Users/apprenticegc/Work/lunar-horse/yokan-projects/legend-dad
task lint
git add project/server/packages/game-server/src/test-agent.js
git commit -m "test: update agent test to verify replay recording and context builder

Co-Authored-By: Claude Opus 4.6 (1M context) <noreply@anthropic.com>"
```

---

## Summary

| Task | Component | Commits |
|---|---|---|
| 1 | Install dependencies | 1 |
| 2 | SurrealDB connection + schema | 1 |
| 3 | Embedder module (fastembed) | 1 |
| 4 | onEvent callback on ConnectionManager | 1 |
| 5 | Recorder module | 1 |
| 6 | Context Builder | 1 |
| 7 | Update agent for replay context | 1 |
| 8 | Wire replay into server entry | 1 |
| 9 | JSON schemas | 1 |
| 10 | Integration test with replay | 1 |
| **Total** | | **10 commits** |
