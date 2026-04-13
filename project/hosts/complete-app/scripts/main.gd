# scripts/main.gd
extends Control

const MAP_WIDTH := 10
const MAP_HEIGHT := 8
const TILE_SIZE := 32

# Father's map: small town with paths, buildings, water
# 0=grass, 1=path, 2=building, 3=water (references atlas coords)
const FATHER_MAP := [
	[0,0,0,2,2,0,0,0,3,3],
	[0,0,1,1,1,1,0,0,3,3],
	[0,1,1,0,0,1,1,0,0,3],
	[2,1,0,0,0,0,1,0,0,0],
	[2,1,0,0,0,0,1,1,1,0],
	[0,1,1,0,2,0,0,0,1,0],
	[0,0,1,1,1,1,1,1,1,0],
	[0,0,0,0,0,0,0,0,0,0],
]

# Son's map: same layout but ruined
# 0=dead_grass, 1=path, 2=ruin, 3=blocked
const SON_MAP := [
	[0,0,0,2,2,0,0,0,3,3],
	[0,0,1,1,1,1,0,0,3,3],
	[0,1,1,0,0,1,1,0,0,3],
	[2,1,0,0,0,0,1,0,0,0],
	[2,1,0,0,0,0,1,1,1,0],
	[0,1,1,0,2,0,0,0,1,0],
	[0,0,1,1,1,1,1,1,1,0],
	[0,0,0,0,0,0,0,0,0,0],
]

const BOULDER_COL := 5
const BOULDER_ROW := 3
const BLOCKED_COL := 5
const BLOCKED_ROW := 3

var world: World
var tileset: TileSet

var father_view: SubViewportContainer
var son_view: SubViewportContainer
var father_player: E_Player
var son_player: E_Player
var father_tilemap: TileMapLayer
var son_tilemap: TileMapLayer
var boulder_entity: E_Interactable
var blocked_entity: E_Interactable

var active_era: C_TimelineEra.Era = C_TimelineEra.Era.FATHER
var map_is_open := false

const ACTIVE_VIEW_SCALE := 0.50
const INACTIVE_VIEW_SCALE := 0.40

# Visual nodes (Node2D) that live in SubViewports — synced from ECS data.
var _visuals: Array[EntityVisual] = []

# Debug HUD
var _debug_label: Label

# Battle state
var in_battle := false
var _battle_manager: BattleManager = null
var _battle_ui: BattleUI = null
var _battle_enemy_entity: E_Enemy = null
var _battle_enemy_visual: EntityVisual = null
var _ws_client: Node = null

# Enemy entities
var _enemy_entities: Array[E_Enemy] = []
var _enemy_visuals: Array[EntityVisual] = []

func _ready() -> void:
	LocationManager.load_location("whispering-woods")
	tileset = LocationManager.get_tileset()

	# Create ECS World — entities live here as children of the World node.
	world = World.new()
	world.name = "World"
	add_child(world)
	ECS.world = world

	_build_world_map()

	father_view = _build_game_view(C_TimelineEra.Era.FATHER, FATHER_MAP, 0)
	son_view = _build_game_view(C_TimelineEra.Era.SON, SON_MAP, 1)
	add_child(father_view)
	add_child(son_view)

	# Store tilemap references as metadata for systems to find.
	world.set_meta("father_tilemap", father_tilemap)
	world.set_meta("son_tilemap", son_tilemap)

	# --- Spawn entities (GECS manages tree placement) ---
	father_player = E_Player.new()
	father_player.era = C_TimelineEra.Era.FATHER
	father_player.start_col = 2
	father_player.start_row = 2
	father_player.name = "FatherPlayer"
	ECS.world.add_entity(father_player)

	son_player = E_Player.new()
	son_player.era = C_TimelineEra.Era.SON
	son_player.start_col = 7
	son_player.start_row = 4
	son_player.name = "SonPlayer"
	ECS.world.add_entity(son_player)

	boulder_entity = E_Interactable.new()
	boulder_entity.era = C_TimelineEra.Era.FATHER
	boulder_entity.start_col = BOULDER_COL
	boulder_entity.start_row = BOULDER_ROW
	boulder_entity.interact_type = C_Interactable.InteractType.BOULDER
	boulder_entity.id = "boulder_father"
	boulder_entity.linked_id = "blocked_son"
	boulder_entity.name = "Boulder"
	ECS.world.add_entity(boulder_entity)

	blocked_entity = E_Interactable.new()
	blocked_entity.era = C_TimelineEra.Era.SON
	blocked_entity.start_col = BLOCKED_COL
	blocked_entity.start_row = BLOCKED_ROW
	blocked_entity.interact_type = C_Interactable.InteractType.BOULDER
	blocked_entity.id = "blocked_son"
	blocked_entity.linked_id = "boulder_father"
	blocked_entity.name = "BlockedPath"
	ECS.world.add_entity(blocked_entity)

	# --- Create visual sprites in SubViewports ---
	_create_visual(father_view, father_player, EntityVisual.VisualType.PLAYER_FATHER)
	_create_visual(son_view, son_player, EntityVisual.VisualType.PLAYER_SON)
	_create_visual(father_view, boulder_entity, EntityVisual.VisualType.BOULDER)
	_create_visual(son_view, blocked_entity, EntityVisual.VisualType.BLOCKED)

	# Register systems
	var input_system = S_PlayerInput.new()
	var movement_system = S_GridMovement.new()
	var action_processor = S_ActionProcessor.new()
	world.add_systems([input_system, movement_system, action_processor])

	# Debug HUD (top-right corner, above everything)
	_debug_label = Label.new()
	_debug_label.name = "DebugHUD"
	_debug_label.add_theme_font_size_override("font_size", 11)
	_debug_label.add_theme_color_override("font_color", Color.WHITE)
	_debug_label.add_theme_color_override("font_shadow_color", Color.BLACK)
	_debug_label.add_theme_constant_override("shadow_offset_x", 1)
	_debug_label.add_theme_constant_override("shadow_offset_y", 1)
	_debug_label.position = Vector2(10, 10)
	_debug_label.z_index = 100
	# Use a CanvasLayer so it's always on top
	var hud_layer = CanvasLayer.new()
	hud_layer.layer = 100
	hud_layer.name = "DebugHUDLayer"
	add_child(hud_layer)
	hud_layer.add_child(_debug_label)

	# --- Spawn overworld enemies ---
	_spawn_enemy(C_TimelineEra.Era.FATHER, 4, 4, "slime")
	_spawn_enemy(C_TimelineEra.Era.FATHER, 7, 6, "slime")

	# --- WebSocket client ---
	var ws_client_script = preload("res://scripts/ws_client.gd")
	var ws_client = ws_client_script.new()
	ws_client.name = "WSClient"
	add_child(ws_client)
	_ws_client = ws_client

	GameActions.action_switch_era.connect(_switch_active_era)
	GameActions.state_changed.connect(func(event_name: String, data: Dictionary):
		_ws_client.send_state_event(event_name, data)
	)

	_update_layout()
	get_viewport().size_changed.connect(_update_layout)

func _create_visual(view: SubViewportContainer, entity: Entity, type: EntityVisual.VisualType) -> void:
	var visual = EntityVisual.new()
	visual.visual_type = type
	visual.entity = entity
	var grid_pos = entity.get_component(C_GridPosition) as C_GridPosition
	if grid_pos:
		visual.position = Vector2(grid_pos.visual_x, grid_pos.visual_y)
	view.get_node("SubViewport").add_child(visual)
	_visuals.append(visual)

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

func _check_enemy_encounter() -> void:
	var active_player = father_player if active_era == C_TimelineEra.Era.FATHER else son_player
	var player_gp = active_player.get_component(C_GridPosition) as C_GridPosition
	var player_era = active_player.get_component(C_TimelineEra) as C_TimelineEra
	if not player_gp or not player_era:
		return

	var face_col = player_gp.col + player_gp.facing.x
	var face_row = player_gp.row + player_gp.facing.y

	for i in _enemy_entities.size():
		var enemy = _enemy_entities[i]
		var e_era = enemy.get_component(C_TimelineEra) as C_TimelineEra
		if e_era.era != player_era.era:
			continue
		var e_gp = enemy.get_component(C_GridPosition) as C_GridPosition
		if e_gp.col == face_col and e_gp.row == face_row:
			if Input.is_action_just_pressed("ui_accept") or Input.is_action_just_pressed("interact"):
				_start_battle(enemy, _enemy_visuals[i])
				return

func _start_battle(enemy_entity: E_Enemy, enemy_visual: EntityVisual) -> void:
	in_battle = true
	_battle_enemy_entity = enemy_entity
	_battle_enemy_visual = enemy_visual

	var active_view = father_view if active_era == C_TimelineEra.Era.FATHER else son_view
	var viewport = active_view.get_node("SubViewport")

	_battle_ui = BattleUI.new()
	_battle_ui.name = "BattleUI"
	_battle_ui.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	_battle_ui.z_index = 100
	viewport.add_child(_battle_ui)

	_battle_manager = BattleManager.new()
	_battle_manager.name = "BattleManager"
	add_child(_battle_manager)
	_battle_manager.battle_ended.connect(_on_battle_ended)

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

	if _battle_ui:
		_battle_ui.queue_free()
		_battle_ui = null
	if _battle_manager:
		_battle_manager.battle_ended.disconnect(_on_battle_ended)
		_battle_manager.queue_free()
		_battle_manager = null

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

	if not result.get("won", false) and not result.get("fled", false):
		get_tree().reload_current_scene()

func _input(event: InputEvent) -> void:
	if in_battle:
		return  # Battle manager handles input
	# Tab toggles active era
	if event is InputEventKey and event.pressed and event.keycode == KEY_TAB:
		get_viewport().set_input_as_handled()
		GameActions.switch_era()
	# M toggles world map
	if event is InputEventKey and event.pressed and event.keycode == KEY_M:
		get_viewport().set_input_as_handled()
		_toggle_map()

func _process(delta: float) -> void:
	if in_battle:
		return  # BattleManager drives its own _process
	ECS.process(delta)
	_sync_visuals()
	_update_cameras()
	_update_debug_hud()
	_check_enemy_encounter()

func _sync_visuals() -> void:
	for visual in _visuals:
		if not visual.entity:
			continue
		var grid_pos = visual.entity.get_component(C_GridPosition) as C_GridPosition
		if grid_pos:
			visual.position = Vector2(grid_pos.visual_x, grid_pos.visual_y)
		# Hide interactables that have been activated
		if visual.entity.has_component(C_Interactable):
			var interact = visual.entity.get_component(C_Interactable) as C_Interactable
			visual.visible = (interact.state == C_Interactable.InteractState.DEFAULT)

func _update_cameras() -> void:
	var active_player = father_player if active_era == C_TimelineEra.Era.FATHER else son_player
	var inactive_player = son_player if active_era == C_TimelineEra.Era.FATHER else father_player
	var active_view = father_view if active_era == C_TimelineEra.Era.FATHER else son_view
	var inactive_view = son_view if active_era == C_TimelineEra.Era.FATHER else father_view

	var active_cam = active_view.get_node("SubViewport/Camera2D") as Camera2D
	var inactive_cam = inactive_view.get_node("SubViewport/Camera2D") as Camera2D

	# Follow players via component data (entities don't have position).
	var active_gp = active_player.get_component(C_GridPosition) as C_GridPosition
	var inactive_gp = inactive_player.get_component(C_GridPosition) as C_GridPosition
	if active_gp:
		var target = Vector2(active_gp.visual_x + TILE_SIZE / 2.0, active_gp.visual_y + TILE_SIZE / 2.0)
		active_cam.position = active_cam.position.lerp(target, 0.1)
	if inactive_gp:
		var target = Vector2(inactive_gp.visual_x + TILE_SIZE / 2.0, inactive_gp.visual_y + TILE_SIZE / 2.0)
		inactive_cam.position = inactive_cam.position.lerp(target, 0.1)

func _switch_active_era() -> void:
	if active_era == C_TimelineEra.Era.FATHER:
		active_era = C_TimelineEra.Era.SON
		father_player.get_component(C_PlayerControlled).active = false
		son_player.get_component(C_PlayerControlled).active = true
	else:
		active_era = C_TimelineEra.Era.FATHER
		father_player.get_component(C_PlayerControlled).active = true
		son_player.get_component(C_PlayerControlled).active = false
	_update_layout()
	LocationManager.swap_era(active_era)
	# Emit state change for WS
	GameActions.state_changed.emit("era_switched", {
		"active_era": "FATHER" if active_era == C_TimelineEra.Era.FATHER else "SON",
		"active_entity_id": "father" if active_era == C_TimelineEra.Era.FATHER else "son",
	})

func _toggle_map() -> void:
	map_is_open = not map_is_open
	_update_layout()

func _update_layout() -> void:
	var viewport_size = get_viewport_rect().size
	var active_view_node: SubViewportContainer
	var inactive_view_node: SubViewportContainer

	if active_era == C_TimelineEra.Era.FATHER:
		active_view_node = father_view
		inactive_view_node = son_view
	else:
		active_view_node = son_view
		inactive_view_node = father_view

	if map_is_open:
		var tween = create_tween().set_parallel(true)
		tween.tween_property(active_view_node, "position",
			Vector2(-active_view_node.size.x - 20, active_view_node.position.y), 0.4) \
			.set_ease(Tween.EASE_IN_OUT).set_trans(Tween.TRANS_CUBIC)
		tween.tween_property(inactive_view_node, "position",
			Vector2(viewport_size.x + 20, inactive_view_node.position.y), 0.4) \
			.set_ease(Tween.EASE_IN_OUT).set_trans(Tween.TRANS_CUBIC)
	else:
		var active_w = viewport_size.x * ACTIVE_VIEW_SCALE
		var active_h = viewport_size.y * ACTIVE_VIEW_SCALE
		var active_pos = Vector2(20, 20)

		var inactive_w = viewport_size.x * INACTIVE_VIEW_SCALE
		var inactive_h = viewport_size.y * INACTIVE_VIEW_SCALE
		var inactive_pos = Vector2(
			viewport_size.x - inactive_w - 20,
			viewport_size.y - inactive_h - 20
		)

		active_view_node.size = Vector2(active_w, active_h)
		active_view_node.get_node("SubViewport").size = Vector2i(int(active_w), int(active_h))
		inactive_view_node.size = Vector2(inactive_w, inactive_h)
		inactive_view_node.get_node("SubViewport").size = Vector2i(int(inactive_w), int(inactive_h))

		# Active view in front
		move_child(active_view_node, get_child_count() - 1)

		var tween = create_tween().set_parallel(true)
		tween.tween_property(active_view_node, "position", active_pos, 0.3) \
			.set_ease(Tween.EASE_IN_OUT).set_trans(Tween.TRANS_CUBIC)
		tween.tween_property(inactive_view_node, "position", inactive_pos, 0.3) \
			.set_ease(Tween.EASE_IN_OUT).set_trans(Tween.TRANS_CUBIC)

		active_view_node.modulate.a = 1.0
		inactive_view_node.modulate.a = 0.75

func _build_game_view(era: C_TimelineEra.Era, map_data: Array, source_id: int) -> SubViewportContainer:
	var container = SubViewportContainer.new()
	container.stretch = true
	container.mouse_filter = Control.MOUSE_FILTER_IGNORE

	var viewport = SubViewport.new()
	viewport.name = "SubViewport"
	viewport.transparent_bg = false
	viewport.canvas_item_default_texture_filter = SubViewport.DEFAULT_CANVAS_ITEM_TEXTURE_FILTER_NEAREST
	container.add_child(viewport)

	# TileMapLayer
	var tilemap = TileMapLayer.new()
	tilemap.name = "TileMapLayer"
	tilemap.tile_set = tileset
	viewport.add_child(tilemap)

	# Populate tiles
	for row in range(MAP_HEIGHT):
		for col in range(MAP_WIDTH):
			var atlas_coord = Vector2i(map_data[row][col], 0)
			tilemap.set_cell(Vector2i(col, row), source_id, atlas_coord)

	# Store tilemap reference
	if era == C_TimelineEra.Era.FATHER:
		father_tilemap = tilemap
	else:
		son_tilemap = tilemap

	# Camera centered on map
	var camera = Camera2D.new()
	camera.name = "Camera2D"
	camera.position = Vector2(MAP_WIDTH * TILE_SIZE / 2.0, MAP_HEIGHT * TILE_SIZE / 2.0)
	viewport.add_child(camera)

	# Era label overlay
	var label = Label.new()
	label.name = "EraLabel"
	var era_text = "FATHER ERA" if era == C_TimelineEra.Era.FATHER else "SON ERA"
	label.text = era_text
	label.add_theme_font_size_override("font_size", 12)
	label.position = Vector2(8, 4)
	if era == C_TimelineEra.Era.FATHER:
		label.add_theme_color_override("font_color", Color(1.0, 0.8, 0.0))
	else:
		label.add_theme_color_override("font_color", Color(1.0, 0.53, 0.53))
	container.add_child(label)

	return container

func _build_world_map() -> void:
	var world_map_layer = CanvasLayer.new()
	world_map_layer.name = "WorldMapLayer"
	world_map_layer.layer = -1
	add_child(world_map_layer)

	var bg = ColorRect.new()
	bg.name = "MapBackground"
	bg.color = Color(0.77, 0.64, 0.40)
	bg.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	world_map_layer.add_child(bg)

	var locations = {
		"Aldenmere": Vector2(0.35, 0.35),
		"Haven Town": Vector2(0.65, 0.55),
		"Iron Peaks": Vector2(0.55, 0.15),
		"Silverwood": Vector2(0.2, 0.3),
		"Ashenmoor": Vector2(0.3, 0.75),
		"Duskholm": Vector2(0.8, 0.7),
	}

	for loc_name in locations:
		var label = Label.new()
		label.text = loc_name
		label.add_theme_font_size_override("font_size", 14)
		label.add_theme_color_override("font_color", Color(0.35, 0.24, 0.11))
		label.name = "Loc_" + loc_name.replace(" ", "")
		label.position = locations[loc_name] * Vector2(1024, 600)
		world_map_layer.add_child(label)

func _update_debug_hud() -> void:
	if not _debug_label:
		return
	var active_player = father_player if active_era == C_TimelineEra.Era.FATHER else son_player
	var era_name = "FATHER" if active_era == C_TimelineEra.Era.FATHER else "SON"
	var gp = active_player.get_component(C_GridPosition) as C_GridPosition
	var facing_name = "?"
	if gp:
		if gp.facing == Vector2i.UP: facing_name = "UP"
		elif gp.facing == Vector2i.DOWN: facing_name = "DOWN"
		elif gp.facing == Vector2i.LEFT: facing_name = "LEFT"
		elif gp.facing == Vector2i.RIGHT: facing_name = "RIGHT"

	var target_col = gp.col + gp.facing.x if gp else 0
	var target_row = gp.row + gp.facing.y if gp else 0

	# Check what's at the facing tile
	var facing_content = "empty"
	var interactables = ECS.world.query.with_all([C_Interactable, C_GridPosition, C_TimelineEra]).execute()
	for e in interactables:
		var e_era = e.get_component(C_TimelineEra) as C_TimelineEra
		if e_era.era != active_era:
			continue
		var e_pos = e.get_component(C_GridPosition) as C_GridPosition
		if e_pos.col == target_col and e_pos.row == target_row:
			var interact = e.get_component(C_Interactable) as C_Interactable
			facing_content = "BOULDER (%s)" % ("active" if interact.state == C_Interactable.InteractState.DEFAULT else "DONE")
			break

	var boulder_state = boulder_entity.get_component(C_Interactable) as C_Interactable
	var blocked_state = blocked_entity.get_component(C_Interactable) as C_Interactable

	var entity_count = ECS.world.query.with_all([C_GridPosition]).execute().size()

	_debug_label.text = (
		"Era: %s | Pos: (%d,%d) | Facing: %s\n" % [era_name, gp.col if gp else 0, gp.row if gp else 0, facing_name]
		+ "Looking at: (%d,%d) = %s\n" % [target_col, target_row, facing_content]
		+ "Boulder: %s | Blocked: %s\n" % [
			"DEFAULT" if boulder_state.state == C_Interactable.InteractState.DEFAULT else "ACTIVATED",
			"DEFAULT" if blocked_state.state == C_Interactable.InteractState.DEFAULT else "ACTIVATED"]
		+ "Entities in world: %d\n" % entity_count
		+ "Controls: Arrows=move | Tab=switch era | M=map | E=interact"
	)
