"""
LLM Key Encryption Service — versioned Fernet-based encryption for BYOK keys.

Payload format:
  - New rows:    "v1:<fernet-ciphertext>"
  - Legacy rows: "<fernet-ciphertext>"  (no prefix, JWT_SECRET-derived key)

On decrypt, legacy rows are flagged (needs_reencryption=True) so the caller can
UPDATE the row to the v1 format (lazy migration).
"""

from __future__ import annotations

import base64
import hashlib
import logging

from cryptography.fernet import Fernet, InvalidToken

logger = logging.getLogger(__name__)

_CURRENT_VERSION = "v1"
_PREFIX = f"{_CURRENT_VERSION}:"


class LLMKeyEncryption:
    """Versioned Fernet encryption for BYOK LLM keys.

    Construction:
        byok_key      — raw bytes of the BYOK_ENCRYPTION_KEY (Fernet-compatible).
                        If None, falls back to a key derived from legacy_secret (dev only).
        legacy_secret — JWT_SECRET string, used to derive the legacy Fernet key for
                        decrypting old rows that have no v1: prefix.
    """

    def __init__(self, byok_key: bytes | None, legacy_secret: str | None) -> None:
        if byok_key is None:
            # Dev fallback: derive encryption key from JWT_SECRET.
            # Production raises at config load time (config/__init__.py) before we get here.
            logger.warning(
                "BYOK_ENCRYPTION_KEY is not set; deriving encryption key from "
                "JWT_SECRET (dev fallback only). DO NOT USE IN PRODUCTION."
            )
            if legacy_secret is None:
                raise RuntimeError(
                    "Cannot initialise LLMKeyEncryption: both byok_key and "
                    "legacy_secret are None."
                )
            byok_key = self._derive_legacy_key(legacy_secret)

        self._current_fernet = Fernet(byok_key)
        self._legacy_fernet: Fernet | None = (
            Fernet(self._derive_legacy_key(legacy_secret)) if legacy_secret else None
        )

    @staticmethod
    def _derive_legacy_key(secret: str) -> bytes:
        """Reproduce the pre-v1 SHA-256 → base64url Fernet key derivation.

        SHA-256 always produces 32 bytes; base64url-encoding yields a valid 44-char
        Fernet key. This matches the original llm_key_service.py derivation exactly.
        """
        return base64.urlsafe_b64encode(hashlib.sha256(secret.encode()).digest())

    def encrypt(self, plaintext: str) -> str:
        """Encrypt plaintext. Returns 'v1:<ciphertext>'."""
        ct = self._current_fernet.encrypt(plaintext.encode()).decode()
        return f"{_PREFIX}{ct}"

    def decrypt(self, stored: str) -> tuple[str, bool]:
        """Decrypt a stored value.

        Returns:
            (plaintext, needs_reencryption)

            needs_reencryption is True when the row used the legacy (no-prefix) format.
            The caller SHOULD UPDATE the DB row to migrate it to the v1 format.

        Raises:
            ValueError — if the payload cannot be decrypted (corrupt or wrong key).
        """
        if stored.startswith(_PREFIX):
            ct = stored[len(_PREFIX):]
            return self._current_fernet.decrypt(ct.encode()).decode(), False

        # Legacy row: no prefix, JWT_SECRET-derived key.
        if self._legacy_fernet is None:
            raise ValueError(
                "Legacy LLM key row encountered but no legacy fallback key configured. "
                "Ensure jwt_secret is available during service initialisation."
            )
        try:
            plaintext = self._legacy_fernet.decrypt(stored.encode()).decode()
            return plaintext, True
        except InvalidToken as exc:
            raise ValueError(
                "Legacy row decrypt failed — payload may be corrupt or encrypted "
                "with a different JWT_SECRET."
            ) from exc


def _build_singleton() -> LLMKeyEncryption:
    """Construct the module-level singleton by reading settings."""
    from app.config import settings  # lazy import avoids circular at collection time

    byok_raw = settings.byok_encryption_key
    byok_key: bytes | None = byok_raw.encode() if byok_raw else None
    return LLMKeyEncryption(byok_key=byok_key, legacy_secret=settings.jwt_secret)


#: Module-level singleton — import this everywhere instead of constructing ad-hoc.
llm_key_crypto: LLMKeyEncryption = _build_singleton()
