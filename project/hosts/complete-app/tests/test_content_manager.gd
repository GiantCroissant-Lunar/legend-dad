# project/hosts/complete-app/tests/test_content_manager.gd
extends GutTest

const ContentManagerScript = preload("res://scripts/content_manager.gd")

var _cm

func before_each() -> void:
	_cm = ContentManagerScript.new()
	add_child_autofree(_cm)

func test_load_manifest_from_dictionary() -> void:
	_cm.load_manifest_dict({
		"schema_version": 1,
		"bundles": {
			"hud-core": {
				"kind": "hud",
				"policy": "eager",
				"pck": "hud-core@aaa.pck",
				"deps": []
			}
		}
	})
	assert_eq(_cm.describe("hud-core")["kind"], "hud")
	assert_false(_cm.is_loaded("hud-core"))

func test_describe_unknown_bundle_returns_empty() -> void:
	_cm.load_manifest_dict({"schema_version": 1, "bundles": {}})
	assert_eq(_cm.describe("does-not-exist"), {})

func test_dependency_loaded_before_dependent() -> void:
	var loaded_order: Array[String] = []
	_cm.bundle_loaded.connect(func(id): loaded_order.append(id))
	_cm.load_manifest_dict({
		"schema_version": 1,
		"bundles": {
			"base": {"kind": "hud", "policy": "lazy", "pck": "base@1.pck", "deps": []},
			"child": {"kind": "hud", "policy": "lazy", "pck": "child@1.pck", "deps": ["base"]}
		}
	})
	# Stub the actual PCK loader so we test ordering, not file IO.
	_cm._test_pck_loader = func(_path: String) -> bool: return true
	_cm.load_bundle("child")
	assert_eq(loaded_order, ["base", "child"])

func test_unload_refused_when_dependent_loaded() -> void:
	_cm.load_manifest_dict({
		"schema_version": 1,
		"bundles": {
			"base": {"kind": "hud", "policy": "lazy", "pck": "base@1.pck", "deps": []},
			"child": {"kind": "hud", "policy": "lazy", "pck": "child@1.pck", "deps": ["base"]}
		}
	})
	_cm._test_pck_loader = func(_p): return true
	_cm.load_bundle("child")
	var ok := _cm.unload_bundle("base")
	assert_false(ok, "should refuse to unload base while child is loaded")
	assert_true(_cm.is_loaded("base"))

func test_load_failed_signal_when_pck_missing() -> void:
	_cm.load_manifest_dict({
		"schema_version": 1,
		"bundles": {
			"missing": {"kind": "hud", "policy": "lazy", "pck": "missing@1.pck", "deps": []}
		}
	})
	_cm._test_pck_loader = func(_p): return false
	var failed_with: Array = []
	_cm.bundle_load_failed.connect(func(id, reason): failed_with.append([id, reason]))
	var ok := _cm.load_bundle("missing")
	assert_false(ok)
	assert_eq(failed_with.size(), 1)
	assert_eq(failed_with[0][0], "missing")
