# ComfyUI Asset Pipeline

Generates **grayscale** pixel art tilesets for legend-dad. Color is applied at runtime via Godot palette shader.

## Key Concept: Grayscale Tiles + Palette Shader

Tiles are authored as grayscale (16 levels → 16 palette indices). A Godot shader maps grayscale values to a 16x1 palette texture at runtime. This enables:

- **Era system**: Same tiles, different palette (father = vibrant, son = muted)
- **Fewer assets**: One grayscale tileset per biome, unlimited color variations
- **Simpler generation**: ComfyUI generates grayscale without color consistency concerns

See `vault/world/biomes/_art-pipeline.md` for full technical details.

## Architecture

```
Vault (biome defs + palette hex values)
  │
  ├─→ ComfyUI headless (batch grayscale tileset generation)
  │     tileset-runner.mjs reads biome defs → queues workflows → quantize to 16 grays
  │
  └─→ Krita + AI Diffusion (interactive tile refinement)
        Same ComfyUI server as backend (http://127.0.0.1:8188)
        Inpaint, refine, manual pixel edits on individual tiles
        Custom workflows via ETN_* bridge nodes
```

## Workflow Approach

Workflows are stored in **editor format** (with UI positions, group boxes) so they can be:
1. **Opened in ComfyUI's browser UI** for visual editing and testing
2. **Run headless** by extracting the inner node graph and POSTing to `/prompt` API

This replaces the API-only format used in ultima-magic.

## Directory Structure

```
project/comfyui/
  workflows/
    tileset-base.json          # Editor-format: generate grayscale tileset sheet
  palettes/
    dawnbringer-16.hex         # Universal palette (characters, UI)
    fantasy-rpg.hex            # Thornwall palette
    deep-forest-16.hex         # Whispering Woods palette
    damage-dice-10-6.hex       # Iron Peaks palette
  lib/
    comfyui-client.mjs         # HTTP client (queue, poll, download)
    tileset-runner.mjs         # Read vault biome defs → queue tileset jobs
    workflow-loader.mjs        # Load editor-format JSON, extract prompt object
    palette-generator.mjs      # Generate palette .hex files from vault frontmatter
  README.md
```

## Krita AI Diffusion Integration

[krita-ai-diffusion](https://github.com/Acly/krita-ai-diffusion) v1.49+ uses ComfyUI as backend.

**Setup**:
- Plugin connects to same ComfyUI server at `http://127.0.0.1:8188`
- Custom workflows go in `%APPDATA%/krita-ai-diffusion/workflows/`
- Required custom nodes auto-installed: `comfyui-tooling-nodes` (ETN_* bridge nodes)

**Tile refinement workflow**:
1. Open grayscale tileset in Krita
2. Select tile region → **Inpaint** mode to regenerate/fix
3. Use **Refine** (img2img) for style adjustment
4. Manual pixel edits with pencil tool
5. **Live preview** for real-time feedback
6. Export final grayscale tileset for LDtk

**Custom workflows**: Can load ComfyUI editor-format or API-format JSON. ETN_* nodes bridge Krita layers/selections into the ComfyUI graph. Parameters auto-generate UI controls in Krita.

## Palette Swatch Files

Palette `.hex` files are plain text, one hex color per line:
```
#140c1c
#442434
#30346d
...
```

Used by the pipeline for:
- Generating 16x1 PNG swatches (for IPAdapter/reference)
- Post-generation quantization (map grayscale output to nearest palette gray level)
- Documentation and reference

## Commands

```bash
# Generate palette .hex files from vault frontmatter
task comfyui:palettes

# Generate grayscale tileset for a biome (headless)
task comfyui:tileset -- --biome=field

# Generate all tilesets
task comfyui:tilesets
```
