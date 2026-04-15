class_name C_Enemy
extends Component

## Identifies which enemy type this is. The id maps to
## res://content/enemies/enemies-core/{id}.tres via
## ContentManager.get_enemy_definition.
@export var enemy_type: String = "slime"

func _init(p_type: String = "slime"):
	enemy_type = p_type
