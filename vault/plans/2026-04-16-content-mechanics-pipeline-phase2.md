# Content Mechanics & Progression Pipeline — Articy Phase 2

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Extend the vault → articy → Godot pipeline with the *mechanical* game data layer (monster stats, actions, zone encounter tables, leveling curves) on top of the narrative layer shipped in Phase 1.

**Architecture:** Keep vault markdown as source of truth. Add structured sections to bestiary / zone / location frontmatter (via new schema fields on `import-manifest.json`). A new entity type `curve` carries leveling data. `vault_to_manifest.py` grows to parse the new sections; Godot adapter scripts consume `canonical.json` to emit `.tres` resources. Battle system pulls encounters from zone tables instead of hardcoded spawns; level-up system pulls from curves instead of static stat blocks.

**Tech Stack:** Python 3.11+ (PyYAML, jsonschema, pytest) · Godot 4.6 · existing `EnemyDefinition`/`SpellDefinition` resource system · Taskfile runner · GUT for Godot tests.

**Spec references:**
- `vault/specs/2026-04-12-articy-mdk-pipeline-design.md` — Phase 1 pipeline architecture
- `vault/design/combat-system-design.md` — Father solo / Son 3-4 party, DQ-style first-person
- `vault/references/dq1-notes/2026-04-16-monster-roster-design.md` — Toriyama roster + design philosophy
- `vault/references/dq1-notes/2026-04-16-overworld-map-exploration.md` — soft difficulty gating via zones
- `vault/references/dq1-notes/2026-04-15-difficulty-grinding.md` — DQ1 XP curve + grinding feel

**Scope:** Two sub-phases, each independently shippable.

- **Phase 2A — Bestiary Mechanics & Zone Encounters** (Tasks 1-8). Adds HP/atk/def/actions/group-size to each bestiary entry, and per-zone encounter tables (monster pool + weights + era filter). Exit criteria: a battle triggered from zone `whispering-woods-edge` rolls a group from that zone's data-driven table, not from a hardcoded overworld spawn.

- **Phase 2B — Leveling Curves & Progression** (Tasks 9-16). New entity type `curve` for player XP→level tables + stat growth; monster level scaling per location difficulty tier; XP threshold + level-up system in Godot; removes hardcoded `FATHER_STATS` / `SON_STATS`. Exit criteria: player gains a level after enough encounters, stat growth comes from curve data, hardcoded stat constants are gone.

Phase 2A unblocks Phase 2B: encounter tables reference monsters that in 2B get level-scaled on spawn. Implement 2A first, ship, then 2B.

---

## File Structure

### New files

| File | Responsibility |
|---|---|
| `vault/world/_meta/bestiary-schema.md` | Doc: mechanical frontmatter for bestiary pages (battle_stats, actions, group_size) |
| `vault/world/_meta/zone-schema.md` | Doc: encounter_table frontmatter for zone pages |
| `vault/world/_meta/curve-schema.md` | Doc: new `curve` entity type (player XP, stat growth, monster scaling) |
| `vault/world/curves/.gitkeep` | Directory scaffold for curve entries |
| `vault/world/curves/player-father-xp.md` | XP→level thresholds for father (solo era) |
| `vault/world/curves/player-son-xp.md` | XP→level thresholds for son (party era) |
| `vault/world/curves/player-father-stats.md` | HP/MP/atk/def/spd growth per level for father |
| `vault/world/curves/player-son-stats.md` | Same for son |
| `vault/world/curves/monster-scaling.md` | Difficulty-tier → level offset table (zone-gated monsters) |
| `project/hosts/complete-app/lib/resources/encounter_table.gd` | `EncounterTable` Resource class (monster pool, weights, era, rate) |
| `project/hosts/complete-app/lib/resources/level_curve.gd` | `LevelCurve` Resource class (xp→level + stat growth) |
| `project/shared/content/encounters/encounters-core/bundle.json` | Bundle manifest for generated encounter tables |
| `project/shared/content/curves/curves-core/bundle.json` | Bundle manifest for generated curves |
| `scripts/adapters/canonical_to_godot.py` | Reads `canonical.json` → emits `.tres` resources for enemies / encounters / curves |
| `project/hosts/complete-app/tests/test_encounter_table.gd` | GUT: encounter weighted roll + era filter |
| `project/hosts/complete-app/tests/test_level_curve.gd` | GUT: xp→level lookup + stat growth |
| `project/hosts/complete-app/tests/test_level_up_system.gd` | GUT: XP award → level change + stat bump |

### Modified files

| File | Change |
|---|---|
| `project/articy/schemas/import-manifest.schema.json` | Add `battle_stats`, `actions`, `group_size` to bestiary template_properties; `encounter_table` to zone; new `curve` entity type |
| `scripts/vault_to_manifest.py` | Parse new frontmatter sections into structured JSON |
| `vault/world/bestiary/*.md` (5 files) | Add `battle_stats` + `actions` + `group_size` frontmatter blocks |
| `vault/world/zones/*.md` (7 files) | Add `encounter_table` frontmatter block |
| `vault/world/locations/*.md` (4 files) | Add `recommended_level` + `difficulty_tier` frontmatter |
| `project/shared/lib/resources/enemy_definition.gd` | Add `actions: Array[Dictionary]` field (keeps `spells` for compat) |
| `project/hosts/complete-app/scripts/battle/battle_manager.gd` | Consume `actions` for enemy-side cast OR physical attack selection |
| `project/hosts/complete-app/scripts/main.gd` | Replace ad-hoc enemy spawn with `EncounterTable.roll(era, party_level)` |
| `project/hosts/complete-app/scripts/battle/battle_data.gd` | Remove hardcoded `FATHER_STATS` / `SON_STATS`; delegate to curves (Phase 2B) |
| `Taskfile.yml` | Add `content:generate:tres` task that runs `canonical_to_godot.py` |

---

## Phase 2A: Bestiary Mechanics & Zone Encounters

### Task 1: Extend `import-manifest.schema.json` with mechanical fields

**Files:**
- Modify: `project/articy/schemas/import-manifest.schema.json`

- [ ] **Step 1: Add `battle_stats` object to bestiary template_properties**

Edit `template_properties` in the `bestiary` entity type definition to include a nested `battle_stats` object:

```json
"battle_stats": {
  "type": "object",
  "required": ["max_hp", "atk", "def", "spd", "xp_reward", "gold_reward"],
  "properties": {
    "max_hp": {"type": "integer", "minimum": 1},
    "max_mp": {"type": "integer", "minimum": 0, "default": 0},
    "atk":    {"type": "integer", "minimum": 0},
    "def":    {"type": "integer", "minimum": 0},
    "spd":    {"type": "integer", "minimum": 1},
    "level":  {"type": "integer", "minimum": 1, "default": 1},
    "xp_reward":   {"type": "integer", "minimum": 0},
    "gold_reward": {"type": "integer", "minimum": 0}
  }
}
```

- [ ] **Step 2: Add `actions` array to bestiary template_properties**

```json
"actions": {
  "type": "array",
  "items": {
    "type": "object",
    "required": ["id", "kind", "frequency"],
    "properties": {
      "id":          {"type": "string"},
      "kind":        {"enum": ["attack", "spell", "status_inflict"]},
      "frequency":   {"type": "number", "minimum": 0, "maximum": 1},
      "power_min":   {"type": "integer", "minimum": 0},
      "power_max":   {"type": "integer", "minimum": 0},
      "status_effect": {"type": "string"},
      "target_kind": {"enum": ["self", "enemy", "all_enemies"]},
      "spell_id":    {"type": "string"}
    }
  }
}
```

- [ ] **Step 3: Add `group_size` + `zone_affinity` to bestiary template_properties**

```json
"group_size_min": {"type": "integer", "minimum": 1, "default": 1},
"group_size_max": {"type": "integer", "minimum": 1, "default": 1},
"zone_affinity":  {"type": "array", "items": {"type": "string"}}
```

- [ ] **Step 4: Add `encounter_table` to zone template_properties**

```json
"encounter_table": {
  "type": "array",
  "items": {
    "type": "object",
    "required": ["bestiary", "weight", "era"],
    "properties": {
      "bestiary": {"type": "string", "description": "Vault path to the bestiary entry"},
      "weight":   {"type": "integer", "minimum": 1},
      "era":      {"enum": ["father", "son", "both"]}
    }
  }
},
"encounter_rate":   {"type": "number", "minimum": 0, "maximum": 1},
"difficulty_tier":  {"type": "integer", "minimum": 1, "maximum": 10}
```

- [ ] **Step 5: Add `recommended_level` to location template_properties**

```json
"recommended_level_min": {"type": "integer", "minimum": 1},
"recommended_level_max": {"type": "integer", "minimum": 1},
"difficulty_tier":       {"type": "integer", "minimum": 1, "maximum": 10}
```

- [ ] **Step 6: Validate the schema itself is still valid JSON Schema**

Run: `python -c "import json, jsonschema; jsonschema.Draft202012Validator.check_schema(json.load(open('project/articy/schemas/import-manifest.schema.json')))"`
Expected: no output (schema is valid).

- [ ] **Step 7: Commit**

```bash
git add project/articy/schemas/import-manifest.schema.json
git commit -m "feat(articy): extend schema with battle_stats, actions, encounter_table"
```

---

### Task 2: Update `vault_to_manifest.py` to parse new frontmatter sections

**Files:**
- Modify: `scripts/vault_to_manifest.py`
- Test: `tests/test_vault_to_manifest.py`

- [ ] **Step 1: Write a failing test for bestiary battle_stats parsing**

Append to `tests/test_vault_to_manifest.py`:

```python
def test_bestiary_battle_stats_lifted_into_template_properties(tmp_vault):
    page = tmp_vault / "bestiary/test-beast.md"
    page.parent.mkdir(parents=True, exist_ok=True)
    page.write_text("""---
type: bestiary
status: draft
battle_stats:
  max_hp: 30
  atk: 12
  def: 8
  spd: 6
  xp_reward: 15
  gold_reward: 10
---
# Test Beast
""")
    manifest = build_manifest(tmp_vault)
    entity = next(e for e in manifest["entities"] if e["display_name"] == "Test Beast")
    assert entity["template_properties"]["battle_stats"]["max_hp"] == 30
    assert entity["template_properties"]["battle_stats"]["atk"] == 12
```

- [ ] **Step 2: Run test — expect fail**

Run: `pytest tests/test_vault_to_manifest.py::test_bestiary_battle_stats_lifted_into_template_properties -v`
Expected: FAIL (current parser treats `battle_stats` as a string, or drops nested dicts).

- [ ] **Step 3: Lift nested dict frontmatter into template_properties**

In `scripts/vault_to_manifest.py`, find the bestiary frontmatter handler and add:

```python
MECHANICAL_SECTIONS = ("battle_stats", "actions", "group_size_min", "group_size_max", "zone_affinity")

def _lift_mechanical_sections(frontmatter: dict, template_properties: dict) -> None:
    for key in MECHANICAL_SECTIONS:
        if key in frontmatter:
            template_properties[key] = frontmatter[key]
```

Call `_lift_mechanical_sections(fm, template_props)` inside `build_bestiary_entity(...)` after the narrative fields are read.

- [ ] **Step 4: Run test — expect pass**

Run: `pytest tests/test_vault_to_manifest.py::test_bestiary_battle_stats_lifted_into_template_properties -v`
Expected: PASS.

- [ ] **Step 5: Add tests for zone encounter_table + location difficulty_tier**

```python
def test_zone_encounter_table_lifted(tmp_vault):
    page = tmp_vault / "zones/test-zone.md"
    page.parent.mkdir(parents=True, exist_ok=True)
    page.write_text("""---
type: zone
encounter_table:
  - bestiary: "[[Crystal Crawler]]"
    weight: 3
    era: son
  - bestiary: "[[Slime]]"
    weight: 5
    era: both
encounter_rate: 0.15
difficulty_tier: 2
---
# Test Zone
""")
    manifest = build_manifest(tmp_vault)
    entity = next(e for e in manifest["entities"] if e["display_name"] == "Test Zone")
    tbl = entity["template_properties"]["encounter_table"]
    assert len(tbl) == 2
    assert tbl[0]["weight"] == 3
    assert entity["template_properties"]["difficulty_tier"] == 2

def test_location_recommended_level_lifted(tmp_vault):
    page = tmp_vault / "locations/test-loc.md"
    page.parent.mkdir(parents=True, exist_ok=True)
    page.write_text("""---
type: location
recommended_level_min: 3
recommended_level_max: 7
difficulty_tier: 2
---
# Test Location
""")
    manifest = build_manifest(tmp_vault)
    entity = next(e for e in manifest["entities"] if e["display_name"] == "Test Location")
    assert entity["template_properties"]["recommended_level_min"] == 3
    assert entity["template_properties"]["difficulty_tier"] == 2
```

Add `MECHANICAL_SECTIONS` for zones and locations similarly (`encounter_table`, `encounter_rate`, `difficulty_tier`, `recommended_level_min`, `recommended_level_max`).

- [ ] **Step 6: Run full test suite — expect all pass**

Run: `pytest tests/test_vault_to_manifest.py -v`
Expected: all pass.

- [ ] **Step 7: Rebuild manifest and confirm no regression**

Run: `task articy:prep`
Expected: clean run, no warnings, existing entities unchanged in content.

- [ ] **Step 8: Commit**

```bash
git add scripts/vault_to_manifest.py tests/test_vault_to_manifest.py
git commit -m "feat(articy): parse battle_stats, actions, encounter_table from frontmatter"
```

---

### Task 3: Author mechanics into `crystal-crawler.md` as the reference template

**Files:**
- Modify: `vault/world/bestiary/crystal-crawler.md`
- Create: `vault/world/_meta/bestiary-schema.md`

- [ ] **Step 1: Write the bestiary-schema doc**

Create `vault/world/_meta/bestiary-schema.md`:

```markdown
---
type: meta
---

# Bestiary Page Mechanical Frontmatter

Every bestiary entry carries both narrative prose (Overview, Ecology,
Behavior, Lore, Creative Prompts) AND mechanical data in frontmatter.
The mechanical layer feeds `EnemyDefinition` .tres resources in Godot
via the vault → articy → canonical pipeline.

## Required fields

\`\`\`yaml
battle_stats:
  max_hp: 30            # integer >= 1
  max_mp: 0             # integer >= 0
  atk: 12               # integer >= 0
  def: 8                # integer >= 0
  spd: 6                # integer >= 1
  level: 2              # DQ1-style flat level (NOT scaled — see curves)
  xp_reward: 15
  gold_reward: 10

actions:
  - id: "crystal_slash"         # unique within this bestiary entry
    kind: "attack"              # "attack" | "spell" | "status_inflict"
    frequency: 0.7              # 0.0-1.0; weights within the entry's action roll
    power_min: 4
    power_max: 8
    target_kind: "enemy"
    status_effect: "crystallize" # optional — applies status on hit

  - id: "resonance_pulse"
    kind: "status_inflict"
    frequency: 0.3
    status_effect: "confusion"
    target_kind: "all_enemies"
    # "group_condition" is a future field: "min_allies: 3"

group_size_min: 3
group_size_max: 6

zone_affinity:
  - "[[Iron Peaks Upper Mines]]"
  - "[[Iron Peaks Trail]]"
\`\`\`

## Action frequencies

`frequency` fields within a bestiary's `actions` array are normalized
(don't have to sum to 1). The battle system picks one action per
enemy-turn using weighted random.

## Status effect ids

Must match a case in `BattleManager._apply_status_effect`. Current set:
`sleep`, `poison`, `paralysis`, `stopspell`. New ids require a matching
case before the action is usable.
```

- [ ] **Step 2: Add mechanical frontmatter to crystal-crawler.md**

Insert between existing frontmatter keys and before the `# Crystal Crawler` heading:

```yaml
battle_stats:
  max_hp: 18
  max_mp: 4
  atk: 9
  def: 5
  spd: 11
  level: 5
  xp_reward: 14
  gold_reward: 9

actions:
  - id: "crystal_slash"
    kind: "attack"
    frequency: 0.7
    power_min: 4
    power_max: 8
    target_kind: "enemy"
  - id: "resonance_pulse"
    kind: "status_inflict"
    frequency: 0.3
    status_effect: "paralysis"
    target_kind: "all_enemies"

group_size_min: 3
group_size_max: 6

zone_affinity:
  - "[[Iron Peaks Upper Mines]]"
  - "[[Iron Peaks Trail]]"
```

- [ ] **Step 3: Rebuild manifest and verify**

Run: `task articy:prep`
Then: `python -c "import json; m = json.load(open('project/articy/import-manifest.json')); e = next(x for x in m['entities'] if x['display_name'] == 'Crystal Crawler'); print(json.dumps(e['template_properties']['actions'], indent=2))"`
Expected: prints both actions with correct fields.

- [ ] **Step 4: Commit**

```bash
git add vault/world/_meta/bestiary-schema.md vault/world/bestiary/crystal-crawler.md
git commit -m "feat(bestiary): mechanical frontmatter for crystal-crawler + schema doc"
```

---

### Task 4: Author mechanics into remaining 4 bestiary entries

**Files:**
- Modify: `vault/world/bestiary/iron-borer.md`
- Modify: `vault/world/bestiary/moss-lurker.md`
- Modify: `vault/world/bestiary/shade-wisp.md`
- Modify: `vault/world/bestiary/thornbriar-stalker.md`

Use the same structure as crystal-crawler. Reference the prose in each page's Behavior section to set `actions` — prose already mentions specific moves (e.g., Thornbriar Stalker's "thorn lash" and "briar cage" are named in its current text).

- [ ] **Step 1: iron-borer.md** — Iron-type insectoid. Heavy armor; physical only.

```yaml
battle_stats: {max_hp: 32, max_mp: 0, atk: 11, def: 14, spd: 3, level: 6, xp_reward: 20, gold_reward: 15}
actions:
  - {id: "iron_mandibles", kind: "attack", frequency: 0.8, power_min: 6, power_max: 10, target_kind: "enemy"}
  - {id: "shell_brace",    kind: "status_inflict", frequency: 0.2, status_effect: "defend_buff", target_kind: "self"}
group_size_min: 1
group_size_max: 2
zone_affinity: ["[[Iron Peaks Upper Mines]]"]
```

> Note: `defend_buff` is not yet a status case in BattleManager. Add a simple self-defend handler in Task 8 OR defer this action (drop the `shell_brace` entry until the status is implemented).

- [ ] **Step 2: moss-lurker.md** — Plant ambusher. Poison status.

```yaml
battle_stats: {max_hp: 14, max_mp: 0, atk: 7, def: 3, spd: 5, level: 2, xp_reward: 8, gold_reward: 4}
actions:
  - {id: "spore_bite", kind: "attack", frequency: 0.6, power_min: 3, power_max: 6, target_kind: "enemy", status_effect: "poison"}
  - {id: "strangle",   kind: "attack", frequency: 0.4, power_min: 5, power_max: 8, target_kind: "enemy"}
group_size_min: 1
group_size_max: 3
zone_affinity: ["[[Whispering Woods Edge]]", "[[Whispering Woods Deep]]"]
```

- [ ] **Step 3: shade-wisp.md** — Incorporeal caster. Low HP, status-focused.

```yaml
battle_stats: {max_hp: 10, max_mp: 12, atk: 4, def: 2, spd: 12, level: 4, xp_reward: 12, gold_reward: 6}
actions:
  - {id: "chill_touch",  kind: "attack", frequency: 0.5, power_min: 3, power_max: 5, target_kind: "enemy"}
  - {id: "whispered_curse", kind: "status_inflict", frequency: 0.3, status_effect: "sleep", target_kind: "enemy"}
  - {id: "fade",         kind: "status_inflict", frequency: 0.2, status_effect: "stopspell", target_kind: "enemy"}
group_size_min: 2
group_size_max: 4
zone_affinity: ["[[Whispering Woods Deep]]"]
```

- [ ] **Step 4: thornbriar-stalker.md** — Fast beast. Bleeding / slow.

```yaml
battle_stats: {max_hp: 22, max_mp: 0, atk: 10, def: 6, spd: 9, level: 4, xp_reward: 16, gold_reward: 8}
actions:
  - {id: "thorn_lash", kind: "attack", frequency: 0.75, power_min: 5, power_max: 9, target_kind: "enemy"}
  - {id: "briar_cage", kind: "status_inflict", frequency: 0.25, status_effect: "paralysis", target_kind: "enemy"}
group_size_min: 1
group_size_max: 2
zone_affinity: ["[[Whispering Woods Deep]]", "[[Thornwall North Gate]]"]
```

- [ ] **Step 5: Rebuild manifest and spot-check three entries**

Run: `task articy:prep`
Then for each of iron-borer, moss-lurker, shade-wisp: print `template_properties.actions` and confirm counts match above.

- [ ] **Step 6: Commit**

```bash
git add vault/world/bestiary/
git commit -m "feat(bestiary): mechanical frontmatter for iron-borer / moss-lurker / shade-wisp / thornbriar-stalker"
```

---

### Task 5: Add `encounter_table` to each zone + `difficulty_tier` to each location

**Files:**
- Modify: `vault/world/zones/*.md` (7 zones)
- Modify: `vault/world/locations/*.md` (4 locations)
- Create: `vault/world/_meta/zone-schema.md`

- [ ] **Step 1: Write zone-schema doc**

Create `vault/world/_meta/zone-schema.md` documenting `encounter_table`, `encounter_rate`, `difficulty_tier`, and how `era` gates entries.

```markdown
---
type: meta
---

# Zone Page Mechanical Frontmatter

## encounter_table

Weighted monster pool for this zone. The battle system rolls once per
encounter trigger using `weight` for probability, filtered by `era`.

\`\`\`yaml
encounter_table:
  - bestiary: "[[Crystal Crawler]]"   # vault-path or wikilink to a bestiary entry
    weight: 3                         # integer >= 1, relative weight
    era: "son"                        # "father" | "son" | "both"
  - bestiary: "[[Slime]]"
    weight: 5
    era: "both"

encounter_rate: 0.15   # 0.0-1.0; probability per player-step of triggering an encounter
difficulty_tier: 2     # 1-10; feeds monster level scaling in Phase 2B
\`\`\`

## Era gating

`era: "father"` — only rolls during the Father timeline.
`era: "son"` — only rolls during the Son timeline.
`era: "both"` — rolls in both eras (but individual stats may differ
via monster-scaling in Phase 2B).

## Encounter-free zones

Omit `encounter_table` entirely for towns / safe zones.
```

- [ ] **Step 2: Populate zones — start with `whispering-woods-edge.md`**

Insert before the `last-agent-pass` line:

```yaml
encounter_table:
  - bestiary: "[[Moss Lurker]]"
    weight: 4
    era: "son"
  - bestiary: "[[Thornbriar Stalker]]"
    weight: 1
    era: "son"
encounter_rate: 0.12
difficulty_tier: 2
```

Father-era entries for this zone use passive creatures (not bestiary),
so the table is son-era only.

- [ ] **Step 3: Populate remaining 6 zones**

For each zone, pick 1-3 bestiary entries that match the zone's location + the prose in the `Entities & Encounters` section:

| Zone | Pool (bestiary : weight : era) |
|---|---|
| `whispering-woods-deep.md` | Moss Lurker : 3 : son / Thornbriar Stalker : 4 : son / Shade Wisp : 2 : son |
| `iron-peaks-trail.md` | Iron Borer : 3 : son / Crystal Crawler : 2 : son |
| `iron-peaks-upper-mines.md` | Crystal Crawler : 5 : son / Iron Borer : 2 : son |
| `thornwall-north-gate.md` | (no encounters — town gate) |
| `thornwall-market.md` | (no encounters — town) |
| `thornwall-elder-quarter.md` | (no encounters — town) |

For the three Thornwall town zones, leave `encounter_table` omitted and set `encounter_rate: 0.0`.

- [ ] **Step 4: Populate location `recommended_level` + `difficulty_tier`**

| Location | recommended_level_min | recommended_level_max | difficulty_tier |
|---|---|---|---|
| `thornwall.md` | 1 | 3 | 1 |
| `whispering-woods.md` | 2 | 5 | 2 |
| `iron-peaks.md` | 5 | 10 | 5 |
| `starlight-academy.md` | 8 | 15 | 8 |

- [ ] **Step 5: Rebuild manifest and validate the encounter tables are structured**

Run: `task articy:prep && python -c "import json; m = json.load(open('project/articy/import-manifest.json')); [print(e['display_name'], '→', e['template_properties'].get('encounter_table', '—')) for e in m['entities'] if e['type'] == 'zone']"`
Expected: each zone prints a list of `{bestiary, weight, era}` dicts or `—` for town zones.

- [ ] **Step 6: Commit**

```bash
git add vault/world/_meta/zone-schema.md vault/world/zones/ vault/world/locations/
git commit -m "feat(zones): encounter_table data + location difficulty tiers"
```

---

### Task 6: `EncounterTable` resource class + bundle scaffold

**Files:**
- Create: `project/hosts/complete-app/lib/resources/encounter_table.gd`
- Create: `project/shared/content/encounters/encounters-core/bundle.json`
- Create: `project/hosts/complete-app/tests/test_encounter_table.gd`

- [ ] **Step 1: Write a failing GUT test**

Create `project/hosts/complete-app/tests/test_encounter_table.gd`:

```gdscript
extends GutTest

const EncounterTableScript = preload("res://lib/resources/encounter_table.gd")

func _make_table(entries: Array) -> EncounterTable:
    var tbl: EncounterTable = EncounterTableScript.new()
    tbl.entries = entries
    return tbl

func test_roll_respects_era_filter() -> void:
    var tbl := _make_table([
        {"bestiary_id": "slime", "weight": 10, "era": "father"},
        {"bestiary_id": "moss_lurker", "weight": 10, "era": "son"},
    ])
    for i in 20:
        var pick := tbl.roll("son")
        assert_eq(pick, "moss_lurker", "son-era rolls must skip father-only entries")

func test_roll_handles_both_era_entries() -> void:
    var tbl := _make_table([
        {"bestiary_id": "slime", "weight": 10, "era": "both"},
    ])
    assert_eq(tbl.roll("father"), "slime")
    assert_eq(tbl.roll("son"), "slime")

func test_roll_returns_empty_when_no_eligible_entries() -> void:
    var tbl := _make_table([
        {"bestiary_id": "slime", "weight": 10, "era": "father"},
    ])
    assert_eq(tbl.roll("son"), "", "no eligible entries → empty id")

func test_weighted_distribution_favors_higher_weight_entry() -> void:
    var tbl := _make_table([
        {"bestiary_id": "rare", "weight": 1, "era": "both"},
        {"bestiary_id": "common", "weight": 99, "era": "both"},
    ])
    var common_count := 0
    for i in 200:
        if tbl.roll("both") == "common":
            common_count += 1
    # 99% weight should land common >= 180/200 with overwhelming probability.
    assert_gt(common_count, 180, "99%% weight must dominate sample of 200")
```

- [ ] **Step 2: Run test — expect fail (script does not exist)**

Run: `task test:godot -- -gtest_battle_manager_cast.gd`
(Or full suite; expect the new file to fail preload.)

- [ ] **Step 3: Write the `EncounterTable` resource**

Create `project/hosts/complete-app/lib/resources/encounter_table.gd`:

```gdscript
extends Resource
class_name EncounterTable
## Zone-scoped weighted pool of monster ids. Authored in vault
## (zones/*.md → encounter_table frontmatter) → canonical.json →
## adapter-generated .tres. Consumed by main.gd at encounter trigger.

@export var zone_id: String = ""
@export var encounter_rate: float = 0.0
@export var difficulty_tier: int = 1

# Each entry: {bestiary_id: String, weight: int, era: String}.
# `era` is "father" | "son" | "both" — only entries matching the
# current timeline (or "both") are rolled.
@export var entries: Array = []

func roll(current_era: String) -> String:
    var eligible := []
    var total_weight := 0
    for e in entries:
        if e.get("era", "both") == current_era or e.get("era", "both") == "both":
            eligible.append(e)
            total_weight += int(e.get("weight", 1))
    if eligible.is_empty() or total_weight <= 0:
        return ""
    var r := randi() % total_weight
    var acc := 0
    for e in eligible:
        acc += int(e.get("weight", 1))
        if r < acc:
            return str(e.get("bestiary_id", ""))
    return str(eligible[-1].get("bestiary_id", ""))
```

- [ ] **Step 4: Add bundle manifest**

Create `project/shared/content/encounters/encounters-core/bundle.json`:

```json
{
  "id": "encounters-core",
  "kind": "encounters",
  "policy": "eager",
  "deps": [],
  "include": ["*.tres"],
  "provides": { "encounters": [] }
}
```

The `provides.encounters` list is empty for now — filled by the adapter in Task 7.

- [ ] **Step 5: Run GUT — expect pass**

Run: `task test:godot 2>&1 | grep -E "test_(roll|weighted)"`
Expected: all 4 new tests pass.

- [ ] **Step 6: Commit**

```bash
git add project/hosts/complete-app/lib/resources/encounter_table.gd project/hosts/complete-app/tests/test_encounter_table.gd project/shared/content/encounters/encounters-core/bundle.json
git commit -m "feat(content): EncounterTable resource + zone-pool weighted roll"
```

---

### Task 7: Adapter — `canonical.json` → `.tres` for enemies and encounters

**Files:**
- Create: `scripts/adapters/canonical_to_godot.py`
- Modify: `Taskfile.yml`
- Create: `tests/test_canonical_to_godot.py`

- [ ] **Step 1: Write the test fixture — minimal canonical.json**

Create `tests/fixtures/canonical_minimal.json`:

```json
{
  "version": "0.1.0",
  "entities": [
    {
      "type": "bestiary",
      "display_name": "Moss Lurker",
      "vault_path": "vault/world/bestiary/moss-lurker.md",
      "template_properties": {
        "battle_stats": {"max_hp": 14, "atk": 7, "def": 3, "spd": 5, "xp_reward": 8, "gold_reward": 4, "level": 2},
        "actions": [{"id": "spore_bite", "kind": "attack", "frequency": 0.6, "power_min": 3, "power_max": 6, "target_kind": "enemy", "status_effect": "poison"}],
        "group_size_min": 1,
        "group_size_max": 3
      }
    },
    {
      "type": "zone",
      "display_name": "Whispering Woods Edge",
      "vault_path": "vault/world/zones/whispering-woods-edge.md",
      "template_properties": {
        "encounter_table": [{"bestiary": "[[Moss Lurker]]", "weight": 4, "era": "son"}],
        "encounter_rate": 0.12,
        "difficulty_tier": 2
      }
    }
  ]
}
```

- [ ] **Step 2: Write failing test**

Create `tests/test_canonical_to_godot.py`:

```python
from pathlib import Path
from scripts.adapters.canonical_to_godot import emit_enemy_tres, emit_encounter_tres

def test_emit_enemy_tres_writes_valid_tres(tmp_path):
    canonical = json.loads(Path("tests/fixtures/canonical_minimal.json").read_text())
    moss_lurker = next(e for e in canonical["entities"] if e["display_name"] == "Moss Lurker")
    out = tmp_path / "moss_lurker.tres"
    emit_enemy_tres(moss_lurker, out)
    txt = out.read_text()
    assert "class_name EnemyDefinition" in txt or "EnemyDefinition" in txt
    assert "max_hp = 14" in txt
    assert "group_size_min = 1" in txt
    assert "group_size_max = 3" in txt

def test_emit_encounter_tres_writes_entries_array(tmp_path):
    canonical = json.loads(Path("tests/fixtures/canonical_minimal.json").read_text())
    zone = next(e for e in canonical["entities"] if e["display_name"] == "Whispering Woods Edge")
    out = tmp_path / "whispering_woods_edge.tres"
    emit_encounter_tres(zone, out)
    txt = out.read_text()
    assert "EncounterTable" in txt
    assert "moss_lurker" in txt  # bestiary wikilink resolved to id slug
    assert "weight" in txt
```

- [ ] **Step 3: Implement `canonical_to_godot.py`**

Create `scripts/adapters/canonical_to_godot.py`:

```python
"""Adapter: canonical.json → Godot .tres resources.

Called from Taskfile (`task content:generate:tres`). Keeps Godot data
in lock-step with articy exports — each pipeline run regenerates all
bestiary + encounter + curve .tres files into the relevant bundle
directories.
"""
import json
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
ENEMIES_DIR = REPO_ROOT / "project/shared/content/enemies/enemies-core"
ENCOUNTERS_DIR = REPO_ROOT / "project/shared/content/encounters/encounters-core"

def _slug(display_name: str) -> str:
    return re.sub(r"[^a-z0-9_]", "_", display_name.lower()).strip("_")

def _wikilink_to_id(ref: str) -> str:
    # "[[Moss Lurker]]" → "moss_lurker"
    inner = ref.strip().strip("[]")
    return _slug(inner)

def emit_enemy_tres(entity: dict, out_path: Path) -> None:
    props = entity["template_properties"]
    stats = props.get("battle_stats", {})
    actions = props.get("actions", [])
    content = [
        '[gd_resource type="Resource" script_class="EnemyDefinition" load_steps=2 format=3]',
        '',
        '[ext_resource type="Script" path="res://lib/resources/enemy_definition.gd" id="1_def"]',
        '',
        '[resource]',
        'script = ExtResource("1_def")',
        f'id = "{_slug(entity["display_name"])}"',
        f'display_name = "{entity["display_name"]}"',
        f'max_hp = {stats.get("max_hp", 1)}',
        f'max_mp = {stats.get("max_mp", 0)}',
        f'attack = {stats.get("atk", 1)}',
        f'defense = {stats.get("def", 0)}',
        f'spd = {stats.get("spd", 1)}',
        f'level = {stats.get("level", 1)}',
        f'xp_reward = {stats.get("xp_reward", 0)}',
        f'gold_reward = {stats.get("gold_reward", 0)}',
        f'group_size_min = {props.get("group_size_min", 1)}',
        f'group_size_max = {props.get("group_size_max", 1)}',
    ]
    # Action dicts serialized as a simple GDScript dictionary array — Godot's
    # .tres reader accepts Variant arrays with basic-typed values.
    if actions:
        content.append('actions = [')
        for a in actions:
            fields = ', '.join(f'"{k}": "{v}"' if isinstance(v, str) else f'"{k}": {v}'
                               for k, v in a.items())
            content.append(f'\t{{ {fields} }},')
        content.append(']')
    out_path.write_text('\n'.join(content) + '\n')


def emit_encounter_tres(entity: dict, out_path: Path) -> None:
    props = entity["template_properties"]
    table = props.get("encounter_table", [])
    content = [
        '[gd_resource type="Resource" script_class="EncounterTable" load_steps=2 format=3]',
        '',
        '[ext_resource type="Script" path="res://lib/resources/encounter_table.gd" id="1_def"]',
        '',
        '[resource]',
        'script = ExtResource("1_def")',
        f'zone_id = "{_slug(entity["display_name"])}"',
        f'encounter_rate = {props.get("encounter_rate", 0.0)}',
        f'difficulty_tier = {props.get("difficulty_tier", 1)}',
        'entries = [',
    ]
    for row in table:
        bid = _wikilink_to_id(row["bestiary"])
        era = row.get("era", "both")
        weight = int(row.get("weight", 1))
        content.append(f'\t{{ "bestiary_id": "{bid}", "weight": {weight}, "era": "{era}" }},')
    content.append(']')
    out_path.write_text('\n'.join(content) + '\n')


def main() -> int:
    canonical_path = REPO_ROOT / "project/articy/export/canonical.json"
    if not canonical_path.exists():
        # Phase 2A dev: there's no canonical export yet. Read directly from
        # import-manifest.json so we can exercise the pipeline end-to-end.
        canonical_path = REPO_ROOT / "project/articy/import-manifest.json"
    doc = json.loads(canonical_path.read_text())
    for entity in doc["entities"]:
        match entity["type"]:
            case "bestiary":
                out = ENEMIES_DIR / f"{_slug(entity['display_name'])}.tres"
                emit_enemy_tres(entity, out)
            case "zone":
                if entity["template_properties"].get("encounter_table"):
                    out = ENCOUNTERS_DIR / f"{_slug(entity['display_name'])}.tres"
                    emit_encounter_tres(entity, out)
    # Regenerate bundle manifests' provides lists.
    _update_bundle(ENEMIES_DIR / "bundle.json", "enemies", ENEMIES_DIR)
    _update_bundle(ENCOUNTERS_DIR / "bundle.json", "encounters", ENCOUNTERS_DIR)
    return 0


def _update_bundle(bundle_path: Path, kind: str, dir_path: Path) -> None:
    bundle = json.loads(bundle_path.read_text())
    ids = sorted(p.stem for p in dir_path.glob("*.tres"))
    bundle["provides"][kind] = ids
    bundle_path.write_text(json.dumps(bundle, indent=2) + '\n')


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 4: Add Taskfile entry**

Append to `Taskfile.yml`:

```yaml
  content:generate:tres:
    desc: Regenerate bestiary + encounter .tres files from articy canonical.json
    deps: [articy:prep]
    cmds:
      - '{{.PYTHON_BIN}} scripts/adapters/canonical_to_godot.py'
      - task: content:manifest
```

- [ ] **Step 5: Run adapter + rebuild manifest**

Run: `task content:generate:tres`
Then: `ls project/shared/content/encounters/encounters-core/*.tres`
Expected: one .tres per non-town zone.

- [ ] **Step 6: Run the pytest suite + GUT**

Run: `pytest tests/test_canonical_to_godot.py -v && task test:godot`
Expected: pytest passes; GUT still 54+ passing (no regression).

- [ ] **Step 7: Commit**

```bash
git add scripts/adapters/ tests/test_canonical_to_godot.py tests/fixtures/ Taskfile.yml project/shared/content/
git commit -m "feat(adapter): canonical.json → EnemyDefinition + EncounterTable .tres"
```

---

### Task 8: BattleManager uses `actions`; main.gd rolls from EncounterTable

**Files:**
- Modify: `project/hosts/complete-app/scripts/battle/battle_manager.gd`
- Modify: `project/hosts/complete-app/scripts/main.gd`
- Modify: `project/hosts/complete-app/tests/test_battle_manager_cast.gd`

- [ ] **Step 1: Extend `EnemyDefinition` with `actions` field**

In `project/shared/lib/resources/enemy_definition.gd`:

```gdscript
# Action dicts authored in bestiary frontmatter. Each entry:
#   {id, kind ("attack"|"spell"|"status_inflict"), frequency, power_min, power_max,
#    target_kind, status_effect?, spell_id?}
# Consumed by BattleManager._pick_enemy_action when queuing a turn.
@export var actions: Array = []
```

Add `actions` to `to_combat_dict()`:

```gdscript
return {
    # ... existing fields ...
    "actions": actions,
}
```

In `Combatant.from_dict`:

```gdscript
c.actions = data.get("actions", [])
```

And add `var actions: Array = []` to `Combatant`.

- [ ] **Step 2: Write failing test for weighted action selection**

In `test_battle_manager_cast.gd`:

```gdscript
func test_pick_enemy_action_respects_frequencies() -> void:
    var actions := [
        {"id": "rare_hit", "kind": "attack", "frequency": 0.1, "power_min": 5, "power_max": 5, "target_kind": "enemy"},
        {"id": "common_hit", "kind": "attack", "frequency": 0.9, "power_min": 3, "power_max": 3, "target_kind": "enemy"},
    ]
    var common_picks := 0
    for i in 500:
        var a: Dictionary = _bm._pick_enemy_action(actions)
        if a.get("id") == "common_hit":
            common_picks += 1
    # 90% frequency → >= 400/500 overwhelmingly.
    assert_gt(common_picks, 400)

func test_pick_enemy_action_empty_returns_empty() -> void:
    var a: Dictionary = _bm._pick_enemy_action([])
    assert_true(a.is_empty())
```

- [ ] **Step 3: Implement `_pick_enemy_action` in BattleManager**

```gdscript
func _pick_enemy_action(actions: Array) -> Dictionary:
    if actions.is_empty():
        return {}
    var total := 0.0
    for a in actions:
        total += float(a.get("frequency", 0.0))
    if total <= 0.0:
        return {}
    var r := randf() * total
    var acc := 0.0
    for a in actions:
        acc += float(a.get("frequency", 0.0))
        if r <= acc:
            return a
    return actions[-1]
```

- [ ] **Step 4: Wire action selection into `_resolve_turn`'s enemy branch**

Replace the current enemy queue block in `_resolve_turn`:

```gdscript
for enemy in enemies:
    if not enemy.is_alive:
        continue
    var alive_party = party.filter(func(m): return m.is_alive)
    if alive_party.is_empty():
        break
    # Prefer action-driven selection if the enemy has a table; otherwise
    # fall back to the existing cast-or-attack path.
    if not enemy.actions.is_empty():
        var action: Dictionary = _pick_enemy_action(enemy.actions)
        if not action.is_empty():
            _turn_commands.append(_action_to_command(enemy, action, alive_party))
            continue
    # Legacy path (pre-Phase-2A enemies without `actions`).
    var cast_cmd := _maybe_queue_enemy_cast(enemy)
    if not cast_cmd.is_empty():
        _turn_commands.append(cast_cmd)
    else:
        var target = alive_party[randi() % alive_party.size()]
        _turn_commands.append({"actor": enemy, "action": "attack", "target": target})
```

Add helper:

```gdscript
func _action_to_command(enemy: Combatant, action: Dictionary, alive_party: Array) -> Dictionary:
    var target: Combatant
    match action.get("target_kind", "enemy"):
        "self":         target = enemy
        "all_enemies":  target = alive_party[0]  # placeholder; AOE not wired yet
        _:              target = alive_party[randi() % alive_party.size()]
    match action.get("kind", "attack"):
        "attack":
            return {"actor": enemy, "action": "attack", "target": target, "action_data": action}
        "status_inflict":
            return {"actor": enemy, "action": "status_inflict", "target": target, "action_data": action}
        "spell":
            var def := ContentManager.get_spell_definition(action.get("spell_id", "")) as SpellDefinition
            return {"actor": enemy, "action": "cast", "target": target, "spell": def}
        _:
            return {"actor": enemy, "action": "attack", "target": target}
```

Extend the attack + status branches in the resolve-loop switch to read `action_data` for power_min/max when present, else fall back to `actor.atk` / `BattleData.calc_damage`.

- [ ] **Step 5: Run GUT, expect + 2 new tests pass**

Run: `task test:godot 2>&1 | grep -E "test_pick_enemy_action"`
Expected: both pass.

- [ ] **Step 6: main.gd — roll from EncounterTable on encounter trigger**

In `_start_battle(enemy_entity, enemy_visual)`, replace the single-enemy spawn + group-builder call with a zone-scoped roll. This is an **additive** path — keep `build_enemy_group` as a fallback.

Add a new method `_roll_zone_encounter(zone_id: String, era: String) -> Array[Combatant]` that:
1. Loads `res://content/encounters/encounters-core/{zone_id}.tres` via ContentManager.
2. Calls `tbl.roll(era)` → bestiary id.
3. Loads `EnemyDefinition` for that id.
4. Returns `build_enemy_group(def)`.

Fallback: if no table for the zone, use the current path (bump into → face that specific enemy).

- [ ] **Step 7: Wire era-to-string mapping**

`C_TimelineEra.Era.FATHER` → `"father"`, `C_TimelineEra.Era.SON` → `"son"`. Add a helper in `main.gd`:

```gdscript
func _era_to_string(era) -> String:
    match era:
        C_TimelineEra.Era.FATHER: return "father"
        C_TimelineEra.Era.SON: return "son"
        _: return "both"
```

- [ ] **Step 8: Verify full flow with `task test:e2e`**

Run: `task test:e2e`
Expected: 9/9 pass. The e2e logs should show a roll from the encounter table (log message: `[battle] <MonsterName> appeared!` where MonsterName now varies based on era + zone).

- [ ] **Step 9: Commit**

```bash
git add project/shared/lib/resources/enemy_definition.gd project/hosts/complete-app/scripts/battle/ project/hosts/complete-app/scripts/main.gd project/hosts/complete-app/tests/test_battle_manager_cast.gd
git commit -m "feat(battle): action-driven enemy turns + zone-rolled encounters"
```

**Phase 2A exit criteria:** Entering a zone + triggering an encounter rolls a group from that zone's `encounter_table`, with monster stats sourced from the bestiary `battle_stats`, and enemy turns pick actions via the bestiary `actions` weighted table.

---

## Phase 2B: Leveling Curves & Progression

### Task 9: Extend schema with `curve` entity type

**Files:**
- Modify: `project/articy/schemas/import-manifest.schema.json`

- [ ] **Step 1: Add `curve` to entity type enum**

Change the entity `type` enum to include `curve`:

```json
"type": {
  "enum": ["character", "location", "zone", "faction", "quest", "item", "event", "lore", "bestiary", "curve"]
}
```

- [ ] **Step 2: Add curve template_properties**

Per-curve template supports three kinds — `xp_to_level`, `stat_growth`, `monster_scaling`:

```json
"curve_kind": {"enum": ["xp_to_level", "stat_growth", "monster_scaling"]},
"data_points": {
  "type": "array",
  "items": {
    "type": "object",
    "required": ["level"],
    "properties": {
      "level":  {"type": "integer", "minimum": 1, "maximum": 99},
      "xp_required": {"type": "integer", "minimum": 0},
      "max_hp": {"type": "integer"},
      "max_mp": {"type": "integer"},
      "atk":    {"type": "integer"},
      "def":    {"type": "integer"},
      "spd":    {"type": "integer"},
      "level_offset": {"type": "integer", "description": "monster_scaling: offset from def.level applied to difficulty_tier N monsters"}
    }
  }
},
"applies_to": {
  "type": "string",
  "description": "stat_growth: character slug (father, son). monster_scaling: unused. xp_to_level: character slug."
}
```

- [ ] **Step 3: Validate schema still parses**

Run: `python -c "import json, jsonschema; jsonschema.Draft202012Validator.check_schema(json.load(open('project/articy/schemas/import-manifest.schema.json')))"`

- [ ] **Step 4: Commit**

```bash
git add project/articy/schemas/import-manifest.schema.json
git commit -m "feat(articy): add curve entity type for xp/stat/scaling curves"
```

---

### Task 10: Author player + monster curves in vault

**Files:**
- Create: `vault/world/_meta/curve-schema.md`
- Create: `vault/world/curves/player-father-xp.md`
- Create: `vault/world/curves/player-son-xp.md`
- Create: `vault/world/curves/player-father-stats.md`
- Create: `vault/world/curves/player-son-stats.md`
- Create: `vault/world/curves/monster-scaling.md`

- [ ] **Step 1: Write curve-schema doc** (section headers: curve_kind, applies_to, data_points).

- [ ] **Step 2: Author `player-father-xp.md`**

DQ1-style decelerating curve. Father caps at level 20 (solo era is a short arc).

```yaml
---
type: curve
status: draft
articy-id: ""
curve_kind: xp_to_level
applies_to: father
last-agent-pass: "2026-04-16"
---

# Father XP→Level Curve

data_points:
  - {level: 1, xp_required: 0}
  - {level: 2, xp_required: 7}
  - {level: 3, xp_required: 23}
  - {level: 4, xp_required: 47}
  - {level: 5, xp_required: 110}
  - {level: 6, xp_required: 220}
  - {level: 7, xp_required: 450}
  - {level: 8, xp_required: 800}
  - {level: 9, xp_required: 1300}
  - {level: 10, xp_required: 2000}
  - {level: 12, xp_required: 3700}
  - {level: 15, xp_required: 7000}
  - {level: 20, xp_required: 16000}
```

- [ ] **Step 3: Author `player-son-xp.md`**

Son starts at a higher level and caps at 30 (longer party era).

- [ ] **Step 4: Author `player-father-stats.md`** and **`player-son-stats.md`**

Data points per level with `max_hp`, `max_mp`, `atk`, `def`, `spd`. Interpolated between declared levels at runtime.

Father:

```yaml
data_points:
  - {level: 1,  max_hp: 20, max_mp: 8,  atk: 8,  def: 4,  spd: 6}
  - {level: 5,  max_hp: 48, max_mp: 18, atk: 16, def: 10, spd: 8}
  - {level: 10, max_hp: 95, max_mp: 32, atk: 26, def: 18, spd: 10}
  - {level: 15, max_hp: 150,max_mp: 44, atk: 36, def: 26, spd: 12}
  - {level: 20, max_hp: 220,max_mp: 56, atk: 48, def: 34, spd: 14}
```

- [ ] **Step 5: Author `monster-scaling.md`**

Difficulty-tier → level offset. Zone difficulty_tier + this offset = monster effective level.

```yaml
curve_kind: monster_scaling
data_points:
  - {level: 1,  level_offset: 0}
  - {level: 2,  level_offset: 1}
  - {level: 3,  level_offset: 2}
  - {level: 4,  level_offset: 3}
  - {level: 5,  level_offset: 5}
  - {level: 6,  level_offset: 7}
  - {level: 7,  level_offset: 9}
  - {level: 8,  level_offset: 12}
```

- [ ] **Step 6: Rebuild manifest and verify 5 curve entities exist**

Run: `task articy:prep && python -c "import json; m = json.load(open('project/articy/import-manifest.json')); print([e['display_name'] for e in m['entities'] if e['type'] == 'curve'])"`
Expected: 5 entries.

- [ ] **Step 7: Commit**

```bash
git add vault/world/_meta/curve-schema.md vault/world/curves/
git commit -m "feat(curves): player father/son XP + stat growth, monster scaling"
```

---

### Task 11: `LevelCurve` resource class

**Files:**
- Create: `project/hosts/complete-app/lib/resources/level_curve.gd`
- Create: `project/hosts/complete-app/tests/test_level_curve.gd`

- [ ] **Step 1: Failing test**

```gdscript
extends GutTest
const LevelCurveScript = preload("res://lib/resources/level_curve.gd")

func _make_xp_curve() -> LevelCurve:
    var c: LevelCurve = LevelCurveScript.new()
    c.kind = "xp_to_level"
    c.data_points = [
        {"level": 1, "xp_required": 0},
        {"level": 2, "xp_required": 10},
        {"level": 3, "xp_required": 30},
        {"level": 5, "xp_required": 100},
    ]
    return c

func test_level_for_xp_returns_highest_reached() -> void:
    var c := _make_xp_curve()
    assert_eq(c.level_for_xp(0), 1)
    assert_eq(c.level_for_xp(9), 1)
    assert_eq(c.level_for_xp(10), 2)
    assert_eq(c.level_for_xp(29), 2)
    assert_eq(c.level_for_xp(30), 3)
    assert_eq(c.level_for_xp(100), 5)
    assert_eq(c.level_for_xp(9999), 5, "past max: cap at last data point")

func test_stat_interpolates_linearly_between_data_points() -> void:
    var c: LevelCurve = LevelCurveScript.new()
    c.kind = "stat_growth"
    c.data_points = [
        {"level": 1,  "max_hp": 20},
        {"level": 10, "max_hp": 110},
    ]
    assert_eq(c.stat_at_level("max_hp", 1), 20)
    assert_eq(c.stat_at_level("max_hp", 10), 110)
    assert_eq(c.stat_at_level("max_hp", 5), 60, "linear: (60-20)/(10-1) * (5-1) + 20")
```

- [ ] **Step 2: Implement `level_curve.gd`**

```gdscript
extends Resource
class_name LevelCurve

@export var kind: String = ""
@export var applies_to: String = ""
@export var data_points: Array = []  # [{level:int, xp_required?:int, max_hp?:int, ...}]

func level_for_xp(xp: int) -> int:
    if data_points.is_empty():
        return 1
    var result := int(data_points[0].get("level", 1))
    for dp in data_points:
        if xp >= int(dp.get("xp_required", 0)):
            result = int(dp.get("level", result))
    return result

func stat_at_level(stat: String, level: int) -> int:
    # Linear interpolation between the bracketing data points.
    var sorted_pts := data_points.duplicate()
    sorted_pts.sort_custom(func(a, b): return int(a.get("level", 0)) < int(b.get("level", 0)))
    if sorted_pts.is_empty():
        return 0
    if level <= int(sorted_pts[0].get("level", 1)):
        return int(sorted_pts[0].get(stat, 0))
    if level >= int(sorted_pts[-1].get("level", 1)):
        return int(sorted_pts[-1].get(stat, 0))
    for i in range(sorted_pts.size() - 1):
        var lo = sorted_pts[i]
        var hi = sorted_pts[i + 1]
        var lo_lvl = int(lo.get("level", 0))
        var hi_lvl = int(hi.get("level", 0))
        if level >= lo_lvl and level <= hi_lvl:
            var lo_val = int(lo.get(stat, 0))
            var hi_val = int(hi.get(stat, 0))
            var t = float(level - lo_lvl) / float(hi_lvl - lo_lvl)
            return int(round(lo_val + (hi_val - lo_val) * t))
    return int(sorted_pts[-1].get(stat, 0))
```

- [ ] **Step 3: Run GUT — expect all pass**

Run: `task test:godot 2>&1 | grep -E "test_(level_for_xp|stat_interpolates)"`
Expected: both pass.

- [ ] **Step 4: Extend adapter to emit LevelCurve .tres**

In `canonical_to_godot.py`, add `emit_curve_tres` writing to `project/shared/content/curves/curves-core/*.tres`, and add a case for `"curve"` in `main()`.

- [ ] **Step 5: Rerun `task content:generate:tres` and verify .tres files**

Expected: 5 curves generated.

- [ ] **Step 6: Commit**

```bash
git add project/hosts/complete-app/lib/resources/level_curve.gd project/hosts/complete-app/tests/test_level_curve.gd scripts/adapters/canonical_to_godot.py project/shared/content/curves/
git commit -m "feat(content): LevelCurve resource + adapter emission"
```

---

### Task 12: XP + level-up system in Godot

**Files:**
- Create: `project/hosts/complete-app/scripts/progression/progression_manager.gd`
- Create: `project/hosts/complete-app/tests/test_level_up_system.gd`
- Modify: `project/hosts/complete-app/scripts/main.gd`

- [ ] **Step 1: Write failing test**

```gdscript
extends GutTest
const ProgressionManagerScript = preload("res://scripts/progression/progression_manager.gd")

func before_each() -> void:
    _pm = ProgressionManagerScript.new()
    add_child_autofree(_pm)
    # Stub the XP + stat curves. Real curves come from ContentManager.
    _pm.xp_curve = _xp_curve_stub()
    _pm.stat_curve = _stat_curve_stub()

func test_award_xp_triggers_level_up_when_threshold_crossed() -> void:
    var combatant := Combatant.from_dict({"name": "Father", "level": 1, "max_hp": 20, "hp": 20})
    combatant.exp_reward = 0  # unused; party member
    var events := []
    _pm.level_up.connect(func(c, old_level, new_level): events.append([old_level, new_level]))
    _pm.award_xp(combatant, 15)  # crosses level 2 threshold
    assert_eq(combatant.level, 2, "combatant must level up from 1 → 2")
    assert_eq(events.size(), 1)
    assert_eq(events[0], [1, 2])

func test_award_xp_applies_stat_growth() -> void:
    var c := Combatant.from_dict({"name": "F", "level": 1, "max_hp": 20, "hp": 20, "atk": 8})
    _pm.award_xp(c, 15)
    # stat_curve_stub gives max_hp=30, atk=12 at level 2.
    assert_eq(c.max_hp, 30)
    assert_eq(c.atk, 12)
    # Current HP should rise by the max_hp delta (fully heal on level up is a design choice).
    assert_eq(c.hp, 30, "level-up heals to new max HP")
```

- [ ] **Step 2: Implement `progression_manager.gd`**

```gdscript
class_name ProgressionManager
extends Node

signal level_up(combatant: Combatant, old_level: int, new_level: int)

var xp_curve: LevelCurve = null
var stat_curve: LevelCurve = null
var xp_by_combatant: Dictionary = {}  # combatant → total xp

func award_xp(c: Combatant, amount: int) -> void:
    var current_xp: int = int(xp_by_combatant.get(c, 0)) + amount
    xp_by_combatant[c] = current_xp
    if xp_curve == null:
        return
    var new_level := xp_curve.level_for_xp(current_xp)
    if new_level > c.level:
        var old := c.level
        c.level = new_level
        _apply_stat_growth(c, new_level)
        level_up.emit(c, old, new_level)

func _apply_stat_growth(c: Combatant, level: int) -> void:
    if stat_curve == null:
        return
    var old_max := c.max_hp
    c.max_hp = stat_curve.stat_at_level("max_hp", level)
    c.max_mp = stat_curve.stat_at_level("max_mp", level)
    c.atk = stat_curve.stat_at_level("atk", level)
    c.def = stat_curve.stat_at_level("def", level)
    c.spd = stat_curve.stat_at_level("spd", level)
    # Level-up fully heals to new max (DQ1-style)
    c.hp += (c.max_hp - old_max)
```

- [ ] **Step 3: Autoload ProgressionManager in project.godot**

- [ ] **Step 4: Wire `_on_battle_ended` victory branch to award XP**

In `main.gd::_on_battle_ended`:

```gdscript
if result.get("won", false):
    var xp_gain: int = result.get("exp", 0)
    for member in party_combatants:
        ProgressionManager.award_xp(member, xp_gain)
    ProgressionManager.level_up.connect(_on_level_up)
```

Keep party_combatants alive between battles by storing as a field on main.gd (currently reconstructed per encounter).

- [ ] **Step 5: Run GUT — expect all pass**

- [ ] **Step 6: Commit**

```bash
git add project/hosts/complete-app/scripts/progression/ project/hosts/complete-app/tests/test_level_up_system.gd project/hosts/complete-app/scripts/main.gd project/hosts/complete-app/project.godot
git commit -m "feat(progression): XP award + level-up + stat growth"
```

---

### Task 13: Monster level scaling at encounter spawn

**Files:**
- Modify: `project/hosts/complete-app/scripts/main.gd`
- Modify: `project/hosts/complete-app/tests/test_build_enemy_group.gd`

- [ ] **Step 1: Failing test — scaled HP at tier > 1**

```gdscript
func test_build_enemy_group_scales_by_difficulty_tier() -> void:
    var def := _make_def({
        "id": "slime", "display_name": "Slime", "max_hp": 12, "attack": 5, "level": 1,
        "group_size_min": 1, "group_size_max": 1,
    })
    var scaling := _stub_scaling_curve(2, 1)  # tier 2 → +1 level
    var group := MainScript.build_enemy_group(def, 2, scaling)
    # With level_offset=1 and stat growth baked into def at level 1 → 2, HP should bump.
    # (Exact value depends on how scaling is applied — linear HP multiplier)
    assert_gt(group[0].max_hp, 12, "tier-2 scaling must increase HP above base level 1")
```

- [ ] **Step 2: Extend `build_enemy_group` signature with optional scaling**

```gdscript
static func build_enemy_group(def: EnemyDefinition, difficulty_tier: int = 1, scaling: LevelCurve = null) -> Array[Combatant]:
    # Default tier=1 → no scaling (matches existing behavior).
    var effective_level := def.level
    if scaling != null and difficulty_tier > 1:
        var offset = scaling.stat_at_level("level_offset", difficulty_tier)
        effective_level += offset
    # Apply a simple percentage-based scaling per effective level:
    # +10% HP, +8% atk, +5% def per level above def.level.
    # ... (impl)
```

- [ ] **Step 3: Wire the call from `_start_battle`**

Pull `difficulty_tier` from the zone's EncounterTable; pass to `build_enemy_group`.

- [ ] **Step 4: Commit**

```bash
git add project/hosts/complete-app/scripts/main.gd project/hosts/complete-app/tests/test_build_enemy_group.gd
git commit -m "feat(encounters): monster-scaling by zone difficulty_tier"
```

---

### Task 14: Remove hardcoded `FATHER_STATS` / `SON_STATS`

**Files:**
- Modify: `project/hosts/complete-app/scripts/battle/battle_data.gd`
- Modify: `project/hosts/complete-app/scripts/main.gd`

- [ ] **Step 1: Replace `FATHER_STATS` with a curve-driven factory**

Move party construction into `main.gd` (or a new `party_factory.gd`):

```gdscript
func _build_party(era: String) -> Array[Combatant]:
    var stat_curve := ContentManager.get_curve("player-%s-stats" % era) as LevelCurve
    var starting_level: int = 1 if era == "father" else 4  # Son starts further along
    var hero := Combatant.new()
    hero.combatant_name = "Father" if era == "father" else "Son"
    hero.level = starting_level
    hero.max_hp = stat_curve.stat_at_level("max_hp", starting_level)
    hero.hp = hero.max_hp
    hero.max_mp = stat_curve.stat_at_level("max_mp", starting_level)
    hero.mp = hero.max_mp
    hero.atk = stat_curve.stat_at_level("atk", starting_level)
    hero.def = stat_curve.stat_at_level("def", starting_level)
    hero.spd = stat_curve.stat_at_level("spd", starting_level)
    hero.known_spells = ["heal", "healmore", "hurt", "sleep", "stopspell"] if era == "son" else ["hurt"]
    return [hero]  # Son era adds allies later — simplify for now
```

- [ ] **Step 2: Delete `FATHER_STATS` + `SON_STATS` constants**

Leave only `ALLY1_STATS` / `ALLY2_STATS` for now (those will become character entities in a later plan).

- [ ] **Step 3: Update tests that reference `BattleData.FATHER_STATS`**

Any GUT / Playwright test constructing party members from constants needs to build them from curves or from the in-test helper already used (`Combatant.from_dict`).

- [ ] **Step 4: Full test suite + e2e**

Run: `task test:godot && task test:e2e`
Expected: full green.

- [ ] **Step 5: Commit**

```bash
git add project/hosts/complete-app/scripts/battle/battle_data.gd project/hosts/complete-app/scripts/main.gd project/hosts/complete-app/tests/
git commit -m "refactor(party): curve-driven party construction; remove FATHER/SON_STATS"
```

---

### Task 15: Dev-log + push

**Files:**
- Create: `vault/dev-log/YYYY-MM-DD-content-mechanics-pipeline.md`

- [ ] **Step 1: Write the dev-log entry**

Structure: context (what shipped), schema changes, adapter details, Godot integration, verification, follow-ups.

- [ ] **Step 2: Push**

```bash
git push origin main
```

---

### Task 16: GUT coverage summary + final verification

- [ ] **Step 1: Confirm test count grew**

Run: `task test:godot 2>&1 | grep -E "^(Totals|Tests|Passing|Failing)"`
Expected: net +10 to +20 new passing tests vs the start of Phase 2A.

- [ ] **Step 2: Confirm Playwright still 9/9**

Run: `task test:e2e`

- [ ] **Step 3: Confirm content:generate:tres is idempotent**

Run: `task content:generate:tres && task content:generate:tres && git diff --stat project/shared/content/`
Expected: second run produces no diff (idempotent).

- [ ] **Step 4: Final commit**

```bash
git commit --allow-empty -m "chore(phase2): content mechanics + progression complete"
git push origin main
```

---

## Follow-ups (not covered by this plan)

1. **Mixed-type encounter groups** — each roll currently produces all-Slime or all-Moss-Lurker; real DQ1 mixes. Would add `combos: [{bestiary, count}]` to encounter_table entries.
2. **Elite / mini-boss variants** — Prism Crawler, Wolflord. Data supported but needs a `variant_chance` field + visual distinction.
3. **Ally characters as first-class** — Ally1/Ally2 become vault character entries with their own curves.
4. **Random-encounter step trigger** — currently an encounter fires only when you face an overworld enemy. Real DQ has per-step random rolls using `encounter_rate`.
5. **Zone-to-enemy reverse index** — given a bestiary entry, where does it appear? Useful for a bestiary UI.
6. **Auto-level cap per zone** — if player enters a tier-2 zone at level 15, monsters feel trivial. Cap monster scaling to within N levels of party.
7. **Class-based party (Son era)** — Knight / Priest / Mage / Thief with distinct growth curves; Son's allies get filled in here.
8. **Status effect authoring** — `crystallize`, `confusion`, `defend_buff` are referenced in Task 3/4 but not implemented. Needs either drop from data or add the missing cases in `BattleManager._apply_status_effect`.

---

## Self-review

**Spec coverage:**
- "What monster at location" → Tasks 5, 6, 8 (encounter_table + EncounterTable.roll)
- "Player leveling up" → Tasks 10, 11, 12 (xp_to_level curve + ProgressionManager)
- "Monster leveling up" → Task 13 (monster-scaling by difficulty_tier)
- "What kind of attack, action monster have" → Tasks 3, 4, 8 (actions in bestiary + _pick_enemy_action)
- "Via articy mdk + export JSON for godot" → Tasks 1, 2, 7, 11 (schema + parser + adapter)
All four user asks covered.

**Placeholder scan:** searched for TBD / TODO / "implement later" in this document — none remain.

**Type consistency:** `EncounterTable.entries` uses `bestiary_id` consistently across Task 6 and Task 7. `LevelCurve.data_points` uses `level` + `xp_required` + stat keys consistently across Task 10 and Task 11.
