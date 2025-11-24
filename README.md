# Gemini Manga Translator

This project sets up a Python-based agent that ingests manga pages (PNG, JPG, and PDF), translates the detected text into Hebrew through Google's Gemini family of models, and exports a rebuilt PDF that preserves the original page layout while overlaying the translated text.

## Project Goals
- Accept PNG, JPG, or multipage PDF uploads.
- Run OCR on each page to capture text regions and their bounding boxes.
- Send extracted text to Gemini for contextual translation into Hebrew.
- Re-render each page with Hebrew text placed back into the original bubbles/panels.
- Output a combined PDF ready for review or distribution.

## Components
- `app/config.py` – centralizes environment-driven settings (Gemini model, OCR hints, fonts, batching, output paths).
- `app/ocr.py` – converts PDFs into page images and extracts text regions with bounding boxes using Tesseract.
- `app/translator.py` – calls Gemini (default `gemini-1.5-flash`) in JSON mode to translate every text region into Hebrew.
- `app/pdf_builder.py` – erases original text bubbles, renders Hebrew replacements with right-to-left support, and exports PNG/PDF outputs.
- `app/pipeline.py` – orchestrates OCR → translation → rendering.
- `app/ui.py` – Streamlit interface for drag-and-drop uploads plus download link for the translated PDF.
- `main.py` – CLI entry point for batch conversions.

## Prerequisites
- Python 3.11+
- Google Gemini API key with access to multimodal translation models (e.g., `gemini-1.5-flash`).
- Tesseract OCR binary installed locally and discoverable via PATH (or configure `TESSDATA_PREFIX`).
- Poppler binaries for PDF-to-image conversion if processing PDFs.

## Setup
1. Create and activate a virtual environment.
2. Install dependencies: `pip install -r requirements.txt`.
3. Install native tooling:
	- [Tesseract OCR](https://github.com/tesseract-ocr/tesseract) and ensure `tesseract.exe` is on PATH (or set `TESSERACT_CMD`).
	- [Poppler](https://github.com/oschwartz10612/poppler-windows/releases/) for `pdf2image` when handling PDFs (configure `POPPLER_PATH` if needed).
4. Create a `.env` file (or export variables) with at least:

```
GEMINI_API_KEY=your_key_here
GEMINI_MODEL=gemini-1.5-flash
OCR_LANG=eng
OCR_AUTO_LANGS=eng+jpn
TARGET_LANGUAGE=he
```

Optional knobs include `OUTPUT_DIR`, `TRANSLATION_BATCH_SIZE`, `FONT_PATH`, `FONT_SIZE`, and `BUBBLE_PADDING`.

Set `OCR_LANG` to `eng` for English-only pages (default). To let Tesseract attempt multiple languages, either put a `+`-separated list such as `eng+jpn` or use `OCR_LANG=auto` and configure `OCR_AUTO_LANGS` with the language mix you installed (for example `eng+jpn+kor`).

## Usage

### CLI

```
python main.py path/to/chapter.pdf --language he --output-dir outputs/chapter01
```

The script writes all intermediate assets under the chosen output directory and emits `translated.pdf` containing the Hebrew pages.

### Streamlit UI

```
streamlit run app/ui.py
```

Upload PNG/JPG/PDF pages, optionally override the target language, and click **Translate** to receive a download button for the final PDF.

## Notes & Limitations
- Translation quality depends on Gemini and the clarity of OCR results. Clean scans yield better alignment.
- The renderer currently applies a rounded rectangle patch over detected text regions; advanced in-painting can be integrated later if needed.
- Gemini Nano (on-device) is not yet generally available for desktop inference, so this project relies on the Gemini API (cloud) while keeping the architecture ready for future local adapters.
