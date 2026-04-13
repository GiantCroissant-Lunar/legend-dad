# LDtk Tile Placement Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace hardcoded tile arrays in main.gd with runtime LDtk level parsing, supporting base terrain + per-era overlay layers and decoupled collision metadata.

**Architecture:** `ldtk_importer.gd` gains `autoLayerTiles` parsing. A new `LdtkLevelPlacer` class takes parsed LDtk data and places tiles on a TileMapLayer, merging base + era overlay. `main.gd` delegates tile placement to `LdtkLevelPlacer` instead of using hardcoded arrays. `s_action_processor.gd` reads walkability from a collision grid dictionary instead of TileSet custom data.

**Tech Stack:** GDScript (Godot 4.6), LDtk 1.5.3 JSON format, GUT testing framework

**Spec:** `docs/superpowers/specs/2026-04-14-ldtk-tile-placement-design.md`

---

## File Structure

| File | Responsibility |
|------|---------------|
| `scripts/ldtk_importer.gd` (modify) | Parse `autoLayerTiles` arrays from LDtk layer instances |
| `scripts/ldtk_level_placer.gd` (create) | Place tiles on TileMapLayer from parsed LDtk data with era overlay merging |
| `scripts/main.gd` (modify) | Use `LdtkLevelPlacer` instead of hardcoded `FATHER_MAP`/`SON_MAP` |
| `scripts/location_manager.gd` (modify) | Expose LDtk project path; store collision data |
| `ecs/systems/s_action_processor.gd` (modify) | Read walkability from collision grid, not TileSet custom data |
| `tests/test_ldtk_importer.gd` (create) | Tests for autoLayerTiles parsing |
| `tests/test_ldtk_level_placer.gd` (create) | Tests for tile placement and era overlay logic |

---

### Task 1: Add autoLayerTiles parsing to LdtkImporter

**Files:**
- Modify: `project/hosts/complete-app/scripts/ldtk_importer.gd:66-81` (match block) and `:117-148` (intgrid import)
- Test: `project/hosts/complete-app/tests/test_ldtk_importer.gd`

- [ ] **Step 1: Write failing test for autoLayerTiles extraction**

Create `project/hosts/complete-app/tests/test_ldtk_importer.gd`:

```gdscript
extends GutTest

func _make_layer_instance(identifier: String, type: String, grid_size: int, auto_tiles: Array, intgrid_csv: Array = [], c_wid: int = 4, c_hei: int = 4) -> Dictionary:
	return {
		"__identifier": identifier,
		"__type": type,
		"__gridSize": grid_size,
		"__cWid": c_wid,
		"__cHei": c_hei,
		"layerDefUid": 50,
		"intGridCsv": intgrid_csv,
		"autoLayerTiles": auto_tiles,
		"entityInstances": [],
		"gridTiles": [],
	}

func _make_auto_tile(px_x: int, px_y: int, src_x: int, src_y: int, flip: int = 0) -> Dictionary:
	return { "px": [px_x, px_y], "src": [src_x, src_y], "t": 0, "f": flip }

func _make_project(layers: Array, intgrid_values: Array = []) -> Dictionary:
	return {
		"defs": {
			"layers": [{
				"uid": 50,
				"identifier": "Terrain",
				"intGridValues": intgrid_values,
			}]
		},
		"levels": [{
			"identifier": "TestLevel",
			"uid": 1,
			"iid": "test-iid",
			"worldX": 0, "worldY": 0,
			"pxWid": 64, "pxHei": 64,
			"layerInstances": layers,
		}]
	}

func test_parses_auto_layer_tiles_into_metadata():
	var auto_tiles = [
		_make_auto_tile(0, 0, 32, 0),    # cell (0,0) -> atlas (2,0) at grid_size=16
		_make_auto_tile(16, 32, 48, 16),  # cell (1,2) -> atlas (3,1)
	]
	var layer = _make_layer_instance("Terrain", "IntGrid", 16, auto_tiles)
	var project = _make_project([layer])

	var level_node = LdtkImporter.import_level(project, "TestLevel")
	assert_not_null(level_node, "Level should be imported")

	var terrain = level_node.get_node("Terrain")
	assert_not_null(terrain, "Terrain layer node should exist")

	var tiles: Array = terrain.get_meta("auto_layer_tiles")
	assert_eq(tiles.size(), 2, "Should have 2 auto-layer tiles")

	# First tile: px(0,0)/16 = grid(0,0), src(32,0)/16 = atlas(2,0)
	assert_eq(tiles[0]["position"], Vector2i(0, 0))
	assert_eq(tiles[0]["atlas_coords"], Vector2i(2, 0))
	assert_eq(tiles[0]["flip"], 0)

	# Second tile: px(16,32)/16 = grid(1,2), src(48,16)/16 = atlas(3,1)
	assert_eq(tiles[1]["position"], Vector2i(1, 2))
	assert_eq(tiles[1]["atlas_coords"], Vector2i(3, 1))

func test_empty_auto_layer_tiles_still_creates_node():
	var layer = _make_layer_instance("Terrain", "IntGrid", 16, [], [0,0,0,0,1,1,0,0,0,0,0,0,0,0,0,0])
	var project = _make_project([layer])

	var level_node = LdtkImporter.import_level(project, "TestLevel")
	var terrain = level_node.get_node("Terrain")
	assert_not_null(terrain)

	var tiles: Array = terrain.get_meta("auto_layer_tiles")
	assert_eq(tiles.size(), 0, "Should have empty auto_layer_tiles array")
	# IntGrid CSV should still be present
	var csv: Array = terrain.get_meta("intgrid_csv")
	assert_eq(csv.size(), 16)

func test_handles_null_layer_instances():
	var project = {
		"defs": { "layers": [] },
		"levels": [{
			"identifier": "EmptyLevel",
			"uid": 1, "iid": "empty-iid",
			"worldX": 0, "worldY": 0,
			"pxWid": 64, "pxHei": 64,
			"layerInstances": null,
		}]
	}
	var level_node = LdtkImporter.import_level(project, "EmptyLevel")
	assert_not_null(level_node, "Should return empty level node even with null layers")
	assert_eq(level_node.get_child_count(), 0)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd project/hosts/complete-app && godot --headless -s addons/gut/gut_cmdln.gd -gdir=res://tests -gtest=test_ldtk_importer.gd --quit-on-finish`
Expected: FAIL — `auto_layer_tiles` meta not set, null layers crash

- [ ] **Step 3: Implement autoLayerTiles parsing in LdtkImporter**

In `project/hosts/complete-app/scripts/ldtk_importer.gd`, modify `import_level` to handle null `layerInstances`:

Replace lines 61-62:
```gdscript
	var layer_instances: Array = level_data.get("layerInstances", [])
	for i in range(layer_instances.size() - 1, -1, -1):
```
With:
```gdscript
	var raw_layers = level_data.get("layerInstances", null)
	if raw_layers == null:
		return level_node
	var layer_instances: Array = raw_layers
	for i in range(layer_instances.size() - 1, -1, -1):
```

Then modify `_import_intgrid_layer` to parse autoLayerTiles. Replace lines 117-148 entirely:

```gdscript
static func _import_intgrid_layer(layer: Dictionary, layer_defs: Dictionary) -> Node2D:
	var identifier: String = layer.get("__identifier", "IntGrid")
	var grid_size: int = layer.get("__gridSize", 16)
	var c_wid: int = layer.get("__cWid", 0)
	var c_hei: int = layer.get("__cHei", 0)
	var csv: Array = layer.get("intGridCsv", [])
	var raw_auto_tiles: Array = layer.get("autoLayerTiles", [])

	# Need at least CSV or auto-tiles to create a node
	if csv.is_empty() and raw_auto_tiles.is_empty():
		return null

	# Get intgrid value definitions from layer def
	var layer_def_uid: int = layer.get("layerDefUid", -1)
	var layer_def: Dictionary = layer_defs.get(layer_def_uid, {})
	var intgrid_values: Array = layer_def.get("intGridValues", [])

	var node := Node2D.new()
	node.name = identifier
	node.set_meta("layer_type", "IntGrid")
	node.set_meta("grid_size", grid_size)
	node.set_meta("grid_width", c_wid)
	node.set_meta("grid_height", c_hei)

	# Store raw IntGrid CSV
	node.set_meta("intgrid_csv", csv)

	# Store value lookup
	var value_map := {}
	for val in intgrid_values:
		value_map[val.get("value", 0)] = val.get("identifier", "")
	node.set_meta("intgrid_value_map", value_map)

	# Parse autoLayerTiles: convert px coords to grid coords, src to atlas coords
	var auto_tiles: Array = []
	for tile in raw_auto_tiles:
		var px: Array = tile.get("px", [0, 0])
		var src: Array = tile.get("src", [0, 0])
		auto_tiles.append({
			"position": Vector2i(int(px[0]) / grid_size, int(px[1]) / grid_size),
			"atlas_coords": Vector2i(int(src[0]) / grid_size, int(src[1]) / grid_size),
			"flip": tile.get("f", 0),
		})
	node.set_meta("auto_layer_tiles", auto_tiles)

	return node
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd project/hosts/complete-app && godot --headless -s addons/gut/gut_cmdln.gd -gdir=res://tests -gtest=test_ldtk_importer.gd --quit-on-finish`
Expected: All 3 tests PASS

- [ ] **Step 5: Commit**

```bash
git add project/hosts/complete-app/scripts/ldtk_importer.gd project/hosts/complete-app/tests/test_ldtk_importer.gd
git commit -m "feat: add autoLayerTiles parsing to LdtkImporter"
```

---

### Task 2: Create LdtkLevelPlacer

**Files:**
- Create: `project/hosts/complete-app/scripts/ldtk_level_placer.gd`
- Test: `project/hosts/complete-app/tests/test_ldtk_level_placer.gd`

- [ ] **Step 1: Write failing test for base tile placement**

Create `project/hosts/complete-app/tests/test_ldtk_level_placer.gd`:

```gdscript
extends GutTest

# Minimal TileSet with a 4x2 atlas (8 tiles) for testing
var _tileset: TileSet

func before_each():
	_tileset = TileSet.new()
	_tileset.tile_size = Vector2i(32, 32)

	var image = Image.create(128, 64, false, Image.FORMAT_RGBA8)
	image.fill(Color.WHITE)
	var texture = ImageTexture.create_from_image(image)

	var source = TileSetAtlasSource.new()
	source.texture = texture
	source.texture_region_size = Vector2i(32, 32)
	_tileset.add_source(source, 0)

	# Create 8 tiles: (0,0) through (3,1)
	for col in range(4):
		for row in range(2):
			source.create_tile(Vector2i(col, row))

func _make_tile(pos: Vector2i, atlas: Vector2i, flip: int = 0) -> Dictionary:
	return { "position": pos, "atlas_coords": atlas, "flip": flip }

func test_places_base_terrain_tiles():
	var base_tiles = [
		_make_tile(Vector2i(0, 0), Vector2i(0, 0)),
		_make_tile(Vector2i(1, 0), Vector2i(1, 0)),
		_make_tile(Vector2i(0, 1), Vector2i(2, 0)),
	]
	var tilemap = TileMapLayer.new()
	tilemap.tile_set = _tileset
	add_child_autofree(tilemap)

	LdtkLevelPlacer.place_tiles(tilemap, base_tiles, 0)

	assert_eq(tilemap.get_cell_source_id(Vector2i(0, 0)), 0)
	assert_eq(tilemap.get_cell_atlas_coords(Vector2i(0, 0)), Vector2i(0, 0))
	assert_eq(tilemap.get_cell_atlas_coords(Vector2i(1, 0)), Vector2i(1, 0))
	assert_eq(tilemap.get_cell_atlas_coords(Vector2i(0, 1)), Vector2i(2, 0))
	# Unplaced cell should be empty
	assert_eq(tilemap.get_cell_source_id(Vector2i(3, 3)), -1)

func test_overlay_overwrites_base_tiles():
	var base_tiles = [
		_make_tile(Vector2i(0, 0), Vector2i(0, 0)),
		_make_tile(Vector2i(1, 0), Vector2i(1, 0)),
		_make_tile(Vector2i(2, 0), Vector2i(2, 0)),
	]
	var overlay_tiles = [
		_make_tile(Vector2i(1, 0), Vector2i(3, 0)),  # overwrite cell (1,0)
	]
	var tilemap = TileMapLayer.new()
	tilemap.tile_set = _tileset
	add_child_autofree(tilemap)

	LdtkLevelPlacer.place_tiles(tilemap, base_tiles, 0)
	LdtkLevelPlacer.place_tiles(tilemap, overlay_tiles, 0)

	# Cell (0,0) unchanged
	assert_eq(tilemap.get_cell_atlas_coords(Vector2i(0, 0)), Vector2i(0, 0))
	# Cell (1,0) overwritten by overlay
	assert_eq(tilemap.get_cell_atlas_coords(Vector2i(1, 0)), Vector2i(3, 0))
	# Cell (2,0) unchanged
	assert_eq(tilemap.get_cell_atlas_coords(Vector2i(2, 0)), Vector2i(2, 0))

func test_build_collision_grid_from_intgrid():
	# 4x4 grid CSV: row-major
	# row 0: empty(0), solid(1), empty(0), empty(0)
	# row 1: empty(0), empty(0), water(2), empty(0)
	var csv = [0,1,0,0, 0,0,2,0, 0,0,0,0, 0,0,0,3]
	var grid_width = 4

	var collision = LdtkLevelPlacer.build_collision_grid(csv, grid_width)

	# empty (0) = walkable
	assert_true(collision[Vector2i(0, 0)], "empty should be walkable")
	# solid (1) = not walkable
	assert_false(collision[Vector2i(1, 0)], "solid should not be walkable")
	# water (2) = not walkable
	assert_false(collision[Vector2i(2, 1)], "water should not be walkable")
	# pit (3) = not walkable
	assert_false(collision[Vector2i(3, 3)], "pit should not be walkable")

func test_empty_tiles_array_is_noop():
	var tilemap = TileMapLayer.new()
	tilemap.tile_set = _tileset
	add_child_autofree(tilemap)

	LdtkLevelPlacer.place_tiles(tilemap, [], 0)
	# No cells should be set
	assert_eq(tilemap.get_used_cells().size(), 0)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd project/hosts/complete-app && godot --headless -s addons/gut/gut_cmdln.gd -gdir=res://tests -gtest=test_ldtk_level_placer.gd --quit-on-finish`
Expected: FAIL — `LdtkLevelPlacer` class not found

- [ ] **Step 3: Implement LdtkLevelPlacer**

Create `project/hosts/complete-app/scripts/ldtk_level_placer.gd`:

```gdscript
class_name LdtkLevelPlacer
## Places tiles on a TileMapLayer from parsed LDtk autoLayerTiles data.
## Supports base + overlay merging for era switching.
##
## Usage:
##   LdtkLevelPlacer.place_tiles(tilemap, base_tiles, source_id)
##   LdtkLevelPlacer.place_tiles(tilemap, overlay_tiles, source_id)  # overwrites

## Collision IntGrid values that block movement.
const BLOCKING_VALUES := [1, 2, 3]  # solid, water, pit


## Place auto-layer tiles onto a TileMapLayer.
## Each tile is { "position": Vector2i, "atlas_coords": Vector2i, "flip": int }.
## Calling this twice on the same tilemap overlays — non-empty cells overwrite.
static func place_tiles(tilemap: TileMapLayer, tiles: Array, source_id: int) -> void:
	for tile in tiles:
		var pos: Vector2i = tile["position"]
		var atlas: Vector2i = tile["atlas_coords"]
		var flip: int = tile.get("flip", 0)
		var alt := 0
		if flip & 1:
			alt |= TileSetAtlasSource.TRANSFORM_FLIP_H
		if flip & 2:
			alt |= TileSetAtlasSource.TRANSFORM_FLIP_V
		tilemap.set_cell(pos, source_id, atlas, alt)


## Build a walkability grid from Collision IntGrid CSV.
## Returns Dictionary[Vector2i, bool] — true = walkable, false = blocked.
## IntGrid value 0 (empty) = walkable; values 1 (solid), 2 (water), 3 (pit) = blocked.
static func build_collision_grid(intgrid_csv: Array, grid_width: int) -> Dictionary:
	var grid := {}
	for i in intgrid_csv.size():
		var col := i % grid_width
		var row := i / grid_width
		var value: int = intgrid_csv[i]
		grid[Vector2i(col, row)] = value not in BLOCKING_VALUES
	return grid
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd project/hosts/complete-app && godot --headless -s addons/gut/gut_cmdln.gd -gdir=res://tests -gtest=test_ldtk_level_placer.gd --quit-on-finish`
Expected: All 4 tests PASS

- [ ] **Step 5: Commit**

```bash
git add project/hosts/complete-app/scripts/ldtk_level_placer.gd project/hosts/complete-app/tests/test_ldtk_level_placer.gd
git commit -m "feat: add LdtkLevelPlacer for tile placement and collision grid"
```

---

### Task 3: Add collision grid storage to LocationManager

**Files:**
- Modify: `project/hosts/complete-app/scripts/location_manager.gd:15-26` (vars), `:47-73` (load_location), `:106-117` (unload)

- [ ] **Step 1: Add LDtk project path constant and collision grid storage**

In `project/hosts/complete-app/scripts/location_manager.gd`, add after line 16 (`PCK_BASE_DIR`):

```gdscript
const LDTK_PROJECT_PATH := "res://ldtk/legend-dad.ldtk"
```

Add after line 26 (`_using_fallback`):

```gdscript
var _ldtk_project: Dictionary = {}
var _collision_grids: Dictionary = {}  # era -> Dictionary[Vector2i, bool]
```

- [ ] **Step 2: Load LDtk project in load_location**

In `load_location`, after line 59 (`var config: Dictionary = ...`), add LDtk project loading:

Replace lines 59-73 with:

```gdscript
	var config: Dictionary = _locations_registry[location_name]
	var pck_filename: String = config.get("pck", "")
	var biome: String = config.get("biome", "")
	var pck_path := "res://%s" % pck_filename

	# Load LDtk project (always — layout is independent of art assets)
	if _ldtk_project.is_empty():
		_ldtk_project = LdtkImporter.load_project(LDTK_PROJECT_PATH)

	# Try loading PCK
	var pck_loaded := false
	if FileAccess.file_exists(pck_path):
		pck_loaded = ProjectSettings.load_resource_pack(pck_path)

	if pck_loaded:
		_load_from_pck(location_name, biome)
	else:
		push_warning("LocationManager: PCK not available for '%s', using fallback" % location_name)
		_load_fallback(location_name)
```

- [ ] **Step 3: Add collision grid and level data accessors**

Add these methods at the end of the file (before the closing of the class):

```gdscript

func get_ldtk_project() -> Dictionary:
	return _ldtk_project


func set_collision_grid(era: C_TimelineEra.Era, grid: Dictionary) -> void:
	_collision_grids[era] = grid


func is_walkable(era: C_TimelineEra.Era, col: int, row: int) -> bool:
	var grid: Dictionary = _collision_grids.get(era, {})
	return grid.get(Vector2i(col, row), false)
```

- [ ] **Step 4: Clear collision grids on unload**

In `unload_location`, add `_collision_grids = {}` after `_using_fallback = false` (line 115):

```gdscript
	_collision_grids = {}
```

- [ ] **Step 5: Commit**

```bash
git add project/hosts/complete-app/scripts/location_manager.gd
git commit -m "feat: add LDtk project loading and collision grid to LocationManager"
```

---

### Task 4: Update s_action_processor to use collision grid

**Files:**
- Modify: `project/hosts/complete-app/ecs/systems/s_action_processor.gd:129-137`

- [ ] **Step 1: Update _is_tile_walkable signature and call site**

First, update the call site in `_process_move` (line 51) to pass era:

Replace:
```gdscript
		if tilemap and _is_tile_walkable(tilemap, new_col, new_row):
```
With:
```gdscript
		if tilemap and _is_tile_walkable(tilemap, new_col, new_row, era_comp.era):
```

Then replace `_is_tile_walkable` (lines 129-137):

```gdscript
func _is_tile_walkable(tilemap: TileMapLayer, col: int, row: int) -> bool:
	var cell_coords = Vector2i(col, row)
	var source_id = tilemap.get_cell_source_id(cell_coords)
	if source_id == -1:
		return false
	var tile_data = tilemap.get_cell_tile_data(cell_coords)
	if tile_data:
		return tile_data.get_custom_data("walkable") as bool
	return false
```

With:

```gdscript
func _is_tile_walkable(tilemap: TileMapLayer, col: int, row: int, era: C_TimelineEra.Era = C_TimelineEra.Era.FATHER) -> bool:
	# Use LocationManager collision grid (from LDtk Collision layer) if available.
	if LocationManager.is_location_loaded():
		return LocationManager.is_walkable(era, col, row)

	# Legacy fallback: read from TileSet custom data
	var cell_coords = Vector2i(col, row)
	var source_id = tilemap.get_cell_source_id(cell_coords)
	if source_id == -1:
		return false
	var tile_data = tilemap.get_cell_tile_data(cell_coords)
	if tile_data:
		return tile_data.get_custom_data("walkable") as bool
	return false
```

- [ ] **Step 2: Commit**

```bash
git add project/hosts/complete-app/ecs/systems/s_action_processor.gd
git commit -m "feat: use LocationManager collision grid for walkability checks"
```

---

### Task 5: Wire LDtk tile placement into main.gd

**Files:**
- Modify: `project/hosts/complete-app/scripts/main.gd:1-32` (remove constants), `:75-90` (_ready), `:414-462` (_build_game_view), `:344-358` (_switch_active_era)

- [ ] **Step 1: Remove hardcoded map constants**

Delete lines 4-38 (MAP_WIDTH, MAP_HEIGHT, FATHER_MAP, SON_MAP, BOULDER_COL/ROW, BLOCKED_COL/ROW constants).

Replace with:

```gdscript
const TILE_SIZE := 32

# Level dimensions from LDtk (set at runtime)
var map_width := 0
var map_height := 0
```

- [ ] **Step 2: Add LDtk level data vars**

Add after `var active_era` (was line 51):

```gdscript
# LDtk parsed layer data
var _base_terrain_tiles: Array = []
var _father_terrain_tiles: Array = []
var _son_terrain_tiles: Array = []
var _collision_csv: Array = []
var _collision_grid_width: int = 0
```

- [ ] **Step 3: Add _load_ldtk_level method**

Add this method (place it after `_ready` and before `_create_visual`):

```gdscript
func _load_ldtk_level(level_name: String) -> void:
	var project = LocationManager.get_ldtk_project()
	if project.is_empty():
		push_warning("main: No LDtk project loaded, using empty level")
		return

	var level_node = LdtkImporter.import_level(project, level_name)
	if not level_node:
		push_warning("main: Level '%s' not found in LDtk project" % level_name)
		return

	# Read level dimensions
	map_width = level_node.get_meta("px_width", 320) / 16  # LDtk grid is 16px
	map_height = level_node.get_meta("px_height", 256) / 16

	# Extract layer data
	for child in level_node.get_children():
		var layer_name: String = child.name
		match layer_name:
			"Terrain":
				_base_terrain_tiles = child.get_meta("auto_layer_tiles", [])
			"Terrain_Father":
				_father_terrain_tiles = child.get_meta("auto_layer_tiles", [])
			"Terrain_Son":
				_son_terrain_tiles = child.get_meta("auto_layer_tiles", [])
			"Collision":
				_collision_csv = child.get_meta("intgrid_csv", [])
				_collision_grid_width = child.get_meta("grid_width", map_width)

	# Build collision grids (same collision for both eras by default)
	if not _collision_csv.is_empty():
		var collision_grid = LdtkLevelPlacer.build_collision_grid(_collision_csv, _collision_grid_width)
		LocationManager.set_collision_grid(C_TimelineEra.Era.FATHER, collision_grid)
		LocationManager.set_collision_grid(C_TimelineEra.Era.SON, collision_grid)

	level_node.queue_free()
```

- [ ] **Step 4: Rewrite _build_game_view to use LDtk data**

Replace the entire `_build_game_view` method (was lines 414-462):

```gdscript
func _build_game_view(era: C_TimelineEra.Era) -> SubViewportContainer:
	var container = SubViewportContainer.new()
	container.stretch = true
	container.mouse_filter = Control.MOUSE_FILTER_IGNORE

	var viewport = SubViewport.new()
	viewport.name = "SubViewport"
	viewport.transparent_bg = false
	viewport.canvas_item_default_texture_filter = SubViewport.DEFAULT_CANVAS_ITEM_TEXTURE_FILTER_NEAREST
	container.add_child(viewport)

	# TileMapLayer
	var tilemap = LocationManager.create_tilemap_for_era(era)
	viewport.add_child(tilemap)

	# Place base terrain tiles
	LdtkLevelPlacer.place_tiles(tilemap, _base_terrain_tiles, 0)

	# Overlay era-specific tiles
	var overlay = _father_terrain_tiles if era == C_TimelineEra.Era.FATHER else _son_terrain_tiles
	LdtkLevelPlacer.place_tiles(tilemap, overlay, 0)

	# Store tilemap reference
	if era == C_TimelineEra.Era.FATHER:
		father_tilemap = tilemap
	else:
		son_tilemap = tilemap

	# Camera centered on map
	var camera = Camera2D.new()
	camera.name = "Camera2D"
	camera.position = Vector2(map_width * TILE_SIZE / 2.0, map_height * TILE_SIZE / 2.0)
	viewport.add_child(camera)

	# Era label overlay
	var label = Label.new()
	label.name = "EraLabel"
	var era_text = "FATHER ERA" if era == C_TimelineEra.Era.FATHER else "SON ERA"
	label.text = era_text
	label.add_theme_font_size_override("font_size", 12)
	label.position = Vector2(8, 4)
	if era == C_TimelineEra.Era.FATHER:
		label.add_theme_color_override("font_color", Color(1.0, 0.8, 0.0))
	else:
		label.add_theme_color_override("font_color", Color(1.0, 0.53, 0.53))
	container.add_child(label)

	return container
```

- [ ] **Step 5: Update _ready to use LDtk flow**

Replace lines 75-90 of `_ready` (the section from `LocationManager.load_location` through `add_child(son_view)`):

```gdscript
	LocationManager.load_location("whispering-woods")
	tileset = LocationManager.get_tileset()

	# Load level layout from LDtk
	_load_ldtk_level("Whispering_Woods_Edge")

	# Create ECS World — entities live here as children of the World node.
	world = World.new()
	world.name = "World"
	add_child(world)
	ECS.world = world

	_build_world_map()

	father_view = _build_game_view(C_TimelineEra.Era.FATHER)
	son_view = _build_game_view(C_TimelineEra.Era.SON)
	add_child(father_view)
	add_child(son_view)
```

- [ ] **Step 6: Update _switch_active_era for era re-rendering**

In `_switch_active_era`, add tilemap re-rendering after `LocationManager.swap_era(active_era)` (was line 354). Add:

```gdscript
	# Re-render tilemaps with correct era overlay
	_rerender_tilemap(father_tilemap, C_TimelineEra.Era.FATHER)
	_rerender_tilemap(son_tilemap, C_TimelineEra.Era.SON)
```

And add this helper method:

```gdscript
func _rerender_tilemap(tilemap: TileMapLayer, era: C_TimelineEra.Era) -> void:
	tilemap.clear()
	LdtkLevelPlacer.place_tiles(tilemap, _base_terrain_tiles, 0)
	var overlay = _father_terrain_tiles if era == C_TimelineEra.Era.FATHER else _son_terrain_tiles
	LdtkLevelPlacer.place_tiles(tilemap, overlay, 0)
```

- [ ] **Step 7: Commit**

```bash
git add project/hosts/complete-app/scripts/main.gd
git commit -m "feat: wire LDtk tile placement into main.gd, remove hardcoded maps"
```

---

### Task 6: Fallback behavior when LDtk has no painted data

**Files:**
- Modify: `project/hosts/complete-app/scripts/main.gd` (_load_ldtk_level, _build_game_view)

Since LDtk levels currently have `layerInstances: null` (not yet painted), the game would show an empty tilemap. We need a fallback that uses the old TilesetFactory approach when no LDtk tiles are available.

- [ ] **Step 1: Add fallback check in _ready**

In `_ready`, after `_load_ldtk_level("Whispering_Woods_Edge")`, add:

```gdscript
	# Fallback: if LDtk has no painted tiles, use hardcoded test layout
	if _base_terrain_tiles.is_empty() and _father_terrain_tiles.is_empty() and _son_terrain_tiles.is_empty():
		push_warning("main: No LDtk terrain tiles found, using fallback layout")
		_generate_fallback_layout()
```

- [ ] **Step 2: Add _generate_fallback_layout method**

This generates simple test tiles so the game remains playable during development:

```gdscript
func _generate_fallback_layout() -> void:
	# Simple 10x8 test layout using atlas coords from TilesetFactory
	# 0=grass/walkable, 1=path/walkable, 2=building/blocked, 3=water/blocked
	var layout = [
		[0,0,0,2,2,0,0,0,3,3],
		[0,0,1,1,1,1,0,0,3,3],
		[0,1,1,0,0,1,1,0,0,3],
		[2,1,0,0,0,0,1,0,0,0],
		[2,1,0,0,0,0,1,1,1,0],
		[0,1,1,0,2,0,0,0,1,0],
		[0,0,1,1,1,1,1,1,1,0],
		[0,0,0,0,0,0,0,0,0,0],
	]
	map_width = 10
	map_height = 8
	for row in range(map_height):
		for col in range(map_width):
			_base_terrain_tiles.append({
				"position": Vector2i(col, row),
				"atlas_coords": Vector2i(layout[row][col], 0),
				"flip": 0,
			})

	# Build collision: tiles 2 and 3 are not walkable
	var collision_grid := {}
	for row in range(map_height):
		for col in range(map_width):
			var value = layout[row][col]
			collision_grid[Vector2i(col, row)] = value < 2  # 0,1 = walkable
	LocationManager.set_collision_grid(C_TimelineEra.Era.FATHER, collision_grid)
	LocationManager.set_collision_grid(C_TimelineEra.Era.SON, collision_grid)
```

- [ ] **Step 3: Commit**

```bash
git add project/hosts/complete-app/scripts/main.gd
git commit -m "feat: add fallback layout when LDtk levels are unpainted"
```

---

### Task 7: Run full test suite and verify

**Files:** None (verification only)

- [ ] **Step 1: Run GUT tests**

```bash
cd project/hosts/complete-app && godot --headless -s addons/gut/gut_cmdln.gd -gdir=res://tests --quit-on-finish
```

Expected: All tests pass (test_example, test_ldtk_importer, test_ldtk_level_placer)

- [ ] **Step 2: Run full test suite via Taskfile**

```bash
task test
```

Expected: All suites pass (pytest, vitest, GUT)

- [ ] **Step 3: Commit any fixes if needed**

Only if test runs exposed issues that need fixing.

---

### Task 8: Copy LDtk file to Godot project for runtime access

**Files:**
- Modify: `Taskfile.yml` (add ldtk sync task)

The LDtk file lives at `project/ldtk/legend-dad.ldtk` but `LdtkImporter` reads from `res://ldtk/legend-dad.ldtk`. We need a symlink or copy step.

- [ ] **Step 1: Check if ldtk directory exists in Godot project**

```bash
ls -la project/hosts/complete-app/ldtk/ 2>/dev/null || echo "does not exist"
```

- [ ] **Step 2: Create symlink from Godot project to LDtk source**

```bash
ln -sf ../../../ldtk project/hosts/complete-app/ldtk
```

This makes `res://ldtk/legend-dad.ldtk` resolve correctly at runtime.

- [ ] **Step 3: Verify the symlink works**

```bash
ls -la project/hosts/complete-app/ldtk/legend-dad.ldtk
```

Expected: Shows the symlink pointing to the actual `.ldtk` file

- [ ] **Step 4: Add ldtk symlink to .gitignore if not tracked**

Check if `.gitignore` needs updating:

```bash
echo "# LDtk symlink is created by setup" >> project/hosts/complete-app/.gitignore 2>/dev/null
```

- [ ] **Step 5: Commit**

```bash
git add project/hosts/complete-app/ldtk project/hosts/complete-app/.gitignore
git commit -m "feat: symlink LDtk project into Godot for runtime access"
```
