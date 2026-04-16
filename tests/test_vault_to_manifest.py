import json
import subprocess
import sys
from pathlib import Path

import jsonschema

from vault_to_manifest import (
    build_entity,
    extract_creative_prompts,
    extract_sections,
    generate_manifest,
    parse_vault_page,
)


def test_parse_frontmatter_extracts_type(sample_character_md):
    page = parse_vault_page(sample_character_md)
    assert page["frontmatter"]["type"] == "character"


def test_parse_frontmatter_extracts_articy_id(sample_character_md):
    page = parse_vault_page(sample_character_md)
    assert page["frontmatter"]["articy-id"] == ""


def test_parse_frontmatter_extracts_connections(sample_character_md):
    page = parse_vault_page(sample_character_md)
    assert "[[Elder Aldric]]" in page["frontmatter"]["connections"]


def test_parse_content_extracts_body(sample_character_md):
    page = parse_vault_page(sample_character_md)
    assert "# Sera" in page["content"]
    assert "## Backstory" in page["content"]


def test_extract_sections_finds_h2_headings(sample_character_md):
    page = parse_vault_page(sample_character_md)
    sections = extract_sections(page["content"])
    assert "Overview" in sections
    assert "Backstory" in sections
    assert "Personality & Motivation" in sections
    assert "Relationships" in sections
    assert "Creative Prompts" in sections


def test_extract_sections_content_is_stripped(sample_character_md):
    page = parse_vault_page(sample_character_md)
    sections = extract_sections(page["content"])
    assert sections["Overview"].startswith("A young scholar")


def test_extract_creative_prompts(sample_character_md):
    page = parse_vault_page(sample_character_md)
    sections = extract_sections(page["content"])
    prompts = extract_creative_prompts(sections.get("Creative Prompts", ""))
    assert "portrait" in prompts
    assert "voice" in prompts
    assert "theme-music" in prompts
    assert len(prompts["portrait"]) >= 100


def test_build_entity_sets_display_name(sample_character_md):
    entity = build_entity(sample_character_md, "vault/world/characters/sera.md")
    assert entity["display_name"] == "Sera"


def test_build_entity_sets_type(sample_character_md):
    entity = build_entity(sample_character_md, "vault/world/characters/sera.md")
    assert entity["type"] == "character"


def test_build_entity_extracts_template_properties(sample_character_md):
    entity = build_entity(sample_character_md, "vault/world/characters/sera.md")
    props = entity["template_properties"]
    assert "backstory" in props
    assert "personality_and_motivation" in props
    assert "overview" in props


def test_build_entity_extracts_creative_prompts(sample_character_md):
    entity = build_entity(sample_character_md, "vault/world/characters/sera.md")
    assert "portrait" in entity["creative_prompts"]
    assert "voice" in entity["creative_prompts"]
    assert "theme-music" in entity["creative_prompts"]


def test_build_entity_parses_connections(sample_character_md):
    entity = build_entity(sample_character_md, "vault/world/characters/sera.md")
    targets = [c["target_vault_path"] for c in entity["connections"]]
    assert any("Elder Aldric" in t for t in targets)


def test_build_entity_sets_vault_path(sample_character_md):
    entity = build_entity(sample_character_md, "vault/world/characters/sera.md")
    assert entity["vault_path"] == "vault/world/characters/sera.md"


def test_build_entity_defaults_status_to_new(sample_character_md):
    entity = build_entity(sample_character_md, "vault/world/characters/sera.md")
    assert entity["status"] == "new"


def test_generate_manifest_from_vault_dir(tmp_vault, schema):
    vault_world = tmp_vault / "vault" / "world"
    manifest = generate_manifest(vault_world)
    assert manifest["version"] == "0.1.0"
    assert manifest["generated_by"] == "vault_to_manifest"
    assert len(manifest["entities"]) == 2


def test_generate_manifest_validates_against_schema(tmp_vault, schema):
    vault_world = tmp_vault / "vault" / "world"
    manifest = generate_manifest(vault_world)
    jsonschema.validate(manifest, schema)


def test_generate_manifest_entity_types(tmp_vault, schema):
    vault_world = tmp_vault / "vault" / "world"
    manifest = generate_manifest(vault_world)
    types = {e["type"] for e in manifest["entities"]}
    assert types == {"character", "location"}


def test_generate_manifest_json_roundtrip(tmp_vault, schema):
    vault_world = tmp_vault / "vault" / "world"
    manifest = generate_manifest(vault_world)
    text = json.dumps(manifest, indent=2)
    reloaded = json.loads(text)
    jsonschema.validate(reloaded, schema)


def test_cli_generates_manifest_file(tmp_vault):
    vault_world = tmp_vault / "vault" / "world"
    output_file = tmp_vault / "import-manifest.json"
    result = subprocess.run(
        [sys.executable, "scripts/vault_to_manifest.py", str(vault_world), str(output_file)],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr
    assert output_file.exists()
    data = json.loads(output_file.read_text())
    assert len(data["entities"]) == 2


def test_cli_validates_against_schema_flag(tmp_vault):
    vault_world = tmp_vault / "vault" / "world"
    output_file = tmp_vault / "import-manifest.json"
    schema_file = Path(__file__).parent.parent / "project" / "articy" / "schemas" / "import-manifest.schema.json"
    result = subprocess.run(
        [
            sys.executable,
            "scripts/vault_to_manifest.py",
            str(vault_world),
            str(output_file),
            "--schema",
            str(schema_file),
        ],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr
    assert "Validated against schema" in result.stdout


# --- Phase 2A: Mechanical frontmatter lifting ---


def test_bestiary_battle_stats_lifted(sample_bestiary_md):
    entity = build_entity(sample_bestiary_md, "vault/world/bestiary/crystal-crawler.md")
    stats = entity["template_properties"]["battle_stats"]
    assert stats["max_hp"] == 18
    assert stats["atk"] == 9
    assert stats["def"] == 5
    assert stats["spd"] == 11
    assert stats["xp_reward"] == 14
    assert stats["gold_reward"] == 9


def test_bestiary_actions_lifted(sample_bestiary_md):
    entity = build_entity(sample_bestiary_md, "vault/world/bestiary/crystal-crawler.md")
    actions = entity["template_properties"]["actions"]
    assert len(actions) == 2
    assert actions[0]["id"] == "crystal_slash"
    assert actions[0]["kind"] == "attack"
    assert actions[0]["frequency"] == 0.7
    assert actions[1]["id"] == "resonance_pulse"
    assert actions[1]["status_effect"] == "paralysis"


def test_bestiary_group_size_lifted(sample_bestiary_md):
    entity = build_entity(sample_bestiary_md, "vault/world/bestiary/crystal-crawler.md")
    assert entity["template_properties"]["group_size_min"] == 3
    assert entity["template_properties"]["group_size_max"] == 6


def test_bestiary_zone_affinity_lifted(sample_bestiary_md):
    entity = build_entity(sample_bestiary_md, "vault/world/bestiary/crystal-crawler.md")
    affinity = entity["template_properties"]["zone_affinity"]
    assert len(affinity) == 2
    assert "[[Iron Peaks Upper Mines]]" in affinity


def test_zone_encounter_table_lifted(sample_zone_md):
    entity = build_entity(sample_zone_md, "vault/world/zones/whispering-woods-edge.md")
    tbl = entity["template_properties"]["encounter_table"]
    assert len(tbl) == 2
    assert tbl[0]["bestiary"] == "[[Moss Lurker]]"
    assert tbl[0]["weight"] == 4
    assert tbl[0]["era"] == "son"
    assert entity["template_properties"]["encounter_rate"] == 0.12
    assert entity["template_properties"]["difficulty_tier"] == 2


def test_location_recommended_level_lifted(sample_location_with_tier_md):
    entity = build_entity(sample_location_with_tier_md, "vault/world/locations/whispering-woods.md")
    assert entity["template_properties"]["recommended_level_min"] == 2
    assert entity["template_properties"]["recommended_level_max"] == 5
    assert entity["template_properties"]["difficulty_tier"] == 2


def test_bestiary_validates_against_schema(sample_bestiary_md, schema):
    entity = build_entity(sample_bestiary_md, "vault/world/bestiary/crystal-crawler.md")
    manifest = {
        "version": "0.1.0",
        "generated": "2026-04-16T00:00:00+00:00",
        "generated_by": "vault_to_manifest",
        "entities": [entity],
    }
    jsonschema.validate(manifest, schema)


def test_zone_validates_against_schema(sample_zone_md, schema):
    entity = build_entity(sample_zone_md, "vault/world/zones/whispering-woods-edge.md")
    manifest = {
        "version": "0.1.0",
        "generated": "2026-04-16T00:00:00+00:00",
        "generated_by": "vault_to_manifest",
        "entities": [entity],
    }
    jsonschema.validate(manifest, schema)
