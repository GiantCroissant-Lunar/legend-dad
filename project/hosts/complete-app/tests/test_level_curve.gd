# project/hosts/complete-app/tests/test_level_curve.gd
#
# Covers LevelCurve.level_for_xp and stat_at_level — the pure lookup
# functions used by ProgressionManager for XP→level and stat growth.
extends GutTest

const LevelCurveScript = preload("res://lib/resources/level_curve.gd")


func _make_xp_curve() -> LevelCurve:
	var c: LevelCurve = LevelCurveScript.new()
	c.kind = "xp_to_level"
	c.data_points = [
		{"level": 1, "xp_required": 0},
		{"level": 2, "xp_required": 10},
		{"level": 3, "xp_required": 30},
		{"level": 5, "xp_required": 100},
	]
	return c


func _make_stat_curve() -> LevelCurve:
	var c: LevelCurve = LevelCurveScript.new()
	c.kind = "stat_growth"
	c.data_points = [
		{"level": 1,  "max_hp": 20, "atk": 8},
		{"level": 10, "max_hp": 110, "atk": 26},
	]
	return c


func test_level_for_xp_returns_highest_reached() -> void:
	var c := _make_xp_curve()
	assert_eq(c.level_for_xp(0), 1)
	assert_eq(c.level_for_xp(9), 1)
	assert_eq(c.level_for_xp(10), 2)
	assert_eq(c.level_for_xp(29), 2)
	assert_eq(c.level_for_xp(30), 3)
	assert_eq(c.level_for_xp(100), 5)
	assert_eq(c.level_for_xp(9999), 5, "past max: cap at last data point")


func test_level_for_xp_empty_returns_1() -> void:
	var c: LevelCurve = LevelCurveScript.new()
	c.data_points = []
	assert_eq(c.level_for_xp(999), 1)


func test_stat_at_level_returns_exact_data_point() -> void:
	var c := _make_stat_curve()
	assert_eq(c.stat_at_level("max_hp", 1), 20)
	assert_eq(c.stat_at_level("max_hp", 10), 110)
	assert_eq(c.stat_at_level("atk", 1), 8)
	assert_eq(c.stat_at_level("atk", 10), 26)


func test_stat_at_level_interpolates_linearly() -> void:
	var c := _make_stat_curve()
	# Midpoint: level 5.5 → (20 + 110) / 2 = 65, but level 5 is closer to lo
	# level 5: t = (5-1)/(10-1) = 4/9 ≈ 0.444 → 20 + 90*0.444 = 60
	assert_eq(c.stat_at_level("max_hp", 5), 60)


func test_stat_at_level_clamps_below_min() -> void:
	var c := _make_stat_curve()
	assert_eq(c.stat_at_level("max_hp", 0), 20, "below min level returns first data point")


func test_stat_at_level_clamps_above_max() -> void:
	var c := _make_stat_curve()
	assert_eq(c.stat_at_level("max_hp", 99), 110, "above max level returns last data point")


func test_stat_at_level_missing_stat_returns_0() -> void:
	var c := _make_stat_curve()
	assert_eq(c.stat_at_level("spd", 5), 0, "stat not in data_points returns 0")
