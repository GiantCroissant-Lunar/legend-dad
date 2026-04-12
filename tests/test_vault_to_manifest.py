from vault_to_manifest import parse_vault_page


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
