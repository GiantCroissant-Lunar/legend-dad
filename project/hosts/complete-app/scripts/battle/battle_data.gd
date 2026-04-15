class_name BattleData

const FATHER_STATS := {
	"name": "Father",
	"max_hp": 60,
	"max_mp": 20,
	"atk": 15,
	"def": 10,
	"spd": 8,
	"level": 3,
	"spells": ["hurt"],
}

const SON_STATS := {
	"name": "Son",
	"max_hp": 50,
	"max_mp": 25,
	"atk": 12,
	"def": 8,
	"spd": 10,
	"level": 2,
	# DQ1 level gates: Heal L3, Hurt L4, Sleep L7, Healmore L15.
	# Gating by level is pre-MVP — Son knows the full caster kit so we
	# can iterate on spell behavior without a progression system.
	"spells": ["heal", "healmore", "hurt", "sleep"],
}

const ALLY1_STATS := {
	"name": "Ally1",
	"max_hp": 45,
	"max_mp": 30,
	"atk": 10,
	"def": 7,
	"spd": 9,
	"level": 2,
	"spells": [],
}

const ALLY2_STATS := {
	"name": "Ally2",
	"max_hp": 65,
	"max_mp": 10,
	"atk": 14,
	"def": 12,
	"spd": 6,
	"level": 2,
	"spells": [],
}

# Enemy stats moved to res://content/enemies/enemies-core/*.tres and
# accessed via ContentManager.get_enemy_definition(id). Player/ally stats
# still live here — no content iteration need for them yet.

static func calc_damage(atk: int, def: int) -> int:
	var base = atk - def / 2
	var variance = randi_range(-2, 2)
	return maxi(1, base + variance)

static func calc_flee_chance(party_spd: int, enemy_spd: int) -> bool:
	var chance = 0.5 + 0.1 * (party_spd - enemy_spd)
	chance = clampf(chance, 0.1, 0.9)
	return randf() < chance
