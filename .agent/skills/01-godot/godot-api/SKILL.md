---
name: godot-api
description: Look up Godot 4.6.2 engine class APIs — methods, properties, signals, enums. Use when you need to find which class to use, verify a method signature, or look up specific API details for GDScript.
category: 01-godot
layer: engine
context: fork
model: sonnet
agent: Explore
related_skills:
  - "@context-discovery"
---

# Godot API Lookup

$ARGUMENTS

Legend-dad targets **Godot 4.6.2-stable** (GDScript). API docs are generated from that tag.

## How to Answer

1. Read `${SKILL_DIR}/doc_api/_common.md` — index of ~128 common classes (Node/Node2D, physics 2D, visuals, UI, signals, timers, resources).
2. If the class isn't there, read `${SKILL_DIR}/doc_api/_other.md`.
3. Read `${SKILL_DIR}/doc_api/{ClassName}.md` — full API with descriptions for all methods, properties, signals, constants, and virtual methods.
4. Return what the caller asked for:
   - **Specific question** (e.g. "how do I detect body-entered on Area2D") → relevant methods/signals with descriptions.
   - **Full API request** (e.g. "full API for CharacterBody2D") → the entire class doc.

**GDScript syntax reference:** `${SKILL_DIR}/gdscript.md` — language features, patterns, and common recipes. Read when the caller asks about GDScript idioms (typed arrays, signals, `@onready`, `await`, tweens, state machines).

## Bootstrap

If `doc_api/` is empty, run the converter once:

```bash
bash ${SKILL_DIR}/tools/ensure_doc_api.sh
```

This shallow-clones `godotengine/godot` at tag `4.6.2-stable`, sparse-checks out `doc/classes`, and splits each `.xml` into per-class markdown under `doc_api/`. Safe to re-run — skips if already populated.

To regenerate against a newer tag, delete `doc_api/` and edit `tools/ensure_doc_api.sh` (`GODOT_TAG` at the top).

## Output Discipline

- Be targeted. Full class docs are large; quote only the relevant signature + brief description.
- Include the `doc_api/{Class}.md` path so the caller can follow up for more detail.
- If the caller asks for a class that doesn't exist in either index, say so — don't invent methods.
