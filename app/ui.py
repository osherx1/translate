"""Streamlit UI entry point for manual uploads."""

from __future__ import annotations

import tempfile
import sys
from pathlib import Path

import streamlit as st

try:
    from app.pipeline import MangaTranslationPipeline
    from app.models import TranslationJob
except ModuleNotFoundError:  # Streamlit Cloud runs this file without repo root on sys.path
    ROOT_DIR = Path(__file__).resolve().parents[1]
    if str(ROOT_DIR) not in sys.path:
        sys.path.insert(0, str(ROOT_DIR))
    from app.pipeline import MangaTranslationPipeline
    from app.models import TranslationJob


def render_ui() -> None:
    st.set_page_config(page_title="Gemini Manga Translator", layout="wide")
    st.title("Gemini Manga Translator")
    st.caption("Upload PNG, JPG, or PDF files and receive a Hebrew PDF while preserving the artwork.")

    pipeline = _init_pipeline()
    if pipeline is None:
        return
    target_language = st.text_input("Target language", value="he")
    uploaded_file = st.file_uploader("Upload PNG, JPG, or PDF", type=["png", "jpg", "jpeg", "pdf"])
    if not uploaded_file:
        st.info("Select a file to begin.")
        return

    if st.button("Translate" + (f" to {target_language.upper()}" if target_language else "")):
        tmp_dir = Path(tempfile.mkdtemp(prefix="manga-agent-"))
        input_path = tmp_dir / uploaded_file.name
        input_path.write_bytes(uploaded_file.getbuffer())
        outputs_dir = tmp_dir / "outputs"
        job = TranslationJob(input_path=input_path, outputs_dir=outputs_dir, target_language=target_language or "he")
        with st.spinner("Running OCR, translation, and rendering..."):
            pdf_path = pipeline.run(job)
        with pdf_path.open("rb") as handle:
            st.success("Translation complete!")
            st.download_button(
                label="Download Hebrew PDF",
                data=handle.read(),
                file_name=f"{input_path.stem}-hebrew.pdf",
                mime="application/pdf",
            )


@st.cache_resource(show_spinner=False)
def _get_pipeline() -> MangaTranslationPipeline:
    return MangaTranslationPipeline.from_env()


def _init_pipeline() -> MangaTranslationPipeline | None:
    try:
        return _get_pipeline()
    except Exception as exc:  # noqa: BLE001
        st.error("Failed to initialize pipeline: %s" % exc)
        st.info(
            "Set GEMINI_API_KEY (and optionally TESSERACT_CMD, POPPLER_PATH, FONT_PATH) before launching the UI.",
        )
        if st.button("Retry initialization"):
            st.cache_resource.clear()
            st.experimental_rerun()
        return None
