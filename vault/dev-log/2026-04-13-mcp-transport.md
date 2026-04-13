---
date: 2026-04-13
agent: claude-code
version: 0.1.0-109
session: mcp-transport-wiring
---

# MCP Streamable HTTP Transport + Game Player Skill

## Summary

Wired the existing Mastra MCPServer to a Streamable HTTP transport on `/mcp` so Claude Code (and any MCP client) can call game tools against a running game server with a live Godot connection. Added a `poll_events` tool for receiving game state events. Created a `game-player` agent skill documenting the MCP gameplay workflow.

## Commits

- `b4fecd4` feat: add EventQueue and EventQueueRegistry for MCP sessions
- `0dc728e` feat: add poll_events MCP tool for draining game event buffer
- `e0034f6` feat: register poll_events tool in MCPServer when event registry provided
- `c396821` feat: wire MCP Streamable HTTP transport on /mcp endpoint
- `42088da` feat: register legend-dad-game MCP server for Claude Code
- `3d0729d` fix: address code review — encapsulation and dead parameter
- `9137e87` feat: add game-player agent skill for MCP-based game operation
- `b2b960b` fix: use eager default queue for MCP event broadcasting

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
- `.agent/skills/06-gameplay/game-player/SKILL.md` — agent skill for game operation
- `.agent/skills/INDEX.md` — added 06-gameplay category

## Blockers

None.

## Next Steps

- Test with real Godot build — `task build && task serve`, open in browser, verify Claude Code MCP tools drive the actual game
- Wire .env into Taskfile/nodemon — so `task dev` auto-loads API keys
- Godot gameplay replay spec — father's recorded actions replaying during son's adventure
- Consider filing a Mastra issue about `onsessioninitialized` being overridden in `startHTTP`
