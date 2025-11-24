"""Shared data models for OCR blocks and translations."""

from __future__ import annotations

from pathlib import Path
from typing import List, Tuple

from pydantic import BaseModel


BBox = Tuple[int, int, int, int]


class TextRegion(BaseModel):
    bbox: BBox
    text: str
    confidence: float


class PageExtraction(BaseModel):
    page_index: int
    image_path: Path
    regions: List[TextRegion]

    @property
    def total_characters(self) -> int:
        return sum(len(region.text) for region in self.regions)


class RegionTranslation(BaseModel):
    bbox: BBox
    source_text: str
    translated_text: str
    confidence: float


class PageTranslation(BaseModel):
    page_index: int
    image_path: Path
    regions: List[RegionTranslation]


class TranslationJob(BaseModel):
    input_path: Path
    outputs_dir: Path
    target_language: str = "he"

    @property
    def is_pdf(self) -> bool:
        return self.input_path.suffix.lower() == ".pdf"

    @property
    def work_dir(self) -> Path:
        return self.outputs_dir / "work"


class RenderedPage(BaseModel):
    page_index: int
    output_path: Path
