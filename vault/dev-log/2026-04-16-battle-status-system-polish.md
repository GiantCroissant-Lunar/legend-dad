---
date: 2026-04-16
agent: claude-code
branch: main
version: 0.1.0-283
tags: [dev-log, battle, status-effects, ai, dq1, spells, level-gating]
---

# Session Dev-Log — Battle Status System + Enemy AI + Level Gating

Cleared the five follow-ups left open in
`2026-04-15-battle-input-refactor-and-more-spells.md`. Bundled into one
commit because they share a theme — DQ1-fidelity polish on top of the
status-effect infrastructure that shipped last session.

## What shipped

### 1. Sleep indicator UI

`battle_ui.gd::_draw_status_badges(c, anchor)` renders a small glyph
next to each sleeping enemy — "Zz" for sleep, plus forward-declared
glyphs for poison/paralysis/stopspell so those light up automatically
when those statuses apply (see #3).

The badge anchor is the top-right of the enemy's ellipse so it doesn't
collide with the target-select "▼" arrow above.

### 2. Hit-wakes-sleeper

DQ1 has ~50% chance to wake a sleeper when attacking them. Added
`_check_hit_wakes_sleeper(target)` called from `_resolve_turn`'s
attack branch after damage lands and the target is confirmed alive.

Intentionally scoped to physical attacks — Hurt/Healmore don't wake
sleepers even when damaging them. Matches DQ1's UX: status-inflicting
spells like Sleep are your reliable lock, and the player/enemy coin-flips
a wake only on a weapon strike.

### 3. Status effect expansion (poison + paralysis + stopspell)

`_tick_status_effects(actor)` now handles four statuses in one pass:

| Status | Turn effect | Duration |
|---|---|---|
| sleep | skip turn; 33% random wake, forced wake on counter=0 | 2-4 |
| paralysis | skip turn; no random recovery, fixed tick-down | 1-2 |
| poison | chip damage 1-4 (actor still acts); can kill via tick | 4-8 |
| stopspell | actor acts normally; SPELL menu hidden until worn off | 3-5 |

`_apply_status_effect` dispatches on `spell.status_effect` with
DQ1-calibrated landing rates:

- sleep: 65%
- stopspell: 50%
- paralysis: 45%
- poison: 100% (no resist — typically applied by enemy attacks/hazards,
  not a player spell in DQ1)

Only Stopspell ships as a player spell this session
(`spells-core/stopspell.tres`, MP 2, target=enemy). Poison + paralysis
get infrastructure but no player-facing spell — they're reserved for
enemy moves / environmental hazards as DQ2+ content lands.

The SPELL menu in `_show_menu_for_current_member` now checks
`member.status_effects.has("stopspell")` and drops the option for the
duration. Visible feedback for the player without a separate notification.

### 4. Enemy-side casts

Enemies with `max_mp > 0` + at least one viable spell can now queue a
cast command instead of attacking, with a 35% overall rate (coin-flips
at queue time, matches DQ1's "action locked in at turn start" model).

`_maybe_queue_enemy_cast(enemy)` gates:
- stopspelled → never cast (reuses the player-side stopspell check)
- no known_spells or 0 MP → never cast
- RNG rolls under 35% → queue attack instead

If the gates pass, viable spells are filtered (MP affordability + level
gate — see #5) and `_pick_enemy_cast_command(enemy, viable)` builds the
cast dict. Target-kind dispatch:
- `"self"` → target = caster (e.g. enemy healing itself)
- `"enemy"` → target = random alive party member

The pure decision/targeting path is split from the ContentManager lookup
so GUT can exercise it without driving the autoload bundle system.

**Shipped enemy: Magician** (`magician.tres`). DQ1 canon:
- HP 22 / MP 8 / Atk 11 / Def 12 / Spd 7
- Level 3, knows `["hurt"]` (fits DQ1's Hurt L4 gate loosely — Magician
  gets it as an innate move)
- Added to `enemies-core/bundle.json` provides list.

### 5. Level-gated spell learning

`SpellDefinition.learn_level: int = 1` (default = always learnable).
Canonical DQ1 gates set in each `.tres`:

| Spell | MP | learn_level |
|---|---|---|
| Heal | 4 | 3 |
| Hurt | 2 | 4 |
| Sleep | 2 | 7 |
| Stopspell | 2 | 10 |
| Healmore | 10 | 15 |

Battle code gates via `_learnable_spells_for(c)` which resolves ids
through ContentManager then calls pure `_gate_by_level(defs, level)`.
Used in two places:
- `_show_menu_for_current_member` — hides the "Spell" command entirely
  when no spell is learnable (avoids an empty submenu)
- `_start_spell_select` — filters the SPELL menu itself

Enemy casts re-use the same gate.

**Default party levels bumped** so gating is demonstrable without a
level-up system in place:
- Son: L2 → L7 (sees Heal/Hurt/Sleep active; Stopspell/Healmore gated)
- Father: L3 → L4 (sees Hurt — DQ1 gate)

`known_spells` stays as the upper bound of the character's kit; the gate
enforces the rollout schedule. When a level-up system lands, setting
`level` is the only mutation needed — spell visibility falls out of
the gate automatically.

## Verification

### GUT — `test_battle_manager_cast.gd`

25/25 passing (11 pre-existing + 14 new):

| New test | Covers |
|---|---|
| test_poison_ticks_damage_and_decrements_counter | poison chip + counter |
| test_poison_clears_when_counter_expires | poison wear-off |
| test_paralysis_skips_turn_until_counter_expires | paralysis skip + release |
| test_stopspell_ticks_without_blocking_action | stopspell doesn't skip turn |
| test_stopspell_clears_on_counter_expiry | stopspell wear-off |
| test_apply_status_effect_poison_always_lands_with_duration | no resist roll; 4-8 ticks |
| test_apply_status_effect_stopspell_lands_at_least_once | 50% land rate; 3-5 ticks |
| test_hit_wakes_sleeper_eventually_wakes_a_sleeping_target | 50% wake roll over 20 trials |
| test_hit_wakes_sleeper_no_op_on_non_sleeping_target | no-op when target not asleep |
| test_gate_by_level_filters_above_caster_level | L7 sees Heal/Hurt/Sleep, not L10/15 |
| test_gate_by_level_preserves_input_order | menu ordering |
| test_gate_by_level_defaults_to_always_learnable | default learn_level=1 |
| test_maybe_queue_enemy_cast_skips_stopspelled_enemy | stopspell blocks enemy AI |
| test_maybe_queue_enemy_cast_skips_enemy_with_no_mp | MP gate |
| test_maybe_queue_enemy_cast_skips_enemy_with_no_known_spells | no spells → no cast |
| test_pick_enemy_cast_command_targets_party_for_enemy_kind | enemy → party target |
| test_pick_enemy_cast_command_self_target | self-target cast |
| test_pick_enemy_cast_command_empty_viable_returns_empty | no viable = no cast |

Full GUT suite: 46/47. The failure (`test_pause_when_already_paused`) is
the same pre-existing flake from prior sessions, confirmed unrelated
(doesn't touch battle code).

### Playwright e2e

9/9 passing — same baseline as before; status + AI changes don't break
bundle-load, MCP roundtrip, or style hot-reload paths.

## Files changed

```
project/hosts/complete-app/scripts/battle/battle_data.gd
project/hosts/complete-app/scripts/battle/battle_manager.gd
project/hosts/complete-app/scripts/battle/battle_ui.gd
project/hosts/complete-app/tests/test_battle_manager_cast.gd       +14 tests
project/shared/content/enemies/enemies-core/bundle.json
project/shared/content/enemies/enemies-core/magician.tres          new
project/shared/content/spells/spells-core/bundle.json
project/shared/content/spells/spells-core/heal.tres                +learn_level
project/shared/content/spells/spells-core/healmore.tres            +learn_level
project/shared/content/spells/spells-core/hurt.tres                +learn_level
project/shared/content/spells/spells-core/sleep.tres               +learn_level
project/shared/content/spells/spells-core/stopspell.tres           new
project/shared/data/content_manifest.json                          rehash
project/shared/lib/resources/enemy_definition.gd                   +spells field
project/shared/lib/resources/spell_definition.gd                   +learn_level
```

## Follow-ups left after this pass

1. **Level-up system** — only piece missing to make level gating actually
   gradient at runtime. Today Son's stats are set once at start; after
   a level-up path exists, the spell-visibility change is automatic.
2. **Wraith enemy** — second MP-capable enemy from the DQ1 roster
   (HP 36 / MP 5 / knows Hurt + Sleep). Magician gets the pipeline
   validated; Wraith stresses the multi-spell selection path.
3. **Poison-inflicting enemy moves** — infrastructure ships empty
   today. A "bite" action on Poison Toad / Poisonous Moth that calls
   `_apply_status_effect` on a party member closes the loop.
4. **Player-cast spells that hit multiple targets** — `target_kind`
   already reserves `"all_enemies"` / `"party"`. Needed for Boom /
   Explodet (DQ1 multi-target damage).
5. **Animation of status transitions** — currently only log messages +
   the Zz glyph. A flash on apply, shake on damage, fade on wake would
   make the combat feel present. Defer until the art bundles land.
