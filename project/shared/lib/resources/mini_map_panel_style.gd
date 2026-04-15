extends Resource
class_name MiniMapPanelStyle
##
## Visual tunables for `mini_map_panel.gd`. See
## `activity_log_panel_style.gd` for why these live in a .tres rather than
## as `const` on the script.

@export var bg_color: Color = Color(0.05, 0.05, 0.15, 0.85)
@export var border_color: Color = Color(0.6, 0.7, 0.9, 0.8)
@export var header_color: Color = Color(0.6, 0.7, 0.9)
@export var walkable_color: Color = Color(0.15, 0.2, 0.15)
@export var blocked_color: Color = Color(0.3, 0.3, 0.35)
@export var player_color: Color = Color(1.0, 0.8, 0.0)
@export var enemy_color: Color = Color(0.8, 0.2, 0.2)
@export var border_width: float = 2.0
@export var padding: float = 8.0
