class_name S_Interaction
extends System

func query() -> QueryBuilder:
	return q.with_all([C_PlayerControlled, C_GridPosition, C_TimelineEra])

func process(entities: Array[Entity], _components: Array, _delta: float) -> void:
	if not Input.is_action_just_pressed("ui_accept"):
		return

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

func _activate(entity: Entity, interactable: C_Interactable) -> void:
	interactable.state = C_Interactable.InteractState.ACTIVATED
	entity.visible = false

	var link = entity.get_component(C_TimelineLinked) as C_TimelineLinked
	if not link or link.linked_entity_id.is_empty():
		return

	var all_linked = ECS.world.query.with_all([C_TimelineLinked, C_Interactable]).execute()
	for linked_entity in all_linked:
		if linked_entity.id == link.linked_entity_id:
			var linked_interact = linked_entity.get_component(C_Interactable) as C_Interactable
			linked_interact.state = C_Interactable.InteractState.ACTIVATED
			linked_entity.visible = false
			break
