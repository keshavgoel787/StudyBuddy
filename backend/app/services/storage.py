import os
import uuid
from pathlib import Path
from fastapi import UploadFile
from app.config import get_settings

settings = get_settings()


def save_uploaded_file(file: UploadFile, subfolder: str = "notes") -> str:
    """
    Save an uploaded file to local storage.
    Returns the relative file path.
    """
    # Create upload directory if it doesn't exist
    upload_dir = Path(settings.upload_dir) / subfolder
    upload_dir.mkdir(parents=True, exist_ok=True)

    # Generate unique filename
    file_extension = Path(file.filename).suffix
    unique_filename = f"{uuid.uuid4()}{file_extension}"
    file_path = upload_dir / unique_filename

    # Save file
    with open(file_path, "wb") as buffer:
        content = file.file.read()
        buffer.write(content)

    # Return relative path
    return str(file_path.relative_to(settings.upload_dir))


def get_file_path(relative_path: str) -> Path:
    """Get absolute path from relative path"""
    return Path(settings.upload_dir) / relative_path
