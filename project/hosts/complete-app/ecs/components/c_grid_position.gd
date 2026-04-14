class_name C_GridPosition
extends Component

@export var col: int = 0
@export var row: int = 0
@export var facing: Vector2i = Vector2i.DOWN
## Smooth pixel position for rendering (lerped toward grid target).
@export var visual_x: float = 0.0
@export var visual_y: float = 0.0

func _init(p_col: int = 0, p_row: int = 0):
	col = p_col
	row = p_row
	visual_x = float(p_col * GameConfig.cell_size)
	visual_y = float(p_row * GameConfig.cell_size)
