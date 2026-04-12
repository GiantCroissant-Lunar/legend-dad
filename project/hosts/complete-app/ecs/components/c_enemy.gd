class_name C_Enemy
extends Component

## Identifies which enemy type this is (indexes into BattleData.ENEMIES).
@export var enemy_type: String = "slime"

func _init(p_type: String = "slime"):
	enemy_type = p_type
