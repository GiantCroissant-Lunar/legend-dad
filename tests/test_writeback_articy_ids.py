"""Tests for writeback_articy_ids.py."""

import json

from scripts.writeback_articy_ids import patch_frontmatter_articy_id, writeback_ids


class TestPatchFrontmatter:
    def test_replaces_empty_articy_id(self):
        text = '---\ntype: character\narticy-id: ""\ntags: []\n---\n\n# Sera\n'
        result = patch_frontmatter_articy_id(text, "0x01000001")
        assert 'articy-id: "0x01000001"' in result

    def test_replaces_existing_articy_id(self):
        text = '---\ntype: character\narticy-id: "0xOLD"\ntags: []\n---\n\n# Sera\n'
        result = patch_frontmatter_articy_id(text, "0xNEW")
        assert 'articy-id: "0xNEW"' in result
        assert "0xOLD" not in result

    def test_preserves_other_frontmatter(self):
        text = '---\ntype: character\nstatus: draft\narticy-id: ""\ntags: [protagonist]\nera: "Age of Starlight"\n---\n\n# Sera\n'
        result = patch_frontmatter_articy_id(text, "0xABC")
        assert "type: character" in result
        assert "status: draft" in result
        assert "tags: [protagonist]" in result
        assert 'era: "Age of Starlight"' in result
        assert 'articy-id: "0xABC"' in result

    def test_preserves_content_after_frontmatter(self):
        text = '---\ntype: character\narticy-id: ""\n---\n\n# Sera\n\n## Overview\n\nA young scholar.\n'
        result = patch_frontmatter_articy_id(text, "0x123")
        assert "## Overview" in result
        assert "A young scholar." in result

    def test_no_frontmatter_returns_unchanged(self):
        text = "# Sera\n\nNo frontmatter here.\n"
        result = patch_frontmatter_articy_id(text, "0x123")
        assert result == text


class TestWritebackIds:
    def _make_vault_page(self, vault_dir, rel_path, articy_id=""):
        page_path = vault_dir / rel_path
        page_path.parent.mkdir(parents=True, exist_ok=True)
        page_path.write_text(
            f'---\ntype: character\nstatus: draft\narticy-id: "{articy_id}"\ntags: []\nconnections: []\nera: ""\nlast-agent-pass: "2026-04-12"\n---\n\n# Test\n',
            encoding="utf-8",
        )
        return page_path

    def _make_manifest(self, tmp_path, entities):
        manifest = {
            "version": "0.1.0",
            "generated": "2026-04-12T00:00:00+00:00",
            "generated_by": "vault_to_manifest",
            "entities": entities,
        }
        # Put manifest at project/articy/import-manifest.json
        manifest_dir = tmp_path / "project" / "articy"
        manifest_dir.mkdir(parents=True, exist_ok=True)
        manifest_path = manifest_dir / "import-manifest.json"
        with open(manifest_path, "w", encoding="utf-8") as f:
            json.dump(manifest, f)
        return manifest_path

    def test_writes_articy_id_to_vault_page(self, tmp_path):
        self._make_vault_page(tmp_path, "vault/world/characters/sera.md")
        manifest_path = self._make_manifest(tmp_path, [
            {
                "vault_path": "vault/world/characters/sera.md",
                "articy_id": "0x01000001",
                "type": "character",
                "status": "new",
                "display_name": "Sera",
                "template_properties": {},
                "connections": [],
                "creative_prompts": {},
            }
        ])

        updated = writeback_ids(manifest_path, vault_root=tmp_path)
        assert len(updated) == 1

        text = (tmp_path / "vault/world/characters/sera.md").read_text(encoding="utf-8")
        assert 'articy-id: "0x01000001"' in text

    def test_skips_already_matching_id(self, tmp_path):
        self._make_vault_page(tmp_path, "vault/world/characters/sera.md", articy_id="0x01000001")
        manifest_path = self._make_manifest(tmp_path, [
            {
                "vault_path": "vault/world/characters/sera.md",
                "articy_id": "0x01000001",
                "type": "character",
                "status": "unchanged",
                "display_name": "Sera",
                "template_properties": {},
                "connections": [],
                "creative_prompts": {},
            }
        ])

        updated = writeback_ids(manifest_path, vault_root=tmp_path)
        assert len(updated) == 0

    def test_skips_empty_articy_id(self, tmp_path):
        self._make_vault_page(tmp_path, "vault/world/characters/sera.md")
        manifest_path = self._make_manifest(tmp_path, [
            {
                "vault_path": "vault/world/characters/sera.md",
                "articy_id": "",
                "type": "character",
                "status": "new",
                "display_name": "Sera",
                "template_properties": {},
                "connections": [],
                "creative_prompts": {},
            }
        ])

        updated = writeback_ids(manifest_path, vault_root=tmp_path)
        assert len(updated) == 0

    def test_warns_on_missing_vault_page(self, tmp_path, capsys):
        manifest_path = self._make_manifest(tmp_path, [
            {
                "vault_path": "vault/world/characters/nonexistent.md",
                "articy_id": "0x123",
                "type": "character",
                "status": "new",
                "display_name": "Ghost",
                "template_properties": {},
                "connections": [],
                "creative_prompts": {},
            }
        ])

        updated = writeback_ids(manifest_path, vault_root=tmp_path)
        assert len(updated) == 0
        assert "not found" in capsys.readouterr().err

    def test_multiple_entities(self, tmp_path):
        self._make_vault_page(tmp_path, "vault/world/characters/sera.md")
        self._make_vault_page(tmp_path, "vault/world/locations/academy.md")
        manifest_path = self._make_manifest(tmp_path, [
            {
                "vault_path": "vault/world/characters/sera.md",
                "articy_id": "0x01",
                "type": "character",
                "status": "new",
                "display_name": "Sera",
                "template_properties": {},
                "connections": [],
                "creative_prompts": {},
            },
            {
                "vault_path": "vault/world/locations/academy.md",
                "articy_id": "0x02",
                "type": "location",
                "status": "new",
                "display_name": "Academy",
                "template_properties": {},
                "connections": [],
                "creative_prompts": {},
            },
        ])

        updated = writeback_ids(manifest_path, vault_root=tmp_path)
        assert len(updated) == 2
