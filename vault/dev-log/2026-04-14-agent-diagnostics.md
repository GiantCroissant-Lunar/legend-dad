---
date: 2026-04-14
agent: Claude Code (Opus 4.6)
version: 0.1.0-192
---

# Agent Diagnostics: Cell Movement Fix, Time Service, Screenshot Capture

## Summary

Implemented three features to fix the tile-size movement bug and add diagnostic tools for both AI agents and human developers:

1. **GameConfig autoload** — single source of truth for cell_size (read from LDtk), map dimensions, and movement tuning. Eliminated all hardcoded `TILE_SIZE = 32` constants across 7 files.
2. **TimeService autoload** — pause/resume/speed control/frame-stepping via `Engine.time_scale`. Exposed as WS commands, MCP tools, and keyboard shortcuts (P/N/[/]).
3. **Screenshot capture (MVP)** — SubViewport texture capture via WS command + MCP tool, plus Playwright browser-level screenshot tool.

## Commits

- `e9bc5c9` feat: add GameConfig autoload as single source of truth for cell size
- `c525713` refactor: migrate TILE_SIZE/MOVE_SPEED/move_cooldown constants to GameConfig
- `4a4ce24` feat: wire GameConfig into LocationManager and main for dynamic cell size
- `bb9ef87` feat: add TimeService autoload with pause/resume/speed/frame-step
- `9acaaa9` feat: add time control WS commands and PROCESS_MODE_ALWAYS for ws_client
- `7ca137f` feat: add time control keyboard shortcuts (P/N/[/]) and HUD display
- `d6fbc5f` feat: add time control MCP tools (set_time_speed, pause, resume, step_frame)
- `4de1a74` feat: add screenshot WS command for SubViewport capture
- `b0fc1fa` feat: add screenshot MCP tool for SubViewport capture
- `d1b134b` feat: add browser_screenshot MCP tool via Playwright
- `7612370` docs: update WS message schema with time control and screenshot commands

## Decisions

- **Cell size from LDtk:** `defaultGridSize` (16) is read at location load time rather than hardcoded. This means changing the LDtk grid automatically fixes all rendering.
- **Engine.time_scale for pause:** Idiomatic Godot approach. WS client uses `PROCESS_MODE_ALWAYS` to stay responsive during pause.
- **Screenshot MVP over video:** On-demand screenshots combined with frame-stepping gives 80% diagnostic value at 20% complexity. ffmpeg video capture deferred to future work.
- **Playwright added to game-server deps:** Required for browser_screenshot tool. Could be moved to a separate package later if it bloats the dependency tree.

## Blockers

None.

## Next Steps

- Manual visual verification: run `task dev`, check tile sizes look correct, test P/N/[/] shortcuts
- Run full `task test` suite (including GUT tests for GameConfig/TimeService)
- Future: ffmpeg video capture (SubViewport frame streaming), replay visualization
