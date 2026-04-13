"""Tests for tileset_preprocess.py — slice and reassemble tile atlas."""

from pathlib import Path

import pytest
from PIL import Image


@pytest.fixture
def sample_512(tmp_path: Path) -> Path:
    """Create a 512x512 test image with a 16x16 grid of 32px cells.
    Each cell has a unique gray value so we can verify slicing.
    Uses pixelated_tileset filename (preferred input stage)."""
    img = Image.new("L", (512, 512), 0)
    for row in range(16):
        for col in range(16):
            gray = (row * 16 + col) % 256
            for y in range(row * 32, (row + 1) * 32):
                for x in range(col * 32, (col + 1) * 32):
                    img.putpixel((x, y), gray)
    path = tmp_path / "pixelated_tileset_00001_.png"
    img.save(path)
    return tmp_path


def test_preprocess_creates_atlas(sample_512: Path):
    from scripts.tileset_preprocess import preprocess_atlas

    output = preprocess_atlas(
        input_dir=sample_512,
        biome="test",
        tile_size=32,
    )
    assert output.exists()
    assert output.name == "atlas_32x32.png"
    img = Image.open(output)
    assert img.size == (512, 512)


def test_preprocess_requantizes_to_16_levels(sample_512: Path):
    from scripts.tileset_preprocess import preprocess_atlas

    output = preprocess_atlas(
        input_dir=sample_512,
        biome="test",
        tile_size=32,
    )
    img = Image.open(output)
    import numpy as np

    arr = np.array(img)
    unique = np.unique(arr)
    # Should have exactly 16 evenly-spaced gray levels
    assert len(unique) == 16
    assert unique[0] == 0
    assert unique[-1] == 255
    # Check spacing is even (17 apart: 0,17,34,...,255)
    diffs = np.diff(unique)
    assert all(d == 17 for d in diffs)


def test_preprocess_rejects_missing_input(tmp_path: Path):
    from scripts.tileset_preprocess import preprocess_atlas

    with pytest.raises(FileNotFoundError):
        preprocess_atlas(input_dir=tmp_path, biome="nonexistent", tile_size=32)
