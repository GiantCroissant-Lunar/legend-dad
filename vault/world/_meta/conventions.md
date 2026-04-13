---
type: meta
---

# World Bible Conventions

## Frontmatter Schema

Every vault page under `vault/world/` must start with YAML frontmatter:

| Field | Type | Required | Description |
|---|---|---|---|
| `type` | string | yes | One of: character, location, zone, faction, quest, item, event, lore, bestiary |
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

### zone
1. Overview (what this map area is, its role in gameplay)
2. Layout & Terrain (walkable areas, obstacles, elevation, water)
3. Entities & Encounters (NPCs, enemies, interactables placed here)
4. Era Variants (how this zone differs between father/son timelines)
5. Creative Prompts (tilemap-art, ambience, music)

**Zone-specific frontmatter:**
- `parent-location`: [[Location]] this zone belongs to
- `zone-type`: overworld | town | dungeon | cave | interior | boss-arena
- `floor`: integer (for multi-floor dungeons/caves, 0-indexed)
- `grid-width`: integer (zone width in tiles)
- `grid-height`: integer (zone height in tiles)

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
4. Creative Prompts (item-art, sound-effect)

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
- Each prompt must be self-contained (>=100 characters)

## Linking Rules

- Every page must contain at least one `[[Obsidian link]]` to another vault page
- Use exact page names (case-sensitive)
- Add linked pages to the `connections` frontmatter list

## Status Workflow

```
draft -> reviewed -> (imported to articy)
  ^        |
  +--------+  (if changes needed)
```

Only humans promote `draft` -> `reviewed`. Agents always write `status: draft`.
