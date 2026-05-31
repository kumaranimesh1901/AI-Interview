"""Cloud file storage service using Cloudinary."""

from __future__ import annotations

import logging
import os
from typing import Optional

import cloudinary
import cloudinary.api
import cloudinary.uploader

from config.settings import settings

logger = logging.getLogger(__name__)


class StorageService:
    """Handles file uploads and retrieval via Cloudinary."""

    def __init__(self) -> None:
        """Configure Cloudinary from environment settings."""
        cloudinary.config(
            cloud_name=settings.CLOUDINARY_CLOUD_NAME,
            api_key=settings.CLOUDINARY_API_KEY,
            api_secret=settings.CLOUDINARY_API_SECRET,
        )

    def upload_resume(self, file, user_id: int) -> dict:
        """
        Upload a resume PDF to Cloudinary.

        Args:
            file: File-like object or bytes to upload.
            user_id: Owner user ID (used for folder organization).

        Returns:
            Dict with ``url`` (secure URL) and ``public_id``.
        """
        try:
            result = cloudinary.uploader.upload(
                file,
                folder=f"resumes/user_{user_id}",
                resource_type="raw",
                format="pdf",
            )
            return {
                "url": result["secure_url"],
                "public_id": result["public_id"],
            }
        except Exception as exc:
            logger.error("Upload error: %s", exc)
            raise

    def get_resume_url(self, public_id: str) -> str:
        """
        Build a secure URL for a stored resume.

        Args:
            public_id: Cloudinary public ID.

        Returns:
            HTTPS URL string.
        """
        return cloudinary.CloudinaryImage(public_id).build_url()

    def delete_resume(self, public_id: str) -> bool:
        """
        Delete a resume from Cloudinary.

        Args:
            public_id: Cloudinary public ID.

        Returns:
            True if deleted successfully, False on error.
        """
        try:
            cloudinary.uploader.destroy(public_id, resource_type="raw")
            return True
        except Exception as exc:
            logger.error("Delete error: %s", exc)
            return False


# Singleton for app-wide use
storage_service = StorageService()
