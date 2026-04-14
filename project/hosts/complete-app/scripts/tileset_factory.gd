class_name TilesetFactory

## Creates a simple prototype TileSet with colored tiles.
## Tile IDs:
##   Source 0 (father era):
##     Atlas coord (0,0) = grass (green)    - walkable
##     Atlas coord (1,0) = path (brown)     - walkable
##     Atlas coord (2,0) = building (dark)  - not walkable
##     Atlas coord (3,0) = water (blue)     - not walkable
##   Source 1 (son era):
##     Atlas coord (0,0) = dead grass (dark green) - walkable
##     Atlas coord (1,0) = path (brown)            - walkable
##     Atlas coord (2,0) = ruin (dark brown)       - not walkable
##     Atlas coord (3,0) = blocked (gray)          - not walkable

static func create_tileset() -> TileSet:
	var tileset = TileSet.new()
	tileset.tile_size = Vector2i(GameConfig.cell_size, GameConfig.cell_size)

	# Add custom data layer for walkability
	tileset.add_custom_data_layer()
	tileset.set_custom_data_layer_name(0, "walkable")
	tileset.set_custom_data_layer_type(0, TYPE_BOOL)

	# Create father era source (source_id = 0)
	_add_colored_source(tileset, 0, [
		Color(0.23, 0.42, 0.12),  # grass
		Color(0.55, 0.45, 0.33),  # path
		Color(0.42, 0.35, 0.23),  # building
		Color(0.17, 0.35, 0.55),  # water
	], [true, true, false, false])

	# Create son era source (source_id = 1)
	_add_colored_source(tileset, 1, [
		Color(0.29, 0.29, 0.16),  # dead grass
		Color(0.55, 0.45, 0.33),  # path
		Color(0.29, 0.23, 0.17),  # ruin
		Color(0.33, 0.33, 0.33),  # blocked
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
