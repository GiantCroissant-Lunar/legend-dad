---
type: meta
status: draft
last-agent-pass: "2026-04-13"
---

# Art Pipeline — Tileset Generation & Palette System

## Grayscale + Shader Palette Swap

Tiles are authored as **grayscale** images. Color comes from a **runtime palette shader** in Godot. This means:

- Each tile is a grayscale value (0-255) mapping to a palette index
- The palette is a 16x1 texture (16 colors, one row)
- A Godot shader samples the grayscale value and looks up the palette texture
- Swapping the palette texture changes the entire biome's look (era variants, seasons, time-of-day)

### Advantages
- **Era system**: Father's era = vibrant palette, Son's era = desaturated palette. Same tiles, different mood.
- **Fewer assets**: One set of grayscale tiles per biome, unlimited color variations via palette swap.
- **ComfyUI simplicity**: Generate grayscale tiles without worrying about color consistency.
- **LDtk compatibility**: LDtk displays grayscale tiles (readable in editor). Godot colorizes at runtime.

### Grayscale Value Mapping

For a 16-color palette, grayscale values map to palette indices:

| Grayscale Range | Palette Index | Typical Use |
|---|---|---|
| 0-15 | 0 | Darkest (outlines, deep shadow) |
| 16-31 | 1 | Very dark |
| 32-47 | 2 | Dark |
| 48-63 | 3 | Dark-mid |
| 64-79 | 4 | Mid-dark |
| 80-95 | 5 | Mid |
| 96-111 | 6 | Mid |
| 112-127 | 7 | Mid-light |
| 128-143 | 8 | Mid-light |
| 144-159 | 9 | Light-mid |
| 160-175 | 10 | Light |
| 176-191 | 11 | Light |
| 192-207 | 12 | Very light |
| 208-223 | 13 | Highlight |
| 224-239 | 14 | Bright highlight |
| 240-255 | 15 | Brightest |

The shader divides the grayscale value by 16 to get the palette index, then samples the palette texture at that X coordinate.

## Generation Pipeline

### Stage 1: ComfyUI Headless — Base Tileset Generation

Generate grayscale tileset sheets using ComfyUI in headless mode.

```
Vault biome def → tileset-runner.mjs → ComfyUI /prompt API → grayscale tileset PNG
```

Workflow: `project/comfyui/workflows/tileset-base.json`
- Input: biome prompt template + tile category
- Model: SDXL + pixel art LoRA
- Output: tileset sheet (e.g. 256x256 = 16x16 grid of 16x16 tiles)
- Post-process: quantize to 16 grayscale levels

### Stage 2: Krita + AI Diffusion — Interactive Refinement

Open generated tilesets in Krita with the [krita-ai-diffusion](https://github.com/Acly/krita-ai-diffusion) plugin for pixel-level editing.

**Krita AI Diffusion** uses ComfyUI as its backend (same server, same models). Key features for tileset work:

- **Inpaint**: Fix individual tiles — select a tile, describe what you want, regenerate just that area
- **Refine (img2img)**: Adjust a tile's detail level or style while keeping structure
- **Live preview**: See changes in real-time as you paint
- **ControlNet**: Use line art / scribble control to guide tile shapes
- **Custom workflows**: Load custom ComfyUI workflows via ETN_* bridge nodes

**Setup**:
- Plugin connects to ComfyUI at `http://127.0.0.1:8188` (same server used for headless)
- Custom workflows go in `%APPDATA%/krita-ai-diffusion/workflows/`
- Required custom nodes: `comfyui-tooling-nodes` (ETN_* bridge nodes)

**Tile editing workflow**:
1. Open grayscale tileset in Krita (e.g. `field-tileset-grayscale.png`)
2. Select a tile region (16x16 or larger)
3. Use **Inpaint** mode to regenerate/fix that tile
4. Use pencil tool for manual pixel corrections
5. Verify tiling: copy tile to pattern, test seamless edges
6. Export final grayscale tileset

### Stage 3: Palette Authoring

Palette swatch images (16x1 PNG) are created from hex values in vault frontmatter.

Each location gets:
- A **base palette** (father's era — full color)
- An **era variant** (son's era — desaturated/darkened)
- Optional: night, indoor, weather variants

Palette swatches stored in `project/comfyui/palettes/` as both `.hex` (text) and `.png` (swatch image).

### Stage 4: Godot Shader

A palette swap shader in Godot:

```gdscript
# Pseudocode — actual shader in ShaderMaterial
shader_type canvas_item;
uniform sampler2D palette_texture;  // 16x1 palette PNG

void fragment() {
    float gray = texture(TEXTURE, UV).r;  // grayscale tile
    int index = int(gray * 15.0);          // 0-15 palette index
    COLOR = texelFetch(palette_texture, ivec2(index, 0), 0);
}
```

Swap `palette_texture` at runtime to change era/mood.

## Tool Chain Summary

| Tool | Role | Mode |
|---|---|---|
| ComfyUI | Generate base grayscale tilesets | Headless (API) |
| Krita + AI Diffusion | Refine individual tiles, fix edges | Interactive |
| Vault | Source of truth for biome defs + palettes | Read by scripts |
| LDtk | Level design with grayscale tiles | Interactive |
| Godot | Runtime palette shader, final rendering | Runtime |

## File Flow

```
vault/world/biomes/*.md           # Biome defs + palette hex
  ↓
project/comfyui/palettes/*.hex    # Palette swatch files
project/comfyui/palettes/*.png    # Palette swatch PNGs (16x1)
  ↓
project/comfyui/workflows/*.json  # Editor-format ComfyUI workflows
  ↓ (headless)                     ↓ (interactive)
build/tilesets/raw/               Krita opens directly
  ↓ (quantize to 16 grays)
build/tilesets/grayscale/
  ↓ (after Krita refinement)
project/ldtk/tilesets/            # Final grayscale tilesets for LDtk
  ↓
project/hosts/complete-app/       # Godot imports + palette shader
```
