"""CLI entry point for the Gemini Manga Translator project."""

from __future__ import annotations

import argparse
from datetime import datetime
from pathlib import Path

from app.config import AppSettings
from app.models import TranslationJob
from app.pipeline import MangaTranslationPipeline


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Translate manga pages to Hebrew via Gemini")
    parser.add_argument("input", type=Path, help="Path to PNG/JPG/PDF")
    parser.add_argument("--language", "-l", default=None, help="Target language (default: he)")
    parser.add_argument(
        "--output-dir",
        "-o",
        type=Path,
        default=None,
        help="Destination directory for translated artifacts",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    settings = AppSettings.from_env()
    pipeline = MangaTranslationPipeline(settings)
    output_dir = args.output_dir or settings.output.out_dir / f"run-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
    job = TranslationJob(
        input_path=args.input,
        outputs_dir=output_dir,
        target_language=args.language or settings.processing.target_language,
    )
    pdf_path = pipeline.run(job)
    print(f"✅ Translated PDF written to {pdf_path}")


if __name__ == "__main__":
    main()
