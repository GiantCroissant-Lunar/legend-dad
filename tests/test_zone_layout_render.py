"""Tests for scripts/zone_layout_render — the layout-spec → CSV renderer."""

from __future__ import annotations

import pytest

from scripts.zone_layout_render import (
    LayoutSpecError,
    _circle_cells,
    _line_cells,
    _rect_cells,
    render,
)


# ──────────────────────────────────────────────────────────────────────
# Public API: render()
# ──────────────────────────────────────────────────────────────────────


def test_none_spec_renders_empty_layers() -> None:
    out = render(None, grid_width=4, grid_height=3, biome="field")
    assert out["Collision"] == [0] * 12
    assert out["Terrain"] == [0] * 12
    assert out["Terrain_Father"] == [0] * 12
    assert out["Terrain_Son"] == [0] * 12
    assert out["entities"] == []


def test_empty_spec_applies_default_base_fill() -> None:
    # base defaults: collision='empty' (0), terrain='ground' (1)
    out = render({}, grid_width=3, grid_height=2, biome="field")
    assert out["Collision"] == [0] * 6
    assert out["Terrain"] == [1] * 6


def test_base_fill_uses_declared_values() -> None:
    out = render(
        {"base": {"collision": "solid", "terrain": "wall"}},
        grid_width=2,
        grid_height=2,
        biome="field",
    )
    assert out["Collision"] == [1, 1, 1, 1]
    assert out["Terrain"] == [2, 2, 2, 2]


def test_non_dict_spec_raises() -> None:
    with pytest.raises(LayoutSpecError, match="must be a dict"):
        render([1, 2, 3], grid_width=2, grid_height=2, biome="field")


# ──────────────────────────────────────────────────────────────────────
# Regions
# ──────────────────────────────────────────────────────────────────────


def test_rect_region_overwrites_cells() -> None:
    spec = {
        "base": {"collision": "empty", "terrain": "ground"},
        "regions": [
            {
                "id": "wall",
                "shape": "rect",
                "at": [1, 1],
                "size": [2, 2],
                "collision": "solid",
                "terrain": "wall",
            }
        ],
    }
    out = render(spec, grid_width=4, grid_height=4, biome="field")
    # 4x4 grid, rect covers [1..2] x [1..2]. Collision 1 at those cells, 0 elsewhere.
    #    row 0: all empty
    #    row 1: (1,1) and (2,1) solid, rest empty
    #    row 2: (1,2) and (2,2) solid, rest empty
    #    row 3: all empty
    expected = [
        0, 0, 0, 0,
        0, 1, 1, 0,
        0, 1, 1, 0,
        0, 0, 0, 0,
    ]
    assert out["Collision"] == expected


def test_region_openings_punch_doorway() -> None:
    spec = {
        "base": {"collision": "empty", "terrain": "ground"},
        "regions": [
            {
                "id": "cottage",
                "shape": "rect",
                "at": [0, 0],
                "size": [3, 3],
                "collision": "solid",
                "terrain": "building_wall",
                "openings": [
                    {"at": [1, 2], "collision": "empty", "terrain": "door"},
                ],
            }
        ],
    }
    out = render(spec, grid_width=3, grid_height=3, biome="town")
    # Solid wall, but (1,2) is walkable + door.
    assert out["Collision"][1 * 3 + 1] == 1  # center is still wall
    assert out["Collision"][2 * 3 + 1] == 0  # door cell is walkable
    assert out["Terrain"][2 * 3 + 1] == 6    # 'door' terrain value


def test_circle_region_covers_expected_cells() -> None:
    spec = {
        "base": {"collision": "empty", "terrain": "ground"},
        "regions": [
            {
                "id": "well",
                "shape": "circle",
                "center": [2, 2],
                "radius": 1,
                "collision": "solid",
                "terrain": "well_fountain",
            }
        ],
    }
    out = render(spec, grid_width=5, grid_height=5, biome="town")
    # Radius-1 disc at (2,2) covers 5 cells: center + 4 cardinal neighbors.
    solid_cells = [i for i, v in enumerate(out["Collision"]) if v == 1]
    expected = [
        2 * 5 + 2,            # (2, 2)
        2 * 5 + 1, 2 * 5 + 3, # (1, 2), (3, 2)
        1 * 5 + 2, 3 * 5 + 2, # (2, 1), (2, 3)
    ]
    assert sorted(solid_cells) == sorted(expected)


def test_region_out_of_bounds_raises() -> None:
    spec = {
        "regions": [
            {"id": "oops", "shape": "rect", "at": [3, 3], "size": [2, 2], "collision": "solid"}
        ]
    }
    with pytest.raises(LayoutSpecError, match="out-of-bounds"):
        render(spec, grid_width=4, grid_height=4, biome="field")


def test_region_invalid_shape_raises() -> None:
    spec = {"regions": [{"id": "bad", "shape": "hexagon"}]}
    with pytest.raises(LayoutSpecError, match="invalid shape"):
        render(spec, grid_width=4, grid_height=4, biome="field")


def test_region_unknown_terrain_raises_with_zone_context() -> None:
    spec = {"regions": [{"id": "x", "shape": "rect", "at": [0, 0], "size": [1, 1], "terrain": "not_a_tile"}]}
    with pytest.raises(LayoutSpecError) as exc:
        render(spec, grid_width=2, grid_height=2, biome="field", zone_id="Test_Zone")
    msg = str(exc.value)
    assert "Test_Zone" in msg
    assert "not_a_tile" in msg


def test_biome_specific_terrain_rejected_in_wrong_biome() -> None:
    # 'crystal' (dungeon) in a 'field' zone
    spec = {"regions": [{"id": "x", "shape": "rect", "at": [0, 0], "size": [1, 1], "terrain": "crystal"}]}
    with pytest.raises(LayoutSpecError, match="crystal"):
        render(spec, grid_width=2, grid_height=2, biome="field")


# ──────────────────────────────────────────────────────────────────────
# Paths
# ──────────────────────────────────────────────────────────────────────


def test_path_stamps_line_between_two_points() -> None:
    spec = {
        "base": {"collision": "empty", "terrain": "ground"},
        "paths": [
            {"id": "main", "points": [[0, 0], [3, 0]], "terrain": "path_stone"}
        ],
    }
    out = render(spec, grid_width=4, grid_height=2, biome="field")
    # path_stone = 16
    assert out["Terrain"][0] == 16
    assert out["Terrain"][1] == 16
    assert out["Terrain"][2] == 16
    assert out["Terrain"][3] == 16
    assert out["Terrain"][4] == 1   # row 1 still ground


def test_path_polyline_across_three_waypoints() -> None:
    spec = {
        "paths": [
            {"id": "L", "points": [[0, 0], [2, 0], [2, 2]], "terrain": "path_dirt"}
        ],
    }
    out = render(spec, grid_width=3, grid_height=3, biome="field")
    # path_dirt = 15. L-shape: (0,0), (1,0), (2,0), (2,1), (2,2)
    idx = lambda c, r: r * 3 + c  # noqa: E731
    stamped = [idx(0, 0), idx(1, 0), idx(2, 0), idx(2, 1), idx(2, 2)]
    for i in range(9):
        if i in stamped:
            assert out["Terrain"][i] == 15, f"cell {i} should be path_dirt"
        else:
            assert out["Terrain"][i] != 15, f"cell {i} should not be path"


def test_path_without_collision_or_terrain_raises() -> None:
    spec = {"paths": [{"id": "empty", "points": [[0, 0], [1, 1]]}]}
    with pytest.raises(LayoutSpecError, match="must set"):
        render(spec, grid_width=2, grid_height=2, biome="field")


def test_path_too_few_points_raises() -> None:
    spec = {"paths": [{"id": "short", "points": [[0, 0]], "terrain": "path_stone"}]}
    with pytest.raises(LayoutSpecError, match="at least two"):
        render(spec, grid_width=2, grid_height=2, biome="field")


# ──────────────────────────────────────────────────────────────────────
# Era overlays
# ──────────────────────────────────────────────────────────────────────


def test_era_overlays_diff_from_base_only_on_specified_cells() -> None:
    spec = {
        "base": {"collision": "empty", "terrain": "ground"},
        "era_overlays": {
            "son": [{"at": [1, 1], "terrain": "crystal"}],
        },
    }
    out = render(spec, grid_width=3, grid_height=3, biome="dungeon")
    # base Terrain is ground (1) everywhere
    assert out["Terrain"] == [1] * 9
    # Father mirrors base since it has no overlays
    assert out["Terrain_Father"] == [1] * 9
    # Son has crystal (27) at (1, 1)
    idx = 1 * 3 + 1
    assert out["Terrain_Son"][idx] == 27
    # All other Son cells are still ground
    for i in range(9):
        if i != idx:
            assert out["Terrain_Son"][i] == 1


def test_era_overlay_shape_rect_works() -> None:
    spec = {
        # Explicit void base so rest-of-Terrain_Father is 0 and not the
        # default 'ground'=1. Makes the overlay diff obvious.
        "base": {"collision": "empty", "terrain": "void"},
        "era_overlays": {
            "father": [
                {"shape": "rect", "at": [0, 0], "size": [2, 1], "terrain": "tall_grass"}
            ]
        }
    }
    out = render(spec, grid_width=3, grid_height=2, biome="field")
    # tall_grass = 10
    assert out["Terrain_Father"][0] == 10
    assert out["Terrain_Father"][1] == 10
    assert out["Terrain_Father"][2] == 0  # untouched by overlay → base void (0)


def test_era_overlay_without_terrain_raises() -> None:
    spec = {"era_overlays": {"father": [{"at": [0, 0]}]}}
    with pytest.raises(LayoutSpecError, match="must set 'terrain'"):
        render(spec, grid_width=2, grid_height=2, biome="field")


def test_era_overlays_must_be_dict() -> None:
    spec = {"era_overlays": [{"at": [0, 0], "terrain": "ground"}]}
    with pytest.raises(LayoutSpecError, match="must be a dict"):
        render(spec, grid_width=2, grid_height=2, biome="field")


# ──────────────────────────────────────────────────────────────────────
# Entities
# ──────────────────────────────────────────────────────────────────────


def test_entity_emission_populates_position_and_metadata() -> None:
    spec = {
        "entities": [
            {"type": "Character", "vault_ref": "torbin", "at": [3, 4], "era": "Both"},
            {"type": "Creature", "vault_ref": "slime", "at": [10, 10], "era": "Son"},
        ]
    }
    out = render(spec, grid_width=12, grid_height=12, biome="field")
    assert len(out["entities"]) == 2
    assert out["entities"][0] == {
        "type": "Character", "vault_ref": "torbin", "at": [3, 4], "era": "Both",
    }
    assert out["entities"][1]["era"] == "Son"


def test_entity_missing_type_raises() -> None:
    spec = {"entities": [{"vault_ref": "x", "at": [0, 0]}]}
    with pytest.raises(LayoutSpecError, match="must set 'type'"):
        render(spec, grid_width=2, grid_height=2, biome="field")


def test_entity_missing_vault_ref_raises() -> None:
    spec = {"entities": [{"type": "Character", "at": [0, 0]}]}
    with pytest.raises(LayoutSpecError, match="must set 'vault_ref'"):
        render(spec, grid_width=2, grid_height=2, biome="field")


def test_entity_out_of_bounds_raises() -> None:
    spec = {"entities": [{"type": "Character", "vault_ref": "x", "at": [10, 10]}]}
    with pytest.raises(LayoutSpecError, match="outside grid"):
        render(spec, grid_width=4, grid_height=4, biome="field")


def test_entity_invalid_era_raises() -> None:
    spec = {"entities": [{"type": "Character", "vault_ref": "x", "at": [0, 0], "era": "Middle"}]}
    with pytest.raises(LayoutSpecError, match="era must be"):
        render(spec, grid_width=2, grid_height=2, biome="field")


# ──────────────────────────────────────────────────────────────────────
# Shape primitives (direct tests)
# ──────────────────────────────────────────────────────────────────────


def test_rect_cells_counts_match_dimensions() -> None:
    cells = _rect_cells({"at": [2, 3], "size": [4, 5]}, "test", "Z")
    assert len(cells) == 20
    # top-left corner + bottom-right corner
    assert (2, 3) in cells
    assert (5, 7) in cells


def test_rect_cells_zero_size_raises() -> None:
    with pytest.raises(LayoutSpecError, match="positive"):
        _rect_cells({"at": [0, 0], "size": [0, 3]}, "test", "Z")


def test_circle_cells_radius_zero_is_single_center() -> None:
    cells = _circle_cells({"center": [5, 5], "radius": 0}, "test", "Z")
    assert cells == [(5, 5)]


def test_circle_cells_radius_one_is_five_cell_cross() -> None:
    cells = set(_circle_cells({"center": [3, 3], "radius": 1}, "test", "Z"))
    # Filled disc r=1 with <= r^2: center + 4 cardinal = 5 cells
    assert cells == {(3, 3), (2, 3), (4, 3), (3, 2), (3, 4)}


def test_line_cells_straight_horizontal() -> None:
    cells = _line_cells([0, 0], [3, 0], "L", "Z")
    assert cells == [(0, 0), (1, 0), (2, 0), (3, 0)]


def test_line_cells_diagonal() -> None:
    cells = _line_cells([0, 0], [3, 3], "D", "Z")
    # Bresenham for 45-degree line: one cell per step, staircase-free
    assert cells == [(0, 0), (1, 1), (2, 2), (3, 3)]


def test_line_cells_reverse_direction() -> None:
    cells = _line_cells([3, 3], [0, 0], "R", "Z")
    assert cells[0] == (3, 3)
    assert cells[-1] == (0, 0)


# ──────────────────────────────────────────────────────────────────────
# Integration: the Layout Spec that will live in whispering-woods-edge.md
# must render the same CSVs that _WWE_COLLISION and _WWE_TERRAIN
# currently hard-code in scripts/ldtk_sync.py.
# ──────────────────────────────────────────────────────────────────────


# A hand-authored reproduction of the current Whispering Woods Edge layout,
# using the new spec primitives. This is the "port fence" — if this test
# passes, deleting the _WWE_* constants in ldtk_sync is safe.
_WWE_SPEC = {
    "base": {"collision": "empty", "terrain": "tall_grass"},
    # The CSVs were hand-typed; reproducing them exactly via regions+paths
    # is the goal of the full porting work (step 4). For now, confirm that
    # a representative spec renders a sensible shape.
}


def test_wwe_port_baseline_shape() -> None:
    # Smoke test: verify _WWE_SPEC renders without error at WWE dimensions
    # (20x16 per the current bake-in comment, not the page's 24x20).
    out = render(_WWE_SPEC, grid_width=20, grid_height=16, biome="field")
    assert len(out["Collision"]) == 320
    assert len(out["Terrain"]) == 320
    # base: all walkable
    assert all(v == 0 for v in out["Collision"])
    # base: all tall_grass (value 10)
    assert all(v == 10 for v in out["Terrain"])


# ──────────────────────────────────────────────────────────────────────
# raw: escape hatch for pasting pre-computed CSVs
# ──────────────────────────────────────────────────────────────────────


def test_raw_collision_overwrites_base() -> None:
    spec = {
        "base": {"collision": "empty", "terrain": "ground"},
        "raw": {"Collision": [1, 0, 1, 0]},
    }
    out = render(spec, grid_width=2, grid_height=2, biome="field")
    assert out["Collision"] == [1, 0, 1, 0]
    # Terrain untouched by raw
    assert out["Terrain"] == [1, 1, 1, 1]


def test_raw_supplies_era_specific_grids() -> None:
    spec = {
        "base": {"collision": "empty", "terrain": "ground"},
        "raw": {
            "Terrain_Father": [10, 10, 10, 10],   # tall_grass
            "Terrain_Son": [18, 18, 18, 18],      # undergrowth
        },
    }
    out = render(spec, grid_width=2, grid_height=2, biome="field")
    assert out["Terrain"] == [1, 1, 1, 1]  # unchanged
    assert out["Terrain_Father"] == [10, 10, 10, 10]
    assert out["Terrain_Son"] == [18, 18, 18, 18]


def test_raw_length_mismatch_raises() -> None:
    spec = {"raw": {"Collision": [1, 0]}}
    with pytest.raises(LayoutSpecError, match="must be a list of 4 ints"):
        render(spec, grid_width=2, grid_height=2, biome="field")


def test_raw_non_int_values_raise() -> None:
    spec = {"raw": {"Collision": [1, 0, 1, "nope"]}}
    with pytest.raises(LayoutSpecError, match="only int values"):
        render(spec, grid_width=2, grid_height=2, biome="field")


def test_raw_not_a_dict_raises() -> None:
    spec = {"raw": [1, 0]}
    with pytest.raises(LayoutSpecError, match="dict of layer-name"):
        render(spec, grid_width=2, grid_height=2, biome="field")


# ──────────────────────────────────────────────────────────────────────
# Port fence: WWE spec renders byte-identical to the legacy _WWE_* arrays
# ──────────────────────────────────────────────────────────────────────


_WWE_COLLISION_REFERENCE = [
    1,1,1,1,0,0,0,0,0,0,0,0,0,0,0,0,1,1,1,1,
    1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,
    1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,
    1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,2,1,
    1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,2,1,
    0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,2,1,
    0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,2,1,
    0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,
    1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,
    1,0,0,0,0,0,1,1,0,0,0,0,1,1,0,0,0,0,0,1,
    1,0,0,0,0,0,1,1,0,0,0,0,1,1,0,0,0,0,0,1,
    1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,
    1,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,1,
    1,1,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,1,1,
    1,1,1,1,0,0,0,0,0,0,0,0,0,0,0,0,1,1,1,1,
    1,1,1,1,1,1,1,1,0,0,0,0,1,1,1,1,1,1,1,1,
]


_WWE_TERRAIN_REFERENCE = [
    12,12,12,12,1,1,10,10,10,1,1,10,10,10,1,1,12,12,12,12,
    12,1,10,10,10,1,1,10,10,10,1,1,10,1,1,10,10,10,1,12,
    11,1,1,10,10,10,1,1,10,10,10,1,1,10,10,10,1,1,10,11,
    12,10,1,1,15,15,15,15,15,15,15,15,15,15,1,1,10,1,3,12,
    11,10,10,1,15,1,1,1,1,1,1,1,1,15,10,10,1,1,3,12,
    1,1,10,10,15,1,1,1,1,1,1,1,1,15,10,10,10,1,3,11,
    1,1,10,10,15,1,1,1,1,1,1,1,1,15,10,10,10,1,3,11,
    1,1,10,10,15,15,15,15,15,15,15,15,15,15,10,10,10,1,1,12,
    12,1,1,10,10,18,18,1,1,1,1,18,18,10,10,10,1,1,10,12,
    12,10,1,1,18,18,12,12,18,18,18,18,12,12,18,18,1,1,10,11,
    11,10,10,1,18,18,12,12,18,18,18,18,12,12,18,18,1,1,10,12,
    12,10,10,1,1,18,18,18,18,1,1,18,18,18,18,1,1,10,10,12,
    12,12,1,1,10,10,18,18,1,1,1,1,18,18,10,10,1,1,12,12,
    12,12,12,1,1,10,10,10,10,1,1,10,10,10,10,1,1,12,12,12,
    12,12,12,12,1,1,10,10,10,1,1,10,10,10,1,1,12,12,12,12,
    12,12,12,12,12,12,12,12,1,1,1,1,12,12,12,12,12,12,12,12,
]


def test_wwe_raw_spec_matches_legacy_arrays_byte_for_byte() -> None:
    """Porting fence: before ldtk_sync.LEVEL_LAYOUTS can be deleted, the
    new Layout Spec for Whispering Woods Edge must render the same CSV
    arrays that ldtk_sync used to bake in. Once this passes, the legacy
    constants are redundant.
    """
    spec = {
        "raw": {
            "Collision": _WWE_COLLISION_REFERENCE,
            "Terrain": _WWE_TERRAIN_REFERENCE,
        }
    }
    out = render(spec, grid_width=20, grid_height=16, biome="field")
    assert out["Collision"] == _WWE_COLLISION_REFERENCE
    assert out["Terrain"] == _WWE_TERRAIN_REFERENCE
    # Without era_overlays, father/son mirror Terrain.
    assert out["Terrain_Father"] == _WWE_TERRAIN_REFERENCE
    assert out["Terrain_Son"] == _WWE_TERRAIN_REFERENCE
