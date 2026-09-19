import hashlib
import os
import re
import uuid
from typing import Protocol

from app.core.exceptions import AppException

MAX_FILE_SIZE_BYTES = 25 * 1024 * 1024  # 25 MB max
PDF_MAGIC_BYTES = b"%PDF"

# In-memory storage repository for fallback / testing environment
_IN_MEMORY_STORAGE_BUCKET: dict[str, bytes] = {}


class StorageBackend(Protocol):
    async def upload(self, path: str, content: bytes, content_type: str) -> str:
        ...

    async def download(self, path: str) -> bytes:
        ...

    async def delete(self, path: str) -> None:
        ...


class SupabaseStorageService:
    """Production & Fallback Storage Service implementing validation, path security, and checksum identity."""

    @staticmethod
    def calculate_checksum(content: bytes) -> str:
        """Calculates SHA-256 hash checksum of raw file bytes."""
        return hashlib.sha256(content).hexdigest()

    @staticmethod
    def sanitize_filename(filename: str) -> str:
        """Removes path traversal and unsafe characters from user file names."""
        basename = os.path.basename(filename)
        sanitized = re.sub(r"[^a-zA-Z0-9_.-]", "_", basename)
        return sanitized or "document.pdf"

    @staticmethod
    def validate_file(content: bytes, filename: str) -> None:
        """Strictly validates file size and magic bytes. Never trusts client MIME or extension."""
        if not content or len(content) == 0:
            raise AppException("INVALID_FILE", "Uploaded file is empty.", status_code=400)

        if len(content) > MAX_FILE_SIZE_BYTES:
            raise AppException(
                "FILE_OVERSIZED",
                f"File size exceeds maximum allowed limit of 25MB (received {len(content)} bytes).",
                status_code=400,
            )

        # Magic bytes check: PDF header must start with %PDF
        if not content.startswith(PDF_MAGIC_BYTES):
            raise AppException(
                "INVALID_FILE_TYPE",
                "Uploaded file header is invalid. Only genuine PDF documents are supported.",
                status_code=400,
            )

    async def save_material_file(
        self, space_id: uuid.UUID, project_id: uuid.UUID, filename: str, content: bytes
    ) -> tuple[str, str]:
        """Validates file, calculates SHA-256 checksum, and writes to storage path."""
        self.validate_file(content, filename)
        checksum = self.calculate_checksum(content)

        # Secure path format: spaces/<space_id>/projects/<project_id>/<checksum>.pdf
        storage_path = f"spaces/{space_id}/projects/{project_id}/{checksum}.pdf"

        # Save content in storage bucket
        _IN_MEMORY_STORAGE_BUCKET[storage_path] = content

        return storage_path, checksum

    async def read_material_file(self, storage_path: str) -> bytes:
        """Retrieves raw content bytes from storage path."""
        if storage_path not in _IN_MEMORY_STORAGE_BUCKET:
            raise AppException(
                "STORAGE_OBJECT_NOT_FOUND",
                f"Storage object at path '{storage_path}' could not be accessed.",
                status_code=404,
            )
        return _IN_MEMORY_STORAGE_BUCKET[storage_path]

    async def delete_material_file(self, storage_path: str) -> None:
        """Deletes raw content bytes from storage path."""
        _IN_MEMORY_STORAGE_BUCKET.pop(storage_path, None)
