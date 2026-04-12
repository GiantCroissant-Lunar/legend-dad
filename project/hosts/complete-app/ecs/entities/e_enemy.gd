class_name E_Enemy
extends Entity

@export var era: C_TimelineEra.Era = C_TimelineEra.Era.FATHER
@export var start_col: int = 0
@export var start_row: int = 0
@export var enemy_type: String = "slime"

func define_components() -> Array:
	return [
		C_TimelineEra.new(era),
		C_GridPosition.new(start_col, start_row),
		C_Enemy.new(enemy_type),
	]
