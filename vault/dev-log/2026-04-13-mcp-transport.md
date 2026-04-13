---
date: 2026-04-13
agent: claude-code
version: 0.1.0-111
session: mcp-transport-wiring
---

# MCP Streamable HTTP Transport + Game Player Skill

## Summary

Wired the existing Mastra MCPServer to a Streamable HTTP transport on `/mcp` so Claude Code (and any MCP client) can call game tools against a running game server with a live Godot connection. Added a `poll_events` tool for receiving game state events. Created a `game-player` agent skill with a 7-step startup checklist. Verified full stack end-to-end: web build, both servers, MCP handshake, Godot connection, and 19/19 test suite passing.

## Commits

- `b4fecd4` feat: add EventQueue and EventQueueRegistry for MCP sessions
- `0dc728e` feat: add poll_events MCP tool for draining game event buffer
- `e0034f6` feat: register poll_events tool in MCPServer when event registry provided
- `c396821` feat: wire MCP Streamable HTTP transport on /mcp endpoint
- `42088da` feat: register legend-dad-game MCP server for Claude Code
- `3d0729d` fix: address code review — encapsulation and dead parameter
- `9137e87` feat: add game-player agent skill for MCP-based game operation
- `b2b960b` fix: use eager default queue for MCP event broadcasting
- `12cd2a6` docs: add dev-log for MCP transport session
- `3be207d` docs: document Mastra onsessioninitialized bug and workaround
- `dc6da79` docs: add startup checklist and verification steps to game-player skill

## Decisions

1. **Streamable HTTP over stdio** — tools depend on a live Godot WebSocket connection in the same process. stdio would spawn a separate server with no Godot connection.
2. **WebSocket MCP not viable** — MCP spec doesn't define WS transport (chose Streamable HTTP instead), and Claude Code's MCP client doesn't support it. Also protocol mismatch between game protocol and MCP JSON-RPC.
3. **poll_events over push notifications** — MCP Streamable HTTP supports server-initiated SSE, but Claude Code may not act on server-pushed MCP notifications. Polling is guaranteed to work and matches Claude's turn-based model.
4. **Eager default queue** — Mastra's `startHTTP` overrides the `onsessioninitialized` callback internally (their code hardcodes it at line 3635 of dist/index.js). Workaround: create a "default" queue at startup for the single-client case.
5. **Independent skill, no coupling to agent.js** — Game world knowledge is duplicated between `mastra/agent.js` (for GLM/Qwen agents) and `game-player` skill (for Claude Code). Different audiences, different needs.

## Files Created/Modified

- `src/mcp/event-queue.js` — EventQueue (ring buffer) + EventQueueRegistry (session management, GC)
- `src/mastra/tools/poll-events.js` — poll_events Mastra tool
- `src/mastra/index.js` — optional eventRegistry param, conditional poll_events registration
- `src/index.js` — `/mcp` route, default queue, event broadcast wiring
- `src/test-mcp.js` — 19-test end-to-end MCP verification
- `.claude/settings.json` — MCP server registration for Claude Code
- `.agent/skills/06-gameplay/game-player/SKILL.md` — agent skill with 7-step startup checklist
- `.agent/skills/INDEX.md` — added 06-gameplay category
- `vault/specs/2026-04-13-mcp-transport-design.md` — spec with Known Issues section

## Verification (full stack)

| Step | Check | Result |
|------|-------|--------|
| 1 | Web build exists | `complete-app.html` present |
| 2 | Start servers (`task dev`) | `:8080` static + `:3000` game server |
| 3 | Health check | `mcp_enabled: true` |
| 4 | MCP endpoint | Returns server info + tools capability |
| 5 | Open browser | Godot game loaded, both eras visible |
| 6 | Godot connected | `godot_connected: true` |
| 7 | Test suite | 19/19 passed |

## Blockers

None.

## Next Steps

- Set up testing infrastructure: GUT for Godot tests, Playwright/agent-browser for browser E2E tests, `task test` command
- Wire .env into Taskfile/nodemon — so `task dev` auto-loads API keys
- Godot gameplay replay spec — father's recorded actions replaying during son's adventure
- Consider filing a Mastra issue about `onsessioninitialized` being overridden in `startHTTP`
