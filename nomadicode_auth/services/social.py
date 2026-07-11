"""Mobile-friendly social login.

The mobile / SPA client obtains a provider token (Google ID token,
Facebook access token, etc.) and POSTs it to ``/auth/social/<provider>/``.
We verify it directly against the provider, then upsert a Django user
+ allauth SocialAccount link and mint a JWT.

To add a provider, register a verifier with ``@register_verifier``.
Built-in: ``google``, ``facebook``.
"""

from typing import Callable

import jwt
import requests
from allauth.socialaccount.adapter import get_adapter as get_social_adapter
from allauth.socialaccount.models import SocialAccount, SocialApp, SocialToken
from django.contrib.auth import get_user_model
from django.db import transaction

from ..conf import settings as pkg_settings

User = get_user_model()


class SocialLoginFailed(Exception):
    pass


# ---- provider verifier registry ----

_verifiers: dict[str, Callable[..., dict]] = {}


def register_verifier(provider: str):
    """Decorator: register a function returning a normalized profile dict.

    Expected return shape::

        {
          "uid": str,          # provider-side user id
          "email": str | None,
          "first_name": str,
          "last_name": str,
          "picture": str | None,
          "extra": dict,        # raw provider payload
        }
    """

    def decorator(fn):
        _verifiers[provider] = fn
        return fn

    return decorator


@register_verifier("google")
def _verify_google(
    *, id_token: str | None = None, access_token: str | None = None, **_
):
    if id_token:
        app = _require_app("google")
        try:
            unverified = jwt.decode(id_token, options={"verify_signature": False})
        except jwt.PyJWTError as exc:
            raise SocialLoginFailed("Malformed Google id_token.") from exc
        if unverified.get("aud") != app.client_id:
            raise SocialLoginFailed("Google id_token audience mismatch.")
        # Real verification against Google's tokeninfo endpoint.
        resp = requests.get(
            "https://oauth2.googleapis.com/tokeninfo",
            params={"id_token": id_token},
            timeout=10,
        )
        if resp.status_code != 200:
            raise SocialLoginFailed("Google rejected the id_token.")
        data = resp.json()
        return {
            "uid": data["sub"],
            "email": data.get("email"),
            "first_name": data.get("given_name", ""),
            "last_name": data.get("family_name", ""),
            "picture": data.get("picture"),
            "extra": data,
        }

    if not access_token:
        raise SocialLoginFailed("Google login requires id_token or access_token.")

    resp = requests.get(
        "https://www.googleapis.com/oauth2/v3/userinfo",
        headers={"Authorization": f"Bearer {access_token}"},
        timeout=10,
    )
    if resp.status_code != 200:
        raise SocialLoginFailed("Google rejected the access_token.")
    data = resp.json()
    return {
        "uid": data["sub"],
        "email": data.get("email"),
        "first_name": data.get("given_name", ""),
        "last_name": data.get("family_name", ""),
        "picture": data.get("picture"),
        "extra": data,
    }


@register_verifier("facebook")
def _verify_facebook(*, access_token: str | None = None, **_):
    if not access_token:
        raise SocialLoginFailed("Facebook login requires access_token.")

    app = _require_app("facebook")

    # debug_token tells us the token is valid and whose it is.
    debug = requests.get(
        "https://graph.facebook.com/debug_token",
        params={
            "input_token": access_token,
            "access_token": f"{app.client_id}|{app.secret}",
        },
        timeout=10,
    ).json()
    data = debug.get("data") or {}
    if not data.get("is_valid") or data.get("app_id") != app.client_id:
        raise SocialLoginFailed("Invalid Facebook token.")
    uid = data["user_id"]

    profile = requests.get(
        f"https://graph.facebook.com/{uid}",
        params={
            "fields": "id,first_name,last_name,email,picture.type(large)",
            "access_token": access_token,
        },
        timeout=10,
    ).json()
    return {
        "uid": profile["id"],
        "email": profile.get("email"),
        "first_name": profile.get("first_name", ""),
        "last_name": profile.get("last_name", ""),
        "picture": (profile.get("picture") or {}).get("data", {}).get("url"),
        "extra": profile,
    }


# ---- main entry point ----


@transaction.atomic
def login_with_provider_token(*, provider: str, request=None, **token_kwargs):
    if provider not in pkg_settings.SOCIAL_PROVIDERS:
        raise SocialLoginFailed(f"Provider '{provider}' is not enabled.")
    verifier = _verifiers.get(provider)
    if verifier is None:
        raise SocialLoginFailed(f"No verifier registered for '{provider}'.")

    profile = verifier(**token_kwargs)
    user, _ = _get_or_create_user(provider, profile)
    _link_social_account(user, provider, profile, token_kwargs)
    return user


# ---- helpers ----


def _require_app(provider: str) -> SocialApp:
    # The adapter blends DB SocialApp rows with settings-backed apps
    # (SOCIALACCOUNT_PROVIDERS / NOMADICODE_AUTH["SOCIAL"]).
    try:
        return get_social_adapter().get_app(None, provider=provider)
    except SocialApp.DoesNotExist:
        raise SocialLoginFailed(f"No SocialApp configured for '{provider}'.")


def _get_or_create_user(provider: str, profile: dict):
    existing_link = (
        SocialAccount.objects.filter(provider=provider, uid=profile["uid"])
        .select_related("user")
        .first()
    )
    if existing_link:
        return existing_link.user, False

    email = profile.get("email")
    user = None
    if email:
        user = User.objects.filter(email__iexact=email).first()
    if user is None:
        user = User.objects.create_user(
            email=email,
            password=None,
            first_name=profile.get("first_name", ""),
            last_name=profile.get("last_name", ""),
        )
        # Random unusable password — user can reset via "forgot password".
        user.set_unusable_password()

    # Social-verified emails are trusted.
    changed_fields = []
    if email and hasattr(user, "email_verified") and not user.email_verified:
        user.email_verified = True
        changed_fields.append("email_verified")
    if not user.first_name and profile.get("first_name"):
        user.first_name = profile["first_name"]
        changed_fields.append("first_name")
    if not user.last_name and profile.get("last_name"):
        user.last_name = profile["last_name"]
        changed_fields.append("last_name")
    if profile.get("picture") and hasattr(user, "profile_picture_url"):
        user.profile_picture_url = profile["picture"]
        changed_fields.append("profile_picture_url")
    if changed_fields:
        user.save(update_fields=changed_fields)
    return user, True


def _link_social_account(user, provider: str, profile: dict, token_kwargs: dict):
    link, _ = SocialAccount.objects.update_or_create(
        provider=provider,
        uid=profile["uid"],
        defaults={"user": user, "extra_data": profile.get("extra", {})},
    )
    raw_token = token_kwargs.get("access_token") or token_kwargs.get("id_token")
    if raw_token:
        # Settings-backed apps are unsaved instances — SocialToken.app is
        # nullable precisely for that case.
        app = SocialApp.objects.filter(provider=provider).first()
        SocialToken.objects.update_or_create(
            app=app, account=link, defaults={"token": raw_token}
        )
    return link
