from vault_to_manifest import build_entity, extract_creative_prompts, extract_sections, parse_vault_page


def test_parse_frontmatter_extracts_type(sample_character_md):
    page = parse_vault_page(sample_character_md)
    assert page["frontmatter"]["type"] == "character"


def test_parse_frontmatter_extracts_articy_id(sample_character_md):
    page = parse_vault_page(sample_character_md)
    assert page["frontmatter"]["articy-id"] == ""


def test_parse_frontmatter_extracts_connections(sample_character_md):
    page = parse_vault_page(sample_character_md)
    assert "[[Elder Aldric]]" in page["frontmatter"]["connections"]


def test_parse_content_extracts_body(sample_character_md):
    page = parse_vault_page(sample_character_md)
    assert "# Sera" in page["content"]
    assert "## Backstory" in page["content"]


def test_extract_sections_finds_h2_headings(sample_character_md):
    page = parse_vault_page(sample_character_md)
    sections = extract_sections(page["content"])
    assert "Overview" in sections
    assert "Backstory" in sections
    assert "Personality & Motivation" in sections
    assert "Relationships" in sections
    assert "Creative Prompts" in sections


def test_extract_sections_content_is_stripped(sample_character_md):
    page = parse_vault_page(sample_character_md)
    sections = extract_sections(page["content"])
    assert sections["Overview"].startswith("A young scholar")


def test_extract_creative_prompts(sample_character_md):
    page = parse_vault_page(sample_character_md)
    sections = extract_sections(page["content"])
    prompts = extract_creative_prompts(sections.get("Creative Prompts", ""))
    assert "portrait" in prompts
    assert "voice" in prompts
    assert "theme-music" in prompts
    assert len(prompts["portrait"]) >= 100


def test_build_entity_sets_display_name(sample_character_md):
    entity = build_entity(sample_character_md, "vault/world/characters/sera.md")
    assert entity["display_name"] == "Sera"


def test_build_entity_sets_type(sample_character_md):
    entity = build_entity(sample_character_md, "vault/world/characters/sera.md")
    assert entity["type"] == "character"


def test_build_entity_extracts_template_properties(sample_character_md):
    entity = build_entity(sample_character_md, "vault/world/characters/sera.md")
    props = entity["template_properties"]
    assert "backstory" in props
    assert "personality_and_motivation" in props
    assert "overview" in props


def test_build_entity_extracts_creative_prompts(sample_character_md):
    entity = build_entity(sample_character_md, "vault/world/characters/sera.md")
    assert "portrait" in entity["creative_prompts"]
    assert "voice" in entity["creative_prompts"]
    assert "theme-music" in entity["creative_prompts"]


def test_build_entity_parses_connections(sample_character_md):
    entity = build_entity(sample_character_md, "vault/world/characters/sera.md")
    targets = [c["target_vault_path"] for c in entity["connections"]]
    assert any("Elder Aldric" in t for t in targets)


def test_build_entity_sets_vault_path(sample_character_md):
    entity = build_entity(sample_character_md, "vault/world/characters/sera.md")
    assert entity["vault_path"] == "vault/world/characters/sera.md"


def test_build_entity_defaults_status_to_new(sample_character_md):
    entity = build_entity(sample_character_md, "vault/world/characters/sera.md")
    assert entity["status"] == "new"
