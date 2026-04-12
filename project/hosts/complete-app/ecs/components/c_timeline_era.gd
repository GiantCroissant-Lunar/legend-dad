class_name C_TimelineEra
extends Component

enum Era { FATHER, SON }

@export var era: Era = Era.FATHER

func _init(p_era: Era = Era.FATHER):
	era = p_era
