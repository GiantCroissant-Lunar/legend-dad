---
type: bestiary
status: draft
articy-id: "72057594037929564"
tags: [ghost, spectral, ambient, all-locations, light]
connections:
  - "[[Thornwall]]"
  - "[[Whispering Woods]]"
  - "[[Iron Peaks]]"
era: "Both"
battle_stats:
  max_hp: 10
  max_mp: 12
  atk: 4
  def: 2
  spd: 12
  level: 4
  xp_reward: 12
  gold_reward: 6
actions:
  - id: "chill_touch"
    kind: "attack"
    frequency: 0.5
    power_min: 3
    power_max: 5
    target_kind: "enemy"
  - id: "whispered_curse"
    kind: "status_inflict"
    frequency: 0.3
    status_effect: "sleep"
    target_kind: "enemy"
  - id: "fade"
    kind: "status_inflict"
    frequency: 0.2
    status_effect: "stopspell"
    target_kind: "enemy"
group_size_min: 2
group_size_max: 4
zone_affinity:
  - "[[Whispering Woods Deep]]"
last-agent-pass: "2026-04-16"
---

# Shade Wisp

## Overview

The Shade Wisp is a small, ghostly entity that manifests as a flickering sphere of pale light surrounded by wisps of shadow that trail behind it like dark smoke. No larger than a clenched fist, it drifts silently through dark spaces -- shadowed forest clearings, unlit mine tunnels, and the dim alleys of Thornwall after nightfall. Its light shifts between cold blue-white and a sickly amber depending on its state, and it moves with a drifting, moth-like unpredictability.

In Kaelen's era, Shade Wisps were a familiar and largely harmless phenomenon. Travellers knew them as corpse-candles, fool's lanterns, or simply "the little lights." They appeared most often near places where the boundary between the living world and something older felt thin -- old graveyards, ruined shrines, the deepest parts of the Whispering Woods. Following one was considered foolish, as they tended to lead the unwary into bogs or off trail edges, but they posed no direct physical threat.

By Aric's time, the wisps have changed. They appear in far greater numbers, their light burns hotter and more erratic, and they have developed an aggressive territoriality. A single wisp remains little more than a nuisance, but clusters of them can drain the vitality of living creatures, leaving victims cold and exhausted. The transformation is one of the most visible signs that something fundamental has shifted in the land's spiritual fabric.

## Ecology & Habitat

Shade Wisps are not biological creatures in any conventional sense. They appear to be manifestations of residual spiritual energy -- echoes left behind by the dead, by old magic, or by the land itself. They are most commonly found in locations with strong connections to the past: battlefields, abandoned settlements, the roots of ancient trees, and the deepest galleries of the Iron Peaks where the oldest rock is exposed.

They are drawn to darkness and repelled by strong natural light, which is why they are rarely seen during full daylight hours. Artificial light affects them differently -- a lantern or torch does not drive them away but instead seems to agitate them, causing their movements to become more rapid and erratic. In the Son's era, wisps have been observed congregating around the fracture points where the land is splitting, forming dense clouds of flickering light that miners and travellers have learned to avoid.

## Behavior

In JRPG encounters during the Father's era, Shade Wisps typically do not initiate combat. They may appear as environmental elements during exploration, adding atmosphere. If provoked or cornered, a single wisp uses **Flicker Touch**, a weak cold-elemental attack that deals minor damage and may cause the Chill status.

In the Son's era, wisps are hostile and appear in swarms of four to eight. Their primary threat is **Vitality Drain**, a magical attack that saps HP and transfers a portion to other wisps in the group, making them difficult to wear down individually. Their most dangerous ability is **Shade Convergence**: when enough wisps are present, they merge temporarily into a **Shade Wraith**, a larger spectral form with significantly higher stats and the ability to use **Soul Chill**, a party-wide cold and dark elemental attack that can inflict the Dread status, reducing the party's attack power. Defeating the wraith causes it to split back into weakened individual wisps.

## Lore & Cultural Significance

Every region has its own relationship with the Shade Wisps. In Thornwall, they are called "the watch-fires of the dead" and are believed to be the spirits of those who died defending the town in ages past, still walking their old patrols. It is considered respectful to bow when one passes and deeply unlucky to swat at them. In the Whispering Woods, foresters know them as "path-takers" and believe they are the forest's way of testing whether a traveller belongs -- those who follow a wisp and find their way back are said to have the forest's blessing.

The miners of Iron Peaks have the most practical view: they call them "gas-ghosts" and originally assumed they were a luminous effect caused by underground vapours. This theory was never satisfying, given that the wisps move with apparent intent, but it was preferable to the alternative. The wisps' transformation into aggressive entities in Aric's era has forced a reckoning with the spiritual explanations that the rational-minded miners long dismissed. Whatever the wisps truly are, their agitation seems to mirror the land's own distress, as though the energy that once rested quietly in dark places has been stirred awake and cannot find peace.

## Creative Prompts

### Creature Art

16-bit pixel art of a small floating sphere of pale ghostly light roughly fist-sized with trailing tendrils of dark shadow streaming behind it, animated with a gentle bobbing drift and flickering light that shifts between cold blue-white and dim amber, translucent and slightly see-through against a dark background, with subtle particle effects of tiny motes swirling around the core, shown in both a calm passive state and an agitated aggressive state with brighter erratic light and sharper shadow trails, JRPG sprite style

### Sound Design

Soft ethereal humming tone that wavers in pitch like a distant singing voice heard through water, layered with faint whispering just below the threshold of intelligibility, a gentle chime-like tinkling for passive movement, transitioning to a sharper discordant buzzing drone when aggressive, the Vitality Drain ability should sound like a slow inhale of breath combined with crystalline wind-chime decay, and Soul Chill should be a deep resonant chord that drops in temperature-evoking low frequencies
