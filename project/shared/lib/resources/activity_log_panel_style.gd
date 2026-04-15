extends Resource
class_name ActivityLogPanelStyle
##
## Visual tunables for `activity_log_panel.gd`. Values live in a .tres so
## they hot-reload on F9 — GDScript `const` values are baked into .gdc at
## export time and don't re-parse on the web build (see
## vault/dev-log/2026-04-15-hot-reload-widget-vanish-fix.md).
##
## Change colors/sizes by editing
## `project/shared/content/hud/hud-core/activity_log_panel_style.tres`,
## then `task content:build -- hud-core` and press F9 in the running game.

@export var bg_color: Color = Color(0.05, 0.05, 0.15, 0.85)
@export var border_color: Color = Color(0.6, 0.7, 0.9, 0.8)
@export var header_color: Color = Color(0.6, 0.7, 0.9)
@export var text_color: Color = Color.WHITE
@export var msg_font_size: int = 30
@export var header_font_size: int = 33
@export var line_height: float = 48.0
@export var padding: float = 10.0
@export var border_width: float = 2.0
