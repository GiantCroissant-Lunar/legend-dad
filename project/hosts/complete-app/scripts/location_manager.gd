class_name LocationManagerClass
extends Node

## Manages location PCK loading/unloading with palette shader support.
## Falls back to TilesetFactory when no PCK is available.
##
## Usage:
##   LocationManager.load_location("whispering-woods")
##   LocationManager.swap_era(C_TimelineEra.Era.SON)
##   LocationManager.unload_location()

signal location_loaded(location_name: String)
signal location_unloaded(location_name: String)

const LOCATIONS_PATH := "res://data/locations.json"
const PCK_BASE_DIR := "res://locations/"
const LDTK_PROJECT_PATH := "res://ldtk/legend-dad.ldtk"
const PCK_SERVER_URL := "http://localhost:3000/pck/"

var _current_location := ""
var _current_biome := ""
var _locations_registry := {}
var _father_tilemap: TileMapLayer
var _son_tilemap: TileMapLayer
var _father_palette: Texture2D
var _son_palette: Texture2D
var _tileset: TileSet
var _using_fallback := false
var _ldtk_project: Dictionary = {}
var _collision_grids: Dictionary = {}  # era -> Dictionary[Vector2i, bool]


func _ready() -> void:
	_load_registry()


func _load_registry() -> void:
	if not FileAccess.file_exists(LOCATIONS_PATH):
		push_warning("LocationManager: locations.json not found at %s" % LOCATIONS_PATH)
		return
	var file := FileAccess.open(LOCATIONS_PATH, FileAccess.READ)
	var json := JSON.new()
	var err := json.parse(file.get_as_text())
	file.close()
	if err != OK:
		push_error("LocationManager: failed to parse locations.json: %s" % json.get_error_message())
		return
	_locations_registry = json.data


func load_location(location_name: String) -> void:
	if _current_location == location_name:
		return

	if not _current_location.is_empty():
		unload_location()

	if location_name not in _locations_registry:
		push_warning("LocationManager: unknown location '%s', using fallback" % location_name)
		_load_fallback(location_name)
		return

	var config: Dictionary = _locations_registry[location_name]
	var pck_filename: String = config.get("pck", "")
	var biome: String = config.get("biome", "")
	var pck_path := "res://%s" % pck_filename

	# Load LDtk project (always — layout is independent of art assets)
	if _ldtk_project.is_empty():
		_ldtk_project = LdtkImporter.load_project(LDTK_PROJECT_PATH)

	# Set cell size from LDtk project metadata
	if _ldtk_project.has("defaultGridSize"):
		GameConfig.cell_size = int(_ldtk_project["defaultGridSize"])

	# Try loading PCK — native path first, then HTTP fetch for web builds
	var pck_loaded := false
	if FileAccess.file_exists(pck_path):
		pck_loaded = ProjectSettings.load_resource_pack(pck_path)

	if not pck_loaded and OS.has_feature("web"):
		# Web builds: fetch PCK from game server, save to user://, then load
		pck_loaded = await _fetch_pck_web(pck_filename)

	if pck_loaded:
		_load_from_pck(location_name, biome)
	else:
		push_warning("LocationManager: PCK not available for '%s', using fallback" % location_name)
		_load_fallback(location_name)


func _fetch_pck_web(pck_filename: String) -> bool:
	var url := PCK_SERVER_URL + pck_filename
	var http := HTTPRequest.new()
	add_child(http)
	http.request(url)
	var result: Array = await http.request_completed
	http.queue_free()

	var response_code: int = result[1]
	var body: PackedByteArray = result[3]
	if response_code != 200 or body.is_empty():
		push_warning("LocationManager: HTTP fetch failed for '%s' (code %d)" % [pck_filename, response_code])
		return false

	# Save to user:// so load_resource_pack can find it
	var local_path := "user://" + pck_filename
	var file := FileAccess.open(local_path, FileAccess.WRITE)
	if not file:
		push_error("LocationManager: cannot write PCK to %s" % local_path)
		return false
	file.store_buffer(body)
	file.close()

	var loaded := ProjectSettings.load_resource_pack(local_path)
	if loaded:
		print("LocationManager: PCK loaded from server: %s" % pck_filename)
	return loaded


func _load_from_pck(location_name: String, biome: String) -> void:
	var loc_dir := PCK_BASE_DIR + location_name + "/"

	# Load TileSet
	_tileset = load(loc_dir + "tileset.tres") as TileSet
	if not _tileset:
		push_error("LocationManager: failed to load tileset from PCK for '%s'" % location_name)
		_load_fallback(location_name)
		return

	# Load palettes
	_father_palette = load(loc_dir + "palette_father.png") as Texture2D
	_son_palette = load(loc_dir + "palette_son.png") as Texture2D

	_current_location = location_name
	_current_biome = biome
	_using_fallback = false
	location_loaded.emit(location_name)


func _load_fallback(location_name: String) -> void:
	_tileset = TilesetFactory.create_tileset()
	_father_palette = null
	_son_palette = null
	_current_location = location_name
	_current_biome = _locations_registry.get(location_name, {}).get("biome", "")
	_using_fallback = true
	location_loaded.emit(location_name)


func unload_location() -> void:
	var old_name := _current_location
	_tileset = null
	_father_palette = null
	_son_palette = null
	_father_tilemap = null
	_son_tilemap = null
	_current_location = ""
	_current_biome = ""
	_using_fallback = false
	_collision_grids = {}
	# _ldtk_project intentionally kept: single project file is shared across all locations
	if not old_name.is_empty():
		location_unloaded.emit(old_name)


func create_tilemap_for_era(era: C_TimelineEra.Era) -> TileMapLayer:
	var tilemap := TileMapLayer.new()
	tilemap.name = "TileMapLayer"
	tilemap.tile_set = _tileset
	if era == C_TimelineEra.Era.FATHER:
		_father_tilemap = tilemap
	else:
		_son_tilemap = tilemap

	# Apply palette shader if we have palette textures (PCK mode)
	if not _using_fallback:
		var palette := _father_palette if era == C_TimelineEra.Era.FATHER else _son_palette
		if palette:
			PaletteManager.apply_palette(tilemap, palette)

	return tilemap


func swap_era(era: int) -> void:
	if _using_fallback:
		return  # Fallback tiles don't use palette shader
	var palette := _father_palette if era == C_TimelineEra.Era.FATHER else _son_palette
	if not palette:
		return
	if _father_tilemap:
		PaletteManager.swap_palette(_father_tilemap, palette)
	if _son_tilemap:
		PaletteManager.swap_palette(_son_tilemap, palette)


func get_current_location() -> String:
	return _current_location


func is_location_loaded() -> bool:
	return not _current_location.is_empty()


func is_using_fallback() -> bool:
	return _using_fallback


func force_fallback() -> void:
	_tileset = TilesetFactory.create_tileset()
	_father_palette = null
	_son_palette = null
	_using_fallback = true


func get_tileset() -> TileSet:
	return _tileset


func get_ldtk_project() -> Dictionary:
	return _ldtk_project


func set_collision_grid(era: C_TimelineEra.Era, grid: Dictionary) -> void:
	_collision_grids[era] = grid


func is_walkable(era: C_TimelineEra.Era, col: int, row: int) -> bool:
	var grid: Dictionary = _collision_grids.get(era, {})
	return grid.get(Vector2i(col, row), false)
