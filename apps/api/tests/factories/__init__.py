"""Test factories package.

Plain async factory functions that create model state via the HTTP surface
(preferred) or the service layer (when HTTP cannot reach the required state).

Import explicitly in tests — e.g.:
    from tests.factories.user import make_user
    from tests.factories.org import make_org, add_member
"""
