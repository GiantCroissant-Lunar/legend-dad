class_name S_PlayerInput
extends System

const TILE_SIZE := 32
var move_cooldown := 0.15
var _cooldown_timer := 0.0

func query() -> QueryBuilder:
	return q.with_all([C_PlayerControlled, C_GridPosition, C_TimelineEra])

func process(entities: Array[Entity], _components: Array, delta: float) -> void:
	_cooldown_timer -= delta
	if _cooldown_timer > 0.0:
		return

	var direction := Vector2i.ZERO
	if Input.is_action_pressed("ui_right"):
		direction = Vector2i.RIGHT
	elif Input.is_action_pressed("ui_left"):
		direction = Vector2i.LEFT
	elif Input.is_action_pressed("ui_down"):
		direction = Vector2i.DOWN
	elif Input.is_action_pressed("ui_up"):
		direction = Vector2i.UP

	if direction == Vector2i.ZERO:
		return

	for entity in entities:
		var pc = entity.get_component(C_PlayerControlled) as C_PlayerControlled
		if not pc or not pc.active:
			continue

		var grid_pos = entity.get_component(C_GridPosition) as C_GridPosition
		grid_pos.facing = direction

		var new_col = grid_pos.col + direction.x
		var new_row = grid_pos.row + direction.y

		var era_comp = entity.get_component(C_TimelineEra) as C_TimelineEra
		var tilemap = _get_tilemap_for_era(era_comp.era)
		if tilemap and _is_tile_walkable(tilemap, new_col, new_row):
			if not _is_tile_occupied(new_col, new_row, era_comp.era, entity):
				grid_pos.col = new_col
				grid_pos.row = new_row
				_cooldown_timer = move_cooldown

func _get_tilemap_for_era(era: C_TimelineEra.Era) -> TileMapLayer:
	var world_node = ECS.world as Node
	var meta_key = "father_tilemap" if era == C_TimelineEra.Era.FATHER else "son_tilemap"
	if world_node.has_meta(meta_key):
		return world_node.get_meta(meta_key) as TileMapLayer
	return null

func _is_tile_walkable(tilemap: TileMapLayer, col: int, row: int) -> bool:
	var cell_coords = Vector2i(col, row)
	var source_id = tilemap.get_cell_source_id(cell_coords)
	if source_id == -1:
		return false
	var tile_data = tilemap.get_cell_tile_data(cell_coords)
	if tile_data:
		return tile_data.get_custom_data("walkable") as bool
	return false

func _is_tile_occupied(col: int, row: int, era: C_TimelineEra.Era, exclude: Entity) -> bool:
	var all_entities = ECS.world.query.with_all([C_GridPosition, C_TimelineEra]).execute()
	for e in all_entities:
		if e == exclude:
			continue
		var e_era = e.get_component(C_TimelineEra) as C_TimelineEra
		if e_era.era != era:
			continue
		var e_pos = e.get_component(C_GridPosition) as C_GridPosition
		if e_pos.col == col and e_pos.row == row:
			return true
	return false
