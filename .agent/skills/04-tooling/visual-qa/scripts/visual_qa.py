#!/usr/bin/env python3
"""Visual QA — analyze game screenshots via Claude vision.

Three modes:
  Static:   visual_qa.py [--context "..."] reference.png screenshot.png
  Dynamic:  visual_qa.py [--context "..."] reference.png frame1.png frame2.png ...
  Question: visual_qa.py --question "what's wrong?" screenshot.png [frame2.png ...]

Static mode (2 images): reference + single game screenshot. For static scenes.
Dynamic mode (3+ images): reference + frame sequence at 2 FPS cadence. For motion.
Question mode: free-form question + any number of screenshots. No reference needed.

--context: Task context (Goal, Requirements, Verify) for goal verification.
--question: Free-form question about the screenshots (replaces reference-based modes).
--model: Override model (default: claude-haiku-4-5-20251001).
--log: Path to JSONL log file for debug logging.

Requires: ANTHROPIC_API_KEY.

Ported from godogen's Gemini-backed script for legend-dad. See:
  vault/specs/2026-04-15-visual-qa-skill-backend.md
  vault/specs/2026-04-15-visual-qa-vs-existing-verification.md
"""

import base64
import json
import os
import sys
from datetime import UTC, datetime
from pathlib import Path

import anthropic

PROMPTS_DIR = Path(__file__).parent
STATIC_PROMPT = PROMPTS_DIR / "static_prompt.md"
DYNAMIC_PROMPT = PROMPTS_DIR / "dynamic_prompt.md"
QUESTION_PROMPT = PROMPTS_DIR / "question_prompt.md"

# Haiku 4.5 — strong-enough vision for 2D HUD/sprite QA at a cost low enough
# to stay inside an iteration loop. Override with --model when a harder call
# warrants Sonnet (e.g. motion/ambiguous dynamic-mode frames).
DEFAULT_MODEL = "claude-haiku-4-5-20251001"
# Generous enough for a ~20-issue report; reports longer than this usually
# mean the input is fractally broken and human review is needed anyway.
MAX_TOKENS = 4096


def log_entry(log_path, *, mode, model, query, files, output):
    """Append a JSONL log entry."""
    entry = {
        "ts": datetime.now(UTC).isoformat(),
        "mode": mode,
        "model": model,
        "query": query,
        "files": files,
        "output": output,
    }
    with open(log_path, "a") as f:
        f.write(json.dumps(entry) + "\n")


def _image_block(path: Path) -> dict:
    data = base64.standard_b64encode(path.read_bytes()).decode("ascii")
    # Infer media type from suffix; default to png for anything unexpected.
    suffix = path.suffix.lower()
    media_type = {
        ".png": "image/png",
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".webp": "image/webp",
        ".gif": "image/gif",
    }.get(suffix, "image/png")
    return {
        "type": "image",
        "source": {"type": "base64", "media_type": media_type, "data": data},
    }


def _text_block(text: str) -> dict:
    return {"type": "text", "text": text}


def main():
    args = sys.argv[1:]
    context = None
    question = None
    model = DEFAULT_MODEL
    log_path = None

    # Parse named flags
    while len(args) >= 2:
        if args[0] == "--context":
            context = args[1]
            args = args[2:]
        elif args[0] == "--question":
            question = args[1]
            args = args[2:]
        elif args[0] == "--model":
            model = args[1]
            args = args[2:]
        elif args[0] == "--log":
            log_path = args[1]
            args = args[2:]
        else:
            break

    if question:
        # Question mode: just screenshots, no reference
        if len(args) < 1:
            print(
                f'Usage: {sys.argv[0]} --question "..." <screenshot.png> [frame2.png ...]',
                file=sys.stderr,
            )
            sys.exit(1)
        paths = [Path(p) for p in args]
        for p in paths:
            if not p.exists():
                print(f"Error: {p} not found", file=sys.stderr)
                sys.exit(1)

        prompt = QUESTION_PROMPT.read_text()
        prompt += f"\n\n## Question\n\n{question}\n"
        if context:
            prompt += f"\n## Additional Context\n\n{context}\n"

        content: list[dict] = [_text_block(prompt)]
        for i, p in enumerate(paths, 1):
            label = "Screenshot:" if len(paths) == 1 else f"Frame {i}:"
            content.append(_text_block(label))
            content.append(_image_block(p))

        mode = "question"
        query = question
        desc = f"question ({len(paths)} image{'s' if len(paths) != 1 else ''})"
    else:
        # Reference-based modes (static/dynamic)
        if len(args) < 2:
            print(
                f'Usage: {sys.argv[0]} [--context "..."] <reference.png> <screenshot.png> [frame2.png ...]',
                file=sys.stderr,
            )
            print(
                f'       {sys.argv[0]} --question "..." <screenshot.png> [frame2.png ...]',
                file=sys.stderr,
            )
            sys.exit(1)

        paths = [Path(p) for p in args]
        for p in paths:
            if not p.exists():
                print(f"Error: {p} not found", file=sys.stderr)
                sys.exit(1)

        static = len(paths) == 2
        prompt = (STATIC_PROMPT if static else DYNAMIC_PROMPT).read_text()
        if context:
            prompt += f"\n\n## Task Context\n\n{context}\n"

        content = [_text_block(prompt), _text_block("Reference (visual target):"), _image_block(paths[0])]

        if static:
            content.append(_text_block("Game screenshot:"))
            content.append(_image_block(paths[1]))
            mode = "static"
            desc = "static (reference + screenshot)"
        else:
            for i, p in enumerate(paths[1:], 1):
                content.append(_text_block(f"Frame {i}:"))
                content.append(_image_block(p))
            mode = "dynamic"
            desc = f"dynamic (reference + {len(paths) - 1} frames)"

        query = context or ""

    if not (os.environ.get("ANTHROPIC_API_KEY") or os.environ.get("ANTHROPIC_AUTH_TOKEN")):
        print(
            "Error: ANTHROPIC_API_KEY not set. Either export it, or use the `--native`"
            " path from SKILL.md (which reads images via the Claude harness and skips"
            " this script entirely).",
            file=sys.stderr,
        )
        sys.exit(2)

    print(f"Analyzing {desc} with {model}...", file=sys.stderr)

    client = anthropic.Anthropic()
    try:
        response = client.messages.create(
            model=model,
            max_tokens=MAX_TOKENS,
            messages=[{"role": "user", "content": content}],
        )
    except anthropic.APIError as e:
        print(f"Error: Claude API call failed: {e}", file=sys.stderr)
        sys.exit(1)

    # Concatenate text blocks — Claude responses are usually single-block
    # but the API returns a list for extensibility.
    text_parts = [block.text for block in response.content if block.type == "text"]
    output = "".join(text_parts)
    if not output.strip():
        print("Error: Claude returned no text", file=sys.stderr)
        sys.exit(1)

    print(output)

    if log_path:
        log_entry(
            log_path,
            mode=mode,
            model=model,
            query=query,
            files=[str(p) for p in paths],
            output=output,
        )


if __name__ == "__main__":
    main()
