"""Authentication service with bcrypt password hashing."""

from __future__ import annotations

import logging
from typing import Optional, Tuple

import bcrypt
from sqlalchemy.orm import Session

from database import crud
from models.user import User
from utils.validators import validate_email, validate_password, validate_username

logger = logging.getLogger(__name__)


class AuthService:
    """Handles user registration, login, and password verification."""

    @staticmethod
    def hash_password(password: str) -> str:
        """
        Hash a plain-text password with bcrypt.

        Args:
            password: Plain password.

        Returns:
            UTF-8 decoded hash string.
        """
        try:
            salt = bcrypt.gensalt(rounds=12)
            hashed = bcrypt.hashpw(password.encode("utf-8"), salt)
            return hashed.decode("utf-8")
        except Exception as exc:
            logger.exception("hash_password failed: %s", exc)
            raise

    @staticmethod
    def verify_password(password: str, password_hash: str) -> bool:
        """
        Verify password against stored hash.

        Args:
            password: Plain password.
            password_hash: Stored bcrypt hash.

        Returns:
            True if password matches.
        """
        try:
            return bcrypt.checkpw(
                password.encode("utf-8"),
                password_hash.encode("utf-8"),
            )
        except Exception as exc:
            logger.exception("verify_password failed: %s", exc)
            return False

    def register(
        self,
        db: Session,
        username: str,
        email: str,
        password: str,
        confirm_password: str,
    ) -> Tuple[bool, str, Optional[User]]:
        """
        Register a new user.

        Returns:
            Tuple of (success, message, user).
        """
        try:
            ok, msg = validate_username(username)
            if not ok:
                return False, msg, None

            ok, msg = validate_email(email)
            if not ok:
                return False, msg, None

            ok, msg = validate_password(password, confirm_password)
            if not ok:
                return False, msg, None

            if crud.get_user_by_username(db, username):
                return False, "Username already taken.", None

            if crud.get_user_by_email(db, email):
                return False, "Email already registered.", None

            password_hash = self.hash_password(password)
            user = crud.create_user(db, username, email, password_hash)
            db.commit()
            logger.info("User registered: %s", username)
            return True, "Registration successful.", user
        except Exception as exc:
            db.rollback()
            logger.exception("register failed: %s", exc)
            return False, f"Registration failed: {exc}", None

    def login(
        self,
        db: Session,
        username: str,
        password: str,
    ) -> Tuple[bool, str, Optional[User]]:
        """
        Authenticate user credentials.

        Returns:
            Tuple of (success, message, user).
        """
        try:
            if not username or not password:
                return False, "Username and password are required.", None

            user = crud.get_user_by_username(db, username)
            if not user:
                return False, "Invalid username or password.", None

            if not self.verify_password(password, user.password_hash):
                return False, "Invalid username or password.", None

            logger.info("User logged in: %s", user.username)
            return True, "Login successful.", user
        except Exception as exc:
            logger.exception("login failed: %s", exc)
            return False, f"Login failed: {exc}", None

    def get_user(self, db: Session, user_id: int) -> Optional[User]:
        """Fetch user by ID."""
        try:
            return crud.get_user_by_id(db, user_id)
        except Exception as exc:
            logger.exception("get_user failed: %s", exc)
            return None


auth_service = AuthService()
