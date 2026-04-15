# project/hosts/content-app/preview/preview_hud.gd
extends Control

const MockKernel := preload("res://preview/mock_kernel.gd")

@export var widget_id: String = "activity_log_panel"

@onready var _slot: Control = $Slot
@onready var _id_input: LineEdit = $Toolbar/IdInput

var _kernel: MockKernel


func _ready() -> void:
	_kernel = MockKernel.new()
	add_child(_kernel)
	_id_input.text = widget_id
	_id_input.text_submitted.connect(_on_id_submitted)
	_load(widget_id)


func _on_id_submitted(new_id: String) -> void:
	_load(new_id)


func _load(id: String) -> void:
	for c in _slot.get_children():
		c.queue_free()
	var widget_def: Resource = _kernel.cm.get_hud_widget(id)
	if widget_def == null:
		push_warning("preview_hud: no widget definition for %s" % id)
		return
	if widget_def.has_method("get") and widget_def.get("scene") != null:
		var inst: Node = (widget_def.scene as PackedScene).instantiate()
		_slot.add_child(inst)
