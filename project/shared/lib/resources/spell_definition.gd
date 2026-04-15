extends Resource
class_name SpellDefinition
##
## Data definition for a combat spell. Instances live inside the
## `spells-*` bundles as `.tres`, loaded via
## ContentManager.get_spell_definition(id). Stats are hot-reloadable on
## F9 (same .tres-driven iteration loop as hud-core styles and
## enemies-core stats).
##
## DQ1 inheritance: MP costs and power bands match the NES Dragon Quest
## canon (see vault/references/dq1-notes/2026-04-15-spell-system.md).

@export var id: String
@export var display_name: String
@export var description: String

# Resource cost.
@export var mp_cost: int = 0

# Who the spell hits.
#   "self"         — actor is the target (Heal, Healmore)
#   "enemy"        — single enemy picked via TARGET_SELECT (Hurt)
#   "all_enemies"  — every alive enemy at once (no DQ1 spell uses this yet,
#                    reserved for future Boom/Explodet)
#   "party"        — all party members (no DQ1 spell; reserved)
@export var target_kind: String = "enemy"

# What the spell does.
#   "damage" — roll power_min..power_max dmg against target (no def red.)
#   "heal"   — restore power_min..power_max HP to target
# Future: "sleep", "stopspell" once the status-effect system exists.
@export var effect_kind: String = "damage"

# Inclusive power roll range. For damage effects this is raw damage; for
# heal effects it's raw HP restored.
@export var power_min: int = 0
@export var power_max: int = 0

# Flavor / forward-compat fields — declared so .tres instances can carry
# them today and future battle code can consume them without a schema
# migration.
@export var element: String = ""       # "fire", "ice" — visual tint only for now
@export var status_effect: String = "" # "sleep", "poison" — unused pre-status-system

# Minimum caster level required to use this spell. DQ1 canon gates spells
# by hero level (Heal L3, Hurt L4, Sleep L7, Stopspell L10, Healmore L15).
# The battle menu filters out spells where `learn_level > caster.level` —
# so a caster's `known_spells` list is the upper bound of their kit, and
# this field enforces the rollout schedule. Default 1 = always learnable.
@export var learn_level: int = 1
