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


## Convert IntGrid CSV to tile placement array.
## Maps IntGrid value N to atlas coords (N % atlas_columns, N / atlas_columns).
## Skips cells with value 0 (void/empty).
static func intgrid_to_tiles(intgrid_csv: Array, grid_width: int, atlas_columns: int = 16) -> Array:
	var tiles: Array = []
	for i in intgrid_csv.size():
		var value: int = intgrid_csv[i]
		if value == 0:
			continue
		var col := i % grid_width
		var row := i / grid_width
		tiles.append({
			"position": Vector2i(col, row),
			"atlas_coords": Vector2i(value % atlas_columns, value / atlas_columns),
			"flip": 0,
		})
	return tiles


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
