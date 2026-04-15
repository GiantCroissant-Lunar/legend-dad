---
date: 2026-04-15
agent: claude-code
branch: main
version: 0.1.0-281
tags: [dev-log, spells, battle, content-manager, bundle, dq1, feature]
---

# Session Dev-Log — spells-core Bundle + Cast Action

Pairs a new `spells-core` content bundle with a working cast action in
`BattleManager`. Follows the pattern established by `enemies-core`
earlier today — .tres-driven data, hot-reloadable tunables, DQ1-inspired
content.

## What landed

### Content

`project/shared/content/spells/spells-core/`

```
bundle.json        kind=spells, policy=eager
heal.tres          MP 4, self-target, heal 25-30 HP
hurt.tres          MP 2, enemy-target, fire damage 8-12 (bypasses def)
```

DQ1 canonical values — see `vault/references/dq1-notes/2026-04-15-spell-system.md`
for the full 10-spell list. Three more combat-useful spells (Sleep,
Stopspell, Healmore) defer until a status-effect system exists; four
utility spells (Radiant, Outside, Return, Repel) defer until there's an
overworld-state hook for them.

### Schema

`project/shared/lib/resources/spell_definition.gd` — new Resource class
with `mp_cost`, `target_kind` (self/enemy/all_enemies/party),
`effect_kind` (damage/heal), `power_min`/`max`, plus forward-compat
`element` and `status_effect` fields.

### Battle flow

`BattleManager`:

- New `SPELL_SELECT` state between `COMMAND` and `TARGET_SELECT`.
- Menu construction now includes `"Spell"` iff the current member's
  `known_spells` is non-empty. Options for Father: `[Attack, Spell,
  Defend, Flee]`; Ally1/Ally2 (no spells): `[Attack, Defend, Flee]`.
- Spell sub-menu shows labels like `"Heal (MP 4)"` so players can make
  informed MP/effect trade-offs.
- `self`-target spells queue immediately; `enemy`-target spells route
  through the existing `TARGET_SELECT` flow via `_pending_cast`.
- Cancel (Backspace) during TARGET_SELECT returns to the spell sub-menu
  (matches DQ UX), not the top-level command menu.
- Resolution extracted into `_apply_cast(actor, target, spell)` so the
  math is testable in isolation. Handles MP shortfall, null spell
  fallback, and target-died-mid-turn redirect.

`Combatant.from_dict` extended to pull `spells` from the stat dict into
`known_spells: Array[String]`.

`BattleData` player stats now include `spells`:

- Father → `["hurt"]` (martial caster with a single offensive spell)
- Son → `["heal", "hurt"]` (DQ1-style dual caster)
- Ally1/Ally2 → `[]`

### Wire-up

- `ContentManager.get_spell_definition(id)` (new)
- `lib/contracts/content_manager_api.gd` — docstring updated
- `main.gd` unchanged (party construction already reads from BattleData
  stats, which now carry spell lists)

### Input map fix

The project had no `ui_*` actions registered in `project.godot`. Menu
navigation via arrow keys + Enter was therefore broken for real players
— only the existing `interact` (E) action worked as "accept". Added
explicit bindings for `ui_accept` (Enter/Space), `ui_cancel` (Esc),
`ui_up`/`down`/`left`/`right` (arrow keys). Genuine gameplay fix
surfaced while trying to drive the menu from Playwright.

## Verification

### GUT unit test

`project/hosts/complete-app/tests/test_battle_manager_cast.gd` — 6/6
passing:

| Test | What it asserts |
|---|---|
| `test_heal_deducts_mp_and_restores_hp` | self-heal works; MP drops by cost, HP rises by rolled amount |
| `test_heal_clamps_at_max_hp` | over-heal clamps to `max_hp` |
| `test_hurt_deducts_mp_and_damages_enemy_bypassing_defense` | damage spells ignore target's `def` (DQ1 semantics) |
| `test_insufficient_mp_returns_false_and_spends_nothing` | MP shortfall early-returns, no state change |
| `test_null_spell_is_safely_rejected` | defensive guard against malformed commands |
| `test_damage_spell_redirects_when_target_already_dead` | mid-turn target death routes damage to an alive sibling |

Full suite: 23/24 passing (1 pre-existing unrelated flake in
`test_time_service.gd::test_pause_when_already_paused`, confirmed by
`git stash + task test:godot` on clean main).

### Playwright integration test

`project/server/packages/e2e/tests/cast-spell.spec.js` — scoped to what
Playwright can reliably verify:

- `spells-core@{hash}.pck` fetched eagerly at boot
- `[battle-menu] Father options=[Attack, Spell, Defend, Flee]` line
  appears after combat starts — proves the bundle → ContentManager →
  Combatant.known_spells → menu construction pipeline

**Why the test doesn't drive the menu keyboard-first:** Chrome throttles
tab RAF after ~2s of lost focus, freezing Godot's main loop. Combat
input uses polling-based `Input.is_action_just_pressed` in `_process`,
which simply stops firing when RAF drops to ~1Hz. F9 works across
throttled windows because it's handled via `_unhandled_input` (event-
driven). Refactoring battle menu handlers to `_unhandled_input` would
make them drivable from Playwright too, but that's a bigger UX change
for later — `_apply_cast` is the math-bearing part and it's
unit-tested.

Also: `workers: 1, fullyParallel: false` added to `playwright.config.js`
— `hot-reload.spec.js`, `style-hot-reload.spec.js`, and
`cast-spell.spec.js` all mutate shared content files; running them in
parallel created races.

### Full e2e suite

9/9 passing end-to-end (serial).

## Files changed

```
project/shared/lib/resources/spell_definition.gd                        new
project/shared/content/spells/spells-core/                              new bundle (3 files)
project/hosts/complete-app/tests/test_battle_manager_cast.gd            new (6 tests)
project/server/packages/e2e/tests/cast-spell.spec.js                    new
project/hosts/complete-app/scripts/battle/battle_manager.gd             SPELL_SELECT state + _apply_cast
project/hosts/complete-app/scripts/battle/battle_data.gd                spells added to player stats
project/hosts/complete-app/scripts/battle/combatant.gd                  known_spells field + from_dict
project/hosts/complete-app/scripts/content_manager.gd                   get_spell_definition
project/shared/lib/contracts/content_manager_api.gd                     contract doc
project/hosts/complete-app/project.godot                                ui_* InputMap bindings
project/shared/data/content_manifest.json                               regenerated (4 bundles)
project/server/packages/e2e/playwright.config.js                        workers:1 + fullyParallel:false
```

## Follow-ups

1. **Refactor battle-menu input from polling → `_unhandled_input`** —
   fixes Playwright throttling headache AND improves menu responsiveness
   under any frame-rate dip. Enables future e2e coverage of menu flow.
2. **More spells** — Sleep (Rarihō) once a status-effect system exists;
   Healmore (Behoimi) is trivial once Son reaches level 15 (level
   progression is pre-MVP). Room for Father-specific martial spells too.
3. **Spell assignment via level-up** — DQ1 gates spells by caster level.
   Port that curve when level-up is implemented.
4. **Enemy-side casts** — `SpellDefinition` carries forward-compat
   `status_effect`/`element` fields but no enemy currently has
   `max_mp > 0`. When Magician or Wraith enemies are added to
   `enemies-core`, wire enemy AI to pick + cast.
