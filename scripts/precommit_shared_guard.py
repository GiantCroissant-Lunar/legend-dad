#!/usr/bin/env python3
"""Reject staged files inside paths that are symlinks/junctions to project/shared.

Editing through a link causes the change to land in shared/ silently, which makes
review confusing. Force authors to edit shared/ directly.
"""

from __future__ import annotations

import sys

# Per-host blocked link names. Must match LINKS in scripts/setup_shared_links.py.
BLOCKED = {
    "complete-app": ("addons", "lib", "shaders", "data"),
    "content-app": ("addons", "lib", "shaders", "data", "content"),
}


def is_blocked(path: str) -> bool:
    # git / pre-commit normalise paths to forward slashes and never include
    # leading "./" — but normalise defensively so direct callers (CI scripts,
    # ad-hoc invocations) get the same answer.
    normalized = path.replace("\\", "/").lstrip("./")
    parts = normalized.split("/")
    # Need at least: project / hosts / {host} / {linked-sub} / {filename}
    if len(parts) < 5:
        return False
    if parts[0] != "project" or parts[1] != "hosts":
        return False
    host = parts[2]
    sub = parts[3]
    return sub in BLOCKED.get(host, ())


def main(args: list[str]) -> int:
    blocked = [p for p in args if is_blocked(p)]
    if blocked:
        print(
            "ERROR: refusing to commit files inside paths that are linked from "
            "project/shared. Edit the file under project/shared/ instead.",
            file=sys.stderr,
        )
        for p in blocked:
            print(f"  {p}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
