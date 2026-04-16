"""Tests for scripts/ldtk_vocabulary — IntGrid name↔value resolution."""

from __future__ import annotations

import pytest

from scripts.ldtk_vocabulary import (
    INTGRID_COLLISION,
    INTGRID_TERRAIN,
    biome_terrain_symbols,
    collision_name,
    collision_value,
    terrain_name,
    terrain_value,
)


# --- Collision lookups ---

def test_collision_value_round_trip() -> None:
    for entry in INTGRID_COLLISION:
        assert collision_value(entry["identifier"]) == entry["value"]
        assert collision_name(entry["value"]) == entry["identifier"]


def test_collision_value_unknown_name_raises() -> None:
    with pytest.raises(KeyError) as exc:
        collision_value("walkable")  # 'empty' is the canonical name
    assert "walkable" in str(exc.value)


def test_collision_name_unknown_value_raises() -> None:
    with pytest.raises(KeyError):
        collision_name(99)


# --- Terrain lookups ---

def test_terrain_value_round_trip_without_biome() -> None:
    for entry in INTGRID_TERRAIN:
        assert terrain_value(entry["identifier"]) == entry["value"]
        assert terrain_name(entry["value"]) == entry["identifier"]


def test_terrain_value_universal_works_in_every_biome() -> None:
    # 'ground' (value 1) is in the universal range, must be valid everywhere
    for biome in ("field", "dungeon", "town"):
        assert terrain_value("ground", biome) == 1


def test_terrain_value_biome_specific_rejected_in_wrong_biome() -> None:
    # 'crystal' is a dungeon-only symbol. A field zone painting 'crystal'
    # is almost certainly a mistake the agent should be told about.
    with pytest.raises(KeyError) as exc:
        terrain_value("crystal", "field")
    msg = str(exc.value)
    assert "crystal" in msg
    assert "field" in msg


def test_terrain_value_biome_specific_works_in_matching_biome() -> None:
    assert terrain_value("crystal", "dungeon") == 27
    assert terrain_value("cobblestone", "town") == 30
    assert terrain_value("tree_trunk", "field") == 12


def test_terrain_value_unknown_name_raises() -> None:
    with pytest.raises(KeyError):
        terrain_value("not_a_real_tile")


def test_terrain_value_unknown_biome_raises() -> None:
    with pytest.raises(KeyError) as exc:
        terrain_value("ground", "swamp")
    assert "swamp" in str(exc.value)


# --- biome_terrain_symbols ---

def test_biome_terrain_symbols_for_field_contains_universal_and_field() -> None:
    symbols = biome_terrain_symbols("field")
    # universal
    assert "ground" in symbols
    assert "door" in symbols
    # field
    assert "tree_trunk" in symbols
    assert "path_stone" in symbols
    # not dungeon/town
    assert "crystal" not in symbols
    assert "cobblestone" not in symbols


def test_biome_terrain_symbols_returns_sorted() -> None:
    symbols = biome_terrain_symbols("town")
    assert symbols == sorted(symbols)


def test_biome_terrain_symbols_unknown_biome_raises() -> None:
    with pytest.raises(KeyError):
        biome_terrain_symbols("underwater")
