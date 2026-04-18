"""Tests for migration 003_add_refresh_tokens — T-2.0 RED.

Verifies:
- Migration file exists and is structurally valid.
- Revision chain: down_revision == '002_add_user_sso_fields'.
- refresh_tokens table is present in the DB after migration is applied.
- Required columns, unique index on jti, and FK to users.id are correct.
"""

import importlib.util
from pathlib import Path

import pytest
from sqlalchemy import create_engine, inspect

from app.config import settings

MIGRATION_FILE = (
    Path(__file__).parent.parent.parent
    / "alembic"
    / "versions"
    / "003_add_refresh_tokens.py"
)


# ---------------------------------------------------------------------------
# Structural tests (no DB needed) — fail fast if file doesn't exist yet
# ---------------------------------------------------------------------------


class TestRefreshTokensMigrationStructure:
    """Given the migration file, it must be importable with correct metadata."""

    def test_migration_file_exists(self):
        """Migration file 003_add_refresh_tokens.py must exist."""
        assert MIGRATION_FILE.exists(), (
            f"Migration file not found: {MIGRATION_FILE}\n"
            "Create it with: alembic revision -m 'add_refresh_tokens'"
        )

    def test_migration_has_upgrade_and_downgrade(self):
        """Migration module must expose upgrade() and downgrade()."""
        if not MIGRATION_FILE.exists():
            pytest.skip("Migration file not found")
        spec = importlib.util.spec_from_file_location("migration_003", MIGRATION_FILE)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        assert callable(getattr(mod, "upgrade", None)), "upgrade() not found"
        assert callable(getattr(mod, "downgrade", None)), "downgrade() not found"

    def test_migration_revision_chain(self):
        """down_revision must point to 002_add_user_sso_fields."""
        if not MIGRATION_FILE.exists():
            pytest.skip("Migration file not found")
        spec = importlib.util.spec_from_file_location("migration_003", MIGRATION_FILE)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        assert mod.down_revision == "002_add_user_sso_fields", (
            f"Expected down_revision='002_add_user_sso_fields', got: {mod.down_revision!r}"
        )


# ---------------------------------------------------------------------------
# Schema tests (require DB with migration applied)
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module")
def sync_engine():
    """Synchronous SQLAlchemy engine for schema inspection."""
    engine = create_engine(settings.database_url_sync)
    yield engine
    engine.dispose()


class TestRefreshTokensSchema:
    """Given migration 003 has been applied, the schema must be correct."""

    def test_table_exists(self, sync_engine):
        """refresh_tokens table must be present after alembic upgrade head."""
        inspector = inspect(sync_engine)
        tables = inspector.get_table_names()
        assert "refresh_tokens" in tables, (
            "refresh_tokens table not found — apply the migration first:\n"
            "  cd apps/api && alembic upgrade head"
        )

    def test_required_columns_present(self, sync_engine):
        """All required columns must exist on refresh_tokens."""
        inspector = inspect(sync_engine)
        if "refresh_tokens" not in inspector.get_table_names():
            pytest.fail("refresh_tokens table missing — run: alembic upgrade head")
        cols = {c["name"] for c in inspector.get_columns("refresh_tokens")}
        required = {
            "id", "jti", "user_id", "family_id",
            "token_hash", "expires_at", "revoked_at", "created_at",
        }
        missing = required - cols
        assert not missing, f"Missing columns on refresh_tokens: {missing}"

    def test_jti_index_exists(self, sync_engine):
        """jti must have a unique index for fast token lookup."""
        inspector = inspect(sync_engine)
        if "refresh_tokens" not in inspector.get_table_names():
            pytest.fail("refresh_tokens table missing — run: alembic upgrade head")
        indexes = inspector.get_indexes("refresh_tokens")
        jti_indexes = [idx for idx in indexes if "jti" in idx["column_names"]]
        assert jti_indexes, "No index found on jti column"
        assert any(idx["unique"] for idx in jti_indexes), "jti index must be UNIQUE"

    def test_user_id_fk_to_users(self, sync_engine):
        """user_id must have FK to users.id."""
        inspector = inspect(sync_engine)
        if "refresh_tokens" not in inspector.get_table_names():
            pytest.fail("refresh_tokens table missing — run: alembic upgrade head")
        fks = inspector.get_foreign_keys("refresh_tokens")
        user_fks = [fk for fk in fks if "user_id" in fk["constrained_columns"]]
        assert user_fks, "No FK found for user_id on refresh_tokens"
        assert user_fks[0]["referred_table"] == "users"
