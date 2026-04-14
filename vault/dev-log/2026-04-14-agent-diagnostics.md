---
date: 2026-04-14
agent: Claude Code (Opus 4.6)
version: 0.1.0-194
---

# Agent Diagnostics: Cell Movement Fix, Time Service, Screenshot Capture

## Summary

15 commits delivering three features plus a movement bug fix:

1. **GameConfig autoload** — single source of truth for cell_size (read from LDtk `defaultGridSize`), map dimensions, and movement tuning. Eliminated all hardcoded `TILE_SIZE = 32` across 7 files. Added AGENTS.md rule 5 prohibiting hardcoded adjustable values.
2. **TimeService autoload** — pause/resume/speed control/frame-stepping via `Engine.time_scale`. Exposed as WS commands, 4 MCP tools, and keyboard shortcuts (P/N/[/]). Debug HUD shows time state.
3. **Screenshot capture (MVP)** — SubViewport texture capture via WS `screenshot` command + MCP tool (supports viewport selection, format, quality, resize). Playwright browser-level screenshot as separate MCP tool.
4. **Debounced movement fix** — root-caused stale `_pending_move` persisting across frames after key release, causing double-moves. Implemented reactive debounce: first press fires instantly, pending cleared each frame, repeat moves only after 200ms sustained hold.

## Commits

- `587a59c` docs: add agent diagnostics design spec and no-hardcoded-values rule
- `89cc219` docs: add agent diagnostics implementation plan
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
- `9fe4c5d` docs: add dev-log for agent diagnostics session
- `984c94d` fix: debounced movement — tap moves exactly 1 cell, hold repeats after delay

## Decisions

- **Cell size from LDtk:** `defaultGridSize` (16) read at location load time. Changing LDtk grid automatically propagates to all rendering and movement.
- **No hardcoded adjustable values (AGENTS.md rule 5):** All tunable constants must have a single source of truth. Enforced project-wide going forward.
- **Engine.time_scale for pause:** Idiomatic Godot approach. WS client and TimeService use `PROCESS_MODE_ALWAYS` to stay responsive during pause.
- **Screenshot MVP over video:** On-demand screenshots + frame-stepping gives precise before/after diagnostics. ffmpeg video deferred.
- **Reactive debounce for movement:** Borrowed from RxJS patterns. `_pending_move` cleared every frame (no stale queuing), re-set by S_PlayerInput if key still held. `move_repeat_delay` (200ms) prevents accidental double-moves on tap while allowing smooth continuous movement on sustained hold.
- **Playwright added to game-server deps:** Required for `browser_screenshot` MCP tool.

## Root Cause Analysis: Double-Move Bug

**Symptom:** Player moved +2 cells per key tap instead of +1.

**Investigation:** Added diagnostic prints to `s_action_processor.gd` — `_on_move` signal handler, cooldown check, and actual move execution. Console output from headless Playwright run revealed:
- First move fired correctly at `cooldown_was=-4.416` (deeply negative from idle time)
- `_pending_move` persisted as `RIGHT` even after key release (80ms hold)
- Cooldown expired 5 frames later, stale `_pending_move` fired second move

**Root cause:** `_pending_move` was only cleared on successful move execution, not on each frame. Signal from `S_PlayerInput` set it, but nothing cleared it when the key was released. The pending value leaked through the cooldown window.

**Fix:** Reactive debounce pattern — always consume `_pending_move` at start of each frame, track hold duration independently, gate repeat moves behind `move_repeat_delay`.

## Verified

- Playwright automated test: short tap (80ms) = exactly +1 cell, confirmed via HUD position
- Pause key (P) shows "Time: PAUSED" in HUD
- Tiles render at correct visual scale (camera zoom uses consistent cell_size units)
- Server tests: 12 passed, 1 skipped, 0 failures

## Next Steps

- Run full `task test` suite (including GUT tests for GameConfig/TimeService)
- Test WS screenshot command end-to-end with an MCP agent
- Future: ffmpeg video capture, replay visualization
