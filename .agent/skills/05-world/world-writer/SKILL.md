---
name: world-writer
description: "Generate world bible pages for the Obsidian vault using prompt templates and existing lore as context. Use when creating new lore, character backstories, location histories, faction profiles, or any world-building content."
category: 05-world
layer: world
related_skills:
  - "@lore-checker"
  - "@lore-extractor"
  - "@articy-authoring"
---

# World Writer

Generate rich, internally consistent lore pages for the world bible vault at `vault/world/`.

## Process

1. **Read context first.** Always read `vault/world/history/timeline.md` before writing anything. Read all pages listed in the topic's `connections` or referenced in the prompt template.
2. **Read the prompt template** from `vault/world/_meta/prompts/` matching the content type (character-backstory, location-history, culture-profile, timeline-event, faction-profile, bestiary-entry).
3. **Read relevant design docs** from `vault/specs/` or `vault/design/` when the prompt template specifies mechanical constraints.
4. **Generate the page** with proper YAML frontmatter and all required sections per `vault/world/_meta/conventions.md`.
5. **Delegate to @lore-checker** to validate the draft against timeline and canon.

## Writing Guidelines

- Write in a **narrative, in-world tone** — as if authored by a chronicler or scholar within the world.
- Ground every claim in existing lore. Do not invent new proper nouns (places, characters, factions) unless the prompt explicitly asks for it.
- Use `[[Obsidian links]]` to reference other vault pages. Every page must link to at least one other page.
- Respect game mechanics from the RFCs — do not contradict stat systems, spell rules, or equipment tiers.
- Keep pages focused. One concept per page.

## Output Format

Every page must start with YAML frontmatter:

```yaml
---
type: character | location | faction | event | lore | quest
status: draft
articy-id: ""
tags: []
connections: []
era: ""
last-agent-pass: "YYYY-MM-DD"
---
```

Set `status: draft` always. Only humans promote to `reviewed`.

## Creative Prompts (Mandatory)

Every page MUST end with a `## Creative Prompts` section containing structured prompt blocks for downstream asset generation agents (art, music, sound, voice). These prompts are the bridge between the world bible and production.

Each prompt type uses a fenced `prompt` block. Include only the types relevant to the page's content type — see `vault/world/_meta/conventions.md` for the full mapping:

| Page Type | Required Prompts |
|-----------|-----------------|
| character | `portrait`, `voice`, `theme-music` |
| location | `environment-art`, `ambience`, `music` |
| faction | `emblem`, `theme-music`, `color-palette` |
| event | `scene-art`, `sound-design` |
| lore | `concept-art` (if visual), `music` (if atmospheric) |
| bestiary | `creature-art`, `sound-design` |

### Prompt Rules

- Write prompts in **production-ready language** — an art/music agent should use them directly without rewriting.
- Prefix visual prompts with the game's art style: "16-bit pixel art, grayscale base with palette-swap tinting."
- Include **emotional tone** — not just physical description but the feeling the asset should evoke.
- Keep each prompt **self-contained** — the agent generating a portrait reads only the prompt block, not the full page.

## Prompt Templates

Templates live in `vault/world/_meta/prompts/`. Each includes:
- Output format (frontmatter + required sections)
- Tone guidelines
- Required context reads
- Constraints from game mechanics (RFCs)
- Minimum `[[link]]` count
- Required creative prompt types

Available templates: `character-backstory`, `location-history`, `culture-profile`, `timeline-event`, `faction-profile`, `bestiary-entry`.
