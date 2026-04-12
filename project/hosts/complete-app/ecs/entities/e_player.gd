class_name E_Player
extends Entity

@export var era: C_TimelineEra.Era = C_TimelineEra.Era.FATHER
@export var start_col: int = 0
@export var start_row: int = 0

func define_components() -> Array:
	return [
		C_TimelineEra.new(era),
		C_GridPosition.new(start_col, start_row),
		C_PlayerControlled.new(era == C_TimelineEra.Era.FATHER),
	]

func on_ready():
	var grid_pos = get_component(C_GridPosition) as C_GridPosition
	if grid_pos:
		position = Vector2(grid_pos.col * 32, grid_pos.row * 32)
