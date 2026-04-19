"""Unit tests — lazy re-encryption persistence (byok-plan-gate C2).

Verifies that when a UserLLMKey row contains a legacy-format encrypted key
(no 'v1:' prefix, encrypted with JWT_SECRET), the first USE (decrypt call via
get_user_key_for_provider) re-encrypts the key with BYOK_ENCRYPTION_KEY and
persists the updated value to the DB via db.flush().

Design ref: apps/api/app/services/llm_key_service.py — lazy migration block.
"""

from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


@pytest.mark.asyncio
async def test_lazy_reencryption_persists_v1_prefix_on_first_use():
    """Legacy key (no v1: prefix) is re-encrypted and persisted with v1: prefix on first USE."""
    from app.services.llm_key_service import get_user_key_for_provider

    # Arrange — simulate a legacy UserLLMKey row
    mock_key_row = MagicMock()
    mock_key_row.api_key_encrypted = "legacy_encrypted_payload"  # no v1: prefix
    mock_key_row.user_id = "aaaaaaaa-0000-0000-0000-000000000001"
    mock_key_row.provider = "google"
    mock_key_row.is_active = True
    mock_key_row.created_at = datetime.now(UTC)
    mock_key_row.updated_at = None

    mock_scalar_result = MagicMock()
    mock_scalar_result.scalar_one_or_none.return_value = mock_key_row

    mock_db = AsyncMock()
    mock_db.execute.return_value = mock_scalar_result

    with patch("app.services.llm_key_service.llm_key_crypto") as mock_crypto:
        # decrypt returns (plaintext, needs_reencrypt=True) for legacy keys
        mock_crypto.decrypt.return_value = ("plain-api-key-1234", True)
        # encrypt returns a v1-prefixed ciphertext
        mock_crypto.encrypt.return_value = "v1:new_encrypted_payload_abc"

        result = await get_user_key_for_provider("aaaaaaaa-0000-0000-0000-000000000001", "google", mock_db)

    # Assert — plaintext is returned correctly
    assert result == "plain-api-key-1234"

    # Assert — re-encrypted key is written back to the row with v1: prefix
    assert mock_key_row.api_key_encrypted == "v1:new_encrypted_payload_abc"
    assert mock_key_row.api_key_encrypted.startswith("v1:")

    # Assert — updated_at was refreshed
    assert mock_key_row.updated_at is not None

    # Assert — db.flush() was called to persist the migration
    mock_db.flush.assert_called_once()


@pytest.mark.asyncio
async def test_no_reencryption_when_key_already_v1():
    """Modern v1: key does NOT trigger re-encryption or db.flush()."""
    from app.services.llm_key_service import get_user_key_for_provider

    mock_key_row = MagicMock()
    mock_key_row.api_key_encrypted = "v1:already_modern_payload"
    mock_key_row.user_id = "aaaaaaaa-0000-0000-0000-000000000002"
    mock_key_row.provider = "openai"
    mock_key_row.is_active = True
    mock_key_row.created_at = datetime.now(UTC)

    mock_scalar_result = MagicMock()
    mock_scalar_result.scalar_one_or_none.return_value = mock_key_row

    mock_db = AsyncMock()
    mock_db.execute.return_value = mock_scalar_result

    with patch("app.services.llm_key_service.llm_key_crypto") as mock_crypto:
        # needs_reencrypt=False for modern keys
        mock_crypto.decrypt.return_value = ("sk-modern-key", False)

        result = await get_user_key_for_provider("aaaaaaaa-0000-0000-0000-000000000002", "openai", mock_db)

    assert result == "sk-modern-key"

    # encrypt must NOT have been called
    mock_crypto.encrypt.assert_not_called()

    # db.flush must NOT have been called
    mock_db.flush.assert_not_called()


@pytest.mark.asyncio
async def test_returns_none_when_no_key_found():
    """Returns None gracefully when the user has no key for the requested provider."""
    from app.services.llm_key_service import get_user_key_for_provider

    mock_scalar_result = MagicMock()
    mock_scalar_result.scalar_one_or_none.return_value = None

    mock_db = AsyncMock()
    mock_db.execute.return_value = mock_scalar_result

    result = await get_user_key_for_provider("aaaaaaaa-0000-0000-0000-000000000003", "anthropic", mock_db)

    assert result is None
    mock_db.flush.assert_not_called()
