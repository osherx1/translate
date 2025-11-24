"""Rendering helpers to rebuild translated pages back into PDF."""

from __future__ import annotations

from pathlib import Path
from typing import List, Sequence

from bidi.algorithm import get_display
from PIL import Image, ImageDraw, ImageFont

from .models import PageTranslation, RegionTranslation, RenderedPage


class PDFRenderer:
    def __init__(self, font_path: Path | None, font_size: int, bubble_padding: int) -> None:
        self.font_path = font_path
        self.font_size = font_size
        self.padding = bubble_padding
        self._font_cache: ImageFont.FreeTypeFont | ImageFont.ImageFont | None = None

    def render_page(self, translation: PageTranslation, out_dir: Path) -> RenderedPage:
        out_dir.mkdir(parents=True, exist_ok=True)
        image = Image.open(translation.image_path).convert("RGBA")
        draw = ImageDraw.Draw(image, "RGBA")
        font = self._load_font()
        for region in translation.regions:
            self._draw_region(draw, font, region, image.size)
        rgb_image = image.convert("RGB")
        output_path = out_dir / f"page-{translation.page_index:03d}.png"
        rgb_image.save(output_path)
        return RenderedPage(page_index=translation.page_index, output_path=output_path)

    def bundle_pdf(self, rendered_pages: List[RenderedPage], output_pdf: Path) -> Path:
        if not rendered_pages:
            raise ValueError("No rendered pages to bundle")
        output_pdf.parent.mkdir(parents=True, exist_ok=True)
        images = [Image.open(page.output_path).convert("RGB") for page in rendered_pages]
        images[0].save(output_pdf, save_all=True, append_images=images[1:])
        return output_pdf

    def _load_font(self) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
        if self._font_cache:
            return self._font_cache
        if self.font_path and self.font_path.exists():
            try:
                self._font_cache = ImageFont.truetype(str(self.font_path), self.font_size)
                return self._font_cache
            except OSError:
                pass
        self._font_cache = ImageFont.load_default()
        return self._font_cache

    def _draw_region(
        self,
        draw: ImageDraw.ImageDraw,
        font: ImageFont.FreeTypeFont | ImageFont.ImageFont,
        region: RegionTranslation,
        canvas_size: tuple[int, int],
    ) -> None:
        bbox = self._pad_bbox(region.bbox, canvas_size)
        draw.rounded_rectangle(bbox, radius=6, fill=(255, 255, 255, 235))
        max_width = max(10, bbox[2] - bbox[0] - self.padding * 2)
        lines = self._wrap_text(region.translated_text, font, max_width)
        y_cursor = bbox[1] + self.padding
        line_height = font.getbbox("Ay")[3] - font.getbbox("Ay")[1] + 2
        for line in lines:
            display_text = get_display(line)
            draw.text((bbox[2] - self.padding, y_cursor), display_text, font=font, fill="black", anchor="ra")
            y_cursor += line_height

    def _pad_bbox(self, bbox: Sequence[int], canvas_size: tuple[int, int]) -> tuple[int, int, int, int]:
        x0, y0, x1, y1 = bbox
        x0 = max(0, x0 - self.padding)
        y0 = max(0, y0 - self.padding)
        x1 = min(canvas_size[0], x1 + self.padding)
        y1 = min(canvas_size[1], y1 + self.padding)
        return (x0, y0, x1, y1)

    def _wrap_text(
        self,
        text: str,
        font: ImageFont.FreeTypeFont | ImageFont.ImageFont,
        max_width: int,
    ) -> List[str]:
        sanitized = text.replace("\n", " ").strip()
        if not sanitized:
            return [""]
        words = sanitized.split()
        lines: List[str] = []
        current = ""
        for word in words:
            candidate = f"{current} {word}".strip()
            if candidate and self._text_width(candidate, font) <= max_width:
                current = candidate
            else:
                if current:
                    lines.append(current)
                current = word
        if current:
            lines.append(current)
        return lines or [sanitized]

    def _text_width(self, text: str, font: ImageFont.FreeTypeFont | ImageFont.ImageFont) -> int:
        bbox = font.getbbox(text)
        return bbox[2] - bbox[0]
