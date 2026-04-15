# project/hosts/content-app/preview/preview_combat.gd
##
## Loads an enemy by id, plops it in a fake arena, and lets you trigger fake
## combat actions via toolbar buttons. mock_kernel.actions emits signals so
## any HUD widgets that subscribe to GameActions will react.
extends Control

const MockKernel := preload("res://preview/mock_kernel.gd")

@export var enemy_id: String = "goblin"

@onready var _enemy_slot: Control = $EnemySlot
@onready var _id_input: LineEdit = $Toolbar/IdInput
@onready var _attack_btn: Button = $Toolbar/AttackBtn

var _kernel: MockKernel


func _ready() -> void:
	_kernel = MockKernel.new()
	add_child(_kernel)
	_id_input.text = enemy_id
	_id_input.text_submitted.connect(func(s): _load_enemy(s))
	_attack_btn.pressed.connect(func(): _kernel.actions.emit_signal("action_interact"))
	_load_enemy(enemy_id)


func _load_enemy(id: String) -> void:
	for c in _enemy_slot.get_children():
		c.queue_free()
	var def: Resource = _kernel.cm.get_enemy_definition(id)
	if def == null:
		push_warning("preview_combat: no enemy %s" % id)
		return
	var sprite := TextureRect.new()
	if def.get("sprite") != null:
		sprite.texture = def.sprite
	sprite.custom_minimum_size = Vector2(128, 128)
	_enemy_slot.add_child(sprite)
	var name_label := Label.new()
	name_label.text = "%s (HP %d)" % [def.get("display_name"), def.get("max_hp")]
	_enemy_slot.add_child(name_label)
