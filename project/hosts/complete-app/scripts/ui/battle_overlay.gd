# scripts/ui/battle_overlay.gd
# DQ first-person style battle overlay — drawn on a CanvasLayer above game views.
class_name BattleOverlay
extends Control

# --- Colors (DQ-inspired) ---
const BG_COLOR = Color(0.05, 0.05, 0.15)
const BORDER_COLOR = Color(0.6, 0.7, 0.9, 0.8)
const TEXT_COLOR = Color.WHITE
const MENU_HIGHLIGHT = Color(1.0, 0.8, 0.0)
const MENU_NORMAL = Color(0.7, 0.7, 0.7)
const HP_GREEN = Color(0.2, 0.8, 0.2)
const HP_RED = Color(0.8, 0.2, 0.2)
const HP_BAR_BG = Color(0.2, 0.2, 0.2)
const BORDER_WIDTH = 2.0

# Sky gradient
const SKY_TOP = Color(0.05, 0.08, 0.25)
const SKY_BOTTOM = Color(0.15, 0.3, 0.55)
# Ground
const GROUND_TOP = Color(0.12, 0.25, 0.1)
const GROUND_BOTTOM = Color(0.08, 0.15, 0.06)

# --- Zone proportions ---
const MONSTER_ZONE = 0.55
const COMMAND_ZONE = 0.20
const STATUS_ZONE = 0.25

# --- State (set by BattleManager) ---
var enemies: Array[Combatant] = []
var party: Array[Combatant] = []
var menu_items: Array[String] = []
var menu_cursor: int = 0
var show_menu: bool = false
var current_member_name: String = ""
var target_cursor: int = 0
var show_target_select: bool = false
# In-battle message shown briefly in monster zone
var flash_message: String = ""
var _flash_timer: float = 0.0
const FLASH_DURATION = 1.2

func show_flash(text: String) -> void:
	flash_message = text
	_flash_timer = FLASH_DURATION

func _process(delta: float) -> void:
	if _flash_timer > 0.0:
		_flash_timer -= delta
		if _flash_timer <= 0.0:
			flash_message = ""
	queue_redraw()

func _draw() -> void:
	var sz = size

	# Outer background + border
	draw_rect(Rect2(Vector2.ZERO, sz), BG_COLOR)
	draw_rect(Rect2(Vector2.ZERO, sz), BORDER_COLOR, false, BORDER_WIDTH)

	var monster_h: float = sz.y * MONSTER_ZONE
	var command_y: float = monster_h
	var command_h: float = sz.y * COMMAND_ZONE
	var status_y: float = command_y + command_h
	var status_h: float = sz.y * STATUS_ZONE

	_draw_landscape(sz, monster_h)
	_draw_monsters(sz, monster_h)
	_draw_flash_message(sz, monster_h)

	# Divider between monster zone and command zone
	draw_line(Vector2(BORDER_WIDTH, command_y), Vector2(sz.x - BORDER_WIDTH, command_y),
		BORDER_COLOR, 1.0)

	_draw_command_menu(sz, command_y, command_h)

	# Divider between command and status
	draw_line(Vector2(BORDER_WIDTH, status_y), Vector2(sz.x - BORDER_WIDTH, status_y),
		BORDER_COLOR, 1.0)

	_draw_party_status(sz, status_y, status_h)

func _draw_landscape(sz: Vector2, area_h: float) -> void:
	# Sky gradient (top 65% of monster zone)
	var sky_h: float = area_h * 0.65
	var sky_steps: int = 20
	for i in range(sky_steps):
		var t: float = float(i) / sky_steps
		var color: Color = SKY_TOP.lerp(SKY_BOTTOM, t)
		var step_h: float = sky_h / sky_steps
		draw_rect(Rect2(BORDER_WIDTH, BORDER_WIDTH + t * sky_h, sz.x - BORDER_WIDTH * 2, step_h + 1), color)

	# Ground gradient (bottom 35% of monster zone)
	var ground_y: float = sky_h
	var ground_h: float = area_h - sky_h
	var ground_steps: int = 10
	for i in range(ground_steps):
		var t: float = float(i) / ground_steps
		var color: Color = GROUND_TOP.lerp(GROUND_BOTTOM, t)
		var step_h: float = ground_h / ground_steps
		draw_rect(Rect2(BORDER_WIDTH, ground_y + t * ground_h, sz.x - BORDER_WIDTH * 2, step_h + 1), color)

	# Horizon line
	draw_line(Vector2(BORDER_WIDTH, sky_h), Vector2(sz.x - BORDER_WIDTH, sky_h),
		Color(0.3, 0.5, 0.3, 0.5), 1.0)

func _draw_monsters(sz: Vector2, area_h: float) -> void:
	if enemies.is_empty():
		return

	var spacing: float = sz.x / (enemies.size() + 1)
	var ground_y: float = area_h * 0.65

	for i in enemies.size():
		var enemy: Combatant = enemies[i]
		var cx: float = spacing * (i + 1)
		var cy: float = ground_y + (area_h - ground_y) * 0.4

		if enemy.is_alive:
			var sil_w: float = 40.0
			var sil_h: float = 50.0
			var sil_color: Color = Color(0.1, 0.1, 0.12).lerp(enemy.color, 0.3)

			_draw_silhouette(Vector2(cx, cy), sil_w, sil_h, sil_color)

			draw_string(ThemeDB.fallback_font, Vector2(cx - 25, cy + sil_h / 2 + 14),
				enemy.combatant_name, HORIZONTAL_ALIGNMENT_LEFT, -1, 11, TEXT_COLOR)

			var hp_text: String = "%d/%d" % [enemy.hp, enemy.max_hp]
			draw_string(ThemeDB.fallback_font, Vector2(cx - 18, cy + sil_h / 2 + 26),
				hp_text, HORIZONTAL_ALIGNMENT_LEFT, -1, 9, Color(0.6, 0.6, 0.6))
		else:
			_draw_silhouette(Vector2(cx, cy + 10), 25, 20, Color(0.15, 0.15, 0.15, 0.4))

		if show_target_select and i == target_cursor and enemy.is_alive:
			draw_string(ThemeDB.fallback_font, Vector2(cx - 6, cy - 35), "▼",
				HORIZONTAL_ALIGNMENT_LEFT, -1, 18, MENU_HIGHLIGHT)

func _draw_silhouette(center: Vector2, w: float, h: float, color: Color) -> void:
	var points = PackedVector2Array()
	var half_w: float = w / 2.0
	var half_h: float = h / 2.0
	var steps: int = 16
	for i_step in range(steps + 1):
		var t: float = float(i_step) / steps
		var angle: float = t * TAU
		var rx: float = half_w * (1.0 + 0.15 * sin(angle))
		var ry: float = half_h
		points.append(center + Vector2(cos(angle) * rx, sin(angle) * ry))
	draw_colored_polygon(points, color)

	var eye_y: float = center.y - half_h * 0.2
	var eye_spacing: float = half_w * 0.4
	draw_circle(Vector2(center.x - eye_spacing, eye_y), 3.0, Color(0.9, 0.2, 0.2, 0.8))
	draw_circle(Vector2(center.x + eye_spacing, eye_y), 3.0, Color(0.9, 0.2, 0.2, 0.8))

func _draw_flash_message(sz: Vector2, area_h: float) -> void:
	if flash_message.is_empty():
		return
	var bar_h: float = 24.0
	var bar_y: float = area_h * 0.65 - bar_h - 4.0
	var alpha: float = clampf(_flash_timer / FLASH_DURATION, 0.0, 1.0)
	draw_rect(Rect2(BORDER_WIDTH, bar_y, sz.x - BORDER_WIDTH * 2, bar_h),
		Color(0.0, 0.0, 0.1, 0.7 * alpha))
	draw_string(ThemeDB.fallback_font, Vector2(12, bar_y + 16), flash_message,
		HORIZONTAL_ALIGNMENT_LEFT, -1, 12, Color(1, 1, 1, alpha))

func _draw_command_menu(sz: Vector2, y: float, h: float) -> void:
	draw_rect(Rect2(BORDER_WIDTH, y + 1, sz.x - BORDER_WIDTH * 2, h - 1),
		Color(0.03, 0.03, 0.12))

	if not show_menu:
		draw_string(ThemeDB.fallback_font, Vector2(16, y + h / 2 + 4), "...",
			HORIZONTAL_ALIGNMENT_LEFT, -1, 12, MENU_NORMAL)
		return

	var menu_x: float = 16.0
	var menu_y: float = y + 8.0

	draw_string(ThemeDB.fallback_font, Vector2(menu_x, menu_y + 12),
		current_member_name + ":", HORIZONTAL_ALIGNMENT_LEFT, -1, 12, MENU_HIGHLIGHT)
	menu_y += 20.0

	for i in menu_items.size():
		var color: Color = MENU_HIGHLIGHT if i == menu_cursor else MENU_NORMAL
		var prefix: String = "> " if i == menu_cursor else "  "
		draw_string(ThemeDB.fallback_font, Vector2(menu_x, menu_y + 12),
			prefix + menu_items[i], HORIZONTAL_ALIGNMENT_LEFT, -1, 12, color)
		menu_y += 18.0

func _draw_party_status(sz: Vector2, y: float, h: float) -> void:
	draw_rect(Rect2(BORDER_WIDTH, y + 1, sz.x - BORDER_WIDTH * 2, h - 1),
		Color(0.03, 0.03, 0.12))

	var status_x: float = 12.0
	var status_y: float = y + 8.0
	var bar_w: float = 70.0
	var bar_h: float = 7.0

	for member in party:
		var color: Color = TEXT_COLOR if member.is_alive else Color(0.4, 0.4, 0.4)
		var name_text: String = member.combatant_name
		if member.is_defending:
			name_text += " [DEF]"

		draw_string(ThemeDB.fallback_font, Vector2(status_x, status_y + 11),
			name_text, HORIZONTAL_ALIGNMENT_LEFT, -1, 11, color)

		var bar_x: float = status_x + 75
		draw_rect(Rect2(bar_x, status_y + 4, bar_w, bar_h), HP_BAR_BG)
		var hp_ratio: float = float(member.hp) / float(member.max_hp) if member.max_hp > 0 else 0.0
		var bar_color: Color = HP_GREEN if hp_ratio > 0.3 else HP_RED
		draw_rect(Rect2(bar_x, status_y + 4, bar_w * hp_ratio, bar_h), bar_color)

		var hp_text: String = "%d/%d" % [member.hp, member.max_hp]
		draw_string(ThemeDB.fallback_font, Vector2(bar_x + bar_w + 4, status_y + 11),
			hp_text, HORIZONTAL_ALIGNMENT_LEFT, -1, 9, color)

		status_y += 20.0
