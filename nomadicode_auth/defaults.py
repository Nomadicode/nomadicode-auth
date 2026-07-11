"""Inject the allauth / headless settings the package needs.

Called from ``NomadicodeAuthConfig.ready()`` so consumer projects only
configure ``NOMADICODE_AUTH`` — no ACCOUNT_* / HEADLESS_* /
SOCIALACCOUNT_* boilerplate. Any of these settings a project defines
itself in settings.py is left untouched and wins over the default.

allauth reads all of these lazily (per request / at system-check time,
both after app ``ready()``), so injecting them here is safe.
"""

from django.conf import settings as django_settings

from .conf import frontend_url, settings as pkg_settings

ADAPTER_DEFAULTS = {
    "ACCOUNT_USER_MODEL_USERNAME_FIELD": None,
    "ACCOUNT_LOGIN_METHODS": {"email"},
    "ACCOUNT_SIGNUP_FIELDS": ["email*", "password1*"],
    "ACCOUNT_ADAPTER": "nomadicode_auth.adapters.NomadicodeAccountAdapter",
    "SOCIALACCOUNT_ADAPTER": "nomadicode_auth.adapters.NomadicodeSocialAccountAdapter",
    "SOCIALACCOUNT_EMAIL_AUTHENTICATION": True,
    "HEADLESS_ONLY": True,
    "HEADLESS_TOKEN_STRATEGY": "nomadicode_auth.token_strategy.NomadicodeJWTTokenStrategy",
}


def _default(name, value):
    if not hasattr(django_settings, name):
        setattr(django_settings, name, value)


def apply_default_settings():
    for name, value in ADAPTER_DEFAULTS.items():
        _default(name, value)

    _default(
        "ACCOUNT_EMAIL_VERIFICATION",
        "mandatory" if pkg_settings.REQUIRE_VERIFIED_EMAIL else "optional",
    )

    # JWT policy comes from the NOMADICODE_AUTH keys.
    _default("HEADLESS_JWT_ALGORITHM", pkg_settings.JWT_ALGORITHM)
    _default("HEADLESS_JWT_ACCESS_TOKEN_EXPIRES_IN", pkg_settings.JWT_ACCESS_TTL)
    _default("HEADLESS_JWT_REFRESH_TOKEN_EXPIRES_IN", pkg_settings.JWT_REFRESH_TTL)
    _default("HEADLESS_JWT_ROTATE_REFRESH_TOKEN", pkg_settings.JWT_ROTATE_REFRESH)

    # Frontend URLs allauth renders into emails / redirects, derived from
    # FRONTEND_URL + the *_PATH templates ({key} placeholders intact).
    _default(
        "HEADLESS_FRONTEND_URLS",
        {
            "account_confirm_email": frontend_url(
                pkg_settings.FRONTEND_EMAIL_CONFIRM_PATH
            ),
            "account_reset_password_from_key": frontend_url(
                pkg_settings.FRONTEND_PASSWORD_RESET_PATH
            ),
            "socialaccount_login_error": frontend_url(
                pkg_settings.FRONTEND_LOGIN_ERROR_PATH
            ),
        },
    )

    # NOMADICODE_AUTH["SOCIAL"] credentials become settings-backed
    # SocialApps (no SocialApp rows needed).
    social = pkg_settings.SOCIAL
    if social:
        _default(
            "SOCIALACCOUNT_PROVIDERS",
            {provider: {"APP": dict(config)} for provider, config in social.items()},
        )
