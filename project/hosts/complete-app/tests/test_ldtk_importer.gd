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
