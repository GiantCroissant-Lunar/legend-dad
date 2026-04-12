---
name: lore-checker
description: "Validate vault pages against the master timeline and existing canon for contradictions. Use after generating or editing any world bible content."
category: 05-world
layer: world
related_skills:
  - "@world-writer"
  - "@lore-extractor"
---

# Lore Checker

Consistency validator for the legend-dad world bible. Does NOT generate content — only validates.

## Process

1. Read `vault/world/history/timeline.md` (mandatory).
2. Read all pages referenced in the target page's `connections` frontmatter.
3. Read all pages that share the same `tags` values.
4. Compare names, dates, locations, faction relationships, and character details.
5. Report findings.

## Output Format

```markdown
## Lore Check: [page name]

### Status: PASS | WARN | FAIL

### Issues Found
- [CONTRADICTION] [description] — conflicts with [[page]]
- [MISSING LINK] [description] — should reference [[page]]
- [TIMELINE ERROR] [description] — date X conflicts with timeline

### Suggestions
- [suggestion for resolution]
```

If no issues: `### Status: PASS` with a brief confirmation.

## Validation Rules

- **Proper nouns** — names must match exactly across pages (case-sensitive).
- **Chronology** — events must respect ordering in `vault/world/history/timeline.md`.
- **Faction membership** — characters must belong to factions they're listed under.
- **Mechanical consistency** — spells, abilities, and equipment must not contradict RFC rules.
- **Link coverage** — every page should reference at least one other vault page.
- **Frontmatter completeness** — all required fields per `vault/world/_meta/conventions.md`.
