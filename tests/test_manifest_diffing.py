"""Tests for manifest diffing logic in vault_to_manifest.py."""

import json
from pathlib import Path

from scripts.vault_to_manifest import (
    _entity_content_hash,
    diff_against_previous,
    generate_manifest,
)


def _make_entity(vault_path="vault/world/characters/sera.md", articy_id="", display_name="Sera", **overrides):
    """Build a minimal entity dict for testing."""
    entity = {
        "vault_path": vault_path,
        "articy_id": articy_id,
        "type": "character",
        "status": "new",
        "display_name": display_name,
        "template_properties": {"overview": "A young scholar."},
        "connections": [],
        "creative_prompts": {},
        "dialogue_hooks": [],
        "flow_notes": "",
    }
    entity.update(overrides)
    return entity


def _make_manifest(*entities):
    return {
        "version": "0.1.0",
        "generated": "2026-04-12T00:00:00+00:00",
        "generated_by": "vault_to_manifest",
        "entities": list(entities),
    }


def _write_manifest(path: Path, manifest: dict):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(manifest, f)


class TestEntityContentHash:
    def test_identical_entities_same_hash(self):
        a = _make_entity()
        b = _make_entity()
        assert _entity_content_hash(a) == _entity_content_hash(b)

    def test_different_display_name_different_hash(self):
        a = _make_entity(display_name="Sera")
        b = _make_entity(display_name="Aldric")
        assert _entity_content_hash(a) != _entity_content_hash(b)

    def test_different_template_props_different_hash(self):
        a = _make_entity(template_properties={"overview": "Original"})
        b = _make_entity(template_properties={"overview": "Changed"})
        assert _entity_content_hash(a) != _entity_content_hash(b)

    def test_different_creative_prompts_different_hash(self):
        a = _make_entity(creative_prompts={})
        b = _make_entity(creative_prompts={"portrait": "pixel art..."})
        assert _entity_content_hash(a) != _entity_content_hash(b)

    def test_articy_id_not_in_hash(self):
        """articy_id changes should not affect the content hash."""
        a = _make_entity(articy_id="")
        b = _make_entity(articy_id="0x01000001")
        assert _entity_content_hash(a) == _entity_content_hash(b)


class TestDiffAgainstPrevious:
    def test_no_previous_file_all_new(self, tmp_path):
        manifest = _make_manifest(_make_entity())
        result = diff_against_previous(manifest, tmp_path / "nonexistent.json")
        assert result["entities"][0]["status"] == "new"

    def test_new_entity(self, tmp_path):
        prev = _make_manifest()
        _write_manifest(tmp_path / "prev.json", prev)

        current = _make_manifest(_make_entity())
        result = diff_against_previous(current, tmp_path / "prev.json")
        assert result["entities"][0]["status"] == "new"

    def test_unchanged_entity(self, tmp_path):
        entity = _make_entity(articy_id="0x01000001")
        prev = _make_manifest(entity)
        _write_manifest(tmp_path / "prev.json", prev)

        current = _make_manifest(_make_entity())
        result = diff_against_previous(current, tmp_path / "prev.json")
        assert result["entities"][0]["status"] == "unchanged"
        assert result["entities"][0]["articy_id"] == "0x01000001"

    def test_updated_entity(self, tmp_path):
        prev_entity = _make_entity(
            articy_id="0x01000001",
            template_properties={"overview": "Original text."},
        )
        prev = _make_manifest(prev_entity)
        _write_manifest(tmp_path / "prev.json", prev)

        current_entity = _make_entity(
            template_properties={"overview": "Updated text."},
        )
        current = _make_manifest(current_entity)
        result = diff_against_previous(current, tmp_path / "prev.json")
        assert result["entities"][0]["status"] == "updated"
        assert result["entities"][0]["articy_id"] == "0x01000001"

    def test_deleted_entity_warning(self, tmp_path, capsys):
        prev_entity = _make_entity(
            vault_path="vault/world/characters/removed.md",
            articy_id="0x01000002",
        )
        prev = _make_manifest(prev_entity)
        _write_manifest(tmp_path / "prev.json", prev)

        current = _make_manifest()
        diff_against_previous(current, tmp_path / "prev.json")
        captured = capsys.readouterr()
        assert "removed from vault" in captured.err
        assert "vault/world/characters/removed.md" in captured.err

    def test_empty_articy_id_stays_new(self, tmp_path):
        """Entity in previous manifest with empty articy_id should still be 'new'."""
        prev_entity = _make_entity(articy_id="")
        prev = _make_manifest(prev_entity)
        _write_manifest(tmp_path / "prev.json", prev)

        current = _make_manifest(_make_entity())
        result = diff_against_previous(current, tmp_path / "prev.json")
        assert result["entities"][0]["status"] == "new"

    def test_articy_id_carry_forward_on_unchanged(self, tmp_path):
        prev_entity = _make_entity(articy_id="0xABCD1234")
        prev = _make_manifest(prev_entity)
        _write_manifest(tmp_path / "prev.json", prev)

        current_entity = _make_entity(articy_id="")
        current = _make_manifest(current_entity)
        result = diff_against_previous(current, tmp_path / "prev.json")
        assert result["entities"][0]["articy_id"] == "0xABCD1234"

    def test_multiple_entities_mixed_status(self, tmp_path):
        sera = _make_entity(vault_path="vault/world/characters/sera.md", articy_id="0x01")
        aldric = _make_entity(
            vault_path="vault/world/characters/aldric.md",
            articy_id="0x02",
            display_name="Elder Aldric",
            template_properties={"overview": "Old mentor."},
        )
        prev = _make_manifest(sera, aldric)
        _write_manifest(tmp_path / "prev.json", prev)

        sera_new = _make_entity(vault_path="vault/world/characters/sera.md")
        aldric_changed = _make_entity(
            vault_path="vault/world/characters/aldric.md",
            display_name="Elder Aldric",
            template_properties={"overview": "Updated mentor bio."},
        )
        brand_new = _make_entity(
            vault_path="vault/world/locations/academy.md",
            display_name="Academy",
            type="location",
        )
        current = _make_manifest(sera_new, aldric_changed, brand_new)
        result = diff_against_previous(current, tmp_path / "prev.json")

        by_path = {e["vault_path"]: e for e in result["entities"]}
        assert by_path["vault/world/characters/sera.md"]["status"] == "unchanged"
        assert by_path["vault/world/characters/sera.md"]["articy_id"] == "0x01"
        assert by_path["vault/world/characters/aldric.md"]["status"] == "updated"
        assert by_path["vault/world/characters/aldric.md"]["articy_id"] == "0x02"
        assert by_path["vault/world/locations/academy.md"]["status"] == "new"


class TestDiffingEndToEnd:
    def test_full_round_trip(self, tmp_vault):
        """Generate manifest, write it, change vault, regenerate, and verify diffing."""
        vault_world = tmp_vault / "vault" / "world"

        first = generate_manifest(vault_world)
        first["entities"][0]["articy_id"] = "0xFIRST"
        prev_path = tmp_vault / "prev.json"
        _write_manifest(prev_path, first)

        second = generate_manifest(vault_world)
        result = diff_against_previous(second, prev_path)

        by_path = {e["vault_path"]: e for e in result["entities"]}
        sera = by_path["vault/world/characters/sera.md"]
        assert sera["status"] == "unchanged"
        assert sera["articy_id"] == "0xFIRST"

    def test_vault_edit_triggers_updated(self, tmp_vault):
        vault_world = tmp_vault / "vault" / "world"

        first = generate_manifest(vault_world)
        first["entities"][0]["articy_id"] = "0xSERA"
        prev_path = tmp_vault / "prev.json"
        _write_manifest(prev_path, first)

        sera_path = vault_world / "characters" / "sera.md"
        text = sera_path.read_text(encoding="utf-8")
        text = text.replace("A young scholar from the Academy of Starlight.", "An experienced mage from the Academy.")
        sera_path.write_text(text, encoding="utf-8")

        second = generate_manifest(vault_world)
        result = diff_against_previous(second, prev_path)
        sera = next(e for e in result["entities"] if "sera" in e["vault_path"])
        assert sera["status"] == "updated"
        assert sera["articy_id"] == "0xSERA"
