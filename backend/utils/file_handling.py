from __future__ import annotations

from pathlib import Path

from fastapi import HTTPException, UploadFile, status

SUPPORTED_EXTENSIONS: dict[str, str] = {
    ".pdb": "pdb",
    ".sdf": "sdf",
    ".mol": "mol",
    ".xyz": "xyz",
}


async def extract_file_payload(upload: UploadFile) -> tuple[str, bytes]:
    """Validate an uploaded molecule file and return its format and raw bytes."""
    if upload.filename is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Uploaded file is missing a filename.")

    suffix = Path(upload.filename).suffix.lower()
    if suffix not in SUPPORTED_EXTENSIONS:
        supported = ", ".join(sorted(SUPPORTED_EXTENSIONS))
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file type '{suffix}'. Supported extensions: {supported}.",
        )

    content = await upload.read()
    if not content:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Uploaded file is empty.")

    return SUPPORTED_EXTENSIONS[suffix], content
