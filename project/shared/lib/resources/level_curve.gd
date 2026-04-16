extends Resource
class_name LevelCurve
## Progression curve for XP→level, stat growth, or monster scaling.
## Authored in vault (curves/*.md) → articy → adapter-generated .tres.
## Consumed by ProgressionManager (xp/stat) and encounter spawn (scaling).

@export var kind: String = ""         # "xp_to_level" | "stat_growth" | "monster_scaling"
@export var applies_to: String = ""   # "father" | "son" | "" (monster_scaling)
@export var data_points: Array = []   # [{level, xp_required?, max_hp?, atk?, ...}]


## XP curves: return the highest level whose xp_required <= xp.
func level_for_xp(xp: int) -> int:
	if data_points.is_empty():
		return 1
	var result := int(data_points[0].get("level", 1))
	for dp in data_points:
		if xp >= int(dp.get("xp_required", 0)):
			result = int(dp.get("level", result))
	return result


## Stat/scaling curves: linearly interpolate a stat value at the given level.
func stat_at_level(stat: String, level: int) -> int:
	var sorted_pts := data_points.duplicate()
	sorted_pts.sort_custom(func(a, b): return int(a.get("level", 0)) < int(b.get("level", 0)))
	if sorted_pts.is_empty():
		return 0
	# Clamp to bounds
	if level <= int(sorted_pts[0].get("level", 1)):
		return int(sorted_pts[0].get(stat, 0))
	if level >= int(sorted_pts[-1].get("level", 1)):
		return int(sorted_pts[-1].get(stat, 0))
	# Interpolate between bracketing points
	for i in range(sorted_pts.size() - 1):
		var lo = sorted_pts[i]
		var hi = sorted_pts[i + 1]
		var lo_lvl = int(lo.get("level", 0))
		var hi_lvl = int(hi.get("level", 0))
		if level >= lo_lvl and level <= hi_lvl:
			var lo_val = int(lo.get(stat, 0))
			var hi_val = int(hi.get(stat, 0))
			var t = float(level - lo_lvl) / float(hi_lvl - lo_lvl)
			return int(round(lo_val + (hi_val - lo_val) * t))
	return int(sorted_pts[-1].get(stat, 0))
