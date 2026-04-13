#!/usr/bin/env python3
"""Classify and rearrange a grayscale tileset atlas into semantic IntGrid order.

Analyzes each 32x32 cell by brightness, edge density, and variance, then
assigns tiles to IntGrid positions based on visual profile matching.

Usage:
    python3 scripts/tile_classifier.py --biome=field --tile-size=32

Input:  build/tilesets/{biome}/atlas_32x32.png (from tileset_preprocess.py)
Output: build/tilesets/{biome}/atlas_32x32.png (overwritten, semantically ordered)
        build/tilesets/{biome}/atlas_unclassified.png (backup of original)
"""

from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageFilter

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_INPUT_DIR = PROJECT_ROOT / "build" / "tilesets"

# Tile visual profiles: (brightness, edge_density, variance) each 0.0-1.0
# brightness: 0=black, 1=white
# edge_density: 0=flat, 1=lots of edges
# variance: 0=uniform, 1=highly varied

UNIVERSAL_PROFILES = {
    0: ("void", 0.05, 0.05, 0.05),
    1: ("ground", 0.55, 0.15, 0.15),
    2: ("wall", 0.25, 0.60, 0.35),
    3: ("water_shallow", 0.45, 0.10, 0.10),
    4: ("water_deep", 0.20, 0.08, 0.08),
    5: ("pit", 0.08, 0.20, 0.10),
    6: ("door", 0.40, 0.55, 0.45),
    7: ("stairs_up", 0.45, 0.50, 0.35),
    8: ("stairs_down", 0.35, 0.50, 0.35),
    9: ("bridge", 0.50, 0.35, 0.30),
}

BIOME_PROFILES = {
    "field": {
        10: ("tall_grass", 0.40, 0.35, 0.30),
        11: ("bush", 0.30, 0.55, 0.45),
        12: ("tree_trunk", 0.20, 0.60, 0.50),
        13: ("fallen_log", 0.30, 0.40, 0.35),
        14: ("cliff_edge", 0.25, 0.55, 0.30),
        15: ("path_dirt", 0.60, 0.12, 0.12),
        16: ("path_stone", 0.55, 0.30, 0.25),
        17: ("stream_crossing", 0.42, 0.25, 0.20),
        18: ("undergrowth", 0.35, 0.40, 0.45),
        19: ("hollow", 0.18, 0.30, 0.25),
    },
    "dungeon": {
        20: ("cave_floor", 0.40, 0.20, 0.15),
        21: ("cave_wall", 0.25, 0.55, 0.35),
        22: ("lava", 0.35, 0.15, 0.20),
        23: ("mine_track", 0.45, 0.45, 0.30),
        24: ("cracked_floor", 0.42, 0.35, 0.25),
        25: ("ore_vein", 0.38, 0.50, 0.40),
        26: ("rubble", 0.30, 0.50, 0.40),
        27: ("crystal", 0.55, 0.45, 0.45),
        28: ("ice_floor", 0.65, 0.10, 0.10),
        29: ("dark_zone", 0.10, 0.15, 0.10),
    },
    "town": {
        30: ("cobblestone", 0.50, 0.30, 0.20),
        31: ("fence", 0.40, 0.55, 0.35),
        32: ("garden", 0.40, 0.35, 0.35),
        33: ("market_stall", 0.45, 0.50, 0.40),
        34: ("well_fountain", 0.40, 0.45, 0.35),
        35: ("building_wall", 0.30, 0.50, 0.30),
        36: ("interior_floor", 0.55, 0.15, 0.15),
        37: ("counter", 0.35, 0.45, 0.30),
        38: ("furniture", 0.30, 0.50, 0.40),
        39: ("signpost_lamp", 0.50, 0.45, 0.40),
    },
}


def analyze_cell(cell: Image.Image) -> tuple[float, float, float]:
    """Compute (brightness, edge_density, variance) for a grayscale cell."""
    arr = np.array(cell, dtype=np.float32) / 255.0

    brightness = float(np.mean(arr))
    variance = float(np.std(arr))

    # Edge density via Sobel-like filter
    edges = cell.filter(ImageFilter.FIND_EDGES)
    edge_arr = np.array(edges, dtype=np.float32) / 255.0
    edge_density = float(np.mean(edge_arr))

    return brightness, edge_density, variance


def profile_distance(
    cell_features: tuple[float, float, float],
    target_profile: tuple[float, float, float],
) -> float:
    """Euclidean distance between cell features and target profile."""
    return sum((a - b) ** 2 for a, b in zip(cell_features, target_profile, strict=False)) ** 0.5


def classify_atlas(
    atlas_path: Path,
    biome: str,
    tile_size: int = 32,
) -> Path:
    """Rearrange atlas tiles into semantic IntGrid order.

    Returns path to the rearranged atlas.
    """
    atlas = Image.open(atlas_path).convert("L")
    width, height = atlas.size
    cols = width // tile_size
    rows = height // tile_size

    # Extract all cells and analyze
    cells: list[tuple[Image.Image, tuple[float, float, float]]] = []
    for row in range(rows):
        for col in range(cols):
            left = col * tile_size
            upper = row * tile_size
            cell = atlas.crop((left, upper, left + tile_size, upper + tile_size))
            features = analyze_cell(cell)
            cells.append((cell, features))

    # Build target profiles for this biome
    profiles = dict(UNIVERSAL_PROFILES)
    profiles.update(BIOME_PROFILES.get(biome, {}))

    # Greedy assignment: for each IntGrid value, find best matching unassigned cell
    assigned: dict[int, Image.Image] = {}
    used_indices: set[int] = set()

    # Sort profiles by specificity (higher edge+variance first — more distinctive tiles first)
    sorted_values = sorted(
        profiles.keys(),
        key=lambda v: -(profiles[v][2] + profiles[v][3]),
    )

    for intgrid_value in sorted_values:
        _name, target_b, target_e, target_v = profiles[intgrid_value]
        target = (target_b, target_e, target_v)

        best_idx = -1
        best_dist = float("inf")
        for i, (_, features) in enumerate(cells):
            if i in used_indices:
                continue
            dist = profile_distance(features, target)
            if dist < best_dist:
                best_dist = dist
                best_idx = i

        if best_idx >= 0:
            assigned[intgrid_value] = cells[best_idx][0]
            used_indices.add(best_idx)

    # Collect unassigned cells for remaining positions
    remaining = [cells[i][0] for i in range(len(cells)) if i not in used_indices]
    remaining_iter = iter(remaining)

    # Build output atlas
    output = Image.new("L", (width, height), 0)
    for row in range(rows):
        for col in range(cols):
            idx = row * cols + col
            if idx in assigned:
                tile = assigned[idx]
            else:
                tile = next(remaining_iter, None)
                if tile is None:
                    continue
            output.paste(tile, (col * tile_size, row * tile_size))

    # Backup original and write rearranged
    backup_path = atlas_path.parent / "atlas_unclassified.png"
    shutil.copy2(atlas_path, backup_path)
    output.save(atlas_path)

    print(f"Classified {len(assigned)} tiles for biome '{biome}'")
    print(f"  Backup saved to {backup_path}")

    # Print assignment summary
    for v in sorted(assigned.keys()):
        name = profiles[v][0]
        print(f"  IntGrid {v:2d} ({name})")

    return atlas_path


def main() -> int:
    parser = argparse.ArgumentParser(description="Classify tileset atlas into IntGrid order")
    parser.add_argument("--biome", required=True, help="Biome name (field, dungeon, town)")
    parser.add_argument("--tile-size", type=int, default=32, help="Tile size in pixels")
    parser.add_argument("--input-dir", type=Path, default=DEFAULT_INPUT_DIR)
    args = parser.parse_args()

    biome_dir = args.input_dir / args.biome
    atlas_path = biome_dir / f"atlas_{args.tile_size}x{args.tile_size}.png"

    if not atlas_path.exists():
        print(f"Error: atlas not found at {atlas_path}", file=sys.stderr)
        return 1

    classify_atlas(atlas_path, args.biome, args.tile_size)
    print(f"Atlas rearranged: {atlas_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
