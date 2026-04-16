class_name ProgressionManager
extends Node
## Manages XP accumulation and level-up for party combatants.
## Curves are loaded from ContentManager at startup; award_xp is called
## after each battle victory via main.gd._on_battle_ended.

signal level_up(combatant: Combatant, old_level: int, new_level: int)

# Curve pairs per character slug. Set by main.gd or tests.
var xp_curves: Dictionary = {}     # "father" → LevelCurve (xp_to_level)
var stat_curves: Dictionary = {}   # "father" → LevelCurve (stat_growth)
var xp_totals: Dictionary = {}     # combatant_name → total XP


func award_xp(combatant: Combatant, amount: int) -> void:
	var key := combatant.combatant_name
	var current_xp: int = int(xp_totals.get(key, 0)) + amount
	xp_totals[key] = current_xp

	# Find the XP curve for this combatant's character type
	var xp_curve: LevelCurve = _find_curve(xp_curves, key)
	if xp_curve == null:
		return

	var new_level := xp_curve.level_for_xp(current_xp)
	if new_level > combatant.level:
		var old_level := combatant.level
		combatant.level = new_level
		_apply_stat_growth(combatant, new_level)
		level_up.emit(combatant, old_level, new_level)


func get_xp(combatant_name: String) -> int:
	return int(xp_totals.get(combatant_name, 0))


func _apply_stat_growth(combatant: Combatant, level: int) -> void:
	var stat_curve: LevelCurve = _find_curve(stat_curves, combatant.combatant_name)
	if stat_curve == null:
		return
	var old_max_hp := combatant.max_hp
	combatant.max_hp = stat_curve.stat_at_level("max_hp", level)
	combatant.max_mp = stat_curve.stat_at_level("max_mp", level)
	combatant.atk = stat_curve.stat_at_level("atk", level)
	combatant.def = stat_curve.stat_at_level("def", level)
	combatant.spd = stat_curve.stat_at_level("spd", level)
	# Level-up fully heals to new max (DQ1 style)
	combatant.hp += (combatant.max_hp - old_max_hp)
	combatant.hp = mini(combatant.hp, combatant.max_hp)


func _find_curve(curves: Dictionary, combatant_name: String) -> LevelCurve:
	# Try exact name match first, then lowercase
	if curves.has(combatant_name):
		return curves[combatant_name]
	var lower := combatant_name.to_lower()
	if curves.has(lower):
		return curves[lower]
	return null
