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
def tmp_vault(tmp_path, sample_character_md, sample_location_md):
    """Create a temporary vault structure with sample pages."""
    world = tmp_path / "vault" / "world"
    (world / "characters").mkdir(parents=True)
    (world / "locations").mkdir(parents=True)
    (world / "characters" / "sera.md").write_text(sample_character_md, encoding="utf-8")
    (world / "locations" / "starlight-academy.md").write_text(sample_location_md, encoding="utf-8")
    return tmp_path
