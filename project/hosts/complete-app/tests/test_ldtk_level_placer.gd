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
