# project/hosts/content-app/preview/mock_kernel.gd
##
## Stand-in for kernel autoloads (ContentManager, GameActions, WS) when
## running preview scenes from content-app. Attach as the first child of any
## preview root scene; later scripts can call MockKernel.cm.load_bundle(...)
## etc. without a real complete-app runtime.
extends Node


class MockContentManager extends RefCounted:
	signal bundle_loading(id: String)
	signal bundle_loaded(id: String)
	signal bundle_load_failed(id: String, reason: String)
	signal bundle_unloaded(id: String)
	func load_bundle(id: String) -> bool:
		emit_signal("bundle_loading", id)
		emit_signal("bundle_loaded", id)
		return true
	func unload_bundle(id: String) -> bool:
		emit_signal("bundle_unloaded", id)
		return true
	func is_loaded(_id: String) -> bool:
		return true
	func loaded_bundles() -> Array[String]:
		return []
	func describe(_id: String) -> Dictionary:
		return {}
	func get_enemy_definition(id: String) -> Resource:
		var p := "res://content/enemies/enemies-forest/%s.tres" % id
		return load(p) if ResourceLoader.exists(p) else null
	func get_npc_definition(id: String) -> Resource:
		var p := "res://content/npcs/npcs-thornwall/%s.tres" % id
		return load(p) if ResourceLoader.exists(p) else null
	func get_hud_widget(id: String) -> Resource:
		var p := "res://content/hud/hud-core/%s.tres" % id
		return load(p) if ResourceLoader.exists(p) else null
	func get_item_definition(id: String) -> Resource:
		var p := "res://content/items/items-common/%s.tres" % id
		return load(p) if ResourceLoader.exists(p) else null


class MockGameActions extends RefCounted:
	signal action_move(direction: Vector2i)
	signal action_interact()
	signal action_switch_era()


var cm: MockContentManager
var actions: MockGameActions


func _init() -> void:
	cm = MockContentManager.new()
	actions = MockGameActions.new()
