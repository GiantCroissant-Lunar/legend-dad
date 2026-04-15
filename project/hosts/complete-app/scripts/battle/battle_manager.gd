class_name BattleManager
extends Node

signal battle_ended(result: Dictionary)

enum State { INTRO, COMMAND, SPELL_SELECT, TARGET_SELECT, RESOLVE, VICTORY, DEFEAT, FLEE }

var state: State = State.INTRO
var party: Array[Combatant] = []
var enemies: Array[Combatant] = []
var ui: Control = null

var _current_member_idx: int = 0
var _turn_commands: Array[Dictionary] = []

var _message_queue: Array[String] = []
var _message_timer: float = 0.0
const MESSAGE_DELAY := 0.6

var _input_cooldown: float = 0.0
const INPUT_COOLDOWN := 0.15

# SPELL_SELECT state: the menu shows the caster's known spells as resolved
# SpellDefinition resources. _pending_cast stores the spell currently being
# targeted (non-self spells transition to TARGET_SELECT after the caster
# picks a spell).
var _spell_menu: Array[Resource] = []
var _pending_cast: Resource = null

func start_battle(p_party: Array[Combatant], p_enemies: Array[Combatant], p_ui: Control) -> void:
	party = p_party
	enemies = p_enemies
	ui = p_ui
	state = State.INTRO
	_turn_commands.clear()
	_current_member_idx = 0

	if ui:
		ui.set("enemies", enemies)
		ui.set("party", party)
		ui.set("show_menu", false)
		ui.set("show_target_select", false)

	var enemy_names = []
	for e in enemies:
		enemy_names.append(e.combatant_name)
	_add_message("%s appeared!" % " and ".join(enemy_names))
	_message_timer = MESSAGE_DELAY * 2

func _process(delta: float) -> void:
	_input_cooldown -= delta

	match state:
		State.INTRO:
			_process_intro(delta)
		State.COMMAND:
			_process_command(delta)
		State.SPELL_SELECT:
			_process_spell_select(delta)
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
	for member in party:
		member.is_defending = false
	_show_menu_for_current_member()

func _show_menu_for_current_member() -> void:
	while _current_member_idx < party.size() and not party[_current_member_idx].is_alive:
		_current_member_idx += 1

	if _current_member_idx >= party.size():
		_resolve_turn()
		return

	var member = party[_current_member_idx]
	var items: Array = ["Attack"]
	if not member.known_spells.is_empty():
		items.append("Spell")
	items.append_array(["Defend", "Flee"])
	if ui:
		ui.set("show_menu", true)
		ui.set("show_target_select", false)
		ui.set("menu_items", items)
		ui.set("menu_cursor", 0)
		ui.set("current_member_name", member.combatant_name)
	# Tagged print — lets e2e tests assert that a caster's menu includes
	# "Spell" without driving the menu with keyboard input (see note in
	# tests/cast-spell.spec.js on why keyboard navigation is unreliable).
	print("[battle-menu] %s options=%s" % [member.combatant_name, items])
	_input_cooldown = INPUT_COOLDOWN

func _process_command(_delta: float) -> void:
	if _input_cooldown > 0.0:
		return

	if Input.is_action_just_pressed("ui_down"):
		if ui:
			ui.set("menu_cursor", (ui.get("menu_cursor") + 1) % (ui.get("menu_items") as Array).size())
		_input_cooldown = INPUT_COOLDOWN
	elif Input.is_action_just_pressed("ui_up"):
		if ui:
			var items: Array = ui.get("menu_items")
			ui.set("menu_cursor", (ui.get("menu_cursor") - 1 + items.size()) % items.size())
		_input_cooldown = INPUT_COOLDOWN
	elif Input.is_action_just_pressed("ui_accept") or Input.is_action_just_pressed("interact"):
		var selected: String = ""
		if ui:
			var items: Array = ui.get("menu_items")
			selected = items[ui.get("menu_cursor")]
		_input_cooldown = INPUT_COOLDOWN
		match selected:
			"Attack":
				_pending_cast = null
				_start_target_select()
			"Spell":
				_start_spell_select()
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

func _start_spell_select() -> void:
	state = State.SPELL_SELECT
	var member = party[_current_member_idx]
	_spell_menu.clear()
	var labels: Array[String] = []
	for spell_id in member.known_spells:
		var def := ContentManager.get_spell_definition(spell_id) as SpellDefinition
		if def == null:
			push_warning("BattleManager: unknown spell id '%s'" % spell_id)
			continue
		_spell_menu.append(def)
		labels.append("%s (MP %d)" % [def.display_name, def.mp_cost])
	if _spell_menu.is_empty():
		# Shouldn't happen — _show_menu_for_current_member only offered
		# "Spell" when the caster had known_spells. Fail soft.
		_add_message("%s has no spells." % member.combatant_name)
		state = State.COMMAND
		_show_menu_for_current_member()
		return
	if ui:
		ui.set("show_menu", true)
		ui.set("show_target_select", false)
		ui.set("menu_items", labels)
		ui.set("menu_cursor", 0)
	_input_cooldown = INPUT_COOLDOWN


func _process_spell_select(_delta: float) -> void:
	if _input_cooldown > 0.0:
		return
	if Input.is_action_just_pressed("ui_down"):
		if ui:
			ui.set("menu_cursor", (ui.get("menu_cursor") + 1) % _spell_menu.size())
		_input_cooldown = INPUT_COOLDOWN
	elif Input.is_action_just_pressed("ui_up"):
		if ui:
			ui.set("menu_cursor", (ui.get("menu_cursor") - 1 + _spell_menu.size()) % _spell_menu.size())
		_input_cooldown = INPUT_COOLDOWN
	elif Input.is_action_just_pressed("ui_cancel") or Input.is_key_pressed(KEY_BACKSPACE):
		state = State.COMMAND
		_show_menu_for_current_member()
		_input_cooldown = INPUT_COOLDOWN
	elif Input.is_action_just_pressed("ui_accept") or Input.is_action_just_pressed("interact"):
		var cursor: int = ui.get("menu_cursor") if ui else 0
		var spell: SpellDefinition = _spell_menu[cursor] as SpellDefinition
		var member = party[_current_member_idx]
		if member.mp < spell.mp_cost:
			# Not enough MP — flash + stay on the spell menu.
			_add_message("Not enough MP for %s." % spell.display_name)
			_input_cooldown = INPUT_COOLDOWN
			return
		_pending_cast = spell
		_input_cooldown = INPUT_COOLDOWN
		match spell.target_kind:
			"self":
				_turn_commands.append({
					"actor": member,
					"action": "cast",
					"target": member,
					"spell": spell,
				})
				_pending_cast = null
				_current_member_idx += 1
				state = State.COMMAND
				_show_menu_for_current_member()
			"enemy":
				_start_target_select()
			_:
				push_warning("BattleManager: unhandled target_kind '%s' for spell '%s'" % [spell.target_kind, spell.id])
				state = State.COMMAND
				_show_menu_for_current_member()


func _start_target_select() -> void:
	state = State.TARGET_SELECT
	if ui:
		ui.set("show_menu", false)
		ui.set("show_target_select", true)
		ui.set("target_cursor", 0)
	for i in enemies.size():
		if enemies[i].is_alive:
			if ui:
				ui.set("target_cursor", i)
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
		var target_enemy: Combatant = enemies[ui.get("target_cursor") if ui else 0]
		if _pending_cast != null:
			_turn_commands.append({
				"actor": member,
				"action": "cast",
				"target": target_enemy,
				"spell": _pending_cast,
			})
			_pending_cast = null
		else:
			_turn_commands.append({
				"actor": member,
				"action": "attack",
				"target": target_enemy,
			})
		if ui:
			ui.set("show_target_select", false)
		_current_member_idx += 1
		state = State.COMMAND
		_show_menu_for_current_member()
		_input_cooldown = INPUT_COOLDOWN
	elif Input.is_action_just_pressed("ui_cancel") or Input.is_key_pressed(KEY_BACKSPACE):
		if ui:
			ui.set("show_target_select", false)
		# If cancel'd during a cast targeting step, go back to the spell
		# menu rather than the top-level command menu — matches DQ UX.
		if _pending_cast != null:
			_pending_cast = null
			_start_spell_select()
		else:
			state = State.COMMAND
			_show_menu_for_current_member()
		_input_cooldown = INPUT_COOLDOWN

func _move_target_cursor(dir: int) -> void:
	if not ui:
		return
	var cursor: int = ui.get("target_cursor")
	cursor = (cursor + dir + enemies.size()) % enemies.size()
	ui.set("target_cursor", cursor)
	var attempts = 0
	while not enemies[ui.get("target_cursor")].is_alive and attempts < enemies.size():
		cursor = (ui.get("target_cursor") + dir + enemies.size()) % enemies.size()
		ui.set("target_cursor", cursor)
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
		if ui:
			ui.set("show_menu", false)
		state = State.FLEE
		_message_timer = MESSAGE_DELAY * 2
	else:
		_add_message("Couldn't escape!")
		_turn_commands.clear()
		_resolve_turn()

func _resolve_turn() -> void:
	state = State.RESOLVE
	if ui:
		ui.set("show_menu", false)
		ui.set("show_target_select", false)

	for enemy in enemies:
		if enemy.is_alive:
			var alive_party = party.filter(func(m): return m.is_alive)
			if alive_party.is_empty():
				break
			var target = alive_party[randi() % alive_party.size()]
			_turn_commands.append({
				"actor": enemy,
				"action": "attack",
				"target": target,
			})

	_turn_commands.sort_custom(func(a, b): return a["actor"].spd > b["actor"].spd)

	for cmd in _turn_commands:
		var actor: Combatant = cmd["actor"]
		var target: Combatant = cmd["target"]
		if not actor.is_alive:
			continue
		match cmd["action"]:
			"attack":
				if not target.is_alive:
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
			"cast":
				var spell: SpellDefinition = cmd.get("spell") as SpellDefinition
				_apply_cast(actor, target, spell)
			"defend":
				_add_message("%s defends." % actor.combatant_name)

	_message_timer = MESSAGE_DELAY * _turn_commands.size()
	_turn_commands.clear()

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

# Applies a queued "cast" command: pays MP, rolls power, and applies the
# effect to `target`. Extracted from the turn-resolution switch so GUT can
# test the math directly without driving the state machine + input layer
# through Playwright (see tests/test_battle_manager_cast.gd).
#
# Preconditions enforced here rather than at the caller so tests exercise
# the real guard paths:
#   - spell == null -> log fumble, return
#   - mp shortfall -> log shortfall, return (no MP spent)
#   - damage target dead -> redirect to an alive counterpart, or skip
#
# Returns true iff the cast resolved (MP spent + effect applied or redirected).
func _apply_cast(actor: Combatant, target: Combatant, spell: SpellDefinition) -> bool:
	if spell == null:
		_add_message("%s fumbles a spell!" % actor.combatant_name)
		return false
	if actor.mp < spell.mp_cost:
		_add_message("%s lacks MP for %s." % [actor.combatant_name, spell.display_name])
		return false
	actor.mp -= spell.mp_cost
	_add_message("%s casts %s!" % [actor.combatant_name, spell.display_name])
	var amount := randi_range(spell.power_min, spell.power_max)
	match spell.effect_kind:
		"damage":
			# DQ1-style: spell damage bypasses defense.
			if not target.is_alive:
				var alive_pool: Array = (party if actor.is_enemy else enemies).filter(
					func(c): return c.is_alive
				)
				if alive_pool.is_empty():
					return true
				target = alive_pool[randi() % alive_pool.size()]
			target.hp = maxi(0, target.hp - amount)
			_add_message("%s takes %d damage." % [target.combatant_name, amount])
			if not target.is_alive:
				_add_message("%s is defeated!" % target.combatant_name)
		"heal":
			var restored := mini(amount, target.max_hp - target.hp)
			target.hp += restored
			_add_message("%s recovers %d HP." % [target.combatant_name, restored])
		_:
			_add_message("(spell had no effect)")
	return true


func _add_message(text: String) -> void:
	ActivityLog.log_msg(text)
	if ui and ui.has_method("show_flash"):
		ui.show_flash(text)
