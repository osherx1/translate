"""High-level orchestration for the manga translation flow."""

from __future__ import annotations

from pathlib import Path
from typing import List

from .config import AppSettings
from .models import PageTranslation, RenderedPage, TranslationJob
from .ocr import OCRService
from .pdf_builder import PDFRenderer
from .translator import GeminiTranslator


class MangaTranslationPipeline:
    def __init__(self, settings: AppSettings) -> None:
        self.settings = settings
        self.ocr = OCRService(settings.ocr)
        self.translator = GeminiTranslator(settings.gemini, settings.processing)
        self.renderer = PDFRenderer(
            font_path=settings.rendering.font_path,
            font_size=settings.rendering.font_size,
            bubble_padding=settings.rendering.bubble_padding,
        )

    @classmethod
    def from_env(cls) -> "MangaTranslationPipeline":
        return cls(AppSettings.from_env())

    def run(self, job: TranslationJob) -> Path:
        job.outputs_dir.mkdir(parents=True, exist_ok=True)
        pages_dir = job.outputs_dir / "pages"
        extractions = self.ocr.extract(job.input_path, job.work_dir)
        translations = self._translate(extractions, job.target_language)
        rendered_pages = self._render(translations, pages_dir)
        return self.renderer.bundle_pdf(rendered_pages, job.outputs_dir / "translated.pdf")

    def _translate(self, extractions, target_language: str) -> List[PageTranslation]:
        return [self.translator.translate_page(extraction, target_language) for extraction in extractions]

    def _render(self, translations: List[PageTranslation], pages_dir: Path) -> List[RenderedPage]:
        return [self.renderer.render_page(translation, pages_dir) for translation in translations]
