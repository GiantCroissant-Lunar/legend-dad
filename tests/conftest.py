import json
from pathlib import Path

import pytest

SCHEMA_PATH = Path(__file__).parent.parent / "project" / "articy" / "schemas" / "import-manifest.schema.json"


@pytest.fixture()
def schema():
    with open(SCHEMA_PATH) as f:
        return json.load(f)


@pytest.fixture()
def sample_character_md():
    return """\
---
type: character
status: draft
articy-id: ""
tags: [protagonist]
connections:
  - "[[Elder Aldric]]"
era: "Age of Starlight"
last-agent-pass: "2026-04-12"
---

# Sera

## Overview

A young scholar from the Academy of Starlight.

## Backstory

Sera grew up in the shadow of the Academy.

## Personality & Motivation

Curious, cautious, fiercely loyal to her mentor.

## Relationships

- [[Elder Aldric]] \u2014 her mentor at the Academy
- [[Starlight Academy]] \u2014 her faction

## Creative Prompts

### portrait

16-bit pixel art, grayscale base with palette-swap tinting. Young woman with short dark hair, wearing scholar robes. Expression is thoughtful, slightly guarded. Warm amber lighting from a desk lamp.

### voice

Soft-spoken, measured cadence, slight tremor when discussing the Academy. Mid-range pitch, educated vocabulary but not pretentious.

### theme-music

Melancholic piano melody in A minor, builds from single notes to gentle chords. Evokes studying alone in a vast library at night.
"""


@pytest.fixture()
def sample_location_md():
    return """\
---
type: location
status: draft
articy-id: ""
tags: [academy, hub]
connections:
  - "[[Sera]]"
era: "Age of Starlight"
last-agent-pass: "2026-04-12"
---

# Starlight Academy

## Overview

An ancient academy perched on a cliff overlooking the Moonlit Sea.

## Atmosphere & Appearance

Towering spires of white stone, perpetually bathed in starlight.

## History

Founded in the First Era by the Starweavers.

## Notable Features

- The Great Library \u2014 largest collection of star charts
- The Observatory \u2014 where students study celestial patterns

## Creative Prompts

### environment-art

16-bit pixel art, grayscale base with palette-swap tinting. Towering white stone academy on a cliff edge, night sky filled with stars. Warm light glowing from tall arched windows. Sense of ancient knowledge and quiet grandeur.

### ambience

Gentle wind, distant waves crashing on cliffs below, faint sound of turning pages, occasional bell chime from a tower.

### music

Ethereal strings and soft choir, key of D major, slow tempo. Evokes wonder and the vastness of accumulated knowledge.
"""


@pytest.fixture()
def sample_bestiary_md():
    return """\
---
type: bestiary
status: draft
articy-id: ""
tags: [insectoid, son-era]
connections:
  - "[[Iron Peaks]]"
era: "Son"
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
last-agent-pass: "2026-04-16"
---

# Crystal Crawler

## Overview

A crystalline insectoid found deep in Iron Peaks.

## Ecology & Habitat

Thrives in mineral-rich cave systems.

## Behavior

Hunts in swarms, using resonance pulses to disorient prey.

## Lore & Cultural Significance

Miners consider them a sign of rich ore veins nearby.

## Creative Prompts

### creature-art

16-bit pixel art crystalline beetle with glowing facets.

### sound-design

Chittering clicks with crystalline resonance.
"""


@pytest.fixture()
def sample_zone_md():
    return """\
---
type: zone
status: draft
articy-id: ""
tags: [forest, starter]
connections:
  - "[[Whispering Woods]]"
era: "Both"
encounter_table:
  - bestiary: "[[Moss Lurker]]"
    weight: 4
    era: "son"
  - bestiary: "[[Thornbriar Stalker]]"
    weight: 1
    era: "son"
encounter_rate: 0.12
difficulty_tier: 2
last-agent-pass: "2026-04-16"
---

# Whispering Woods Edge

## Overview

The outer fringe of the ancient Whispering Woods.

## Layout & Terrain

Dense undergrowth gives way to towering oaks.

## Entities & Encounters

Moss Lurkers hide among fallen logs.

## Era Variants

Father era: peaceful. Son era: corrupted.

## Creative Prompts

### tilemap-art

16-bit forest tiles, dappled sunlight through canopy.

### ambience

Rustling leaves, distant bird calls, occasional crack of twigs.

### music

Gentle woodwind melody shifting to minor key for encounters.
"""


@pytest.fixture()
def sample_location_with_tier_md():
    return """\
---
type: location
status: draft
articy-id: ""
tags: [forest]
connections: []
era: "Both"
recommended_level_min: 2
recommended_level_max: 5
difficulty_tier: 2
last-agent-pass: "2026-04-16"
---

# Whispering Woods

## Overview

A vast ancient forest stretching south of Thornwall.

## Atmosphere & Appearance

Towering oaks with thick canopy filtering sunlight.

## History

Once home to the Forest Wardens before the corruption.

## Notable Features

- The Heartwood — an ancient tree at the center
- The Overgrown Path — half-hidden trail to deeper woods

## Creative Prompts

### environment-art

16-bit forest landscape with ancient trees.

### ambience

Wind through leaves, distant water sounds.

### music

Mysterious woodland theme in D minor.
"""


@pytest.fixture()
def tmp_vault(tmp_path, sample_character_md, sample_location_md):
    """Create a temporary vault structure with sample pages."""
    world = tmp_path / "vault" / "world"
    (world / "characters").mkdir(parents=True)
    (world / "locations").mkdir(parents=True)
    (world / "characters" / "sera.md").write_text(sample_character_md, encoding="utf-8")
    (world / "locations" / "starlight-academy.md").write_text(sample_location_md, encoding="utf-8")
    return tmp_path
