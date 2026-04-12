class_name E_Interactable
extends Entity

@export var era: C_TimelineEra.Era = C_TimelineEra.Era.FATHER
@export var start_col: int = 0
@export var start_row: int = 0
@export var interact_type: C_Interactable.InteractType = C_Interactable.InteractType.BOULDER
@export var linked_id: String = ""

func define_components() -> Array:
	return [
		C_TimelineEra.new(era),
		C_GridPosition.new(start_col, start_row),
		C_Interactable.new(interact_type),
		C_TimelineLinked.new(linked_id),
	]
