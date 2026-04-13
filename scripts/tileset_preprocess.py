#!/usr/bin/env python3
"""Slice a ComfyUI grayscale tileset into clean 32px cells and reassemble.

Usage:
    python3 scripts/tileset_preprocess.py --biome=field --tile-size=32

Input:  build/tilesets/{biome}/grayscale_tileset_*.png (512x512)
Output: build/tilesets/{biome}/atlas_32x32.png (512x512, clean grid)
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from PIL import Image

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_INPUT_DIR = PROJECT_ROOT / "build" / "tilesets"


def preprocess_atlas(
    input_dir: Path,
    biome: str,
    tile_size: int = 32,
) -> Path:
    """Slice source image into grid cells and reassemble a clean atlas.

    Args:
        input_dir: Directory containing grayscale_tileset_*.png files.
                   If a biome subdirectory exists, it's used automatically.
        biome: Biome name (used for subdirectory lookup).
        tile_size: Size of each tile in pixels.

    Returns:
        Path to the output atlas PNG.

    Raises:
        FileNotFoundError: If no source image is found.
    """
    biome_dir = input_dir / biome if (input_dir / biome).is_dir() else input_dir
    # Prefer pixelated stage (182+ gray levels) over grayscale stage (only 3 levels).
    # The PixelArt-Detector's palette converter crushes tonal range; we do our own
    # 16-level quantization below.
    candidates = sorted(biome_dir.glob("pixelated_tileset_*.png"))
    if not candidates:
        candidates = sorted(biome_dir.glob("grayscale_tileset_*.png"))
    if not candidates:
        raise FileNotFoundError(f"No grayscale_tileset_*.png found in {biome_dir}")

    source_path = candidates[-1]  # Use the latest
    source = Image.open(source_path).convert("L")  # Force true grayscale
    width, height = source.size
    cols = width // tile_size
    rows = height // tile_size

    # Requantize to exactly 16 evenly-spaced gray levels.
    # ComfyUI's PixelArt-Detector often collapses to 2-4 levels; we need 16
    # so each gray value maps to a distinct palette shader entry.
    import numpy as np

    arr = np.array(source, dtype=np.float32)
    lo, hi = float(arr.min()), float(arr.max())
    if hi > lo:
        arr = (arr - lo) / (hi - lo)  # Normalize to 0-1
    arr = np.floor(arr * 15.0).clip(0, 15) / 15.0  # Quantize to 16 levels
    arr = (arr * 255.0).astype(np.uint8)
    source = Image.fromarray(arr)

    # Create clean output image
    output = Image.new(source.mode, (cols * tile_size, rows * tile_size), 0)

    for row in range(rows):
        for col in range(cols):
            left = col * tile_size
            upper = row * tile_size
            cell = source.crop((left, upper, left + tile_size, upper + tile_size))
            output.paste(cell, (left, upper))

    output_path = biome_dir / f"atlas_{tile_size}x{tile_size}.png"
    output.save(output_path)
    return output_path


def main() -> int:
    parser = argparse.ArgumentParser(description="Preprocess ComfyUI tileset into clean atlas")
    parser.add_argument("--biome", required=True, help="Biome name (field, dungeon, town)")
    parser.add_argument("--tile-size", type=int, default=32, help="Tile size in pixels (default: 32)")
    parser.add_argument("--input-dir", type=Path, default=DEFAULT_INPUT_DIR, help="Input directory")
    args = parser.parse_args()

    try:
        output = preprocess_atlas(
            input_dir=args.input_dir,
            biome=args.biome,
            tile_size=args.tile_size,
        )
        print(f"Atlas written to {output}")
        return 0
    except FileNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
