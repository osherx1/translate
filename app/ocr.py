"""OCR helpers for extracting text regions from manga pages."""

from __future__ import annotations

import logging
import shutil
from pathlib import Path
from typing import List

import pytesseract
from PIL import Image
from pdf2image import convert_from_path

from .config import OCRSettings
from .models import PageExtraction, TextRegion


LOGGER = logging.getLogger(__name__)


class OCRService:
    def __init__(self, settings: OCRSettings) -> None:
        self.settings = settings
        if settings.tesseract_cmd:
            pytesseract.pytesseract.tesseract_cmd = settings.tesseract_cmd

    def extract(self, input_path: Path, work_dir: Path) -> List[PageExtraction]:
        work_dir.mkdir(parents=True, exist_ok=True)
        image_paths = self._prepare_images(input_path, work_dir)
        extractions: List[PageExtraction] = []
        for idx, image_path in enumerate(image_paths):
            extractions.append(self._extract_single(image_path, idx))
        return extractions

    def _prepare_images(self, input_path: Path, work_dir: Path) -> List[Path]:
        if input_path.suffix.lower() == ".pdf":
            LOGGER.info("Converting PDF to images via pdf2image")
            poppler = str(self.settings.poppler_path) if self.settings.poppler_path else None
            pil_pages = convert_from_path(str(input_path), dpi=self.settings.dpi, poppler_path=poppler)
            image_paths: List[Path] = []
            for idx, page in enumerate(pil_pages):
                target = work_dir / f"page-{idx:03d}.png"
                page.save(target, format="PNG")
                image_paths.append(target)
            return image_paths

        target = work_dir / input_path.name
        if input_path != target:
            shutil.copy2(input_path, target)
        return [target]

    def _language_candidates(self) -> List[str]:
        hint = (self.settings.language_hint or "").strip()
        if not hint:
            return ["eng"]
        if hint.lower() == "auto":
            # Try configured auto languages first, then fall back to English-only.
            auto_value = self.settings.auto_languages.strip() or "eng"
            return [auto_value, "eng"]
        return [hint]

    def _extract_single(self, image_path: Path, page_index: int) -> PageExtraction:
        image = Image.open(image_path).convert("RGB")
        config = "--psm 6"
        last_error: pytesseract.TesseractError | None = None
        for lang in self._language_candidates():
            try:
                data = pytesseract.image_to_data(image, lang=lang, config=config)
            except pytesseract.TesseractError as err:  # Missing language data or OCR failure.
                last_error = err
                LOGGER.warning("Tesseract failed with lang '%s': %s", lang, err)
                continue
            regions = self._parse_tesseract_output(data)
            LOGGER.info("Page %s (%s): captured %s text regions", page_index, lang, len(regions))
            return PageExtraction(page_index=page_index, image_path=image_path, regions=regions)
        if last_error:
            raise last_error
        raise RuntimeError("OCR failed for all configured languages.")

    def _parse_tesseract_output(self, data: str) -> List[TextRegion]:
        lines = data.splitlines()
        if not lines:
            return []
        regions: List[TextRegion] = []
        for row in lines[1:]:
            cols = row.split("\t")
            if len(cols) != 12:
                continue
            try:
                conf = float(cols[10])
            except ValueError:
                continue
            text = cols[11].strip()
            if conf < 30 or not text:
                continue
            x, y, w, h = map(int, cols[6:10])
            bbox = (x, y, x + w, y + h)
            regions.append(TextRegion(bbox=bbox, text=text, confidence=conf / 100))
        return regions
