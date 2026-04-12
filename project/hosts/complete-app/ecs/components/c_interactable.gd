class_name C_Interactable
extends Component

enum InteractType { BOULDER, SWITCH }
enum InteractState { DEFAULT, ACTIVATED }

@export var type: InteractType = InteractType.BOULDER
@export var state: InteractState = InteractState.DEFAULT

func _init(p_type: InteractType = InteractType.BOULDER):
	type = p_type
	state = InteractState.DEFAULT
