class_name S_GridMovement
extends System

func query() -> QueryBuilder:
	return q.with_all([C_GridPosition])

func process(entities: Array[Entity], _components: Array, delta: float) -> void:
	var cs := GameConfig.cell_size
	for entity in entities:
		var grid_pos = entity.get_component(C_GridPosition) as C_GridPosition
		var target_x = float(grid_pos.col * cs)
		var target_y = float(grid_pos.row * cs)
		grid_pos.visual_x = lerpf(grid_pos.visual_x, target_x, GameConfig.move_speed * delta)
		grid_pos.visual_y = lerpf(grid_pos.visual_y, target_y, GameConfig.move_speed * delta)
