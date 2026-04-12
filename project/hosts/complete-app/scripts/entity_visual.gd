## A Node2D that visually represents an ECS entity in a SubViewport.
## main.gd creates these and syncs position/visibility from component data.
class_name EntityVisual
extends Node2D

const TILE_SIZE := 32

enum VisualType { PLAYER_FATHER, PLAYER_SON, BOULDER, BLOCKED }

var visual_type: VisualType = VisualType.PLAYER_FATHER
## The ECS entity this visual represents — used to read component data.
var entity: Entity = null

func _draw() -> void:
	match visual_type:
		VisualType.PLAYER_FATHER:
			draw_rect(Rect2(4, 4, TILE_SIZE - 8, TILE_SIZE - 8), Color(1.0, 0.8, 0.0))
			_draw_facing_arrow()
		VisualType.PLAYER_SON:
			draw_rect(Rect2(4, 4, TILE_SIZE - 8, TILE_SIZE - 8), Color(0.6, 0.8, 1.0))
			_draw_facing_arrow()
		VisualType.BOULDER:
			draw_circle(Vector2(TILE_SIZE / 2.0, TILE_SIZE / 2.0), TILE_SIZE / 3.0, Color(0.5, 0.5, 0.5))
		VisualType.BLOCKED:
			draw_circle(Vector2(TILE_SIZE / 2.0, TILE_SIZE / 2.0), TILE_SIZE / 3.0, Color(0.4, 0.2, 0.2))

func _draw_facing_arrow() -> void:
	if not entity:
		return
	var grid_pos = entity.get_component(C_GridPosition) as C_GridPosition
	if grid_pos:
		var center = Vector2(TILE_SIZE / 2.0, TILE_SIZE / 2.0)
		var arrow_end = center + Vector2(grid_pos.facing) * 10.0
		draw_line(center, arrow_end, Color.WHITE, 2.0)

func _process(_delta: float) -> void:
	queue_redraw()
