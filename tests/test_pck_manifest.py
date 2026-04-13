"""Tests for pck_manifest.py — generate PCK build manifest from LDtk data."""

import json
from pathlib import Path

import pytest
from PIL import Image


@pytest.fixture
def mock_ldtk(tmp_path: Path) -> Path:
    """Create a minimal LDtk project file with IntGrid values."""
    ldtk = {
        "levels": [
            {
                "identifier": "Whispering_Woods_Edge",
                "uid": 100,
                "iid": "aaa-bbb",
                "worldX": 0,
                "worldY": 0,
                "pxWid": 320,
                "pxHei": 256,
                "layerInstances": [
                    {
                        "__identifier": "Collision",
                        "__type": "IntGrid",
                        "__gridSize": 32,
                        "__cWid": 10,
                        "__cHei": 8,
                        "layerDefUid": 1,
                        "intGridCsv": [1, 1, 0, 0, 0, 0, 0, 0, 0, 0] * 8,
                    }
                ],
            }
        ],
        "defs": {
            "layers": [
                {
                    "uid": 1,
                    "identifier": "Collision",
                    "__type": "IntGrid",
                    "intGridValues": [
                        {"value": 0, "identifier": "empty"},
                        {"value": 1, "identifier": "solid"},
                    ],
                }
            ]
        },
    }
    path = tmp_path / "test.ldtk"
    path.write_text(json.dumps(ldtk))
    return path


@pytest.fixture
def mock_atlas(tmp_path: Path) -> Path:
    """Create a dummy atlas image."""
    img = Image.new("L", (512, 512), 128)
    path = tmp_path / "atlas_32x32.png"
    img.save(path)
    return path


@pytest.fixture
def mock_hex(tmp_path: Path) -> Path:
    """Create a dummy palette hex file."""
    path = tmp_path / "test.hex"
    colors = [f"#{i:02x}{i:02x}{i:02x}" for i in range(0, 256, 16)]
    path.write_text("\n".join(colors) + "\n")
    return path


def test_generate_manifest(mock_ldtk: Path, mock_atlas: Path, mock_hex: Path, tmp_path: Path):
    from scripts.pck_manifest import generate_manifest

    manifest = generate_manifest(
        ldtk_path=mock_ldtk,
        location="whispering-woods",
        biome="field",
        atlas_path=mock_atlas,
        father_hex=mock_hex,
        son_hex=mock_hex,
        output_dir=tmp_path / "output",
    )
    assert manifest["location"] == "whispering-woods"
    assert manifest["biome"] == "field"
    assert manifest["tile_size"] == 32
    assert manifest["grid_columns"] == 16
    assert manifest["grid_rows"] == 16
    assert Path(manifest["palettes"]["father"]).exists()
    assert Path(manifest["palettes"]["son"]).exists()
    # Manifest JSON file should exist
    assert (tmp_path / "output" / "manifest.json").exists()


def test_hex_to_palette_png(mock_hex: Path, tmp_path: Path):
    from scripts.pck_manifest import hex_to_palette_png

    output = hex_to_palette_png(mock_hex, tmp_path / "palette.png")
    assert output.exists()
    img = Image.open(output)
    assert img.size[1] == 1  # 1 pixel tall
    assert img.size[0] == 16  # 16 colors
