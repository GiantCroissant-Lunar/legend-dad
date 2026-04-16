# project/hosts/complete-app/tests/test_zone_encounter_wiring.gd
#
# Verifies the zone-encounter routing contract:
#   LocationManager.get_current_zone() + Main.roll_zone_encounter_from_table()
#
# Does NOT drive the full _start_battle pipeline — that requires the ECS
# world, ContentManager bundles, and a battle overlay, none of which are
# in scope for a unit test. Instead, exercises the public surface so a
# future regression in zone_id plumbing fails here before it reaches
# combat.
extends GutTest

const MainScript = preload("res://scripts/main.gd")
const EncounterTableScript = preload("res://lib/resources/encounter_table.gd")
const LevelCurveScript = preload("res://lib/resources/level_curve.gd")
const LocationManagerScript = preload("res://scripts/location_manager.gd")


func _make_table(zone: String, tier: int, entries: Array) -> EncounterTable:
	var tbl: EncounterTable = EncounterTableScript.new()
	tbl.zone_id = zone
	tbl.difficulty_tier = tier
	tbl.entries = entries
	return tbl


func _scaling_curve() -> LevelCurve:
	var c: LevelCurve = LevelCurveScript.new()
	c.kind = "monster_scaling"
	c.data_points = [
		{"level": 1, "level_offset": 0},
		{"level": 3, "level_offset": 2},
		{"level": 5, "level_offset": 5},
	]
	return c


# --- LocationManager zone tracking ---

func test_location_manager_zone_starts_empty() -> void:
	var lm: LocationManagerClass = LocationManagerScript.new()
	add_child_autofree(lm)
	assert_eq(lm.get_current_zone(), "", "freshly constructed LocationManager has no zone")


func test_location_manager_set_get_current_zone_round_trip() -> void:
	var lm: LocationManagerClass = LocationManagerScript.new()
	add_child_autofree(lm)
	lm.set_current_zone("whispering_woods_edge")
	assert_eq(lm.get_current_zone(), "whispering_woods_edge")
	lm.set_current_zone("")
	assert_eq(lm.get_current_zone(), "", "setting empty zone must clear tracking")


# --- Main.roll_zone_encounter_from_table routing ---

func test_null_table_returns_empty() -> void:
	var out := MainScript.roll_zone_encounter_from_table(null, "son", null)
	assert_eq(out.size(), 0, "null table must short-circuit to empty array")


func test_table_with_no_era_matches_returns_empty() -> void:
	# Table has only father-era entries; rolling for son era finds nothing.
	var tbl := _make_table("test_zone", 1, [
		{"bestiary_id": "slime", "weight": 10, "era": "father"},
	])
	var out := MainScript.roll_zone_encounter_from_table(tbl, "son", null)
	assert_eq(out.size(), 0, "era-filtered roll with no matches returns empty")


func test_empty_entries_table_returns_empty() -> void:
	var tbl := _make_table("test_zone", 1, [])
	var out := MainScript.roll_zone_encounter_from_table(tbl, "both", null)
	assert_eq(out.size(), 0)


func test_roll_miss_in_content_manager_returns_empty() -> void:
	# ContentManager has no bundles loaded in the GUT harness, so any
	# bestiary_id the roll produces resolves to null. The routing must
	# treat that as "no encounter" rather than crashing.
	var tbl := _make_table("test_zone", 1, [
		{"bestiary_id": "does_not_exist", "weight": 10, "era": "both"},
	])
	var out := MainScript.roll_zone_encounter_from_table(tbl, "both", null)
	assert_eq(out.size(), 0, "unknown bestiary_id must fall through to empty")


func test_difficulty_tier_propagates_from_table() -> void:
	# Even with ContentManager empty (enemy_def=null -> empty result), the
	# table's difficulty_tier is the value the caller would pass into
	# build_enemy_group. Documenting the plumbing here so a rename/refactor
	# of tbl.difficulty_tier shows up as a test failure.
	var tbl := _make_table("tier5_zone", 5, [])
	assert_eq(tbl.difficulty_tier, 5, "difficulty_tier is stored on the table")


func test_scaling_curve_is_optional() -> void:
	# Both null and non-null scaling curves are accepted without error; the
	# empty-entries short-circuit means no enemy_def lookup actually happens.
	var tbl := _make_table("test_zone", 3, [])
	var no_scaling := MainScript.roll_zone_encounter_from_table(tbl, "son", null)
	var with_scaling := MainScript.roll_zone_encounter_from_table(tbl, "son", _scaling_curve())
	assert_eq(no_scaling.size(), 0)
	assert_eq(with_scaling.size(), 0)
