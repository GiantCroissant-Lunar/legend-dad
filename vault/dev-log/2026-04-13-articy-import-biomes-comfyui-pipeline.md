---
type: dev-log
date: 2026-04-13
agent: claude-opus-4.6
version: 0.1.0
tags: [articy, ldtk, biome, palette, comfyui, krita, tileset, pipeline]
---

# Articy Import, Biome System & ComfyUI Art Pipeline

## Summary

Completed the full articy import of all 21 vault entities, designed the biome/IntGrid system for LDtk, selected lospec palettes for all locations, and built the ComfyUI tileset generation pipeline with grayscale palette-swap architecture.

## Commits

- `4598438` feat: import 21 entities into articy and write back IDs to vault
- `84d78eb` feat: add biome system with IntGrid vocabulary and open-top town architecture
- `e4daa17` feat: add palette system and ComfyUI art pipeline with grayscale tile approach
- `5a704d5` feat: add ComfyUI editor-format tileset workflow and workflow docs

## What Was Done

### 1. Articy Import (completed)

- Fixed stale quicktype types — `zone` was missing from `TypeEnum` in generated C#/Python
- Ran `task articy:types` to regenerate, then `task articy:build` to rebuild MDK plugin
- Successfully imported all 21 entities into articy:draft X (1 new template LD_Zone, 8 existing)
- Ran `task articy:writeback` — wrote articy IDs to 14 vault pages
- Verified with `task articy:prep` — all entities show `status: unchanged`
- Ran `task ldtk:sync` — 9 entity defs, 7 levels preserved

### 2. Biome System

Created `vault/world/biomes/` with IntGrid vocabulary:

| Biome | Range | File | Locations |
|---|---|---|---|
| Universal | 0-9 | `_conventions.md` | All |
| Field | 10-19 | `field.md` | Whispering Woods |
| Dungeon | 20-29 | `dungeon.md` | Iron Peaks |
| Town | 30-39 | `town.md` | Thornwall, Starlight Academy |

Key decision: **Open-top buildings** — town interiors visible directly on the map, no screen transitions. Buildings are wall tiles forming rooms with interior floor inside. Inspired by Eastward/CrossCode.

Added `biome`, `palette`, `ldtk-file` fields to all 4 location frontmatter files and `biome` field to all 7 zone files.

### 3. LDtk Multi-File Architecture

Decided on: one world-overview.ldtk + one .ldtk per location:
```
project/ldtk/
  world-overview.ldtk       # Locations as levels
  thornwall.ldtk             # 3 zones as levels
  whispering-woods.ldtk      # 2 zones as levels
  iron-peaks.ldtk            # 2 zones as levels
```

Not yet implemented — `ldtk_sync.py` still generates single file.

### 4. Palette Selection

Selected 16-color lospec palettes for all locations:

| Location | Palette | URL |
|---|---|---|
| Thornwall | Fantasy RPG | lospec.com/palette-list/fantasy-rpg |
| Whispering Woods | Deep Forest 16 | lospec.com/palette-list/deep-forest-16 |
| Iron Peaks | Damage Dice 10 & 6 | lospec.com/palette-list/damage-dice-10-6 |
| Universal | DawnBringer 16 | lospec.com/palette-list/dawnbringer-16 |

Hex values recorded in location frontmatter (`palette-hex` field) and as `.hex` files in `project/comfyui/palettes/`.

### 5. Grayscale + Palette Shader Architecture

Tiles are authored as **grayscale** (16 levels). Color comes from a runtime Godot shader that maps gray → palette texture (16x1 PNG). Benefits:
- Era swap = just change palette texture (father = vibrant, son = muted)
- One tileset per biome, unlimited color variations
- Simpler ComfyUI generation (no color consistency concerns)

### 6. ComfyUI Pipeline

Created `project/comfyui/` with:
- `lib/comfyui-client.mjs` — HTTP client for ComfyUI API (queue, poll, download)
- `lib/workflow-loader.mjs` — Bridge between editor-format and API-format workflows
- `lib/palette-generator.mjs` — Generate palette files from vault frontmatter
- `workflows/tileset-grayscale.json` — **Editor-format** workflow (drag & drop into ComfyUI UI)

Workflow node chain: Checkpoint → LoRA → KSampler → VAE Decode → PixelArt Detector (downscale) → Palette Converter (quantize to 16 grays) → Save

Requires custom node: [ComfyUI-PixelArt-Detector](https://github.com/dimtoneff/ComfyUI-PixelArt-Detector)

### 7. Krita AI Diffusion Research

[krita-ai-diffusion](https://github.com/Acly/krita-ai-diffusion) v1.49 uses ComfyUI as backend (same server). Supports:
- Inpaint individual tiles, refine (img2img), live preview
- Custom ComfyUI workflows via ETN_* bridge nodes
- Custom models, LoRAs, style presets

Role in pipeline: interactive refinement after headless batch generation.

## Decisions & Rationale

| Decision | Why |
|---|---|
| Open-top buildings | Simpler than roof-hide mechanic, modern indie JRPG feel, one biome covers outdoor+indoor |
| Grayscale tiles + palette shader | Era system via palette swap, fewer assets, simpler generation |
| Editor-format workflows | Openable in ComfyUI browser UI for visual editing, also runnable headless |
| Lospec 16-color palettes | Industry standard for pixel art, matches 16 grayscale levels |
| ComfyUI-PixelArt-Detector | Best-in-class for palette restriction + pixelization in ComfyUI |

## New Files

```
vault/world/biomes/
  _conventions.md          # Universal IntGrid, LDtk architecture, palettes
  _art-pipeline.md         # Grayscale + shader pipeline, tool chain
  _comfyui-workflows.md    # Workflow docs, required nodes, biome prompts
  field.md                 # IntGrid 10-19
  dungeon.md               # IntGrid 20-29
  town.md                  # IntGrid 30-39 (outdoor + open-top interiors)

project/comfyui/
  README.md
  lib/comfyui-client.mjs
  lib/workflow-loader.mjs
  lib/palette-generator.mjs
  workflows/tileset-grayscale.json
  palettes/dawnbringer-16.hex
  palettes/fantasy-rpg.hex
  palettes/deep-forest-16.hex
  palettes/damage-dice-10-6.hex
  palettes/grayscale-16.hex
```

## Blockers / Open Items

1. **LDtk restructure** — `ldtk_sync.py` needs updating for multi-file per-location architecture
2. **ComfyUI setup** — need to install PixelArt-Detector node, create grayscale-16.png swatch, verify checkpoint/LoRA names
3. **Godot palette shader** — not yet written
4. **tileset-runner.mjs** — headless batch runner not yet implemented
5. **Krita workflow files** — no custom ETN_* workflows created yet
6. **Era palette variants** — son's era desaturated palettes not yet defined
7. **Starlight Academy zones** — no zones defined yet for this location

## Next Steps

1. Install ComfyUI-PixelArt-Detector, test tileset-grayscale.json workflow
2. Generate first grayscale tileset (field biome as easiest start)
3. Open in Krita, refine with AI Diffusion
4. Write Godot palette shader
5. Update `ldtk_sync.py` for multi-file architecture
6. Import grayscale tileset into LDtk, set up auto-rules
