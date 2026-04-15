import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from setup_shared_links import LINKS, create_link, ensure_all_links


def test_link_table_covers_expected_targets():
    # Sanity: complete-app gets these (NOT content), content-app gets all + content
    complete = {entry for entry in LINKS if entry.host == "complete-app"}
    content = {entry for entry in LINKS if entry.host == "content-app"}
    complete_names = {entry.name for entry in complete}
    content_names = {entry.name for entry in content}
    assert complete_names == {"addons", "lib", "shaders", "data"}
    assert content_names == {"addons", "lib", "shaders", "data", "content"}


def test_create_link_makes_pointer_to_target(tmp_path):
    target = tmp_path / "shared" / "addons"
    target.mkdir(parents=True)
    (target / "marker.txt").write_text("hello")
    host = tmp_path / "hosts" / "complete-app"
    host.mkdir(parents=True)

    create_link(host, "addons", target)

    link = host / "addons"
    assert link.exists()
    # Reading through the link must see the file in the target
    assert (link / "marker.txt").read_text() == "hello"


def test_create_link_is_idempotent(tmp_path):
    target = tmp_path / "shared" / "addons"
    target.mkdir(parents=True)
    host = tmp_path / "hosts" / "complete-app"
    host.mkdir(parents=True)

    create_link(host, "addons", target)
    create_link(host, "addons", target)  # second call must not raise

    assert (host / "addons").exists()


def test_create_link_replaces_stale_link(tmp_path):
    old_target = tmp_path / "shared" / "old"
    new_target = tmp_path / "shared" / "new"
    old_target.mkdir(parents=True)
    new_target.mkdir(parents=True)
    (old_target / "old.txt").write_text("stale")
    (new_target / "new.txt").write_text("fresh")
    host = tmp_path / "hosts" / "complete-app"
    host.mkdir(parents=True)

    create_link(host, "addons", old_target)
    create_link(host, "addons", new_target)

    assert (host / "addons" / "new.txt").exists()
    assert not (host / "addons" / "old.txt").exists()


def test_ensure_all_links_creates_all_entries(tmp_path):
    project = tmp_path / "project"
    shared = project / "shared"
    for sub in ("addons", "lib", "shaders", "data", "content"):
        (shared / sub).mkdir(parents=True)
    (project / "hosts" / "complete-app").mkdir(parents=True)
    (project / "hosts" / "content-app").mkdir(parents=True)

    ensure_all_links(project)

    for entry in LINKS:
        assert (project / "hosts" / entry.host / entry.name).exists(), entry
