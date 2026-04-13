---
type: meta
status: draft
last-agent-pass: "2026-04-13"
---

# ComfyUI Workflows for Tileset Generation

## Required Custom Nodes

Install these in `ComfyUI/custom_nodes/`:

| Node Package | GitHub | Purpose |
|---|---|---|
| **ComfyUI-PixelArt-Detector** | [dimtoneff/ComfyUI-PixelArt-Detector](https://github.com/dimtoneff/ComfyUI-PixelArt-Detector) | Pixelize, downscale, palette load/convert, grid preview |
| **ComfyUI-PixydustQuantizer** | [sousakujikken/ComfyUI-PixydustQuantizer](https://github.com/sousakujikken/ComfyUI-PixydustQuantizer) | 16-color retro quantization with dithering (optional, alternative to PixelArt-Detector's converter) |
| **PixelArt-Processing-Nodes** | [GENKAIx/PixelArt-Processing-Nodes-for-ComfyUI](https://github.com/GENKAIx/PixelArt-Processing-Nodes-for-ComfyUI) | Simpler downscale/quantize (optional lightweight alternative) |

### Installation

```bash
cd ComfyUI/custom_nodes
git clone https://github.com/dimtoneff/ComfyUI-PixelArt-Detector
# Optional:
git clone https://github.com/sousakujikken/ComfyUI-PixydustQuantizer
git clone https://github.com/GENKAIx/PixelArt-Processing-Nodes-for-ComfyUI
```

Restart ComfyUI after installing.

## Workflow: tileset-grayscale.json

**Location**: `project/comfyui/workflows/tileset-grayscale.json`

**Format**: ComfyUI editor format — drag & drop into ComfyUI browser UI, or run headless via API.

### Node Graph

```
[Checkpoint SDXL] ─→ [LoRA Pixel Art] ─→ [KSampler] ─→ [VAE Decode]
                                             ↑                 │
[Positive Prompt] ─→ [CLIP Encode +] ────────┘                 │
[Negative Prompt] ─→ [CLIP Encode -] ────────┘                 │
[Empty Latent 1024x1024] ────────────────────┘                 │
                                                                ├─→ [Save Raw]
                                                                │
                                                                ├─→ [PixelArt Detector] ─→ [ImageScale 512x512]
                                                                │                              │
                                                                │                              ├─→ [Save Pixelated]
                                                                │                              │
[Palette Loader (grayscale-16)] ───────────────────────────────────→ [Palette Converter]
                                                                                  │
                                                                                  └─→ [Save Grayscale Final]
```

### Groups (visual in editor)

1. **Model + LoRA** — Checkpoint and pixel art LoRA loading
2. **Prompts** — Positive/negative prompt primitives
3. **Generate** — CLIP encode, empty latent, KSampler, VAE decode
4. **Pixelize + Downscale** — PixelArt Detector → nearest-neighbor upscale
5. **Quantize to 16 Grays** — Palette converter restricts to 16 grayscale levels

### Three Outputs

| Output | Path Prefix | Purpose |
|---|---|---|
| Raw | `legend-dad/raw/tileset` | Full 1024x1024 generated image |
| Pixelated | `legend-dad/pixelated/tileset` | Downscaled + nearest-neighbor upscaled (crisp pixels) |
| Grayscale | `legend-dad/grayscale/tileset` | Quantized to 16 gray levels (final for Godot) |

### Parameters to Customize

| Node | Widget | Default | Change to |
|---|---|---|---|
| Checkpoint | ckpt_name | `sd_xl_base_1.0.safetensors` | Your local SDXL checkpoint |
| LoRA | lora_name | `pixel-art-xl-v1.1.safetensors` | Your pixel art LoRA |
| LoRA | strength | 0.85 / 0.85 | Adjust to taste (0.7-1.0) |
| Positive Prompt | text | Forest tileset prompt | Change per biome (see below) |
| KSampler | seed | 0 (randomize) | Fix for reproducibility |
| KSampler | steps | 25 | 20-30 |
| KSampler | cfg | 7 | 6-8 |
| Palette Loader | palette | `grayscale-16.png` | Must create this palette swatch |
| Palette Converter | max_colors | 16 | Keep at 16 for our system |

### Biome Prompts

Replace the positive prompt text per biome:

**Field (Whispering Woods)**:
```
16-bit pixel art tileset sheet, top-down 3/4 perspective, 16x16 tile grid layout,
JRPG style, grayscale, monochrome, black and white tonal values only,
old-growth forest biome, grass tiles, dirt path tiles, tree trunk tiles,
bush tiles, water stream tiles, stone path tiles, fallen log, wildflowers,
seamless tile edges, clean pixel edges, no anti-aliasing, flat background
```

**Dungeon (Iron Peaks)**:
```
16-bit pixel art tileset sheet, top-down 3/4 perspective, 16x16 tile grid layout,
JRPG style, grayscale, monochrome, black and white tonal values only,
underground cave mine biome, cave floor tiles, cave wall tiles, mine track tiles,
ore vein tiles, crystal tiles, lava pool tiles, rubble tiles, torch bracket,
seamless tile edges, clean pixel edges, no anti-aliasing, flat background,
dark ambient lighting with localized light sources
```

**Town (Thornwall)**:
```
16-bit pixel art tileset sheet, top-down 3/4 perspective, 16x16 tile grid layout,
JRPG style, grayscale, monochrome, black and white tonal values only,
medieval village biome with open-top buildings interiors visible,
cobblestone tiles, building wall tiles, wood floor tiles, furniture tiles,
fence tiles, market stall, well, door frame, window, roof edge,
seamless tile edges, clean pixel edges, no anti-aliasing, flat background,
warm ambient lighting
```

## Grayscale Palette Swatch

The workflow needs a `grayscale-16.png` palette image for the Palette Loader node. This is a 16x1 PNG with 16 evenly-spaced gray values:

```
#000000  #111111  #222222  #333333
#444444  #555555  #666666  #777777
#888888  #999999  #aaaaaa  #bbbbbb
#cccccc  #dddddd  #eeeeee  #ffffff
```

Place this file in ComfyUI's palette directory (usually `ComfyUI/custom_nodes/ComfyUI-PixelArt-Detector/palettes/`).

## Krita AI Diffusion Follow-Up

After generating base tilesets with ComfyUI headless:

1. Open grayscale tileset PNG in Krita
2. Connect Krita AI Diffusion to same ComfyUI server (`http://127.0.0.1:8188`)
3. Select individual tile regions (16x16 or groups)
4. Use **Inpaint** to regenerate broken tiles
5. Use **Refine** (img2img) for style consistency
6. Manual pixel edits for tiling seams
7. Export final grayscale tileset for LDtk

## Reference Workflows (External)

Community workflows to study and adapt:

- [PixelArt-Detector example workflows](https://github.com/dimtoneff/ComfyUI-PixelArt-Detector/tree/main/example_workflows) — Editor format, drag & drop
- [OpenArt: Pixel Art Workflow](https://openart.ai/workflows/megaaziib/pixel-art-workflow/09EGyt3ZOBM9kD4ZZGP5) — Accurate pixel count generation
- [OpenArt: Pixel Art Fast Generator](https://openart.ai/workflows/megaaziib/pixel-art-fast-generator/XkwkHIWGhMLWxQuBIsd1) — Color-limited output
- [Pixel Art ComfyUI Workflow Guide](https://inzaniak.github.io/blog/articles/the-pixel-art-comfyui-workflow-guide.html) — Step-by-step tutorial
- [CivitAI: Proper Pixel Art in ComfyUI](https://civitai.com/articles/2754/how-to-make-proper-pixel-art-in-comfyui) — Best practices
- [SDXL Pixel Art Workflow (Gist)](https://gist.github.com/zaro/9243d32d56f81655fdf9e3edd48f4ed1) — Minimal SDXL setup
