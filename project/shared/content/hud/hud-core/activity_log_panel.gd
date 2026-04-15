# scripts/ui/activity_log_panel.gd
# Always-visible windowed panel in bottom-left showing activity messages.
#
# Visual tunables live in `activity_log_panel_style.tres` — edited there,
# not here, because GDScript `const` values are baked into compiled .gdc
# at web-export time and cannot hot-reload. .tres data hot-reloads cleanly
# on F9 via ContentManager's CACHE_MODE_REPLACE_DEEP chain.
class_name ActivityLogPanel
extends Control

@export var style: ActivityLogPanelStyle

func _ready() -> void:
	# Emitted by tests/hot-reload.spec.js assertions as well as by any
	# visual-qa iteration — proves the reload path read a fresh style.tres.
	if style:
		print("[style-alp] bg_color=", style.bg_color)
	ActivityLog.message_added.connect(_on_message_added)

func _on_message_added(_text: String) -> void:
	queue_redraw()

func _draw() -> void:
	if style == null:
		return
	var sz = size

	# Background
	draw_rect(Rect2(Vector2.ZERO, sz), style.bg_color)

	# Border
	draw_rect(Rect2(Vector2.ZERO, sz), style.border_color, false, style.border_width)

	# Header
	var header_y: float = style.padding + style.header_font_size
	draw_string(ThemeDB.fallback_font, Vector2(style.padding, header_y), "Activity Log",
		HORIZONTAL_ALIGNMENT_LEFT, -1, style.header_font_size, style.header_color)

	# Divider under header
	var div_y: float = header_y + 6.0
	draw_line(Vector2(style.padding, div_y), Vector2(sz.x - style.padding, div_y),
		Color(0.3, 0.3, 0.5, 0.6), 1.0)

	# Messages (newest at bottom, auto-scroll)
	var content_y: float = div_y + 6.0
	var available_h: float = sz.y - content_y - style.padding
	var max_visible: int = maxi(1, int(available_h / style.line_height))
	var msgs: Array[String] = ActivityLog.messages
	var start: int = maxi(0, msgs.size() - max_visible)

	for i in range(start, msgs.size()):
		var line_y: float = content_y + (i - start) * style.line_height + style.msg_font_size
		var msg: String = msgs[i]

		# Separator lines get dimmer color
		var color: Color = style.text_color
		if msg.begins_with("---"):
			color = style.header_color

		draw_string(ThemeDB.fallback_font, Vector2(style.padding, line_y), msg,
			HORIZONTAL_ALIGNMENT_LEFT, int(sz.x - style.padding * 2), style.msg_font_size, color)
