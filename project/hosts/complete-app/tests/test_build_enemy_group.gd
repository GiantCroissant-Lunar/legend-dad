# project/hosts/complete-app/tests/test_build_enemy_group.gd
#
# Covers Main.build_enemy_group — the encounter group builder that rolls
# a count from EnemyDefinition.group_size_min/max and names the
# combatants with A/B/C suffixes when count > 1.
#
# The function is static on Main so GUT can call it without spinning up
# ECS + ContentManager. Enemy definitions are hand-built instead of
# loaded from .tres, so the gate math is deterministic.
extends GutTest

const MainScript = preload("res://scripts/main.gd")
const EnemyDefinitionScript = preload("res://lib/resources/enemy_definition.gd")


func _make_def(fields: Dictionary) -> EnemyDefinition:
	var def: EnemyDefinition = EnemyDefinitionScript.new()
	for key in fields.keys():
		def.set(key, fields[key])
	return def


func test_solo_default_returns_one_combatant_with_base_name() -> void:
	var def := _make_def({
		"id": "boss",
		"display_name": "Boss",
		"max_hp": 100,
		"attack": 20,
		"defense": 10,
	})
	# group_size_min/max default to 1.
	var group := MainScript.build_enemy_group(def)
	assert_eq(group.size(), 1, "default 1-1 group → exactly one combatant")
	assert_eq(group[0].combatant_name, "Boss", "solo encounter keeps base name — no 'A' suffix")
	assert_true(group[0].is_enemy, "combatants must be marked as enemies")


func test_multi_enemy_group_gets_letter_suffixes_in_order() -> void:
	var def := _make_def({
		"id": "slime",
		"display_name": "Slime",
		"max_hp": 12,
		"attack": 5,
		"group_size_min": 3,
		"group_size_max": 3,  # pin to 3 for deterministic assert
	})
	var group := MainScript.build_enemy_group(def)
	assert_eq(group.size(), 3)
	assert_eq(group[0].combatant_name, "Slime A")
	assert_eq(group[1].combatant_name, "Slime B")
	assert_eq(group[2].combatant_name, "Slime C")


func test_group_of_one_skips_the_suffix_even_when_range_allows_more() -> void:
	# group_size_min=1 means the roll CAN produce a solo encounter even
	# for enemies that commonly run in packs. When that happens, no
	# suffix — reads naturally as "A Slime attacks".
	var def := _make_def({
		"id": "slime",
		"display_name": "Slime",
		"group_size_min": 1,
		"group_size_max": 1,  # force the 1-roll path
	})
	var group := MainScript.build_enemy_group(def)
	assert_eq(group.size(), 1)
	assert_eq(group[0].combatant_name, "Slime", "solo roll must not append 'A'")


func test_group_size_clamps_when_min_exceeds_max() -> void:
	# Defensive: if a .tres accidentally has min=3 max=1, clamp to max=min.
	var def := _make_def({
		"id": "weird",
		"display_name": "Weird",
		"group_size_min": 3,
		"group_size_max": 1,
	})
	var group := MainScript.build_enemy_group(def)
	assert_eq(group.size(), 3, "min overrides max when backwards — ensures a valid roll")


func test_group_size_floors_at_one_when_min_is_zero() -> void:
	var def := _make_def({
		"id": "weird",
		"display_name": "Weird",
		"group_size_min": 0,
		"group_size_max": 0,
	})
	var group := MainScript.build_enemy_group(def)
	assert_eq(group.size(), 1, "0-0 is nonsensical; floor at 1 so encounter never spawns empty")


func test_null_def_returns_empty_group() -> void:
	var group := MainScript.build_enemy_group(null)
	assert_eq(group.size(), 0, "null def → empty array, caller falls through to whatever fallback")


func test_group_stats_come_from_def_to_combat_dict() -> void:
	# Sanity: each generated combatant inherits HP/atk/def from the shared def.
	var def := _make_def({
		"id": "slime",
		"display_name": "Slime",
		"max_hp": 12,
		"attack": 5,
		"defense": 2,
		"spd": 3,
		"xp_reward": 4,
		"gold_reward": 3,
		"group_size_min": 2,
		"group_size_max": 2,
	})
	var group := MainScript.build_enemy_group(def)
	for c in group:
		assert_eq(c.max_hp, 12)
		assert_eq(c.hp, 12, "spawns at full HP")
		assert_eq(c.atk, 5)
		assert_eq(c.def, 2)
		assert_eq(c.exp_reward, 4)
		assert_eq(c.gold_reward, 3)


# --- Phase 2B: Difficulty-tier scaling ---

const LevelCurveScript = preload("res://lib/resources/level_curve.gd")

func _stub_scaling_curve() -> LevelCurve:
	var c: LevelCurve = LevelCurveScript.new()
	c.kind = "monster_scaling"
	c.data_points = [
		{"level": 1, "level_offset": 0},
		{"level": 2, "level_offset": 1},
		{"level": 5, "level_offset": 5},
	]
	return c


func test_build_enemy_group_tier_1_no_scaling() -> void:
	var def := _make_def({
		"id": "slime", "display_name": "Slime", "max_hp": 12, "attack": 5,
		"group_size_min": 1, "group_size_max": 1,
	})
	var scaling := _stub_scaling_curve()
	var group := MainScript.build_enemy_group(def, 1, scaling)
	assert_eq(group[0].max_hp, 12, "tier 1 = no scaling")


func test_build_enemy_group_tier_2_scales_stats() -> void:
	var def := _make_def({
		"id": "slime", "display_name": "Slime", "max_hp": 12, "attack": 5,
		"defense": 2, "level": 1,
		"group_size_min": 1, "group_size_max": 1,
	})
	var scaling := _stub_scaling_curve()
	var group := MainScript.build_enemy_group(def, 2, scaling)
	# level_offset=1 at tier 2 → +10% HP = ceil(12 * 1.1) = 14
	assert_gt(group[0].max_hp, 12, "tier 2 must scale HP above base")
	assert_gt(group[0].atk, 5, "tier 2 must scale ATK above base")
