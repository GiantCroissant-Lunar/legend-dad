---
date: 2026-04-15
agent: claude-code
branch: main
version: 0.1.0-282
tags: [dev-log, battle, input, spells, dq1, status-effects, refactor]
---

# Session Dev-Log — Battle Input Refactor + Healmore + Sleep

Two bundled changes:

1. **Battle menu input → event-driven.** Moved all
   `Input.is_action_just_pressed(...)` polling out of `_process_command`
   / `_process_spell_select` / `_process_target_select` /
   `_process_victory` / `_process_defeat` / `_process_flee` into a
   single `_input(event)` dispatcher with per-state handlers. The menu
   stays responsive even when `_process` is throttled (browser tab
   background, frame hitches).

2. **Two more DQ1 spells** landed, powered by a minimal status-effect
   system: **Healmore** (MP 10, +85-100 HP self — trivial extension of
   the existing heal path) and **Sleep** (MP 2, ~65% land rate,
   2-4 turn duration, ~33% random wake per tick + forced wake on
   counter=0). 4 DQ1 spells total now: Heal, Hurt, Healmore, Sleep.

## Input refactor details

### Before → after

| Old (polling) | New (event-driven) |
|---|---|
| `_process_command(delta)` polled Input | `_handle_command_event(event)` called from `_input` |
| `_process_spell_select(delta)` polled Input | `_handle_spell_select_event(event)` |
| `_process_target_select(delta)` polled Input | `_handle_target_select_event(event)` |
| `_process_victory/defeat/flee(delta)` ticked timer + polled Input | Timer ticked in main `_process`; input in `_handle_end_event` / `_handle_flee_event` |
| `_process(delta)` dispatched to all the above | `_process(delta)` now only ticks timers; `_input(event)` dispatches input |

### Why `_input` (not `_unhandled_input`)

Tried `_unhandled_input` first. Events never reached the battle manager
under that handler — likely because something further up the tree (GUI
focus routing on the battle_overlay Control, or an addon like GUIDE)
consumes key events before they become "unhandled." `_input` fires
earlier in the pipeline, with the same visibility guarantee for
keyboard events that `Input.is_action_just_pressed` had.

### What this buys in practice

- Real players on machines with frame drops still get responsive menu
  input. Previously, any frame-skip could drop a press.
- `INPUT_COOLDOWN` still enforces the 150ms debounce — kept the same
  feel for users, just event-driven underneath.
- Doesn't require any of the ui_* InputMap bindings added last session
  to still be present, but they continue to work (the refactored
  handlers use `event.is_action_pressed("ui_down")` etc).

### What it does NOT fix

Chrome-headed Playwright can't reliably drive the menu via keyboard
under tab-focus throttling. After the first keystroke post-menu-open,
subsequent presses are dropped — whether via Playwright's `.keyboard`,
direct `dispatchEvent`, or clicking canvas between presses.
`task test:godot`'s GUT suite is the authoritative integration test for
cast flow math. The `cast-spell.spec.js` e2e spec stays scoped to
bundle-load + menu-presence assertions; the cast resolution itself is
covered by `tests/test_battle_manager_cast.gd` (11 tests now).

## Status-effect infrastructure

Minimal, first slice:

- `Combatant.status_effects: Dictionary` — `{status_id → turns_remaining}`.
  Currently only `"sleep"` is implemented; the shape generalizes to
  poison, stun, stopspell, etc. without schema churn.
- `BattleManager._tick_status_effects(actor) -> bool` — called at the
  start of each actor's resolve step. Returns `false` to skip the
  action (e.g. still asleep). Handles random wake (~33% per tick) and
  forced wake when counter hits 0. Extracted for GUT testing.
- `BattleManager._apply_status_effect(target, spell)` — called from
  `_apply_cast` when `spell.effect_kind == "status"`. Dispatches on
  `spell.status_effect` (sleep, …). Returns `true`/`false` so the
  caster can see whether it landed.
- Spell `.tres` schema already carried `effect_kind` + `status_effect`
  from the first-slice design. Sleep uses `effect_kind="status"`,
  `status_effect="sleep"`, `power_min/max=0`.

### DQ1 fidelity vs scope

- Sleep landing rate: 65% (DQ1 is infamously unreliable; this is in the
  right ballpark and tunable per-spell in a future rev).
- Sleep duration: 2-4 turns, with random wake each tick. Matches the
  "unreliable lock" feel.
- No "lost wake to attack" mechanic yet (DQ: hitting a sleeper sometimes
  wakes them). Filed for later.
- No status indicator in the battle overlay UI — just the `_add_message`
  log line ("Slime falls asleep!", "is still asleep", "wakes up!").

## Verification

### GUT — `test_battle_manager_cast.gd`

11 tests now (6 original + 5 new), all passing:

| Test | What it locks down |
|---|---|
| test_heal_deducts_mp_and_restores_hp | heal math + MP cost |
| test_heal_clamps_at_max_hp | heal can't over-restore |
| test_hurt_deducts_mp_and_damages_enemy_bypassing_defense | DQ1 magic bypasses defense |
| test_insufficient_mp_returns_false_and_spends_nothing | MP shortfall guard |
| test_null_spell_is_safely_rejected | null-spell early return |
| test_damage_spell_redirects_when_target_already_dead | mid-turn death redirect |
| **test_sleep_sets_status_effect_on_landing** | Sleep spell consumes MP |
| **test_apply_status_effect_sleep_sets_turn_counter** | on landing, 2-4 turn counter is set |
| **test_tick_status_effects_asleep_actor_skipped_until_wake** | sleep skips the actor's turn |
| **test_tick_status_effects_forces_wake_when_counter_expires** | counter=1 → wake next tick |
| **test_tick_status_effects_no_status_returns_can_act** | no status → actor acts freely |

Full GUT suite: 28/29 passing. The remaining failure
(`test_pause_when_already_paused`) is a pre-existing flake unrelated to
this session, confirmed by `git stash && task test:godot` on a clean
main.

### Playwright e2e

9/9 passing (same set as last session, plus cast-spell's bundle+menu
assertions which still hold after the refactor).

## Files changed

```
project/hosts/complete-app/scripts/battle/battle_manager.gd   input refactor + _tick_status_effects + _apply_status_effect
project/hosts/complete-app/scripts/battle/combatant.gd        status_effects field
project/hosts/complete-app/scripts/battle/battle_data.gd      Son gains healmore + sleep
project/hosts/complete-app/tests/test_battle_manager_cast.gd  +5 GUT tests
project/shared/content/spells/spells-core/healmore.tres       new (MP 10, 85-100 heal)
project/shared/content/spells/spells-core/sleep.tres          new (MP 2, status)
project/shared/content/spells/spells-core/bundle.json         provides list updated
project/shared/data/content_manifest.json                     rebuild hash bump
```

## Follow-ups

1. **Status indicator UI** — render a "Zz" sprite on sleeping enemies
   in the battle overlay. Trivial once there's demand for visual
   feedback beyond the log line.
2. **Hit-wakes-sleeper** — DQ1 has ~50% chance that attacking a sleeper
   wakes them early. Small addition to `_resolve_turn` — fold it into
   the attack case after damage lands.
3. **More status effects** — poison (tick damage), stopspell (block
   MP actions), paralysis. Schema generalizes; just add cases.
4. **Enemy-side casts** — `SpellDefinition.max_mp`-using enemies
   (Magician, Wraith) when those land in `enemies-core`. The current
   resolve loop queues enemy attacks in a separate step; extending it
   to sometimes queue a cast instead is a small AI selection function.
5. **Level-gated spell learning** — DQ1's canonical Lv 3/4/7/15
   thresholds for Heal/Hurt/Sleep/Healmore. Pair with a level-up
   system when that lands.
