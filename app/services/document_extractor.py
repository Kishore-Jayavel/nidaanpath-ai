"""
NidaanPath AI — app/services/document_extractor.py
Handles PDF text extraction and file validation.
"""
from __future__ import annotations
import os
import re
from typing import Optional, Tuple


ALLOWED_EXTENSIONS = {'pdf', 'png', 'jpg', 'jpeg'}
ALLOWED_MIMETYPES = {'application/pdf', 'image/png', 'image/jpeg'}


def allowed_file(filename: str) -> bool:
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def extract_text_from_pdf(file_path: str) -> Tuple[str, bool]:
    """
    Extract text from a PDF file.
    Returns (text, success).
    """
    try:
        from pypdf import PdfReader
        reader = PdfReader(file_path)
        text_parts = []
        for page in reader.pages:
            t = page.extract_text()
            if t:
                text_parts.append(t)
        full_text = '\n'.join(text_parts).strip()
        return full_text, bool(full_text)
    except Exception as e:
        return f"[PDF extraction failed: {e}]", False


def extract_text_from_image(file_path: str) -> Tuple[str, bool]:
    """
    Extract text from an image (OCR fallback).
    Returns (text, success).
    """
    try:
        import pytesseract
        from PIL import Image
        img = Image.open(file_path)
        text = pytesseract.image_to_string(img)
        return text.strip(), bool(text.strip())
    except Exception:
        return "[Image OCR not available — install Tesseract for image text extraction]", False


def extract_text(file_path: str) -> Tuple[str, bool]:
    """Route extraction to PDF or image handler based on extension."""
    ext = file_path.rsplit('.', 1)[-1].lower()
    if ext == 'pdf':
        return extract_text_from_pdf(file_path)
    elif ext in {'png', 'jpg', 'jpeg'}:
        return extract_text_from_image(file_path)
    return "[Unsupported file type]", False


def get_demo_report_number(filename: str) -> Optional[int]:
    """Detect demo report number from filename (e.g., '01_initial...' → 1)."""
    match = re.match(r'^0?(\d+)_', os.path.basename(filename))
    if match:
        num = int(match.group(1))
        if 1 <= num <= 10:
            return num
    return None


def secure_save_file(file_obj, upload_folder: str) -> Tuple[str, str]:
    """
    Save an uploaded file securely and return (secure_filename, full_path).
    """
    from werkzeug.utils import secure_filename
    import uuid
    fname = secure_filename(file_obj.filename)
    unique_name = f"{uuid.uuid4().hex}_{fname}"
    full_path = os.path.join(upload_folder, unique_name)
    file_obj.save(full_path)
    return unique_name, full_path
