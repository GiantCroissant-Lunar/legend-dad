class_name BattleManager
extends Node

signal battle_ended(result: Dictionary)

enum State { INTRO, COMMAND, TARGET_SELECT, RESOLVE, VICTORY, DEFEAT, FLEE }

var state: State = State.INTRO
var party: Array[Combatant] = []
var enemies: Array[Combatant] = []
var ui: BattleUI = null

var _current_member_idx: int = 0
var _turn_commands: Array[Dictionary] = []

var _message_queue: Array[String] = []
var _message_timer: float = 0.0
const MESSAGE_DELAY := 0.6

var _input_cooldown: float = 0.0
const INPUT_COOLDOWN := 0.15

func start_battle(p_party: Array[Combatant], p_enemies: Array[Combatant], p_ui: BattleUI) -> void:
	party = p_party
	enemies = p_enemies
	ui = p_ui
	state = State.INTRO
	_turn_commands.clear()
	_current_member_idx = 0

	ui.enemies = enemies
	ui.party = party
	ui.message_lines.clear()
	ui.show_menu = false
	ui.show_target_select = false

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
	elif Input.is_action_just_pressed("ui_cancel") or Input.is_key_pressed(KEY_BACKSPACE):
		ui.show_target_select = false
		state = State.COMMAND
		_show_menu_for_current_member()
		_input_cooldown = INPUT_COOLDOWN

func _move_target_cursor(dir: int) -> void:
	var start = ui.target_cursor
	ui.target_cursor = (ui.target_cursor + dir + enemies.size()) % enemies.size()
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
		_turn_commands.clear()
		_resolve_turn()

func _resolve_turn() -> void:
	state = State.RESOLVE
	ui.show_menu = false
	ui.show_target_select = false

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

func _add_message(text: String) -> void:
	ui.message_lines.append(text)
	if ui.message_lines.size() > 20:
		ui.message_lines.pop_front()
