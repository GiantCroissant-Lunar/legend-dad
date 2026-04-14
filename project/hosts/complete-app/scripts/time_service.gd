class_name TimeServiceClass
extends Node

## Wraps Engine.time_scale with pause/resume/frame-step for diagnostics.
## Must use PROCESS_MODE_ALWAYS so it ticks even when time_scale = 0.

var _current_speed: float = 1.0
var _saved_speed: float = 1.0
var _paused: bool = false
var _step_requested: bool = false
var _step_active: bool = false

const MIN_SPEED := 0.25
const MAX_SPEED := 4.0

func _ready() -> void:
	process_mode = Node.PROCESS_MODE_ALWAYS

func _process(_delta: float) -> void:
	if _step_requested:
		Engine.time_scale = _saved_speed
		_step_requested = false
		_step_active = true
	elif _step_active:
		Engine.time_scale = 0.0
		_step_active = false

func set_speed(multiplier: float) -> void:
	var clamped := clampf(multiplier, MIN_SPEED, MAX_SPEED)
	_current_speed = clamped
	if not _paused:
		Engine.time_scale = clamped

func pause() -> void:
	if _paused:
		return
	_saved_speed = _current_speed
	_paused = true
	Engine.time_scale = 0.0

func resume() -> void:
	if not _paused:
		return
	_paused = false
	_step_requested = false
	_step_active = false
	Engine.time_scale = _saved_speed

func step_frame() -> void:
	if not _paused:
		return
	_step_requested = true

func get_state() -> Dictionary:
	return {
		"paused": _paused,
		"speed": _current_speed,
	}
