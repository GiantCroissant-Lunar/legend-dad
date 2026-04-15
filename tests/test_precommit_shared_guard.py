# tests/test_precommit_shared_guard.py
import subprocess
import sys
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "precommit_shared_guard.py"


def run(args):
    return subprocess.run(
        [sys.executable, str(SCRIPT), *args],
        capture_output=True,
        text=True,
    )


def test_allows_files_outside_linked_paths():
    result = run(["scripts/foo.py", "vault/notes.md", "project/shared/addons/bar.gd"])
    assert result.returncode == 0, result.stderr


def test_blocks_files_inside_complete_app_linked_dirs():
    cases = [
        "project/hosts/complete-app/addons/something.gd",
        "project/hosts/complete-app/lib/foo.gd",
        "project/hosts/complete-app/shaders/x.gdshader",
        "project/hosts/complete-app/data/locations.json",
    ]
    for path in cases:
        result = run([path])
        assert result.returncode != 0, f"should reject {path}"
        assert "linked from project/shared" in result.stderr


def test_blocks_files_inside_content_app_linked_dirs():
    result = run(["project/hosts/content-app/content/hud/foo.tscn"])
    assert result.returncode != 0
    assert "linked from project/shared" in result.stderr


def test_allows_other_paths_inside_host_projects():
    # scripts/, scenes/, preview/ are NOT linked — they should pass.
    cases = [
        "project/hosts/complete-app/scripts/main.gd",
        "project/hosts/complete-app/scenes/main.tscn",
        "project/hosts/content-app/preview/preview_main.tscn",
        "project/hosts/content-app/scripts/bundle_packager.gd",
    ]
    for path in cases:
        result = run([path])
        assert result.returncode == 0, f"should allow {path}: {result.stderr}"
