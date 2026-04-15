#!/usr/bin/env python3
"""Iterate every bundle.json under project/shared/content/ and run task content:build."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


def main() -> int:
    repo_root = Path(__file__).resolve().parents[1]
    content_root = repo_root / "project" / "shared" / "content"
    failures: list[str] = []
    for bundle_json in sorted(content_root.rglob("bundle.json")):
        with bundle_json.open() as f:
            meta = json.load(f)
        bundle_id = meta.get("id")
        if not bundle_id:
            print(f"skip: {bundle_json} has no 'id'", file=sys.stderr)
            continue
        print(f"building bundle: {bundle_id}")
        rc = subprocess.run(
            ["task", "content:build", "--", bundle_id],
            cwd=repo_root,
        ).returncode
        if rc != 0:
            failures.append(bundle_id)
    if failures:
        print(f"FAILED: {failures}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
