class_name C_GridPosition
extends Component

@export var col: int = 0
@export var row: int = 0
@export var facing: Vector2i = Vector2i.DOWN

func _init(p_col: int = 0, p_row: int = 0):
	col = p_col
	row = p_row
