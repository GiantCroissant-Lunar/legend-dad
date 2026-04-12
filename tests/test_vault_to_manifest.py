from vault_to_manifest import extract_creative_prompts, extract_sections, parse_vault_page


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
