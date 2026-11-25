import os
import re
import uuid
from pathlib import Path
from typing import Dict, Optional, Set, Tuple

from fastapi import UploadFile, status

from app.config import get_settings
from app.middleware.exceptions import AppException

SAFE_FILENAME_RE = re.compile(r"[^A-Za-z0-9._-]+")

VIDEO_EXTENSIONS: Set[str] = {".mp4", ".webm", ".mov"}
MATERIAL_EXTENSIONS: Set[str] = {".pdf", ".ppt", ".pptx", ".doc", ".docx", ".txt", ".zip"}
ASSIGNMENT_EXTENSIONS: Set[str] = {".pdf", ".doc", ".docx", ".zip", ".txt", ".png", ".jpg", ".jpeg"}
IMAGE_EXTENSIONS: Set[str] = {".png", ".jpg", ".jpeg", ".webp"}

EXT_TO_MIME: Dict[str, str] = {
    ".pdf": "application/pdf",
    ".ppt": "application/vnd.ms-powerpoint",
    ".pptx": "application/vnd.openxmlformats-officedocument.presentationml.presentation",
    ".doc": "application/msword",
    ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    ".txt": "text/plain",
    ".zip": "application/zip",
    ".png": "image/png",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".webp": "image/webp",
    ".mp4": "video/mp4",
    ".webm": "video/webm",
    ".mov": "video/quicktime",
}


def sanitize_filename(filename: Optional[str]) -> str:
    """Strip directory traversal components and unsafe characters."""
    base = Path(filename or "file").name
    cleaned = SAFE_FILENAME_RE.sub("_", base).strip("._")
    return cleaned or "file"


def _verify_magic_bytes(ext: str, header: bytes) -> bool:
    """Perform server-side magic byte checks so browser MIME headers are never trusted blindly."""
    if ext == ".pdf":
        return header.startswith(b"%PDF-")
    if ext in {".docx", ".pptx", ".zip"}:
        return header.startswith(b"PK\x03\x04") or header.startswith(b"PK\x05\x06")
    if ext in {".doc", ".ppt"}:
        return header.startswith(b"\xD0\xCF\x11\xE0\xA1\xB1\x1A\xE1")
    if ext == ".png":
        return header.startswith(b"\x89PNG\r\n\x1a\n")
    if ext in {".jpg", ".jpeg"}:
        return header.startswith(b"\xFF\xD8\xFF")
    if ext == ".webp":
        return len(header) >= 12 and header[:4] == b"RIFF" and header[8:12] == b"WEBP"
    if ext == ".mp4":
        return len(header) >= 12 and header[4:8] == b"ftyp"
    if ext == ".mov":
        return len(header) >= 8 and header[4:8] in {b"ftyp", b"moov", b"mdat", b"wide"}
    if ext == ".webm":
        return header.startswith(b"\x1A\x45\xDF\xA3")
    if ext == ".txt":
        return b"\x00" not in header
    return False


async def save_upload_file(
    upload: UploadFile,
    category_dir: str,
    allowed_extensions: Set[str],
    max_size_mb: int,
) -> Tuple[str, str, str, int]:
    """
    Validate and persist an uploaded file.
    Returns (original_clean_name, storage_key, verified_mime_type, file_size_bytes).
    """
    clean_name = sanitize_filename(upload.filename)
    ext = Path(clean_name).suffix.lower()
    if ext not in allowed_extensions:
        raise AppException(
            status_code=status.HTTP_400_BAD_REQUEST,
            code="INVALID_FILE_TYPE",
            message=f"File extension '{ext or 'none'}' is not allowed. Allowed: {sorted(allowed_extensions)}",
        )

    content = await upload.read()
    file_size = len(content)
    if file_size == 0:
        raise AppException(
            status_code=status.HTTP_400_BAD_REQUEST,
            code="EMPTY_FILE",
            message="Uploaded file is empty.",
        )

    max_bytes = max_size_mb * 1024 * 1024
    if file_size > max_bytes:
        raise AppException(
            status_code=status.HTTP_400_BAD_REQUEST,
            code="FILE_TOO_LARGE",
            message=f"File exceeds maximum allowed size of {max_size_mb} MB.",
        )

    if not _verify_magic_bytes(ext, content[:32]):
        raise AppException(
            status_code=status.HTTP_400_BAD_REQUEST,
            code="INVALID_FILE_SIGNATURE",
            message="File contents do not match the declared file type.",
        )

    storage_key = f"{category_dir}/{uuid.uuid4().hex}{ext}"
    save_bytes(storage_key, content)
    verified_mime = EXT_TO_MIME.get(ext, "application/octet-stream")
    return clean_name, storage_key, verified_mime, file_size


def _upload_root() -> Path:
    settings = get_settings()
    root = Path(settings.UPLOAD_DIR)
    if not root.is_absolute():
        backend_dir = Path(__file__).resolve().parents[2]
        root = backend_dir / root
    root.mkdir(parents=True, exist_ok=True)
    return root.resolve()


def resolve_storage_path(storage_key: str) -> Path:
    """Resolve storage key safely inside UPLOAD_DIR, blocking path traversal."""
    root = _upload_root()
    target = (root / storage_key).resolve()
    if not str(target).startswith(str(root)):
        raise AppException(
            status_code=status.HTTP_400_BAD_REQUEST,
            code="INVALID_STORAGE_KEY",
            message="Invalid file storage path.",
        )
    return target


def save_bytes(storage_key: str, data: bytes) -> Path:
    """Write raw bytes to local storage (or configured object storage)."""
    target = resolve_storage_path(storage_key)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(data)
    return target


def delete_stored_file(storage_key: Optional[str]) -> None:
    """Remove a stored file if it exists."""
    if not storage_key:
        return
    try:
        target = resolve_storage_path(storage_key)
        if target.exists() and target.is_file():
            os.remove(target)
    except Exception:
        pass
