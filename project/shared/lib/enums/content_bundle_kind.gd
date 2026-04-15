class_name ContentBundleKind
extends RefCounted

enum Kind { HUD, ENEMIES, NPCS, ITEMS, DIALOGUE, LOCATION }

const NAMES := {
    Kind.HUD: "hud",
    Kind.ENEMIES: "enemies",
    Kind.NPCS: "npcs",
    Kind.ITEMS: "items",
    Kind.DIALOGUE: "dialogue",
    Kind.LOCATION: "location",
}

static func from_string(name: String) -> int:
    for key in NAMES:
        if NAMES[key] == name:
            return key
    push_error("Unknown ContentBundleKind: %s" % name)
    return -1
