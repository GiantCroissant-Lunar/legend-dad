---
date: 2026-04-12
agent: claude-code
branch: main
version: 0.1.0-99
tags: [websocket, agent, mastra, replay, surrealdb, fastembed, infra]
---

# Session Log — WS Agent Protocol + Replay System + Infra

## Summary

Built two interconnected features plus infrastructure: a WebSocket agent protocol that lets AI agents control the game as a normal player, a replay system that records sessions to SurrealDB with per-turn vector embeddings for agent learning, and model provider rotation with centralized env config.

## What Was Built

### WS Agent Protocol

- **Godot action bus** (`GameActions` autoload) — decouples input sources from game logic via signals
- **WSClient** (Godot) ��� connects to Node.js server, dispatches commands to action bus, pushes state
- **S_ActionProcessor** — new ECS system processing the action bus (replaces S_Interaction, simplifies S_PlayerInput)
- **Mastra-powered server** — replaced echo server with full agent runtime
- **4 game tools** — `move`, `interact`, `switch_era`, `get_state` as Mastra `createTool()` with Zod schemas
- **MCP server** — tools exposed via Mastra MCPServer (transport wiring deferred)
- **Connection manager** — Godot/agent client routing, handshake protocol, command ack correlation
- **State store** — in-memory cache updated by Godot state events
- **WS protocol** — JSON message format (command, command_ack, state_event, state_snapshot, handshake)

### Replay System

- **SurrealDB schema** — 3 tables: `replay_session`, `replay_event`, `replay_turn` with HNSW vector index
- **fastembed integration** — BGE-small-en-v1.5 model (384 dims) for per-turn embeddings
- **Recorder** — passive observer on ConnectionManager, writes raw events + embedded turns
- **Context Builder** — queries session summaries + vector-searched similar turns for agent context injection
- **JSON schemas** — canonical schemas for WS messages, game state, replay records (quicktype-ready)
- **Agent updated** — `createGameAgent` now async, injects replay context into instructions

### Model Provider Rotation + Infra

- **Provider rotation** — round-robin between Z.AI (GLM-5.1) and Alibaba (Qwen 3.5-plus) to avoid rate limits
- **`infra/.env`** — centralized environment config for API keys, SurrealDB, ports (gitignored)
- **`infra/.env.example`** — committed template without secrets

## Verification

- Agent (GLM-5.1 via Z.AI) successfully controlled game: `get_state → move right → move right → move down`
- Agent recognized nearby enemy (slime) and warned about it
- Replay data written to SurrealDB: sessions, events, turns with embeddings
- Context builder retrieves past session history + similar turns via vector search
- Replay learning confirmed: context grew across 3 runs (155 → 519 → 892 chars)
- Provider rotation tested: zai selected, alibaba available as fallback

## Commits

35 commits total (32 on `feature/ws-agent-protocol` merged as `d37d206`, plus 3 post-merge).

Key commits:
- `80ab47c` chore: add mastra and zod dependencies
- `51e1d71` feat: replace echo server with Mastra-powered game server
- `9942389` feat: add GameActions autoload
- `fafa749` feat: wire WSClient into main scene
- `d9d329b` feat: add Mastra game-playing agent + verification test
- `0d70eea` feat: add SurrealDB connection and replay schema
- `550a95b` feat: add fastembed wrapper
- `0023d90` feat: add replay Recorder
- `b13abb9` test: update agent test to verify replay recording
- `e7918ef` feat: add model provider rotation (zai + alibaba)
- `5ad4990` chore: add infra/.env.example and gitignore secrets

## Decisions

| Decision | Choice | Rationale |
|---|---|---|
| Agent protocol | Semantic commands over WS | Agent sends move/interact, not raw key events |
| Server architecture | Mastra monolith | Tools = protocol, MCP exposure, agent runtime in-process |
| Action bus pattern | Autoload singleton | Standard Godot pattern; deferred ECS alternatives noted |
| Replay storage | SurrealDB (existing, port 6480) | Already running; multi-model (document + vector) |
| Embeddings | fastembed local (384d) | No API dependency, ~5ms per embed |
| Embedding granularity | Per-turn | Action + surrounding state = natural decision unit |
| Recording location | Node.js only | Server sees all WS traffic; Godot unchanged |
| Agent model | GLM-5.1 via Z.AI (OpenAI-compatible) | Available via coding plan API |
| Fallback model | Qwen 3.5-plus via Alibaba | Round-robin rotation to avoid rate limits |
| Env config | `infra/.env` (gitignored) | Centralized secrets, `.env.example` committed |

## Known Issues

- Pre-commit biome hook version mismatch (1.9.0 pinned vs 1.9.4 installed) causes formatting race during commit — files pass `pre-commit run --all-files` but fail during `git commit`
- SurrealDB SDK v2 → v3 compatibility: `db.create(Table)` had CBOR encoding issues, switched to `db.query("CREATE ...")`
- fastembed `libc++abi` crash at process exit — cosmetic, occurs after `process.exit(0)`
- MCP server transport not wired (created but not started — needs stdio or HTTP endpoint for Claude Code)

## Blockers

None.

## Next Steps

1. **Wire `.env` into Taskfile/nodemon** — `task dev` should auto-load `infra/.env`
2. **Test with real Godot build** — `task build && task serve`, verify WSClient connects in browser
3. **Wire MCP transport** — enable Claude Code to call game tools directly
4. **Godot gameplay replay** — father's recorded actions replay during son's adventure (separate design spec needed)
5. **Playwright integration** — automated browser testing with the real Godot web build
6. **Battle system WS commands** — currently observe-only, add battle action tools
7. **Fix biome pre-commit version** — pin project biome to match hook version
