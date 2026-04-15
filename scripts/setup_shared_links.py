#!/usr/bin/env python3
"""Create cross-platform links from each Godot host project to project/shared/.

On macOS/Linux: relative POSIX symlinks.
On Windows: directory junctions via `mklink /J` (no admin/dev-mode required).
"""

from __future__ import annotations

import os
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

IS_WINDOWS = sys.platform.startswith("win")


@dataclass(frozen=True)
class LinkEntry:
    host: str  # "complete-app" or "content-app"
    name: str  # link name under the host project (e.g., "addons")
    target: str  # path under shared/ (e.g., "addons")


# The complete (thin runtime) project never links shared/content/ — that's
# authoring territory and importing the same source from two projects causes
# .import file conflicts.
LINKS: tuple[LinkEntry, ...] = (
    LinkEntry("complete-app", "addons", "addons"),
    LinkEntry("complete-app", "lib", "lib"),
    LinkEntry("complete-app", "shaders", "shaders"),
    LinkEntry("complete-app", "data", "data"),
    LinkEntry("content-app", "addons", "addons"),
    LinkEntry("content-app", "lib", "lib"),
    LinkEntry("content-app", "shaders", "shaders"),
    LinkEntry("content-app", "data", "data"),
    LinkEntry("content-app", "content", "content"),
)


def create_link(host_dir: Path, name: str, target_dir: Path) -> None:
    """Create or refresh a single link from host_dir/name to target_dir."""
    target_dir = target_dir.resolve()
    link_path = host_dir / name
    # Remove any stale entry (link, junction, or directory) without touching the target.
    # os.path.lexists does NOT follow links, so it returns True for broken symlinks
    # AND stale Windows junctions (where is_symlink()/exists() both return False).
    if os.path.lexists(str(link_path)):
        if link_path.is_symlink() or link_path.is_file():
            link_path.unlink()
        else:
            # Directory or junction. On Windows, junctions are reported as dirs
            # by Path.is_dir(); rmdir works for both empty dirs and junctions.
            # A stale junction has is_symlink()=False and is_file()=False, so it
            # lands here — rmdir removes the junction entry without touching target.
            try:
                link_path.rmdir()
            except OSError:
                # Non-empty real directory — refuse to clobber user content.
                raise SystemExit(f"Refusing to replace non-empty directory: {link_path}") from None

    if IS_WINDOWS:
        # mklink /J creates a directory junction and does NOT require admin.
        result = subprocess.run(
            ["cmd", "/c", "mklink", "/J", str(link_path), str(target_dir)],
            check=False,
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            raise SystemExit(f"mklink /J failed for {link_path} -> {target_dir}: {result.stderr.strip()}") from None
    else:
        rel_target = os.path.relpath(target_dir, link_path.parent)
        link_path.symlink_to(rel_target, target_is_directory=True)


def ensure_all_links(project_root: Path) -> None:
    """Create every entry in LINKS, idempotently."""
    shared = project_root / "shared"
    if not shared.is_dir():
        raise SystemExit(f"Expected shared dir at {shared}")
    for entry in LINKS:
        host_dir = project_root / "hosts" / entry.host
        target_dir = (shared / entry.target).resolve()
        if not host_dir.is_dir():
            raise SystemExit(f"Host project missing: {host_dir}")
        if not target_dir.is_dir():
            raise SystemExit(f"Shared target missing: {target_dir}")
        create_link(host_dir, entry.name, target_dir)


def main() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    project_root = repo_root / "project"
    ensure_all_links(project_root)
    print(f"Linked {len(LINKS)} entries under {project_root}/hosts/")


if __name__ == "__main__":
    main()
