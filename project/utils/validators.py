"""Input validation utilities."""

from __future__ import annotations

import logging
import re
from typing import Tuple

logger = logging.getLogger(__name__)

EMAIL_PATTERN = re.compile(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$")
USERNAME_PATTERN = re.compile(r"^[a-zA-Z0-9_]{3,30}$")


def validate_username(username: str) -> Tuple[bool, str]:
    """Validate username format."""
    try:
        if not username or not username.strip():
            return False, "Username is required."
        if not USERNAME_PATTERN.match(username.strip()):
            return (
                False,
                "Username must be 3-30 characters (letters, numbers, underscore).",
            )
        return True, ""
    except Exception as exc:
        logger.exception("validate_username error: %s", exc)
        return False, "Invalid username."


def validate_email(email: str) -> Tuple[bool, str]:
    """Validate email format."""
    try:
        if not email or not email.strip():
            return False, "Email is required."
        if not EMAIL_PATTERN.match(email.strip()):
            return False, "Invalid email address."
        return True, ""
    except Exception as exc:
        logger.exception("validate_email error: %s", exc)
        return False, "Invalid email."


def validate_password(password: str, confirm: str = "") -> Tuple[bool, str]:
    """Validate password strength and optional confirmation."""
    try:
        if not password:
            return False, "Password is required."
        if len(password) < 8:
            return False, "Password must be at least 8 characters."
        if confirm and password != confirm:
            return False, "Passwords do not match."
        return True, ""
    except Exception as exc:
        logger.exception("validate_password error: %s", exc)
        return False, "Invalid password."


def validate_pdf_filename(filename: str) -> Tuple[bool, str]:
    """Ensure uploaded file is a PDF."""
    try:
        if not filename:
            return False, "No file selected."
        if not filename.lower().endswith(".pdf"):
            return False, "Only PDF files are supported."
        return True, ""
    except Exception as exc:
        logger.exception("validate_pdf_filename error: %s", exc)
        return False, "Invalid file."
