class_name BattleUI
extends Control

const BG_COLOR := Color(0.05, 0.05, 0.15)
const TEXT_COLOR := Color.WHITE
const MENU_HIGHLIGHT := Color(1.0, 0.8, 0.0)
const MENU_NORMAL := Color(0.7, 0.7, 0.7)
const HP_GREEN := Color(0.2, 0.8, 0.2)
const HP_RED := Color(0.8, 0.2, 0.2)
const HP_BAR_BG := Color(0.2, 0.2, 0.2)

var enemies: Array[Combatant] = []
var party: Array[Combatant] = []
var message_lines: Array[String] = []
var menu_items: Array[String] = []
var menu_cursor: int = 0
var show_menu: bool = false
var current_member_name: String = ""
var target_cursor: int = 0
var show_target_select: bool = false

func _draw() -> void:
	var sz = size
	draw_rect(Rect2(Vector2.ZERO, sz), BG_COLOR)

	var enemy_area_h = sz.y * 0.4
	_draw_enemies(sz, enemy_area_h)

	var msg_y = enemy_area_h
	var msg_h = sz.y * 0.25
	_draw_messages(sz, msg_y, msg_h)

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
			var rx = 30.0
			var ry = 25.0
			_draw_ellipse(Vector2(cx, cy), rx, ry, enemy.color)
			draw_string(ThemeDB.fallback_font, Vector2(cx - 25, cy + ry + 16), enemy.combatant_name,
				HORIZONTAL_ALIGNMENT_LEFT, -1, 11, TEXT_COLOR)
			var hp_text = "%d/%d" % [enemy.hp, enemy.max_hp]
			draw_string(ThemeDB.fallback_font, Vector2(cx - 20, cy + ry + 30), hp_text,
				HORIZONTAL_ALIGNMENT_LEFT, -1, 10, Color(0.6, 0.6, 0.6))
		else:
			_draw_ellipse(Vector2(cx, cy), 20, 15, Color(0.3, 0.3, 0.3, 0.3))

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

func _draw_menu(sz: Vector2, y: float, _h: float) -> void:
	if not show_menu:
		return
	var menu_x = 16.0
	var menu_y = y + 8.0
	draw_string(ThemeDB.fallback_font, Vector2(menu_x, menu_y + 14), current_member_name + ":",
		HORIZONTAL_ALIGNMENT_LEFT, -1, 12, MENU_HIGHLIGHT)
	menu_y += 22.0
	for i in menu_items.size():
		var color = MENU_HIGHLIGHT if i == menu_cursor else MENU_NORMAL
		var prefix = "> " if i == menu_cursor else "  "
		draw_string(ThemeDB.fallback_font, Vector2(menu_x, menu_y + 14), prefix + menu_items[i],
			HORIZONTAL_ALIGNMENT_LEFT, -1, 13, color)
		menu_y += 20.0

func _draw_status(sz: Vector2, y: float, _h: float) -> void:
	var status_x = sz.x * 0.55
	var status_y = y + 8.0
	for member in party:
		var color = TEXT_COLOR if member.is_alive else Color(0.5, 0.5, 0.5)
		var name_text = member.combatant_name
		if member.is_defending:
			name_text += " [DEF]"
		draw_string(ThemeDB.fallback_font, Vector2(status_x, status_y + 12), name_text,
			HORIZONTAL_ALIGNMENT_LEFT, -1, 12, color)
		var bar_x = status_x + 80
		var bar_w = 80.0
		var bar_h = 8.0
		draw_rect(Rect2(bar_x, status_y + 4, bar_w, bar_h), HP_BAR_BG)
		var hp_ratio = float(member.hp) / float(member.max_hp) if member.max_hp > 0 else 0.0
		var bar_color = HP_GREEN if hp_ratio > 0.3 else HP_RED
		draw_rect(Rect2(bar_x, status_y + 4, bar_w * hp_ratio, bar_h), bar_color)
		var hp_text = "%d/%d" % [member.hp, member.max_hp]
		draw_string(ThemeDB.fallback_font, Vector2(bar_x + bar_w + 6, status_y + 12), hp_text,
			HORIZONTAL_ALIGNMENT_LEFT, -1, 10, color)
		status_y += 22.0

func _process(_delta: float) -> void:
	queue_redraw()
