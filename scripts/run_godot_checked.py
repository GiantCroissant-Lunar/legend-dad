#!/usr/bin/env python3
from __future__ import annotations

import subprocess
import sys

ERROR_PATTERNS = (
    "SCRIPT ERROR:",
    "Parse Error:",
    "Compile Error:",
    'Failed to load script "',
)


def main() -> int:
    if len(sys.argv) < 2:
        print("usage: run_godot_checked.py <godot command> [args ...]", file=sys.stderr)
        return 2

    process = subprocess.Popen(
        sys.argv[1:],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
    )

    saw_error_pattern = False

    assert process.stdout is not None
    for line in process.stdout:
        sys.stdout.write(line)
        if any(pattern in line for pattern in ERROR_PATTERNS):
            saw_error_pattern = True

    return_code = process.wait()

    if return_code != 0:
        return return_code

    if saw_error_pattern:
        print(
            "run_godot_checked.py: detected Godot script/load errors in output; failing task",
            file=sys.stderr,
        )
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
