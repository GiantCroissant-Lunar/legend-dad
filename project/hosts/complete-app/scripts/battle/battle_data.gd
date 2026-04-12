class_name BattleData

const FATHER_STATS := {
	"name": "Father",
	"max_hp": 60,
	"max_mp": 20,
	"atk": 15,
	"def": 10,
	"spd": 8,
	"level": 3,
}

const SON_STATS := {
	"name": "Son",
	"max_hp": 50,
	"max_mp": 25,
	"atk": 12,
	"def": 8,
	"spd": 10,
	"level": 2,
}

const ALLY1_STATS := {
	"name": "Ally1",
	"max_hp": 45,
	"max_mp": 30,
	"atk": 10,
	"def": 7,
	"spd": 9,
	"level": 2,
}

const ALLY2_STATS := {
	"name": "Ally2",
	"max_hp": 65,
	"max_mp": 10,
	"atk": 14,
	"def": 12,
	"spd": 6,
	"level": 2,
}

const ENEMIES := {
	"slime": {
		"name": "Slime",
		"max_hp": 12,
		"atk": 5,
		"def": 2,
		"spd": 3,
		"exp": 4,
		"gold": 3,
		"color": Color(0.2, 0.8, 0.3),
	},
	"bandit": {
		"name": "Bandit",
		"max_hp": 25,
		"atk": 10,
		"def": 5,
		"spd": 7,
		"exp": 12,
		"gold": 8,
		"color": Color(0.7, 0.3, 0.3),
	},
	"wolf": {
		"name": "Wolf",
		"max_hp": 18,
		"atk": 8,
		"def": 3,
		"spd": 12,
		"exp": 8,
		"gold": 5,
		"color": Color(0.5, 0.5, 0.5),
	},
}

static func calc_damage(atk: int, def: int) -> int:
	var base = atk - def / 2
	var variance = randi_range(-2, 2)
	return maxi(1, base + variance)

static func calc_flee_chance(party_spd: int, enemy_spd: int) -> bool:
	var chance = 0.5 + 0.1 * (party_spd - enemy_spd)
	chance = clampf(chance, 0.1, 0.9)
	return randf() < chance
