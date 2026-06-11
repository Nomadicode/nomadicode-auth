"""Mint access/refresh tokens server-side (post-signup, post-verify, tests)."""

from importlib import import_module

from allauth.headless.tokens.strategies.jwt.internal import (
    create_access_token,
    create_refresh_token,
)
from django.conf import settings
from django.contrib.auth import (
    BACKEND_SESSION_KEY,
    HASH_SESSION_KEY,
    SESSION_KEY,
)


def _new_session_for_user(user):
    """Create a session carrying full Django auth state.

    Refresh-token validation resolves the user through Django's
    ``auth.get_user()``, which needs the backend path and the session
    auth hash in addition to the user id — a bare ``_auth_user_id``
    yields AnonymousUser and refresh fails. Mirrors ``auth.login()``
    without the request/signal machinery.
    """
    engine = import_module(settings.SESSION_ENGINE)
    session = engine.SessionStore()
    session[SESSION_KEY] = user._meta.pk.value_to_string(user)
    session[BACKEND_SESSION_KEY] = "django.contrib.auth.backends.ModelBackend"
    session[HASH_SESSION_KEY] = user.get_session_auth_hash()
    session.save()
    return session


def issue_jwt_for_user(user, claims=None):
    session = _new_session_for_user(user)
    merged = {"user_id": str(user.pk)}
    if claims:
        merged.update(claims)
    access = create_access_token(user, session, merged)
    refresh = create_refresh_token(user, session)
    session.save()
    return access, refresh
