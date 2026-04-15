#!/usr/bin/env python3
"""Mirror `.agent/skills/{NN-category}/{skill}/` into `.claude/skills/{skill}/`.

`.agent/skills/` is the source of truth for legend-dad agent skills,
organized by numbered category (00-meta, 01-godot, 03-presentation, ...).
Claude Code discovers skills from `.claude/skills/{name}/SKILL.md` (flat),
so we mirror each skill dir to the flat runtime location.

Cross-platform (matches setup_shared_links.py):
- macOS/Linux: relative POSIX symlinks
- Windows: directory junctions via `mklink /J` (no admin/dev-mode needed)

Idempotent — safe to re-run. Removes stale links that no longer match a
source skill. Skip-lists a skill if its source dir is missing a SKILL.md.
"""

from __future__ import annotations

import os
import re
import subprocess
import sys
from pathlib import Path

IS_WINDOWS = sys.platform.startswith("win")

# Numbered category dirs we treat as skill containers. Anything else in
# `.agent/skills/` is ignored (e.g., INDEX.md).
CATEGORY_PATTERN = re.compile(r"^\d{2}-[a-z][a-z0-9-]*$")


def discover_source_skills(agent_skills_root: Path) -> list[tuple[str, Path]]:
    """Walk `.agent/skills/{NN-category}/{skill}/` and collect (name, path) pairs.

    A directory is a skill iff it contains SKILL.md.
    """
    skills: list[tuple[str, Path]] = []
    for category in sorted(agent_skills_root.iterdir()):
        if not category.is_dir():
            continue
        if not CATEGORY_PATTERN.match(category.name):
            continue
        for skill in sorted(category.iterdir()):
            if not skill.is_dir():
                continue
            if not (skill / "SKILL.md").is_file():
                continue
            skills.append((skill.name, skill.resolve()))
    return skills


def remove_link(link_path: Path) -> None:
    """Remove a link/junction/file without touching the target."""
    if not os.path.lexists(str(link_path)):
        return
    if link_path.is_symlink() or link_path.is_file():
        link_path.unlink()
    else:
        # Directory or Windows junction (is_symlink()=False, is_dir()=True).
        try:
            link_path.rmdir()
        except OSError as exc:
            # Non-empty real directory — refuse to clobber.
            raise SystemExit(f"Refusing to replace non-empty directory: {link_path}") from exc


def create_link(link_path: Path, target_dir: Path) -> None:
    """Link link_path -> target_dir. Replaces any existing entry."""
    remove_link(link_path)
    if IS_WINDOWS:
        result = subprocess.run(
            ["cmd", "/c", "mklink", "/J", str(link_path), str(target_dir)],
            check=False,
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            raise SystemExit(f"mklink /J failed for {link_path} -> {target_dir}: {result.stderr.strip()}")
    else:
        rel_target = os.path.relpath(target_dir, link_path.parent)
        link_path.symlink_to(rel_target, target_is_directory=True)


def prune_orphans(claude_skills_root: Path, valid_names: set[str]) -> list[str]:
    """Remove any link in claude_skills_root not in valid_names. Returns removed names."""
    if not claude_skills_root.is_dir():
        return []
    removed: list[str] = []
    for entry in claude_skills_root.iterdir():
        if entry.name in valid_names:
            continue
        # Only prune things we would have created: symlinks/junctions (not real dirs).
        if entry.is_symlink() or (IS_WINDOWS and entry.is_dir() and not any(entry.iterdir())):
            remove_link(entry)
            removed.append(entry.name)
        elif entry.is_dir():
            # Real directory we didn't create — leave it alone.
            continue
        else:
            remove_link(entry)
            removed.append(entry.name)
    return removed


def main() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    agent_skills = repo_root / ".agent" / "skills"
    claude_skills = repo_root / ".claude" / "skills"

    if not agent_skills.is_dir():
        raise SystemExit(f"Missing source skill dir: {agent_skills}")

    skills = discover_source_skills(agent_skills)
    if not skills:
        print(f"No skills found under {agent_skills}/**/SKILL.md")
        return

    # Detect name collisions across categories — we go flat in .claude/skills/.
    seen: dict[str, Path] = {}
    for name, src in skills:
        if name in seen:
            raise SystemExit(
                f"Duplicate skill name '{name}' in categories:\n  {seen[name]}\n  {src}\n"
                "Rename one — .claude/skills/ is flat."
            )
        seen[name] = src

    claude_skills.mkdir(parents=True, exist_ok=True)

    for name, src in skills:
        create_link(claude_skills / name, src)

    removed = prune_orphans(claude_skills, {name for name, _ in skills})

    print(f"Synced {len(skills)} skill(s) into {claude_skills.relative_to(repo_root)}/:")
    for name, src in skills:
        rel_src = src.relative_to(repo_root)
        print(f"  {name}  ->  {rel_src}")
    if removed:
        print(f"Removed {len(removed)} stale link(s): {', '.join(removed)}")


if __name__ == "__main__":
    main()
