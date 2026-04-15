# project/hosts/complete-app/tests/test_battle_manager_cast.gd
#
# Tests BattleManager._apply_cast — the pure resolution half of the cast
# pipeline. Driving the full menu flow in a headless Godot run is
# impractical (the state machine expects Input polling and a live _process
# loop), and Playwright can't keep a tab unthrottled long enough for
# menu-keyboard navigation. So this suite hand-crafts Combatants +
# SpellDefinitions and calls _apply_cast directly.
extends GutTest

const BattleManagerScript = preload("res://scripts/battle/battle_manager.gd")
const SpellDefinitionScript = preload("res://lib/resources/spell_definition.gd")

var _bm: BattleManager
var _caster: Combatant
var _ally: Combatant
var _enemy: Combatant

func before_each() -> void:
	_bm = BattleManagerScript.new()
	add_child_autofree(_bm)

	_caster = Combatant.from_dict({
		"name": "Son",
		"max_hp": 50,
		"max_mp": 25,
		"atk": 12,
		"def": 8,
		"spd": 10,
		"level": 2,
		"spells": ["heal", "hurt"],
	})
	# Wound the caster so Heal has something to restore.
	_caster.hp = 20

	_ally = Combatant.from_dict({
		"name": "Ally",
		"max_hp": 40,
		"max_mp": 0,
		"atk": 10,
		"def": 5,
	})

	_enemy = Combatant.from_dict({
		"name": "Slime",
		"max_hp": 12,
		"atk": 5,
		"def": 2,
	}, true)

	# Populate party/enemies so the redirect-on-dead-target branch has pools.
	_bm.party = [_caster, _ally]
	_bm.enemies = [_enemy]


func _make_spell(fields: Dictionary) -> SpellDefinition:
	var spell: SpellDefinition = SpellDefinitionScript.new()
	for key in fields.keys():
		spell.set(key, fields[key])
	return spell


func test_heal_deducts_mp_and_restores_hp() -> void:
	var heal := _make_spell({
		"id": "heal",
		"display_name": "Heal",
		"mp_cost": 4,
		"target_kind": "self",
		"effect_kind": "heal",
		"power_min": 25,
		"power_max": 25,  # pin for deterministic assert
	})
	var before_mp := _caster.mp
	var before_hp := _caster.hp

	var ok := _bm._apply_cast(_caster, _caster, heal)

	assert_true(ok, "heal should resolve successfully")
	assert_eq(_caster.mp, before_mp - heal.mp_cost, "MP must drop by mp_cost")
	assert_eq(_caster.hp, before_hp + 25, "HP must increase by power amount")


func test_heal_clamps_at_max_hp() -> void:
	_caster.hp = _caster.max_hp - 5  # only 5 HP missing
	var heal := _make_spell({
		"id": "heal",
		"display_name": "Heal",
		"mp_cost": 4,
		"target_kind": "self",
		"effect_kind": "heal",
		"power_min": 50,
		"power_max": 50,  # way more than missing HP
	})

	_bm._apply_cast(_caster, _caster, heal)

	assert_eq(_caster.hp, _caster.max_hp, "HP must clamp at max_hp")


func test_hurt_deducts_mp_and_damages_enemy_bypassing_defense() -> void:
	var hurt := _make_spell({
		"id": "hurt",
		"display_name": "Hurt",
		"mp_cost": 2,
		"target_kind": "enemy",
		"effect_kind": "damage",
		"power_min": 8,
		"power_max": 8,  # pin
	})
	var before_mp := _caster.mp
	var before_hp := _enemy.hp

	_bm._apply_cast(_caster, _enemy, hurt)

	assert_eq(_caster.mp, before_mp - hurt.mp_cost, "caster MP must drop")
	# DQ1 semantics: spell damage ignores defense. Raw power is 8.
	assert_eq(_enemy.hp, before_hp - 8, "enemy HP must drop by raw power (def ignored)")


func test_insufficient_mp_returns_false_and_spends_nothing() -> void:
	_caster.mp = 1  # less than heal's cost
	var heal := _make_spell({
		"id": "heal",
		"mp_cost": 4,
		"target_kind": "self",
		"effect_kind": "heal",
		"power_min": 25,
		"power_max": 25,
	})
	var hp_before := _caster.hp

	var ok := _bm._apply_cast(_caster, _caster, heal)

	assert_false(ok, "cast must fail on MP shortfall")
	assert_eq(_caster.mp, 1, "MP must stay at 1 — no spend on failure")
	assert_eq(_caster.hp, hp_before, "HP must not move on failed cast")


func test_null_spell_is_safely_rejected() -> void:
	var hp_before := _enemy.hp
	var mp_before := _caster.mp

	var ok := _bm._apply_cast(_caster, _enemy, null)

	assert_false(ok)
	assert_eq(_caster.mp, mp_before)
	assert_eq(_enemy.hp, hp_before)


func test_damage_spell_redirects_when_target_already_dead() -> void:
	# Simulate: original target died earlier in the turn. Add a second
	# enemy so the redirect has something to hit.
	var second_enemy := Combatant.from_dict({
		"name": "Slime2",
		"max_hp": 12,
		"atk": 5,
		"def": 2,
	}, true)
	_bm.enemies = [_enemy, second_enemy]
	_enemy.hp = 0  # original target dead

	var hurt := _make_spell({
		"id": "hurt",
		"mp_cost": 2,
		"target_kind": "enemy",
		"effect_kind": "damage",
		"power_min": 8,
		"power_max": 8,
	})

	_bm._apply_cast(_caster, _enemy, hurt)

	assert_eq(_enemy.hp, 0, "original dead target must stay at 0")
	assert_eq(second_enemy.hp, 12 - 8, "redirect must land on the alive sibling")
