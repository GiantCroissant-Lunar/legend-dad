# Agent Diagnostics Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Fix the tile-size movement bug by introducing a single source of truth for cell size, then add time manipulation and screenshot tools for agent/human diagnostics.

**Architecture:** Three layers built in dependency order: (1) `GameConfig` autoload reads cell_size from LDtk and replaces all hardcoded `TILE_SIZE` constants, (2) `TimeService` autoload wraps `Engine.time_scale` with pause/resume/frame-step exposed via WS+MCP, (3) screenshot capture via SubViewport texture grab and Playwright page capture, both exposed as MCP tools.

**Tech Stack:** Godot 4.6 (GDScript), Node.js (ES modules), Mastra MCP tools (zod schemas), Vitest, GUT

---

## File Map

### New Files

| File | Responsibility |
|---|---|
| `project/hosts/complete-app/scripts/game_config.gd` | Autoload: single source of truth for cell_size, map dimensions, tunable constants |
| `project/hosts/complete-app/scripts/time_service.gd` | Autoload: pause/resume/speed/frame-step via Engine.time_scale |
| `project/hosts/complete-app/tests/test_game_config.gd` | GUT tests for GameConfig |
| `project/hosts/complete-app/tests/test_time_service.gd` | GUT tests for TimeService |
| `project/server/packages/game-server/src/mastra/tools/time-control.js` | MCP tools: set_time_speed, pause_time, resume_time, step_frame |
| `project/server/packages/game-server/src/mastra/tools/screenshot.js` | MCP tool: screenshot (SubViewport capture via WS) |
| `project/server/packages/game-server/src/mastra/tools/browser-screenshot.js` | MCP tool: browser_screenshot (Playwright page capture) |
| `project/server/packages/game-server/src/__tests__/time-control.test.js` | Vitest tests for time-control MCP tools |
| `project/server/packages/game-server/src/__tests__/screenshot.test.js` | Vitest tests for screenshot MCP tools |

### Modified Files

| File | Change |
|---|---|
| `project/hosts/complete-app/project.godot` | Register GameConfig and TimeService autoloads |
| `project/hosts/complete-app/scripts/location_manager.gd` | Set GameConfig.cell_size from LDtk project |
| `project/hosts/complete-app/scripts/main.gd` | Remove TILE_SIZE, use GameConfig, add time shortcuts, add screenshot handler |
| `project/hosts/complete-app/ecs/systems/s_grid_movement.gd` | Remove TILE_SIZE, use GameConfig.cell_size |
| `project/hosts/complete-app/ecs/systems/s_action_processor.gd` | Remove TILE_SIZE, use GameConfig for cooldown |
| `project/hosts/complete-app/ecs/components/c_grid_position.gd` | Remove hardcoded `* 32`, use GameConfig.cell_size |
| `project/hosts/complete-app/scripts/entity_visual.gd` | Remove TILE_SIZE, use GameConfig.cell_size |
| `project/hosts/complete-app/scripts/tileset_factory.gd` | Remove TILE_SIZE, use GameConfig.cell_size |
| `project/hosts/complete-app/scripts/pck_builder.gd` | Remove TILE_SIZE, read from manifest only |
| `project/hosts/complete-app/scripts/ws_client.gd` | Add process_mode ALWAYS, handle time/screenshot commands |
| `project/server/packages/game-server/src/mastra/index.js` | Register new MCP tools |
| `project/server/packages/game-server/src/ws/protocol.js` | No change needed (createCommand is generic) |
| `project/server/packages/game-server/schemas/ws-messages.schema.json` | Add time/screenshot command schemas |

---

## Task 1: Create GameConfig Autoload

**Files:**
- Create: `project/hosts/complete-app/scripts/game_config.gd`
- Create: `project/hosts/complete-app/tests/test_game_config.gd`
- Modify: `project/hosts/complete-app/project.godot`

- [ ] **Step 1: Write GUT test for GameConfig**

Create `project/hosts/complete-app/tests/test_game_config.gd`:

```gdscript
extends GutTest

func test_default_values():
	# GameConfig should have sensible defaults before any location is loaded
	assert_eq(GameConfig.cell_size, 16, "default cell_size should be 16 (LDtk default)")
	assert_eq(GameConfig.map_width, 0, "map_width should be 0 before level load")
	assert_eq(GameConfig.map_height, 0, "map_height should be 0 before level load")
	assert_almost_eq(GameConfig.move_speed, 8.0, 0.01, "default move_speed should be 8.0")
	assert_almost_eq(GameConfig.move_cooldown, 0.15, 0.01, "default move_cooldown should be 0.15")

func test_cell_size_setter():
	var original = GameConfig.cell_size
	GameConfig.cell_size = 32
	assert_eq(GameConfig.cell_size, 32, "cell_size should be settable")
	GameConfig.cell_size = original

func test_map_dimensions_setter():
	GameConfig.map_width = 20
	GameConfig.map_height = 16
	assert_eq(GameConfig.map_width, 20)
	assert_eq(GameConfig.map_height, 16)
	GameConfig.map_width = 0
	GameConfig.map_height = 0
```

- [ ] **Step 2: Run test to verify it fails**

Run: `task test:godot` (or `$GODOT_PATH --headless --path project/hosts/complete-app -s addons/gut/gut_cmdln.gd -gtest=res://tests/test_game_config.gd`)
Expected: FAIL — `GameConfig` autoload not found.

- [ ] **Step 3: Create GameConfig autoload**

Create `project/hosts/complete-app/scripts/game_config.gd`:

```gdscript
class_name GameConfigClass
extends Node

## Single source of truth for cell/tile dimensions and tunable gameplay constants.
## Populated at runtime by LocationManager (cell_size) and main.gd (map dimensions).
## Never hardcode these values elsewhere — always read from GameConfig.

## Cell size in pixels, read from LDtk project's defaultGridSize.
var cell_size: int = 16

## Current level dimensions in cells.
var map_width: int = 0
var map_height: int = 0

## Movement tuning.
var move_speed: float = 8.0
var move_cooldown: float = 0.15
```

- [ ] **Step 4: Register autoload in project.godot**

In `project/hosts/complete-app/project.godot`, add `GameConfig` to the `[autoload]` section, after `LocationManager`:

```ini
GameConfig="*res://scripts/game_config.gd"
```

- [ ] **Step 5: Run test to verify it passes**

Run: `task test:godot` (with test_game_config.gd)
Expected: PASS — all 3 tests green.

- [ ] **Step 6: Commit**

```bash
git add project/hosts/complete-app/scripts/game_config.gd \
       project/hosts/complete-app/tests/test_game_config.gd \
       project/hosts/complete-app/project.godot
git commit -m "feat: add GameConfig autoload as single source of truth for cell size"
```

---

## Task 2: Migrate All TILE_SIZE References to GameConfig

**Files:**
- Modify: `project/hosts/complete-app/ecs/components/c_grid_position.gd`
- Modify: `project/hosts/complete-app/ecs/systems/s_grid_movement.gd`
- Modify: `project/hosts/complete-app/ecs/systems/s_action_processor.gd`
- Modify: `project/hosts/complete-app/scripts/entity_visual.gd`
- Modify: `project/hosts/complete-app/scripts/tileset_factory.gd`
- Modify: `project/hosts/complete-app/scripts/pck_builder.gd`

- [ ] **Step 1: Update c_grid_position.gd**

Replace the hardcoded `* 32` in `_init`:

```gdscript
class_name C_GridPosition
extends Component

@export var col: int = 0
@export var row: int = 0
@export var facing: Vector2i = Vector2i.DOWN
## Smooth pixel position for rendering (lerped toward grid target).
@export var visual_x: float = 0.0
@export var visual_y: float = 0.0

func _init(p_col: int = 0, p_row: int = 0):
	col = p_col
	row = p_row
	visual_x = float(p_col * GameConfig.cell_size)
	visual_y = float(p_row * GameConfig.cell_size)
```

- [ ] **Step 2: Update s_grid_movement.gd**

Remove `TILE_SIZE` constant, use `GameConfig.cell_size`:

```gdscript
class_name S_GridMovement
extends System

func query() -> QueryBuilder:
	return q.with_all([C_GridPosition])

func process(entities: Array[Entity], _components: Array, delta: float) -> void:
	var cs := GameConfig.cell_size
	for entity in entities:
		var grid_pos = entity.get_component(C_GridPosition) as C_GridPosition
		var target_x = float(grid_pos.col * cs)
		var target_y = float(grid_pos.row * cs)
		grid_pos.visual_x = lerpf(grid_pos.visual_x, target_x, GameConfig.move_speed * delta)
		grid_pos.visual_y = lerpf(grid_pos.visual_y, target_y, GameConfig.move_speed * delta)
```

- [ ] **Step 3: Update s_action_processor.gd**

Remove `TILE_SIZE` constant (it was declared but not used for pixel math). Use `GameConfig.move_cooldown`:

In `s_action_processor.gd`, remove lines:
```
const TILE_SIZE := 32
var move_cooldown := 0.15
```
Replace with:
```gdscript
var _cooldown_timer := 0.0
```
And change the cooldown assignment in `_process_move` from `_cooldown_timer = move_cooldown` to:
```gdscript
_cooldown_timer = GameConfig.move_cooldown
```

- [ ] **Step 4: Update entity_visual.gd**

Remove `TILE_SIZE` constant, use `GameConfig.cell_size`:

```gdscript
class_name EntityVisual
extends Node2D

enum VisualType { PLAYER_FATHER, PLAYER_SON, BOULDER, BLOCKED, ENEMY }

var visual_type: VisualType = VisualType.PLAYER_FATHER
var entity: Entity = null
var enemy_color: Color = Color(0.2, 0.8, 0.3)

func _draw() -> void:
	var cs := GameConfig.cell_size
	match visual_type:
		VisualType.PLAYER_FATHER:
			draw_rect(Rect2(4, 4, cs - 8, cs - 8), Color(1.0, 0.8, 0.0))
			_draw_facing_arrow()
		VisualType.PLAYER_SON:
			draw_rect(Rect2(4, 4, cs - 8, cs - 8), Color(0.6, 0.8, 1.0))
			_draw_facing_arrow()
		VisualType.BOULDER:
			draw_circle(Vector2(cs / 2.0, cs / 2.0), cs / 3.0, Color(0.5, 0.5, 0.5))
		VisualType.BLOCKED:
			draw_circle(Vector2(cs / 2.0, cs / 2.0), cs / 3.0, Color(0.4, 0.2, 0.2))
		VisualType.ENEMY:
			var center = Vector2(cs / 2.0, cs / 2.0)
			var half = cs / 3.0
			var points = PackedVector2Array([
				center + Vector2(0, -half),
				center + Vector2(half, 0),
				center + Vector2(0, half),
				center + Vector2(-half, 0),
			])
			draw_colored_polygon(points, enemy_color)

func _draw_facing_arrow() -> void:
	if not entity:
		return
	var grid_pos = entity.get_component(C_GridPosition) as C_GridPosition
	if grid_pos:
		var cs := GameConfig.cell_size
		var center = Vector2(cs / 2.0, cs / 2.0)
		var arrow_end = center + Vector2(grid_pos.facing) * 10.0
		draw_line(center, arrow_end, Color.WHITE, 2.0)

func _process(_delta: float) -> void:
	queue_redraw()
```

- [ ] **Step 5: Update tileset_factory.gd**

Remove `TILE_SIZE` constant, use `GameConfig.cell_size`:

```gdscript
class_name TilesetFactory

static func create_tileset() -> TileSet:
	var cs := GameConfig.cell_size
	var tileset = TileSet.new()
	tileset.tile_size = Vector2i(cs, cs)

	tileset.add_custom_data_layer()
	tileset.set_custom_data_layer_name(0, "walkable")
	tileset.set_custom_data_layer_type(0, TYPE_BOOL)

	_add_colored_source(tileset, 0, [
		Color(0.23, 0.42, 0.12),
		Color(0.55, 0.45, 0.33),
		Color(0.42, 0.35, 0.23),
		Color(0.17, 0.35, 0.55),
	], [true, true, false, false])

	_add_colored_source(tileset, 1, [
		Color(0.29, 0.29, 0.16),
		Color(0.55, 0.45, 0.33),
		Color(0.29, 0.23, 0.17),
		Color(0.33, 0.33, 0.33),
	], [true, true, false, false])

	return tileset

static func _add_colored_source(
	tileset: TileSet,
	source_id: int,
	colors: Array,
	walkable_flags: Array
) -> void:
	var cs := GameConfig.cell_size
	var atlas_width = colors.size() * cs
	var image = Image.create(atlas_width, cs, false, Image.FORMAT_RGBA8)

	for i in colors.size():
		var color: Color = colors[i]
		for x in range(i * cs, (i + 1) * cs):
			for y in range(cs):
				if x == i * cs or x == (i + 1) * cs - 1 or y == 0 or y == cs - 1:
					image.set_pixel(x, y, color.darkened(0.3))
				else:
					image.set_pixel(x, y, color)

	var texture = ImageTexture.create_from_image(image)
	var atlas_source = TileSetAtlasSource.new()
	atlas_source.texture = texture
	atlas_source.texture_region_size = Vector2i(cs, cs)
	tileset.add_source(atlas_source, source_id)

	for i in colors.size():
		atlas_source.create_tile(Vector2i(i, 0))
		var tile_data = atlas_source.get_tile_data(Vector2i(i, 0), 0)
		tile_data.set_custom_data("walkable", walkable_flags[i])
```

- [ ] **Step 6: Update pck_builder.gd**

Remove `const TILE_SIZE := 32`. The pck_builder already reads `tile_size` from the manifest. Just change the fallback default on line 43:

```gdscript
var tile_size: int = manifest.get("tile_size", 16)
```

(Fallback to 16 matches LDtk default. This script runs headless so it cannot access the GameConfig autoload — it reads from manifest data instead, which is correct.)

- [ ] **Step 7: Run all Godot tests**

Run: `task test:godot`
Expected: All existing tests pass. The `test_game_config.gd` tests pass. No regressions in `test_ldtk_importer.gd` or `test_ldtk_level_placer.gd`.

- [ ] **Step 8: Commit**

```bash
git add project/hosts/complete-app/ecs/components/c_grid_position.gd \
       project/hosts/complete-app/ecs/systems/s_grid_movement.gd \
       project/hosts/complete-app/ecs/systems/s_action_processor.gd \
       project/hosts/complete-app/scripts/entity_visual.gd \
       project/hosts/complete-app/scripts/tileset_factory.gd \
       project/hosts/complete-app/scripts/pck_builder.gd
git commit -m "refactor: replace all hardcoded TILE_SIZE with GameConfig.cell_size"
```

---

## Task 3: Wire GameConfig Into LocationManager and Main

**Files:**
- Modify: `project/hosts/complete-app/scripts/location_manager.gd`
- Modify: `project/hosts/complete-app/scripts/main.gd`

- [ ] **Step 1: Set GameConfig.cell_size from LDtk in LocationManager**

In `location_manager.gd`, after `_ldtk_project` is loaded in `load_location()`, set the cell size. Add after line 70 (`_ldtk_project = LdtkImporter.load_project(LDTK_PROJECT_PATH)`):

```gdscript
	# Set cell size from LDtk project metadata
	if _ldtk_project.has("defaultGridSize"):
		GameConfig.cell_size = int(_ldtk_project["defaultGridSize"])
```

- [ ] **Step 2: Update main.gd — remove TILE_SIZE, use GameConfig everywhere**

Replace the entire `main.gd` with these changes (showing only the changed sections):

Remove line 4: `const TILE_SIZE := 32`

In `_load_ldtk_level`, fix map dimension calculation (line 419-420):
```gdscript
	map_width = level_node.get_meta("px_width", 320) / GameConfig.cell_size
	map_height = level_node.get_meta("px_height", 256) / GameConfig.cell_size
```

Also set GameConfig map dimensions in `_load_ldtk_level`, after computing map_width/height:
```gdscript
	GameConfig.map_width = map_width
	GameConfig.map_height = map_height
```

In `_generate_fallback_layout` (after setting map_width/map_height):
```gdscript
	GameConfig.map_width = map_width
	GameConfig.map_height = map_height
```

In `_update_cameras` (lines 324, 327), replace `TILE_SIZE` with `GameConfig.cell_size`:
```gdscript
	if active_gp:
		var cs := GameConfig.cell_size
		var target = Vector2(active_gp.visual_x + cs / 2.0, active_gp.visual_y + cs / 2.0)
		active_cam.position = active_cam.position.lerp(target, 0.1)
	if inactive_gp:
		var cs := GameConfig.cell_size
		var target = Vector2(inactive_gp.visual_x + cs / 2.0, inactive_gp.visual_y + cs / 2.0)
		inactive_cam.position = inactive_cam.position.lerp(target, 0.1)
```

In `_build_game_view` (lines 526-532), replace camera setup:
```gdscript
	var cs := GameConfig.cell_size
	camera.position = Vector2(map_width * cs / 2.0, map_height * cs / 2.0)
	var map_pixel_height := float(map_height * cs)
	var target_zoom := 1.0
	if map_pixel_height > 0:
		target_zoom = float(viewport.size.y) / map_pixel_height
	camera.zoom = Vector2(target_zoom, target_zoom)
```

In `_update_camera_zoom` (line 554), replace:
```gdscript
	var map_pixel_height := float(map_height * GameConfig.cell_size)
```

- [ ] **Step 3: Run the game manually to verify visual fix**

Run: `task dev` and open the game in browser.
Expected: Tiles should appear correctly sized. Player movement should visually move exactly one cell. Camera zoom should fit the map at proper scale.

- [ ] **Step 4: Run all tests**

Run: `task test:godot`
Expected: All tests pass.

- [ ] **Step 5: Commit**

```bash
git add project/hosts/complete-app/scripts/location_manager.gd \
       project/hosts/complete-app/scripts/main.gd
git commit -m "fix: wire GameConfig.cell_size from LDtk, fixing tile size mismatch"
```

---

## Task 4: Create TimeService Autoload

**Files:**
- Create: `project/hosts/complete-app/scripts/time_service.gd`
- Create: `project/hosts/complete-app/tests/test_time_service.gd`
- Modify: `project/hosts/complete-app/project.godot`

- [ ] **Step 1: Write GUT test for TimeService**

Create `project/hosts/complete-app/tests/test_time_service.gd`:

```gdscript
extends GutTest

func after_each():
	# Restore time scale after each test
	Engine.time_scale = 1.0

func test_initial_state():
	var state = TimeService.get_state()
	assert_eq(state["paused"], false)
	assert_almost_eq(state["speed"], 1.0, 0.01)

func test_set_speed():
	TimeService.set_speed(0.5)
	assert_almost_eq(Engine.time_scale, 0.5, 0.01)
	var state = TimeService.get_state()
	assert_almost_eq(state["speed"], 0.5, 0.01)

func test_set_speed_clamps_low():
	TimeService.set_speed(0.1)
	assert_almost_eq(Engine.time_scale, 0.25, 0.01, "should clamp to 0.25 minimum")

func test_set_speed_clamps_high():
	TimeService.set_speed(10.0)
	assert_almost_eq(Engine.time_scale, 4.0, 0.01, "should clamp to 4.0 maximum")

func test_pause_and_resume():
	TimeService.set_speed(2.0)
	TimeService.pause()
	assert_almost_eq(Engine.time_scale, 0.0, 0.01)
	assert_true(TimeService.get_state()["paused"])

	TimeService.resume()
	assert_almost_eq(Engine.time_scale, 2.0, 0.01, "should restore previous speed")
	assert_false(TimeService.get_state()["paused"])

func test_pause_when_already_paused():
	TimeService.pause()
	TimeService.pause()  # should be idempotent
	assert_true(TimeService.get_state()["paused"])
	TimeService.resume()
	assert_almost_eq(Engine.time_scale, 1.0, 0.01, "should restore to 1.0 (default)")

func test_resume_when_not_paused():
	TimeService.resume()  # should be no-op
	assert_false(TimeService.get_state()["paused"])
	assert_almost_eq(Engine.time_scale, 1.0, 0.01)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `task test:godot` (with test_time_service.gd)
Expected: FAIL — `TimeService` autoload not found.

- [ ] **Step 3: Create TimeService autoload**

Create `project/hosts/complete-app/scripts/time_service.gd`:

```gdscript
class_name TimeServiceClass
extends Node

## Wraps Engine.time_scale with pause/resume/frame-step for diagnostics.
## Must use PROCESS_MODE_ALWAYS so it ticks even when time_scale = 0.

var _current_speed: float = 1.0
var _saved_speed: float = 1.0
var _paused: bool = false
var _step_requested: bool = false
var _step_active: bool = false

const MIN_SPEED := 0.25
const MAX_SPEED := 4.0

func _ready() -> void:
	process_mode = Node.PROCESS_MODE_ALWAYS

func _process(_delta: float) -> void:
	if _step_requested:
		Engine.time_scale = _saved_speed
		_step_requested = false
		_step_active = true
	elif _step_active:
		Engine.time_scale = 0.0
		_step_active = false

func set_speed(multiplier: float) -> void:
	var clamped := clampf(multiplier, MIN_SPEED, MAX_SPEED)
	_current_speed = clamped
	if not _paused:
		Engine.time_scale = clamped

func pause() -> void:
	if _paused:
		return
	_saved_speed = _current_speed
	_paused = true
	Engine.time_scale = 0.0

func resume() -> void:
	if not _paused:
		return
	_paused = false
	_step_requested = false
	_step_active = false
	Engine.time_scale = _saved_speed

func step_frame() -> void:
	if not _paused:
		return
	_step_requested = true

func get_state() -> Dictionary:
	return {
		"paused": _paused,
		"speed": _current_speed,
	}
```

- [ ] **Step 4: Register autoload in project.godot**

Add to `[autoload]` section after `GameConfig`:

```ini
TimeService="*res://scripts/time_service.gd"
```

- [ ] **Step 5: Run test to verify it passes**

Run: `task test:godot` (with test_time_service.gd)
Expected: PASS — all 7 tests green.

- [ ] **Step 6: Commit**

```bash
git add project/hosts/complete-app/scripts/time_service.gd \
       project/hosts/complete-app/tests/test_time_service.gd \
       project/hosts/complete-app/project.godot
git commit -m "feat: add TimeService autoload with pause/resume/speed/frame-step"
```

---

## Task 5: Add Time Control Commands to WS Client

**Files:**
- Modify: `project/hosts/complete-app/scripts/ws_client.gd`

- [ ] **Step 1: Set process_mode ALWAYS on ws_client.gd**

In `ws_client.gd`, add to `_ready()` after `_connect_to_server()`:

```gdscript
func _ready() -> void:
	process_mode = Node.PROCESS_MODE_ALWAYS
	_connect_to_server()
```

- [ ] **Step 2: Add time command handlers**

In `ws_client.gd`, add new cases to `_handle_command()` match block, after the `"get_state"` case:

```gdscript
		"time_set_speed":
			var speed: float = payload.get("speed", 1.0)
			TimeService.set_speed(speed)
			_send_command_ack(cmd_id, true)

		"time_pause":
			TimeService.pause()
			_send_command_ack(cmd_id, true)

		"time_resume":
			TimeService.resume()
			_send_command_ack(cmd_id, true)

		"time_step":
			TimeService.step_frame()
			_send_command_ack(cmd_id, true)
```

- [ ] **Step 3: Run server tests to verify nothing broke**

Run: `task test:server`
Expected: All existing tests pass (mock-godot doesn't need to handle these new commands yet).

- [ ] **Step 4: Commit**

```bash
git add project/hosts/complete-app/scripts/ws_client.gd
git commit -m "feat: add time control WS commands and PROCESS_MODE_ALWAYS for ws_client"
```

---

## Task 6: Add Time Control Keyboard Shortcuts

**Files:**
- Modify: `project/hosts/complete-app/scripts/main.gd`

- [ ] **Step 1: Add keyboard shortcuts in main.gd _input()**

In `main.gd`, add to the `_input` function, after the existing `KEY_M` handler:

```gdscript
	# P toggles pause
	if event is InputEventKey and event.pressed and event.keycode == KEY_P:
		get_viewport().set_input_as_handled()
		if TimeService.get_state()["paused"]:
			TimeService.resume()
		else:
			TimeService.pause()
	# N steps one frame (while paused)
	if event is InputEventKey and event.pressed and event.keycode == KEY_N:
		get_viewport().set_input_as_handled()
		TimeService.step_frame()
	# [ decreases speed
	if event is InputEventKey and event.pressed and event.keycode == KEY_BRACKETLEFT:
		get_viewport().set_input_as_handled()
		var state = TimeService.get_state()
		TimeService.set_speed(state["speed"] - 0.25)
	# ] increases speed
	if event is InputEventKey and event.pressed and event.keycode == KEY_BRACKETRIGHT:
		get_viewport().set_input_as_handled()
		var state = TimeService.get_state()
		TimeService.set_speed(state["speed"] + 0.25)
```

- [ ] **Step 2: Add time state to debug HUD**

In `main.gd`, at the end of `_update_debug_hud()`, append the time state to the debug label text. Add before the final assignment to `_debug_label.text`:

```gdscript
	var time_state = TimeService.get_state()
	var time_text := ""
	if time_state["paused"]:
		time_text = "Time: PAUSED"
	else:
		time_text = "Time: %.2fx" % time_state["speed"]
```

Then append `time_text` to the label string:

```gdscript
	_debug_label.text = (
		"Era: %s | Pos: (%d,%d) | Facing: %s\n" % [era_name, gp.col if gp else 0, gp.row if gp else 0, facing_name]
		+ "Looking at: (%d,%d) = %s\n" % [target_col, target_row, facing_content]
		+ "Boulder: %s | Blocked: %s\n" % [
			"DEFAULT" if boulder_state.state == C_Interactable.InteractState.DEFAULT else "ACTIVATED",
			"DEFAULT" if blocked_state.state == C_Interactable.InteractState.DEFAULT else "ACTIVATED"]
		+ "Entities in world: %d | %s\n" % [entity_count, time_text]
		+ "Controls: Arrows=move | Tab=era | M=map | E=interact | P=pause | N=step | []=speed"
	)
```

- [ ] **Step 3: Manual test — verify shortcuts work in browser**

Run: `task dev`, open game. Press P to pause, N to step, [ and ] to change speed. Debug HUD should show current time state.

- [ ] **Step 4: Commit**

```bash
git add project/hosts/complete-app/scripts/main.gd
git commit -m "feat: add time control keyboard shortcuts (P/N/[/]) and HUD display"
```

---

## Task 7: Create Time Control MCP Tools

**Files:**
- Create: `project/server/packages/game-server/src/mastra/tools/time-control.js`
- Create: `project/server/packages/game-server/src/__tests__/time-control.test.js`
- Modify: `project/server/packages/game-server/src/mastra/index.js`

- [ ] **Step 1: Write Vitest test for time control tools**

Create `project/server/packages/game-server/src/__tests__/time-control.test.js`:

```javascript
import { describe, it, expect, vi, beforeEach } from "vitest";
import {
  createSetTimeSpeedTool,
  createPauseTimeTool,
  createResumeTimeTool,
  createStepFrameTool,
} from "../mastra/tools/time-control.js";

function makeMockConnMgr() {
  return {
    sendCommandToGodot: vi.fn().mockResolvedValue({ success: true, error: null }),
  };
}

describe("time-control tools", () => {
  let connMgr;

  beforeEach(() => {
    connMgr = makeMockConnMgr();
  });

  it("set_time_speed sends time_set_speed command", async () => {
    const tool = createSetTimeSpeedTool(connMgr);
    const result = await tool.execute({ speed: 0.5 });
    expect(connMgr.sendCommandToGodot).toHaveBeenCalledWith("time_set_speed", { speed: 0.5 });
    expect(result.success).toBe(true);
  });

  it("pause_time sends time_pause command", async () => {
    const tool = createPauseTimeTool(connMgr);
    const result = await tool.execute({});
    expect(connMgr.sendCommandToGodot).toHaveBeenCalledWith("time_pause", {});
    expect(result.success).toBe(true);
  });

  it("resume_time sends time_resume command", async () => {
    const tool = createResumeTimeTool(connMgr);
    const result = await tool.execute({});
    expect(connMgr.sendCommandToGodot).toHaveBeenCalledWith("time_resume", {});
    expect(result.success).toBe(true);
  });

  it("step_frame sends time_step command", async () => {
    const tool = createStepFrameTool(connMgr);
    const result = await tool.execute({});
    expect(connMgr.sendCommandToGodot).toHaveBeenCalledWith("time_step", {});
    expect(result.success).toBe(true);
  });
});
```

- [ ] **Step 2: Run test to verify it fails**

Run: `task test:server`
Expected: FAIL — module not found.

- [ ] **Step 3: Create time-control.js MCP tools**

Create `project/server/packages/game-server/src/mastra/tools/time-control.js`:

```javascript
import { createTool } from "@mastra/core/tools";
import { z } from "zod";

const ackSchema = z.object({
  success: z.boolean(),
  error: z.string().nullable(),
});

export function createSetTimeSpeedTool(connMgr) {
  return createTool({
    id: "set_time_speed",
    description:
      "Set game time speed multiplier. 1.0 = normal, 0.25 = quarter speed, 2.0 = double speed. Clamped to 0.25–4.0.",
    inputSchema: z.object({
      speed: z.number().min(0.25).max(4.0).describe("Time speed multiplier"),
    }),
    outputSchema: ackSchema,
    execute: async (input) => {
      const ack = await connMgr.sendCommandToGodot("time_set_speed", { speed: input.speed });
      return { success: ack.success, error: ack.error ?? null };
    },
  });
}

export function createPauseTimeTool(connMgr) {
  return createTool({
    id: "pause_time",
    description: "Pause the game. All game logic stops but WS connection stays active.",
    inputSchema: z.object({}),
    outputSchema: ackSchema,
    execute: async () => {
      const ack = await connMgr.sendCommandToGodot("time_pause", {});
      return { success: ack.success, error: ack.error ?? null };
    },
  });
}

export function createResumeTimeTool(connMgr) {
  return createTool({
    id: "resume_time",
    description: "Resume the game from paused state. Restores previous time speed.",
    inputSchema: z.object({}),
    outputSchema: ackSchema,
    execute: async () => {
      const ack = await connMgr.sendCommandToGodot("time_resume", {});
      return { success: ack.success, error: ack.error ?? null };
    },
  });
}

export function createStepFrameTool(connMgr) {
  return createTool({
    id: "step_frame",
    description:
      "Advance exactly one game frame while paused. Only works when game is paused. Useful for precise before/after screenshot comparison.",
    inputSchema: z.object({}),
    outputSchema: ackSchema,
    execute: async () => {
      const ack = await connMgr.sendCommandToGodot("time_step", {});
      return { success: ack.success, error: ack.error ?? null };
    },
  });
}
```

- [ ] **Step 4: Register tools in mastra/index.js**

In `project/server/packages/game-server/src/mastra/index.js`, add import:

```javascript
import {
  createSetTimeSpeedTool,
  createPauseTimeTool,
  createResumeTimeTool,
  createStepFrameTool,
} from "./tools/time-control.js";
```

Inside `createMastraServer`, after `const getStateTool = ...`:

```javascript
  const setTimeSpeedTool = createSetTimeSpeedTool(connMgr);
  const pauseTimeTool = createPauseTimeTool(connMgr);
  const resumeTimeTool = createResumeTimeTool(connMgr);
  const stepFrameTool = createStepFrameTool(connMgr);
```

Add to `tools` object:

```javascript
    set_time_speed: setTimeSpeedTool,
    pause_time: pauseTimeTool,
    resume_time: resumeTimeTool,
    step_frame: stepFrameTool,
```

- [ ] **Step 5: Run test to verify it passes**

Run: `task test:server`
Expected: PASS — all new and existing tests green.

- [ ] **Step 6: Commit**

```bash
git add project/server/packages/game-server/src/mastra/tools/time-control.js \
       project/server/packages/game-server/src/__tests__/time-control.test.js \
       project/server/packages/game-server/src/mastra/index.js
git commit -m "feat: add time control MCP tools (set_time_speed, pause, resume, step_frame)"
```

---

## Task 8: Add Screenshot Command to WS Client (Godot Side)

**Files:**
- Modify: `project/hosts/complete-app/scripts/ws_client.gd`

- [ ] **Step 1: Add screenshot command handler**

In `ws_client.gd`, add a new case to `_handle_command()`:

```gdscript
		"screenshot":
			_handle_screenshot(cmd_id, payload)
```

Then add the handler method:

```gdscript
func _handle_screenshot(cmd_id: String, payload: Dictionary) -> void:
	var viewport_target: String = payload.get("viewport", "active")
	var format: String = payload.get("format", "jpeg")
	var quality: int = payload.get("quality", 80)
	var max_width: int = payload.get("max_width", 0)

	var main_node = get_tree().root.get_node_or_null("Main")
	if not main_node:
		_send_command_ack(cmd_id, false, "Main node not found")
		return

	var ack := { "type": "command_ack", "id": cmd_id, "success": true, "error": null }

	if viewport_target == "both":
		ack["father_screenshot"] = _capture_viewport(main_node.father_view, format, quality, max_width)
		ack["son_screenshot"] = _capture_viewport(main_node.son_view, format, quality, max_width)
	else:
		var view: SubViewportContainer
		if viewport_target == "father":
			view = main_node.father_view
		elif viewport_target == "son":
			view = main_node.son_view
		else:
			# "active" — use current era
			if main_node.active_era == C_TimelineEra.Era.FATHER:
				view = main_node.father_view
			else:
				view = main_node.son_view
		ack["screenshot"] = _capture_viewport(view, format, quality, max_width)

	_send_json(ack)

func _capture_viewport(view: SubViewportContainer, format: String, quality: int, max_width: int) -> String:
	var viewport = view.get_node("SubViewport") as SubViewport
	var image := viewport.get_texture().get_image()

	if max_width > 0 and image.get_width() > max_width:
		var ratio := float(max_width) / float(image.get_width())
		var new_height := int(float(image.get_height()) * ratio)
		image.resize(max_width, new_height)

	var buffer: PackedByteArray
	var mime: String
	if format == "png":
		buffer = image.save_png_to_buffer()
		mime = "image/png"
	else:
		buffer = image.save_jpg_to_buffer(clamp(quality, 1, 100) / 100.0)
		mime = "image/jpeg"

	return "data:%s;base64,%s" % [mime, Marshalls.raw_to_base64(buffer)]
```

- [ ] **Step 2: Manual test — verify screenshot via WS**

Run: `task dev`. Connect to WS and send:
```json
{"type": "command", "id": "test_ss", "action": "screenshot", "payload": {"viewport": "active", "format": "jpeg", "quality": 80}}
```
Expected: Receive `command_ack` with base64-encoded image data.

- [ ] **Step 3: Commit**

```bash
git add project/hosts/complete-app/scripts/ws_client.gd
git commit -m "feat: add screenshot WS command for SubViewport capture"
```

---

## Task 9: Create Screenshot MCP Tools

**Files:**
- Create: `project/server/packages/game-server/src/mastra/tools/screenshot.js`
- Create: `project/server/packages/game-server/src/__tests__/screenshot.test.js`
- Modify: `project/server/packages/game-server/src/mastra/index.js`

- [ ] **Step 1: Write Vitest test for screenshot tool**

Create `project/server/packages/game-server/src/__tests__/screenshot.test.js`:

```javascript
import { describe, it, expect, vi, beforeEach } from "vitest";
import { createScreenshotTool } from "../mastra/tools/screenshot.js";

function makeMockConnMgr() {
  return {
    sendCommandToGodot: vi.fn().mockResolvedValue({
      success: true,
      error: null,
      screenshot: "data:image/jpeg;base64,/9j/fake",
    }),
  };
}

describe("screenshot tool", () => {
  let connMgr;

  beforeEach(() => {
    connMgr = makeMockConnMgr();
  });

  it("sends screenshot command with defaults", async () => {
    const tool = createScreenshotTool(connMgr);
    const result = await tool.execute({});
    expect(connMgr.sendCommandToGodot).toHaveBeenCalledWith("screenshot", {
      viewport: "active",
      format: "jpeg",
      quality: 80,
      max_width: 0,
    });
    expect(result.success).toBe(true);
    expect(result.screenshot).toContain("data:image/jpeg;base64,");
  });

  it("passes viewport and format options through", async () => {
    const tool = createScreenshotTool(connMgr);
    await tool.execute({ viewport: "both", format: "png", max_width: 256 });
    expect(connMgr.sendCommandToGodot).toHaveBeenCalledWith("screenshot", {
      viewport: "both",
      format: "png",
      quality: 80,
      max_width: 256,
    });
  });
});
```

- [ ] **Step 2: Run test to verify it fails**

Run: `task test:server`
Expected: FAIL — module not found.

- [ ] **Step 3: Create screenshot.js MCP tool**

Create `project/server/packages/game-server/src/mastra/tools/screenshot.js`:

```javascript
import { createTool } from "@mastra/core/tools";
import { z } from "zod";

export function createScreenshotTool(connMgr) {
  return createTool({
    id: "screenshot",
    description:
      "Capture a screenshot of the game SubViewport. Use with pause_time/step_frame for precise before/after comparison. Returns base64-encoded image data.",
    inputSchema: z.object({
      viewport: z
        .enum(["active", "father", "son", "both"])
        .default("active")
        .describe("Which viewport to capture"),
      format: z.enum(["png", "jpeg"]).default("jpeg").describe("Image format"),
      quality: z.number().min(1).max(100).default(80).describe("JPEG quality (1-100)"),
      max_width: z
        .number()
        .min(0)
        .default(0)
        .describe("Max width in pixels (0 = no resize)"),
    }),
    outputSchema: z.object({
      success: z.boolean(),
      error: z.string().nullable(),
      screenshot: z.string().optional(),
      father_screenshot: z.string().optional(),
      son_screenshot: z.string().optional(),
    }),
    execute: async (input) => {
      const ack = await connMgr.sendCommandToGodot("screenshot", {
        viewport: input.viewport ?? "active",
        format: input.format ?? "jpeg",
        quality: input.quality ?? 80,
        max_width: input.max_width ?? 0,
      });
      return {
        success: ack.success,
        error: ack.error ?? null,
        screenshot: ack.screenshot ?? undefined,
        father_screenshot: ack.father_screenshot ?? undefined,
        son_screenshot: ack.son_screenshot ?? undefined,
      };
    },
  });
}
```

- [ ] **Step 4: Register screenshot tool in mastra/index.js**

In `project/server/packages/game-server/src/mastra/index.js`, add import:

```javascript
import { createScreenshotTool } from "./tools/screenshot.js";
```

Inside `createMastraServer`, after the time control tools:

```javascript
  const screenshotTool = createScreenshotTool(connMgr);
```

Add to `tools` object:

```javascript
    screenshot: screenshotTool,
```

- [ ] **Step 5: Run test to verify it passes**

Run: `task test:server`
Expected: PASS — all tests green.

- [ ] **Step 6: Commit**

```bash
git add project/server/packages/game-server/src/mastra/tools/screenshot.js \
       project/server/packages/game-server/src/__tests__/screenshot.test.js \
       project/server/packages/game-server/src/mastra/index.js
git commit -m "feat: add screenshot MCP tool for SubViewport capture"
```

---

## Task 10: Create Browser Screenshot MCP Tool

**Files:**
- Create: `project/server/packages/game-server/src/mastra/tools/browser-screenshot.js`
- Modify: `project/server/packages/game-server/src/mastra/index.js`

- [ ] **Step 1: Create browser-screenshot.js**

Create `project/server/packages/game-server/src/mastra/tools/browser-screenshot.js`:

```javascript
import { createTool } from "@mastra/core/tools";
import { z } from "zod";
import { chromium } from "playwright";
import { join } from "node:path";
import { mkdirSync } from "node:fs";

export function createBrowserScreenshotTool() {
  return createTool({
    id: "browser_screenshot",
    description:
      "Capture a full-page screenshot of the game running in the browser via Playwright. Saves PNG to build/_artifacts/latest/screenshots/. Reuses existing Chromium if available.",
    inputSchema: z.object({
      filename: z
        .string()
        .default("")
        .describe("Screenshot filename (without extension). Defaults to timestamp."),
      game_url: z
        .string()
        .default("http://localhost:8080")
        .describe("URL of the running game"),
    }),
    outputSchema: z.object({
      success: z.boolean(),
      path: z.string().optional(),
      error: z.string().nullable(),
    }),
    execute: async (input) => {
      let browser;
      try {
        const filename = input.filename || `screenshot-${Date.now()}`;
        const screenshotDir = join(
          process.cwd(),
          "..",
          "..",
          "..",
          "build",
          "_artifacts",
          "latest",
          "screenshots",
        );
        mkdirSync(screenshotDir, { recursive: true });
        const screenshotPath = join(screenshotDir, `${filename}.png`);

        browser = await chromium.launch({ headless: true });
        const page = await browser.newPage();
        await page.goto(input.game_url || "http://localhost:8080", {
          waitUntil: "networkidle",
          timeout: 10000,
        });
        // Wait for game to render
        await page.waitForTimeout(2000);
        await page.screenshot({ path: screenshotPath, fullPage: true });

        return { success: true, path: screenshotPath, error: null };
      } catch (err) {
        return { success: false, error: err.message };
      } finally {
        if (browser) await browser.close();
      }
    },
  });
}
```

- [ ] **Step 2: Register in mastra/index.js**

Add import:

```javascript
import { createBrowserScreenshotTool } from "./tools/browser-screenshot.js";
```

Inside `createMastraServer`, add:

```javascript
  const browserScreenshotTool = createBrowserScreenshotTool();
```

Add to `tools` object:

```javascript
    browser_screenshot: browserScreenshotTool,
```

- [ ] **Step 3: Run all tests**

Run: `task test:server`
Expected: All tests pass (browser-screenshot doesn't need a unit test since it's an integration with Playwright — tested via E2E).

- [ ] **Step 4: Commit**

```bash
git add project/server/packages/game-server/src/mastra/tools/browser-screenshot.js \
       project/server/packages/game-server/src/mastra/index.js
git commit -m "feat: add browser_screenshot MCP tool via Playwright"
```

---

## Task 11: Update WS Message Schema and Run Full Test Suite

**Files:**
- Modify: `project/server/packages/game-server/schemas/ws-messages.schema.json`

- [ ] **Step 1: Add new command types to WS message schema**

In `project/server/packages/game-server/schemas/ws-messages.schema.json`, find the `command` message's `action` enum and add the new values:

```json
"action": {
  "type": "string",
  "enum": ["move", "interact", "switch_era", "get_state", "time_set_speed", "time_pause", "time_resume", "time_step", "screenshot"]
}
```

Also add optional screenshot fields to the `command_ack` properties:

```json
"screenshot": { "type": "string", "description": "Base64-encoded screenshot (single viewport)" },
"father_screenshot": { "type": "string", "description": "Base64-encoded father viewport screenshot" },
"son_screenshot": { "type": "string", "description": "Base64-encoded son viewport screenshot" }
```

- [ ] **Step 2: Run the full test suite**

Run: `task test`
Expected: All test suites pass — Python, Vitest, GUT, and (if web build is available) Playwright E2E.

- [ ] **Step 3: Commit**

```bash
git add project/server/packages/game-server/schemas/ws-messages.schema.json
git commit -m "docs: update WS message schema with time control and screenshot commands"
```

---

## Task 12: Final Verification and Dev Log

**Files:**
- Create: `vault/dev-log/2026-04-14-agent-diagnostics.md`

- [ ] **Step 1: Manual end-to-end verification**

1. Run `task dev` and open the game in browser
2. Verify tiles are correctly sized (not too small)
3. Verify player moves exactly one cell per arrow press
4. Press P to pause, N to step — verify HUD shows state
5. Press [ and ] to change speed — verify HUD shows speed
6. Connect an MCP client and test: `pause_time`, `screenshot`, `step_frame`, `screenshot`, `resume_time`

- [ ] **Step 2: Write dev log entry**

Create `vault/dev-log/2026-04-14-agent-diagnostics.md` with session summary, commits, decisions, and next steps per the AGENTS.md dev-log convention.

- [ ] **Step 3: Commit dev log**

```bash
git add vault/dev-log/2026-04-14-agent-diagnostics.md
git commit -m "docs: add dev-log for agent diagnostics session"
```
