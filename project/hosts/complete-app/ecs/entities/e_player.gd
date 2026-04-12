class_name E_Player
extends Entity

@export var era: C_TimelineEra.Era = C_TimelineEra.Era.FATHER
@export var start_col: int = 0
@export var start_row: int = 0

const TILE_SIZE := 32
const FATHER_COLOR := Color(1.0, 0.8, 0.0)  # Gold
const SON_COLOR := Color(0.6, 0.8, 1.0)  # Light blue

func define_components() -> Array:
	return [
		C_TimelineEra.new(era),
		C_GridPosition.new(start_col, start_row),
		C_PlayerControlled.new(era == C_TimelineEra.Era.FATHER),
	]

func on_ready():
	var grid_pos = get_component(C_GridPosition) as C_GridPosition
	if grid_pos:
		position = Vector2(grid_pos.col * TILE_SIZE, grid_pos.row * TILE_SIZE)

func _draw() -> void:
	var color = FATHER_COLOR if era == C_TimelineEra.Era.FATHER else SON_COLOR
	draw_rect(Rect2(4, 4, TILE_SIZE - 8, TILE_SIZE - 8), color)
	var grid_pos = get_component(C_GridPosition) as C_GridPosition
	if grid_pos:
		var center = Vector2(TILE_SIZE / 2.0, TILE_SIZE / 2.0)
		var arrow_end = center + Vector2(grid_pos.facing) * 10.0
		draw_line(center, arrow_end, Color.WHITE, 2.0)

func _process(_delta: float) -> void:
	queue_redraw()
