# project/hosts/content-app/preview/preview_main.gd
extends Control

const PREVIEWS := {
	"HUD": "res://preview/preview_hud.tscn",
	"Combat": "res://preview/preview_combat.tscn",
}

@onready var _list: VBoxContainer = $List


func _ready() -> void:
	for label in PREVIEWS.keys():
		var btn := Button.new()
		btn.text = label
		btn.pressed.connect(func(): _open(PREVIEWS[label]))
		_list.add_child(btn)


func _open(scene_path: String) -> void:
	get_tree().change_scene_to_file(scene_path)
