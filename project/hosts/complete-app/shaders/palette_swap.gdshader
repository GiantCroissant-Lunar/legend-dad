shader_type canvas_item;

// 16x1 palette texture — each pixel is one color in the palette.
// Swap this uniform at runtime to change era, time-of-day, weather, etc.
uniform sampler2D palette_texture : filter_nearest, repeat_disable;

// Number of colors in the palette (default 16 for our system).
uniform int palette_size : hint_range(2, 256) = 16;

void fragment() {
	// Sample the grayscale tile texture
	vec4 tex = texture(TEXTURE, UV);

	// Use red channel as grayscale value (grayscale images have R=G=B)
	float gray = tex.r;

	// Map grayscale 0.0-1.0 to palette index 0-(palette_size-1)
	// Adding 0.5/palette_size centers the lookup within each palette slot
	// to avoid edge sampling issues
	float palette_u = (floor(gray * float(palette_size - 1)) + 0.5) / float(palette_size);

	// Sample the palette texture at the computed index
	vec4 palette_color = texture(palette_texture, vec2(palette_u, 0.5));

	// Preserve original alpha (transparency from the tile)
	COLOR = vec4(palette_color.rgb, tex.a);
}
