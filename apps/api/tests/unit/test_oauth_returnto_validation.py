"""Unit tests for validate_relative_path in security.py."""

import pytest

from app.core.security import validate_relative_path


# ---------------------------------------------------------------------------
# Accepts valid relative paths
# ---------------------------------------------------------------------------


def test_accepts_root_slash():
    assert validate_relative_path("/") is True


def test_accepts_deep_path():
    assert validate_relative_path("/admin/invoices/123") is True


def test_accepts_path_with_query():
    assert validate_relative_path("/chat?foo=bar") is True


def test_accepts_path_with_fragment():
    assert validate_relative_path("/chat#section") is True


def test_accepts_path_at_max_length():
    path = "/" + "a" * 2047  # exactly 2048 chars
    assert validate_relative_path(path) is True


# ---------------------------------------------------------------------------
# Rejects invalid inputs
# ---------------------------------------------------------------------------


def test_rejects_none():
    assert validate_relative_path(None) is False


def test_rejects_empty_string():
    assert validate_relative_path("") is False


def test_rejects_protocol_relative():
    assert validate_relative_path("//evil.com/path") is False


def test_rejects_absolute_https():
    assert validate_relative_path("https://evil.com/") is False


def test_rejects_absolute_http():
    assert validate_relative_path("http://evil.com/") is False


def test_rejects_redirect_trick():
    """Defence-in-depth: path containing :// anywhere is rejected."""
    assert validate_relative_path("/redirect?next=https://evil.com") is False


def test_rejects_control_char_newline():
    assert validate_relative_path("/foo\n") is False


def test_rejects_control_char_null():
    assert validate_relative_path("/foo\x00") is False


def test_rejects_missing_leading_slash():
    assert validate_relative_path("admin/users") is False


def test_rejects_over_max_length():
    path = "/" + "a" * 2048  # 2049 chars — one over the limit
    assert validate_relative_path(path) is False


def test_rejects_javascript_scheme():
    assert validate_relative_path("javascript:alert(1)") is False
