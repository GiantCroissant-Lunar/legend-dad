#!/usr/bin/env python3
"""Generate project/shared/data/content_manifest.json from per-bundle bundle.json files.

Walks shared/content/{kind}/{bundle-id}/bundle.json, looks for matching
{bundle-id}@{hash}.pck in build/_artifacts/pck/, and writes a single manifest.
Bundles without a built PCK are skipped (with a warning) so the runtime never
references missing files.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

PCK_RE = re.compile(r"^([a-z0-9-]+)@([0-9a-f]+)\.pck$")


def _find_pck(pck_dir: Path, bundle_id: str) -> str | None:
    """Return the filename of the most recent PCK for this bundle, or None."""
    candidates = []
    for p in pck_dir.glob(f"{bundle_id}@*.pck"):
        m = PCK_RE.match(p.name)
        if m and m.group(1) == bundle_id:
            candidates.append(p)
    if not candidates:
        return None
    # Newest by mtime wins (deterministic when only one exists).
    candidates.sort(key=lambda p: p.stat().st_mtime)
    return candidates[-1].name


def _load_bundle_jsons(content_root: Path) -> list[dict]:
    bundles = []
    for bundle_json in content_root.rglob("bundle.json"):
        with bundle_json.open() as f:
            data = json.load(f)
        if "id" not in data:
            print(f"WARNING: skipping {bundle_json} (missing 'id')", file=sys.stderr)
            continue
        bundles.append(data)
    return bundles


def build_manifest(content_root: Path, pck_dir: Path) -> dict:
    out = {"schema_version": 1, "bundles": {}}
    for b in _load_bundle_jsons(content_root):
        bundle_id = b["id"]
        pck_name = _find_pck(pck_dir, bundle_id)
        if pck_name is None:
            print(
                f"WARNING: no PCK found for bundle '{bundle_id}' — skipping in manifest",
                file=sys.stderr,
            )
            continue
        m = PCK_RE.match(pck_name)
        content_hash = m.group(2) if m else ""
        entry = {
            "kind": b["kind"],
            "policy": b["policy"],
            "pck": pck_name,
            "deps": list(b.get("deps", [])),
        }
        if "provides" in b:
            entry["provides"] = dict(b["provides"])
        if content_hash:
            entry["content_hash"] = content_hash
        out["bundles"][bundle_id] = entry
    return out


def main() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    content_root = repo_root / "project" / "shared" / "content"
    pck_dir = repo_root / "build" / "_artifacts" / "pck"
    out_path = repo_root / "project" / "shared" / "data" / "content_manifest.json"

    pck_dir.mkdir(parents=True, exist_ok=True)
    manifest = build_manifest(content_root=content_root, pck_dir=pck_dir)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(manifest, indent=2) + "\n")
    print(f"Wrote {out_path} ({len(manifest['bundles'])} bundles)")


if __name__ == "__main__":
    main()
