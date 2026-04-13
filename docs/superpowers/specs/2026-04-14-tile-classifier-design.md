# Tile Classifier: Automated Atlas Rearrangement

## Problem

ComfyUI generates a 512x512 grayscale tileset sheet (16x16 grid of 32px tiles). The tiles are stylistically coherent but have no semantic ordering. The IntGrid vocabulary expects specific tile types at specific atlas positions (value N = atlas position N). Currently, atlas position 10 contains whatever SDXL happened to generate there, not "tall_grass" art.

## Research Summary

Industry approaches to AI tileset generation:
- **Per-tile generation with ControlNet** ([tilemapgen](https://github.com/charmed-ai/tilemapgen)) — generate each tile individually using depth/canny guidance. High control but slow (40 generations per biome).
- **Non-manifold parallel diffusion** ([BorisTheBrave](https://www.boristhebrave.com/2025/02/04/generating-tilesets-with-stable-diffusion/)) — all tiles denoised simultaneously with neighbor context. Seamless but requires custom diffusion code.
- **Sheet generation + curation** — generate full sheets, then classify/assign tiles. Most practical for existing pipeline.

We use approach 3: keep the existing ComfyUI sheet generation, add automated post-processing.

## Solution

A `tile_classifier.py` script that analyzes each 32x32 cell in the grayscale atlas, classifies it by visual properties, and rearranges tiles so atlas position N contains art matching IntGrid value N.

### Pipeline

```
ComfyUI (generate 512x512 sheet)
  -> tileset_preprocess.py (force grayscale + clean grid)
  -> tile_classifier.py (analyze cells, rearrange to semantic order)
  -> atlas_32x32.png (position N = IntGrid value N)
```

### Classification Features

For each 32x32 cell, compute:

| Feature | How | What it tells us |
|---------|-----|-----------------|
| Mean brightness | Average pixel value (0-255) | Dark = dense objects (tree, wall), Light = open terrain (ground, path) |
| Edge density | Sobel edge detection, count edge pixels | High = textured/detailed (bush, rubble), Low = flat (ground, water) |
| Brightness variance | Std deviation of pixel values | Uniform = smooth surfaces (water, path), Varied = foliage/mixed |

### Tile Profiles per IntGrid Value

Each IntGrid value gets a target visual profile. The classifier matches generated tiles to the closest profile.

**Universal (0-9):**

| Value | Name | Brightness | Edges | Variance |
|-------|------|-----------|-------|----------|
| 0 | void | very low | low | low |
| 1 | ground | high | low | low |
| 2 | wall | low | high | medium |
| 3 | water_shallow | medium | low | low |
| 4 | water_deep | low | low | low |
| 5 | pit | very low | medium | low |
| 6 | door | medium | high | high |
| 7 | stairs_up | medium | high | medium |
| 8 | stairs_down | medium | high | medium |
| 9 | bridge | medium | medium | medium |

**Field biome (10-19):**

| Value | Name | Brightness | Edges | Variance |
|-------|------|-----------|-------|----------|
| 10 | tall_grass | medium | medium | medium |
| 11 | bush | medium-low | high | high |
| 12 | tree_trunk | low | high | high |
| 13 | fallen_log | medium-low | medium | medium |
| 14 | cliff_edge | low | high | medium |
| 15 | path_dirt | high | low | low |
| 16 | path_stone | high | medium | medium |
| 17 | stream_crossing | medium | medium | medium |
| 18 | undergrowth | medium | medium | high |
| 19 | hollow | low | medium | medium |

(Dungeon 20-29 and Town 30-39 follow same pattern with biome-appropriate profiles.)

### Classification Algorithm

1. Extract all 256 cells from the 16x16 atlas
2. Compute (brightness, edges, variance) for each cell
3. Normalize features to 0-1 range
4. For each IntGrid value needed by the biome (universal 0-9 + biome-specific 10-19/20-29/30-39):
   - Compute distance from each unassigned cell to the target profile
   - Assign the closest cell
   - Mark that cell as used
5. Fill remaining atlas positions with leftover cells (for decoration tiles)
6. Reassemble the 512x512 atlas with tiles in semantic order

### Output

Same `atlas_32x32.png` filename and format. The only difference is tile ordering — position N now contains art that visually matches IntGrid value N.

### Taskfile Integration

```yaml
tileset:classify:
  desc: Classify and rearrange tileset atlas into semantic IntGrid order
  cmds:
    - "{{.PYTHON_BIN}} scripts/tile_classifier.py --biome={{.CLI_ARGS}}"
```

The full pipeline command becomes:
```bash
task comfyui:tileset -- --biome=field    # Generate raw sheet
task tileset:preprocess -- field          # Grayscale + clean grid
task tileset:classify -- field            # Rearrange to semantic order
task pck:build -- whispering-woods        # Build PCK with ordered atlas
```

## Files

| File | Purpose |
|------|---------|
| `scripts/tile_classifier.py` (create) | Analyze + rearrange atlas |
| `Taskfile.yml` (modify) | Add `tileset:classify` task |

## Scope

- Automated classification using brightness/edges/variance
- Per-biome tile profiles
- Deterministic output (same input atlas = same assignment)
- No manual curation step (fully automated)
- If classification quality is poor, we revisit with ControlNet per-tile generation (option A from research)

## Verification

1. Run `task tileset:classify -- field`
2. Visually inspect output atlas — position 1 should look like ground, position 12 like tree trunk, etc.
3. Run game in browser — LDtk terrain should show visually distinct tiles per IntGrid value
4. Compare father/son era palettes — same tile shapes, different colorization
