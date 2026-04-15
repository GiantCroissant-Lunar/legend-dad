# project/hosts/complete-app/scripts/content_manager.gd
extends Node
##
## Autoloaded as ContentManager. Loads/unloads PCK bundles described by
## project/shared/data/content_manifest.json (or the equivalent fetched at
## runtime over HTTP for web builds).
##
## See res://lib/contracts/content_manager_api.gd for the public contract.

signal bundle_loading(bundle_id: String)
signal bundle_loaded(bundle_id: String)
signal bundle_load_failed(bundle_id: String, reason: String)
signal bundle_unloaded(bundle_id: String)
signal bundle_will_reload(bundle_id: String)

const MANIFEST_PATH := "res://data/content_manifest.json"
# Where fetched PCKs are cached on web. user:// maps to IndexedDB in the browser.
const WEB_PCK_CACHE_DIR := "user://pck_cache"

var _manifest: Dictionary = {"schema_version": 1, "bundles": {}}
var _loaded: Dictionary = {}  # bundle_id -> true
# Test seam: tests inject a callable that simulates ProjectSettings.load_resource_pack.
var _test_pck_loader: Callable = Callable()


func _ready() -> void:
	var f := FileAccess.open(MANIFEST_PATH, FileAccess.READ)
	if f == null:
		push_warning("ContentManager: no manifest at %s — running in fallback" % MANIFEST_PATH)
		return
	var raw := f.get_as_text()
	var parsed: Variant = JSON.parse_string(raw)
	if typeof(parsed) != TYPE_DICTIONARY:
		push_error("ContentManager: malformed manifest")
		return
	load_manifest_dict(parsed)


func load_manifest_dict(d: Dictionary) -> void:
	_manifest = d


func describe(bundle_id: String) -> Dictionary:
	var bundles: Dictionary = _manifest.get("bundles", {})
	return bundles.get(bundle_id, {})


func is_loaded(bundle_id: String) -> bool:
	return _loaded.has(bundle_id)


func loaded_bundles() -> Array[String]:
	var out: Array[String] = []
	for k in _loaded.keys():
		out.append(k)
	return out


func load_bundle(bundle_id: String) -> bool:
	if is_loaded(bundle_id):
		return true
	var entry := describe(bundle_id)
	if entry.is_empty():
		emit_signal("bundle_load_failed", bundle_id, "unknown bundle")
		return false
	# Load deps depth-first.
	for dep in entry.get("deps", []):
		var dep_ok: bool = await load_bundle(dep)
		if not dep_ok:
			emit_signal("bundle_load_failed", bundle_id, "dep '%s' failed" % dep)
			return false
	emit_signal("bundle_loading", bundle_id)
	var pck_name := str(entry.get("pck", ""))
	var ok: bool
	if _test_pck_loader.is_valid():
		# Tests inject a fake loader; preserve the legacy res:// path shape so
		# existing test contracts don't shift.
		ok = _test_pck_loader.call("res://pck/%s" % pck_name)
	elif OS.has_feature("web"):
		# load_resource_pack on web reads from Emscripten MEMFS, not the network,
		# so res://pck/... is not reachable. Fetch via HTTP, write to user://,
		# then load from there.
		ok = await _load_pck_web(pck_name)
	else:
		# Native (editor / headless / desktop export). Local pck/ symlink or
		# baked-in res:// path resolves directly.
		ok = ProjectSettings.load_resource_pack("res://pck/%s" % pck_name, false)
	if not ok:
		emit_signal("bundle_load_failed", bundle_id, "PCK load failed: %s" % pck_name)
		return false
	_loaded[bundle_id] = true
	emit_signal("bundle_loaded", bundle_id)
	return true


# Fetches a PCK over HTTP, caches it under user:// (IndexedDB on the browser),
# and asks Godot to load it. Mirrors the per-call HTTPRequest pattern
# `LocationManager._fetch_pck_web` already uses successfully in production.
func _load_pck_web(pck_name: String) -> bool:
	# Always overwrite — hashed filenames mean stale cache CAN'T happen by
	# design, and writing fresh bytes guards against any corruption from
	# earlier broken builds during development.
	DirAccess.make_dir_recursive_absolute(
		ProjectSettings.globalize_path(WEB_PCK_CACHE_DIR)
	)
	var cache_path := "%s/%s" % [WEB_PCK_CACHE_DIR, pck_name]

	# Build absolute URL relative to where the wasm is served.
	var origin := str(JavaScriptBridge.eval("window.location.origin", true))
	var pathname := str(JavaScriptBridge.eval("window.location.pathname", true))
	var base := pathname.get_base_dir().rstrip("/")
	var url := "%s%s/pck/%s" % [origin, base, pck_name]

	# Fresh HTTPRequest per call — reusing one across calls is unreliable
	# on multi-threaded web (request_completed may not fire).
	var http := HTTPRequest.new()
	add_child(http)
	var err := http.request(url)
	if err != OK:
		push_error("ContentManager: HTTPRequest.request failed (%d) for %s" % [err, url])
		http.queue_free()
		return false
	var result: Array = await http.request_completed
	http.queue_free()

	var response_code: int = result[1]
	var body: PackedByteArray = result[3]
	if response_code != 200 or body.is_empty():
		push_error(
			"ContentManager: HTTP fetch failed for %s (code %d, %d bytes)"
			% [url, response_code, body.size()]
		)
		return false

	var f := FileAccess.open(cache_path, FileAccess.WRITE)
	if f == null:
		push_error("ContentManager: cannot write %s" % cache_path)
		return false
	f.store_buffer(body)
	f.close()
	return ProjectSettings.load_resource_pack(cache_path, false)


func unload_bundle(bundle_id: String) -> bool:
	if not is_loaded(bundle_id):
		return true
	# Refuse if any other loaded bundle declares this as a dep.
	for other_id in _loaded.keys():
		if other_id == bundle_id:
			continue
		var other := describe(other_id)
		if bundle_id in other.get("deps", []):
			push_warning("Refusing to unload %s — %s depends on it" % [bundle_id, other_id])
			return false
	# Godot has no public API to unload a PCK individually. Mark as unloaded so
	# the runtime stops referencing its resources; physical memory is reclaimed
	# only when references drop and the resource cache evicts. This is a known
	# Godot 4 limitation — bundle authors should keep PCKs small.
	_loaded.erase(bundle_id)
	emit_signal("bundle_unloaded", bundle_id)
	return true


# Lookup helpers — content code looks up by stable ID, not by res:// path.
# After a bundle loads, its resources live at res://content/{kind}/{bundle}/...
# These helpers centralize the path convention.

func get_enemy_definition(id: String) -> Resource:
	return _load_resource_by_kind("enemies", id, ".tres")

func get_npc_definition(id: String) -> Resource:
	return _load_resource_by_kind("npcs", id, ".tres")

func get_hud_widget(id: String) -> Resource:
	return _load_resource_by_kind("hud", id, ".tres")

func get_item_definition(id: String) -> Resource:
	return _load_resource_by_kind("items", id, ".tres")


func _load_resource_by_kind(kind: String, id: String, ext: String) -> Resource:
	# Try every loaded bundle of this kind for a matching resource.
	for bundle_id in _loaded.keys():
		var entry := describe(bundle_id)
		if entry.get("kind", "") != kind:
			continue
		var path := "res://content/%s/%s/%s%s" % [kind, bundle_id, id, ext]
		if ResourceLoader.exists(path):
			return load(path)
	return null
