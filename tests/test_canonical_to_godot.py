import json
from pathlib import Path

from adapters.canonical_to_godot import emit_enemy_tres, emit_encounter_tres


def test_emit_enemy_tres_writes_valid_tres(tmp_path):
    entity = {
        "display_name": "Moss Lurker",
        "template_properties": {
            "battle_stats": {"max_hp": 14, "atk": 7, "def": 3, "spd": 5, "xp_reward": 8, "gold_reward": 4, "level": 2},
            "actions": [
                {"id": "spore_bite", "kind": "attack", "frequency": 0.6, "power_min": 3, "power_max": 6, "target_kind": "enemy", "status_effect": "poison"},
            ],
            "group_size_min": 1,
            "group_size_max": 3,
        },
    }
    out = tmp_path / "moss_lurker.tres"
    emit_enemy_tres(entity, out)
    txt = out.read_text()
    assert 'script_class="EnemyDefinition"' in txt
    assert "max_hp = 14" in txt
    assert "attack = 7" in txt
    assert "defense = 3" in txt
    assert "group_size_min = 1" in txt
    assert "group_size_max = 3" in txt
    assert 'id = "moss_lurker"' in txt


def test_emit_encounter_tres_writes_entries(tmp_path):
    entity = {
        "display_name": "Whispering Woods Edge",
        "template_properties": {
            "encounter_table": [
                {"bestiary": "[[Moss Lurker]]", "weight": 4, "era": "son"},
                {"bestiary": "[[Thornbriar Stalker]]", "weight": 1, "era": "son"},
            ],
            "encounter_rate": 0.12,
            "difficulty_tier": 2,
        },
    }
    out = tmp_path / "whispering_woods_edge.tres"
    emit_encounter_tres(entity, out)
    txt = out.read_text()
    assert 'script_class="EncounterTable"' in txt
    assert '"moss_lurker"' in txt
    assert '"thornbriar_stalker"' in txt
    assert "encounter_rate = 0.12" in txt
    assert "difficulty_tier = 2" in txt


def test_emit_enemy_tres_with_spell_actions(tmp_path):
    entity = {
        "display_name": "Shade Wisp",
        "template_properties": {
            "battle_stats": {"max_hp": 10, "atk": 4, "def": 2, "spd": 12, "max_mp": 12, "xp_reward": 12, "gold_reward": 6, "level": 4},
            "actions": [
                {"id": "chill_touch", "kind": "attack", "frequency": 0.5},
                {"id": "cast_sleep", "kind": "spell", "frequency": 0.3, "spell_id": "sleep"},
            ],
            "group_size_min": 2,
            "group_size_max": 4,
        },
    }
    out = tmp_path / "shade_wisp.tres"
    emit_enemy_tres(entity, out)
    txt = out.read_text()
    assert "max_mp = 12" in txt
    assert 'spells = PackedStringArray("sleep")' in txt
