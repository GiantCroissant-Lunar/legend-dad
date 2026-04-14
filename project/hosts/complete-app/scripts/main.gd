# scripts/main.gd
extends Control

# Level dimensions from LDtk (set at runtime)
var map_width := 0
var map_height := 0

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

# LDtk parsed layer data
var _base_terrain_tiles: Array = []
var _father_terrain_tiles: Array = []
var _son_terrain_tiles: Array = []
var _collision_csv: Array = []
var _collision_grid_width: int = 0

const ACTIVE_VIEW_SCALE := 0.50
const INACTIVE_VIEW_SCALE := 0.40

# Visual nodes (Node2D) that live in SubViewports — synced from ECS data.
var _visuals: Array[EntityVisual] = []

# Debug HUD
var _debug_label: Label

# Battle state
var in_battle := false
var _battle_manager: BattleManager = null
var _battle_overlay: BattleOverlay = null
var _battle_enemy_entity: E_Enemy = null
var _battle_enemy_visual: EntityVisual = null
var _ws_client: Node = null

# HUD layer (z=50) — hosts activity log, mini-map, battle overlay
var _hud_layer: CanvasLayer = null
var _activity_log_panel: ActivityLogPanel = null
var _mini_map_panel: MiniMapPanel = null

# Enemy entities
var _enemy_entities: Array[E_Enemy] = []
var _enemy_visuals: Array[EntityVisual] = []

func _ready() -> void:
	await LocationManager.load_location("whispering-woods")
	tileset = LocationManager.get_tileset()

	# Load level layout from LDtk
	_load_ldtk_level("Whispering_Woods_Edge")

	# Fallback: if LDtk has no painted tiles, use hardcoded test layout
	if _base_terrain_tiles.is_empty() and _father_terrain_tiles.is_empty() and _son_terrain_tiles.is_empty():
		push_warning("main: No LDtk terrain tiles found, using fallback layout")
		_generate_fallback_layout()

	# Create ECS World — entities live here as children of the World node.
	world = World.new()
	world.name = "World"
	add_child(world)
	ECS.world = world

	_build_world_map()

	father_view = _build_game_view(C_TimelineEra.Era.FATHER)
	son_view = _build_game_view(C_TimelineEra.Era.SON)
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
	boulder_entity.start_col = 5
	boulder_entity.start_row = 3
	boulder_entity.interact_type = C_Interactable.InteractType.BOULDER
	boulder_entity.id = "boulder_father"
	boulder_entity.linked_id = "blocked_son"
	boulder_entity.name = "Boulder"
	ECS.world.add_entity(boulder_entity)

	blocked_entity = E_Interactable.new()
	blocked_entity.era = C_TimelineEra.Era.SON
	blocked_entity.start_col = 5
	blocked_entity.start_row = 3
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

	# --- HUD Layer (z=50): activity log, mini-map, battle overlay ---
	_hud_layer = CanvasLayer.new()
	_hud_layer.name = "HUDLayer"
	_hud_layer.layer = 50
	add_child(_hud_layer)

	_activity_log_panel = ActivityLogPanel.new()
	_activity_log_panel.name = "ActivityLogPanel"
	_hud_layer.add_child(_activity_log_panel)

	_mini_map_panel = MiniMapPanel.new()
	_mini_map_panel.name = "MiniMapPanel"
	_hud_layer.add_child(_mini_map_panel)

	ActivityLog.log_msg("Entered Whispering Woods")

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
	GameActions.action_interact.connect(_try_enemy_encounter)
	GameActions.state_changed.connect(func(event_name: String, data: Dictionary):
		_ws_client.send_state_event(event_name, data)
	)

	_update_layout()
	get_viewport().size_changed.connect(_update_layout)
	_ready_complete = true

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

func _try_enemy_encounter() -> void:
	if in_battle or not _ready_complete:
		return
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
			_start_battle(enemy, _enemy_visuals[i])
			return

func _start_battle(enemy_entity: E_Enemy, enemy_visual: EntityVisual) -> void:
	in_battle = true
	_battle_enemy_entity = enemy_entity
	_battle_enemy_visual = enemy_visual

	# Create battle overlay on the HUD layer
	_battle_overlay = BattleOverlay.new()
	_battle_overlay.name = "BattleOverlay"
	_hud_layer.add_child(_battle_overlay)

	# Dim the active view
	var active_view = father_view if active_era == C_TimelineEra.Era.FATHER else son_view
	active_view.modulate.a = 0.5

	# Position the overlay
	_update_hud_layout(get_viewport_rect().size)

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

	ActivityLog.log_battle_start()
	_battle_manager.start_battle(party_combatants, enemy_combatants, _battle_overlay)

func _on_battle_ended(result: Dictionary) -> void:
	in_battle = false

	ActivityLog.log_battle_end()

	if _battle_overlay:
		_battle_overlay.queue_free()
		_battle_overlay = null
	if _battle_manager:
		_battle_manager.battle_ended.disconnect(_on_battle_ended)
		_battle_manager.queue_free()
		_battle_manager = null

	# Restore active view brightness
	var active_view = father_view if active_era == C_TimelineEra.Era.FATHER else son_view
	active_view.modulate.a = 1.0

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

		if result.get("won", false):
			ActivityLog.log_msg("Victory! Gained %d EXP, %d gold." % [result.get("exp", 0), result.get("gold", 0)])
		else:
			ActivityLog.log_msg("Escaped from battle.")

	if not result.get("won", false) and not result.get("fled", false):
		ActivityLog.log_msg("The party was defeated...")
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
	# P toggles pause
	if event is InputEventKey and event.pressed and event.keycode == KEY_P:
		get_viewport().set_input_as_handled()
		if TimeService.get_state()["paused"]:
			TimeService.resume()
		else:
			TimeService.pause()
	# N steps one frame (while paused)
	if event is InputEventKey and event.pressed and event.keycode == KEY_N:
		get_viewport().set_input_as_handled()
		TimeService.step_frame()
	# [ decreases speed
	if event is InputEventKey and event.pressed and event.keycode == KEY_BRACKETLEFT:
		get_viewport().set_input_as_handled()
		var state = TimeService.get_state()
		TimeService.set_speed(state["speed"] - 0.25)
	# ] increases speed
	if event is InputEventKey and event.pressed and event.keycode == KEY_BRACKETRIGHT:
		get_viewport().set_input_as_handled()
		var state = TimeService.get_state()
		TimeService.set_speed(state["speed"] + 0.25)

var _ready_complete := false

func _process(delta: float) -> void:
	if not _ready_complete:
		return  # _ready() still awaiting (PCK fetch, etc.)
	if in_battle:
		return  # BattleManager drives its own _process
	ECS.process(delta)
	_sync_visuals()
	_update_cameras()
	_update_debug_hud()

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
	var cs := GameConfig.cell_size
	if active_gp:
		var target = Vector2(active_gp.visual_x + cs / 2.0, active_gp.visual_y + cs / 2.0)
		active_cam.position = active_cam.position.lerp(target, 0.1)
	if inactive_gp:
		var target = Vector2(inactive_gp.visual_x + cs / 2.0, inactive_gp.visual_y + cs / 2.0)
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
	ActivityLog.log_msg("Switched to %s ERA" % ("FATHER" if active_era == C_TimelineEra.Era.FATHER else "SON"))
	LocationManager.swap_era(active_era)
	# Re-render tilemaps with correct era overlay
	_rerender_tilemap(father_tilemap, C_TimelineEra.Era.FATHER)
	_rerender_tilemap(son_tilemap, C_TimelineEra.Era.SON)
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

		# Update camera zoom to fit map height in each viewport
		_update_camera_zoom(active_view_node, active_h)
		_update_camera_zoom(inactive_view_node, inactive_h)

		# Active view in front
		move_child(active_view_node, get_child_count() - 1)

		var tween = create_tween().set_parallel(true)
		tween.tween_property(active_view_node, "position", active_pos, 0.3) \
			.set_ease(Tween.EASE_IN_OUT).set_trans(Tween.TRANS_CUBIC)
		tween.tween_property(inactive_view_node, "position", inactive_pos, 0.3) \
			.set_ease(Tween.EASE_IN_OUT).set_trans(Tween.TRANS_CUBIC)

		active_view_node.modulate.a = 1.0 if not in_battle else 0.5
		inactive_view_node.modulate.a = 0.75

	# Position HUD panels
	_update_hud_layout(viewport_size)

func _load_ldtk_level(level_name: String) -> void:
	var project = LocationManager.get_ldtk_project()
	if project.is_empty():
		push_warning("main: No LDtk project loaded, using empty level")
		return

	var level_node = LdtkImporter.import_level(project, level_name)
	if not level_node:
		push_warning("main: Level '%s' not found in LDtk project" % level_name)
		return

	# Read level dimensions
	map_width = level_node.get_meta("px_width", 320) / GameConfig.cell_size
	map_height = level_node.get_meta("px_height", 256) / GameConfig.cell_size
	GameConfig.map_width = map_width
	GameConfig.map_height = map_height

	# Extract layer data — prefer autoLayerTiles, fall back to IntGrid CSV
	for child in level_node.get_children():
		var layer_name: String = child.name
		match layer_name:
			"Terrain":
				_base_terrain_tiles = child.get_meta("auto_layer_tiles", [])
				if _base_terrain_tiles.is_empty():
					var csv: Array = child.get_meta("intgrid_csv", [])
					var gw: int = child.get_meta("grid_width", map_width)
					_base_terrain_tiles = LdtkLevelPlacer.intgrid_to_tiles(csv, gw)
			"Terrain_Father":
				_father_terrain_tiles = child.get_meta("auto_layer_tiles", [])
				if _father_terrain_tiles.is_empty():
					var csv: Array = child.get_meta("intgrid_csv", [])
					var gw: int = child.get_meta("grid_width", map_width)
					_father_terrain_tiles = LdtkLevelPlacer.intgrid_to_tiles(csv, gw)
			"Terrain_Son":
				_son_terrain_tiles = child.get_meta("auto_layer_tiles", [])
				if _son_terrain_tiles.is_empty():
					var csv: Array = child.get_meta("intgrid_csv", [])
					var gw: int = child.get_meta("grid_width", map_width)
					_son_terrain_tiles = LdtkLevelPlacer.intgrid_to_tiles(csv, gw)
			"Collision":
				_collision_csv = child.get_meta("intgrid_csv", [])
				_collision_grid_width = child.get_meta("grid_width", map_width)

	# Build collision grids (same collision for both eras by default)
	if not _collision_csv.is_empty():
		var collision_grid = LdtkLevelPlacer.build_collision_grid(_collision_csv, _collision_grid_width)
		LocationManager.set_collision_grid(C_TimelineEra.Era.FATHER, collision_grid)
		LocationManager.set_collision_grid(C_TimelineEra.Era.SON, collision_grid)

	level_node.queue_free()

func _generate_fallback_layout() -> void:
	# Simple 10x8 test layout using atlas coords from TilesetFactory.
	# NOTE: these values are atlas column indices (not IntGrid values),
	# so collision is computed manually here — do not use build_collision_grid.
	# 0=grass/walkable, 1=path/walkable, 2=building/blocked, 3=water/blocked
	var layout = [
		[0,0,0,2,2,0,0,0,3,3],
		[0,0,1,1,1,1,0,0,3,3],
		[0,1,1,0,0,1,1,0,0,3],
		[2,1,0,0,0,0,1,0,0,0],
		[2,1,0,0,0,0,1,1,1,0],
		[0,1,1,0,2,0,0,0,1,0],
		[0,0,1,1,1,1,1,1,1,0],
		[0,0,0,0,0,0,0,0,0,0],
	]
	map_width = 10
	map_height = 8
	GameConfig.map_width = map_width
	GameConfig.map_height = map_height
	for row in range(map_height):
		for col in range(map_width):
			_base_terrain_tiles.append({
				"position": Vector2i(col, row),
				"atlas_coords": Vector2i(layout[row][col], 0),
				"flip": 0,
			})

	# Build collision: tiles 2 and 3 are not walkable
	var collision_grid := {}
	for row in range(map_height):
		for col in range(map_width):
			var value = layout[row][col]
			collision_grid[Vector2i(col, row)] = value < 2  # 0,1 = walkable
	LocationManager.set_collision_grid(C_TimelineEra.Era.FATHER, collision_grid)
	LocationManager.set_collision_grid(C_TimelineEra.Era.SON, collision_grid)

func _build_game_view(era: C_TimelineEra.Era) -> SubViewportContainer:
	var container = SubViewportContainer.new()
	container.stretch = true
	container.mouse_filter = Control.MOUSE_FILTER_IGNORE

	var viewport = SubViewport.new()
	viewport.name = "SubViewport"
	viewport.transparent_bg = false
	viewport.canvas_item_default_texture_filter = SubViewport.DEFAULT_CANVAS_ITEM_TEXTURE_FILTER_NEAREST
	container.add_child(viewport)

	# TileMapLayer
	var tilemap = LocationManager.create_tilemap_for_era(era)
	viewport.add_child(tilemap)

	# Source ID: TilesetFactory uses 0=father, 1=son; PCK tilesets use 0 for both
	var source_id := 0
	if LocationManager.is_using_fallback() and era == C_TimelineEra.Era.SON:
		source_id = 1

	# Place base terrain tiles
	LdtkLevelPlacer.place_tiles(tilemap, _base_terrain_tiles, source_id)

	# Overlay era-specific tiles
	var overlay = _father_terrain_tiles if era == C_TimelineEra.Era.FATHER else _son_terrain_tiles
	LdtkLevelPlacer.place_tiles(tilemap, overlay, source_id)

	# Store tilemap reference
	if era == C_TimelineEra.Era.FATHER:
		father_tilemap = tilemap
	else:
		son_tilemap = tilemap

	# Camera: zoom to fit map height with some padding, follow player later
	var camera = Camera2D.new()
	camera.name = "Camera2D"
	var cs := GameConfig.cell_size
	camera.position = Vector2(map_width * cs / 2.0, map_height * cs / 2.0)
	# Zoom so the map height fills the viewport (tiles stay readable at any resolution)
	var map_pixel_height := float(map_height * cs)
	var target_zoom := 1.0
	if map_pixel_height > 0:
		target_zoom = float(viewport.size.y) / map_pixel_height
	camera.zoom = Vector2(target_zoom, target_zoom)
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

func _update_camera_zoom(view: SubViewportContainer, viewport_height: float) -> void:
	var camera = view.get_node("SubViewport/Camera2D") as Camera2D
	if not camera:
		return
	var map_pixel_height := float(map_height * GameConfig.cell_size)
	if map_pixel_height <= 0:
		return
	var target_zoom := viewport_height / map_pixel_height
	camera.zoom = Vector2(target_zoom, target_zoom)


func _update_hud_layout(viewport_size: Vector2) -> void:
	if _activity_log_panel:
		var log_w := viewport_size.x * 0.35
		var log_h := viewport_size.y * 0.35
		_activity_log_panel.position = Vector2(20, viewport_size.y - log_h - 20)
		_activity_log_panel.size = Vector2(log_w, log_h)

	if _mini_map_panel:
		var map_w := viewport_size.x * 0.15
		var map_h := viewport_size.y * 0.15
		# Ensure minimum usable size
		map_w = maxf(map_w, 100)
		map_h = maxf(map_h, 100)
		_mini_map_panel.position = Vector2(viewport_size.x - map_w - 20, 20)
		_mini_map_panel.size = Vector2(map_w, map_h)

	if _battle_overlay:
		# Same size and position as active view
		var active_w := viewport_size.x * ACTIVE_VIEW_SCALE
		var active_h := viewport_size.y * ACTIVE_VIEW_SCALE
		_battle_overlay.position = Vector2(20, 20)
		_battle_overlay.size = Vector2(active_w, active_h)

func _rerender_tilemap(tilemap: TileMapLayer, era: C_TimelineEra.Era) -> void:
	var source_id := 0
	if LocationManager.is_using_fallback() and era == C_TimelineEra.Era.SON:
		source_id = 1
	tilemap.clear()
	LdtkLevelPlacer.place_tiles(tilemap, _base_terrain_tiles, source_id)
	var overlay = _father_terrain_tiles if era == C_TimelineEra.Era.FATHER else _son_terrain_tiles
	LdtkLevelPlacer.place_tiles(tilemap, overlay, source_id)

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

	var time_state = TimeService.get_state()
	var time_text := ""
	if time_state["paused"]:
		time_text = "Time: PAUSED"
	else:
		time_text = "Time: %.2fx" % time_state["speed"]

	_debug_label.text = (
		"Era: %s | Pos: (%d,%d) | Facing: %s\n" % [era_name, gp.col if gp else 0, gp.row if gp else 0, facing_name]
		+ "Looking at: (%d,%d) = %s\n" % [target_col, target_row, facing_content]
		+ "Boulder: %s | Blocked: %s\n" % [
			"DEFAULT" if boulder_state.state == C_Interactable.InteractState.DEFAULT else "ACTIVATED",
			"DEFAULT" if blocked_state.state == C_Interactable.InteractState.DEFAULT else "ACTIVATED"]
		+ "Entities in world: %d | %s\n" % [entity_count, time_text]
		+ "Controls: Arrows=move | Tab=era | M=map | E=interact | P=pause | N=step | []=speed"
	)
