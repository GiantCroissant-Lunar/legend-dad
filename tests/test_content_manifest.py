import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from content_manifest import build_manifest

FIXTURES = Path(__file__).resolve().parent / "fixtures" / "manifest"


def test_build_manifest_collects_all_bundle_jsons():
    manifest = build_manifest(
        content_root=FIXTURES / "content",
        pck_dir=FIXTURES / "pck",
    )
    assert manifest["schema_version"] == 1
    assert set(manifest["bundles"].keys()) == {"hud-core", "enemies-forest"}


def test_build_manifest_attaches_pck_filenames():
    manifest = build_manifest(
        content_root=FIXTURES / "content",
        pck_dir=FIXTURES / "pck",
    )
    assert manifest["bundles"]["hud-core"]["pck"] == "hud-core@a3f1b2.pck"
    assert manifest["bundles"]["enemies-forest"]["pck"] == "enemies-forest@c5e0d1.pck"


def test_build_manifest_carries_policy_kind_deps_provides():
    manifest = build_manifest(
        content_root=FIXTURES / "content",
        pck_dir=FIXTURES / "pck",
    )
    hud = manifest["bundles"]["hud-core"]
    assert hud["kind"] == "hud"
    assert hud["policy"] == "eager"
    assert hud["deps"] == []
    assert hud["provides"]["widgets"] == ["activity_log_panel", "minimap"]


def test_build_manifest_skips_bundle_with_no_pck(tmp_path):
    # Bundle declared but never built -> exclude from manifest with a warning.
    content = tmp_path / "content" / "items" / "items-common"
    content.mkdir(parents=True)
    (content / "bundle.json").write_text(
        json.dumps(
            {
                "id": "items-common",
                "kind": "items",
                "policy": "lazy",
                "deps": [],
                "include": ["**/*.tres"],
                "provides": {},
            }
        )
    )
    pck_dir = tmp_path / "pck"
    pck_dir.mkdir()

    manifest = build_manifest(content_root=tmp_path / "content", pck_dir=pck_dir)
    assert "items-common" not in manifest["bundles"]


def test_build_manifest_validates_against_schema():
    schema_path = Path(__file__).resolve().parents[1] / "project" / "shared" / "data" / "content_manifest.schema.json"
    if not schema_path.exists():
        # Schema file lives in repo. If somehow missing, skip.
        return
    import jsonschema

    manifest = build_manifest(
        content_root=FIXTURES / "content",
        pck_dir=FIXTURES / "pck",
    )
    jsonschema.validate(instance=manifest, schema=json.loads(schema_path.read_text()))
