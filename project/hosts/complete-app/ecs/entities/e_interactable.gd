class_name E_Interactable
extends Entity

@export var era: C_TimelineEra.Era = C_TimelineEra.Era.FATHER
@export var start_col: int = 0
@export var start_row: int = 0
@export var interact_type: C_Interactable.InteractType = C_Interactable.InteractType.BOULDER
@export var linked_id: String = ""

const TILE_SIZE := 32
const BOULDER_COLOR := Color(0.5, 0.5, 0.5)  # Gray
const BLOCKED_COLOR := Color(0.4, 0.2, 0.2)  # Dark red

func define_components() -> Array:
	return [
		C_TimelineEra.new(era),
		C_GridPosition.new(start_col, start_row),
		C_Interactable.new(interact_type),
		C_TimelineLinked.new(linked_id),
	]

func on_ready():
	var grid_pos = get_component(C_GridPosition) as C_GridPosition
	if grid_pos:
		position = Vector2(grid_pos.col * TILE_SIZE, grid_pos.row * TILE_SIZE)

func _draw() -> void:
	var interactable = get_component(C_Interactable) as C_Interactable
	if not interactable or interactable.state == C_Interactable.InteractState.ACTIVATED:
		return
	var color = BOULDER_COLOR if era == C_TimelineEra.Era.FATHER else BLOCKED_COLOR
	draw_circle(Vector2(TILE_SIZE / 2.0, TILE_SIZE / 2.0), TILE_SIZE / 3.0, color)

func _process(_delta: float) -> void:
	queue_redraw()
