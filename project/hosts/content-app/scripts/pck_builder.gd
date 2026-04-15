extends SceneTree

## Headless tool script: reads a manifest.json and builds a location .pck file.
##
## Usage (via Taskfile):
##   python3 scripts/run_godot_checked.py \
##     $GODOT_PATH --headless --path project/hosts/complete-app \
##     --script scripts/pck_builder.gd -- --location=whispering-woods

func _init() -> void:
	var location := _get_arg("--location")
	if location.is_empty():
		push_error("pck_builder: --location argument required")
		quit(1)
		return

	var project_root := _find_project_root()
	var manifest_path := project_root + "/build/_artifacts/pck/" + location + "/manifest.json"

	if not FileAccess.file_exists(manifest_path):
		push_error("pck_builder: manifest not found at %s" % manifest_path)
		quit(1)
		return

	var result := _build_pck(manifest_path, location, project_root)
	quit(0 if result else 1)


func _build_pck(manifest_path: String, location: String, project_root: String) -> bool:
	# Read manifest
	var file := FileAccess.open(manifest_path, FileAccess.READ)
	var json := JSON.new()
	var err := json.parse(file.get_as_text())
	file.close()
	if err != OK:
		push_error("pck_builder: failed to parse manifest: %s" % json.get_error_message())
		return false

	var manifest: Dictionary = json.data
	var tile_size: int = manifest.get("tile_size", 16)
	var grid_cols: int = manifest.get("grid_columns", 16)
	var grid_rows: int = manifest.get("grid_rows", 16)
	var tiles: Array = manifest.get("tiles", [])

	# Load atlas image
	var atlas_path: String = manifest.get("atlas_path", "")
	var atlas_image := Image.load_from_file(atlas_path)
	if atlas_image == null:
		push_error("pck_builder: failed to load atlas from %s" % atlas_path)
		return false

	var atlas_texture := ImageTexture.create_from_image(atlas_image)

	# Create TileSet
	var tileset := TileSet.new()
	tileset.tile_size = Vector2i(tile_size, tile_size)

	# Custom data layers
	tileset.add_custom_data_layer()
	tileset.set_custom_data_layer_name(0, "walkable")
	tileset.set_custom_data_layer_type(0, TYPE_BOOL)
	tileset.add_custom_data_layer()
	tileset.set_custom_data_layer_name(1, "tile_type")
	tileset.set_custom_data_layer_type(1, TYPE_STRING)

	# Atlas source
	var atlas_source := TileSetAtlasSource.new()
	atlas_source.texture = atlas_texture
	atlas_source.texture_region_size = Vector2i(tile_size, tile_size)
	tileset.add_source(atlas_source, 0)

	# Create tiles and assign properties
	for tile_data in tiles:
		var atlas_x: int = tile_data.get("atlas_x", 0)
		var atlas_y: int = tile_data.get("atlas_y", 0)
		var coords := Vector2i(atlas_x, atlas_y)
		atlas_source.create_tile(coords)
		var td := atlas_source.get_tile_data(coords, 0)
		td.set_custom_data("walkable", tile_data.get("walkable", true))
		td.set_custom_data("tile_type", tile_data.get("type", "decoration"))

	# Save TileSet resource
	var loc_dir := "res://locations/" + location + "/"
	DirAccess.make_dir_recursive_absolute(loc_dir)
	var save_err := ResourceSaver.save(tileset, loc_dir + "tileset.tres")
	if save_err != OK:
		push_error("pck_builder: failed to save tileset: %s" % error_string(save_err))
		return false

	# Bake palettes as self-contained ImageTexture resources. Copying the raw
	# PNGs is not enough — Godot's image loader requires `.import` metadata that
	# points at a `.godot/imported/*.ctex` binary which lives outside the PCK,
	# so the PNGs would fail to resolve at runtime. Saving as .tres embeds the
	# pixel data directly into the resource (same trick the atlas uses inside
	# tileset.tres above), making the PCK fully self-describing.
	var palettes: Dictionary = manifest.get("palettes", {})
	if not _bake_palette_texture(palettes.get("father", ""), loc_dir + "palette_father.tres"):
		return false
	if not _bake_palette_texture(palettes.get("son", ""), loc_dir + "palette_son.tres"):
		return false

	# Copy manifest for debugging — atlas/palette PNGs intentionally not packed:
	# they're embedded in the saved resources above and the raw PNGs would
	# require .import companions to load at runtime.
	_copy_file(manifest_path, loc_dir + "manifest.json")

	# Pack into PCK
	var pck_path := project_root + "/build/_artifacts/pck/" + location + ".pck"
	var packer := PCKPacker.new()
	var pck_err := packer.pck_start(pck_path)
	if pck_err != OK:
		push_error("pck_builder: failed to start PCK: %s" % error_string(pck_err))
		return false

	# Add all files in the location directory
	var dir := DirAccess.open(loc_dir)
	if dir:
		dir.list_dir_begin()
		var filename := dir.get_next()
		while filename != "":
			if not dir.current_is_dir():
				var full_path := loc_dir + filename
				var res_path := "res://locations/" + location + "/" + filename
				packer.add_file(res_path, full_path)
				print("  Packed: %s" % res_path)
			filename = dir.get_next()
		dir.list_dir_end()

	pck_err = packer.flush()
	if pck_err != OK:
		push_error("pck_builder: failed to flush PCK: %s" % error_string(pck_err))
		return false

	print("PCK written to %s" % pck_path)
	return true


func _copy_file(src: String, dst: String) -> void:
	if src.is_empty() or not FileAccess.file_exists(src):
		push_warning("pck_builder: source file not found: %s" % src)
		return
	var data := FileAccess.get_file_as_bytes(src)
	var out := FileAccess.open(dst, FileAccess.WRITE)
	out.store_buffer(data)
	out.close()


# Loads a PNG from the host filesystem and saves an ImageTexture .tres resource
# that embeds the pixel data — the runtime can then `load(...tres)` directly
# without depending on Godot's import pipeline (.import + .ctex).
func _bake_palette_texture(src_path: String, dst_path: String) -> bool:
	if src_path.is_empty() or not FileAccess.file_exists(src_path):
		push_error("pck_builder: palette source not found: %s" % src_path)
		return false
	var img := Image.load_from_file(src_path)
	if img == null:
		push_error("pck_builder: failed to load palette image %s" % src_path)
		return false
	var tex := ImageTexture.create_from_image(img)
	var err := ResourceSaver.save(tex, dst_path)
	if err != OK:
		push_error("pck_builder: failed to save palette %s: %s" % [dst_path, error_string(err)])
		return false
	return true


func _get_arg(prefix: String) -> String:
	for arg in OS.get_cmdline_user_args():
		if arg.begins_with(prefix + "="):
			return arg.substr(prefix.length() + 1)
		if arg.begins_with(prefix):
			return arg.substr(prefix.length())
	return ""


func _find_project_root() -> String:
	# Walk up from the Godot project dir to find the repo root (has Taskfile.yml)
	var dir := OS.get_executable_path().get_base_dir()
	# Use the project path (cwd when running --path)
	var project_path := ProjectSettings.globalize_path("res://")
	var current := project_path
	for i in range(10):
		if FileAccess.file_exists(current + "/Taskfile.yml"):
			return current.rstrip("/")
		current = current.get_base_dir()
	# Fallback: assume project/hosts/complete-app is 3 levels deep
	return ProjectSettings.globalize_path("res://").get_base_dir().get_base_dir().get_base_dir()
