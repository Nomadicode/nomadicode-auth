"""Mint access/refresh tokens server-side (post-signup, post-verify, tests)."""

from importlib import import_module

from allauth.headless.tokens.strategies.jwt.internal import (
    create_access_token,
    create_refresh_token,
)
from django.conf import settings


def _new_session_for_user(user):
    engine = import_module(settings.SESSION_ENGINE)
    session = engine.SessionStore()
    session["_auth_user_id"] = str(user.pk)
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
