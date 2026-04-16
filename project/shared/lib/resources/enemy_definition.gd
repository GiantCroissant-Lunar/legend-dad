extends Resource
class_name EnemyDefinition
##
## Data definition for an enemy. Lives inside the `enemies-*` bundles as a
## `.tres` so stats can be iterated on via F9 hot-reload (see
## `vault/dev-log/2026-04-15-hud-style-tres-live-iteration.md` for the
## iteration policy — tunable values live in data, not `const`).
##
## Consumed by:
##   - main.gd._spawn_enemy (visual tint)
##   - main.gd._start_battle / Combatant.from_dict (stats)

@export var id: String
@export var display_name: String
@export var sprite: Texture2D

# Core combat stats (mirrors the shape Combatant.from_dict expects).
@export var max_hp: int = 1
@export var max_mp: int = 0
@export var attack: int = 1
@export var defense: int = 0
@export var spd: int = 1
@export var level: int = 1

# Rewards on defeat.
@export var xp_reward: int = 1
@export var gold_reward: int = 0

# Overworld/battle visual tint used when no sprite is set (current game uses
# a simple colored rect per enemy during the pixel-art iteration phase).
@export var tint_color: Color = Color(0.8, 0.8, 0.8)

# Optional behavior tree (Beehave). Not used yet; kept for forward-compat.
@export var behavior_tree: PackedScene

# Spell ids this enemy can cast (resolved via ContentManager.get_spell_definition
# at battle time). Enemies with max_mp > 0 AND at least one viable spell here
# get a chance to queue a cast each turn — see BattleManager._maybe_queue_enemy_cast.
@export var spells: PackedStringArray = PackedStringArray()

# Group-size range rolled at encounter time. A single overworld entity
# represents the whole group; on encounter, main.gd rolls
# randi_range(group_size_min, group_size_max) copies into the battle.
# Defaults match a solo encounter so rare/boss enemies stay 1-of-1 unless
# their .tres opts in. DQ1 canon: weak fodder (Slime, Dracky, Wolf) runs
# in packs; tougher units (Bandit, Magician, Metal Scorpion) solo.
@export var group_size_min: int = 1
@export var group_size_max: int = 1

# Action dicts authored in bestiary frontmatter. Each entry:
#   {id, kind ("attack"|"spell"|"status_inflict"), frequency, power_min, power_max,
#    target_kind, status_effect?, spell_id?}
# Consumed by BattleManager._pick_enemy_action when queuing a turn.
@export var actions: Array = []

# Returns a Dictionary in the shape Combatant.from_dict expects, so callers
# don't need to know about the field-name difference between this Resource
# (`attack`/`defense`/`xp_reward`/...) and the dict shape the battle code
# was originally written against (`atk`/`def`/`exp`/...).
func to_combat_dict() -> Dictionary:
	return {
		"name": display_name,
		"max_hp": max_hp,
		"max_mp": max_mp,
		"atk": attack,
		"def": defense,
		"spd": spd,
		"level": level,
		"color": tint_color,
		"exp": xp_reward,
		"gold": gold_reward,
		"spells": Array(spells),
		"actions": actions,
	}
