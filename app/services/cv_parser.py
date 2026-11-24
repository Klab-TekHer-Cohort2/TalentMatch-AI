import io
import re
import uuid
import zipfile
from pathlib import Path

import pdfplumber
from docx import Document
from fastapi import UploadFile

from ..config import settings

ALLOWED_EXTENSIONS = {".pdf", ".docx"}


class CVValidationError(ValueError):
    pass


def validate_upload(upload: UploadFile) -> tuple[bytes, str]:
    """Validate extension, size and file signature. Returns (bytes, extension)."""
    filename = Path(upload.filename or "").name
    extension = Path(filename).suffix.lower()
    if extension not in ALLOWED_EXTENSIONS:
        raise CVValidationError("Only PDF and DOCX files are supported")

    upload.file.seek(0)
    contents = upload.file.read(settings.max_upload_bytes + 1)
    if not contents:
        raise CVValidationError("The uploaded file is empty")
    if len(contents) > settings.max_upload_bytes:
        raise CVValidationError(f"File exceeds the {settings.max_upload_mb} MB limit")

    if extension == ".pdf":
        if not contents.startswith(b"%PDF"):
            raise CVValidationError("File content is not a valid PDF")
    else:
        if not contents.startswith(b"PK\x03\x04"):
            raise CVValidationError("File content is not a valid DOCX")
        try:
            with zipfile.ZipFile(io.BytesIO(contents)) as archive:
                names = archive.namelist()
                if "word/document.xml" not in names:
                    raise CVValidationError("DOCX archive is missing its document body")
                total_uncompressed = sum(info.file_size for info in archive.infolist())
                if total_uncompressed > settings.max_upload_bytes * 8:
                    raise CVValidationError("DOCX archive is too large when expanded")
        except zipfile.BadZipFile:
            raise CVValidationError("Corrupted DOCX file")

    return contents, extension


def extract_text(contents: bytes, extension: str) -> str:
    try:
        if extension == ".pdf":
            parts: list[str] = []
            with pdfplumber.open(io.BytesIO(contents)) as pdf:
                if len(pdf.pages) > 30:
                    raise CVValidationError("PDF has too many pages (maximum 30)")
                for page in pdf.pages:
                    parts.append(page.extract_text() or "")
            text = "\n".join(parts)
        else:
            document = Document(io.BytesIO(contents))
            parts = [paragraph.text for paragraph in document.paragraphs]
            for table in document.tables:
                for row in table.rows:
                    parts.append(" | ".join(cell.text for cell in row.cells))
            text = "\n".join(parts)
    except CVValidationError:
        raise
    except Exception as exc:
        raise CVValidationError(f"Could not read the document: {exc}") from exc

    text = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f]", " ", text)
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text).strip()

    if len(text) < 40:
        raise CVValidationError(
            "No readable text found. Scanned/image-only CVs are not supported; upload a text-based PDF or DOCX."
        )
    return text[:80000]


def save_upload(contents: bytes, extension: str) -> str:
    destination = settings.upload_path / f"{uuid.uuid4().hex}{extension}"
    destination.write_bytes(contents)
    return str(destination)


def remove_file(path: str | None) -> None:
    if not path:
        return
    try:
        Path(path).unlink(missing_ok=True)
    except OSError:
        pass
