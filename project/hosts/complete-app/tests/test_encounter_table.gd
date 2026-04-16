# project/hosts/complete-app/tests/test_encounter_table.gd
#
# Covers EncounterTable.roll — the weighted random selector that filters
# by era and picks a bestiary_id from the zone's encounter pool.
extends GutTest

const EncounterTableScript = preload("res://lib/resources/encounter_table.gd")


func _make_table(entry_list: Array) -> EncounterTable:
	var tbl: EncounterTable = EncounterTableScript.new()
	tbl.entries = entry_list
	return tbl


func test_roll_respects_era_filter() -> void:
	var tbl := _make_table([
		{"bestiary_id": "slime", "weight": 10, "era": "father"},
		{"bestiary_id": "moss_lurker", "weight": 10, "era": "son"},
	])
	for i in 20:
		var pick := tbl.roll("son")
		assert_eq(pick, "moss_lurker", "son-era rolls must skip father-only entries")


func test_roll_handles_both_era_entries() -> void:
	var tbl := _make_table([
		{"bestiary_id": "slime", "weight": 10, "era": "both"},
	])
	assert_eq(tbl.roll("father"), "slime")
	assert_eq(tbl.roll("son"), "slime")


func test_roll_returns_empty_when_no_eligible_entries() -> void:
	var tbl := _make_table([
		{"bestiary_id": "slime", "weight": 10, "era": "father"},
	])
	assert_eq(tbl.roll("son"), "", "no eligible entries should return empty id")


func test_weighted_distribution_favors_higher_weight_entry() -> void:
	var tbl := _make_table([
		{"bestiary_id": "rare", "weight": 1, "era": "both"},
		{"bestiary_id": "common", "weight": 99, "era": "both"},
	])
	var common_count := 0
	for i in 200:
		if tbl.roll("both") == "common":
			common_count += 1
	# 99% weight should land common >= 180/200 with overwhelming probability.
	assert_gt(common_count, 180, "99%% weight must dominate sample of 200")


func test_roll_empty_table_returns_empty() -> void:
	var tbl := _make_table([])
	assert_eq(tbl.roll("son"), "")


func test_roll_mixed_eras() -> void:
	var tbl := _make_table([
		{"bestiary_id": "wolf", "weight": 5, "era": "father"},
		{"bestiary_id": "moss_lurker", "weight": 3, "era": "son"},
		{"bestiary_id": "slime", "weight": 2, "era": "both"},
	])
	# Father era: wolf + slime eligible, moss_lurker excluded
	for i in 20:
		var pick := tbl.roll("father")
		assert_ne(pick, "moss_lurker", "father-era must not roll son-only entry")
