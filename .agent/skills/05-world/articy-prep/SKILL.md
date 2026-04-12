---
name: articy-prep
description: "Format reviewed vault pages into Articy-import-ready structured data. Use when preparing world bible content for import into Articy:draft."
category: 05-world
layer: world
related_skills:
  - "@world-writer"
  - "@lore-checker"
  - "@articy-authoring"
---

# Articy Prep

Take vault pages with `status: reviewed` and produce structured summaries suitable for manual import into Articy:draft.

## Process

1. Read the vault page — reject if `status` is not `reviewed`.
2. Map content to Articy entity types (Character, NPC, Location, Quest, Item).
3. Extract fields that match Articy template properties.
4. Output a structured summary.

## Output Format

```yaml
articy_entity:
  type: Character | NPC | Location | Quest | Item
  display_name: ""
  template_properties:
    # fields matching the Articy template for this entity type
  dialogue_hooks:
    # key lines or conversation topics to author in Articy
  flow_notes:
    # quest flow or branching logic notes
```

## Rules

- Only process pages with `status: reviewed`. Reject draft pages.
- Do not invent dialogue — only suggest hooks and topics for Articy authoring.
- Reference existing Articy global variables from the project when relevant.
- Check `project/articy/` for existing entity templates to match field names.
