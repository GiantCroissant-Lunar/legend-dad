"""Convert vault/world/ markdown pages into an articy import manifest."""

from __future__ import annotations

import argparse
import hashlib
import json as json_mod
import re
import sys
from datetime import UTC, datetime
from pathlib import Path

import yaml


def parse_vault_page(text: str) -> dict:
    """Parse a vault markdown page into frontmatter dict and content string."""
    if not text.startswith("---"):
        return {"frontmatter": {}, "content": text}
    parts = text.split("---", 2)
    if len(parts) < 3:
        return {"frontmatter": {}, "content": text}
    frontmatter = yaml.safe_load(parts[1]) or {}
    content = parts[2].strip()
    return {"frontmatter": frontmatter, "content": content}


def extract_sections(content: str) -> dict[str, str]:
    """Split markdown content into a dict keyed by ## heading name."""
    sections: dict[str, str] = {}
    current_heading = None
    current_lines: list[str] = []

    for line in content.split("\n"):
        h2_match = re.match(r"^## (.+)$", line)
        if h2_match:
            if current_heading is not None:
                sections[current_heading] = "\n".join(current_lines).strip()
            current_heading = h2_match.group(1).strip()
            current_lines = []
        elif current_heading is not None:
            current_lines.append(line)

    if current_heading is not None:
        sections[current_heading] = "\n".join(current_lines).strip()

    return sections


def extract_creative_prompts(creative_section: str) -> dict[str, str]:
    """Extract ### sub-headings from the Creative Prompts section."""
    prompts: dict[str, str] = {}
    current_key = None
    current_lines: list[str] = []

    for line in creative_section.split("\n"):
        h3_match = re.match(r"^### (.+)$", line)
        if h3_match:
            if current_key is not None:
                prompts[current_key] = "\n".join(current_lines).strip()
            current_key = h3_match.group(1).strip()
            current_lines = []
        elif current_key is not None:
            current_lines.append(line)

    if current_key is not None:
        prompts[current_key] = "\n".join(current_lines).strip()

    return prompts


_TEMPLATE_SECTIONS = {
    "Overview": "overview",
    "Layout & Terrain": "layout_and_terrain",
    "Entities & Encounters": "entities_and_encounters",
    "Era Variants": "era_variants",
    "Backstory": "backstory",
    "Personality & Motivation": "personality_and_motivation",
    "Atmosphere & Appearance": "atmosphere_and_appearance",
    "History": "history",
    "Notable Features": "notable_features",
    "Purpose & Goals": "purpose_and_goals",
    "Hierarchy & Structure": "hierarchy_and_structure",
    "Territory & Influence": "territory_and_influence",
    "Narrative Arc": "narrative_arc",
    "Objectives & Stakes": "objectives_and_stakes",
    "Branching Points": "branching_points",
    "Lore & Origin": "lore_and_origin",
    "Purpose & Usage": "purpose_and_usage",
    "Causes": "causes",
    "Consequences": "consequences",
    "Involved Entities": "involved_entities",
    "Details": "details",
    "Cultural Significance": "cultural_significance",
    "Ecology & Habitat": "ecology_and_habitat",
    "Behavior": "behavior",
    "Lore & Cultural Significance": "lore_and_cultural_significance",
}

_LINK_PATTERN = re.compile(r"\[\[([^\]]+)\]\]")


def _extract_display_name(content: str) -> str:
    """Extract the H1 heading as display name."""
    for line in content.split("\n"):
        m = re.match(r"^# (.+)$", line)
        if m:
            return m.group(1).strip()
    return ""


def _parse_obsidian_links(frontmatter_connections: list) -> list[dict]:
    """Convert frontmatter connection strings like '[[Name]]' into connection dicts."""
    connections = []
    for entry in frontmatter_connections:
        for match in _LINK_PATTERN.finditer(str(entry)):
            connections.append(
                {
                    "target_vault_path": match.group(1),
                    "relation": "related_to",
                }
            )
    return connections


def _extract_dialogue_hooks(sections: dict[str, str]) -> list[str]:
    """Extract dialogue hooks from Relationships/Branching Points sections."""
    hooks = []
    for key in ("Relationships", "Branching Points"):
        text = sections.get(key, "")
        for line in text.split("\n"):
            line = line.strip()
            if line.startswith("- ") and "\u2014" in line:
                hooks.append(line.lstrip("- "))
    return hooks


def build_entity(text: str, vault_path: str) -> dict:
    """Build a manifest entity dict from raw vault page text."""
    page = parse_vault_page(text)
    fm = page["frontmatter"]
    sections = extract_sections(page["content"])

    template_props = {}
    for heading, key in _TEMPLATE_SECTIONS.items():
        if heading in sections:
            template_props[key] = sections[heading]

    creative_section = sections.get("Creative Prompts", "")
    creative_prompts = extract_creative_prompts(creative_section)

    connections = _parse_obsidian_links(fm.get("connections", []))
    dialogue_hooks = _extract_dialogue_hooks(sections)

    return {
        "vault_path": vault_path,
        "articy_id": fm.get("articy-id", ""),
        "type": fm.get("type", ""),
        "status": "new",
        "display_name": _extract_display_name(page["content"]),
        "template_properties": template_props,
        "connections": connections,
        "creative_prompts": creative_prompts,
        "dialogue_hooks": dialogue_hooks,
        "flow_notes": sections.get("Branching Points", ""),
    }


_TYPE_DIRS = {
    "characters": "character",
    "locations": "location",
    "zones": "zone",
    "factions": "faction",
    "quests": "quest",
    "items": "item",
    "history": "event",
    "lore": "lore",
    "bestiary": "bestiary",
}


def generate_manifest(vault_world: Path) -> dict:
    """Scan vault/world/ and build a complete import manifest."""
    entities = []

    for dir_name, _entity_type in _TYPE_DIRS.items():
        type_dir = vault_world / dir_name
        if not type_dir.is_dir():
            continue
        for md_file in sorted(type_dir.glob("*.md")):
            if md_file.name.startswith("_") or md_file.name == "timeline.md":
                continue
            text = md_file.read_text(encoding="utf-8")
            vault_path = f"vault/world/{dir_name}/{md_file.name}"
            entity = build_entity(text, vault_path)
            entities.append(entity)

    return {
        "version": "0.1.0",
        "generated": datetime.now(UTC).isoformat(),
        "generated_by": "vault_to_manifest",
        "entities": entities,
    }


def _entity_content_hash(entity: dict) -> str:
    """Hash the mutable content fields of an entity for change detection."""
    parts = [
        entity.get("display_name", ""),
        json_mod.dumps(entity.get("template_properties", {}), sort_keys=True),
        json_mod.dumps(entity.get("creative_prompts", {}), sort_keys=True),
        json_mod.dumps(entity.get("connections", []), sort_keys=True),
        json_mod.dumps(entity.get("dialogue_hooks", []), sort_keys=True),
        entity.get("flow_notes", ""),
    ]
    return hashlib.sha256("|".join(parts).encode()).hexdigest()


def diff_against_previous(manifest: dict, previous_path: Path) -> dict:
    """Compare manifest against a previous version and set status + carry articy_ids.

    Modifies entities in-place:
    - New entity (not in previous): status stays "new"
    - Changed entity: status = "updated", articy_id carried forward
    - Unchanged entity: status = "unchanged", articy_id carried forward
    - Entities in previous but missing from new are logged as warnings
    """
    if not previous_path.exists():
        return manifest

    with open(previous_path, encoding="utf-8") as f:
        previous = json_mod.load(f)

    prev_by_path: dict[str, dict] = {}
    for entity in previous.get("entities", []):
        prev_by_path[entity["vault_path"]] = entity

    for entity in manifest["entities"]:
        vp = entity["vault_path"]
        prev = prev_by_path.pop(vp, None)
        if prev is None:
            entity["status"] = "new"
        else:
            prev_id = prev.get("articy_id", "")
            entity["articy_id"] = prev_id
            if not prev_id:
                # No articy_id means never imported — treat as new
                entity["status"] = "new"
            elif _entity_content_hash(entity) == _entity_content_hash(prev):
                entity["status"] = "unchanged"
            else:
                entity["status"] = "updated"

    for vp in prev_by_path:
        print(f"Warning: entity removed from vault: {vp}", file=sys.stderr)

    return manifest


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Generate articy import manifest from vault/world/")
    parser.add_argument("vault_world", type=Path, help="Path to vault/world/ directory")
    parser.add_argument("output", type=Path, help="Output path for import-manifest.json")
    parser.add_argument("--schema", type=Path, help="JSON Schema file to validate against")
    parser.add_argument("--previous", type=Path, help="Path to previous manifest for diffing")
    args = parser.parse_args(argv)

    if not args.vault_world.is_dir():
        print(f"Error: {args.vault_world} is not a directory", file=sys.stderr)
        return 1

    manifest = generate_manifest(args.vault_world)

    if args.previous:
        manifest = diff_against_previous(manifest, args.previous)

    if args.schema:
        import jsonschema as js

        with open(args.schema) as f:
            schema = json_mod.load(f)
        js.validate(manifest, schema)
        print(f"Validated against schema: {args.schema}")

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with open(args.output, "w", encoding="utf-8") as f:
        json_mod.dump(manifest, f, indent=2)

    print(f"Generated manifest with {len(manifest['entities'])} entities -> {args.output}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
