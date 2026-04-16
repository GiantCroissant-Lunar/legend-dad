"""Adapter: import-manifest.json → Godot .tres resources.

Called from Taskfile (`task content:generate:tres`). Keeps Godot data
in lock-step with articy exports — each pipeline run regenerates all
bestiary + encounter .tres files into the relevant bundle directories.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
ENEMIES_DIR = REPO_ROOT / "project/shared/content/enemies/enemies-core"
ENCOUNTERS_DIR = REPO_ROOT / "project/shared/content/encounters/encounters-core"


def _slug(display_name: str) -> str:
    return re.sub(r"[^a-z0-9_]", "_", display_name.lower()).strip("_")


def _wikilink_to_id(ref: str) -> str:
    """'[[Moss Lurker]]' → 'moss_lurker'."""
    inner = ref.strip().strip("[]")
    return _slug(inner)


def emit_enemy_tres(entity: dict, out_path: Path) -> None:
    """Write an EnemyDefinition .tres from a bestiary manifest entity."""
    props = entity["template_properties"]
    stats = props.get("battle_stats", {})
    actions = props.get("actions", [])
    slug = _slug(entity["display_name"])

    # Map bestiary spells from actions with kind=spell
    spell_ids = [a["spell_id"] for a in actions if a.get("kind") == "spell" and a.get("spell_id")]

    lines = [
        '[gd_resource type="Resource" script_class="EnemyDefinition" load_steps=2 format=3]',
        "",
        '[ext_resource type="Script" path="res://lib/resources/enemy_definition.gd" id="1_def"]',
        "",
        "[resource]",
        'script = ExtResource("1_def")',
        f'id = "{slug}"',
        f'display_name = "{entity["display_name"]}"',
        f"max_hp = {stats.get('max_hp', 1)}",
        f"max_mp = {stats.get('max_mp', 0)}",
        f"attack = {stats.get('atk', 1)}",
        f"defense = {stats.get('def', 0)}",
        f"spd = {stats.get('spd', 1)}",
        f"level = {stats.get('level', 1)}",
        f"xp_reward = {stats.get('xp_reward', 0)}",
        f"gold_reward = {stats.get('gold_reward', 0)}",
        f"group_size_min = {props.get('group_size_min', 1)}",
        f"group_size_max = {props.get('group_size_max', 1)}",
    ]
    if spell_ids:
        packed = ", ".join(f'"{s}"' for s in spell_ids)
        lines.append(f"spells = PackedStringArray({packed})")

    out_path.write_text("\n".join(lines) + "\n")


def emit_encounter_tres(entity: dict, out_path: Path) -> None:
    """Write an EncounterTable .tres from a zone manifest entity."""
    props = entity["template_properties"]
    table = props.get("encounter_table", [])
    slug = _slug(entity["display_name"])

    lines = [
        '[gd_resource type="Resource" script_class="EncounterTable" load_steps=2 format=3]',
        "",
        '[ext_resource type="Script" path="res://lib/resources/encounter_table.gd" id="1_def"]',
        "",
        "[resource]",
        'script = ExtResource("1_def")',
        f'zone_id = "{slug}"',
        f"encounter_rate = {float(props.get('encounter_rate', 0.0))}",
        f"difficulty_tier = {int(props.get('difficulty_tier', 1))}",
        "entries = [",
    ]
    for row in table:
        bid = _wikilink_to_id(row["bestiary"])
        era = row.get("era", "both")
        weight = int(row.get("weight", 1))
        lines.append(f'\t{{ "bestiary_id": "{bid}", "weight": {weight}, "era": "{era}" }},')
    lines.append("]")

    out_path.write_text("\n".join(lines) + "\n")


def _update_bundle(bundle_path: Path, kind: str, dir_path: Path) -> None:
    """Update a bundle.json's provides list with all .tres files in the dir."""
    bundle = json.loads(bundle_path.read_text(encoding="utf-8"))
    ids = sorted(p.stem for p in dir_path.glob("*.tres"))
    bundle["provides"][kind] = ids
    bundle_path.write_text(json.dumps(bundle, indent=2) + "\n")


def main() -> int:
    manifest_path = REPO_ROOT / "project/articy/import-manifest.json"
    if not manifest_path.exists():
        print(f"Error: {manifest_path} not found", file=sys.stderr)
        return 1

    doc = json.loads(manifest_path.read_text(encoding="utf-8"))
    enemies_written = 0
    encounters_written = 0

    for entity in doc["entities"]:
        entity_type = entity.get("type", "")
        tp = entity.get("template_properties", {})

        if entity_type == "bestiary" and tp.get("battle_stats"):
            out = ENEMIES_DIR / f"{_slug(entity['display_name'])}.tres"
            emit_enemy_tres(entity, out)
            enemies_written += 1

        elif entity_type == "zone" and tp.get("encounter_table"):
            out = ENCOUNTERS_DIR / f"{_slug(entity['display_name'])}.tres"
            emit_encounter_tres(entity, out)
            encounters_written += 1

    # Update bundle manifests
    _update_bundle(ENEMIES_DIR / "bundle.json", "enemies", ENEMIES_DIR)
    _update_bundle(ENCOUNTERS_DIR / "bundle.json", "encounters", ENCOUNTERS_DIR)

    print(f"Generated {enemies_written} enemy .tres, {encounters_written} encounter .tres")
    return 0


if __name__ == "__main__":
    sys.exit(main())
