# Articy Pipeline Phase 1: Vault Infrastructure & Import Manifest

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the vault-side infrastructure and vault-to-manifest pipeline so agents can write world content and generate articy-importable JSON.

**Architecture:** Vault markdown pages with YAML frontmatter → Python parser (`vault_to_manifest.py`) → JSON import manifest validated against JSON Schema → quicktype generates C#/Python types from schema. All intelligence lives in Python scripts; the MDK plugin (Phase 2) will be a thin consumer.

**Tech Stack:** Python 3.11+ (PyYAML, jsonschema, pytest), quicktype (global install), go-task (Taskfile.yml)

**Spec:** `vault/specs/2026-04-12-articy-mdk-pipeline-design.md`

**Scope:** Phase 1 only — vault scaffolding, JSON Schema, vault-to-manifest.py, Taskfile tasks, skill updates. MDK plugin, canonical export, and adapters are Phase 2 (requires articy project to exist).

---

## File Structure

**New files:**

| File | Responsibility |
|---|---|
| `vault/world/_meta/conventions.md` | Frontmatter schema, section requirements per entity type |
| `vault/world/characters/.gitkeep` | Directory scaffold |
| `vault/world/locations/.gitkeep` | Directory scaffold |
| `vault/world/factions/.gitkeep` | Directory scaffold |
| `vault/world/quests/.gitkeep` | Directory scaffold |
| `vault/world/items/.gitkeep` | Directory scaffold |
| `vault/world/history/timeline.md` | Master timeline stub |
| `vault/world/lore/.gitkeep` | Directory scaffold |
| `vault/world/bestiary/.gitkeep` | Directory scaffold |
| `project/articy/schemas/import-manifest.schema.json` | JSON Schema for the vault → articy contract |
| `project/articy/generated/.gitkeep` | quicktype output directory |
| `scripts/vault_to_manifest.py` | Main parser: vault markdown → import-manifest.json |
| `tests/conftest.py` | Pytest fixtures (tmp vault dirs, sample pages) |
| `tests/test_vault_to_manifest.py` | Unit + integration tests for the parser |

**Modified files:**

| File | Change |
|---|---|
| `Taskfile.yml` | Add `articy:prep`, `articy:types`, `articy:validate` tasks |
| `pyproject.toml` | Add `[tool.pytest.ini_options]` section |
| `.agent/skills/05-world/articy-prep/SKILL.md` | Update to call `vault_to_manifest.py` |
| `.agent/skills/05-world/world-writer/SKILL.md` | Fix paths for legend-dad |
| `.agent/skills/05-world/lore-checker/SKILL.md` | Fix paths for legend-dad |
| `.agent/skills/05-world/world-refiner/SKILL.md` | Fix paths for legend-dad |
| `.agent/skills/05-world/lore-extractor/SKILL.md` | Fix paths for legend-dad |

---

### Task 1: Scaffold vault/world/ directories

**Files:**
- Create: `vault/world/characters/.gitkeep`
- Create: `vault/world/locations/.gitkeep`
- Create: `vault/world/factions/.gitkeep`
- Create: `vault/world/quests/.gitkeep`
- Create: `vault/world/items/.gitkeep`
- Create: `vault/world/history/timeline.md`
- Create: `vault/world/lore/.gitkeep`
- Create: `vault/world/bestiary/.gitkeep`

- [ ] **Step 1: Create entity type directories**

```bash
mkdir -p vault/world/{characters,locations,factions,quests,items,lore,bestiary}
touch vault/world/{characters,locations,factions,quests,items,lore,bestiary}/.gitkeep
```

- [ ] **Step 2: Create history directory with timeline stub**

Create `vault/world/history/timeline.md`:

```markdown
---
type: timeline
status: draft
last-agent-pass: ""
---

# Master Timeline

All events are listed in chronological order. @lore-checker validates against this file.

## Eras

<!-- Define eras here as they are created -->

## Events

<!-- Events in chronological order -->
<!-- Format: ### [Era] — Event Name -->
<!-- Include: date/period, involved entities, consequences -->
```

- [ ] **Step 3: Commit**

```bash
git add vault/world/
git commit -m "feat: scaffold vault/world/ entity directories and timeline stub"
```

---

### Task 2: Create vault conventions document

**Files:**
- Create: `vault/world/_meta/conventions.md`

- [ ] **Step 1: Write conventions.md**

Create `vault/world/_meta/conventions.md`:

```markdown
---
type: meta
---

# World Bible Conventions

## Frontmatter Schema

Every vault page under `vault/world/` must start with YAML frontmatter:

| Field | Type | Required | Description |
|---|---|---|---|
| `type` | string | yes | One of: character, location, faction, quest, item, event, lore, bestiary |
| `status` | string | yes | `draft` (agent-created) or `reviewed` (human-promoted) |
| `articy-id` | string | yes | Empty string until first articy import. MDK plugin fills this. |
| `tags` | list | yes | Freeform tags for categorization |
| `connections` | list | yes | `[[Obsidian links]]` to related pages |
| `era` | string | yes | Timeline era this entity belongs to (empty if not applicable) |
| `last-agent-pass` | string | yes | ISO date of last agent edit (YYYY-MM-DD) |

## Required Sections by Type

### character
1. Overview (1-2 paragraphs)
2. Backstory
3. Personality & Motivation
4. Relationships
5. Creative Prompts (portrait, voice, theme-music)

### location
1. Overview
2. Atmosphere & Appearance
3. History
4. Notable Features
5. Creative Prompts (environment-art, ambience, music)

### faction
1. Overview
2. Purpose & Goals
3. Hierarchy & Structure
4. Territory & Influence
5. Creative Prompts (emblem, theme-music, color-palette)

### quest
1. Overview
2. Narrative Arc
3. Objectives & Stakes
4. Branching Points
5. Creative Prompts (scene-art, music, sound-design)

### item
1. Overview
2. Lore & Origin
3. Purpose & Usage

### event
1. Overview
2. Causes
3. Consequences
4. Involved Entities
5. Creative Prompts (scene-art, sound-design)

### lore
1. Overview
2. Details
3. Cultural Significance

### bestiary
1. Overview
2. Ecology & Habitat
3. Behavior
4. Lore & Cultural Significance
5. Creative Prompts (creature-art, sound-design)

## Creative Prompt Rules

- Write prompts in production-ready language for downstream asset generation (ComfyUI)
- Prefix visual prompts with the game's art style (define in project conventions when established)
- Include emotional tone, not just physical description
- Each prompt must be self-contained (≥100 characters)

## Linking Rules

- Every page must contain at least one `[[Obsidian link]]` to another vault page
- Use exact page names (case-sensitive)
- Add linked pages to the `connections` frontmatter list

## Status Workflow

```
draft → reviewed → (imported to articy)
  ↑        |
  └────────┘  (if changes needed)
```

Only humans promote `draft` → `reviewed`. Agents always write `status: draft`.
```

- [ ] **Step 2: Remove old .gitkeep from _meta/**

```bash
rm vault/world/_meta/.gitkeep
rm vault/world/_meta/prompts/.gitkeep
```

- [ ] **Step 3: Commit**

```bash
git add vault/world/_meta/
git commit -m "docs: add world bible conventions and frontmatter schema"
```

---

### Task 3: Create import manifest JSON Schema

**Files:**
- Create: `project/articy/schemas/import-manifest.schema.json`
- Create: `project/articy/generated/.gitkeep`

- [ ] **Step 1: Create directory structure**

```bash
mkdir -p project/articy/schemas
mkdir -p project/articy/generated
mkdir -p project/articy/export
touch project/articy/generated/.gitkeep
touch project/articy/export/.gitkeep
```

- [ ] **Step 2: Write the JSON Schema**

Create `project/articy/schemas/import-manifest.schema.json`:

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "import-manifest.schema.json",
  "title": "Articy Import Manifest",
  "description": "Contract between vault parser and MDK plugin. Generated by vault_to_manifest.py.",
  "type": "object",
  "required": ["version", "generated", "generated_by", "entities"],
  "additionalProperties": false,
  "properties": {
    "version": {
      "type": "string",
      "pattern": "^\\d+\\.\\d+\\.\\d+$",
      "description": "Schema version (semver)"
    },
    "generated": {
      "type": "string",
      "format": "date-time",
      "description": "ISO 8601 timestamp of generation"
    },
    "generated_by": {
      "type": "string",
      "description": "Tool that generated this manifest"
    },
    "entities": {
      "type": "array",
      "items": { "$ref": "#/$defs/entity" }
    }
  },
  "$defs": {
    "entity": {
      "type": "object",
      "required": ["vault_path", "articy_id", "type", "status", "display_name", "template_properties", "connections", "creative_prompts"],
      "additionalProperties": false,
      "properties": {
        "vault_path": {
          "type": "string",
          "description": "Relative path to the source vault page"
        },
        "articy_id": {
          "type": "string",
          "description": "Articy entity ID. Empty on first run, filled by MDK plugin."
        },
        "type": {
          "type": "string",
          "enum": ["character", "location", "faction", "quest", "item", "event", "lore", "bestiary"],
          "description": "Entity type, maps to articy template"
        },
        "status": {
          "type": "string",
          "enum": ["new", "updated", "unchanged"],
          "description": "Diff status vs previous manifest"
        },
        "display_name": {
          "type": "string",
          "minLength": 1,
          "description": "Entity display name in articy"
        },
        "template_properties": {
          "type": "object",
          "additionalProperties": { "type": "string" },
          "description": "Flat key-value map matching articy template fields"
        },
        "connections": {
          "type": "array",
          "items": { "$ref": "#/$defs/connection" },
          "description": "Relationships to other entities"
        },
        "creative_prompts": {
          "type": "object",
          "additionalProperties": { "type": "string" },
          "description": "Asset generation prompts keyed by type (portrait, voice, etc.)"
        },
        "dialogue_hooks": {
          "type": "array",
          "items": { "type": "string" },
          "description": "Hints for dialogue authoring in articy"
        },
        "flow_notes": {
          "type": "string",
          "description": "Hints for quest/flow design in articy"
        }
      }
    },
    "connection": {
      "type": "object",
      "required": ["target_vault_path", "relation"],
      "additionalProperties": false,
      "properties": {
        "target_vault_path": {
          "type": "string",
          "description": "Vault path of the target entity"
        },
        "relation": {
          "type": "string",
          "description": "Relationship type (e.g. member_of, mentor, located_in)"
        }
      }
    }
  }
}
```

- [ ] **Step 3: Validate the schema itself is valid JSON Schema**

```bash
python3 -c "
import json, jsonschema
with open('project/articy/schemas/import-manifest.schema.json') as f:
    schema = json.load(f)
jsonschema.validators.Draft202012Validator.check_schema(schema)
print('Schema is valid')
"
```

Expected: `Schema is valid`

- [ ] **Step 4: Commit**

```bash
git add project/articy/
git commit -m "feat: add import manifest JSON Schema for vault-to-articy contract"
```

---

### Task 4: Write vault_to_manifest.py — test infrastructure

**Files:**
- Create: `tests/conftest.py`
- Modify: `pyproject.toml` (add pytest config)

- [ ] **Step 1: Add pytest config to pyproject.toml**

Append to `pyproject.toml`:

```toml
[tool.pytest.ini_options]
testpaths = ["tests"]
pythonpath = ["scripts"]
```

The `pythonpath` setting lets tests `import vault_to_manifest` directly.

- [ ] **Step 2: Create conftest.py with fixtures**

Create `tests/conftest.py`:

```python
import json
from pathlib import Path

import pytest

SCHEMA_PATH = Path(__file__).parent.parent / "project" / "articy" / "schemas" / "import-manifest.schema.json"


@pytest.fixture()
def schema():
    with open(SCHEMA_PATH) as f:
        return json.load(f)


@pytest.fixture()
def sample_character_md():
    return """\
---
type: character
status: draft
articy-id: ""
tags: [protagonist]
connections:
  - "[[Elder Aldric]]"
era: "Age of Starlight"
last-agent-pass: "2026-04-12"
---

# Sera

## Overview

A young scholar from the Academy of Starlight.

## Backstory

Sera grew up in the shadow of the Academy.

## Personality & Motivation

Curious, cautious, fiercely loyal to her mentor.

## Relationships

- [[Elder Aldric]] — her mentor at the Academy
- [[Starlight Academy]] — her faction

## Creative Prompts

### portrait

16-bit pixel art, grayscale base with palette-swap tinting. Young woman with short dark hair, wearing scholar robes. Expression is thoughtful, slightly guarded. Warm amber lighting from a desk lamp.

### voice

Soft-spoken, measured cadence, slight tremor when discussing the Academy. Mid-range pitch, educated vocabulary but not pretentious.

### theme-music

Melancholic piano melody in A minor, builds from single notes to gentle chords. Evokes studying alone in a vast library at night.
"""


@pytest.fixture()
def sample_location_md():
    return """\
---
type: location
status: draft
articy-id: ""
tags: [academy, hub]
connections:
  - "[[Sera]]"
era: "Age of Starlight"
last-agent-pass: "2026-04-12"
---

# Starlight Academy

## Overview

An ancient academy perched on a cliff overlooking the Moonlit Sea.

## Atmosphere & Appearance

Towering spires of white stone, perpetually bathed in starlight.

## History

Founded in the First Era by the Starweavers.

## Notable Features

- The Great Library — largest collection of star charts
- The Observatory — where students study celestial patterns

## Creative Prompts

### environment-art

16-bit pixel art, grayscale base with palette-swap tinting. Towering white stone academy on a cliff edge, night sky filled with stars. Warm light glowing from tall arched windows. Sense of ancient knowledge and quiet grandeur.

### ambience

Gentle wind, distant waves crashing on cliffs below, faint sound of turning pages, occasional bell chime from a tower.

### music

Ethereal strings and soft choir, key of D major, slow tempo. Evokes wonder and the vastness of accumulated knowledge.
"""


@pytest.fixture()
def tmp_vault(tmp_path, sample_character_md, sample_location_md):
    """Create a temporary vault structure with sample pages."""
    world = tmp_path / "vault" / "world"
    (world / "characters").mkdir(parents=True)
    (world / "locations").mkdir(parents=True)
    (world / "characters" / "sera.md").write_text(sample_character_md)
    (world / "locations" / "starlight-academy.md").write_text(sample_location_md)
    return tmp_path
```

- [ ] **Step 3: Verify fixtures load**

```bash
python3 -m pytest tests/ --collect-only
```

Expected: `no tests ran` (collection only, no errors)

- [ ] **Step 4: Commit**

```bash
git add tests/conftest.py pyproject.toml
git commit -m "test: add pytest config and vault fixtures for manifest tests"
```

---

### Task 5: Write vault_to_manifest.py — frontmatter parsing

**Files:**
- Create: `scripts/vault_to_manifest.py`
- Create: `tests/test_vault_to_manifest.py`

- [ ] **Step 1: Write failing test for frontmatter parsing**

Create `tests/test_vault_to_manifest.py`:

```python
import json
import subprocess
import sys
from pathlib import Path

import jsonschema

from vault_to_manifest import parse_vault_page


def test_parse_frontmatter_extracts_type(sample_character_md):
    page = parse_vault_page(sample_character_md)
    assert page["frontmatter"]["type"] == "character"


def test_parse_frontmatter_extracts_articy_id(sample_character_md):
    page = parse_vault_page(sample_character_md)
    assert page["frontmatter"]["articy-id"] == ""


def test_parse_frontmatter_extracts_connections(sample_character_md):
    page = parse_vault_page(sample_character_md)
    assert '[[Elder Aldric]]' in page["frontmatter"]["connections"]


def test_parse_content_extracts_body(sample_character_md):
    page = parse_vault_page(sample_character_md)
    assert "# Sera" in page["content"]
    assert "## Backstory" in page["content"]
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
python3 -m pytest tests/test_vault_to_manifest.py -v
```

Expected: FAIL with `ModuleNotFoundError` or `ImportError`

- [ ] **Step 3: Implement parse_vault_page**

Create `scripts/vault_to_manifest.py`:

```python
"""Convert vault/world/ markdown pages into an articy import manifest."""

from __future__ import annotations

import yaml


def parse_vault_page(text: str) -> dict:
    """Parse a vault markdown page into frontmatter dict and content string."""
    if not text.startswith("---"):
        return {"frontmatter": {}, "content": text}
    parts = text.split("---", 2)
    if len(parts) < 3:
        return {"frontmatter": {}, "content": text}
    frontmatter = yaml.safe_load(parts[1]) or {}
    content = parts[2].strip()
    return {"frontmatter": frontmatter, "content": content}
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
python3 -m pytest tests/test_vault_to_manifest.py -v
```

Expected: 4 passed

- [ ] **Step 5: Commit**

```bash
git add scripts/vault_to_manifest.py tests/test_vault_to_manifest.py
git commit -m "feat: add vault page frontmatter parser with tests"
```

---

### Task 6: Write vault_to_manifest.py — section extraction

**Files:**
- Modify: `scripts/vault_to_manifest.py`
- Modify: `tests/test_vault_to_manifest.py`

- [ ] **Step 1: Write failing tests for section extraction**

Append to `tests/test_vault_to_manifest.py` (imports already at top of file):

```python
from vault_to_manifest import extract_sections, extract_creative_prompts


def test_extract_sections_finds_h2_headings(sample_character_md):
    page = parse_vault_page(sample_character_md)
    sections = extract_sections(page["content"])
    assert "Overview" in sections
    assert "Backstory" in sections
    assert "Personality & Motivation" in sections
    assert "Relationships" in sections
    assert "Creative Prompts" in sections


def test_extract_sections_content_is_stripped(sample_character_md):
    page = parse_vault_page(sample_character_md)
    sections = extract_sections(page["content"])
    assert sections["Overview"].startswith("A young scholar")


def test_extract_creative_prompts(sample_character_md):
    page = parse_vault_page(sample_character_md)
    sections = extract_sections(page["content"])
    prompts = extract_creative_prompts(sections.get("Creative Prompts", ""))
    assert "portrait" in prompts
    assert "voice" in prompts
    assert "theme-music" in prompts
    assert len(prompts["portrait"]) >= 100
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
python3 -m pytest tests/test_vault_to_manifest.py -v -k "section or creative"
```

Expected: FAIL with `ImportError` (extract_sections not defined)

- [ ] **Step 3: Implement extract_sections and extract_creative_prompts**

Append to `scripts/vault_to_manifest.py`:

```python
import re


def extract_sections(content: str) -> dict[str, str]:
    """Split markdown content into a dict keyed by ## heading name."""
    sections: dict[str, str] = {}
    current_heading = None
    current_lines: list[str] = []

    for line in content.split("\n"):
        h2_match = re.match(r"^## (.+)$", line)
        if h2_match:
            if current_heading is not None:
                sections[current_heading] = "\n".join(current_lines).strip()
            current_heading = h2_match.group(1).strip()
            current_lines = []
        elif current_heading is not None:
            current_lines.append(line)

    if current_heading is not None:
        sections[current_heading] = "\n".join(current_lines).strip()

    return sections


def extract_creative_prompts(creative_section: str) -> dict[str, str]:
    """Extract ### sub-headings from the Creative Prompts section."""
    prompts: dict[str, str] = {}
    current_key = None
    current_lines: list[str] = []

    for line in creative_section.split("\n"):
        h3_match = re.match(r"^### (.+)$", line)
        if h3_match:
            if current_key is not None:
                prompts[current_key] = "\n".join(current_lines).strip()
            current_key = h3_match.group(1).strip()
            current_lines = []
        elif current_key is not None:
            current_lines.append(line)

    if current_key is not None:
        prompts[current_key] = "\n".join(current_lines).strip()

    return prompts
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
python3 -m pytest tests/test_vault_to_manifest.py -v
```

Expected: 7 passed

- [ ] **Step 5: Commit**

```bash
git add scripts/vault_to_manifest.py tests/test_vault_to_manifest.py
git commit -m "feat: add markdown section and creative prompt extraction"
```

---

### Task 7: Write vault_to_manifest.py — entity building

**Files:**
- Modify: `scripts/vault_to_manifest.py`
- Modify: `tests/test_vault_to_manifest.py`

- [ ] **Step 1: Write failing tests for entity building**

Append to `tests/test_vault_to_manifest.py` (add `build_entity` to imports at top):

```python
from vault_to_manifest import build_entity


def test_build_entity_sets_display_name(sample_character_md):
    entity = build_entity(sample_character_md, "vault/world/characters/sera.md")
    assert entity["display_name"] == "Sera"


def test_build_entity_sets_type(sample_character_md):
    entity = build_entity(sample_character_md, "vault/world/characters/sera.md")
    assert entity["type"] == "character"


def test_build_entity_extracts_template_properties(sample_character_md):
    entity = build_entity(sample_character_md, "vault/world/characters/sera.md")
    props = entity["template_properties"]
    assert "backstory" in props
    assert "personality_and_motivation" in props
    assert "overview" in props


def test_build_entity_extracts_creative_prompts(sample_character_md):
    entity = build_entity(sample_character_md, "vault/world/characters/sera.md")
    assert "portrait" in entity["creative_prompts"]
    assert "voice" in entity["creative_prompts"]
    assert "theme-music" in entity["creative_prompts"]


def test_build_entity_parses_connections(sample_character_md):
    entity = build_entity(sample_character_md, "vault/world/characters/sera.md")
    targets = [c["target_vault_path"] for c in entity["connections"]]
    # connections are raw [[link]] names, not resolved paths yet
    assert any("Elder Aldric" in t for t in targets)


def test_build_entity_sets_vault_path(sample_character_md):
    entity = build_entity(sample_character_md, "vault/world/characters/sera.md")
    assert entity["vault_path"] == "vault/world/characters/sera.md"


def test_build_entity_defaults_status_to_new(sample_character_md):
    entity = build_entity(sample_character_md, "vault/world/characters/sera.md")
    assert entity["status"] == "new"
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
python3 -m pytest tests/test_vault_to_manifest.py -v -k "build_entity"
```

Expected: FAIL with `ImportError`

- [ ] **Step 3: Implement build_entity**

Append to `scripts/vault_to_manifest.py`:

```python
# Sections that become template_properties (not creative prompts, not relationships)
_TEMPLATE_SECTIONS = {
    "Overview": "overview",
    "Backstory": "backstory",
    "Personality & Motivation": "personality_and_motivation",
    "Atmosphere & Appearance": "atmosphere_and_appearance",
    "History": "history",
    "Notable Features": "notable_features",
    "Purpose & Goals": "purpose_and_goals",
    "Hierarchy & Structure": "hierarchy_and_structure",
    "Territory & Influence": "territory_and_influence",
    "Narrative Arc": "narrative_arc",
    "Objectives & Stakes": "objectives_and_stakes",
    "Branching Points": "branching_points",
    "Lore & Origin": "lore_and_origin",
    "Purpose & Usage": "purpose_and_usage",
    "Causes": "causes",
    "Consequences": "consequences",
    "Involved Entities": "involved_entities",
    "Details": "details",
    "Cultural Significance": "cultural_significance",
    "Ecology & Habitat": "ecology_and_habitat",
    "Behavior": "behavior",
    "Lore & Cultural Significance": "lore_and_cultural_significance",
}

_LINK_PATTERN = re.compile(r"\[\[([^\]]+)\]\]")


def _extract_display_name(content: str) -> str:
    """Extract the H1 heading as display name."""
    for line in content.split("\n"):
        m = re.match(r"^# (.+)$", line)
        if m:
            return m.group(1).strip()
    return ""


def _parse_obsidian_links(frontmatter_connections: list) -> list[dict]:
    """Convert frontmatter connection strings like '[[Name]]' into connection dicts."""
    connections = []
    for entry in frontmatter_connections:
        for match in _LINK_PATTERN.finditer(str(entry)):
            connections.append({
                "target_vault_path": match.group(1),
                "relation": "related_to",
            })
    return connections


def _extract_dialogue_hooks(sections: dict[str, str]) -> list[str]:
    """Extract dialogue hooks if a Relationships section has bullet points with dialogue context."""
    hooks = []
    for key in ("Relationships", "Branching Points"):
        text = sections.get(key, "")
        for line in text.split("\n"):
            line = line.strip()
            if line.startswith("- ") and "—" in line:
                hooks.append(line.lstrip("- "))
    return hooks


def build_entity(text: str, vault_path: str) -> dict:
    """Build a manifest entity dict from raw vault page text."""
    page = parse_vault_page(text)
    fm = page["frontmatter"]
    sections = extract_sections(page["content"])

    template_props = {}
    for heading, key in _TEMPLATE_SECTIONS.items():
        if heading in sections:
            template_props[key] = sections[heading]

    creative_section = sections.get("Creative Prompts", "")
    creative_prompts = extract_creative_prompts(creative_section)

    connections = _parse_obsidian_links(fm.get("connections", []))
    dialogue_hooks = _extract_dialogue_hooks(sections)

    return {
        "vault_path": vault_path,
        "articy_id": fm.get("articy-id", ""),
        "type": fm.get("type", ""),
        "status": "new",
        "display_name": _extract_display_name(page["content"]),
        "template_properties": template_props,
        "connections": connections,
        "creative_prompts": creative_prompts,
        "dialogue_hooks": dialogue_hooks,
        "flow_notes": sections.get("Branching Points", ""),
    }
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
python3 -m pytest tests/test_vault_to_manifest.py -v
```

Expected: 14 passed

- [ ] **Step 5: Commit**

```bash
git add scripts/vault_to_manifest.py tests/test_vault_to_manifest.py
git commit -m "feat: add entity builder from vault pages"
```

---

### Task 8: Write vault_to_manifest.py — manifest generation + validation

**Files:**
- Modify: `scripts/vault_to_manifest.py`
- Modify: `tests/test_vault_to_manifest.py`

- [ ] **Step 1: Write failing tests for manifest generation**

Append to `tests/test_vault_to_manifest.py` (add `generate_manifest` to imports at top):

```python
from vault_to_manifest import generate_manifest


def test_generate_manifest_from_vault_dir(tmp_vault, schema):
    vault_world = tmp_vault / "vault" / "world"
    manifest = generate_manifest(vault_world)
    assert manifest["version"] == "0.1.0"
    assert manifest["generated_by"] == "vault_to_manifest"
    assert len(manifest["entities"]) == 2


def test_generate_manifest_validates_against_schema(tmp_vault, schema):
    vault_world = tmp_vault / "vault" / "world"
    manifest = generate_manifest(vault_world)
    jsonschema.validate(manifest, schema)


def test_generate_manifest_entity_types(tmp_vault, schema):
    vault_world = tmp_vault / "vault" / "world"
    manifest = generate_manifest(vault_world)
    types = {e["type"] for e in manifest["entities"]}
    assert types == {"character", "location"}


def test_generate_manifest_json_roundtrip(tmp_vault, schema):
    vault_world = tmp_vault / "vault" / "world"
    manifest = generate_manifest(vault_world)
    text = json.dumps(manifest, indent=2)
    reloaded = json.loads(text)
    jsonschema.validate(reloaded, schema)
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
python3 -m pytest tests/test_vault_to_manifest.py -v -k "generate_manifest"
```

Expected: FAIL with `ImportError`

- [ ] **Step 3: Implement generate_manifest**

Append to `scripts/vault_to_manifest.py`:

```python
from datetime import datetime, timezone
from pathlib import Path

# Entity type directories under vault/world/
_TYPE_DIRS = {
    "characters": "character",
    "locations": "location",
    "factions": "faction",
    "quests": "quest",
    "items": "item",
    "history": "event",
    "lore": "lore",
    "bestiary": "bestiary",
}


def generate_manifest(vault_world: Path) -> dict:
    """Scan vault/world/ and build a complete import manifest."""
    entities = []

    for dir_name, entity_type in _TYPE_DIRS.items():
        type_dir = vault_world / dir_name
        if not type_dir.is_dir():
            continue
        for md_file in sorted(type_dir.glob("*.md")):
            if md_file.name.startswith("_") or md_file.name == "timeline.md":
                continue
            text = md_file.read_text(encoding="utf-8")
            # Build relative vault path from the vault/world/ root's parent
            # e.g. vault/world/characters/sera.md
            vault_path = f"vault/world/{dir_name}/{md_file.name}"
            entity = build_entity(text, vault_path)
            entities.append(entity)

    return {
        "version": "0.1.0",
        "generated": datetime.now(timezone.utc).isoformat(),
        "generated_by": "vault_to_manifest",
        "entities": entities,
    }
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
python3 -m pytest tests/test_vault_to_manifest.py -v
```

Expected: 18 passed

- [ ] **Step 5: Commit**

```bash
git add scripts/vault_to_manifest.py tests/test_vault_to_manifest.py
git commit -m "feat: add manifest generation from vault directory with schema validation"
```

---

### Task 9: Write vault_to_manifest.py — CLI entry point

**Files:**
- Modify: `scripts/vault_to_manifest.py`
- Modify: `tests/test_vault_to_manifest.py`

- [ ] **Step 1: Write failing test for CLI**

Append to `tests/test_vault_to_manifest.py` (imports already at top of file):

```python
def test_cli_generates_manifest_file(tmp_vault):
    vault_world = tmp_vault / "vault" / "world"
    output_file = tmp_vault / "import-manifest.json"
    result = subprocess.run(
        [sys.executable, "scripts/vault_to_manifest.py", str(vault_world), str(output_file)],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr
    assert output_file.exists()
    data = json.loads(output_file.read_text())
    assert len(data["entities"]) == 2


def test_cli_validates_against_schema_flag(tmp_vault, schema):
    vault_world = tmp_vault / "vault" / "world"
    output_file = tmp_vault / "import-manifest.json"
    schema_file = Path(__file__).parent.parent / "project" / "articy" / "schemas" / "import-manifest.schema.json"
    result = subprocess.run(
        [
            sys.executable, "scripts/vault_to_manifest.py",
            str(vault_world), str(output_file),
            "--schema", str(schema_file),
        ],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr
    assert "Validated against schema" in result.stdout
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
python3 -m pytest tests/test_vault_to_manifest.py -v -k "cli"
```

Expected: FAIL (no CLI entry point yet)

- [ ] **Step 3: Implement CLI entry point**

Append to `scripts/vault_to_manifest.py`:

```python
import argparse
import json as json_mod
import sys


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Generate articy import manifest from vault/world/")
    parser.add_argument("vault_world", type=Path, help="Path to vault/world/ directory")
    parser.add_argument("output", type=Path, help="Output path for import-manifest.json")
    parser.add_argument("--schema", type=Path, help="JSON Schema file to validate against")
    args = parser.parse_args(argv)

    if not args.vault_world.is_dir():
        print(f"Error: {args.vault_world} is not a directory", file=sys.stderr)
        return 1

    manifest = generate_manifest(args.vault_world)

    if args.schema:
        with open(args.schema) as f:
            schema = json_mod.load(f)
        jsonschema.validate(manifest, schema)
        print(f"Validated against schema: {args.schema}")

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with open(args.output, "w", encoding="utf-8") as f:
        json_mod.dump(manifest, f, indent=2)

    print(f"Generated manifest with {len(manifest['entities'])} entities -> {args.output}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

Also add the missing import at the top of the file:

```python
import jsonschema
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
python3 -m pytest tests/test_vault_to_manifest.py -v
```

Expected: 20 passed

- [ ] **Step 5: Run the script against the real (empty) vault to verify it works**

```bash
python3 scripts/vault_to_manifest.py vault/world project/articy/import-manifest.json --schema project/articy/schemas/import-manifest.schema.json
```

Expected: `Generated manifest with 0 entities` (vault is empty)

- [ ] **Step 6: Commit**

```bash
git add scripts/vault_to_manifest.py tests/test_vault_to_manifest.py
git commit -m "feat: add CLI entry point for vault_to_manifest.py"
```

---

### Task 10: Add Taskfile tasks + quicktype generation

**Files:**
- Modify: `Taskfile.yml`

- [ ] **Step 1: Add articy tasks to Taskfile.yml**

Append the following tasks to `Taskfile.yml`:

```yaml
  articy:prep:
    desc: Generate articy import manifest from vault/world/
    cmds:
      - >-
        python3 scripts/vault_to_manifest.py
        vault/world
        project/articy/import-manifest.json
        --schema project/articy/schemas/import-manifest.schema.json

  articy:types:
    desc: Regenerate typed code from articy JSON schemas via quicktype
    cmds:
      - mkdir -p project/articy/generated/python
      - mkdir -p project/articy/generated/csharp
      - >-
        quicktype
        --src-lang schema
        --lang python
        --python-version 3.11
        -o project/articy/generated/python/import_manifest.py
        project/articy/schemas/import-manifest.schema.json
      - >-
        quicktype
        --src-lang schema
        --lang csharp
        --namespace LegendDad.Articy
        -o project/articy/generated/csharp/ImportManifest.cs
        project/articy/schemas/import-manifest.schema.json
      - echo "Types generated in project/articy/generated/"

  articy:validate:
    desc: Validate existing import manifest against JSON schema
    cmds:
      - >-
        python3 -c "
        import json, jsonschema, sys;
        schema = json.load(open('project/articy/schemas/import-manifest.schema.json'));
        manifest = json.load(open('project/articy/import-manifest.json'));
        jsonschema.validate(manifest, schema);
        print(f'Valid: {len(manifest[\"entities\"])} entities')
        "
```

- [ ] **Step 2: Verify tasks run**

```bash
task articy:prep
```

Expected: `Generated manifest with 0 entities`

```bash
task articy:types
```

Expected: Types generated in `project/articy/generated/python/` and `project/articy/generated/csharp/`

- [ ] **Step 3: Add generated files to .gitignore or commit them**

The generated types should be committed so both Mac and Windows have them without needing quicktype installed. Verify the files exist:

```bash
ls project/articy/generated/python/import_manifest.py
ls project/articy/generated/csharp/ImportManifest.cs
```

- [ ] **Step 4: Commit**

```bash
git add Taskfile.yml project/articy/
git commit -m "feat: add articy Taskfile tasks and quicktype type generation"
```

---

### Task 11: Create sample vault page + end-to-end verification

**Files:**
- Create: `vault/world/characters/sera.md` (sample page for testing the full pipeline)

- [ ] **Step 1: Create a sample character page**

Create `vault/world/characters/sera.md` using the content from the `sample_character_md` fixture in `tests/conftest.py` (identical content — a character named Sera from the Academy of Starlight).

- [ ] **Step 2: Run the full pipeline**

```bash
task articy:prep
```

Expected: `Generated manifest with 1 entities`

- [ ] **Step 3: Inspect the output**

```bash
python3 -c "
import json
with open('project/articy/import-manifest.json') as f:
    m = json.load(f)
print(json.dumps(m, indent=2)[:2000])
"
```

Verify:
- `entities[0].display_name` is `"Sera"`
- `entities[0].type` is `"character"`
- `entities[0].creative_prompts` has `portrait`, `voice`, `theme-music`
- `entities[0].status` is `"new"`

- [ ] **Step 4: Validate**

```bash
task articy:validate
```

Expected: `Valid: 1 entities`

- [ ] **Step 5: Run all tests**

```bash
python3 -m pytest tests/ -v
```

Expected: All tests pass

- [ ] **Step 6: Commit**

```bash
git add vault/world/characters/sera.md project/articy/import-manifest.json
git commit -m "feat: add sample character page and verify end-to-end pipeline"
```

---

### Task 12: Update agent skills for legend-dad

**Files:**
- Modify: `.agent/skills/05-world/articy-prep/SKILL.md`
- Modify: `.agent/skills/05-world/world-writer/SKILL.md`
- Modify: `.agent/skills/05-world/lore-checker/SKILL.md`
- Modify: `.agent/skills/05-world/world-refiner/SKILL.md`
- Modify: `.agent/skills/05-world/lore-extractor/SKILL.md`

- [ ] **Step 1: Update @articy-prep**

Replace the process section in `.agent/skills/05-world/articy-prep/SKILL.md`:

The updated skill should:
1. Run `task articy:prep` to generate the import manifest
2. Read and review `project/articy/import-manifest.json`
3. Report entity count, any new entities, any validation errors
4. If entities have empty `articy-id`, note they need MDK import

Remove references to `project/articy/` entity templates (doesn't exist yet). Remove the YAML output format (replaced by JSON manifest).

- [ ] **Step 2: Update @world-writer**

In `.agent/skills/05-world/world-writer/SKILL.md`:
- Change `world/history/timeline.md` references to `vault/world/history/timeline.md`
- Change `world/_meta/conventions.md` to `vault/world/_meta/conventions.md`
- Change `world/_meta/prompts/` to `vault/world/_meta/prompts/`
- Remove references to `docs/rfcs/` (old project paths)
- Remove "Ultima Magic" references, replace with "legend-dad"

- [ ] **Step 3: Update @lore-checker**

In `.agent/skills/05-world/lore-checker/SKILL.md`:
- Change `world/history/timeline.md` to `vault/world/history/timeline.md`
- Change `world/_meta/conventions.md` to `vault/world/_meta/conventions.md`
- Remove "Ultima Magic" references

- [ ] **Step 4: Update @world-refiner**

In `.agent/skills/05-world/world-refiner/SKILL.md`:
- Change `world/history/timeline.md` to `vault/world/history/timeline.md`
- No other path changes needed (references are relative)

- [ ] **Step 5: Update @lore-extractor**

In `.agent/skills/05-world/lore-extractor/SKILL.md`:
- Remove old `docs/rfcs/` priority sources table
- Replace with: "Read source documents specified in the task. Check `vault/specs/` and `vault/design/` for design documents."
- Change output paths to `vault/world/` subdirectories
- Remove "Ultima Magic" references

- [ ] **Step 6: Run linter on any modified Python/JS**

```bash
task lint
```

Expected: Pass (skill files are markdown, no lint needed, but verify no regressions)

- [ ] **Step 7: Commit**

```bash
git add .agent/skills/05-world/
git commit -m "refactor: update world-building skills for legend-dad articy pipeline"
```

---

## Summary

| Task | What it builds | Tests |
|---|---|---|
| 1 | vault/world/ directory scaffold | — |
| 2 | _meta/conventions.md | — |
| 3 | JSON Schema for import manifest | Schema self-validation |
| 4 | Test infrastructure (conftest, pytest config) | Fixture loading |
| 5 | Frontmatter parser | 4 unit tests |
| 6 | Section + creative prompt extraction | 3 unit tests |
| 7 | Entity builder | 7 unit tests |
| 8 | Manifest generator + schema validation | 4 integration tests |
| 9 | CLI entry point | 2 CLI tests |
| 10 | Taskfile tasks + quicktype generation | Manual verification |
| 11 | Sample page + E2E pipeline | E2E verification |
| 12 | Agent skill updates | Lint check |

**Total:** 12 tasks, ~20 automated tests, ~12 commits

**What's deferred to Phase 2** (requires articy project):
- MDK import plugin (C#)
- MDK export plugin (C#)
- Canonical export JSON Schema
- Adapter scripts (ComfyUI, LDtk, Godot)
- Manifest diffing logic (new/updated/unchanged — Phase 1 always marks "new")
