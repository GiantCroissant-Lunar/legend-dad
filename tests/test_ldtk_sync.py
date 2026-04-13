"""Tests for LDtk project sync script."""

import json

from scripts.ldtk_sync import (
    LDTK_JSON_VERSION,
    TYPE_TO_ENTITY,
    UidAllocator,
    generate_ldtk_project,
    merge_ldtk_project,
)


def _make_manifest(*entity_types):
    entities = []
    for t in entity_types:
        entities.append({
            "vault_path": f"vault/world/{t}s/test.md",
            "articy_id": "",
            "type": t,
            "status": "new",
            "display_name": f"Test {t.title()}",
            "template_properties": {},
            "connections": [],
            "creative_prompts": {},
            "dialogue_hooks": [],
            "flow_notes": "",
        })
    return {
        "version": "0.1.0",
        "generated": "2026-04-13T00:00:00+00:00",
        "generated_by": "vault_to_manifest",
        "entities": entities,
    }


class TestUidAllocator:
    def test_sequential_ids(self):
        uid = UidAllocator(1)
        assert uid.next() == 1
        assert uid.next() == 2
        assert uid.next() == 3

    def test_next_uid_property(self):
        uid = UidAllocator(10)
        uid.next()
        uid.next()
        assert uid.next_uid == 12


class TestGenerateLdtkProject:
    def test_json_version(self):
        project = generate_ldtk_project(_make_manifest("character"))
        assert project["jsonVersion"] == LDTK_JSON_VERSION

    def test_has_all_entity_defs(self):
        project = generate_ldtk_project(_make_manifest("character"))
        identifiers = {e["identifier"] for e in project["defs"]["entities"]}
        assert identifiers == set(TYPE_TO_ENTITY.values())

    def test_entity_defs_have_fields(self):
        project = generate_ldtk_project(_make_manifest("character"))
        for entity_def in project["defs"]["entities"]:
            field_names = {f["identifier"] for f in entity_def["fieldDefs"]}
            assert "display_name" in field_names
            assert "vault_path" in field_names
            assert "era" in field_names
            assert "articy_id" in field_names

    def test_entity_defs_have_unique_uids(self):
        project = generate_ldtk_project(_make_manifest("character"))
        uids = [e["uid"] for e in project["defs"]["entities"]]
        assert len(uids) == len(set(uids))

    def test_field_defs_have_unique_uids(self):
        project = generate_ldtk_project(_make_manifest("character"))
        all_field_uids = []
        for entity_def in project["defs"]["entities"]:
            for field_def in entity_def["fieldDefs"]:
                all_field_uids.append(field_def["uid"])
        assert len(all_field_uids) == len(set(all_field_uids))

    def test_enums_created(self):
        project = generate_ldtk_project(_make_manifest("character"))
        enum_names = {e["identifier"] for e in project["defs"]["enums"]}
        assert "EntityType" in enum_names
        assert "Era" in enum_names

    def test_era_enum_values(self):
        project = generate_ldtk_project(_make_manifest("character"))
        era_enum = next(e for e in project["defs"]["enums"] if e["identifier"] == "Era")
        values = {v["id"] for v in era_enum["values"]}
        assert values == {"Father", "Son", "Both"}

    def test_entity_type_enum_has_all_types(self):
        project = generate_ldtk_project(_make_manifest("character"))
        et_enum = next(e for e in project["defs"]["enums"] if e["identifier"] == "EntityType")
        values = {v["id"] for v in et_enum["values"]}
        assert values == set(TYPE_TO_ENTITY.values())

    def test_layers_created(self):
        project = generate_ldtk_project(_make_manifest("character"))
        layer_names = [l["identifier"] for l in project["defs"]["layers"]]
        assert "Entities" in layer_names
        assert "Collision" in layer_names
        assert "Terrain" in layer_names

    def test_collision_layer_has_intgrid_values(self):
        project = generate_ldtk_project(_make_manifest("character"))
        collision = next(l for l in project["defs"]["layers"] if l["identifier"] == "Collision")
        assert collision["type"] == "IntGrid"
        value_ids = {v["identifier"] for v in collision["intGridValues"]}
        assert "solid" in value_ids
        assert "water" in value_ids

    def test_entities_layer_type(self):
        project = generate_ldtk_project(_make_manifest("character"))
        entities_layer = next(l for l in project["defs"]["layers"] if l["identifier"] == "Entities")
        assert entities_layer["type"] == "Entities"

    def test_has_default_level(self):
        project = generate_ldtk_project(_make_manifest("character"))
        assert len(project["levels"]) == 1
        assert project["levels"][0]["identifier"] == "Level_0"
        assert project["levels"][0]["worldDepth"] == 0

    def test_next_uid_is_correct(self):
        project = generate_ldtk_project(_make_manifest("character"))
        all_uids = []
        for e in project["defs"]["entities"]:
            all_uids.append(e["uid"])
            for f in e["fieldDefs"]:
                all_uids.append(f["uid"])
        for l in project["defs"]["layers"]:
            all_uids.append(l["uid"])
        for en in project["defs"]["enums"]:
            all_uids.append(en["uid"])
        assert project["nextUid"] > max(all_uids)

    def test_grid_size(self):
        project = generate_ldtk_project(_make_manifest("character"))
        assert project["defaultGridSize"] == 16


class TestMergeLdtkProject:
    def test_preserves_levels(self):
        existing = generate_ldtk_project(_make_manifest("character"))
        existing["levels"] = [{"identifier": "TestLevel", "uid": 999}]

        new_defs = generate_ldtk_project(_make_manifest("character", "location"))
        merged = merge_ldtk_project(existing, new_defs)

        assert len(merged["levels"]) == 1
        assert merged["levels"][0]["identifier"] == "TestLevel"

    def test_updates_entity_defs(self):
        existing = generate_ldtk_project(_make_manifest("character"))
        new_defs = generate_ldtk_project(_make_manifest("character"))
        merged = merge_ldtk_project(existing, new_defs)

        assert len(merged["defs"]["entities"]) == len(new_defs["defs"]["entities"])

    def test_updates_next_uid(self):
        existing = generate_ldtk_project(_make_manifest("character"))
        existing["nextUid"] = 1  # artificially low
        new_defs = generate_ldtk_project(_make_manifest("character"))
        merged = merge_ldtk_project(existing, new_defs)

        assert merged["nextUid"] == new_defs["nextUid"]


class TestEndToEnd:
    def test_generate_and_roundtrip(self, tmp_path):
        manifest = _make_manifest("character", "location", "item")
        project = generate_ldtk_project(manifest)

        out_path = tmp_path / "test.ldtk"
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(project, f)

        with open(out_path, encoding="utf-8") as f:
            loaded = json.load(f)

        assert loaded["jsonVersion"] == LDTK_JSON_VERSION
        assert len(loaded["defs"]["entities"]) == 8
        assert len(loaded["defs"]["enums"]) == 2
