class_name Combatant
extends RefCounted

var combatant_name: String = ""
var max_hp: int = 0
var hp: int = 0
var max_mp: int = 0
var mp: int = 0
var atk: int = 0
var def: int = 0
var spd: int = 0
var level: int = 1
var is_enemy: bool = false
var color: Color = Color.WHITE
var exp_reward: int = 0
var gold_reward: int = 0
# Spell ids this combatant can cast. Looked up via
# ContentManager.get_spell_definition(id) at cast time. Empty = no magic.
var known_spells: Array[String] = []

var is_alive: bool:
	get: return hp > 0

var is_defending: bool = false

static func from_dict(data: Dictionary, enemy: bool = false) -> Combatant:
	var c = Combatant.new()
	c.combatant_name = data.get("name", "???")
	c.max_hp = data.get("max_hp", 10)
	c.hp = c.max_hp
	c.max_mp = data.get("max_mp", 0)
	c.mp = c.max_mp
	c.atk = data.get("atk", 5)
	c.def = data.get("def", 3)
	c.spd = data.get("spd", 5)
	c.level = data.get("level", 1)
	c.is_enemy = enemy
	c.color = data.get("color", Color.WHITE)
	c.exp_reward = data.get("exp", 0)
	c.gold_reward = data.get("gold", 0)
	var spells_raw: Array = data.get("spells", [])
	var spells: Array[String] = []
	for s in spells_raw:
		spells.append(str(s))
	c.known_spells = spells
	return c
