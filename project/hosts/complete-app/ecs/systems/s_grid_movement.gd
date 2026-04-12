class_name S_GridMovement
extends System

const TILE_SIZE := 32
const MOVE_SPEED := 8.0

func query() -> QueryBuilder:
	return q.with_all([C_GridPosition])

func process(entities: Array[Entity], _components: Array, delta: float) -> void:
	for entity in entities:
		var grid_pos = entity.get_component(C_GridPosition) as C_GridPosition
		var target_x = float(grid_pos.col * TILE_SIZE)
		var target_y = float(grid_pos.row * TILE_SIZE)
		grid_pos.visual_x = lerpf(grid_pos.visual_x, target_x, MOVE_SPEED * delta)
		grid_pos.visual_y = lerpf(grid_pos.visual_y, target_y, MOVE_SPEED * delta)
