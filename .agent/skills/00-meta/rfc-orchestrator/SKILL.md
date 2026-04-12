---
name: rfc-orchestrator
description: Map RFC features to skill compositions and dispatch implementation phases. Use when starting work on an RFC, planning implementation order, or deciding which skills to compose for a feature. Acts as the production lead that translates game design into agent-executable plans.
category: 00-meta
layer: governance
related_skills:
  - "@context-discovery"
  - "@validation-guard"
  - "@skill-creator"
  - "@autoloop"
---

# RFC Orchestrator

This skill maps the project's 8 MVP RFCs to concrete skill compositions. Use it to determine **which skills to load**, **in what order**, and **what packages to create** when implementing an RFC feature.

## Workflow

1. Run `@context-discovery` pre-flight first
2. Identify the RFC(s) being implemented
3. Look up the skill matrix below for required skills
4. Compose the implementation plan following the phase order
5. After implementation, run `@validation-guard`

## Skill Matrix

Maps RFC features to the skills that implement them. Load all listed skills before starting work.

### RFC-001: Core Grid System
**Package:** `com.giantcroissant.game.grid` → `UltimaMagic.Grid`

| Skill | Why |
|---|---|
| `@unity-package-setup` | Scaffold the package structure |
| `@unity-scriptableobject-data` | TileDefinition, TerrainType data |
| `@unity-configurable-data` | Grid dimensions, tile sizes — never hardcode |
| `@unity-vcontainer` | Register GridService, IGridQuery |
| `@unity-messagepipe` | Publish GridLoadedMessage, TileChangedMessage |
| `@unity-unitask` | Async grid loading |
| `@unity-mcp` | Create scenes, GameObjects, test in editor |

### RFC-002: Game State Machine
**Package:** `com.giantcroissant.game.statemachine` → `UltimaMagic.StateMachine`

| Skill | Why |
|---|---|
| `@unity-package-setup` | Scaffold the package |
| `@unity-vcontainer` | Register GameStateManager, child scopes per state |
| `@unity-messagepipe` | StateTransitionMessage, RequestStateChangeMessage |
| `@unity-r3-reactive` | ReactiveProperty<GameState> for UI binding |
| `@unity-unitask` | Async state transitions with cancellation |
| `@unity-configurable-data` | Transition rules, allowed state paths |

### RFC-003: Overworld Movement
**Package:** `com.giantcroissant.game.traverse` → `UltimaMagic.Traverse`

| Skill | Why |
|---|---|
| `@unity-package-setup` | Scaffold the package |
| `@unity-input-system` | Traverse action map (Move cardinal, Interact, Menu) |
| `@unity-unitask` | Tween movement (~0.15s per tile) |
| `@unity-vcontainer` | Register TraverseController, CameraController |
| `@unity-messagepipe` | PlayerMovedMessage, EncounterTriggeredMessage |
| `@unity-configurable-data` | Move speed, encounter rates per terrain |
| `@unity-mcp` | Scene setup, orthographic camera, test |

### RFC-004: First-Person Dungeon
**Package:** `com.giantcroissant.game.explore` → `UltimaMagic.Explore`

| Skill | Why |
|---|---|
| `@unity-package-setup` | Scaffold the package |
| `@unity-input-system` | Explore action map (Move, Strafe, Turn, Interact) |
| `@unity-unitask` | Tween movement (~0.2s per step) |
| `@unity-vcontainer` | Register ExploreController, ExploreRenderer |
| `@unity-messagepipe` | PlayerSteppedMessage, ExploreEnteredMessage |
| `@unity-configurable-data` | Step duration, FOV, render distance |
| `@unity-mcp` | 3D geometry setup (cubes/planes for walls/floors) |

### RFC-005: Combat System
**Package:** `com.giantcroissant.game.combat` → `UltimaMagic.Combat`

| Skill | Why |
|---|---|
| `@unity-package-setup` | Scaffold the package |
| `@unity-scriptableobject-data` | EnemyDefinition, SpellDefinition, ActionDefinition |
| `@unity-configurable-data` | Damage formulas, initiative calc, XP tables |
| `@unity-vcontainer` | Register CombatManager, TurnResolver, DamageCalculator |
| `@unity-messagepipe` | ActionSelectedMessage, DamageDealtMessage, CombatEndedMessage |
| `@unity-r3-reactive` | HP/MP as ReactiveProperty for live UI updates |
| `@unity-unitask` | Async turn resolution, action animations |
| `@unity-uitoolkit` | Combat action selection UI |

### RFC-006: Party & Character System
**Package:** `com.giantcroissant.game.party` → `UltimaMagic.Party`

| Skill | Why |
|---|---|
| `@unity-package-setup` | Scaffold the package |
| `@unity-scriptableobject-data` | CharacterClassDefinition, StatDefinition, ItemDefinition |
| `@unity-configurable-data` | Level-up tables, stat growth curves |
| `@unity-vcontainer` | Register PartyManager, InventoryService |
| `@unity-messagepipe` | PartyChangedMessage, ItemAcquiredMessage |
| `@unity-r3-reactive` | Character stats as ReactiveProperty for UI |

### RFC-007: UI System
**Package:** `com.giantcroissant.game.ui` → `UltimaMagic.UI`

| Skill | Why |
|---|---|
| `@unity-package-setup` | Scaffold the package |
| `@unity-uitoolkit` | All screens: HUD, Combat, Dialogue, Menu, Title |
| `@unity-r3-reactive` | Data binding to game state |
| `@unity-vcontainer` | Register UIManager, inject into screen controllers |
| `@unity-messagepipe` | Subscribe to state changes for screen swapping |
| `@unity-unitask` | Async screen transitions (ShowAsync/HideAsync) |
| `@unity-mcp` | Create UXML/USS assets, preview in editor |

### RFC-008: MVP Roadmap
**Role:** Integration plan — not a package itself, but defines the implementation order.

## Implementation Phases

From RFC-008, the build order is:

### Phase 1 — Foundation
1. `RFC-001` Core Grid System
2. `RFC-002` Game State Machine
3. `RFC-006` Party & Character System (data layer only)
4. `RFC-007` UI System (UIManager skeleton + Title screen)

### Phase 2 — Overworld Loop
5. `RFC-003` Overworld Movement
6. `RFC-007` UI: TraverseHUD
7. Integration: walk on grid → trigger encounters

### Phase 3 — Combat Loop
8. `RFC-005` Combat System
9. `RFC-007` UI: CombatUI
10. Integration: encounter → combat → victory/defeat → return to overworld

### Phase 4 — Dungeon Loop
11. `RFC-004` First-Person Dungeon
12. `RFC-007` UI: ExploreHUD
13. Integration: enter dungeon tile → first-person explore → encounter → combat

### Phase 5 — Polish & Integration
14. `RFC-006` Party: full inventory, equipment
15. `RFC-007` UI: GameMenuUI, DialogueOverlay
16. Full vertical slice playthrough

## Composition Pattern

When implementing any RFC, the agent loop is:

```
1. @context-discovery          → produce ContextReport
2. @rfc-orchestrator           → look up skill matrix for the RFC
3. Load required skills        → read SKILL.md for each
4. @unity-package-setup        → scaffold package (if new)
5. Implement feature           → using loaded skill patterns
6. @validation-guard           → verify compliance
7. @unity-mcp                  → test in editor
```

## Autonomous Implementation Loop (via @autoloop)

When the user signals autonomous mode (e.g., "implement RFC-001", "build the grid system"), engage the `@autoloop` protocol for hands-free implementation:

### Setup
```
1. Create branch: autoloop/rfc<NNN>-<name> from main
2. Run @context-discovery → produce ContextReport
3. Look up skill matrix for the target RFC
4. Decompose the RFC into ordered implementation tasks
5. Establish baseline: clean compile, zero tests, no package yet
6. Initialize results.tsv
```

### Loop (NEVER STOP until phase complete)
```
FOR EACH task in the RFC decomposition:
  1. Plan    — pick the next task (one focused change)
  2. Code    — implement using loaded skill patterns
  3. Commit  — git add + commit with descriptive message
  4. Compile — read_console(filter_type="Error") > compile.log
               grep for errors only (protect context window)
  5. Validate — run @validation-guard (inline, not full report)
  6. Decide:
     - COMPILES + VALIDATES → KEEP (advance branch)
     - COMPILE ERROR → attempt fix (max 3 tries), then DISCARD
     - VALIDATION FAIL (BLOCK) → attempt fix, then DISCARD
     - VALIDATION FAIL (WARN) → KEEP but log the warning
  7. Log     — append to results.tsv
  8. Continue to next task
```

### Task Decomposition Example (RFC-001 Grid)
```
1. Scaffold package structure (com.giantcroissant.grid)
2. Define GridPosition, TileType enums, TerrainType
3. Define TileDefinition ScriptableObject
4. Implement GridMap data structure (2D array)
5. Implement GridService with IGridQuery interface
6. Register in LifetimeScope
7. Add MessagePipe messages (GridLoadedMessage, TileChangedMessage)
8. Create test scene with sample grid
9. Write EditMode tests for GridMap
```

Each step is one autoloop iteration: implement → commit → compile → validate → keep/discard.

### Context Window Rules
- Redirect compile output: `read_console(filter_type="Error")` only
- Don't dump full scene hierarchies — use `page_size=50` and stop early
- Keep only: current task, compile status, validation result, next task
- Log everything else to results.tsv

### Completion
When all tasks are done:
1. Run full `@validation-guard` report
2. Run tests via `@unity-mcp`
3. Log final state to results.tsv
4. Report summary to user
5. Branch is ready for merge or PR

## Related Skills

- `@autoloop` (00-meta) — autonomous loop infrastructure (keep/discard cycle, git branching, context management)
- `@context-discovery` (00-meta) — mandatory pre-flight before implementation
- `@validation-guard` (00-meta) — mandatory post-flight after implementation
- `@skill-creator` (00-meta) — create new skills if gaps are found during implementation
