# Architecture Plan

## Overview
The agent ingests manga pages (PNG, JPG, PDF), runs OCR to extract text regions plus bounding boxes, translates each region into Hebrew via Gemini, and rebuilds a PDF that preserves the visual layout.

## Key Components
1. **File Loader** – normalizes uploads and converts PDFs into page images using `pdf2image`.
2. **OCR Layer** – uses `pytesseract` (or, optionally, Google Cloud Vision later) to capture bounding boxes and confidence scores for each paragraph/speech balloon.
3. **Translation Layer** – batches text regions and sends them to Gemini (`gemini-1.5-flash` by default) with instructions to output Hebrew while respecting context.
4. **Layout/Rendering** – uses Pillow + ReportLab to cover original text (in-paint) and draw translated text, matching orientation/direction. Keeps fonts configurable to support Hebrew typography.
5. **UI Layer** – Streamlit interface for drag-and-drop uploads, previewing progress, and downloading the resulting PDF.

## Processing Flow
1. User uploads file via Streamlit UI or CLI argument.
2. Pipeline writes the upload into a working directory and determines page sources.
3. OCR service iterates through pages, returning `PageExtraction` objects containing bounding boxes and text.
4. Translator groups text into context-aware bundles (per balloon or panel) and obtains Hebrew translations.
5. Renderer paints clean bubbles using bounding boxes, writes the translated text using dynamic fonts, and exports each page as PNG.
6. Rendered PNGs are combined into a final PDF for download.

## Open Questions
- Whether to add automatic speech-bubble segmentation for cleaner backgrounds (possible future enhancement).
- Whether "Gemini Nano" should run locally (requires Android/Pixel hardware) vs. using Gemini API (current plan).

This plan will guide the implementation in the customization step.
