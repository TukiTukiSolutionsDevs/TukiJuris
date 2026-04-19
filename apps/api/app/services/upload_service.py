"""Upload service — file persistence and text extraction."""

import logging
import uuid
from pathlib import Path

logger = logging.getLogger(__name__)

UPLOAD_DIR = Path("/app/uploads")  # Docker volume
ALLOWED_TYPES = {
    "application/pdf": "pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document": "docx",
    "image/jpeg": "jpg",
    "image/png": "png",
    "image/webp": "webp",
    "text/plain": "txt",
}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB


async def save_file(file_content: bytes, filename: str, content_type: str) -> tuple[str, str]:
    """Save file to disk and return (storage_path, file_type)."""
    file_type = ALLOWED_TYPES.get(content_type)
    if not file_type:
        raise ValueError(f"Tipo de archivo no soportado: {content_type}")

    if len(file_content) > MAX_FILE_SIZE:
        raise ValueError("El archivo excede el tamaño máximo de 10MB")

    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    unique_name = f"{uuid.uuid4().hex}.{file_type}"
    path = UPLOAD_DIR / unique_name
    path.write_bytes(file_content)
    return str(path), file_type


async def extract_text(file_path: str, file_type: str) -> tuple[str, int | None]:
    """Extract text from a file. Returns (text, page_count)."""
    try:
        if file_type == "pdf":
            return await _extract_pdf(file_path)
        elif file_type == "docx":
            return await _extract_docx(file_path)
        elif file_type == "txt":
            return await _extract_txt(file_path)
        elif file_type in ("jpg", "png", "webp"):
            # For images, return a placeholder — OCR can be added later
            return "[Imagen adjunta — el análisis OCR estará disponible próximamente]", None
        else:
            return "", None
    except Exception as e:
        logger.warning("Text extraction failed for %s: %s", file_path, e)
        return f"[Error al extraer texto: {str(e)}]", None


async def _extract_pdf(path: str) -> tuple[str, int | None]:
    """Extract text from PDF using PyMuPDF (fitz)."""
    try:
        import fitz  # PyMuPDF

        doc = fitz.open(path)
        pages = []
        for page in doc:
            pages.append(page.get_text())
        doc.close()
        return "\n\n".join(pages), len(pages)
    except ImportError:
        # Fallback: basic extraction without fitz
        return "[PDF recibido — instalar PyMuPDF para extraer texto]", None


async def _extract_docx(path: str) -> tuple[str, int | None]:
    """Extract text from DOCX."""
    try:
        from docx import Document

        doc = Document(path)
        paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
        return "\n\n".join(paragraphs), None
    except ImportError:
        return "[DOCX recibido — instalar python-docx para extraer texto]", None


async def _extract_txt(path: str) -> tuple[str, int | None]:
    """Read plain text file."""
    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        return f.read(), None
