# Save / validate resume files
# app/services/file_handler.py

import os
import uuid
from fastapi import UploadFile, HTTPException

UPLOAD_DIR = "uploads"
ALLOWED_EXTENSIONS = {".pdf", ".docx"}
MAX_UPLOAD_SIZE = 10 * 1024 * 1024  # 10 MB

os.makedirs(UPLOAD_DIR, exist_ok=True)


def _validate_extension(filename: str) -> str:
    if not filename:
        raise HTTPException(status_code=400, detail="File name is required.")
    ext = os.path.splitext(filename)[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid file type '{ext}'. Only PDF and DOCX are accepted.",
        )
    return ext


async def save_file(file: UploadFile) -> str:
    """Validate and persist the uploaded file; returns the on-disk path."""
    if not file:
        raise HTTPException(status_code=400, detail="No file uploaded.")

    ext = _validate_extension(file.filename)
    content = await file.read()

    if not content:
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")
    if len(content) > MAX_UPLOAD_SIZE:
        mb = MAX_UPLOAD_SIZE // (1024 * 1024)
        raise HTTPException(
            status_code=413,
            detail=f"File exceeds the {mb} MB limit.",
        )

    unique_name = f"{uuid.uuid4().hex}{ext}"
    file_path = os.path.join(UPLOAD_DIR, unique_name)

    try:
        with open(file_path, "wb") as fh:
            fh.write(content)
    except OSError as exc:
        raise HTTPException(status_code=500, detail=f"Error saving file: {exc}")

    return file_path
