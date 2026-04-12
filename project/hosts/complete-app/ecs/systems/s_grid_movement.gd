class_name S_GridMovement
extends System

const TILE_SIZE := 32
const MOVE_SPEED := 8.0

func query() -> QueryBuilder:
	return q.with_all([C_GridPosition])

func process(entities: Array[Entity], _components: Array, delta: float) -> void:
	for entity in entities:
		var grid_pos = entity.get_component(C_GridPosition) as C_GridPosition
		var target = Vector2(grid_pos.col * TILE_SIZE, grid_pos.row * TILE_SIZE)
		entity.position = entity.position.lerp(target, MOVE_SPEED * delta)
