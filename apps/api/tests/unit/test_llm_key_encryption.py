"""Unit tests for LLMKeyEncryption — byok-plan-gate Sprint.

Tests v1 round-trip, legacy row detection, key isolation, and config behaviour.
No DB, no Docker required.
Run: python -m pytest tests/unit/test_llm_key_encryption.py -v
"""

import base64
import hashlib

import pytest
from cryptography.fernet import Fernet

from app.services.llm_key_encryption import LLMKeyEncryption


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_byok_key() -> bytes:
    """Generate a fresh valid Fernet key."""
    return Fernet.generate_key()


def _derive_legacy(secret: str) -> bytes:
    """Reproduce legacy derivation for test assertions."""
    return base64.urlsafe_b64encode(hashlib.sha256(secret.encode()).digest())


# ---------------------------------------------------------------------------
# v1 round-trip
# ---------------------------------------------------------------------------


class TestV1RoundTrip:
    def test_encrypt_produces_v1_prefix(self):
        svc = LLMKeyEncryption(byok_key=_make_byok_key(), legacy_secret="s")
        ct = svc.encrypt("sk-test-key-12345")
        assert ct.startswith("v1:"), f"Expected v1: prefix, got: {ct[:10]}"

    def test_decrypt_v1_returns_original(self):
        svc = LLMKeyEncryption(byok_key=_make_byok_key(), legacy_secret="s")
        plaintext = "sk-openai-key-abc123"
        ct = svc.encrypt(plaintext)
        recovered, needs_reencrypt = svc.decrypt(ct)
        assert recovered == plaintext
        assert needs_reencrypt is False

    def test_v1_needs_reencryption_is_false(self):
        svc = LLMKeyEncryption(byok_key=_make_byok_key(), legacy_secret="s")
        _, needs_reencrypt = svc.decrypt(svc.encrypt("anything"))
        assert needs_reencrypt is False


# ---------------------------------------------------------------------------
# Legacy row detection and lazy migration signal
# ---------------------------------------------------------------------------


class TestLegacyDecrypt:
    def _make_legacy_row(self, secret: str, plaintext: str) -> str:
        """Produce a legacy-format ciphertext (no v1: prefix)."""
        fernet = Fernet(_derive_legacy(secret))
        return fernet.encrypt(plaintext.encode()).decode()

    def test_legacy_decrypt_returns_plaintext(self):
        secret = "jwt-secret-abc"
        svc = LLMKeyEncryption(byok_key=_make_byok_key(), legacy_secret=secret)
        legacy_ct = self._make_legacy_row(secret, "my-api-key")
        plaintext, _ = svc.decrypt(legacy_ct)
        assert plaintext == "my-api-key"

    def test_legacy_decrypt_flags_reencryption(self):
        secret = "jwt-secret-abc"
        svc = LLMKeyEncryption(byok_key=_make_byok_key(), legacy_secret=secret)
        legacy_ct = self._make_legacy_row(secret, "my-api-key")
        _, needs_reencrypt = svc.decrypt(legacy_ct)
        assert needs_reencrypt is True

    def test_legacy_without_legacy_key_raises(self):
        """If no legacy_secret is provided, legacy rows cannot be decrypted."""
        byok_key = _make_byok_key()
        svc = LLMKeyEncryption(byok_key=byok_key, legacy_secret=None)

        # Produce a legacy row using a separate fernet
        fernet = Fernet(_derive_legacy("some-secret"))
        legacy_ct = fernet.encrypt(b"key").decode()

        with pytest.raises(ValueError, match="no legacy fallback"):
            svc.decrypt(legacy_ct)

    def test_corrupt_legacy_payload_raises_value_error(self):
        svc = LLMKeyEncryption(byok_key=_make_byok_key(), legacy_secret="jwt-secret")
        with pytest.raises(ValueError, match="Legacy row decrypt failed"):
            svc.decrypt("not-valid-fernet-data-at-all")


# ---------------------------------------------------------------------------
# Key isolation: BYOK_ENCRYPTION_KEY vs JWT-derived
# ---------------------------------------------------------------------------


class TestKeyIsolation:
    def test_byok_key_produces_different_ciphertext_than_legacy(self):
        """A row encrypted with the new BYOK key must NOT be decryptable by the legacy key."""
        secret = "shared-jwt-secret"
        byok_key = _make_byok_key()
        svc = LLMKeyEncryption(byok_key=byok_key, legacy_secret=secret)

        v1_ct = svc.encrypt("plaintext-value")
        assert v1_ct.startswith("v1:")

        # Attempt to decrypt v1 ciphertext with legacy Fernet alone — must fail
        legacy_fernet = Fernet(_derive_legacy(secret))
        raw_ct = v1_ct[len("v1:"):]
        with pytest.raises(Exception):  # InvalidToken or similar
            legacy_fernet.decrypt(raw_ct.encode())

    def test_different_byok_keys_produce_non_interchangeable_ciphertexts(self):
        key_a = _make_byok_key()
        key_b = _make_byok_key()
        svc_a = LLMKeyEncryption(byok_key=key_a, legacy_secret="s")
        svc_b = LLMKeyEncryption(byok_key=key_b, legacy_secret="s")

        ct = svc_a.encrypt("my-key")
        with pytest.raises(Exception):
            svc_b.decrypt(ct)


# ---------------------------------------------------------------------------
# Dev fallback when BYOK_ENCRYPTION_KEY is missing
# ---------------------------------------------------------------------------


class TestDevFallback:
    def test_missing_byok_key_with_legacy_secret_warns_and_works(self, caplog):
        """byok_key=None + legacy_secret → falls back to JWT-derived key with a warning."""
        import logging
        with caplog.at_level(logging.WARNING, logger="app.services.llm_key_encryption"):
            svc = LLMKeyEncryption(byok_key=None, legacy_secret="dev-secret")

        assert any("BYOK_ENCRYPTION_KEY is not set" in r.message for r in caplog.records)
        # Encryption still works
        ct = svc.encrypt("key-value")
        assert ct.startswith("v1:")
        plaintext, _ = svc.decrypt(ct)
        assert plaintext == "key-value"

    def test_missing_both_byok_and_legacy_raises_runtime_error(self):
        """byok_key=None AND legacy_secret=None → RuntimeError at construction."""
        with pytest.raises(RuntimeError, match="both byok_key and legacy_secret are None"):
            LLMKeyEncryption(byok_key=None, legacy_secret=None)
