# project/hosts/content-app/scripts/bundle_packager.gd
##
## Headless tool: read shared/content/{kind}/{bundle-id}/bundle.json,
## validate, hash included files, pack into build/_artifacts/pck/{id}@{hash}.pck.
##
## Run via: task content:build -- {bundle-id}
extends SceneTree


func _init() -> void:
	var args := OS.get_cmdline_user_args()
	var bundle_id := ""
	for a in args:
		if a.begins_with("--bundle="):
			bundle_id = a.substr("--bundle=".length())
	if bundle_id.is_empty():
		push_error("bundle_packager: missing --bundle=<id>")
		quit(2)
		return
	var rc := _build(bundle_id)
	quit(rc)


func _build(bundle_id: String) -> int:
	# Resolve source dir under res://content/{kind}/{bundle_id}/
	var bundle_dir := _find_bundle_dir(bundle_id)
	if bundle_dir.is_empty():
		push_error("bundle_packager: cannot find bundle dir for %s" % bundle_id)
		return 3
	var bundle_json_path := "%s/bundle.json" % bundle_dir
	var f := FileAccess.open(bundle_json_path, FileAccess.READ)
	if f == null:
		push_error("bundle_packager: missing bundle.json at %s" % bundle_json_path)
		return 4
	var meta: Dictionary = JSON.parse_string(f.get_as_text())

	# Collect files matching include patterns.
	var include_globs: Array = meta.get("include", [])
	var files := _collect_files(bundle_dir, include_globs)
	if files.is_empty():
		push_error("bundle_packager: no files matched include patterns for %s" % bundle_id)
		return 5

	# Compute content hash (sha1 of sorted file contents).
	var hash_ctx := HashingContext.new()
	hash_ctx.start(HashingContext.HASH_SHA1)
	files.sort()
	for path in files:
		var fh := FileAccess.open(path, FileAccess.READ)
		if fh:
			hash_ctx.update(fh.get_buffer(fh.get_length()))
	var hash_bytes := hash_ctx.finish()
	var hash_hex := hash_bytes.hex_encode().substr(0, 6)

	# Pack into build/_artifacts/pck/{id}@{hash}.pck
	var out_dir := ProjectSettings.globalize_path("res://").path_join("../../../build/_artifacts/pck")
	DirAccess.make_dir_recursive_absolute(out_dir)
	var out_path := "%s/%s@%s.pck" % [out_dir, bundle_id, hash_hex]

	var packer := PCKPacker.new()
	var err := packer.pck_start(out_path)
	if err != OK:
		push_error("bundle_packager: pck_start failed (%d)" % err)
		return 6
	for path in files:
		# The path inside the PCK preserves res:// layout so loaded resources
		# appear at the same paths the runtime expects.
		var pck_internal_path := path  # Already res://content/{kind}/{id}/...
		err = packer.add_file(pck_internal_path, ProjectSettings.globalize_path(path))
		if err != OK:
			push_error("bundle_packager: add_file failed for %s" % path)
			return 7
	# Also include bundle.json itself for runtime debugging.
	var bj_internal := "%s/bundle.json" % bundle_dir
	packer.add_file(bj_internal, ProjectSettings.globalize_path(bundle_json_path))
	err = packer.flush()
	if err != OK:
		push_error("bundle_packager: flush failed (%d)" % err)
		return 8
	print("Built %s -> %s" % [bundle_id, out_path])
	return 0


func _find_bundle_dir(bundle_id: String) -> String:
	# Walk res://content/*/*/bundle.json and find one matching bundle_id.
	var content_root := "res://content"
	var d := DirAccess.open(content_root)
	if d == null:
		return ""
	for kind in d.get_directories():
		var kd := DirAccess.open("%s/%s" % [content_root, kind])
		if kd == null:
			continue
		for sub in kd.get_directories():
			var bj := "%s/%s/%s/bundle.json" % [content_root, kind, sub]
			if FileAccess.file_exists(bj):
				var raw := FileAccess.get_file_as_string(bj)
				var meta: Variant = JSON.parse_string(raw)
				if typeof(meta) == TYPE_DICTIONARY and meta.get("id", "") == bundle_id:
					return "%s/%s/%s" % [content_root, kind, sub]
	return ""


func _collect_files(root: String, globs: Array) -> Array[String]:
	var collected: Array[String] = []
	_walk(root, collected)
	if globs.is_empty():
		return collected
	var matched: Array[String] = []
	for f in collected:
		for g in globs:
			if f.match("%s/%s" % [root, g]):
				matched.append(f)
				break
	return matched


func _walk(dir_path: String, acc: Array[String]) -> void:
	var d := DirAccess.open(dir_path)
	if d == null:
		return
	d.list_dir_begin()
	var name := d.get_next()
	while name != "":
		if name.begins_with("."):
			name = d.get_next(); continue
		var full := "%s/%s" % [dir_path, name]
		if d.current_is_dir():
			_walk(full, acc)
		else:
			# Skip Godot's bookkeeping that should not ship in PCKs.
			if not (name.ends_with(".import") or name == "bundle.json"):
				acc.append(full)
		name = d.get_next()
	d.list_dir_end()
