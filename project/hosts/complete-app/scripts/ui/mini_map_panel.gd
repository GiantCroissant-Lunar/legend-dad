# scripts/ui/mini_map_panel.gd
# Small windowed panel in top-right showing simplified map grid.
class_name MiniMapPanel
extends Control

const BG_COLOR = Color(0.05, 0.05, 0.15, 0.85)
const BORDER_COLOR = Color(0.6, 0.7, 0.9, 0.8)
const HEADER_COLOR = Color(0.6, 0.7, 0.9)
const WALKABLE_COLOR = Color(0.15, 0.2, 0.15)
const BLOCKED_COLOR = Color(0.3, 0.3, 0.35)
const PLAYER_COLOR = Color(1.0, 0.8, 0.0)
const ENEMY_COLOR = Color(0.8, 0.2, 0.2)
const BORDER_WIDTH = 2.0
const PADDING = 8.0

func _process(_delta: float) -> void:
	queue_redraw()

func _draw() -> void:
	var sz = size

	# Background + border
	draw_rect(Rect2(Vector2.ZERO, sz), BG_COLOR)
	draw_rect(Rect2(Vector2.ZERO, sz), BORDER_COLOR, false, BORDER_WIDTH)

	# Header
	var header_y: float = PADDING + 10.0
	draw_string(ThemeDB.fallback_font, Vector2(PADDING, header_y), "Map",
		HORIZONTAL_ALIGNMENT_LEFT, -1, 10, HEADER_COLOR)

	var map_w: int = GameConfig.map_width
	var map_h: int = GameConfig.map_height
	if map_w <= 0 or map_h <= 0:
		return

	# Grid area below header
	var grid_top: float = header_y + 6.0
	var grid_area_w: float = sz.x - PADDING * 2
	var grid_area_h: float = sz.y - grid_top - PADDING
	var dot_size: float = minf(grid_area_w / map_w, grid_area_h / map_h)
	dot_size = minf(dot_size, 8.0)

	var grid_offset_x: float = PADDING + (grid_area_w - dot_size * map_w) / 2.0
	var grid_offset_y: float = grid_top + (grid_area_h - dot_size * map_h) / 2.0

	# Get collision grid for active era
	var active_era: C_TimelineEra.Era = _get_active_era()
	var collision_grid: Dictionary = LocationManager.get_collision_grid(active_era)

	# Draw grid cells
	for row in range(map_h):
		for col in range(map_w):
			var rect_pos = Vector2(
				grid_offset_x + col * dot_size,
				grid_offset_y + row * dot_size
			)
			var cell_rect = Rect2(rect_pos, Vector2(dot_size - 1, dot_size - 1))
			var key = Vector2i(col, row)
			var walkable: bool = collision_grid.get(key, true)
			draw_rect(cell_rect, WALKABLE_COLOR if walkable else BLOCKED_COLOR)

	# Draw entities (player + enemies)
	var entities = ECS.world.query.with_all([C_GridPosition, C_TimelineEra]).execute()
	for entity in entities:
		var e_era = entity.get_component(C_TimelineEra) as C_TimelineEra
		if e_era.era != active_era:
			continue
		var gp = entity.get_component(C_GridPosition) as C_GridPosition
		var dot_pos = Vector2(
			grid_offset_x + gp.col * dot_size + dot_size * 0.15,
			grid_offset_y + gp.row * dot_size + dot_size * 0.15
		)
		var dot_rect = Rect2(dot_pos, Vector2(dot_size * 0.7, dot_size * 0.7))

		if entity.has_component(C_PlayerControlled):
			draw_rect(dot_rect, PLAYER_COLOR)
		elif entity.has_component(C_Enemy):
			draw_rect(dot_rect, ENEMY_COLOR)

func _get_active_era() -> C_TimelineEra.Era:
	var main_node = get_tree().current_scene
	if main_node and "active_era" in main_node:
		return main_node.active_era
	return C_TimelineEra.Era.FATHER
