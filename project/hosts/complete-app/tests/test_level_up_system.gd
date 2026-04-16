# project/hosts/complete-app/tests/test_level_up_system.gd
#
# Covers ProgressionManager.award_xp — XP accumulation, level-up
# detection, stat growth application, and signal emission.
extends GutTest

const ProgressionManagerScript = preload("res://scripts/progression/progression_manager.gd")
const LevelCurveScript = preload("res://lib/resources/level_curve.gd")

var _pm: ProgressionManager


func _xp_curve_stub() -> LevelCurve:
	var c: LevelCurve = LevelCurveScript.new()
	c.kind = "xp_to_level"
	c.data_points = [
		{"level": 1, "xp_required": 0},
		{"level": 2, "xp_required": 10},
		{"level": 3, "xp_required": 30},
	]
	return c


func _stat_curve_stub() -> LevelCurve:
	var c: LevelCurve = LevelCurveScript.new()
	c.kind = "stat_growth"
	c.data_points = [
		{"level": 1, "max_hp": 20, "max_mp": 8, "atk": 8, "def": 4, "spd": 6},
		{"level": 2, "max_hp": 30, "max_mp": 12, "atk": 12, "def": 6, "spd": 7},
		{"level": 3, "max_hp": 42, "max_mp": 16, "atk": 16, "def": 8, "spd": 8},
	]
	return c


func before_each() -> void:
	_pm = ProgressionManagerScript.new()
	add_child_autofree(_pm)
	_pm.xp_curves = {"Father": _xp_curve_stub()}
	_pm.stat_curves = {"Father": _stat_curve_stub()}


func test_award_xp_triggers_level_up_when_threshold_crossed() -> void:
	var c := Combatant.from_dict({"name": "Father", "level": 1, "max_hp": 20, "hp": 20, "atk": 8})
	var events := []
	_pm.level_up.connect(func(comb, old_level, new_level): events.append([old_level, new_level]))
	_pm.award_xp(c, 15)  # crosses level 2 threshold (10)
	assert_eq(c.level, 2, "combatant must level up from 1 to 2")
	assert_eq(events.size(), 1)
	assert_eq(events[0], [1, 2])


func test_award_xp_applies_stat_growth() -> void:
	var c := Combatant.from_dict({"name": "Father", "level": 1, "max_hp": 20, "hp": 20, "atk": 8})
	_pm.award_xp(c, 15)
	assert_eq(c.max_hp, 30)
	assert_eq(c.atk, 12)
	assert_eq(c.hp, 30, "level-up heals to new max HP")


func test_award_xp_accumulates_across_calls() -> void:
	var c := Combatant.from_dict({"name": "Father", "level": 1, "max_hp": 20, "hp": 20})
	_pm.award_xp(c, 5)
	assert_eq(c.level, 1, "5 XP not enough for level 2")
	_pm.award_xp(c, 6)  # total 11 → level 2
	assert_eq(c.level, 2)
	assert_eq(_pm.get_xp("Father"), 11)


func test_award_xp_no_curve_does_not_crash() -> void:
	_pm.xp_curves = {}
	var c := Combatant.from_dict({"name": "Father", "level": 1, "max_hp": 20, "hp": 20})
	_pm.award_xp(c, 100)
	assert_eq(c.level, 1, "no curve = no level change")


func test_award_xp_multi_level_jump() -> void:
	var c := Combatant.from_dict({"name": "Father", "level": 1, "max_hp": 20, "hp": 20})
	_pm.award_xp(c, 50)  # crosses both L2 (10) and L3 (30)
	assert_eq(c.level, 3)
	assert_eq(c.max_hp, 42)
