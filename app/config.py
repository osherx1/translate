"""Configuration helpers for the translator agent."""

from __future__ import annotations

from pathlib import Path
from typing import Optional

from pydantic import BaseModel, Field


class GeminiSettings(BaseModel):
    api_key: str = Field(..., description="Google Gemini API key")
    model: str = Field(default="gemini-1.5-flash", description="Gemini model used for translation")
    max_output_tokens: int = Field(default=2048)
    temperature: float = Field(default=0.4)


class OCRSettings(BaseModel):
    language_hint: str = Field(default="eng", description="Primary OCR language code or 'auto'")
    auto_languages: str = Field(default="eng+jpn", description="Languages string used when language_hint=auto")
    dpi: int = Field(default=300, ge=72, le=600)
    tesseract_cmd: Optional[str] = Field(default=None, description="Optional absolute path to tesseract executable")
    poppler_path: Optional[Path] = Field(default=None, description="Optional path to Poppler bin directory")


class OutputSettings(BaseModel):
    out_dir: Path = Field(default=Path("outputs"))


class ProcessingSettings(BaseModel):
    target_language: str = Field(default="he")
    batch_size: int = Field(default=16, ge=1, le=64)
    max_chars_per_batch: int = Field(default=1500, ge=200, le=6000)


class RenderingSettings(BaseModel):
    font_path: Optional[Path] = None
    font_size: int = Field(default=28, ge=10, le=72)
    bubble_padding: int = Field(default=6, ge=0, le=40)


class AppSettings(BaseModel):
    gemini: GeminiSettings
    ocr: OCRSettings = Field(default_factory=OCRSettings)
    output: OutputSettings = Field(default_factory=OutputSettings)
    processing: ProcessingSettings = Field(default_factory=ProcessingSettings)
    rendering: RenderingSettings = Field(default_factory=RenderingSettings)

    @classmethod
    def from_env(cls) -> "AppSettings":
        from dotenv import load_dotenv
        import os

        load_dotenv()
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise RuntimeError("GEMINI_API_KEY is required")
        model = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")
        output_dir = Path(os.getenv("OUTPUT_DIR", "outputs")).expanduser()
        ocr_lang = os.getenv("OCR_LANG", "eng")
        ocr_auto_langs = os.getenv("OCR_AUTO_LANGS", "eng+jpn")
        tess_path = os.getenv("TESSERACT_CMD")
        poppler_env = os.getenv("POPPLER_PATH")
        poppler_path = Path(poppler_env).expanduser() if poppler_env else None
        target_language = os.getenv("TARGET_LANGUAGE", "he")
        batch_size = int(os.getenv("TRANSLATION_BATCH_SIZE", "16"))
        max_chars = int(os.getenv("TRANSLATION_MAX_CHARS", "1500"))
        font_path_env = os.getenv("FONT_PATH")
        font_path = Path(font_path_env).expanduser() if font_path_env else None
        font_size = int(os.getenv("FONT_SIZE", "28"))
        bubble_padding = int(os.getenv("BUBBLE_PADDING", "6"))

        return cls(
            gemini=GeminiSettings(api_key=api_key, model=model),
            ocr=OCRSettings(
                language_hint=ocr_lang,
                auto_languages=ocr_auto_langs,
                tesseract_cmd=tess_path,
                poppler_path=poppler_path,
            ),
            output=OutputSettings(out_dir=output_dir),
            processing=ProcessingSettings(target_language=target_language, batch_size=batch_size, max_chars_per_batch=max_chars),
            rendering=RenderingSettings(font_path=font_path, font_size=font_size, bubble_padding=bubble_padding),
        )


DEFAULT_SETTINGS: Optional[AppSettings] = None
