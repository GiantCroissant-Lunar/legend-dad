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

1. Run `task articy:prep` to generate the import manifest.
2. Read and review `project/articy/import-manifest.json`.
3. Report entity count, any new entities, and any validation errors.
4. If entities have empty `articy-id`, note they need MDK import.

## Output Format

Report results in plain prose:

- Total entity count from the manifest
- List any new entities (not previously in the manifest)
- List any validation errors found
- List entities with empty `articy-id` that require MDK import

## Rules

- Only process pages with `status: reviewed`. Reject draft pages.
- Do not invent dialogue — only suggest hooks and topics for Articy authoring.
- Reference existing Articy global variables from the project when relevant.
