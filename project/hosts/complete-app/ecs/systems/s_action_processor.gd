class_name S_ActionProcessor
extends System

## Processes semantic actions from the GameActions bus.
## Handles movement (with cooldown) and interactions.

const TILE_SIZE := 32
var move_cooldown := 0.15
var _cooldown_timer := 0.0
var _pending_move := Vector2i.ZERO
var _pending_interact := false

func _init() -> void:
	GameActions.action_move.connect(_on_move)
	GameActions.action_interact.connect(_on_interact)

func _on_move(direction: Vector2i) -> void:
	_pending_move = direction

func _on_interact() -> void:
	_pending_interact = true

func query() -> QueryBuilder:
	return q.with_all([C_PlayerControlled, C_GridPosition, C_TimelineEra])

func process(entities: Array[Entity], _components: Array, delta: float) -> void:
	_cooldown_timer -= delta

	if _pending_move != Vector2i.ZERO and _cooldown_timer <= 0.0:
		_process_move(entities, _pending_move)
		_pending_move = Vector2i.ZERO

	if _pending_interact:
		_process_interact(entities)
		_pending_interact = false

func _process_move(entities: Array[Entity], direction: Vector2i) -> void:
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
				# Emit state change for WS
				GameActions.state_changed.emit("entity_updated", {
					"entity_id": entity.name,
					"components": {
						"grid_position": { "col": grid_pos.col, "row": grid_pos.row, "facing": _vec2i_to_string(grid_pos.facing) },
					},
				})

func _process_interact(entities: Array[Entity]) -> void:
	for entity in entities:
		var pc = entity.get_component(C_PlayerControlled) as C_PlayerControlled
		if not pc or not pc.active:
			continue

		var grid_pos = entity.get_component(C_GridPosition) as C_GridPosition
		var era_comp = entity.get_component(C_TimelineEra) as C_TimelineEra

		var target_col = grid_pos.col + grid_pos.facing.x
		var target_row = grid_pos.row + grid_pos.facing.y

		var interactables = ECS.world.query.with_all([
			C_Interactable, C_GridPosition, C_TimelineEra
		]).execute()

		for target_entity in interactables:
			var t_era = target_entity.get_component(C_TimelineEra) as C_TimelineEra
			if t_era.era != era_comp.era:
				continue
			var t_pos = target_entity.get_component(C_GridPosition) as C_GridPosition
			if t_pos.col != target_col or t_pos.row != target_row:
				continue

			var interactable = target_entity.get_component(C_Interactable) as C_Interactable
			if interactable.state == C_Interactable.InteractState.DEFAULT:
				_activate(target_entity, interactable)
			break

func _activate(_entity: Entity, interactable: C_Interactable) -> void:
	interactable.state = C_Interactable.InteractState.ACTIVATED

	var link = _entity.get_component(C_TimelineLinked) as C_TimelineLinked
	var linked_id := ""
	if link and not link.linked_entity_id.is_empty():
		linked_id = link.linked_entity_id

	# Emit state change for WS
	GameActions.state_changed.emit("interaction_result", {
		"entity_id": _entity.name,
		"interactable_type": "BOULDER" if interactable.type == C_Interactable.InteractType.BOULDER else "SWITCH",
		"new_state": "ACTIVATED",
		"linked_entity_id": linked_id,
	})

	if linked_id.is_empty():
		return

	var all_linked = ECS.world.query.with_all([C_TimelineLinked, C_Interactable]).execute()
	for linked_entity in all_linked:
		if linked_entity.id == linked_id:
			var linked_interact = linked_entity.get_component(C_Interactable) as C_Interactable
			linked_interact.state = C_Interactable.InteractState.ACTIVATED
			break

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

func _vec2i_to_string(v: Vector2i) -> String:
	if v == Vector2i.UP: return "up"
	if v == Vector2i.DOWN: return "down"
	if v == Vector2i.LEFT: return "left"
	if v == Vector2i.RIGHT: return "right"
	return "down"
