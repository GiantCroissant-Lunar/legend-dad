# Battle System Prototype Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add Dragon Quest-style first-person turn-based combat to the dual-timeline prototype — battle screen transition, command menu, turn resolution, damage calculation, victory/defeat, and one overworld enemy that triggers combat.

**Architecture:** Combat is a state machine managed by `BattleManager` (a plain Node, not an ECS system). When the player walks into an enemy entity on the overworld, `main.gd` transitions the active era's SubViewport to show a `BattleUI` scene instead of the tilemap. The battle runs independently of the ECS loop (ECS pauses during combat). On victory/defeat, control returns to the overworld. Enemy entities use existing ECS components (`C_GridPosition`, `C_TimelineEra`) plus a new `C_Enemy` component.

**Tech Stack:** Godot 4.6 (GDScript), existing GECS components, web export

**Design Reference:** `vault/design/combat-system-design.md`

---

## File Structure

```
project/hosts/complete-app/
├── ecs/
│   ├── components/
│   │   └── c_enemy.gd                    # Marks an entity as an overworld enemy
│   └── entities/
│       └── e_enemy.gd                    # Overworld enemy entity
├── scripts/
│   ├── main.gd                           # Modified: battle trigger, state management
│   ├── entity_visual.gd                  # Modified: add ENEMY visual type
│   ├── battle/
│   │   ├── battle_manager.gd             # State machine: command → resolve → check
│   │   ├── battle_ui.gd                  # Draws the battle screen (enemies, menu, status)
│   │   ├── battle_data.gd                # Static data: combatant stats, damage formula
│   │   └── combatant.gd                  # Runtime combatant state (HP, ATK, DEF, SPD)
│   └── tileset_factory.gd               # Unchanged
└── project.godot                         # Modified: add battle input actions
```

**Responsibility summary:**

| File | Purpose |
|------|---------|
| `c_enemy.gd` | Component tagging overworld entities as enemies, stores enemy type ID |
| `e_enemy.gd` | Overworld enemy entity with grid position, era, and enemy tag |
| `battle_data.gd` | Static definitions: enemy stat tables, damage formula, EXP/gold rewards |
| `combatant.gd` | Runtime state for one combatant (player or enemy) during a fight |
| `battle_manager.gd` | State machine driving the battle loop: idle → command → resolve → check |
| `battle_ui.gd` | Control node that renders the entire battle screen via `_draw()` |
| `main.gd` | Integration: detects enemy collision, starts/ends battle, pauses ECS |
| `entity_visual.gd` | Extended: draws overworld enemy sprites |

---

## Task 1: Enemy Component and Entity

**Files:**
- Create: `project/hosts/complete-app/ecs/components/c_enemy.gd`
- Create: `project/hosts/complete-app/ecs/entities/e_enemy.gd`

- [ ] **Step 1: Create c_enemy.gd**

```gdscript
class_name C_Enemy
extends Component

## Identifies which enemy type this is (indexes into BattleData.ENEMIES).
@export var enemy_type: String = "slime"

func _init(p_type: String = "slime"):
	enemy_type = p_type
```

- [ ] **Step 2: Create e_enemy.gd**

```gdscript
class_name E_Enemy
extends Entity

@export var era: C_TimelineEra.Era = C_TimelineEra.Era.FATHER
@export var start_col: int = 0
@export var start_row: int = 0
@export var enemy_type: String = "slime"

func define_components() -> Array:
	return [
		C_TimelineEra.new(era),
		C_GridPosition.new(start_col, start_row),
		C_Enemy.new(enemy_type),
	]
```

- [ ] **Step 3: Commit**

```bash
git add project/hosts/complete-app/ecs/components/c_enemy.gd project/hosts/complete-app/ecs/entities/e_enemy.gd
git commit -m "feat: add C_Enemy component and E_Enemy entity for overworld enemies"
```

---

## Task 2: Battle Data (Static Definitions)

**Files:**
- Create: `project/hosts/complete-app/scripts/battle/battle_data.gd`

- [ ] **Step 1: Create battle_data.gd**

This file contains all static combat data: enemy stat tables, the damage formula, and the player's base stats. No game state — purely definitions.

```gdscript
class_name BattleData

## Player base stats at level 1. In a full game these scale with level.
## For the prototype, stats are fixed.
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

## Placeholder party members for son's era.
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

## Enemy definitions keyed by enemy_type string.
const ENEMIES := {
	"slime": {
		"name": "Slime",
		"max_hp": 12,
		"atk": 5,
		"def": 2,
		"spd": 3,
		"exp": 4,
		"gold": 3,
		"color": Color(0.2, 0.8, 0.3),  # Green for placeholder drawing
	},
	"bandit": {
		"name": "Bandit",
		"max_hp": 25,
		"atk": 10,
		"def": 5,
		"spd": 7,
		"exp": 12,
		"gold": 8,
		"color": Color(0.7, 0.3, 0.3),  # Red
	},
	"wolf": {
		"name": "Wolf",
		"max_hp": 18,
		"atk": 8,
		"def": 3,
		"spd": 12,
		"exp": 8,
		"gold": 5,
		"color": Color(0.5, 0.5, 0.5),  # Gray
	},
}

## Calculate damage dealt by attacker to defender.
## DQ-style: ATK - DEF/2, with variance and minimum 1.
static func calc_damage(atk: int, def: int) -> int:
	var base = atk - def / 2
	var variance = randi_range(-2, 2)
	return maxi(1, base + variance)

## Check if flee attempt succeeds. Based on party average speed vs enemy speed.
static func calc_flee_chance(party_spd: int, enemy_spd: int) -> bool:
	var chance = 0.5 + 0.1 * (party_spd - enemy_spd)
	chance = clampf(chance, 0.1, 0.9)
	return randf() < chance
```

- [ ] **Step 2: Commit**

```bash
git add project/hosts/complete-app/scripts/battle/battle_data.gd
git commit -m "feat: add BattleData with enemy stats, damage formula, and player stats"
```

---

## Task 3: Combatant Runtime State

**Files:**
- Create: `project/hosts/complete-app/scripts/battle/combatant.gd`

- [ ] **Step 1: Create combatant.gd**

A simple data class holding the runtime state of one combatant during battle. Created from static data at battle start.

```gdscript
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
## For enemies: display color (placeholder sprite).
var color: Color = Color.WHITE
## For enemies: rewards.
var exp_reward: int = 0
var gold_reward: int = 0

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
	return c
```

- [ ] **Step 2: Commit**

```bash
git add project/hosts/complete-app/scripts/battle/combatant.gd
git commit -m "feat: add Combatant runtime state class for battle participants"
```

---

## Task 4: Battle UI (Drawing the Battle Screen)

**Files:**
- Create: `project/hosts/complete-app/scripts/battle/battle_ui.gd`

- [ ] **Step 1: Create battle_ui.gd**

A Control node that renders the entire first-person battle screen using `_draw()`. It shows enemies as colored shapes at the top, a message log in the middle, a command menu at the bottom-left, and party status at the bottom-right.

```gdscript
class_name BattleUI
extends Control

## Colors
const BG_COLOR := Color(0.05, 0.05, 0.15)
const TEXT_COLOR := Color.WHITE
const MENU_HIGHLIGHT := Color(1.0, 0.8, 0.0)
const MENU_NORMAL := Color(0.7, 0.7, 0.7)
const HP_GREEN := Color(0.2, 0.8, 0.2)
const HP_RED := Color(0.8, 0.2, 0.2)
const HP_BAR_BG := Color(0.2, 0.2, 0.2)

## State set by BattleManager each frame.
var enemies: Array[Combatant] = []
var party: Array[Combatant] = []
var message_lines: Array[String] = []
var menu_items: Array[String] = []
var menu_cursor: int = 0
var show_menu: bool = false
var current_member_name: String = ""
## Which enemy is targeted (for attack target selection).
var target_cursor: int = 0
var show_target_select: bool = false

func _draw() -> void:
	var sz = size
	# Background
	draw_rect(Rect2(Vector2.ZERO, sz), BG_COLOR)

	# --- Enemy area (top 40%) ---
	var enemy_area_h = sz.y * 0.4
	_draw_enemies(sz, enemy_area_h)

	# --- Message area (middle 25%) ---
	var msg_y = enemy_area_h
	var msg_h = sz.y * 0.25
	_draw_messages(sz, msg_y, msg_h)

	# --- Bottom panel (35%): menu left, status right ---
	var panel_y = msg_y + msg_h
	var panel_h = sz.y * 0.35
	draw_line(Vector2(0, panel_y), Vector2(sz.x, panel_y), Color(0.3, 0.3, 0.4), 1.0)
	_draw_menu(sz, panel_y, panel_h)
	_draw_status(sz, panel_y, panel_h)

func _draw_enemies(sz: Vector2, area_h: float) -> void:
	if enemies.is_empty():
		return
	var spacing = sz.x / (enemies.size() + 1)
	for i in enemies.size():
		var enemy = enemies[i]
		var cx = spacing * (i + 1)
		var cy = area_h * 0.5
		if enemy.is_alive:
			# Draw enemy as a colored ellipse (placeholder)
			var rx = 30.0
			var ry = 25.0
			_draw_ellipse(Vector2(cx, cy), rx, ry, enemy.color)
			# Enemy name below
			draw_string(ThemeDB.fallback_font, Vector2(cx - 25, cy + ry + 16), enemy.combatant_name,
				HORIZONTAL_ALIGNMENT_LEFT, -1, 11, TEXT_COLOR)
			# HP fraction
			var hp_text = "%d/%d" % [enemy.hp, enemy.max_hp]
			draw_string(ThemeDB.fallback_font, Vector2(cx - 20, cy + ry + 30), hp_text,
				HORIZONTAL_ALIGNMENT_LEFT, -1, 10, Color(0.6, 0.6, 0.6))
		else:
			# Dead enemy — draw faded
			_draw_ellipse(Vector2(cx, cy), 20, 15, Color(0.3, 0.3, 0.3, 0.3))

		# Target cursor
		if show_target_select and i == target_cursor and enemy.is_alive:
			draw_string(ThemeDB.fallback_font, Vector2(cx - 5, cy - 35), "▼",
				HORIZONTAL_ALIGNMENT_LEFT, -1, 16, MENU_HIGHLIGHT)

func _draw_ellipse(center: Vector2, rx: float, ry: float, color: Color) -> void:
	var points = PackedVector2Array()
	for angle_deg in range(0, 361, 10):
		var rad = deg_to_rad(angle_deg)
		points.append(center + Vector2(cos(rad) * rx, sin(rad) * ry))
	draw_colored_polygon(points, color)

func _draw_messages(sz: Vector2, y: float, h: float) -> void:
	draw_rect(Rect2(0, y, sz.x, h), Color(0.0, 0.0, 0.1, 0.8))
	var line_h = 18.0
	var max_lines = int(h / line_h) - 1
	var start = maxi(0, message_lines.size() - max_lines)
	for i in range(start, message_lines.size()):
		var line_y = y + 14 + (i - start) * line_h
		draw_string(ThemeDB.fallback_font, Vector2(12, line_y), message_lines[i],
			HORIZONTAL_ALIGNMENT_LEFT, -1, 13, TEXT_COLOR)

func _draw_menu(sz: Vector2, y: float, h: float) -> void:
	if not show_menu:
		return
	var menu_x = 16.0
	var menu_y = y + 8.0
	# Show which party member is choosing
	draw_string(ThemeDB.fallback_font, Vector2(menu_x, menu_y + 14), current_member_name + ":",
		HORIZONTAL_ALIGNMENT_LEFT, -1, 12, MENU_HIGHLIGHT)
	menu_y += 22.0
	for i in menu_items.size():
		var color = MENU_HIGHLIGHT if i == menu_cursor else MENU_NORMAL
		var prefix = "> " if i == menu_cursor else "  "
		draw_string(ThemeDB.fallback_font, Vector2(menu_x, menu_y + 14), prefix + menu_items[i],
			HORIZONTAL_ALIGNMENT_LEFT, -1, 13, color)
		menu_y += 20.0

func _draw_status(sz: Vector2, y: float, h: float) -> void:
	var status_x = sz.x * 0.55
	var status_y = y + 8.0
	for member in party:
		var color = TEXT_COLOR if member.is_alive else Color(0.5, 0.5, 0.5)
		var name_text = member.combatant_name
		if member.is_defending:
			name_text += " [DEF]"
		draw_string(ThemeDB.fallback_font, Vector2(status_x, status_y + 12), name_text,
			HORIZONTAL_ALIGNMENT_LEFT, -1, 12, color)
		# HP bar
		var bar_x = status_x + 80
		var bar_w = 80.0
		var bar_h = 8.0
		draw_rect(Rect2(bar_x, status_y + 4, bar_w, bar_h), HP_BAR_BG)
		var hp_ratio = float(member.hp) / float(member.max_hp) if member.max_hp > 0 else 0.0
		var bar_color = HP_GREEN if hp_ratio > 0.3 else HP_RED
		draw_rect(Rect2(bar_x, status_y + 4, bar_w * hp_ratio, bar_h), bar_color)
		# HP number
		var hp_text = "%d/%d" % [member.hp, member.max_hp]
		draw_string(ThemeDB.fallback_font, Vector2(bar_x + bar_w + 6, status_y + 12), hp_text,
			HORIZONTAL_ALIGNMENT_LEFT, -1, 10, color)
		status_y += 22.0

func _process(_delta: float) -> void:
	queue_redraw()
```

- [ ] **Step 2: Commit**

```bash
git add project/hosts/complete-app/scripts/battle/battle_ui.gd
git commit -m "feat: add BattleUI with first-person DQ-style battle screen rendering"
```

---

## Task 5: Battle Manager (State Machine)

**Files:**
- Create: `project/hosts/complete-app/scripts/battle/battle_manager.gd`

- [ ] **Step 1: Create battle_manager.gd**

The core battle state machine. It receives combatants, runs the turn loop, and emits signals when battle ends.

```gdscript
class_name BattleManager
extends Node

signal battle_ended(result: Dictionary)
## result = { "won": bool, "exp": int, "gold": int, "fled": bool }

enum State { INTRO, COMMAND, TARGET_SELECT, RESOLVE, VICTORY, DEFEAT, FLEE }

var state: State = State.INTRO
var party: Array[Combatant] = []
var enemies: Array[Combatant] = []
var ui: BattleUI = null

## Command phase tracking
var _current_member_idx: int = 0
var _turn_commands: Array[Dictionary] = []
## Each command: { "actor": Combatant, "action": String, "target": Combatant }

## Message queue for displaying text one line at a time
var _message_queue: Array[String] = []
var _message_timer: float = 0.0
const MESSAGE_DELAY := 0.6

## Input cooldown to prevent instant double-press
var _input_cooldown: float = 0.0
const INPUT_COOLDOWN := 0.15

func start_battle(p_party: Array[Combatant], p_enemies: Array[Combatant], p_ui: BattleUI) -> void:
	party = p_party
	enemies = p_enemies
	ui = p_ui
	state = State.INTRO
	_turn_commands.clear()
	_current_member_idx = 0

	# Sync UI state
	ui.enemies = enemies
	ui.party = party
	ui.message_lines.clear()
	ui.show_menu = false
	ui.show_target_select = false

	# Intro message
	var enemy_names = []
	for e in enemies:
		enemy_names.append(e.combatant_name)
	_add_message("%s appeared!" % " and ".join(enemy_names))
	_message_timer = MESSAGE_DELAY * 2  # Longer pause for intro

func _process(delta: float) -> void:
	_input_cooldown -= delta

	match state:
		State.INTRO:
			_process_intro(delta)
		State.COMMAND:
			_process_command(delta)
		State.TARGET_SELECT:
			_process_target_select(delta)
		State.RESOLVE:
			pass  # Awaiting turn resolution — input ignored
		State.VICTORY:
			_process_victory(delta)
		State.DEFEAT:
			_process_defeat(delta)
		State.FLEE:
			_process_flee(delta)

func _process_intro(delta: float) -> void:
	_message_timer -= delta
	if _message_timer <= 0.0:
		_start_command_phase()

func _start_command_phase() -> void:
	state = State.COMMAND
	_turn_commands.clear()
	_current_member_idx = 0
	# Reset defend flags
	for member in party:
		member.is_defending = false
	_show_menu_for_current_member()

func _show_menu_for_current_member() -> void:
	# Skip dead members
	while _current_member_idx < party.size() and not party[_current_member_idx].is_alive:
		_current_member_idx += 1

	if _current_member_idx >= party.size():
		# All commands collected — resolve turn
		_resolve_turn()
		return

	var member = party[_current_member_idx]
	ui.show_menu = true
	ui.show_target_select = false
	ui.menu_items = ["Attack", "Defend", "Flee"]
	ui.menu_cursor = 0
	ui.current_member_name = member.combatant_name
	_input_cooldown = INPUT_COOLDOWN

func _process_command(_delta: float) -> void:
	if _input_cooldown > 0.0:
		return

	if Input.is_action_just_pressed("ui_down"):
		ui.menu_cursor = (ui.menu_cursor + 1) % ui.menu_items.size()
		_input_cooldown = INPUT_COOLDOWN
	elif Input.is_action_just_pressed("ui_up"):
		ui.menu_cursor = (ui.menu_cursor - 1 + ui.menu_items.size()) % ui.menu_items.size()
		_input_cooldown = INPUT_COOLDOWN
	elif Input.is_action_just_pressed("ui_accept") or Input.is_action_just_pressed("interact"):
		var selected = ui.menu_items[ui.menu_cursor]
		_input_cooldown = INPUT_COOLDOWN
		match selected:
			"Attack":
				_start_target_select()
			"Defend":
				var member = party[_current_member_idx]
				member.is_defending = true
				_turn_commands.append({
					"actor": member,
					"action": "defend",
					"target": member,
				})
				_current_member_idx += 1
				_show_menu_for_current_member()
			"Flee":
				_attempt_flee()

func _start_target_select() -> void:
	state = State.TARGET_SELECT
	ui.show_menu = false
	ui.show_target_select = true
	# Find first alive enemy
	ui.target_cursor = 0
	for i in enemies.size():
		if enemies[i].is_alive:
			ui.target_cursor = i
			break
	_input_cooldown = INPUT_COOLDOWN

func _process_target_select(_delta: float) -> void:
	if _input_cooldown > 0.0:
		return

	if Input.is_action_just_pressed("ui_right"):
		_move_target_cursor(1)
		_input_cooldown = INPUT_COOLDOWN
	elif Input.is_action_just_pressed("ui_left"):
		_move_target_cursor(-1)
		_input_cooldown = INPUT_COOLDOWN
	elif Input.is_action_just_pressed("ui_accept") or Input.is_action_just_pressed("interact"):
		var member = party[_current_member_idx]
		_turn_commands.append({
			"actor": member,
			"action": "attack",
			"target": enemies[ui.target_cursor],
		})
		ui.show_target_select = false
		_current_member_idx += 1
		state = State.COMMAND
		_show_menu_for_current_member()
		_input_cooldown = INPUT_COOLDOWN
	elif Input.is_action_just_pressed("ui_cancel"):
		# Go back to command menu
		ui.show_target_select = false
		state = State.COMMAND
		_show_menu_for_current_member()
		_input_cooldown = INPUT_COOLDOWN

func _move_target_cursor(dir: int) -> void:
	var start = ui.target_cursor
	ui.target_cursor = (ui.target_cursor + dir + enemies.size()) % enemies.size()
	# Skip dead enemies
	var attempts = 0
	while not enemies[ui.target_cursor].is_alive and attempts < enemies.size():
		ui.target_cursor = (ui.target_cursor + dir + enemies.size()) % enemies.size()
		attempts += 1

func _attempt_flee() -> void:
	var avg_spd = 0
	var alive_count = 0
	for m in party:
		if m.is_alive:
			avg_spd += m.spd
			alive_count += 1
	if alive_count > 0:
		avg_spd /= alive_count
	var enemy_max_spd = 0
	for e in enemies:
		if e.is_alive:
			enemy_max_spd = maxi(enemy_max_spd, e.spd)

	if BattleData.calc_flee_chance(avg_spd, enemy_max_spd):
		_add_message("Escaped successfully!")
		ui.show_menu = false
		state = State.FLEE
		_message_timer = MESSAGE_DELAY * 2
	else:
		_add_message("Couldn't escape!")
		# Enemies still get their turn
		_turn_commands.clear()
		_resolve_turn()

func _resolve_turn() -> void:
	state = State.RESOLVE
	ui.show_menu = false
	ui.show_target_select = false

	# Add enemy actions
	for enemy in enemies:
		if enemy.is_alive:
			# Enemies always attack a random alive party member
			var alive_party = party.filter(func(m): return m.is_alive)
			if alive_party.is_empty():
				break
			var target = alive_party[randi() % alive_party.size()]
			_turn_commands.append({
				"actor": enemy,
				"action": "attack",
				"target": target,
			})

	# Sort by speed (highest first)
	_turn_commands.sort_custom(func(a, b): return a["actor"].spd > b["actor"].spd)

	# Execute all commands with messages
	for cmd in _turn_commands:
		var actor: Combatant = cmd["actor"]
		var target: Combatant = cmd["target"]
		if not actor.is_alive:
			continue
		match cmd["action"]:
			"attack":
				if not target.is_alive:
					# Retarget to a random alive combatant on the same side
					if actor.is_enemy:
						var alive = party.filter(func(m): return m.is_alive)
						if alive.is_empty():
							continue
						target = alive[randi() % alive.size()]
					else:
						var alive = enemies.filter(func(e): return e.is_alive)
						if alive.is_empty():
							continue
						target = alive[randi() % alive.size()]
				var damage = BattleData.calc_damage(actor.atk, target.def)
				if target.is_defending:
					damage = maxi(1, damage / 2)
				target.hp = maxi(0, target.hp - damage)
				_add_message("%s attacks %s! %d damage." % [actor.combatant_name, target.combatant_name, damage])
				if not target.is_alive:
					_add_message("%s is defeated!" % target.combatant_name)
			"defend":
				_add_message("%s defends." % actor.combatant_name)

	_message_timer = MESSAGE_DELAY * _turn_commands.size()
	_turn_commands.clear()

	# After a delay, check win/loss
	await get_tree().create_timer(_message_timer).timeout
	_check_battle_end()

func _check_battle_end() -> void:
	var all_enemies_dead = enemies.all(func(e): return not e.is_alive)
	var all_party_dead = party.all(func(m): return not m.is_alive)

	if all_enemies_dead:
		state = State.VICTORY
		var total_exp = 0
		var total_gold = 0
		for e in enemies:
			total_exp += e.exp_reward
			total_gold += e.gold_reward
		_add_message("Victory! Gained %d EXP and %d gold." % [total_exp, total_gold])
		_message_timer = MESSAGE_DELAY * 3
	elif all_party_dead:
		state = State.DEFEAT
		_add_message("The party has been defeated...")
		_message_timer = MESSAGE_DELAY * 3
	else:
		# Next turn
		_start_command_phase()

func _process_victory(delta: float) -> void:
	_message_timer -= delta
	if _message_timer <= 0.0:
		if Input.is_action_just_pressed("ui_accept") or Input.is_action_just_pressed("interact"):
			var total_exp = 0
			var total_gold = 0
			for e in enemies:
				total_exp += e.exp_reward
				total_gold += e.gold_reward
			battle_ended.emit({"won": true, "exp": total_exp, "gold": total_gold, "fled": false})

func _process_defeat(delta: float) -> void:
	_message_timer -= delta
	if _message_timer <= 0.0:
		if Input.is_action_just_pressed("ui_accept") or Input.is_action_just_pressed("interact"):
			battle_ended.emit({"won": false, "exp": 0, "gold": 0, "fled": false})

func _process_flee(delta: float) -> void:
	_message_timer -= delta
	if _message_timer <= 0.0:
		if Input.is_action_just_pressed("ui_accept") or Input.is_action_just_pressed("interact"):
			battle_ended.emit({"won": false, "exp": 0, "gold": 0, "fled": true})

func _add_message(text: String) -> void:
	ui.message_lines.append(text)
	# Keep message log bounded
	if ui.message_lines.size() > 20:
		ui.message_lines.pop_front()
```

- [ ] **Step 2: Commit**

```bash
git add project/hosts/complete-app/scripts/battle/battle_manager.gd
git commit -m "feat: add BattleManager state machine for turn-based combat loop"
```

---

## Task 6: Add Enemy Visual Type

**Files:**
- Modify: `project/hosts/complete-app/scripts/entity_visual.gd`

- [ ] **Step 1: Add ENEMY to EntityVisual**

Add the ENEMY visual type so overworld enemies are visible on the tilemap.

Replace the full file with:

```gdscript
## A Node2D that visually represents an ECS entity in a SubViewport.
## main.gd creates these and syncs position/visibility from component data.
class_name EntityVisual
extends Node2D

const TILE_SIZE := 32

enum VisualType { PLAYER_FATHER, PLAYER_SON, BOULDER, BLOCKED, ENEMY }

var visual_type: VisualType = VisualType.PLAYER_FATHER
## The ECS entity this visual represents — used to read component data.
var entity: Entity = null
## For enemies: the color from BattleData.
var enemy_color: Color = Color(0.2, 0.8, 0.3)

func _draw() -> void:
	match visual_type:
		VisualType.PLAYER_FATHER:
			draw_rect(Rect2(4, 4, TILE_SIZE - 8, TILE_SIZE - 8), Color(1.0, 0.8, 0.0))
			_draw_facing_arrow()
		VisualType.PLAYER_SON:
			draw_rect(Rect2(4, 4, TILE_SIZE - 8, TILE_SIZE - 8), Color(0.6, 0.8, 1.0))
			_draw_facing_arrow()
		VisualType.BOULDER:
			draw_circle(Vector2(TILE_SIZE / 2.0, TILE_SIZE / 2.0), TILE_SIZE / 3.0, Color(0.5, 0.5, 0.5))
		VisualType.BLOCKED:
			draw_circle(Vector2(TILE_SIZE / 2.0, TILE_SIZE / 2.0), TILE_SIZE / 3.0, Color(0.4, 0.2, 0.2))
		VisualType.ENEMY:
			# Draw enemy as a diamond shape
			var center = Vector2(TILE_SIZE / 2.0, TILE_SIZE / 2.0)
			var half = TILE_SIZE / 3.0
			var points = PackedVector2Array([
				center + Vector2(0, -half),
				center + Vector2(half, 0),
				center + Vector2(0, half),
				center + Vector2(-half, 0),
			])
			draw_colored_polygon(points, enemy_color)

func _draw_facing_arrow() -> void:
	if not entity:
		return
	var grid_pos = entity.get_component(C_GridPosition) as C_GridPosition
	if grid_pos:
		var center = Vector2(TILE_SIZE / 2.0, TILE_SIZE / 2.0)
		var arrow_end = center + Vector2(grid_pos.facing) * 10.0
		draw_line(center, arrow_end, Color.WHITE, 2.0)

func _process(_delta: float) -> void:
	queue_redraw()
```

- [ ] **Step 2: Commit**

```bash
git add project/hosts/complete-app/scripts/entity_visual.gd
git commit -m "feat: add ENEMY visual type to EntityVisual for overworld enemy sprites"
```

---

## Task 7: Integrate Battle into Main Scene

**Files:**
- Modify: `project/hosts/complete-app/scripts/main.gd`

This is the integration task. main.gd needs to:
1. Spawn an enemy entity on the father's map
2. Detect when the player walks into an enemy (collision in S_PlayerInput already blocks movement — we add a special check)
3. Transition to battle: pause ECS, create BattleUI + BattleManager in the active SubViewport
4. On battle end: destroy battle nodes, resume ECS, remove defeated enemy

- [ ] **Step 1: Add battle state, enemy spawning, and encounter detection to main.gd**

Add these new variables after the existing variable declarations (after `var _debug_label: Label`):

```gdscript
# Battle state
var in_battle := false
var _battle_manager: BattleManager = null
var _battle_ui: BattleUI = null
var _battle_enemy_entity: E_Enemy = null
var _battle_enemy_visual: EntityVisual = null

# Enemy entities
var _enemy_entities: Array[E_Enemy] = []
var _enemy_visuals: Array[EntityVisual] = []
```

At the end of `_ready()`, after the debug HUD setup but before `_update_layout()`, add enemy spawning:

```gdscript
	# --- Spawn overworld enemies ---
	_spawn_enemy(C_TimelineEra.Era.FATHER, 4, 4, "slime")
	_spawn_enemy(C_TimelineEra.Era.FATHER, 7, 6, "slime")
```

Add the `_spawn_enemy` helper method:

```gdscript
func _spawn_enemy(era: C_TimelineEra.Era, col: int, row: int, enemy_type: String) -> void:
	var enemy = E_Enemy.new()
	enemy.era = era
	enemy.start_col = col
	enemy.start_row = row
	enemy.enemy_type = enemy_type
	enemy.name = "Enemy_%s_%d_%d" % [enemy_type, col, row]
	ECS.world.add_entity(enemy)
	_enemy_entities.append(enemy)

	var view = father_view if era == C_TimelineEra.Era.FATHER else son_view
	var visual = EntityVisual.new()
	visual.visual_type = EntityVisual.VisualType.ENEMY
	visual.entity = enemy
	var enemy_data = BattleData.ENEMIES.get(enemy_type, {})
	visual.enemy_color = enemy_data.get("color", Color(0.2, 0.8, 0.3))
	var gp = enemy.get_component(C_GridPosition) as C_GridPosition
	if gp:
		visual.position = Vector2(gp.visual_x, gp.visual_y)
	view.get_node("SubViewport").add_child(visual)
	_visuals.append(visual)
	_enemy_visuals.append(visual)
```

Modify `_process()` to check for enemy encounter and skip ECS when in battle:

```gdscript
func _process(delta: float) -> void:
	if in_battle:
		return  # BattleManager drives its own _process
	ECS.process(delta)
	_sync_visuals()
	_update_cameras()
	_update_debug_hud()
	_check_enemy_encounter()
```

Add the encounter check:

```gdscript
func _check_enemy_encounter() -> void:
	var active_player = father_player if active_era == C_TimelineEra.Era.FATHER else son_player
	var player_gp = active_player.get_component(C_GridPosition) as C_GridPosition
	var player_era = active_player.get_component(C_TimelineEra) as C_TimelineEra
	if not player_gp or not player_era:
		return

	# Check facing tile for an enemy
	var face_col = player_gp.col + player_gp.facing.x
	var face_row = player_gp.row + player_gp.facing.y

	for i in _enemy_entities.size():
		var enemy = _enemy_entities[i]
		var e_era = enemy.get_component(C_TimelineEra) as C_TimelineEra
		if e_era.era != player_era.era:
			continue
		var e_gp = enemy.get_component(C_GridPosition) as C_GridPosition
		# Trigger when player is adjacent and presses interact
		if e_gp.col == face_col and e_gp.row == face_row:
			if Input.is_action_just_pressed("ui_accept") or Input.is_action_just_pressed("interact"):
				_start_battle(enemy, _enemy_visuals[i])
				return
```

Add battle start/end methods:

```gdscript
func _start_battle(enemy_entity: E_Enemy, enemy_visual: EntityVisual) -> void:
	in_battle = true
	_battle_enemy_entity = enemy_entity
	_battle_enemy_visual = enemy_visual

	# Determine which view to use
	var active_view = father_view if active_era == C_TimelineEra.Era.FATHER else son_view
	var viewport = active_view.get_node("SubViewport")

	# Create battle UI — fills the SubViewport
	_battle_ui = BattleUI.new()
	_battle_ui.name = "BattleUI"
	_battle_ui.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	_battle_ui.z_index = 100  # Above tilemap and entities
	viewport.add_child(_battle_ui)

	# Create battle manager
	_battle_manager = BattleManager.new()
	_battle_manager.name = "BattleManager"
	add_child(_battle_manager)
	_battle_manager.battle_ended.connect(_on_battle_ended)

	# Build combatant lists
	var party_combatants: Array[Combatant] = []
	if active_era == C_TimelineEra.Era.FATHER:
		party_combatants.append(Combatant.from_dict(BattleData.FATHER_STATS))
	else:
		party_combatants.append(Combatant.from_dict(BattleData.SON_STATS))
		party_combatants.append(Combatant.from_dict(BattleData.ALLY1_STATS))
		party_combatants.append(Combatant.from_dict(BattleData.ALLY2_STATS))

	var enemy_comp = enemy_entity.get_component(C_Enemy) as C_Enemy
	var enemy_data = BattleData.ENEMIES.get(enemy_comp.enemy_type, BattleData.ENEMIES["slime"])
	var enemy_combatants: Array[Combatant] = []
	enemy_combatants.append(Combatant.from_dict(enemy_data, true))

	_battle_manager.start_battle(party_combatants, enemy_combatants, _battle_ui)

func _on_battle_ended(result: Dictionary) -> void:
	in_battle = false

	# Clean up battle nodes
	if _battle_ui:
		_battle_ui.queue_free()
		_battle_ui = null
	if _battle_manager:
		_battle_manager.battle_ended.disconnect(_on_battle_ended)
		_battle_manager.queue_free()
		_battle_manager = null

	# If won or fled, remove the enemy from the overworld
	if result.get("won", false) or result.get("fled", false):
		if _battle_enemy_visual:
			_battle_enemy_visual.queue_free()
			_visuals.erase(_battle_enemy_visual)
			_enemy_visuals.erase(_battle_enemy_visual)
		if _battle_enemy_entity:
			_enemy_entities.erase(_battle_enemy_entity)
			ECS.world.remove_entity(_battle_enemy_entity)
		_battle_enemy_entity = null
		_battle_enemy_visual = null

	# If defeated, for prototype just restart the scene
	if not result.get("won", false) and not result.get("fled", false):
		get_tree().reload_current_scene()
```

Also modify `_input()` to block era/map toggling during battle:

```gdscript
func _input(event: InputEvent) -> void:
	if in_battle:
		return  # Battle manager handles input
	# Tab toggles active era
	if event is InputEventKey and event.pressed and event.keycode == KEY_TAB:
		get_viewport().set_input_as_handled()
		_toggle_era()
	# M toggles world map
	if event is InputEventKey and event.pressed and event.keycode == KEY_M:
		get_viewport().set_input_as_handled()
		_toggle_map()
```

- [ ] **Step 2: Commit**

```bash
git add project/hosts/complete-app/scripts/main.gd
git commit -m "feat: integrate battle system with overworld — encounter detection, battle start/end, enemy spawning"
```

---

## Task 8: Input Actions for Battle

**Files:**
- Modify: `project/hosts/complete-app/project.godot`

- [ ] **Step 1: Add ui_cancel input action**

The battle needs `ui_cancel` for backing out of target selection. Godot has a default `ui_cancel` mapped to Escape, but in web export Escape can exit fullscreen. Add Backspace as an additional binding. Add after the `interact` action:

```ini
ui_cancel_battle={
"deadzone": 0.2,
"events": [Object(InputEventKey,"resource_local_to_scene":false,"resource_name":"","device":-1,"window_id":0,"alt_pressed":false,"shift_pressed":false,"ctrl_pressed":false,"meta_pressed":false,"pressed":false,"keycode":4194305,"physical_keycode":0,"key_label":0,"unicode":0,"location":0,"echo":false,"script":null)
]
}
```

Note: Keycode 4194305 = KEY_BACKSPACE. Actually, let's use the built-in `ui_cancel` which already exists in Godot (mapped to Escape). No new action needed. But update `battle_manager.gd` to also accept Backspace — change the cancel check in `_process_target_select`:

Replace `Input.is_action_just_pressed("ui_cancel")` in `battle_manager.gd` with:

```gdscript
	elif Input.is_action_just_pressed("ui_cancel") or Input.is_key_pressed(KEY_BACKSPACE):
```

- [ ] **Step 2: Commit**

```bash
git add project/hosts/complete-app/scripts/battle/battle_manager.gd
git commit -m "feat: add Backspace as alternative cancel key for battle target selection"
```

---

## Task 9: Build and Test

**Files:** No new files.

- [ ] **Step 1: Build web export**

```bash
cd /Users/apprenticegc/Work/lunar-horse/yokan-projects/legend-dad && task build
```

- [ ] **Step 2: Serve and test**

```bash
task serve
```

Open `http://localhost:8080/complete-app.html`.

Expected test flow:
1. See two game views with father (gold) and son (blue) players
2. See two diamond-shaped green enemies on father's map (at tiles 4,4 and 7,6)
3. Walk father player next to a slime, face it, press E
4. Battle screen appears in the father's view: slime shown as green ellipse, command menu shows "Attack / Defend / Flee"
5. Select Attack → target cursor appears on slime → press E to confirm
6. Messages show: "Father attacks! X damage to Slime." then "Slime attacks! Y damage to Father."
7. After slime dies: "Victory! Gained 4 EXP and 3 gold." Press E to return to overworld
8. Slime is gone from the map
9. Press Tab → switch to son's era. Walk to an enemy if one exists. Son should have 3 party members in combat.

- [ ] **Step 3: Fix any issues**

```bash
git add -A
git commit -m "fix: resolve issues found during battle system testing"
```

---

## Summary

| Task | Description | Files | Depends On |
|------|-------------|-------|------------|
| 1 | Enemy component + entity | 2 new files | None |
| 2 | Battle data (stats, formulas) | 1 new file | None |
| 3 | Combatant runtime state | 1 new file | None |
| 4 | Battle UI (rendering) | 1 new file | Task 3 |
| 5 | Battle Manager (state machine) | 1 new file | Tasks 2-4 |
| 6 | Enemy visual type | 1 modified file | Task 1 |
| 7 | Main scene integration | 1 modified file | Tasks 1-6 |
| 8 | Input actions for battle | 1 modified file | Task 5 |
| 9 | Build and test | No files | Tasks 1-8 |

**Parallel opportunities:** Tasks 1-4 are independent. Task 5 depends on 2-4. Tasks 6-8 depend on prior tasks. Task 9 is final verification.
