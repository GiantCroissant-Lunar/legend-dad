class_name LdtkImporter
## Reads LDtk .ldtk JSON files and creates Godot nodes.
##
## Usage:
##   var importer = LdtkImporter.new()
##   var level_node = importer.import_level(ldtk_data, "Level_0")
##   add_child(level_node)
##
## The importer creates:
##   - Node2D container per level
##   - TileMapLayer per IntGrid/Tile layer (collision, terrain)
##   - Node2D per entity instance with metadata (display_name, vault_path, era, etc.)

const LDTK_DIR := "res://ldtk/"


## Load and parse an LDtk project file. Returns the parsed Dictionary.
static func load_project(path: String) -> Dictionary:
	if not FileAccess.file_exists(path):
		push_error("LDtk file not found: %s" % path)
		return {}
	var file := FileAccess.open(path, FileAccess.READ)
	var text := file.get_as_text()
	file.close()
	var json := JSON.new()
	var err := json.parse(text)
	if err != OK:
		push_error("Failed to parse LDtk JSON: %s at line %d" % [json.get_error_message(), json.get_error_line()])
		return {}
	return json.data


## Get list of level identifiers from an LDtk project.
static func get_level_names(project: Dictionary) -> PackedStringArray:
	var names := PackedStringArray()
	for level in project.get("levels", []):
		names.append(level.get("identifier", ""))
	return names


## Import a single level by identifier. Returns a Node2D containing all layers.
static func import_level(project: Dictionary, level_identifier: String) -> Node2D:
	var level_data := _find_level(project, level_identifier)
	if level_data.is_empty():
		push_error("Level not found: %s" % level_identifier)
		return null

	var level_node := Node2D.new()
	level_node.name = level_identifier
	level_node.set_meta("ldtk_uid", level_data.get("uid", -1))
	level_node.set_meta("ldtk_iid", level_data.get("iid", ""))
	level_node.set_meta("world_x", level_data.get("worldX", 0))
	level_node.set_meta("world_y", level_data.get("worldY", 0))
	level_node.set_meta("px_width", level_data.get("pxWid", 0))
	level_node.set_meta("px_height", level_data.get("pxHei", 0))

	# Build layer def lookup
	var layer_defs := _build_layer_def_lookup(project)

	# Process layer instances (reversed — LDtk stores top-first, Godot draws bottom-first)
	var raw_layers = level_data.get("layerInstances", null)
	if raw_layers == null:
		return level_node
	var layer_instances: Array = raw_layers
	for i in range(layer_instances.size() - 1, -1, -1):
		var layer := layer_instances[i] as Dictionary
		var layer_type: String = layer.get("__type", "")

		match layer_type:
			"IntGrid":
				var intgrid_node := _import_intgrid_layer(layer, layer_defs)
				if intgrid_node:
					level_node.add_child(intgrid_node)
			"Entities":
				var entities_node := _import_entity_layer(layer)
				if entities_node:
					level_node.add_child(entities_node)
			"Tiles":
				var tiles_node := _import_tile_layer(layer)
				if tiles_node:
					level_node.add_child(tiles_node)
			"AutoLayer":
				pass  # Auto layers are visual only — handled by LDtk export

	return level_node


## Import all levels from an LDtk project. Returns a Node2D containing all levels.
static func import_all_levels(project: Dictionary) -> Node2D:
	var root := Node2D.new()
	root.name = "LdtkWorld"
	for level in project.get("levels", []):
		var level_id: String = level.get("identifier", "")
		var level_node := import_level(project, level_id)
		if level_node:
			level_node.position = Vector2(
				level.get("worldX", 0),
				level.get("worldY", 0)
			)
			root.add_child(level_node)
	return root


# --- Private helpers ---

static func _find_level(project: Dictionary, identifier: String) -> Dictionary:
	for level in project.get("levels", []):
		if level.get("identifier", "") == identifier:
			return level
	return {}


static func _build_layer_def_lookup(project: Dictionary) -> Dictionary:
	var lookup := {}
	for layer_def in project.get("defs", {}).get("layers", []):
		lookup[layer_def.get("uid", -1)] = layer_def
	return lookup


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


static func _import_entity_layer(layer: Dictionary) -> Node2D:
	var identifier: String = layer.get("__identifier", "Entities")
	var entity_instances: Array = layer.get("entityInstances", [])

	if entity_instances.is_empty():
		return null

	var node := Node2D.new()
	node.name = identifier
	node.set_meta("layer_type", "Entities")

	for entity_inst in entity_instances:
		var entity_node := _import_entity_instance(entity_inst)
		if entity_node:
			node.add_child(entity_node)

	return node


static func _import_entity_instance(entity: Dictionary) -> Node2D:
	var identifier: String = entity.get("__identifier", "Entity")
	var px: Array = entity.get("px", [0, 0])
	var width: int = entity.get("width", 16)
	var height: int = entity.get("height", 16)

	var node := Node2D.new()
	node.name = identifier
	node.position = Vector2(px[0], px[1])

	# Core metadata
	node.set_meta("ldtk_type", identifier)
	node.set_meta("ldtk_iid", entity.get("iid", ""))
	node.set_meta("ldtk_def_uid", entity.get("defUid", -1))
	node.set_meta("width", width)
	node.set_meta("height", height)
	node.set_meta("tags", entity.get("__tags", []))

	# Parse field instances into metadata
	for field in entity.get("fieldInstances", []):
		var field_id: String = field.get("__identifier", "")
		var field_value = field.get("__value", null)
		if field_id and field_value != null:
			node.set_meta(field_id, field_value)

	return node


static func _import_tile_layer(layer: Dictionary) -> Node2D:
	var identifier: String = layer.get("__identifier", "Tiles")
	var grid_tiles: Array = layer.get("gridTiles", [])

	if grid_tiles.is_empty():
		return null

	var node := Node2D.new()
	node.name = identifier
	node.set_meta("layer_type", "Tiles")
	node.set_meta("grid_size", layer.get("__gridSize", 16))
	node.set_meta("grid_tiles", grid_tiles)

	return node
