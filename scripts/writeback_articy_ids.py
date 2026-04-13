"""Write articy IDs from an updated import manifest back to vault page frontmatter."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path


def patch_frontmatter_articy_id(text: str, articy_id: str) -> str:
    """Replace the articy-id value in YAML frontmatter, preserving everything else."""
    # Match the articy-id line in frontmatter (between --- delimiters)
    pattern = r"(^---\n.*?)(articy-id:\s*)(\"[^\"]*\"|'[^']*'|\S*)(.*?^---)"
    match = re.search(pattern, text, re.MULTILINE | re.DOTALL)
    if not match:
        return text

    before = match.group(1)
    key = match.group(2)
    after = match.group(4)

    return text[: match.start()] + before + key + f'"{articy_id}"' + after + text[match.end() :]


def writeback_ids(manifest_path: Path, vault_root: Path | None = None) -> list[str]:
    """Read manifest and patch vault pages with articy IDs.

    Returns list of updated file paths.
    """
    with open(manifest_path, encoding="utf-8") as f:
        manifest = json.load(f)

    # Determine vault root: if not given, infer from manifest paths
    # Manifest vault_path values are like "vault/world/characters/sera.md"
    # relative to the project root (manifest_path's grandparent typically)
    if vault_root is None:
        vault_root = manifest_path.parent.parent.parent  # project/articy/import-manifest.json -> project root

    updated = []
    for entity in manifest.get("entities", []):
        articy_id = entity.get("articy_id", "")
        vault_path = entity.get("vault_path", "")
        if not articy_id or not vault_path:
            continue

        page_path = vault_root / vault_path
        if not page_path.exists():
            print(f"Warning: vault page not found: {page_path}", file=sys.stderr)
            continue

        text = page_path.read_text(encoding="utf-8")

        # Check if articy-id already matches
        current_match = re.search(r'articy-id:\s*"([^"]*)"', text)
        if current_match and current_match.group(1) == articy_id:
            continue  # Already up to date

        patched = patch_frontmatter_articy_id(text, articy_id)
        if patched != text:
            page_path.write_text(patched, encoding="utf-8")
            updated.append(str(vault_path))
            print(f"Updated: {vault_path} -> articy_id: {articy_id}")

    return updated


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Write articy IDs from manifest back to vault frontmatter")
    parser.add_argument("manifest", type=Path, help="Path to import-manifest.json")
    parser.add_argument("--vault-root", type=Path, help="Project root directory (default: inferred from manifest path)")
    args = parser.parse_args(argv)

    if not args.manifest.exists():
        print(f"Error: manifest not found: {args.manifest}", file=sys.stderr)
        return 1

    updated = writeback_ids(args.manifest, args.vault_root)
    print(f"Wrote articy IDs to {len(updated)} vault pages.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
