class_name C_TimelineEra
extends Component

const Era = TimelineEra.Era  # alias for callers that referenced C_TimelineEra.Era

@export var era: int = Era.FATHER

func _init(p_era: int = Era.FATHER):
	era = p_era
