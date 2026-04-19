"""Input validation and sanitization utilities."""

import html
import re

# ---------------------------------------------------------------------------
# Password policy constants
# ---------------------------------------------------------------------------

MIN_PASSWORD_LENGTH = 8
MAX_PASSWORD_LENGTH = 128


def validate_password(password: str) -> tuple[bool, str]:
    """Validate password strength.

    Returns:
        (is_valid, error_message) — error_message is empty string when valid.
    """
    if len(password) < MIN_PASSWORD_LENGTH:
        return False, f"Password must be at least {MIN_PASSWORD_LENGTH} characters"
    if len(password) > MAX_PASSWORD_LENGTH:
        return False, f"Password must be at most {MAX_PASSWORD_LENGTH} characters"
    if not re.search(r"[A-Z]", password):
        return False, "Password must contain at least one uppercase letter"
    if not re.search(r"[a-z]", password):
        return False, "Password must contain at least one lowercase letter"
    if not re.search(r"[0-9]", password):
        return False, "Password must contain at least one digit"
    return True, ""


# ---------------------------------------------------------------------------
# Input sanitization
# ---------------------------------------------------------------------------


def sanitize_input(text: str, max_length: int = 10000) -> str:
    """Sanitize user input for storage — strip dangerous content.

    Use only on content being STORED (e.g. document titles, names).
    Do NOT use on search/query parameters — lawyers type special chars
    like "Art. 1351" and those must reach the query engine intact.
    """
    if not text:
        return ""
    # Truncate to configured max
    text = text[:max_length]
    # Remove null bytes (can cause issues in C extensions and databases)
    text = text.replace("\x00", "")
    # Escape HTML entities to prevent XSS in stored content
    text = html.escape(text)
    return text.strip()


# ---------------------------------------------------------------------------
# Slug validation
# ---------------------------------------------------------------------------


def validate_slug(slug: str) -> tuple[bool, str]:
    """Validate URL slug format.

    Rules: lowercase alphanumeric, hyphens allowed, no leading/trailing hyphens,
    3–50 characters.
    """
    if not slug:
        return False, "Slug cannot be empty"
    if len(slug) < 3 or len(slug) > 50:
        return False, "Slug must be 3-50 characters"
    if not re.match(r"^[a-z0-9][a-z0-9-]*[a-z0-9]$", slug):
        return (
            False,
            "Slug must be lowercase alphanumeric with hyphens, "
            "no leading/trailing hyphens",
        )
    return True, ""


# ---------------------------------------------------------------------------
# Email format validation
# ---------------------------------------------------------------------------


def validate_email_format(email: str) -> tuple[bool, str]:
    """Basic email format validation (does not verify deliverability)."""
    if not email or len(email) > 320:
        return False, "Invalid email"
    pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
    if not re.match(pattern, email):
        return False, "Invalid email format"
    return True, ""


# ---------------------------------------------------------------------------
# SQL injection prevention — whitelist validators for dynamic query params
# ---------------------------------------------------------------------------

_VALID_LEGAL_AREAS: frozenset[str] = frozenset(
    {
        "civil",
        "penal",
        "laboral",
        "tributario",
        "administrativo",
        "corporativo",
        "constitucional",
        "registral",
        "competencia",
        "compliance",
        "comercio_exterior",
    }
)


def validate_legal_area(area: str) -> bool:
    """Whitelist validation for legal area parameter used in raw queries."""
    return area in _VALID_LEGAL_AREAS


def validate_sort_field(field: str, allowed: set[str]) -> bool:
    """Whitelist validation for ORDER BY fields (prevents SQL injection)."""
    return field in allowed
