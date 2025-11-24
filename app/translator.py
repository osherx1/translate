"""Gemini translation helpers."""

from __future__ import annotations

import json
import logging
from textwrap import dedent
from typing import Iterable, List

from google import generativeai as genai

from .config import GeminiSettings, ProcessingSettings
from .models import PageExtraction, PageTranslation, RegionTranslation, TextRegion


LOGGER = logging.getLogger(__name__)


class GeminiTranslator:
    def __init__(self, gemini_settings: GeminiSettings, processing: ProcessingSettings) -> None:
        genai.configure(api_key=gemini_settings.api_key)
        self.model = genai.GenerativeModel(
            gemini_settings.model,
            generation_config={
                "temperature": gemini_settings.temperature,
                "max_output_tokens": gemini_settings.max_output_tokens,
            },
        )
        self.batch_size = processing.batch_size
        self.max_chars = processing.max_chars_per_batch

    def translate_page(self, extraction: PageExtraction, target_language: str) -> PageTranslation:
        translated_regions: List[RegionTranslation] = []
        for chunk in self._chunk_regions(extraction.regions):
            translations = self._call_model(chunk, target_language)
            for region, translated in zip(chunk, translations):
                translated_regions.append(
                    RegionTranslation(
                        bbox=region.bbox,
                        source_text=region.text,
                        translated_text=translated,
                        confidence=region.confidence,
                    )
                )
        return PageTranslation(page_index=extraction.page_index, image_path=extraction.image_path, regions=translated_regions)

    def _chunk_regions(self, regions: List[TextRegion]) -> Iterable[List[TextRegion]]:
        chunk: List[TextRegion] = []
        char_count = 0
        for region in regions:
            chunk.append(region)
            char_count += len(region.text)
            if len(chunk) >= self.batch_size or char_count >= self.max_chars:
                yield chunk
                chunk = []
                char_count = 0
        if chunk:
            yield chunk

    def _call_model(self, regions: List[TextRegion], target_language: str) -> List[str]:
        payload = {
            "target_language": target_language,
            "blocks": [{"text": region.text} for region in regions],
        }
        prompt = dedent(
            f"""
            You are an expert manga translator. Translate each block of text to {target_language}.
            Respond with a JSON array of strings matching the length of the provided blocks. Each array
            element must correspond to the block at the same index. Do not add numbering or extra text.

            Input JSON:
            {json.dumps(payload, ensure_ascii=False)}
            """
        ).strip()
        try:
            response = self.model.generate_content([prompt])
            text = response.text.strip()
            translations = self._parse_translations(text, len(regions))
            LOGGER.debug("Received translations for %s regions", len(translations))
            return translations
        except Exception as exc:  # noqa: BLE001
            LOGGER.warning("Falling back to source text due to translation error: %s", exc)
            return [region.text for region in regions]

    def _parse_translations(self, response_text: str, expected: int) -> List[str]:
        start = response_text.find("[")
        end = response_text.rfind("]")
        if start == -1 or end == -1:
            raise ValueError("Response missing JSON array")
        json_payload = response_text[start : end + 1]
        data = json.loads(json_payload)
        if not isinstance(data, list) or len(data) != expected:
            raise ValueError("Unexpected translation payload length")
        return [str(item).strip() for item in data]
