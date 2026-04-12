class_name C_TimelineLinked
extends Component

## The entity ID of the linked counterpart in the other era.
@export var linked_entity_id: String = ""

func _init(p_linked_id: String = ""):
	linked_entity_id = p_linked_id
