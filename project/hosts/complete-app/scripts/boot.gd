# project/hosts/complete-app/scripts/boot.gd
extends Control

@onready var _status: Label = $StatusLabel


func _ready() -> void:
	_set_status("Booting…")
	await get_tree().process_frame
	_set_status("Loading manifest…")
	var manifest := _load_manifest()
	if manifest.is_empty():
		_set_status("No content manifest — running in fallback mode")
		return
	_set_status("Loading eager bundles…")
	var eager_ids := _eager_bundle_ids(manifest)
	for id in eager_ids:
		_set_status("Loading %s…" % id)
		var ok: bool = ContentManager.load_bundle(id)
		if not ok:
			_set_status("Failed to load %s — see logs" % id)
	_set_status("Ready")
	# Hand off to gameplay main scene once gameplay scene is implemented in a
	# follow-up plan. For this plan, boot.tscn is the terminus and the rest
	# comes from server state via WS.


func _load_manifest() -> Dictionary:
	var path := "res://data/content_manifest.json"
	if not FileAccess.file_exists(path):
		push_warning("boot: no manifest at %s" % path)
		return {}
	var parsed: Variant = JSON.parse_string(FileAccess.get_file_as_string(path))
	if typeof(parsed) != TYPE_DICTIONARY:
		push_error("boot: malformed manifest")
		return {}
	return parsed


func _eager_bundle_ids(manifest: Dictionary) -> Array[String]:
	var out: Array[String] = []
	var bundles: Dictionary = manifest.get("bundles", {})
	for id in bundles.keys():
		if bundles[id].get("policy", "") == "eager":
			out.append(id)
	return out


func _set_status(msg: String) -> void:
	if _status:
		_status.text = msg
	print("[boot] ", msg)
