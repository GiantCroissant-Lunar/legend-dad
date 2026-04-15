---
date: 2026-04-15
agent: claude-code
branch: main
version: 0.1.0-280
tags: [dev-log, content-manager, enemies, dq1, bundle, refactor]
---

# Session Dev-Log — First Non-HUD Content Bundle (`enemies-core`)

Populates the first non-HUD content bundle the content-runtime-split
work scaffolded for but never filled in. Retires the hardcoded
`BattleData.ENEMIES` dict in favor of `.tres` definitions loaded through
`ContentManager.get_enemy_definition(id)` — closes a direct violation of
the project rule in `AGENTS.md` about hardcoded tunable constants, and
delivers the second data-driven hot-reload surface after `hud-core`.

## What landed

### Bundle

`project/shared/content/enemies/enemies-core/`

```
bundle.json                 kind=enemies, policy=eager
slime.tres                  port from BattleData.ENEMIES
bandit.tres                 port
wolf.tres                   port
skeleton.tres               DQ1 (mid-game undead, HP 30 / ATK 12 / DEF 6)
dracky.tres                 DQ1 (early fast bat variant)
metal_scorpion.tres         DQ1 (desert, high SPD)
```

Six enemies: three ports keep save-compat with existing encounter code,
three new ones introduce DQ1's early-game roster. Stats are scaled to
the current 12–30 HP / 4–12 ATK band (the project is pre-balance — DQ1's
NES-authentic values would be out of range) but relative tiers preserve
the DQ1 progression feel.

### Resource schema

`project/shared/lib/resources/enemy_definition.gd` extended to cover
every field the battle code needs. Field names stay readable on the
Resource side (`attack`, `defense`, `xp_reward`, `gold_reward`,
`tint_color`) and a `to_combat_dict()` helper maps them to the shape
`Combatant.from_dict` already expects (`atk`/`def`/`exp`/`gold`/`color`).

### Wire-up

`main.gd`:
- `_spawn_enemy` — reads `tint_color` from the enemy def instead of
  `BattleData.ENEMIES[id].color`. Push-warning'd fallback to a safe
  default if the id isn't in the loaded bundle.
- `_start_battle` — constructs the enemy `Combatant` via
  `enemy_def.to_combat_dict()`. Falls back to slime if the id resolves
  to null so a typo can't wedge combat.
- Seed spawns now include one of the DQ1 additions (`dracky`,
  `skeleton`) so the new content is actually playable on boot.

`battle_data.gd`:
- Dropped `ENEMIES` dict and its embedded Color literals.
- Player/ally stats and `calc_damage` / `calc_flee_chance` retained —
  no hot-iteration need for those yet.

`c_enemy.gd` comment updated to point at the bundle convention.

## Verification

Full e2e suite: **8 passed**.

Notable lines from lazy-bundle-load.spec.js:

```
[ContentManager] fetching http://localhost:7601/pck/hud-core@09edde.pck
[ContentManager] fetched hud-core@09edde.pck in 166 ms
[ContentManager] fetching http://localhost:7601/pck/enemies-core@463b56.pck
[ContentManager] fetched enemies-core@463b56.pck in 228 ms
[ContentManager] fetching http://localhost:7601/pck/hud-battle@b9d664.pck
[ContentManager] fetched hud-battle@b9d664.pck in 232 ms
```

- `enemies-core` fetched at boot (new eager bundle)
- Player successfully engaged combat → `get_enemy_definition("dracky")`
  (or whichever the interact-path enemy resolved to) returned a valid
  def → `to_combat_dict()` fed Combatant → battle manager advanced.

Visual spot-check preserved at
`vault/references/visual-qa-experiment/2026-04-15-enemies-core-spotcheck.png`:
entity count 7 (2 players + 3 enemies + 2 boulders), green slime + bone
skeleton visible in the overworld tilemap. Dracky is at (7, 6), probably
behind tileset terrain — entity count confirms it spawned.

## Iteration loop

Same pattern as HUD styles:

```
edit slime.tres (e.g. bump max_hp, change tint)
task content:build -- enemies-core
F9
```

Overworld tint updates via `_spawn_enemy` (fires on scene construction
only — page reload required to re-spawn with new tint). Combat stats
propagate the next time `_start_battle` runs (next encounter).

If we want a fully live overworld-tint loop, `_spawn_enemy` would need
to hook `bundle_loaded` for `enemies-core` and re-apply tint to existing
visuals. Filed as a follow-up — not needed for the first slice.

## Scope notes

- **Spells deferred.** No spell system exists in the battle code
  (searched `project/hosts/complete-app/scripts/battle/` — no cast /
  mp_cost / magic). Porting the 10 DQ1 spell notes into a `spells-core`
  bundle would only create unreferenced data. When the battle system
  grows a cast action, pair that change with the bundle in one session.
- **Beehave behavior tree field** on `EnemyDefinition` is declared but
  unused — kept forward-compat with the notes on DQ1's eventual
  behavior patterns.
- `EnemyDefinition` currently has no `spells: Array[SpellDefinition]`
  field. Will add when `SpellDefinition` exists.

## Files changed

```
project/shared/lib/resources/enemy_definition.gd       extended schema + to_combat_dict
project/shared/content/enemies/enemies-core/           new bundle, 6 .tres + bundle.json
project/hosts/complete-app/scripts/main.gd             ContentManager wire-up, DQ1 spawns
project/hosts/complete-app/scripts/battle/battle_data.gd   removed ENEMIES dict
project/hosts/complete-app/ecs/components/c_enemy.gd   doc comment refresh
project/shared/data/content_manifest.json              regenerated (3 bundles)
vault/references/visual-qa-experiment/                 spot-check PNG
```
