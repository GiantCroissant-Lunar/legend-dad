---
name: docling
description: Convert documents (PDF, DOCX, PPTX, XLSX, HTML, images, audio) to structured markdown, HTML, or JSON using Docling. Use when ingesting external documents, research papers, specs, or any non-markdown source into the project knowledge base. Use for document-to-markdown conversion before QMD indexing.
category: 04-tooling
layer: tooling
requires:
  python: ">=3.10"
related_skills:
  - "@qmd-search"
  - "@context-discovery"
---

# Docling Skill

[Docling](https://github.com/docling-project/docling) converts diverse document formats into structured, AI-friendly representations. Use it to ingest external docs into the project knowledge base.

## When to Use

- Converting PDFs (research papers, specs, datasheets) to markdown
- Ingesting DOCX/PPTX/XLSX files from stakeholders
- Extracting text and tables from scanned documents (OCR)
- Processing images containing text or diagrams
- Transcribing audio files (WAV, MP3) via ASR
- Preparing documents for QMD indexing (`@qmd-search`)
- Batch converting a folder of mixed-format documents

## Supported Formats

| Format | Notes |
|---|---|
| PDF | Page layout, reading order, tables, formulas, image classification |
| DOCX | Word documents |
| PPTX | PowerPoint presentations |
| XLSX | Excel spreadsheets |
| HTML | Web pages |
| Images | PNG, TIFF, JPEG — OCR extraction |
| Audio | WAV, MP3 — ASR transcription |
| LaTeX | .tex files |
| Plain text | .txt, .qmd, .Rmd |
| WebVTT | Subtitles/captions |
| USPTO | Patent documents |
| JATS | Academic articles |
| XBRL | Financial reports |

## CLI Usage

### Basic Conversion

```bash
# Convert a single file (outputs markdown by default)
docling document.pdf

# Convert from URL
docling https://arxiv.org/pdf/2408.09869

# Specify output directory
docling document.pdf --output docs/converted/

# Convert to specific format
docling document.pdf --to md        # Markdown (default)
docling document.pdf --to json      # Lossless JSON
docling document.pdf --to html      # HTML
docling document.pdf --to doctags   # DocTags format
```

### VLM Pipeline (Better Quality for Complex PDFs)

```bash
# Uses GraniteDocling visual language model
docling --pipeline vlm --vlm-model granite_docling document.pdf
```

### Batch Conversion

```bash
# Convert all PDFs in a directory
docling ./research-papers/

# Convert mixed formats
docling ./incoming-docs/
```

## Python API

### Basic Conversion

```python
from docling.document_converter import DocumentConverter

converter = DocumentConverter()
result = converter.convert("document.pdf")

# Export to markdown
md = result.document.export_to_markdown()

# Export to other formats
html = result.document.export_to_html()
json_doc = result.document.export_to_dict()  # lossless JSON
```

### Batch Conversion

```python
from docling.document_converter import DocumentConverter
from pathlib import Path

converter = DocumentConverter()
sources = list(Path("./research-papers").glob("*.pdf"))

for source in sources:
    result = converter.convert(str(source))
    output = Path("docs/converted") / f"{source.stem}.md"
    output.write_text(result.document.export_to_markdown())
```

### Advanced: Custom Pipeline

```python
from docling.document_converter import DocumentConverter, PdfFormatOption
from docling.pipeline.standard_pdf_pipeline import StandardPdfPipeline

converter = DocumentConverter(
    format_options={
        "pdf": PdfFormatOption(pipeline_cls=StandardPdfPipeline)
    }
)
result = converter.convert("document.pdf")
```

## Workflow: Ingest External Docs into QMD

Standard pipeline for adding external documents to the searchable knowledge base:

```bash
# 1. Convert documents to markdown
docling ./incoming/ --output docs/external/

# 2. Add to QMD collection (if new directory)
qmd collection add docs/external --name external --mask "**/*.md"
qmd context add qmd://external "Converted external documents: research papers, specs, reference material"

# 3. Index and embed
qmd update
qmd embed

# 4. Search
qmd query "relevant topic" -c external
```

## Workflow: Process Research for RFC Development

```bash
# Convert reference papers
docling https://arxiv.org/pdf/XXXX.XXXXX --output docs/research/

# Convert game design docs from stakeholders
docling game-design-spec.docx --output docs/design/

# Make searchable
qmd update && qmd embed

# Find relevant sections for RFC writing
qmd query "procedural dungeon generation algorithms" -c docs
```

## MCP Server

Docling provides an MCP server for agentic applications:

```bash
pip install docling[mcp]
# Then configure as MCP server in settings
```

## Workflow: Large PDF Ingestion (Chunked)

Large PDFs (100+ pages, image-heavy ebooks) will hit OCR memory limits if processed in one pass. Use chunked conversion to handle them reliably.

### Why This Matters

The standard pipeline processes all pages at once. RapidOCR allocates large float32 arrays per page — a 120-page ebook with full-bleed images will OOM around page 100+. Chunking by page range avoids this.

### Chunked Conversion Script

```python
from docling.document_converter import DocumentConverter
from pathlib import Path
import math

def convert_large_pdf(pdf_path: str, output_dir: str, chunk_size: int = 20):
    """Convert a large PDF in page-range chunks to avoid OOM."""
    import pypdfium2 as pdfium

    pdf = pdfium.PdfDocument(pdf_path)
    total_pages = len(pdf)
    pdf.close()

    converter = DocumentConverter()
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    stem = Path(pdf_path).stem

    all_md = []
    num_chunks = math.ceil(total_pages / chunk_size)

    for chunk_idx in range(num_chunks):
        start = chunk_idx * chunk_size + 1
        end = min((chunk_idx + 1) * chunk_size, total_pages)
        print(f"Converting pages {start}-{end} of {total_pages}...")

        try:
            result = converter.convert(
                pdf_path,
                page_range=(start, end)
            )
            md = result.document.export_to_markdown()
            all_md.append(f"<!-- pages {start}-{end} -->\n{md}")
        except Exception as e:
            print(f"  Chunk {start}-{end} failed: {e}")
            # Retry with smaller chunks
            for page in range(start, end + 1):
                try:
                    result = converter.convert(pdf_path, page_range=(page, page))
                    md = result.document.export_to_markdown()
                    all_md.append(f"<!-- page {page} -->\n{md}")
                except Exception as e2:
                    all_md.append(f"<!-- page {page} FAILED: {e2} -->")

    combined = "\n\n".join(all_md)
    (output / f"{stem}.md").write_text(combined, encoding="utf-8")
    print(f"Done. {total_pages} pages -> {output / stem}.md")
    return combined
```

### Usage

```python
# For ebooks, game dev guides, large spec documents
convert_large_pdf(
    "docs/assets/hud/2022_2DGameArt_EBook.pdf",
    "docs/converted/",
    chunk_size=15  # Smaller chunks for image-heavy PDFs
)
```

### Quality Validation

After conversion, check quality before indexing:

```python
def validate_conversion(md_path: str) -> dict:
    """Check conversion quality — detect OCR failures and sparse pages."""
    text = Path(md_path).read_text(encoding="utf-8")
    lines = text.split("\n")
    total_lines = len(lines)
    image_markers = sum(1 for l in lines if "<!-- image -->" in l)
    failed_pages = sum(1 for l in lines if "FAILED:" in l)
    empty_sections = sum(1 for l in lines if l.strip() == "")

    quality = {
        "total_lines": total_lines,
        "image_markers": image_markers,
        "failed_pages": failed_pages,
        "image_density": image_markers / max(1, total_lines),
        "text_density": (total_lines - image_markers - empty_sections) / max(1, total_lines),
    }

    if quality["image_density"] > 0.3:
        quality["recommendation"] = "Image-heavy — consider VLM pipeline for better extraction"
    elif failed_pages > 0:
        quality["recommendation"] = f"{failed_pages} pages failed — retry those with VLM or smaller chunks"
    else:
        quality["recommendation"] = "Good quality — ready for QMD indexing"

    return quality
```

### Decision: Standard vs VLM Pipeline

| PDF Type | Pipeline | Chunk Size |
|---|---|---|
| Text-heavy (specs, research) | Standard | 30-50 pages |
| Mixed text+images (ebooks) | Standard first, VLM retry on failures | 15-20 pages |
| Image-heavy (art guides, slide decks) | VLM | 5-10 pages |
| Scanned documents | VLM | 10-15 pages |

### Full Ingest Pipeline (Large PDF → Searchable)

```bash
# 1. Chunked conversion
python -c "
from docling_chunked import convert_large_pdf
convert_large_pdf('docs/assets/book.pdf', 'docs/converted/', chunk_size=15)
"

# 2. Validate
python -c "
from docling_validate import validate_conversion
print(validate_conversion('docs/converted/book.md'))
"

# 3. Index into QMD
qmd collection add docs/converted --name reference-books --mask "**/*.md"
qmd context add qmd://reference-books "Converted reference books and guides"
qmd update && qmd embed

# 4. Search
qmd query "2D lighting normal maps" -c reference-books
```

## Important Notes

- **First run** downloads ML models (~1-2GB) for layout detection and OCR
- **Heron** is the default layout model — fast and accurate for most PDFs
- **VLM pipeline** (`--pipeline vlm`) gives better results for complex layouts but is slower
- **Local processing** — no cloud dependencies, safe for sensitive documents
- **Python 3.10+** required (3.9 support dropped in v2.70.0)
- Already installed: Docling v2.77.0 at `C:\Users\User\AppData\Roaming\Python\Python313\site-packages`
- **Large PDFs** (100+ pages): Always use chunked conversion to avoid OOM — see workflow above
- **Image-heavy PDFs**: Use smaller chunk sizes (5-15 pages) and consider VLM pipeline

## Checklist

- [ ] Use `docling` CLI for one-off conversions
- [ ] Use Python API for batch/automated pipelines
- [ ] **Use chunked conversion for PDFs over 50 pages**
- [ ] **Validate conversion quality before indexing**
- [ ] **Retry failed pages with VLM pipeline or smaller chunks**
- [ ] Always output to `docs/` subdirectory to keep project organized
- [ ] Run `qmd update && qmd embed` after adding new converted docs
- [ ] Prefer VLM pipeline for complex PDFs with mixed layouts
- [ ] Check conversion quality — review markdown output before indexing
