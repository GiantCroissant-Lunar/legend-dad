class_name S_PlayerInput
extends System

## Reads hardware input and dispatches to the GameActions bus.
## No longer processes movement directly — S_ActionProcessor handles that.

func query() -> QueryBuilder:
	return q.with_all([C_PlayerControlled])

func process(_entities: Array[Entity], _components: Array, _delta: float) -> void:
	var direction := Vector2i.ZERO
	if Input.is_action_pressed("ui_right"):
		direction = Vector2i.RIGHT
	elif Input.is_action_pressed("ui_left"):
		direction = Vector2i.LEFT
	elif Input.is_action_pressed("ui_down"):
		direction = Vector2i.DOWN
	elif Input.is_action_pressed("ui_up"):
		direction = Vector2i.UP

	if direction != Vector2i.ZERO:
		GameActions.move(direction)

	if Input.is_action_just_pressed("ui_accept") or Input.is_action_just_pressed("interact"):
		GameActions.interact()
