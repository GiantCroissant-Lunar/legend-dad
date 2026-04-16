extends Resource
class_name EncounterTable
## Zone-scoped weighted pool of monster ids. Authored in vault
## (zones/*.md → encounter_table frontmatter) → articy export →
## adapter-generated .tres. Consumed by main.gd at encounter trigger.

@export var zone_id: String = ""
@export var encounter_rate: float = 0.0
@export var difficulty_tier: int = 1

# Each entry: {bestiary_id: String, weight: int, era: String}.
# `era` is "father" | "son" | "both" — only entries matching the
# current timeline (or "both") are rolled.
@export var entries: Array = []

func roll(current_era: String) -> String:
	var eligible := []
	var total_weight := 0
	for e in entries:
		if e.get("era", "both") == current_era or e.get("era", "both") == "both":
			eligible.append(e)
			total_weight += int(e.get("weight", 1))
	if eligible.is_empty() or total_weight <= 0:
		return ""
	var r := randi() % total_weight
	var acc := 0
	for e in eligible:
		acc += int(e.get("weight", 1))
		if r < acc:
			return str(e.get("bestiary_id", ""))
	return str(eligible[-1].get("bestiary_id", ""))
