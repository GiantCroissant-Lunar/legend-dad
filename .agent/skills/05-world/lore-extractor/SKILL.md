---
name: lore-extractor
description: "Extract world facts from RFCs and design docs into vault-formatted pages. Use when populating the world bible from existing project documentation."
category: 05-world
layer: world
related_skills:
  - "@world-writer"
  - "@lore-checker"
  - "@rfc-orchestrator"
---

# Lore Extractor

Read RFC and design documents, identify world-building facts (not game mechanics), and write them as properly formatted vault pages.

## Process

1. Read the source document(s) specified in the task.
2. Identify **world facts**: character descriptions, location details, faction information, historical events, cultural elements, quest narratives.
3. Separate world facts from pure game mechanics (stat tables, THAC0 progressions, damage formulas stay in the RFCs).
4. For each distinct concept, create or update a vault page at the correct path under `vault/world/`.
5. Follow frontmatter schema from `vault/world/_meta/conventions.md`.

## Extraction Rules

| Source content | Extract to vault | Leave in RFC |
|---------------|-----------------|-------------|
| NPC personality, backstory, motivation, relationships | Yes | No |
| NPC stat blocks (HP, AC, THAC0) | No | Yes |
| Location history, atmosphere, purpose | Yes | No |
| Location tile types, grid coordinates | No | Yes |
| Enemy lore, ecology, faction allegiance | Yes | No |
| Enemy damage dice, saving throws | No | Yes |
| Quest narrative arc, motivations, stakes | Yes | No |
| Quest variable names, condition flags | No | Yes |
| Spell in-world traditions, cultural meaning | Yes | No |
| Spell damage formulas, slot costs | No | Yes |

## Output Rules

- **Do not paraphrase mechanics as lore.** "Sera has INT 16" stays in the RFC. "Sera studied at the Academy of Starlight" goes to the vault.
- **Preserve original names exactly.** Do not rename or alias characters, places, or factions.
- **Mark all extracted content as `status: draft`.**
- **Add `connections`** to link related pages.
- **Note the source** at the bottom of each page:

```markdown
---
> Extracted from: [source file path]
```

## Sources

Read source documents specified in the task. Check `vault/specs/` and `vault/design/` for design documents.
