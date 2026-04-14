# Agent Diagnostics: Cell Movement, Time Service, Screenshot Capture

**Date:** 2026-04-14
**Status:** Draft
**Scope:** Three features that improve movement correctness and agent/human diagnostic capabilities

## Problem

1. Player appears to jump 2 tiles per move because `TILE_SIZE = 32` is hardcoded across 7 files while LDtk uses a 16px grid. `map_height = px_height / 16` produces cell counts in 16px units, but rendering multiplies by 32, doubling the map's pixel footprint and shrinking tiles visually.
2. The AI agent has no tools to diagnose visual issues — no screenshot capture, no way to slow/pause the game for precise inspection.
3. Hardcoded magic numbers (`TILE_SIZE`, `MOVE_SPEED`, `move_cooldown`) violate the new AGENTS.md rule 5: "No hardcoded adjustable values."

## Feature 1: GameConfig Autoload — Single Source of Truth

### Purpose

Replace all scattered `TILE_SIZE = 32` constants with a single `GameConfig` autoload that reads values from data sources at runtime.

### Autoload: `GameConfig`

**File:** `project/hosts/complete-app/scripts/game_config.gd`
**Registered as:** autoload `GameConfig` in `project.godot`

**Properties:**

| Property | Type | Source | Default |
|---|---|---|---|
| `cell_size` | `int` | LDtk project `defaultGridSize` | 16 |
| `map_width` | `int` | LDtk level `pxWid / cell_size` | 0 |
| `map_height` | `int` | LDtk level `pxHei / cell_size` | 0 |
| `move_speed` | `float` | Config (future: location data) | 8.0 |
| `move_cooldown` | `float` | Config (future: location data) | 0.15 |

**Population flow:**

1. `LocationManager.load_location()` parses LDtk project, calls `GameConfig.cell_size = project.defaultGridSize`
2. `main.gd._load_ldtk_level()` computes `GameConfig.map_width = px_width / GameConfig.cell_size`, same for height
3. Fallback layout sets `GameConfig.map_width/height` directly

### Files to Change

Remove local `TILE_SIZE` constant, replace with `GameConfig.cell_size`:

| File | Current Usage | Change |
|---|---|---|
| `main.gd` | Camera zoom, camera follow offset, view building | `GameConfig.cell_size` everywhere |
| `s_grid_movement.gd` | `col * TILE_SIZE` pixel conversion | `col * GameConfig.cell_size` |
| `s_action_processor.gd` | Unused constant (declared but not referenced for pixel math) | Remove constant |
| `entity_visual.gd` | Draw sizes for placeholder sprites | `GameConfig.cell_size` |
| `c_grid_position.gd` | `_init` sets `visual_x = col * 32` | `visual_x = col * GameConfig.cell_size` |
| `tileset_factory.gd` | Atlas generation, tile_size | `GameConfig.cell_size` |
| `pck_builder.gd` | Fallback constant, already reads manifest | Remove constant, use manifest value |

### Camera Zoom Fix

Current broken logic in `_update_camera_zoom`:
```
map_pixel_height = map_height * TILE_SIZE  # map_height in 16px cells, TILE_SIZE=32 → 2x too large
target_zoom = viewport_height / map_pixel_height  # zoom too small → tiles tiny
```

Fixed:
```
map_pixel_height = GameConfig.map_height * GameConfig.cell_size  # consistent units
target_zoom = viewport_height / map_pixel_height
```

Since `map_height` will now be computed as `px_height / cell_size` using the same `cell_size`, the units are consistent and tiles render at the correct visual size.

## Feature 2: TimeService Autoload + MCP Tools

### Purpose

Allow both humans and AI agents to pause, slow down, speed up, and frame-step the game for precise visual diagnostics.

### Autoload: `TimeService`

**File:** `project/hosts/complete-app/scripts/time_service.gd`
**Registered as:** autoload `TimeService` in `project.godot`
**Process mode:** `PROCESS_MODE_ALWAYS` (must tick even when `Engine.time_scale = 0`)

**API:**

| Method | Behavior |
|---|---|
| `set_speed(multiplier: float)` | Sets `Engine.time_scale`. Clamps to 0.25–4.0. Stores as `_current_speed`. |
| `pause()` | Stores current speed in `_saved_speed`, sets `Engine.time_scale = 0.0`, sets `_paused = true` |
| `resume()` | Restores `Engine.time_scale = _saved_speed`, sets `_paused = false` |
| `step_frame()` | Only works when paused. Sets `_step_requested = true`. In `_process`: unpauses for one tick, re-pauses. |
| `get_state() -> Dictionary` | Returns `{ "paused": bool, "speed": float }` |

**Frame-step implementation:**

```
# In _process (runs even when paused due to PROCESS_MODE_ALWAYS):
if _step_requested:
    Engine.time_scale = _saved_speed
    _step_requested = false
    _step_active = true
elif _step_active:
    Engine.time_scale = 0.0
    _step_active = false
```

Timing detail: `Engine.time_scale` affects the `delta` computed at frame start. So when `step_frame()` restores time_scale, the current frame's delta is still 0 (already computed). The *next* frame gets a real delta — that's the one game logic actually processes. TimeService re-pauses in that same frame's `_process`, but since delta was already computed, all other nodes still get the real delta. Net result: exactly one frame of game logic per step.

### WS Client Fix

`ws_client.gd` must set `process_mode = Node.PROCESS_MODE_ALWAYS` so WebSocket polling continues during pause. Add in `_ready()`.

### WS Protocol — New Commands

| Command | Payload | Behavior |
|---|---|---|
| `time_set_speed` | `{ "speed": float }` | Calls `TimeService.set_speed(speed)` |
| `time_pause` | `{}` | Calls `TimeService.pause()` |
| `time_resume` | `{}` | Calls `TimeService.resume()` |
| `time_step` | `{}` | Calls `TimeService.step_frame()` |

All return standard `command_ack` with `{ success: true }`.

### MCP Tools (Server Side)

Four new tools registered in Mastra:

| Tool | Input | Output |
|---|---|---|
| `set_time_speed` | `{ speed: number }` | `{ success, error }` |
| `pause_time` | `{}` | `{ success, error }` |
| `resume_time` | `{}` | `{ success, error }` |
| `step_frame` | `{}` | `{ success, error }` |

Each sends the corresponding WS command to Godot and awaits `command_ack`.

### Human Keyboard Shortcuts

Added in `main.gd._input()`:

| Key | Action |
|---|---|
| `P` | Toggle pause/resume |
| `N` | Step one frame (while paused) |
| `[` | Decrease speed by 0.25x (min 0.25) |
| `]` | Increase speed by 0.25x (max 4.0) |

Debug HUD (`_update_debug_hud`) shows current time state: `Time: 1.0x` or `Time: PAUSED` or `Time: 0.5x`.

## Feature 3: Screenshot Capture (MVP — On-Demand)

### Purpose

Allow agents and humans to capture precise game screenshots for visual diagnostics. Combined with TimeService, enables before/after comparison of individual frames.

### Godot Side — Screenshot Command in `ws_client.gd`

New command handler for `screenshot`:

**Payload:**
```json
{
  "viewport": "father" | "son" | "both",  // default: active era
  "format": "png" | "jpeg",               // default: "jpeg"
  "quality": 80,                           // jpeg quality, 1-100
  "max_width": 512                         // optional downscale
}
```

**Implementation:**
1. Find the target SubViewport(s) via `get_tree().root.get_node("Main")`
2. Call `viewport.get_texture().get_image()`
3. Optionally resize if `max_width` is set: `image.resize(max_width, proportional_height)`
4. Encode: `image.save_png_to_buffer()` or `image.save_jpg_to_buffer(quality)`
5. Base64-encode the buffer
6. Return in `command_ack`:

Single viewport:
```json
{ "success": true, "screenshot": "data:image/jpeg;base64,..." }
```

Both viewports:
```json
{ "success": true, "father_screenshot": "data:image/...", "son_screenshot": "data:image/..." }
```

### MCP Tool — `screenshot`

**Input:**
```json
{
  "viewport": "father" | "son" | "both",  // optional, default: active
  "format": "png" | "jpeg",               // optional, default: "jpeg"
  "quality": 80,                           // optional
  "max_width": 512                         // optional
}
```

**Output:** `{ success, screenshot(s), error }`

### MCP Tool — `browser_screenshot`

Uses Playwright (already available in E2E test infra) to capture the full browser page.

**Input:**
```json
{
  "filename": "my-capture"  // optional, default: timestamp
}
```

**Implementation:**
- Server-side: reuses existing Playwright browser context if running (E2E test infra), or connects to a running Chromium instance via CDP. Does not start a fresh browser per call.
- Calls `page.screenshot()` on the game page
- Saves to `build/_artifacts/latest/screenshots/{filename}.png`
- Returns `{ success, path, error }`

### Agent Diagnostic Workflow

Typical movement diagnosis sequence:
```
pause_time()
screenshot({ viewport: "both" })          → before state
step_frame()
screenshot({ viewport: "both" })          → after one frame
step_frame() × N                          → advance through animation
screenshot({ viewport: "both" })          → after animation
resume_time()
```

Compare screenshots to verify player moved exactly one cell visually.

## Future Follow-Up (Not In Scope)

- **Video capture:** SubViewport frame streaming to ffmpeg for continuous recording
- **Replay visualization:** combine replay system recordings with screenshot capture
- **Remote capture:** capture from headless Godot running on CI

## Dependencies

- LDtk project file must have `defaultGridSize` set (currently 16)
- Playwright available for `browser_screenshot` (already installed for E2E)
- No new external dependencies (no ffmpeg for MVP)
