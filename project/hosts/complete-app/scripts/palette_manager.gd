## Applies the palette swap shader to a TileMapLayer or Sprite2D.
##
## Usage:
##   var pm = PaletteManager.new()
##   pm.apply_palette(tilemap_layer, preload("res://palettes/fantasy-rpg.png"))
##   pm.swap_palette(tilemap_layer, preload("res://palettes/fantasy-rpg-son.png"))
class_name PaletteManager

const PALETTE_SHADER = preload("res://shaders/palette_swap.gdshader")


## Apply the palette shader to a CanvasItem (TileMapLayer, Sprite2D, etc.)
## with the given palette texture.
static func apply_palette(node: CanvasItem, palette: Texture2D, palette_size: int = 16) -> void:
	var mat := ShaderMaterial.new()
	mat.shader = PALETTE_SHADER
	mat.set_shader_parameter("palette_texture", palette)
	mat.set_shader_parameter("palette_size", palette_size)
	node.material = mat


## Swap the palette on a node that already has the palette shader applied.
static func swap_palette(node: CanvasItem, palette: Texture2D) -> void:
	var mat := node.material as ShaderMaterial
	if mat == null:
		push_warning("PaletteManager: node has no ShaderMaterial, call apply_palette first")
		return
	mat.set_shader_parameter("palette_texture", palette)


## Remove the palette shader from a node (show raw grayscale).
static func remove_palette(node: CanvasItem) -> void:
	node.material = null
