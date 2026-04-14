# scripts/ui/activity_log_panel.gd
# Always-visible windowed panel in bottom-left showing activity messages.
class_name ActivityLogPanel
extends Control

const BG_COLOR = Color(0.05, 0.05, 0.15, 0.85)
const BORDER_COLOR = Color(0.6, 0.7, 0.9, 0.8)
const HEADER_COLOR = Color(0.6, 0.7, 0.9)
const TEXT_COLOR = Color.WHITE
const LINE_HEIGHT = 16.0
const PADDING = 8.0
const BORDER_WIDTH = 2.0

func _ready() -> void:
	ActivityLog.message_added.connect(_on_message_added)

func _on_message_added(_text: String) -> void:
	queue_redraw()

func _draw() -> void:
	var sz = size

	# Background
	draw_rect(Rect2(Vector2.ZERO, sz), BG_COLOR)

	# Border
	draw_rect(Rect2(Vector2.ZERO, sz), BORDER_COLOR, false, BORDER_WIDTH)

	# Header
	var header_y: float = PADDING + 12.0
	draw_string(ThemeDB.fallback_font, Vector2(PADDING, header_y), "Activity Log",
		HORIZONTAL_ALIGNMENT_LEFT, -1, 11, HEADER_COLOR)

	# Divider under header
	var div_y: float = header_y + 4.0
	draw_line(Vector2(PADDING, div_y), Vector2(sz.x - PADDING, div_y),
		Color(0.3, 0.3, 0.5, 0.6), 1.0)

	# Messages (newest at bottom, auto-scroll)
	var content_y: float = div_y + 4.0
	var available_h: float = sz.y - content_y - PADDING
	var max_visible: int = int(available_h / LINE_HEIGHT)
	var msgs: Array[String] = ActivityLog.messages
	var start: int = maxi(0, msgs.size() - max_visible)

	for i in range(start, msgs.size()):
		var line_y: float = content_y + (i - start) * LINE_HEIGHT + 12.0
		var msg: String = msgs[i]

		# Separator lines get dimmer color
		var color: Color = TEXT_COLOR
		if msg.begins_with("---"):
			color = HEADER_COLOR

		draw_string(ThemeDB.fallback_font, Vector2(PADDING, line_y), msg,
			HORIZONTAL_ALIGNMENT_LEFT, int(sz.x - PADDING * 2), 10, color)
